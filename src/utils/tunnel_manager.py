"""
TryCloudflare tunnel management utilities
Handles tunnel lifecycle, URL retrieval, and cleanup
"""

import threading
import time
import subprocess
import re
import psutil
from typing import Optional, Callable
from dataclasses import dataclass


@dataclass
class TunnelInfo:
    """Information about an active tunnel"""
    url: Optional[str] = None
    process: Optional[subprocess.Popen] = None
    thread: Optional[threading.Thread] = None
    is_active: bool = False
    error_message: Optional[str] = None
    port: int = 5000


class TunnelManager:
    """Manages TryCloudflare tunnel lifecycle"""
    
    def __init__(self):
        self.tunnel_info = TunnelInfo()
        self._url_callback: Optional[Callable[[str], None]] = None
        self._error_callback: Optional[Callable[[str], None]] = None
        self._lock = threading.Lock()
    
    def set_callbacks(self, url_callback: Optional[Callable[[str], None]] = None, 
                     error_callback: Optional[Callable[[str], None]] = None):
        """Set callbacks for tunnel URL and error notifications"""
        self._url_callback = url_callback
        self._error_callback = error_callback
    
    def start_tunnel(self, port: int = 5000) -> bool:
        """
        Start TryCloudflare tunnel for the specified port
        
        Args:
            port: Port number to tunnel
            
        Returns:
            bool: True if tunnel startup was initiated successfully
        """
        with self._lock:
            if self.tunnel_info.is_active:
                self._notify_error("Tunnel is already active")
                return False
            
            self.tunnel_info.port = port
            self.tunnel_info.error_message = None
            
            # Start tunnel in background thread
            tunnel_thread = threading.Thread(
                target=self._run_tunnel_process,
                daemon=True,
                name="TunnelManager"
            )
            
            self.tunnel_info.thread = tunnel_thread
            tunnel_thread.start()
            
            return True
    
    def _run_tunnel_process(self):
        """Run the tunnel process and monitor its output"""
        try:
            print(f"Starting TryCloudflare tunnel for port {self.tunnel_info.port}...")
            
            # Use system cloudflared binary (cross-platform)
            import shutil
            import re
            
            # Find cloudflared in system PATH
            cloudflared_binary = shutil.which("cloudflared")
            if not cloudflared_binary:
                raise RuntimeError("cloudflared not found in PATH. Please install cloudflared first.")
            
            print(f"Using cloudflared binary: {cloudflared_binary}")
            
            # Start cloudflared process directly
            args = [cloudflared_binary, "tunnel", "--url", f"http://127.0.0.1:{self.tunnel_info.port}"]
            
            cloudflared = subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                encoding="utf-8",
            )
            
            # Store process immediately for cleanup
            self.tunnel_info.process = cloudflared
            
            # Parse tunnel URL from stderr
            tunnel_url = None
            url_pattern = re.compile(r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com')
            
            for _ in range(30):  # Give it 30 lines to find URL
                line = cloudflared.stderr.readline()
                if not line:
                    break
                    
                print(f"Cloudflared: {line.strip()}")
                
                url_match = url_pattern.search(line)
                if url_match:
                    tunnel_url = url_match.group(0)
                    break
            
            if not tunnel_url:
                cloudflared.terminate()
                raise RuntimeError("Failed to get tunnel URL from cloudflared")
            
            # Create compatible URL structure to match expected interface
            from collections import namedtuple
            Urls = namedtuple('Urls', ['tunnel', 'metrics', 'process'])
            tunnel_url = Urls(tunnel_url, f"http://127.0.0.1:20241/metrics", cloudflared)
            
            with self._lock:
                self.tunnel_info.url = tunnel_url
                self.tunnel_info.is_active = True
            
            print(f"TryCloudflare tunnel established: {tunnel_url}")
            self._notify_url(tunnel_url.tunnel)
            
            # Keep the tunnel alive by monitoring the process
            while self.tunnel_info.is_active:
                time.sleep(1)
                
        except ImportError as e:
            error_msg = "pycloudflared is not installed. Run: pip install pycloudflared"
            self._notify_error(error_msg)
            print(f"Tunnel error: {error_msg}")
        except Exception as e:
            error_msg = f"Failed to start tunnel: {str(e)}"
            with self._lock:
                self.tunnel_info.error_message = error_msg
            self._notify_error(error_msg)
            print(f"Tunnel error: {error_msg}")
            import traceback
            traceback.print_exc()
        finally:
            with self._lock:
                self.tunnel_info.is_active = False
                if not self.tunnel_info.error_message:
                    print("TryCloudflare tunnel stopped")
    
    def stop_tunnel(self) -> bool:
        """
        Stop the active tunnel
        
        Returns:
            bool: True if tunnel was stopped successfully
        """
        with self._lock:
            if not self.tunnel_info.is_active:
                return True
            
            self.tunnel_info.is_active = False
            
            # Clean up any cloudflared processes
            self._cleanup_cloudflared_processes()
            
            # Reset tunnel info
            self.tunnel_info.url = None
            self.tunnel_info.process = None
            self.tunnel_info.error_message = None
            
            print("TryCloudflare tunnel stopped")
            return True
    
    def get_tunnel_url(self) -> Optional[str]:
        """Get the current tunnel URL"""
        with self._lock:
            return self.tunnel_info.url if self.tunnel_info.is_active else None
    
    def is_tunnel_active(self) -> bool:
        """Check if tunnel is currently active"""
        with self._lock:
            return self.tunnel_info.is_active
    
    def get_tunnel_status(self) -> dict:
        """Get complete tunnel status information"""
        with self._lock:
            return {
                'active': self.tunnel_info.is_active,
                'url': self.tunnel_info.url,
                'port': self.tunnel_info.port,
                'error': self.tunnel_info.error_message
            }
    
    def _cleanup_cloudflared_processes(self):
        """Clean up any orphaned cloudflared processes"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_name = proc.info['name']
                    cmdline = proc.info.get('cmdline', [])
                    
                    # Look for cloudflared processes
                    if 'cloudflared' in proc_name.lower():
                        print(f"Terminating cloudflared process: {proc_name} (PID: {proc.info['pid']})")
                        proc.terminate()
                    
                    # Also check for processes with cloudflared in command line
                    elif cmdline and any('cloudflared' in arg for arg in cmdline):
                        print(f"Terminating cloudflared-related process: {proc_name} (PID: {proc.info['pid']})")
                        proc.terminate()
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
        except Exception as e:
            print(f"Error cleaning up cloudflared processes: {e}")
    
    def _notify_url(self, url: str):
        """Notify callback about tunnel URL"""
        if self._url_callback:
            try:
                self._url_callback(url)
            except Exception as e:
                print(f"Error in tunnel URL callback: {e}")
    
    def _notify_error(self, error_message: str):
        """Notify callback about tunnel error"""
        if self._error_callback:
            try:
                self._error_callback(error_message)
            except Exception as e:
                print(f"Error in tunnel error callback: {e}")
    
    def __del__(self):
        """Cleanup when manager is destroyed"""
        try:
            self.stop_tunnel()
        except:
            pass


# Global tunnel manager instance
_tunnel_manager_instance = None


def get_tunnel_manager() -> TunnelManager:
    """Get the global tunnel manager instance (singleton pattern)"""
    global _tunnel_manager_instance
    if _tunnel_manager_instance is None:
        _tunnel_manager_instance = TunnelManager()
    return _tunnel_manager_instance


def cleanup_tunnel_processes():
    """Utility function to clean up any orphaned tunnel processes"""
    manager = get_tunnel_manager()
    manager._cleanup_cloudflared_processes()


def start_tunnel_for_api(port: int = 5000, url_callback: Optional[Callable[[str], None]] = None, 
                        error_callback: Optional[Callable[[str], None]] = None) -> bool:
    """
    Convenience function to start tunnel for API server
    
    Args:
        port: API server port
        url_callback: Callback function for when tunnel URL is available
        error_callback: Callback function for tunnel errors
        
    Returns:
        bool: True if tunnel startup was initiated successfully
    """
    manager = get_tunnel_manager()
    manager.set_callbacks(url_callback, error_callback)
    return manager.start_tunnel(port)