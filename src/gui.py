import threading, webbrowser, api, sys, re, platform, tkinter as tk
import utils.response_utils as response_utils
import utils.deepseek_driver as deepseek
import utils.storage_manager as storage
import utils.process_manager as process
import utils.gui_builder as gui_builder
import utils.logging_manager as logging_manager
from packaging import version
from core import get_state_manager, StateEvent

__version__ = "2.7.0"

# Local GUI state (not shared across modules)
root = None
storage_manager = None
icon_path = None

# Original config template
original_config = {
    "browser": "Chrome",
    "model": "DeepSeek",
    "check_version": True,
    "show_ip": False,
    "show_console": False,
    "models": {
        "deepseek": {
            "email": "",
            "password": "",
            "auto_login": False,
            "text_file": False,
            "deepthink": False,
            "search": False
        }
    },
    "logging": {
        "enabled": False,
        "max_file_size": 1048576,  # 1MB in bytes
        "max_files": 10
    }
}

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
        
        # UNFORTUNATELY, this also means that all of the normal built-in modal behaviors
        # ... now must be written manually. Tell Microsoft I want to have my cake and eat it too.
        # - Lyubomir
        #
        #
        # If you're reading this, it's likely I've been hunted down by Microsoft for this comment.
        parent_window.bind("<FocusIn>", on_parent_focus)
        
        # Store the binding so we can clean it up later
        setattr(window, '_parent_focus_binding', on_parent_focus)
        setattr(window, '_parent_window', parent_window)
        
        # Override destroy to clean up bindings
        original_destroy = window.destroy
        def cleanup_and_destroy():
            try:
                if hasattr(window, '_parent_window') and hasattr(window, '_parent_focus_binding'):
                    getattr(window, '_parent_window').unbind("<FocusIn>", getattr(window, '_parent_focus_binding'))
            except (AttributeError, tk.TclError):
                pass
            original_destroy()
        
        window.destroy = cleanup_and_destroy
    
    # Common modal setup
    window.focus_force()
    window.lift()

# =============================================================================================================================
# Console Window
# =============================================================================================================================

class ConsoleRedirector:
    def __init__(self, callback):
        self.callback = callback

    def write(self, text):
        if text and text.strip():
            try:
                self.callback(text.rstrip('\n')) 
            except Exception:
                pass
    
    def flush(self):
        pass

def create_console_window() -> None:
    state = get_state_manager()
    
    try:
        console_window = gui_builder.ConsoleWindow()
        console_window.create(
            visible=False,
            title="Console Output",
            width=700,
            height=400,
            min_width=400,
            min_height=250,
            icon=icon_path
        )
        console_window.protocol("WM_DELETE_WINDOW", lambda: None)
        console_textbox = console_window.create_textbox("console_window")
        
        # Update state
        state.console_window = console_window
        
        try:
            # Use colored_add for console output to support color formatting
            sys.stdout = ConsoleRedirector(console_textbox.colored_add)
            sys.stderr = ConsoleRedirector(lambda text: console_textbox.colored_add(f"[color:red]{text}"))
        except Exception:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

        print("[color:green]Console window created and ready.")
    except Exception as e:
        print(f"Error creating console window: {e}")

def start_services() -> None:
    state = get_state_manager()
    
    try:
        state.clear_messages()
        state.show_message("[color:green]Please wait...")
        threading.Thread(target=api.run_services, daemon=True).start()
    except Exception as e:
        state.clear_messages()
        state.show_message("[color:red]Selenium failed to start.")
        print(f"Error starting services: {e}")

# =============================================================================================================================
# Config Window
# =============================================================================================================================

def on_console_toggle(value: bool) -> None:
    state = get_state_manager()
    
    try:
        if state.console_window:
            state.console_window.show(show=value, root=root, center=True)
    except Exception as e:
        print(f"Error when toggling console visibility: {e}")

def format_file_size(size_bytes: int) -> str:
    """Convert bytes to human readable format"""
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes // (1024 * 1024)} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes // 1024} KB"
    else:
        return f"{size_bytes} B"

