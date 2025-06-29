from typing import Dict, Any, Optional
from processors.base_processor import ProcessorPipeline, ProcessingError
from processors.character_processor import CharacterProcessor, MessageFormatter
from processors.deepseek_processor import DeepSeekProcessor
from processors.content_processor import ContentProcessor
from models.message_models import ChatRequest, ChatResponse, DeepSeekSettings


class MessagePipeline:
    """Main pipeline for processing chat messages"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.pipeline = ProcessorPipeline()
        self.content_processor = ContentProcessor()
        self._setup_pipeline()
    
    def _setup_pipeline(self):
        """Setup the processing pipeline with default processors"""
        # Add processors in order
        self.pipeline.add_processor(DeepSeekProcessor(self.config))
        self.pipeline.add_processor(CharacterProcessor(self.config))
    
    def process_request(self, request_data: Dict[str, Any]) -> ChatRequest:
        """Process incoming request data into a ChatRequest"""
        try:
            # Create ChatRequest from raw data
            request = ChatRequest.from_dict(request_data)
            
            # Process through pipeline
            processed_request = self.pipeline.process(request)
            
            return processed_request
            
        except Exception as e:
            raise ProcessingError(f"Failed to process request: {e}") from e
    
    def format_for_api(self, request: ChatRequest) -> str:
        """Format processed request for API consumption"""
        return MessageFormatter.format_for_api(request)
    
    def process_response_content(self, html_content: str) -> str:
        """Process HTML response content to clean markdown"""
        return self.content_processor.process_html_to_markdown(html_content)
    
    def get_closing_symbol(self, text: str) -> str:
        """Get closing symbol for text if needed"""
        return self.content_processor.get_closing_symbol(text)
    
    def create_response(self, content: str, model: str, streaming: bool = False) -> ChatResponse:
        """Create a properly formatted response"""
        return ChatResponse(content=content, model=model)
    
    def update_config(self, new_config: Dict[str, Any]):
        """Update pipeline configuration"""
        self.config.update(new_config)
        
        # Recreate pipeline with new config
        self.pipeline = ProcessorPipeline()
        self._setup_pipeline()
    
    def get_pipeline_info(self) -> Dict[str, Any]:
        """Get information about the current pipeline"""
        return {
            'processor_count': len(self.pipeline.processors),
            'processor_types': [p.__class__.__name__ for p in self.pipeline.processors],
            'config_keys': list(self.config.keys())
        }


class PipelineFactory:
    """Factory for creating configured message pipelines"""
    
    @staticmethod
    def create_default_pipeline(config: Optional[Dict[str, Any]] = None) -> MessagePipeline:
        """Create a pipeline with default processors"""
        return MessagePipeline(config)
    
    @staticmethod
    def create_custom_pipeline(
        config: Optional[Dict[str, Any]] = None,
        processor_types: Optional[list] = None
    ) -> MessagePipeline:
        """Create a pipeline with custom processors"""
        pipeline = MessagePipeline(config)
        
        if processor_types:
            # Clear default processors
            pipeline.pipeline.processors.clear()
            
            # Add custom processors
            for processor_type in processor_types:
                if hasattr(processor_type, '__init__'):
                    processor = processor_type(config)
                    pipeline.pipeline.add_processor(processor)
        
        return pipeline


# Utility functions for backward compatibility
def process_character_data(data: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Legacy function for processing character data - maintains backward compatibility"""
    try:
        pipeline = MessagePipeline(config)
        request = pipeline.process_request(data)
        return pipeline.format_for_api(request)
    except Exception as e:
        print(f"Error processing character data: {e}")
        return None


def get_streaming_setting(data: Dict[str, Any]) -> bool:
    """Get streaming setting from request data"""
    return bool(data.get("stream", False))


def get_deepseek_settings(data: Dict[str, Any]) -> Dict[str, bool]:
    """Get DeepSeek settings from request data"""
    try:
        request = ChatRequest.from_dict(data)
        settings = DeepSeekSettings.detect_from_messages(request.messages)
        
        return {
            'deepthink': settings.deepthink,
            'search': settings.search
        }
    except Exception:
        return {'deepthink': False, 'search': False}