---
icon: providers/aistudio
---

# :providers-aistudio: Google AI Studio Behavior

This page covers the toggles and options that control how IntenseRP interacts with **Google AI Studio** (`aistudio.google.com`).

---

## :material-tune: Modes (model IDs)

In IntenseRP Next v2, the `model` you select in SillyTavern is still mostly a **behavior preset**, not a true Gemini model picker.

For Google AI Studio, these model IDs map to the following behavior:

| Model ID | Behavior |
|---|---|
| `aistudio-auto` | Uses your IntenseRP settings |
| `aistudio-chat` | Suppresses `<think>` output and lowers Thinking Level on supported Gemini 3 / 3.1 models |
| `aistudio-reasoner` | Uses your configured Thinking Level and Send Thinking setting |

!!! note "Why chat mode works differently here"
    Google AI Studio's supported Gemini models do not expose a true "thinking off" switch the way some other providers do.

    So IntenseRP approximates a chat-like mode by:

    - lowering Thinking Level to the minimum available (when the model supports it), and
    - suppressing `<think>` output to the client

---

## :material-chip: Real Gemini model selection (web UI)

Google AI Studio has a real Gemini model picker in the web UI:

:material-arrow-right: **Settings** -> **Provider Behavior** -> **Google AI Studio** -> **Model**

Currently supported:

- `Gemma 4 31B IT`
- `Gemma 4 26B A4B IT`
- `Gemini 3.1 Pro`
- `Gemini 3.1 Flash Lite`
- `Gemini 3 Flash`
- `Gemini 2.5 Pro`
- `Gemini 2.5 Flash`
- `Gemini 2.5 Flash Lite`

This is separate from the API `aistudio-*` behavior presets.

---

## :material-login: Authentication

Google AI Studio uses a Google login flow. IntenseRP supports both:

- **Manual login**
- **Auto Login** (best-effort Google form autofill)

!!! warning "Persistent Sessions strongly recommended"
    Google can still ask for manual confirmation, CAPTCHAs, or extra account checks even when Auto Login is enabled.

    In practice, **Persistent Sessions** are the main quality-of-life feature here. If your Google session stays alive, AI Studio becomes much smoother to use.

!!! note "First-use legal acknowledgement"
    On accounts that have never used AI Studio before, Google may show a legal / terms acknowledgement modal after login.

    IntenseRP now detects that modal, notifies you, and waits for **you** to accept it manually before continuing with setup.

### Auto Login Redirect Timeout

If Auto Login fills your credentials but Google does not return to AI Studio quickly enough, IntenseRP falls back to manual completion.

:material-arrow-right: **Settings** -> **Provider Behavior** -> **Google AI Studio** -> **Auto Login Redirect Timeout (s)**

Default is 15 seconds.

---

## :material-head-cog: Thinking

Google AI Studio exposes **Thinking Level** instead of a simple on/off reasoning toggle.

### Enable Thinking

When enabled, IntenseRP uses your configured **Thinking Level** on supported Gemini 3 / 3.1 models.

When disabled, IntenseRP falls back to the lowest available level instead.

:material-arrow-right: **Settings** -> **Provider Behavior** -> **Google AI Studio** -> **Enable Thinking**

### Thinking Level

Controls the level IntenseRP selects on supported Gemini 3 / 3.1 models:

- `Minimal`
- `Low`
- `Medium`
- `High`

:material-arrow-right: **Settings** -> **Provider Behavior** -> **Google AI Studio** -> **Thinking Level**

!!! note "Gemini 2.5 models"
    Gemini 2.5 models use a different internal budgeting system, so IntenseRP does not apply Thinking Level changes to them.

### Send Thinking

When enabled, Gemini thinking summaries are included in the API response, wrapped in `<think>` tags.

:material-arrow-right: **Settings** -> **Provider Behavior** -> **Google AI Studio** -> **Send Thinking**

---

## :material-magnify: Search and URL Context

Google AI Studio exposes two browsing-style tools in the web UI:

### Enable Search

Toggles **Grounding with Google Search**.

:material-arrow-right: **Settings** -> **Provider Behavior** -> **Google AI Studio** -> **Enable Search**

### Enable URL Context

Toggles **URL Context** browsing.

:material-arrow-right: **Settings** -> **Provider Behavior** -> **Google AI Studio** -> **Enable URL Context**

!!! note "Grounding payloads"
    AI Studio can emit extra grounding/search payloads into the same response stream. IntenseRP strips those provider-specific payloads and forwards only the assistant text.

---

