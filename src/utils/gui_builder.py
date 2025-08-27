from typing import Optional, List, Callable
import customtkinter as ctk
import re
import json
import webbrowser
import os
import sys
import platform
from utils.font_loader import get_font_tuple
from utils import storage_manager
from PIL import Image, ImageDraw
import requests
from io import BytesIO
import threading

# ============================================================================================================================
# Cross-Platform GUI Utilities
# ============================================================================================================================

def set_window_icon(window, icon_path: Optional[str]) -> None:
    """
    Set window icon in a cross-platform way.
    Uses .ico files on Windows and PNG files with iconphoto() on Linux.
    """
    if not icon_path:
        return
        
    try:
        if sys.platform.startswith('win'):
            # Windows - use .ico file with iconbitmap
            if icon_path.endswith('.ico') and os.path.exists(icon_path):
                window.iconbitmap(icon_path)
                return
            elif icon_path.endswith(('.xbm', '.png')):
                # Convert path to .ico for Windows
                ico_path = icon_path.replace('.xbm', '.ico').replace('.png', '.ico')
                if os.path.exists(ico_path):
                    window.iconbitmap(ico_path)
                    return
        else:
            # Linux/Unix - prefer iconphoto with PNG for better compatibility
            png_candidates = []
            
            if icon_path.endswith('.ico'):
                png_candidates = [
                    icon_path.replace('.ico', '.png'),
                    icon_path.replace('.ico', '.xbm')
                ]
            elif icon_path.endswith('.xbm'):
                png_candidates = [
                    icon_path.replace('.xbm', '.png'),
                    icon_path
                ]
            elif icon_path.endswith('.png'):
                png_candidates = [icon_path]
            
            # Try PNG first (most reliable on Linux)
            for candidate in png_candidates:
                if candidate.endswith('.png') and os.path.exists(candidate):
                    try:
                        import tkinter as tk
                        photo = tk.PhotoImage(file=candidate)
                        window.iconphoto(False, photo)
                        return
                    except Exception as png_error:
                        print(f"Failed to load PNG icon {candidate}: {png_error}")
                        continue
            
            # Fallback to XBM with iconbitmap (less reliable but worth trying)
            for candidate in png_candidates:
                if candidate.endswith('.xbm') and os.path.exists(candidate):
                    try:
                        # Validate XBM file format first
                        with open(candidate, 'r') as f:
                            content = f.read()
                            if '#define' in content and 'static' in content:
                                window.iconbitmap(candidate)
                                return
                            else:
                                print(f"Invalid XBM format in file: {candidate}")
                    except Exception as xbm_error:
                        print(f"Failed to load XBM icon {candidate}: {xbm_error}")
                        continue
                
    except Exception as e:
        print(f"Could not set window icon: {e}")

# =============================================================================================================================
# Simple Tooltip Implementation
# =============================================================================================================================

