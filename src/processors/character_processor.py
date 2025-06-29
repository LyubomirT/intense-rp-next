import re
from typing import Dict, Any
from processors.base_processor import BaseProcessor
from models.message_models import ChatRequest, CharacterInfo, MessageRole


class CharacterProcessor(BaseProcessor):
    """Processes character-specific data and formatting"""
    
    def can_process(self, request: ChatRequest) -> bool:
        """Always can process character data"""
        return True
    
    def process(self, request: ChatRequest) -> ChatRequest:
        """Process character information and format messages"""
        
        # Clean up duplicate system messages
        self._cleanup_duplicate_system_messages(request)
        
        # Extract character info
        character_info = self._extract_character_info(request)
        
        # Format messages with character names
        self._format_messages_with_names(request, character_info)
        
        # Clean up content
        self._cleanup_content(request)
        
        # Replace template variables
        self._replace_template_variables(request)
        
        return request
    
    def _cleanup_duplicate_system_messages(self, request: ChatRequest) -> None:
        """Remove duplicate consecutive system messages"""
        messages = request.messages
        
        if (len(messages) >= 2 and 
            messages[-1].role == MessageRole.SYSTEM and 
            messages[-2].role == MessageRole.SYSTEM):
            messages.pop(-2)
    
    def _extract_character_info(self, request: ChatRequest) -> CharacterInfo:
        """Extract character and user names from messages"""
        character_info = CharacterInfo()
        
        # Combine all message content to search for names
        all_content = "\n\n".join([
            f"{msg.role.value}: {msg.content}" for msg in request.messages
        ])
        
        character_info.extract_names_from_content(all_content)
        return character_info
    
    def _format_messages_with_names(self, request: ChatRequest, character_info: CharacterInfo) -> None:
        """Replace generic role names with character names"""
        for message in request.messages:
            # Replace system prefix
            if message.content.startswith("system: "):
                message.content = message.content.replace("system: ", "", 1)
            
            # Replace role names in content
            message.content = message.content.replace("assistant:", f"{character_info.character_name}:")
            message.content = message.content.replace("user:", f"{character_info.user_name}:")
    
    def _cleanup_content(self, request: ChatRequest) -> None:
        """Remove unwanted markers and clean up formatting"""
        cleanup_patterns = [
            (r"({{r1}}|\[r1\]|\(r1\))", ""),  # Remove r1 markers
            (r"({{search}}|\[search\])", ""),  # Remove search markers
            (r'DATA1:\s*"[^"]*"', ""),        # Remove DATA1 definitions
            (r'DATA2:\s*"[^"]*"', ""),        # Remove DATA2 definitions
            (r"\n{3,}", "\n\n"),              # Reduce multiple newlines
        ]
        
        for message in request.messages:
            content = message.content
            
            for pattern, replacement in cleanup_patterns:
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
            
            message.content = content.strip()
    
    def _replace_template_variables(self, request: ChatRequest) -> None:
        """Replace template variables with actual values"""
        replacements = {
            "{{temperature}}": str(request.temperature),
            "{{max_tokens}}": str(request.max_tokens),
        }
        
        for message in request.messages:
            content = message.content
            
            for template, value in replacements.items():
                content = content.replace(template, value)
            
            message.content = content


class MessageFormatter:
    """Utility class for formatting messages"""
    
    @staticmethod
    def format_for_api(request: ChatRequest) -> str:
        """Format messages for API consumption"""
        formatted_messages = []
        
        for message in request.messages:
            if message.content.strip():  # Only include non-empty messages
                formatted_messages.append(f"{message.role.value}: {message.content}")
        
        content = "\n\n".join(formatted_messages)
        return f"[Important Information]\n{content.strip()}"
    
    @staticmethod
    def extract_final_user_prompt(request: ChatRequest) -> str:
        """Extract the final user prompt for display"""
        user_messages = request.get_user_messages()
        if user_messages:
            return user_messages[-1].content
        return ""