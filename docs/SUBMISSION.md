# Final submission

Team: **Kasukabe Defence Force** — Aditya Ahirwar, Abhishek, Tapis Samaiya.

The runnable entry is the repository's `main` branch. `Kasukabe Defence Force.zip` is reference material; judges do not execute the archive. The demo task is `lantern_room`, seed 7.

## Required material

- `baseline-results/`: all eight reference/no-op gates and trajectories.
- `test-run-logs/`: actual native API investigations, with historical source identities retained and failures included.
- `sample-trajectories/`: an actual model success, an actual model failure, and a separately labeled scripted reference.
- `design-doc.pdf`: two-page environment/reward/defence/limits description.
- `deck.pdf`: fourteen-slide presentation; editable PowerPoint is also included.
- `MANIFEST.json`: source commit, run identities and SHA-256 for every packaged file.

The package also contains policy evidence, validation, the caption-only live investigation tutorial and its captions. Scripted feasibility, prepared training checkpoints, frozen full-case experiments and native model runs are labeled separately.

## Run from a fresh clone

Create `.env` from `.env.example`. Configure detective `MODEL`, `API_KEY`, `BASE_URL`; configure environment-owned `NPC_MODEL`, `NPC_API_KEY`, `NPC_BASE_URL`. `APPEND_FILE=inputs/append.txt` must exist and be nonempty. No real credential is shipped.

```bash
docker compose up --build --abort-on-container-exit --exit-code-from harness
```

`MODE=baselines` checks all eight tasks. `MODE=all` is a development batch, not a guarantee that all cases fit a single finals slot. The selected task's reference and no-op run automatically before a detective request. Full native runs allow 40 model replies, ten tools per reply and 600 seconds from the first model request.

## Final checks and limits

`FINAL_SUBMISSION_VALIDATION.json` identifies the validated source, fresh-clone command and results. `FAIRNESS_RESULT.json` records bounded-refusal probes. Scores, proof requirements and isolation remain programmatic. Three corroborated reassuring nonanswers can record an eligible external eyewitness account; formal access and specifically authorized inventory requests also resolve. No new memory, compelled self-incrimination or reward is created by that procedure.

Only the organizer-provided GPT-Luna deployment was available for real calls. Other response formats and provider adapters have fixture tests. The optional selector's frozen elite result remains 0/2; no full-case learning advantage is claimed. Historical videos and native runs predate the final cooperation rule and retain their original labels.

## Final handoff

The PDF asks for a **private repo named after the team**, an organizer invitation and one team-named ZIP uploaded through the emailed form. The existing `mercy-house` repo and live demo remain public by team choice. The team will handle the private competition copy, organizer access and form upload. No form has been submitted by this tooling.

Rebuild after the final commit with `python scripts/build_submission.py`. Optional presentation authoring uses `requirements-presentation.txt` and LibreOffice; these are not runtime dependencies. The archive builder verifies required files, PDF page counts, hashes, configured credential values and archive integrity. Old leaking demo transcripts and duplicate development handoff files were removed; historical empirical results and failures remain available.
