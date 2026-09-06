/**
 * mockApi.js — THE SEAM.
 *
 * Every piece of data the UI renders comes through this file. Nothing in App.jsx
 * knows where scripture or answers come from. To go live, reimplement the three
 * exported functions against the FastAPI backend and delete the tables below;
 * the component contract does not change.
 *
 *   askBerean(query, translation)  -> Promise<Answer>
 *   getPassage(ref, translation)   -> Promise<Passage | null>
 *   TRANSLATIONS                   -> Translation[]
 *
 * DATA CONTRACT
 *   Ref     { book, chapter, verseStart, verseEnd }
 *   Answer  { id, text, citations: Ref[], sources: string[], grounded: boolean }
 *   Passage { ref, refLabel, translation, verses: [{n, text}],
 *             context: string, commentary?: {source, text},
 *             lemmas: [{ word, translit, strongs, gloss, note }],
 *             crossRefs: Ref[] }
 *
 * TEXT LICENSING: only public-domain / freely-licensed translations are shipped.
 * KJV and WEB are public domain. BSB is free for any use. ESV / NIV / NASB are
 * copyrighted and are deliberately NOT included — they appear in the dropdown as
 * locked to make the constraint visible rather than silently ignored.
 */

export const TRANSLATIONS = [
  { id: "BSB", name: "Berean Standard Bible", note: "Free for any use", locked: false },
  { id: "WEB", name: "World English Bible", note: "Public domain", locked: false },
  { id: "KJV", name: "King James Version", note: "Public domain", locked: false },
  { id: "ESV", name: "English Standard Version", note: "Licence required", locked: true },
  { id: "NIV", name: "New International Version", note: "Licence required", locked: true },
  { id: "NASB", name: "New American Standard", note: "Licence required", locked: true },
];

export const SAMPLE_PROMPTS = [
  "What does the Bible say about anxiety?",
  "Compare 'grace' in the OT vs NT",
  "Is there hope when plans fall apart?",
  "How do I find my purpose?",
];

const ref = (book, chapter, verseStart, verseEnd = verseStart) => ({
  book, chapter, verseStart, verseEnd,
});

export const refKey = (r) => `${r.book} ${r.chapter}:${r.verseStart}${r.verseEnd !== r.verseStart ? `-${r.verseEnd}` : ""}`;

/* ------------------------------------------------------------------ */
/* PASSAGES — keyed by canonical ref, text per translation             */
/* ------------------------------------------------------------------ */

