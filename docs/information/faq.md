---
icon: material/help-circle-outline
---

# Frequently Asked Questions

Got questions about IntenseRP Next? This page covers the most common ones, organized by topic. Click any question to see the answer.

## General Questions

??? question "What exactly is IntenseRP Next?"
    IntenseRP Next is a bridge application that connects SillyTavern to DeepSeek's chat interface. It acts as a local API server that translates between SillyTavern's OpenAI-compatible format and DeepSeek's web interface. Think of it as an interpreter that handles all the technical complexity so you can use DeepSeek's AI models in SillyTavern without needing an official API key.

??? question "Is this the same as the original IntenseRP API?"
    No, IntenseRP Next is a complete reimagining of the original IntenseRP API by Omega-Slender. While it serves the same purpose and maintains compatibility, the codebase has been rebuilt from scratch with better architecture, more features, and improved reliability. The original creator gave permission to continue the project under the MIT license.

??? question "Do I need to pay for anything?"
    IntenseRP Next itself is completely free and open source. You're using DeepSeek's free chat interface through browser automation, so there are no API costs. The only requirement is a free DeepSeek account. Your only costs are electricity and internet bandwidth.

??? question "Why not just use DeepSeek's official API?"
    DeepSeek's official API costs money per token, while their chat interface is free. IntenseRP Next lets you use the free chat interface with SillyTavern, giving you the same powerful models without the usage costs. The trade-off is that you can't control certain parameters like temperature, but for many users, free access is worth this limitation.

## Technical Details

??? question "How does IntenseRP Next actually work?"
    The application runs a local web server on port 5000 that mimics OpenAI's API format. When SillyTavern sends a request, IntenseRP Next launches a browser (Chrome, Firefox, or Edge), navigates to DeepSeek's chat interface, logs you in automatically (if configured), sends your message, and captures the response. This response is then formatted and sent back to SillyTavern. It's browser automation made seamless.

??? question "What's the difference between DOM scraping and network interception?"
    DOM scraping extracts responses from the rendered HTML on the page. It works with all browsers but can struggle with complex content like code blocks. Network interception (Chrome/Edge) captures responses directly from the network stream before they're rendered, providing much more reliable results. It's like the difference between taking a photo of a printed document versus getting the original digital file.

??? question "Why does IntenseRP Next need a browser window open?"
    Since we're using DeepSeek's chat interface rather than an API, we need an actual browser to interact with their website. The browser window is where the magic happens - it's not just for show. Closing it will break the connection. Think of it as IntenseRP Next's workspace where it types your messages and reads DeepSeek's responses.

??? question "Can I minimize the browser window?"
    Yes! The browser window can be minimized and IntenseRP Next will continue working normally. Just don't close it completely. You can also move it to another desktop or workspace if you want it out of sight.

## Compatibility & Requirements

??? question "Which browsers work with IntenseRP Next?"
    Chrome and Edge are the recommended browsers and support all features including network interception. Firefox is supported but may have more issues with Cloudflare challenges and doesn't support network interception. Safari support is experimental. For the best experience, use Chrome or Edge.

??? question "Does IntenseRP Next work on Mac or Linux?"
    The source code works on all platforms. Pre-built binaries are currently only available for Windows and Linux. Mac users need to run from source for now. The core functionality is the same across all platforms.

??? question "What Python version do I need if building from source?"
    Python 3.12 or higher is required. The application uses modern Python features and type hints that aren't available in older versions. Most dependencies are pure Python, so they should install easily with pip.

??? question "Can I use this with other frontends besides SillyTavern?"
    Technically yes, if the frontend supports OpenAI-compatible endpoints. IntenseRP Next mimics OpenAI's chat completion API, so any client that can connect to a custom OpenAI endpoint should work. However, it's specifically designed and tested with SillyTavern.

## Common Issues

??? question "Why do I keep getting Cloudflare challenges?"
    Cloudflare protects DeepSeek from bots, and sometimes it gets suspicious of automated browsers. Enable "Persistent cookies" in Advanced Settings to maintain your browser session between restarts. Using Chrome also helps since it has undetected mode enabled by default. If challenges persist, try using the service less frequently or switch to a different IP address.

??? question "What does 'server is busy' mean when DeepSeek clearly isn't?"
    This is DeepSeek's way of rate limiting heavy users. It often happens with very long conversations that use lots of context. The solution is to either wait a while, start a new conversation with less context, or switch to a different DeepSeek account. See the [Rate Limits](rate-limits.md) page for more details.

??? question "Why does my browser close immediately after starting?"
    This usually means the browser driver (like chromedriver) is outdated or incompatible with your browser version. IntenseRP Next uses SeleniumBase which should handle driver updates automatically, but sometimes manual intervention is needed. Try updating your browser to the latest version or clearing the browser data in Advanced Settings.

??? question "Can I run multiple instances of IntenseRP Next?"
    Not recommended. Each instance needs its own port (configurable in Advanced Settings, default 5000) and browser profile. Running multiple instances can cause conflicts and increase your chances of hitting rate limits. If you need multiple connections, consider using different DeepSeek accounts with a single instance instead.

