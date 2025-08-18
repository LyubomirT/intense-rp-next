"""
Automatic UI generation for configuration windows
Generates UI from configuration schema
"""

from typing import Dict, Any, Optional, Callable
import utils.gui_builder as gui_builder
from utils.font_loader import get_font_tuple
from .config_schema import get_config_schema, ConfigFieldType, ConfigField, ValidationError
from .config_manager import ConfigManager, ConfigValidationError
from .config_validators import ConditionalValidator


class ConfigUIGenerator:
    """Generates configuration UI from schema"""
    
    def __init__(self, config_manager: ConfigManager, command_handlers: Optional[Dict[str, Callable]] = None):
        self.config_manager = config_manager
        self.command_handlers = command_handlers or {}
        self.window = None
        self.frames = {}
        
    def create_config_window(self, icon_path: Optional[str] = None) -> gui_builder.ConfigWindow:
        """Create the complete configuration window"""
        self.window = gui_builder.ConfigWindow()
        self.window.create(
            visible=True,
            title="Settings",
            width=900,
            height=600,
            min_width=800,
            min_height=550,
            icon=icon_path
        )
        
        # Generate sections from schema
        for section in get_config_schema():
            frame = self.window.create_section_frame(
                id=section.id,
                title=section.title,
                bg_color=("white", "gray20")
            )
            
            self.frames[section.id] = frame
            self._create_section_widgets(frame, section)
        
        # Create button section
        self._create_button_section()
        
        # Set initial active section
        first_section = get_config_schema()[0]
        self.window.set_active_section(first_section.id)
        
        return self.window
    
    def _create_section_widgets(self, frame: gui_builder.ConfigFrame, section) -> None:
        """Create widgets for a configuration section"""
        row = 0
        
        # Section title
        frame.create_title(
            id=f"{section.id}_title",
            text=section.title,
            row=row,
            row_grid=True
        )
        row += 1
        
        # Create fields
        for field in section.fields:
            if field.field_type == ConfigFieldType.TEXT:
                self._create_text_field(frame, field, row)
            elif field.field_type == ConfigFieldType.PASSWORD:
                self._create_password_field(frame, field, row)
            elif field.field_type == ConfigFieldType.SWITCH:
                self._create_switch_field(frame, field, row)
            elif field.field_type == ConfigFieldType.DROPDOWN:
                self._create_dropdown_field(frame, field, row)
            elif field.field_type == ConfigFieldType.BUTTON:
                self._create_button_field(frame, field, row)
            elif field.field_type == ConfigFieldType.TEXTAREA:
                self._create_textarea_field(frame, field, row)
            elif field.field_type == ConfigFieldType.DIVIDER:
                self._create_divider_field(frame, field, row)
            
            row += 1
    
    def _create_text_field(self, frame: gui_builder.ConfigFrame, field: ConfigField, row: int) -> None:
        """Create a text entry field"""
        current_value = self.config_manager.get(field.key, field.default)
        
        # Special handling for display conversion
        if field.validation == "file_size" and isinstance(current_value, int):
            from config.config_validators import ConfigValidator
            display_value = ConfigValidator.format_file_size(current_value)
        elif field.validation == "max_files" and isinstance(current_value, int):
            display_value = str(current_value)
        else:
            display_value = str(current_value) if current_value is not None else ""
        
        entry = frame.create_entry(
            id=field.key,
            label_text=field.label,
            default_value=display_value,
            row=row,
            row_grid=True,
            tooltip=field.help_text
        )
        
        # Special handling for browser path field - initially hide if not Custom Chromium
        if field.key == "browser_path":
            current_browser = self.config_manager.get('browser', 'Chrome')
            if current_browser != "Custom Chromium":
                entry.grid_remove()  # Actually hide the field
                entry.delete(0, "end")  # Clear the field
    
    def _create_password_field(self, frame: gui_builder.ConfigFrame, field: ConfigField, row: int) -> None:
        """Create a password field"""
        current_value = self.config_manager.get(field.key, field.default)
        display_value = str(current_value) if current_value is not None else ""
        
        frame.create_password(
            id=field.key,
            label_text=field.label,
            default_value=display_value,
            row=row,
            row_grid=True,
            tooltip=field.help_text
        )
    
    def _create_switch_field(self, frame: gui_builder.ConfigFrame, field: ConfigField, row: int) -> None:
        """Create a switch/toggle field"""
        current_value = self.config_manager.get(field.key, field.default)
        
        # Handle command callbacks
        command = None
        if field.command and field.command in self.command_handlers:
            command = self.command_handlers[field.command]
        
        frame.create_switch(
            id=field.key,
            label_text=field.label,
            default_value=bool(current_value),
            command=command,
            row=row,
            row_grid=True,
            tooltip=field.help_text
        )
    
    def _create_dropdown_field(self, frame: gui_builder.ConfigFrame, field: ConfigField, row: int) -> None:
        """Create a dropdown/option menu field"""
        current_value = self.config_manager.get(field.key, field.default)
        display_value = str(current_value) if current_value is not None else str(field.default)
        
        # Special handling for formatting preset dropdown
        if field.key == "formatting.preset":
            def on_preset_change(value):
                self._update_textarea_state(value)
            
            menu = frame.create_option_menu(
                id=field.key,
                label_text=field.label,
                default_value=display_value,
                options=field.options or [],
                row=row,
                row_grid=True,
                tooltip=field.help_text
            )
            
            # Configure callback for preset changes
            menu.configure(command=on_preset_change)
        # Special handling for browser dropdown
        elif field.key == "browser":
            def on_browser_change(value):
                self._update_browser_path_visibility(value)
            
            menu = frame.create_option_menu(
                id=field.key,
                label_text=field.label,
                default_value=display_value,
                options=field.options or [],
                row=row,
                row_grid=True,
                tooltip=field.help_text
            )
            
            # Configure callback for browser changes
            menu.configure(command=on_browser_change)
        else:
            frame.create_option_menu(
                id=field.key,
                label_text=field.label,
                default_value=display_value,
                options=field.options or [],
                row=row,
                row_grid=True,
                tooltip=field.help_text
            )
    
    def _create_button_field(self, frame: gui_builder.ConfigFrame, field: ConfigField, row: int) -> None:
        """Create a button field"""
        command = None
        if field.command and field.command in self.command_handlers:
            command = self.command_handlers[field.command]
        
        button = frame.create_button(
            id=field.key or f"{field.label.lower().replace(' ', '_')}_btn",
            text=field.label,
            command=command,
            row=row,
            row_grid=True,
            tooltip=field.help_text
        )
        
        # Special handling for browser path browse button - initially hide if not Custom Chromium
        if field.key == "browser_path_browse":
            current_browser = self.config_manager.get('browser', 'Chrome')
            if current_browser != "Custom Chromium":
                button.grid_remove()  # Actually hide the button
    
    def _create_textarea_field(self, frame: gui_builder.ConfigFrame, field: ConfigField, row: int) -> None:
        """Create a textarea field"""
        current_value = self.config_manager.get(field.key, field.default)
        display_value = str(current_value) if current_value is not None else ""
        
        textbox = frame.create_textarea(
            id=field.key,
            label_text=field.label,
            default_value=display_value,
            row=row,
            row_grid=True,
            tooltip=field.help_text
        )
        
        # Special handling for formatting template textareas
        if field.key in ["formatting.user_template", "formatting.char_template"]:
            # Set initial state based on current preset
            preset = self.config_manager.get('formatting.preset', 'Classic (Name)')
            
            if preset != 'Custom':
                # Show preset content instead of actual config value
                preset_templates = self._get_preset_templates(preset)
                template_key = 'user' if field.key == "formatting.user_template" else 'char'
                textbox.delete("0.0", "end")
                textbox.insert("0.0", preset_templates[template_key])
                # Disable with visual styling
                textbox.configure(
                    state="disabled",
                    text_color=("gray60", "gray40")
                )
            else:
                # In Custom mode, load from hidden variables
                hidden_key = 'custom_user_template' if field.key == "formatting.user_template" else 'custom_char_template'
                custom_content = self.config_manager.get_hidden_var(hidden_key, "{name}: {content}")
                textbox.delete("0.0", "end")
                textbox.insert("0.0", custom_content)
    
    def _create_divider_field(self, frame: gui_builder.ConfigFrame, field: ConfigField, row: int) -> None:
        """Create a divider field for visual separation"""
        import customtkinter as ctk
        
        # Create a container frame for the divider
        divider_frame = ctk.CTkFrame(frame, fg_color="transparent")
        divider_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(10, 10), padx=15)
        divider_frame.grid_columnconfigure(0, weight=1)
        
        if field.label and field.label.strip():
            # Divider with text
            divider_frame.grid_columnconfigure(1, weight=0)
            divider_frame.grid_columnconfigure(2, weight=1)
            
            # Left line
            left_line = ctk.CTkFrame(divider_frame, height=1, fg_color=("gray70", "gray30"))
            left_line.grid(row=0, column=0, sticky="ew", pady=10)
            
            # Text label
            divider_label = ctk.CTkLabel(
                divider_frame, 
                text=field.label,
                font=get_font_tuple("Blinker", 12),
                text_color=("gray60", "gray40")
            )
            divider_label.grid(row=0, column=1, padx=10)
            
            # Right line
            right_line = ctk.CTkFrame(divider_frame, height=1, fg_color=("gray70", "gray30"))
            right_line.grid(row=0, column=2, sticky="ew", pady=10)
        else:
            # Plain divider line
            divider_line = ctk.CTkFrame(divider_frame, height=1, fg_color=("gray70", "gray30"))
            divider_line.grid(row=0, column=0, sticky="ew", pady=10)
    
    def _update_textarea_state(self, preset_value: str) -> None:
        """Update textarea state based on preset selection"""
        # Get current preset to know if we're switching FROM Custom
        current_preset = self.config_manager.get('formatting.preset', 'Classic (Role)')
        
        # Find both formatting template textareas
        for section in get_config_schema():
            frame = self.frames.get(section.id)
            if not frame:
                continue
                
            user_textarea = frame.get_widget("formatting.user_template")
            char_textarea = frame.get_widget("formatting.char_template")
            
            if preset_value == "Custom":
                # Enable textareas and restore custom content from hidden variables
                if user_textarea:
                    user_textarea.configure(
                        state="normal",
                        text_color=("black", "white")  # Restore normal text color
                    )
                    custom_content = self.config_manager.get_hidden_var('custom_user_template', "{name}: {content}")
                    user_textarea.delete("0.0", "end")
                    user_textarea.insert("0.0", custom_content)
                    
                if char_textarea:
                    char_textarea.configure(
                        state="normal",
                        text_color=("black", "white")  # Restore normal text color
                    )
                    custom_content = self.config_manager.get_hidden_var('custom_char_template', "{name}: {content}")
                    char_textarea.delete("0.0", "end")
                    char_textarea.insert("0.0", custom_content)
            else:
                # Show preset content
                preset_templates = self._get_preset_templates(preset_value)
                
                if user_textarea:
                    # Save current content to hidden variables if switching FROM Custom
                    if current_preset == "Custom":
                        current_content = user_textarea.get("0.0", "end").rstrip('\n')
                        self.config_manager.set_hidden_var('custom_user_template', current_content)
                    # Enable first, then modify content, then disable
                    user_textarea.configure(state="normal")
                    user_textarea.delete("0.0", "end")
                    user_textarea.insert("0.0", preset_templates['user'])
                    # Now disable with visual styling
                    user_textarea.configure(
                        state="disabled",
                        text_color=("gray60", "gray40")
                    )
                
                if char_textarea:
                    # Save current content to hidden variables if switching FROM Custom
                    if current_preset == "Custom":
                        current_content = char_textarea.get("0.0", "end").rstrip('\n')
                        self.config_manager.set_hidden_var('custom_char_template', current_content)
                    # Enable first, then modify content, then disable
                    char_textarea.configure(state="normal")
                    char_textarea.delete("0.0", "end")
                    char_textarea.insert("0.0", preset_templates['char'])
                    # Now disable with visual styling
                    char_textarea.configure(
                        state="disabled",
                        text_color=("gray60", "gray40")
                    )
    
    def _update_browser_path_visibility(self, browser_value: str) -> None:
        """Update browser path field visibility based on browser selection"""
        # Find the browser path field and browse button in the advanced settings section
        for section in get_config_schema():
            frame = self.frames.get(section.id)
            if not frame:
                continue
                
            browser_path_widget = frame.get_widget("browser_path")
            browse_button_widget = frame.get_widget("browser_path_browse")
            
            if browser_path_widget:
                if browser_value == "Custom Chromium":
                    # Show the browser path field
                    browser_path_widget.configure(state="normal")
                    browser_path_widget.grid()  # Make sure it's in the grid
                    # Show the browse button if it exists
                    if browse_button_widget:
                        browse_button_widget.configure(state="normal")
                        browse_button_widget.grid()  # Make sure it's in the grid
                else:
                    # Actually hide the browser path field
                    browser_path_widget.grid_remove()  # Remove from grid layout
                    browser_path_widget.delete(0, "end")  # Clear the field
                    # Actually hide the browse button if it exists
                    if browse_button_widget:
                        browse_button_widget.grid_remove()  # Remove from grid layout
                break
    
    def _get_preset_templates(self, preset: str) -> dict:
        """Get the templates for a specific preset"""
        from processors.character_processor import MessageFormatter
        
        if preset in MessageFormatter.PRESETS:
            preset_config = MessageFormatter.PRESETS[preset]
            return {
                'user': preset_config['pattern'],
                'char': preset_config['pattern']
            }
        else:
            # Fallback
            return {
                'user': '{role}: {content}',
                'char': '{role}: {content}'
            }
    
    def _create_button_section(self) -> None:
        """Create the save/cancel button section"""
        button_container = self.window.create_button_section()
        button_container.grid_columnconfigure(0, weight=1)
        button_container.grid_columnconfigure(1, weight=1)
        
        save_button = gui_builder.ctk.CTkButton(
            button_container,
            text="Save",
            command=self._save_config,
            width=80,
            font=get_font_tuple("Blinker", 14)
        )
        save_button.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        
        cancel_button = gui_builder.ctk.CTkButton(
            button_container,
            text="Cancel",
            command=self._cancel_config,
            width=80,
            font=get_font_tuple("Blinker", 14)
        )
        cancel_button.grid(row=0, column=1, padx=5, pady=5, sticky="w")
    
    def _cancel_config(self) -> None:
        """Cancel configuration and close window"""
        self._clear_ui_generator_reference()
        self.window.destroy()
    
    def _save_config(self) -> None:
        """Save configuration from UI"""
        try:
            validation_errors = []
            
            # Get current UI state for conditional validation
            ui_config = self._get_ui_config_state()
            
            # First pass: validate user input before conversion
            for section in get_config_schema():
                frame = self.frames.get(section.id)
                if not frame:
                    continue
                
                for field in section.fields:
                    if field.validation and field.key:
                        widget_value = frame.get_widget_value(field.key)
                        if widget_value is not None:
                            # Check if we should validate this field based on current UI state
                            if self._should_validate_field_ui(field, ui_config):
                                # Validate the user input (string format)
                                errors = self.config_manager.validator.validate_field(field, widget_value, ui_config)
                                validation_errors.extend(errors)
            
            if validation_errors:
                self._mark_validation_errors(validation_errors)
                return
            
            # Second pass: convert and store values
            for section in get_config_schema():
                frame = self.frames.get(section.id)
                if not frame:
                    continue
                
                for field in section.fields:
                    if field.key:  # Skip buttons without keys
                        widget = frame.get_widget(field.key)
                        widget_value = frame.get_widget_value(field.key)
                        
                        # Special handling for formatting textareas - save to hidden variables if in Custom mode
                        if field.key in ["formatting.user_template", "formatting.char_template"] and widget:
                            preset = self.config_manager.get('formatting.preset', 'Classic (Name)')
                            if preset == "Custom":
                                # Save current textarea content to hidden variables
                                current_content = widget.get("0.0", "end").rstrip('\n')
                                hidden_key = 'custom_user_template' if field.key == "formatting.user_template" else 'custom_char_template'
                                self.config_manager.set_hidden_var(hidden_key, current_content)
                        
                        if widget_value is not None:
                            processed_value = self._convert_ui_value(field, widget_value)
                            self.config_manager.set(field.key, processed_value)
            
            # Save without additional validation (already validated)
            try:
                self.config_manager.save()
                
                # Apply console settings immediately after saving
                self._apply_console_settings_after_save()
                
                # Clear reference to this UI generator
                self._clear_ui_generator_reference()
                
                self.window.destroy()
            except Exception as e:
                print(f"Error saving configuration: {e}")
                
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def _apply_console_settings_after_save(self) -> None:
        """Apply console settings immediately after saving configuration"""
        try:
            from core import get_state_manager
            import utils.console_manager as console_manager
            
            state = get_state_manager()
            if hasattr(state, 'console_manager') and state.console_manager:
                # Get the newly saved config
                new_settings = console_manager.ConsoleSettings(self.config_manager.get_all())
                state.console_manager.update_settings(new_settings)
                print("[color:green]Console settings applied automatically after save")
        except Exception as e:
            print(f"Error applying console settings after save: {e}")
    
    def _clear_ui_generator_reference(self) -> None:
        """Clear reference to this UI generator from state manager"""
        try:
            from core import get_state_manager
            
            state = get_state_manager()
            if hasattr(state, 'current_ui_generator') and state.current_ui_generator is self:
                state.current_ui_generator = None
        except Exception as e:
            print(f"Error clearing UI generator reference: {e}")
    
    def _get_ui_config_state(self) -> dict:
        """Get current UI state as config dict for validation"""
        ui_config = {}
        
        for section in get_config_schema():
            frame = self.frames.get(section.id)
            if not frame:
                continue
            
            for field in section.fields:
                if field.key:
                    widget_value = frame.get_widget_value(field.key)
                    if widget_value is not None:
                        # Build nested structure
                        keys = field.key.split('.')
                        current = ui_config
                        
                        for key in keys[:-1]:
                            if key not in current:
                                current[key] = {}
                            current = current[key]
                        
                        # For switches, convert to boolean for conditional checks
                        if field.field_type == ConfigFieldType.SWITCH:
                            current[keys[-1]] = bool(widget_value)
                        else:
                            current[keys[-1]] = widget_value
        
        return ui_config
    
    def _should_validate_field_ui(self, field: ConfigField, ui_config: dict) -> bool:
        """Check if field should be validated based on current UI state"""
        # Logging fields should only be validated if logging is enabled
        if field.key and field.key.startswith("logging.") and field.key != "logging.enabled":
            logging_enabled = ui_config.get("logging", {}).get("enabled", False)
            return logging_enabled
        
        # DeepSeek auth fields should only be validated if auto_login is enabled
        if field.key in ["models.deepseek.email", "models.deepseek.password"]:
            auto_login = ui_config.get("models", {}).get("deepseek", {}).get("auto_login", False)
            return auto_login
        
        # Dump directory should only be validated if console dumping is enabled
        if field.key == "console.dump_directory":
            dump_enabled = ui_config.get("console", {}).get("dump_enabled", False)
            return dump_enabled
        
        # API keys should only be validated if API authentication is enabled
        if field.key == "security.api_keys":
            api_auth_enabled = ui_config.get("security", {}).get("api_auth_enabled", False)
            return api_auth_enabled
        
        # Browser path should only be validated if Custom Chromium is selected
        if field.key == "browser_path":
            browser = ui_config.get("browser", "Chrome")
            return browser == "Custom Chromium"
        
        # By default, validate the field
        return True
    
    def _convert_ui_value(self, field: ConfigField, ui_value: str) -> Any:
        """Convert UI string value to appropriate type"""
        if field.field_type == ConfigFieldType.SWITCH:
            return bool(ui_value)
        elif field.validation == "file_size":
            # Parse the human-readable format to bytes for storage (original behavior)
            from config.config_validators import ConfigValidator
            return ConfigValidator._parse_file_size(ui_value.strip())
        elif field.validation == "max_files":
            # Convert to integer for storage (original behavior)
            return int(ui_value.strip())
        elif field.field_type == ConfigFieldType.DROPDOWN and field.key == "console.font_size":
            return int(ui_value)
        else:
            return ui_value
    
    def _mark_validation_errors(self, errors: list) -> None:
        """Mark fields with validation errors"""
        # Reset all field colors first
        self._reset_field_colors()
        
        # Mark fields with errors using field keys directly
        for error in errors:
            if isinstance(error, ValidationError):
                if error.field and error.field.highlight_errors:
                    self._mark_field_error(error.field_key)
            else:
                # Fallback for legacy string errors (should not happen with new system)
                self._mark_field_error_by_message(error)
        
        # Show error messages to user
        self._show_validation_errors(errors)
    
    def _reset_field_colors(self) -> None:
        """Reset all field border colors to normal"""
        for section in get_config_schema():
            frame = self.frames.get(section.id)
            if not frame:
                continue
            
            for field in section.fields:
                if field.key and field.field_type in [ConfigFieldType.TEXT, ConfigFieldType.PASSWORD, ConfigFieldType.TEXTAREA]:
                    widget = frame.get_widget(field.key)
                    if widget:
                        widget.configure(border_color="gray")
    
    def _mark_field_error_by_message(self, error_message: str) -> None:
        """Legacy fallback method for marking field errors by message (deprecated)"""
        # This method is kept for backward compatibility but should not be used
        # with the new ValidationError system. New code should use field keys directly.
        # 
        # If this method is called, it means there's still some old-style validation
        # that returns string errors instead of ValidationError objects.
        print(f"[color:yellow]Warning: Using deprecated error message matching for: {error_message}")
        
        # Basic fallback - try to extract field information from error message
        # This is much simpler than the old keyword mapping but less reliable
        if "email" in error_message.lower():
            self._mark_field_error("models.deepseek.email")
        elif "password" in error_message.lower():
            self._mark_field_error("models.deepseek.password")
        elif "file size" in error_message.lower():
            self._mark_field_error("logging.max_file_size")
        elif "max files" in error_message.lower():
            self._mark_field_error("logging.max_files")
        elif "directory" in error_message.lower():
            self._mark_field_error("console.dump_directory")
        elif "port" in error_message.lower():
            self._mark_field_error("api.port")
        elif "api key" in error_message.lower():
            self._mark_field_error("security.api_keys")
        elif "browser" in error_message.lower():
            self._mark_field_error("browser_path")
        elif "idle timeout" in error_message.lower():
            self._mark_field_error("refresh_timer.idle_timeout")
        elif "grace period" in error_message.lower():
            self._mark_field_error("refresh_timer.grace_period")
    
    def _mark_field_error(self, field_key: str) -> None:
        """Mark a specific field as having an error"""
        # Find the frame containing this field
        for section in get_config_schema():
            frame = self.frames.get(section.id)
            if not frame:
                continue
            
            for field in section.fields:
                if field.key == field_key:
                    widget = frame.get_widget(field_key)
                    
                    if widget and hasattr(widget, 'configure'):
                        widget.configure(border_color="red")
                        
                        # For textarea, make border thicker to be more visible
                        if field.field_type == ConfigFieldType.TEXTAREA:
                            try:
                                widget.configure(border_width=2)
                            except Exception:
                                pass  # Ignore if border_width not supported
                    return
    
    def _show_validation_errors(self, errors: list) -> None:
        """Show validation errors to the user"""
        try:
            import tkinter.messagebox as messagebox
            
            # Extract error messages from ValidationError objects
            error_messages = []
            for error in errors:
                if isinstance(error, ValidationError):
                    error_messages.append(error.message)
                else:
                    error_messages.append(str(error))
            
            if len(error_messages) == 1:
                title = "Configuration Error"
                message = f"Please fix the following issue:\n\n{error_messages[0]}"
            else:
                title = "Configuration Errors"
                message = f"Please fix the following issues:\n\n" + "\n".join(f"• {error}" for error in error_messages)
            
            # ConfigWindow inherits from CTkToplevel, so use self.window directly as parent
            parent_window = self.window if self.window else None
            
            # Show dialog on top of the settings window
            messagebox.showerror(title, message, parent=parent_window)
            
        except Exception as e:
            # Fallback: print to console
            print("[color:yellow]Settings validation errors:")
            for error in errors:
                if isinstance(error, ValidationError):
                    print(f"  - {error.message}")
                else:
                    print(f"  - {error}")