def parse_file_size(size_str: str) -> int:
    """Convert human readable size to bytes"""
    try:
        size_str = size_str.strip().upper()
        if size_str.endswith('MB'):
            return int(float(size_str[:-2].strip()) * 1024 * 1024)
        elif size_str.endswith('KB'):
            return int(float(size_str[:-2].strip()) * 1024)
        elif size_str.endswith('B'):
            return int(size_str[:-1].strip())
        else:
            # Assume bytes if no unit
            return int(size_str)
    except (ValueError, IndexError):
        return 1048576  # Default 1MB

def open_config_window() -> None:
    global root
    state = get_state_manager()
    
    try:
        config_window = gui_builder.ConfigWindow()
        config_window.create(
            visible=True,
            title="Settings",
            width=750,
            height=500,
            min_width=650,
            min_height=450,
            icon=icon_path
        )
        # Use cross-platform modal approach that preserves Mica on Windows
        make_window_modal(config_window, root)
        config_window.center(root)

        # Update state
        state.config_window = config_window

        # Get current config
        config = state.config

        # Create DeepSeek Settings section
        deepseek_model = config["models"]["deepseek"]
        deepseek_frame = config_window.create_section_frame(
            id="deepseek_frame",
            title="DeepSeek Settings",
            bg_color=("white", "gray20")
        )

        deepseek_frame.create_title(id="deepseek_settings", text="DeepSeek Settings", row=0, row_grid=True)
        deepseek_frame.create_entry(id="email", label_text="Email:", default_value=deepseek_model["email"], row=1, row_grid=True)
        deepseek_frame.create_password(id="password", label_text="Password:", default_value=deepseek_model["password"], row=2, row_grid=True)
        deepseek_frame.create_switch(id="auto_login", label_text="Auto login:", default_value=deepseek_model["auto_login"], row=3, row_grid=True)
        deepseek_frame.create_switch(id="text_file", label_text="Text file:", default_value=deepseek_model["text_file"], row=4, row_grid=True)
        deepseek_frame.create_switch(id="deepthink", label_text="Deepthink:", default_value=deepseek_model["deepthink"], row=5, row_grid=True)
        deepseek_frame.create_switch(id="search", label_text="Search:", default_value=deepseek_model["search"], row=6, row_grid=True)
        
        # Create Logging Settings section
        logging_config = config["logging"]
        logging_frame = config_window.create_section_frame(
            id="logging_frame",
            title="Logging Settings",
            bg_color=("white", "gray20")
        )
        
        logging_frame.create_title(id="logging_settings", text="Logging Settings", row=0, row_grid=True)
        logging_frame.create_switch(id="enabled", label_text="Store logfiles:", default_value=logging_config["enabled"], row=1, row_grid=True)
        logging_frame.create_entry(id="max_file_size", label_text="Max file size:", default_value=format_file_size(logging_config["max_file_size"]), row=2, row_grid=True)
        logging_frame.create_entry(id="max_files", label_text="Max files:", default_value=str(logging_config["max_files"]), row=3, row_grid=True)
        
        # Create Advanced Settings section
        advanced_frame = config_window.create_section_frame(
            id="advanced_frame",
            title="Advanced Settings",
            bg_color=("white", "gray20")
        )

        advanced_frame.create_title(id="advanced_settings", text="Advanced Settings", row=0, row_grid=True)
        advanced_frame.create_option_menu(id="browser", label_text="Browser:", default_value=config["browser"], options=["Chrome", "Firefox", "Edge", "Safari"], row=1, row_grid=True)
        advanced_frame.create_switch(id="check_version", label_text="Check version at startup:", default_value=config["check_version"], row=2, row_grid=True)
        advanced_frame.create_switch(id="show_console", label_text="Show Console:", default_value=config["show_console"], command=on_console_toggle, row=3, row_grid=True)
        advanced_frame.create_switch(id="show_ip", label_text="Show IP:", default_value=config["show_ip"], row=4, row_grid=True)
        
        # Create button section
        button_container = config_window.create_button_section()
        button_container.grid_columnconfigure(0, weight=1)
        button_container.grid_columnconfigure(1, weight=1)

        save_button = gui_builder.ctk.CTkButton(
            button_container, 
            text="Save", 
            command=lambda: save_config(config_window, deepseek_frame, logging_frame, advanced_frame),
            width=80
        )
        save_button.grid(row=0, column=0, padx=5, pady=5, sticky="e")

        cancel_button = gui_builder.ctk.CTkButton(
            button_container, 
            text="Cancel", 
            command=config_window.destroy,
            width=80
        )
        cancel_button.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Set initial active section
        config_window.set_active_section("deepseek_frame")

        print("Settings window created with sidebar navigation.")
    except Exception as e:
        print(f"Error opening config window: {e}")

