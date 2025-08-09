---
icon: material/cog-outline
---

# Important Config

Getting IntenseRP Next configured properly takes just a minute or two, and most settings can be left at their defaults. This page covers the essential options you'll want to look at when setting up for the first time, plus a few nice-to-have features that can improve your experience.

Before you start, make sure you've installed IntenseRP Next and have it running. If you haven't done that yet, check out the [Download & Install](download-and-install.md) guide first.

# Legend

For a better distinction of what's important and what can be skipped, this page has a simple icon system to indicate the significance of each setting:

| Icon | Meaning | Description |
|------|---------|-------------|
| :material-check-circle:{ .recommended } | **Recommended** | Settings you should definitely configure |
| :material-star:{ .nice-to-have } | **Nice to Have** | Features that enhance the experience |
| :material-palette:{ .subjective } | **Subjective** | Personal preference settings |

<!-- Custom CSS for icon colors -->
<style>
.recommended { color: #51cf66; }
.nice-to-have { color: #ffd43b; }
.subjective { color: #74c0fc; }
</style>

## Getting to Settings

Click the **Settings** button in the main window to open the configuration panel. You'll see a sidebar on the left with different sections - we'll focus on the most important ones for getting started. On the right, you'll find the actual settings you can adjust.

## DeepSeek Settings

This is where you'll spend most of your configuration time. These settings control how IntenseRP Next connects to and interacts with DeepSeek.

### :material-check-circle:{ .recommended } Email and Password

If you want automatic login, enter your DeepSeek credentials here. These are encrypted and stored locally on your machine. Without these, you'll need to manually log in every time you start IntenseRP Next, which gets annoying pretty quickly.

Simply enter your email and password, then flip the **Auto login** switch to enable automatic authentication.

!!! important "Security Note"
    Your DeepSeek credentials are stored securely and not sent over the network. They are only used locally to authenticate your session. Additionally, they're encrypted with a secret key stored in your IntenseRP Next directory, so even if someone gains access to your files, they won't be able to read your credentials.

### :material-star:{ .nice-to-have } Intercept Network

This is a Chrome/Edge/Brave feature that significantly improves response capture reliability. When enabled, IntenseRP Next uses a browser extension to intercept DeepSeek's responses directly from the network stream instead of scraping them from the page.

You'll notice the difference most with streaming responses, complex structures, HTML tags, images, LaTeX, and code blocks - they come through cleanly without formatting issues. If you're using Chrome, Edge, or Brave (which are recommended), definitely turn this on.

### :material-palette:{ .subjective } Deepthink and Search

These options control DeepSeek's special features. **Deepthink** enables the R1 reasoning model globally, even when you don't use triggers like `{{r1}}` in your messages. **Search** allows DeepSeek to search the web, also globally.

Some users love these features, others find them unnecessary. They're off by default, so enable them based on your preferences and use cases.

## Advanced Settings

A few options here are worth considering even for new users.

### :material-check-circle:{ .recommended } Browser Selection

IntenseRP Next supports Chrome, Firefox, Edge, Safari (experimentally), and Brave. Chrome, Edge, and Brave are the recommended choices because they have the best Cloudflare bypass capabilities and support all features including network interception.

If you must use a different browser, all Chromium-based browsers (Chrome, Edge, Brave) are good options. Firefox works but may struggle more with Cloudflare challenges.

### :material-star:{ .nice-to-have } Persistent Cookies

Available for Chrome, Edge, and Brave, this feature saves your browser session between IntenseRP Next restarts. Enable this and you won't need to deal with Cloudflare challenges as often - your browser will remember that it's already been verified.

Additionally, this allows you to stay logged into DeepSeek without needing to re-enter your credentials every time you start IntenseRP Next, and decreases chances of getting blocked by Cloudflare by a huge margin.

### :material-palette:{ .subjective } Show Console

The console window displays detailed logs of what IntenseRP Next is doing behind the scenes. It's invaluable for troubleshooting but can be distracting during normal use.

If you're technically inclined or want to understand how things work, enable it. Otherwise, leave it off and only turn it on if you run into issues.

## Message Formatting

This section might seem complex at first glance, but the defaults work well for most users.

### :material-palette:{ .subjective } Formatting Preset

IntenseRP Next offers several ways to format messages before sending them to DeepSeek. The default **Classic (Name)** preset uses character names like "Sarah: Hello there!" which works well for roleplay scenarios.

Other presets include:
- **Classic (Role)** - Uses "user:" and "assistant:" labels
- **Wrapped** formats - XML-style formatting for clearer message boundaries
- **Divided** formats - Visual separators between messages
- **Custom** - Define your own formatting templates

Unless you have specific formatting needs, stick with the default. You can always experiment later.

## What You Can Skip

Several sections in settings are either for advanced users or handle edge cases:

**Console Settings** only matter if you use the console window regularly. The defaults are fine.

**Logging Settings** control debug log files. Unless you're troubleshooting or helping with development, leave these disabled to save disk space and reduce I/O overhead.

**Text file** mode in DeepSeek Settings sends prompts as file attachments instead of text. This is rarely needed and can actually cause issues with some prompts.

## Saving Your Configuration

!!! important "Don't Forget to Save"
    After making changes, click the **Save** button at the bottom of the settings window. Your configuration is encrypted and stored in the `save` folder within your IntenseRP Next directory.

!!! danger "Closing the Settings Window"
    If you close the settings window without saving, your changes will be lost!

## Quick Setup Checklist

If you're in a hurry, here's a quick checklist to get IntenseRP Next configured and ready to use:

1. Open Settings
2. Enter your DeepSeek email and password
3. Enable Auto login
4. If using Chrome or Edge, enable Intercept Network
5. Enable Persistent cookies (Chrome/Edge only)
6. Click Save

That's it! With these settings, IntenseRP Next will automatically log you into DeepSeek, maintain your session between restarts, and capture responses reliably.

---

Ready to connect to SillyTavern? Head over to [Connect to SillyTavern](connect-to-sillytavern.md) to complete your setup. If you want to explore more features after getting the basics working, check out [Try out more features](if-it-worked/try-out-more-features.md).