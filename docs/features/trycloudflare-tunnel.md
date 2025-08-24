---
icon: material/tunnel
---

# TryCloudflare Tunnel

Do you want to share your IntenseRP Next instance with a friend across the internet? Or maybe you need to access it from your phone while away from home? The TryCloudflare tunnel feature makes this possible by creating a secure public URL that connects to your local IntenseRP Next server.

!!! warning "Security First"
    This feature exposes your IntenseRP Next instance to the **entire internet**. Only use this when you actually need to share access, and **always** enable API key authentication when using tunnels. Think of it like leaving your front door open - you really want to know who's coming in.

## What is TryCloudflare?

TryCloudflare is Cloudflare's free tunneling service that creates a temporary public URL (like `https://random-name.trycloudflare.com`) that forwards to your local IntenseRP Next server. It's like having a secure tunnel from the internet directly to your computer.

The best part is that it's completely free and doesn't require a Cloudflare account. With the catch being that the URLs are temporary and change each time you restart the tunnel.

## Prerequisites

Before you can use this feature, you need to install `cloudflared` on your system:

### :material-microsoft-windows: Windows Installation

!!! info "winget"
    You can, and should, use `winget` to install `cloudflared` on Windows:

    ```powershell
    winget install --id Cloudflare.Cloudflared
    ```

    It automates most installation steps and is the recommended way to install `cloudflared` in the official documentation.

1. Download the latest `cloudflared` for Windows from the [official releases page](https://github.com/cloudflare/cloudflared/releases)
2. Look for `cloudflared-windows-amd64.exe` 
3. Rename it to `cloudflared.exe` and place it somewhere in your PATH (like `C:\Windows\System32` or create a dedicated folder and add it to PATH)
4. Test it by opening Command Prompt and typing `cloudflared --version`

### :material-linux: Linux Installation

Check out the official [Cloudflare documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/) for detailed instructions.

The [Cloudflare Package Repository](https://pkg.cloudflare.com/index.html) is also a great resource as it has most distributions covered.

!!! info "macOS Users"
    While not officially tested, macOS users can install cloudflared via Homebrew: `brew install cloudflared`. Let us know if it works!

## Setting It Up

Once you have `cloudflared` installed, enabling the tunnel is super simple:

1. Open IntenseRP Next and click **Settings**
2. Navigate to **Advanced Settings**
3. Find the **Network Settings** section
4. Toggle **Enable TryCloudflare Tunnel** to ON
5. Leave **Auto-start Tunnel** enabled (recommended)
6. Click **Save**

That's it! When you start IntenseRP Next, it will automatically create a tunnel and display the public URL in the console.

## Using the Tunnel

When the tunnel starts successfully, you'll see something like this in your console:

```
[color:cyan]Starting TryCloudflare tunnel for port 5000...
[color:green]TryCloudflare tunnel established
[color:yellow]Tunnel URL: https://random-words-here.trycloudflare.com
```

This URL can be used from anywhere on the internet. Share it with whoever needs access, and they can use it in SillyTavern just like the local URL.

!!! tip "URL Changes"
    The tunnel URL changes every time you restart IntenseRP Next. If you're sharing with others, you'll need to send them the new URL each time, as well replace the old one in SillyTavern.

## Security Best Practices

### :material-shield-check: Always Use API Keys

When using tunnels, **always** enable API key authentication:

1. In Settings, go to **Security Settings**
2. Enable **API Authentication**
3. Click **Generate API Key** to create a secure key
4. Share this key **only** with people you trust
5. They'll need to enter it in SillyTavern's API key field
6. (Optional) Create many API keys for different users or devices

### :material-eye-off: Keep It Private

- Only enable the tunnel when you actually need it
- Disable it immediately when you're done sharing
- Never post your tunnel URL publicly (Discord servers, forums, etc.)
- Treat the URL like a password - it's a direct line to your computer

### :material-timer-sand: Temporary by Design

The temporary nature of TryCloudflare URLs is actually a security feature. Even if someone gets your URL, it won't work after you restart the application.

## Common Use Cases

### Remote Access

Access your IntenseRP Next instance from your phone or another computer:

1. Start IntenseRP Next with tunnel enabled
2. Copy the tunnel URL from the console
3. Use it in SillyTavern on your other device
4. Don't forget to add the API key if you enabled authentication!

### Sharing with Friends

Let a friend use your DeepSeek bridge temporarily:

1. Enable API authentication and generate a key
2. Start the tunnel
3. Send them both the URL and API key (use secure messaging!)
4. When done, either restart IntenseRP Next or disable the tunnel

### Testing and Development

Developers can use tunnels to test IntenseRP Next from different networks or devices without complex network configuration.

## Troubleshooting

??? failure "Cloudflared not found in PATH"
    Make sure `cloudflared` is properly installed and accessible. Test by running `cloudflared --version` in your terminal. If it doesn't work, you may need to add its location to your system's PATH variable.

??? failure "Tunnel fails to start"
    1. Check your internet connection
    2. Ensure no firewall is blocking `cloudflared`
    3. Try running `cloudflared tunnel --url http://127.0.0.1:5000` manually to test
    4. Check if your ISP blocks outbound connections on port 7844

??? failure "Can't connect to tunnel URL"
    1. Make sure IntenseRP Next is actually running
    2. Verify the URL is typed correctly (they're long and random!)
    3. Check if you need to provide an API key
    4. Some corporate networks block Cloudflare tunnels

## Technical Details

For the curious, here's what happens under the hood:

1. IntenseRP Next starts your API server on `localhost:5000` (or your configured port)
2. It launches `cloudflared` as a subprocess
3. Cloudflared establishes an encrypted tunnel to Cloudflare's edge network
4. Cloudflare assigns a random subdomain and forwards traffic through the tunnel
5. Anyone accessing the public URL has their traffic routed through Cloudflare to your local server

The connection is encrypted end-to-end, so your data is secure in transit. However, anyone with the URL can access your server, which is why authentication is so important.

!!! warning "Not for Production"
    TryCloudflare is designed for temporary use and testing. For permanent public hosting, consider Cloudflare's paid tunnel services or proper server hosting. The free tier has usage limits and the URLs are intentionally temporary.

## Disabling the Tunnel

To stop using the tunnel feature:

- **Temporarily**: Just close IntenseRP Next - the tunnel stops automatically
- **Permanently**: Go to Settings → Advanced Settings and toggle off **Enable TryCloudflare Tunnel**

Remember, no tunnel = no external access = better security!

---

!!! question "Need Help?"
    If you're having trouble with tunnels, check our [Troubleshooting Guide](../welcome/quick-start-guide/if-it-didnt/troubleshooting.md) or ask in the [GitHub Discussions](https://github.com/LyubomirT/intense-rp-next/discussions). Remember to never share your actual tunnel URLs when asking for help!

---

### Note

You can still run `cloudflared` commands manually if needed. Just make sure to specify the correct parameters and options (like your port, specific setup, access tokens, etc.)