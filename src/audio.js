// 《山河织路》 — original procedural soundscape (WebAudio, no samples).
// Five era ambiences, a shared pentatonic score, and launch / UI effects.

const midi = (n) => 440 * Math.pow(2, (n - 69) / 12);
const CHORDS = [
  [50, 57, 62, 66], // rural: D major add9, open
  [48, 55, 60, 64], // town: C major 7
  [45, 52, 57, 60], // city: A minor 7
  [43, 50, 55, 59], // rail: G major 7
  [38, 45, 50, 53], // future: D minor-ish, low
];
const SCALES = [
  [62, 64, 66, 69, 71, 74, 76, 78],
  [60, 62, 64, 67, 69, 72, 74, 76],
  [57, 60, 62, 64, 67, 69, 72, 74],
  [59, 62, 64, 66, 69, 71, 74, 76],
  [50, 53, 57, 62, 65, 69, 74, 77],
];

function makeNoise(ctx, seconds = 4, brown = false) {
  const n = Math.floor(ctx.sampleRate * seconds);
  const buf = ctx.createBuffer(2, n, ctx.sampleRate);
  for (let ch = 0; ch < 2; ch++) {
    const d = buf.getChannelData(ch);
    let last = 0;
    for (let i = 0; i < n; i++) {
      const w = Math.random() * 2 - 1;
      if (brown) { last = (last + 0.02 * w) / 1.02; d[i] = last * 3.5; }
      else d[i] = w;
    }
  }
  return buf;
}

function impulse(ctx, seconds = 2.6, decay = 2.4) {
  const n = Math.floor(ctx.sampleRate * seconds);
  const b = ctx.createBuffer(2, n, ctx.sampleRate);
  for (let ch = 0; ch < 2; ch++) {
    const d = b.getChannelData(ch);
    for (let i = 0; i < n; i++) {
      const t = i / n;
      d[i] = (Math.random() * 2 - 1) * Math.pow(1 - t, decay) * (ch ? 0.82 : 1);
    }
  }
  return b;
}

export class Soundscape {
  constructor(onChange, initialOn = true) {
    this.onChange = onChange;
    this.on = !!initialOn;
    this.ctx = null;
    this.master = null;
    this.music = null;
    this.reverb = null;
    this.amb = null;
    this.chapter = -1;
    this.chimeTimer = null;
    this.lastChime = 0;
    this.white = null;
    this.brown = null;
  }

  init() {
    if (this.ctx) { this.resume(true); return; }
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    const ctx = this.ctx = new AC();
    this.master = ctx.createGain();
    this.master.gain.value = this.on ? 0.2 : 0;
    this.master.connect(ctx.destination);
    // shared reverb
    this.reverb = ctx.createConvolver();
    this.reverb.buffer = impulse(ctx);
    const wet = ctx.createGain(); wet.gain.value = 0.3;
    this.reverb.connect(wet); wet.connect(this.master);
    // music bus
    this.music = ctx.createGain(); this.music.gain.value = 0.5;
    const mLP = ctx.createBiquadFilter(); mLP.type = 'lowpass'; mLP.frequency.value = 1500; mLP.Q.value = 0.3;
    this.music.connect(mLP); mLP.connect(this.master);
    const mSend = ctx.createGain(); mSend.gain.value = 0.35; mLP.connect(mSend); mSend.connect(this.reverb);
    // beds
    this.white = makeNoise(ctx, 4, false);
    this.brown = makeNoise(ctx, 5, true);
    this.startPads();
    this.scheduleChime();
    if (this.chapter >= 0) this.buildChapter(this.chapter, true);
  }

  startPads() {
    const ctx = this.ctx;
    this.pads = [];
    for (let k = 0; k < 4; k++) {
      const o = ctx.createOscillator();
      o.type = k === 0 ? 'sine' : (k === 2 ? 'triangle' : 'sine');
      o.frequency.value = midi(CHORDS[0][k]);
      o.detune.value = (k - 1.5) * 3;
      const g = ctx.createGain(); g.gain.value = k === 0 ? 0.11 : 0.045;
      o.connect(g); g.connect(this.music);
      o.start();
      this.pads.push(o);
    }
  }

  setChapter(i) {
    this.chapter = i;
    if (!this.ctx) return;
    const t = this.ctx.currentTime;
    const chord = CHORDS[i] || CHORDS[0];
    this.pads.forEach((o, k) => {
      o.frequency.cancelScheduledValues(t);
      o.frequency.setTargetAtTime(midi(chord[k] || chord[2]), t, 1.6);
    });
    this.buildChapter(i);
  }

