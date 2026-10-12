// Talking portrait: a base picture plus mouth and eye cut-outs (made by
// scripts/prepare_portrait.py), shown on top of each other. Works in any
// browser, so the same code runs on the web and inside a Capacitor phone app.
//
//   const p = await TalkingPortrait.create(element, "characters/maya");
//   p.say("Kumusta ka?", { lang: "fil-PH" });   // speaks with lip-sync
//   p.playVisemes([{ t: 0, shape: "ah" }, ...]); // timings from a TTS service

const MOUTH_FOR_LETTER = {
  a: "ah", e: "half", i: "half", o: "oh", u: "oh", y: "half",
  m: "closed", b: "closed", p: "closed",
  w: "oh", r: "half", l: "half", f: "half", v: "half",
};

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
  say(text, { lang = "en-US", voice = null, rate = 1 } = {}) {
    this.stop();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = lang;
    u.rate = rate;
    if (voice) u.voice = voice;
    const msPerLetter = 75 / rate;
    let letters = [];
    let tick = null;
    const run = () => {
      tick = setInterval(() => {
        const ch = letters.shift();
        if (ch === undefined) return this.setMouth("closed");
        this.setMouth(MOUTH_FOR_LETTER[ch] ?? (/[a-z]/.test(ch) ? "half" : "closed"));
      }, msPerLetter);
    };
    // Each word boundary re-syncs the mouth with where the voice actually is.
    u.onboundary = (e) => {
      if (e.name && e.name !== "word") return;
      const word = text.slice(e.charIndex).match(/^[^\s]+/);
      letters = word ? [...word[0].toLowerCase()] : [];
    };
    u.onstart = () => {
      letters = [...text.toLowerCase()];
      run();
      this.container.classList.add("tp-talking");
    };
    u.onend = u.onerror = () => {
      clearInterval(tick);
      this.setMouth("closed");
      this.container.classList.remove("tp-talking");
    };
    this.ticker = () => clearInterval(tick);
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
