from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import utils.webdriver_utils as selenium
import utils.deepseek_driver as deepseek
import socket, time, threading, json
from typing import Generator
from waitress import serve
from core import get_state_manager, StateEvent
from pipeline.message_pipeline import MessagePipeline, ProcessingError
from functools import wraps

app = Flask(__name__)
# Enable CORS for all routes to allow extension communication
CORS(app, origins=["chrome-extension://*", "http://127.0.0.1:*", "http://localhost:*"])

# Global storage for network interception data
network_data = {
    'request_data': None,
    'response_started': False,
    'stream_buffer': [],
    'events': [],
    'completed': False,
    'error': None,
    'thinking_active': False,
    'thinking_buffer': "",
    'thinking_started': False
}

# =============================================================================================================================
# Authentication Functions
# =============================================================================================================================

def get_valid_api_keys():
    """Get list of valid API keys from configuration"""
    state = get_state_manager()
    api_keys_text = state.get_config_value("security.api_keys", "")
    
    if not api_keys_text or not api_keys_text.strip():
        return []
    
    # Parse API keys from textarea (one per line)
    lines = api_keys_text.strip().split('\n')
    valid_keys = []
    
    for line in lines:
        key = line.strip()
        if key and len(key) >= 16:  # Only include non-empty keys with minimum length
            valid_keys.append(key)
    
    return valid_keys

def is_api_auth_enabled():
    """Check if API authentication is enabled"""
    state = get_state_manager()
    return state.get_config_value("security.api_auth_enabled", False)

def validate_api_key(provided_key):
    """Validate provided API key against configured keys"""
    if not provided_key:
        return False
    
    valid_keys = get_valid_api_keys()
    return provided_key in valid_keys

def require_auth(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip authentication if not enabled
        if not is_api_auth_enabled():
            return f(*args, **kwargs)
        
        # Check for Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({
                "error": {
                    "message": "Missing Authorization header. Please provide Bearer token.",
                    "type": "authentication_error",
                    "code": "missing_authorization"
                }
            }), 401
        
        # Extract Bearer token
        if not auth_header.startswith('Bearer '):
            return jsonify({
                "error": {
                    "message": "Invalid Authorization header format. Use: Authorization: Bearer <your-api-key>",
                    "type": "authentication_error", 
                    "code": "invalid_authorization_format"
                }
            }), 401
        
        api_key = auth_header[7:]  # Remove "Bearer " prefix
        
        # Validate API key
        if not validate_api_key(api_key):
            return jsonify({
                "error": {
                    "message": "Invalid API key. Please check your Bearer token.",
                    "type": "authentication_error",
                    "code": "invalid_api_key"
                }
            }), 401
        
        # Authentication successful, proceed with original function
        return f(*args, **kwargs)
    
    return decorated_function

# =============================================================================================================================
# API Endpoints
# =============================================================================================================================

@app.route("/models", methods=["GET"])
@require_auth
def model() -> Response:
    state = get_state_manager()
    
    if not state.driver:
        return jsonify({}), 503

    state.show_message("\n[color:purple]API CONNECTION:")
    try:
        state.show_message("[color:white]- [color:green]Successful connection.")
        return get_model_response()
    except Exception as e:
        state.show_message("[color:white]- [color:red]Error connecting.")
        print(f"Error connecting to API: {e}")
        return jsonify({}), 500

