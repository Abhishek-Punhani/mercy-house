> Historical implementation review. For current proof rules and isolation use [POLICY_AND_REWARD.md](POLICY_AND_REWARD.md), [SECURITY.md](SECURITY.md) and [PS_COMPLIANCE_AUDIT.md](PS_COMPLIANCE_AUDIT.md). In particular, partial sleeve evidence no longer identifies a killer.

# Review of the current world and information boundaries

## What changed

| Area | Finding | Change |
|---|---|---|
| Detective context | Old versions instructed suspicion and enumerated answers | Current opening uses ordinary life memories, local surroundings and a generic assignment; no named conclusions |
| Characters | Full private profile shared with untrusted questions | Private decision/public speaker split; typed disclosure permissions; separate histories |
| Motive pressure | Open-ended meetings could be postponed indefinitely | Explicit urgent configuration: dawn departure and existing private intentions; no forced killing or silent retries |
| Family relationships | Reused surnames and first names caused accidental associations | Detective Arun Mehra, Kabir/Nalin Mehta, Savitri's deceased husband Pranab; existing relationships remain factual |
| Locations | Locked and sealed descriptions were cosmetic; quarry was mentioned but absent | Enforced access grants; real quarry route; reciprocal route tests |
| Paper | Draft described a future forgery | Innocent pre-existing offcut; forgery emits the threat; handwriting requires a separate signed sample |
| Clothing | Torn clothing existed before the attack | Starts intact and carried; attack tears it; it moves with its owner until released or left at home |
| Garden | Searching immediately exposed underground bodies | Surface discovery, secured spade and a timed excavation are separate steps |
| Perception | Action menus could imply an unheard event; listening could invent a voice | Aid/departure affordances depend on local perception; sound is delivered only to nearby people; partial view does not name the killer |
| Persuasion | Repeated friendly prompts could dump secrets | Ordinary rapport affects witness disclosure; intimate/incriminating memories also need relevant acquired material |
| Runtime requests | Unknown/invalid actions were incompletely logged | Strict schema checks, fixed public errors, request/result audit even for denied actions |
| Permissions | Spoken claims could be confused with capabilities | Only an authorized grant action creates access; speech cannot make objects, authority or facts |
| Scoring | Full names rejected; unknown prose automatically treated as false | Full names normalize to observed IDs; unknown semantics are flagged separately; limited non-confession proof path |
| Docker | Default command still ran V1 | Separate V2 world and public-only harness images; V1 explicitly preserved as legacy |
| Egress/credentials | World could hold keys and depend on direct internet | Internal-only world, no provider keys, authenticated fixed-endpoint broker in trusted harness |
| Transport failure | Broker deadline raced the caller and printed a broken-pipe traceback | Earlier broker timeout, generic error and safe closed-connection handling; regression test |

## Authoritative files

`setting.py` supplies current profiles, locations, own-life context and scenario pressure. `world.py` executes physical actions and creates perceptions/traces. `boundaries.py` supplies projections, memory gates and audit chaining. `agents.py` supplies isolated planner/speaker calls. `tools.py` and `validation.py` define public capability limits. `service.py`, `client.py`, the two role Dockerfiles and default Compose define the runtime boundary. `detective.py` records the detective's observable trajectory.

The regenerated character, location, evidence and opening documents are review artifacts. They are not wholesale inputs to the detective. The file manifest identifies historical V1 artifacts; their easy scores are not evidence about the current world. Historical docs are retained rather than quietly rewritten as successful V2 results.

## Validation and limits

The automated suite tests causal evidence creation, local knowledge, ordinary persuasion, secret-disclosure gating, prompt/context canaries, runtime/path attempts, strict arguments, access locks, excavation, alternate report names, non-confession proof, API authentication and audit edits. A built-image probe found no setting/world/legacy solution/private-log mount in the public image. A world-container probe failed an external connection and found no API credentials. The offline V2 Docker integration passed its no-op/boundary smoke.

Live character calls under stronger pressure produced an incident in a four-participant calibration. This is not a measured probability increase or full-town calibration. Live questioning showed less disclosure before reassurance and a partial account afterward, with no private canary leak in the tested extraction attempt. A full isolated run submitted a report but is not claimed as a successful investigation; it exposed verifier name matching and provider-timeout issues, now covered by regressions.

The natural-language speaker can still hallucinate. The audit chain is tamper-evident relative to its retained head, not externally immutable. The trusted harness still holds control credentials and has provider-network access; it must not expose a shell to the model. Ghost mechanics, continuous offstage activity, full lifetime generation, exhaustive report interpretation and the complete hackathon multi-task oracle contract remain unfinished.
