/**
 * api.js — the live backend, drop-in replacement for mockApi.js.
 *
 * Same three functions, same shapes. App.jsx switches between mock and live by
 * changing one import; nothing else in the UI knows the difference. That was
 * the point of building the mock behind a seam.
 *
 *   askBerean(query, translation)  -> Promise<Answer>
 *   getPassage(ref, translation)   -> Promise<Passage | null>
 *   TRANSLATIONS / SAMPLE_PROMPTS  -> loaded from the server at boot
 *
 * Failure policy: when the backend is unreachable this does NOT silently fall
 * back to mock text. A Bible tool that quietly starts making things up is the
 * exact failure mode the whole design exists to prevent — so it surfaces the
 * outage instead.
 */

const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const refKey = (r) =>
  `${r.book} ${r.chapter}:${r.verseStart}${r.verseEnd !== r.verseStart ? `-${r.verseEnd}` : ""}`;

class BackendDown extends Error {}

async function post(path, body) {
  let res;
  try {
    res = await fetch(new URL(path, BASE), {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new BackendDown(`Cannot reach the Berean backend at ${BASE}.`);
  }
  if (!res.ok) throw new Error(`${path} -> ${res.status} ${await res.text()}`);
  return res.json();
}

async function get(path, params = {}) {
  const url = new URL(path, BASE);
  Object.entries(params).forEach(([k, v]) => v != null && url.searchParams.set(k, v));
  let res;
  try {
    res = await fetch(url, { headers: { Accept: "application/json" } });
  } catch {
    throw new BackendDown(`Cannot reach the Berean backend at ${BASE}.`);
  }
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`${path} -> ${res.status} ${await res.text()}`);
  return res.json();
}

/* ---- bootstrap: translations and sample prompts come from the server ---- */

export let TRANSLATIONS = [
  { id: "BSB", name: "Berean Standard Bible", note: "Public domain", locked: false },
];
export let SAMPLE_PROMPTS = [];

let _ready = null;
export function ready() {
  if (!_ready) {
    _ready = get("/translations")
      .then((d) => {
        TRANSLATIONS = d.translations;
        SAMPLE_PROMPTS = d.samplePrompts;
        return d;
      })
      .catch((e) => {
        _ready = null;              // allow a retry on the next call
        throw e;
      });
  }
  return _ready;
}

export async function health() {
  return get("/health");
}

/* ---- the three the UI actually calls ---- */

let idSeq = 0;

/**
 * @param history prior turns, oldest first, EXCLUDING the current question.
 *   Retrieval runs against the last user turn plus `query`, so a fragment like
 *   "which psalms did he write during that?" still finds its subject.
 */
export async function askBerean(query, translation, history = []) {
  try {
    const d = await post("/ask", { q: query, translation, history });
    return {
      id: `msg_${Date.now()}_${idSeq++}`,
      text: d.text,
      citations: d.citations,
      sources: d.sources,
      grounded: d.grounded,
      retrievalOnly: Boolean(d.retrieval_only),
      dropped: d.dropped || [],
      turns: d.turns,
    };
  } catch (e) {
    return {
      id: `err_${Date.now()}_${idSeq++}`,
      text:
        e instanceof BackendDown
          ? `${e.message}\n\nStart it with:\n\n    make api\n\nI will not answer from memory while it is down — inventing scripture is the one failure this app is built to prevent.`
          : `The backend returned an error:\n\n${e.message}`,
      citations: [],
      sources: [],
      grounded: false,
      dropped: [],
    };
  }
}

export async function getPassage(r, translation) {
  try {
    return await get("/passage", { ref: refKey(r), translation });
  } catch {
    return null;
  }
}

/* The server is the authority on what exists; the UI optimistically renders
 * pills and lets /passage 404 rather than round-tripping every citation. */
export const hasPassage = () => true;
