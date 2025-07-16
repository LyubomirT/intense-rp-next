import re
from typing import Dict, Any
from processors.base_processor import BaseProcessor
from models.message_models import ChatRequest, CharacterInfo, MessageRole


class CharacterProcessor(BaseProcessor):
    """Processes character-specific data and formatting"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.config_manager = config.get('config_manager') if config else None
    
    def can_process(self, request: ChatRequest) -> bool:
        """Always can process character data"""
        return True
    
    def process(self, request: ChatRequest) -> ChatRequest:
        """Process character information and format messages using original logic"""
        
        # Clean up duplicate system messages first
        self._cleanup_duplicate_system_messages(request)
        
        # Use the original approach: combine all messages, then process the combined string
        combined_content = self._combine_messages(request)
        
        # Extract character info - prioritize API parameters over message content
        character_info = self._extract_character_info_from_combined(combined_content)
        
        # Override with API parameters if provided (highest priority)
        if request.api_char_name is not None:
            character_info.character_name = request.api_char_name
        if request.api_user_name is not None:
            character_info.user_name = request.api_user_name
        
        # Process the combined content (like original logic)
        processed_content = self._process_combined_content(combined_content, character_info, request)
        
        # Apply new formatting system if configured
        if self.config_manager:
            formatter = MessageFormatter(self.config_manager)
            formatted_content = formatter.format_messages(request, character_info)
            # Apply template replacements from original logic
            formatted_content = self._apply_template_replacements(formatted_content, request)
            request._processed_content = formatted_content
        else:
            # Fallback to original logic
            request._processed_content = processed_content
        
        return request
    
    def _cleanup_duplicate_system_messages(self, request: ChatRequest) -> None:
        """Remove duplicate consecutive system messages"""
        messages = request.messages
        
        if (len(messages) >= 2 and 
            messages[-1].role == MessageRole.SYSTEM and 
            messages[-2].role == MessageRole.SYSTEM):
            messages.pop(-2)
    
    def _combine_messages(self, request: ChatRequest) -> str:
        """Combine messages like the original code did"""
        formatted_messages = [f"{msg.role.value}: {msg.content}" for msg in request.messages]
        return "\n\n".join(formatted_messages)
    
    def _extract_character_info_from_combined(self, content: str) -> CharacterInfo:
        """Extract character info from combined content (original approach)"""
        character_info = CharacterInfo()
        
        character_match = re.search(r'DATA1:\s*"([^"]*)"', content)
        user_match = re.search(r'DATA2:\s*"([^"]*)"', content)
        
        if character_match:
            character_info.character_name = character_match.group(1)
        if user_match:
            character_info.user_name = user_match.group(1)
            
        return character_info
    
    def _process_combined_content(self, content: str, character_info: CharacterInfo, request: ChatRequest) -> str:
        """Process combined content using original logic"""
        
        # Remove DATA1 and DATA2 lines
        content = re.sub(r'DATA1:\s*"[^"]*"', "", content)
        content = re.sub(r'DATA2:\s*"[^"]*"', "", content)
        
        # Remove other markers
        content = re.sub(r"({{r1}}|\[r1\]|\(r1\))", "", content, flags=re.IGNORECASE)
        content = re.sub(r"({{search}}|\[search\])", "", content, flags=re.IGNORECASE)
        
        # Replace role names only if we have explicit character info from DATA1/DATA2
        # This prevents corrupting existing character names in user content
        has_explicit_char_info = (
            character_info.character_name != "Character" or 
            character_info.user_name != "User"
        )
        
        if has_explicit_char_info:
            # Only replace role prefixes at the start of lines or after double newlines
            # to avoid corrupting existing character names in content
            content = re.sub(r'(^|\n\n)system:\s*', r'\1', content)
            content = re.sub(r'(^|\n\n)assistant:\s*', fr'\1{character_info.character_name}: ', content)
            content = re.sub(r'(^|\n\n)user:\s*', fr'\1{character_info.user_name}: ', content)
        else:
            # If no explicit character info, just remove system role prefix
            # but preserve user/assistant content as-is to avoid corrupting character names
            content = re.sub(r'(^|\n\n)system:\s*', r'\1', content)
        
        # Replace template variables
        content = self._apply_template_replacements(content, request)
        
        return content.strip()
    
    def _apply_template_replacements(self, content: str, request: ChatRequest) -> str:
        """Apply template variable replacements"""
        content = content.replace("{{temperature}}", str(request.temperature))
        content = content.replace("{{max_tokens}}", str(request.max_tokens))
        
        # Clean up extra newlines
        content = re.sub(r"\n{3,}", "\n\n", content)
        
        return content.strip()


class MessageFormatter:
    """Utility class for formatting messages"""
    
    # Predefined formatting templates
    PRESETS = {
        "Classic": {
            "pattern": "{role}: {content}",
            "separator": "\n\n",
            "description": "Traditional role-based formatting (user/assistant/system)"
        },
        "Wrapped": {
            "pattern": "<{role}>\n{content}\n</{role}>",
            "separator": "\n\n",
            "description": "XML-style wrapped formatting with roles"
        },
        "Divided": {
            "pattern": "----------- {role} -----------\n{content}",
            "separator": "\n----------- ----------- -----------\n",
            "description": "Divided formatting with visual separators"
        }
    }
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
    
    @staticmethod
    def format_for_api(request: ChatRequest) -> str:
        """Format messages for API consumption"""
        
        # If we have processed content, use it directly
        if hasattr(request, '_processed_content'):
            return f"[Important Information]\n{request._processed_content}"
        
        # Fallback to individual message processing
        formatted_messages = []
        
        for message in request.messages:
            if message.content.strip():  # Only include non-empty messages
                formatted_messages.append(f"{message.role.value}: {message.content}")
        
        content = "\n\n".join(formatted_messages)
        return f"[Important Information]\n{content.strip()}"
    
    def format_messages(self, request: ChatRequest, character_info: CharacterInfo) -> str:
        """Format messages based on current configuration"""
        
        # Get formatting configuration
        preset = self._get_config_value('formatting.preset', 'Classic')
        
        if preset == 'Custom':
            return self._format_custom(request, character_info)
        elif preset in self.PRESETS:
            return self._format_preset(request, character_info, preset)
        else:
            # Fallback to Classic
            return self._format_preset(request, character_info, 'Classic')
    
    def _get_config_value(self, key: str, default: Any) -> Any:
        """Get configuration value with fallback"""
        if self.config_manager:
            return self.config_manager.get(key, default)
        return default
    
    def _format_preset(self, request: ChatRequest, character_info: CharacterInfo, preset: str) -> str:
        """Format using a predefined preset"""
        preset_config = self.PRESETS[preset]
        
        formatted_messages = []
        
        for message in request.messages:
            if not message.content.strip():
                continue
                
            # Get both role and name for template substitution
            literal_role = self._get_literal_role(message.role)
            character_name = self._get_character_name(message.role, character_info)
            
            # Apply pattern (presets use {role} for literal roles)
            formatted_message = preset_config['pattern'].format(
                role=literal_role,
                name=character_name,
                content=message.content.strip()
            )
            
            formatted_messages.append(formatted_message)
        
        # Join with separator
        result = preset_config['separator'].join(formatted_messages)
        
        return result
    
    def _format_custom(self, request: ChatRequest, character_info: CharacterInfo) -> str:
        """Format using custom templates"""
        
        # Get custom templates
        user_template = self._get_config_value('formatting.user_template', '{name}: {content}')
        char_template = self._get_config_value('formatting.char_template', '{name}: {content}')
        
        formatted_messages = []
        
        for message in request.messages:
            if not message.content.strip():
                continue
                
            # Choose template based on role
            if message.role == MessageRole.USER:
                template = user_template
            elif message.role == MessageRole.ASSISTANT:
                template = char_template
            elif message.role == MessageRole.SYSTEM:
                # System messages use character template
                template = char_template
            else:
                # Fallback
                template = '{name}: {content}'
            
            # Get both role and name for template substitution
            literal_role = self._get_literal_role(message.role)
            character_name = self._get_character_name(message.role, character_info)
            
            # Apply template (supports both {role} and {name})
            formatted_message = template.format(
                role=literal_role,
                name=character_name,
                content=message.content.strip()
            )
            
            formatted_messages.append(formatted_message)
        
        return '\n\n'.join(formatted_messages)
    
    def _get_literal_role(self, role: MessageRole) -> str:
        """Get the literal role name (user, assistant, system)"""
        return role.value.lower()
    
    def _get_character_name(self, role: MessageRole, character_info: CharacterInfo) -> str:
        """Get the character name for a role"""
        if role == MessageRole.USER:
            return character_info.user_name or 'User'
        elif role == MessageRole.ASSISTANT:
            return character_info.character_name or 'Assistant'
        elif role == MessageRole.SYSTEM:
            return 'System'
        else:
            return role.value
    
    def _get_role_name(self, role: MessageRole, character_info: CharacterInfo) -> str:
        """Get the display name for a role (backward compatibility)"""
        return self._get_character_name(role, character_info)
    
    @staticmethod
    def extract_final_user_prompt(request: ChatRequest) -> str:
        """Extract the final user prompt for display"""
        user_messages = request.get_user_messages()
        if user_messages:
            return user_messages[-1].content
        return ""