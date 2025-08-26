import threading, webbrowser, api, sys, os, re, platform, tkinter as tk
import utils.response_utils as response_utils
import utils.deepseek_driver as deepseek
import utils.process_manager as process
import utils.gui_builder as gui_builder
from utils.gui_builder import ContributorWindow, WelcomeWindow
from utils.welcome_utils import WelcomeManager
import utils.console_manager as console_manager
import utils.webdriver_utils as selenium
import utils.api_key_generator as api_key_gen
from packaging import version
from core import get_state_manager, StateEvent

# New modular config system imports
from config.config_manager import ConfigManager
from config.config_ui_generator import ConfigUIGenerator

__version__ = "1.3.2" 

# Local GUI state (not shared across modules)
root = None
storage_manager = None
config_manager = None
icon_path = None

# =============================================================================================================================
# Modal Window Management
# =============================================================================================================================

def make_window_modal(window, parent_window):
    """
    Make a window modal in a cross-platform way that preserves Mica effect on Windows 11.
    On Windows, we avoid using transient() to preserve the Mica backdrop effect.
    """
    is_windows = platform.system() == "Windows"
    
    if not is_windows:
        # On non-Windows platforms, use traditional transient approach
        window.transient(parent_window)
        window.grab_set()
    else:
        # On Windows, we use alternative approach to preserve Mica effect
        # This makes the window always on top and handle focus manually
        window.attributes("-topmost", True)
        window.grab_set()
        
        # Bind focus events to maintain modal behavior
        def on_parent_focus(_event=None):
            if window.winfo_exists():
                window.focus_force()
                window.lift()
        
        binding_id = parent_window.bind("<FocusIn>", on_parent_focus)
        
        # Store the binding ID and parent for cleanup
        setattr(window, '_parent_focus_binding_id', binding_id)
        setattr(window, '_parent_window', parent_window)

        # UNFORTUNATELY, this also means that all of the normal built-in modal behaviors
        # ... now must be written manually. Tell Microsoft I want to have my cake and eat it too.
        #                                                                           - Lyubomir
        #
        #
        # If you're reading this, it's likely I've been hunted down by Microsoft for this comment.
        
        # Override destroy to clean up bindings
        original_destroy = window.destroy
        def cleanup_and_destroy():
            try:
                if hasattr(window, '_parent_window') and hasattr(window, '_parent_focus_binding_id'):
                    parent = getattr(window, '_parent_window')
                    binding_id = getattr(window, '_parent_focus_binding_id')
                    
                    if parent.winfo_exists():
                        parent.unbind("<FocusIn>", binding_id)
            except (AttributeError, tk.TclError):
                pass
            finally:
                original_destroy()
        
        window.destroy = cleanup_and_destroy
    
    # Common modal setup
    window.focus_force()
    window.lift()

# =============================================================================================================================
# Console Window
# =============================================================================================================================

def create_console_window() -> None:
    """Create console window using the new console manager"""
    state = get_state_manager()
    
    try:
        # Initialize console manager
        console_mgr = console_manager.ConsoleManager(state, storage_manager)
        console_mgr.initialize(config_manager.get_all(), icon_path)
        
        # Store console manager in state
        state.console_manager = console_mgr
        
    except Exception as e:
        print(f"Error creating console window: {e}")

def start_services() -> None:
    state = get_state_manager()
    
    try:
        state.clear_messages()
        state.show_message("[color:green]Please wait...")
        threading.Thread(target=api.run_services, daemon=True).start()
    except Exception as e:
        state.show_message("[color:red]Selenium failed to start.")
        print(f"Error starting services: {e}")

def stop_services() -> None:
    state = get_state_manager()
    
    try:
        state.clear_messages()
        state.show_message("[color:yellow]Stopping services...")
        api.close_selenium()
        state.show_message("[color:cyan]Services stopped successfully.")
    except Exception as e:
        state.show_message("[color:red]Error stopping services.")
        print(f"Error stopping services: {e}")

def toggle_services() -> None:
    """Toggle between starting and stopping services based on current state"""
    state = get_state_manager()
    
    if state.driver:
        stop_services()
    else:
        start_services()

def update_start_button_state(state_change) -> None:
    """Observer function to update start button text based on browser state"""
    global root
    
    try:
        if root:
            start_button = root.get_widget("start")
            if start_button:
                if state_change.event_type == StateEvent.BROWSER_STARTED:
                    start_button.configure(text="Stop")
                elif state_change.event_type == StateEvent.BROWSER_STOPPED:
                    start_button.configure(text="Start")
    except Exception as e:
        print(f"Error updating start button state: {e}")

