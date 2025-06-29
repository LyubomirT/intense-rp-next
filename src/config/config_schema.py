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
                    key="models.deepseek.search",
                    label="Search:",
                    field_type=ConfigFieldType.SWITCH,
                    default=False,
                    help_text="Enable web search capability"
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
            id="advanced_settings",
            title="Advanced Settings", 
            fields=[
                ConfigField(
                    key="browser",
                    label="Browser:",
                    field_type=ConfigFieldType.DROPDOWN,
                    default="Chrome",
                    options=["Chrome", "Firefox", "Edge", "Safari"],
                    help_text="Browser to use for automation"
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
                    key="show_ip",
                    label="Show IP:",
                    field_type=ConfigFieldType.SWITCH,
                    default=False,
                    help_text="Display local IP address in startup message"
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