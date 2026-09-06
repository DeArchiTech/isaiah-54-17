# isaiah-54-17

An AI scripture-study app that **verifies every citation before you see it**.

Ask a question, get an answer with references. Tap a reference, get the actual
verse. The thing worth studying here is what happens in between: every reference
the model writes is looked up in a database, and the ones that do not resolve are
removed from the answer.

> *No weapon formed against you shall prosper.* — Isaiah 54:17

This is a teaching template. It is small enough to read in an afternoon and real
enough to be useful, and it is written for people who want to build things that
are both technically honest and worth building.

---

## The one idea

Ask a language model about scripture and it will sometimes produce a reference
that is perfectly well-formed and does not exist. Romans 8:99. A chapter of
Philippians nobody wrote. The wording around it will be fluent and confident.

The usual mitigation looks like this:

```python
system = "Only cite the passages provided. Do not invent references."
```

That reduces the rate. It does not make a guarantee, because **a prompt is a
request, not a constraint.** If the correctness of your app depends on the model
choosing to comply, your app is not correct — it is lucky.

So the guarantee is made in code instead. From [`api/berean/answer.py`](api/berean/answer.py):

```python
# THE GATE — nothing unverified reaches the client.
claimed    = find_inline(text)                       # parse every [Book C:V]
good, bad  = store.validate(con, claimed, translation)   # look each one up
if bad:
    text = _strip_invalid(text, bad)                 # unwrap the fakes
```

Run it yourself:

```
$ make test
accepted: ['Romans 8:28']
dropped : ['Romans 8:99']
```

The generalisation has nothing to do with scripture: **if correctness matters,
check the model's output against a source of truth you control.** Scripture just
happens to be a domain where a wrong answer is unambiguously wrong, which makes
it an unusually good place to learn the pattern. A hallucinated verse reference
can be proven false in one lookup. A hallucinated business insight cannot.

---

## Quickstart

```bash
git clone <this repo> && cd isaiah-54-17
make setup          # venv, deps, npm, pre-commit hook, .env from the template
$EDITOR .env        # add your Anthropic key
make ingest         # downloads 3 public-domain translations, builds the index
make api            # backend  -> :8000
make web            # frontend -> :5173   (second terminal)
```

`make ingest` takes about twelve minutes, almost all of it embedding 31,086
verse windows on CPU. It runs once. Everything else starts in seconds.

No key? `make ingest` and `make test` still work, and `/ask` degrades to
retrieval-only — it returns real ranked references and says plainly that it is
not writing a synthesis. It does not fake an answer.

---

## How it is put together

```
api/berean/
  refs.py      canonical references — parsing, abbreviations, ordering
  store.py     SQLite. verse-level. the only source of displayed text
  search.py    Chroma + FTS5, fused. finds candidates, never supplies text
  answer.py    the model call, and the citation gate
  lexicon.py   curated historical/original-language notes
  ingest.py    download -> SQLite -> index
web/src/
  mockApi.js   the seam: fake data, real contract
  api.js       the same contract, against the live backend
  App.jsx      one component, swaps between the two by changing one import
```

### Three decisions worth stealing

**1. Verses, not chunks.** The default RAG move is to split documents into
~1000-character chunks and let the vector store hold the text. That is wrong
here: a chunk boundary landing mid-verse makes every citation approximate, and
approximate is the one thing a citation cannot be. Scripture lives in SQLite at
verse granularity, keyed `(translation, book, chapter, verse)`.

Chroma answers *"what is near this meaning?"*. SQLite answers *"what are the
exact words at this address?"*. Those are different questions, and only one of
them is allowed to be approximate. **Let the structure of your domain decide
your index granularity — chunking is a default, not a law.**

**2. Build against a seam.** The UI was written first, against `mockApi.js`: a
documented contract with hand-checked fake data. Going live changed one import.
This is not ceremony. It means the interface is designed rather than accreted,
the frontend is never blocked on the backend, and there is always a version that
demos on a plane.

**3. The failure has to be honest.** When the backend is down, the app says so
and refuses to answer. When there is no lexical data for a passage, it says
"no entry yet — coverage is a hand-checked subset" rather than rendering an
empty box. An empty panel implies there is nothing to say. In an app whose whole
claim is that it does not make things up, **silence has to be labelled.**

---

## Scripture texts and licensing

Three public-domain translations are supported: **BSB**, **KJV**, **ASV**. They
are downloaded on setup and **not committed to this repository**.

ESV, NIV and NASB are copyrighted. They appear in the UI marked *"licence
required"* and the server refuses to serve them whatever the client asks for
(`_resolve()` in [`api/app.py`](api/app.py)). Making the constraint visible
seemed better than pretending it does not exist.

## What this app will not do

It retrieves; it does not pronounce. Where a reading is contested it says so and
names the alternatives, rather than settling a question that traditions have not
settled. It makes no doctrinal claims. That is a design constraint, and it is
also the only honest posture for a tool that cannot be accountable for what it
says.

---

## What is still wrong with it

An honest template should say where it is weak.

**Retrieval is the weak link, not generation.** This surprised me and it is the
most useful thing in the repo. The model's output is consistently *better* than
the retrieval feeding it. Most tutorials obsess over prompts and model choice;
the actual bottleneck was finding the right verses.

Specifically: compound queries still fail. Ask for *"persecution of David"* and
no single verse contains both words — scripture says it as narrative, Saul
*sought* David. Keyword search returns New Testament persecution with no David;
vector search returns David with no persecution; fusing them interleaves two
half-right lists. Fixing that properly needs query decomposition or a
knowledge-graph layer. It is a genuinely open problem and a good exercise.

**Also open:** lexical coverage is 10 hand-checked passages (the real fix is
ingesting a Strong's-tagged text such as STEPBible TAHOT/TAGNT, CC-BY); the
citation regex does not yet handle comma lists like `[1 Samuel 29:6, 9]`.

---

## Keeping keys out of the repository

`make setup` installs [`scripts/preflight.sh`](scripts/preflight.sh) as a
pre-commit hook. It scans **staged content**, not filenames, for credential
shapes and non-placeholder secret assignments, and refuses commits that carry
them.

It exists because of a real incident. A sibling project baked a live API key
into a Dockerfile, and it sat in that repository's history for fourteen months.
A `.gitignore` would not have caught it — the file was *supposed* to be
committed; the key just should not have been in it. And once a secret is in
history, deleting the file does nothing.

Two habits worth forming, both cheap:

- **Count before you stage.** `git status --porcelain | wc -l`. A number far
  larger than you expected means a virtualenv or a data directory is about to
  become permanent.
- **Scan content, not names.** The dangerous secret is in a file you meant to
  commit.

---

## Licence

MIT for the code. Scripture texts are not covered by it and are not distributed
here — see [LICENSE](LICENSE).
