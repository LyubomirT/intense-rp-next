"""
Automatic UI generation for configuration windows
Generates UI from configuration schema
"""

from typing import Dict, Any, Optional, Callable
import utils.gui_builder as gui_builder
from utils.font_loader import get_font_tuple
from config.config_schema import get_config_schema, ConfigFieldType, ConfigField
from config.config_manager import ConfigManager, ConfigValidationError
from config.config_validators import ConditionalValidator


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
            width=750,
            height=500,
            min_width=650,
            min_height=450,
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
        
        frame.create_entry(
            id=field.key,
            label_text=field.label,
            default_value=display_value,
            row=row,
            row_grid=True,
            tooltip=field.help_text
        )
    
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
        
        frame.create_button(
            id=field.key or f"{field.label.lower().replace(' ', '_')}_btn",
            text=field.label,
            command=command,
            row=row,
            row_grid=True,
            tooltip=field.help_text
        )
    
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
            preset = self.config_manager.get('formatting.preset', 'Classic')
            
            # Always store the actual config value as custom content
            textbox._custom_content = display_value
            
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
    
    def _update_textarea_state(self, preset_value: str) -> None:
        """Update textarea state based on preset selection"""
        # Get current preset to know if we're switching FROM Custom
        current_preset = self.config_manager.get('formatting.preset', 'Classic')
        
        # Find both formatting template textareas
        for section in get_config_schema():
            frame = self.frames.get(section.id)
            if not frame:
                continue
                
            user_textarea = frame.get_widget("formatting.user_template")
            char_textarea = frame.get_widget("formatting.char_template")
            
            if preset_value == "Custom":
                # Enable textareas and restore custom content
                for textarea in [user_textarea, char_textarea]:
                    if textarea:
                        textarea.configure(
                            state="normal",
                            text_color=("black", "white")  # Restore normal text color
                        )
                        # Restore custom content if it exists
                        if hasattr(textarea, '_custom_content'):
                            textarea.delete("0.0", "end")
                            textarea.insert("0.0", textarea._custom_content)
            else:
                # Show preset content
                preset_templates = self._get_preset_templates(preset_value)
                
                if user_textarea:
                    # Only save content if we're switching FROM Custom (real content)
                    if current_preset == "Custom":
                        user_textarea._custom_content = user_textarea.get("0.0", "end").rstrip('\n')
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
                    # Only save content if we're switching FROM Custom (real content)
                    if current_preset == "Custom":
                        char_textarea._custom_content = char_textarea.get("0.0", "end").rstrip('\n')
                    # Enable first, then modify content, then disable
                    char_textarea.configure(state="normal")
                    char_textarea.delete("0.0", "end")
                    char_textarea.insert("0.0", preset_templates['char'])
                    # Now disable with visual styling
                    char_textarea.configure(
                        state="disabled",
                        text_color=("gray60", "gray40")
                    )
    
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
            command=self.window.destroy,
            width=80,
            font=get_font_tuple("Blinker", 14)
        )
        cancel_button.grid(row=0, column=1, padx=5, pady=5, sticky="w")
    
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
                        
                        # Special handling for formatting textareas - save custom content
                        if field.key in ["formatting.user_template", "formatting.char_template"] and widget:
                            if hasattr(widget, '_custom_content'):
                                widget_value = widget._custom_content
                        
                        if widget_value is not None:
                            processed_value = self._convert_ui_value(field, widget_value)
                            self.config_manager.set(field.key, processed_value)
            
            # Save without additional validation (already validated)
            try:
                self.config_manager.storage_manager.save_config(
                    path_root="executable",
                    sub_path="save", 
                    new=self.config_manager._config,
                    original=self.config_manager._original_config
                )
                print("Configuration saved successfully.")
                self.window.destroy()
            except Exception as e:
                print(f"Error saving configuration: {e}")
                
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
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
        
        # Mark fields mentioned in errors
        for error in errors:
            self._mark_field_error_by_message(error)
    
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
        """Mark a field as having an error based on error message"""
        # Map error messages to field keys - improved mapping
        error_mapping = {
            "models.deepseek.email": ["email", "Email"],
            "models.deepseek.password": ["password", "Password"],
            "logging.max_file_size": ["Max file size", "file size", "File size"],
            "logging.max_files": ["Max files", "max files", "Files"],
        }
        
        for field_key, keywords in error_mapping.items():
            if any(keyword in error_message for keyword in keywords):
                self._mark_field_error(field_key)
                break
    
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
                    return