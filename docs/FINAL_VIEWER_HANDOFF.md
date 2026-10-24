# Final viewer handoff

The public demo is https://mercyhouse.abhi07.xyz. Use **Quick tour** for the seven-step introduction. First-time visitors see an invitation to take it; the tour can be reopened at any time. It never starts a paid investigation.

## Starting with another provider

**New investigation** offers the configured hackathon endpoint, OpenAI, Anthropic, Google Gemini, OpenRouter, Groq, DeepSeek, Mistral, Together, Fireworks, xAI, Cerebras, and a custom OpenAI-compatible HTTPS endpoint. Enter a model ID available to your account and its provider API key. The model must support tool calling and JSON output; a provider preset does not guarantee that every model on that provider implements both. API keys are separate from consumer chat subscriptions. Changing providers clears the key and model field so that an old provider's credential is not reused accidentally.

Claude's official endpoint uses a Messages API adapter, including tool calls, tool results and JSON-only character prompts. Gemini uses its documented OpenAI-compatible endpoint. Other presets and custom providers use Chat Completions. For Azure's v1 API, use the resource's `/openai/v1` API base. Deployment names are entered by the user; there is no hardcoded model list. Custom Claude proxies should expose the compatible Chat Completions protocol, such as through LiteLLM. Bedrock's signed AWS API, Vertex service-account authentication, arbitrary custom authentication headers, private/local endpoints, and consumer subscription logins are not implemented.

On the public site, the visitor's key powers both detective and character agents for that run. The public host holds no team API key. Local/judging configurations retain separate character credentials. The configured local key cannot be forwarded to a different provider. Provider endpoints must resolve exclusively to public IP addresses. The gateway resolves again for each request, validates all returned addresses, connects directly to a validated address, and uses the original hostname for TLS certificate checking and SNI. It does not follow redirects or honor proxy environment variables. Browser code never receives the model gateway's credentials.

## Voice playback

Incoming live events enter a buffer immediately. One playback loop displays and narrates each exchange before advancing, even when the investigation has already finished in the background. Pausing affects only the viewer, not the running detective. Switching off voice, seeking, changing runs or closing a reading cancels pending speech and removes highlighting. Rereading a conversation pauses playback first.

The spoken text contains the actual public question and answer. Character names are not repeatedly prepended. Long text is split without rewriting whitespace, and speech boundary offsets map back to the original text. The current word highlights when the browser supplies word-boundary events. A browser without these events outlines the speaking paragraph instead; it does not display invented word timings. Failed or unavailable speech falls back to readable text.

Each character has a consistent voice assignment during the page session, preferring installed local English voices. Different characters receive different voices while enough are available; voices are reused when the device has fewer voices than characters. This uses the browser speech service, with no model audio call or additional audio server. Some browser-provided voices may use that browser's online speech service. Device audibility and voice availability need a manual check on the presentation laptop.

## Evidence for this update

- `FINAL_VIEWER_VALIDATION.json`: real browser interactions, with a controlled speech-event fixture to reproduce live event bursts, word boundaries, cancellation, mobile layout and the tour. No model calls.
- `FINAL_NATIVE_SMOKE.json`: a fresh isolated Lantern Room investigation scored 1.0 in 142.804 seconds and 24 detective replies. It asked Nell five questions, Maren four and Tobin four, including shown-record follow-ups. This is one development run, not a reliability estimate.
- `PROVIDER_TRANSPORT_SMOKE.json`: two real calls through the new DNS-pinned transport to the organizer endpoint, covering detective tool calling and character JSON output. Other providers have protocol fixture tests; no claim of paid live testing across all brands.
- Final regression suite: 127 town/runtime tests, 9 earlier tests, and 15 browser-state/speech tests passed. A fresh no-cache build of all four images completed in 21.587 seconds locally. These are engineering checks, not model-solving success rates.
- `submission-walkthrough.mp4`: captioned screen recording of actual viewer interactions with retained API investigation replays. No fresh live case is presented as running; no API key or hidden case file appears. The recording has no audio track. `SUBMISSION_VIDEO.json` identifies the chapters and recording details.

## Submission status

The environment, baseline routes, public viewer, CPU-trained action selector, editable presentation, design document and packaged trajectories are available. The core remaining weakness is full-case policy transfer: both frozen elite cases scored zero. Prepared checkpoint gains do not establish strong autonomous investigation. A small development set solved introductory cases, while important characters can still refuse crucial evidence in harder cases. Before presenting, try voice on the actual laptop, rehearse the walkthrough and finish the organizer's submission form and required character-model configuration. No result guarantees a competition win.

## API references

Wire adapters follow [Claude tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview), [Gemini compatibility](https://ai.google.dev/gemini-api/docs/openai), [Groq API](https://console.groq.com/docs/api-reference), [Together compatibility](https://docs.together.ai/docs/inference/openai-compatibility), [Fireworks compatibility](https://docs.fireworks.ai/tools-sdks/openai-compatibility), and [Cerebras compatibility](https://inference-docs.cerebras.ai/resources/openai). Word highlighting uses the [browser speech boundary event](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesisUtterance/boundary_event), which is not available consistently across browsers.
