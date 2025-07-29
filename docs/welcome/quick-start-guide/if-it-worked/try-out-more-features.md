---
icon: material/rocket-launch
---

# Try Out More Features

:material-check-circle: **Congratulations!** You've successfully set up IntenseRP Next and connected it to SillyTavern. You're now ready to explore the full capabilities of this bridge between SillyTavern and DeepSeek.

## What's Next?

Now that you have the basics working, here are some features you might want to explore:

### Message Formatting

IntenseRP Next gives you control over how your messages are formatted when sent to DeepSeek. This can significantly improve response quality, especially for roleplay.

Try changing the **Formatting Preset** in Settings:

- **Classic (Name)** - Uses character names like "Sarah: Hello there!"
- **Wrapped (Name)** - Formats messages with XML-style tags: `<Sarah>Hello there!</Sarah>`
- **Divided (Name)** - Uses visual separators to clearly distinguish between speakers

For even more control, try the **Custom** preset which lets you define your own message templates.

### DeepSeek Special Features

DeepSeek has some unique capabilities that you can access through IntenseRP Next:

- **DeepThink (R1 Mode)** - Add `{{r1}}` or `[r1]` anywhere in your message to enable DeepSeek's reasoning mode, which makes responses more thoughtful and carefully considered
- **Web Search** - Include `{{search}}` or `[search]` to let DeepSeek search the web to enhance its response with current information

You can also enable these globally in Settings so you don't need to add the tags manually.

### Network Interception

If you're using Chrome (recommended), enable **Network Interception** in DeepSeek Settings. This feature:

- Captures responses directly from the network stream instead of the page
- Handles complex content like code blocks and LaTeX much better
- Provides more reliable streaming with fewer interruptions

??? tip "Pro Tip: Persistent Sessions"
    Enable **Persistent cookies** in Advanced Settings to maintain your DeepSeek login between sessions. This also helps with Cloudflare challenges, making your experience much smoother.

## Testing Your Setup

A quick way to test everything is working properly is to try a message with several features:

```
{{r1}} Tell me about the features of IntenseRP Next. Include a code example of how to use it with Python.
```

This will:

1. Activate DeepThink mode for a more comprehensive answer
2. Ask about the bridge itself (meta!)
3. Request a code block to test formatting

## Common Questions

??? question "Do I need to restart IntenseRP Next after changing settings?"
    Most settings take effect immediately, but some browser-related changes might require a restart. When in doubt, restart the application to ensure all your settings are applied.

??? question "Why does streaming pause sometimes during code blocks?"
    This is normal when using DOM scraping (without Network Interception). DeepSeek applies complex formatting to code blocks, which can temporarily interrupt the stream. Network Interception fixes this issue.

## Where to Go From Here

Ready to learn more about IntenseRP Next's capabilities? Check out these sections:

- [Advanced Configuration](../../features/advanced-configuration.md) for power-user settings
- [Formatting Templates](../../features/formatting-templates/pre-defined-templates.md) to customize how messages look
- [Troubleshooting](../if-it-didnt/troubleshooting.md) if you encounter any issues

Happy chatting with your AI characters!