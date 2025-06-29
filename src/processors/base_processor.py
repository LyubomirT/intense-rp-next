from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from models.message_models import ChatRequest, ProcessedMessage


class ProcessingError(Exception):
    """Base exception for processing errors"""
    pass


class BaseProcessor(ABC):
    """Abstract base class for message processors"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    @abstractmethod
    def process(self, request: ChatRequest) -> ChatRequest:
        """Process the chat request and return modified version"""
        pass
    
    @abstractmethod
    def can_process(self, request: ChatRequest) -> bool:
        """Check if this processor can handle the request"""
        pass
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value with dotted notation"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value


class ProcessorPipeline:
    """Manages a pipeline of processors"""
    
    def __init__(self, processors: Optional[List[BaseProcessor]] = None):
        self.processors = processors or []
    
    def add_processor(self, processor: BaseProcessor) -> None:
        """Add a processor to the pipeline"""
        self.processors.append(processor)
    
    def remove_processor(self, processor_type: type) -> None:
        """Remove a processor by type"""
        self.processors = [p for p in self.processors if not isinstance(p, processor_type)]
    
    def process(self, request: ChatRequest) -> ChatRequest:
        """Process request through the entire pipeline"""
        current_request = request
        
        for processor in self.processors:
            try:
                if processor.can_process(current_request):
                    current_request = processor.process(current_request)
            except Exception as e:
                raise ProcessingError(f"Error in {processor.__class__.__name__}: {e}") from e
        
        return current_request
    
    def get_active_processors(self, request: ChatRequest) -> List[BaseProcessor]:
        """Get list of processors that can handle this request"""
        return [p for p in self.processors if p.can_process(request)]