  stopAmbience() {
    const a = this.amb;
    if (!a) return;
    this.amb = null;
    a.timers.forEach(clearTimeout);
    const t = this.ctx.currentTime;
    try { a.gain.gain.cancelScheduledValues(t); a.gain.gain.setTargetAtTime(0.0001, t, 0.5); } catch (e) {}
    setTimeout(() => {
      a.sources.forEach((s) => { try { s.stop(); } catch (e) {} });
      try { a.gain.disconnect(); } catch (e) {}
    }, 2200);
  }

  makeBed(buffer, type, freq, q, gainVal, gainLfo) {
    const ctx = this.ctx;
    const s = ctx.createBufferSource(); s.buffer = buffer; s.loop = true;
    const f = ctx.createBiquadFilter(); f.type = type; f.frequency.value = freq; f.Q.value = q;
    const g = ctx.createGain(); g.gain.value = gainVal;
    s.connect(f); f.connect(g); g.connect(this.amb.gain);
    if (gainLfo) {
      const l = ctx.createOscillator(); l.type = 'sine'; l.frequency.value = gainLfo;
      const lg = ctx.createGain(); lg.gain.value = gainVal * 0.45;
      l.connect(lg); lg.connect(g.gain); l.start();
      this.amb.sources.push(l);
    }
    s.start();
    this.amb.sources.push(s);
    return g;
  }

  buildChapter(i, immediate = false) {
    if (!this.ctx) return;
    this.stopAmbience();
    const ctx = this.ctx;
    const bus = ctx.createGain();
    bus.gain.value = immediate ? 1 : 0.0001;
    bus.connect(this.master);
    this.amb = { gain: bus, sources: [], timers: [] };
    if (!immediate) bus.gain.setTargetAtTime(1, ctx.currentTime, 0.9);

    if (i === 0) {
      this.makeBed(this.white, 'lowpass', 520, 0.7, 0.10, 0.07);
      this.makeBed(this.white, 'bandpass', 1800, 0.8, 0.012, 0.13);
      this.birdLoop();
    } else if (i === 1) {
      this.makeBed(this.brown, 'bandpass', 420, 0.6, 0.075, 0.05);
      this.makeBed(this.white, 'lowpass', 900, 0.5, 0.018, 0.09);
      this.bellLoop();
    } else if (i === 2) {
      this.makeBed(this.white, 'highpass', 1300, 0.4, 0.055, 0.18);
      this.makeBed(this.brown, 'lowpass', 240, 0.8, 0.085, 0.06);
      this.makeBed(this.white, 'bandpass', 3100, 1.2, 0.012, 0.4);
      this.hornLoop();
    } else if (i === 3) {
      this.makeBed(this.white, 'bandpass', 340, 0.5, 0.05, 0.11);
      this.makeBed(this.brown, 'lowpass', 180, 0.6, 0.07, 0.04);
      this.clackLoop();
    } else {
      this.makeBed(this.white, 'highpass', 2400, 0.5, 0.016, 0.05);
      this.makeBed(this.brown, 'lowpass', 120, 0.7, 0.05, 0.03);
      const sub = ctx.createOscillator(); sub.type = 'sine'; sub.frequency.value = 55;
      const sg = ctx.createGain(); sg.gain.value = 0.035;
      sub.connect(sg); sg.connect(bus); sub.start(); this.amb.sources.push(sub);
      this.pingLoop();
    }
  }

  birdLoop() {
    const tick = () => {
      if (!this.ctx || this.amb == null) return;
      const t = this.ctx.currentTime;
      for (let k = 0; k < 2 + Math.floor(Math.random() * 3); k++) {
        const o = this.ctx.createOscillator(); o.type = 'sine';
        const s = t + k * 0.12 + Math.random() * 0.1;
        const f = 2200 + Math.random() * 1600;
        o.frequency.setValueAtTime(f, s);
        o.frequency.exponentialRampToValueAtTime(f * (0.6 + Math.random() * 0.5), s + 0.09);
        const g = this.ctx.createGain();
        g.gain.setValueAtTime(0.0001, s);
        g.gain.exponentialRampToValueAtTime(0.018, s + 0.01);
        g.gain.exponentialRampToValueAtTime(0.0001, s + 0.14);
        o.connect(g); g.connect(this.amb.gain); o.start(s); o.stop(s + 0.16);
      }
      this.amb.timers.push(setTimeout(tick, 3800 + Math.random() * 5200));
    };
    tick();
  }