@app.route("/chat/completions", methods=["POST"])
@require_auth
def bot_response() -> Response:
    state = get_state_manager()
    
    try:
        data = request.get_json()
        if not data:
            print("Error: Empty data was received.")
            return jsonify({}), 503

        # Initialize message pipeline with current config and config manager
        config_with_manager = state.config or {}
        config_with_manager['config_manager'] = state._config_manager
        pipeline = MessagePipeline(config_with_manager)
        
        # Process the request
        try:
            processed_request = pipeline.process_request(data)
            formatted_message = pipeline.format_for_api(processed_request)
        except ProcessingError as e:
            print(f"Error processing request: {e}")
            return jsonify({}), 503

        streaming = processed_request.stream

        if not formatted_message:
            print("Error: Data could not be processed.")
            return jsonify({}), 503
        if not state.driver:
            print("Error: Selenium is not active.")
            return jsonify({}), 503

        current_message = state.increment_response_id()

        state.show_message(f"\n[color:purple]GENERATING RESPONSE {current_message}:")
        state.show_message("[color:white]- [color:green]Character data has been received.")
        
        # Log prefix usage
        if processed_request.has_prefix():
            state.show_message(f"[color:white]- [color:cyan]Prefix detected: {len(processed_request.prefix_content)} characters")
        
        # Check if network interception is enabled
        intercept_network = state.get_config_value("models.deepseek.intercept_network", False)
        
        if intercept_network:
            # Get send_thoughts setting - only applies when deepthink is enabled
            send_thoughts = state.get_config_value("models.deepseek.send_thoughts", True) if processed_request.use_deepthink else False
            return deepseek_network_response(
                current_message, 
                formatted_message, 
                streaming, 
                processed_request.use_deepthink,
                processed_request.use_search,
                processed_request.use_text_file,
                pipeline,
                processed_request.prefix_content,
                send_thoughts
            )
        else:
            return deepseek_response(
                current_message, 
                formatted_message, 
                streaming, 
                processed_request.use_deepthink,
                processed_request.use_search,
                processed_request.use_text_file,
                pipeline,
                processed_request.prefix_content
            )
    except Exception as e:
        print(f"Error receiving JSON from Sillytavern: {e}")
        return jsonify({}), 500

def deepseek_response(
    current_id: int, 
    formatted_message: str, 
    streaming: bool, 
    deepthink: bool, 
    search: bool, 
    text_file: bool,
    pipeline: MessagePipeline,
    prefix_content: str = None
) -> Response:
    state = get_state_manager()

    def client_disconnected() -> bool:
        if not streaming:
            disconnect_checker = request.environ.get('waitress.client_disconnected')
            return disconnect_checker and disconnect_checker()
        return False
    
    def interrupted() -> bool:
        return current_id != state.last_response or state.driver is None or client_disconnected()

    def safe_interrupt_response() -> Response:
        deepseek.new_chat(state.driver)
        return create_response("", streaming, pipeline)

    try:
        if not selenium.current_page(state.driver, "https://chat.deepseek.com"):
            state.show_message("[color:white]- [color:red]You must be on the DeepSeek website.")
            return create_response("You must be on the DeepSeek website.", streaming, pipeline)

        if selenium.current_page(state.driver, "https://chat.deepseek.com/sign_in"):
            state.show_message("[color:white]- [color:red]You must be logged into DeepSeek.")
            return create_response("You must be logged into DeepSeek.", streaming, pipeline)

        if interrupted():
            return safe_interrupt_response()

        deepseek.configure_chat(state.driver, deepthink, search)
        state.show_message("[color:white]- [color:cyan]Chat reset and configured.")

        if interrupted():
            return safe_interrupt_response()

        if not deepseek.send_chat_message(state.driver, formatted_message, text_file, prefix_content):
            state.show_message("[color:white]- [color:red]Could not paste prompt.")
            return create_response("Could not paste prompt.", streaming, pipeline)

        state.show_message("[color:white]- [color:green]Prompt pasted and sent.")

        if interrupted():
            return safe_interrupt_response()

        if not deepseek.active_generate_response(state.driver):
            state.show_message("[color:white]- [color:red]No response generated.")
            return create_response("No response generated.", streaming, pipeline)

        if interrupted():
            return safe_interrupt_response()

        state.show_message("[color:white]- [color:cyan]Awaiting response.")
        last_sent_position = 0
        last_content_hash = None
        stable_content = None

        if streaming:
            def streaming_response() -> Generator[str, None, None]:
                nonlocal last_sent_position, last_content_hash, stable_content
                hybrid_mode = False  # Flag to track when we switch to hybrid mode
                
                try:
                    while deepseek.is_response_generating(state.driver):
                        if interrupted():
                            break

                        current_text = deepseek.get_last_message(state.driver, pipeline)
                        if not current_text:
                            time.sleep(0.2)
                            continue
                        
                        # Check for code blocks in raw HTML to determine if we should switch to hybrid mode
                        if not hybrid_mode:
                            raw_html = deepseek.get_last_message_raw_html(state.driver)
                            if raw_html and deepseek.has_code_block_in_html(raw_html):
                                hybrid_mode = True
                                state.show_message("[color:white]- [color:yellow]Code block detected, switching to hybrid mode...")
                        
                        # Generate hash to detect content changes vs processing artifacts
                        current_hash = deepseek._get_content_hash(current_text)
                        
                        # Handle content hash changes (real content updates)
                        if current_hash != last_content_hash:
                            last_content_hash = current_hash
                            stable_content = current_text
                            
                            # Only send incremental content if NOT in hybrid mode
                            if not hybrid_mode and len(current_text) > last_sent_position:
                                new_content = current_text[last_sent_position:]
                                last_sent_position = len(current_text)
                                yield create_response_streaming(new_content, pipeline)
                        
                        time.sleep(0.2)

                    if interrupted():
                        return safe_interrupt_response()

                    # Final processing - get the complete response
                    final_text = deepseek.wait_for_response_completion(state.driver, pipeline)
                    
                    if final_text:
                        # Send any remaining content based on position
                        if len(final_text) > last_sent_position:
                            final_content = final_text[last_sent_position:]
                            if final_content:
                                yield create_response_streaming(final_content, pipeline)
                    
                    # Send closing symbol if needed
                    closing = pipeline.get_closing_symbol(final_text) if final_text else ""
                    if closing:
                        yield create_response_streaming(closing, pipeline)
                    
                    state.show_message("[color:white]- [color:green]Completed.")
                except GeneratorExit:
                    deepseek.new_chat(state.driver)
                
                except Exception as e:
                    deepseek.new_chat(state.driver)
                    print(f"Streaming error: {e}")
                    state.show_message("[color:white]- [color:red]Unknown error occurred.")
                    yield create_response_streaming("Error receiving response.", pipeline)
            return Response(streaming_response(), content_type="text/event-stream")
        else:
            final_text = deepseek.wait_for_response_completion(state.driver, pipeline)
            
            if interrupted():
                return safe_interrupt_response()
            
            response_text = final_text if final_text else "Error receiving response."
            closing = pipeline.get_closing_symbol(final_text) if final_text else ""
            response = response_text + closing
            
            state.show_message("[color:white]- [color:green]Completed.")
            return create_response_jsonify(response, pipeline)
    
    except Exception as e:
        print(f"Error generating response: {e}")
        state.show_message("[color:white]- [color:red]Unknown error occurred.")
        return create_response("Error receiving response.", streaming, pipeline)

