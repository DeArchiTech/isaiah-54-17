"""Ingest scripture JSON -> SQLite -> Chroma.

    python -m berean.ingest              # download, then build everything
    python -m berean.ingest /some/dir    # use JSON already on disk

The corpus is NOT committed to this repository. It is downloaded on first run
from scrollmapper/bible_databases, which publishes one JSON per translation.
Only public-domain texts are fetched; see config.TRANSLATIONS.

Budget roughly twelve minutes for the first run. Almost all of it is embedding
31k verse windows on CPU; the SQLite load takes seconds.
"""
from __future__ import annotations
import json, sys, time, urllib.request
from pathlib import Path

from .config import (VERSE_DB, CHROMA_DB, COLLECTION, BASE_TRANSLATION, WINDOW,
                     DATA_DIR, open_translations)
from .refs import canonical_book, BOOK_INDEX
from . import store


SOURCE_URL = ("https://raw.githubusercontent.com/scrollmapper/bible_databases"
              "/master/formats/json/{code}.json")


def fetch(code: str, dest_dir: Path) -> Path:
    """Download one translation if we do not already have it."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / f"{code}.json"
    if path.exists() and path.stat().st_size > 1_000_000:
        print(f"  {code}.json already present")
        return path
    url = SOURCE_URL.format(code=code)
    print(f"  downloading {code} …", end="", flush=True)
    with urllib.request.urlopen(url, timeout=180) as r:
        data = r.read()
    if len(data) < 1_000_000:
        raise SystemExit(f"\n{code}: got {len(data)} bytes, expected several MB — aborting")
    path.write_bytes(data)
    print(f" {len(data)/1e6:.1f} MB")
    return path


def load_translation(con, code: str, path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    rows, skipped = [], set()
    for book in data["books"]:
        canon = canonical_book(book["name"])
        if not canon:
            skipped.add(book["name"])          # apocrypha etc — not served
            continue
        bno = BOOK_INDEX[canon]
        for ch in book["chapters"]:
            for v in ch["verses"]:
                text = " ".join(str(v["text"]).split())
                if text:
                    rows.append((code, canon, bno, int(ch["chapter"]), int(v["verse"]), text))
    con.executemany(
        "INSERT OR REPLACE INTO verses (translation,book,book_no,chapter,verse,text)"
        " VALUES (?,?,?,?,?,?)", rows)
    con.execute("DELETE FROM verses_fts WHERE translation = ?", (code,))
    con.executemany(
        "INSERT INTO verses_fts (text,translation,book,chapter,verse) VALUES (?,?,?,?,?)",
        [(r[5], r[0], r[1], r[3], r[4]) for r in rows])
    con.commit()
    seen = {r[1] for r in rows}
    if len(seen) != 66:
        # A book name this loader cannot resolve is silent data loss, and a
        # missing book means every citation into it fails later for no visible
        # reason. Fail the ingest instead.
        missing = [b for b in BOOK_INDEX if b not in seen]
        raise SystemExit(
            f"ingest aborted for {code}: loaded {len(seen)}/66 books.\n"
            f"  missing: {missing}\n"
            f"  unresolved source names: {sorted(skipped)}\n"
            f"  -> add the alias to berean/refs.py:_EXTRA_ALIASES")
    return len(rows)


def build_index(con, translation: str = BASE_TRANSLATION, batch: int = 2000):
    """Embed sliding verse windows; the citation anchor is the centre verse."""
    import chromadb
    from chromadb.utils import embedding_functions

    CHROMA_DB.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DB))
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    col = client.create_collection(
        COLLECTION,
        embedding_function=embedding_functions.DefaultEmbeddingFunction(),
        metadata={"hnsw:space": "cosine", "translation": translation},
    )

    rows = con.execute(
        "SELECT book, book_no, chapter, verse, text FROM verses "
        "WHERE translation=? ORDER BY book_no, chapter, verse", (translation,)
    ).fetchall()
    print(f"  indexing {len(rows):,} verses from {translation}")

    docs, ids, metas = [], [], []
    total, t0 = 0, time.time()
    for i, r in enumerate(rows):
        lo, hi = max(0, i - WINDOW), min(len(rows), i + WINDOW + 1)
        window = [rows[j] for j in range(lo, hi)
                  if rows[j]["book"] == r["book"] and rows[j]["chapter"] == r["chapter"]]
        docs.append(" ".join(w["text"] for w in window))
        ids.append(f'{r["book"]}|{r["chapter"]}|{r["verse"]}')
        metas.append({"book": r["book"], "book_no": r["book_no"],
                      "chapter": r["chapter"], "verse": r["verse"],
                      "testament": "OT" if r["book_no"] < BOOK_INDEX["Matthew"] else "NT"})
        if len(docs) >= batch:
            col.add(documents=docs, ids=ids, metadatas=metas)
            total += len(docs); docs, ids, metas = [], [], []
            print(f"    {total:,}/{len(rows):,}  ({time.time()-t0:.0f}s)", flush=True)
    if docs:
        col.add(documents=docs, ids=ids, metadatas=metas)
        total += len(docs)
    print(f"  indexed {total:,} windows in {time.time()-t0:.0f}s")
    return total


def topup_index(con, books: list[str], translation: str = BASE_TRANSLATION):
    """Add windows for specific books to an existing index.

    Used after a book-name alias fix: rebuilding all 30k embeddings to add one
    book costs eleven minutes for no reason.
    """
    import chromadb
    from chromadb.utils import embedding_functions

    client = chromadb.PersistentClient(path=str(CHROMA_DB))
    col = client.get_collection(
        COLLECTION, embedding_function=embedding_functions.DefaultEmbeddingFunction())

    added = 0
    for book in books:
        rows = con.execute(
            "SELECT book, book_no, chapter, verse, text FROM verses "
            "WHERE translation=? AND book=? ORDER BY chapter, verse", (translation, book)
        ).fetchall()
        docs, ids, metas = [], [], []
        for i, r in enumerate(rows):
            lo, hi = max(0, i - WINDOW), min(len(rows), i + WINDOW + 1)
            window = [rows[j] for j in range(lo, hi) if rows[j]["chapter"] == r["chapter"]]
            docs.append(" ".join(w["text"] for w in window))
            ids.append(f'{r["book"]}|{r["chapter"]}|{r["verse"]}')
            metas.append({"book": r["book"], "book_no": r["book_no"],
                          "chapter": r["chapter"], "verse": r["verse"],
                          "testament": "OT" if r["book_no"] < BOOK_INDEX["Matthew"] else "NT"})
        if docs:
            col.upsert(documents=docs, ids=ids, metadatas=metas)
            added += len(docs)
        print(f"  topped up {book}: {len(docs)} windows")
    return added


def main(src_dir: str | None = None):
    src = Path(src_dir) if src_dir else (DATA_DIR / "sources")
    con = store.connect()
    for code in open_translations():
        print(f"* {code}")
        path = (src / f"{code}.json") if src_dir else fetch(code, src)
        if not path.exists():
            raise SystemExit(f"missing {path}")
        print(f"  {load_translation(con, code, path):,} verses")
    print("counts:", store.counts(con))
    build_index(con)
    print("\ndone — start the API with:  make api")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
