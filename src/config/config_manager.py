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
        self._hidden_vars = {}  # Hidden variables stored in separate files
        self._load_config()
        self._load_hidden_vars()
    
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
        
        merged_config = merge_recursive(self._original_config, saved_config)
        
        # Handle backward compatibility for formatting presets
        merged_config = self._migrate_formatting_presets(merged_config)
        
        return merged_config
    
    def _migrate_formatting_presets(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate old formatting preset values to new (Name)/(Role) format"""
        try:
            formatting = config.get('formatting', {})
            preset = formatting.get('preset', '')
            
            # Map old preset names to new format
            preset_migration = {
                'Classic': 'Classic (Name)',     # Default to Name for better UX
                'Wrapped': 'Wrapped (Name)',     # Default to Name for better UX  
                'Divided': 'Divided (Name)',     # Default to Name for better UX
                'Custom': 'Custom'               # Custom stays the same
            }
            
            if preset in preset_migration:
                old_preset = preset
                new_preset = preset_migration[preset]
                config['formatting']['preset'] = new_preset
                print(f"Migrated formatting preset from '{old_preset}' to '{new_preset}'")
            
        except Exception as e:
            print(f"Error migrating formatting presets: {e}")
        
        return config
    
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
            self._save_hidden_vars()
            print("Configuration saved successfully.")
        except Exception as e:
            raise Exception(f"Failed to save configuration: {e}") from e
    
    def _load_hidden_vars(self) -> None:
        """Load hidden variables from encrypted files"""
        try:
            import os
            from cryptography.fernet import Fernet
            
            save_path = self.storage_manager.get_path("executable", "save")
            if not save_path or not os.path.exists(save_path):
                # Set defaults
                self._hidden_vars['custom_user_template'] = "{name}: {content}"
                self._hidden_vars['custom_char_template'] = "{name}: {content}"
                return
            
            # Load encryption key (same as main config)
            key = self.storage_manager._load_key("executable", "save")
            if not key:
                # Set defaults if no key exists
                self._hidden_vars['custom_user_template'] = "{name}: {content}"
                self._hidden_vars['custom_char_template'] = "{name}: {content}"
                return
            
            fernet = Fernet(key)
            
            # Load encrypted custom template files
            user_template_file = os.path.join(save_path, "custom_user_template.enc")
            char_template_file = os.path.join(save_path, "custom_char_template.enc")
            
            if os.path.exists(user_template_file):
                with open(user_template_file, 'rb') as f:
                    encrypted_data = f.read()
                    decrypted_data = fernet.decrypt(encrypted_data)
                    self._hidden_vars['custom_user_template'] = decrypted_data.decode('utf-8')
            else:
                self._hidden_vars['custom_user_template'] = "{name}: {content}"
                
            if os.path.exists(char_template_file):
                with open(char_template_file, 'rb') as f:
                    encrypted_data = f.read()
                    decrypted_data = fernet.decrypt(encrypted_data)
                    self._hidden_vars['custom_char_template'] = decrypted_data.decode('utf-8')
            else:
                self._hidden_vars['custom_char_template'] = "{name}: {content}"
                
        except Exception as e:
            print(f"Error loading hidden variables: {e}")
            # Set defaults
            self._hidden_vars['custom_user_template'] = "{name}: {content}"
            self._hidden_vars['custom_char_template'] = "{name}: {content}"
    
    def _save_hidden_vars(self) -> None:
        """Save hidden variables to encrypted files"""
        try:
            import os
            from cryptography.fernet import Fernet
            
            save_path = self.storage_manager.get_path("executable", "save")
            if not save_path:
                return
            
            os.makedirs(save_path, exist_ok=True)
            
            # Ensure encryption key exists (same as main config)
            key = self.storage_manager._load_key("executable", "save")
            if not key:
                self.storage_manager._generate_key("executable", "save")
                key = self.storage_manager._load_key("executable", "save")
                if not key:
                    raise ValueError("Could not load or create encryption key")
            
            fernet = Fernet(key)
            
            # Save encrypted custom template files
            user_template_file = os.path.join(save_path, "custom_user_template.enc")
            char_template_file = os.path.join(save_path, "custom_char_template.enc")
            
            user_template = self._hidden_vars.get('custom_user_template', "{name}: {content}")
            char_template = self._hidden_vars.get('custom_char_template', "{name}: {content}")
            
            # Encrypt and save user template
            encrypted_user = fernet.encrypt(user_template.encode('utf-8'))
            with open(user_template_file, 'wb') as f:
                f.write(encrypted_user)
                
            # Encrypt and save char template
            encrypted_char = fernet.encrypt(char_template.encode('utf-8'))
            with open(char_template_file, 'wb') as f:
                f.write(encrypted_char)
                
        except Exception as e:
            print(f"Error saving hidden variables: {e}")
    
    def get_hidden_var(self, key: str, default: str = "") -> str:
        """Get a hidden variable value"""
        return self._hidden_vars.get(key, default)
    
    def set_hidden_var(self, key: str, value: str) -> None:
        """Set a hidden variable value"""
        self._hidden_vars[key] = value
    
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