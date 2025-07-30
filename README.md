<img src="/images/IntenseRP Next release Strip.png" alt="IntenseRP Next release Strip">
<h2 align="center">Welcome to IntenseRP Next</h2>

**IntenseRP Next** is a completely reimagined and reworked successor to the original IntenseRP API by Omega-Slender. This new version brings lots of improvements, fixes, and features that make connecting DeepSeek AI to SillyTavern easy and reliable.

![Preview](/images/PreviewIntenseRpNext_optim.gif)

<div align="center">

![GitHub release (latest by date)](https://img.shields.io/github/v/release/LyubomirT/intense-rp-next?style=flat-square)
![License](https://img.shields.io/github/license/LyubomirT/intense-rp-next?style=flat-square)
![GitHub stars](https://img.shields.io/github/stars/LyubomirT/intense-rp-next?style=flat-square)
![GitHub issues](https://img.shields.io/github/issues/LyubomirT/intense-rp-next?style=flat-square)
![Beta](https://img.shields.io/badge/status-beta-orange?style=flat-square)

</div>

## 🔥 What's New in IntenseRP Next

I've completely reimagined the original project with a focus on **reliability**, **user experience**, and **modern architecture**. As of now, the project is in **beta** but already stable enough for daily use. Here are the main things that have changed:

### 🌟 Key Improvements

- **🔌 Network Interception**: Chrome extension using CDP (Chrome DevTools Protocol) for way more reliable response capture (essentially skipping HTML to Markdown conversion)
- **🎨 Better UX**: Improved interface and console with multiple color themes (console for now), custom fonts, and intuitive configuration
- **📝 Smart Message Processing**: Pipeline-based system that handles custom message formatting, character recognition, and content processing
- **🛡️ Better Cloudflare Bypass**: Improved browser automation with persistent profiles and undetected Chrome mode
- **⚙️ Schema-Driven Config**: Auto-generating configuration UI to make it easier for us developers to add new features
- **💾 Persistent Sessions**: Keep your login sessions across app restarts (Chrome/Edge only)

### 🎯 Recent Additions

- **Official Docs!**: Now you can find all the information you need in the official documentation. It's currently hosted on ReadTheDocs and you can find it right here: [IntenseRP Next Documentation](https://intense-rp-next.readthedocs.io/en/latest/)
- **Send Thoughts**: Now you can toggle whether you want to see DeepSeek's thoughts in the response or not.
- **`name` parameter**: Now IntenseRP Next supports the `name` parameter in the request, which allows you to specify the character name for the response and override `DATA1` and `DATA2` variables.

> [!NOTE]
> The project is in a "stable beta" state, meaning it's ready for daily use but may still have some rough edges. If you run into any issues, please report them on GitHub!


## 🚀 Quick Start

### 📦 Requirements

**For Windows Users:**
- 🖥️ Windows 10/11 x64
- 🌐 A browser (Chrome is recommended)
- 📁 The application package in [Releases](https://github.com/LyubomirT/intense-rp-next/releases)

**For Linux Users:**

Currently, only Windows binaries are available, but I'm actively working on Linux support. If you're interested in helping test the Linux version, please reach out!

**For Source Code:**
- 🐍 Python 3.12+ from [python.org](https://www.python.org/)
- 📚 Dependencies auto-install from `requirements.txt`

> [!WARNING]
> If on Linux, you should also install `scikit-build` (via `pip`) alongside `CMake` and `tcl-dev` `tk-dev` (via your package manager) packages if you want to have `tkextrafont` support for custom fonts. If you don't want to use custom fonts, it will still work but will fall back to Arial. You can simply remove the `tkextrafont` dependency from `requirements.txt` if you don't want to use custom fonts at all.

### 🎮 Getting Started

1. **Download**: Grab the latest release from [Releases](https://github.com/LyubomirT/intense-rp-next/releases) or clone the repo
2. **Run**: Double-click `Intense RP API.exe` or run `python src/main.pyw`
3. **Configure**: Hit the Settings button and fill in your DeepSeek credentials
4. **Choose Browser**: Chrome is recommended for best Cloudflare bypass and network interception
5. **Start**: Click the big Start button and let the magic happen
6. **Connect**: Use `http://127.0.0.1:5000/` in SillyTavern

## 🤖 SillyTavern Integration

### API Connection Setup

1. In SillyTavern, go to **API Connections**
2. Select **Custom (OpenAI-compatible)** as your Chat Completion Source
3. Set **Custom Endpoint** to `http://127.0.0.1:5000/`
4. Hit **Connect** and you're good to go!

### 🎭 Enhanced Features

**DeepThink (R1) Mode**: Just add `{{r1}}` or `[r1]` to your message to enable reasoning mode

**Web Search**: Include `{{search}}` or `[search]` to let DeepSeek search the web

**Custom Formatting**: Choose from multiple message formatting presets or create your own

## 📊 Future Plans

IntenseRP Next is not stopping here! More stuff is coming in very soon:

| Feature | Status | Priority |
|---------|---------|----------|
| 🔄 **Immediate Streaming for CDP** | Planning | High |
| 🖥️ **Switch to Qt6** | Research | Medium |
| 🎭 **Puppeteer Integration** | Planned | Medium |
| 🐧 **Linux Binaries** | Planned | High |
| 🔄 **Auto-updater for Binaries** | Planning | Medium |
| 🌐 **Cloudflare Tunnels Support** | Research | Medium |
| 📡 **Local Network Availability** | Planned | Medium |

## 🐛 Known Issues & Solutions

### Cloudflare Bypass Issues

Likely caused by Cloudflare's challenges. Most of the times this happens when you frequently log in and out of DeepSeek. Technically, the best ways to fix this are:
- **Use Persistent Profiles**: Enable persistent profiles in the settings to keep your session alive. ALSO, this lets the browser store cookies and session data, which helps with Cloudflare challenges.
- **Use Undetected Chrome**: This, obviously, only works if you use Chrome. IntenseRP automatically enables undetected Chrome mode, which helps bypass Cloudflare's bot detection.

### Network Interception Broken Or Unstable

Please note that the feature is still in beta and might not work perfectlly in all cases. Also, note that this has only been implemented and tested for Chrome. If you use Edge, it might not work as well, if at all. IntenseRP Next falls back to the old HTML to Markdown conversion if network interception fails, so you can still use it, but with less reliability.

### Code Blocks Temporarily Pausing Streaming

This is common and actually expected behavior for DOM Scraping (it works properly with CDP). The reason is that DeepSeek AI applies a lot of formatting and transformations to its code blocks, which makes true streaming produce garbled output when trying to convert it to Markdown. IntenseRP Next will automatically pause streaming when it detects a code block in the response and then send the rest of the response after it's completed. CDP doesn't have this issue because it deals with Markdown directly, without any formatting or messy DOM manipulation.

## 🤝 Contributing

We'd love your help making IntenseRP Next even better! If you have:
- 🐛 Bug reports
- 💡 Feature suggestions  
- 🔧 Code contributions
- 📖 Documentation improvements
- 🧪 Testing and feedback

Then please get involved!

Just open an issue or submit a PR. We value all of the contributors for their time and effort, and I'll make sure to give credit where it's due.

## 📝 Credits & History

**IntenseRP Next** is a spiritual and technical successor to the original **IntenseRP API** by [Omega-Slender](https://github.com/Omega-Slender). While many of the original ideas and concepts are preserved, as well as some of the code, the project has been rewritten from the ground up. Nevertheless, the original project laid the foundation for this new version, and I want to acknowledge that.

### 👥 Contributors

<div align="center">

| [<img src="https://avatars.githubusercontent.com/u/127299159?s=100&v=4" width="100px;"/><br /><sub><b>LyubomirT</b></sub>](https://github.com/LyubomirT) | [<img src="https://avatars.githubusercontent.com/u/134849645?s=100&v=4" width="100px;"/><br /><sub><b>Omega-Slender</b></sub>](https://github.com/Omega-Slender) | [<img src="https://avatars.githubusercontent.com/u/103206423?s=100&v=4" width="100px;"/><br /><sub><b>Deaquay</b></sub>](https://github.com/Deaquay) | [<img src="https://avatars.githubusercontent.com/u/131772052?s=100&v=4" width="100px;"/><br /><sub><b>Vova12344weq</b></sub>](https://github.com/Vova12344weq) |
|:---:|:---:|:---:|:---:|
| Lead Developer | Original Creator | Contributor | Testing & QA |


Find all of our contributors on [GitHub](https://github.com/LyubomirT/intense-rp-next/graphs/contributors)

</div>

## 📄 License

This project is open source and available under the [MIT License](https://opensource.org/licenses/MIT) license.

> [!IMPORTANT]
> I've officially received permission from Omega-Slender to relicense the original IntenseRP API under the MIT License. This means that the original distribution license is no longer valid, and this project is now fully compliant with the MIT License.

# 📋 Legal Stuff

1. This project is not affiliated with or endorsed by Omega-Slender or the original IntenseRP API.
2. The original IntenseRP API is available under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/), and you can find it [here](https://github.com/Omega-Slender/intense-rp-api).
3. I do not claim ownership of the original IntenseRP API code, and this project is a separate work that builds upon its ideas and concepts.

## 🔗 Links

- **Original Project**: [IntenseRP API by Omega-Slender](https://github.com/omega-slender/intense-rp-api)
- **SillyTavern**: [Official Website](https://sillytavernai.com/)
- **DeepSeek AI**: [chat.deepseek.com](https://chat.deepseek.com/)

---

<div align="center">

Made with ❤️ for the SillyTavern community

⭐ **Like the project? Give it a star!** ⭐

</div>