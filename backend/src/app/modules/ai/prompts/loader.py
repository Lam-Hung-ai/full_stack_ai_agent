from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


@lru_cache
def load_prompt(name: str) -> str:
    """The text of `prompts/<name>.md`, read once per process."""
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8").strip()
