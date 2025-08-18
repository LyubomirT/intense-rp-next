"""
Configuration validation functions for IntenseRP API
Handles all validation logic for configuration fields
"""

import re
from typing import List, Any
from .config_schema import ConfigField, ValidationError


class ConfigValidator:
    """Handles validation of configuration fields"""
    
    def __init__(self):
        # Register validation functions
        self.validators = {
            'email': self._validate_email,
            'password': self._validate_password,
            'file_size': self._validate_file_size,
            'max_files': self._validate_max_files,
            'dump_directory': self._validate_dump_directory,
            'port': self._validate_port,
            'api_keys': self._validate_api_keys,
            'browser_path': self._validate_browser_path,
            'refresh_idle_timeout': self._validate_refresh_idle_timeout,
            'refresh_grace_period': self._validate_refresh_grace_period,
        }
    
    def validate_field(self, field: ConfigField, value: Any, config_data: dict = None) -> List[ValidationError]:
        """Validate a single field and return list of ValidationError objects"""
        if not field.validation:
            return []
        
        # Check conditional validation - skip if dependency not met
        if config_data and not self._should_validate_field(field, config_data):
            return []
        
        validator_func = self.validators.get(field.validation)
        if not validator_func:
            return [ValidationError(field.key or "unknown", f"Unknown validator: {field.validation}", field)]
        
        try:
            error_messages = validator_func(field, value)
            # Convert string error messages to ValidationError objects
            return [ValidationError(field.key or "unknown", msg, field) for msg in error_messages]
        except Exception as e:
            return [ValidationError(field.key or "unknown", f"Validation error for {field.label}: {e}", field)]
    
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
        
        # Dump directory should only be validated if console dumping is enabled
        if field.key == "console.dump_directory":
            dump_enabled = config_data.get("console", {}).get("dump_enabled", False)
            return dump_enabled
        
        # API keys should only be validated if API authentication is enabled
        if field.key == "security.api_keys":
            api_auth_enabled = config_data.get("security", {}).get("api_auth_enabled", False)
            return api_auth_enabled
        
        # Browser path should only be validated if Custom Chromium browser is selected
        if field.key == "browser_path":
            browser = config_data.get("browser", "Chrome")
            return browser == "Custom Chromium"
        
        # Refresh timer fields should only be validated if refresh timer is enabled
        if field.key and field.key.startswith("refresh_timer.") and field.key != "refresh_timer.enabled":
            refresh_enabled = config_data.get("refresh_timer", {}).get("enabled", False)
            if not refresh_enabled:
                return False
            
            # Grace period field should only be validated if "use grace period" is enabled
            if field.key == "refresh_timer.grace_period":
                use_grace_period = config_data.get("refresh_timer", {}).get("use_grace_period", True)
                return use_grace_period
            
            return True
        
        # Tunnel fields should only be validated if tunnel is enabled
        if field.key and field.key.startswith("tunnel.") and field.key != "tunnel.enabled":
            tunnel_enabled = config_data.get("tunnel", {}).get("enabled", False)
            return tunnel_enabled
        
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
    
    def _validate_dump_directory(self, field: ConfigField, value: str) -> List[str]:
        """Validate dump directory path"""
        # Empty string is allowed (use default condumps/ directory)
        if not value or not value.strip():
            return []
        
        directory_path = value.strip()
        
        # Check if it's a valid path format
        try:
            import os
            # Check if path is valid format
            if not os.path.isabs(directory_path):
                # Relative paths are allowed
                pass
            
            # Check if directory exists
            if not os.path.exists(directory_path):
                return [f"{field.label} Directory does not exist: {directory_path}"]
            
            # Check if it's actually a directory
            if not os.path.isdir(directory_path):
                return [f"{field.label} Path is not a directory: {directory_path}"]
            
            # Check if directory is writable
            if not os.access(directory_path, os.W_OK):
                return [f"{field.label} Directory is not writable: {directory_path}"]
            
            return []
        except Exception:
            return [f"{field.label} Invalid directory path format"]
    
    def _validate_port(self, field: ConfigField, value) -> List[str]:
        """Validate network port number"""
        if value is None:
            return [f"{field.label} Port number is required"]
        
        # Handle integer values (stored format)
        if isinstance(value, int):
            if value < 1024 or value > 65535:
                return [f"{field.label} Port must be between 1024 and 65535"]
            return []
        
        # Handle string values (user input format)
        if not value or not str(value).strip():
            return [f"{field.label} Port number is required"]
        
        try:
            port = int(str(value).strip())
            if port < 1024 or port > 65535:
                return [f"{field.label} Port must be between 1024 and 65535"]
            return []
        except ValueError:
            return [f"{field.label} Port must be a valid number"]
    
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
    
    def _validate_api_keys(self, field: ConfigField, value: str) -> List[str]:
        """Validate API keys"""
        if not value or not value.strip():
            return [f"{field.label} At least one API key is required when authentication is enabled"]
        
        lines = value.strip().split('\n')
        valid_keys = []
        
        for i, line in enumerate(lines, 1):
            key = line.strip()
            if not key:
                continue  # Skip empty lines
            
            # Basic validation - API key should be at least 16 characters for security
            if len(key) < 16:
                return [f"{field.label} API key on line {i} is too short (minimum 16 characters)"]
            
            # Check for duplicates
            if key in valid_keys:
                return [f"{field.label} Duplicate API key found on line {i}"]
            
            valid_keys.append(key)
        
        if not valid_keys:
            return [f"{field.label} At least one valid API key is required"]
        
        return []
    
    def _validate_browser_path(self, field: ConfigField, value: str) -> List[str]:
        """Validate custom browser binary path"""
        if not value or not value.strip():
            return [f"{field.label} Browser path is required when using Custom Chromium"]
        
        browser_path = value.strip()
        
        # Check if file exists
        try:
            import os
            if not os.path.exists(browser_path):
                return [f"{field.label} Browser executable not found: {browser_path}"]
            
            # Check if it's a file (not directory)
            if not os.path.isfile(browser_path):
                return [f"{field.label} Path is not a file: {browser_path}"]
            
            # Check if file is executable (on Unix systems)
            if hasattr(os, 'access'):
                if not os.access(browser_path, os.X_OK):
                    return [f"{field.label} Browser executable is not executable: {browser_path}"]
            
            # Basic filename validation for common browser executables
            filename = os.path.basename(browser_path).lower()
            valid_names = ['chrome', 'chromium', 'msedge', 'brave', 'opera', 'vivaldi']
            
            # Check if filename contains any known browser names
            is_valid_browser = any(name in filename for name in valid_names) or filename.endswith('.exe')
            
            if not is_valid_browser:
                return [f"{field.label} File does not appear to be a Chromium-based browser executable. Expected names: {', '.join(valid_names)}"]
            
            return []
            
        except Exception as e:
            return [f"{field.label} Error validating browser path: {str(e)}"]

    def _validate_refresh_idle_timeout(self, field: ConfigField, value) -> List[str]:
        """Validate refresh idle timeout in minutes"""
        if value is None:
            return [f"{field.label} Idle timeout is required"]
        
        # Handle integer values (stored format)
        if isinstance(value, int):
            if value < 1 or value > 60:
                return [f"{field.label} Idle timeout must be between 1 and 60 minutes"]
            return []
        
        # Handle string values (user input format)
        if not value or not str(value).strip():
            return [f"{field.label} Idle timeout is required"]
        
        try:
            timeout = int(str(value).strip())
            if timeout < 1 or timeout > 60:
                return [f"{field.label} Idle timeout must be between 1 and 60 minutes"]
            return []
        except ValueError:
            return [f"{field.label} Idle timeout must be a valid number"]

    def _validate_refresh_grace_period(self, field: ConfigField, value) -> List[str]:
        """Validate refresh grace period in seconds"""
        if value is None:
            return [f"{field.label} Grace period is required"]
        
        # Handle integer values (stored format)
        if isinstance(value, int):
            if value < 5 or value > 120:
                return [f"{field.label} Grace period must be between 5 and 120 seconds"]
            return []
        
        # Handle string values (user input format)
        if not value or not str(value).strip():
            return [f"{field.label} Grace period is required"]
        
        try:
            grace = int(str(value).strip())
            if grace < 5 or grace > 120:
                return [f"{field.label} Grace period must be between 5 and 120 seconds"]
            return []
        except ValueError:
            return [f"{field.label} Grace period must be a valid number"]

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