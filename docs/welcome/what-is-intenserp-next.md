---
icon: material/help-circle
---

# What is IntenseRP Next?

IntenseRP Next is a bridge application that connects DeepSeek AI's powerful language models to SillyTavern, making it easy to use DeepSeek for creative writing and roleplaying. At its core, IntenseRP Next is a reimagined and rebuilt version of the original IntenseRP API, with a focus on reliability, user experience, and modern architecture.

## The Origin Story

The original IntenseRP API was created by [Omega-Slender](https://github.com/Omega-Slender) as a way to connect SillyTavern to DeepSeek's web interface. It was an innovative approach that gave SillyTavern users access to DeepSeek's capabilities without requiring an official API. While it worked well for many users, as with any first-generation tool, there were areas that could be improved.

In July 2025, [LyubomirT](https://github.com/LyubomirT) took on the challenge of rebuilding the project from the ground up, while maintaining compatibility with the original concept. This became "IntenseRP Next" - a spiritual and technical successor that preserved the core functionality while addressing limitations and adding new features.

!!! quote "From the Creator"
    The goal wasn't just to fix issues but to create something that would be reliable, easy to maintain, and future-proof. I wanted to make sure users spent their time chatting with AI, not troubleshooting connection problems.

    ...Though I must also admit it is currently a bit rough, but I don't think it's that big of a surprise, given that the project is in a beta state. I hope to polish it up in the future, but for now, it works well enough for most users.

## Philosophy and Principles

IntenseRP Next is built around several core principles:

### 1. Reliability Above All

The most important job of IntenseRP Next is to work consistently. This means handling Cloudflare challenges, dealing with network issues gracefully, and making sure streaming responses don't break in the middle of generation. The Chrome extension for network interception is a direct result of this principle - by capturing responses at the network level, we avoid many of the issues that arise from scraping HTML.

### 2. Simplicity for End Users

Not everyone is a programmer or technical expert. IntenseRP Next aims to be easy to use for everyone, regardless of technical background. The interface is clean and focused, the documentation is thorough but accessible, and the default settings work well without extensive customization.

### 3. Modularity and Maintainability

Under the hood, IntenseRP Next uses a completely redesigned architecture based on modular components. This makes it easier to fix bugs, add features, and maintain the codebase over time. The schema-driven configuration system automatically generates the settings UI, which means new options can be added without having to redesign the interface.

### 4. Open Source and Community-Driven

IntenseRP Next is completely open source (MIT License) and developed with input from the community. Suggestions, bug reports, and contributions are not just welcomed but actively encouraged. The project aims to serve the needs of its users rather than following a predetermined roadmap.

??? note "What is the MIT License?"
    The MIT License is one of the most permissive open source licenses. It means you can:
    
    * ✅ **Use** the software for any purpose (personal, commercial, etc.)
    * ✅ **Modify** the code to suit your needs
    * ✅ **Distribute** copies of the software
    * ✅ **Sell** software that includes this code
    * ✅ **Create private forks** without sharing your changes
    
    The only requirements are to include the original copyright notice and license text. There's no warranty, but you're free to do almost anything with the code!

## What Makes it Different?

If you're familiar with the original IntenseRP API, you might be wondering what's changed. Here are the key improvements:

### Network Interception

The biggest technical improvement is the Chrome extension that uses the Chrome DevTools Protocol (CDP) to intercept network traffic directly. This captures DeepSeek's responses exactly as they're sent over the network, avoiding the need to scrape HTML from the page. The result is more reliable response capture, better streaming, and proper handling of code blocks and other formatted content.

!!! tip "Why This Matters"
    If you've ever had a response suddenly stop generating, or code blocks appear mangled, network interception solves these problems by getting the content directly from DeepSeek rather than trying to extract it from the page.

### Better Cloudflare Handling

IntenseRP Next includes improved browser automation with persistent profiles and undetected Chrome mode, making it much better at bypassing Cloudflare's bot detection. This means fewer captchas, fewer disconnections, and a smoother experience overall.

### Persistent Sessions

The app now maintains browser sessions between restarts, so you don't need to log in to DeepSeek every time you use it. This is especially helpful for users who run IntenseRP Next frequently.

### Flexible Message Formatting

The new message processing system supports multiple formatting presets and custom templates, giving you control over how messages are structured when sent to DeepSeek. This can improve the quality of responses, especially for complex roleplay scenarios or multi-user conversations.

### Comprehensive Logging

When things do go wrong, IntenseRP Next provides detailed logs that make it easier to diagnose and fix problems. The console window shows exactly what's happening behind the scenes, and logs can be saved to files for troubleshooting.

## How Does It Work?

At a high level, IntenseRP Next acts as a translator between SillyTavern and DeepSeek:

1. SillyTavern sends a request to IntenseRP Next's local API endpoint
2. IntenseRP Next processes this request, formatting the messages appropriately
3. It then automates a Chrome/Edge/Firefox browser to interact with DeepSeek's web interface
4. The browser sends the formatted messages to DeepSeek and captures the response
5. IntenseRP Next returns this response to SillyTavern in the expected format

The magic happens in steps 3 and 4, where IntenseRP Next handles all the complexities of browser automation and response capture so you don't have to.

!!! info "Technical Overview"
    For those interested in the technical details, IntenseRP Next uses Selenium for browser automation, a custom Chrome extension for network interception, and a Flask-based API server to communicate with SillyTavern. The architecture is modular, with separate components for message processing, character handling, browser automation, and configuration management.

## Who Is It For?

IntenseRP Next is designed for:

- SillyTavern users who want to access DeepSeek's language models
- People who prefer DeepSeek's free web interface over other AI options
- Anyone looking for a reliable, easy-to-use bridge between SillyTavern and DeepSeek

You don't need to be a technical expert to use IntenseRP Next. The default settings work well for most users, and the interface is designed to be straightforward and user-friendly.

## Ready to Get Started?

If you're ready to try IntenseRP Next, head over to the [Download & Install](quick-start-guide/download-and-install.md) guide. The setup process is straightforward and usually takes just a few minutes.

If you're coming from the original IntenseRP API, check out the [Migration Guide](quick-start-guide/migration-guide.md) to see what's changed and how to transition your setup.