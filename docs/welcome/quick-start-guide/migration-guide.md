---
icon: material/arrow-right-bold
---

# Migration Guide

Switching to IntenseRP Next is straightforward, whether you're coming from the original IntenseRP API or updating from an earlier version of IntenseRP Next. The main thing to remember is that your settings and saved data can move with you - you just need to copy one folder.

!!! info "Auto-updater Coming Soon"
    We're working on an automatic updater that will handle migrations between IntenseRP Next versions for you. Until then, the manual process below takes just a minute or two.

## From the Original IntenseRP API

If you've been using Omega-Slender's original IntenseRP API, welcome! The migration process is simple and preserves your existing configuration.

### Step 1: Copy Your Settings

First, you'll need to transfer your saved configuration. Navigate to your old IntenseRP API installation folder and look for a directory called `save`. This folder contains your encrypted settings, including any saved DeepSeek credentials.

Copy the entire `save` folder and paste it into the root directory of your new IntenseRP Next installation. The structure should look like this:

```
intenserp-next/
├── IntenseRP Next.exe
├── save/              ← Your copied folder goes here
│   ├── config.enc
│   └── secret.key
└── ... other files
```

### Step 2: Update Your SillyTavern Connection

The model naming convention has changed in IntenseRP Next. In SillyTavern's API settings, you'll need to update the model name from the old `rp-intense-x.x.x` format to the new simplified format (usually something like `intense-rp-next-X` where `X` is the version number).

Head to your **API Connections** in SillyTavern and make sure your Custom Endpoint is still set to `http://127.0.0.1:5000/`. The connection process remains the same - IntenseRP Next uses the same port and endpoints as the original.

### Step 3: First Launch

When you start IntenseRP Next for the first time after migration, it will automatically detect and upgrade your old configuration format. You might see a message in the console about "migrating formatting presets" - this is normal and ensures your settings work with the new features.

!!! tip "New Features Available"
    After migrating, check out the Settings window to explore new options like network interception (Chrome only), persistent browser sessions, and custom message formatting templates. These weren't available in the original version but can significantly improve your experience.

## From a Previous Version of IntenseRP Next

Updating between versions of IntenseRP Next is even simpler since the configuration format remains consistent.

### Step 1: Backup and Copy Settings

Just like with the original migration, locate the `save` folder in your current IntenseRP Next installation. This contains all your settings, credentials, and preferences.

Copy this folder to your new IntenseRP Next installation directory, replacing any existing `save` folder if prompted. Your settings will be preserved exactly as they were.

### Step 2: Launch and Go

That's it! Start the new version and everything should work exactly as before. The configuration system is designed to be forward-compatible, so newer versions can read settings from older ones without issues.

If the new version includes new configuration options, they'll be added with sensible defaults that won't disrupt your existing setup.

## Troubleshooting Migration

Most migrations go smoothly, but if you run into issues, here are the common fixes:

**Can't find the save folder?** If you never changed any settings in the original IntenseRP API, there might not be a `save` folder. In this case, just start fresh with IntenseRP Next - the default settings are good to go.

**Settings not loading?** Make sure you copied the entire `save` folder, not just the files inside it. The folder structure needs to be preserved for the encryption keys to work properly.

**Browser login not persisting?** This is a new feature in IntenseRP Next. After migration, you'll need to enable "Persistent cookies" in Settings and log in once more. After that, your browser session will survive restarts.

!!! warning "Chrome Extension Note"
    If you're planning to use the network interception feature (Chrome only), you don't need to install anything manually. IntenseRP Next includes the extension and will load it automatically when you enable the feature in Settings.

## What's Different?

While IntenseRP Next maintains compatibility with the original, there are some behavior changes you might notice:

The response capture is more reliable, especially for long responses or those containing code blocks. The browser automation is smoother and handles Cloudflare challenges better. And the settings window now has more options, all generated automatically from the configuration schema.

These changes are designed to be improvements, but if you prefer the old behavior for any reason, most features can be toggled on or off in Settings.

---

Need help with migration? Check out the [Troubleshooting](if-it-didnt/troubleshooting.md) page or reach out on [GitHub](https://github.com/LyubomirT/intense-rp-next/issues) if you run into any issues. The community is helpful and most migration questions get sorted out quickly.