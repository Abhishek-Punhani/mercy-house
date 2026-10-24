# Completed five-skill local policy training

The final selector was trained on this laptop’s CPU: **20,000 episodes in 530.243 seconds**, with **460 learned coefficients**, zero model API calls and no GPU. LLM weights stay fixed. Checkpoint: [action-selector-final.json](../models/action-selector-final.json). Machine-readable result: [RL_TRAINING_RESULT.json](RL_TRAINING_RESULT.json).

## Measured checkpoint performance

Final run `logs/selector-final-curriculum-145`, seed 145. Eighty training checkpoints and eighty disjoint evaluation checkpoints, sixteen per skill; stochastic and greedy evaluation run each held-out checkpoint twice. These repetitions are correlated and are not 160 independent case plots. Candidate order is shuffled. The saved checkpoint is the final fixed-budget model, not the best of the evaluated checkpoints.

| Policy | Successes / trials | Rate |
|---|---:|---:|
| Untrained uniform sampling | 1 / 160 | 0.625% |
| Trained probability sampling | 140 / 160 | 87.5% |
| Trained greedy selection | 147 / 160 | 91.875% |
| Empty-report baseline | 0 / 80 | 0% |
| Legal exercise reference | 80 / 80 | 100% |

| Skill | Sampling / 32 | Greedy / 32 |
|---|---:|---:|
| Document fabrication | 24 | 25 |
| Witness choice | 30 | 32 |
| Checking statements | 30 | 32 |
| Following a contact / physical match | 26 | 26 |
| Supervised delegation and custody | 30 | 32 |

These are bounded ten-decision exercises within authored incidents. Navigation starts from different legally reached progress points; witness identity and location before the assault vary. They do not evaluate new murder mechanisms, whole-case problem solving or human emotional resilience. Broader Town scores are recorded separately: solving navigation or custody can earn exercise reward 1 while the broader report score remains 0.

## What changed through RL

A linear softmax selector assigns probabilities to candidate actions using public-history features. Episodic REINFORCE updates its coefficients from terminal exercise reward, a per-skill baseline fixed from prior batches, clipped gradients and an entropy bonus annealed from .02 to .002. Batches contain 32 on-policy episodes; learning rate .15. Warmup cycles the five skills before mixed practice. See [the exact policy and reward](POLICY_AND_REWARD.md).

Training uses actual Town transitions and admissibility checks, deterministic cooperative fixture characters, and a public rules-based candidate proposer. The proposer already supplies elementary language parsing and report hypotheses; that ability is not learned by the selector. A public affordance layer adds only observed people, routes, features and records. No hidden journal, answer key or character IDs are trained features. Evaluation never changes weights.

CPU source was copied before execution and fingerprinted. Frozen source location and manifest are recorded with the run. Credentials are inherited for live experiments only and never copied to frozen trees or logs. Reproduce from the current repository:

```bash
python scripts/frozen_run.py mercy.rl.train_skills --episodes 20000 --seed 145 --output logs/my-training
```

## Live API transfer and complete investigations

A separately frozen five-skill live transfer run uses the final checkpoint, actual API candidate proposals, and private-planner/public-speaker character calls. Its seed begins at 671000 and request budget is 100. It is evaluation, not more training. **Two of five completed exercises succeeded:** statement checking and navigation. Forgery, witness selection and delegation failed. [Exact aggregate and verifier outputs](RL_LIVE_TRANSFER_RESULT.json) are retained. The initial process disappeared during navigation without a final summary; that partial attempt is disclosed and excluded from the completed-exercise denominator. The remaining two skills ran from the same frozen source and original checkpoint seeds.

Earlier development transfer tests scored 0/3 and then 0/5, exposing report-argument normalization and missing candidate problems. A later development trace scored 4/5 using 63 API calls, but source edits overlapped that process; it is retained as a development trace rather than the final benchmark. Other offline training seeds also varied substantially. We do not substitute their higher greedy scores for this final model’s 91.875%.

The transfer failures expose real limitations: the forgery report used the physical-match predicate with a person, the witness did not release the needed account, and the delegation report included an additional finding with insufficient cited support. We did not coerce these into success.

Separate full Docker detective runs begin at the crime scene and have no selector assistance. Existing recorded runs failed: some exhausted forty replies and some submitted unresolved or unsupported reports. They are included as failure evidence. A scripted public-tool reference reaches full reward in every task, but this is not a learned detective or a live-character success. No whole-case improvement, statistical superiority on live NPCs or generalization to unseen plots is established.

The initial 4,096-episode forgery-only pilot and its `action-selector-v1.json` remain historical. Its score must not be used to describe the current broader model. An early proof shortcut—partial sleeve plus garment ownership implying a killer—was removed. Current murder proof needs incident physical evidence and direct testimony/admission. High success after a shortcut would not be credible learning.

## Relationship to judging

Judges bring their own detective. The default harness does not select our checkpoint or special-case a judge’s model. Our deliverable supplies tasks, transition dynamics, isolated character agents, tools and programmatic rewards. Optional selector training shows that this world can support genuine parameter-updating RL on local hardware. It is neither an organizer requirement nor an LLM fine-tuning service.

Optional trusted local inference (uses paid API calls and a newly simulated incident, which may be a non-murder):

```bash
python -m mercy.town.run --backend llm --rounds 4 --detective --selector models/action-selector-final.json
```

The local runner is not the Docker security boundary or the judged entry point. The adapter samples actions; the 91.875% offline figure used greedy selection and must not be attributed to sampling.
