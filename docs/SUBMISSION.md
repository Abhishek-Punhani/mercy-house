# Local submission handoff

The private GitHub repository has been created/configured and pushed under the user’s later explicit authorization. The user still handles organizer access and the submission form. The protected live demo is documented in DEPLOYMENT.md.

The project-root `Kasukabe Defence Force.zip` is reference material; judges clone and run the source repository. It contains all eight reference/no-op gate trajectories, at least three actual API model runs including failures, actual beginner model success, a separately labeled scripted full-inquest reference, two-page design PDF, fourteen-slide editable PowerPoint and PDF, CPU policy evidence, the negative family comparison, validation and a hashed manifest.

- `sample-trajectories/success-model/`: actual cold-start native detective with live character agents and acquired proof.
- `sample-trajectories/success-reference/`: privileged scripted public-tool route, not an LLM result.
- `sample-trajectories/failure-model/`: an actual failed detective run.
- `test-run-logs/`: fifteen actual native model runs, including ten failures and five beginner successes. Four are the original development calibration; four later user-started UI tests are separately documented in SAVED_UI_RUN_RESULTS.json.
- `rl/family-calibration/`: predeclared three-case comparison. Private response-bank files are excluded. This is a different NPC condition from the live beginner runs.
- `MANIFEST.json`: source commit, run identities, trajectory labels and per-file hashes.

Rebuild after final source commit with `python scripts/build_submission.py`. Chrome and pdfinfo are local document authoring tools, not runtime dependencies. The builder checks page counts, archive integrity and configured credential values without printing them. Never include `.env` in the repository, zip or logs.

Use local `main` for the private team-named repository, invite the exact organizer username from their email, and upload the team-named zip. Configure the judged detective’s MODEL/API_KEY/BASE_URL and the environment’s own NPC_MODEL/NPC_API_KEY/NPC_BASE_URL. Development sharing is explicitly user-authorized; it is not evidence that the PS waives its own-setup rule for finals. A fresh clone must be configured because the ignored local .env is not shipped.

Current evidence: all eight scripted gates 1/0; 114 town, 9 legacy and 9 Node tests; browser/filter/form checks; real-command isolation. Four development beginner runs succeeded; one separately saved user beginner run also succeeded. No reliable solving claim across harder families. Historical CPU greedy checkpoints 147/160 and live checkpoints 2/5 are separate; new matched family calibration gives LLM-ranked 1/3 versus frozen selector 0/3. The fresh source-trained selector separately scored96/96 on held-out prepared skill checkpoints and0/2 on the predeclared full-scope elite test (baseline also0/2). The selector stays optional.

See VALIDATION_RESULT.json for current cold-build and fresh-clone timings. Organizer-machine timing and separate NPC deployment remain external. The optional viewer runs locally at http://localhost:8787 and is independent of judging. No universal security or winning guarantee is made.


Latest reference material also includes SOURCE_TRAINING_REPORT/RESULT, ELITE_TRANSFER_RESULT, the case solvability audit, the private-reviewer design, and two correctly labeled UI screenshots. New source-policy weights and immutable training/elite manifests are separate from historical20k prototype artifacts. Private author-review snapshots, private response banks and optional LLM audit outputs are excluded.

The presentation authoring script uses optional python-pptx1.0.2 and LibreOffice (`pip install -r requirements-presentation.txt`), never runtime dependencies. `scripts/build_presentation.py` regenerates editable docs/deck.pptx and docs/deck.pdf; unchanged input hashes reuse artifacts. The final zip remains reference material; source main is the judged runnable entry.

The final introduction names Aditya Ahirwar, Abhishek and Tapis Samaiya. The thank-you slide has validated QR codes and clickable repository/live URLs. The private repository and authenticated hosted demo require access; no login secret is embedded.
