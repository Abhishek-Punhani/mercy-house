# Story viewer

Open https://mercyhouse.abhi07.xyz, or run `python -m mercy.viewer.server` locally and open http://localhost:8787. **Quick tour** explains the controls. Recorded cases cost no model calls; **New investigation** starts the standard isolated detective harness.

Choose a case, read its public briefing, select a provider and model ID, enter a provider API key, and start. The public site uses that visitor key for both detective and character calls. It stores no team key. Local judging configurations keep the two model roles separate. A chat-product subscription is not an API credential.

## What appears

The scene follows actual movement and observed people. Dialogue is the question and answer returned by the environment. The evidence tray contains acquired records; the interview notebook retains observed exchanges. Notes and hypotheses are the detective's stated claims, not verified facts or hidden reasoning. The final report and its cited records remain visible with supported, false and unsupported findings.

The library distinguishes actual API runs, scripted references and trained-selector checkpoints. Checkpoints can contain prior acquired material; they are not whole-case successes. Recorded failures remain available.

## Providers

The selector includes OpenAI, Anthropic, Gemini, OpenRouter, Groq, DeepSeek, Mistral, Together, Fireworks, xAI and Cerebras, plus configured and custom options. Claude's official endpoint uses a Messages API adapter. The others use compatible Chat Completions endpoints. Choose a model supporting tool calls and JSON output. Deployment names are entered by the user.

Custom endpoints must use public HTTPS on port 443. DNS results are validated and connections are pinned to a validated public address with TLS hostname verification. Redirects and proxy environment variables are not used. Azure's compatible v1 API can use its `/openai/v1` base. Bedrock signing, Vertex service accounts, custom authentication headers and private/local endpoints are not implemented. Protocol fixtures cover adapters; real provider tests used the organizer's deployment only.

Changing providers clears the key and model fields. Keys are not returned in public responses, written to configuration files, stored in browser storage or copied into source snapshots. Only the browser that starts a public run receives its Stop token. The public library is shared and is not private account storage.

## Optional voice

Voice mode uses the browser speech service, with no model audio call or microphone. One playback loop waits for each spoken exchange while incoming live events buffer. Pausing affects the viewer; the detective continues running. Seeking, changing runs or disabling voice cancels pending speech and removes highlights.

Word highlighting uses browser boundary events. If those events are unavailable, the speaking paragraph is outlined instead. Installed English voices are assigned consistently to characters, preferring local voices. Devices with fewer voices reuse them, and some browser-provided voices may use online speech. Text remains readable if speech fails. Check audibility on the presentation laptop.

## Limits and validation

The viewer serves explicit assets and public event endpoints. It excludes private memories, the hidden journal, raw private character context and provider credentials. Host/Origin checks and CSRF protect writes; private paths are denied. It assumes a trusted host and Docker daemon.

Browser checks cover desktop/mobile layout, provider configuration, tour, reports, source links, buffered live bursts, speech cancellation and word boundaries. Speech timing fixtures do not certify device audio. Machine results are in `FINAL_VIEWER_VALIDATION.json`, `FINAL_HOSTED_BROWSER.json` and `BRIEFING_VOICE_VALIDATION.json`.

The caption-only tutorial is `investigation-end-to-end.mp4`. It starts a fresh public-site investigation through the real form, then shows the final report and sources. Its manifest is `INVESTIGATION_VIDEO.json`. The older `submission-walkthrough.mp4` is separately labeled as a retained-replay overview.


Practice runs use 100 replies for intermediate/advanced cases and 40 for introductory cases. The website enables practice mode automatically. For a local extended run set `MERCY_PRACTICE=1`; default official judging remains 40 replies. Both modes keep the 600-second timer and ten tools per reply. Practice scores are labeled separately and are not judging-limit results.
