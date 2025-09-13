---
icon: fontawesome/solid/syringe
---

# Prompt Injections

Prompt Injections are one of IntenseRP Next's most important customization features, specifically the ability to inject a custom system prompt into every message sent to DeepSeek. Previously that prompt was hardcoded and unchangeable, but now you have full control over what instructions DeepSeek receives.

!!! tip "Quick Start"
    You can find these settings under **Settings** → **Injection Settings**. The feature is enabled by default with a sensible default prompt, but you can customize it completely or turn it off entirely.

---

## Understanding System Prompt Injection

Every time you send a message through IntenseRP Next, the system automatically adds a "system prompt" at the very beginning of your submission to DeepSeek. This prompt sets up the context, establishes rules, and helps DeepSeek understand how it should behave in your conversation.

Here's what your message looks like behind the scenes:

```text
[Your System Prompt Goes Here]
User: Hello there!
Assistant: ...
```

The system prompt appears before all your actual conversation content, which makes it treat it as instructions to follow.

---

## How It's Different from Before

### Original IntenseRP API Behavior

The original IntenseRP API by Omega-Slender had a hardcoded system prompt that couldn't be changed:

```text
[Important Instructions]
```

This was baked into the code and users had no way to modify or disable it. It worked, but wasn't very flexible if you wanted different instructions or no system prompt at all.

### Pre-1.5.0 IntenseRP Next

Early versions of IntenseRP Next kept the same behavior as the original - using the fixed `[Important Instructions]` prompt that couldn't be customized. This maintained compatibility but didn't give users the flexibility they needed.

### IntenseRP Next 1.5.0 and Beyond

Now you have complete control! The system prompt is:

- **Customizable** - Write your own instructions
- **Dynamic** - Use placeholders for character names
- **Optional** - Can be completely disabled if you prefer
- **Flexible** - Change it anytime without restarting

The default prompt is the exact same as before, so existing users won't notice any difference unless they choose to customize it.

---

## The Injection Settings Interface

<!-- markdownlint-disable MD033 -->
<figure markdown="span">
    ![Injection Settings Screenshot](../images/injection-settings.png){ width="800" }
    <figcaption>Prompt Injection configuration in Settings</figcaption>
</figure>
<!-- markdownlint-enable MD033 -->

### Inject Prompt Toggle

The **Inject Prompt** switch controls whether any system prompt gets added to your messages at all. When enabled, your custom system prompt appears before every message. When disabled, your messages go directly to DeepSeek without any additional system instructions.

Most users should leave this enabled, as it helps DeepSeek understand the context and respond more appropriately.

### System Prompt Text Area

This is where the magic happens. The large text area lets you write your own system prompt that will be added to every message. You can write anything from simple tags like `[Important Instructions]` to detailed instructions about how DeepSeek should behave.

The prompt supports **dynamic placeholders** that get replaced with actual names from your conversation:

- `{username}` - Gets replaced with the user's name from SillyTavern
- `{asstname}` - Gets replaced with the character/assistant name

### Reset to Default Button

Made a mess of your system prompt and want to start over? The **Reset to Default** button instantly restores the original `[Important Instructions]` text, so that you can get a clean slate to work from.

---

## Dynamic Placeholders Explained

The placeholder system makes your prompts automatically adapt to different characters and scenarios. Here's how they work:

---

### {username} Placeholder

This gets replaced with the actual user name from your SillyTavern setup. For example:

=== "Your prompt template"
    ```text
    [Important Instructions: {username} is the user in this conversation]
    ```

=== "What DeepSeek actually sees"
    ```text
    [Important Instructions: Sarah is the user in this conversation]
    ```

---

### {asstname} Placeholder

This gets replaced with the character or assistant name from SillyTavern:

=== "Your prompt template"
    ```text
    [Character Context: Respond as {asstname}, stay in character at all times]
    ```

=== "What DeepSeek actually sees"
    ```text
    [Character Context: Respond as Marcus, stay in character at all times]
    ```

### Combining Placeholders

