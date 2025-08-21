---
icon: material/swap-horizontal
---

# Model Switching

Many users have very different workflows, and with how quirky IntenseRP Next can be, it's (sort of) best to support more of them. Hence why there are four ways of controlling reasoning.

DeepSeek itself currently only hosts two models, **DeepSeek V3.1 (NoThink)** (`chat`) and **DeepSeek V3.1 (Think)** (`reasoner`). NoThink is always used by default in their chat interface, unless you specifically toggle on `DeepThink` in their UI (which is what IntenseRP Next uses for reasoning).

## The Four Ways to Control Reasoning

Below are the four methods you can use to control the model usage, from the highest to the lowest priority.

### 1. Model Suffixes (Highest Priority)
The newest and most direct way to control reasoning is by choosing specific model variants in SillyTavern:

- **`intense-rp-next-1`** - Standard model, respects all other reasoning controls
- **`intense-rp-next-1-chat`** - Forces reasoning **OFF**, ignores everything else
- **`intense-rp-next-1-reasoner`** - Forces reasoning **ON**, but still respects Send Thoughts setting

These model variants appear in SillyTavern's model selection dropdown alongside the base model. When you select `-chat` or `-reasoner`, that choice overrides all other reasoning controls.

!!! example "Model Override in Action"
    Let's say you have Deepthink enabled globally, add `{{r1}}` to your message, or set `use_r1: true` in the API request. Normally this would definitely trigger reasoning mode.

    But if you're using `intense-rp-next-1-chat`, reasoning stays OFF. The model suffix wins every time. Even if all of the other options are enabled.

### 2. API Parameters (Second Priority)
When integrating directly with the API or using advanced SillyTavern features, you can control reasoning through request parameters:

```json
{
  "model": "intense-rp-next-1",
  "use_r1": true,
  "messages": [...]
}
```

The `use_r1` parameter directly tells IntenseRP Next whether to use reasoning mode for that specific request. This overrides message tags and global settings, but model suffixes still take precedence.

### 3. Message Content Tags (Third Priority)
You can activate reasoning for individual messages using special markers:

- `{{r1}}` - Standard reasoning activation
- `[r1]` - Alternative syntax
- `(r1)` - Another alternative

These tags are detected automatically and removed from your message before sending to DeepSeek. They're perfect for when you want reasoning on just one message without changing your global settings.

```
Hey, you. You're finally awake. How many fingers do you see? {{r1}}
```

!!! tip "Tag Placement"
    You can place reasoning tags anywhere in your message. They'll be stripped out before the message reaches DeepSeek, so they won't clutter your actual conversation.

### 4. Global Configuration (Lowest Priority)
The **DeepThink** toggle in DeepSeek Settings acts as your fallback default (though it's also the most obvious setting, I won't lie). When no higher-priority option specifies otherwise, this setting determines whether reasoning mode is used.

This is great for setting your general preference - if you like the DeepThink model's writing style, enable it here and it'll be your default unless you specifically override it.

## Still Sending Thoughts

There's one setting that works differently: **Send Thoughts**. This controls whether you see the `<think>` tags containing DeepSeek's reasoning process, but it only applies when reasoning is actually enabled.

Importantly, the `-reasoner` model respects the Send Thoughts setting. So you can force reasoning ON while still controlling whether you see the thinking process.

!!! warning "Network Interception Required"
    Send Thoughts only works with Network Interception enabled. If you're using DOM scraping, you won't see the reasoning process even when Send Thoughts is enabled.

---