class SimpleTooltip:
    """Simple tooltip implementation for CustomTkinter widgets"""
    
    def __init__(self, widget: ctk.CTkBaseClass, text: str, delay: int = 500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window = None
        self.show_timer = None
        
        # Bind hover events
        self.widget.bind("<Enter>", self._on_enter)
        self.widget.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, event=None):
        """Mouse entered widget"""
        self._cancel_timer()
        self.show_timer = self.widget.after(self.delay, self._show_tooltip)
    
    def _on_leave(self, event=None):
        """Mouse left widget"""
        self._cancel_timer()
        self._hide_tooltip()
    
    def _cancel_timer(self):
        """Cancel pending tooltip display"""
        if self.show_timer:
            self.widget.after_cancel(self.show_timer)
            self.show_timer = None
    
    def _show_tooltip(self):
        """Display the tooltip"""
        if self.tooltip_window:
            return
        
        # Get widget position
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        # Create tooltip window
        self.tooltip_window = ctk.CTkToplevel()
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.geometry(f"+{x}+{y}")
        
        # Create tooltip label with modern styling
        label = ctk.CTkLabel(
            self.tooltip_window,
            text=self.text,
            corner_radius=6,
            fg_color=("gray90", "gray20"),
            text_color=("gray10", "gray90"),
            font=get_font_tuple("Blinker", 12)
        )
        label.pack(padx=8, pady=4)
        
        # Keep tooltip on top but don't steal focus
        self.tooltip_window.lift()
        self.tooltip_window.attributes('-topmost', True)
    
    def _hide_tooltip(self):
        """Hide the tooltip"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

def create_tooltip(widget: ctk.CTkBaseClass, text: str) -> Optional[SimpleTooltip]:
    """Create a tooltip for a widget if text is provided"""
    if text and text.strip():
        return SimpleTooltip(widget, text.strip())
    return None

# =============================================================================================================================
# Configuration Constants
# =============================================================================================================================

class UIConstants:
    SIDEBAR_WIDTH = 220
    SIDEBAR_SCROLLABLE_WIDTH = 190
    SIDEBAR_TITLE_HEIGHT = 60
    
    BUTTON_HEIGHT = 35
    BUTTON_SPACING = 4
    BUTTON_CORNER_RADIUS = 8
    
    MIN_BUTTONS_FOR_OVERFLOW = 3
    OVERFLOW_CHECK_DELAY = 10
    
    PADDING_SMALL = 5
    PADDING_MEDIUM = 10
    PADDING_LARGE = 15
    
    WEIGHT_NONE = 0
    WEIGHT_FULL = 1
    
    SCROLL_UNITS_PER_WHEEL = 2

# =============================================================================================================================
# Rows and Columns Utils
# =============================================================================================================================

def _set_row_grid(obj: ctk.CTkBaseClass, row: int) -> None:
    obj.grid_rowconfigure(row, weight=UIConstants.WEIGHT_FULL)

# =============================================================================================================================
# Widget Utils
# =============================================================================================================================

def _save_widget(obj: ctk.CTkBaseClass, widget_id: str, widget: ctk.CTkBaseClass) -> None:
    if not hasattr(obj, "_widgets"):
        obj._widgets = {}
    obj._widgets[widget_id] = widget

def _get_widget(obj: ctk.CTkBaseClass, widget_id: str) -> Optional[ctk.CTkBaseClass]:
    return getattr(obj, "_widgets", {}).get(widget_id)

def _get_widget_value(obj: ctk.CTkBaseClass, widget_id: str) -> Optional[str]:
    widget = getattr(obj, "_widgets", {}).get(widget_id)
    if widget and hasattr(widget, "get"):
        # Handle CTkTextbox widgets differently
        if isinstance(widget, ctk.CTkTextbox):
            return widget.get("0.0", "end").rstrip('\n')  # Remove trailing newline
        else:
            return widget.get()
    return None

# =============================================================================================================================
# Frame Utils
# =============================================================================================================================

def _save_frame(obj: ctk.CTkBaseClass, frame_id: str, frame: ctk.CTkFrame) -> None:
    if not hasattr(obj, "_frames"):
        obj._frames = {}
    obj._frames[frame_id] = frame

def _get_frame(obj: ctk.CTkBaseClass, frame_id: str) -> Optional[ctk.CTkFrame]:
    return getattr(obj, "_frames", {}).get(frame_id)

# =============================================================================================================================
# Parent Window Utils
# =============================================================================================================================

def _create_parent_window(
    parent: ctk.CTkToplevel,
    visible: bool,
    title: str,
    width: int,
    height: int,
    min_width: Optional[int] = None,
    min_height: Optional[int] = None,
    icon: Optional[str] = None
) -> None:
    parent.title(title)
    
    if visible:
        parent.geometry(f"{width}x{height}")
        if min_width or min_height:
            parent.minsize(min_width or 0, min_height or 0)
        if icon:
            parent.after(200, lambda: set_window_icon(parent, icon))
    else:
        parent.withdraw()

def _center_parent_window(parent: ctk.CTkToplevel, root: ctk.CTk, width: Optional[int] = None, height: Optional[int] = None) -> None:
    root.update_idletasks()
    parent.update_idletasks()
    
    width = width or parent.winfo_width()
    height = height or parent.winfo_height()
    x = root.winfo_x() + (root.winfo_width() - width) // 2
    y = root.winfo_y() + (root.winfo_height() - height) // 2
    parent.geometry(f"{width}x{height}+{x}+{y}")

# =============================================================================================================================
# Textbox Widget
# =============================================================================================================================

class CustomTextbox(ctk.CTkTextbox):
    def _ensure_max_lines(self, max_lines: int = 500) -> None:
        self.update_idletasks()
        total_lines = int(self.index("end-1c").split('.')[0])
        if total_lines > max_lines:
            self.delete("1.0", f"{total_lines - max_lines + 1}.0")

    def add_colors(self) -> None:
        self._color_map = {
            "red": "#ff6b6b",
            "green": "#51cf66", 
            "yellow": "#ffd43b",
            "blue": "#74c0fc",
            "cyan": "#66d9ef",
            "white": "#f8f9fa",
            "purple": "#d084f5",
            "orange": "#ff8c42",
            "pink": "#f783ac",
            "gray": "#adb5bd"
        }
        for tag, color in self._color_map.items():
            self.tag_config(tag, foreground=color)
    
    def clear(self) -> None:
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.configure(state="disabled")

    def colored_add(self, text: str) -> None:
        """Add colored text to textbox (improved for console output)"""
        if not text:
            return
            
        pattern = r'\[color:(\w+)\]'
        parts = re.split(pattern, text)
        current_tag = "white"

        self.configure(state="normal")
        self._ensure_max_lines()

        for i, part in enumerate(parts):
            if i % 2 == 0:
                if part:
                    self.insert("end", part, current_tag)
            else:
                tag = part.lower()
                current_tag = tag if hasattr(self, "_color_map") and tag in self._color_map else "white"

        # Only add newline if the text doesn't already end with one
        if not text.endswith('\n'):
            self.insert("end", "\n")
        
        self.configure(state="disabled")
        self.see("end")

    def add(self, text: str) -> None:
        self.configure(state="normal")
        self._ensure_max_lines()
        self.insert("end", text)
        self.configure(state="disabled")
        self.see("end")

# =============================================================================================================================
# Root Window
# =============================================================================================================================

def apply_appearance() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

class RootWindow(ctk.CTk):
    def create(
        self,
        title: str,
        width: int,
        height: int,
        min_width: Optional[int] = None,
        min_height: Optional[int] = None,
        icon: Optional[str] = None
    ) -> None:
        self._last_title = title
        self._last_width = width
        self._last_height = height
        self._last_min_width = min_width
        self._last_min_height = min_height
        self._last_icon = icon

        self.title(title)
        self.geometry(f"{width}x{height}")
        if min_width or min_height:
            self.minsize(min_width or 0, min_height or 0)
        
        if icon:
            set_window_icon(self, icon)

    def center(self) -> None:
        self.update_idletasks()

        width = self._last_width or self.winfo_width()
        height = self._last_height or self.winfo_height()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        self.geometry(f"{width}x{height}+{x}+{y}")

    def get_widget(self, id: str) -> Optional[ctk.CTkBaseClass]:
        return _get_widget(self, id)

    def get_widget_value(self, id: str) -> Optional[str]:
        return _get_widget_value(self, id)

    def create_title(self, id: str, text: str, row: int = 0, column: int = 0, row_grid: bool = False) -> ctk.CTkLabel:
        label = ctk.CTkLabel(self, text=text, font=get_font_tuple("Blinker", 20, "bold"))
        label.grid(row=row, column=column, padx=UIConstants.PADDING_MEDIUM, pady=(UIConstants.PADDING_MEDIUM, 0), sticky="nsew")

        if row_grid:
            _set_row_grid(self, row)

        _save_widget(self, id, label)
        return label
    
    def create_textbox(self, id: str, row: int = 0, column: int = 0, row_grid: bool = False, bg_color: Optional[str]= None) -> CustomTextbox:
        textbox = CustomTextbox(self, state="disabled", font=get_font_tuple("Blinker", 16), wrap="none", fg_color=bg_color)
        textbox.grid(row=row, column=column, padx=UIConstants.PADDING_MEDIUM, pady=UIConstants.PADDING_MEDIUM, sticky="nsew")

        if row_grid:
            _set_row_grid(self, row)

        _save_widget(self, id, textbox)
        return textbox

    def create_button(self, id: str, text: str, command: Optional[Callable] = None, row: int = 0, column: int = 0, row_grid: bool = False) -> ctk.CTkButton:
        button = ctk.CTkButton(self, text=text, command=command, font=get_font_tuple("Blinker", 14))
        button.grid(row=row, column=column, padx=UIConstants.PADDING_MEDIUM, pady=(0, UIConstants.PADDING_MEDIUM), sticky="ew")

        if row_grid:
            _set_row_grid(self, row)

        _save_widget(self, id, button)
        return button

# =============================================================================================================================
# Config Window
# =============================================================================================================================

class ConfigFrame(ctk.CTkFrame):
    def get_widget(self, id: str) -> Optional[ctk.CTkBaseClass]:
        return _get_widget(self, id)
    
    def get_widget_value(self, id: str) -> Optional[str]:
        return _get_widget_value(self, id)
    
    def create_title(self, id: str, text: str, row: int = 0, row_grid: bool = False) -> ctk.CTkLabel:
        label = ctk.CTkLabel(self, text=text, font=get_font_tuple("Blinker", 16, "bold"))
        label.grid(row=row, column=0, columnspan=2, padx=UIConstants.PADDING_LARGE, pady=(UIConstants.PADDING_LARGE, UIConstants.PADDING_MEDIUM), sticky="w")

        if row_grid:
            _set_row_grid(self, row)

        _save_widget(self, id, label)
        return label

    def create_entry(self, id: str, label_text: str, default_value: str, row: int = 0, row_grid: bool = False, tooltip: Optional[str] = None) -> ctk.CTkEntry:
        ctk.CTkLabel(self, text=label_text, font=get_font_tuple("Blinker", 14)).grid(row=row, column=0, padx=UIConstants.PADDING_LARGE, pady=8, sticky="w")
        entry = ctk.CTkEntry(self, width=300, border_color="gray", font=get_font_tuple("Blinker", 14))
        entry.grid(row=row, column=1, padx=UIConstants.PADDING_LARGE, pady=8, sticky="ew")
        entry.insert(0, default_value)

        if row_grid:
            _set_row_grid(self, row)

        # Add tooltip if provided
        if tooltip:
            create_tooltip(entry, tooltip)

        _save_widget(self, id, entry)
        return entry

    def create_password(self, id: str, label_text: str, default_value: str, row: int = 0, row_grid: bool = False, tooltip: Optional[str] = None) -> ctk.CTkEntry:
        ctk.CTkLabel(self, text=label_text, font=get_font_tuple("Blinker", 14)).grid(row=row, column=0, padx=UIConstants.PADDING_LARGE, pady=8, sticky="w")
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=row, column=1, padx=UIConstants.PADDING_LARGE, pady=8, sticky="ew")
        frame.grid_columnconfigure(0, weight=UIConstants.WEIGHT_FULL)

        # Create entry without show parameter initially to insert the actual text
        entry = ctk.CTkEntry(frame, border_color="gray", font=get_font_tuple("Blinker", 14))
        entry.grid(row=0, column=0, padx=(0, UIConstants.PADDING_SMALL), sticky="ew")
        entry.insert(0, default_value)
        
        # Now configure to hide the password
        entry.configure(show="*")
        
        def toggle():
            show_state = entry.cget("show")
            if show_state == "*":
                # Currently hidden, show the password
                entry.configure(show="")
                toggle_btn.configure(text="Hide")
            else:
                # Currently visible, hide the password
                entry.configure(show="*")
                toggle_btn.configure(text="Show")

        toggle_btn = ctk.CTkButton(frame, text="Show", width=60, command=toggle, font=get_font_tuple("Blinker", 12))
        toggle_btn.grid(row=0, column=1, sticky="e")

        if row_grid:
            _set_row_grid(self, row)

        # Add tooltip if provided
        if tooltip:
            create_tooltip(entry, tooltip)

        _save_widget(self, id, entry)
        return entry

    def create_switch(self, id: str, label_text: str, default_value: bool, command: Callable[[bool], None] = None, row: int = 0, row_grid: bool = False, tooltip: Optional[str] = None) -> ctk.CTkSwitch:
        ctk.CTkLabel(self, text=label_text, font=get_font_tuple("Blinker", 14)).grid(row=row, column=0, padx=UIConstants.PADDING_LARGE, pady=8, sticky="w")
        var = ctk.BooleanVar(value=default_value)
        switch = ctk.CTkSwitch(self, variable=var, text="", font=get_font_tuple("Blinker", 14))
        switch.grid(row=row, column=1, padx=UIConstants.PADDING_LARGE, pady=8, sticky="w")

        if command:
            switch.configure(command=lambda: command(var.get()))

        if row_grid:
            _set_row_grid(self, row)

        # Add tooltip if provided
        if tooltip:
            create_tooltip(switch, tooltip)

        _save_widget(self, id, switch)
        return switch

    def create_option_menu(self, id: str, label_text: str, default_value: str, options: List[str], row: int = 0, row_grid: bool = False, tooltip: Optional[str] = None) -> ctk.CTkOptionMenu:
        ctk.CTkLabel(self, text=label_text, font=get_font_tuple("Blinker", 14)).grid(row=row, column=0, padx=UIConstants.PADDING_LARGE, pady=8, sticky="w")
        var = ctk.StringVar(value=default_value)
        menu = ctk.CTkOptionMenu(self, variable=var, values=options, font=get_font_tuple("Blinker", 14))
        menu.grid(row=row, column=1, padx=UIConstants.PADDING_LARGE, pady=8, sticky="ew")

        if row_grid:
            _set_row_grid(self, row)

        # Add tooltip if provided
        if tooltip:
            create_tooltip(menu, tooltip)

        _save_widget(self, id, menu)
        return menu
    
    def create_button(self, id: str, text: str, command: Optional[Callable] = None, row: int = 0, column: int = 0, row_grid: bool = False, tooltip: Optional[str] = None) -> ctk.CTkButton:        
        button = ctk.CTkButton(self, text=text, command=command, font=get_font_tuple("Blinker", 14))
        button.grid(row=row, column=column, padx=8, pady=UIConstants.PADDING_SMALL, sticky="ew")

        if row_grid:
            _set_row_grid(self, row)

        # Add tooltip if provided
        if tooltip:
            create_tooltip(button, tooltip)

        _save_widget(self, id, button)
        return button
    
    def create_textarea(self, id: str, label_text: str, default_value: str, row: int = 0, row_grid: bool = False, tooltip: Optional[str] = None) -> ctk.CTkTextbox:
        """Create a multi-line text area widget"""
        ctk.CTkLabel(self, text=label_text, font=get_font_tuple("Blinker", 14)).grid(row=row, column=0, padx=UIConstants.PADDING_LARGE, pady=8, sticky="nw")
        
        textbox = ctk.CTkTextbox(
            self, 
            width=300, 
            height=100, 
            border_color="gray",
            fg_color=("white", "gray17"),
            text_color=("black", "white"),
            font=get_font_tuple("Blinker", 14)
        )
        textbox.grid(row=row, column=1, padx=UIConstants.PADDING_LARGE, pady=8, sticky="ew")
        textbox.insert("0.0", default_value)

        if row_grid:
            _set_row_grid(self, row)

        # Add tooltip if provided
        if tooltip:
            create_tooltip(textbox, tooltip)

        _save_widget(self, id, textbox)
        return textbox

class SidebarNavButton(ctk.CTkButton):
    def __init__(self, parent, section_id: str, text: str, command: Callable, **kwargs):
        super().__init__(parent, text=text, command=command, **kwargs)
        self.section_id = section_id
        self._is_active = False
        self._configure_appearance()
    
    def _configure_appearance(self):
        """Configure the button's visual appearance"""
        self.configure(
            height=UIConstants.BUTTON_HEIGHT,
            corner_radius=UIConstants.BUTTON_CORNER_RADIUS,
            fg_color="transparent",
            text_color=("gray70", "gray70"),
            hover_color=("gray20", "gray20"),
            anchor="w",
            font=get_font_tuple("Blinker", 13)
        )
    
    def set_active(self, active: bool):
        self._is_active = active
        if active:
            self.configure(
                fg_color=("gray20", "gray20"),
                text_color=("white", "white")
            )
        else:
            self.configure(
                fg_color="transparent",
                text_color=("gray70", "gray70")
            )

