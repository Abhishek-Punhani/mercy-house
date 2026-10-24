# The living casebook — local story viewer

The viewer is an optional presentation and debugging companion. The standard judge command and headless harness continue independently. No hosted site, remote repository or public service is created.

Start from the project root with Python 3.10+ and open the printed address:

```bash
python -m mercy.viewer.server --port 8787
```

Open **http://localhost:8787**. Recorded cases need no API calls or Docker. For a new live investigation Docker must be running and the server’s ignored `.env` must configure the character agents. The detective can use a different OpenAI-compatible HTTPS endpoint, deployment name and key supplied through the form.

## What works

- Fourteen original vector room/landscape backdrops; location transitions follow actual movement.
- Character mascots appear after public discovery. During an interview the detective and witness move into focus with their actual question and answer.
- A left-hand casebook shows current activity, explicitly stated notes and hypotheses. No private reasoning or invented emotion scores are displayed.
- An evidence tray contains acquired material, recollections, comparisons and custody records. Documents open with their actual text and source basis.
- Play, pause, seek, step and speed controls for recorded events. During a live run these controls pause the display only; a separate Stop button ends the containers.
- A provider/task/seed form starts the isolated standard detective harness. The selected task’s reference/no-op gate runs first. Keys are not returned in API responses, written to viewer configuration files, stored in browser storage or copied into source snapshots.
- Live server-sent events include real tool starts/results, public decision notes and model-request status. CLI town calls are recorded too. Provider reasoning fields and raw request messages are excluded from the viewer stream.
- A final report distinguishes supported, false and unsupported findings. Failed models remain failed.
- Recorded CPU-selector evaluations show the measured probability of selecting an action. It is explicitly not a probability of guilt. Checkpoint exercise reward and broader Town score are separate.

## Replay provenance

The library includes four public-tool family references, fifteen actual API detective runs (ten failures and five beginner successes), and three actual trained-selector checkpoint evaluations. It defaults to an actual beginner success. Difficulty filters select introductory, intermediate, advanced and training replays. Reference and model replays are labeled separately. Selector checkpoints begin with previously acquired public material; they are not fresh crime-scene solutions. New local live runs become saved replays after completion or server restart.

Regenerate bundled replays with `python scripts/build_viewer_replays.py`. This reads public trajectories from the prior submission archive, current reference execution and the recorded selector evaluations. It never reads private actor audits or world snapshots.

## Investigation improvements

`review_records` lets the detective reread up to twelve genuinely acquired records without travelling back after context trimming. `record_note` stores concise stated plans and hypotheses; a note cannot become proof or discover material. The harness retains a public acquired-record index and current task scope. Witness dialogue instructions distinguish voluntary withholding from a factual negative observation. These changes do not relax disclosure eligibility, fabricate admissions or lower reward requirements.

Two additional full detective runs were recorded during this work: seeds 23 and 24, both Last Witness. Both failed with false accusations and score 0. The second used revised withholding dialogue and more tool calls per reply, but this is not evidence of a solving improvement. They are development runs, not a controlled paired experiment. Offline selector 147/160 and prior live checkpoint 2/5 results remain historical measurements against their recorded source versions. No new policy training is claimed for this UI. The later family expansion added four live beginner successes; it does not change those original-town failures. A separate controlled comparison is documented in CASE_FAMILIES.md.

## Separation and limits

The loopback server is trusted administration on the host, with authority to start only its own fixed Compose projects. It does not run a user-supplied command. Judge credentials never silently replace the town’s credentials: character configuration is resolved separately from the original server settings. Live builds snapshot only source/Docker files into the ignored run folder; `.env` is excluded. Keys reach the configured model-gateway container through process environment and its temporary container configuration. Run cleanup removes the containers.

The detective workspace has no viewer source, private logs, browser, host-loopback listener, provider key or Docker socket. The viewer itself serves only explicit assets and public event endpoints. Host checks, same-origin POST checks and an ephemeral CSRF token protect run controls. No arbitrary file or private-world endpoint is exposed. Conversation/document text is rendered as text, not executable HTML.

This is a local companion, not a multi-user internet service. Bind remains 127.0.0.1. Restarting the server preserves public replay history; a process interrupted outside normal cleanup can leave a Compose project requiring local cleanup. One concurrent live investigation is allowed. Three additional causal families are now implemented. Complete live solving is demonstrated only in the small beginner calibration; reliable solving across families remains research work.

## Verification

Python tests cover projection canaries, provider-role separation, endpoint validation, key redaction, frozen-source exclusion, private-path denial, CSRF/origin rejection, SSE and casebook proof integrity. Node tests cover replay causality, acquired-record retention and observed presence. Chrome browser checks exercise dialogue, evidence details, verdict labels, provider-key absence, RL probability labels and mobile layout. The current container command-isolation probe also passes.

Development browser checks use a dedicated local headless Chrome instance and `node --experimental-websocket scripts/qa_viewer.mjs`; these are not runtime dependencies. Raw results and screenshots are under ignored `logs/`; the compact validation report and representative screenshot are in `docs/`.


## Persistent final report

Completed runs now show a persistent solved/unsolved/not-graded panel beneath the playback controls. It contains the actual accepted submission, cited acquired sources, narrative, exact report JSON, programmatic findings and reward breakdown. Forced-end and missing-submission runs have explicit notices. Checkpoint exercise reward and full Town score remain separate. `assisted` is rendered as knowingly facilitating the fatal incident; `aided` is help given to the victim. No expected-answer list or private world is exposed. See UI_REPORT_IMPROVEMENTS.md.
