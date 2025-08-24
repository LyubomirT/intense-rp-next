---
icon: material/wrench
---

# Troubleshooting

Running into issues with IntenseRP Next? This page has initial troubleshooting steps for common problems. If these don't resolve your issue, we'll point you to more detailed resources.

## Quick Checks

Before you troubleshoot, you can try some of these quick fixes. Many issues are temporary and can be resolved by one of these steps:

1. **Restart IntenseRP Next** - Sometimes the simplest solution works best
2. **Check your internet connection** - Make sure you can access DeepSeek's website directly
3. **Verify DeepSeek is operational** - Try logging into DeepSeek manually to confirm the service is up
4. **Check your browser** - Make sure Chrome/Firefox/Edge is updated to the latest version

## Common Issues

### Connection Problems

??? failure "IntenseRP Next won't connect to DeepSeek"
    1. Make sure you're properly logged in to DeepSeek
    2. Check if you've enabled **Auto login** in settings with the correct credentials
    3. Try enabling **Persistent cookies** in Advanced Settings
    4. If you encounter Cloudflare challenges repeatedly, try the **Persistent cookies** option. If you already have it enabled, try clicking **Clear browser data** in Advanced Settings to reset your session

??? failure "SillyTavern can't connect to IntenseRP Next"
    1. Confirm IntenseRP Next is running and shows "API IS NOW ACTIVE!"
    2. Verify you're using the correct URL in SillyTavern (usually `http://127.0.0.1:5000/`)
    3. Check if your firewall is blocking connections to port 5000
    4. Try restarting both SillyTavern and IntenseRP Next

    !!! info "Tip"
        Network Interception uses the same port (5000) as the API, so if you can connect to the API, you should also be able to use Network Interception. If it doesn't work, then it's likely a browser, OS, or network issue rather than a problem with IntenseRP Next itself.

### Response Issues

??? failure "Responses stop in the middle or time out"
    1. Check your internet connection stability
    2. If using Chrome or Edge, enable **Network Interception** in DeepSeek Settings
    3. Try disabling streaming in SillyTavern
    4. Ensure your prompts aren't excessively long (DeepSeek has context limits)

??? failure "Code blocks look broken or cause streaming to pause"
    This is a known limitation when using DOM scraping. The solution is to:

    1. Switch to Chrome or Edge browser if you haven't already
    2. Enable **Network Interception** in DeepSeek Settings
    3. Restart IntenseRP Next

### Browser Issues

??? failure "Browser closes unexpectedly or crashes"
    1. Make sure you have the latest browser version installed
    2. Try clearing browser data using the button in Advanced Settings
    3. Disable any browser extensions that might interfere with automation
    4. Try switching to a different browser in Advanced Settings

??? failure "Cloudflare challenges appear too frequently"
    1. Enable **Persistent cookies** in Advanced Settings
    2. Use Chrome or Edge (it has **Undetected Mode** enabled by default)
    3. Avoid frequent logging in/out of DeepSeek
    4. Try not to restart IntenseRP Next too frequently
    5. Give it some time - DeepSeek may be temporarily blocking your IP due to too many requests

## Checking Logs

IntenseRP Next creates detailed logs that can help diagnose issues. To access them:

1. In Settings, enable **Store logfiles** under Logging Settings
2. Use the application for a while until your issue occurs
3. Logs are stored in the `logs` folder within your IntenseRP Next installation directory

The logs contain valuable information about what IntenseRP Next was doing when the issue occurred.

## Still Having Problems?

If you've tried these steps and still have issues:

1. **Ask for Help** - Reach out to the community for assistance. You can ask in the [GitHub Discussions](https://github.com/LyubomirT/intense-rp-next/discussions) or the developer on Discord (`@lyubomirt`).

2. **Open a GitHub Issue** - Report your problem on our [GitHub Issues page](https://github.com/LyubomirT/intense-rp-next/issues)

    When opening an issue, please include:

    - A clear description of the problem
    - Steps to reproduce the issue
    - Your system information (OS, browser version)
    - Log files if possible (see below)

### How to Upload Logs to GitHub Issues

To share log files when reporting an issue:

1. Navigate to the `logs` folder in your IntenseRP Next installation
2. Find the relevant log file (usually the most recent one)
3. In your GitHub issue, you can either:
---
- Attach the log file directly (drag and drop onto the issue text area)
- Copy the relevant portions into the issue with proper formatting (use the ```log code block format)
- Upload to a text sharing service like [Gist](https://gist.github.com) and include the link

!!! warning "Privacy Note"
    Before sharing logs, review them to make sure there's no sensitive information like your DeepSeek email. You can edit the logs to remove sensitive details if needed before uploading.

## Expected Behavior

Normally, IntenseRP Next should:

- Only support Chrome/Edge for network interception
- Connect to DeepSeek without frequent Cloudflare challenges
- Provide reliable streaming responses without interruptions
- Pause during code blocks only when using DOM scraping (without network interception)
- Allow SillyTavern to connect and send messages without issues

If you're experiencing behavior outside of this, it may indicate a configuration issue or bug.

!!! info "Remember"
    Sometimes, issues may not be caused by an error in IntenseRP Next itself, but rather by changes on DeepSeek's end or temporary network problems. Always check DeepSeek's status page or community forums for any ongoing issues.

!!! warning "It could be on your end, too"
    Sometimes, and, unfortunately, quite often, local misconfigurations or system incompatibilities can cause issues that seem like bugs in IntenseRP Next. Always double-check your setup, browser, and network conditions before assuming there's a problem with the application itself.

Remember that IntenseRP Next is connecting to DeepSeek's web interface, not using an official API, so occasional hiccups are normal. The application includes multiple fallback mechanisms to handle these cases (relatively) gracefully.