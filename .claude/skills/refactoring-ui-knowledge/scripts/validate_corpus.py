#!/usr/bin/env python3
"""Validate intact canonical Markdown source and chapter coverage in this skill."""
from pathlib import Path
from hashlib import sha256
import re, sys
ROOT = Path(__file__).resolve().parent.parent
REFS = ROOT / 'references'
ORIGINAL = REFS / 'SOURCE-markdown-nguyen-ban.md'
EXPECTED_HASH = "eb267e1cf7dc9460aeea8302d8014a922d2afc3c7216c7e27794d9083d74407b"
FILES = ['01-bat-dau-thiet-ke.md', '02-hierarchy.md', '03-layout-spacing.md', '04-typography-nen-tang.md', '05-typography-nang-cao.md', '06-mau-sac.md', '07-chieu-sau.md', '08-hinh-anh.md', '09-hoan-thien.md', '10-luyen-tap-nang-trinh.md']
SECTIONS = ['Vấn đề', 'Mục tiêu', 'Lý thuyết', 'Khi nào áp dụng', 'Cách làm', 'Nên / Không nên', 'Ví dụ đúng/sai', 'Lỗi thường gặp', 'Ngoại lệ', 'Checklist', 'Tóm tắt']

def check():
    raw=ORIGINAL.read_bytes()
    assert sha256(raw).hexdigest()==EXPECTED_HASH, 'Source Markdown altered from verified original'
    t=raw.decode('utf-8')
    lessons=list(re.finditer(r'^## Bài\s+(\d+)', t, re.M))
    assert [int(x.group(1)) for x in lessons]==list(range(1,53)), 'Expected 52 lessons'
    for section in SECTIONS:
        assert len(re.findall(r'^### '+re.escape(section)+r'$',t,re.M))==52, 'Missing '+section
    chunks=[]
    for name in FILES:
        fp=REFS/name
        assert fp.is_file(), 'Missing chapter '+name
        chunks.append(fp.read_text(encoding='utf-8').strip())
    # Check per-chapter exact inclusion; separate headers cannot be accidentally edited.
    for ch in chunks:
        assert ch in t, 'A chapter differs from canonical Markdown'
    workflow=(REFS/'11-quy-trinh-va-checklist-nguyen-ban.md').read_text(encoding='utf-8').strip()
    assert workflow in t
    print('PASS: original SHA256, 52 lessons, 11 fields per lesson, 10 verbatim chapters, full workflows')

if __name__=='__main__':
    try: check()
    except Exception as exc:
        print('FAIL:', exc, file=sys.stderr); sys.exit(1)