## :material-text-box-edit: System Prompt Field

AI Studio has its own **System Instructions** box, and IntenseRP can optionally use it for the leading `system` messages in your chat.

:material-arrow-right: **Settings** -> **Provider Behavior** -> **Google AI Studio** -> **Use System Prompt Field**

When this is enabled, IntenseRP:

- pulls consecutive `system` messages from the start of the request
- pastes them into AI Studio's native System Instructions UI
- removes those leading `system` messages from the normal chat prompt before sending
- also moves your configured prompt injection there when **Injection Position** is set to `Before`

Anything after the first non-`system` message stays in the normal prompt on purpose. Mid-chat `system` messages are left alone, because AI Studio's separate system field is global to the whole chat and mixing both behaviors would get weird fast.

!!! note "Startup cleanup"
    AI Studio stores system instructions in browser local storage. When this option is enabled, IntenseRP clears that local cache once on page load and refreshes the tab so old instructions do not pile up.

---

## :material-file-upload: File Upload Mode

Google AI Studio can now upload the prompt as a text file through its native media picker flow.

:material-arrow-right: **Settings** -> **Provider Behavior** -> **Google AI Studio** -> **Send As Text File**

This is a best-effort implementation because AI Studio does not expose a clean direct file input - it opens a native picker from the media menu instead.

!!! note "First upload on a fresh AI Studio account"
    On accounts that have not uploaded media before, AI Studio may show a copyright acknowledgement dialog after you pick the file.

    IntenseRP now waits briefly for that dialog and clicks **Agree to the copyright acknowledgement** automatically when it appears.

### Text File Message

Optional text to send alongside the uploaded prompt file.

Leave it empty to try file-only requests.

:material-arrow-right: **Settings** -> **Provider Behavior** -> **Google AI Studio** -> **Text File Message**

### File Upload Timeout

Controls how long IntenseRP waits (in seconds) for the send button to become available after the file is selected.

:material-arrow-right: **Settings** -> **Provider Behavior** -> **Google AI Studio** -> **File Upload Timeout**

---

## :material-tune: Sampling and output controls

Google AI Studio is currently the only provider in IntenseRP that applies all 3 of these OpenAI-style request controls in the web UI:

- `temperature`
- `top_p`
- `max_tokens`

You can set defaults in Settings, and request-level API values still win when provided.

### Temperature

:material-arrow-right: **Settings** -> **Provider Behavior** -> **Google AI Studio** -> **Temperature**

Default is `1.0`.

### Top P

:material-arrow-right: **Settings** -> **Provider Behavior** -> **Google AI Studio** -> **Top P**

Default is `0.95`.

### Max Output Tokens

:material-arrow-right: **Settings** -> **Provider Behavior** -> **Google AI Studio** -> **Max Output Tokens**

Default is `65536`.

---

## :material-shield-off: Safety Filters

On first AI Studio startup, IntenseRP automatically moves AI Studio's safety sliders to their lowest position once for that browser session.

!!! warning "What it does"
    This does not guarantee uncensored output. It only lowers the safety sliders that AI Studio exposes in the UI.

---

## :material-shield-off: Anti-Censorship

Google AI Studio can hard-block a reply on the backend. When that happens, you usually get either:

- no usable assistant text in the stream, or
- a turn in the UI that shows **Content blocked** in the **Safety Ratings** button area

:material-arrow-right: **Settings** -> **Provider Behavior** -> **Google AI Studio** -> **Anti-Censorship**

When this is enabled, IntenseRP does an invasive recovery flow:

1. It watches the intercepted AI Studio response and the latest assistant turn for a hard-block signal
2. If the turn is blocked, IntenseRP edits that assistant message in-place
3. It replaces the blocked turn with your configured **Replacement Message**
4. It sends your configured **Continue Nudge** as a normal text message
5. It retries this up to 3 follow-up nudges

Blocked attempts stay hidden from the API stream. As soon as a recovery attempt reaches real assistant answer text again, that retry streams normally.

!!! note "Not the same as DeepSeek"
    DeepSeek anti-censorship is basically a frontend workaround. AI Studio's version is more of a backend recovery trick, because the censorship is enforced deeper in the request/response flow.

!!! warning "Reuse Matching Chat gets disabled for that chat"
    If IntenseRP detects hard censorship in the current AI Studio chat, it clears that chat out of the clean-regeneration cache.

    In plain English: the next identical request will start fresh instead of trying to regenerate inside that now-cursed chat.

### Replacement Message

Text used to replace the blocked assistant turn before IntenseRP sends the continue nudge.

