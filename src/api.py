from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import utils.webdriver_utils as selenium
import utils.deepseek_driver as deepseek
import socket, time, threading, json
from typing import Generator
from waitress import serve
from core import get_state_manager, StateEvent
from pipeline.message_pipeline import MessagePipeline, ProcessingError
from utils.message_dump_manager import get_dump_manager
from functools import wraps
import time

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
    'thinking_started': False,
    'ready': False,  # CDP readiness flag
    'censored': False,  # Anti-censorship flag
    'censorship_detected': False  # Track if censorship was detected in stream
}

# Note for self: STOP CONFUSING THE NETWORK PARAMETER NAMES

def detect_censorship(json_data: dict) -> bool:
    """
    Detect DeepSeek censorship tokens in streaming data
    Returns True if censorship is detected, False otherwise
    """
    try:
        # Primary detection: Check for CONTENT_FILTER status
        if 'v' in json_data:
            content_value = json_data['v']
            
            # Handle batch operations that contain censorship indicators
            if (json_data.get('p') == 'response' and 
                json_data.get('o') == 'BATCH' and 
                isinstance(content_value, list)):
                
                for item in content_value:
                    if isinstance(item, dict):
                        # Check for CONTENT_FILTER status
                        if (item.get('p') == 'status' and 
                            item.get('v') == 'CONTENT_FILTER'):
                            return True
                        
                        # Check for TEMPLATE_RESPONSE fragments (secondary indicator)
                        if (item.get('p') == 'fragments' and 
                            isinstance(item.get('v'), list)):
                            for fragment in item['v']:
                                if (isinstance(fragment, dict) and 
                                    fragment.get('type') == 'TEMPLATE_RESPONSE'):
                                    return True
            
            # Handle direct status updates
            elif (json_data.get('p') == 'response/status' and 
                  content_value == 'CONTENT_FILTER'):
                return True
        
        return False
    except Exception as e:
        print(f"Error in censorship detection: {e}")
        return False

# =============================================================================================================================
# Authentication Functions
# =============================================================================================================================

def get_valid_api_keys():
    """Get list of valid API keys from configuration"""
    state = get_state_manager()
    api_keys_config = state.get_config_value("security.api_keys", {})

    if not api_keys_config or not isinstance(api_keys_config, dict):
        return []

    # Extract API key values from the name:key dictionary
    valid_keys = []
    for name, key in api_keys_config.items():
        if key and isinstance(key, str) and len(key.strip()) >= 16:
            valid_keys.append(key.strip())

    return valid_keys

def get_api_key_name(provided_key):
    """Get the name associated with an API key for logging purposes"""
    if not provided_key:
        return "unknown"

    state = get_state_manager()
    api_keys_config = state.get_config_value("security.api_keys", {})

    if not api_keys_config or not isinstance(api_keys_config, dict):
        return "unknown"

    # Find the name for the provided key
    for name, key in api_keys_config.items():
        if key and isinstance(key, str) and key.strip() == provided_key.strip():
            return name

    return "unknown"

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
            print(f"[color:yellow]Authentication failed: Invalid API key provided")
            return jsonify({
                "error": {
                    "message": "Invalid API key. Please check your Bearer token.",
                    "type": "authentication_error",
                    "code": "invalid_api_key"
                }
            }), 401

        # Authentication successful - log with key name for security
        key_name = get_api_key_name(api_key)
        print(f"[color:green]API request authenticated successfully using key: '{key_name}'")

        # Proceed with original function
        return f(*args, **kwargs)
    
    return decorated_function

# =============================================================================================================================
# API Endpoints
# =============================================================================================================================

@app.route("/", methods=["GET"])
def health_check():
    # Note: This it technically not needed, but Cloudflare is really picky about health checks
    # At least I got TryCloudflare working despite the political mess
    # So this isn't as bad as it seems
    """Health check endpoint for Cloudflare Tunnel"""
    return jsonify({
          "status": "ok",
          "service": "IntenseRP Next"
    })

