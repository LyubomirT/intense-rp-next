"""
Configuration validation functions for IntenseRP API
Handles all validation logic for configuration fields
"""

import re
from typing import List, Any
import os
from config.config_schema import ConfigField


class ConfigValidator:
    """Handles validation of configuration fields"""
    
    def __init__(self):
        # Register validation functions
        self.validators = {
            'email': self._validate_email,
            'password': self._validate_password,
            'file_size': self._validate_file_size,
            'max_files': self._validate_max_files,
            'directory_path': self._validate_directory_path,
        }
    
    def validate_field(self, field: ConfigField, value: Any, config_data: dict = None) -> List[str]:
        """Validate a single field and return list of error messages"""
        if not field.validation:
            return []
        
        # Check conditional validation - skip if dependency not met
        if config_data and not self._should_validate_field(field, config_data):
            return []
        
        validator_func = self.validators.get(field.validation)
        if not validator_func:
            return [f"Unknown validator: {field.validation}"]
        
        try:
            return validator_func(field, value)
        except Exception as e:
            return [f"Validation error for {field.label}: {e}"]
    
    def _should_validate_field(self, field: ConfigField, config_data: dict) -> bool:
        """Check if field should be validated based on conditional logic"""
        # Logging fields should only be validated if logging is enabled
        if field.key and field.key.startswith("logging.") and field.key != "logging.enabled":
            logging_enabled = config_data.get("logging", {}).get("enabled", False)
            return logging_enabled
        
        # DeepSeek auth fields should only be validated if auto_login is enabled
        if field.key in ["models.deepseek.email", "models.deepseek.password"]:
            auto_login = config_data.get("models", {}).get("deepseek", {}).get("auto_login", False)
            return auto_login
        
        # By default, validate the field
        return True
    
    def _validate_email(self, field: ConfigField, value: str) -> List[str]:
        """Validate email address"""
        if not value or not value.strip():
            return [f"{field.label} Email is required"]
        
        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(email_pattern, value.strip()):
            return [f"{field.label} Invalid email format"]
        
        return []
    
    def _validate_password(self, field: ConfigField, value: str) -> List[str]:
        """Validate password"""
        if not value or not value.strip():
            return [f"{field.label} Password is required"]
        
        if len(value.strip()) < 6:
            return [f"{field.label} Password must be at least 6 characters"]
        
        return []
    
    def _validate_file_size(self, field: ConfigField, value) -> List[str]:
        """Validate file size format (e.g., '1 MB', '500 KB') or integer bytes"""
        if value is None:
            return [f"{field.label} File size is required"]
        
        # Handle integer values (stored format)
        if isinstance(value, int):
            if value <= 0:
                return [f"{field.label} File size must be greater than 0"]
            return []
        
        # Handle string values (user input format)
        if not value or not str(value).strip():
            return [f"{field.label} File size is required"]
        
        try:
            self._parse_file_size(str(value).strip())
            return []
        except ValueError:
            return [f"{field.label} Invalid file size format. Use format like '1 MB' or '500 KB'"]
    
    def _validate_max_files(self, field: ConfigField, value) -> List[str]:
        """Validate max files count"""
        if value is None:
            return [f"{field.label} Max files count is required"]
        
        # Handle integer values (stored format)
        if isinstance(value, int):
            if value < 1 or value > 100:
                return [f"{field.label} Max files must be between 1 and 100"]
            return []
        
        # Handle string values (user input format)
        if not value or not str(value).strip():
            return [f"{field.label} Max files count is required"]
        
        try:
            max_files = int(str(value).strip())
            if max_files < 1 or max_files > 100:
                return [f"{field.label} Max files must be between 1 and 100"]
            return []
        except ValueError:
            return [f"{field.label} Max files must be a valid number"]

    def _validate_directory_path(self, field: ConfigField, value: str) -> List[str]:
        """Validate directory path"""
        if not value or not value.strip():
            return []  # Empty path is allowed (will use default)
    
        path = value.strip()
        
        # Check if path is absolute
        if not os.path.isabs(path):
            return [f"{field.label} Path must be absolute"]
        
        # Check if parent directory exists (the path itself doesn't need to exist yet)
        parent_dir = os.path.dirname(path)
        if parent_dir and not os.path.exists(parent_dir):
            return [f"{field.label} Parent directory does not exist: {parent_dir}"]
        
        # Check if path is writable (if it exists) or if parent is writable
        test_dir = path if os.path.exists(path) else parent_dir
        if test_dir and not os.access(test_dir, os.W_OK):
            return [f"{field.label} Directory is not writable: {test_dir}"]
        
        return []
    
    @staticmethod
    def _parse_file_size(size_str: str) -> int:
        """Convert human readable size to bytes (same logic as original)"""
        try:
            size_str = size_str.strip().upper()
            if size_str.endswith('MB'):
                return int(float(size_str[:-2].strip()) * 1024 * 1024)
            elif size_str.endswith('KB'):
                return int(float(size_str[:-2].strip()) * 1024)
            elif size_str.endswith('B'):
                return int(size_str[:-1].strip())
            else:
                # Assume bytes if no unit
                return int(size_str)
        except (ValueError, IndexError):
            raise ValueError("Invalid file size format")
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Convert bytes to human readable format (same logic as original)"""
        if size_bytes >= 1024 * 1024:
            return f"{size_bytes // (1024 * 1024)} MB"
        elif size_bytes >= 1024:
            return f"{size_bytes // 1024} KB"
        else:
            return f"{size_bytes} B"


class ConditionalValidator:
    """Handles conditional validation (e.g., email/password required if auto_login is True)"""
    
    @staticmethod
    def validate_deepseek_auth(config_data: dict) -> List[str]:
        """Validate DeepSeek authentication settings - NOTE: Now handled in main validation"""
        # This is now handled by the main validator's conditional logic
        # Keeping this method for backward compatibility but it does nothing
        return []
    
    @staticmethod
    def validate_all_conditional(config_data: dict) -> List[str]:
        """Run all conditional validations"""
        errors = []
        # Note: Most conditional validation is now handled in the main field validator
        # This method is kept for any cross-field validations that might be added later
        return errors