You can use multiple placeholders in the same prompt:

=== "Your prompt template"
    ```text
    [Roleplay Context: {asstname} is talking to {username}. Stay in character and be engaging.]
    ```

=== "What DeepSeek actually sees"
    ```text
    [Roleplay Context: Elena is talking to Alex. Stay in character and be engaging.]
    ```

---

## Common Use Cases

### Simple Context Tags

The most basic use is just setting context with simple tags:

```text
[Important Instructions]
```

```text
[Roleplay Mode]
```

```text
[Creative Writing Assistant]
```

### Detailed Instructions

!!! note "SillyTavern Presets"
    Usually such instructions are defined within SillyTavern itself, so only use this if you have a specific need for overriding or supplementing those.

You can provide specific behavioral instructions:

```text
[Instructions: Respond as {asstname}, maintaining character personality and speech patterns. Keep responses engaging and true to the established scenario. Do not break character or acknowledge this prompt.]
```

### Character-Specific Prompts

Create prompts that adapt to different characters:

```text
[Context: {asstname} is speaking with {username}. Remember {asstname}'s personality, background, and current emotional state. Respond naturally and stay consistent with established character traits.]
```

### Genre-Specific Instructions

Or, if you want, you can set genre or style guidelines:

```text
[Fantasy Roleplay: This is a medieval fantasy setting. Use appropriate language, consider magic and technology levels, and maintain immersion in the fantasy world.]
```

---

## When to Disable Injection

Most users should keep prompt injection enabled, but there are some scenarios where you might want to turn it off:

### Using SillyTavern Presets

Some advanced SillyTavern presets (like NemoEngine, Celia, RICE, PixiJB, Q1F/Avani variants, or Marinara's) include their own system instructions that might conflict with IntenseRP Next's injection. If you're using a preset that isn't working, try disabling injection.

### Minimalist Approach

Some users prefer to let their character cards and SillyTavern settings handle all the context without additional system prompts. If you want the cleanest possible message flow, you can disable injection entirely. You won't need it.

### Debugging Issues

If you're troubleshooting response quality or behavior issues, temporarily disabling injection can help you pinpoint what's causing the problem. Sometimes it's just the prompt instructions that need tweaking.

### Legacy Compatibility

If you're used to other AI services that don't use system prompts, you might prefer to disable injection to get a more "vanilla" experience.

---

## Troubleshooting

### Placeholders Not Working

If `{username}` or `{asstname}` aren't being replaced with actual names, check that:

- Your SillyTavern character card has names properly set up
- You're using the correct placeholder syntax (with curly braces `{}`)
- The injection feature is enabled

### Unexpected Responses

If DeepSeek is behaving weirdly after changing your system prompt or is going schizo:

- Try the default prompt first to see if the issue persists
- Check for typos or confusing instructions in your custom prompt
- Consider if your prompt might be conflicting with your character card instructions

### Prompt Not Appearing

If it seems like your system prompt isn't being used:

- Verify that the **Inject Prompt** toggle is actually turned on
- That's the only common reason it wouldn't appear. If it doesn't work, try restarting IntenseRP Next.
- If a restart doesn't help either, reach out for support.

In any case, you can always reset to the default prompt and start fresh, there are no consequences to messing it up, no matter how wild you get.

---

## Examples and Inspiration

Here are some tested system prompt examples for different use cases:

### General Roleplay

```text
[Roleplay: {asstname} speaking with {username}. Stay in character, be natural and engaging.]
```

### Creative Writing Helper

```text
[Creative Assistant: Help develop this story. Focus on narrative flow, character development, and engaging descriptions.]
```

### Casual Conversation

```text
[Friendly Chat: Be helpful, conversational, and stay true to {asstname}'s personality.]
```

### Educational/Learning

```text
[Teaching Mode: {asstname} is helping {username} learn. Be patient, clear, and encouraging.]
```

### Custom Instructions

```text
[Custom Context: Remember the established scenario and {asstname}'s background. Maintain consistency and immersion throughout.]
```