@app.route("/models", methods=["GET"])
@require_auth
def model() -> Response:
    # Record API activity for refresh timer
    try:
        import utils.deepseek_driver as deepseek
        deepseek.record_activity()
    except Exception:
        pass  # Don't let activity tracking failures break the API
    
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
    # Record API activity for refresh timer
    try:
        import utils.deepseek_driver as deepseek
        deepseek.record_activity()
    except Exception:
        pass  # Don't let activity tracking failures break the API
    
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
                send_thoughts,
                processed_request.model
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
                processed_request.prefix_content,
                processed_request.model
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
    prefix_content: str = None,
    model: str = "intense-rp-next-1"
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
        return create_response("", streaming, pipeline, model)

    try:
        if not selenium.current_page(state.driver, "https://chat.deepseek.com"):
            state.show_message("[color:white]- [color:red]You must be on the DeepSeek website.")
            return create_response("You must be on the DeepSeek website.", streaming, pipeline, model)

        if selenium.current_page(state.driver, "https://chat.deepseek.com/sign_in"):
            state.show_message("[color:white]- [color:red]You must be logged into DeepSeek.")
            return create_response("You must be logged into DeepSeek.", streaming, pipeline, model)

        if interrupted():
            return safe_interrupt_response()

        # Check for Clean Regeneration feature
        clean_regeneration_enabled = state.get_config_value("models.deepseek.clean_regeneration", False)
        used_regeneration = False
        
        if clean_regeneration_enabled:
            try:
                dump_manager = get_dump_manager()
                
                # Compare current message with previous dump
                if dump_manager.compare_dumps(formatted_message):
                    state.show_message("[color:white]- [color:cyan]Identical message detected, attempting regeneration...")
                    
                    # Check if regenerate button is available and not censored
                    if deepseek.can_use_regenerate_button(state.driver):
                        # Use regeneration instead of new chat (DOM scraping doesn't need early CDP)
                        if deepseek.click_regenerate_button(state.driver):
                            used_regeneration = True
                            state.show_message("[color:white]- [color:green]Using regeneration instead of new chat.")
                        else:
                            state.show_message("[color:white]- [color:yellow]Regeneration failed, falling back to new chat.")
                    else:
                        state.show_message("[color:white]- [color:yellow]Regenerate button unavailable/censored, using new chat.")
                else:
                    state.show_message("[color:white]- [color:cyan]Message content changed, proceeding with new chat.")
            except Exception as e:
                state.show_message(f"[color:white]- [color:yellow]Clean Regeneration error: {e}, using new chat.")
        
        # Only configure new chat if we didn't use regeneration
        if not used_regeneration:
            deepseek.configure_chat(state.driver, deepthink, search)
            state.show_message("[color:white]- [color:cyan]Chat reset and configured.")

        if interrupted():
            return safe_interrupt_response()

        # Only send new message if we didn't use regeneration
        if not used_regeneration:
            if not deepseek.send_chat_message(state.driver, formatted_message, text_file, prefix_content):
                state.show_message("[color:white]- [color:red]Could not paste prompt.")
                return create_response("Could not paste prompt.", streaming, pipeline, model)

            state.show_message("[color:white]- [color:green]Prompt pasted and sent.")
        else:
            state.show_message("[color:white]- [color:green]Regeneration initiated.")

        if interrupted():
            return safe_interrupt_response()

        if not deepseek.active_generate_response(state.driver):
            state.show_message("[color:white]- [color:red]No response generated.")
            return create_response("No response generated.", streaming, pipeline, model)

        if interrupted():
            return safe_interrupt_response()

        state.show_message("[color:white]- [color:cyan]Awaiting response.")
        
        # Wait for generation to actually start (stop button appears) after loading phase
        if not deepseek.wait_for_generation_to_start(state.driver):
            state.show_message("[color:white]- [color:red]Response generation did not start.")
            return create_response("Response generation timeout.", streaming, pipeline, model)
        
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
                                yield create_response_streaming(new_content, pipeline, model)
                        
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
                                yield create_response_streaming(final_content, pipeline, model)
                    
                    # Send closing symbol if needed
                    closing = pipeline.get_closing_symbol(final_text) if final_text else ""
                    if closing:
                        yield create_response_streaming(closing, pipeline, model)
                    
                    # Update dumps after successful generation (only if Clean Regeneration is enabled)
                    if clean_regeneration_enabled:
                        try:
                            dump_manager = get_dump_manager()
                            dump_manager.update_dumps_after_success()
                        except Exception as e:
                            print(f"Warning: Could not update dumps after success: {e}")
                    
                    state.show_message("[color:white]- [color:green]Completed.")
                except GeneratorExit:
                    deepseek.new_chat(state.driver)
                
                except Exception as e:
                    deepseek.new_chat(state.driver)
                    print(f"Streaming error: {e}")
                    state.show_message("[color:white]- [color:red]Unknown error occurred.")
                    yield create_response_streaming("Error receiving response.", pipeline, model)
            return Response(streaming_response(), content_type="text/event-stream")
        else:
            final_text = deepseek.wait_for_response_completion(state.driver, pipeline)
            
            if interrupted():
                return safe_interrupt_response()
            
            response_text = final_text if final_text else "Error receiving response."
            closing = pipeline.get_closing_symbol(final_text) if final_text else ""
            response = response_text + closing
            
            # Update dumps after successful generation (only if Clean Regeneration is enabled)
            if clean_regeneration_enabled:
                try:
                    dump_manager = get_dump_manager()
                    dump_manager.update_dumps_after_success()
                except Exception as e:
                    print(f"Warning: Could not update dumps after success: {e}")
            
            state.show_message("[color:white]- [color:green]Completed.")
            return create_response_jsonify(response, pipeline, model)
    
    except Exception as e:
        print(f"Error generating response: {e}")
        state.show_message("[color:white]- [color:red]Unknown error occurred.")
        return create_response("Error receiving response.", streaming, pipeline, model)

