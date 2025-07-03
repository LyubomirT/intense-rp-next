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
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        role_str = data.get('role', 'user').lower()
        role = MessageRole(role_str) if role_str in [r.value for r in MessageRole] else MessageRole.USER
        return cls(role=role, content=data.get('content', ''))


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
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatRequest':
        messages = [Message.from_dict(msg) for msg in data.get('messages', [])]
        
        return cls(
            messages=messages,
            temperature=data.get('temperature', 1.0),
            max_tokens=data.get('max_tokens', 300),
            stream=data.get('stream', False),
            # Extract API parameters with priority over content detection
            api_char_name=data.get('char_name') or data.get('DATA1'),
            api_user_name=data.get('user_name') or data.get('DATA2'),
            api_use_search=data.get('use_search'),
            api_use_r1=data.get('use_r1')
        )
    
    def get_user_messages(self) -> List[Message]:
        return [msg for msg in self.messages if msg.role == MessageRole.USER]
    
    def get_system_messages(self) -> List[Message]:
        return [msg for msg in self.messages if msg.role == MessageRole.SYSTEM]
    
    def get_last_user_message(self) -> Optional[Message]:
        user_messages = self.get_user_messages()
        return user_messages[-1] if user_messages else None


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
        
        # Check the second-to-last message if it's from user
        if len(messages) >= 2 and messages[-2].role == MessageRole.USER:
            content = messages[-2].content
            
            # Check for deepthink markers
            if re.search(r'({{r1}}|\[r1\]|\(r1\))', content, re.IGNORECASE):
                settings.deepthink = True
            
            # Check for search markers
            if re.search(r'({{search}}|\[search\])', content, re.IGNORECASE):
                settings.search = True
        
        return settings