def deepseek_network_response(
    current_id: int, 
    formatted_message: str, 
    streaming: bool, 
    deepthink: bool, 
    search: bool, 
    text_file: bool,
    pipeline: MessagePipeline,
    prefix_content: str = None,
    send_thoughts: bool = True
) -> Response:
    """Handle DeepSeek response using network interception instead of DOM scraping"""
    state = get_state_manager()

    def client_disconnected() -> bool:
        if not streaming:
            disconnect_checker = request.environ.get('waitress.client_disconnected')
            return disconnect_checker and disconnect_checker()
        return False
    
    def interrupted() -> bool:
        return current_id != state.last_response or state.driver is None or client_disconnected()

    def safe_interrupt_response() -> Response:
        deepseek.new_chat(state.driver)
        deepseek.disable_network_interception(state.driver)
        return create_response("", streaming, pipeline)

    try:
        if not selenium.current_page(state.driver, "https://chat.deepseek.com"):
            state.show_message("[color:white]- [color:red]You must be on the DeepSeek website.")
            return create_response("You must be on the DeepSeek website.", streaming, pipeline)

        if selenium.current_page(state.driver, "https://chat.deepseek.com/sign_in"):
            state.show_message("[color:white]- [color:red]You must be logged into DeepSeek.")
            return create_response("You must be logged into DeepSeek.", streaming, pipeline)

        if interrupted():
            return safe_interrupt_response()

        # Reset network data for new request
        network_data['request_data'] = None
        network_data['response_started'] = False
        network_data['stream_buffer'] = []
        network_data['events'] = []
        network_data['completed'] = False
        network_data['error'] = None
        network_data['thinking_active'] = False
        network_data['thinking_buffer'] = ""
        network_data['thinking_started'] = False
        
        # Enable network interception
        deepseek.enable_network_interception(state.driver)
        state.show_message("[color:white]- [color:cyan]CDP network interception enabled.")

        # Configure chat and send message
        deepseek.configure_chat(state.driver, deepthink, search)
        state.show_message("[color:white]- [color:cyan]Chat reset and configured.")

        if interrupted():
            return safe_interrupt_response()

        if not deepseek.send_chat_message(state.driver, formatted_message, text_file, prefix_content):
            state.show_message("[color:white]- [color:red]Could not paste prompt.")
            deepseek.disable_network_interception(state.driver)
            return create_response("Could not paste prompt.", streaming, pipeline)

        state.show_message("[color:white]- [color:green]Prompt pasted and sent.")

        if interrupted():
            return safe_interrupt_response()

        # Wait for network data to be received
        state.show_message("[color:white]- [color:cyan]Waiting for network response...")
        
        if streaming:
            def network_streaming_response() -> Generator[str, None, None]:
                try:
                    # Wait for response to start
                    timeout = 30  # 30 second timeout
                    start_time = time.time()
                    
                    while not network_data['response_started']:
                        if interrupted() or time.time() - start_time > timeout:
                            break
                        time.sleep(0.1)
                    
                    if not network_data['response_started']:
                        yield create_response_streaming("Error: Network response did not start", pipeline)
                        return
                    
                    # Stream the data as it arrives
                    last_processed_index = 0
                    finish_event_received = False
                    timeout_start = time.time()
                    max_total_time = 300  # 5 minutes absolute timeout
                    
                    while not finish_event_received:
                        if interrupted() or time.time() - timeout_start > max_total_time:
                            break
                        
                        # Process new stream data
                        stream_buffer = network_data['stream_buffer']
                        current_buffer_length = len(stream_buffer)
                        
                        for i in range(last_processed_index, current_buffer_length):
                            item = stream_buffer[i]
                            if item['type'] == 'data':
                                content = item['content']
                                if content:
                                    # Parse streaming data with immediate forwarding
                                    chunks = parse_network_stream_data_for_streaming(content, send_thoughts)
                                    for chunk in chunks:
                                        if chunk:
                                            yield create_response_streaming(chunk, pipeline)
                        
                        last_processed_index = current_buffer_length
                        
                        # Check for finish event
                        events = network_data['events']
                        for event in events:
                            if event.get('event') == 'finish':
                                finish_event_received = True
                                break
                            
                        time.sleep(0.1)
                    
                    # If thinking mode is still active at stream end, close it (only if send_thoughts is enabled)
                    if network_data['thinking_active'] and send_thoughts:
                        yield create_response_streaming("\n</think>\n\n", pipeline)
                    # Reset thinking state regardless of send_thoughts setting
                    if network_data['thinking_active']:
                        network_data['thinking_active'] = False
                        network_data['thinking_started'] = False
                    
                    # Check for errors
                    if network_data['error']:
                        yield create_response_streaming(f"Error: {network_data['error']}", pipeline)
                    
                    state.show_message("[color:white]- [color:green]Network response completed.")
                    
                except GeneratorExit:
                    deepseek.disable_network_interception(state.driver)
                    deepseek.new_chat(state.driver)
                except Exception as e:
                    deepseek.disable_network_interception(state.driver)
                    deepseek.new_chat(state.driver)
                    print(f"Network streaming error: {e}")
                    state.show_message("[color:white]- [color:red]Network streaming error occurred.")
                    yield create_response_streaming("Error receiving network response.", pipeline)
                finally:
                    deepseek.disable_network_interception(state.driver)
                    
            return Response(network_streaming_response(), content_type="text/event-stream")
        else:
            # Non-streaming mode
            timeout = 300  # 5 minutes timeout to match streaming mode
            start_time = time.time()
            
            while not network_data['completed']:
                if interrupted() or time.time() - start_time > timeout:
                    break
                time.sleep(0.1)
            
            if network_data['error']:
                response_text = f"Error: {network_data['error']}"
            else:
                # Combine all stream data
                state.show_message(f"[color:cyan]Combining {len(network_data['stream_buffer'])} stream items...")
                response_text = combine_network_stream_data(network_data['stream_buffer'], send_thoughts)
                state.show_message(f"[color:cyan]Final combined response length: {len(response_text)}")
            
            deepseek.disable_network_interception(state.driver)
            state.show_message("[color:white]- [color:green]Network response completed.")
            return create_response_jsonify(response_text, pipeline)
    
    except Exception as e:
        print(f"Error in network response: {e}")
        state.show_message("[color:white]- [color:red]Network response error occurred.")
        deepseek.disable_network_interception(state.driver)
        return create_response("Error receiving network response.", streaming, pipeline)