# =============================================================================================================================
# Config Window - Now Using Modular System
# =============================================================================================================================

def on_console_toggle(value: bool) -> None:
    """Handle console window toggle"""
    state = get_state_manager()
    
    try:
        if hasattr(state, 'console_manager') and state.console_manager:
            state.console_manager.show(value, root, center=True)
    except Exception as e:
        print(f"Error when toggling console visibility: {e}")

def preview_console_changes() -> None:
    """Preview console settings changes"""
    state = get_state_manager()
    
    try:
        if hasattr(state, 'console_manager') and state.console_manager:
            # Get current values from the active config window if it exists
            current_ui_generator = getattr(state, 'current_ui_generator', None)
            
            if current_ui_generator:
                # Get current UI state for console settings
                ui_config = current_ui_generator._get_ui_config_state()
                
                # Try to get values directly from console frame widgets
                console_frame = current_ui_generator.frames.get('console_settings')
                if console_frame:
                    font_family = console_frame.get_widget_value('console.font_family')
                    font_size = console_frame.get_widget_value('console.font_size')
                    color_palette = console_frame.get_widget_value('console.color_palette')
                    word_wrap = console_frame.get_widget_value('console.word_wrap')
                    
                    # Create settings structure expected by ConsoleSettings constructor
                    console_config = {}
                    console_config['font_family'] = font_family if font_family is not None else 'Consolas'
                    console_config['font_size'] = int(font_size) if font_size is not None else 12
                    console_config['color_palette'] = color_palette if color_palette is not None else 'Modern'
                    console_config['word_wrap'] = bool(word_wrap) if word_wrap is not None else True
                    
                    console_settings = {'console': console_config}
                else:
                    # Fallback to parsed UI config
                    console_settings = ui_config
                
                # Apply settings
                new_settings = console_manager.ConsoleSettings(console_settings)
                state.console_manager.update_settings(new_settings)
                print("[color:green]Console settings applied in preview mode")
            else:
                # Fallback to saved config if no UI window found
                new_settings = console_manager.ConsoleSettings(config_manager.get_all())
                state.console_manager.update_settings(new_settings)
                print("[color:yellow]Applied saved console settings (no UI window found)")
            
    except Exception as e:
        print(f"Error applying console settings: {e}")

def clear_browser_data() -> None:
    """Clear browser data (cookies, cache, etc.)"""
    global config_manager
    
    try:
        # Get current browser setting
        browser = config_manager.get("browser", "Chrome").lower()
        
        # Only works for Chromium browsers
        if browser in ("chrome", "edge"):
            success = selenium.clear_browser_data(browser)
            if success:
                print(f"[color:green]Browser data cleared for {browser.title()}")
            else:
                print(f"[color:red]Failed to clear browser data for {browser.title()}")
        else:
            print(f"[color:yellow]Browser data clearing not supported for {browser.title()}")
            
    except Exception as e:
        print(f"[color:red]Error clearing browser data: {e}")

def generate_api_key() -> None:
    """Generate a new API key and add it to the textarea"""
    state = get_state_manager()
    
    try:
        # Get reference to current UI generator
        current_ui_generator = getattr(state, 'current_ui_generator', None)
        if not current_ui_generator:
            print("[color:red]Error: Settings window not available")
            return
        
        # Find the security settings frame
        security_frame = None
        for section_id, frame in current_ui_generator.frames.items():
            if section_id == "security_settings":
                security_frame = frame
                break
        
        if not security_frame:
            print("[color:red]Error: Security settings not found")
            return
        
        # Get the API keys textarea widget
        api_keys_widget = security_frame.get_widget("security.api_keys")
        if not api_keys_widget:
            print("[color:red]Error: API keys textarea not found") 
            return
        
        # Generate new API key
        new_key = api_key_gen.generate_api_key()
        
        # Get current content from textarea
        current_content = api_keys_widget.get("0.0", "end-1c")
        
        # Add new key to content
        updated_content = api_key_gen.APIKeyGenerator.add_key_to_textarea(current_content, new_key)
        
        # Update textarea
        api_keys_widget.delete("0.0", "end")
        api_keys_widget.insert("0.0", updated_content)
        
        print(f"[color:green]Generated new API key: {new_key}")
        print("[color:cyan]Key added to the list above. Remember to save your settings!")
        
    except Exception as e:
        print(f"[color:red]Error generating API key: {e}")

