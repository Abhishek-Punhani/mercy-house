# Problem statement compliance

This maps the supplied organizer PDF to the submitted environment. Document instructions are competition requirements, not permission to change team accounts or credentials. Current machine evidence is in `FINAL_SUBMISSION_VALIDATION.json`, `VALIDATION_RESULT.json` and the ZIP manifest.

| Requirement | Implementation / evidence |
|---|---|
| At least five tasks, two difficulty levels | Eight tasks, four causal families and three designed levels. `lantern_room` is the demo. |
| Stateful tools and observations | Schemas validate presence, access, custody, comparisons and reports; actions persist within an episode. |
| Same seed, same starting hash | Factory replay of recorded/authored tapes; repeated reset and 184 task/seed reference/no-op checks. |
| Programmatic verifier; no LLM score | Acquired provenance supports scoped findings. Reward is coverage − .20 false − .10 unsupported, clamped to [0,1]. |
| Reference ≥.95, no-op ≤.05 before model | Selected-task gates run automatically. All-task baseline material is packaged. |
| Model override | MODEL/API_KEY/BASE_URL configure the detective independently from environment character settings. Native, legacy and structured-text replies are parsed. Only one real deployment was available. |
| Exact APPEND_FILE suffix | UTF-8 text is appended unchanged; absent/empty files stop model runs. |
| Fresh-clone Compose command | Four pinned standard-library images. Build, gates, model and logs are exercised by the final validation runner. |
| Isolation | Private world, credential gateway, trusted harness and real shell are separate. No answer files, keys, controller token, Docker socket or outside network in the shell. |
| Limits / failure recovery | 40 replies, ten calls per reply, 600 seconds; bounded tool, model and grading deadlines. Malformed replies consume steps and produce feedback. |
| Full telemetry | Model inputs/raw outputs, parsed actions, tool results, errors, state hash, reward, usage, latency and terminal reason are retained. |
| Environment-owned LLM setup | Separate NPC settings are supported. Development sharing was explicitly authorized; finals still need the team's own NPC setup as stated in the PDF. |
| Required ZIP | Gates, at least three model runs, success/failure examples, two-page design PDF and presentation PDF; manifest and credential scan. |
| Private team-named repo, invite and form | Team handles these external submission steps. The public demo/dev repo is not presented as meeting the private-repository requirement. |

The PDF's finals weighting is presentation 30, functional Run A 30 and build-quality Run B 40. UI polish and optional policy training do not replace scoring integrity or graceful error handling.

Bounded cooperation addresses permanent NPC refusal without relaxing proof. Stress scripts establish routes under an always-declining actor; they are not new LLM success rates. Murder still needs physical incident support and a genuine named first-hand account. Partial views, guesses, self-written notes and arbitrary local files cannot become proof.

Known limits: four authored families, finite proof semantics, unscored narrative/emotions, no continuous lifetime simulation or scored supernatural cause, limited live model/provider coverage and no demonstrated full-case policy advantage. The frozen elite comparison remains 0/2 in both arms and predates the final cooperation rule. Container security assumes a trusted host and Docker daemon. Organizer-machine timing remains external.