def parse_network_stream_data_for_streaming(data: str, send_thoughts: bool = True) -> list:
    """Parse network stream data for streaming mode, returning list of chunks to send immediately"""
    try:
        chunks = []
        
        # Handle different types of data
        if data.startswith('{'):
            # JSON data
            import json
            json_data = json.loads(data)
            
            # Handle DeepSeek specific format
            if 'v' in json_data:
                path = json_data.get('p')
                content_value = json_data['v']
                
                # Handle thinking content start
                if path == 'response/thinking_content':
                    if send_thoughts:
                        if not network_data['thinking_active']:
                            # Starting thinking mode - send opening <think> tag
                            chunks.append("<think>\n")
                            network_data['thinking_active'] = True
                            network_data['thinking_started'] = True
                        
                        # Send thinking content immediately
                        if isinstance(content_value, str):
                            chunks.append(content_value)
                        elif isinstance(content_value, list):
                            for item in content_value:
                                if isinstance(item, dict) and 'v' in item:
                                    chunks.append(str(item['v']))
                    else:
                        # Track thinking state but don't send content
                        if not network_data['thinking_active']:
                            network_data['thinking_active'] = True
                            network_data['thinking_started'] = True
                
                # Handle regular content start - this ends thinking mode
                elif path == 'response/content':
                    # If we were in thinking mode, close it first (only if send_thoughts is enabled)
                    if network_data['thinking_active']:
                        if send_thoughts:
                            chunks.append("\n</think>\n\n")
                        # Reset thinking state
                        network_data['thinking_active'] = False
                        network_data['thinking_started'] = False
                    
                    # Send regular content immediately
                    if isinstance(content_value, str):
                        chunks.append(content_value)
                    elif isinstance(content_value, list):
                        for item in content_value:
                            if isinstance(item, dict) and 'v' in item and item.get('p') == 'response/content':
                                chunks.append(str(item['v']))
                
                # Handle continuation chunks (no path specified)
                elif path is None:
                    # If we're in thinking mode and send_thoughts is enabled, send thinking content
                    if network_data['thinking_active'] and send_thoughts:
                        if isinstance(content_value, str):
                            chunks.append(content_value)
                        elif isinstance(content_value, list):
                            for item in content_value:
                                if isinstance(item, dict) and 'v' in item:
                                    chunks.append(str(item['v']))
                    # Send content as regular content only if not in thinking mode
                    elif not network_data['thinking_active']:
                        if isinstance(content_value, str):
                            chunks.append(content_value)
                        elif isinstance(content_value, list):
                            for item in content_value:
                                if isinstance(item, dict) and 'v' in item:
                                    chunks.append(str(item['v']))
                    # If thinking mode is active but send_thoughts is disabled, ignore content completely
                
                # Handle batch operations
                elif path == 'response' and json_data.get('o') == 'BATCH':
                    if isinstance(content_value, list):
                        for item in content_value:
                            if isinstance(item, dict) and 'v' in item:
                                item_path = item.get('p')
                                if item_path == 'response/thinking_content':
                                    if send_thoughts:
                                        if not network_data['thinking_active']:
                                            chunks.append("<think>\n")
                                            network_data['thinking_active'] = True
                                            network_data['thinking_started'] = True
                                        chunks.append(str(item['v']))
                                    else:
                                        # Track thinking state but don't send content
                                        if not network_data['thinking_active']:
                                            network_data['thinking_active'] = True
                                            network_data['thinking_started'] = True
                                elif item_path == 'response/content':
                                    # If we were in thinking mode, close it first (only if send_thoughts is enabled)
                                    if network_data['thinking_active']:
                                        if send_thoughts:
                                            chunks.append("\n</think>\n\n")
                                        network_data['thinking_active'] = False
                                        network_data['thinking_started'] = False
                                    chunks.append(str(item['v']))
            
            # Handle simple content updates (fallback) - only if not in thinking mode
            elif 'v' in json_data and not network_data['thinking_active']:
                content = json_data['v']
                if isinstance(content, str):
                    chunks.append(content)
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and 'v' in item:
                            chunks.append(str(item['v']))
            
            # Handle complex response structure - only if not in thinking mode
            elif 'response' in json_data and 'content' in json_data['response'] and not network_data['thinking_active']:
                chunks.append(json_data['response']['content'])
        else:
            # Plain text data
            chunks.append(data)
        
        return chunks
    except Exception as e:
        print(f"Error parsing network stream data for streaming: {e}")
        return []