def deepseek_network_response(
    current_id: int, 
    formatted_message: str, 
    streaming: bool, 
    deepthink: bool, 
    search: bool, 
    text_file: bool,
    pipeline: MessagePipeline,
    prefix_content: str = None,
    send_thoughts: bool = True,
    model: str = "intense-rp-next-1"
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
        return create_response("", streaming, pipeline, model)

    try:
        if not selenium.current_page(state.driver, "https://chat.deepseek.com"):
            state.show_message("[color:white]- [color:red]You must be on the DeepSeek website.")
            return create_response("You must be on the DeepSeek website.", streaming, pipeline, model)

        if selenium.current_page(state.driver, "https://chat.deepseek.com/sign_in"):
            state.show_message("[color:white]- [color:red]You must be logged into DeepSeek.")
            return create_response("You must be logged into DeepSeek.", streaming, pipeline, model)

        if interrupted():
            return safe_interrupt_response()

        # Check for Clean Regeneration feature and start CDP early if needed
        clean_regeneration_enabled = state.get_config_value("models.deepseek.clean_regeneration", False)
        used_regeneration = False
        regeneration_possible = False
        
        if clean_regeneration_enabled:
            try:
                dump_manager = get_dump_manager()
                
                # Compare current message with previous dump
                if dump_manager.compare_dumps(formatted_message):
                    state.show_message("[color:white]- [color:cyan]Identical message detected, checking if regeneration is possible...")
                    
                    # Check if regenerate button is available and not censored (but don't click yet)
                    if deepseek.can_use_regenerate_button(state.driver):
                        regeneration_possible = True
                        state.show_message("[color:white]- [color:green]Regeneration possible, starting CDP interception early...")
                    else:
                        state.show_message("[color:white]- [color:yellow]Regenerate button unavailable/censored, using new chat.")
                else:
                    state.show_message("[color:white]- [color:cyan]Message content changed, proceeding with new chat.")
            except Exception as e:
                state.show_message(f"[color:white]- [color:yellow]Clean Regeneration error: {e}, using new chat.")

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
        network_data['ready'] = False  # Reset readiness flag
        network_data['censored'] = False  # Reset anti-censorship flag
        network_data['censorship_detected'] = False  # Reset censorship detection flag
        # ^^ CDP READINESS FLAG ^^
        
        # Enable network interception (early if regeneration is possible)
        deepseek.enable_network_interception(state.driver)
        if regeneration_possible:
            state.show_message("[color:white]- [color:cyan]CDP network interception starting (early for regeneration)...")
        else:
            state.show_message("[color:white]- [color:cyan]CDP network interception starting...")

        # Wait for extension to signal readiness
        readiness_timeout = 10.0  # 10 second timeout
        start_time = time.time()
        
        state.show_message("[color:yellow]Waiting for CDP to become ready...")
        while not network_data['ready'] and (time.time() - start_time) < readiness_timeout:
            time.sleep(0.1)  # Check every 100ms
            
        if network_data['ready']:
            if regeneration_possible:
                state.show_message("[color:green]CDP ready! Now clicking regenerate button...")
                # No extra buffer needed - CDP is ready, click immediately
            else:
                state.show_message("[color:green]CDP ready! Adding 500ms buffer before proceeding...")
                time.sleep(0.5)  # Additional buffer for extra safety
        else:
            state.show_message("[color:yellow]CDP readiness timeout - proceeding anyway (may lose first chunk)")

        # Now that CDP is ready, click regenerate button if possible
        if regeneration_possible:
            try:
                if deepseek.click_regenerate_button(state.driver):
                    used_regeneration = True
                    state.show_message("[color:white]- [color:green]Regenerate button clicked - CDP should catch the request.")
                else:
                    state.show_message("[color:white]- [color:yellow]Regeneration click failed, falling back to new chat.")
                    regeneration_possible = False
            except Exception as e:
                state.show_message(f"[color:white]- [color:yellow]Error clicking regenerate: {e}, falling back to new chat.")
                regeneration_possible = False

        # Configure chat and send message (only if not using regeneration)
        if not used_regeneration:
            deepseek.configure_chat(state.driver, deepthink, search)
            state.show_message("[color:white]- [color:cyan]Chat reset and configured.")
        
        if interrupted():
            return safe_interrupt_response()

        # Only send new message if we didn't use regeneration
        if not used_regeneration:
            if not deepseek.send_chat_message(state.driver, formatted_message, text_file, prefix_content):
                state.show_message("[color:white]- [color:red]Could not paste prompt.")
                deepseek.disable_network_interception(state.driver)
                return create_response("Could not paste prompt.", streaming, pipeline, model)

            state.show_message("[color:white]- [color:green]Prompt pasted and sent.")
        else:
            state.show_message("[color:white]- [color:green]Regeneration initiated - waiting for network response.")

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
                        yield create_response_streaming("Error: Network response did not start", pipeline, model)
                        return
                    
                    # Stream the data as it arrives
                    last_processed_index = 0
                    finish_event_received = False
                    timeout_start = time.time()
                    max_total_time = 300  # 5 minutes absolute timeout
                    
                    while not finish_event_received:
                        if interrupted() or time.time() - timeout_start > max_total_time:
                            break
                        
                        # Check for censorship detection - stop streaming if detected
                        if network_data['censorship_detected']:
                            finish_event_received = True
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
                                            yield create_response_streaming(chunk, pipeline, model)
                        
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
                        yield create_response_streaming("\n</think>\n\n", pipeline, model)
                    # Reset thinking state regardless of send_thoughts setting
                    if network_data['thinking_active']:
                        network_data['thinking_active'] = False
                        network_data['thinking_started'] = False
                    
                    # Check for errors
                    if network_data['error']:
                        yield create_response_streaming(f"Error: {network_data['error']}", pipeline, model)
                    
                    # Update dumps after successful generation (only if Clean Regeneration is enabled)
                    if clean_regeneration_enabled:
                        try:
                            dump_manager = get_dump_manager()
                            dump_manager.update_dumps_after_success()
                        except Exception as e:
                            print(f"Warning: Could not update dumps after success: {e}")
                    
                    # Show completion message with censorship status
                    completion_message = "Network response completed (censored)" if network_data['censorship_detected'] else "Network response completed."
                    state.show_message(f"[color:white]- [color:green]{completion_message}")
                    
                except GeneratorExit:
                    deepseek.disable_network_interception(state.driver)
                    deepseek.new_chat(state.driver)
                except Exception as e:
                    deepseek.disable_network_interception(state.driver)
                    deepseek.new_chat(state.driver)
                    print(f"Network streaming error: {e}")
                    state.show_message("[color:white]- [color:red]Network streaming error occurred.")
                    yield create_response_streaming("Error receiving network response.", pipeline, model)
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
                # Check for censorship - complete early if detected
                if network_data['censorship_detected']:
                    break
                time.sleep(0.1)
            
            if network_data['error']:
                response_text = f"Error: {network_data['error']}"
            else:
                # Combine all stream data
                state.show_message(f"[color:cyan]Combining {len(network_data['stream_buffer'])} stream items...")
                response_text = combine_network_stream_data(network_data['stream_buffer'], send_thoughts)
                
                # Log censorship detection
                if network_data['censorship_detected']:
                    state.show_message(f"[color:yellow]Censorship detected - response truncated at {len(response_text)} characters")
                else:
                    state.show_message(f"[color:cyan]Final combined response length: {len(response_text)}")
            
            # Update dumps after successful generation (only if Clean Regeneration is enabled)
            if clean_regeneration_enabled:
                try:
                    dump_manager = get_dump_manager()
                    dump_manager.update_dumps_after_success()
                except Exception as e:
                    print(f"Warning: Could not update dumps after success: {e}")
            
            deepseek.disable_network_interception(state.driver)
            completion_message = "Network response completed (censored)" if network_data['censorship_detected'] else "Network response completed."
            state.show_message(f"[color:white]- [color:green]{completion_message}")
            return create_response_jsonify(response_text, pipeline, model)
    
    except Exception as e:
        print(f"Error in network response: {e}")
        state.show_message("[color:white]- [color:red]Network response error occurred.")
        deepseek.disable_network_interception(state.driver)
        return create_response("Error receiving network response.", streaming, pipeline, model)

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
                
                # NEW FORMAT: Handle fragment creation/updates
                if path == 'response/fragments' and json_data.get('o') == 'APPEND':
                    # New fragment being created
                    if isinstance(content_value, list):
                        for fragment in content_value:
                            if isinstance(fragment, dict) and 'type' in fragment:
                                fragment_type = fragment['type']
                                fragment_content = fragment.get('content', '')
                                
                                if fragment_type == 'THINK':
                                    # Starting thinking fragment
                                    if send_thoughts:
                                        if not network_data['thinking_active']:
                                            chunks.append("<think>\n")
                                            network_data['thinking_active'] = True
                                            network_data['thinking_started'] = True
                                        chunks.append(fragment_content)
                                    else:
                                        # Track thinking state but don't send content
                                        if not network_data['thinking_active']:
                                            network_data['thinking_active'] = True
                                            network_data['thinking_started'] = True
                                
                                elif fragment_type == 'RESPONSE':
                                    # Starting response fragment - end thinking mode first
                                    if network_data['thinking_active']:
                                        if send_thoughts:
                                            chunks.append("\n</think>\n\n")
                                        network_data['thinking_active'] = False
                                        network_data['thinking_started'] = False
                                    chunks.append(fragment_content)
                
                elif path and path.startswith('response/fragments/') and path.endswith('/content'):
                    # Content update for existing fragment (NEW FORMAT)
                    if isinstance(content_value, str):
                        # Determine if this is thinking or response content by current mode
                        if network_data['thinking_active'] and send_thoughts:
                            chunks.append(content_value)
                        elif not network_data['thinking_active']:
                            chunks.append(content_value)
                        # If thinking_active but send_thoughts is False, ignore content
                
                # LEGACY FORMAT: Handle thinking content start
                elif path == 'response/thinking_content':
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
                
                # LEGACY FORMAT: Handle regular content start - this ends thinking mode
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
                
                # LEGACY FORMAT: Handle continuation chunks (no path specified)
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
                
                # LEGACY FORMAT: Handle batch operations
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
                
                # NEW FORMAT: Handle fragment creation/updates
                if path == 'response/fragments' and json_data.get('o') == 'APPEND':
                    # New fragment being created
                    if isinstance(content_value, list):
                        result = ""
                        for fragment in content_value:
                            if isinstance(fragment, dict) and 'type' in fragment:
                                fragment_type = fragment['type']
                                fragment_content = fragment.get('content', '')
                                
                                if fragment_type == 'THINK':
                                    # Starting thinking fragment
                                    if send_thoughts:
                                        if not network_data['thinking_active']:
                                            network_data['thinking_active'] = True
                                            network_data['thinking_buffer'] = ""
                                            network_data['thinking_started'] = True
                                        network_data['thinking_buffer'] += fragment_content
                                    else:
                                        # Track thinking state but don't accumulate content
                                        if not network_data['thinking_active']:
                                            network_data['thinking_active'] = True
                                            network_data['thinking_started'] = True
                                    # Return empty while accumulating thinking content
                                
                                elif fragment_type == 'RESPONSE':
                                    # Starting response fragment - end thinking mode first
                                    if network_data['thinking_active']:
                                        if send_thoughts:
                                            thinking_content = network_data['thinking_buffer'].strip()
                                            if thinking_content:
                                                result += f"<think>\n{thinking_content}\n</think>\n\n"
                                        # Reset thinking state
                                        network_data['thinking_active'] = False
                                        network_data['thinking_buffer'] = ""
                                        network_data['thinking_started'] = False
                                    result += fragment_content
                        
                        return result
                
                elif path and path.startswith('response/fragments/') and path.endswith('/content'):
                    # Content update for existing fragment (NEW FORMAT)
                    if isinstance(content_value, str):
                        # Determine if this is thinking or response content by current mode
                        if network_data['thinking_active']:
                            if send_thoughts:
                                network_data['thinking_buffer'] += content_value
                            # Return empty while accumulating/ignoring thinking content
                            return ""
                        else:
                            # Regular content
                            return content_value
                
                # LEGACY FORMAT: Handle thinking content start
                elif path == 'response/thinking_content':
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
                
                # LEGACY FORMAT: Handle regular content start - this ends thinking mode
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
                
                # LEGACY FORMAT: Handle continuation chunks (no path specified)
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
                
                # LEGACY FORMAT: Handle batch operations
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
            network_data['censored'] = False
            network_data['censorship_detected'] = False
            # Note: Don't reset 'ready' here as this endpoint is called after readiness is confirmed
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
            # Optimization because burned CPUs are not healthy CPUs.
            stream_content = data['data']
            should_check_censorship = False
            
            # Only parse and check if the content looks like it might contain censorship indicators
            if (stream_content.startswith('{') and 
                ('CONTENT_FILTER' in stream_content or 
                 'TEMPLATE_RESPONSE' in stream_content or
                 '"o": "BATCH"' in stream_content or
                 '"p": "response"' in stream_content)):
                should_check_censorship = True
            
            if should_check_censorship:
                try:
                    import json
                    json_data = json.loads(stream_content)
                    
                    # Check if this data contains censorship indicators
                    if detect_censorship(json_data):
                        network_data['censorship_detected'] = True
                        network_data['completed'] = True  # Mark as completed to end stream
                        state = get_state_manager()
                        state.show_message("[color:yellow]Censorship detected - truncating response")
                        
                        # Don't add the censorship content to stream buffer
                        # Trigger finish event to end streaming gracefully
                        network_data['events'].append({
                            'type': 'event',
                            'event': 'finish',
                            'timestamp': time.time() * 1000
                        })
                        return jsonify({"status": "censorship_detected"}), 200
                except Exception as e:
                    # If parsing fails, continue with normal processing
                    print(f"Error checking censorship in stream data: {e}")
            
            # Normal processing - append to buffer if not censored
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

@app.route("/network/ready", methods=["POST"])
def network_ready():
    """Handle readiness confirmation from extension"""
    try:
        data = request.get_json()
        if data and 'ready' in data:
            network_data['ready'] = bool(data['ready'])
            state = get_state_manager()
            if data['ready']:
                state.show_message("[color:green]CDP network interception ready")
            else:
                state.show_message("[color:cyan]CDP network interception stopped")
        return jsonify({"status": "confirmed"}), 200
    except Exception as e:
        state = get_state_manager()
        state.show_message(f"[color:red]Error handling readiness confirmation: {e}")
        return jsonify({"error": str(e)}), 500

# =============================================================================================================================
# Response Creation Functions
# =============================================================================================================================

def get_model_response() -> Response:
    """Get model information response"""
    base_time = int(time.time() * 1000)
    return jsonify({
        "object": "list",
        "data": [
            {
                "id": "intense-rp-next-1",
                "object": "model",
                "created": base_time
            },
            {
                "id": "intense-rp-next-1-chat",
                "object": "model",
                "created": base_time
            },
            {
                "id": "intense-rp-next-1-reasoner",
                "object": "model", 
                "created": base_time
            }
        ]
    })

def create_response_jsonify(text: str, pipeline: MessagePipeline, model: str = "intense-rp-next-1") -> Response:
    """Create JSON response"""
    return jsonify({
        "id": "chatcmpl-intenserp",
        "object": "chat.completion",
        "created": int(time.time() * 1000),
        "model": model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": text},
            "finish_reason": "stop"
        }]
    })

