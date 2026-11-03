"""Recognize a file by its first bytes (AGENTS §17.6), after hr-ai.

A technical primitive: it only knows what a format looks like. Which formats
a use case accepts is that module's policy. Neither the file name nor the
browser's content type is trusted; the leading bytes are.
"""

from collections.abc import Callable
from dataclasses import dataclass

#: Bytes read from the start of an object to recognize it.
SNIFF_BYTES = 4096
#: PDF readers look for "%PDF-" anywhere in the first 1024 bytes.
PDF_HEADER_WINDOW = 1024


@dataclass(frozen=True)
class FileType:
    mime: str
    extensions: tuple[str, ...]
    sniff: Callable[[bytes], bool]

    def fits(self, prefix: bytes) -> bool:
        return self.sniff(prefix)


def _starts(signature: bytes) -> Callable[[bytes], bool]:
    return lambda prefix: prefix.startswith(signature)


def looks_like_text(prefix: bytes) -> bool:
    """UTF-8 without NUL bytes; a cut multi-byte character at the end of the
    sample is tolerated."""
    if b"\x00" in prefix:
        return False
    try:
        prefix.decode("utf-8")
    except UnicodeDecodeError as error:
        return error.start >= len(prefix) - 3
    return True


PNG = FileType("image/png", (".png",), _starts(b"\x89PNG\r\n\x1a\n"))
JPEG = FileType("image/jpeg", (".jpg", ".jpeg"), _starts(b"\xff\xd8\xff"))
GIF = FileType("image/gif", (".gif",), lambda p: p[:6] in (b"GIF87a", b"GIF89a"))
WEBP = FileType(
    "image/webp", (".webp",), lambda p: p[:4] == b"RIFF" and p[8:12] == b"WEBP"
)
PDF = FileType(
    "application/pdf", (".pdf",), lambda p: b"%PDF-" in p[:PDF_HEADER_WINDOW]
)
PLAIN_TEXT = FileType("text/plain", (".txt", ".log"), looks_like_text)
MARKDOWN = FileType("text/markdown", (".md", ".markdown"), looks_like_text)
CSV = FileType("text/csv", (".csv",), looks_like_text)
JSON = FileType("application/json", (".json",), looks_like_text)


def extension_of(name: str) -> str:
    dot = name.rfind(".")
    return name[dot:].lower() if dot > 0 else ""