def parse_network_stream_data(data: str, send_thoughts: bool = True) -> str:
    """Parse network stream data to extract content, handling thinking content with <think> tags"""
    try:
        # Handle different types of data
        if data.startswith('{'):
            # JSON data
            import json
            json_data = json.loads(data)
            
            # Handle DeepSeek specific format
            if 'v' in json_data:
                path = json_data.get('p')
                content_value = json_data['v']
                
                # Handle thinking content start
                if path == 'response/thinking_content':
                    if send_thoughts:
                        if not network_data['thinking_active']:
                            # Starting thinking mode
                            network_data['thinking_active'] = True
                            network_data['thinking_buffer'] = ""
                            network_data['thinking_started'] = True
                        
                        # Accumulate thinking content
                        if isinstance(content_value, str):
                            network_data['thinking_buffer'] += content_value
                        elif isinstance(content_value, list):
                            for item in content_value:
                                if isinstance(item, dict) and 'v' in item:
                                    network_data['thinking_buffer'] += str(item['v'])
                    else:
                        # Track thinking state but don't accumulate content
                        if not network_data['thinking_active']:
                            network_data['thinking_active'] = True
                            network_data['thinking_started'] = True
                    
                    # Return empty string while accumulating/ignoring thinking content
                    return ""
                
                # Handle regular content start - this ends thinking mode
                elif path == 'response/content':
                    result = ""
                    
                    # If we were in thinking mode, wrap and flush the thinking buffer (only if send_thoughts is enabled)
                    if network_data['thinking_active']:
                        if send_thoughts:
                            thinking_content = network_data['thinking_buffer'].strip()
                            if thinking_content:
                                result = f"<think>\n{thinking_content}\n</think>\n\n"
                        
                        # Reset thinking state
                        network_data['thinking_active'] = False
                        network_data['thinking_buffer'] = ""
                        network_data['thinking_started'] = False
                    
                    # Add regular content
                    if isinstance(content_value, str):
                        result += content_value
                    elif isinstance(content_value, list):
                        for item in content_value:
                            if isinstance(item, dict) and 'v' in item and item.get('p') == 'response/content':
                                result += str(item['v'])
                    
                    return result
                
                # Handle continuation chunks (no path specified)
                elif path is None:
                    # If we're in thinking mode, accumulate this content as thinking (only if send_thoughts is enabled)
                    if network_data['thinking_active']:
                        if send_thoughts:
                            if isinstance(content_value, str):
                                network_data['thinking_buffer'] += content_value
                            elif isinstance(content_value, list):
                                for item in content_value:
                                    if isinstance(item, dict) and 'v' in item:
                                        network_data['thinking_buffer'] += str(item['v'])
                        # Return empty while accumulating/ignoring thinking content
                        return ""
                    else:
                        # Not in thinking mode, treat as regular content
                        if isinstance(content_value, str):
                            return content_value
                        elif isinstance(content_value, list):
                            result = ""
                            for item in content_value:
                                if isinstance(item, dict) and 'v' in item:
                                    result += str(item['v'])
                            return result
                
                # Handle batch operations
                elif path == 'response' and json_data.get('o') == 'BATCH':
                    if isinstance(content_value, list):
                        result = ""
                        thinking_content_found = False
                        regular_content_found = False
                        
                        # Check for thinking content in batch
                        for item in content_value:
                            if isinstance(item, dict) and 'v' in item:
                                item_path = item.get('p')
                                if item_path == 'response/thinking_content':
                                    thinking_content_found = True
                                    if send_thoughts:
                                        if not network_data['thinking_active']:
                                            network_data['thinking_active'] = True
                                            network_data['thinking_buffer'] = ""
                                            network_data['thinking_started'] = True
                                        network_data['thinking_buffer'] += str(item['v'])
                                    else:
                                        # Track thinking state but don't accumulate content
                                        if not network_data['thinking_active']:
                                            network_data['thinking_active'] = True
                                            network_data['thinking_started'] = True
                                elif item_path == 'response/content':
                                    regular_content_found = True
                                    # If we were in thinking mode, flush it first (only if send_thoughts is enabled)
                                    if network_data['thinking_active']:
                                        if send_thoughts:
                                            thinking_content = network_data['thinking_buffer'].strip()
                                            if thinking_content:
                                                result += f"<think>\n{thinking_content}\n</think>\n\n"
                                        
                                        # Reset thinking state
                                        network_data['thinking_active'] = False
                                        network_data['thinking_buffer'] = ""
                                        network_data['thinking_started'] = False
                                    
                                    result += str(item['v'])
                        
                        return result
            
            # Handle simple content updates (fallback)
            elif 'v' in json_data:
                content = json_data['v']
                if isinstance(content, str):
                    return content
                elif isinstance(content, list):
                    result = ""
                    for item in content:
                        if isinstance(item, dict) and 'v' in item:
                            result += str(item['v'])
                    return result
            
            # Handle complex response structure
            elif 'response' in json_data and 'content' in json_data['response']:
                return json_data['response']['content']
            
            return ""
        else:
            # Plain text data
            return data
    except Exception as e:
        print(f"Error parsing network stream data: {e}")
        return ""

