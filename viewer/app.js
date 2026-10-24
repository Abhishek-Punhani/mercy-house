import { backdrop, portrait } from "./art.js";
import {
  initialState,
  stateAt,
  actionTitle,
  recordKind,
  recordLabel,
  recordText,
  reportOutcome,
  findingDescription,
  interviewGroups,
} from "./state.js";
import { BrowserVoice, caseBriefing, dialogueParts } from "./speech.js";

const $ = (id) => document.getElementById(id);
const csrf = document.querySelector('meta[name="mercy-csrf"]').content;
const runControls = new Map();
let voiceEnabled = false,
  playbackGeneration = 0,
  pumpingGeneration = null,
  speechProgress = null;
const voice = new BrowserVoice(globalThis, (message) => {
  for (const id of ["voice-status", "preview-audio-status", "briefing-audio-status"]) {
    const status = $(id); if (status) status.textContent = message;
  }
}, (progress) => {
  speechProgress = progress;
  paintSpeech();
});
function paintSpeech() {
  document.querySelectorAll(".speaking-text").forEach(el => {
    el.classList.remove("speaking-text");
    el.textContent = el.textContent;
  });
  const p = speechProgress, el = p?.target && $(p.target);
  if (!el || el.textContent !== p.fullText) return;
  el.classList.add("speaking-text");
  if (!p.boundary) return;
  const mark = node("mark", "spoken-word", p.fullText.slice(p.start, p.end));
  el.replaceChildren(document.createTextNode(p.fullText.slice(0, p.start)), mark,
    document.createTextNode(p.fullText.slice(p.end)));
}
let settings = {},
  runs = [],
  run = null,
  events = [],
  position = 0,
  state = initialState(),
  playing = false,
  live = false,
  stream = null,
  clock = null,
  filter = "all",
  sceneId = "",
  actorKey = "",
  opened = false,
  announcedReport = "",
  libraryGeneration = 0;
const icon = {
  go: "↗",
  ask: "◌",
  search: "⌕",
  collect: "◇",
  compare: "≋",
  request_access: "⚿",
  excavate: "⌁",
  submit_report: "▤",
  people_here: "♧",
  look: "◈",
  record_note: "✎",
  review_records: "▱",
  run_command: "›_",
};