def save_config(
        config_window: gui_builder.ConfigWindow,
        deepseek_frame: gui_builder.ConfigFrame,
        logging_frame: gui_builder.ConfigFrame,
        advanced_frame: gui_builder.ConfigFrame
    ) -> None:
    try:
        global original_config
        state = get_state_manager()
        
        email_entry = deepseek_frame.get_widget("email")
        password_entry = deepseek_frame.get_widget("password")
        auto_login = deepseek_frame.get_widget_value("auto_login")
        
        def is_valid_email(email: str) -> bool:
            return re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email) is not None
        
        def is_valid_password(password: str, min_length: int = 6) -> bool:
            return len(password.strip()) >= min_length
        
        def set_entry_style(entry, valid: bool) -> None:
            entry.configure(border_color="gray" if valid else "red")
        
        # Validate email/password if auto_login is enabled
        if auto_login:
            valid_email = is_valid_email(email_entry.get())
            set_entry_style(email_entry, valid_email)
            
            valid_password = is_valid_password(password_entry.get())
            set_entry_style(password_entry, valid_password)

            if not valid_email or not valid_password:
                return
        else:
            set_entry_style(email_entry, True)
            set_entry_style(password_entry, True)

        # Validate logging settings
        max_file_size_entry = logging_frame.get_widget("max_file_size")
        max_files_entry = logging_frame.get_widget("max_files")
        
        try:
            max_file_size_bytes = parse_file_size(max_file_size_entry.get())
            set_entry_style(max_file_size_entry, True)
        except:
            set_entry_style(max_file_size_entry, False)
            return
            
        try:
            max_files_int = int(max_files_entry.get().strip())
            if max_files_int < 1 or max_files_int > 100:
                raise ValueError()
            set_entry_style(max_files_entry, True)
        except:
            set_entry_style(max_files_entry, False)
            return

        # Build new configuration
        new_config = {
            "browser": advanced_frame.get_widget_value("browser"),
            "check_version": advanced_frame.get_widget_value("check_version"),
            "show_console": advanced_frame.get_widget_value("show_console"),
            "show_ip": advanced_frame.get_widget_value("show_ip"),
            "models": {
                "deepseek": {
                    "email": deepseek_frame.get_widget_value("email"),
                    "password": deepseek_frame.get_widget_value("password"),
                    "auto_login": deepseek_frame.get_widget_value("auto_login"),
                    "text_file": deepseek_frame.get_widget_value("text_file"),
                    "deepthink": deepseek_frame.get_widget_value("deepthink"),
                    "search": deepseek_frame.get_widget_value("search")
                }
            },
            "logging": {
                "enabled": logging_frame.get_widget_value("enabled"),
                "max_file_size": max_file_size_bytes,
                "max_files": max_files_int
            }
        }
        
        # Save configuration
        storage_manager.save_config(path_root="executable", sub_path="save", new=new_config, original=original_config)
        state.set_config(new_config)
        
        # Reinitialize logging with new settings
        if state.logging_manager:
            state.logging_manager.initialize(new_config)
        
        config_window.destroy()
        print("The config window was closed successfully.")
    except Exception as e:
        print(f"Error saving config: {e}")

