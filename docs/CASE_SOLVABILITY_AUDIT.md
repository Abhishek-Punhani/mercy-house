# Case consistency and solvability audit

**Result: passed with stated limits.** Every current scoped target has a legal reference route in the tested seeds. The audit found and corrected real factual/provenance defects; it does not certify that no possible prose contradiction exists.

This is an author-side deterministic audit. It knows the private case definitions to test coverage, while the source-only probe below receives only public observations. It is not an LLM replacing the official programmatic verifier. No provider calls were made.

## Corrections made

| Finding | Resolution |
|---|---|
| The exact report phrase grave relocation was not normalized to the existing burials entity, rejecting an otherwise equivalent supported finding. | Added exact folded aliases for grave relocation, burial relocation and relocation of graves. Full acquired reference proof succeeds; naming the same facts without acquisition still earns zero; negated or embedded phrases are not matched. Historical model and frozen elite results are preserved. |
| Burial evidence and comparison labeled Savitri as the physical mover despite the text naming Nalin as carrier. | Only commissioned/Savitri and moved/Nalin are attributed. Remains alone carry no role attribution. Wrong moved/Savitri report is rejected. |
| Cover initials and a missing register entry did not independently identify the writer of the deletion instruction. | Added an independently signed and countersigned routine maintenance receipt. Attributing alteration to Vedant requires both the register discrepancy and independent handwriting comparison; three-way or composed two-way examinations are accepted. |
| The threat comparison cited a lower-case d although the original threat wording contained none. | Added the natural warning sentence You have been warned, which contains the described stroke. |
| Dev remembered leaving the spade at the beds but the object was in the tool shed. | Memory now names the tool shed beside the beds. |
| Nalin called the storage location the archive visitors book while the actual feature is in the entrance hall. | Memory now identifies the entrance-hall visitors book. |
| Static bridge scenery already described a wreck before the sabotage and even in the safe counterfactual. | Bridge scenery and brake placement now reflect actual crossing outcome. No sabotage produces no fatalities or wreck state. |
| Niv really delivered the warning but a truthful transmission finding had no admissible proof route. | The countersigned delivery docket supports optional relayed/Niv with the acquired warning. Ivo remains the scoped public-relay target; bell target count remains three. |
| A docket created during delivery described Tessa entering the chapel later in the tape. | The docket records contemporaneous local observation: Tessa is still in the inn common room at delivery. Regression stops the tape at delivery to check this. |
| Canonical proof did not consistently follow the acquired material actually examined by a cited comparison, although family proof already did. | Canonical support expands protected comparison dependencies. Self-written notes do not create source dependencies or proof. |
| The author plot summary described a hatch sighting that does not occur in the recorded tape. | Root updated the summary to distinguish the actual cry/heard sound from the unused hatch possibility. No eyewitness was invented. |

The task target meanings and scalar score weights remain unchanged. The full original inquest still has seven material targets; Bell Before Dawn still has three. Adding Niv’s supported delivery does not silently make him a murderer or create a new compulsory target.

## Legal routes and seeded coverage

Tested all eight tasks at 23 exact seeds: **0–15, 37, 82, 211, 307, 401, −9223372036854775808 and 9223372036854775807**. All **184 reference/no-op pairs passed**, with reference score 1.0 and no-op score 0.0. The repeat builds agreed on initial hashes. Location exits, reciprocal routes, character homes/current locations and physical object placement were checked. Reference actions had no tool errors. The sweep took 8.857 seconds locally with fixture characters.

| Task | Reference actions at seed 7 | Scoped targets |
|---|---:|---:|
| lantern_room | 5 | 1 |
| second_passenger | 16 | 3 |
| bell_before_dawn | 17 | 3 |
| last_witness | 10 | 1 |
| borrowed_signature | 20 | 1 |
| brothers_letter | 31 | 1 |
| garden_burials | 31 | 2 |
| mercy_inquest | 35 | 7 |

All references fit even the conservative one-action-per-reply interpretation of the 40-reply limit; none needs more than one call per reply. References know the solution but still acquire admissible sources through legal public tools. They prove feasibility, not that a fresh model can find the route.

## Independent public-information feasibility

`tests/town/public_feasibility.py` contains a separate scripted investigator. Its investigation function receives only `opening` and `step(tool, args)`. It never reads the world object, causal journal, private case, target list or proof propositions. It explores visible routes, searches available features, interviews observed living people, compares acquired records, and derives names/intent from returned text.

It solved both assailant assignments (seeds 0 and 1) for each new family:

| Family | Seeds | Public actions per run | Conservative batched reply bound | Score |
|---|---|---:|---:|---:|
| lantern_room | 0, 1 | 25 | 12 | 1.0 |
| second_passenger | 0, 1 | 112 | 24 | 1.0 |
| bell_before_dawn | 0, 1 | 201 | 36 | 1.0 |

The reply bounds group already-known independent calls into batches of at most ten, reserve separate discovery/interview turns and one turn per movement, and include final submission. They remain at most 40. This is a calculated legal schedule, not a measured API response count. The probe is intentionally exhaustive and genre-specific; it is **not an LLM or learned-policy performance result**. It uses cooperative fixtures and does not establish success against arbitrary refusal.

Reproduce the additional audit regressions and public-only probe:

```bash
python -m unittest discover -s tests/town -p test_case_audit.py -v
python tests/town/public_feasibility.py
```

Nine regression methods cover exact semantic aliases without proof relaxation, payer/carrier separation, independent register attribution and comparison composition, optional delivery, contemporaneous docket wording, conditional wreck state, physically possible biography/evidence details, and source-only discovery for both seeded roles. Existing family tests also check no attack/no corpse, intact brake/no fatalities, unadulterated drink/no death, unseen causal knowledge, wrong-actor proofs and guessed/self-written sources.

## Remaining limits

- Programmatic proof vocabulary and authored routes are finite; this is not a formal proof of every natural-language claim or an exhaustive absence-of-contradiction certificate.
- Reference and source-only feasibility runs use cooperative fixture characters. A live character may permanently refuse an eligible disclosure; successful routes do not guarantee live cooperation.
- In the canonical recorded murder Vedant is the only independent named eyewitness. Complete attribution needs his disclosure or an eligible admission by Savitri. Sera only hears the cry in this tape; clothing alone remains insufficient.
- The source-only probes are scripted genre-specific investigators with public text parsing and exhaustive 2/3-record examinations, not trained or LLM successes. Batched reply bounds are calculated schedules, not measured API reply counts.
- Narrative prose, internal grief/ego and supernatural causes are not scored. No ghost influence or continuous offstage lifetime simulation is implemented.
- Historical metrics refer to their frozen source versions. The new independent register sample, payer/carrier correction and later docket wording mean older logs are evidence of their old versions, not automatic validation of current source.
- The separate source-inspired training worker validates its training-only adaptations. This audit covers the current eight public tasks and four case families, not all future generated stories.
- Security relies on the documented trusted-host/container boundary; these data/proof checks are not universal jailbreak certification.

The exact source hashes, individual 184 gate rows, six public-only probe results and correction list are in `CASE_SOLVABILITY_AUDIT.json`. Parent packaging will regenerate the current author exports and scripted replays; historical model runs remain labeled by their original source conditions.