const PASSAGES = {
  "Philippians 4:6-7": {
    ref: ref("Philippians", 4, 6, 7),
    verses: {
      BSB: [
        { n: 6, text: "Be anxious for nothing, but in everything, by prayer and petition, with thanksgiving, present your requests to God." },
        { n: 7, text: "And the peace of God, which surpasses all understanding, will guard your hearts and your minds in Christ Jesus." },
      ],
      WEB: [
        { n: 6, text: "In nothing be anxious, but in everything, by prayer and petition with thanksgiving, let your requests be made known to God." },
        { n: 7, text: "And the peace of God, which surpasses all understanding, will guard your hearts and your thoughts in Christ Jesus." },
      ],
      KJV: [
        { n: 6, text: "Be careful for nothing; but in every thing by prayer and supplication with thanksgiving let your requests be made known unto God." },
        { n: 7, text: "And the peace of God, which passeth all understanding, shall keep your hearts and minds through Christ Jesus." },
      ],
    },
    context:
      "Written from Roman custody around AD 62. Paul is chained to a rotating guard and does not know whether his trial ends in release or execution — the letter's repeated command to rejoice is issued from that position, not from safety. Philippi was a Roman colony of retired soldiers, so the military vocabulary in verse 7 would have landed on its intended audience.",
    commentary: {
      source: "Matthew Henry, Commentary on the Whole Bible (1710, public domain)",
      text: "The peace of God is that peace which God gives, and it passeth all understanding: it is what cannot be fully comprehended, and it keeps the heart as with a garrison.",
    },
    lemmas: [
      { word: "μεριμνάω", translit: "merimnaō", strongs: "G3309", gloss: "to be anxious", note: "Likely from merizō, 'to divide'. The picture is a mind pulled into parts — not fear, but fragmentation." },
      { word: "εἰρήνη", translit: "eirēnē", strongs: "G1515", gloss: "peace", note: "Carries the freight of Hebrew shalom — wholeness and repair, not merely the absence of conflict." },
      { word: "φρουρέω", translit: "phroureō", strongs: "G5432", gloss: "will guard", note: "A garrison term: to post a military sentry. The peace is not a feeling here; it is a soldier at the gate." },
    ],
    crossRefs: [ref("1 Peter", 5, 6, 7), ref("Matthew", 6, 25, 27), ref("Isaiah", 26, 3)],
  },

  "1 Peter 5:6-7": {
    ref: ref("1 Peter", 5, 6, 7),
    verses: {
      BSB: [
        { n: 6, text: "Humble yourselves, therefore, under God's mighty hand, that He may exalt you at the proper time." },
        { n: 7, text: "Cast all your anxiety on Him, because He cares for you." },
      ],
      WEB: [
        { n: 6, text: "Humble yourselves therefore under the mighty hand of God, that he may exalt you in due time," },
        { n: 7, text: "casting all your worries on him, because he cares for you." },
      ],
      KJV: [
        { n: 6, text: "Humble yourselves therefore under the mighty hand of God, that he may exalt you in due time:" },
        { n: 7, text: "Casting all your care upon him; for he careth for you." },
      ],
    },
    context:
      "Addressed to scattered believers in Asia Minor facing social hostility rather than state persecution — shunning, slander, lost work. Verses 6 and 7 are one sentence in Greek: the casting is how the humbling is done, not a separate instruction.",
    lemmas: [
      { word: "ἐπιρίπτω", translit: "epiriptō", strongs: "G1977", gloss: "cast upon", note: "Used in Luke 19:35 of throwing cloaks onto the colt — a decisive heave off yourself onto something else." },
      { word: "μέριμνα", translit: "merimna", strongs: "G3308", gloss: "anxiety, care", note: "The noun behind Paul's verb in Philippians 4:6. Same root, same divided mind." },
      { word: "μέλει", translit: "melei", strongs: "G3199", gloss: "it matters to him", note: "Impersonal: literally 'it is a care to Him concerning you.' Your concern becomes His concern." },
    ],
    crossRefs: [ref("Philippians", 4, 6, 7), ref("Psalms", 55, 22)],
  },

  "Matthew 6:25-27": {
    ref: ref("Matthew", 6, 25, 27),
    verses: {
      BSB: [
        { n: 25, text: "Therefore I tell you, do not worry about your life, what you will eat or drink; or about your body, what you will wear. Is not life more than food, and the body more than clothes?" },
        { n: 26, text: "Look at the birds of the air: They do not sow or reap or gather into barns—and yet your heavenly Father feeds them. Are you not much more valuable than they?" },
        { n: 27, text: "Who of you by worrying can add a single hour to his life?" },
      ],
      WEB: [
        { n: 25, text: "Therefore I tell you, don't be anxious for your life: what you will eat, or what you will drink; nor yet for your body, what you will wear. Isn't life more than food, and the body more than clothing?" },
        { n: 26, text: "See the birds of the sky, that they don't sow, neither do they reap, nor gather into barns. Your heavenly Father feeds them. Aren't you of much more value than they?" },
        { n: 27, text: "Which of you by being anxious, can add one moment to his lifespan?" },
      ],
      KJV: [
        { n: 25, text: "Therefore I say unto you, Take no thought for your life, what ye shall eat, or what ye shall drink; nor yet for your body, what ye shall put on. Is not the life more than meat, and the body than raiment?" },
        { n: 26, text: "Behold the fowls of the air: for they sow not, neither do they reap, nor gather into barns; yet your heavenly Father feedeth them. Are ye not much better than they?" },
        { n: 27, text: "Which of you by taking thought can add one cubit unto his stature?" },
      ],
    },
    context:
      "From the Sermon on the Mount, spoken to a subsistence-agrarian crowd for whom a failed harvest was a genuine survival threat. The argument is not that the worry is irrational — it is that it is ineffective, and that the hearer has misjudged their own worth.",
    lemmas: [
      { word: "μεριμνάω", translit: "merimnaō", strongs: "G3309", gloss: "to worry", note: "The same verb Paul commands against in Philippians 4:6 — a deliberate echo." },
      { word: "ἡλικία", translit: "hēlikia", strongs: "G2244", gloss: "stature / lifespan", note: "Ambiguous in Greek: height or age. KJV chose 'cubit unto his stature'; modern versions read it as lifespan." },
    ],
    crossRefs: [ref("Philippians", 4, 6, 7), ref("Luke", 12, 22, 26)],
  },

  "Jeremiah 29:11": {
    ref: ref("Jeremiah", 29, 11),
    verses: {
      BSB: [{ n: 11, text: "For I know the plans I have for you, declares the LORD, plans to prosper you and not to harm you, plans to give you a future and a hope." }],
      WEB: [{ n: 11, text: "For I know the thoughts that I think toward you, says Yahweh, thoughts of peace, and not of evil, to give you hope and a future." }],
      KJV: [{ n: 11, text: "For I know the thoughts that I think toward you, saith the LORD, thoughts of peace, and not of evil, to give you an expected end." }],
    },
    context:
      "The most quoted and most decontextualised verse in the Bible. It is a letter to deportees in Babylon, and the surrounding verses set the terms: the promise is collective, not individual, and it arrives after seventy years (v.10). Verse 5 tells the same audience to build houses and plant gardens — i.e. this is a promise for a generation that will mostly die in exile.",
    commentary: {
      source: "Jamieson-Fausset-Brown, Commentary Critical and Explanatory (1871, public domain)",
      text: "An expected end — literally, 'a latter end and expectation'; that is, the end which you hope for, and which shall not disappoint you.",
    },
    lemmas: [
      { word: "מַחֲשָׁבָה", translit: "machashabah", strongs: "H4284", gloss: "thoughts, plans", note: "From chashab, 'to weave' or 'to reckon'. Deliberate design, not a passing intention." },
      { word: "שָׁלוֹם", translit: "shalom", strongs: "H7965", gloss: "peace, welfare", note: "Rendered 'prosper' in BSB — the Hebrew is wider: intactness, everything in its place." },
      { word: "תִּקְוָה", translit: "tiqvah", strongs: "H8615", gloss: "hope", note: "Concretely a cord or rope — the same word for Rahab's scarlet line in Joshua 2:18. Hope as something you hold onto." },
    ],
    crossRefs: [ref("Jeremiah", 29, 4, 7), ref("Romans", 15, 13)],
  },

  "Romans 15:13": {
    ref: ref("Romans", 15, 13),
    verses: {
      BSB: [{ n: 13, text: "Now may the God of hope fill you with all joy and peace as you believe in Him, so that you may overflow with hope by the power of the Holy Spirit." }],
      WEB: [{ n: 13, text: "Now may the God of hope fill you with all joy and peace in believing, that you may abound in hope in the power of the Holy Spirit." }],
      KJV: [{ n: 13, text: "Now the God of hope fill you with all joy and peace in believing, that ye may abound in hope, through the power of the Holy Ghost." }],
    },
    context:
      "The closing benediction of Paul's argument to a Roman church split between Jewish and Gentile believers. 'Hope' here is the payoff of eleven chapters of argument, not a mood — it names the confidence that the two groups share one future.",
    lemmas: [
      { word: "ἐλπίς", translit: "elpis", strongs: "G1680", gloss: "hope", note: "Confident expectation of a specific outcome. Unlike English 'hope', it carries no implication of doubt." },
      { word: "περισσεύω", translit: "perisseuō", strongs: "G4052", gloss: "to overflow", note: "Surplus language — more than the container holds. Used of the leftover baskets after the feeding of the five thousand." },
    ],
    crossRefs: [ref("Jeremiah", 29, 11), ref("Romans", 5, 3, 5)],
  },

  "Romans 8:28": {
    ref: ref("Romans", 8, 28),
    verses: {
      BSB: [{ n: 28, text: "And we know that God works all things together for the good of those who love Him, who are called according to His purpose." }],
      WEB: [{ n: 28, text: "We know that all things work together for good for those who love God, for those who are called according to his purpose." }],
      KJV: [{ n: 28, text: "And we know that all things work together for good to them that love God, to them who are the called according to his purpose." }],
    },
    context:
      "Sits inside a passage about suffering and groaning creation (vv. 18-27), which is what 'all things' refers back to. The verse is a claim about trajectory under pressure, and the manuscripts differ on whether God or 'all things' is the subject — hence the split between BSB and KJV above.",
    lemmas: [
      { word: "συνεργέω", translit: "synergeō", strongs: "G4903", gloss: "to work together", note: "Root of English 'synergy'. Whether God is the subject is a genuine textual question, not a translation preference." },
      { word: "πρόθεσις", translit: "prothesis", strongs: "G4286", gloss: "purpose", note: "Literally 'a setting forth' — the same word used for the showbread set out in the temple. Purpose as something placed deliberately." },
    ],
    crossRefs: [ref("Ephesians", 2, 10), ref("Romans", 8, 18, 21)],
  },

  "Ephesians 2:10": {
    ref: ref("Ephesians", 2, 10),
    verses: {
      BSB: [{ n: 10, text: "For we are God's workmanship, created in Christ Jesus to do good works, which God prepared in advance as our way of life." }],
      WEB: [{ n: 10, text: "For we are his workmanship, created in Christ Jesus for good works, which God prepared before that we would walk in them." }],
      KJV: [{ n: 10, text: "For we are his workmanship, created in Christ Jesus unto good works, which God hath before ordained that we should walk in them." }],
    },
    context:
      "Immediately follows the letter's sharpest denial that works save anyone (vv. 8-9). The sequence matters: the works are the output of the making, not the price of it. Ephesus was a craft city — the temple of Artemis supported a large guild of metalworkers — so 'workmanship' was shop-floor vocabulary.",
    lemmas: [
      { word: "ποίημα", translit: "poiēma", strongs: "G4161", gloss: "workmanship", note: "The root of English 'poem'. A made thing, valued for what it is rather than what it produces." },
      { word: "περιπατέω", translit: "peripateō", strongs: "G4043", gloss: "to walk in", note: "Ordinary walking-around language, used across the NT for the whole conduct of a life." },
    ],
    crossRefs: [ref("Ephesians", 2, 8, 9), ref("Romans", 8, 28)],
  },

  "Genesis 6:8": {
    ref: ref("Genesis", 6, 8),
    verses: {
      BSB: [{ n: 8, text: "Noah, however, found favor in the eyes of the LORD." }],
      WEB: [{ n: 8, text: "But Noah found favor in Yahweh's eyes." }],
      KJV: [{ n: 8, text: "But Noah found grace in the eyes of the LORD." }],
    },
    context:
      "The first occurrence of chen in the Hebrew Bible, placed as the hinge of the flood narrative — one clause of favour against a chapter of judgment. KJV renders it 'grace'; most modern versions say 'favour', which is why word-study across translations can quietly mislead.",
    lemmas: [
      { word: "חֵן", translit: "chen", strongs: "H2580", gloss: "favour, grace", note: "Relational and often asymmetric — what a superior extends to an inferior. It is found, not earned, but the OT rarely makes it a technical term." },
    ],
    crossRefs: [ref("Exodus", 34, 6), ref("Ephesians", 2, 8, 9)],
  },

  "Exodus 34:6": {
    ref: ref("Exodus", 34, 6),
    verses: {
      BSB: [{ n: 6, text: "Then the LORD passed in front of Moses and called out: “The LORD, the LORD God, compassionate and gracious, slow to anger, abounding in loving devotion and faithfulness,”" }],
      WEB: [{ n: 6, text: "Yahweh passed by before him, and proclaimed, “Yahweh! Yahweh, a merciful and gracious God, slow to anger, and abundant in loving kindness and truth,”" }],
      KJV: [{ n: 6, text: "And the LORD passed by before him, and proclaimed, The LORD, The LORD God, merciful and gracious, longsuffering, and abundant in goodness and truth," }],
    },
    context:
      "God's self-description, given immediately after the golden calf — i.e. the definitive OT statement of grace is delivered to a people who have just broken the covenant. Quoted or alluded to more than a dozen times across the OT; it functions as Israel's creed.",
    lemmas: [
      { word: "חֶסֶד", translit: "chesed", strongs: "H2617", gloss: "loyal love", note: "The heavyweight OT grace word — covenant loyalty that persists when the other party has forfeited it. Notoriously hard to translate; 'lovingkindness' was coined for it." },
      { word: "חַנּוּן", translit: "channun", strongs: "H2587", gloss: "gracious", note: "Same root as chen. Used only of God in the Hebrew Bible." },
    ],
    crossRefs: [ref("Genesis", 6, 8), ref("Ephesians", 2, 8, 9)],
  },

  "Ephesians 2:8-9": {
    ref: ref("Ephesians", 2, 8, 9),
    verses: {
      BSB: [
        { n: 8, text: "For it is by grace you have been saved through faith, and this not from yourselves; it is the gift of God," },
        { n: 9, text: "not by works, so that no one can boast." },
      ],
      WEB: [
        { n: 8, text: "for by grace you have been saved through faith, and that not of yourselves; it is the gift of God," },
        { n: 9, text: "not of works, that no one would boast." },
      ],
      KJV: [
        { n: 8, text: "For by grace are ye saved through faith; and that not of yourselves: it is the gift of God:" },
        { n: 9, text: "Not of works, lest any man should boast." },
      ],
    },
    context:
      "Where charis becomes a technical term. Paul is writing into a Greco-Roman patronage culture in which a gift created a debt and a public obligation to the giver — verse 9 exists to cut that expectation off, which is a sharper move in its own setting than it reads as now.",
    lemmas: [
      { word: "χάρις", translit: "charis", strongs: "G5485", gloss: "grace", note: "Ordinary Greek for a favour or benefaction. The NT keeps the word and removes the reciprocity that made it work." },
      { word: "δῶρον", translit: "dōron", strongs: "G1435", gloss: "gift", note: "Chosen over the patronage vocabulary a Greek reader would expect — a present, not a benefaction requiring return." },
    ],
    crossRefs: [ref("Genesis", 6, 8), ref("Exodus", 34, 6), ref("Ephesians", 2, 10)],
  },
};

