from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
import threading
from enum import Enum

class StateEvent(Enum):
    BROWSER_STARTED = "browser_started"
    BROWSER_STOPPED = "browser_stopped"
    CONFIG_UPDATED = "config_updated"
    MESSAGE_LOGGED = "message_logged"
    RESPONSE_GENERATED = "response_generated"
    TUNNEL_STARTED = "tunnel_started"
    TUNNEL_STOPPED = "tunnel_stopped"
    TUNNEL_URL_READY = "tunnel_url_ready"
    TUNNEL_ERROR = "tunnel_error"

@dataclass
class StateChange:
    event_type: StateEvent
    data: Any = None
    timestamp: float = None

class StateManager:
    """Centralized state management for the application"""
    
    def __init__(self):
        self._lock = threading.RLock()
        self._observers: List[Callable[[StateChange], None]] = []
        
        # Browser state
        self._driver = None
        self._last_driver = 0
        self._last_response = 0
        
        # UI state
        self._textbox = None
        self._console_window = None
        self._config_window = None
        
        # Application state - now just a reference to external config manager
        self._config_manager = None
        self._logging_manager = None
        self._console_manager = None
        
        # Tunnel state
        self._tunnel_manager = None
        self._tunnel_url = None
        self._tunnel_active = False
        
        # Runtime state
        self._is_running = False
        
    # Observer pattern for state changes
    def subscribe(self, observer: Callable[[StateChange], None]) -> None:
        """Subscribe to state changes"""
        with self._lock:
            if observer not in self._observers:
                self._observers.append(observer)
    
    def unsubscribe(self, observer: Callable[[StateChange], None]) -> None:
        """Unsubscribe from state changes"""
        with self._lock:
            if observer in self._observers:
                self._observers.remove(observer)
    
    def _notify_observers(self, event_type: StateEvent, data: Any = None) -> None:
        """Notify all observers of state change"""
        import time
        change = StateChange(event_type, data, time.time())
        
        # Make a copy to avoid issues if observers list changes during iteration
        with self._lock:
            observers_copy = self._observers.copy()
        
        for observer in observers_copy:
            try:
                observer(change)
            except Exception as e:
                print(f"Error notifying observer: {e}")
    
    # Browser state management
    @property
    def driver(self):
        with self._lock:
            return self._driver
    
    @driver.setter
    def driver(self, value):
        with self._lock:
            old_value = self._driver
            self._driver = value
            
            if old_value is None and value is not None:
                self._notify_observers(StateEvent.BROWSER_STARTED, value)
            elif old_value is not None and value is None:
                self._notify_observers(StateEvent.BROWSER_STOPPED, old_value)
    
    @property
    def last_driver(self) -> int:
        with self._lock:
            return self._last_driver
    
    @last_driver.setter
    def last_driver(self, value: int):
        with self._lock:
            self._last_driver = value
    
    @property
    def last_response(self) -> int:
        with self._lock:
            return self._last_response
    
    @last_response.setter
    def last_response(self, value: int):
        with self._lock:
            self._last_response = value
            self._notify_observers(StateEvent.RESPONSE_GENERATED, value)
    
    def increment_response_id(self) -> int:
        """Atomically increment and return the response ID"""
        with self._lock:
            self._last_response += 1
            self._notify_observers(StateEvent.RESPONSE_GENERATED, self._last_response)
            return self._last_response
    
    def increment_driver_id(self) -> int:
        """Atomically increment and return the driver ID"""
        with self._lock:
            self._last_driver += 1
            return self._last_driver
    
    # UI state management
    @property
    def textbox(self):
        with self._lock:
            return self._textbox
    
    @textbox.setter
    def textbox(self, value):
        with self._lock:
            self._textbox = value
    
    @property
    def console_window(self):
        with self._lock:
            return self._console_window
    
    @console_window.setter
    def console_window(self, value):
        with self._lock:
            self._console_window = value
    
    @property
    def config_window(self):
        with self._lock:
            return self._config_window
    
    @config_window.setter
    def config_window(self, value):
        with self._lock:
            self._config_window = value
    
    # Configuration management - now delegated to ConfigManager
    def set_config_manager(self, config_manager) -> None:
        """Set the external config manager"""
        with self._lock:
            self._config_manager = config_manager
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get configuration (backward compatibility)"""
        if self._config_manager:
            return self._config_manager.get_all()
        return {}
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update configuration and notify observers (backward compatibility)"""
        if self._config_manager:
            for key, value in new_config.items():
                self._config_manager.set(key, value)
            self._notify_observers(StateEvent.CONFIG_UPDATED, self._config_manager.get_all())
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """Replace entire configuration (backward compatibility)"""
        if self._config_manager:
            # Clear and rebuild config
            for key, value in config.items():
                self._config_manager.set(key, value)
            self._notify_observers(StateEvent.CONFIG_UPDATED, self._config_manager.get_all())
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a specific config value with dotted notation (e.g., 'models.deepseek.email')"""
        if self._config_manager:
            return self._config_manager.get(key, default)
        return default
    
    def set_config_value(self, key: str, value: Any) -> None:
        """Set a specific config value with dotted notation"""
        if self._config_manager:
            self._config_manager.set(key, value)
            self._notify_observers(StateEvent.CONFIG_UPDATED, self._config_manager.get_all())
    
    # Logging manager
    @property
    def logging_manager(self):
        with self._lock:
            return self._logging_manager
    
    @logging_manager.setter
    def logging_manager(self, value):
        with self._lock:
            self._logging_manager = value

    @property
    def console_manager(self):
        with self._lock:
            return self._console_manager
    
    @console_manager.setter
    def console_manager(self, value):
        with self._lock:
            self._console_manager = value
    
    # Tunnel management
    @property
    def tunnel_manager(self):
        with self._lock:
            return self._tunnel_manager
    
    @tunnel_manager.setter
    def tunnel_manager(self, value):
        with self._lock:
            self._tunnel_manager = value
    
    def initialize_tunnel_manager(self):
        """Initialize tunnel manager with callbacks"""
        if self._tunnel_manager is None:
            from utils.tunnel_manager import get_tunnel_manager
            with self._lock:
                self._tunnel_manager = get_tunnel_manager()
                # Set up callbacks to update state
                self._tunnel_manager.set_callbacks(
                    url_callback=self._on_tunnel_url,
                    error_callback=self._on_tunnel_error
                )
    
    def _on_tunnel_url(self, url: str):
        """Callback for when tunnel URL becomes available"""
        with self._lock:
            self._tunnel_url = url
            self._tunnel_active = True
        
        # Display tunnel URL in console
        self.show_message(f"[color:yellow]Tunnel URL: [color:white]{url}")
        self._notify_observers(StateEvent.TUNNEL_URL_READY, url)
    
    def _on_tunnel_error(self, error_message: str):
        """Callback for tunnel errors"""
        with self._lock:
            self._tunnel_active = False
            self._tunnel_url = None
        
        # Display tunnel error in console
        self.show_message(f"[color:red]Tunnel Error: {error_message}")
        self._notify_observers(StateEvent.TUNNEL_ERROR, error_message)
    
    def start_tunnel(self, port: int = None) -> bool:
        """Start tunnel for the specified port"""
        if port is None:
            port = self.get_config_value('api.port', 5000)
        
        self.initialize_tunnel_manager()
        
        with self._lock:
            if self._tunnel_active:
                return False  # Already active
            
            if self._tunnel_manager:
                success = self._tunnel_manager.start_tunnel(port)
                if success:
                    self._notify_observers(StateEvent.TUNNEL_STARTED, port)
                return success
        return False
    
    def stop_tunnel(self) -> bool:
        """Stop the active tunnel"""
        with self._lock:
            if self._tunnel_manager and self._tunnel_active:
                success = self._tunnel_manager.stop_tunnel()
                if success:
                    self._tunnel_active = False
                    self._tunnel_url = None
                    self._notify_observers(StateEvent.TUNNEL_STOPPED, None)
                return success
        return True
    
    def get_tunnel_url(self) -> Optional[str]:
        """Get the current tunnel URL"""
        with self._lock:
            return self._tunnel_url if self._tunnel_active else None
    
    def is_tunnel_active(self) -> bool:
        """Check if tunnel is active"""
        with self._lock:
            return self._tunnel_active
    
    def get_tunnel_status(self) -> Dict[str, Any]:
        """Get tunnel status information"""
        with self._lock:
            if self._tunnel_manager:
                status = self._tunnel_manager.get_tunnel_status()
                # Add state manager's view of tunnel status
                status['state_manager_active'] = self._tunnel_active
                status['state_manager_url'] = self._tunnel_url
                return status
            else:
                return {
                    'active': False,
                    'url': None,
                    'port': None,
                    'error': None,
                    'state_manager_active': self._tunnel_active,
                    'state_manager_url': self._tunnel_url
                }
    
    # Application lifecycle
    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._is_running
    
    @is_running.setter
    def is_running(self, value: bool):
        with self._lock:
            self._is_running = value
    
    # Utility methods
    def show_message(self, text: str) -> None:
        """Show message in textbox and console if available"""
        textbox = self.textbox
        logging_manager = self.logging_manager
        console_manager = self.console_manager
        
        try:
            # Show in main textbox
            if textbox:
                textbox.colored_add(text)
            
            # Show in console if it exists and is different from main textbox
            if console_manager and console_manager.console_textbox and console_manager.console_textbox != textbox:
                console_manager.add_message(text)
            
            # Log to file
            if logging_manager:
                logging_manager.log_message(text)
                
            self._notify_observers(StateEvent.MESSAGE_LOGGED, text)
        except Exception as e:
            print(f"Error showing message: {e}")
    
    def clear_messages(self) -> None:
        """Clear messages in textbox and console if available"""
        textbox = self.textbox
        console_manager = self.console_manager
        
        try:
            if textbox:
                textbox.clear()
                
            if console_manager:
                console_manager.clear()
        except Exception as e:
            print(f"Error clearing messages: {e}")
    
    def reset_browser_state(self) -> None:
        """Reset browser-related state"""
        with self._lock:
            if self._driver:
                try:
                    self._driver.quit()
                except Exception:
                    pass
            
            self._driver = None
            self._last_response = 0
            
            # Also stop tunnel if active
            if self._tunnel_active and self._tunnel_manager:
                try:
                    self._tunnel_manager.stop_tunnel()
                    self._tunnel_active = False
                    self._tunnel_url = None
                except Exception:
                    pass
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get a summary of current state for debugging"""
        with self._lock:
            config_summary = {}
            if self._config_manager:
                try:
                    config_summary = self._config_manager.get_config_summary()
                except Exception:
                    config_summary = {"error": "Failed to get config summary"}
            
            tunnel_status = self.get_tunnel_status() if self._tunnel_manager else {'active': False}
            
            return {
                'has_driver': self._driver is not None,
                'driver_id': self._last_driver,
                'response_id': self._last_response,
                'has_textbox': self._textbox is not None,
                'has_console_manager': self._console_manager is not None,
                'has_config_manager': self._config_manager is not None,
                'has_tunnel_manager': self._tunnel_manager is not None,
                'tunnel_status': tunnel_status,
                'config_summary': config_summary,
                'is_running': self._is_running,
                'observer_count': len(self._observers)
            }

# Global singleton instance
_state_manager_instance = None
_state_manager_lock = threading.Lock()

def get_state_manager() -> StateManager:
    """Get the global state manager instance (singleton)"""
    global _state_manager_instance
    
    if _state_manager_instance is None:
        with _state_manager_lock:
            if _state_manager_instance is None:
                _state_manager_instance = StateManager()
    
    return _state_manager_instance

def reset_state_manager() -> None:
    """Reset the global state manager (mainly for testing)"""
    global _state_manager_instance
    with _state_manager_lock:
        if _state_manager_instance:
            _state_manager_instance.reset_browser_state()
        _state_manager_instance = None