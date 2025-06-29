"""
Simplified response utilities that delegate to the new pipeline system.
This file maintains backward compatibility while using the new architecture.
"""

from flask import jsonify, Response
import time, json
from typing import Dict, Any, Optional
from pipeline.message_pipeline import MessagePipeline, process_character_data, get_streaming_setting, get_deepseek_settings

__version__ = "2.7.0"

# Global pipeline instance for backward compatibility
_pipeline_instance: Optional[MessagePipeline] = None

def get_pipeline(config: Optional[Dict[str, Any]] = None) -> MessagePipeline:
    """Get or create pipeline instance"""
    global _pipeline_instance
    
    if _pipeline_instance is None or config is not None:
        _pipeline_instance = MessagePipeline(config)
    
    return _pipeline_instance

# =============================================================================================================================
# Legacy Functions for Backward Compatibility
# =============================================================================================================================

def process_character(put_data: dict, config: Optional[Dict[str, Any]] = None) -> str | None:
    """
    Legacy character processing function that delegates to the new pipeline.
    Maintains backward compatibility.
    """
    return process_character_data(put_data, config)

def get_streaming(put_data: dict) -> bool:
    """Get streaming setting from request data"""
    return get_streaming_setting(put_data)

def get_deepseek_deepthink(put_data: dict) -> bool:
    """Get DeepSeek deepthink setting from request data"""
    settings = get_deepseek_settings(put_data)
    return settings.get('deepthink', False)

def get_deepseek_search(put_data: dict) -> bool:
    """Get DeepSeek search setting from request data"""
    settings = get_deepseek_settings(put_data)
    return settings.get('search', False)

# =============================================================================================================================
# Response Creation Functions
# =============================================================================================================================

def get_model() -> Response:
    """Get model information response"""
    global __version__
    return jsonify({
        "object": "list",
        "data": [{
            "id": f"rp-intense-{__version__}",
            "object": "model",
            "created": int(time.time() * 1000)
        }]
    })

def create_response_jsonify(text: str) -> Response:
    """Create JSON response"""
    global __version__
    return jsonify({
        "id": "chatcmpl-intenserp",
        "object": "chat.completion",
        "created": int(time.time() * 1000),
        "model": f"rp-intense-{__version__}",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": text},
            "finish_reason": "stop"
        }]
    })

def create_response_streaming(text: str) -> str:
    """Create streaming response chunk"""
    global __version__
    return "data: " + json.dumps({
        "id": "chatcmpl-intenserp",
        "object": "chat.completion.chunk",
        "created": int(time.time() * 1000),
        "model": f"rp-intense-{__version__}",
        "choices": [{"index": 0, "delta": {"content": text}}]
    }) + "\n\n"

def create_response(text: str, streaming: bool) -> Response:
    """Create appropriate response based on streaming setting"""
    if streaming:
        return Response(create_response_streaming(text), content_type="text/event-stream")
    return create_response_jsonify(text)

# =============================================================================================================================
# Content Processing Functions
# =============================================================================================================================

def process_html_content(html_content: str, config: Optional[Dict[str, Any]] = None) -> str:
    """Process HTML content to clean markdown using the pipeline"""
    pipeline = get_pipeline(config)
    return pipeline.process_response_content(html_content)

def get_closing_symbol(text: str, config: Optional[Dict[str, Any]] = None) -> str:
    """Get closing symbol for text if needed"""
    pipeline = get_pipeline(config)
    return pipeline.get_closing_symbol(text)

# =============================================================================================================================
# Utility Functions
# =============================================================================================================================

def update_pipeline_config(config: Dict[str, Any]) -> None:
    """Update the global pipeline configuration"""
    global _pipeline_instance
    if _pipeline_instance:
        _pipeline_instance.update_config(config)
    else:
        _pipeline_instance = MessagePipeline(config)

def get_pipeline_info() -> Dict[str, Any]:
    """Get information about the current pipeline"""
    pipeline = get_pipeline()
    return pipeline.get_pipeline_info()

def reset_pipeline() -> None:
    """Reset the global pipeline instance"""
    global _pipeline_instance
    _pipeline_instance = None