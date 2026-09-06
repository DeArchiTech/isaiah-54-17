"""A tiny corpus, built in a temp file.

The real index is ~290 MB and takes twelve minutes to build. Tests that need a
full corpus to run are tests nobody runs, so these build a handful of real
verses instead — enough to prove the gate, fast enough to run on every save.
"""
import pytest
from berean import store

VERSES = [
    # (translation, book, chapter, verse, text)
    ("BSB", "Philippians", 4, 6, "Be anxious for nothing, but in everything, by prayer and petition, with thanksgiving, present your requests to God."),
    ("BSB", "Philippians", 4, 7, "And the peace of God, which surpasses all understanding, will guard your hearts and your minds in Christ Jesus."),
    ("BSB", "Romans", 8, 28, "And we know that God works all things together for the good of those who love Him, who are called according to His purpose."),
    ("BSB", "Genesis", 1, 1, "In the beginning God created the heavens and the earth."),
    ("KJV", "Romans", 8, 28, "And we know that all things work together for good to them that love God, to them who are the called according to his purpose."),
]


@pytest.fixture
def con(tmp_path):
    from berean.refs import BOOK_INDEX
    c = store.connect(tmp_path / "test.sqlite3")
    c.executemany(
        "INSERT INTO verses (translation,book,book_no,chapter,verse,text) VALUES (?,?,?,?,?,?)",
        [(t, b, BOOK_INDEX[b], ch, v, txt) for t, b, ch, v, txt in VERSES])
    c.commit()
    yield c
    c.close()