function node(tag, className, text) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (text !== undefined) el.textContent = String(text);
  return el;
}
function toast(text) {
  $("toast").textContent = text;
  $("toast").classList.remove("hidden");
  setTimeout(() => $("toast").classList.add("hidden"), 6000);
}
async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Mercy-CSRF": csrf,
      ...options.headers,
    },
  });
  const value = await response.json();
  if (!response.ok) throw new Error(value.error || "Request failed");
  return value;
}
function kindLabel(item) {
  return item.kind === "reference"
    ? "SCRIPTED REFERENCE"
    : item.kind === "selector-checkpoint"
      ? "RL CHECKPOINT REPLAY"
      : item.kind === "live-model" &&
          ["starting", "building", "running", "stopping"].includes(item.status)
        ? "LIVE API MODEL"
        : "RECORDED API MODEL";
}
function showDetail(title, text, kicker = "FROM THE CASEBOOK") {
  $("detail-title").textContent = title;
  $("detail-kicker").textContent = kicker;
  $("detail-body").replaceChildren(node("div", "", text));
  $("detail-dialog").showModal();
}
function addActor(id, name, appearance = "") {
  const el = node("div", "actor");
  el.innerHTML = portrait(id, appearance);
  el.append(node("span", "actor-name", name));
  return el;
}
function renderActors() {
  const conversation = state.conversation,
    ids = conversation
      ? ["detective", conversation.pid]
      : [
          "detective",
          ...state.here
            .filter(
              (id) => !state.people[id]?.appearance?.includes("Motionless"),
            )
            .slice(0, 4),
        ];
  const key = JSON.stringify([sceneId, ids, !!conversation]);
  if (key === actorKey) return;
  actorKey = key;
  $("occupants").classList.toggle("interview", !!conversation);
  $("occupants").replaceChildren(
    ...ids.map((id) =>
      addActor(
        id,
        id === "detective" ? "Inspector Mehra" : state.people[id]?.name || id,
        state.people[id]?.appearance || "",
      ),
    ),
  );
}
function renderRecords() {
  const records = Object.values(state.records)
    .filter((r) => !["note"].includes(recordKind(r)))
    .filter(
      (r) =>
        filter === "all" ||
        (filter === "material" && r.object_id) ||
        (filter === "accounts" && r.recollections),
    )
    .reverse();
  $("evidence-list").replaceChildren();
  if (!records.length) {
    const empty = node("div", "evidence-empty");
    empty.append(
      node("span", "", "▱"),
      node("h3", "", "Nothing on the table. Yet."),
      node("p", "", "Acquired material and accounts will appear here."),
    );
    $("evidence-list").append(empty);
    return;
  }
  for (const record of records) {
    const card = node("button", "evidence-card");
    card.type = "button";
    card.setAttribute("aria-label", "Read " + recordLabel(record));
    card.append(
      node("span", "record-type", recordKind(record).toUpperCase()),
      node("span", "record-corner", record.record_id),
      node("h3", "", recordLabel(record)),
      node("p", "", recordText(record)),
      node(
        "small",
        "",
        state.secured.includes(record.object_id)
          ? "SECURED IN CUSTODY"
          : record.where
            ? "FOUND AT " + record.where.replaceAll("_", " ").toUpperCase()
            : record.recollections
              ? "RECOLLECTIONS RETAIN THEIR SOURCE BASIS"
              : "ACQUIRED OBSERVATION",
      ),
    );
    card.addEventListener("click", () => {
      $("detail-title").textContent = recordLabel(record);
      $("detail-kicker").textContent =
        record.record_id + " · " + recordKind(record).toUpperCase();
      const content = [node("div", "", recordText(record))];
      if (record.recollections)
        for (const m of record.recollections)
          content.push(
            node(
              "span",
              "source-line",
              m.basis.replaceAll("_", " ").toUpperCase() + " — " + m.text,
            ),
          );
      if (record.compared)
        content.push(
          node(
            "span",
            "source-line",
            "Compared acquired sources: " + record.compared.join(", "),
          ),
        );
      if (record.where)
        content.push(
          node(
            "span",
            "source-line",
            "Found at " +
              record.where.replaceAll("_", " ") +
              ". Found by " +
              record.found_by +
              ".",
          ),
        );
      $("detail-body").replaceChildren(...content);
      $("detail-dialog").showModal();
    });
    $("evidence-list").append(card);
  }
}
function renderTimeline() {
  $("timeline-meta").textContent = state.history.length + " ACTIONS OBSERVED";
  $("timeline-events").replaceChildren();
  if (!state.history.length) {
    $("timeline-events").append(
      node(
        "p",
        "empty-copy",
        "Movement, discoveries and conversations will appear here.",
      ),
    );
    return;
  }
  for (const item of state.history.slice(-12).reverse()) {
    const row = node("div", "timeline-item"),
      content = node("div");
    let detail = "";
    const o = item.observation;
    if (o.error) detail = o.error;
    else if (item.action.tool === "go")
      detail = o.place?.name || "Following a visible route.";
    else if (o.findings)
      detail = o.findings.length
        ? o.findings.map(recordLabel).join(" · ")
        : "No new material found on this feature.";
    else if (o.words)
      detail = o.words.slice(0, 180) + (o.words.length > 180 ? "…" : "");
    else if (o.observation) detail = o.observation.slice(0, 180);
    else if (o.people) detail = o.people.map((p) => p.name).join(" · ");
    else if (o.summary) detail = o.summary;
    else if (o.secured) detail = "Custody recorded for " + o.secured;
    else if (o.submitted)
      detail = "The final report is being checked against acquired support.";
    else if (o.records)
      detail = "Reviewed " + o.records.length + " acquired records.";
    else if (item.action.tool === "run_command")
      detail = o.timed_out
        ? "Command timed out; the investigation can continue."
        : "Isolated command completed. Local files cannot create evidence.";
    else if (o.granted !== undefined)
      detail = o.granted ? "Access was granted." : "Access was declined.";
    else detail = "A public observation was recorded.";
    content.append(
      node("strong", "", actionTitle(item.action, state)),
      node("p", "", detail),
    );
    row.append(
      node("span", "timeline-icon", icon[item.action.tool] || "·"),
      content,
      node(
        "small",
        "",
        item.reply ? "REPLY " + item.reply : "EVENT " + item.seq,
      ),
    );
    $("timeline-events").append(row);
  }
}
function renderInterviews() {
  const groups = interviewGroups(state);
  $("interview-panel").classList.toggle("hidden", !groups.length);
  $("interview-count").textContent =
    groups.reduce((total, g) => total + g.exchanges.length, 0) +
    " QUESTIONS OBSERVED";
  const opened = new Set(
    [...$("interview-list").querySelectorAll("details[open]")].map(
      (d) => d.dataset.person,
    ),
  );
  $("interview-list").replaceChildren(
    ...groups.map((group) => {
      const detail = node("details", "interview-group");
      detail.dataset.person = group.pid;
      detail.open = opened.has(group.pid);
      detail.append(
        node(
          "summary",
          "",
          group.name +
            " · " +
            group.exchanges.length +
            " " +
            (group.exchanges.length === 1 ? "exchange" : "exchanges"),
        ),
      );
      for (const [i, exchange] of group.exchanges.entries()) {
        const entry = node("div", "interview-entry");
        entry.append(
          node(
            "small",
            "",
            String(i + 1).padStart(2, "0") +
              (exchange.reply ? " · REPLY " + exchange.reply : ""),
          ),
          node("p", "interview-question", exchange.question),
          node("p", "", exchange.answer),
        );
        if (exchange.show.length)
          entry.append(
            node(
              "small",
              "",
              "Presented acquired records: " + exchange.show.join(", "),
            ),
          );
        detail.append(entry);
      }
      return detail;
    }),
  );
}
function reportBlocks() {
  const blocks = [],
    finished = state.finished,
    result = finished?.result || {},
    submission = state.submission;
  const provenance =
    run.kind === "reference"
      ? "This is a scripted reference with cooperative fixture characters. It demonstrates a legal proof route; it is not a learned detective result."
      : run.kind === "selector-checkpoint"
        ? "This is an actual trained-selector skill checkpoint with previously acquired material. Its exercise reward is separate from the broader Town report score; it is not a fresh crime-scene solve."
        : "This is an actual API detective run. Its submitted conclusions are checked against the evidence it acquired.";
  blocks.push(node("p", "report-provenance", provenance));
  if (finished) {
    const metrics = node("div", "report-metrics");
    const entries = [];
    if (finished.exercise_reward !== undefined)
      entries.push(["Exercise reward", finished.exercise_reward]);
    entries.push(
      [
        run.kind === "selector-checkpoint"
          ? "Town report score"
          : "Investigation reward",
        result.score ?? "Not graded",
      ],
      ["Supported findings", result.supported_findings?.length ?? 0],
      ["False findings", result.false_findings?.length ?? 0],
      ["Unsupported findings", result.unsupported_findings?.length ?? 0],
    );
    for (const [label, value] of entries) {
      const cell = node("div", "report-metric");
      cell.append(node("strong", "", value), node("span", "", label));
      metrics.append(cell);
    }
    blocks.push(metrics);
    const components = result.reward_components;
    if (components) {
      const box = node("div", "report-formula");
      box.append(
        node("span", "eyebrow", "PROGRAMMATIC REWARD BREAKDOWN"),
        node(
          "p",
          "",
          Number(components.supported_coverage ?? 0).toFixed(3) +
            " supported coverage − " +
            Number(components.false_penalty ?? 0).toFixed(3) +
            " false penalty − " +
            Number(components.unsupported_penalty ?? 0).toFixed(3) +
            " unsupported penalty → " +
            Number(result.score ?? 0).toFixed(3) +
            " reward (clamped to 0–1)",
        ),
      );
      blocks.push(box);
    }
  }
  const submitted = node("div", "report-submission");
  submitted.append(
    node(
      "h3",
      "",
      submission ? "The detective’s submitted report" : "Submission record",
    ),
  );
  if (submission) {
    if (!submission.findings.length)
      submitted.append(
        node(
          "p",
          "report-muted",
          "The detective submitted an empty findings list.",
        ),
      );
    for (const [i, f] of submission.findings.entries()) {
      const claim = node("div", "report-claim");
      claim.append(
        node("span", "report-claim-number", String(i + 1).padStart(2, "0")),
        node("p", "report-assertion", findingDescription(f)),
      );
      const sources = node("div", "report-sources");
      sources.append(node("span", "report-muted", "Cited sources: "));
      if (!f.sources?.length)
        sources.append(node("span", "report-muted", "none"));
      for (const rid of f.sources || []) {
        const record = state.records[rid];
        const button = node("button", "report-source", rid);
        button.type = "button";
        button.title = record
          ? recordLabel(record)
          : "No acquired record with this ID";
        button.addEventListener("click", () =>
          showDetail(
            record ? recordLabel(record) : "Unacquired source",
            record
              ? recordText(record) +
                  (record.recollections
                    ? "\n\n" +
                      record.recollections
                        .map((m) => m.basis + " — " + m.text)
                        .join("\n")
                    : "")
              : "This source ID is not present in the acquired casebook.",
            String(rid) + " · CITED BY THE DETECTIVE",
          ),
        );
        sources.append(button);
      }
      claim.append(sources);
      submitted.append(claim);
    }
    submitted.append(
      node("span", "eyebrow", "SUBMITTED NARRATIVE · UNSCORED"),
      node(
        "p",
        "report-narrative",
        submission.narrative || "No narrative was submitted.",
      ),
    );
    const raw = node("details", "report-raw");
    raw.append(
      node("summary", "", "Exact submitted report JSON"),
      node(
        "pre",
        "",
        JSON.stringify(
          { findings: submission.findings, narrative: submission.narrative },
          null,
          2,
        ),
      ),
    );
    submitted.append(raw);
  } else
    submitted.append(
      node(
        "p",
        "report-muted",
        finished
          ? "No accepted submit_report action is captured in this public trace. A step/time cap can be graded automatically with an empty report; an older shell trace may omit the inner tool action. The recorded verifier result above remains authoritative."
          : "No accepted report has been observed yet.",
      ),
    );
  blocks.push(submitted);
  if (finished) {
    const judgments = node("div", "report-judgments");
    judgments.append(node("h3", "", "What the verifier established"));
    let findings = 0;
    for (const [key, label] of [
      ["supported_findings", "SUPPORTED"],
      ["false_findings", "FALSE"],
      ["unsupported_findings", "UNSUPPORTED"],
      ["unresolved_findings", "UNRESOLVED"],
    ])
      for (const finding of result[key] || []) {
        const item = node("div", "report-verdict " + key);
        item.append(
          node("span", "", label),
          node("p", "", findingDescription(finding)),
        );
        judgments.append(item);
        findings++;
      }
    if (!findings)
      judgments.append(
        node(
          "p",
          "report-muted",
          "No structured findings were established in the recorded grade.",
        ),
      );
    if (result.limitations)
      judgments.append(node("p", "report-muted", result.limitations));
    blocks.push(judgments);
  }
  return blocks;
}
function renderReport() {
  const visible = !!(state.submission || state.finished);
  $("report-panel").classList.toggle("hidden", !visible);
  if (!visible) return;
  const outcome = reportOutcome(state, run?.kind);
  $("report-panel").dataset.outcome = outcome.tone;
  const heading = node("div", "report-heading"),
    copy = node("div");
  copy.append(
    node(
      "span",
      "eyebrow",
      state.finished
        ? "FINAL RESULT · PROGRAMMATIC VERIFIER"
        : "REPORT RECEIVED",
    ),
    node("h2", "", outcome.label),
    node("p", "", outcome.detail),
  );
  heading.append(
    copy,
    node(
      "span",
      "report-seal",
      outcome.tone === "success" ? "✓" : outcome.tone === "failure" ? "!" : "…",
    ),
  );
  $("report-content").replaceChildren(heading, ...reportBlocks());
  if (state.finished && announcedReport !== run.id) {
    announcedReport = run.id;
    toast(
      outcome.label +
        " — submitted report and verifier findings are below the replay controls.",
    );
  }
}
function render() {
  const place = state.scene.place || {};
  if (place.id && place.id !== sceneId) {
    sceneId = place.id;
    $("backdrop").innerHTML = backdrop(sceneId);
    document.querySelector(".stage").classList.remove("scene-change");
    void document.querySelector(".stage").offsetWidth;
    document.querySelector(".stage").classList.add("scene-change");
  }
  $("location-name").textContent = place.name || "The town is waiting";
  $("scene-description").textContent = place.description || "";
  $("reply-count").textContent = state.reply
    ? run?.kind === "reference"
      ? "ACTION " + state.reply
      : run?.kind === "selector-checkpoint"
        ? "DECISION " + state.reply + " / " + run.max_steps
        : "REPLY " + state.reply + " / " + (run?.reply_limit || 40)
    : "PROLOGUE";
  $("activity-text").textContent = state.status;
  $("activity-detail").textContent =
    state.pending?.tool === "model_request"
      ? "The model request is in progress. No private reasoning is shown."
      : state.pending
        ? "Waiting for this action to return. The scene follows actual engine events."
        : state.finished
          ? "The submitted report and verifier findings are visible below the replay controls."
          : live
            ? "The agent is running independently."
            : "The stage reflects the selected replay event.";
  $("decision-note").textContent =
    state.note ||
    "No decision note recorded yet. The detective’s private reasoning is not shown.";
  $("selector-panel").classList.toggle("hidden", !state.selection);
  if (state.selection) {
    $("selector-choice").textContent =
      state.selection.tool +
      " · " +
      (state.selection.probability * 100).toFixed(1) +
      "% among " +
      state.selection.count +
      " candidates";
    $("selector-probability").value = state.selection.probability;
  }
  $("hypotheses").replaceChildren(
    ...state.hypotheses.map((h) => {
      const item = node("div", "hypothesis");
      item.append(
        node("span", "", h.status.replaceAll("_", " ")),
        node("div", "", h.statement),
        node(
          "small",
          "",
          h.sources.length
            ? "Sources: " + h.sources.join(", ")
            : "No acquired source cited.",
        ),
      );
      return item;
    }),
  );
  $("record-count").textContent = Object.values(state.records).filter(
    (r) => recordKind(r) !== "note",
  ).length;
  $("people-count").textContent = Object.keys(state.people).length;
  $("place-count").textContent = state.visited.length;
  $("conversation").classList.toggle("hidden", !state.conversation);
  if (state.conversation) {
    const c = state.conversation;
    $("question-text").textContent = c.question;
    $("answer-text").textContent = c.answer;
    $("witness-name").textContent = state.people[c.pid]?.name || c.pid;
    $("dialogue-basis").textContent =
      [
        ...new Set(c.recollections.map((m) => m.basis.replaceAll("_", " "))),
      ].join(" · ") || "NO FACTUAL RECOLLECTION RELEASED";
  }
  renderActors();
  renderRecords();
  renderTimeline();
  renderInterviews();
  renderReport();
  $("event-count").textContent = position + " / " + events.length;
  $("seek").max = events.length;
  $("seek").value = position;
  $("play-button").textContent = playing ? "Ⅱ" : "▶";
  $("play-button").setAttribute(
    "aria-label",
    playing ? "Pause the viewer" : "Play the viewer",
  );
  $("play-label").textContent = live
    ? playing
      ? "Following live"
      : "Display paused"
    : playing
      ? "Playing recorded events"
      : "Recorded replay";
  $("playback-note").textContent = live
    ? "Playback controls affect the viewer only. The agent continues."
    : run?.kind === "reference"
      ? "Scripted public-tool reference · fixture characters"
      : run?.kind === "selector-checkpoint"
        ? "RL skill checkpoint · prior acquired material · not a whole-case run"
        : "Recorded API detective · actual observations";
  $("stage-caption").textContent = state.finished
    ? reportOutcome(state, run?.kind).label + " · " + state.finished.termination
    : state.pending
      ? actionTitle(state.pending, state)
      : state.conversation
        ? "A conversation, with limits on what each person knows."
        : state.scene.immediately_visible ||
          "Only acquired observations are shown.";
  $("arrival-card").classList.toggle("hidden", opened || live || position > 1);
  $("stop-button").classList.toggle(
    "hidden",
    !live ||
      !!state.finished ||
      (settings.public_demo && !runControls.has(run.id)),
  );
  paintSpeech();
  $("end-button").textContent = state.finished
    ? "Read final report →"
    : "Go to report →";
}
function seek(value, narrate = false) {
  if (!narrate) voice.cancel();
  position = Math.max(1, Math.min(events.length, value));
  state = stateAt(events, position);
  opened = true;
  render();
  const parts =
    narrate && voiceEnabled
      ? dialogueParts(events[position - 1], state.people)
      : [];
  return parts.length ? voice.speak(parts) : Promise.resolve();
}
function pause() {
  playing = false;
  playbackGeneration++;
  voice.cancel();
  if (clock) clearTimeout(clock);
  clock = null;
  render();
}
async function tick() {
  if (!playing || pumpingGeneration === playbackGeneration) return;
  if (clock) clearTimeout(clock);
  clock = null;
  if (position >= events.length) {
    if (!live) pause();
    return;
  }
  const generation = playbackGeneration;
  pumpingGeneration = generation;
  await seek(position + 1, true);
  if (pumpingGeneration === generation) pumpingGeneration = null;
  if (!playing || generation !== playbackGeneration) return;
  const current = events[position - 1];
  const delay = live ? 120 : (current?.action?.tool === "ask" && !voiceEnabled ? 5500 : current?.type === "reply" ? 350 : 1400) / Number($("speed-select").value);
  clock = setTimeout(tick, delay);
}
function play() {
  if (!events.length && !live) return;
  opened = true;
  playing = true;
  playbackGeneration++;
  if (!live && position >= events.length) seek(1);
  render();
  tick();
}
async function loadRun(ident) {
  pause();
  if (stream) {
    stream.close();
    stream = null;
  }
  run = await api("/api/runs/" + encodeURIComponent(ident));
  events = run.events || [];
  position = Math.min(1, events.length);
  state = stateAt(events, position);
  opened = false;
  sceneId = "";
  actorKey = "";
  live =
    run.kind === "live-model" &&
    ["starting", "building", "running", "stopping"].includes(run.status);
  $("run-kind").textContent = kindLabel(run);
  $("case-title").textContent = run.label;
  $("provider-label").textContent = run.model || "Public-tool reconstruction";
  $("status-dot").classList.toggle("live", live);
  $("arrival-label").textContent =
    run.kind === "reference"
      ? "A recorded public-tool reference. No model calls."
      : run.kind === "selector-checkpoint"
        ? "An actual trained-selector checkpoint run. Prior evidence is included."
        : "A recorded model run. Failures are retained.";
  render();
  if (live) {
    playing = true;
    opened = true;
    stream = new EventSource(
      "/api/runs/" +
        encodeURIComponent(ident) +
        "/events?after=" +
        events.length,
    );
    stream.onmessage = (message) => {
      const event = JSON.parse(message.data);
      if (event.seq <= events.length) return;
      events.push(event);
      // Ingest immediately; display through one speech-aware playback pump.
      // Never jump to a newer scene while the current utterance is speaking.
      if (playing) {
        if (pumpingGeneration !== playbackGeneration && !clock) tick();
      } else render();
      if (["finished", "run_error", "stopped"].includes(event.type)) {
        live = false;
        run.status = "finished";
        stream.close();
        stream = null;
        $("status-dot").classList.remove("live");
        $("run-kind").textContent = kindLabel(run);
        if (!playing) render();
      }
    };
    stream.onerror = () => {
      $("activity-detail").textContent =
        "Reconnecting to the local observer feed…";
    };
    if (events.length) seek(events.length);
    else render();
  }
}
function showReport() {
  if (!state.finished) {
    const end = events.findIndex(
      (e) =>
        e.type === "finished" || e.type === "run_error" || e.type === "stopped",
    );
    if (end < 0) {
      toast(
        live
          ? "The investigation is still running."
          : "No final report was recorded.",
      );
      return;
    }
    pause();
    seek(end + 1);
  }
  const outcome = reportOutcome(state, run.kind);
  $("detail-title").textContent = outcome.label;
  $("detail-kicker").textContent =
    "FINAL VERIFIER RESULT · " + state.finished.termination.toUpperCase();
  $("detail-body").replaceChildren(...reportBlocks());
  if (!$("detail-dialog").open) $("detail-dialog").showModal();
}
async function showLibrary() {
  const generation = ++libraryGeneration;
  const data = await api("/api/runs");
  if (generation !== libraryGeneration) return;
  runs = data.runs;
  $("library-list").replaceChildren();
  const level = $("library-level").value;
  for (const item of runs.filter(
    (r) => level === "all" || r.difficulty === level,
  )) {
    const button = node("button", "library-entry");
    button.dataset.runId = item.id;
    button.append(
      node(
        "span",
        "badge",
        kindLabel(item) + " · " + (item.difficulty || "recorded").toUpperCase(),
      ),
      node("strong", "", item.label),
      node(
        "small",
        "",
        (item.description || "Recorded investigation") + " · seed " + item.seed,
      ),
    );
    button.addEventListener("click", () => {
      libraryGeneration++;
      $("library-dialog").close();
      loadRun(item.id).catch((e) => toast(e.message));
    });
    $("library-list").append(button);
  }
  if (!$("library-dialog").open) $("library-dialog").showModal();
}
function configure() {
  pause();
  $("form-error").textContent = "";
  $("configuration-status").textContent = settings.public_demo
    ? "Replays are free to watch. For a live case, enter your own key for your selected provider. It powers both the detective and characters for this run and is not saved by the viewer."
    : settings.characters_configured
      ? "Town character model is configured server-side."
      : "Town character credentials are not configured. Add NPC settings to the server .env before a live run.";
  $("configured-key-input")
    .closest("label")
    .classList.toggle("hidden", !!settings.public_demo);
  $("endpoint-input").readOnly = false;
  $("configured-key-input").disabled = !settings.key_configured;
  $("configured-key-input").checked = !!settings.key_configured && $("endpoint-input").value === settings.defaults.base_url;
  $("configured-key-input").dispatchEvent(new Event("change"));
  updateBriefingPreview();
  $("settings-dialog").showModal();
}
function selectedBriefing() {
  return (
    settings.tasks?.find((task) => task.task_id === $("task-input").value) || {}
  );
}
function updateBriefingPreview() {
  const task = selectedBriefing();
  $("run-budget").textContent = "Practice limit: " + (task.practice_reply_limit || (["intermediate","advanced"].includes(task.difficulty) ? 100 : 40)) + " model replies and 10 minutes from the first request. Official judging remains capped at 40 replies. Playback does not pause the agent.";
  $("briefing-preview-title").textContent = task.name || "Before you begin";
  $("briefing-preview-text").textContent = caseBriefing(task);
}
function showBriefing(startReplay = false) {
  pause();
  const initial = state.opening || {},
    task = {
      ...(settings.tasks?.find((t) => t.task_id === run?.task_id) || {}),
      ...initial.task,
    };
  $("briefing-title").textContent = task.name || run?.label || "Case briefing";
  $("briefing-text").textContent = caseBriefing(task, initial.now || {});
  $("briefing-continue").classList.toggle("hidden", !startReplay);
  $("briefing-dialog").showModal();
}
$("run-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  $("form-error").textContent = "";
  const seed = Number($("seed-input").value);
  if (!Number.isSafeInteger(seed)) {
    $("form-error").textContent =
      "Enter a seed within JavaScript’s exact integer range.";
    return;
  }
  const body = {
    task_id: $("task-input").value,
    seed,
    model: $("model-input").value,
    base_url: $("endpoint-input").value,
    api_key: $("key-input").value,
    use_configured_key: $("configured-key-input").checked,
  };
  $("start-button").disabled = true;
  try {
    const value = await api("/api/runs", {
      method: "POST",
      body: JSON.stringify(body),
    });
    if (value.control_token) runControls.set(value.id, value.control_token);
    $("key-input").value = "";
    $("settings-dialog").close();
    await loadRun(value.id);
    toast("The isolated live investigation is starting.");
  } catch (error) {
    $("form-error").textContent = error.message;
  } finally {
    $("key-input").value = "";
    body.api_key = "";
    $("start-button").disabled = false;
  }
});
$("provider-input").addEventListener("change", () => {
  const provider = settings.providers.find(p => p.id === $("provider-input").value);
  $("key-input").value = "";
  $("endpoint-input").value = provider.id === "configured" ? settings.defaults.base_url : provider.base_url;
  $("model-input").value = provider.id === "configured" ? settings.defaults.model : "";
  $("model-input").placeholder = "Enter a model ID available on this provider";
  $("configured-key-input").checked = false;
  $("configured-key-input").dispatchEvent(new Event("change"));
});
$("endpoint-input").addEventListener("input", () => {
  $("configured-key-input").checked = false;
  $("configured-key-input").dispatchEvent(new Event("change"));
});
$("configured-key-input").addEventListener("change", () => {
  const enabled = $("configured-key-input").checked;
  $("key-field").classList.toggle("hidden", enabled);
  $("key-input").required = !enabled;
});
$("stop-button").addEventListener("click", async () => {
  try {
    await api("/api/runs/" + run.id + "/stop", {
      method: "POST",
      body: "{}",
      headers: runControls.has(run.id)
        ? { "X-Mercy-Run-Control": runControls.get(run.id) }
        : {},
    });
    toast("Stopping this live run.");
  } catch (e) {
    toast(e.message);
  }
});
$("library-button").addEventListener("click", () =>
  showLibrary().catch((e) => toast(e.message)),
);
$("new-button").addEventListener("click", configure);
$("library-level").addEventListener("change", () =>
  showLibrary().catch((e) => toast(e.message)),
);
$("begin-button").addEventListener("click", () => showBriefing(true));
$("play-button").addEventListener("click", () => (playing ? pause() : play()));
$("briefing-button").addEventListener("click", () => showBriefing(false));
$("briefing-continue").addEventListener("click", () => {
  voice.cancel();
  $("briefing-dialog").close();
  play();
});
$("task-input").addEventListener("change", () => {
  voice.cancel();
  updateBriefingPreview();
});
$("listen-preview").addEventListener("click", () =>
  voice.speak(
    [{ speaker: "narrator", target: "briefing-preview-text", text: $("briefing-preview-text").textContent }],
    { interrupt: true },
  ),
);
$("listen-briefing").addEventListener("click", () =>
  voice.speak([{ speaker: "narrator", target: "briefing-text", text: $("briefing-text").textContent }], {
    interrupt: true,
  }),
);
$("stop-voice").addEventListener("click", () => voice.cancel());
$("stop-briefing-voice").addEventListener("click", () => voice.cancel());
$("voice-toggle").addEventListener("change", (event) => {
  voiceEnabled = event.target.checked;
  voice.cancel();
  $("voice-status").textContent = voiceEnabled
    ? "Voice on. Upcoming questions and spoken answers will be read aloud."
    : "Voice off. Text remains available.";
});
$("read-conversation").addEventListener("click", () => {
  pause();
  if (!state.conversation) {
    toast("No interview is shown at this event.");
    return;
  }
  const c = state.conversation;
  voice.speak(
    dialogueParts(
      {
        type: "action",
        action: { tool: "ask", args: { pid: c.pid, question: c.question } },
        observation: { words: c.answer },
      },
      state.people,
    ),
    { interrupt: true },
  );
});
window.addEventListener("pagehide", () => voice.cancel());
$("next-button").addEventListener("click", () => {
  pause();
  seek(position + 1);
});
$("back-button").addEventListener("click", () => {
  pause();
  seek(position - 1);
});
$("seek").addEventListener("input", (event) => {
  const value = Number(event.target.value);
  pause();
  seek(value);
});
$("end-button").addEventListener("click", showReport);
$("scene-button").addEventListener("click", () =>
  showDetail(
    state.scene.place?.name || "The room",
    state.scene.place?.description || "No room description acquired.",
    "CURRENT PUBLIC SCENE",
  ),
);
$("biography-button").addEventListener("click", () =>
  showDetail(
    "Arun’s remembered life",
    state.opening?.your_life?.recollections || "No remembered life recorded.",
    "HIS OWN HISTORY · NOT EVIDENCE OF GUILT",
  ),
);
$("scope-button").addEventListener("click", () =>
  showDetail(
    state.opening?.task?.name || "The assignment",
    (state.opening?.task?.scope || state.opening?.assignment || "") +
      "\n\nFull success: " +
      (state.opening?.task?.success || "Acquire support for the report."),
    "PUBLIC TASK · NO ANSWER CHECKLIST",
  ),
);
$("about-button").addEventListener("click", () =>
  showDetail(
    "An observer, not an oracle",
    "The stage reads public observations only. Undisclosed memories, private planner calls, credentials and provider reasoning fields are excluded.\n\nNotes show the detective’s stated views, not a measurement of internal emotions. Playback does not change the world or its reward.\n\n" +
      (run?.description || "") +
      "\nRun: " +
      (run?.id || "—") +
      "\nKind: " +
      (run?.kind || "—"),
    "HOW THIS VIEW WORKS",
  ),
);
document.querySelectorAll(".close-dialog").forEach((button) =>
  button.addEventListener("click", () => {
    voice.cancel();
    button.closest("dialog").close();
  }),
);
document
  .querySelectorAll("dialog")
  .forEach((dialog) => dialog.addEventListener("close", () => voice.cancel()));