def browse_browser_path() -> None:
    """Browse for a custom browser executable path"""
    state = get_state_manager()
    
    try:
        # Get reference to current UI generator
        current_ui_generator = getattr(state, 'current_ui_generator', None)
        if not current_ui_generator:
            print("[color:red]Error: Settings window not available")
            return
        
        # Import file dialog
        from tkinter import filedialog
        
        # Define file types for browser executables
        if platform.system() == "Windows":
            filetypes = [
                ("Executable files", "*.exe"),
                ("All files", "*.*")
            ]
        else:
            filetypes = [
                ("All files", "*.*")
            ]
        
        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Select Chromium-based Browser Executable",
            filetypes=filetypes,
            parent=current_ui_generator.window
        )
        
        if file_path:
            # Find the browser_path field and update it
            for section in current_ui_generator.frames.values():
                browser_path_widget = section.get_widget("browser_path")
                if browser_path_widget:
                    # Clear current value and set new path
                    browser_path_widget.delete(0, "end")
                    browser_path_widget.insert(0, file_path)
                    print(f"[color:green]Browser path updated: {file_path}")
                    break
    
    except Exception as e:
        print(f"[color:red]Error browsing for browser path: {e}")

def open_config_window() -> None:
    """Open configuration window using the new modular system"""
    global root, config_manager
    state = get_state_manager()
    
    try:
        # Set up command handlers for special actions
        command_handlers = {
            'on_console_toggle': on_console_toggle,
            'preview_console_changes': preview_console_changes,
            'clear_browser_data': clear_browser_data,
            'generate_api_key': generate_api_key,
            'browse_browser_path': browse_browser_path,
        }
        
        # Create UI generator
        ui_generator = ConfigUIGenerator(config_manager, command_handlers)
        
        # Store reference to current UI generator for preview functionality
        state.current_ui_generator = ui_generator
        
        # Create and show window
        config_window = ui_generator.create_config_window(icon_path)
        make_window_modal(config_window, root)
        config_window.center(root)
        
        # Store in state for reference
        state.config_window = config_window
        
        print("Settings window created with new modular system.")
        
    except Exception as e:
        print(f"Error opening config window: {e}")

# =============================================================================================================================
# Credits
# =============================================================================================================================

def open_credits() -> None:
    try:
        global root, icon_path
        if root:
            contributor_window = ContributorWindow(root, icon_path)
            contributor_window.center()
            contributor_window.lift()
            contributor_window.focus()
            print("Contributors window opened.")
    except Exception as e:
        print(f"Error opening contributors window: {e}")

# =============================================================================================================================
# Update Window
# =============================================================================================================================

def create_update_window(last_version: str) -> None:
    global root, icon_path
    try:
        # Create new update window instead of basic one
        update_window = gui_builder.BetterUpdateWindow(root, last_version, icon_path)
        make_window_modal(update_window, root)
        update_window.center()

        print(f"Better update window created for version {last_version}.")
    except Exception as e:
        print(f"Error opening update window: {e}")

# Legacy function - replaced by the newer update system
# def open_github(update_window: gui_builder.UpdateWindow) -> None:
#     try:
#         webbrowser.open("https://github.com/LyubomirT/intense-rp-next")
#         update_window.destroy()
#         print("Github link opened.")
#     except Exception as e:
#         print(f"Error opening github: {e}")

# =============================================================================================================================
# Root Window
# =============================================================================================================================

def on_close_root() -> None:
    global root, storage_manager
    state = get_state_manager()
    
    try:
        # Restore console streams using console manager
        if hasattr(state, 'console_manager') and state.console_manager:
            state.console_manager.cleanup()
        else:
            # Fallback to manual restoration
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

        api.close_selenium()
        process.kill_driver_processes()

        temp_files = storage_manager.get_temp_files()
        if temp_files:
            for file in temp_files:
                storage_manager.delete_file("temp", file)

        if root:
            root.destroy()

        print("The program was successfully closed.")
    except Exception as e:
        print(f"Error closing root: {e}")

