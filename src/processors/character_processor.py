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
        
        # Store the processed content back - we'll let the formatter handle this
        # For now, store in a special attribute
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
        
        # Replace role names (original logic)
        content = content.replace("system: ", "")
        content = content.replace("assistant:", f"{character_info.character_name}:")
        content = content.replace("user:", f"{character_info.user_name}:")
        
        # Replace template variables
        content = content.replace("{{temperature}}", str(request.temperature))
        content = content.replace("{{max_tokens}}", str(request.max_tokens))
        
        # Clean up extra newlines
        content = re.sub(r"\n{3,}", "\n\n", content)
        
        return content.strip()


class MessageFormatter:
    """Utility class for formatting messages"""
    
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
    
    @staticmethod
    def extract_final_user_prompt(request: ChatRequest) -> str:
        """Extract the final user prompt for display"""
        user_messages = request.get_user_messages()
        if user_messages:
            return user_messages[-1].content
        return ""