"""isaiah-54-17 — FastAPI service.

Every response shape here matches `web/src/mockApi.js` exactly, so the UI can be
built and demonstrated with no backend at all and then switched to this one by
changing a single import. That is deliberate: it keeps the interface honest and
it means the frontend is never blocked on the model.

The endpoint that matters is /ask. Read `berean/answer.py` first — the citation
gate lives there, and it is the reason this project exists.
"""
from __future__ import annotations
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware

from berean import store, search, lexicon, answer as answer_mod
from berean.config import TRANSLATIONS, open_translations, BASE_TRANSLATION
from berean.refs import parse, Ref

con = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global con
    con = store.connect()
    yield
    con.close()

app = FastAPI(title="Cyber-Holy-Spirit", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

SAMPLE_PROMPTS = [
    "What does the Bible say about anxiety?",
    "Compare 'grace' in the OT vs NT",
    "Is there hope when plans fall apart?",
    "How do I find my purpose?",
]


def _resolve(translation: str) -> str:
    """Never serve a licensed text, whatever the client asks for."""
    t = (translation or BASE_TRANSLATION).upper()
    if t not in TRANSLATIONS or TRANSLATIONS[t]["locked"]:
        return BASE_TRANSLATION
    return t


@app.get("/health")
def health():
    return {
        "ok": True,
        "verses": store.counts(con),
        "indexed_windows": search.indexed_count(),
        "translations": open_translations(),
        "lexicon_entries": lexicon.COVERAGE,
        "model_configured": answer_mod._has_model(),
    }


@app.get("/translations")
def translations():
    return {"translations": [{"id": k, **v} for k, v in TRANSLATIONS.items()],
            "base": BASE_TRANSLATION, "samplePrompts": SAMPLE_PROMPTS}


@app.get("/passage")
def passage(ref: str = Query(..., description="e.g. 'Philippians 4:6-7'"),
            translation: str = BASE_TRANSLATION):
    r = parse(ref)
    if not r:
        raise HTTPException(400, f"unparseable reference: {ref!r}")
    requested = (translation or BASE_TRANSLATION).upper()
    served = _resolve(translation)
    verses = store.get_verses(con, r, served)
    if not verses:
        raise HTTPException(404, f"{r.label} not present in {served}")

    entry = lexicon.get(r.label)
    return {
        "ref": r.dict(),
        "refLabel": r.label,
        "translation": served,
        "requestedTranslation": requested,
        "testament": r.testament,
        "verses": verses,
        "context": entry.get("context"),
        "commentary": entry.get("commentary"),
        "lemmas": entry.get("lemmas", []),
        "hasLexicon": lexicon.has_lexicon(r.label),
        "crossRefs": [h["ref"].dict() for h in
                      answer_mod.retrieve(con, " ".join(v["text"] for v in verses),
                                          served, k=4)
                      if h["ref"].label != r.label][:3],
    }


@app.get("/search")
def semantic_search(q: str, translation: str = BASE_TRANSLATION,
                    k: int = 8, testament: str | None = None):
    served = _resolve(translation)
    hits = []
    for h in search.hybrid(con, q, k=k, testament=testament):
        r: Ref = h["ref"]
        verses = store.get_verses(con, r, served)
        if verses:
            hits.append({"ref": r.dict(), "refLabel": r.label,
                         "score": h.get("rank", h["score"]), "via": h.get("via"),
                         "testament": h["testament"], "text": verses[0]["text"]})
    return {"query": q, "translation": served, "hits": hits}


class Turn(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str


class AskRequest(BaseModel):
    q: str
    translation: str = BASE_TRANSLATION
    # Prior turns, oldest first, EXCLUDING the current question. Retrieval runs
    # against the last user turn plus `q` so a fragment like "what about the
    # Psalms?" still finds its subject; the model receives the real history.
    history: list[Turn] = Field(default_factory=list, max_length=40)


@app.get("/ask")
def ask(q: str, translation: str = BASE_TRANSLATION):
    """Single-shot. Kept for scripts and curl; the UI uses POST."""
    served = _resolve(translation)
    out = answer_mod.answer(con, q, served)
    out["translation"] = served
    return out


@app.post("/ask")
def ask_conversational(req: AskRequest):
    served = _resolve(req.translation)
    history = [t.model_dump() for t in req.history]
    if history and history[0]["role"] != "user":
        history = history[1:]              # Claude requires a user turn first
    out = answer_mod.answer(con, req.q, served, history=history)
    out["translation"] = served
    # User turns, not message count — "turn 5" for a third question is
    # arithmetic leaking into the UI.
    out["turns"] = sum(1 for t in history if t["role"] == "user") + 1
    return out


@app.get("/exists")
def exists(ref: str, translation: str = BASE_TRANSLATION):
    r = parse(ref)
    return {"ref": ref, "valid": bool(r) and store.exists(con, r, _resolve(translation))}