def combine_network_stream_data(stream_buffer: list, send_thoughts: bool = True) -> str:
    """Combine all network stream data into a single response"""
    try:
        result = ""
        for item in stream_buffer:
            if item['type'] == 'data':
                content = parse_network_stream_data(item['content'], send_thoughts)
                if content:
                    result += content
        
        # Check if there's any remaining thinking content to flush (only if send_thoughts is enabled)
        if send_thoughts and network_data['thinking_active'] and network_data['thinking_buffer'].strip():
            thinking_content = network_data['thinking_buffer'].strip()
            result += f"<think>\n{thinking_content}\n</think>\n\n"
            
            # Reset thinking state
            network_data['thinking_active'] = False
            network_data['thinking_buffer'] = ""
            network_data['thinking_started'] = False
        
        return result
    except Exception as e:
        print(f"Error combining network stream data: {e}")
        return "Error processing network response."

# =============================================================================================================================
# Network Interception Routes
# =============================================================================================================================

@app.route("/network/request", methods=["POST"])
def network_request():
    """Handle network request data from extension"""
    try:
        data = request.get_json()
        if data:
            network_data['request_data'] = data
            network_data['response_started'] = False
            network_data['stream_buffer'] = []
            network_data['events'] = []
            network_data['completed'] = False
            network_data['error'] = None
            network_data['thinking_active'] = False
            network_data['thinking_buffer'] = ""
            network_data['thinking_started'] = False
            print(f"[color:cyan]Network request intercepted: {data.get('requestId', 'unknown')}")
        return jsonify({"status": "received"}), 200
    except Exception as e:
        print(f"Error handling network request: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/network/response-start", methods=["POST"])