document.querySelectorAll("dialog").forEach((dialog) =>
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) {
      const box = dialog.getBoundingClientRect();
      if (
        event.clientX < box.left ||
        event.clientX > box.right ||
        event.clientY < box.top ||
        event.clientY > box.bottom
      )
        dialog.close();
    }
  }),
);
document.querySelectorAll("[data-filter]").forEach((button) =>
  button.addEventListener("click", () => {
    filter = button.dataset.filter;
    document
      .querySelectorAll("[data-filter]")
      .forEach((b) => b.classList.toggle("active", b === button));
    renderRecords();
  }),
);

const tourSteps = [
  ["Welcome to Mercy House", "Watch a recorded investigation for free, or bring a provider API key to start a live case. You are observing the detective; playback controls never direct its decisions.", "library-button"],
  ["Read the case first", "The case briefing gives you the public starting situation and assignment. Hidden answers stay outside the viewer. You can listen to this briefing before opening the case.", "briefing-button"],
  ["Follow the investigation", "The scene changes as the detective travels. Interviews show the actual question and answer. The notebook keeps every exchange already observed, including follow-up questions.", "conversation"],
  ["Listen at your pace", "Turn on Voice mode to hear dialogue. Playback waits until speech ends. Words highlight when your browser supplies word-boundary events. Characters use consistent installed voices; devices with few voices may share them.", "voice-toggle"],
  ["Check the sources", "The evidence tray contains only acquired material. Click a record to read it. A witness statement or a letter can still be wrong; the detective must test its claims.", "evidence-list"],
  ["Read the result", "Go to report shows the submitted conclusions and the rule-based verifier’s supported, false and unsupported findings. Recorded successes and failures are both retained. Scripted references and training checkpoints are labeled.", "end-button"],
  ["Try your own model", "New investigation lets you choose the case, provider, model ID and seed. A public live run uses your key for the detective and characters. Keys are cleared from the form and are never included in replays. Start with Level 1; longer cases remain difficult.", "new-button"],
];
let tourPosition = 0;
function finishTour() {
  $("tour-dialog").close();
  document.querySelectorAll(".tour-target").forEach(el => el.classList.remove("tour-target"));
  try { localStorage.setItem("mercy-tour-v1", "seen"); } catch {}
}
function renderTour() {
  const [title, copy, target] = tourSteps[tourPosition];
  $("tour-title").textContent = title;
  $("tour-copy").textContent = copy;
  $("tour-counter").textContent = "QUICK TOUR · " + (tourPosition + 1) + " / " + tourSteps.length;
  $("tour-back").disabled = tourPosition === 0;
  $("tour-next").textContent = tourPosition === tourSteps.length - 1 ? "Explore the case →" : "Next →";
  document.querySelectorAll(".tour-target").forEach(el => el.classList.remove("tour-target"));
  const el = $(target);
  if (el && !el.classList.contains("hidden")) { el.classList.add("tour-target"); el.scrollIntoView({ block: "center", behavior: "smooth" }); }
}
$("tour-button").addEventListener("click", () => {
  pause(); tourPosition = 0; renderTour(); $("tour-dialog").showModal();
});
$("tour-next").addEventListener("click", () => {
  if (tourPosition === tourSteps.length - 1) finishTour();
  else { tourPosition++; renderTour(); }
});
$("tour-back").addEventListener("click", () => { if (tourPosition) { tourPosition--; renderTour(); } });
$("tour-skip").addEventListener("click", finishTour);
$("tour-dialog").addEventListener("close", () => {
  document.querySelectorAll(".tour-target").forEach(el => el.classList.remove("tour-target"));
});