class SidebarManager:
    """Manages sidebar creation, overflow detection, and button handling"""
    
    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.buttons = {}
        self.is_scrollable = False
        
    def calculate_required_height(self) -> int:
        """Calculate the height required for all sidebar buttons"""
        total_buttons = len(self.buttons)
        button_space = UIConstants.BUTTON_HEIGHT + UIConstants.BUTTON_SPACING
        return total_buttons * button_space
    
    def get_available_height(self) -> int:
        """Get the available height in the sidebar"""
        try:
            self.parent_window.update_idletasks()
            return self.parent_window.sidebar_container.winfo_height() - UIConstants.SIDEBAR_TITLE_HEIGHT
        except:
            return 0
    
    def should_use_scrollable(self) -> bool:
        """Determine if sidebar should be scrollable based on content"""
        if len(self.buttons) <= UIConstants.MIN_BUTTONS_FOR_OVERFLOW:
            return False
        
        required = self.calculate_required_height()
        available = self.get_available_height()
        return required > available
    
    def create_sidebar_button(self, parent, section_id: str, text: str, command: Callable) -> SidebarNavButton:
        """Create a sidebar navigation button with consistent styling"""
        button = SidebarNavButton(parent, section_id=section_id, text=text, command=command)
        row = len(self.buttons)
        button.grid(row=row, column=0, padx=UIConstants.PADDING_MEDIUM, pady=UIConstants.BUTTON_SPACING//2, sticky="ew")
        return button
    
    def recreate_buttons_in_parent(self, new_parent):
        """Recreate all buttons in a new parent widget"""
        button_data = [(sid, btn.cget("text"), btn.cget("command"), btn._is_active) 
                      for sid, btn in self.buttons.items()]
        
        self.buttons.clear()
        
        for section_id, text, command, was_active in button_data:
            button = self.create_sidebar_button(new_parent, section_id, text, command)
            self.buttons[section_id] = button
            if was_active:
                button.set_active(True)

class ConfigWindow(ctk.CTkToplevel):
    def create(
        self,
        visible: bool,
        title: str,
        width: int,
        height: int,
        min_width: Optional[int] = None,
        min_height: Optional[int] = None,
        icon: Optional[str] = None
    ) -> None:
        self._last_title = title
        self._last_width = width
        self._last_height = height
        self._last_min_width = min_width
        self._last_min_height = min_height
        self._last_icon = icon
        self._content_frames = {}

        _create_parent_window(self, visible, title, width, height, min_width, min_height, icon)
        
        self.sidebar_manager = SidebarManager(self)
        
        self.grid_columnconfigure(0, weight=UIConstants.WEIGHT_NONE)  # Sidebar - fixed width
        self.grid_columnconfigure(1, weight=UIConstants.WEIGHT_FULL)  # Content - expandable
        self.grid_rowconfigure(0, weight=UIConstants.WEIGHT_FULL)     # Main content area
        self.grid_rowconfigure(1, weight=UIConstants.WEIGHT_NONE)     # Button area
        
        self._create_layout()
    
    def _create_layout(self):
        """Create the main sidebar + content layout"""
        self._create_sidebar()
        self._create_content_area()
        self._create_button_area()
        self._setup_scrolling()
        
    def _create_sidebar(self):
        """Create the sidebar container and initial frame"""
        self.sidebar_container = ctk.CTkFrame(self, width=UIConstants.SIDEBAR_WIDTH, fg_color=("gray95", "gray10"))
        self.sidebar_container.grid(row=0, column=0, sticky="nsew", 
                                  padx=(UIConstants.PADDING_MEDIUM, UIConstants.PADDING_SMALL), 
                                  pady=UIConstants.PADDING_MEDIUM)
        self.sidebar_container.grid_propagate(False)
        self.sidebar_container.grid_columnconfigure(0, weight=UIConstants.WEIGHT_FULL)
        self.sidebar_container.grid_rowconfigure(1, weight=UIConstants.WEIGHT_FULL)
        
        # Sidebar title
        sidebar_title = ctk.CTkLabel(
            self.sidebar_container, 
            text="Settings", 
            font=get_font_tuple("Blinker", 16, "bold"),
            text_color=("gray10", "gray90")
        )
        sidebar_title.grid(row=0, column=0, padx=UIConstants.PADDING_LARGE, 
                          pady=(UIConstants.PADDING_LARGE, UIConstants.PADDING_MEDIUM), sticky="w")
        
        # Initial sidebar frame (non-scrollable)
        self._create_sidebar_frame(scrollable=False)
    
    def _create_sidebar_frame(self, scrollable: bool = False):
        """Create or recreate the sidebar frame (scrollable or not)"""
        if hasattr(self, 'sidebar_frame'):
            self.sidebar_frame.destroy()  # type: ignore
        
        if scrollable:
            self.sidebar_frame = ctk.CTkScrollableFrame(
                self.sidebar_container,
                width=UIConstants.SIDEBAR_SCROLLABLE_WIDTH,
                fg_color="transparent",
                scrollbar_button_color=("gray70", "gray30"),
                scrollbar_button_hover_color=("gray60", "gray40")
            )
        else:
            self.sidebar_frame = ctk.CTkFrame(self.sidebar_container, fg_color="transparent")
        
        self.sidebar_frame.grid(row=1, column=0, sticky="nsew", 
                               padx=UIConstants.PADDING_SMALL, 
                               pady=(0, UIConstants.PADDING_MEDIUM))
        self.sidebar_frame.grid_columnconfigure(0, weight=UIConstants.WEIGHT_FULL)
        
        self.sidebar_manager.is_scrollable = scrollable
    
    def _create_content_area(self):
        """Create the main content area"""
        self.content_frame = ctk.CTkFrame(self, fg_color=("gray96", "gray13"))
        self.content_frame.grid(row=0, column=1, sticky="nsew", 
                               padx=(UIConstants.PADDING_SMALL, UIConstants.PADDING_MEDIUM), 
                               pady=UIConstants.PADDING_MEDIUM)
        self.content_frame.grid_columnconfigure(0, weight=UIConstants.WEIGHT_FULL)
        self.content_frame.grid_rowconfigure(0, weight=UIConstants.WEIGHT_NONE)  # Search bar row
        self.content_frame.grid_rowconfigure(1, weight=UIConstants.WEIGHT_FULL)  # Content row
        
        # Create search bar
        self._create_search_bar()
        
        # Create scrollable frame for content
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self.content_frame,
            fg_color="transparent",
            scrollbar_button_color=("gray70", "gray30"),
            scrollbar_button_hover_color=("gray60", "gray40")
        )
        self.scrollable_frame.grid(row=1, column=0, sticky="nsew", 
                                  padx=UIConstants.PADDING_MEDIUM, 
                                  pady=(0, UIConstants.PADDING_MEDIUM))
        self.scrollable_frame.grid_columnconfigure(0, weight=UIConstants.WEIGHT_FULL)
    
    def _create_search_bar(self):
        """Create the search bar at the top of the content area"""
        search_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        search_frame.grid(row=0, column=0, sticky="ew", padx=UIConstants.PADDING_MEDIUM, pady=(UIConstants.PADDING_MEDIUM, UIConstants.PADDING_SMALL))
        search_frame.grid_columnconfigure(1, weight=UIConstants.WEIGHT_FULL)
        
        # Search icon/label
        search_label = ctk.CTkLabel(
            search_frame, 
            text="🔍", 
            font=get_font_tuple("Blinker", 16),
            text_color=("gray60", "gray40")
        )
        search_label.grid(row=0, column=0, padx=(0, UIConstants.PADDING_SMALL))
        
        # Search entry
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Search settings... (Press Enter to search)",
            font=get_font_tuple("Blinker", 14),
            border_color=("gray70", "gray30"),
            fg_color=("white", "gray20")
        )
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=(0, UIConstants.PADDING_SMALL))
        
        # Bind Enter key to search
        self.search_entry.bind("<Return>", self._on_search)
        
        # Clear search button
        clear_button = ctk.CTkButton(
            search_frame,
            text="×",
            width=30,
            height=30,
            font=get_font_tuple("Blinker", 16, "bold"),
            command=self._clear_search,
            fg_color=("gray80", "gray25"),
            hover_color=("gray70", "gray35"),
            text_color=("gray40", "gray60")
        )
        clear_button.grid(row=0, column=2)
    
    def _on_search(self, event=None):
        """Handle search when Enter is pressed"""
        search_term = self.search_entry.get().strip()
        if search_term:
            # Delegate search logic to the UI generator
            if hasattr(self, 'search_callback') and self.search_callback:
                self.search_callback(search_term)
    
    def _clear_search(self):
        """Clear the search entry"""
        self.search_entry.delete(0, "end")
    
    def set_search_callback(self, callback):
        """Set the search callback function"""
        self.search_callback = callback
    
    def _create_button_area(self):
        """Create the bottom button area"""
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.grid(row=1, column=0, columnspan=2, sticky="ew", 
                              padx=UIConstants.PADDING_MEDIUM, 
                              pady=(0, UIConstants.PADDING_MEDIUM))
        self.button_frame.grid_columnconfigure(0, weight=UIConstants.WEIGHT_FULL)
        
    def _setup_scrolling(self):
        """Setup mouse wheel scrolling for content area"""
        def mousewheel_handler(event):
            try:
                x, y = self.winfo_pointerxy()
                widget = self.winfo_containing(x, y)
                
                # Only scroll if over scrollable content and not over input widgets
                if (widget and self._is_over_scrollable_area(widget) and 
                    not self._is_input_widget(widget)):
                    
                    if hasattr(self.scrollable_frame, '_parent_canvas'):
                        delta = -1 * (event.delta / UIConstants.SCROLL_UNITS_PER_WHEEL)
                        self.scrollable_frame._parent_canvas.yview_scroll(int(delta), "units")
                    return "break"
                return None
                    
            except Exception as e:
                print(f"Mousewheel handler error: {e}")
                return None
        
        self.bind("<MouseWheel>", mousewheel_handler)
        self.bind("<Button-4>", mousewheel_handler)  # Linux scroll up
        self.bind("<Button-5>", mousewheel_handler)  # Linux scroll down

    def _is_over_scrollable_area(self, widget) -> bool:
        """Check if widget is within the scrollable content area"""
        if not widget:
            return False
        
        current = widget
        while current:
            if current == self.scrollable_frame:
                return True
            try:
                current = current.master
            except:
                break
        return False
    
    def _is_input_widget(self, widget) -> bool:
        """Check if widget is an input widget that should receive focus/events"""
        if not widget:
            return False
        
        widget_class = widget.__class__.__name__
        input_widgets = ['CTkEntry', 'CTkTextbox', 'CTkSwitch', 'CTkOptionMenu', 'CTkButton']
        return widget_class in input_widgets
    
    def _check_and_update_sidebar(self):
        """Check if sidebar needs to be converted to scrollable and update if necessary"""
        try:
            should_scroll = self.sidebar_manager.should_use_scrollable()
            
            if should_scroll and not self.sidebar_manager.is_scrollable:
                self._create_sidebar_frame(scrollable=True)
                self.sidebar_manager.recreate_buttons_in_parent(self.sidebar_frame)
                print("Converted sidebar to scrollable due to overflow")
                
        except Exception as e:
            print(f"Error updating sidebar: {e}")
    
    def add_sidebar_section(self, section_id: str, title: str, on_click: Callable) -> SidebarNavButton:
        """Add a navigation button to the sidebar"""
        button = self.sidebar_manager.create_sidebar_button(
            self.sidebar_frame, section_id, title,
            lambda: self._on_sidebar_click(section_id, on_click)
        )
        
        self.sidebar_manager.buttons[section_id] = button
        
        # Check if we need to convert to scrollable after adding button
        self.after(UIConstants.OVERFLOW_CHECK_DELAY, self._check_and_update_sidebar)
        
        return button
    
    def _on_sidebar_click(self, section_id: str, callback: Callable):
        """Handle sidebar button click"""
        self.set_active_section(section_id)
        self.scroll_to_section(section_id)
        if callback:
            callback()
    
    def set_active_section(self, section_id: str):
        """Set the active section in sidebar"""
        for btn_id, button in self.sidebar_manager.buttons.items():
            button.set_active(btn_id == section_id)
    
    def scroll_to_section(self, section_id: str):
        """Scroll content to show specific section"""
        if section_id in self._content_frames:
            frame = self._content_frames[section_id]
            try:
                self.update_idletasks()
                frame.update_idletasks()
                self.scrollable_frame.update_idletasks()
                
                frame_y = frame.winfo_y()
                
                if hasattr(self.scrollable_frame, '_parent_canvas'):
                    canvas = self.scrollable_frame._parent_canvas
                    canvas.update_idletasks()
                    canvas.configure(scrollregion=canvas.bbox("all"))
                    
                    scroll_region = canvas.cget("scrollregion").split()
                    if len(scroll_region) >= 4:
                        total_height = float(scroll_region[3])
                        if total_height > 0:
                            target_pos = max(0.0, min(1.0, frame_y / total_height))
                            canvas.yview_moveto(target_pos)
                        
            except Exception as e:
                print(f"Error scrolling to section: {e}")
    
    def scroll_to_field(self, section_id: str, field_key: str):
        """Scroll content to show specific field and highlight it"""
        if section_id in self._content_frames:
            frame = self._content_frames[section_id]
            field_widget = frame.get_widget(field_key)
            
            if field_widget:
                try:
                    self.update_idletasks()
                    frame.update_idletasks()
                    field_widget.update_idletasks()
                    self.scrollable_frame.update_idletasks()
                    
                    # Get field position relative to scrollable frame
                    frame_y = frame.winfo_y()
                    field_y = field_widget.winfo_y()
                    total_field_y = frame_y + field_y
                    
                    # Add some padding above the field for better visibility
                    padding = 20
                    target_y = max(0, total_field_y - padding)
                    
                    if hasattr(self.scrollable_frame, '_parent_canvas'):
                        canvas = self.scrollable_frame._parent_canvas
                        canvas.update_idletasks()
                        canvas.configure(scrollregion=canvas.bbox("all"))
                        
                        scroll_region = canvas.cget("scrollregion").split()
                        if len(scroll_region) >= 4:
                            total_height = float(scroll_region[3])
                            if total_height > 0:
                                target_pos = max(0.0, min(1.0, target_y / total_height))
                                canvas.yview_moveto(target_pos)
                    
                    # Highlight the field temporarily
                    self._highlight_field(field_widget)
                        
                except Exception as e:
                    print(f"Error scrolling to field: {e}")
            else:
                # Fallback to section scrolling
                self.scroll_to_section(section_id)
    
    def _highlight_field(self, widget):
        """Temporarily highlight a field with visual feedback"""
        try:
            # Store original colors
            original_border_color = None
            original_border_width = None
            
            # Get current colors
            if hasattr(widget, 'cget'):
                try:
                    original_border_color = widget.cget('border_color')
                except:
                    pass
                try:
                    original_border_width = widget.cget('border_width')
                except:
                    pass
            
            # Apply highlight
            highlight_color = "#4a9ee8"  # Blue highlight
            try:
                widget.configure(border_color=highlight_color)
                if hasattr(widget, 'configure') and 'border_width' in str(widget.configure()):
                    widget.configure(border_width=3)
            except:
                pass
            
            # Schedule removal of highlight after 2 seconds
            def remove_highlight():
                try:
                    if original_border_color is not None:
                        widget.configure(border_color=original_border_color)
                    else:
                        widget.configure(border_color="gray")
                    
                    if original_border_width is not None:
                        widget.configure(border_width=original_border_width)
                    else:
                        widget.configure(border_width=1)
                except:
                    pass
            
            self.after(2000, remove_highlight)  # Remove highlight after 2 seconds
            
        except Exception as e:
            print(f"Error highlighting field: {e}")
    
    def center(self, root: ctk.CTk) -> None:
        return _center_parent_window(self, root, self._last_width, self._last_height)
    
    def get_widget(self, id: str) -> Optional[ctk.CTkBaseClass]:
        return _get_widget(self, id)

    def get_widget_value(self, id: str) -> Optional[str]:
        return _get_widget_value(self, id)
    
    def get_frame(self, id: str) -> Optional[ctk.CTkFrame]:
        return _get_frame(self, id)
    
    def create_section_frame(
        self,
        id: str,
        title: str,
        bg_color: Optional[str] = None
    ) -> ConfigFrame:
        """Create a section frame in the scrollable content area"""
        frame = ConfigFrame(self.scrollable_frame, fg_color=bg_color or ("white", "gray20"))
        
        row = len(self._content_frames)
        frame.grid(row=row, column=0, sticky="ew", padx=0, pady=(0, UIConstants.PADDING_LARGE))
        frame.grid_columnconfigure(1, weight=UIConstants.WEIGHT_FULL)
        
        self._content_frames[id] = frame
        _save_frame(self, id, frame)
        
        self.add_sidebar_section(
            section_id=id,
            title=title,
            on_click=lambda: None  # Scrolling is handled in _on_sidebar_click
        )
        
        return frame
    
    def create_button_section(self) -> ctk.CTkFrame:
        """Create the bottom button section"""
        button_container = ctk.CTkFrame(self.button_frame, fg_color="transparent")
        button_container.grid(row=0, column=0, sticky="e", padx=0, pady=UIConstants.PADDING_SMALL)
        return button_container

