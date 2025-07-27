---
icon: material/download
---

# Download & Install

Getting IntenseRP Next up and running is pretty straightforward. You've got two main options: grab a pre-built binary if you're on Windows, or build from source if you want the latest features or you're on a different platform. Let's walk through both approaches.

!!! tip "Quick Decision Helper"
    **Use the binary** if you're on Windows and want the simplest setup.  
    **Build from source** if you're on Linux/macOS, want the latest features, or need to customize something.

!!! info "Binaries on Linux/macOS"
    Right now I don't have pre-built binaries for Linux or macOS, but that's coming soon! At least for Linux, binaries are almost ready and likely to be available in the next few weeks. If you're on macOS, you'll need to build from source for now.

## :material-microsoft-windows: Binary Installation (Windows)

The easiest way to get started on Windows is with our pre-built release. It's a portable package that includes everything you need.

### Step 1: Download the Latest Release

Head over to the [Releases page](https://github.com/LyubomirT/intense-rp-next/releases) and grab the latest `intenserp-next-win32-amd64.zip` file. Look for the one with the green "Latest" tag.

### Step 2: Extract the Archive

Extract the ZIP file to wherever you want to run IntenseRP Next from. Your desktop, a dedicated tools folder, wherever works for you. The app is completely portable, so it won't mess with your system files.

### Step 3: Handle Security Warnings

!!! warning "False Positive Alert"
    Windows Defender or your antivirus might flag the executable as suspicious. This is a common issue with PyInstaller-built apps (we're working on switching to a different bundler). The app is safe - you can check the source code yourself if you're concerned.

If Windows SmartScreen pops up, click "More info" and then "Run anyway". If your antivirus complains, you might need to add an exception for the IntenseRP Next folder.

### Step 4: Run the Application

Double-click `IntenseRP Next.exe` and you're good to go! The app should start up with the main window ready for configuration.

---

## :material-source-branch: From Source Installation

Building from source gives you the latest features and works on all platforms. You'll need Python installed, but that's about it for prerequisites.

### :material-microsoft-windows: Building on Windows

Windows users who want to run from source will need Python and Git. Here's the process:

#### Prerequisites
- **Python 3.12+** from [python.org](https://www.python.org/) (make sure to check "Add Python to PATH" during installation)
- **Git** from [git-scm.com](https://git-scm.com/) (or use GitHub Desktop if you prefer a GUI)

#### Installation Steps

1. **Clone the repository**
   ```cmd
   git clone https://github.com/LyubomirT/intense-rp-next.git
   cd intense-rp-next
   ```

2. **Create a virtual environment** (recommended but optional)
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```cmd
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```cmd
   python src/main.pyw
   ```

That's it! The app should start up just like the binary version.

### :material-linux: Building on Linux

Linux installation is similar to Windows, but with a few platform-specific tweaks. Most distros will have Python pre-installed, so you're already halfway there.

#### Prerequisites
- **Python 3.12+** (usually pre-installed, check with `python3 --version`)
- **Git** (install with your package manager if needed)
- **Development packages** for font support (optional but recommended)

#### Installation Steps

!!! tip "Linux Dependencies"
    Depending on your distro, you might need to install some additional packages for font support and other features. You can quickly install these with your package manager.

=== "Debian/Ubuntu"
       ```bash
       sudo apt update
       sudo apt install git python3-pip python3-venv cmake tcl-dev tk-dev
       ```
   
=== "Fedora"
       ```bash
       sudo dnf install git python3-pip cmake tcl-devel tk-devel
       ```
   
=== "Arch"
       ```bash
       sudo pacman -S git python-pip cmake tcl tk
       ```

The build commands are the same across all distros, so once you have the prerequisites, follow these steps:

1. **Clone and enter the repository**
   ```bash
   git clone https://github.com/LyubomirT/intense-rp-next.git
   cd intense-rp-next
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install scikit-build  # Needed for tkextrafont on Linux
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python src/main.pyw
   ```

!!! info "About Font Support"
    The `tkextrafont` dependency provides custom font support but requires compilation on Linux. If you run into issues or don't need custom fonts, you can remove it from `requirements.txt` - the app will fall back to system fonts.

### :material-apple: Building on macOS

Here's where things get a bit... experimental. The developer doesn't have a Mac to test on (those things are expensive! :material-currency-usd:), so this section is based on how Python projects *usually* work on macOS. If you're a Mac user and get this working, please let us know how it goes!

#### The Theoretical Steps

1. **Install prerequisites**
   - Get Python 3.12+ from [python.org](https://www.python.org/) or use Homebrew
   - Install Git (comes with Xcode Command Line Tools or via Homebrew)

2. **Clone the repository**
   ```bash
   git clone https://github.com/LyubomirT/intense-rp-next.git
   cd intense-rp-next
   ```

3. **Set up Python environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Cross your fingers and run**
   ```bash
   python src/main.pyw
   ```

!!! warning "Uncharted Territory"
    Since this hasn't been properly tested on macOS, you might run into issues. The Chrome extension for network interception should work fine, but there might be quirks with the GUI or browser automation. If you're feeling adventurous and want to help test, we'd love to hear about your experience!

---

## What's Next?

Once you've got IntenseRP Next installed and running, you'll want to:

1. Check out the [Important Config](important-config.md) section to set up your DeepSeek credentials
2. Follow the [Connect to SillyTavern](connect-to-sillytavern.md) guide to get everything talking to each other
3. Browse through [Try out more features](if-it-worked/try-out-more-features.md) to see what else you can do

If you run into any issues during installation, the [Troubleshooting](if-it-didnt/troubleshooting.md) page has solutions for the most common problems.