Default is `.`.

:material-arrow-right: **Settings** -> **Provider Behavior** -> **Google AI Studio** -> **Replacement Message**

### Continue Nudge

Text IntenseRP sends as the next user message after a blocked assistant turn is replaced.

Default is `Continue.`.

:material-arrow-right: **Settings** -> **Provider Behavior** -> **Google AI Studio** -> **Continue Nudge**

!!! tip "Sent as plain text"
    The continue nudge is always typed into the composer normally.

    Even if **Send As Text File** is enabled for the original prompt, IntenseRP does **not** upload the nudge as a file.

---

## :material-refresh: Reuse Matching Chat

When enabled, IntenseRP tries to click AI Studio's regenerate action if:

1. The new prompt matches the cached last prompt
2. Effective AI Studio settings also match

Otherwise it opens a fresh chat.

:material-arrow-right: **Settings** -> **Provider Behavior** -> **Google AI Studio** -> **Reuse Matching Chat**

!!! note "No Search Older Matching Chats here (yet)"
    Google AI Studio does **not** support **Search Older Matching Chats** right now.

    So for AI Studio, **Reuse Matching Chat** only checks the currently remembered latest chat instead of trying older cached conversations.

!!! note "Blocked chats are skipped"
    If AI Studio hard-censors a turn and **Anti-Censorship** kicks in, IntenseRP clears that chat from the clean-regeneration cache instead of reusing it later.

---

## :material-translate: UI language requirement

The Google AI Studio driver currently expects the AI Studio UI language to be English (`en` / `en-US`).

If you see a warning about the language:

1. Switch your Google account language to **English**
2. Reload the AI Studio tab
3. Retry / restart the browser from IntenseRP if needed

---

## :material-code-tags: Per-message macros

You can add `[[...]]` macros to the latest user message to override behavior for that request only.
All macros are stripped before sending.

| Macro | Effect |
|------|--------|
| `[[think]]` | Use the configured Thinking Level |
| `[[nothink]]`, `[[r0]]` | Force the lowest available Thinking Level and suppress `<think>` output |
| `[[r1]]`, `[[r2]]`, `[[r3]]`, `[[r4]]` | Pick a Thinking Level tier (mapped per model) |
| `[[search]]` | Force Search on |
| `[[nosearch]]`, `[[no_search]]` | Force Search off |
| `[[url]]`, `[[urlcontext]]` | Force URL Context on |
| `[[nourl]]`, `[[no_url]]` | Force URL Context off |

!!! tip "Model-name suffixes"
    You can also append a Thinking Level suffix directly to the API model string, for example:

    - `aistudio-auto-high`
    - `aistudio-auto-low`
    - `aistudio-auto-r4`

    IntenseRP strips that suffix, applies the Thinking Level override, then processes the remaining `aistudio-*` behavior preset as normal.

---

## :material-format-list-checks: Quick Reference

| Setting | What It Does | Default |
|---------|--------------|---------|
| **Model** | Selects AI Studio's real Gemini model picker | Gemini 2.5 Flash |
| **Enable Thinking** | Uses a higher Thinking Level on supported Gemini 3 / 3.1 models | Off |
| **Thinking Level** | Picks the Thinking Level when Thinking is enabled | Medium |
| **Send Thinking** | Includes Gemini thinking summaries in response | Off |
| **Enable Search** | Toggles Google Search grounding | Off |
| **Enable URL Context** | Toggles URL Context browsing | Off |
| **Use System Prompt Field** | Moves leading system messages into AI Studio's System Instructions UI | Off |
| **Send As Text File** | Uploads the prompt through AI Studio's media picker | Off |
| **Text File Message** | Optional text sent alongside the uploaded file | (empty) |
| **File Upload Timeout** | Seconds to wait for the send button after file selection | `20` |
| **Anti-Censorship** | Detects blocked AI Studio turns and runs the edit + continue workaround | Off |
| **Replacement Message** | Text used to replace a blocked assistant turn before retrying | `.` |
| **Continue Nudge** | Follow-up user message sent after a blocked turn | `Continue.` |
| **Temperature** | Default temperature | `1.0` |
| **Top P** | Default top-p value | `0.95` |
| **Max Output Tokens** | Default output token budget | `65536` |
| **Auto Login Redirect Timeout (s)** | Wait before falling back to manual Google completion | `15` |
| **Reuse Matching Chat** | Regenerates on duplicate prompts | Off |

---

## :material-arrow-left: Back to Providers

[:material-arrow-left: Providers Overview](../providers.md)
