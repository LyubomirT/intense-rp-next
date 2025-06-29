"""
Configuration manager for IntenseRP API
Handles loading, saving, validation, and access to configuration
"""

from typing import Dict, Any, List, Optional, Tuple
from config.config_schema import get_config_schema, get_default_config, find_field_by_key
from config.config_validators import ConfigValidator


class ConfigValidationError(Exception):
    """Raised when configuration validation fails"""
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(f"Configuration validation failed: {'; '.join(errors)}")


class ConfigManager:
    """Manages application configuration with validation and persistence"""
    
    def __init__(self, storage_manager):
        self.storage_manager = storage_manager
        self.validator = ConfigValidator()
        self._config = {}
        self._original_config = get_default_config()
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from storage with defaults"""
        try:
            saved_config = self.storage_manager.load_config(
                path_root="executable", 
                sub_path="save", 
                original=self._original_config
            )
            self._config = self._merge_with_defaults(saved_config)
        except Exception as e:
            print(f"Error loading config, using defaults: {e}")
            self._config = self._original_config.copy()
    
    def _merge_with_defaults(self, saved_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge saved config with current defaults to handle new fields"""
        def merge_recursive(default: Dict, saved: Dict) -> Dict:
            result = default.copy()
            
            for key, value in saved.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_recursive(result[key], value)
                else:
                    result[key] = value
            
            return result
        
        return merge_recursive(self._original_config, saved_config)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'models.deepseek.email')"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config_ref = self._config
        
        # Navigate to the parent dict
        for k in keys[:-1]:
            if k not in config_ref or not isinstance(config_ref[k], dict):
                config_ref[k] = {}
            config_ref = config_ref[k]
        
        # Set the final value
        config_ref[keys[-1]] = value
    
    def get_section(self, section_key: str) -> Dict[str, Any]:
        """Get an entire configuration section"""
        return self.get(section_key, {})
    
    def update_section(self, section_key: str, values: Dict[str, Any]) -> None:
        """Update multiple values in a section"""
        for key, value in values.items():
            full_key = f"{section_key}.{key}" if section_key else key
            self.set(full_key, value)
    
    def get_all(self) -> Dict[str, Any]:
        """Get complete configuration (copy to prevent external mutation)"""
        import copy
        return copy.deepcopy(self._config)
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate entire configuration against schema"""
        errors = []
        
        for section in get_config_schema():
            for field in section.fields:
                if field.validation and field.key:  # Skip buttons and fields without keys
                    value = self.get(field.key)
                    field_errors = self.validator.validate_field(field, value, self._config)
                    errors.extend(field_errors)
        
        return len(errors) == 0, errors
    
    def validate_field(self, key: str, value: Any) -> List[str]:
        """Validate a single field"""
        field = find_field_by_key(key)
        if field and field.validation:
            return self.validator.validate_field(field, value, self._config)
        return []
    
    def save(self) -> None:
        """Save configuration with validation"""
        is_valid, errors = self.validate()
        if not is_valid:
            raise ConfigValidationError(errors)
        
        try:
            self.storage_manager.save_config(
                path_root="executable",
                sub_path="save", 
                new=self._config,
                original=self._original_config
            )
            print("Configuration saved successfully.")
        except Exception as e:
            raise Exception(f"Failed to save configuration: {e}") from e
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults"""
        self._config = self._original_config.copy()
    
    def export_config(self) -> Dict[str, Any]:
        """Export configuration for backup/sharing"""
        return self.get_all()
    
    def import_config(self, config_data: Dict[str, Any], validate: bool = True) -> None:
        """Import configuration from backup/sharing"""
        if validate:
            # Temporarily set config to validate
            old_config = self._config
            self._config = config_data
            
            try:
                is_valid, errors = self.validate()
                if not is_valid:
                    self._config = old_config  # Restore
                    raise ConfigValidationError(errors)
            except Exception:
                self._config = old_config  # Restore
                raise
        else:
            self._config = config_data.copy()
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration for debugging"""
        summary = {}
        
        for section in get_config_schema():
            section_data = {}
            for field in section.fields:
                if field.key:  # Skip buttons
                    value = self.get(field.key)
                    # Mask passwords in summary
                    if field.field_type.value == "password" and value:
                        section_data[field.key.split('.')[-1]] = "*" * len(str(value))
                    else:
                        section_data[field.key.split('.')[-1]] = value
            summary[section.title] = section_data
        
        return summary