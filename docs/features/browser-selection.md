---
icon: material/web
---

# Browser Selection Guide

No browser is created equal, and we all have different needs and preferences. IntenseRP Next has support for multiple options that you might want to take a look at and see what fits best.

!!! tip "Quick Answer"
    **Chrome** is the gold standard with full feature support and the most testing. **Custom Chromium** browsers like Brave or Vivaldi are nearly as good with better privacy options.

## Browser Compatibility Overview

<div class="browser-table" markdown="1" style="overflow-x: auto;">

| Browser | Rating | Network Interception | Persistent Cookies | Cloudflare Bypass | Why |
|---------|:------:|:--------------------:|:------------------:|:-----------------:|-----|
| :material-google-chrome: **Chrome** | :material-star:{ style="color: #007acc;" }:material-star:{ style="color: #007acc;" }:material-star:{ style="color: #007acc;" }:material-star:{ style="color: #007acc;" }:material-star:{ style="color: #007acc;" } | :material-check: | :material-check: | :material-circle:{ style="color: #51cf66;" } Excellent | Full feature support, most tested |
| :material-application-outline: **Custom Chromium** | :material-star:{ style="color: #007acc;" }:material-star:{ style="color: #007acc;" }:material-star:{ style="color: #007acc;" }:material-star:{ style="color: #007acc;" }:material-star-half:{ style="color: #335c99;" } | :material-check: | :material-check: | :material-circle:{ style="color: #51cf66;" } Excellent | Same as Chrome, better privacy |
| :material-microsoft-edge: **Edge** | :material-star:{ style="color: #51cf66;" }:material-star:{ style="color: #51cf66;" }:material-star:{ style="color: #51cf66;" }:material-star-half:{ style="color: #339966;" } | :material-check: | :material-check: | :material-circle:{ style="color: #ffd43b;" } Good | Chromium-based, reliable |
| :material-firefox: **Firefox** | :material-star:{ style="color: #ffd43b;" }:material-star:{ style="color: #ffd43b;" }:material-star:{ style="color: #ffd43b;" } | :material-close: | :material-close: | :material-circle:{ style="color: #ffd43b;" } Good | Basic features only |
| :material-apple-safari: **Safari** | :material-star:{ style="color: #ff6b6b;" } | :material-close: | :material-close: | :material-circle:{ style="color: #ff6b6b;" } Poor | Experimental, limited testing |

</div>

<style>
.browser-table table th:nth-child(2), 
.browser-table table td:nth-child(2) {
    min-width: 180px !important;
    white-space: nowrap;
}
</style>

## Detailed Browser Analysis

### :material-google-chrome: Chrome (5.0/5 stars)
**The gold standard for IntenseRP Next automation.**

Chrome receives the most development attention and testing. It has native support for all advanced features including Chrome DevTools Protocol (CDP) which powers network interception.

**:material-check-all: What you get:**

- Network interception for reliable response capture
- Persistent cookies for bypassing Cloudflare  
- Undetected mode for better success rates and Cloudflare Turnstile bypass
- Excellent automation stability

**Best for:** Users who want maximum reliability and all features working perfectly.

---

### :material-application-outline: Custom Chromium Browsers (4.75/5 stars)
**Nearly perfect with enhanced privacy options.**

Custom Chromium-based browsers like Brave, Vivaldi, Opera, and others use the same underlying engine as Chrome, meaning that you get identical functionality with privacy and other browser-specific features as a bonus.

**:material-check-all: Same features as Chrome:**

- Full network interception support
- Persistent cookies functionality  
- Excellent Cloudflare bypass
- All automation features work identically

**:material-plus-circle: Additional benefits:**

- Stronger privacy protections
- Built-in ad blocking (Brave)
- Customizable interface (Vivaldi)
- Your existing browser settings and extensions

**Best for:** Privacy-conscious users who want Chrome's reliability without using Google Chrome directly.

!!! example "Popular Custom Chromium Options"
    - **Brave Browser**: Privacy-focused with built-in ad blocking
    - **Vivaldi**: Highly customizable power user browser  
    - **Opera**: Feature-rich with built-in tools
    - **Ungoogled Chromium**: Chrome without Google (and their services).

---

### :material-microsoft-edge: Edge (3.5/5 stars)
**Solid, but not all there.**

Edge uses the same Chromium engine as Chrome, which *should* mean it's reliable. But, realistically, it uses the EdgeDriver instead of the ChromeDriver, which doesn't yet properly support SB's `uc`.

**:material-check: Works well:**

- Network interception supported
- Persistent cookies functionality
- Medium-good Cloudflare bypass performance
- Stable automation

**:material-alert-circle-outline: Limitations:**

- Slightly less tested than Chrome
- Some edge cases may behave differently (no pun intended)
- EdgeDriver limitations

**Best for:** Windows users who prefer Microsoft's browser or corporate environments where Edge is standard. But, sincerely, if you can, please use Chrome or a custom Chromium browser.

---

### :material-firefox: Firefox (3.0/5 stars) 
**Reliable for basic usage.**

