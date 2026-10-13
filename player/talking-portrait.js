// Talking portrait: a base picture plus mouth and eye cut-outs (made by
// scripts/prepare_portrait.py), shown on top of each other. Works in any
// browser, so the same code runs on the web and inside a Capacitor phone app.
//
//   const p = await TalkingPortrait.create(element, "characters/maya");
//   p.say("Kumusta ka?", { lang: "fil-PH" });   // speaks with lip-sync
//   p.playVisemes([{ t: 0, shape: "ah" }, ...]); // timings from a TTS service

// Mouth shape for the main vowel of a syllable.
const MOUTH_FOR_VOWEL = { a: "ah", e: "half", i: "half", o: "oh", u: "oh", y: "half" };

// A letter on its own is read out by name ("ay", "bee", "double-u"):
// the mouth shapes of saying that name.
const LETTER_NAME = {
  a: ["ah", "half"], b: ["closed", "half"], c: ["half", "half"], d: ["half", "half"],
  e: ["half", "half"], f: ["half", "closed"], g: ["half", "half"], h: ["ah", "half"],
  i: ["ah", "half"], j: ["half", "ah"], k: ["half", "ah"], l: ["half", "half"],
  m: ["half", "closed"], n: ["half", "half"], o: ["oh", "oh"], p: ["closed", "half"],
  q: ["half", "oh"], r: ["ah", "ah"], s: ["half", "half"], t: ["half", "half"],
  u: ["half", "oh"], v: ["half", "half"], w: ["half", "oh", "half", "oh"], x: ["half", "half"],
  y: ["ah", "half"], z: ["half", "half"],
};

const SYLLABLE_MS = 190; // one syllable at normal speed

// Split a word into mouth movements: one open shape per syllable, closing
// briefly for m/b/p, with a short in-between shape so it never snaps shut.
function cuesForWord(word, rate) {
  const ms = SYLLABLE_MS / rate;
  const w = word.toLowerCase().replace(/[^a-z']/g, "");
  if (!w) return [];
  if (w.length === 1) {
    // Shorter than the letter takes to say, so the mouth closes between letters.
    return (LETTER_NAME[w] ?? ["half"]).map((shape) => ({ shape, ms: ms * 0.55 }));
  }
  const syllables = w.match(/[^aeiouy]*[aeiouy]+(?:[^aeiouy]*$)?/g) || [w];
  const cues = [];
  for (const s of syllables) {
    if (/^[mbp]/.test(s)) cues.push({ shape: "closed", ms: ms * 0.25 });
    const vowel = s.match(/[aeiouy]/)?.[0];
    cues.push({ shape: MOUTH_FOR_VOWEL[vowel] ?? "half", ms: ms * 0.6 });
    cues.push({ shape: "half", ms: ms * 0.25 });
  }
  return cues;
}

export class TalkingPortrait {
  static async create(container, folder) {
    const info = await (await fetch(`${folder}/layers.json`)).json();
    return new TalkingPortrait(container, folder, info);
  }

  constructor(container, folder, info) {
    this.container = container;
    this.size = info.size;
    container.classList.add("tp");
    this.stage = document.createElement("div");
    this.stage.className = "tp-stage";
    container.appendChild(this.stage);
    this.stage.appendChild(this.img(`${folder}/base.webp`, { x: 0, y: 0, w: info.size, h: info.size }));
    this.layers = {};
    for (const [name, box] of Object.entries(info.layers)) {
      const el = this.img(`${folder}/${name}.webp`, box);
      el.style.opacity = 0;
      this.stage.appendChild(el);
      this.layers[name] = el;
    }
    this.mouth = "closed";
    this.scheduleBlink();
  }

  img(src, box) {
    const el = document.createElement("img");
    el.src = src;
    el.alt = "";
    el.draggable = false;
    const pct = (v) => `${(v / this.size) * 100}%`;
    Object.assign(el.style, { left: pct(box.x), top: pct(box.y), width: pct(box.w), height: pct(box.h) });
    return el;
  }

  setMouth(shape) {
    if (shape === this.mouth) return;
    for (const name of ["half", "oh", "ah"]) {
      const el = this.layers[`mouth_${name}`];
      if (el) el.style.opacity = name === shape ? 1 : 0;
    }
    this.mouth = shape;
  }

  blink() {
    const el = this.layers.eyes_closed;
    if (!el) return;
    el.style.opacity = 1;
    setTimeout(() => (el.style.opacity = 0), 130);
  }

  scheduleBlink() {
    this.blinkTimer = setTimeout(() => {
      this.blink();
      if (Math.random() < 0.2) setTimeout(() => this.blink(), 250); // the odd double blink
      this.scheduleBlink();
    }, 2500 + Math.random() * 3500);
  }

  // Exact lip-sync from timed mouth shapes, e.g. from a TTS service's viseme events.
  playVisemes(cues) {
    this.stop();
    const start = performance.now();
    this.timers = cues.map((c) => setTimeout(() => this.setMouth(c.shape), c.t * 1000 - (performance.now() - start)));
  }

  // Approximate lip-sync from the text while the browser's own voice speaks it.
  say(text, { lang = "en-US", voice = null, rate = 1, pitch = 1 } = {}) {
    this.stop();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = lang;
    u.rate = rate;
    u.pitch = pitch;
    if (voice) u.voice = voice;
    let timer = null;
    const play = (cues) => {
      clearTimeout(timer);
      const next = () => {
        const cue = cues.shift();
        if (!cue) return this.setMouth("closed"); // between words
        this.setMouth(cue.shape);
        timer = setTimeout(next, cue.ms);
      };
      next();
    };
    // Each word boundary starts that word's mouth movements, so the mouth
    // follows where the voice actually is.
    u.onboundary = (e) => {
      if (e.name && e.name !== "word") return;
      const word = text.slice(e.charIndex).match(/^\S+/);
      if (word) play(cuesForWord(word[0], rate));
    };
    u.onstart = () => this.container.classList.add("tp-talking");
    u.onend = u.onerror = () => {
      clearTimeout(timer);
      this.setMouth("closed");
      this.container.classList.remove("tp-talking");
    };
    this.ticker = () => clearTimeout(timer);
    speechSynthesis.speak(u);
  }

  // Remove the portrait from the page (e.g. before showing another character).
  destroy() {
    this.stop();
    clearTimeout(this.blinkTimer);
    this.stage.remove();
    this.container.classList.remove("tp", "tp-talking");
  }

  stop() {
    (this.timers || []).forEach(clearTimeout);
    this.timers = [];
    if (this.ticker) this.ticker();
    if (speechSynthesis.speaking) speechSynthesis.cancel();
    this.setMouth("closed");
  }
}
