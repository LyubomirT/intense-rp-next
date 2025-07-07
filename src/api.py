from flask import Flask, jsonify, request, Response
import utils.webdriver_utils as selenium
import utils.deepseek_driver as deepseek
import socket, time, threading, json
from typing import Generator
from waitress import serve
from core import get_state_manager, StateEvent
from pipeline.message_pipeline import MessagePipeline, ProcessingError

app = Flask(__name__)

@app.route("/models", methods=["GET"])
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
        
        return deepseek_response(
            current_message, 
            formatted_message, 
            streaming, 
            processed_request.use_deepthink,
            processed_request.use_search,
            processed_request.use_text_file,
            pipeline
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
    pipeline: MessagePipeline
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

        if not deepseek.send_chat_message(state.driver, formatted_message, text_file):
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
        initial_text = ""
        last_text = ""

        if streaming:
            def streaming_response() -> Generator[str, None, None]:
                nonlocal initial_text, last_text
                try:
                    while deepseek.is_response_generating(state.driver):
                        if interrupted():
                            break

                        new_text = deepseek.get_last_message(state.driver, pipeline)
                        if new_text and not initial_text:
                            initial_text = new_text
                        
                        if new_text and new_text != last_text and new_text.startswith(initial_text):
                            # Improved differencing logic to handle content changes robustly
                            if len(new_text) > len(last_text) and new_text.startswith(last_text):
                                # Normal case: new content is an extension of previous content
                                diff = new_text[len(last_text):]
                                last_text = new_text
                                yield create_response_streaming(diff, pipeline)
                            elif new_text != last_text:
                                # Edge case: content changed unexpectedly (e.g., HTML processing race condition)
                                # Send the complete new content and update last_text
                                diff = new_text
                                last_text = new_text
                                yield create_response_streaming(diff, pipeline)
                        
                        time.sleep(0.2)

                    if interrupted():
                        return safe_interrupt_response()

                    # Final processing - get the complete response
                    final_text = deepseek.wait_for_response_completion(state.driver, pipeline)
                    
                    if final_text:
                        # Send any remaining content
                        if final_text != last_text:
                            # Check for changes one last time before sending
                            if len(final_text) > len(last_text) and final_text.startswith(last_text):
                                final_diff = final_text[len(last_text):]
                            else:
                                final_diff = final_text
                            
                            if final_diff:
                                yield create_response_streaming(final_diff, pipeline)
                    
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

# =============================================================================================================================
# Response Creation Functions
# =============================================================================================================================

def get_model_response() -> Response:
    """Get model information response"""
    return jsonify({
        "object": "list",
        "data": [{
            "id": "rp-intense-2.7.0",
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
        "model": "rp-intense-2.7.0",
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
        "model": "rp-intense-2.7.0",
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
            state.show_message("[color:yellow]URL 1: [color:white]http://127.0.0.1:5000/")

            # Check show_ip setting using new system
            if state.get_config_value("show_ip", False):
                ip = socket.gethostbyname(socket.gethostname())
                state.show_message(f"[color:yellow]URL 2: [color:white]http://{ip}:5000/")

            state.is_running = True
            serve(app, host="0.0.0.0", port=5000, channel_request_lookahead=1)
        else:
            state.clear_messages()
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