def get_icon_path():
    """Get appropriate icon path for current platform"""
    icon_path = None
    
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        exe_dir = os.path.dirname(sys.executable)
        if sys.platform.startswith('win'):
            icon_path = os.path.join(exe_dir, "newlogo.ico")
        else:
            icon_path = os.path.join(exe_dir, "newlogo.xbm")
            # Fallback to .ico if .xbm doesn't exist
            if not os.path.exists(icon_path):
                icon_path = os.path.join(exe_dir, "newlogo.ico")
    
    # Fallback to storage manager
    if not icon_path or not os.path.exists(icon_path):
        if sys.platform.startswith('win'):
            icon_path = storage_manager.get_existing_path(path_root="base", relative_path="newlogo.ico")
        else:
            icon_path = storage_manager.get_existing_path(path_root="base", relative_path="newlogo.xbm")
            # Fallback to .ico if .xbm doesn't exist
            if not icon_path:
                icon_path = storage_manager.get_existing_path(path_root="base", relative_path="newlogo.ico")
    
    return icon_path

def create_gui() -> None:
    global __version__, root, storage_manager, config_manager, icon_path
    state = get_state_manager()
    
    try:
        # Initialize storage manager and config system
        import utils.storage_manager as storage
        import utils.logging_manager as logging_manager
        
        storage_manager = storage.StorageManager()
        
        # Initialize new config system
        config_manager = ConfigManager(storage_manager)
        
        logging_manager_instance = logging_manager.LoggingManager(storage_manager)
        
        # Try to find icon file
        icon_path = get_icon_path()

        # Set up state manager with config manager
        state.set_config_manager(config_manager)
        state.logging_manager = logging_manager_instance

        # Configure external dependencies
        deepseek.manager = storage_manager
        response_utils.__version__ = __version__
        
        gui_builder.apply_appearance()
        root = gui_builder.RootWindow()
        root.create(
            title=f"INTENSE RP NEXT V{__version__}",
            width=400,
            height=500,
            min_width=250,
            min_height=250,
            icon=icon_path
        )
        
        root.grid_columnconfigure(0, weight=1)
        root.protocol("WM_DELETE_WINDOW", on_close_root)
        root.center()
        
        root.create_title(id="title", text=f"INTENSE RP NEXT V{__version__}", row=0)
        textbox = root.create_textbox(id="textbox", row=1, row_grid=True, bg_color="#272727")
        
        # Create start/stop button - initial text will be updated by observer
        initial_button_text = "Stop" if state.driver else "Start"
        root.create_button(id="start", text=initial_button_text, command=toggle_services, row=2)
        root.create_button(id="settings", text="Settings", command=open_config_window, row=3)
        root.create_button(id="credits", text="Credits", command=open_credits, row=4)
        
        textbox.add_colors()
        
        # Update state with UI components
        state.textbox = textbox
        
        # Subscribe to state changes for button updates
        state.subscribe(update_start_button_state)
        
        # Create console window after config is loaded
        create_console_window()
        
        # Initialize logging with config data
        logging_manager_instance.initialize(config_manager.get_all())
        
        if config_manager.get("check_version", True):
            current_version = version.parse(__version__)
            last_version = storage_manager.get_latest_version()
            if last_version and version.parse(last_version) > current_version:
            # Just for debugging, I occasionally switch between these
            # if last_version == "1.3.2":
                root.after(200, lambda: create_update_window(last_version))
        
        # Show console if configured to do so
        if config_manager.get("show_console", False) and hasattr(state, 'console_manager') and state.console_manager:
            root.after(100, lambda: state.console_manager.show(True, root, center=True))
        
        # Check for first start and show welcome screen if needed
        def show_welcome_if_first_start():
            try:
                welcome_manager = WelcomeManager(storage_manager)
                if welcome_manager.is_first_start():
                    # Create and show welcome window
                    welcome_window = WelcomeWindow(root, __version__, icon_path)
                    make_window_modal(welcome_window, root)
                    welcome_window.center()
                    welcome_window.lift()
                    welcome_window.focus()
                    
                    # Mark as returning user
                    welcome_manager.mark_as_returning()
                    print("Welcome screen shown for first-time user")
                else:
                    print("Returning user detected - welcome screen skipped")
            except Exception as e:
                print(f"Error handling welcome screen: {e}")
        
        # Show welcome screen after a short delay to ensure main window is ready
        root.after(300, show_welcome_if_first_start)
        
        print("Main window created with new modular config system.")
        print(f"Executable path: {storage_manager.get_executable_path()}")
        print(f"Base path: {storage_manager.get_base_path()}")
        
        root.mainloop()
    except Exception as e:
        print(f"Error creating GUI: {e}")