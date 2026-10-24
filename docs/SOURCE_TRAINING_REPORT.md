# Source-mechanism policy training — actual result

A fresh linear action selector was trained on three original interactive checkpoint families inspired by the user’s screen references. **These are not exact TV episodes, source scripts, licensed episode datasets, or LLM fine-tuning.** The task wording, characters and documents are original; existing FamilyTown causal templates are reused.

| Screen reference | Original exercise | Behavior rewarded |
|---|---|---|
| The Mentalist S1E8, The Thin Red Line | Intended-target checkpoint after a two-casualty coach event | Attribute a route instruction and identify the addressed passenger through acquired document comparisons; the other casualty is not automatically the intended target. |
| The Mentalist S1E7, Seeing Red | Forged-warning checkpoint with a daughter/family-friend alternative and a separate relay speaker | Establish the warning’s author using paper and independently signed handwriting; a speaker’s apparent foreknowledge does not establish murder. |
| His & Hers | Trusted-relative assault checkpoint | Obtain a first-hand account with physical traces; refuse an unsupported gossip accusation. The familiar mother is guilty in some seeds and innocent in others. |

Sources: [The Thin Red Line](https://tv.apple.com/nz/episode/thin-red-line/umc.cmc.343dcf9kznkxsuz2rx6jcazs9), [Seeing Red episode/cast](https://www.tvmaze.com/episodes/8884/the-mentalist-1x07-seeing-red), [Netflix’s His & Hers ending explanation](https://www.netflix.com/tudum/articles/his-hers-episode-6-recap-ending-explained). The exercises borrow only broad investigative mechanisms. They do not reproduce the screen stories or claim the policy has understood their episodes. In particular, the His & Hers exercise is a small family-loyalty/false-accusation drill, not that series’ complete serial-murder or framing plot.

## What actually learned

A linear softmax selector assigns probabilities to authored candidate actions using whitelisted public progress and source-basis features. Names, actor handles, protected roles, event truth and answer labels are absent from coefficient keys. Candidate rules perform elementary reading and prepare tool arguments; that language processing was written, not learned. A private feasibility reference checks that legal proof exists but supplies no supervised action labels to the learner.

The new selector starts with zero weights. The historical 20,000-episode Mercy House checkpoint is neither loaded nor overwritten. No canonical Mercy House snapshot or elite trajectory enters this new training run. The API LLM stays fixed.

## Fixed experiment

- 6,000 CPU episodes, seed 526, batch size 32, maximum eight choices per episode.
- 48 training checkpoints: three mechanisms × 16 seeds (920000–920015).
- 48 held-out checkpoints: three mechanisms × 16 disjoint seeds (930000–930015).
- Both culprit assignments occur, but counts are not numerically balanced: 11/5 in training and 9/7 in held-out cases per family. No post-hoc resampling was performed.
- Each sampled evaluation repeats each held-out checkpoint twice, for 96 trials. Empty-report no-op runs once per checkpoint, for 48.
- Cooperative deterministic character fixture, with the normal disclosure and acquired-proof gates. No training API calls and no GPU.
- REINFORCE, learning rate .15, initial entropy .02 annealed to a tenth. Final fixed checkpoint only; no best-of-heldout selection.

## Exactly what earns training reward

Each episode receives **1** only when its final report establishes the requested proposition through acquired admissible sources and contains no false or unsupported finding. It receives **0** otherwise. The requested propositions are targeted, forged and killed for the three exercises respectively.

The checkpoint may start with previously acquired documents or testimony; those legal acquisition actions are recorded and replayed into the public notebook. Collecting a document, making more speeches, naming a correct person without support, quoting a rumour, or alleging psychic guilt earns no automatic success. Comparisons must actually execute. The full Town score is retained separately: completing one training objective can earn exercise reward 1 while covering only one of a full case’s three targets. We never rename that as a complete-case solve.

Honesty, bias resistance and loyalty are limited operational claims here: unsupported accusations fail, and guilty family roles vary. No internal hatred, grief, ego, intelligence or general emotional control is measured. Physical frame planting and every possible inference are not covered by these three small drills.

## Actual results

| Policy | Successful exercise trials |
|---|---:|
| Untrained sampling | 3 / 96 |
| Trained sampling | 89 / 96 |
| Trained greedy | 96 / 96 |
| Empty-report no-op | 0 / 48 |

Training plus evaluation took **48.251 seconds** on the CPU and produced **132 learned coefficients**. Each held-out exercise’s privileged reference achieved 1 and its no-op 0. Public proposer feasibility was independently checked for both culprit roles; a successful acquired-proof report is representable without querying hidden state.

These are disjoint seeds within reused authored checkpoint templates, not unseen-template generalization, native LLM detective performance, or elite-case success. The strong offline result reflects a small, controlled candidate distribution and rule-based reading. A separate frozen elite evaluation is required; do not pool those conditions with this result or claim that 96/96 means the complete town is solved reliably.

One earlier run at logs/source-policy-526 is retained but invalidated: reused engine rendering had left source short names in adapted documents. A regression now checks profile/document consistency and a standalone training biography. The same predeclared configuration was rerun after that data fix; no elite performance was consulted.

## Reproduce

```bash
python scripts/frozen_run.py mercy.rl.train_sources --episodes 6000 --seed 526 --output logs/my-source-training
```

Use a fresh output directory. Runtime training uses only the Python standard library. Current final checkpoint: models/action-selector-sources.json. Raw manifest, learning curve, exercise gates, public trajectories and evaluation: logs/source-policy-526-corrected. The frozen source path and checkpoint SHA256 are in SOURCE_TRAINING_RESULT.json. The historical original selector and its measurements remain separate.

## Subsequent author-text correction

After this immutable experiment finished, the live family engine’s delivery docket was corrected from a future-looking statement (“before Tessa entered the chapel”) to a contemporaneous observation that she was still at the inn. The training adaptation had normalized the character name but inherited the temporal wording. This later prose correction changes no targets, proof predicates or reward rules. Reported measurements belong to the exact frozen source recorded in the manifest; they are not silently relabeled as a rerun of the corrected current source.


## Frozen elite result

The separately preregistered elite test has completed: both the LLM-ranked baseline and new source selector solved0/2 complete task scopes. They share the excluded original Mercy House incident. Three arms reached their choice cap without submitting; the selector’s inquest submission established one non-target garment match and earned0 material coverage. This does not demonstrate improved full-case solving despite the96/96 checkpoint result. See ELITE_TRANSFER_REPORT.md for exact conditions, source hashes and all retained failures.
