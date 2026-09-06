"""Berean AI configuration.

Forked from ai_tutor_be. Two deliberate departures from the parent project:

1. Scripture is NOT stored as chunked PDF text. It lives verse-level in SQLite,
   because a citation must resolve to an exact canonical address. Chroma is used
   only to *find* candidate verses; it is never the source of the text shown.

2. The semantic index is built over ONE translation (the base). Translations are
   a rendering concern: you search once, then display the hit in whichever text
   the reader has selected. Indexing all three would triple the cost to return
   the same references.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader — no dependency, and the precedence is the point.

    A real environment variable always wins over the file. That means the file
    is a convenience for local development and never silently overrides a key
    injected by CI, a container, or a secrets manager. It also means you can
    keep credentials out of the project directory entirely if you prefer:

        ANTHROPIC_API_KEY=$(pass show anthropic) make api

    Anything already set is left alone; quotes and `export` are tolerated.
    """
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.removeprefix("export ").partition("=")
        key, val = key.strip(), val.strip().strip("\"'")
        if key and key not in os.environ:
            os.environ[key] = val


_load_dotenv(REPO / ".env")

DATA_DIR = Path(os.getenv("BEREAN_DATA_DIR", ROOT / "data"))

VERSE_DB = DATA_DIR / "scripture.sqlite3"
CHROMA_DB = DATA_DIR / "chroma"
COLLECTION = "verses"

BASE_TRANSLATION = "BSB"

TRANSLATIONS = {
    "BSB": {"name": "Berean Standard Bible", "note": "Public domain", "locked": False},
    "KJV": {"name": "King James Version", "note": "Public domain", "locked": False},
    "ASV": {"name": "American Standard Version", "note": "Public domain", "locked": False},
    # Present so the constraint is visible in the UI, never served.
    "ESV": {"name": "English Standard Version", "note": "Licence required", "locked": True},
    "NIV": {"name": "New International Version", "note": "Licence required", "locked": True},
    "NASB": {"name": "New American Standard", "note": "Licence required", "locked": True},
}

def open_translations():
    return [t for t, m in TRANSLATIONS.items() if not m["locked"]]

# Window size for the semantic index: a verse plus its neighbours reads better
# to an embedding model than a bare verse, but the citation stays the anchor.
WINDOW = 2
