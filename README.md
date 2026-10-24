# Mercy House

A detective enters a snowbound mountain town in 1900 after an incident executed by character agents. It must reconstruct events through local searches, conversations, access requests and physical comparisons. A lucky name earns zero without acquired support.

The submission is an RL **environment**. Judges supply the detective model. Our environment supplies sixteen character profiles, fourteen locations, isolated character memories, tools, transitions and a programmatic verifier. An optional CPU-trained action selector is a separate research demonstration; it does not replace the judge’s agent or fine-tune an LLM.

## Run

For the optional animated story viewer, run `python -m mercy.viewer.server` and open **http://localhost:8787**. It includes room transitions, character mascots, actual dialogue, an evidence tray, provider configuration, live streaming and labeled recorded replays. Recorded cases make no model calls. [Viewer usage, validation and limits](docs/STORY_VIEWER.md).

The viewer also replays actual trained-selector evaluations with action-selection probabilities. These are labeled skill checkpoints with prior acquired material, separately from full crime-scene model runs. It shows stated plans and hypotheses, not hidden reasoning or invented emotion scores. The standard judging command below remains independent of the viewer.

Docker Compose v2 is required. Create `.env` from `.env.example`. Set `MODEL`, `API_KEY`, `BASE_URL` for the detective and `NPC_MODEL`, `NPC_API_KEY`, `NPC_BASE_URL` for environment characters. User-authorized development sharing uses explicit `ALLOW_SHARED_NPC_KEY=1`; submission NPC deployment must satisfy the PS’s own-setup requirement. No credentials are shipped.

```bash
docker compose up --build --abort-on-container-exit --exit-code-from harness
```

The default demo task is `last_witness`, seed 7. Before a detective request, the selected task’s scripted public-tool reference must score at least .95 and its empty-report baseline at most .05. `APPEND_FILE` defaults to `inputs/append.txt`; its text is appended exactly to the system prompt. Missing or empty instructions stop model runs.

```bash
MODE=baselines docker compose up --build --abort-on-container-exit --exit-code-from harness
MODE=full TASK_ID=borrowed_signature SEED=7 docker compose up --build --abort-on-container-exit --exit-code-from harness
MODE=all docker compose up --build --abort-on-container-exit --exit-code-from harness
```

`full` runs one task; `all` runs all tasks with gates before each; `baselines` checks all tasks without model calls. `all` is a development batch, not a promise that five episodes fit one finals slot. Set `LOCAL_UID` if the host owner differs from 1000. Public logs are under `logs/public/`, protected audits under `logs/private/`.

| TASK_ID | Difficulty | Public objective |
|---|---|---|
| `last_witness` | Introductory, demo | Establish the fatal assailant with physical support and a checked account. |
| `borrowed_signature` | Intermediate | Establish fabrication of a threatening document through comparisons. |
| `brothers_letter` | Advanced | Establish concealed evidence and recover a sourced explanation. |
| `garden_burials` | Advanced | Recover remains and establish relocation independently of garden ownership. |
| `mercy_inquest` | Advanced | Reconstruct seven material acts across the present and historical inquiry. |

These are different objectives over one canonical case, not five independent murder plots. Full success requires all material targets in scope and no false or unsupported findings. Score is supported target coverage minus .20 per distinct false finding and .10 per distinct unsupported finding, clamped to [0,1]. Narrative is unscored. See [reward and policy](docs/POLICY_AND_REWARD.md).

## Local RL training

```bash
python scripts/frozen_run.py mercy.rl.train_skills --episodes 20000 --seed 145 --output logs/my-training
```

CPU only, standard-library Python, no API calls. REINFORCE trains a linear softmax selector across document comparison, witness selection, statement checking, navigation and supervised delegation. A public proposer supplies candidate arguments; the selector learns which to execute. See [actual training and transfer results](docs/RL_TRAINING_REPORT.md). Live evaluations use API calls and start at skill checkpoints, rather than a complete crime scene.

## Isolation and validation

The protected world owns truth, provenance and reward. A separate gateway holds model credentials and contacts configured model endpoints. The detective’s real shell runs in a fourth container with no keys, control token, verifier, private documents or log mounts. It reaches only validated public town actions. Command probes cover denied private routes, blocked internet, forged local proof and timeout recovery. This is tested isolation under the documented threat model, not universal jailbreak resistance.

```bash
python -m unittest discover -s tests/town -v
python -m unittest discover -s tests -p test_world.py -v
python -m mercy.town.reference --output baseline-results
```

Read [PS audit](docs/PS_COMPLIANCE_AUDIT.md), [security](docs/SECURITY.md), [research](docs/RESEARCH_AND_WIN_PLAN.md) and [submission notes](docs/SUBMISSION.md). Full detective model runs so far have failed; the verifier correctly withheld success. Reference success establishes a legal proof route, not reliable LLM success. A fresh no-cache local build took 23.208 seconds; timing on the organizer’s machine remains unverified.

Author review: [plot](docs/CURRENT_PLOT.md), [characters](docs/V2_CHARACTER_PROFILES.md), [locations](docs/V2_LOCATIONS.md), [documents](docs/V2_EVIDENCE_AUTHOR.md), [exact opening](docs/DETECTIVE_OPENING.md). Historical V1 dossiers and transcripts remain labeled historical; their easy scores are not current evidence. Continuous offstage lives, a scored ghost mechanism and unseen-plot generalization remain future work.