def create_response_streaming(text: str, pipeline: MessagePipeline, model: str = "intense-rp-next-1") -> str:
    """Create streaming response chunk"""
    return "data: " + json.dumps({
        "id": "chatcmpl-intenserp",
        "object": "chat.completion.chunk",
        "created": int(time.time() * 1000),
        "model": model,
        "choices": [{"index": 0, "delta": {"content": text}}]
    }) + "\n\n"

def create_response(text: str, streaming: bool, pipeline: MessagePipeline, model: str = "intense-rp-next-1") -> Response:
    """Create appropriate response based on streaming setting"""
    if streaming:
        return Response(create_response_streaming(text, pipeline, model), content_type="text/event-stream")
    return create_response_jsonify(text, pipeline, model)

# =============================================================================================================================
# Selenium Actions
# =============================================================================================================================

def run_services() -> None:
    state = get_state_manager()
    
    try:
        # Clean up msgdump directory on startup for safety
        try:
            dump_manager = get_dump_manager()
            dump_manager.cleanup_dump_directory()
        except Exception as e:
            print(f"Warning: Could not cleanup msgdump directory on startup: {e}")
        
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

            state.clear_main_screen()
            state.show_message("[color:red]API IS NOW ACTIVE!")
            state.show_message("[color:cyan]WELCOME TO INTENSE RP API")
            
            # Get configured API port
            api_port = state.get_config_value("api.port", 5000)
            state.show_message(f"[color:yellow]URL 1: [color:white]http://127.0.0.1:{api_port}/")

            # Check show_ip setting using new system
            if state.get_config_value("show_ip", False):
                ip = socket.gethostbyname(socket.gethostname())
                state.show_message(f"[color:yellow]URL 2: [color:white]http://{ip}:{api_port}/")

            # Start TryCloudflare tunnel if enabled
            tunnel_enabled = state.get_config_value("tunnel.enabled", False)
            
            if tunnel_enabled:
                state.show_message("[color:cyan]Starting TryCloudflare tunnel...")
                try:
                    # Start tunnel in background
                    if state.start_tunnel(api_port):
                        state.show_message("[color:green]TryCloudflare tunnel startup initiated")
                        # Give tunnel a moment to start (URL will be displayed via callback)
                        threading.Timer(2.0, lambda: None).start()
                    else:
                        state.show_message("[color:yellow]TryCloudflare tunnel was already active or failed to start")
                except Exception as e:
                    state.show_message(f"[color:red]Error starting TryCloudflare tunnel: {e}")
                    print(f"Warning: Could not start tunnel: {e}")

            # Start refresh timer if enabled
            try:
                deepseek.start_refresh_timer()
            except Exception as e:
                print(f"Warning: Could not start refresh timer: {e}")

            state.is_running = True
            
            # Bind to network interface only if show_ip is enabled, otherwise localhost only
            host = "0.0.0.0" if state.get_config_value("show_ip", False) else "127.0.0.1"
            serve(app, host=host, port=api_port, channel_request_lookahead=1)
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
            # Stop refresh timer when browser connection is lost
            try:
                deepseek.stop_refresh_timer()
            except Exception as e:
                print(f"Warning: Could not stop refresh timer: {e}")
            
            state.clear_messages()
            state.show_message("[color:red]Browser connection lost!")
            state.driver = None
            break
        time.sleep(2)

def close_selenium() -> None:
    state = get_state_manager()
    try:
        # Clean up msgdump directory on exit for safety
        try:
            dump_manager = get_dump_manager()
            dump_manager.cleanup_dump_directory()
        except Exception as e:
            print(f"Warning: Could not cleanup msgdump directory on exit: {e}")
        
        if state.driver:
            # Stop refresh timer before closing driver
            try:
                deepseek.stop_refresh_timer()
            except Exception as e:
                print(f"Warning: Could not stop refresh timer: {e}")
            
            # Stop tunnel if active
            try:
                if state.is_tunnel_active():
                    state.show_message("[color:cyan]Stopping TryCloudflare tunnel...")
                    state.stop_tunnel()
                    state.show_message("[color:green]TryCloudflare tunnel stopped")
            except Exception as e:
                print(f"Warning: Could not stop tunnel: {e}")
            
            # Increment driver ID first to stop the monitor thread cleanly
            state.increment_driver_id()
            state.driver.quit()
            state.driver = None
    except Exception:
        pass