# =============================================================================================================================
# Console Window
# =============================================================================================================================

class ConsoleWindow(ctk.CTkToplevel):
    def create(
        self,
        visible: bool,
        title: str,
        width: int,
        height: int,
        min_width: Optional[int] = None,
        min_height: Optional[int] = None,
        icon: Optional[str] = None
    ) -> None:
        self._last_title = title
        self._last_width = width
        self._last_height = height
        self._last_min_width = min_width
        self._last_min_height = min_height
        self._last_icon = icon
        
        _create_parent_window(self, visible, title, width, height, min_width, min_height, icon)
    
    def center(self, root: ctk.CTk) -> None:
        return _center_parent_window(self, root, self._last_width, self._last_height)
    
    def get_widget(self, id: str) -> Optional[ctk.CTkBaseClass]:
        return _get_widget(self, id)

    def get_widget_value(self, id: str) -> Optional[str]:
        return _get_widget_value(self, id)
    
    def show(self, show: bool, root: ctk.CTk, center: bool) -> None:
        if (self.winfo_viewable() == 1) == show:
            return
        
        if show:
            self.deiconify()
            self.lift()
            self.geometry(f"{self._last_width}x{self._last_height}")
            self.minsize(self._last_min_width, self._last_min_height)

            if self._last_icon:
                self.after(200, lambda: set_window_icon(self, self._last_icon))

            if center:
                return _center_parent_window(self, root, self._last_width, self._last_height)
        else:
            self.withdraw()
    
    def create_textbox(self, id: str) -> CustomTextbox:
        textbox = CustomTextbox(
            self,
            state="disabled",
            font=get_font_tuple("Consolas", 12),  # Better monospace font for console
            wrap="word",  # Better text wrapping
            border_width=1,
            border_color=("gray60", "gray40"),
            corner_radius=4,
            fg_color=("gray10", "gray5"),  # Darker background
            text_color=("gray90", "gray90"),  # Light text
            scrollbar_button_color=("gray70", "gray30"),
            scrollbar_button_hover_color=("gray60", "gray40")
        )
        textbox.pack(expand=True, fill="both", padx=2, pady=2)
        
        # Initialize color support for console
        textbox.add_colors()
        
        _save_widget(self, id, textbox)
        return textbox

class UpdateWindow(ctk.CTkToplevel):
    def create(
        self,
        visible: bool,
        title: str,
        width: int,
        height: int,
        min_width: Optional[int] = None,
        min_height: Optional[int] = None,
        icon: Optional[str] = None
    ) -> None:
        self._last_title = title
        self._last_width = width
        self._last_height = height
        self._last_min_width = min_width
        self._last_min_height = min_height
        self._last_icon = icon
        
        _create_parent_window(self, visible, title, width, height, min_width, min_height, icon)
    
    def center(self, root: ctk.CTk) -> None:
        return _center_parent_window(self, root, self._last_width, self._last_height)
    
    def get_widget(self, id: str) -> Optional[ctk.CTkBaseClass]:
        return _get_widget(self, id)

    def get_widget_value(self, id: str) -> Optional[str]:
        return _get_widget_value(self, id)
    
    def create_title(
            self, 
            id: str, 
            text: str, 
            row: int = 0, 
            column: int = 0, 
            row_grid: bool = False
        ) -> ctk.CTkLabel:
        label = ctk.CTkLabel(self, text=text, font=get_font_tuple("Blinker", 14, "bold"))
        label.grid(row=row, column=column, padx=UIConstants.PADDING_MEDIUM, pady=(UIConstants.PADDING_MEDIUM, UIConstants.PADDING_MEDIUM), sticky="nsew")
    
        if row_grid:
            _set_row_grid(self, row)

        _save_widget(self, id, label)
        return label
    
    def create_button(
            self, 
            id: str, 
            text: str, 
            command: Optional[Callable] = None, 
            row: int = 0, 
            column: int = 0, 
            row_grid: bool = False
        ) -> ctk.CTkButton:
        
        button = ctk.CTkButton(self, text=text, command=command, font=get_font_tuple("Blinker", 14))
        button.grid(row=row, column=column, padx=UIConstants.PADDING_MEDIUM, pady=(0, UIConstants.PADDING_MEDIUM), sticky="ew")

        if row_grid:
            _set_row_grid(self, row)

        _save_widget(self, id, button)
        return button


# =============================================================================================================================
# Contributor Window
# =============================================================================================================================

