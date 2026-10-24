# Submitted report and investigation result

The local viewer now displays a persistent report panel immediately below the replay controls whenever an accepted report or a terminal result has been observed. Completion produces a visible “Case solved”, “Case not solved”, or “Investigation not graded” heading; an on-screen completion notice points to the report. The existing final-report modal remains available through the replay control.

The panel contains the detective’s actual submitted structured findings, clickable cited source IDs, its unscored narrative, and expandable exact report JSON. A separate section shows the programmatic verifier’s supported, false, unsupported and unresolved findings. Reward cards and a coverage/false-penalty/unsupported-penalty breakdown distinguish the detective’s assertions from the verifier’s findings. Text is rendered through textContent; model-authored markup cannot become executable HTML.

The result follows the authoritative result.success field rather than inferring success from a positive score or termination label. Skill checkpoints say “Checkpoint completed/incomplete” and display exercise reward separately from the broader Town report score. Scripted references remain clearly labeled as privileged feasibility routes with cooperative fixture characters. These UI changes do not add an LLM judge or change reward rules.

Only an accepted public submit_report tool observation records a submission. A denied tool call or arbitrary shell stdout cannot invent an accepted report. Real CLI calls are captured as inner public tool observations in current live action telemetry; the outer run_command result does not erase them. An older archive containing only an outer shell command may lack the exact inner submission. The viewer then states that no accepted submission is captured, preserves the recorded grade, and does not reconstruct one by parsing untrusted shell text. Forced-end grading can likewise have a result without a detective-submitted report.

Seeking backward clears future submission/result state, so opening an investigation does not reveal its future report. The panel shows acquired records and the detective’s own claims; it never requests the hidden target list, private world or character memories. Existing provider-key separation and endpoint controls are unchanged.

Validation: nine Node state tests (four existing plus five report regressions), seven Python viewer-boundary tests, desktop/mobile Chrome checks, and the provider-form validation path pass. Browser tests verify both solved and unsolved persistent panels, actual cited sources, reward breakdown, and mobile report layout without horizontal overflow. No model/API generation calls were required.

Presentation screenshots:

- `docs/ui-report.png`: actual native-tool detective success on Lantern Room, seed 211, using live character agents; the visible reward is 1.0.
- `docs/ui-interview.png`: the original inquest interview in a scripted-reference replay, with that provenance label visible.

Raw local validation: `logs/viewer-report-state-tests.txt`, `logs/viewer-report-python-tests.txt`, `logs/viewer-browser-checks.json`, `logs/viewer-form-checks.json`, and `logs/viewer-report-mobile.png`.

Report prose disambiguates `assisted` as “knowingly facilitated the fatal incident involving” and `aided` as “gave aid to”. Exact submitted JSON retains the original predicate, so assistance in a homicide cannot be mistaken for helping its victim.
