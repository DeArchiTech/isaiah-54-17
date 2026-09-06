"""Semantic search over the verse index.

Returns candidate *references*, never text. Text always comes from the verse
store, in the reader's chosen translation.
"""
from __future__ import annotations
import functools
from .config import CHROMA_DB, COLLECTION, BASE_TRANSLATION as BASE
from .refs import Ref

@functools.lru_cache(maxsize=1)
def _collection():
    import chromadb
    from chromadb.utils import embedding_functions
    client = chromadb.PersistentClient(path=str(CHROMA_DB))
    return client.get_collection(
        COLLECTION, embedding_function=embedding_functions.DefaultEmbeddingFunction())

def search(query: str, k: int = 8, testament: str | None = None) -> list[dict]:
    where = {"testament": testament} if testament in ("OT", "NT") else None
    res = _collection().query(query_texts=[query], n_results=k, where=where,
                              include=["metadatas", "distances"])
    out = []
    for meta, dist in zip(res["metadatas"][0], res["distances"][0]):
        out.append({
            "ref": Ref(meta["book"], meta["chapter"], meta["verse"], meta["verse"]),
            "score": round(1.0 - float(dist), 4),   # cosine distance -> similarity
            "testament": meta["testament"],
        })
    return out

def hybrid(con, query: str, k: int = 8, testament: str | None = None) -> list[dict]:
    """Union of vector and keyword retrieval.

    Measured on this corpus, the two fail in opposite directions. The vector
    index lands in the right neighbourhood but off by a verse or two — asked
    about anxiety it returns Philippians 4:7 and 4:8 while missing 4:6, because
    each document is a 5-verse window and the anchor's own wording gets smeared
    across its neighbours. FTS5 has no such drift: "anxiety" matches the verse
    that contains the word. It is correspondingly blind to paraphrase.

    So: take both, rank agreement highest. A verse both methods surface is the
    strongest signal available here; after that, exact wording beats proximity,
    because a reader who asks about anxiety expects the verse that says it.
    """
    from . import store

    RRF_K = 60  # standard damping; keeps rank 1 from swamping ranks 2-10

    vec = list(search(query, k=k * 3, testament=testament))
    kw = []
    for h in store.keyword_search(con, query, BASE, limit=k * 3):
        r = Ref(h["book"], h["chapter"], h["verse"], h["verse"])
        if testament and r.testament != testament:
            continue
        kw.append({"ref": r, "score": None, "testament": r.testament})

    fused: dict[str, dict] = {}
    for source, hits in (("semantic", vec), ("keyword", kw)):
        for rank, h in enumerate(hits, start=1):
            label = h["ref"].label
            slot = fused.setdefault(label, {**h, "rank": 0.0, "_via": set()})
            slot["rank"] += 1.0 / (RRF_K + rank)
            slot["_via"].add(source)

    merged = []
    for slot in fused.values():
        via = slot.pop("_via")
        slot["via"] = "both" if len(via) == 2 else next(iter(via))
        slot["rank"] = round(slot["rank"], 5)
        merged.append(slot)

    merged.sort(key=lambda h: -h["rank"])
    return merged[:k]


def indexed_count() -> int:
    return _collection().count()