def network_response_start():
    """Handle response start data from extension"""
    try:
        data = request.get_json()
        if data:
            network_data['response_started'] = True
            print(f"[color:cyan]Network response started: {data.get('requestId', 'unknown')}")
        return jsonify({"status": "received"}), 200
    except Exception as e:
        print(f"Error handling network response start: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/network/response-end", methods=["POST"])
def network_response_end():
    """Handle response end data from extension"""
    try:
        data = request.get_json()
        if data:
            network_data['completed'] = True
            print(f"[color:cyan]Network response completed: {data.get('requestId', 'unknown')}")
        return jsonify({"status": "received"}), 200
    except Exception as e:
        print(f"Error handling network response end: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/network/response-error", methods=["POST"])
def network_response_error():
    """Handle response error data from extension"""
    try:
        data = request.get_json()
        if data:
            network_data['error'] = data.get('error', 'Unknown error')
            network_data['completed'] = True
            print(f"[color:red]Network response error: {data.get('error', 'Unknown')}")
        return jsonify({"status": "received"}), 200
    except Exception as e:
        print(f"Error handling network response error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/network/stream-data", methods=["POST"])
def network_stream_data():
    """Handle streaming data from extension"""
    try:
        data = request.get_json()
        if data and 'data' in data:
            # Always append to buffer - streaming mode determined by response generator
            network_data['stream_buffer'].append({
                'type': 'data',
                'content': data['data'],
                'timestamp': data.get('timestamp', time.time() * 1000)
            })
        return jsonify({"status": "received"}), 200
    except Exception as e:
        print(f"Error handling network stream data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/network/stream-event", methods=["POST"])
def network_stream_event():
    """Handle streaming events from extension"""
    try:
        data = request.get_json()
        if data and 'event' in data:
            network_data['events'].append({
                'type': 'event',
                'event': data['event'],
                'timestamp': data.get('timestamp', time.time() * 1000)
            })
        return jsonify({"status": "received"}), 200
    except Exception as e:
        print(f"Error handling network stream event: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/network/debug-log", methods=["POST"])
def network_debug_log():
    """Handle debug logs from extension"""
    try:
        data = request.get_json()
        if data and 'message' in data:
            state = get_state_manager()
            state.show_message(f"[color:yellow]EXT: {data['message']}")
        return jsonify({"status": "received"}), 200
    except Exception as e:
        state = get_state_manager()
        state.show_message(f"[color:red]Error handling debug log: {e}")
        return jsonify({"error": str(e)}), 500

