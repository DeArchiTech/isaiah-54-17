import { useState, useRef, useEffect, useCallback } from "react";
import {
  BookOpen, Send, ChevronDown, Sparkles, X, Lock, Check,
  Scroll, Languages, Link2, Quote, Loader2, AlertTriangle, User,
} from "lucide-react";
import {
  TRANSLATIONS, SAMPLE_PROMPTS, askBerean, getPassage, refKey, hasPassage,
  ready, health,
} from "./api";

/* ============================ streaming hook ============================ */

function useTypewriter(speed = 9) {
  const [state, setState] = useState({ id: null, full: "", shown: "" });
  const timer = useRef(null);

  const stop = useCallback(() => {
    if (timer.current) clearInterval(timer.current);
    timer.current = null;
  }, []);

  const start = useCallback((id, full, onDone) => {
    stop();
    setState({ id, full, shown: "" });
    let i = 0;
    timer.current = setInterval(() => {
      i += Math.max(1, Math.round(full.length / 900));
      if (i >= full.length) {
        stop();
        setState({ id, full, shown: full });
        onDone?.();
      } else {
        setState({ id, full, shown: full.slice(0, i) });
      }
    }, speed);
  }, [speed, stop]);

  const skip = useCallback((onDone) => {
    stop();
    setState((s) => ({ ...s, shown: s.full }));
    onDone?.();
  }, [stop]);

  useEffect(() => stop, [stop]);
  return { ...state, start, skip, streaming: Boolean(timer.current) };
}

/* ============================ small pieces ============================ */

function CitationPill({ label, onClick, disabled }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={disabled ? "Passage not in this demo corpus" : `Open ${label} in the inspector`}
      className={
        "mx-0.5 inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 align-baseline text-[0.82em] font-medium transition " +
        (disabled
          ? "cursor-default border-slate-700 bg-slate-800/60 text-slate-500"
          : "cursor-pointer border-amber-500/30 bg-amber-500/10 text-amber-300 hover:border-amber-400/60 hover:bg-amber-500/20 hover:text-amber-200")
      }
    >
      <BookOpen size={11} className="shrink-0" />
      {label}
    </button>
  );
}

/** Renders assistant text, turning [Book C:V-V] into interactive pills. */
function RichText({ text, onCite }) {
  const parts = [];
  const re = /\[([1-3]?\s?[A-Za-z]+)\s(\d+):(\d+)(?:-(\d+))?\]/g;
  let last = 0, m, k = 0;

  while ((m = re.exec(text)) !== null) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    const r = {
      book: m[1].trim(),
      chapter: Number(m[2]),
      verseStart: Number(m[3]),
      verseEnd: Number(m[4] ?? m[3]),
    };
    const label = refKey(r);
    parts.push(
      <CitationPill key={`c${k++}`} label={label} disabled={!hasPassage(r)} onClick={() => onCite(r)} />
    );
    last = m.index + m[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));

  return (
    <div className="space-y-3 text-[15px] leading-relaxed text-slate-200">
      {splitParas(parts).map((para, i) => (
        <p key={i}>{para}</p>
      ))}
    </div>
  );
}

/* split the mixed string/element array on blank lines, keeping elements intact */
function splitParas(parts) {
  const paras = [[]];
  for (const p of parts) {
    if (typeof p !== "string") { paras[paras.length - 1].push(p); continue; }
    const chunks = p.split("\n\n");
    chunks.forEach((c, i) => {
      if (i > 0) paras.push([]);
      if (c) paras[paras.length - 1].push(c);
    });
  }
  return paras.filter((p) => p.length);
}

