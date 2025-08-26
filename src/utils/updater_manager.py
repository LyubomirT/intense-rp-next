"""
Updater Management for IntenseRP Next
====================================

Handles automatic extraction, execution, and management of updater utilities.
Used by the better update system for seamless updating experience.
"""

import os
import sys
import platform
import tempfile
import zipfile
import subprocess
from typing import Optional, Tuple
from pathlib import Path


class UpdaterManager:
    """Manages updater extraction and execution"""
    
    @staticmethod
    def extract_and_run_updater(download_path: str, storage_manager) -> Tuple[bool, str]:
        """
        Extract and run the updater from a downloaded zip file
        
        Args:
            download_path: Path to the downloaded updater zip file
            storage_manager: StorageManager instance for path resolution
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Validate the download path
            if not os.path.exists(download_path):
                return False, f"Download file not found: {download_path}"
            
            # Get the base directory where we should extract
            base_path = storage_manager.get_base_path()
            
            # Extract the updater
            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                # List all files to find the updater
                file_list = zip_ref.namelist()
                updater_files = [f for f in file_list if 'IntenseRP-Updater' in f and not f.endswith('/')]
                
                if not updater_files:
                    return False, "No updater executable found in the package"
                
                # Extract all files to base directory
                zip_ref.extractall(base_path)
            
            # Find the extracted updater executable
            updater_path = UpdaterManager._find_updater_executable(base_path)
            
            if not updater_path:
                return False, "Updater executable not found after extraction"
            
            # Make executable on Unix systems
            if platform.system() != "Windows":
                os.chmod(updater_path, 0o755)
            
            # Run the updater
            success, message = UpdaterManager._run_updater(updater_path)
            
            return success, message
            
        except zipfile.BadZipFile:
            return False, "Invalid zip file format"
        except PermissionError:
            return False, "Permission denied - unable to extract or run updater"
        except Exception as e:
            return False, f"Extraction failed: {str(e)}"
    
    @staticmethod
    def _find_updater_executable(base_path: str) -> Optional[str]:
        """
        Find the updater executable in the given directory
        
        Args:
            base_path: Directory to search for updater
            
        Returns:
            Path to updater executable or None if not found
        """
        updater_name = "IntenseRP-Updater.exe" if platform.system() == "Windows" else "IntenseRP-Updater"
        
        # Search recursively for the updater
        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file == updater_name:
                    updater_path = os.path.join(root, file)
                    if os.path.isfile(updater_path):
                        return updater_path
        
        return None
    
    @staticmethod
    def _run_updater(updater_path: str) -> Tuple[bool, str]:
        """
        Run the updater executable
        
        Args:
            updater_path: Path to the updater executable
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Verify the file exists and is executable
            if not os.path.isfile(updater_path):
                return False, f"Updater file not found: {updater_path}"
            
            # On Unix systems, check if file is executable
            if platform.system() != "Windows":
                if not os.access(updater_path, os.X_OK):
                    return False, f"Updater is not executable: {updater_path}"
            
            # Start the updater in a visible console window for user interaction
            try:
                if platform.system() == "Windows":
                    # On Windows, create a new console window
                    subprocess.Popen([updater_path], 
                                   cwd=os.path.dirname(updater_path),
                                   creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:
                    # On Unix systems, try to open in terminal
                    try:
                        # Try common terminal emulators
                        for terminal in ["gnome-terminal", "xterm", "konsole", "x-terminal-emulator"]:
                            try:
                                subprocess.Popen([terminal, "-e", updater_path], 
                                               cwd=os.path.dirname(updater_path))
                                break
                            except FileNotFoundError:
                                continue
                        else:
                            # Fallback: run in background
                            subprocess.Popen([updater_path], 
                                           cwd=os.path.dirname(updater_path))
                    except Exception:
                        # Final fallback
                        subprocess.Popen([updater_path], 
                                       cwd=os.path.dirname(updater_path))
                
                return True, "Updater launched in new console window"
                
            except Exception as e:
                return False, f"Failed to launch updater: {str(e)}"
            
        except FileNotFoundError:
            return False, f"Updater executable not found: {updater_path}"
        except PermissionError:
            return False, f"Permission denied running updater: {updater_path}"
        except Exception as e:
            return False, f"Failed to start updater: {str(e)}"
    
    @staticmethod
    def is_updater_compatible(asset_name: str) -> bool:
        """
        Check if an asset is a compatible updater for the current platform
        
        Args:
            asset_name: Name of the asset file
            
        Returns:
            True if asset is compatible updater, False otherwise
        """
        if 'updater' not in asset_name.lower():
            return False
        
        current_platform = platform.system().lower()
        asset_lower = asset_name.lower()
        
        # Check platform compatibility
        if current_platform == "windows":
            return "win32" in asset_lower or "windows" in asset_lower
        elif current_platform == "linux":
            return "linux" in asset_lower
        elif current_platform == "darwin":  # macOS
            return "darwin" in asset_lower or "macos" in asset_lower
        
        return False
    
    @staticmethod
    def get_download_directory(storage_manager) -> str:
        """
        Get appropriate directory for downloading updates
        
        Args:
            storage_manager: StorageManager instance
            
        Returns:
            Path to download directory
        """
        try:
            # Create a downloads folder in the base directory
            base_path = storage_manager.get_base_path()
            download_dir = os.path.join(base_path, "downloads")
            
            # Create directory if it doesn't exist
            os.makedirs(download_dir, exist_ok=True)
            
            return download_dir
        except Exception:
            # Fallback to system temp directory
            return tempfile.gettempdir()
    
    @staticmethod
    def cleanup_download(file_path: str) -> bool:
        """
        Clean up downloaded file after processing
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception as e:
            print(f"Failed to cleanup download file {file_path}: {e}")
        
        return False
    
    @staticmethod
    def verify_updater_permissions(storage_manager) -> Tuple[bool, str]:
        """
        Verify that we have permissions to extract and run updater
        
        Args:
            storage_manager: StorageManager instance
            
        Returns:
            Tuple of (has_permissions: bool, message: str)
        """
        try:
            base_path = storage_manager.get_base_path()
            
            # Check write permissions to base directory
            if not os.access(base_path, os.W_OK):
                return False, f"No write permission to application directory: {base_path}"
            
            # Try creating a test file
            test_file = os.path.join(base_path, "test_permissions.tmp")
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
            except Exception:
                return False, f"Unable to write to application directory: {base_path}"
            
            return True, "Permissions verified"
            
        except Exception as e:
            return False, f"Permission check failed: {str(e)}"