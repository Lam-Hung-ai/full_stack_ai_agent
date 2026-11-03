#!/usr/bin/env python3
"""Verify provenance and section integrity of a packaged source."""
from pathlib import Path
import json, hashlib

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'references/source'
manifest = json.loads((SRC / 'MANIFEST.json').read_text(encoding='utf-8'))
full = (SRC / 'the-design-of-everyday-things-original.md').read_bytes()
expected = manifest['sha256']
actual = hashlib.sha256(full).hexdigest()
assert actual == expected, f'Source SHA mismatch: {expected} != {actual}'
lines = full.decode('utf-8').splitlines(keepends=True)
assert len(lines) == manifest['line_count'], 'Source line count mismatch'
covered = []
for part in manifest['parts']:
    p = SRC / part['file']
    actual_part = p.read_text(encoding='utf-8')
    expected_part = ''.join(lines[part['start_line'] - 1 : part['end_line']])
    assert actual_part == expected_part, f'Source section mismatch: {p.name}'
    covered.extend(range(part['start_line'], part['end_line'] + 1))
assert covered == list(range(1, len(lines) + 1)), 'Source has missing/overlapping line numbers'
for i in range(1, 8):
    assert len(list((ROOT / 'references/chapters').glob(f'{i:02}-*.md'))) == 1, f'Guide chapter {i} missing/duplicate'
for f in (ROOT / 'references').rglob('*.md'):
    if '/source/' in f.as_posix(): continue
    text = f.read_text(encoding='utf-8')
    assert 'TODO:' not in text, f'Unfinished placeholder {f}'
print(f'PASS: {len(lines)} lines, {len(manifest["parts"])} source sections, 7 chapter guides; SHA256 {actual}')
