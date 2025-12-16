"""NoDupeLabs Video Plugins - Video Processing Backends

This module provides video processing backends with 5-tier graceful degradation
for frame extraction, metadata analysis, and perceptual hashing.
"""

from typing import List, Optional, Dict, Any
import logging
import subprocess
import hashlib
import numpy as np
from abc import ABC, abstractmethod
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)


class VideoBackend(ABC):
    """Abstract base class for video backends"""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is available"""

    @abstractmethod
    def extract_frames(self, video_path: str, max_frames: int = 10) -> List[np.ndarray]:
        """Extract key frames from video"""

    @abstractmethod
    def get_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """Get video metadata (duration, resolution, fps, etc.)"""

    @abstractmethod
    def compute_perceptual_hash(self, frame: np.ndarray) -> str:
        """Compute perceptual hash for video frame"""

    @abstractmethod
    def get_priority(self) -> int:
        """Get backend priority (lower number = higher priority)"""


class FFmpegSubprocessBackend(VideoBackend):
    """Tier 5: FFmpeg CLI backend (always available if ffmpeg binary exists)"""

    def __init__(self):
        self.priority = 5
        self._available = self._check_ffmpeg_available()

    def _check_ffmpeg_available(self) -> bool:
        """Check if ffmpeg binary is available in PATH"""
        try:
            result = subprocess.run(['ffmpeg', '-version'],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("FFmpeg binary not found in PATH")
            return False

    def is_available(self) -> bool:
        """Check if FFmpeg backend is available"""
        return self._available

    def extract_frames(self, video_path: str, max_frames: int = 10) -> List[np.ndarray]:
        """Extract frames using FFmpeg CLI"""
        if not self.is_available():
            logger.error("FFmpeg not available")
            return []

        try:
            # Create temporary directory for frames
            temp_dir = Path("temp_frames")
            temp_dir.mkdir(exist_ok=True)

            # FFmpeg command to extract frames
            output_pattern = str(temp_dir / "frame_%04d.png")
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vf', f'fps=1/{max_frames},scale=256:144',
                '-frames:v', str(max_frames),
                output_pattern
            ]

            result = subprocess.run(cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    check=True)

            # Load extracted frames
            frames = []
            for i in range(max_frames):
                frame_path = temp_dir / f"frame_{i:04d}.png"
                if frame_path.exists():
                    try:
                        import cv2
                        frame = cv2.imread(str(frame_path))
                        if frame is not None:
                            frames.append(frame)
                    except ImportError:
                        # Fallback: use PIL if OpenCV not available
                        try:
                            from PIL import Image
                            frame = np.array(Image.open(frame_path))
                            frames.append(frame)
                        except ImportError:
                            logger.warning("Neither OpenCV nor PIL available for frame loading")

            # Clean up
            for f in temp_dir.glob("frame_*.png"):
                f.unlink()
            temp_dir.rmdir()

            return frames

        except Exception as e:
            logger.error(f"Error extracting frames with FFmpeg: {e}")
            return []

    def get_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """Get video metadata using FFmpeg"""
        if not self.is_available():
            return {}

        try:
            cmd = [
                'ffmpeg',
                '-i', video_path
            ]

            result = subprocess.run(cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    check=False)

            metadata = {}
            stderr = result.stderr.decode('utf-8', errors='ignore')

            # Parse basic metadata from FFmpeg output
            for line in stderr.split('\n'):
                if 'Duration:' in line:
                    # Parse duration
                    parts = line.split(',')
                    duration_part = parts[0].split('Duration:')[1].strip()
                    h, m, s = duration_part.split(':')
                    metadata['duration_seconds'] = float(h) * 3600 + float(m) * 60 + float(s)
                elif 'Video:' in line:
                    # Parse video resolution and fps
                    if 'x' in line:
                        res_part = line.split('Video:')[1].split(',')[0].strip()
                        width, height = res_part.split('x')[:2]
                        metadata['width'] = int(width)
                        metadata['height'] = int(height)

            return metadata

        except Exception as e:
            logger.error(f"Error getting video metadata: {e}")
            return {}

    def compute_perceptual_hash(self, frame: np.ndarray) -> str:
        """Compute simple perceptual hash (average hash)"""
        try:
            # Convert to grayscale if needed
            if len(frame.shape) == 3:
                gray = np.mean(frame, axis=2).astype(np.uint8)
            else:
                gray = frame

            # Resize to small fixed size
            resized = cv2.resize(gray, (8, 8)) if 'cv2' in locals() else gray[:8, :8]

            # Compute average and create hash
            avg = np.mean(resized)
            bits = ''.join(['1' if pixel > avg else '0' for pixel in resized.flatten()])
            return hashlib.md5(bits.encode()).hexdigest()

        except Exception as e:
            logger.error(f"Error computing perceptual hash: {e}")
            return ""

    def get_priority(self) -> int:
        """Get backend priority"""
        return self.priority


class OpenCVBackend(VideoBackend):
    """Tier 4: OpenCV backend"""

    def __init__(self):
        self.priority = 4
        self._available = self._check_opencv_available()

    def _check_opencv_available(self) -> bool:
        """Check if OpenCV is available"""
        try:
            return True
        except ImportError:
            logger.warning("OpenCV not available")
            return False

    def is_available(self) -> bool:
        """Check if OpenCV backend is available"""
        return self._available

    def extract_frames(self, video_path: str, max_frames: int = 10) -> List[np.ndarray]:
        """Extract frames using OpenCV"""
        if not self.is_available():
            logger.error("OpenCV not available")
            return []

        try:
            import cv2

            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f"Could not open video: {video_path}")
                return []

            frames = []
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_step = max(1, total_frames // max_frames)

            for i in range(0, total_frames, frame_step):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                if ret:
                    frames.append(frame)
                if len(frames) >= max_frames:
                    break

            cap.release()
            return frames

        except Exception as e:
            logger.error(f"Error extracting frames with OpenCV: {e}")
            return []

    def get_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """Get video metadata using OpenCV"""
        if not self.is_available():
            return {}

        try:
            import cv2

            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return {}

            metadata = {
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'fps': cap.get(cv2.CAP_PROP_FPS),
                'duration_seconds': cap.get(cv2.CAP_PROP_FRAME_COUNT) / max(1, cap.get(cv2.CAP_PROP_FPS)),
                'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            }

            cap.release()
            return metadata

        except Exception as e:
            logger.error(f"Error getting video metadata: {e}")
            return {}

    def compute_perceptual_hash(self, frame: np.ndarray) -> str:
        """Compute perceptual hash using OpenCV"""
        try:
            import cv2

            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame

            # Resize and compute hash
            resized = cv2.resize(gray, (8, 8))
            avg = np.mean(resized)
            bits = ''.join(['1' if pixel > avg else '0' for pixel in resized.flatten()])
            return hashlib.md5(bits.encode()).hexdigest()

        except Exception as e:
            logger.error(f"Error computing perceptual hash: {e}")
            return ""

    def get_priority(self) -> int:
        """Get backend priority"""
        return self.priority


class VideoBackendManager:
    """Manage multiple video backends with automatic fallback"""

    def __init__(self):
        self.backends = []
        self._initialize_backends()

    def _initialize_backends(self):
        """Initialize all available backends in priority order"""
        # Initialize backends in priority order (lower number = higher priority)
        backends_to_try = [
            ('opencv', OpenCVBackend),
            ('ffmpeg', FFmpegSubprocessBackend)
        ]

        for name, backend_class in backends_to_try:
            try:
                backend = backend_class()
                if backend.is_available():
                    self.backends.append(backend)
                    logger.info(f"Initialized {name} backend (priority {backend.get_priority()})")
            except Exception as e:
                logger.warning(f"Failed to initialize {name} backend: {e}")

        # Sort backends by priority
        self.backends.sort(key=lambda x: x.get_priority())

        if not self.backends:
            logger.warning("No video backends available")

    def extract_frames(self, video_path: str, max_frames: int = 10) -> List[np.ndarray]:
        """Extract frames using the best available backend"""
        for backend in self.backends:
            try:
                frames = backend.extract_frames(video_path, max_frames)
                if frames:
                    logger.info(
                        f"Extracted {len(frames)} frames using {backend.__class__.__name__}")
                    return frames
            except Exception as e:
                logger.warning(f"Backend {backend.__class__.__name__} failed: {e}")
                continue

        logger.error("All video backends failed to extract frames")
        return []

    def get_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """Get video metadata using the best available backend"""
        for backend in self.backends:
            try:
                metadata = backend.get_video_metadata(video_path)
                if metadata:
                    logger.info(f"Retrieved metadata using {backend.__class__.__name__}")
                    return metadata
            except Exception as e:
                logger.warning(f"Backend {backend.__class__.__name__} failed: {e}")
                continue

        logger.error("All video backends failed to get metadata")
        return {}

    def compute_perceptual_hash(self, frame: np.ndarray) -> str:
        """Compute perceptual hash using the best available backend"""
        for backend in self.backends:
            try:
                phash = backend.compute_perceptual_hash(frame)
                if phash:
                    return phash
            except Exception as e:
                logger.warning(f"Backend {backend.__class__.__name__} failed: {e}")
                continue

        logger.error("All video backends failed to compute perceptual hash")
        return ""


# Module-level backend manager
VIDEO_MANAGER: Optional[VideoBackendManager] = None


def get_video_backend_manager() -> VideoBackendManager:
    """Get the global video backend manager"""
    global VIDEO_MANAGER
    if VIDEO_MANAGER is None:
        VIDEO_MANAGER = VideoBackendManager()
    return VIDEO_MANAGER


# Initialize manager on import
get_video_backend_manager()

__all__ = [
    'VideoBackend', 'FFmpegSubprocessBackend', 'OpenCVBackend',
    'VideoBackendManager', 'get_video_backend_manager'
]
