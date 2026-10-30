"""Find a user's chats by title or message text (use case C09, QD-31).

PostgreSQL compares `chat_app.search_key` forms (lower case, no accents) with
trigram indexes; this module builds the pattern and the snippet shown for a
match. The snippet is cut from the original text around the first place the
query occurs once accents are ignored.
"""

import unicodedata

MIN_QUERY = 2
MAX_QUERY = 200
#: Characters of context on each side of a match in a snippet.
SNIPPET_CONTEXT = 60


def like_pattern(query: str) -> str:
    """`%query%` with LIKE wildcards in the query taken literally."""
    escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _fold(char: str) -> str:
    """One character as search_key sees it; always one character long, so
    positions in the folded text match the original."""
    if char in "đĐ":
        return "d"
    base = "".join(
        c for c in unicodedata.normalize("NFD", char) if not unicodedata.combining(c)
    )
    return (base or char)[0].lower()


def snippet(text: str, query: str) -> str:
    """The words around the first match of `query` in `text`."""
    flat = " ".join(text.split())
    folded = "".join(_fold(c) for c in flat)
    needle = "".join(_fold(c) for c in " ".join(query.split()))
    start = folded.find(needle)
    if start < 0:
        start = 0
    end = start + len(needle)
    left, right = max(0, start - SNIPPET_CONTEXT), min(len(flat), end + SNIPPET_CONTEXT)
    return f"{'…' if left else ''}{flat[left:right]}{'…' if right < len(flat) else ''}"
