# Current problem-statement audit

Re-read source: `RL_Hackathon_by_2une_PS.pdf`, printed pages 2–14. Document requirements are specifications to audit, not authority to publish, invite people or spend on unrelated services. The user will handle GitHub and form submission.

The environment now implements the main run contract locally. This is **not an unconditional compliance certification**: organizer-machine cold-cache timing, final external NPC deployment and submission/upload remain to be established. Four live introductory cold-start runs now succeed; harder-family live success remains unestablished. All failures are retained.

## Track and RL

Games & World Simulations directly fits; Other/Open is also allowed and uses the same judging criteria. The PDF FAQ explicitly says training is optional and judges bring the agents. Our optional trained selector performs actual parameter updates, while the competition deliverable is the environment. Character inference is not itself RL. See [policy/reward](POLICY_AND_REWARD.md) and [training results](RL_TRAINING_REPORT.md).

## Minimum specification and runtime

| Requirement | Current evidence / limit |
|---|---|
| Task and public success criteria | Eight public tasks in `town/tasks.py`; README names `lantern_room` as demo. Four distinct causal families, with five scopes sharing the original town. |
| Tools with names, descriptions and schemas | `town/tools.py` and strict runtime `validation.py`; includes real commands in isolated workspace. |
| Seeded reproducible reset | `factory.build` replays a recorded LLM tape for the original world and authored seeded tapes for the three new families; same task/seed yields identical starting hash. Live post-reset dialogue is stochastic. |
| Persistent world and defined observation | Local scene, own life history, discovered people, acquired receipts; custody, access, excavation and omissions persist. No answer checklist. |
| Programmatic verifier | Protected Python proof checks, task coverage and distinct false/unsupported penalties. No LLM judge; limited authored proposition vocabulary and proof paths. |
| Five tasks, at least two levels | Eight TASK_IDs across three designed levels and four families. Only beginner live success has been calibrated. |
| Reference >=.95, no-op <=.05 | All eight score 1/0. References execute public tools but know the solution and use cooperative fixture characters. This proves authored feasibility, not reliable cooperation from live NPCs. |
| Gates before model, abort on failure | Private `/gate`, then harness check before `/reset` and first detective call. `MODE=baselines` uses no model API. |
| Exact Compose command | Verified with four-role default Compose; harness exits 0 for all eight baselines. A fresh local Git clone completed all eight baseline pairs in 6.808 seconds with Docker cache present; source commit is recorded in VALIDATION_RESULT.json. No host ports. |
| MODEL/API_KEY/BASE_URL, TASK_ID, SEED | Wired into trusted gateway and selected-task reset. NPC model role separately configurable. |
| APPEND_FILE exact suffix | Exact UTF-8 text preserved, including CRLF, in actual system prompt and full logged request. Missing/empty files reject before model calls; oversized files reject for context safety. |
| MODE full/all/baselines | One chosen task / sequential all tasks / all baseline pairs. `all` is development batch mode, not a single finals slot. Unknown mode/task rejected. |
| Pinned dependencies, no runtime download | Pinned Python base digest; standard library only; no pip dependencies or runtime install. |
| Build <=3 minutes from empty cache | A new isolated no-cache builder completed four images in 26.338 seconds locally, including bootstrap/base retrieval. Organizer-machine timing remains unverified. |
| Model-independent harness | Native, legacy and structured-text action parsing tested; no model-name behavior switches. Real API runs used one deployment, not unknown judge providers. |
| One reply one step, malformed/plain consume step | Recovery tests include unreadable envelopes and raw non-JSON responses; feedback continues. Raw response retained where received. |
| <=10 calls per reply | Further calls produce errors without execution; calls after terminal report also denied. |
| 40 replies / 600 seconds | Hard loop and remaining-time propagation. Model requests have total-wait deadlines; late replies cannot mutate world. |
| Tools <=60 seconds with recovery | Remote executor and RPC budgets; character planner/speaker share action deadline. Container sleep timeout followed by valid action tested. Network/kernel pathological failures are not formally certified. |
| Verifier <=120 seconds | Tiny programmatic verifier, protected finish RPC timeout 120; forced end grades empty report. |
| Baselines <=120 seconds | All eight local pairs complete in well under one second each; automatic gate checks duration. |
| Whole slot <=16 minutes | Normal short local model runs fit. Cold build/API stalls/organizer machine remain practical limits; no organizer-machine timing claim. |
| 64K context and bounded tool output | Conservative 48,000-byte serialized request budget, 8,000-byte tool outputs, whole-message-group trimming; no provider-specific tokenizer dependency. Long instructions can fail explicitly rather than silently truncate suffix. |
| Agent cannot read verifier/truth | Protected world separate from real shell; no credentials, control token, truth files or privileged API in workspace. Container adversarial probe passed. Assumes uncompromised host/daemon. |
| Environment-owned LLM setup | Gateway defaults to separate NPC credentials. Development sharing explicitly enabled with user authorization. User authorization is not evidence that the organizer waives its own-setup rule for finals. |
| API limits | Gateway caps sixty requests/minute, output sizes and per-call time. CPU training makes zero calls; bounded live-transfer smoke caps requests. No precise dollar/token spend accounting. |