/* ------------------------------------------------------------------ */
/* ANSWERS — keyword-routed. Real backend replaces this with retrieval. */
/* ------------------------------------------------------------------ */

const ANSWERS = [
  {
    match: /anxiet|anxious|worry|worried|stress|panic|afraid|fear/i,
    text:
      "Three passages carry most of the weight here, and they are doing different jobs.\n\nPaul writes [Philippians 4:6-7] from custody, and the instruction is a swap rather than a suppression: anxiety out, request in. The verb he uses for anxiety, merimnaō, is built on the idea of division — a mind pulled into parts. What replaces it is described in military terms; the peace \"guards\" the heart the way a garrison holds a gate.\n\nJesus argues differently in [Matthew 6:25-27]. He does not say the worry is unreasonable. He says it is ineffective — it adds nothing — and that the worrier has misjudged their own worth against the birds.\n\n[1 Peter 5:6-7] supplies the mechanics. In Greek those two verses are a single sentence, which means the casting is not a separate step after humbling yourself; it is how the humbling happens.\n\nWhat the text does not do is treat anxiety as sin to be repented of. Every one of these passages assumes the reader is already anxious and addresses what to do next.",
    citations: [ref("Philippians", 4, 6, 7), ref("Matthew", 6, 25, 27), ref("1 Peter", 5, 6, 7)],
    sources: ["Matthew Henry (1710)", "Jamieson-Fausset-Brown (1871)"],
  },
  {
    match: /grace|charis|chesed|favou?r/i,
    text:
      "Worth separating the word from the concept, because they do not track each other.\n\nIn the Old Testament two words are in play. chen is favour that is found rather than earned — [Genesis 6:8] is its first appearance, and the KJV renders it \"grace\" while most modern versions say \"favour\". chesed is the heavier one: covenant loyalty that persists after the other party has defaulted. [Exodus 34:6] is the anchor text, and its timing is the point — it is God's self-description delivered immediately after the golden calf.\n\nIn the New Testament, charis becomes a technical term in [Ephesians 2:8-9]. The Greco-Roman context matters: a gift created a public debt to the giver, so verse 9 exists to cut that expectation off.\n\nThe honest summary is that the concept is continuous and the vocabulary is not. The OT has grace without a single fixed word for it; the NT fixes the word. Anyone claiming the OT is law and the NT is grace has to explain Exodus 34.",
    citations: [ref("Genesis", 6, 8), ref("Exodus", 34, 6), ref("Ephesians", 2, 8, 9)],
    sources: ["Public-domain lexical data (Strong's)"],
  },
  {
    match: /hope|future|despair|plans? fall|fell apart|hopeless|discourag/i,
    text:
      "[Jeremiah 29:11] is the verse people reach for, and it is worth reading with its own address label on. It is a letter to deportees in Babylon. The promise is collective rather than individual, and verse 10 puts it seventy years out — so most of the original readers died in exile with the promise still outstanding. Verse 5 tells them to build houses and plant gardens in the meantime.\n\nThat makes it a sturdier verse than the coffee-mug version, not a weaker one. The Hebrew for hope, tiqvah, is concretely a cord or rope — the same word as Rahab's scarlet line. Something you hold, not something you feel.\n\n[Romans 15:13] is the New Testament counterpart, and it treats hope as an overflow rather than a reserve — perisseuō is surplus language, the leftover baskets after the crowd has eaten.\n\nI would flag that neither passage promises the plan you had. Both promise a future that is not the one you are currently standing in.",
    citations: [ref("Jeremiah", 29, 11), ref("Romans", 15, 13)],
    sources: ["Jamieson-Fausset-Brown (1871)"],
  },
  {
    match: /purpose|calling|meaning|why am i here|what should i do with my life|vocation/i,
    text:
      "Two passages, and the order they are usually quoted in inverts their logic.\n\n[Ephesians 2:10] calls you God's poiēma — the root of English \"poem\". A made thing, valued for being made. It comes directly after the letter's sharpest denial that works save anyone, and that sequence is the argument: the works are the output of the making, not the price of it.\n\n[Romans 8:28] supplies the word \"purpose\" itself. prothesis is literally \"a setting forth\", the same word used for showbread laid out in the temple — something placed deliberately. Note that the verse sits inside a passage about suffering and groaning creation, which is what \"all things\" refers back to.\n\nWhat neither passage offers is a job description. The New Testament vocabulary for purpose is about belonging to a design, and it is consistently vaguer about the specifics than most people asking this question want it to be.",
    citations: [ref("Ephesians", 2, 10), ref("Romans", 8, 28)],
    sources: ["Public-domain lexical data (Strong's)"],
  },
  {
    match: /peace|shalom|calm|rest/i,
    text:
      "[Philippians 4:6-7] is the densest verse on this. The Greek eirēnē carries the freight of Hebrew shalom, which is wholeness and repair rather than the absence of conflict — a broken thing put back, not a quiet room.\n\nThe verb attached to it, phroureō, is a garrison term: to post a sentry. So the peace in verse 7 is not primarily a feeling. It is described as something stationed at a gate, doing a job, whether or not you notice it.\n\n[Romans 15:13] pairs peace with joy as the contents of the same filling, which suggests the two are not alternatives.",
    citations: [ref("Philippians", 4, 6, 7), ref("Romans", 15, 13)],
    sources: ["Matthew Henry (1710)"],
  },
];

