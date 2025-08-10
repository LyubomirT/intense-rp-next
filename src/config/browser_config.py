"""
Browser configuration for resolving browser engine aliases and executable paths.
Declarative maps used by webdriver utilities.
"""

from typing import Dict, List, Optional
import platform
import os
import shutil


# Map user-facing browser names to SeleniumBase engines
BROWSER_ALIASES: Dict[str, str] = {
    "chrome": "chrome",
    "brave": "chrome",   # Brave uses Chrome's WebDriver/engine
    "edge": "edge",
    "firefox": "firefox",
    "safari": "safari",
}

# Sets for behavior grouping
CHROMIUM_BROWSERS = {"chrome", "edge", "brave"}
UC_SUPPORTED_BROWSERS = {"chrome", "brave"}  # browsers that use undetected-chromium
BROWSERS_REQUIRING_BINARY = {"brave"}        # browsers that need a custom binary_location


# Path templates for Chromium-based browsers per OS.
# Placeholders such as {PROGRAMFILES} are resolved from environment variables at runtime.
CHROMIUM_PATH_TEMPLATES: Dict[str, Dict[str, List[str]]] = {
    "Windows": {
        "brave": [
            "{PROGRAMFILES}\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
            "{PROGRAMFILES(X86)}\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
            "{LOCALAPPDATA}\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
        ],
    },
    "Darwin": {
        "brave": [
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        ],
    },
    "Linux": {
        "brave": [
            "/usr/bin/brave-browser",
            "/usr/bin/brave",
            "/snap/bin/brave",
            "/opt/brave.com/brave/brave-browser",
            "/usr/local/bin/brave-browser",
            "/usr/local/bin/brave",
        ],
    },
}


def is_chromium_browser(browser_name: str) -> bool:
    """Whether the browser is Chromium-based (used for extension and profile logic)."""
    return (browser_name or "").lower() in CHROMIUM_BROWSERS


def uses_undetected_chromium(browser_name: str) -> bool:
    """Whether the browser should use undetected-chromium."""
    return (browser_name or "").lower() in UC_SUPPORTED_BROWSERS


def requires_binary_location(browser_name: str) -> bool:
    """Whether Selenium needs an explicit binary_location for the browser."""
    return (browser_name or "").lower() in BROWSERS_REQUIRING_BINARY


def get_browser_engine(browser_name: str) -> str:
    """Resolve the actual SeleniumBase engine for a given browser name."""
    key = (browser_name or "").lower()
    return BROWSER_ALIASES.get(key, key or "chrome")


def _expand_template(path_template: str) -> str:
    """Expand simple {ENV_VAR} placeholders from environment variables."""
    import re

    def replace_var(match):
        var = match.group(1)
        return os.environ.get(var, "")

    return re.sub(r"\{([^}]+)\}", replace_var, path_template)


def get_chromium_browser_path(browser_name: str, user_path: Optional[str] = None) -> Optional[str]:
    """
    Resolve the executable path for a Chromium-based browser.
    Currently used for Brave, which requires setting binary_location.

    If user_path is provided, it takes precedence over auto-detected locations.
    """
    system = platform.system()
    browser_key = (browser_name or "").lower()

    candidates: List[str] = []

    # User-provided override (highest priority)
    if user_path:
        up = user_path.strip()
        if up:
            candidates.insert(0, up)

    # Add declarative template-based candidates
    os_map = CHROMIUM_PATH_TEMPLATES.get(system, {})
    for template in os_map.get(browser_key, []):
        candidates.append(_expand_template(template))

    # Add dynamic PATH-based detections where appropriate
    if system in ("Linux", "Darwin"):
        which_path = shutil.which("brave-browser") or shutil.which("brave")
        if which_path:
            candidates.insert(0, which_path)

    # Return first existing executable
    for path in candidates:
        if path and os.path.exists(path) and os.access(path, os.X_OK):
            return path

    return None
