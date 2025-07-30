---
icon: material/console
---

# Console

The console is IntenseRP Next's real-time information window that shows what's happening behind the scenes. It displays everything from browser automation events to API calls, which is incredibly useful for troubleshooting and understanding how the application works.

While the main interface keeps things clean and simple, the console gives you the full picture when you need it. It's like having a backstage pass to the inner workings of IntenseRP Next.

!!! info "Opening the Console"
    Enable **Show Console** in **Settings** → **Advanced Settings** to display the console window when IntenseRP Next starts. You can also open it later from the main window's menu.

## Understanding Console Output

The console displays color-coded messages indicating different types of activity:

- :material-circle:{ style="color: #51cf66;" } **Green** messages for successful operations (connections, successful logins, API responses)
- :material-circle:{ style="color: #ffd43b;" } **Yellow** messages for warnings and informational content (status updates, configuration changes)
- :material-circle:{ style="color: #ff6b6b;" } **Red** messages for errors and failures (connection issues, browser crashes, authentication problems)
- :material-circle:{ style="color: #74c0fc;" } **Blue** messages for network activity (API requests, response processing)
- :material-circle:{ style="color: #66d9ef;" } **Cyan** messages for debug information (browser actions, extension loading)

All output appears in real-time as events happen, making it perfect for troubleshooting or just watching IntenseRP Next work. 

Frankly, it's oddly satisfying to see a successful login sequence play out in green messages, or to catch a glimpse of the browser automation in action.

## Console vs Log Files

The console and logging system serve different purposes but work well together:

**Console Window** provides real-time display of current activity with color-coding for quick scanning. It's interactive - you can scroll, select text, and see everything as it happens. However, it disappears when you close the window or restart IntenseRP Next.

**Log Files** offer persistent storage of events for later review. They capture the same information but store it in timestamped text files that you can search through or share for debugging. Enable logging in **Settings** → **Logging Settings** if you want both real-time console display and permanent file records.

Most people find the console more useful day-to-day, but having both gives you the best of both worlds.

## Console Customization

Adjust the console appearance in **Settings** → **Console Settings**:

### Font Options
Choose your preferred **Font Family** from system fonts. Adjust **Font Size** to match your screen and preferences. There are some fallbacks, though they're not perfect. Generally the fonts for Windows, macOS, and Linux are included, but not the entire library yet. There are plans to bring the Blinker font to it too as it's shipped with the IntenseRP Next package.

### Color Themes
While mostly useless, you can choose from several color themes to change the console's look:

- **Modern (Redesigned)**: Clean grays and blues with subtle accents, easy on the eyes for extended viewing. Based off the original IntenseRP API console design but improved for readability.
- **Classic**: This is the traditional style of the console and log messages if you prefer the original look.
- **Bright**: An "amplified" version of the Modern theme with more vibrant colors. Good for high contrast displays or if you just like bright colors.

### Display Settings
Enable **Word Wrap** to prevent long lines from requiring horizontal scrolling. The console automatically scrolls to keep the latest messages visible, but you can scroll back through history without losing new events.

## Console Dumping

Console dumping lets you save the current console content to a text file - useful for bug reports or keeping records of specific sessions. Sometimes, log files don't have enough time to capture everything, or you want to share exactly what you saw in the console. If that's the case, this will be your best friend.

### Enabling Console Dumping

1. Go to **Settings** → **Dump Settings**
2. Turn on **Enable Console Dumping**
3. Optionally set a custom **Dump Directory** (defaults to `condumps/` in the project folder)
4. A **Dump Console** button will appear in the console window

### How It Works

When you click **Dump Console**, the current content gets saved to a timestamped text file with color codes stripped for clean, readable text. Files use the format `console_dump_YYYYMMDD_HHMMSS.txt` so you can easily track when each dump was created.

!!! tip "Perfect for Bug Reports"
    Console dumps are invaluable for bug reports. Instead of trying to describe what you're seeing, just dump the console and share the file. It captures the exact sequence of events leading to whatever issue you're experiencing.

## Performance and Usage

The console has minimal performance impact, so there's no real downside to keeping it open. Some users leave it running in the background to keep an eye on things, while others only open it when investigating specific issues.

It **does** get a bit cluttered if for some reason messages are flooding in in a short timeframe, but that's rare. 

(If that does happen, please report it as a bug so we can fix it! Console dumping can actually help with that, too.)

!!! note "Console Keyboard Shortcuts"
    When the console window is active: ++ctrl+c++ to copy selected text, ++ctrl+a++ to select all, ++home++ / ++end++ to jump to beginning/end, and ++prior++ / ++next++ to scroll by pages.

    !!! warning "Mouse Interactions Work Too"
        You can also use the mouse to select text, scroll, and interact with the console. Just click and drag to select, or use the scroll wheel to move through history.