---
icon: material/cog-box
---

# Advanced Configuration

The Advanced Settings section contains options for power users who need more control over IntenseRP Next's behavior. These settings handle network access, debugging tools, and system-level features that most users won't need to touch.

!!! info "Settings Location"
    Find these options in **Settings** → **Advanced Settings**. Some features mentioned here are planned for future releases.

## Network & Access

### :material-router-network: Network Port

Controls which port IntenseRP Next's API server uses. The default is port 5000, but you can change this if another application is already using that port or if you prefer a different port number.

When you change the port:

- IntenseRP Next will display the new port in its URLs when starting
- You'll need to update SillyTavern's connection settings to use the new port
- Any Chrome/Edge extension for network interception will be automatically updated to use the new port

This setting doesn't impact performance whatsoever - it's purely for convenience and compatibility with other applications that might be using the default port.

!!! tip "Port Conflicts"
    If you're getting "address already in use" errors when starting IntenseRP Next, try changing this to a different port like 5001, 5002, or any unused port number.

### :material-ip-network: Show IP

When enabled, IntenseRP Next displays your local network IP address alongside the standard localhost URL when starting. Instead of just seeing:

```
URL 1: http://127.0.0.1:5000/
```

You'll see both URLs:

```
URL 1: http://127.0.0.1:5000/
URL 2: http://192.168.1.105:5000/
```

This is useful when you want to connect to IntenseRP Next from another device on your network, like a tablet running SillyTavern or a secondary computer. The second URL works from any device on the same network as your IntenseRP Next host.

!!! warning "Security Consideration"
    Enabling network access means any device on your local network can potentially connect to your IntenseRP Next instance. Only use this on trusted networks.

Also see [API Key Authentication](#api-key-authentication) for securing access, it pairs very well with this feature.

## Debugging & Monitoring

### :material-console: Show Console

Controls whether the console window appears when IntenseRP Next starts. The console displays real-time information about what the application is doing behind the scenes, including browser automation events, API calls, and error messages.

The console is particularly valuable when troubleshooting issues or monitoring the application's behavior. You'll see colored output indicating different types of events:

- :material-circle:{ style="color: #51cf66;" } **Green** messages for successful operations
- :material-circle:{ style="color: #ffd43b;" } **Yellow** messages for warnings or informational content
- :material-circle:{ style="color: #ff6b6b;" } **Red** messages for errors or failures
- :material-circle:{ style="color: #74c0fc;" } **Blue** messages for network activity
- :material-circle:{ style="color: #66d9ef;" } **Cyan** messages for debug information

The console window has its own customization options in the Console Settings section, where you can adjust fonts, colors, and word wrap behavior.

### :material-file-document-multiple: Log Files

Related to console output, you can enable persistent logging in the **Logging Settings** section. When enabled, IntenseRP Next writes console output to timestamped log files in the `logs` directory. This is invaluable for debugging issues that occur when you're not watching the console.

Log files are automatically managed based on your configured size and count limits, preventing them from consuming too much disk space. Each log file includes timestamps and strips color codes for clean, readable text output.

## Browser Management

### :material-cookie: Persistent Cookies

Maintains browser cookies and session data between IntenseRP Next restarts. This feature significantly improves the user experience by:

- Keeping you logged into DeepSeek between sessions
- Reducing Cloudflare challenge frequency
- Preserving browser state and preferences

Currently works with Chrome and Edge only. The browser data is stored in a dedicated directory within your system's temporary folder.

### :material-broom: Clear Browser Data

A utility button that wipes all stored browser data for your selected browser. Use this when:

- You're experiencing persistent browser issues
- You want to start fresh with a clean session
- You need to clear corrupted browser data

This action cannot be undone, so you'll need to log into DeepSeek again after clearing.

!!! danger "BE VERY CAREFUL"
    In extremely rare cases, browser data is wrongly tied to the user profile you use in the normal browser. Verify that the profile in the browser launched by IntenseRP Next doesn't match your main profile. If it does, you'll have all of your data wiped, including bookmarks, history, and saved passwords. DO NOT do this if it happens.

### :material-update: Check Version at Startup

When enabled, IntenseRP Next checks for updates each time it starts. If a newer version is available on GitHub, you'll see a notification window with a download link. This helps you stay current with bug fixes and new features.

The version check is a simple request to the GitHub repository and doesn't send any personal information.

## Coming Soon

These features are planned for future releases:

### :material-tunnel: Cloudflare Tunnels

Will allow you to expose your IntenseRP Next instance to the internet securely through Cloudflare's tunnel service. This eliminates the need for port forwarding or dealing with dynamic IP addresses when accessing IntenseRP Next remotely.

### :material-format-list-checks: IP Whitelist

Will restrict connections to specific IP addresses or ranges. Will be very useful for API key authentication if you want to have a very secure setup. Only requests from whitelisted IPs will be allowed to connect to IntenseRP Next.

!!! tip "Feature Requests"
    Have ideas for other advanced features? Open a discussion on our [GitHub repository](https://github.com/LyubomirT/intense-rp-next/discussions) to share your suggestions with the community. More important features can be requested in an [Issue](https://github.com/LyubomirT/intense-rp-next/issues) instead.

## Note on Advanced Settings

These settings are intended for users who understand the implications of changing network and browser behavior. Most users can safely ignore these options, as IntenseRP Next works well with default settings, though some are recommended anyway.