const FALLBACK = (query) => ({
  text:
    `This build has no retrieval engine behind it yet, so I am not going to invent an answer about "${query.trim()}" — a Bible tool that fabricates references is worse than no tool.\n\nWhat is wired: the citation pills, the inspector, translation switching across three public-domain texts, and the original-language cards, all driven through a single mockApi seam. When that seam is pointed at real verse-level retrieval, this question gets a real answer through exactly the same path.\n\nQueries with content loaded: anxiety, grace in the OT vs NT, hope, purpose, and peace.`,
  citations: [],
  sources: [],
  grounded: false,
});

/* ------------------------------------------------------------------ */
/* PUBLIC API                                                          */
/* ------------------------------------------------------------------ */

let idSeq = 0;
const nextId = () => `msg_${Date.now()}_${idSeq++}`;
const latency = (ms) => new Promise((r) => setTimeout(r, ms));

export async function askBerean(query, _translation) {
  await latency(320 + Math.random() * 380);
  const hit = ANSWERS.find((a) => a.match.test(query));
  const body = hit
    ? { text: hit.text, citations: hit.citations, sources: hit.sources, grounded: true }
    : FALLBACK(query);
  return { id: nextId(), ...body };
}

export async function getPassage(r, translation) {
  await latency(120);
  const p = PASSAGES[refKey(r)];
  if (!p) return null;
  const verses = p.verses[translation] || p.verses.BSB;
  return {
    ref: p.ref,
    refLabel: refKey(p.ref),
    translation: p.verses[translation] ? translation : "BSB",
    requestedTranslation: translation,
    verses,
    context: p.context,
    commentary: p.commentary || null,
    lemmas: p.lemmas,
    crossRefs: p.crossRefs || [],
  };
}

export const hasPassage = (r) => Boolean(PASSAGES[refKey(r)]);
