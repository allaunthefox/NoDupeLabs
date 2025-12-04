#!/usr/bin/env python3
import json, sys, os
from pathlib import Path
ws = Path(__file__).resolve().parents[1]
# Ensure repo root is on sys.path
sys.path.insert(0, str(ws))
from nodupe.nsfw_classifier import NSFWClassifier
from nodupe.utils.filesystem import get_mime_safe

root = ws / 'nsfw_test_set'
paths = []
for sub in ['safe','explicit','converted']:
    d = root / sub
    if d.exists():
        for p in sorted(d.iterdir()):
            if p.is_file() and p.name != 'meta.json':
                mime = get_mime_safe(p)
                paths.append((p, mime))

print('FILES', len(paths))
clf = NSFWClassifier()
# gather environment/backend debug info
backend_info = None
try:
    import onnxruntime as ort  # type: ignore # pylint: disable=import-error
    ort_ver = getattr(ort, '__version__', None)
except Exception:
    ort_ver = None
if getattr(clf, 'backend', None) is not None:
    backend_info = {
        'backend_class': type(clf.backend).__name__,
        'backend_available': clf.backend.available(),
        'backend_unavailable_reason': getattr(clf.backend, 'unavailable_reason', lambda: None)()
    }
else:
    backend_info = {'backend_class': None}
results = clf.batch_classify(paths)
stats = clf.get_statistics(results)
# Write results to file for later review
out_path = ws / 'nsfw_test_set_classification.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump({'stats':stats, 'results':results, 'backend_info': backend_info, 'onnxruntime_version': ort_ver}, f, indent=2)
print('WROTE', out_path)
print('\nSTATS:')
print(json.dumps(stats, indent=2))
# Print a short sample of per-file results (first 40)
print('\nSAMPLE RESULTS (first 40):')
for fn,r in list(results.items())[:40]:
    print(fn, r)
print('\nDone')
