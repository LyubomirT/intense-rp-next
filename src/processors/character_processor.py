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
        
        # Extract user names from individual messages (STMP-style)
        self._extract_user_names_from_messages(request, character_info)
        
        # Override with API parameters if provided (highest priority)
        if request.api_char_name is not None:
            character_info.character_name = request.api_char_name
        if request.api_user_name is not None:
            character_info.user_name = request.api_user_name
            character_info.add_user_name(request.api_user_name)
        
        # Process the combined content (like original logic)
        processed_content = self._process_combined_content(combined_content, character_info, request)
        
        # Store character info on request for later use
        request._character_info = character_info
        
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
        """Combine messages like the original code did with STMP-style"""
        formatted_messages = []
        for msg in request.messages:
            # Use the actual user name if available (STMP-style)
            if msg.role == MessageRole.USER and msg.has_user_name():
                role_display = msg.get_user_name()
            else:
                role_display = msg.get_display_role()
            formatted_messages.append(f"{role_display}: {msg.content}")
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
            character_info.add_user_name(user_match.group(1))
            
        return character_info
    
    def _extract_user_names_from_messages(self, request: ChatRequest, character_info: CharacterInfo) -> None:
        """Extract user names from individual messages (STMP-style)"""
        for message in request.messages:
            if message.role == MessageRole.USER and message.has_user_name():
                character_info.add_user_name(message.get_user_name())
    
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
            # If no explicit character info, preserve custom roles and just remove system role prefix
            # but preserve user/assistant content as-is to avoid corrupting character names
            content = re.sub(r'(^|\n\n)system:\s*', r'\1', content)
            
            # For custom roles, preserve the role name as-is when no explicit character info
            # This allows custom roles like "Narrator:" to remain unchanged
        
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
        "Classic (Role)": {
            "pattern": "{role}: {content}",
            "separator": "\n\n",
            "description": "Traditional role-based formatting (user/assistant/system)"
        },
        "Classic (Name)": {
            "pattern": "{name}: {content}",
            "separator": "\n\n",
            "description": "Traditional name-based formatting (character names)"
        },
        "Wrapped (Role)": {
            "pattern": "<{role}>\n{content}\n</{role}>",
            "separator": "\n\n",
            "description": "XML-style wrapped formatting with roles"
        },
        "Wrapped (Name)": {
            "pattern": "<{name}>\n{content}\n</{name}>",
            "separator": "\n\n",
            "description": "XML-style wrapped formatting with names"
        },
        "Divided (Role)": {
            "pattern": "----------- {role} -----------\n{content}",
            "separator": "\n----------- ----------- -----------\n",
            "description": "Divided formatting with visual separators and roles"
        },
        "Divided (Name)": {
            "pattern": "----------- {name} -----------\n{content}",
            "separator": "\n----------- ----------- -----------\n",
            "description": "Divided formatting with visual separators and names"
        }
    }
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
    
    def format_for_api(self, request: ChatRequest, character_info: CharacterInfo = None) -> str:
        """Format messages for API consumption with configurable prompt injection"""
        
        # Extract character info if not provided
        if character_info is None:
            character_info = CharacterInfo()
        
        # Get the message content
        content = ""
        if hasattr(request, '_processed_content'):
            content = request._processed_content
        else:
            # Fallback to individual message processing
            formatted_messages = []
            
            for message in request.messages:
                if message.content.strip():  # Only include non-empty messages
                    # Use user name if available (STMP-style), otherwise fall back to display role
                    if message.role == MessageRole.USER and message.has_user_name():
                        role_display = message.get_user_name()
                    else:
                        role_display = message.get_display_role()
                    formatted_messages.append(f"{role_display}: {message.content}")
            
            content = "\n\n".join(formatted_messages).strip()
        
        # Handle prompt injection based on configuration
        injection_enabled = self._get_config_value('injection.enabled', True)
        
        if not injection_enabled:
            # No prompt injection - return content directly
            return content
        
        # Get custom system prompt template
        system_prompt_template = self._get_config_value('injection.system_prompt', '[Important Information]')
        
        # Apply placeholder substitutions
        system_prompt = self._apply_injection_placeholders(system_prompt_template, character_info, request)
        
        # Return formatted content with system prompt
        if system_prompt.strip():
            return f"{system_prompt}\n{content}"
        else:
            return content
    
    def _apply_injection_placeholders(self, template: str, character_info: CharacterInfo, request: ChatRequest) -> str:
        """Apply placeholder substitutions to system prompt template"""
        if not template:
            return template
        
        # Replace {username} with user name
        username = character_info.user_name or "User"
        template = template.replace("{username}", username)
        
        # Replace {asstname} with character/assistant name
        asstname = character_info.character_name or "Assistant"
        template = template.replace("{asstname}", asstname)
        
        return template
    
    def format_messages(self, request: ChatRequest, character_info: CharacterInfo) -> str:
        """Format messages based on current configuration"""
        
        # Get formatting configuration
        preset = self._get_config_value('formatting.preset', 'Classic (Name)')
        
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
            literal_role = self._get_literal_role(message)
            character_name = self._get_character_name(message, character_info)
            
            # Apply pattern (presets use {role} for literal roles)
            formatted_message = preset_config['pattern'].format(
                role=literal_role,
                name=character_name,
                content=message.content.strip()
            )
            
            formatted_messages.append(formatted_message)
        
        # If we have prefix content, add it as a fake assistant message
        if request.has_prefix():
            # Create a fake assistant message for the prefix
            from models.message_models import Message, MessageRole
            fake_assistant_msg = Message(role=MessageRole.ASSISTANT, content=request.prefix_content, original_role="assistant")
            
            # Get both role and name for template substitution
            literal_role = self._get_literal_role(fake_assistant_msg)
            character_name = character_info.character_name
            
            # Apply pattern (presets use {role} for literal roles)
            formatted_prefix = preset_config['pattern'].format(
                role=literal_role,
                name=character_name,
                content=request.prefix_content.strip()
            )
            
            formatted_messages.append(formatted_prefix)
        
        # Join with separator
        result = preset_config['separator'].join(formatted_messages)
        
        return result
    
    def _format_custom(self, request: ChatRequest, character_info: CharacterInfo) -> str:
        """Format using custom templates"""
        
        # Get custom templates from hidden variables
        user_template = self.config_manager.get_hidden_var('custom_user_template', '{name}: {content}')
        char_template = self.config_manager.get_hidden_var('custom_char_template', '{name}: {content}')
        
        formatted_messages = []
        
        for message in request.messages:
            if not message.content.strip():
                continue
                
            # Choose template based on role
            if message.is_custom_role():
                # Custom roles use their original name as the template
                template = '{name}: {content}'
            elif message.role == MessageRole.USER:
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
            literal_role = self._get_literal_role(message)
            character_name = self._get_character_name(message, character_info)
            
            # Apply template (supports both {role} and {name})
            formatted_message = template.format(
                role=literal_role,
                name=character_name,
                content=message.content.strip()
            )
            
            formatted_messages.append(formatted_message)
        
        # If we have prefix content, add it as a fake assistant message
        if request.has_prefix():
            # Create a fake assistant message for the prefix
            from models.message_models import Message, MessageRole
            fake_assistant_msg = Message(role=MessageRole.ASSISTANT, content=request.prefix_content, original_role="assistant")
            
            # Use assistant template for the prefix
            template = char_template
            
            # Get both role and name for template substitution
            literal_role = self._get_literal_role(fake_assistant_msg)
            character_name = character_info.character_name
            
            # Apply template (supports both {role} and {name})
            formatted_prefix = template.format(
                role=literal_role,
                name=character_name,
                content=request.prefix_content.strip()
            )
            
            formatted_messages.append(formatted_prefix)
        
        return '\n\n'.join(formatted_messages)
    
    def _get_literal_role(self, message) -> str:
        """Get the literal role name (supports custom roles)"""
        if message.is_custom_role():
            return message.original_role
        return message.role.value.lower()
    
    def _get_character_name(self, message, character_info: CharacterInfo) -> str:
        """Get the character name for a message (supports custom roles and STMP-style multiple users)"""
        if message.is_custom_role():
            # For custom roles, use the original role name
            return message.original_role
        elif message.role == MessageRole.USER:
            # STMP-style: Use message name if available, otherwise fallback to character_info
            if message.has_user_name():
                return message.get_user_name()
            return character_info.user_name or 'User'
        elif message.role == MessageRole.ASSISTANT:
            # Use message character name if available, otherwise fallback to character_info
            if message.has_character_name():
                return message.get_character_name()
            return character_info.character_name or 'Assistant'
        elif message.role == MessageRole.SYSTEM:
            return 'System'
        else:
            return message.role.value
    
    def _get_role_name(self, message, character_info: CharacterInfo) -> str:
        """Get the display name for a role (backward compatibility)"""
        return self._get_character_name(message, character_info)
    
    @staticmethod
    def extract_final_user_prompt(request: ChatRequest) -> str:
        """Extract the final user prompt for display"""
        user_messages = request.get_user_messages()
        if user_messages:
            return user_messages[-1].content
        return ""