# Original case families and difficulty

Eight public task IDs now cover four causal families. The former `last_witness` task is intermediate; `lantern_room` is the introductory default. The new stories use broad mystery mechanisms rather than copied plots, dialogue or character casts. We cannot guarantee no similar idea exists anywhere in fiction.

## The Lantern Room — introductory

Investigate the fatal assault at the Pine Lantern. Establish the assailant using acquired physical traces and a first-hand account. You choose whom to question and what to inspect.

4 local profiles and 3 places. The seed chooses between two culprit assignments and changes the executed actions, private recollections and physical traces together.

## The Second Passenger — intermediate

Investigate two deaths at the bridge crossing. Establish responsibility for the deaths and whether either passenger was specifically targeted. Distinguish an observed act, the failure mechanism and evidence of intention.

6 local profiles and 4 places. The seed chooses between two culprit assignments and changes the executed actions, private recollections and physical traces together.

## The Bell Before Dawn — advanced

Investigate the death in the chapel and the apparently prophetic warning. Establish responsibility for the death, any fabrication of the warning document, and how it was relayed. Foreknowledge alone does not establish participation in a killing.

6 local profiles and 5 places. The seed chooses between two culprit assignments and changes the executed actions, private recollections and physical traces together.

## What is actually simulated

The original Mercy House case replays recorded LLM decisions. The three new families execute **authored seeded action tapes** through validated movement, possession, attack, sabotage, delivery and drinking transitions. Witnesses receive local perceptions. A repairer who sees tampering does not thereby know an offstage crash’s cause. The private causal journal can know more than witnesses.

History, relatives, motives and ordinary routines are authored. Current residents do not continually improvise lives offstage. Live character LLMs decide post-arrival conversation subject to eligibility and disclosure gates; dialogue cannot create objects or rewrite truth. The detective receives personal recollections, no instructed grudge and no required-answer checklist.

## Difficulty and rewards

Beginner: three rooms, a willing witness and one supported fatal attribution. Intermediate: mechanism, two consequences and intention must be separated. Advanced warning: separate death, authorship and transmission rather than blaming someone for apparently predicting a death. The original full inquest adds loyalty, custody, false documents and historical records. These are designed complexity levels, not established model success-rate bands.

All use the same strict reward: supported target coverage minus .20 per distinct false finding and .10 per distinct unsupported finding, clamped to [0,1]. Complete success requires every scoped target and no false/unsupported conclusions. Correct guesses, self-written notes and arbitrary local files cannot supply provenance. The judge is programmatic, with authored proof paths; narrative is unscored.

## Actual measurements

Four cold-start native-tool API detectives with live character agents solved Lantern Room at seeds 211, 307, 401 and 37, with score 1 and no false/unsupported findings. Seed 37 was added after the first three selected the same culprit, to check the opposite assignment. This is a small development calibration, not an unbiased reliability estimate. The other new families have scripted proof-route successes, not demonstrated live-character solving.

A separate predeclared three-case comparison used equal ranked-candidate contracts and a fixed grounded response bank. LLM-ranked actions succeeded in 1/3, the frozen RL selector in 0/3. It often reported before collecting sufficient proof. No policy advantage is established; the selector stays optional. NPC condition, branch-dependent proposals and budgets differ from the native runs; do not pool these rates. Exact evidence is in FAMILY_VALIDATION_RESULT.json and FAMILY_POLICY_COMPARISON.json.

Historical CPU training results (147/160 offline checkpoints and 2/5 live checkpoint exercises) remain historical. These do not become whole-case results just because we added new cases. No new training is claimed here.

## Presentation

The local viewer starts with an actual beginner model success and offers level filters. Scripted references and checkpoint replays retain their labels. New runs use the selected provider, task and seed; judges still use the independent standard Compose command. Private author review below must never enter an evaluated workspace.

## Reproduce the controlled comparison

With development provider settings configured in the ignored .env, run:

```bash
python scripts/frozen_run.py mercy.rl.compare_families --output logs/new-family-calibration --steps 24 --request-cap 150
```

This makes bounded proposer API calls, keeps selector weights fixed and records its source manifest. It uses fixture-based grounded responses, not live NPCs. Choose a fresh output directory. The published six trajectories are in the submission archive under rl/family-calibration; the protected response-bank files are excluded.
