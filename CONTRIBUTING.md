# Contributing to IntenseRP Next

Thanks for thinking about contributing! IntenseRP Next is a community project that helps connect DeepSeek AI to SillyTavern, and we're always happy to have more people involved.

## Quick Overview

This project is basically a bridge between SillyTavern and DeepSeek AI using browser automation. It's built with Python and has a Chrome/Edge extension for better response capture. Don't worry if that sounds complicated - there are lots of ways to help that don't require being a Python expert.

## Ways to Contribute

### 🐛 Found a Bug?
Just open an issue and tell us what happened. Include:
- What you were trying to do
- What actually happened
- Your operating system and browser
- Any error messages you saw

No need to write a novel - just enough info so we can reproduce the problem.

### 💡 Got an Idea?
Cool! Open an issue and describe your idea. We're pretty open to suggestions, especially if they make the app easier to use or more reliable.

### 🧪 Want to Test Stuff?
This is very helpful! Try out new releases, test on different browsers, or help verify bug fixes. Just let us know what you tried and how it went.

### 📝 Documentation & Writing
See something confusing in the docs? Know how to explain a feature better? Documentation improvements are always welcome. This includes:
- Fixing typos or unclear instructions
- Adding examples or screenshots
- Improving setup guides
- Writing troubleshooting tips

### 💻 Code Contributions
If you want to dive into the code, that's awesome! The project is mostly Python with some JavaScript for the Chrome/Edge extension. Take a look at our documentation - it has detailed technical info about how everything works.

### ⭐ Just Want to Help?
That's great too! You can help by spreading the word, sharing your experiences, or just giving us a star on GitHub. Every little bit helps!

## Getting Started with Development

### Setting Up
1. Clone the repo: `git clone https://github.com/LyubomirT/intense-rp-next.git`
2. Install Python 3.8+ from python.org
3. Install dependencies: `pip install -r requirements.txt`
4. Run the app: `python src/main.pyw`

### Project Structure
- `src/` - Main Python code
- `src/extension/` - Chrome/Edge extension for network interception
- `src/config/` - Configuration system (pretty cool, it auto-generates UI)
- `src/processors/` - Message processing pipeline
- `src/utils/` - Various utility modules

### Before You Code
- Look at existing code to understand the style
- Check if there are related issues or PRs
- For big changes, maybe open an issue first to discuss the approach

## Submitting Changes

### Pull Requests
1. Fork the repo
2. Create a branch for your changes
3. Make your changes
4. Test that everything still works
5. Submit a pull request

Keep PRs focused on one thing if possible. If you're fixing a bug and adding a feature, consider doing them as separate PRs.

### Commit Messages
Just write clear commit messages that explain what you changed. Of course, something more verbose is always welcome, but we don't require it. Just remember that "fix chrome extension not loading" is better than "fix bug".

## Getting Help

### Where to Ask Questions
- **GitHub Issues**: For bugs, feature requests, or technical questions
- **GitHub Discussions**: For general questions about using the app
- **Pull Request Comments**: For questions about specific code changes

### What to Expect
- We try to respond to issues within a few days (but honestly, it's usually much faster)
- Code reviews happen when maintainers have time
- Don't take feedback personally - we're all here to make the project better

## Things to Keep in Mind

### Code Style
- We use snake_case for functions and variables
- Try to match the existing style in the files you're editing
- Don't worry too much about perfect formatting - we're more interested in working code

### Testing
- Test your changes before submitting
- If you're not sure how to test something, ask
- We don't have automated tests yet (feel free to help with that!)

### Browser Compatibility
- Chrome works best (especially for network interception)
- Edge and Firefox are supported but might be less reliable
- Safari support is experimental

### Python Version
- We support Python 3.8+
- Try to avoid using very new Python features unless necessary

## Project Values

This project is built for the SillyTavern community. We care about:
- **Reliability**: It should work consistently
- **Usability**: Non-technical users should be able to use it
- **Maintainability**: Code should be understandable and well-organized
- **Community**: Everyone should feel welcome to contribute

## Recognition

We keep track of contributors in the README and try to give credit where it's due. If you make a significant contribution, let us know if you'd like to be added to the contributors section.

## Questions?

If something in this guide isn't clear, or you have questions about contributing, just ask! Open an issue or start a discussion. We're pretty friendly and happy to help.

Thanks for considering contributing to IntenseRP Next!