// Browser speech reads only the supplied public briefing/dialogue text.
// No audio-generation server or model credentials are used by this module.
export function dialogueParts(event, people = {}) {
  if (
    event?.type !== "action" ||
    event.action?.tool !== "ask" ||
    event.observation?.error
  )
    return [];
  const question = event.action.args?.question,
    answer = event.observation?.words;
  if (!question || !answer) return [];
  return [
    { speaker: "detective", text: "Inspector Mehra. " + question },
    {
      speaker: "witness",
      text: (people[event.action.args.pid]?.name || "Witness") + ". " + answer,
    },
  ];
}
export function caseBriefing(task = {}, scene = {}) {
  const intro =
    task.briefing ||
    "You arrive at the reported scene as Inspector Arun Mehra. Begin with what you can observe, hear the accounts of the people you meet, and support your conclusions with acquired sources.";
  return (
    intro +
    (scene.place?.name
      ? " Your starting point is " + scene.place.name + "."
      : "") +
    (task.scope ? " Your assignment: " + task.scope : "")
  );
}
export class BrowserVoice {
  constructor(environment = globalThis, onStatus = () => {}) {
    this.synth = environment.speechSynthesis;
    this.Utterance = environment.SpeechSynthesisUtterance;
    this.onStatus = onStatus;
    this.queue = [];
    this.current = null;
    this.generation = 0;
    this.timer = null;
    this.utterance = null;
  }
  get supported() {
    return !!(this.synth && this.Utterance);
  }
  cancel() {
    this.generation++;
    if (this.timer) clearTimeout(this.timer);
    this.timer = null;
    const jobs = [...(this.current ? [this.current] : []), ...this.queue];
    this.current = null;
    this.queue = [];
    this.utterance = null;
    for (const job of jobs) job.resolve("cancelled");
    if (this.supported) this.synth.cancel();
    this.onStatus("Voice stopped.");
  }
  speak(parts, { interrupt = false } = {}) {
    if (interrupt) this.cancel();
    if (!this.supported) {
      this.onStatus(
        "Speech is unavailable in this browser. The text remains available.",
      );
      return Promise.resolve("unavailable");
    }
    const chunks = [];
    for (const part of parts) {
      const words = String(part.text || "").split(/\s+/);
      let line = "";
      for (const word of words) {
        if (line.length + word.length > 220 && line) {
          chunks.push({ text: line, speaker: part.speaker });
          line = "";
        }
        line += (line ? " " : "") + word;
      }
      if (line) chunks.push({ text: line, speaker: part.speaker });
    }
    return new Promise((resolve) => {
      this.queue.push({ chunks, resolve });
      this.drain();
    });
  }
  drain() {
    if (this.current || !this.queue.length) return;
    const job = this.queue.shift();
    this.current = job;
    const generation = this.generation;
    let index = 0;
    const finish = (result) => {
      if (generation !== this.generation || this.current !== job) return;
      if (this.timer) clearTimeout(this.timer);
      this.timer = null;
      this.utterance = null;
      this.current = null;
      job.resolve(result);
      this.onStatus(
        result === "finished"
          ? "Voice ready."
          : "Voice unavailable. Continue with the text.",
      );
      this.drain();
    };
    const next = () => {
      if (generation !== this.generation || this.current !== job) return;
      if (this.timer) clearTimeout(this.timer);
      if (index >= job.chunks.length) {
        finish("finished");
        return;
      }
      const part = job.chunks[index++],
        utterance = new this.Utterance(part.text);
      this.utterance = utterance;
      const voices = this.synth
        .getVoices()
        .filter((v) => /^en\b/i.test(v.lang))
        .sort((a, b) => Number(b.localService) - Number(a.localService));
      if (voices.length)
        utterance.voice =
          voices[part.speaker === "witness" && voices.length > 1 ? 1 : 0];
      utterance.lang = utterance.voice?.lang || "en-US";
      utterance.rate = 0.98;
      utterance.onend = next;
      utterance.onerror = () => finish("unavailable");
      this.timer = setTimeout(() => {
        if (generation !== this.generation) return;
        this.cancel();
        this.onStatus(
          "The voice service did not respond. Continue with the text.",
        );
      }, 30000);
      this.onStatus(
        part.speaker === "witness"
          ? "Reading the character’s answer…"
          : part.speaker === "detective"
            ? "Reading the detective’s question…"
            : "Reading the case briefing…",
      );
      try {
        this.synth.speak(utterance);
      } catch {
        finish("unavailable");
      }
    };
    next();
  }
}