class ContributorWindow(ctk.CTkToplevel):
    def __init__(self, parent, icon_path=None):
        super().__init__(parent)
        self.parent = parent
        self.icon_path = icon_path
        self.contributors_data = []
        self._load_contributors_data()
        self._create_window()
        self._create_widgets()
        # Override CustomTkinter's default icon after its 200ms delay
        if self.icon_path:
            self.after(300, self._set_custom_icon)
    
    def _load_contributors_data(self):
        """Load contributors data from JSON file"""
        try:
            # Get the path to the contributors.json file using StorageManager
            from .storage_manager import StorageManager
            storage_manager = StorageManager()
            contributors_file = storage_manager.get_existing_path("base", "assets/contributors.json")
            
            if not contributors_file:
                # Fallback to development path resolution
                script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                contributors_file = os.path.join(script_dir, "assets", "contributors.json")
            
            with open(contributors_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.contributors_data = data.get('contributors', [])
        except Exception as e:
            print(f"Error loading contributors data: {e}")
            # Fallback data if file can't be loaded
            self.contributors_data = [
                {
                    "name": "Claude (Anthropic)",
                    "status": "AI Assistant - Code refactoring and improvements",
                    "avatar_url": "",
                    "github_url": "https://github.com/anthropics"
                }
            ]
    
    def _create_window(self):
        """Set up the main window properties"""
        self.title("Contributors")
        self.geometry("500x600")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
    
    def _set_custom_icon(self):
        """Set custom icon, overriding CustomTkinter's default icon"""
        set_window_icon(self, self.icon_path)  # Changed this line
    
    def _create_widgets(self):
        """Create and layout all widgets"""
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Contributors",
            font=get_font_tuple("Blinker", 24, "bold")
        )
        title_label.grid(row=0, column=0, pady=(20, 10), sticky="ew")
        
        # Scrollable frame for contributors list
        scrollable_frame = ctk.CTkScrollableFrame(
            main_frame,
            fg_color="transparent",
            scrollbar_button_color=("gray70", "gray30"),
            scrollbar_button_hover_color=("gray60", "gray40")
        )
        scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        scrollable_frame.grid_columnconfigure(0, weight=1)
        
        # Create contributor items
        for i, contributor in enumerate(self.contributors_data):
            self._create_contributor_item(scrollable_frame, contributor, i)
        
        # GitHub link button
        github_button = ctk.CTkButton(
            main_frame,
            text="View All Contributors on GitHub",
            command=self._open_github_contributors,
            font=get_font_tuple("Blinker", 14),
            height=40
        )
        github_button.grid(row=2, column=0, pady=(10, 20), padx=20, sticky="ew")
    
    def _create_contributor_item(self, parent, contributor, row):
        """Create a single contributor item"""
        # Container frame for this contributor with slightly brighter background
        item_frame = ctk.CTkFrame(parent, height=80, fg_color=("gray94", "gray16"))
        item_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        item_frame.grid_columnconfigure(0, weight=0)  # Avatar column - fixed width
        item_frame.grid_columnconfigure(1, weight=1)  # Text column - expandable
        item_frame.grid_propagate(False)
        
        # Avatar frame with image support (transparent background)
        avatar_frame = ctk.CTkFrame(item_frame, width=60, height=60, corner_radius=30, fg_color="transparent")
        avatar_frame.grid(row=0, column=0, padx=15, pady=10, rowspan=2)
        avatar_frame.grid_propagate(False)
        
        # Avatar label (will show image or fallback text)
        avatar_initial = ctk.CTkLabel(
            avatar_frame,
            text=contributor['name'][0].upper(),
            font=get_font_tuple("Blinker", 20, "bold"),
            text_color=("gray10", "gray90")
        )
        avatar_initial.place(relx=0.5, rely=0.5, anchor="center")
        
        # Load avatar image if URL is available
        if 'avatar_url' in contributor and contributor['avatar_url']:
            self._load_avatar_image(contributor['avatar_url'], avatar_initial, contributor['name'][0].upper())
        
        # Name
        name_label = ctk.CTkLabel(
            item_frame,
            text=contributor['name'],
            font=get_font_tuple("Blinker", 16, "bold"),
            anchor="w"
        )
        name_label.grid(row=0, column=1, sticky="ew", padx=(10, 15), pady=(8, 0))
        
        # Status
        status_label = ctk.CTkLabel(
            item_frame,
            text=contributor['status'],
            font=get_font_tuple("Blinker", 12),
            anchor="w",
            text_color=("gray50", "gray70")
        )
        status_label.grid(row=1, column=1, sticky="ew", padx=(10, 15), pady=(0, 8))
        
        # Make the item clickable to open GitHub profile
        def open_profile(url=contributor.get('github_url', '')):
            if url:
                try:
                    webbrowser.open(url)
                except Exception as e:
                    print(f"Error opening profile: {e}")
        
        # Store original colors for hover animation
        original_fg_color = ("gray94", "gray16")
        hover_fg_color = ("gray90", "gray20")
        
        # Hover animation functions
        def on_enter(event, frame=item_frame):
            frame.configure(fg_color=hover_fg_color)
            
        def on_leave(event, frame=item_frame):
            frame.configure(fg_color=original_fg_color)
        
        # Bind click and hover events to all elements
        for widget in [item_frame, avatar_frame, avatar_initial, name_label, status_label]:
            widget.bind("<Button-1>", lambda e, url=contributor.get('github_url', ''): open_profile(url))
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.configure(cursor="hand2")
    
    def _open_github_contributors(self):
        """Open the GitHub contributors page"""
        try:
            webbrowser.open("https://github.com/LyubomirT/intense-rp-next/graphs/contributors")
        except Exception as e:
            print(f"Error opening GitHub contributors page: {e}")
    
    def _load_avatar_image(self, url: str, avatar_label: ctk.CTkLabel, fallback_text: str):
        """Load avatar image from URL asynchronously"""
        def load_image():
            try:
                # Download image with timeout
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                # Open image and resize to fit avatar
                image = Image.open(BytesIO(response.content))
                image = image.resize((60, 60), Image.Resampling.LANCZOS)
                
                # Create a circular image with transparent background
                # This approach creates a truly circular image without square borders
                circular_image = Image.new('RGBA', (60, 60), (0, 0, 0, 0))
                
                # Create a circular mask
                mask = Image.new('L', (60, 60), 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, 60, 60), fill=255)
                
                # Paste the original image onto the circular canvas using the mask
                circular_image.paste(image, (0, 0), mask)
                
                # Convert to CTkImage for proper CustomTkinter support
                ctk_image = ctk.CTkImage(light_image=circular_image, dark_image=circular_image, size=(60, 60))
                
                # Update label on main thread
                def update_avatar():
                    avatar_label.configure(image=ctk_image, text="")
                    avatar_label.image = ctk_image  # Keep reference to prevent garbage collection
                
                self.after(0, update_avatar)
                
            except Exception as e:
                print(f"Failed to load avatar from {url}: {e}")
                # Keep the fallback text if image loading fails
        
        # Load image in background thread
        threading.Thread(target=load_image, daemon=True).start()
    
    def center(self):
        """Center the window relative to parent"""
        self.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")


# =============================================================================================================================
# Better Update System Windows
# =============================================================================================================================

class BetterUpdateWindow(ctk.CTkToplevel):
    """Better update notification window with improved styling"""
    
    def __init__(self, parent, version: str, icon_path: Optional[str] = None):
        super().__init__(parent)
        self.parent = parent
        self.version = version
        self.icon_path = icon_path
        self._create_window()
        self._create_widgets()
        if self.icon_path:
            self.after(300, lambda: set_window_icon(self, self.icon_path))
    
    def _create_window(self):
        """Set up the window properties"""
        self.title("New Version Available")
        self.geometry("400x200")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
    
    def _create_widgets(self):
        """Create and layout all widgets"""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text=f"VERSION {self.version} AVAILABLE",
            font=get_font_tuple("Blinker", 16, "bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        # Description
        desc_label = ctk.CTkLabel(
            self,
            text="A new version of IntenseRP Next is ready to download.\nWould you like to update now?",
            font=get_font_tuple("Blinker", 12),
            text_color=("gray50", "gray70")
        )
        desc_label.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="ew")
        
        # Button frame
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        # Download button
        download_btn = ctk.CTkButton(
            button_frame,
            text="Download",
            command=self._on_download_click,
            font=get_font_tuple("Blinker", 14, "bold"),
            height=35
        )
        download_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        # Close button
        close_btn = ctk.CTkButton(
            button_frame,
            text="Later",
            command=self.destroy,
            font=get_font_tuple("Blinker", 14),
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            height=35
        )
        close_btn.grid(row=0, column=1, padx=(5, 0), sticky="ew")
    
    def _on_download_click(self):
        """Handle download button click"""
        self.destroy()
        # Create and show download options window
        download_options_window = DownloadOptionsWindow(self.parent, self.version, self.icon_path)
        download_options_window.center()
    
    def center(self):
        """Center the window relative to parent"""
        self.update_idletasks()
        if self.parent:
            x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.winfo_width() // 2)
            y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.winfo_height() // 2)
            self.geometry(f"+{x}+{y}")