function TranslationPicker({ value, onChange }) {
  const [open, setOpen] = useState(false);
  const boxRef = useRef(null);

  useEffect(() => {
    const h = (e) => { if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, []);

  return (
    <div className="relative" ref={boxRef}>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
        className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800/70 px-3 py-1.5 text-sm font-medium text-slate-200 transition hover:border-slate-600 hover:bg-slate-800"
      >
        {value}
        <ChevronDown size={14} className={"text-slate-400 transition " + (open ? "rotate-180" : "")} />
      </button>

      {open && (
        <div
          role="listbox"
          className="absolute right-0 z-30 mt-2 w-72 overflow-hidden rounded-xl border border-slate-700 bg-slate-900 shadow-2xl shadow-black/60"
        >
          {TRANSLATIONS.map((t) => (
            <button
              key={t.id}
              role="option"
              aria-selected={t.id === value}
              disabled={t.locked}
              onClick={() => { if (!t.locked) { onChange(t.id); setOpen(false); } }}
              className={
                "flex w-full items-center gap-3 px-3 py-2.5 text-left transition " +
                (t.locked ? "cursor-not-allowed opacity-45" : "hover:bg-slate-800")
              }
            >
              <span className="w-12 shrink-0 font-mono text-xs font-semibold text-slate-300">{t.id}</span>
              <span className="min-w-0 flex-1">
                <span className="block truncate text-sm text-slate-200">{t.name}</span>
                <span className="block text-[11px] text-slate-500">{t.note}</span>
              </span>
              {t.locked ? <Lock size={13} className="shrink-0 text-slate-600" />
                : t.id === value ? <Check size={14} className="shrink-0 text-amber-400" /> : null}
            </button>
          ))}
          <div className="border-t border-slate-800 bg-slate-950/60 px-3 py-2 text-[11px] leading-snug text-slate-500">
            Only public-domain and freely-licensed texts are shipped. Locked entries need a publisher licence.
          </div>
        </div>
      )}
    </div>
  );
}

/* ============================ inspector ============================ */

function Inspector({ passage, loading, onClose, onCite }) {
  if (!passage && !loading) {
    return (
      <div className="flex h-full flex-col items-center justify-center px-10 text-center">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5">
          <Scroll size={26} className="text-slate-600" />
        </div>
        <p className="mt-5 text-sm font-medium text-slate-400">Scripture Inspector</p>
        <p className="mt-2 max-w-[16rem] text-[13px] leading-relaxed text-slate-600">
          Select any reference in the conversation to open the passage, its historical setting, and the
          original-language roots behind the translation.
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 size={20} className="animate-spin text-slate-600" />
      </div>
    );
  }

  const downgraded = passage.requestedTranslation !== passage.translation;

  return (
    <div className="flex h-full flex-col">
      <div className="flex shrink-0 items-start justify-between gap-3 border-b border-slate-800 px-6 py-4">
        <div className="min-w-0">
          <h2 className="font-serif text-xl text-amber-100">{passage.refLabel}</h2>
          <p className="mt-0.5 text-[11px] font-medium uppercase tracking-wider text-slate-500">
            {passage.translation}
            {downgraded && (
              <span className="ml-2 normal-case tracking-normal text-amber-600/80">
                — {passage.requestedTranslation} not licensed, showing BSB
              </span>
            )}
          </p>
        </div>
        <button
          onClick={onClose}
          aria-label="Close inspector"
          className="rounded-lg p-1.5 text-slate-500 transition hover:bg-slate-800 hover:text-slate-300"
        >
          <X size={16} />
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-6 py-5">
        {/* passage */}
        <div className="space-y-3 border-l-2 border-amber-500/40 pl-4">
          {passage.verses.map((v) => (
            <p key={v.n} className="font-serif text-[16.5px] leading-[1.75] text-slate-100">
              <sup className="mr-1.5 font-sans text-[10px] font-semibold text-amber-500/70">{v.n}</sup>
              {v.text}
            </p>
          ))}
        </div>

        {/* historical context — only when we actually have some */}
        {passage.context && (
          <section className="mt-6 rounded-xl border border-slate-800 bg-slate-900/60 p-4">
            <h3 className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              <Scroll size={13} className="text-slate-500" /> Historical Context
            </h3>
            <p className="mt-2.5 text-[13.5px] leading-relaxed text-slate-300">{passage.context}</p>
          </section>
        )}

        {/* Original language. Coverage is a curated subset, so say so plainly —
            an empty panel would imply the text has no roots worth noting. */}
        <section className="mt-4 rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <h3 className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            <Languages size={13} className="text-slate-500" /> Original Language
          </h3>
          {passage.lemmas.length === 0 && (
            <p className="mt-2.5 text-[13px] leading-relaxed text-slate-500">
              No lexical entry for this passage yet — coverage is a hand-checked subset,
              not the whole Bible. Nothing is being withheld and nothing is inferred.
            </p>
          )}
          <div className="mt-3 space-y-3">
            {passage.lemmas.map((l) => (
              <div key={l.strongs} className="rounded-lg border border-slate-800 bg-slate-950/50 p-3">
                <div className="flex flex-wrap items-baseline gap-x-2.5 gap-y-1">
                  <span className="font-serif text-lg text-amber-200">{l.word}</span>
                  <span className="text-[13px] italic text-slate-400">{l.translit}</span>
                  <span className="ml-auto rounded border border-slate-700 px-1.5 py-0.5 font-mono text-[10px] text-slate-500">
                    {l.strongs}
                  </span>
                </div>
                <p className="mt-1 text-[13px] font-medium text-slate-200">{l.gloss}</p>
                <p className="mt-1.5 text-[12.5px] leading-relaxed text-slate-400">{l.note}</p>
              </div>
            ))}
          </div>
          {passage.lemmas.length > 0 && (
            <p className="mt-3 text-[11px] text-slate-600">Lexical data: Strong's Concordance (public domain).</p>
          )}
        </section>

        {/* commentary */}
        {passage.commentary && (
          <section className="mt-4 rounded-xl border border-slate-800 bg-slate-900/60 p-4">
            <h3 className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              <Quote size={13} className="text-slate-500" /> Commentary
            </h3>
            <p className="mt-2.5 font-serif text-[14px] italic leading-relaxed text-slate-300">
              “{passage.commentary.text}”
            </p>
            <p className="mt-2 text-[11px] text-slate-500">— {passage.commentary.source}</p>
          </section>
        )}

        {/* cross refs */}
        {passage.crossRefs?.length > 0 && (
          <section className="mt-4 pb-2">
            <h3 className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              <Link2 size={13} className="text-slate-500" /> Cross References
            </h3>
            <div className="mt-2.5 flex flex-wrap gap-1.5">
              {passage.crossRefs.map((r) => (
                <CitationPill key={refKey(r)} label={refKey(r)} disabled={!hasPassage(r)} onClick={() => onCite(r)} />
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}

/* ============================ app ============================ */

const WELCOME = {
  id: "welcome",
  role: "assistant",
  text:
    "I answer from the biblical text and cite every claim, so you can check the work rather than take my word for it. Every reference is verified against the verse store before you see it.\n\nAsk anything, or start with one of these.",
  citations: [],
  sources: [],
  grounded: true,
  done: true,
};

export default function App() {
  const [messages, setMessages] = useState([WELCOME]);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const [translation, setTranslation] = useState("BSB");
  const [passage, setPassage] = useState(null);
  const [loadingPassage, setLoadingPassage] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const [boot, setBoot] = useState({ state: "loading", info: null, error: null });

  const typer = useTypewriter();
  const feedRef = useRef(null);
  const inputRef = useRef(null);

  // TRANSLATIONS / SAMPLE_PROMPTS are live ESM bindings that ready() reassigns;
  // this effect exists to trigger the render that reads the new values.
  useEffect(() => {
    let alive = true;
    ready()
      .then(() => health())
      .then((info) => alive && setBoot({ state: "ready", info, error: null }))
      .catch((e) => alive && setBoot({ state: "down", info: null, error: e.message }));
    return () => { alive = false; };
  }, []);

  useEffect(() => {
    feedRef.current?.scrollTo({ top: feedRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, typer.shown, thinking]);

  const openCitation = useCallback(async (r) => {
    setLoadingPassage(true);
    setMobileOpen(true);
    const p = await getPassage(r, translation);
    setPassage(p);
    setLoadingPassage(false);
  }, [translation]);

  // keep the open passage in sync when the translation changes
  useEffect(() => {
    if (!passage) return;
    let cancelled = false;
    getPassage(passage.ref, translation).then((p) => { if (!cancelled && p) setPassage(p); });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [translation]);

  const send = useCallback(async (raw) => {
    const q = (raw ?? input).trim();
    if (!q || thinking) return;
    setInput("");
    setMessages((m) => [...m, { id: `u_${Date.now()}`, role: "user", text: q }]);
    setThinking(true);

    // Prior turns for the model. The welcome card and any backend-error notice
    // are UI furniture, not conversation — sending them would have the model
    // answering its own boilerplate.
    const history = messages
      .filter((m) => m.id !== "welcome" && m.grounded !== false)
      .map((m) => ({ role: m.role, content: m.text }));

    const ans = await askBerean(q, translation, history);
    setThinking(false);
    setMessages((m) => [...m, { ...ans, role: "assistant", done: false }]);
    typer.start(ans.id, ans.text, () =>
      setMessages((m) => m.map((x) => (x.id === ans.id ? { ...x, done: true } : x)))
    );
  }, [input, thinking, translation, typer, messages]);

  const finishStream = () =>
    typer.skip(() => setMessages((m) => m.map((x) => (x.id === typer.id ? { ...x, done: true } : x))));

  return (
    <div className="flex h-screen flex-col bg-slate-900 text-slate-100 antialiased">
      {/* ---------- header ---------- */}
      <header className="flex shrink-0 items-center justify-between gap-4 border-b border-slate-800 bg-slate-900/95 px-5 py-3 backdrop-blur">
        <div className="flex min-w-0 shrink items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 shadow-lg shadow-amber-900/30">
            <BookOpen size={18} className="text-slate-900" strokeWidth={2.5} />
          </div>
          <div className="min-w-0">
            <h1 className="truncate text-[15px] font-semibold tracking-tight">Cyber-Holy-Spirit</h1>
            <p className="truncate text-[11px] text-slate-500">Scripture study, cited</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span
            title={boot.error || (boot.info ? `${Object.values(boot.info.verses).reduce((a, b) => a + b, 0).toLocaleString()} verses · ${boot.info.indexed_windows.toLocaleString()} indexed` : "")}
            className={
              "rounded-md border px-2 py-1 text-[10px] font-medium uppercase tracking-wider whitespace-nowrap " +
              (boot.state === "ready"
                ? "border-emerald-800/60 bg-emerald-950/40 text-emerald-500"
                : boot.state === "down"
                ? "border-red-900/60 bg-red-950/40 text-red-400"
                : "border-slate-800 bg-slate-800/40 text-slate-500")
            }
          >
            {boot.state === "ready"
              ? `Live · ${boot.info.verses.BSB.toLocaleString()}`
              : boot.state === "down"
              ? "Backend offline"
              : "Connecting…"}
          </span>
          <TranslationPicker value={translation} onChange={setTranslation} />
        </div>
      </header>

      {/* ---------- body ---------- */}
      <div className="flex min-h-0 flex-1">
        {/* LEFT: chat */}
        <main className="flex min-w-0 flex-1 flex-col md:border-r md:border-slate-800">
          <div ref={feedRef} className="min-h-0 flex-1 overflow-y-auto px-5 py-6">
            <div className="mx-auto max-w-2xl space-y-6">
              {messages.map((msg) =>
                msg.role === "user" ? (
                  <div key={msg.id} className="flex justify-end">
                    <div className="flex max-w-[85%] items-start gap-2.5">
                      <div className="rounded-2xl rounded-tr-sm bg-slate-800 px-4 py-2.5 text-[15px] leading-relaxed text-slate-100">
                        {msg.text}
                      </div>
                      <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-slate-800 text-slate-400">
                        <User size={14} />
                      </div>
                    </div>
                  </div>
                ) : (
                  <div key={msg.id} className="flex items-start gap-3">
                    <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-amber-400 to-amber-600">
                      <Sparkles size={13} className="text-slate-900" strokeWidth={2.5} />
                    </div>
                    <div className="min-w-0 flex-1">
                      {msg.grounded === false && (
                        <div className="mb-2.5 flex items-start gap-2 rounded-lg border border-amber-700/40 bg-amber-950/30 px-3 py-2 text-[12.5px] text-amber-200/90">
                          <AlertTriangle size={13} className="mt-0.5 shrink-0" />
                          {msg.text.startsWith("Cannot reach")
                            ? "Backend unreachable — not answering from memory."
                            : "No grounded sources for this query — answering honestly instead of guessing."}
                        </div>
                      )}

                      <div aria-live="polite">
                        <RichText
                          text={msg.done ? msg.text : typer.id === msg.id ? typer.shown : msg.text}
                          onCite={openCitation}
                        />
                      </div>

                      {!msg.done && typer.id === msg.id && (
                        <>
                          <span className="ml-0.5 inline-block h-4 w-[2px] translate-y-0.5 animate-pulse bg-amber-400" />
                          <button
                            onClick={finishStream}
                            className="mt-3 block rounded-md border border-slate-700 px-2 py-1 text-[11px] text-slate-400 transition hover:border-slate-600 hover:text-slate-200"
                          >
                            Skip animation
                          </button>
                        </>
                      )}

                      {msg.done && msg.dropped?.length > 0 && (
                        <p className="mt-3 text-[11px] text-amber-600/80">
                          Citation gate removed {msg.dropped.length} reference
                          {msg.dropped.length > 1 ? "s" : ""} that did not resolve:{" "}
                          {msg.dropped.join(", ")}
                        </p>
                      )}

                      {msg.done && msg.sources?.length > 0 && (
                        <p className="mt-3 text-[11px] text-slate-600">
                          Sources: {msg.sources.join(" · ")}
                          {msg.turns > 1 && ` · turn ${msg.turns}, prior context carried`}
                        </p>
                      )}

                      {msg.id === "welcome" && (
                        <div className="mt-4 flex flex-wrap gap-2">
                          {SAMPLE_PROMPTS.map((p) => (
                            <button
                              key={p}
                              onClick={() => send(p)}
                              className="rounded-full border border-slate-700 bg-slate-800/40 px-3.5 py-1.5 text-[13px] text-slate-300 transition hover:border-amber-500/40 hover:bg-slate-800 hover:text-amber-100"
                            >
                              {p}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )
              )}

              {thinking && (
                <div className="flex items-center gap-3">
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-amber-400 to-amber-600">
                    <Sparkles size={13} className="text-slate-900" strokeWidth={2.5} />
                  </div>
                  <div className="flex gap-1">
                    {[0, 150, 300].map((d) => (
                      <span
                        key={d}
                        className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-600"
                        style={{ animationDelay: `${d}ms` }}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* composer */}
          <div className="shrink-0 border-t border-slate-800 bg-slate-900 px-5 py-4">
            <div className="mx-auto max-w-2xl">
              <div className="flex items-end gap-2 rounded-2xl border border-slate-700 bg-slate-800/50 px-3 py-2 transition focus-within:border-amber-500/50">
                <textarea
                  ref={inputRef}
                  rows={1}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
                  }}
                  placeholder="Ask about a topic, a passage, or a word…"
                  aria-label="Ask a question"
                  className="max-h-32 min-h-[28px] flex-1 resize-none bg-transparent py-1 text-[15px] text-slate-100 placeholder:text-slate-500 focus:outline-none"
                />
                <button
                  onClick={() => send()}
                  disabled={!input.trim() || thinking}
                  aria-label="Send"
                  className="mb-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-amber-500 text-slate-900 transition hover:bg-amber-400 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-500"
                >
                  <Send size={15} />
                </button>
              </div>
              <p className="mt-2 text-center text-[11px] text-slate-600">
                Answers are generated only from retrieved passages. Unverifiable citations are stripped.
              </p>
            </div>
          </div>
        </main>

        {/* RIGHT: inspector (desktop) */}
        <aside className="hidden w-[27rem] shrink-0 bg-slate-950/40 md:block lg:w-[30rem]">
          <Inspector
            passage={passage}
            loading={loadingPassage}
            onClose={() => setPassage(null)}
            onCite={openCitation}
          />
        </aside>
      </div>

      {/* RIGHT: inspector (mobile bottom sheet) */}
      {mobileOpen && (passage || loadingPassage) && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div className="absolute inset-0 bg-black/60" onClick={() => setMobileOpen(false)} />
          <div className="absolute inset-x-0 bottom-0 h-[82vh] rounded-t-2xl border-t border-slate-700 bg-slate-950">
            <Inspector
              passage={passage}
              loading={loadingPassage}
              onClose={() => setMobileOpen(false)}
              onCite={openCitation}
            />
          </div>
        </div>
      )}
    </div>
  );
}