## Features & Settings

??? question "What's the difference between the R1 and V3 models?"
    V3-0324 is DeepSeek's standard chat model - fast and efficient for general conversations. R1-0528 is their reasoning model that thinks through problems step-by-step. R1 (DeepThink mode) produces more thoughtful responses but takes longer. Use V3 for casual chat and R1 for complex questions or when you want to see the AI's reasoning process.

??? question "Should I use network interception?"
    If you're using Chrome or Edge, absolutely yes. Network interception provides more reliable streaming, better handling of formatted content, and captures features like reasoning thoughts that DOM scraping misses. The only reason not to use it is if you're on a browser that doesn't support it (Firefox, Safari).

??? question "What do the different formatting presets actually do?"
    Formatting presets control how messages appear when sent to DeepSeek. "Classic (Name)" uses character names like "John: Hello" which feels natural for roleplay. "Wrapped" uses XML-style tags for clearer boundaries. "Divided" adds visual separators. The preset doesn't affect how messages appear in SillyTavern, only how they're formatted for DeepSeek to understand.

??? question "Why can't I change temperature or other parameters?"
    You're using DeepSeek's chat interface, not their API. The chat interface uses fixed parameters (likely temperature 0.3-0.6) that can't be changed. This is a fundamental limitation of using the free chat interface instead of the paid API. If you need parameter control, you'll have to use DeepSeek's official API or another service.

## Security & Privacy

??? question "Is my DeepSeek password safe?"
    Your credentials are encrypted and stored locally on your machine using industry-standard encryption (Fernet). They're never sent anywhere except to DeepSeek's official login page. The encryption key is generated uniquely for your installation. That said, if you're uncomfortable storing credentials, you can leave the fields blank and log in manually each time.

??? question "Does IntenseRP Next collect any data?"
    No. IntenseRP Next doesn't collect, transmit, or store any usage data, conversations, or personal information beyond what you explicitly configure (like your DeepSeek credentials for auto-login). The only external connection besides DeepSeek is a version check against GitHub, which only downloads a version number.

??? question "Can others on my network see my conversations?"
    By default, IntenseRP Next only accepts connections from localhost (your own computer). If you enable "Show IP" and connect from other devices, those connections are unencrypted HTTP. For maximum privacy, keep the default localhost-only configuration. Future versions will add authentication and HTTPS options.

??? question "What about the browser extension for network interception?"
    The extension only activates on DeepSeek's domain and only captures API responses meant for IntenseRP Next. It doesn't track your browsing, collect data, or interfere with other sites. The extension is loaded from your local IntenseRP Next installation, not from any external source.

## Advanced Usage

??? question "Can I customize the system prompt that's sent to DeepSeek?"
    Yes, but not through IntenseRP Next directly. The system prompt comes from your SillyTavern character card and settings. IntenseRP Next just formats and forwards these messages. To change the system behavior, modify your character's description, scenario, or SillyTavern's prompt settings.

??? question "How do I use this with SillyTavern multiplayer (STMP)?"
    IntenseRP Next automatically detects and handles STMP's name parameters. When multiple users are in a conversation, each message includes the speaker's name, and IntenseRP Next formats these appropriately for DeepSeek. No special configuration needed - it just works.

??? question "Is there a way to save conversations locally?"
    IntenseRP Next doesn't save conversations itself - that's SillyTavern's job. However, you can enable logging in Settings to keep a record of all technical operations. For actual conversation history, use SillyTavern's built-in chat logging and export features.

??? question "Can I modify the code to add my own features?"
    Absolutely! IntenseRP Next is open source under the MIT license. The codebase is modular and well-documented. Check out the [GitHub repository](https://github.com/LyubomirT/intense-rp-next) for contribution guidelines. The schema-driven configuration system makes it particularly easy to add new settings.

## Troubleshooting Tips

??? question "What should I do first when something goes wrong?"
    The classic "turn it off and on again" often works. Restart IntenseRP Next, make sure DeepSeek's website is accessible, and check that your browser is up to date. If problems persist, enable "Show Console" in Advanced Settings to see detailed logs of what's happening. Most issues have clear error messages that point to the solution.

??? question "Where can I get help if I'm stuck?"
    Start with the [Troubleshooting](../quick-start-guide/if-it-didnt/troubleshooting.md) guide for common issues. If that doesn't help, check existing [GitHub issues](https://github.com/LyubomirT/intense-rp-next/issues) to see if others have encountered the same problem. For new issues, open a GitHub issue with your logs and system details. The community is friendly and responsive.

??? question "How do I report a bug effectively?"
    Enable logging in Settings, reproduce the issue, then include the relevant log excerpts in your bug report. Mention your OS, browser, and IntenseRP Next version. Describe what you expected to happen versus what actually happened. If possible, provide steps to reproduce the issue. The more details you provide, the faster bugs get fixed.

!!! tip "Still have questions?"
    If your question isn't answered here, don't hesitate to ask! Open a [discussion on GitHub](https://github.com/LyubomirT/intense-rp-next/discussions) or reach out on Discord. We're always happy to help and your question might make it into this FAQ to help future users.