# Local submission handoff

The user handles GitHub, the organizer invitation and the form. Nothing is published automatically.

The project-root `Kasukabe Defence Force.zip` is reference material; judges clone and run the source repository. It contains all eight reference/no-op gate trajectories, at least three actual API model runs including failures, actual beginner model success, a separately labeled scripted full-inquest reference, two-page design PDF, ten-slide deck, CPU policy evidence, the negative family comparison, validation and a hashed manifest.

- `sample-trajectories/success-model/`: actual cold-start native detective with live character agents and acquired proof.
- `sample-trajectories/success-reference/`: privileged scripted public-tool route, not an LLM result.
- `sample-trajectories/failure-model/`: an actual failed detective run.
- `test-run-logs/`: eleven actual native model runs, including all seven historical original-town failures and four beginner successes.
- `rl/family-calibration/`: predeclared three-case comparison. Private response-bank files are excluded. This is a different NPC condition from the live beginner runs.
- `MANIFEST.json`: source commit, run identities, trajectory labels and per-file hashes.

Rebuild after final source commit with `python scripts/build_submission.py`. Chrome and pdfinfo are local document authoring tools, not runtime dependencies. The builder checks page counts, archive integrity and configured credential values without printing them. Never include `.env` in the repository, zip or logs.

Use local `main` for the private team-named repository, invite the exact organizer username from their email, and upload the team-named zip. Configure the judged detective’s MODEL/API_KEY/BASE_URL and the environment’s own NPC_MODEL/NPC_API_KEY/NPC_BASE_URL. Development sharing is explicitly user-authorized; it is not evidence that the PS waives its own-setup rule for finals. A fresh clone must be configured because the ignored local .env is not shipped.

Current evidence: all eight scripted gates 1/0; 96 town, 9 legacy and 4 Node tests; browser/filter/form checks; real-command isolation. Four live beginner runs succeeded. No reliable solving claim across harder families. Historical CPU greedy checkpoints 147/160 and live checkpoints 2/5 are separate; new matched family calibration gives LLM-ranked 1/3 versus frozen selector 0/3. The selector stays optional.

See VALIDATION_RESULT.json for current cold-build and fresh-clone timings. Organizer-machine timing and separate NPC deployment remain external. The optional viewer runs locally at http://localhost:8787 and is independent of judging. No universal security or winning guarantee is made.
