# Case introductions, optional speech and fuller interviews

The live-run setup now shows a short case introduction before its Begin button. It changes with the selected task, can be read aloud and starts no model request by itself. Recorded cases have a Case briefing button and an introduction before Open case starts playback. Introductions are public setup, not answer dossiers: no killer, hidden witness knowledge, required source list or free evidence is supplied. The real investigator's remembered life and initial scene remain its starting information.

Voice mode reads the detective's question and the character's actual spoken reply. A separate button can reread the conversation on screen. It uses the browser's speech service and does not call the model provider for audio. Voices, sound quality and availability depend on the browser/device. Text stays available if speech fails or is unavailable. No microphone is used and provider reasoning, private memories and undisclosed recollections are not narrated. Browser speech may use the device/browser's configured speech service; this is not a claim that all voices run offline.

Recorded playback waits for a narrated interview to finish before moving on. Pausing, seeking, changing runs or stopping audio cancels queued speech. Live narration follows public interview events; pausing the viewer/audio does not pause the independently running detective. The interview notebook keeps every observed question and answer grouped by person, instead of showing only the latest entries in the short timeline.

## What counts as a reply

One detective model response consumes one of the40 replies. That response may contain up to10 tool calls. Several documents or custody handovers returned by one tool call are one result in that same reply, not additional detective replies. Internal character planner/speaker calls also do not consume detective replies, although they take time and provider requests.

Several acquired records can be shown together in `ask.show`. The model can batch independent tool actions when their arguments are already known. If its next question depends on the answer it just received, it must use another model response to decide that question. Calling an unlimited hidden detective loop inside one tool would defeat the stated budget, so we do not do that. The40-reply,10-call and600-second limits remain unchanged.

## Interview behavior

There is no one- or two-question cap. The investigator guidance now asks for relevant follow-up on timeline, vantage point, source of an account and specific inconsistencies, and for revisiting a person after new evidence. It explicitly avoids rewarding or requiring repetitive questions when a sufficient account already exists.

Each new model request contains a small summary of its received interview history: question count, distinct questions, acquired records shown, actual public answer and released recollection count. It contains no hidden trust, fear, guilt or memory-eligibility information. The character's private planner receives additional derived topic labels for timeline, viewpoint, information source and clarification, rather than the raw hostile question. Disclosure eligibility, physical truth and scoring rules are unchanged.

This is improved prompting, bookkeeping and presentation, not a new policy-training run or a guarantee that every language model will interview well. Historical checkpoint/elite measurements retain their original source versions. Deep questioning is useful when it resolves a real gap; question count alone earns no reward and is not proof of guilt.

## Verification

Regression tests verify more than two questions are legal, several material handovers and tool calls still occupy one detective reply, interview summaries contain only received information, and briefings do not reveal the named solutions. Browser/Node checks cover briefing selection before model calls, spoken question/answer ordering, cancellation, unsupported speech fallback, interview history and mobile layout. Speech lifecycle tests use a mock voice service; they do not certify audibility on every computer. See BRIEFING_VOICE_VALIDATION.json and the native run evidence when present.

Browser API references: [SpeechSynthesis](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis), [SpeechSynthesisUtterance](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesisUtterance).
