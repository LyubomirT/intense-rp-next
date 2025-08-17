"""
Refresh Timer Module for IntenseRP API
Handles automatic page refresh when idle to prevent session timeouts
"""

import threading
import time
from typing import Optional, Callable
from core import get_state_manager


class RefreshTimer:
    """
    Manages automatic page refresh based on activity tracking.
    
    This class implements a two-stage timer system:
    1. Idle timeout: Wait for configured minutes of inactivity
    2. Grace period: Wait additional seconds before actually refreshing
    
    The timer resets whenever activity is detected.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._timer_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_activity_time = time.time()
        self._is_running = False
        self._in_grace_period = False
        
        # Callbacks
        self._refresh_callback: Optional[Callable] = None
        self._grace_period_start_callback: Optional[Callable] = None
        
    def start(self, refresh_callback: Callable, grace_period_start_callback: Optional[Callable] = None) -> None:
        """
        Start the refresh timer.
        
        Args:
            refresh_callback: Function to call when refresh should happen
            grace_period_start_callback: Optional function to call when grace period starts
        """
        with self._lock:
            if self._is_running:
                return
            
            self._refresh_callback = refresh_callback
            self._grace_period_start_callback = grace_period_start_callback
            self._stop_event.clear()
            self._last_activity_time = time.time()
            self._in_grace_period = False
            self._is_running = True
            
            # Start timer thread
            self._timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
            self._timer_thread.start()
            
            print("[color:green]Refresh timer started")
    
    def stop(self) -> None:
        """Stop the refresh timer."""
        with self._lock:
            if not self._is_running:
                return
            
            self._is_running = False
            self._stop_event.set()
            
            # Wait for thread to finish
            if self._timer_thread and self._timer_thread.is_alive():
                self._timer_thread.join(timeout=2.0)
            
            self._timer_thread = None
            self._in_grace_period = False
            
            print("[color:cyan]Refresh timer stopped")
    
    def record_activity(self) -> None:
        """Record user activity, resetting the timer."""
        with self._lock:
            if not self._is_running:
                return
            
            old_time = self._last_activity_time
            self._last_activity_time = time.time()
            
            # If we were in grace period, cancel it
            if self._in_grace_period:
                self._in_grace_period = False
                print("[color:yellow]Activity detected during grace period - refresh cancelled")
            
            # Log activity for debugging (only if significant time has passed)
            if time.time() - old_time > 10:  # More than 10 seconds since last activity
                print(f"[color:blue]Activity recorded - refresh timer reset")
    
    def is_running(self) -> bool:
        """Check if the refresh timer is currently running."""
        with self._lock:
            return self._is_running
    
    def is_in_grace_period(self) -> bool:
        """Check if currently in grace period."""
        with self._lock:
            return self._in_grace_period
    
    def get_time_until_next_check(self) -> float:
        """Get seconds until next timer check (for debugging)."""
        with self._lock:
            if not self._is_running:
                return 0
            
            state = get_state_manager()
            # Convert to int/float to handle string values from config
            try:
                idle_timeout_minutes = int(state.get_config_value("refresh_timer.idle_timeout", 5))
            except (ValueError, TypeError):
                idle_timeout_minutes = 5  # Default fallback
            
            use_grace_period = state.get_config_value("refresh_timer.use_grace_period", True)
            idle_timeout_seconds = idle_timeout_minutes * 60
            time_since_activity = time.time() - self._last_activity_time
            
            if self._in_grace_period:
                try:
                    grace_period_seconds = int(state.get_config_value("refresh_timer.grace_period", 25))
                except (ValueError, TypeError):
                    grace_period_seconds = 25  # Default fallback
                grace_time_elapsed = time.time() - self._grace_period_start_time
                return max(0, grace_period_seconds - grace_time_elapsed)
            else:
                return max(0, idle_timeout_seconds - time_since_activity)
    
    def _timer_loop(self) -> None:
        """Main timer loop that runs in background thread."""
        try:
            while not self._stop_event.is_set():
                try:
                    if self._should_refresh():
                        self._perform_refresh()
                        break  # Stop after refreshing
                    
                    # Check every 5 seconds
                    if self._stop_event.wait(timeout=5.0):
                        break
                        
                except Exception as e:
                    print(f"Error in refresh timer loop: {e}")
                    # Continue the loop despite errors
                    if self._stop_event.wait(timeout=5.0):
                        break
                        
        except Exception as e:
            print(f"Fatal error in refresh timer: {e}")
        finally:
            with self._lock:
                self._is_running = False
                self._in_grace_period = False
    
    def _should_refresh(self) -> bool:
        """Check if refresh should be triggered."""
        with self._lock:
            state = get_state_manager()
            
            # Get configuration and convert to int/float to handle string values
            try:
                idle_timeout_minutes = int(state.get_config_value("refresh_timer.idle_timeout", 5))
            except (ValueError, TypeError):
                idle_timeout_minutes = 5  # Default fallback
            
            try:
                grace_period_seconds = int(state.get_config_value("refresh_timer.grace_period", 25))
            except (ValueError, TypeError):
                grace_period_seconds = 25  # Default fallback
            
            # Check if grace period is enabled
            use_grace_period = state.get_config_value("refresh_timer.use_grace_period", True)
            
            idle_timeout_seconds = idle_timeout_minutes * 60
            time_since_activity = time.time() - self._last_activity_time
            
            if not self._in_grace_period:
                # Check if idle timeout has been reached
                if time_since_activity >= idle_timeout_seconds:
                    if not use_grace_period:
                        # No grace period - refresh immediately
                        print(f"[color:red]Idle timeout reached ({idle_timeout_minutes} minutes) - refreshing immediately")
                        return True
                    else:
                        # Use grace period - enter grace period first
                        self._in_grace_period = True
                        self._grace_period_start_time = time.time()
                        
                        print(f"[color:orange]Idle timeout reached ({idle_timeout_minutes} minutes) - starting {grace_period_seconds}s grace period")
                        
                        # Call grace period callback if provided
                        if self._grace_period_start_callback:
                            try:
                                self._grace_period_start_callback()
                            except Exception as e:
                                print(f"Error in grace period start callback: {e}")
                        
                        return False
            else:
                # We're in grace period - check if it's expired
                grace_time_elapsed = time.time() - self._grace_period_start_time
                if grace_time_elapsed >= grace_period_seconds:
                    print(f"[color:red]Grace period expired - triggering page refresh")
                    return True
            
            return False
    
    def _perform_refresh(self) -> None:
        """Perform the actual refresh."""
        try:
            if self._refresh_callback:
                print("[color:yellow]Refreshing DeepSeek page...")
                self._refresh_callback()
                print("[color:green]Page refresh completed")
            else:
                print("[color:red]No refresh callback configured")
        except Exception as e:
            print(f"[color:red]Error during page refresh: {e}")
        finally:
            # Reset timer state
            with self._lock:
                self._last_activity_time = time.time()
                self._in_grace_period = False


# Global singleton instance
_refresh_timer_instance: Optional[RefreshTimer] = None
_refresh_timer_lock = threading.Lock()


def get_refresh_timer() -> RefreshTimer:
    """Get the global refresh timer instance (singleton)."""
    global _refresh_timer_instance
    
    if _refresh_timer_instance is None:
        with _refresh_timer_lock:
            if _refresh_timer_instance is None:
                _refresh_timer_instance = RefreshTimer()
    
    return _refresh_timer_instance


def start_refresh_timer(refresh_callback: Callable, grace_period_start_callback: Optional[Callable] = None) -> None:
    """Start the global refresh timer."""
    state = get_state_manager()
    
    # Check if refresh timer is enabled
    if not state.get_config_value("refresh_timer.enabled", False):
        return
    
    # Check if browser is available
    if not state.driver:
        print("[color:yellow]Cannot start refresh timer - no browser driver available")
        return
    
    timer = get_refresh_timer()
    timer.start(refresh_callback, grace_period_start_callback)


def stop_refresh_timer() -> None:
    """Stop the global refresh timer."""
    timer = get_refresh_timer()
    timer.stop()


def record_activity() -> None:
    """Record activity in the global refresh timer."""
    timer = get_refresh_timer()
    timer.record_activity()


def is_refresh_timer_running() -> bool:
    """Check if the global refresh timer is running."""
    timer = get_refresh_timer()
    return timer.is_running()


def is_in_grace_period() -> bool:
    """Check if the global refresh timer is in grace period."""
    timer = get_refresh_timer()
    return timer.is_in_grace_period()