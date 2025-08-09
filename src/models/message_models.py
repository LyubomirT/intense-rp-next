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
    name: Optional[str] = None  # Optional name field for user identification (STMP-style)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        role_str = data.get('role', 'user').lower()
        original_role = data.get('role', 'user')  # Store original case-preserved role
        role = MessageRole(role_str) if role_str in [r.value for r in MessageRole] else MessageRole.USER
        name = data.get('name')  # Extract optional name field
        
        # Handle both string and multimodal content formats
        content = data.get('content', '')
        if isinstance(content, list):
            # Multimodal content - extract text parts and ignore images
            text_parts = []
            for block in content:
                if isinstance(block, dict) and block.get('type') == 'text':
                    text_parts.append(block.get('text', ''))
            content = ' '.join(text_parts)
        elif not isinstance(content, str):
            # Fallback for any other unexpected content format
            content = str(content)
            
        return cls(role=role, content=content, original_role=original_role, name=name)
    
    def is_custom_role(self) -> bool:
        """Check if this message has a custom role (not standard user/assistant/system)"""
        if self.original_role is None:
            return False
        return self.original_role.lower() not in ['user', 'assistant', 'system']
    
    def get_display_role(self) -> str:
        """Get the role name to display (original for custom roles, enum value for standard roles)"""
        if self.is_custom_role():
            return self.original_role
        return self.role.value
    
    def get_user_name(self) -> Optional[str]:
        """Get the user name from the message if available"""
        return self.name
    
    def has_user_name(self) -> bool:
        """Check if this message has a user name"""
        return self.name is not None and self.name.strip() != ""


@dataclass
class ChatRequest:
    messages: List[Message]
    temperature: float = 1.0
    max_tokens: int = 300
    stream: bool = False
    model: str = "intense-rp-next-1"  # Model name from request
    
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
            model=data.get('model', 'intense-rp-next-1'),
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
    
    def get_unique_user_names(self) -> List[str]:
        """Get all unique user names from messages (STMP-style multiple users)"""
        names = set()
        for msg in self.messages:
            if msg.role == MessageRole.USER and msg.has_user_name():
                names.add(msg.get_user_name())
        return sorted(list(names))
    
    def get_messages_by_user(self, user_name: str) -> List[Message]:
        """Get all messages from a specific user"""
        return [msg for msg in self.messages 
                if msg.role == MessageRole.USER and msg.get_user_name() == user_name]
    
    def has_multiple_users(self) -> bool:
        """Check if this conversation has multiple users (STMP-style)"""
        return len(self.get_unique_user_names()) > 1
    
    def has_model_suffix(self, suffix: str) -> bool:
        """Check if model name has a specific suffix"""
        return self.model.endswith(f"-{suffix}")
    
    def is_chat_model(self) -> bool:
        """Check if this is a -chat model (forces reasoning OFF)"""
        return self.has_model_suffix("chat")
    
    def is_reasoner_model(self) -> bool:
        """Check if this is a -reasoner model (forces reasoning ON)"""
        return self.has_model_suffix("reasoner")
    
    def get_base_model_name(self) -> str:
        """Get base model name without suffix"""
        if self.is_chat_model():
            return self.model[:-5]  # Remove "-chat"
        elif self.is_reasoner_model():
            return self.model[:-9]  # Remove "-reasoner"
        return self.model


@dataclass
class CharacterInfo:
    character_name: str = "Character"
    user_name: str = "User"  # Primary/fallback user name (for backward compatibility)
    formatted_content: str = ""
    user_names: List[str] = None  # All user names in conversation (STMP-style)
    
    def __post_init__(self):
        if self.user_names is None:
            self.user_names = []
    
    def extract_names_from_content(self, content: str) -> None:
        """Extract character and user names from content"""
        character_match = re.search(r'DATA1:\s*"([^"]*)"', content)
        user_match = re.search(r'DATA2:\s*"([^"]*)"', content)
        
        if character_match:
            self.character_name = character_match.group(1)
        if user_match:
            self.user_name = user_match.group(1)
            # Add to user_names list if not already present
            if self.user_name not in self.user_names:
                self.user_names.append(self.user_name)
    
    def add_user_name(self, name: str) -> None:
        """Add a user name to the list if not already present"""
        if name and name not in self.user_names:
            self.user_names.append(name)
    
    def get_primary_user_name(self) -> str:
        """Get the primary user name (first in list or fallback)"""
        return self.user_names[0] if self.user_names else self.user_name
    
    def has_multiple_users(self) -> bool:
        """Check if there are multiple users in this conversation"""
        return len(self.user_names) > 1


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