class DownloadOptionsWindow(ctk.CTkToplevel):
    """Window for choosing download method"""
    
    def __init__(self, parent, version: str, icon_path: Optional[str] = None):
        super().__init__(parent)
        self.parent = parent
        self.version = version
        self.icon_path = icon_path
        self._create_window()
        self._create_widgets()
        if self.icon_path:
            self.after(300, lambda: set_window_icon(self, self.icon_path))
    
    def _create_window(self):
        """Set up the window properties"""
        # Check if running from source to adjust window size
        try:
            storage_mgr = storage_manager.StorageManager()
            is_source_build = storage_mgr.is_running_from_source()
        except:
            is_source_build = False
            
        self.title("Choose Download Method")
        # Make window taller for source builds to accommodate extra widgets
        height = "400" if is_source_build else "260"
        self.geometry(f"360x{height}")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
    
    def _create_widgets(self):
        """Create and layout all widgets"""
        # Check if running from source
        try:
            storage_mgr = storage_manager.StorageManager()
            is_source_build = storage_mgr.is_running_from_source()
        except:
            is_source_build = False  # Fallback to assuming binary build
            
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Choose Download Method",
            font=get_font_tuple("Blinker", 18, "bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        # Description
        desc_label = ctk.CTkLabel(
            self,
            text="How would you like to download the new version?",
            font=get_font_tuple("Blinker", 12),
            text_color=("gray50", "gray70")
        )
        desc_label.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        # GitHub button
        github_btn = ctk.CTkButton(
            self,
            text="🌐  Visit GitHub (Traditional)",
            command=self._open_github,
            font=get_font_tuple("Blinker", 14),
            height=40,
            corner_radius=8
        )
        github_btn.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        # Source build warning and git update option
        if is_source_build:
            # Warning message
            warning_label = ctk.CTkLabel(
                self,
                text="⚠ Source Build Detected",
                font=get_font_tuple("Blinker", 12, "bold"),
                text_color=("red", "red")
            )
            warning_label.grid(row=3, column=0, padx=20, pady=(0, 5), sticky="ew")
            
            warning_desc = ctk.CTkLabel(
                self,
                text="Binary updater is not compatible with source builds.\nUse git to update instead.",
                font=get_font_tuple("Blinker", 10),
                text_color=("gray50", "gray70")
            )
            warning_desc.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")
            
            # Git update button
            git_btn = ctk.CTkButton(
                self,
                text="🔄  Update via Git",
                command=self._open_git_update,
                font=get_font_tuple("Blinker", 14, "bold"),
                height=40,
                corner_radius=8
            )
            git_btn.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="ew")
            
            # Disabled integrated download button
            integrated_btn = ctk.CTkButton(
                self,
                text="⭳  Integrated Download (Not Available)",
                command=None,
                font=get_font_tuple("Blinker", 14),
                height=40,
                corner_radius=8,
                state="disabled",
                fg_color=("red", "darkred"),
                text_color=("gray", "gray")
            )
            integrated_btn.grid(row=6, column=0, padx=20, pady=(0, 15), sticky="ew")
            
        else:
            # Regular integrated download button for binary builds
            integrated_btn = ctk.CTkButton(
                self,
                text="⭳  Integrated Download (Beta)",
                command=self._open_integrated_download,
                font=get_font_tuple("Blinker", 14, "bold"),
                height=40,
                corner_radius=8
            )
            integrated_btn.grid(row=3, column=0, padx=20, pady=(0, 15), sticky="ew")
        
        # Button frame for back/close (adjust row based on source build)
        button_frame_row = 7 if is_source_build else 4
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=button_frame_row, column=0, padx=20, pady=(0, 20), sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        # Back button
        back_btn = ctk.CTkButton(
            button_frame,
            text="Back",
            command=self._go_back,
            font=get_font_tuple("Blinker", 12),
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            height=30
        )
        back_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        # Close button
        close_btn = ctk.CTkButton(
            button_frame,
            text="Close",
            command=self.destroy,
            font=get_font_tuple("Blinker", 12),
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            height=30
        )
        close_btn.grid(row=0, column=1, padx=(5, 0), sticky="ew")
    
    def _open_github(self):
        """Open GitHub releases page"""
        try:
            webbrowser.open("https://github.com/LyubomirT/intense-rp-next/releases/latest")
            self.destroy()
            print("GitHub releases page opened.")
        except Exception as e:
            print(f"Error opening GitHub: {e}")
    
    def _open_integrated_download(self):
        """Open integrated download window"""
        self.destroy()
        asset_selection_window = AssetSelectionWindow(self.parent, self.version, self.icon_path)
        asset_selection_window.center()
    
    def _go_back(self):
        """Go back to better update window"""
        self.destroy()
        better_update_window = BetterUpdateWindow(self.parent, self.version, self.icon_path)
        better_update_window.center()
    
    def _open_git_update(self):
        """Open git update instructions dialog"""
        try:
            import subprocess
            import platform
            
            # Check if git is available
            try:
                subprocess.run(["git", "--version"], capture_output=True, check=True)
                git_available = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                git_available = False
            
            if git_available:
                # Show git update command dialog
                dialog = GitUpdateDialog(self, self.icon_path)
                dialog.center()
            else:
                # Show git not found dialog
                from tkinter import messagebox
                messagebox.showwarning(
                    "Git Not Found",
                    "Git is not installed or not available in PATH.\n\n"
                    "Please install Git and try again, or update manually:\n"
                    "1. Navigate to your source directory\n"
                    "2. Run: git pull origin main\n"
                    "3. Restart the application"
                )
        except Exception as e:
            print(f"Error checking git availability: {e}")

    def center(self):
        """Center the window relative to parent"""
        self.update_idletasks()
        if self.parent:
            x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.winfo_width() // 2)
            y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.winfo_height() // 2)
            self.geometry(f"+{x}+{y}")


class AssetSelectionWindow(ctk.CTkToplevel):
    """Window for selecting which asset to download"""
    
    def __init__(self, parent, version: str, icon_path: Optional[str] = None):
        super().__init__(parent)
        self.parent = parent
        self.version = version
        self.icon_path = icon_path
        self.selected_asset = None
        self.assets = []
        self.asset_vars = {}
        self._create_window()
        self._load_assets()
        if self.icon_path:
            self.after(300, lambda: set_window_icon(self, self.icon_path))
    
    def _create_window(self):
        """Set up the window properties"""
        self.title("Select Download")
        self.geometry("500x400")
        self.resizable(True, True)
        self.minsize(450, 350)
        self.attributes("-topmost", True)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  # Make scrollable frame expandable
    
    def _load_assets(self):
        """Load assets from GitHub API and create UI"""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Select Download Package",
            font=get_font_tuple("Blinker", 18, "bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        # Loading label
        loading_label = ctk.CTkLabel(
            self,
            text="Loading available downloads...",
            font=get_font_tuple("Blinker", 12),
            text_color=("gray50", "gray70")
        )
        loading_label.grid(row=1, column=0, padx=20, pady=20, sticky="ew")
        
        # Load assets in background thread
        threading.Thread(target=self._fetch_assets, args=(loading_label,), daemon=True).start()
    
    def _fetch_assets(self, loading_label):
        """Fetch assets from GitHub API"""
        try:
            from .github_api import GitHubAPI
            
            # Get release data
            release_data = GitHubAPI.get_latest_release()
            if not release_data:
                self.after(0, lambda: self._show_error("Failed to fetch release information."))
                return
            
            # Get and categorize assets
            assets = GitHubAPI.get_release_assets(release_data)
            if not assets:
                self.after(0, lambda: self._show_error("No downloadable assets found."))
                return
            
            self.assets = assets
            categorized_assets = GitHubAPI.categorize_assets(assets)
            
            # Update UI on main thread
            self.after(0, lambda: self._create_asset_ui(loading_label, categorized_assets))
            
        except Exception as e:
            self.after(0, lambda: self._show_error(f"Error loading assets: {e}"))
    
    def _show_error(self, error_message: str):
        """Show error message"""
        # Clear existing widgets except title
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkLabel) and "Select Download Package" not in widget.cget("text"):
                widget.destroy()
        
        error_label = ctk.CTkLabel(
            self,
            text=error_message,
            font=get_font_tuple("Blinker", 12),
            text_color=("red", "red")
        )
        error_label.grid(row=1, column=0, padx=20, pady=20, sticky="ew")
        
        # Add close button
        close_btn = ctk.CTkButton(
            self,
            text="Close",
            command=self.destroy,
            font=get_font_tuple("Blinker", 14),
            height=35
        )
        close_btn.grid(row=2, column=0, padx=20, pady=20, sticky="ew")
    
    def _create_asset_ui(self, loading_label, categorized_assets):
        """Create the asset selection UI"""
        # Remove loading label
        loading_label.destroy()
        
        # Create scrollable frame for assets
        scrollable_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=("gray70", "gray30"),
            scrollbar_button_hover_color=("gray60", "gray40")
        )
        scrollable_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="nsew")
        scrollable_frame.grid_columnconfigure(0, weight=1)
        
        # Create radio button variable
        self.selected_var = ctk.StringVar()
        
        row = 0
        for platform, assets in categorized_assets.items():
            # Platform header
            platform_label = ctk.CTkLabel(
                scrollable_frame,
                text=f"{platform} ({len(assets)} packages)",
                font=get_font_tuple("Blinker", 16, "bold"),
                anchor="w"
            )
            platform_label.grid(row=row, column=0, padx=10, pady=(10, 5), sticky="ew")
            row += 1
            
            # Assets for this platform
            for asset in assets:
                self._create_asset_item(scrollable_frame, asset, row)
                row += 1
            
            # Add spacing between platforms
            spacing_frame = ctk.CTkFrame(scrollable_frame, height=1, fg_color="transparent")
            spacing_frame.grid(row=row, column=0, pady=5)
            row += 1
        
        # Button frame
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        button_frame.grid_columnconfigure(1, weight=1)
        
        # Back button
        back_btn = ctk.CTkButton(
            button_frame,
            text="Back",
            command=self._go_back,
            font=get_font_tuple("Blinker", 12),
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            height=35,
            width=80
        )
        back_btn.grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        # Download button
        download_btn = ctk.CTkButton(
            button_frame,
            text="Download Selected",
            command=self._start_download,
            font=get_font_tuple("Blinker", 14, "bold"),
            height=35
        )
        download_btn.grid(row=0, column=1, sticky="ew")
        
        # Close button
        close_btn = ctk.CTkButton(
            button_frame,
            text="Close",
            command=self.destroy,
            font=get_font_tuple("Blinker", 12),
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            height=35,
            width=80
        )
        close_btn.grid(row=0, column=2, padx=(10, 0), sticky="e")
    
    def _create_asset_item(self, parent, asset, row):
        """Create a single asset selection item"""
        from .github_api import GitHubAPI
        
        # Container frame
        item_frame = ctk.CTkFrame(
            parent, 
            height=80, 
            fg_color=("gray94", "gray16") if not asset.is_current_platform else ("#3d8bc7", "#2a3b4a")
        )
        item_frame.grid(row=row, column=0, padx=10, pady=2, sticky="ew")
        item_frame.grid_columnconfigure(1, weight=1)
        item_frame.grid_propagate(False)
        
        # Radio button
        radio = ctk.CTkRadioButton(
            item_frame,
            text="",
            variable=self.selected_var,
            value=asset.name,
            font=get_font_tuple("Blinker", 12)
        )
        radio.grid(row=0, column=0, padx=15, pady=10, rowspan=2)
        
        # Asset name and info frame
        info_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        info_frame.grid(row=0, column=1, padx=(10, 15), pady=8, sticky="ew", rowspan=2)
        info_frame.grid_columnconfigure(0, weight=1)
        
        # Friendly name with recommendation badge
        name_text = asset.friendly_name
        if asset.is_updater:
            name_text += " (Recommended)"
        if asset.is_current_platform:
            name_text += " - Your Platform"
        
        name_label = ctk.CTkLabel(
            info_frame,
            text=name_text,
            font=get_font_tuple("Blinker", 14, "bold" if asset.is_updater or asset.is_current_platform else "normal"),
            anchor="w",
            text_color=("green", "lightgreen") if asset.is_updater else ("gray10", "gray90")
        )
        name_label.grid(row=0, column=0, sticky="ew")
        
        # Description and size
        size_text = GitHubAPI.format_file_size(asset.size)
        desc_text = f"{asset.description} • {size_text}"
        
        desc_label = ctk.CTkLabel(
            info_frame,
            text=desc_text,
            font=get_font_tuple("Blinker", 11),
            anchor="w",
            text_color=("gray50", "gray70")
        )
        desc_label.grid(row=1, column=0, sticky="ew")
        
        # Pre-select current platform updater if available
        if asset.is_current_platform and asset.is_updater and not self.selected_var.get():
            self.selected_var.set(asset.name)
    
    def _start_download(self):
        """Start downloading the selected asset"""
        selected_name = self.selected_var.get()
        if not selected_name:
            print("No asset selected")
            return
        
        # Find the selected asset
        selected_asset = None
        for asset in self.assets:
            if asset.name == selected_name:
                selected_asset = asset
                break
        
        if not selected_asset:
            print("Selected asset not found")
            return
        
        # Close this window and start download
        self.destroy()
        download_window = DownloadProgressWindow(self.parent, selected_asset, self.icon_path)
        download_window.center()
    
    def _go_back(self):
        """Go back to download options window"""
        self.destroy()
        download_options_window = DownloadOptionsWindow(self.parent, self.version, self.icon_path)
        download_options_window.center()
    
    def center(self):
        """Center the window relative to parent"""
        self.update_idletasks()
        if self.parent:
            x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.winfo_width() // 2)
            y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.winfo_height() // 2)
            self.geometry(f"+{x}+{y}")


