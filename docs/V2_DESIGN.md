> Historical implementation review. For current proof rules and isolation use [POLICY_AND_REWARD.md](POLICY_AND_REWARD.md), [SECURITY.md](SECURITY.md) and [PS_COMPLIANCE_AUDIT.md](PS_COMPLIANCE_AUDIT.md). In particular, partial sleeve evidence no longer identifies a killer.

# Situated town: current implementation

The earlier named-claim catalog is deprecated. Current authoring lives in `mercy/town/setting.py` and physical event/evidence behavior in `world.py`. Historical V1 dossiers and transcripts are not current ground truth.

## Before and during the incident

Sixteen character profiles include family, home, work, history, relationships, private goals, temperament, starting memories and routine. Fourteen locations have reciprocal routes and local searchable features. Family members mentioned as living elsewhere remain offstage biographies, not additional autonomous agents.

The urgent scenario adds a private deadline and existing intentions for the meeting before Mira's dawn departure. It does not force a kill, secretly retry until success, or change the detective's observations. A three-round, four-participant live calibration produced a killing and planted note; this small sample does not establish an incident probability or a measured improvement over the ordinary scenario.

Agents choose bounded actions. The engine executes them, creates physical traces, and records direct observations, partial views and heard sounds locally. Bodies, injury traces and torn clothing result from the injury event. The shawl is carried by its owner until handed over or left at home. The forged note exists only after a forgery action. The household paper offcut predates it without describing a future act. The woodcutting/quarry route described in the forest is now a real route.

## Detective arrival

The detective receives their own remembered life and relationships, the immediate scene, visible exits/features and a generic assignment. No murderer candidates, global evidence menu, required findings, secret motives or instructions to suspect/trust particular people are sent. They remember childhood, family correspondence, work with Kabir and a former relationship with Leena as ordinary life facts.

The inspector arrives following Mira's invitation, discovers the scene and calls the accompanying constables. Character accounts reflect their own arrival and observations, not invented offstage reports.

## Investigation

The detective can observe, identify people present, travel, search features, assign searches, secure objects, question people, present acquired material, compare records, request access, excavate and report. Locked drawers and the bolted ward enforce real access conditions. Excavation requires locating disturbed ground and securing a spade. A subordinate may conceal fresh unobserved evidence; recorded or secured objects cannot be secretly re-hidden.

Private character decisions and public speech use separate projections and model calls. Reassurance affects rapport and fear; sensitive recollections also require relevant evidence. There is no promise that a model has human emotions. Ordinary persuasion is part of the simulation; attempts to obtain runtime data or change system authority are logged and restricted.

## Verification

No answer checklist is disclosed. The detective chooses generic actor/predicate/object/source findings. Observed IDs and equivalent full character names are accepted. Unknown prose semantics are flagged as unrecognized/unsupported, not automatically declared factually false. Narrative is retained but not scored semantically.

Murder proof can use an admission, a direct eyewitness, or a garment join combined with a partial witness, plus an incident trace. Garment presence alone is insufficient. Forgery requires the threat, matching paper and a separate handwriting specimen; paper ownership alone is insufficient. These are scenario rules, not claims about real forensic or legal sufficiency.

The verifier is still experimental. It does not accept every imaginable valid explanation or cover every historical subplot. A new full live Docker run submitted a report, but the then-current name matching rejected full names; normalization is now regression-tested. No live success score is claimed from that run.

## Execution and isolation

Default Docker Compose now runs V2 with a private world image and public-only detective image. `MODE=baselines` is an offline boundary/no-op integration smoke, not a completed multi-task reference-solution gate. `MODE=full` runs LLM characters and detective. The prior Docker contract is preserved as `docker-compose.legacy.yml`, explicitly historical.

Local CLI runs are useful for trusted development but have filesystem access to private author files in the host process. They must not be represented as an OS sandbox for arbitrary code execution. See SECURITY.md for actual boundaries and limitations.

## Still unfinished

Initial lifetimes and older crimes are authored, not generated by simulating decades. Investigation-time offstage schedules remain coarse. The supernatural mechanics and all secondary killings are not operational in V2. There is no million-world search or proof of universal originality. The complete five-task hackathon oracle contract, export package and arbitrary-shell isolation are not complete. External model outputs are not seed-deterministic: preserve actions and snapshots to replay them.