Firefox works dependably for core functionality but lacks support for advanced features due to its different architecture.

**:material-check: Basic features:**

- Core automation works reliably
- Login and chat functionality  
- Decent Cloudflare handling

**:material-close-circle: Missing features:**

- No network interception (DOM scraping only)
- No persistent cookie sessions
- Responses may be truncated
- LaTeX and complex formatting issues
- Similar Cloudflare bypass limitations

**Best for:** Privacy advocates who prefer Firefox and don't need advanced features.

---

### :material-apple-safari: Safari (1.0/5 stars)
**Use only as a last resort.**

Safari support exists but that's the only positive thing that can be said about it. It's here from the original IntenseRP API, left for reasons unknown even to the maintainer. Perhaps it's best to avoid it altogether.

**:material-alert-circle: Known issues:**

- Frequent login failures
- Response capture problems  
- General automation instability
- Limited WebDriver support

**:material-close-circle: Missing everything:**

- No network interception
- No persistent cookies
- Poor Cloudflare bypass
- Minimal feature support

**Best for:** macOS users with no other browser options available.

## Setting Up Custom Chromium Browsers

Want to use Brave, Vivaldi, Opera, or another Chromium-based browser? Here's how to set it up:

### Step 1: Install Your Preferred Browser

Download and install your chosen browser from their official website:

- **Brave**: [brave.com](https://brave.com)
- **Vivaldi**: [vivaldi.com](https://vivaldi.com)  
- **Opera**: [opera.com](https://opera.com)
- **Ungoogled Chromium**: [ungoogled-software.github.io](https://ungoogled-software.github.io)

!!! note "Portable Versions"
    Some browsers offer portable versions that don't require installation. This can simplify setup and avoid conflicts with existing installations. You can use those too, because you're going to have to point IntenseRP Next to the binary executable either way.

Complete the initial setup and let it finish installing.

### Step 2: Configure IntenseRP Next

1. Open IntenseRP Next and click **Settings**
2. Navigate to **Advanced Settings**
3. Set **Browser** dropdown to **"Custom Chromium"**
4. The **Browser Path** field will appear below
5. Click **Browse** to locate your browser's executable or **enter the path manually**

### Step 3: Find Your Browser Executable

The executable location varies by platform and browser:

=== ":material-microsoft-windows: Windows"
    ```
    Brave: C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe
    Vivaldi: C:\Users\{username}\AppData\Local\Vivaldi\Application\vivaldi.exe  
    Opera: C:\Users\{username}\AppData\Local\Programs\Opera\opera.exe
    ```

=== ":material-linux: Linux"
    ```
    Brave: /usr/bin/brave-browser
    Vivaldi: /opt/vivaldi/vivaldi
    Opera: /usr/bin/opera
    ```

=== ":material-apple: macOS"
    ```
    Brave: /Applications/Brave Browser.app/Contents/MacOS/Brave Browser
    Vivaldi: /Applications/Vivaldi.app/Contents/MacOS/Vivaldi
    Opera: /Applications/Opera.app/Contents/MacOS/Opera
    ```

!!! info "Non-Standard Locations"
    Although rare, some users don't have the browsers in standard locations. If you installed a Chromium-based browser that way (Chrome itself included), that'll work under Custom Chromium.

### Step 4: Save and Test

1. Click **Save** to apply your settings
2. Restart IntenseRP Next
3. Your custom browser will now be used for automation

!!! success "Pro Tip"
    Your custom browser runs in automation mode, separate from your normal browsing. Your regular bookmarks, extensions, and settings won't be affected.

## Choosing the Right Browser

**For maximum reliability:** Use **Chrome** - it's the most tested and supported option.

**For privacy + reliability:** Choose a **Custom Chromium** browser like Brave or Vivaldi - you get Chrome's capabilities with much better privacy.

**For corporate/Windows users:** **Edge** provides good compatibility in business environments.

**For basic usage only:** **Firefox** works fine if you don't need advanced features.

**Avoid:** **Safari** unless you absolutely have no other options on macOS.

## Switching Browsers

To change browsers:

1. **Stop IntenseRP Next** if currently running
2. Open **Settings** → **Advanced Settings**  
3. Select your new **Browser** option
4. For Custom Chromium, set the **Browser Path** using the **Browse** button
5. Click **Save**
6. Restart IntenseRP Next

!!! info "Clean Switch"
    Your browser choice only affects automation - it won't change your daily browsing experience. The automated browser runs in a separate profile from your normal browsing.

## Troubleshooting Browser Issues

??? question "Browser executable not found error"
    Double-check the path to your browser's executable file. Make sure you're pointing to the actual `.exe` file (Windows) or executable binary (Linux/Mac), not just the folder containing it.

??? question "Custom browser won't start"
    Some browsers require additional setup or have different executable names. Try running the browser normally first to make sure it's properly installed, then maybe check out Discussions or Issues for help on the GitHub repository.

??? question "Features not working with custom browser"
    All Chromium-based browsers should support the same features as Chrome. If something isn't working, make sure you're using a recent version of your browser and that it's truly Chromium-based (not Firefox or Safari-based).