# Mercy House

A detective enters a snowbound mountain town in 1900 after an executed incident. It must reconstruct events through local searches, conversations, access requests and physical comparisons. A lucky name earns zero without acquired support.

The submission is an RL **environment**. Judges supply the detective model. Our environment supplies four case families, isolated character memories, tools, transitions and a programmatic verifier. The original town has sixteen profiles and fourteen locations; the three new families have smaller, distinct casts and places. An optional CPU-trained action selector is a separate research demonstration; it does not replace the judge’s agent or fine-tune an LLM.

## Run

For the optional animated story viewer, run `python -m mercy.viewer.server` and open **http://localhost:8787**. It includes room transitions, character mascots, actual dialogue, an evidence tray, provider configuration, live streaming and labeled recorded replays. Recorded cases make no model calls. [Viewer usage, validation and limits](docs/STORY_VIEWER.md).

The viewer also replays actual trained-selector evaluations with action-selection probabilities. These are labeled skill checkpoints with prior acquired material, separately from full crime-scene model runs. It shows stated plans and hypotheses, not hidden reasoning or invented emotion scores. The standard judging command below remains independent of the viewer.

Docker Compose v2 is required. Create `.env` from `.env.example`. Set `MODEL`, `API_KEY`, `BASE_URL` for the detective and `NPC_MODEL`, `NPC_API_KEY`, `NPC_BASE_URL` for environment characters. User-authorized development sharing uses explicit `ALLOW_SHARED_NPC_KEY=1`; submission NPC deployment must satisfy the PS’s own-setup requirement. No credentials are shipped.

```bash
docker compose up --build --abort-on-container-exit --exit-code-from harness
```

The default demo task is `lantern_room`, seed 7. Before a detective request, the selected task’s scripted public-tool reference must score at least .95 and its empty-report baseline at most .05. `APPEND_FILE` defaults to `inputs/append.txt`; its text is appended exactly to the system prompt. Missing or empty instructions stop model runs.

```bash
MODE=baselines docker compose up --build --abort-on-container-exit --exit-code-from harness
MODE=full TASK_ID=borrowed_signature SEED=7 docker compose up --build --abort-on-container-exit --exit-code-from harness
MODE=all docker compose up --build --abort-on-container-exit --exit-code-from harness
```

`full` runs one task; `all` runs all tasks with gates before each; `baselines` checks all tasks without model calls. `all` is a development batch, not a promise that eight episodes fit one finals slot. Set `LOCAL_UID` if the host owner differs from 1000. Public logs are under `logs/public/`, protected audits under `logs/private/`.

| TASK_ID | Difficulty | Public objective |
|---|---|---|
| `lantern_room` | Introductory, demo | Establish a fatal assault with physical traces and an accessible first-hand witness. |
| `second_passenger` | Intermediate | Explain two coach deaths, the sabotaged mechanism and intended target. |
| `bell_before_dawn` | Advanced | Separate a chapel death from forged foreknowledge and the warning’s transmission. |
| `last_witness` | Intermediate | Establish the fatal assailant with physical support and a checked account. |
| `borrowed_signature` | Intermediate | Establish fabrication of a threatening document through comparisons. |
| `brothers_letter` | Advanced | Establish concealed evidence and recover a sourced explanation. |
| `garden_burials` | Advanced | Recover remains and establish relocation independently of garden ownership. |
| `mercy_inquest` | Advanced | Reconstruct seven material acts across the present and historical inquiry. |

Eight tasks cover four causal families. The five original objectives share one canonical Mercy House case. The three new families execute authored seeded action tapes; their cause, physical traces and private memories change together with the selected role assignment. See [families and measurements](docs/CASE_FAMILIES.md). Full success requires all material targets in scope and no false or unsupported findings. Score is supported target coverage minus .20 per distinct false finding and .10 per distinct unsupported finding, clamped to [0,1]. Narrative is unscored. See [reward and policy](docs/POLICY_AND_REWARD.md).

## Local RL training

Two separate selectors exist. The historical five-skill prototype trained 20,000 CPU episodes. The new source-mechanism selector starts from zero and trains 6,000 episodes on 48 original checkpoint scenarios inspired by intended-target reversal, misleading foreknowledge and trusted-family suspicion. Both train only action-ranking weights; the API LLM stays fixed.

