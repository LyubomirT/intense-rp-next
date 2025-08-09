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
        
        # Priority: Model suffix > API parameters > message content detection > config settings
        
        # Check for model suffix overrides first (highest priority)
        if request.is_chat_model():
            # -chat model: Force reasoning OFF, ignore all other sources
            request.use_deepthink = False
        elif request.is_reasoner_model():
            # -reasoner model: Force reasoning ON, but still respect Send Thoughts setting
            request.use_deepthink = True
        else:
            # Normal model: Use existing priority logic
            
            # Check for API parameters first
            if request.api_use_r1 is not None:
                request.use_deepthink = request.api_use_r1
            elif request.api_use_search is not None:
                # If no r1 parameter but search is provided, use detected settings for deepthink
                detected_settings = DeepSeekSettings.detect_from_messages(request.messages)
                request.use_deepthink = detected_settings.deepthink
            else:
                # Auto-detect settings from messages
                detected_settings = DeepSeekSettings.detect_from_messages(request.messages)
                request.use_deepthink = detected_settings.deepthink
            
            # Override with config settings if no API parameters or detection
            config_settings = self._get_config_settings()
            
            # Apply config fallbacks only if not set by API params or detection
            if request.api_use_r1 is None and not request.use_deepthink:
                request.use_deepthink = config_settings.deepthink
        
        # Handle search parameter (not affected by model suffixes)
        if request.api_use_search is not None:
            request.use_search = request.api_use_search
        else:
            # Auto-detect from messages or use config
            detected_settings = DeepSeekSettings.detect_from_messages(request.messages)
            request.use_search = detected_settings.search
            
            # Apply config fallbacks
            config_settings = self._get_config_settings()
            if not request.use_search:
                request.use_search = config_settings.search
        
        # Text file setting comes from config only
        config_settings = self._get_config_settings()
        request.use_text_file = config_settings.text_file
        
        # Clean directives from message content
        self._clean_directives_from_messages(request.messages)
        
        return request
    
    def _get_config_settings(self) -> DeepSeekSettings:
        """Get DeepSeek settings from configuration"""
        deepseek_config = self.get_config_value("models.deepseek", {})
        
        return DeepSeekSettings(
            deepthink=deepseek_config.get("deepthink", False),
            search=deepseek_config.get("search", False),
            text_file=deepseek_config.get("text_file", False)
        )
    
    def _clean_directives_from_messages(self, messages) -> None:
        """Remove DeepSeek directives from all user messages"""
        for message in messages:
            if message.role.value == "user":
                message.content = DeepSeekSettings.clean_directives_from_content(message.content)


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