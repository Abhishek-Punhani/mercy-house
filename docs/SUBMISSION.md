# Local submission handoff

The user will handle GitHub, the organizer invitation and the submission form. No remote is created or contacted by the packaging workflow.

## Reference archive

Generated archive: `Kasukabe Defence Force.zip` at the project root. It contains:

- `baseline-results/gate.json` and all five reference/no-op public trajectories.
- `test-run-logs/`: at least three actual API detective runs, including failures.
- `sample-trajectories/success-reference/`: full-inquest scripted success, explicitly not a learned or LLM run.
- `sample-trajectories/failure-model/`: actual crime-scene model failure.
- `design-doc.pdf`: two pages.
- `deck.pdf`: ten slides for a ten-minute presentation.
- Optional RL weights, learning/evaluation evidence, live-transfer logs without private actor context, validation evidence and limitations.
- `MANIFEST.json`: source commit, run identities, trajectory labels and file hashes.

The zip is judge reference material. The source repository is what judges clone and run. Do not put `.env` in either. Generated PDFs also live in `docs/`; their HTML is editable document source, not a hosted site.

Rebuild after final source commit and completed measurements:

```bash
python scripts/build_submission.py
```

This requires Chrome and `pdfinfo` locally to prepare documents; the runtime Docker environment does not use them. The script checks PDF page counts, archive integrity and the configured credential values without printing them.

## Source handoff

Use the local `main` branch. Create the private team-named GitHub repository, push `main`, invite the exact organizer username from the submission email and submit the team-named archive through the form. Confirm the exact team/repo spelling the form accepts; the package uses the team name from the supplied email. These external actions remain yours, as requested.

On the organizer machine configure the judged detective’s `MODEL`, `API_KEY`, `BASE_URL` and the environment’s own `NPC_MODEL`, `NPC_API_KEY`, `NPC_BASE_URL`. The explicit development sharing switch is not a claim that the PS waives its separate-setup requirement. Never rely on our local ignored `.env` being present in a clone.

## Evidence and honest limits

Current gates pass 1/0 for all five tasks. The final CPU policy trains 20,000 episodes and scores 147/160 greedy offline checkpoint trials; live checkpoint transfer is 2/5, with an interrupted partial attempt disclosed. Full crime-scene API detective runs have not achieved success. The reference success proves an authored legal proof route under cooperative fixture characters. It does not establish that a live character always cooperates.

A fresh isolated no-cache builder completed four images in 23.208 seconds on this machine. A fresh local Git clone also passed the exact Compose baseline command in 5.192 seconds with Docker cache present. Organizer-machine timing remains to verify. Container boundary probes and current tests pass; no universal jailbreak or winning guarantee is made. The package is reviewable and runnable locally, but reliable live solving and additional causal case families remain the main research improvements.


## Viewer update

The source now includes the optional local story viewer (`python -m mercy.viewer.server`, localhost:8787). It is independent of the headless judge command. The reference archive includes its screenshot, validation evidence and two additional failed API runs. Current runtime tests: 86 town + 9 legacy; viewer state tests: 4; nine browser checks and the provider-form failure path pass. A new no-cache build takes 13.474 seconds locally. The original 23.208-second result above describes the pre-viewer source. No live solving improvement is claimed.
