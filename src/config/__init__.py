"""
Configuration management module for IntenseRP API
Provides modular, schema-driven configuration system
"""

from .config_manager import ConfigManager, ConfigValidationError
from .config_schema import get_config_schema, get_default_config, ConfigField, ConfigSection, ConfigFieldType
from .config_ui_generator import ConfigUIGenerator
from .config_validators import ConfigValidator, ConditionalValidator
from .browser_config import (
    get_browser_engine,
    get_chromium_browser_path,
    BROWSER_ALIASES,
    CHROMIUM_BROWSERS,
    is_chromium_browser,
    uses_undetected_chromium,
    requires_binary_location,
)

__all__ = [
    'ConfigManager',
    'ConfigValidationError',
    'ConfigUIGenerator',
    'ConfigValidator',
    'ConditionalValidator',
    'get_config_schema',
    'get_default_config',
    'ConfigField',
    'ConfigSection',
    'ConfigFieldType',
    # Browser config exports
    'get_browser_engine',
    'get_chromium_browser_path',
    'BROWSER_ALIASES',
    'CHROMIUM_BROWSERS',
    'is_chromium_browser',
    'uses_undetected_chromium',
    'requires_binary_location',
]