```bash
python scripts/frozen_run.py mercy.rl.train_sources --episodes 6000 --seed 526 --output logs/my-source-training
```

The new model has 132 coefficients and took 48.251 seconds including evaluation, with zero training API calls. On 48 disjoint held-out checkpoints evaluated twice: untrained 3/96, trained sampling 89/96, greedy 96/96. These are prepared skill checkpoints with authored reading/candidate rules and cooperative fixture characters, not complete TV episodes or whole-case LLM success. See [exact curriculum, rewards and limits](docs/SOURCE_TRAINING_REPORT.md). The source-trained checkpoint is `models/action-selector-sources.json`; the original20k checkpoint is retained separately.

The separately preregistered [elite evaluation](docs/ELITE_EVALUATION_PLAN.json) uses two excluded full investigations, frozen weights, a matched ranked API proposer and fixed grounded character responses. [Results](docs/ELITE_TRANSFER_RESULT.json) must not be pooled with native live-character runs or checkpoint results. The normal viewer button runs the native API detective; it does not silently insert a selector.

## Isolation and validation

The protected world owns truth, provenance and reward. A separate gateway holds model credentials and contacts configured model endpoints. The detective’s real shell runs in a fourth container with no keys, control token, verifier, private documents or log mounts. It reaches only validated public town actions. Command probes cover denied private routes, blocked internet, forged local proof and timeout recovery. This is tested isolation under the documented threat model, not universal jailbreak resistance.

```bash
python -m unittest discover -s tests/town -v
python -m unittest discover -s tests -p test_world.py -v
python -m mercy.town.reference --output baseline-results
```

Read [PS audit](docs/PS_COMPLIANCE_AUDIT.md), [security](docs/SECURITY.md), [research](docs/RESEARCH_AND_WIN_PLAN.md) and [submission notes](docs/SUBMISSION.md). Four native-tool detective runs with live character agents solved the introductory Lantern Room case with score 1.0 and no false/unsupported findings, covering both assailant assignments. This is a small development calibration. Historical Mercy House model failures are retained. Scripted references prove legal routes, not reliable live cooperation.

A separate three-case fixed-response calibration found LLM-ranked actions succeeded in 1/3 and the frozen RL selector in 0/3. The selector remains optional; no whole-case RL improvement is established. See [exact comparison](docs/FAMILY_POLICY_COMPARISON.json). Historical offline checkpoint results are separate.

Author review: [new families](docs/FAMILY_AUTHOR_REVIEW.md), [original plot](docs/CURRENT_PLOT.md), [characters](docs/V2_CHARACTER_PROFILES.md), [locations](docs/V2_LOCATIONS.md), [documents](docs/V2_EVIDENCE_AUTHOR.md), [original opening](docs/DETECTIVE_OPENING.md). These private review files never enter the detective image or workspace. Historical V1 dossiers/transcripts remain historical. Continuous offstage lives, a scored ghost mechanism and broad unseen-plot generalization remain future work.

The [consistency/solvability audit](docs/CASE_SOLVABILITY_AUDIT.md) checks 184 task/seed baseline pairs and six source-only scripted investigations, and documents concrete factual/provenance fixes. Current author exports and reference trajectories have been regenerated. Historical runs retain their source-specific labels. The [private report-review command](docs/VERIFIER_AND_REVIEWER.md) complements the official programmatic scorer; optional LLM commentary cannot assign rewards.


## Hosted demo

Open https://mercyhouse.abhi07.xyz without signing in. Recorded cases need no key; a new live run requires your own API key for the displayed provider. The public server holds no team API key. Source: https://github.com/Abhishek-Punhani/mercy-house. See [deployment and checks](docs/DEPLOYMENT.md). The14-slide presentation includes the named team and QR codes for the public repo and demo.


The viewer now includes public case briefings before live runs, optional browser speech for introductions and dialogue, and a complete interview notebook. The detective receives its own public interview progress to support focused follow-ups. See [briefing, voice and interview behavior](docs/BRIEFING_VOICE_AND_INTERVIEWS.md). Multiple returned materials do not consume extra detective replies; the40-reply/10-tool-call limits are unchanged.