# =============================================================================================================================
# Credits
# =============================================================================================================================

def open_credits() -> None:
    try:
        webbrowser.open("https://linktr.ee/omega_slender")
        print("Credits link opened.")
    except Exception as e:
        print(f"Error opening credits: {e}")

# =============================================================================================================================
# Update Window
# =============================================================================================================================

def create_update_window(last_version: str) -> None:
    global root, icon_path
    try:
        update_window = gui_builder.UpdateWindow()
        update_window.create(
            visible=True,
            title=f"New version available",
            width=250,
            height=110,
            icon=icon_path
        )
        update_window.resizable(False, False)
        # Use cross-platform modal approach that preserves Mica on Windows
        make_window_modal(update_window, root)
        update_window.center(root)
        update_window.grid_columnconfigure(0, weight=1)

        update_window.create_title(id="title", text=f"VERSION {last_version} AVAILABLE", row=0, row_grid=True)
        update_window.create_button(id="download", text="Download", command=lambda: open_github(update_window), row=1, row_grid=True)
        update_window.create_button(id="close", text="Close", command=update_window.destroy, row=2, row_grid=True)

        print("Update window created.")
    except Exception as e:
        print(f"Error opening update window: {e}")

def open_github(update_window: gui_builder.UpdateWindow) -> None:
    try:
        webbrowser.open("https://github.com/omega-slender/intense-rp-api")
        update_window.destroy()
        print("Github link opened.")
    except Exception as e:
        print(f"Error opening github: {e}")

# =============================================================================================================================
# Root Window
# =============================================================================================================================

def on_close_root() -> None:
    global root, storage_manager
    state = get_state_manager()
    
    try:
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

def create_gui() -> None:
    global __version__, root, storage_manager, icon_path
    state = get_state_manager()
    
    try:
        # Initialize local managers
        storage_manager = storage.StorageManager()
        logging_manager_instance = logging_manager.LoggingManager(storage_manager)
        icon_path = storage_manager.get_existing_path(path_root="base", relative_path="icon.ico")

        # Set up state manager
        state.logging_manager = logging_manager_instance

        # Configure external dependencies
        deepseek.manager = storage_manager
        response_utils.__version__ = __version__
        
        gui_builder.apply_appearance()
        root = gui_builder.RootWindow()
        root.create(
            title=f"INTENSE RP API V{__version__}",
            width=400,
            height=500,
            min_width=250,
            min_height=250,
            icon=icon_path
        )
        
        root.grid_columnconfigure(0, weight=1)
        root.protocol("WM_DELETE_WINDOW", on_close_root)
        root.center()
        
        root.create_title(id="title", text=f"INTENSE RP API V{__version__}", row=0)
        textbox = root.create_textbox(id="textbox", row=1, row_grid=True, bg_color="#272727")
        root.create_button(id="start", text="Start", command=start_services, row=2)
        root.create_button(id="settings", text="Settings", command=open_config_window, row=3)
        root.create_button(id="credits", text="Credits", command=open_credits, row=4)
        
        textbox.add_colors()
        
        # Update state with UI components
        state.textbox = textbox
        
        create_console_window()
        
        # Load and set configuration
        config = storage_manager.load_config(path_root="executable", sub_path="save", original=original_config)
        state.set_config(config)
        
        # Initialize logging
        logging_manager_instance.initialize(config)
        
        if config["check_version"]:
            current_version = version.parse(__version__)
            last_version = storage_manager.get_latest_version()
            if last_version and version.parse(last_version) > current_version:
                root.after(200, lambda: create_update_window(last_version))
        
        if state.console_window and config["show_console"]:
            root.after(100, lambda: state.console_window.show(show=config["show_console"], root=root, center=True))
        
        print("Main window created.")
        print(f"Executable path: {storage_manager.get_executable_path()}")
        print(f"Base path: {storage_manager.get_base_path()}")
        
        root.mainloop()
    except Exception as e:
        print(f"Error creating GUI: {e}")