# =============================================================================================================================
# Response Creation Functions
# =============================================================================================================================

def get_model_response() -> Response:
    """Get model information response"""
    return jsonify({
        "object": "list",
        "data": [{
            "id": "intense-rp-next-1",
            "object": "model",
            "created": int(time.time() * 1000)
        }]
    })

def create_response_jsonify(text: str, pipeline: MessagePipeline) -> Response:
    """Create JSON response"""
    return jsonify({
        "id": "chatcmpl-intenserp",
        "object": "chat.completion",
        "created": int(time.time() * 1000),
        "model": "intense-rp-next-1",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": text},
            "finish_reason": "stop"
        }]
    })

def create_response_streaming(text: str, pipeline: MessagePipeline) -> str:
    """Create streaming response chunk"""
    return "data: " + json.dumps({
        "id": "chatcmpl-intenserp",
        "object": "chat.completion.chunk",
        "created": int(time.time() * 1000),
        "model": "intense-rp-next-1",
        "choices": [{"index": 0, "delta": {"content": text}}]
    }) + "\n\n"

def create_response(text: str, streaming: bool, pipeline: MessagePipeline) -> Response:
    """Create appropriate response based on streaming setting"""
    if streaming:
        return Response(create_response_streaming(text, pipeline), content_type="text/event-stream")
    return create_response_jsonify(text, pipeline)

# =============================================================================================================================
# Selenium Actions
# =============================================================================================================================

def run_services() -> None:
    state = get_state_manager()
    
    try:
        state.last_response = 0
        current_driver_id = state.increment_driver_id()
        close_selenium()

        # Get config using the new system (backward compatible)
        config = state.config
        browser = state.get_config_value("browser", "Chrome")
        
        # Initialize webdriver with config for persistent cookies support
        state.driver = selenium.initialize_webdriver(browser, "https://chat.deepseek.com/sign_in", config)
        
        if state.driver:
            threading.Thread(target=monitor_driver, args=(current_driver_id,), daemon=True).start()

            # Check if we're already logged in (persistent cookies might have us logged in)
            try:
                import time
                time.sleep(2)  # Give page time to load
                current_url = state.driver.get_current_url()
                already_logged_in = not current_url.endswith("/sign_in")
                
                if already_logged_in:
                    print("[color:green]Already logged in via persistent cookies!")
                else:
                    # Get DeepSeek config using new system for auto-login
                    auto_login = state.get_config_value("models.deepseek.auto_login", False)
                    if auto_login:
                        email = state.get_config_value("models.deepseek.email", "")
                        password = state.get_config_value("models.deepseek.password", "")
                        if email and password:
                            print("[color:cyan]Attempting auto-login...")
                            deepseek.login(state.driver, email, password)
                        else:
                            print("[color:yellow]Auto-login enabled but email/password not configured")
            except Exception as e:
                print(f"[color:red]Error during login check: {e}")
                # Continue anyway

            state.clear_messages()
            state.show_message("[color:red]API IS NOW ACTIVE!")
            state.show_message("[color:cyan]WELCOME TO INTENSE RP API")
            
            # Get configured API port
            api_port = state.get_config_value("api.port", 5000)
            state.show_message(f"[color:yellow]URL 1: [color:white]http://127.0.0.1:{api_port}/")

            # Check show_ip setting using new system
            if state.get_config_value("show_ip", False):
                ip = socket.gethostbyname(socket.gethostname())
                state.show_message(f"[color:yellow]URL 2: [color:white]http://{ip}:{api_port}/")

            state.is_running = True
            serve(app, host="0.0.0.0", port=api_port, channel_request_lookahead=1)
        else:
            state.show_message("[color:red]Selenium failed to start.")
    except Exception as e:
        print(f"Error starting Selenium: {e}")
    finally:
        state.is_running = False

def monitor_driver(driver_id: int) -> None:
    state = get_state_manager()
    print("Starting browser detection.")
    
    while driver_id == state.last_driver:
        if state.driver and not selenium.is_browser_open(state.driver):
            state.clear_messages()
            state.show_message("[color:red]Browser connection lost!")
            state.driver = None
            break
        time.sleep(2)

def close_selenium() -> None:
    state = get_state_manager()
    try:
        if state.driver:
            state.driver.quit()
            state.driver = None
    except Exception:
        pass