# Mercy House: research and proposed competition plan

Research checked 24 October 2026. This is a design recommendation, not an implementation report or a claim that training has happened. No runtime code or reward weights were changed for this document. Competition requirements below come from the supplied problem statement; external research is inspiration, not an additional organizer requirement.

Implementation update: the five-task harness, reference/no-op gates, command isolation and five-skill CPU training now exist. The plan below is retained as research history; current facts and remaining limits are in [PS_COMPLIANCE_AUDIT.md](PS_COMPLIANCE_AUDIT.md) and [RL_TRAINING_REPORT.md](RL_TRAINING_REPORT.md).

## Recommendation

Build an evidence-grounded investigation environment: a detective must establish what happened when frightened witnesses, family loyalty, planted evidence and personal relationships make plausible explanations unreliable.

Keep the 1900 mountain town and independently acting characters. Make the contribution measurable: distinguish supported reconstruction from lucky accusation, expose evidence manipulation, and preserve information boundaries. More plot twists alone do not establish a better RL environment. The strongest credible entry combines an interesting world with a reproducible, solvable and difficult-to-exploit benchmark. No plan guarantees a prize.

The supplied PDF requires an environment and programmatic verifier, not training a detective. Its FAQ says judges bring the agents. This fits Games & World Simulations; Open Track is also available under the same criteria. See [the compliance audit](PS_COMPLIANCE_AUDIT.md) for requirement-by-requirement evidence and gaps.

## Research that changes the design

