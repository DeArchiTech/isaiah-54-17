"""Verse store — SQLite, verse-level, the single source of truth for text.

Why not Chroma: an embedding index answers "what is near this meaning". A
citation needs "what are the exact words at this address". Those are different
questions and only one of them is allowed to be approximate.
"""
from __future__ import annotations
import sqlite3, re
from pathlib import Path
from .config import VERSE_DB
from .refs import Ref, BOOK_INDEX, parse

_FTS_OPERATORS = {"AND", "OR", "NOT", "NEAR"}

# Stopwords are poison for an OR query: "persecution of David" matched every
# verse containing "of", and "What does the Bible say about anxiety?" surfaced
# Job 22:13 ("What does God know?"). FTS5's porter tokenizer does not remove
# them, so this does. Deliberately short — it drops function words only, never
# anything a reader might be searching for.
_STOPWORDS = {
    "the", "and", "for", "are", "but", "not", "you", "all", "any", "can", "her",
    "was", "one", "our", "out", "his", "has", "had", "him", "she", "its", "who",
    "did", "does", "doe", "what", "when", "where", "which", "with", "from",
    "this", "that", "these", "those", "there", "their", "them", "then", "than",
    "into", "about", "would", "could", "should", "have", "been", "were", "will",
    "say", "says", "said", "tell", "does", "how", "why", "does", "bible",
    "scripture", "verse", "verses", "passage", "mean", "means", "regarding",
    "concerning", "does", "did", "such",
    # Query verbs — they describe what the user wants done, not what they are
    # looking for, so matching them just retrieves whichever verse happens to
    # use the word. "Compare 'grace' in the OT vs NT" was returning
    # 2 Corinthians 10:12 ("compare ourselves with").
    "compare", "contrast", "difference", "differences", "between", "explain",
    "describe", "summarise", "summarize", "list", "give", "show", "find",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS verses (
    translation TEXT NOT NULL,
    book        TEXT NOT NULL,
    book_no     INTEGER NOT NULL,
    chapter     INTEGER NOT NULL,
    verse       INTEGER NOT NULL,
    text        TEXT NOT NULL,
    PRIMARY KEY (translation, book, chapter, verse)
);
CREATE INDEX IF NOT EXISTS idx_addr  ON verses (book_no, chapter, verse);
CREATE INDEX IF NOT EXISTS idx_trans ON verses (translation);
CREATE VIRTUAL TABLE IF NOT EXISTS verses_fts USING fts5(
    text, translation UNINDEXED, book UNINDEXED,
    chapter UNINDEXED, verse UNINDEXED, tokenize='porter'
);
"""

def connect(path: Path | str = VERSE_DB) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path), check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con

def counts(con) -> dict:
    rows = con.execute(
        "SELECT translation, COUNT(*) n FROM verses GROUP BY translation"
    ).fetchall()
    return {r["translation"]: r["n"] for r in rows}

def get_verses(con, ref: Ref, translation: str) -> list[dict]:
    """Exact lookup. Returns [] if the address does not exist in this text."""
    rows = con.execute(
        """SELECT verse, text FROM verses
           WHERE translation=? AND book=? AND chapter=? AND verse BETWEEN ? AND ?
           ORDER BY verse""",
        (translation, ref.book, ref.chapter, ref.verseStart, ref.verseEnd),
    ).fetchall()
    return [{"n": r["verse"], "text": r["text"]} for r in rows]

def exists(con, ref: Ref, translation: str) -> bool:
    return bool(get_verses(con, ref, translation))

def validate(con, refs: list[Ref], translation: str) -> tuple[list[Ref], list[Ref]]:
    """Split refs into (real, invented). Nothing unverified reaches the client."""
    good, bad = [], []
    for r in refs:
        (good if exists(con, r, translation) else bad).append(r)
    return good, bad

def context_window(con, ref: Ref, translation: str, before=2, after=2) -> list[dict]:
    rows = con.execute(
        """SELECT verse, text FROM verses
           WHERE translation=? AND book=? AND chapter=? AND verse BETWEEN ? AND ?
           ORDER BY verse""",
        (translation, ref.book, ref.chapter,
         max(1, ref.verseStart - before), ref.verseEnd + after),
    ).fetchall()
    return [{"n": r["verse"], "text": r["text"]} for r in rows]

def keyword_search(con, query: str, translation: str, limit=20) -> list[dict]:
    """Lexical fallback / complement to the vector index."""
    # FTS5 treats ? " * - : ^ ( ) AND OR NOT NEAR as syntax. User questions are
    # full of them ("What does the Bible say about anxiety?"), so reduce the
    # query to bare word tokens before it ever reaches MATCH.
    # Keep an internal apostrophe (don't, David's) but never an edge one: a
    # bare leading quote opens a string literal to FTS5 and the whole MATCH
    # fails. The app's own sample prompt — Compare 'grace' in the OT vs NT —
    # crashed on exactly this.
    tokens = [t for t in (w.strip("'") for w in re.findall(r"[A-Za-z0-9']+", query or ""))
              if len(t) > 2 and t.upper() not in _FTS_OPERATORS]
    words = [w for w in tokens if w.lower() not in _STOPWORDS]
    if not words:
        words = tokens          # a query made entirely of stopwords: use it as-is
    if not words:
        return []
    # Quote every term. FTS5 treats ' " * - : ^ ( ) as syntax in a BARE term —
    # an apostrophe anywhere in `don't` opens a string literal and the whole
    # MATCH fails with a parse error. A double-quoted term is taken literally,
    # so the only thing left to escape is an embedded double quote (doubled).
    q = " OR ".join('"{}"'.format(w.replace('"', '""')) for w in words)
    rows = con.execute(
        """SELECT book, chapter, verse, text, rank FROM verses_fts
           WHERE verses_fts MATCH ? AND translation = ?
           ORDER BY rank LIMIT ?""",
        (q, translation, limit),
    ).fetchall()
    return [dict(r) for r in rows]
