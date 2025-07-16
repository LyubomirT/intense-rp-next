from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum
import re


class MessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    role: MessageRole
    content: str
    original_role: str = None  # Preserve original role string for custom roles
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        role_str = data.get('role', 'user').lower()
        original_role = data.get('role', 'user')  # Store original case-preserved role
        role = MessageRole(role_str) if role_str in [r.value for r in MessageRole] else MessageRole.USER
        return cls(role=role, content=data.get('content', ''), original_role=original_role)
    
    def is_custom_role(self) -> bool:
        """Check if this message has a custom role (not standard user/assistant/system)"""
        return self.original_role.lower() not in ['user', 'assistant', 'system']
    
    def get_display_role(self) -> str:
        """Get the role name to display (original for custom roles, enum value for standard roles)"""
        if self.is_custom_role():
            return self.original_role
        return self.role.value


@dataclass
class ChatRequest:
    messages: List[Message]
    temperature: float = 1.0
    max_tokens: int = 300
    stream: bool = False
    
    # DeepSeek specific settings
    use_deepthink: bool = False
    use_search: bool = False
    use_text_file: bool = False
    
    # API parameters for character info and settings
    api_char_name: Optional[str] = None  # DATA1
    api_user_name: Optional[str] = None  # DATA2
    api_use_search: Optional[bool] = None  # use_search
    api_use_r1: Optional[bool] = None  # use_r1
    
    # Prefix support for assistant prefill
    prefix_content: Optional[str] = None  # Assistant message content to prefill
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatRequest':
        messages = [Message.from_dict(msg) for msg in data.get('messages', [])]
        
        # Detect prefix content (assistant message with content)
        prefix_content = None
        conversation_messages = messages
        
        if messages and messages[-1].role == MessageRole.ASSISTANT and messages[-1].content.strip():
            # Last message is an assistant message with content - use as prefix
            prefix_content = messages[-1].content
            # Remove the assistant message from conversation messages
            conversation_messages = messages[:-1]
        
        return cls(
            messages=conversation_messages,
            temperature=data.get('temperature', 1.0),
            max_tokens=data.get('max_tokens', 300),
            stream=data.get('stream', False),
            # Extract API parameters with priority over content detection
            api_char_name=data.get('char_name') or data.get('DATA1'),
            api_user_name=data.get('user_name') or data.get('DATA2'),
            api_use_search=data.get('use_search'),
            api_use_r1=data.get('use_r1'),
            prefix_content=prefix_content
        )
    
    def get_user_messages(self) -> List[Message]:
        return [msg for msg in self.messages if msg.role == MessageRole.USER]
    
    def get_system_messages(self) -> List[Message]:
        return [msg for msg in self.messages if msg.role == MessageRole.SYSTEM]
    
    def get_last_user_message(self) -> Optional[Message]:
        user_messages = self.get_user_messages()
        return user_messages[-1] if user_messages else None
    
    def has_prefix(self) -> bool:
        """Check if the request has prefix content for assistant prefill"""
        return self.prefix_content is not None and self.prefix_content.strip() != ""


@dataclass
class CharacterInfo:
    character_name: str = "Character"
    user_name: str = "User"
    formatted_content: str = ""
    
    def extract_names_from_content(self, content: str) -> None:
        """Extract character and user names from content"""
        character_match = re.search(r'DATA1:\s*"([^"]*)"', content)
        user_match = re.search(r'DATA2:\s*"([^"]*)"', content)
        
        if character_match:
            self.character_name = character_match.group(1)
        if user_match:
            self.user_name = user_match.group(1)


@dataclass
class ProcessedMessage:
    """Result of message processing"""
    content: str
    character_info: CharacterInfo
    settings: Dict[str, Any]
    
    def __str__(self) -> str:
        return self.content


@dataclass
class ChatResponse:
    content: str
    model: str
    finish_reason: str = "stop"
    
    def to_dict(self, streaming: bool = False) -> Dict[str, Any]:
        if streaming:
            return {
                "id": "chatcmpl-intenserp",
                "object": "chat.completion.chunk",
                "model": self.model,
                "choices": [{
                    "index": 0,
                    "delta": {"content": self.content}
                }]
            }
        else:
            return {
                "id": "chatcmpl-intenserp",
                "object": "chat.completion",
                "model": self.model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": self.content
                    },
                    "finish_reason": self.finish_reason
                }]
            }


@dataclass
class DeepSeekSettings:
    """DeepSeek-specific processing settings"""
    deepthink: bool = False
    search: bool = False
    text_file: bool = False
    
    @classmethod
    def detect_from_messages(cls, messages: List[Message]) -> 'DeepSeekSettings':
        """Auto-detect settings from message content"""
        settings = cls()
        
        # Check all user messages for directives
        for message in messages:
            if message.role == MessageRole.USER:
                content = message.content
                
                # Check for deepthink markers
                if re.search(r'({{r1}}|\[r1\]|\(r1\))', content, re.IGNORECASE):
                    settings.deepthink = True
                
                # Check for search markers
                if re.search(r'({{search}}|\[search\])', content, re.IGNORECASE):
                    settings.search = True
        
        return settings
    
    @staticmethod
    def clean_directives_from_content(content: str) -> str:
        """Remove DeepSeek directives from message content"""
        # Remove deepthink markers
        content = re.sub(r'{{r1}}\s*', '', content, flags=re.IGNORECASE)
        content = re.sub(r'\[r1\]\s*', '', content, flags=re.IGNORECASE)
        content = re.sub(r'\(r1\)\s*', '', content, flags=re.IGNORECASE)
        
        # Remove search markers
        content = re.sub(r'{{search}}\s*', '', content, flags=re.IGNORECASE)
        content = re.sub(r'\[search\]\s*', '', content, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        content = re.sub(r'\n\s*\n', '\n\n', content)  # Remove empty lines with only whitespace
        content = content.strip()
        
        return content