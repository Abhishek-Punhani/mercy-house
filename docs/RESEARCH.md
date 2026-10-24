# Research behind Mercy House

These sources informed the design. Their results are not evidence that Mercy House's own agents generalize or that its optional selector solves complete investigations.

| Source | Connection to this implementation |
|---|---|
| [TextWorld](https://arxiv.org/abs/1806.11532) | Stateful text interaction, controlled task difficulty and seeded resets. Mercy House uses four authored causal families rather than an open-ended story generator. |
| [ScienceWorld](https://arxiv.org/abs/2203.07540) | Require interactive experiments and acquired observations rather than accept an unsupported answer. |
| [Generative Agents](https://arxiv.org/abs/2304.03442) | Character-local memories and planning. Our authoritative events are separate from beliefs; continuously autonomous offstage lives are not implemented. |
| [Language Agents with RL for Strategic Play in Werewolf](https://arxiv.org/abs/2310.18940) | An LLM proposes actions while a smaller learned policy chooses among them. Our CPU selector changes ranking weights, not LLM weights. |
| [MACHIAVELLI](https://arxiv.org/abs/2304.03279) | Distinguish achievement from harmful behavior. We penalize false/unsupported accusations, using programmatic provenance rather than an LLM judge. |
| [Policy invariance under reward transformations](https://ai.stanford.edu/~ang/papers/shaping-icml99.pdf) | A reason to avoid arbitrary bonuses for collecting objects or asking many questions. No potential-based shaping is claimed in the submitted reward. |

The optional source-mechanism selector trained on original checkpoint exercises inspired by broad mystery mechanisms, not TV scripts. Its exact data, candidate rules, weights and held-out results are documented in `SOURCE_TRAINING_REPORT.md`. The excluded full-case comparison is `ELITE_TRANSFER_REPORT.md`; both arms solved zero of two cases under those frozen conditions. Later cooperation changes were not part of that experiment.

Earlier competition research identified the HUD Frontier/RSI environment hackathon projects [Build](https://www.aivalley.io/hackathons/hud-frontier-rsi-rl-environments-hackathon/projects/7ea169e4-4160-4e83-92bb-23c7bac338c0) and [BrickedUp](https://www.aivalley.io/hackathons/hud-frontier-rsi-rl-environments-hackathon/projects/63a68451-4a43-4dd3-b3ad-cc238ebac252). Those project pages motivated executable demonstrations and matched evaluation conditions. Their awards and team-reported results do not predict this competition's outcome.