class DownloadProgressWindow(ctk.CTkToplevel):
    """Window showing download progress with speed and percentage"""
    
    def __init__(self, parent, asset, icon_path: Optional[str] = None):
        super().__init__(parent)
        self.parent = parent
        self.asset = asset
        self.icon_path = icon_path
        self.download_cancelled = False
        self._create_window()
        self._create_widgets()
        if self.icon_path:
            self.after(300, lambda: set_window_icon(self, self.icon_path))
        
        # Start download in background thread
        threading.Thread(target=self._start_download, daemon=True).start()
    
    def _create_window(self):
        """Set up the window properties"""
        self.title("Downloading...")
        self.geometry("450x200")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        
        # Prevent window from being closed during download
        self.protocol("WM_DELETE_WINDOW", self._on_close_attempt)
    
    def _create_widgets(self):
        """Create and layout all widgets"""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Downloading Update",
            font=get_font_tuple("Blinker", 18, "bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        # File name
        self.filename_label = ctk.CTkLabel(
            self,
            text=f"File: {self.asset.friendly_name}",
            font=get_font_tuple("Blinker", 12),
            text_color=("gray50", "gray70")
        )
        self.filename_label.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            self,
            height=20,
            corner_radius=10
        )
        self.progress_bar.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.progress_bar.set(0)
        
        # Status frame
        status_frame = ctk.CTkFrame(self, fg_color="transparent")
        status_frame.grid(row=3, column=0, padx=20, pady=(0, 15), sticky="ew")
        status_frame.grid_columnconfigure(0, weight=1)
        status_frame.grid_columnconfigure(1, weight=1)
        
        # Progress percentage
        self.percentage_label = ctk.CTkLabel(
            status_frame,
            text="0%",
            font=get_font_tuple("Blinker", 12, "bold"),
            anchor="w"
        )
        self.percentage_label.grid(row=0, column=0, sticky="w")
        
        # Download speed
        self.speed_label = ctk.CTkLabel(
            status_frame,
            text="0 KB/s",
            font=get_font_tuple("Blinker", 12),
            anchor="e"
        )
        self.speed_label.grid(row=0, column=1, sticky="e")
        
        # Cancel button (initially hidden)
        self.cancel_btn = ctk.CTkButton(
            self,
            text="Cancel",
            command=self._cancel_download,
            font=get_font_tuple("Blinker", 12),
            fg_color=("red", "darkred"),
            hover_color=("darkred", "red"),
            height=30,
            width=100
        )
        # Don't grid initially - will be shown after a delay
    
    def _start_download(self):
        """Start the download process"""
        import tempfile
        import time
        
        try:
            # Create persistent download location in user's Downloads folder
            import os
            from pathlib import Path
            
            # Try to get user's Downloads folder, fallback to current directory
            try:
                downloads_dir = Path.home() / "Downloads" / "IntenseRP"
                downloads_dir.mkdir(parents=True, exist_ok=True)
            except:
                # Fallback to current directory if Downloads folder not accessible
                downloads_dir = Path.cwd() / "Downloads"
                downloads_dir.mkdir(exist_ok=True)
            
            download_path = downloads_dir / self.asset.name
            self.final_download_path = str(download_path)  # Store for "Open Folder" button
            
            # Speed tracking variables
            start_time = time.time()
            last_update_time = start_time
            last_downloaded = 0
            
            # Import requests for download
            import requests
            
            # Download with progress tracking (simplified like intenserp_updater)
            response = requests.get(self.asset.download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(str(download_path), 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.download_cancelled:
                        break
                    
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Update progress (like intenserp_updater - simple approach)
                        if total_size > 0:
                            current_time = time.time()
                            
                            # Only update UI every 0.5 seconds to avoid flooding
                            if current_time - last_update_time >= 0.5:
                                # Calculate progress
                                progress = downloaded_size / total_size
                                percentage = int(progress * 100)
                                
                                # Calculate speed
                                time_diff = current_time - last_update_time
                                bytes_diff = downloaded_size - last_downloaded
                                speed_bps = bytes_diff / time_diff if time_diff > 0 else 0
                                speed_text = self._format_speed(speed_bps)
                                
                                # Update UI on main thread (simpler lambda)
                                def update_ui(p=progress, pct=percentage, spd=speed_text):
                                    if not self.download_cancelled:
                                        self._update_progress(p, pct, spd)
                                
                                self.after(0, update_ui)
                                
                                # Update tracking variables
                                last_update_time = current_time
                                last_downloaded = downloaded_size
            
            if not self.download_cancelled:
                # Download completed successfully
                self.after(0, lambda: self._download_completed(str(download_path)))
            
        except Exception as e:
            if not self.download_cancelled:
                self.after(0, lambda: self._download_error(str(e)))
    
    def _update_progress(self, progress: float, percentage: int, speed: str):
        """Update progress UI elements"""
        self.progress_bar.set(progress)
        self.percentage_label.configure(text=f"{percentage}%")
        self.speed_label.configure(text=speed)
        
        # Show cancel button after 3 seconds
        if percentage > 5:
            self.cancel_btn.grid(row=4, column=0, pady=(0, 20))
    
    def _format_speed(self, bytes_per_second: float) -> str:
        """Format download speed in human-readable format"""
        if bytes_per_second < 1024:
            return f"{bytes_per_second:.0f} B/s"
        elif bytes_per_second < 1024 * 1024:
            return f"{bytes_per_second / 1024:.1f} KB/s"
        else:
            return f"{bytes_per_second / (1024 * 1024):.1f} MB/s"
    
    def _download_completed(self, download_path: str):
        """Handle successful download completion"""
        self.progress_bar.set(1.0)
        self.percentage_label.configure(text="100%")
        self.speed_label.configure(text="Complete!")
        
        # Update title
        self.title("Download Complete")
        title_label = self.winfo_children()[0]
        title_label.configure(text="Download Complete!")
        
        # Hide cancel button
        self.cancel_btn.grid_remove()
        
        # Show completion message
        completion_label = ctk.CTkLabel(
            self,
            text="Download completed successfully!",
            font=get_font_tuple("Blinker", 12),
            text_color=("green", "lightgreen")
        )
        completion_label.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        # Handle updater extraction if applicable
        if self.asset.is_updater and self.asset.is_current_platform:
            self._handle_updater_extraction(download_path)
        else:
            self._show_completion_buttons()
    
    def _download_error(self, error_message: str):
        """Handle download error"""
        # Update UI to show error
        self.title("Download Failed")
        title_label = self.winfo_children()[0]
        title_label.configure(text="Download Failed")
        
        error_label = ctk.CTkLabel(
            self,
            text=f"Error: {error_message}",
            font=get_font_tuple("Blinker", 12),
            text_color=("red", "red")
        )
        error_label.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        # Show close button
        close_btn = ctk.CTkButton(
            self,
            text="Close",
            command=self.destroy,
            font=get_font_tuple("Blinker", 14),
            height=35
        )
        close_btn.grid(row=5, column=0, padx=20, pady=(0, 20), sticky="ew")
    
    def _handle_updater_extraction(self, download_path: str):
        """Extract and run updater for current platform"""
        # Show extraction status
        extract_label = ctk.CTkLabel(
            self,
            text="Extracting updater...",
            font=get_font_tuple("Blinker", 12),
            text_color=("blue", "lightblue")
        )
        extract_label.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        try:
            from .storage_manager import StorageManager
            from .updater_manager import UpdaterManager
            
            storage_manager = StorageManager()
            
            # Verify permissions first
            has_permissions, perm_message = UpdaterManager.verify_updater_permissions(storage_manager)
            if not has_permissions:
                extract_label.configure(text=f"Permission error: {perm_message}", text_color=("red", "red"))
                self._show_completion_buttons()
                return
            
            # Extract and run the updater
            success, message = UpdaterManager.extract_and_run_updater(download_path, storage_manager)
            
            if success:
                # Update status to show success
                extract_label.configure(text="Starting updater...", text_color=("green", "lightgreen"))
                
                # Add informational message
                info_label = ctk.CTkLabel(
                    self,
                    text="The updater will handle the rest of the installation.\nThis application will now close.",
                    font=get_font_tuple("Blinker", 11),
                    text_color=("gray50", "gray70")
                )
                info_label.grid(row=5, column=0, padx=20, pady=(5, 10), sticky="ew")
                
                # Close this window and the main application after a short delay
                self.after(2000, self._close_application)
            else:
                # Show error message
                extract_label.configure(text=f"Error: {message}", text_color=("red", "red"))
                self._show_completion_buttons()
        
        except Exception as e:
            extract_label.configure(text=f"Unexpected error: {str(e)}", text_color=("red", "red"))
            self._show_completion_buttons()
    
    def _show_completion_buttons(self):
        """Show completion buttons"""
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=5, column=0, padx=20, pady=(0, 20), sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        # Open folder button
        open_btn = ctk.CTkButton(
            button_frame,
            text="Open Folder",
            command=self._open_download_folder,
            font=get_font_tuple("Blinker", 12),
            height=35
        )
        open_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        # Close button
        close_btn = ctk.CTkButton(
            button_frame,
            text="Close",
            command=self.destroy,
            font=get_font_tuple("Blinker", 12),
            height=35
        )
        close_btn.grid(row=0, column=1, padx=(5, 0), sticky="ew")
    
    def _open_download_folder(self):
        """Open the downloads folder"""
        try:
            if hasattr(self, 'final_download_path') and self.final_download_path:
                import subprocess
                import platform
                
                # Get the folder containing the downloaded file
                folder_path = os.path.dirname(self.final_download_path)
                
                # Open folder in OS file manager
                system = platform.system()
                if system == "Windows":
                    os.startfile(folder_path)
                elif system == "Darwin":  # macOS
                    subprocess.run(["open", folder_path])
                elif system == "Linux":
                    subprocess.run(["xdg-open", folder_path])
                    
                print(f"Opened download folder: {folder_path}")
            else:
                print("Download path not available")
        except Exception as e:
            print(f"Error opening download folder: {e}")
    
    def _close_application(self):
        """Close the entire application"""
        if self.parent:
            self.parent.quit()
    
    def _cancel_download(self):
        """Cancel the ongoing download"""
        self.download_cancelled = True
        self.destroy()
    
    def _on_close_attempt(self):
        """Handle window close attempt during download"""
        # Ask user if they want to cancel
        self._cancel_download()
    
    def center(self):
        """Center the window relative to parent"""
        self.update_idletasks()
        if self.parent:
            x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.winfo_width() // 2)
            y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.winfo_height() // 2)
            self.geometry(f"+{x}+{y}")


# =============================================================================================================================
# Welcome Window
# =============================================================================================================================

class WelcomeWindow(ctk.CTkToplevel):
    """Welcome screen window that appears on first startup"""
    
    def __init__(self, parent, version: str, icon_path: Optional[str] = None):
        super().__init__(parent)
        self.parent = parent
        self.version = version
        self.icon_path = icon_path
        self._create_window()
        self._create_widgets()
        
        # Set icon after a short delay to ensure window is ready
        if self.icon_path:
            self.after(300, lambda: set_window_icon(self, self.icon_path))
    
    def _create_window(self):
        """Set up the window properties"""
        self.title("Welcome to IntenseRP Next!")
        self.geometry("500x450")
        self.resizable(False, False)
        
        # Configure grid weights
        self.grid_columnconfigure(0, weight=1)
        for i in range(8):  # Adjust based on number of rows
            self.grid_rowconfigure(i, weight=0)
        self.grid_rowconfigure(7, weight=1)  # Button area can expand
    
    def _create_widgets(self):
        """Create all widgets for the welcome screen"""
        # Title
        title_label = ctk.CTkLabel(
            self, 
            text=f"🎉 Welcome to IntenseRP Next v{self.version}! 🎉",
            font=get_font_tuple("Blinker", 18, "bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        # Welcome message
        welcome_text = (
            "Hope you enjoy using it!\n\n"
        )
        welcome_label = ctk.CTkLabel(
            self,
            text=welcome_text,
            font=get_font_tuple("Blinker", 12),
            wraplength=460,
            justify="left"
        )
        welcome_label.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="ew")
        
        # Getting started section
        getting_started_label = ctk.CTkLabel(
            self,
            text="Where to start?",
            font=get_font_tuple("Blinker", 14, "bold"),
            anchor="w"
        )
        getting_started_label.grid(row=2, column=0, padx=20, pady=(5, 5), sticky="ew")
        
        # Step 1
        step1_frame = ctk.CTkFrame(self, fg_color="transparent")
        step1_frame.grid(row=3, column=0, padx=30, pady=2, sticky="ew")
        step1_frame.grid_columnconfigure(1, weight=1)
        
        step1_bullet = ctk.CTkLabel(step1_frame, text="1.", font=get_font_tuple("Blinker", 12, "bold"), width=20)
        step1_bullet.grid(row=0, column=0, sticky="w")
        step1_text = ctk.CTkLabel(
            step1_frame, 
            text="Open Settings and configure the app to your liking",
            font=get_font_tuple("Blinker", 12),
            anchor="w"
        )
        step1_text.grid(row=0, column=1, sticky="w", padx=(5, 0))
        
        # Step 2
        step2_frame = ctk.CTkFrame(self, fg_color="transparent")
        step2_frame.grid(row=4, column=0, padx=30, pady=2, sticky="ew")
        step2_frame.grid_columnconfigure(1, weight=1)
        
        step2_bullet = ctk.CTkLabel(step2_frame, text="2.", font=get_font_tuple("Blinker", 12, "bold"), width=20)
        step2_bullet.grid(row=0, column=0, sticky="w")
        step2_text = ctk.CTkLabel(
            step2_frame, 
            text="Visit our documentation website to learn more and get help faster",
            font=get_font_tuple("Blinker", 12),
            anchor="w"
        )
        step2_text.grid(row=0, column=1, sticky="w", padx=(5, 0))
        
        # Step 3
        step3_frame = ctk.CTkFrame(self, fg_color="transparent")
        step3_frame.grid(row=5, column=0, padx=30, pady=2, sticky="ew")
        step3_frame.grid_columnconfigure(1, weight=1)
        
        step3_bullet = ctk.CTkLabel(step3_frame, text="3.", font=get_font_tuple("Blinker", 12, "bold"), width=20)
        step3_bullet.grid(row=0, column=0, sticky="w")
        step3_text = ctk.CTkLabel(
            step3_frame, 
            text="Need help? Contact the developer or report issues/start discussions",
            font=get_font_tuple("Blinker", 12),
            anchor="w"
        )
        step3_text.grid(row=0, column=1, sticky="w", padx=(5, 0))
        
        # Step 4
        step4_frame = ctk.CTkFrame(self, fg_color="transparent")
        step4_frame.grid(row=6, column=0, padx=30, pady=2, sticky="ew")
        step4_frame.grid_columnconfigure(1, weight=1)
        
        step4_bullet = ctk.CTkLabel(step4_frame, text="4.", font=get_font_tuple("Blinker", 12, "bold"), width=20)
        step4_bullet.grid(row=0, column=0, sticky="w")
        step4_text = ctk.CTkLabel(
            step4_frame, 
            text="⭐ Star the repository if you like the project!",
            font=get_font_tuple("Blinker", 12),
            anchor="w"
        )
        step4_text.grid(row=0, column=1, sticky="w", padx=(5, 0))
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        buttons_frame.grid(row=7, column=0, padx=20, pady=20, sticky="ew")
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        buttons_frame.grid_columnconfigure(2, weight=1)
        
        # Open Documentation button
        docs_btn = ctk.CTkButton(
            buttons_frame,
            text="Documentation",
            font=get_font_tuple("Blinker", 12),
            command=self._open_documentation,
            height=35
        )
        docs_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        # GitHub button
        github_btn = ctk.CTkButton(
            buttons_frame,
            text="GitHub",
            font=get_font_tuple("Blinker", 12),
            command=self._open_github,
            height=35
        )
        github_btn.grid(row=0, column=1, padx=5, sticky="ew")
        
        # Continue button
        continue_btn = ctk.CTkButton(
            buttons_frame,
            text="✨ Continue",
            font=get_font_tuple("Blinker", 12, "bold"),
            command=self._continue_to_app,
            height=35
        )
        continue_btn.grid(row=0, column=2, padx=(5, 0), sticky="ew")
        
        # Note at bottom
        note_label = ctk.CTkLabel(
            self,
            text="💡 You can show this welcome screen again by deleting the 'returning' file in the save folder.",
            font=get_font_tuple("Blinker", 10),
            text_color=("gray50", "gray50"),
            wraplength=450
        )
        note_label.grid(row=8, column=0, padx=20, pady=(0, 10), sticky="ew")
    
    def _open_documentation(self):
        """Open the documentation website"""
        try:
            webbrowser.open("https://intense-rp-next.readthedocs.io/en/latest/")
            print("Documentation opened in browser")
        except Exception as e:
            print(f"Error opening documentation: {e}")
    
    def _open_github(self):
        """Open the GitHub repository"""
        try:
            webbrowser.open("https://github.com/LyubomirT/intense-rp-next")
            print("GitHub repository opened in browser")
        except Exception as e:
            print(f"Error opening GitHub: {e}")
    
    def _continue_to_app(self):
        """Continue to the main application"""
        self.destroy()
    
    def center(self):
        """Center the window relative to parent"""
        self.update_idletasks()
        if self.parent:
            x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.winfo_width() // 2)
            y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.winfo_height() // 2)
            self.geometry(f"+{x}+{y}")


class GitUpdateDialog(ctk.CTkToplevel):
    """Dialog for git update instructions when running from source"""
    
    def __init__(self, parent, icon_path: Optional[str] = None):
        super().__init__(parent)
        self.parent = parent
        self.icon_path = icon_path
        self._create_window()
        self._create_widgets()
        if self.icon_path:
            self.after(300, lambda: set_window_icon(self, self.icon_path))
    
    def _create_window(self):
        """Set up the window properties"""
        self.title("Update via Git")
        self.geometry("450x300")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
    
    def _create_widgets(self):
        """Create and layout all widgets"""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Update via Git",
            font=get_font_tuple("Blinker", 18, "bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        # Instructions
        instructions = ctk.CTkLabel(
            self,
            text="To update your source build of IntenseRP Next:",
            font=get_font_tuple("Blinker", 12),
            text_color=("gray50", "gray70")
        )
        instructions.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="ew")
        
        # Command frame
        cmd_frame = ctk.CTkFrame(self)
        cmd_frame.grid(row=2, column=0, padx=20, pady=(0, 15), sticky="ew")
        cmd_frame.grid_columnconfigure(0, weight=1)
        
        # Command label
        cmd_label = ctk.CTkLabel(
            cmd_frame,
            text="Run this command in your project directory:",
            font=get_font_tuple("Blinker", 11),
            anchor="w"
        )
        cmd_label.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="ew")
        
        # Command text (selectable)
        cmd_text = ctk.CTkEntry(
            cmd_frame,
            font=get_font_tuple("Consolas", 11),
            justify="center"
        )
        cmd_text.insert(0, "git pull origin main")
        cmd_text.configure(state="readonly")
        cmd_text.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="ew")
        
        # Warning
        warning_label = ctk.CTkLabel(
            self,
            text="⚠ Make sure to restart the application after updating!",
            font=get_font_tuple("Blinker", 11, "bold"),
            text_color=("orange", "orange")
        )
        warning_label.grid(row=3, column=0, padx=20, pady=(0, 15), sticky="ew")
        
        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        # Run command button (if possible)
        try:
            import subprocess
            run_btn = ctk.CTkButton(
                button_frame,
                text="Run Command",
                command=self._run_git_pull,
                font=get_font_tuple("Blinker", 12, "bold"),
                height=35
            )
            run_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        except ImportError:
            pass
        
        # Close button
        close_btn = ctk.CTkButton(
            button_frame,
            text="Close",
            command=self.destroy,
            font=get_font_tuple("Blinker", 12),
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            height=35
        )
        close_btn.grid(row=0, column=1, padx=(5, 0), sticky="ew")
    
    def _run_git_pull(self):
        """Run git pull command"""
        try:
            import subprocess
            import os
            
            # Get current working directory (should be the project root)
            project_dir = os.getcwd()
            
            # Run git pull
            result = subprocess.run(
                ["git", "pull", "origin", "main"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Success
                from tkinter import messagebox
                messagebox.showinfo(
                    "Update Successful",
                    "Git update completed successfully!\n\n"
                    "Please restart the application to use the updated version."
                )
                self.destroy()
                # Close the parent download options window too
                if self.parent:
                    self.parent.destroy()
            else:
                # Error
                from tkinter import messagebox
                messagebox.showerror(
                    "Update Failed",
                    f"Git update failed:\n\n{result.stderr}"
                )
        except subprocess.TimeoutExpired:
            from tkinter import messagebox
            messagebox.showerror("Update Failed", "Git command timed out.")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Update Failed", f"Error running git command: {e}")
    
    def center(self):
        """Center the window relative to parent"""
        self.update_idletasks()
        if self.parent:
            x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.winfo_width() // 2)
            y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.winfo_height() // 2)
            self.geometry(f"+{x}+{y}")