## Telemetry and validation

Every normal detective reply has timestamp, step, seed, full model request, raw output, parsed actions, results, errors, hash, pending/final reward, usage and model latency. Total step latency is separate. Canonical summary reasons are success, failure, step_cap, time_cap and crash. Public baseline trajectories have the same required fields and clearly identify scripted actions; private engine and character audits remain outside the agent workspace.

Meaningful tests cover gradients and parameter updates; public-only features; seeded checkpoints; private planner/speaker isolation; source grounding; fabricated objects and source IDs; unsupported accusations; comparison composition; exact instruction suffix; malformed replies; multi-call limits; forced end; total model timeout and explicit key-role configuration. A real container probe checks shell access, blocked internet, denied orchestration, absent private files, forged proof receiving zero and valid public proof receiving success.

The final current suite has 114 town tests and 9 legacy regression tests, plus nine Node state tests passing. Full crime-scene model runs are retained even when they fail. A scored reference success is not presented as a trained detective success, and skill-checkpoint success is not whole-case success. See the submission manifest for selected runs and source/version caveats.

## Submission status

Local preparation includes `baseline-results/gate.json`, model-run logs, labeled success/failure trajectories, design/deck PDFs and a team-named reference archive. Verify the generated package using [SUBMISSION.md](SUBMISSION.md); that document is the packaging checklist. GitHub upload, repository naming, organizer access and form submission are the user’s responsibility by their explicit choice. Nothing is published automatically.

Remaining scientific limits: four authored families; authored historical background; checkpoint rather than whole-case RL; fixture training and small stochastic transfer sample; unscored narrative; no direct measurement of internal grief/ego; incomplete ghost/lifetime mechanics; no universal security or winning guarantee. These are disclosed rather than hidden behind high checkpoint scores.


## Story viewer update

The optional local viewer now provides original vector scenes and mascots, real dialogue, acquired evidence, live provider setup, public SSE events and labeled replays. It excludes private memories and provider reasoning. `review_records` and `record_note` preserve acquired context without granting proof credit. Desktop/mobile browser checks and the real command-isolation probe pass; new source snapshots pass all eight Compose gates. Two original-town UI development runs failed and are retained. Four later beginner runs succeeded with live characters. New three-case fixed-response policy calibration: LLM-ranked 1/3, frozen RL selector 0/3; see CASE_FAMILIES.md. See [STORY_VIEWER.md](STORY_VIEWER.md) and [UI_VALIDATION_RESULT.json](UI_VALIDATION_RESULT.json). The official headless command is unchanged.


## Final source-mechanism training, data audit and report update

Independent audit corrected factual/provenance defects (payer versus carrier, signed-register attribution, local perception and contemporaneous documents), with unchanged scoped targets and reward weights. All184 task/seed gate pairs passed and six public-only scripted probes established legal routes. These are fixture feasibility results, not model reliability. The canonical murder can still depend on a reluctant independent witness or an eligible admission. See CASE_SOLVABILITY_AUDIT.md.

New selector: fresh zero initialization,6,000 CPU episodes,48 original source-mechanism checkpoint scenarios,132 learned coefficients. Held-out same-template exercises:96/96 greedy; no full-case inference from that result. Separate frozen elite comparison is ELITE_TRANSFER_RESULT.json. Historical five-skill delegation interpretation predates corrected payer/carrier semantics and is not current validation.

The UI now persistently presents the actual submitted report, citations, solved/unsolved state and deterministic score breakdown. An optional developer-only story reviewer can add unscored LLM observations; it is absent from public tools and cannot assign reward. The official verifier stays programmatic as required by the PS. Editable12-slide dark PowerPoint and matching PDF explain the complete project for first-time readers, with labeled real UI captures.