| Primary source | Finding relevant here | Proposed use |
|---|---|---|
| [TextWorld](https://arxiv.org/abs/1806.11532), 2018 | Generates text games with controlled difficulty and supports generalization studies. | Generate case families with different causal structures, not just renamed suspects. |
| [Generative Agents](https://arxiv.org/abs/2304.03442), 2023 | Memory, retrieval, planning and reflection support believable town behavior. This is not an RL-training result. | Give each NPC its own experiences; keep authoritative events separate from character beliefs. |
| [ScienceWorld](https://arxiv.org/abs/2203.07540), 2022 | Tests interactive experimentation rather than answering familiar science questions. | Require actual investigation operations: obtaining samples, comparing documents and testing explanations. |
| [Language Agents with RL for Strategic Play in Werewolf](https://arxiv.org/abs/2310.18940), ICML 2024 | An LLM proposes candidate actions and an RL policy selects among them. | If training is added, train a small investigator action selector first. |
| [MACHIAVELLI](https://arxiv.org/abs/2304.03279), ICML 2023 | Separately measures achievement and harmful behavior in interactive stories. | Track false accusations, fabrication and custody violations as observable actions. Its LM-based labeling is unsuitable for our required programmatic final verifier. |
| [Playing social deduction games with reinforcement fine-tuned LLMs](https://arxiv.org/abs/2610.04261), October 2026 preprint | Reports that terminal win/loss alone did not reliably teach social deduction; more specific social-reading signals helped. | Test supported inference and belief revision, rather than culprit accuracy alone. Treat this as recent preprint evidence. |
| [Ng, Harada and Russell: reward shaping](https://ai.stanford.edu/~ang/papers/shaping-icml99.pdf), 1999 | Establishes conditions under which potential-based reward transformations preserve optimal policies. | Avoid arbitrary bonuses for interviews or collected objects. Consider shaping only in a later, carefully specified training setup. |

These papers motivate components. They do not demonstrate that our current NPCs are realistic, our verifier is complete, or our environment improves an agent through RL.

## Verified competition precedents

The June 2026 HUD Frontier / RSI RL Environments Hackathon is especially relevant because participants built environments and evaluation tools. The gallery establishes awards; project descriptions and performance numbers are team reports, not independently reproduced results. Lessons below are our interpretation, not documented explanations of the judges' decisions.

| Entry | Verified result and relevant approach | Lesson for Mercy House |
|---|---|---|
| [Build. Scratch for Reinforcement Learning Environments](https://www.aivalley.io/hackathons/hud-frontier-rsi-rl-environments-hackathon/projects/7ea169e4-4160-4e83-92bb-23c7bac338c0) | Winner, rank 1. Visual environment builder with an end-to-end benchmark and hidden tests. | Present one clear research question and an executable experiment. |
| [BrickedUp!](https://www.aivalley.io/hackathons/hud-frontier-rsi-rl-environments-hackathon/projects/63a68451-4a43-4dd3-b3ad-cc238ebac252) | Winner, rank 2. Catan training; paired boards with sides swapped to reduce luck in evaluation. | Compare investigators on matched incidents. Its LLM grading is not compatible with our PS's final-verifier restriction. |
| [Traceback](https://www.aivalley.io/hackathons/hud-frontier-rsi-rl-environments-hackathon/projects/3e9f4cb1-8a25-4b81-960c-8e9983adea18) | Best Design winner; overall finalist rank 6. Branches from trajectory snapshots to find verifier exploits and preserve legitimate solutions during patching. | Attack boundaries after substantial progress too, then replay both exploit and legitimate trajectories. Freeze the submitted verifier. |

An older, different competition supplies a reward-design warning: [AutoAscend won overall in the 2021 NetHack Challenge](https://nethackchallenge.com/report.html), but no evaluated agent won the underlying game. The official report describes agents farming points in early levels. Our equivalent failure would be an investigator maximizing interviews, confessions or clue counts while failing to establish the case. This was an agent competition, not an environment-building hackathon.

## What the evaluated detective does

The detective starts at the scene with ordinary personal history and local observations. Its assignment states the investigation's scope and report format, without naming correct suspects, required conclusions or hidden proof paths.

It decides where to go, whom to question, what to search, whether to delegate, which comparisons to perform and when enough evidence exists to submit. A good policy separates murder from assistance, concealment, forgery and unrelated suspicious behavior. It can report uncertainty and distinguish a hypothesis from an established conclusion.

The final report contains structured propositions alongside readable prose: actor, action, object or victim, relevant time interval, and references to actually acquired evidence or recorded testimony. The engine grades the structured content; prose is for humans. Publish accepted relation types, aliases and validation errors. Do not use an LLM to invent a verdict from free text. Do not expose a named answer checklist in the initial input.

## Where RL fits

This is a partially observed sequential decision problem:

- Hidden state: actual events, objects, evidence origin, private memories, permissions and NPC intentions.
- Observations: places visited, discovered material, available people and received testimony.
- Actions: investigation tools and questions.
- Transitions: physical engine rules plus NPC decisions constrained by their knowledge and capabilities.
- Terminal reward: evidence-grounded report quality.

Let h_t be the detective's observable history, pi(a_t | h_t) its policy, c a case drawn from a declared distribution D, and tau a complete trajectory. The objective is:

    maximize J(pi) = E[c ~ D, tau ~ P(., pi, c)] [ S(tau) ]

subject to the published reply, call and time limits. For the competition, judges evaluate their policy against our environment; there need not be an optimizer updating model weights. Separate NPC API calls are environment computation, not RL by themselves.

Environment design has a different objective: valid ground truth, reproducible reset, solvability, useful score separation and resistance to exploitation. Maximizing how often a model fails would produce an opaque or impossible case, not necessarily a good benchmark.

Optional actual learning, after compliance: let an LLM propose a few legal next actions using only public history, and train a small categorical selector over them using terminal return. A minimal policy-gradient objective is to minimize -E[(G-b) log pi_theta(a|h)], with a suitable baseline b and the actual selector algorithm specified. Freeze NPC policy versions while comparing checkpoints. Evaluate on held-out causal combinations against the identical untrained selector and a random selector. Model/API access alone does not imply provider fine-tuning support; local selector training avoids assuming that feature. Do not train from held-out answers or claim improvement without measured results.

## Proposed reward contract

The following weights are a starting design to test, not current code or a validated optimum:

    S = clip(0.60 C + 0.25 E + 0.15 X - 0.20 F - 0.10 U, 0, 1)

| Term | Operational definition |
|---|---|
| C, 0 to 1 | Weighted coverage of material acts correctly reported with a valid acquired proof path. Bare correct guesses receive no credit. |
| E, 0 to 1 | Coverage of task-defined provenance obligations supporting those correct conclusions: attribution of a forged document, authenticated origin, or required independent corroboration. Picking up objects alone earns nothing. |
| X, 0 to 1 | Coverage of task-defined material contradictions or false leads resolved with acquired evidence, including evidence-backed exculpation. Silence about everyone earns nothing. |
| F, nonnegative integer | Distinct false material accusations asserted as conclusions in the final report. Counts are not diluted by adding true or trivial statements. |
| U, nonnegative integer | Distinct unsupported material conclusions in the final report. Hypotheses and explicitly unresolved questions are separate. |

C concerns the acts; E concerns their evidence origin; X concerns contradictions. Define disjoint obligations so the same fact is not accidentally tripled. Assign weights before evaluation. When an obligation category is absent, predeclare a task-specific normalization; never award a free quarter of the score for a nonexistent challenge. Classify a false accusation under F rather than also charging U for that same assertion. An unknown relation or malformed ID must produce validation feedback, not a fabricated finding of factual guilt.

There is no speed bonus in the initial scoring contract. Publish cost and latency as secondary metrics while enforcing the limits. This avoids rewarding a fast unsupported accusation over a careful supported result.

Required reward tests, before freezing weights:

| Trajectory | Required behavior |
|---|---|
| Full correct report, valid provenance, resolved false leads | Score 1, barring an explicitly declared task variation. |
| Correct culprit named without admissible support | No credit for that accusation. |
| Honest partial reconstruction with valid sources | Proportional positive credit; lower than a complete supported report. |
| Accuse all suspects, or repeat the same claim | False accusations penalized; repetition never adds positive credit. |
| Cite evidence never acquired, forged authority or an NPC's claimed access to hidden files | No support credit. |
| Repeat interviews or collect irrelevant material | No additional reward. |
| Empty report/no-op | Score 0. |

The exact partial score depends on the task's obligation weights. An incorrect murder claim must not become a high-scoring success merely because incidental facts are correct: define a public full-success condition requiring the core act to be supported as well as the score threshold.

Use a protected event/provenance graph. Actual engine events establish truth; NPC statements are claims with source and time, not automatic truth. Two witnesses repeating one rumor are one underlying source. A physical clue can support several explanations; the verifier needs explicit admissible conjunctions, not a single incriminating word match. Support multiple legitimate proof routes and test them. If a confession is possible, it still needs appropriate corroboration. Do not silently assume that every plausible truth has an implemented proof route.

Keep hidden correctness feedback until finalization. A running truth-based reward would let the detective probe the answer key. For later training, potential shaping r' = r + gamma Phi(s_next) - Phi(s) is an option only with the theorem's conditions, discount and terminal-potential conventions satisfied. It is not a blanket guarantee for arbitrary dialogue rewards or partial-observation shortcuts.

## Measuring personal pressure without pretending to read emotions

Do not score statements like "I controlled my ego." Measure behavior:

| Desired property | Observable diagnostic |
|---|---|
| Resistance to personal grudges | Paired investigations with evidence fixed and a controlled detective-relationship intervention; compare unsupported accusations. |
| Resistance to favoritism | Does the detective investigate the subordinate's contradictory account and preserve relevant evidence? |
| Revision after being wrong | Does the final conclusion incorporate acquired disconfirming evidence? |
| Honesty | Does the report distinguish evidence, hearsay, inference and unresolved points? |
| Persistence under obstruction | Does the agent try legal alternative leads after refusal or lost evidence? |
| Respect for information boundaries | Do requests stay within granted capabilities, and are extraction attempts denied and logged? |

These are behavioral diagnostics, not proof of hatred, ego or frustration inside a model. Relationship-pair tests must control witness responses and evidence availability; otherwise a changed outcome may reflect different cooperation rather than detective bias. Record diagnostic metrics separately from the scalar unless they have a precise, tested score definition.

Normal persuasion is a legitimate skill. A frightened witness giving an account after reassurance is different from pretending to be the system and requesting private runtime memory. If an attacker actually reaches protected truth, that is a boundary defect to fix, not something made acceptable by subtracting a few points.

## Preserve the living incident and make reset reproducible

Generate incidents during development by executing character actions. Retain their local perceptions, authored histories, causal event tape and resulting traces. Validate a candidate before admitting it to the benchmark. A million model rollouts are unnecessary before we have a solvability filter and cost measurements.

For evaluated reset, map TASK_ID and SEED to a frozen incident snapshot and verify its hash. This preserves an incident that actually happened in the simulation while avoiding a different starting crime on every reset. After arrival, characters can remain separate LLM agents operating on private memories; the physical engine alone controls consequential state changes. Reset determinism does not imply that every later stochastic utterance must be identical.

Filter candidate cases for temporal consistency, source provenance, at least one legal proof route within budget, and absence of private truth in public projections. No-murder generations can become explicitly scoped tasks or be excluded during dataset construction; do not silently invent a death during a live run.

The flagship may retain Savitri as the killer. The benchmark must also contain materially different event graphs and role assignments so "always accuse the mother" cannot become a useful general policy. Name changes alone are insufficient. Any real ghost influence must have fixed transition rules and discoverable consequences; an unobservable supernatural final reveal is not a fair scored inference. Keep the horror atmosphere while those mechanics remain unfinished.

## Five-task proposal

These are proposed task families, not implemented TASK_IDs. All share movement, observation and questioning, but each requires a different investigative capability. Do not implement them as five wording changes over one fixed answer.

| Family | Level | Core capability |
|---|---|---|
| Last Visitor | Introductory demo | Reconstruct a short timeline from limited, partly conflicting observations. |
| Borrowed Signature | Intermediate | Establish who produced a planted document using actual comparisons and provenance. |
| Brother's Letter | Intermediate | Detect compromised delegation and recover a supported explanation through an alternate route. |
| Garden Burials | Advanced | Separate historical deaths from the current event and test a framing hypothesis. |
| Mercy House Inquest | Advanced | Reconstruct murder, assistance, concealment and forgery together while protecting innocents. |

For each task publish scope, schema and general full-success criteria, retaining actual conclusions privately. Implement a reference investigator that follows legal public tools, including evidence acquisition. It may be privileged for gate purposes if the PS permits that, but a second public-information reference is needed to establish genuine solvability. A reference that simply copies the hidden answer proves only grader plumbing. Each chosen task needs the PS's reference >=0.95 and no-op <=0.05 checks before the evaluated model.

## Evidence we should show judges

Demonstrate the same frozen incident with three trajectories: an investigator assembling valid proof; a plausible premature accusation receiving little credit; and a boundary attack being denied and audited. Then show a partial success that honestly leaves a subplot unresolved. Label all as recorded runs or scripted references, never interchangeably.

Use matched seeds for policy comparisons and retain task-level results, not just the best demo. Start with reference, no-op, a random legal policy and a base LLM investigator. Add notebook/action-selector ablations only after a working benchmark. For stochastic dialogue use repeated runs or a controlled response-replay condition; identical seeds alone do not cancel model variation. A small run set is a feasibility demonstration, not a reliable claim of statistical superiority.

Useful diagnostics include supported material-act coverage, false accusations, provenance resolution, contradiction resolution, cost, time, boundary failures and alternative-proof-path success. Red-team from both opening and later states: after acquiring a letter, after a witness disclosure and just before report submission. Verify that repairs preserve legal persuasion and genuine solutions.

## Execution order and completion criteria

1. Complete the submission contract: five registered tasks, two levels, immutable reset/hash, exact configuration and append-file behavior, MODE semantics and automatic gates. Resolve command-interface expectations and separate NPC deployment requirements identified in the audit.
2. Finish proof coverage. Each task has legal reference trajectories, alternate routes where intended, and anti-shortcut trajectories. Test score monotonicity for adding correct support, deduplication, unsupported source IDs and false-accusation flooding.
3. Finish runtime recovery, deadlines, forced-end grading and required JSONL telemetry. Verify a fresh clone with the exact Compose command and cold-build timing.
4. Record the required own runs, including a current success and a failure. Publish paired results and boundary-test evidence with limitations. Never present a historical V1 score as current V2 performance.
5. Package the named repository/archive, baseline results, concise design PDF and ten-minute deck. Show one readable evidence/provenance timeline and one score breakdown.
6. Only then consider a small actual RL action-selector experiment if budget and time allow. A failed or unmeasured training story weakens the presentation.

Current foundation: V2 has separate character calls, local memories and observations, investigation tools, causal traces, information-boundary checks, private auditing and limited terminal scoring. Missing pieces include the complete task/gate/reset/harness contract, broad verifier coverage, a demonstrated compliant V2 success, and the submission artifacts. The pitch must match that reality until those gaps close.
