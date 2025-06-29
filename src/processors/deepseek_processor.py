from typing import Dict, Any
from processors.base_processor import BaseProcessor
from models.message_models import ChatRequest, DeepSeekSettings


class DeepSeekProcessor(BaseProcessor):
    """Processes DeepSeek-specific settings and configurations"""
    
    def can_process(self, request: ChatRequest) -> bool:
        """Always can process DeepSeek settings"""
        return True
    
    def process(self, request: ChatRequest) -> ChatRequest:
        """Process DeepSeek-specific settings"""
        
        # Auto-detect settings from messages
        detected_settings = DeepSeekSettings.detect_from_messages(request.messages)
        
        # Override with config settings if available
        config_settings = self._get_config_settings()
        
        # Apply settings to request
        request.use_deepthink = detected_settings.deepthink or config_settings.deepthink
        request.use_search = detected_settings.search or config_settings.search
        request.use_text_file = config_settings.text_file
        
        return request
    
    def _get_config_settings(self) -> DeepSeekSettings:
        """Get DeepSeek settings from configuration"""
        deepseek_config = self.get_config_value("models.deepseek", {})
        
        return DeepSeekSettings(
            deepthink=deepseek_config.get("deepthink", False),
            search=deepseek_config.get("search", False),
            text_file=deepseek_config.get("text_file", False)
        )


class DeepSeekConfigValidator:
    """Validates DeepSeek configuration"""
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> bool:
        """Validate DeepSeek configuration"""
        deepseek_config = config.get("models", {}).get("deepseek", {})
        
        # Check required fields for auto-login
        if deepseek_config.get("auto_login", False):
            email = deepseek_config.get("email", "")
            password = deepseek_config.get("password", "")
            
            if not email or not password:
                return False
            
            # Basic email validation
            if "@" not in email or "." not in email:
                return False
            
            # Minimum password length
            if len(password) < 6:
                return False
        
        return True
    
    @staticmethod
    def get_validation_errors(config: Dict[str, Any]) -> list[str]:
        """Get list of validation errors"""
        errors = []
        deepseek_config = config.get("models", {}).get("deepseek", {})
        
        if deepseek_config.get("auto_login", False):
            email = deepseek_config.get("email", "")
            password = deepseek_config.get("password", "")
            
            if not email:
                errors.append("Email is required for auto-login")
            elif "@" not in email or "." not in email:
                errors.append("Invalid email format")
            
            if not password:
                errors.append("Password is required for auto-login")
            elif len(password) < 6:
                errors.append("Password must be at least 6 characters")
        
        return errors