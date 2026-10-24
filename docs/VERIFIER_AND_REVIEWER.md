# Scoring and the private story reviewer

The protected programmatic verifier owns the official investigation score. It knows the executed event journal, authored historical facts, acquired receipts and admissible proof routes. It checks truth and evidentiary support separately. A correct private answer without detective acquisition earns no proof credit.

The supplied PS explicitly asks, “Can the verifier use an LLM?” and answers, “No, programmatic checks only.” Its requirements are followed for official scoring. No language model decides rewards, changes success flags or silently patches the truth.

`mercy.audit.review` is an additional **trusted authoring command outside evaluated episodes**. It rechecks an actual private world snapshot and submitted report, lists each claim's source acquisition and shows privately which targets remain unestablished. It does not replay live witnesses with a different policy and pretend that is the original run. It preserves the original snapshot. Historical rechecks must use the matching source manifest, because current stronger proof rules may differ from historical code.

```bash
python -m mercy.audit.review \
  --world logs/private/RUN/world.json \
  --report logs/private/report-arguments.json \
  --output logs/private/review.json
```

The report file contains the original `submit_report` arguments (`findings`, optional `narrative`). The command can make one optional development API call with `--advisory-model`. This gives an authoring reviewer the story, receipts and report, asking for contradictions or unsupported interpretation. Its commentary is explicitly unscored; model-proposed score/success fields are discarded. An API failure leaves the deterministic result intact. The output includes private answers and is mode 0600; keep it outside public logs, viewer data and the submission archive.

The authoring reviewer is not registered as a detective tool, not served by the viewer, and absent from the detective/workspace images. Its private outputs and full world snapshots are not packaged as public replay content. This complements automated case-consistency tests and the requested independent coding-agent audit; it does not establish universal factual correctness or perfect jailbreaking resistance.

The browser's final report now visibly displays the actual submitted claims and citations, narrative, official programmatic findings, supported/false/unsupported counts and reward breakdown. It distinguishes scripted reference, native model and RL checkpoint runs. Missing submissions, interrupted runs and forced ends remain explicit.