  bellLoop() {
    const ping = () => {
      if (!this.ctx || !this.amb) return;
      const t = this.ctx.currentTime;
      [0, 0.16].forEach((d, k) => {
        const o = this.ctx.createOscillator(); o.type = 'sine';
        o.frequency.value = k ? 1480 : 1180;
        const g = this.ctx.createGain();
        g.gain.setValueAtTime(0.0001, t + d);
        g.gain.exponentialRampToValueAtTime(0.028, t + d + 0.01);
        g.gain.exponentialRampToValueAtTime(0.0001, t + d + 0.5);
        o.connect(g); g.connect(this.amb.gain); o.start(t + d); o.stop(t + d + 0.55);
      });
      this.amb.timers.push(setTimeout(ping, 9000 + Math.random() * 12000));
    };
    this.amb.timers.push(setTimeout(ping, 4200));
  }

  hornLoop() {
    const honk = () => {
      if (!this.ctx || !this.amb) return;
      const t = this.ctx.currentTime;
      const o = this.ctx.createOscillator(); o.type = 'sawtooth'; o.frequency.value = 235;
      const f = this.ctx.createBiquadFilter(); f.type = 'lowpass'; f.frequency.value = 520;
      const g = this.ctx.createGain();
      g.gain.setValueAtTime(0.0001, t);
      g.gain.exponentialRampToValueAtTime(0.012, t + 0.03);
      g.gain.setValueAtTime(0.012, t + 0.22);
      g.gain.exponentialRampToValueAtTime(0.0001, t + 0.4);
      o.connect(f); f.connect(g); g.connect(this.amb.gain); o.start(t); o.stop(t + 0.42);
      this.amb.timers.push(setTimeout(honk, 14000 + Math.random() * 18000));
    };
    this.amb.timers.push(setTimeout(honk, 6500));
  }

  clackLoop() {
    const clack = () => {
      if (!this.ctx || !this.amb) return;
      const t = this.ctx.currentTime;
      [0, 0.16].forEach((d, k) => {
        const s = this.ctx.createBufferSource(); s.buffer = this.white;
        const f = this.ctx.createBiquadFilter(); f.type = 'bandpass'; f.frequency.value = k ? 1900 : 1200; f.Q.value = 1.4;
        const g = this.ctx.createGain();
        g.gain.setValueAtTime(0.0001, t + d);
        g.gain.exponentialRampToValueAtTime(k ? 0.014 : 0.022, t + d + 0.006);
        g.gain.exponentialRampToValueAtTime(0.0001, t + d + 0.09);
        s.connect(f); f.connect(g); g.connect(this.amb.gain);
        s.start(t + d, Math.random() * 2, 0.12);
      });
      this.amb.timers.push(setTimeout(clack, 1150 + Math.random() * 160));
    };
    clack();
  }

  pingLoop() {
    const ping = () => {
      if (!this.ctx || !this.amb) return;
      const t = this.ctx.currentTime;
      const o = this.ctx.createOscillator(); o.type = 'sine';
      o.frequency.setValueAtTime(1320, t);
      o.frequency.exponentialRampToValueAtTime(660, t + 1.4);
      const g = this.ctx.createGain();
      g.gain.setValueAtTime(0.0001, t);
      g.gain.exponentialRampToValueAtTime(0.016, t + 0.02);
      g.gain.exponentialRampToValueAtTime(0.0001, t + 1.7);
      o.connect(g); g.connect(this.amb.gain); o.start(t); o.stop(t + 1.8);
      this.amb.timers.push(setTimeout(ping, 8000 + Math.random() * 9000));
    };
    this.amb.timers.push(setTimeout(ping, 3200));
  }

  scheduleChime() {
    const tick = () => {
      if (this.ctx && this.master && !this.muted) {
        const t = this.ctx.currentTime;
        const i = Math.max(0, this.chapter);
        const scale = SCALES[i] || SCALES[0];
        const n = scale[Math.floor(Math.random() * scale.length)];
        const o = this.ctx.createOscillator(); o.type = 'sine';
        o.frequency.value = midi(n + (i === 4 ? 12 : 0));
        const g = this.ctx.createGain();
        g.gain.setValueAtTime(0.0001, t);
        g.gain.exponentialRampToValueAtTime(0.022, t + 0.03);
        g.gain.exponentialRampToValueAtTime(0.0001, t + 4.6);
        o.connect(g); g.connect(this.music);
        o.start(t); o.stop(t + 4.7);
      }
      this.chimeTimer = setTimeout(tick, 3400 + Math.random() * 3600);
    };
    tick();
  }

