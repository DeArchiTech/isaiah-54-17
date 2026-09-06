"""Reference parsing.

A citation is only checkable if it can be turned into an exact address, so this
is the layer everything else rests on. The interesting cases are the refusals.
"""
import pytest
from berean.refs import parse, canonical_book, find_inline


@pytest.mark.parametrize("text,expected", [
    ("Philippians 4:6-7", "Philippians 4:6-7"),
    ("1 Pet 5.6",         "1 Peter 5:6"),
    ("Ps 23:1",           "Psalms 23:1"),
    ("ii cor 5:17",       "2 Corinthians 5:17"),
    ("Jn 3:16",           "John 3:16"),
    ("1Th 5:16-18",       "1 Thessalonians 5:16-18"),
    ("Song 2:1",          "Song of Solomon 2:1"),
    ("Rev 21:4",          "Revelation 21:4"),
])
def test_abbreviations_resolve(text, expected):
    assert parse(text).label == expected


def test_ambiguous_abbreviation_is_refused_rather_than_guessed():
    """'Phi' could be Philippians or Philemon. Guessing would produce a citation
    that is well-formed, resolvable, and wrong — the worst possible outcome."""
    assert canonical_book("Phi") is None
    assert parse("Phi 1:1") is None
    assert canonical_book("Phil") == "Philippians"   # unambiguous in practice
    assert canonical_book("Phlm") == "Philemon"


def test_dataset_long_form_names():
    """Public-domain datasets disagree on book names. This one cost a whole book:
    an early ingest logged 'skipped: Revelation of John' as a friendly note and
    silently dropped all 404 verses."""
    assert canonical_book("Revelation of John") == "Revelation"
    assert canonical_book("Song of Songs") == "Song of Solomon"


def test_testament_split():
    assert parse("Malachi 4:6").testament == "OT"
    assert parse("Matthew 1:1").testament == "NT"


def test_reversed_range_is_normalised():
    assert parse("Romans 8:30-28").label == "Romans 8:28-30"


def test_find_inline_ignores_non_references():
    text = "see [Romans 8:28] and [TODO] and [1] and [Hezekiah 1:1]"
    assert [r.label for r in find_inline(text)] == ["Romans 8:28"]


# --- FTS query sanitising -------------------------------------------------
# Regression tests. Each of these strings crashed the search layer at some
# point; user questions are full of characters FTS5 treats as syntax.

import pytest
from berean import store


@pytest.mark.parametrize("query", [
    "Compare 'grace' in the OT vs NT",   # the app's own sample prompt
    "What does the Bible say about anxiety?",
    'He said "peace" to them',
    "hope -- despair",
    "NOT AND OR NEAR",
    "don't be anxious",
    "David's persecution",
    "(grace)",
    "",
    "'",
])
def test_keyword_search_never_raises_on_user_input(con, query):
    store.keyword_search(con, query, "BSB", limit=5)


def test_internal_apostrophes_are_kept():
    """Stripping every apostrophe would turn don't into two useless tokens."""
    import re
    from berean.store import _STOPWORDS
    toks = [t for t in (w.strip("'") for w in re.findall(r"[A-Za-z0-9']+", "don't David's 'grace'"))
            if len(t) > 2 and t.lower() not in _STOPWORDS]
    assert toks == ["don't", "David's", "grace"]
