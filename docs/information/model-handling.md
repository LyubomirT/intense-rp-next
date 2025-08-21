---
icon: material/brain
---

# Model Handling

When using IntenseRP Next, you're working with DeepSeek's chat interface rather than their API. This means certain aspects of the model's behavior are completely out of your hands, no matter what settings you adjust in SillyTavern or IntenseRP Next.

## Sampling Parameters: Set in Stone

If you're used to tweaking temperature, top-p, or other sampling parameters in SillyTavern, you'll need to adjust your expectations here. The DeepSeek chat interface doesn't expose these controls. Every response you get uses whatever parameters DeepSeek has decided on for their web interface.

You might try adding instructions to your system prompt like "use a temperature of 1.2" or "limit responses to 500 tokens," but these are just suggestions to the model, not actual parameter changes. The model might acknowledge these instructions, but it won't actually change its underlying sampling behavior.

## The Behind-the-Scenes Settings

DeepSeek has been relatively transparent about some of their system settings. At one point, they published information suggesting their chat interface uses:

- **Temperature**: Either 0.6 or 0.3 (sources vary on which)
- **Top-p**: 0.95
- **Other parameters**: Unknown

These conservative temperature values explain why responses through the chat interface tend to be more consistent and less creative compared to what you might get with higher temperatures through the official API. It's optimized for general chat rather than creative writing.

!!! info "System Prompt"
    Some sources say there is a system prompt, some say there isn't. I wouldn't rely on it being there, but if it is, it likely contains instructions to keep responses "safe and appropriate for a wide audience." This is why you might see more conservative or filtered content compared to using the API directly.

## Content Filtering Differences

Here's something important to know: the chat interface includes content filtering that isn't present in the open-source DeepSeek models or their official API. This means your roleplay might occasionally bump into guardrails that wouldn't exist elsewhere.

The filtering can be... unpredictable. Sometimes perfectly innocent content gets flagged, while other times surprisingly bold content sails through. If your roleplay tends to explore mature themes or venture into spicier territory (we've all been there :material-fire:), you might find the chat interface more restrictive than expected.

!!! info "Working With the Limitations"
    Since you can't adjust the model's parameters directly, your best bet is to work with what you have. Clear, specific prompts tend to work better than trying to fight the system. If you need more creative responses, consider being more explicit about wanting varied or unexpected outputs in your character cards or system prompts.

!!! warning "Content Filtering"
    DeepSeek likely applies a word-based content filter. Meaning that **theoretically**, you could bypass it by using synonyms or creative phrasing. Though, this is risky and could lead to lower quality responses. If you find yourself needing to do this often, it might be worth considering whether the chat interface is the right tool for your roleplay needs.

## The Trade-offs

Using the chat interface through IntenseRP Next means accepting these limitations in exchange for free access to DeepSeek's models. You lose fine-grained control over model behavior, but you gain a straightforward way to use capable AI models without API costs.

For many users, especially those doing casual roleplay rather than highly technical applications, these limitations won't significantly impact the experience. The models are still quite capable within their constraints, and creative prompt engineering can often achieve the results you're looking for.

If you absolutely need control over sampling parameters or want to avoid content filtering, you'll need to use DeepSeek's official API directly (which involves costs) or run their open-source models locally (which requires significant hardware), or use a different service (like Fireworks, OpenRouter, Chutes, TogetherAI, etc.) that does the hosting for you.

!!! info "Other Providers"
    Different providers have different policies, different parameter support, different inference engines, and could even have different quantizations or model versions. Be careful if you do venture into that territory, the experience can vary widely. Most of the providers are paid, too. Some are cheaper than the others, but they all have their own quirks and limitations. Always check the documentation for the specific provider you're using to understand how they handle model parameters and content filtering.

    If you're just looking to explore, OpenRouter is a great place to start looking at different providers, as they aggregate many models and let you compare them easily. Just keep in mind that not all models will be available for free, and some might have their own restrictions or quirks.

## A Note on Model Selection

Interestingly enough, the chat interface lets you choose the exact same models as the API.

Specifically:

- The V3.1 (NoThink) model for standard responses
- The V3.1 (Think) reasoning model when you enable DeepThink

On the API, identical models are used, labeled as `deepseek-chat` and `deepseek-reasoner` respectively. Though other providers likely offer other DeepSeek models like the original R1, or variants like R1-0528 Qwen distills or Chimera merges.

The silver lining? You're always using their latest and most optimized models for chat interactions, even if you can't customize how they behave.