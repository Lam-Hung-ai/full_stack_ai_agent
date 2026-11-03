#!/usr/bin/env python3
"""Search the user-provided Don Norman source by original markdown line number.

This is lexical retrieval, not semantic QA. It deliberately does not mutate the source.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'references/source/the-design-of-everyday-things-original.md'
MANIFEST = ROOT / 'references/source/MANIFEST.json'


def main() -> int:
    parser = argparse.ArgumentParser(description='Find exact text in source with global line ranges')
    parser.add_argument('--query', required=True, help='Search text or regex')
    parser.add_argument('--chapter', type=int, choices=range(1, 8), metavar='1..7', help='Restrict to chapter number')
    parser.add_argument('--regex', action='store_true', help='Treat query as regular expression')
    parser.add_argument('--context', type=int, default=1, help='Context lines before and after a match')
    parser.add_argument('--max', type=int, default=10, help='Maximum number of matches to show')
    parser.add_argument('--trim', type=int, default=350, help='Max characters per printed source line; 0=unlimited')
    args = parser.parse_args()
    if args.context < 0 or args.max < 1 or args.trim < 0:
        parser.error('--context and --trim must be >=0 and --max must be >=1')
    parts = json.loads(MANIFEST.read_text(encoding='utf-8'))['parts']
    if args.chapter:
        part = next(p for p in parts if p['file'] == f'chapter-{args.chapter:02}.md')
        a, b = part['start_line'], part['end_line']
    else:
        a, b = 1, None
    lines = SOURCE.read_text(encoding='utf-8').splitlines()
    if b is None:
        b = len(lines)
    try:
        rgx = re.compile(args.query, re.IGNORECASE) if args.regex else None
    except re.error as e:
        parser.error(f'Invalid regex: {e}')
    hits = []
    for idx in range(a - 1, b):
        line = lines[idx]
        ok = bool(rgx.search(line)) if rgx else args.query.casefold() in line.casefold()
        if ok:
            hits.append(idx)
    print(f'Query: {args.query!r}; scope: L{a}-L{b}; total matches: {len(hits)}; shown: {min(args.max, len(hits))}')
    for idx in hits[:args.max]:
        print(f'\n=== HIT L{idx + 1} ===')
        lo, hi = max(a - 1, idx - args.context), min(b, idx + args.context + 1)
        for k in range(lo, hi):
            line = lines[k]
            line = line if not args.trim or len(line) <= args.trim else line[:args.trim] + ' ...[trimmed; read source for full text]'
            print(f'L{k + 1}: {line}')
    return 0 if hits else 1

if __name__ == '__main__':
    raise SystemExit(main())
