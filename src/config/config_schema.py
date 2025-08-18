"""
Configuration schema definition for IntenseRP API
Declarative approach to defining all configuration options
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import utils.console_manager as console_manager


class ConfigFieldType(Enum):
    TEXT = "text"
    PASSWORD = "password"
    SWITCH = "switch"
    DROPDOWN = "dropdown"
    BUTTON = "button"
    TEXTAREA = "textarea"
    DIVIDER = "divider"


@dataclass
class ValidationError:
    """Structured validation error with field information"""
    field_key: str                     # Field key that failed validation
    message: str                       # Error message
    field: Optional['ConfigField'] = None   # Reference to the field (optional)


@dataclass
class ConfigField:
    """Represents a single configuration field"""
    key: str                           # Dot notation key (e.g., "models.deepseek.email")
    label: str                         # Display label
    field_type: ConfigFieldType        # Widget type
    default: Any                       # Default value
    options: Optional[List[str]] = None     # For dropdown fields
    validation: Optional[str] = None        # Validation function name
    help_text: Optional[str] = None         # Tooltip/help text
    command: Optional[Callable] = None      # For buttons/switches with callbacks
    depends_on: Optional[str] = None        # Conditional field (key that must be True)
    highlight_errors: bool = True           # Whether to show visual error highlighting for this field


@dataclass
class ConfigSection:
    """Represents a section of configuration fields"""
    id: str                           # Unique identifier for the section
    title: str                        # Display title
    fields: List[ConfigField]         # Fields in this section


def get_config_schema() -> List[ConfigSection]:
    """Get the complete configuration schema"""
    return [
        ConfigSection(
            id="deepseek_settings",
            title="DeepSeek Settings",
            fields=[
                ConfigField(
                    key="models.deepseek.email",
                    label="Email:",
                    field_type=ConfigFieldType.TEXT,
                    default="",
                    validation="email",
                    help_text="Required for auto-login"
                ),
                ConfigField(
                    key="models.deepseek.password",
                    label="Password:",
                    field_type=ConfigFieldType.PASSWORD,
                    default="",
                    validation="password",
                    help_text="Minimum 6 characters"
                ),
                ConfigField(
                    key="models.deepseek.auto_login",
                    label="Auto login:",
                    field_type=ConfigFieldType.SWITCH,
                    default=False,
                    help_text="Automatically login using saved credentials"
                ),
                ConfigField(
                    key="models.deepseek.text_file",
                    label="Text file:",
                    field_type=ConfigFieldType.SWITCH,
                    default=False,
                    help_text="Send prompts as file attachments"
                ),
                ConfigField(
                    key="models.deepseek.deepthink",
                    label="Deepthink:",
                    field_type=ConfigFieldType.SWITCH,
                    default=False,
                    help_text="Enable R1 reasoning mode"
                ),
                ConfigField(
                    key="models.deepseek.send_thoughts",
                    label="Send Thoughts:",
                    field_type=ConfigFieldType.SWITCH,
                    default=True,
                    depends_on="models.deepseek.deepthink",
                    help_text="Include R1 thinking content in <think> tags (only when R1 is enabled)"
                ),
                ConfigField(
                    key="models.deepseek.search",
                    label="Search:",
                    field_type=ConfigFieldType.SWITCH,
                    default=False,
                    help_text="Enable web search capability"
                ),
                ConfigField(
                    key="models.deepseek.intercept_network",
                    label="Intercept Network:",
                    field_type=ConfigFieldType.SWITCH,
                    default=False,
                    help_text="Use network interception instead of DOM scraping (Chrome/Edge)"
                ),
            ]
        ),
        
        ConfigSection(
            id="console_settings",
            title="Console Settings",
            fields=[
                ConfigField(
                    key="console.font_family",
                    label="Font Family:",
                    field_type=ConfigFieldType.DROPDOWN,
                    default="Consolas",
                    options=console_manager.ConsoleSettings.FONT_FAMILIES,
                    help_text="Font family for console text"
                ),
                ConfigField(
                    key="console.font_size",
                    label="Font Size:",
                    field_type=ConfigFieldType.DROPDOWN,
                    default="12",
                    options=[str(size) for size in console_manager.ConsoleSettings.FONT_SIZES],
                    help_text="Font size for console text"
                ),
                ConfigField(
                    key="console.color_palette",
                    label="Color Palette:",
                    field_type=ConfigFieldType.DROPDOWN,
                    default="Modern",
                    options=console_manager.ConsoleColorPalettes.get_palette_names(),
                    help_text="Color scheme for console output"
                ),
                ConfigField(
                    key="console.word_wrap",
                    label="Word Wrap:",
                    field_type=ConfigFieldType.SWITCH,
                    default=True,
                    help_text="Wrap long lines in console"
                ),
                ConfigField(
                    key="console.preview",
                    label="Preview Changes",
                    field_type=ConfigFieldType.BUTTON,
                    default=None,
                    command="preview_console_changes",
                    help_text="Apply changes to console immediately"
                ),
            ]
        ),
        
        ConfigSection(
            id="dump_settings",
            title="Dump Settings",
            fields=[
                ConfigField(
                    key="console.dump_enabled",
                    label="Enable Console Dumping:",
                    field_type=ConfigFieldType.SWITCH,
                    default=False,
                    help_text="Enable the 'Dump Console' menu option in the console window"
                ),
                ConfigField(
                    key="console.dump_directory",
                    label="Dump Directory:",
                    field_type=ConfigFieldType.TEXT,
                    default="",
                    validation="dump_directory",
                    help_text="Directory to save console dumps (leave empty to use 'condumps/' in project root)",
                    highlight_errors=False  # Optional field - don't highlight errors as aggressively
                ),
            ]
        ),
        
        ConfigSection(
            id="message_formatting",
            title="Message Formatting",
            fields=[
                ConfigField(
                    key="formatting.preset",
                    label="Formatting Preset:",
                    field_type=ConfigFieldType.DROPDOWN,
                    default="Classic (Name)",
                    options=["Classic (Role)", "Classic (Name)", "Wrapped (Role)", "Wrapped (Name)", "Divided (Role)", "Divided (Name)", "Custom"],
                    help_text="Choose how messages are formatted for DeepSeek. (Role) uses user/assistant labels, (Name) uses character names."
                ),
                ConfigField(
                    key="formatting.user_template",
                    label="User Message Format:",
                    field_type=ConfigFieldType.TEXTAREA,
                    default="{role}: {content}",
                    help_text="Template for user messages. Use {role} for 'user', {name} for character name, {content} for message content."
                ),
                ConfigField(
                    key="formatting.char_template", 
                    label="Character Message Format:",
                    field_type=ConfigFieldType.TEXTAREA,
                    default="{role}: {content}",
                    help_text="Template for character messages. Use {role} for 'assistant', {name} for character name, {content} for message content."
                ),
            ]
        ),
        
        ConfigSection(
            id="logging_settings", 
            title="Logging Settings",
            fields=[
                ConfigField(
                    key="logging.enabled",
                    label="Store logfiles:",
                    field_type=ConfigFieldType.SWITCH,
                    default=False,
                    help_text="Save console output to log files"
                ),
                ConfigField(
                    key="logging.max_file_size",
                    label="Max file size:",
                    field_type=ConfigFieldType.TEXT,
                    default=1048576,  # 1MB in bytes (original format)
                    validation="file_size",
                    help_text="Maximum size per log file (e.g., 1 MB, 500 KB)"
                ),
                ConfigField(
                    key="logging.max_files", 
                    label="Max files:",
                    field_type=ConfigFieldType.TEXT,
                    default=10,  # Integer (original format)
                    validation="max_files",
                    help_text="Maximum number of log files to keep (1-100)"
                ),
            ]
        ),
        
        ConfigSection(
            id="security_settings",
            title="Security Settings",
            fields=[
                ConfigField(
                    key="security.api_auth_enabled",
                    label="Enable API Authentication:",
                    field_type=ConfigFieldType.SWITCH,
                    default=False,
                    help_text="Require Bearer token authentication for API requests"
                ),
                ConfigField(
                    key="security.api_keys",
                    label="API Keys:",
                    field_type=ConfigFieldType.TEXTAREA,
                    default="",
                    validation="api_keys",
                    depends_on="security.api_auth_enabled",
                    help_text="List of valid API keys (one per line). Requests must include Authorization: Bearer <key>"
                ),
                ConfigField(
                    key="security.generate_api_key",
                    label="Generate API Key",
                    field_type=ConfigFieldType.BUTTON,
                    default=None,
                    command="generate_api_key",
                    depends_on="security.api_auth_enabled",
                    help_text="Generate a new secure API key and add it to the list above"
                ),
            ]
        ),
        
        ConfigSection(
            id="advanced_settings",
            title="Advanced Settings", 
            fields=[
                ConfigField(
                    key=None,
                    label="Network Settings",
                    field_type=ConfigFieldType.DIVIDER,
                    default=None
                ),
                ConfigField(
                    key="api.port",
                    label="Network Port:",
                    field_type=ConfigFieldType.TEXT,
                    default=5000,
                    validation="port",
                    help_text="Port number for the API server (1024-65535)"
                ),
                ConfigField(
                    key="show_ip",
                    label="Show IP:",
                    field_type=ConfigFieldType.SWITCH,
                    default=False,
                    help_text="Enable network access and display local IP address. When disabled, API is only accessible from localhost (127.0.0.1)"
                ),
                ConfigField(
                    key=None,
                    label="Browser Configuration",
                    field_type=ConfigFieldType.DIVIDER,
                    default=None
                ),
                ConfigField(
                    key="browser",
                    label="Browser:",
                    field_type=ConfigFieldType.DROPDOWN,
                    default="Chrome",
                    options=["Chrome", "Firefox", "Edge", "Safari", "Custom Chromium"],
                    help_text="Browser to use for automation"
                ),
                ConfigField(
                    key="browser_path",
                    label="Browser Path:",
                    field_type=ConfigFieldType.TEXT,
                    default="",
                    validation="browser_path",
                    help_text="Full path to custom Chromium-based browser executable"
                ),
                ConfigField(
                    key="browser_path_browse",
                    label="Browse",
                    field_type=ConfigFieldType.BUTTON,
                    default=None,
                    command="browse_browser_path",
                    help_text="Browse for Chromium-based browser executable"
                ),
                ConfigField(
                    key="browser_persistent_cookies",
                    label="Persistent cookies:",
                    field_type=ConfigFieldType.SWITCH,
                    default=False,
                    help_text="Enable persistent cookies to bypass Cloudflare and store login sessions (Chrome/Edge only)"
                ),
                ConfigField(
                    key="clear_browser_data",
                    label="Clear Browser Data",
                    field_type=ConfigFieldType.BUTTON,
                    default=None,
                    command="clear_browser_data",
                    help_text="Clear stored cookies and browser data (useful for debugging or starting fresh)"
                ),
                ConfigField(
                    key=None,
                    label="Application Behavior",
                    field_type=ConfigFieldType.DIVIDER,
                    default=None
                ),
                ConfigField(
                    key="check_version",
                    label="Check version at startup:",
                    field_type=ConfigFieldType.SWITCH,
                    default=True,
                    help_text="Check for updates when starting"
                ),
                ConfigField(
                    key="show_console",
                    label="Show Console:",
                    field_type=ConfigFieldType.SWITCH,
                    default=False,
                    command="on_console_toggle",
                    help_text="Show console window on startup"
                ),
                ConfigField(
                    key=None,
                    label="Auto Refresh Settings",
                    field_type=ConfigFieldType.DIVIDER,
                    default=None
                ),
                ConfigField(
                    key="refresh_timer.enabled",
                    label="Auto Refresh Page:",
                    field_type=ConfigFieldType.SWITCH,
                    default=False,
                    help_text="Automatically refresh DeepSeek page when idle to prevent session timeouts"
                ),
                ConfigField(
                    key="refresh_timer.idle_timeout",
                    label="Idle Timeout (minutes):",
                    field_type=ConfigFieldType.TEXT,
                    default=5,
                    validation="refresh_idle_timeout",
                    depends_on="refresh_timer.enabled",
                    help_text="Minutes of inactivity before starting refresh countdown (1-60 minutes)"
                ),
                ConfigField(
                    key="refresh_timer.grace_period",
                    label="Grace Period (seconds):",
                    field_type=ConfigFieldType.TEXT,
                    default=25,
                    validation="refresh_grace_period",
                    depends_on="refresh_timer.enabled",
                    help_text="Seconds to wait after idle timeout before refreshing (5-120 seconds)"
                ),
                ConfigField(
                    key="refresh_timer.use_grace_period",
                    label="Use Grace Period:",
                    field_type=ConfigFieldType.SWITCH,
                    default=True,
                    depends_on="refresh_timer.enabled",
                    help_text="When enabled, warns before refreshing. When disabled, refreshes immediately after idle timeout."
                ),
            ]
        ),
    ]


def get_default_config() -> Dict[str, Any]:
    """Generate default configuration from schema"""
    config = {}
    
    for section in get_config_schema():
        for field in section.fields:
            if field.key and field.default is not None:
                # Build nested structure
                keys = field.key.split('.')
                current = config
                
                for key in keys[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                
                current[keys[-1]] = field.default
    
    return config


def find_field_by_key(key: str) -> Optional[ConfigField]:
    """Find a field by its key"""
    for section in get_config_schema():
        for field in section.fields:
            if field.key == key:
                return field
    return None


def find_section_by_id(section_id: str) -> Optional[ConfigSection]:
    """Find a section by its ID"""
    for section in get_config_schema():
        if section.id == section_id:
            return section
    return None