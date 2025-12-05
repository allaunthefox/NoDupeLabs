# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""NSFW content classification system.

This module implements a multi-tier classification system to detect
potentially NSFW (Not Safe For Work) content. It combines fast heuristics
(filename patterns) with deeper analysis (metadata, ML models) to provide
a confidence score for each file.

Key Features:
    - Tier 1: Filename/path regex matching (instant)
    - Tier 2: Image metadata analysis (resolution, EXIF)
    - Tier 3: Content analysis via ML backends (optional)
    - Privacy-preserving: Fully offline, no data upload
    - Configurable sensitivity threshold

Classes:
    - NSFWClassifier: Main classification engine

Dependencies:
    - re: Regex pattern matching
    - PIL: Image metadata analysis (optional)
    - ..ai.backends: ML model integration (optional)

Example:
    >>> classifier = NSFWClassifier(threshold=2)
    >>> result = classifier.classify(Path("image.jpg"), "image/jpeg")
    >>> if result['flagged']:
    ...     print(f"NSFW detected: {result['reason']}")
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from .deps import check_dep


class NSFWClassifier:
    """Multi-tier NSFW content detector.

    Combines multiple analysis methods to produce a cumulative risk score
    (0-3) for each file. Higher scores indicate higher likelihood of
    NSFW content.

    Confidence Levels:
        0: Safe (no indicators found)
        1: Suspicious (weak indicators, e.g., 'beach', 'model')
        2: Likely (strong indicators, e.g., 'onlyfans', specific sites)
        3: Certain (explicit keywords)

    Attributes:
        threshold (int): Minimum score to flag as NSFW (0-3)
        has_pillow (bool): Whether Pillow is available for image analysis
        backend (Backend): Optional ML backend for content analysis
    """

    # Filename patterns with confidence weights
    FILENAME_PATTERNS: Dict[str, int] = {
        # High confidence (3) - explicit indicators
        r'\b(nsfw|xxx|porn|nude|adult|explicit|18\+|r18|r-18)\b': 3,
        r'\b(sex|hentai|ecchi|lewd|erotic|fetish|bdsm)\b': 3,
        r'\b(blowjob|cum|facial|anal|creampie|milf|teen|threesome|orgy)\b': 3,

        # Medium confidence (2) - strong indicators
        r'\b(onlyfans|patreon|fanbox|subscribestar|fansly|gumroad)\b': 2,
        r'\b(uncensored|uncut|raw|leaked|private|premium)\b': 2,
        r'\b(camgirl|webcam|chaturbate|myfreecams)\b': 2,

        # Low confidence (1) - weak indicators
        r'\b(sexy|hot|lingerie|bikini|bath|shower|swimsuit)\b': 1,
        r'_[0-9]{4}x[0-9]{4,}_': 1,  # High-res images (4000x3000+)
        r'\b(night|secret|hidden|folder|collection|pack)\b': 1,
        r'\b(model|photoshoot|glamour|boudoir)\b': 1,
    }

    # Safe patterns that reduce score
    SAFE_PATTERNS: Dict[str, int] = {
        r'\b(family|vacation|wedding|birthday|graduation|portrait|baby|'
        r'kids)\b':
        -2,
        r'\b(landscape|nature|pet|animal|food|recipe|cooking|garden)\b': -2,
        r'\b(work|office|project|document|invoice|receipt|report|finance)\b':
        -3,
        r'\b(screenshot|screen|desktop|wallpaper|game|gameplay)\b': -2,
        # Art can be NSFW but often isn't
        r'\b(art|drawing|sketch|painting|illustration|anime|manga)\b': -1,
        r'\b(meme|funny|joke|reaction)\b': -2,
    }

    def __init__(
        self,
        threshold: int = 2,
        backend: Optional[Any] = None
    ):
        """
        Initialize NSFW classifier.

        Args:
            threshold: Minimum score (0-3) to flag content as NSFW
            backend: Optional AI backend for ML classification.
                     If None, will attempt to auto-create one.
                     Pass False to disable ML classification entirely.
        """
        if not 0 <= threshold <= 3:
            raise ValueError(f"Threshold must be 0-3, got {threshold}")

        self.threshold = threshold
        self.has_pillow = check_dep("pillow")

        # Dependency injection: accept backend or auto-create
        if backend is False:
            # Explicitly disabled
            self.backend = None
        elif backend is not None:
            # Injected backend
            self.backend = backend
        else:
            # Auto-create (backwards compatibility)
            try:
                from .ai.backends import choose_backend
                self.backend = choose_backend()
            except Exception:  # pylint: disable=broad-except
                self.backend = None  # type: ignore[assignment]

        # Compile regex patterns for performance
        self._filename_regex = [
            (re.compile(pattern, re.IGNORECASE), weight)
            for pattern, weight in self.FILENAME_PATTERNS.items()
        ]
        self._safe_regex = [
            (re.compile(pattern, re.IGNORECASE), weight)
            for pattern, weight in self.SAFE_PATTERNS.items()
        ]

    def classify(self, path: Path, mime: str) -> Dict[str, Any]:
        """
        Classify file for NSFW content.

        Args:
            path: Path to file
            mime: MIME type of file

        Returns:
            {
                'score': int (0-3),
                'flagged': bool (score >= threshold),
                'method': str ('none'|'filename'|'metadata'|'ml'),
                'reason': str (human-readable explanation),
                'threshold': int (threshold used for classification)
            }
        """
        score = 0
        reasons: List[str] = []
        method = "none"

        # TIER 1: Filename analysis
        name_lower = path.name.lower()
        parent_lower = str(path.parent).lower()

        # Check NSFW patterns
        for regex, weight in self._filename_regex:
            if regex.search(name_lower) or regex.search(parent_lower):
                score += weight
                reasons.append(f"pattern_match:{regex.pattern[:30]}")
                method = "filename"

        # Check safe patterns (reduce score)
        for regex, weight in self._safe_regex:
            if regex.search(name_lower) or regex.search(parent_lower):
                score = max(0, score + weight)
                if weight < 0:
                    reasons.append("safe_context")

        # TIER 2: Image metadata analysis
        if self.has_pillow and mime.startswith('image/'):
            img_score, img_reason = self._analyze_image_metadata(path)
            score += img_score
            if img_reason:
                reasons.append(img_reason)
                if method == "none":
                    method = "metadata"

        # TIER 3: Content analysis (ML model)
        # Previously ML only ran on image types. We now allow video/* as well
        # — backends will extract a representative frame if needed.
        if (
            (mime.startswith('image/') or mime.startswith('video/'))
            and self.backend is not None and self.backend.available()
        ):
            try:
                ml_score, ml_reason = self.backend.predict(path)
                # If ML suggests higher confidence, prefer it
                if ml_score > score:
                    score = ml_score
                    method = "ml"
                if ml_reason:
                    reasons.append(ml_reason)
            except Exception:  # pylint: disable=broad-except
                # Backend failure should not break the pipeline; ignore
                pass

        # Clamp score to valid range
        score = min(3, max(0, score))

        # If an ML backend was configured but is not actually available we
        # surface the failure reason so callers and logs can explain why ML
        # analysis wasn't used (eg: missing runtime or unsupported model IR).
        if self.backend is not None and not self.backend.available():
            try:
                reason_text = getattr(
                    self.backend, 'unavailable_reason', lambda: None
                )()
                if reason_text:
                    reasons.append(f"ml_unavailable:{str(reason_text)[:200]}")
            except Exception:
                pass

        return {
            'score': score,
            'flagged': score >= self.threshold,
            'method': method,
            'reason': '; '.join(reasons) if reasons else 'none',
            'threshold': self.threshold
        }

    def _analyze_image_metadata(self, path: Path) -> Tuple[int, Optional[str]]:
        """
        Analyze image EXIF and properties for NSFW indicators.

        Heuristics:
        - Very high resolution (>8000x6000) → +1 (common in adult content)
        - Has camera EXIF → -1 (real photos less likely NSFW)
        - Portrait orientation → +1 (selfies, portraits)

        Args:
            path: Path to image file

        Returns:
            Tuple of (score_adjustment, reason)
        """
        try:
            from PIL import Image  # type: ignore[import-not-found]

            with Image.open(path) as img:
                width, height = img.size

                # Check for very high resolution
                if width * height > 8000 * 6000:
                    return (1, "very_high_res")

                # Check EXIF for camera metadata
                exif = img.getexif()
                if exif:
                    # Common EXIF tags for cameras:
                    # 271: Make, 272: Model, 305: Software
                    camera_tags = [271, 272, 305]
                    if any(tag in exif for tag in camera_tags):
                        return (-1, "camera_metadata")

                # Check aspect ratio
                if height > 0:
                    aspect = width / height

                    # Portrait orientation (tall and narrow)
                    if 0.5 < aspect < 0.7:
                        return (1, "portrait_orientation")

                    # Ultra-wide (common in certain adult content)
                    if aspect > 2.0:
                        return (1, "ultra_wide")

        except Exception:  # pylint: disable=broad-except
            # Silently ignore PIL errors
            pass

        return (0, None)

    def batch_classify(
        self, paths_with_mime: List[Tuple[Path, str]]
    ) -> Dict[str, Dict]:
        """
        Classify multiple files efficiently.

        Args:
            paths_with_mime: List of (Path, mime_type) tuples

        Returns:
            Dictionary mapping str(path) to classification result
        """
        results = {}
        for path, mime in paths_with_mime:
            results[str(path)] = self.classify(path, mime)
        return results

    def get_statistics(self, results: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Calculate statistics from batch classification results.

        Args:
            results: Output from batch_classify()

        Returns:
            {
                'total': int,
                'flagged': int,
                'score_distribution': {0: count, 1: count, 2: count, 3: count},
                'methods_used': {'filename': count, 'metadata': count, ...}
            }
        """
        from collections import Counter

        total = len(results)
        flagged = sum(1 for r in results.values() if r['flagged'])

        scores = [r['score'] for r in results.values()]
        score_dist = dict(Counter(scores))

        methods = [r['method'] for r in results.values()]
        methods_used = dict(Counter(methods))

        return {
            'total': total,
            'flagged': flagged,
            'flagged_percentage': round(
                100 * flagged / total, 2
            ) if total > 0 else 0,
            'score_distribution': score_dist,
            'methods_used': methods_used
        }