  toggle() {
    this.on = !this.on;
    this.muted = !this.on;
    if (this.ctx) {
      this.master.gain.cancelScheduledValues(this.ctx.currentTime);
      this.master.gain.setTargetAtTime(this.on ? 0.2 : 0.0001, this.ctx.currentTime, 0.15);
    }
    this.onChange?.(this.on);
    return this.on;
  }

  suspend() {
    if (!this.ctx) return;
    // Stop the schedulers before freezing the audio clock, so background
    // timers cannot queue many notes at the same timestamp for our return.
    clearTimeout(this.chimeTimer); this.chimeTimer = null;
    this.stopAmbience();
    if (this.ctx.state === 'running') this.ctx.suspend().catch(() => {});
  }
  resume(force = false) {
    if (!this.ctx || (!this.on && !force)) return;
    this.ctx.resume().then(() => {
      if (document.hidden) return;
      if (!this.amb && this.chapter >= 0) this.buildChapter(this.chapter, true);
      if (!this.chimeTimer) this.scheduleChime();
    }).catch(() => {});
  }
  stopLaunch() {
    for (const source of this.launchSources || []) { try { source.stop(); } catch {} }
    this.launchSources = [];
  }

  info() {
    return {
      on: this.on,
      state: this.ctx ? this.ctx.state : 'none',
      chapter: this.chapter,
      master: this.master ? +this.master.gain.value.toFixed(4) : null,
      bed: this.amb ? +this.amb.gain.gain.value.toFixed(4) : null,
      sampleRate: this.ctx ? this.ctx.sampleRate : null,
    };
  }

  sfx(kind) {
    if (!this.ctx || !this.on) return;
    const ctx = this.ctx, t = ctx.currentTime;
    const out = ctx.createGain(); out.gain.value = 0.9; out.connect(this.master);
    if (kind === 'click') {
      const o = ctx.createOscillator(), g = ctx.createGain();
      o.type = 'sine'; o.frequency.value = 690;
      g.gain.setValueAtTime(0.035, t); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.18);
      o.connect(g); g.connect(out); o.start(t); o.stop(t + 0.2);
    } else if (kind === 'whoosh') {
      const s = ctx.createBufferSource(); s.buffer = this.white;
      const f = ctx.createBiquadFilter(); f.type = 'bandpass'; f.Q.value = 0.8;
      f.frequency.setValueAtTime(380, t); f.frequency.exponentialRampToValueAtTime(1500, t + 0.55);
      const g = ctx.createGain();
      g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(0.09, t + 0.06);
      g.gain.exponentialRampToValueAtTime(0.0001, t + 0.9);
      s.connect(f); f.connect(g); g.connect(out); s.start(t, 0, 1.0);
    } else if (kind === 'bell') {
      [1175, 1568].forEach((f, k) => {
        const o = ctx.createOscillator(), g = ctx.createGain();
        o.type = 'sine'; o.frequency.value = f;
        g.gain.setValueAtTime(0.0001, t + k * 0.12);
        g.gain.exponentialRampToValueAtTime(0.03, t + k * 0.12 + 0.01);
        g.gain.exponentialRampToValueAtTime(0.0001, t + k * 0.12 + 0.7);
        o.connect(g); g.connect(out); o.start(t + k * 0.12); o.stop(t + k * 0.12 + 0.75);
      });
    }
  }

  launch() {
    this.stopLaunch();
    if (!this.ctx) this.init();
    if (!this.ctx || !this.on) return;
    const ctx = this.ctx, t = ctx.currentTime;
    const s = ctx.createBufferSource(); s.buffer = this.brown; s.loop = true;
    const f = ctx.createBiquadFilter(); f.type = 'lowpass';
    f.frequency.setValueAtTime(260, t); f.frequency.exponentialRampToValueAtTime(52, t + 8);
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(0.22, t + 1.4);
    g.gain.setValueAtTime(0.22, t + 5.5);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 10);
    s.connect(f); f.connect(g); g.connect(this.master); s.start(t); s.stop(t + 10.2);
    const sub = ctx.createOscillator(); sub.type = 'sine';
    sub.frequency.setValueAtTime(58, t); sub.frequency.exponentialRampToValueAtTime(30, t + 8);
    const sg = ctx.createGain();
    sg.gain.setValueAtTime(0.0001, t); sg.gain.exponentialRampToValueAtTime(0.1, t + 1.8);
    sg.gain.exponentialRampToValueAtTime(0.0001, t + 9);
    sub.connect(sg); sg.connect(this.master); sub.start(t); sub.stop(t + 9.2);
    this.launchSources = [s, sub];
  }
}
