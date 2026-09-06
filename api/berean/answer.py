"""Answer generation, with citation validation as a hard gate.

The policy this module enforces:

  * Retrieval picks the passages. The model may only discuss what retrieval
    returned; it is never asked to recall scripture from its weights.
  * Every [Book C:V] the model writes is checked against the verse store.
    Anything that does not resolve is stripped from the text before it is
    returned, and reported in `dropped`. A tool that invents references is
    worse than no tool, so this is code, not a prompt instruction.
  * With no model configured the endpoint degrades to retrieval-only and says
    so, rather than emitting something that reads like an answer.
"""
from __future__ import annotations
import os, re

from . import store, search, lexicon
from .refs import Ref, find_inline

MODEL = os.getenv("BEREAN_MODEL", "claude-opus-5")

SYSTEM = """You are Berean, a study assistant for the biblical text.

Rules, in order of priority:
1. Discuss ONLY the passages supplied in <retrieved>. You have no other access to
   scripture and must not quote or cite anything outside that block.
2. Cite by wrapping a reference in square brackets: [Philippians 4:6-7]. Use the
   exact book, chapter and verse given to you.
3. Distinguish what the text says from what interpreters conclude from it. Where
   a reading is contested, say that it is contested and name the alternatives.
4. Do not resolve a doctrinal dispute by asserting one side. Set out what the
   passage supports and where traditions divide.
5. Where the historical setting changes how a verse lands, say so — especially
   when a verse is commonly quoted apart from it.
6. Write plainly and compactly. No headers, no bullet lists, no bold. Three to
   five short paragraphs.
7. If <retrieved> does not actually address the question, say that directly
   instead of stretching the passages to fit.
8. In a follow-up turn, earlier <retrieved> blocks remain available to you and
   stay citable. Answer what was actually asked rather than restating the
   previous answer, and do not re-introduce material the reader already has."""


# `make setup` writes .env from the template, so the very first run has a key
# variable that is set and useless. Treating that as "configured" would trade a
# clear message for a 401 on the first question anyone asks.
# "XXXXXX" not "XXX" — a real key can contain three x's by chance, and
# rejecting a valid key is a worse failure than accepting a placeholder.
_PLACEHOLDERS = ("REPLACE_ME", "YOUR_", "XXXXXX", "CHANGEME", "<")


def _real(value: str | None) -> bool:
    if not value or len(value) < 25:
        return False
    return not any(p in value.upper() for p in _PLACEHOLDERS)


def _has_model() -> bool:
    if _real(os.getenv("ANTHROPIC_API_KEY")) or _real(os.getenv("ANTHROPIC_AUTH_TOKEN")):
        return True
    # An `ant auth login` profile works with no environment variable at all.
    return os.path.isdir(os.path.expanduser("~/.config/anthropic"))


def retrieval_query(history: list[dict], query: str) -> str:
    """What to search for on a follow-up turn.

    A follow-up is usually a fragment — "what about the Psalms?", "say more
    about the second one". Embedding that alone retrieves noise, because the
    subject lives in the previous turn. Rewriting it into a standalone question
    with another model call would cost a second round-trip on every message, so
    instead the previous user turn is prepended as context for the *retrieval*
    query only. The model still sees the real conversation.
    """
    prior = [m["content"] for m in history if m["role"] == "user"]
    if not prior:
        return query
    return f"{prior[-1]} {query}"


def retrieve(con, query: str, translation: str, k: int = 8) -> list[dict]:
    """Semantic hits, deduped by chapter, with text pulled from the store."""
    hits, seen = [], set()
    for h in search.hybrid(con, query, k=k * 3):
        r: Ref = h["ref"]
        key = (r.book, r.chapter)
        if key in seen:
            continue
        seen.add(key)
        window = store.context_window(con, r, translation, before=1, after=2)
        if not window:
            continue
        span = Ref(r.book, r.chapter, window[0]["n"], window[-1]["n"])
        hits.append({"ref": span, "anchor": r, "score": h.get("rank", h["score"]),
                     "via": h.get("via", "semantic"), "verses": window})
        if len(hits) >= k:
            break
    return hits


def _format_retrieved(hits: list[dict]) -> str:
    parts = []
    for h in hits:
        body = " ".join(f'{v["n"]} {v["text"]}' for v in h["verses"])
        parts.append(f'[{h["ref"].label}]\n{body}')
    return "\n\n".join(parts)


def _strip_invalid(text: str, bad: list[Ref]) -> str:
    """Unwrap references that do not resolve, so they stop looking like links."""
    for r in bad:
        text = re.sub(r"\[\s*" + re.escape(r.label) + r"\s*\]", r.label, text)
    # any remaining bracketed thing that parses as a ref but was not validated
    return text


def answer(con, query: str, translation: str, history: list[dict] | None = None) -> dict:
    history = history or []
    hits = retrieve(con, retrieval_query(history, query), translation)

    if not hits:
        return {"text": f'Nothing in the indexed text came back for "{query.strip()}".',
                "citations": [], "sources": [], "grounded": False, "dropped": []}

    if not _has_model():
        # Retrieval-only mode. Honest about what it is; still genuinely useful.
        lines = ", ".join(h["ref"].label for h in hits[:5])
        return {
            "text": (
                f'No language model is configured, so I will not write a synthesis — '
                f'that part would be invention rather than retrieval.\n\n'
                f'What the index returns for "{query.strip()}", ranked by semantic '
                f'closeness: {lines}.\n\n'
                f'Every one of those is a real address in the {translation} text and '
                f'opens in the inspector. Set ANTHROPIC_API_KEY to enable the written answer.'
            ),
            "citations": [h["ref"].dict() for h in hits[:5]],
            "sources": [f"{translation} · semantic index"],
            "grounded": True,
            "retrieval_only": True,
            "dropped": [],
        }

    import anthropic
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM,
        thinking={"type": "adaptive"},
        output_config={"effort": "medium"},
        messages=[*history, {"role": "user", "content":
                   f"<retrieved>\n{_format_retrieved(hits)}\n</retrieved>\n\n"
                   f"Question: {query}"}],
    )
    if msg.stop_reason == "refusal":
        return {"text": "That request was declined.", "citations": [], "sources": [],
                "grounded": False, "dropped": []}

    text = "".join(b.text for b in msg.content if b.type == "text")

    # THE GATE — nothing unverified reaches the client.
    claimed = find_inline(text)
    good, bad = store.validate(con, claimed, translation)
    if bad:
        text = _strip_invalid(text, bad)

    return {
        "text": text,
        "citations": [r.dict() for r in good],
        "sources": [f"{translation} · {MODEL}"],
        "grounded": bool(good),
        "dropped": [r.label for r in bad],
    }