async function boot() {
  for (const id of [
    "voice-toggle",
    "listen-preview",
    "listen-briefing",
    "read-conversation",
  ])
    $(id).disabled = !voice.supported;
  $("voice-status").textContent = voice.supported
    ? "Voice off. Enable it to hear public dialogue. Voices depend on your browser and device."
    : "Speech is unavailable in this browser. All text remains readable.";
  $("detective-portrait").innerHTML = portrait("detective");
  $("backdrop").innerHTML = backdrop("archive");
  try {
    settings = await api("/api/config");
    const data = await api("/api/runs");
    runs = data.runs;
    $("task-input").replaceChildren(
      ...settings.tasks.map((task) => {
        const option = node("option", "", task.name + " · " + task.difficulty);
        option.value = task.task_id;
        return option;
      }),
    );
    $("provider-input").replaceChildren(...settings.providers.map(p => {
      const option = node("option", "", p.name); option.value = p.id; return option;
    }));
    $("model-input").value = settings.defaults.model;
    $("endpoint-input").value = settings.defaults.base_url;
    if (runs.length) await loadRun(runs[0].id);
    else {
      $("arrival-label").textContent =
        "No recorded cases yet. Start a live investigation.";
      $("begin-button").textContent = "Configure a detective →";
      $("begin-button").addEventListener("click", configure);
    }
    try { if (!localStorage.getItem("mercy-tour-v1")) toast("New here? Choose Quick tour at the top for a guided introduction."); } catch {}
  } catch (error) {
    toast(error.message);
    $("stage-caption").textContent = "The local viewer service is unavailable.";
  }
}
boot();
