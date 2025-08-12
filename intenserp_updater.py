#!/usr/bin/env python3
"""
IntenseRP Next Updater - CLI Tool for Installing and Updating IntenseRP Next
===========================================================================

A modern CLI tool with colored widgets for managing IntenseRP Next installations.
Supports installation, updating, and release information display.

Huge thanks to the open-source community for overfilling Python with amazing
libraries and frameworks, this file has 0 external dependencies and is insanely
lightweight thanks to that.
"""

import os
import sys
import json
import shutil
import zipfile
import tempfile
import platform
import subprocess
import requests
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import time

# ============================================================================
# Constants and Configuration
# ============================================================================

REPO_OWNER = "LyubomirT"
REPO_NAME = "intense-rp-next"
GITHUB_API_BASE = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main"
VERSION_URL = f"{GITHUB_RAW_BASE}/version.txt"
RELEASES_URL = f"{GITHUB_API_BASE}/releases/latest"
WIN_ZIP_NAME = "intenserp-next-win32-amd64.zip"
EXECUTABLE_NAME = "IntenseRP Next.exe"
SAVE_DIR_NAME = "save"

# ============================================================================
# Color and Styling System
# ============================================================================

class Colors:
    """ANSI color codes for terminal styling"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Basic colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

class Symbols:
    """Unicode symbols for enhanced UI display"""
    # Status symbols
    SUCCESS = "✓"
    ERROR = "✗"
    WARNING = "⚠"
    INFO = "ℹ"
    ARROW_RIGHT = "→"
    ARROW_DOWN = "↓"
    
    # Progress and UI
    PROGRESS_FULL = "█"
    PROGRESS_PARTIAL = "▓"
    PROGRESS_EMPTY = "░"
    
    # Decorative
    STAR = "★"
    BULLET = "•"
    DIAMOND = "◆"
    
    # Box drawing
    BOX_H = "─"
    BOX_V = "│"
    BOX_TL = "┌"
    BOX_TR = "┐"
    BOX_BL = "└"
    BOX_BR = "┘"
    BOX_CROSS = "┼"

# ============================================================================
# UI Widget System
# ============================================================================

class UIWidgets:
    """Reusable UI components with styling"""
    
    @staticmethod
    def print_colored(text: str, color: str = Colors.WHITE, end: str = '\n') -> None:
        """Print text with color formatting"""
        print(f"{color}{text}{Colors.RESET}", end=end)
    
    @staticmethod
    def print_header(title: str, width: int = 70) -> None:
        """Print a styled header with borders"""
        print()
        UIWidgets.print_colored(Symbols.BOX_TL + Symbols.BOX_H * (width - 2) + Symbols.BOX_TR, Colors.CYAN)
        UIWidgets.print_colored(f"{Symbols.BOX_V} {title.center(width - 4)} {Symbols.BOX_V}", Colors.CYAN)
        UIWidgets.print_colored(Symbols.BOX_BL + Symbols.BOX_H * (width - 2) + Symbols.BOX_BR, Colors.CYAN)
        print()
    
    @staticmethod
    def print_section(title: str) -> None:
        """Print a section header"""
        print()
        UIWidgets.print_colored(f"{Symbols.DIAMOND} {title}", Colors.BRIGHT_YELLOW)
        UIWidgets.print_colored(Symbols.BOX_H * 50, Colors.YELLOW)
    
    @staticmethod
    def print_success(message: str) -> None:
        """Print a success message"""
        UIWidgets.print_colored(f"{Symbols.SUCCESS} {message}", Colors.BRIGHT_GREEN)
    
    @staticmethod
    def print_error(message: str) -> None:
        """Print an error message"""
        UIWidgets.print_colored(f"{Symbols.ERROR} {message}", Colors.BRIGHT_RED)
    
    @staticmethod
    def print_warning(message: str) -> None:
        """Print a warning message"""
        UIWidgets.print_colored(f"{Symbols.WARNING} {message}", Colors.BRIGHT_YELLOW)
    
    @staticmethod
    def print_info(message: str) -> None:
        """Print an info message"""
        UIWidgets.print_colored(f"{Symbols.INFO} {message}", Colors.BRIGHT_BLUE)
    
    @staticmethod
    def print_step(step_num: int, message: str) -> None:
        """Print a numbered step"""
        UIWidgets.print_colored(f"{step_num}. ", Colors.BRIGHT_CYAN, end="")
        UIWidgets.print_colored(message, Colors.WHITE)
    
    @staticmethod
    def print_progress_bar(current: int, total: int, width: int = 40, prefix: str = "") -> None:
        """Print a progress bar"""
        if total == 0:
            percentage = 0
        else:
            percentage = (current / total) * 100
        
        filled_width = int(width * current // total) if total > 0 else 0
        bar = (Symbols.PROGRESS_FULL * filled_width + 
               Symbols.PROGRESS_EMPTY * (width - filled_width))
        
        UIWidgets.print_colored(f"\r{prefix}[", Colors.WHITE, end="")
        UIWidgets.print_colored(bar[:filled_width], Colors.BRIGHT_GREEN, end="")
        UIWidgets.print_colored(bar[filled_width:], Colors.DIM, end="")
        UIWidgets.print_colored(f"] {percentage:.1f}%", Colors.WHITE, end="")
        
        if current >= total:
            print()  # New line when complete
    
    @staticmethod
    def prompt_choice(question: str, choices: list, default: Optional[int] = None) -> int:
        """Prompt user for a choice from a list"""
        print()
        UIWidgets.print_colored(question, Colors.BRIGHT_WHITE)
        print()
        
        for i, choice in enumerate(choices, 1):
            default_marker = " (default)" if default == i else ""
            UIWidgets.print_colored(f"  {i}. {choice}{default_marker}", Colors.CYAN)
        
        print()
        while True:
            try:
                UIWidgets.print_colored("Enter your choice: ", Colors.BRIGHT_WHITE, end="")
                choice_input = input().strip()
                
                if not choice_input and default is not None:
                    return default
                
                choice_num = int(choice_input)
                if 1 <= choice_num <= len(choices):
                    return choice_num
                else:
                    UIWidgets.print_error(f"Please enter a number between 1 and {len(choices)}")
            except ValueError:
                UIWidgets.print_error("Please enter a valid number")
            except KeyboardInterrupt:
                print()
                UIWidgets.print_warning("Operation cancelled by user")
                sys.exit(0)
    
    @staticmethod
    def prompt_input(question: str, required: bool = True) -> str:
        """Prompt user for text input"""
        while True:
            try:
                UIWidgets.print_colored(f"{question}: ", Colors.BRIGHT_WHITE, end="")
                response = input().strip()
                
                if not response and required:
                    UIWidgets.print_error("This field is required. Please enter a value.")
                    continue
                
                return response
            except KeyboardInterrupt:
                print()
                UIWidgets.print_warning("Operation cancelled by user")
                sys.exit(0)
    
    @staticmethod
    def prompt_confirm(question: str, default: bool = False) -> bool:
        """Prompt user for yes/no confirmation"""
        default_text = "Y/n" if default else "y/N"
        
        while True:
            try:
                UIWidgets.print_colored(f"{question} ({default_text}): ", Colors.BRIGHT_WHITE, end="")
                response = input().strip().lower()
                
                if not response:
                    return default
                
                if response in ['y', 'yes']:
                    return True
                elif response in ['n', 'no']:
                    return False
                else:
                    UIWidgets.print_error("Please enter 'y' for yes or 'n' for no")
            except KeyboardInterrupt:
                print()
                UIWidgets.print_warning("Operation cancelled by user")
                sys.exit(0)

# ============================================================================
# System Utilities
# ============================================================================

class SystemUtils:
    """System-related utility functions"""
    
    @staticmethod
    def check_windows_version() -> bool:
        """Check if running on Windows 10 or 11"""
        if platform.system() != "Windows":
            return False
        
        try:
            # Get Windows version
            version = platform.version()
            # Windows 10 is version 10.0.x, Windows 11 is version 10.0.x with build >= 22000
            major, minor, build = map(int, version.split('.'))
            
            # Windows 10/11 have major version 10
            return major >= 10
        except:
            return False
    
    @staticmethod
    def is_process_running(exe_name: str) -> bool:
        """Check if a process is running by executable name"""
        try:
            # Use tasklist to check for running processes
            result = subprocess.run(
                ['tasklist', '/FI', f'IMAGENAME eq {exe_name}'],
                capture_output=True,
                text=True,
                check=True
            )
            return exe_name.lower() in result.stdout.lower()
        except:
            return False
    
    @staticmethod
    def kill_process(exe_name: str) -> bool:
        """Attempt to kill a process by executable name"""
        try:
            subprocess.run(
                ['taskkill', '/F', '/IM', exe_name],
                capture_output=True,
                check=True
            )
            return True
        except:
            return False
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

# ============================================================================
# GitHub API Interface
# ============================================================================

class GitHubAPI:
    """Interface for GitHub API operations"""
    
    @staticmethod
    def get_latest_version() -> Optional[str]:
        """Get the latest version from version.txt"""
        try:
            response = requests.get(VERSION_URL, timeout=10)
            response.raise_for_status()
            return response.text.strip()
        except requests.RequestException as e:
            UIWidgets.print_error(f"Failed to fetch version: {e}")
            return None
    
    @staticmethod
    def get_latest_release() -> Optional[Dict[str, Any]]:
        """Get the latest release information"""
        try:
            response = requests.get(RELEASES_URL, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            UIWidgets.print_error(f"Failed to fetch release info: {e}")
            return None
    
    @staticmethod
    def find_windows_asset(release_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find the Windows ZIP asset in release data"""
        assets = release_data.get('assets', [])
        for asset in assets:
            if asset['name'] == WIN_ZIP_NAME:
                return asset
        return None
    
    @staticmethod
    def download_file(url: str, destination: Path, progress_callback=None) -> bool:
        """Download a file with progress tracking"""
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress_callback(downloaded_size, total_size)
            
            return True
        except requests.RequestException as e:
            UIWidgets.print_error(f"Download failed: {e}")
            return False

# ============================================================================
# Core Updater Logic
# ============================================================================

class IntenseRPUpdater:
    """Main updater class for IntenseRP Next"""
    
    def __init__(self):
        self.temp_dir = None
    
    def __enter__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="intenserp_updater_")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except:
                pass  # Best effort cleanup
    
    def show_welcome(self) -> int:
        """Display welcome screen and get user choice"""
        UIWidgets.print_header("IntenseRP Next Updater v1.0", 70)
        
        UIWidgets.print_colored("Welcome to the IntenseRP Next Updater!", Colors.BRIGHT_WHITE)
        UIWidgets.print_colored("This tool helps you install and update IntenseRP Next easily.", Colors.WHITE)
        
        choices = [
            "Install IntenseRP Next",
            "Update IntenseRP Next", 
            "Show Latest Release Info",
            "Exit"
        ]
        
        return UIWidgets.prompt_choice("What would you like to do?", choices)
    
    def check_system_compatibility(self) -> bool:
        """Check if the system is compatible"""
        UIWidgets.print_section("System Compatibility Check")
        
        if not SystemUtils.check_windows_version():
            UIWidgets.print_error("This updater requires Windows 10 or Windows 11")
            UIWidgets.print_info("Other operating systems are not supported for automatic updates")
            return False
        
        UIWidgets.print_success("Windows 10/11 detected - system compatible")
        return True
    
    def show_latest_release_info(self) -> None:
        """Display information about the latest release"""
        UIWidgets.print_section("Latest Release Information")
        
        UIWidgets.print_info("Fetching latest release information...")
        
        # Get version
        version = GitHubAPI.get_latest_version()
        if not version:
            UIWidgets.print_error("Unable to fetch version information")
            return
        
        # Get release data
        release_data = GitHubAPI.get_latest_release()
        if not release_data:
            UIWidgets.print_error("Unable to fetch release information")
            return
        
        # Find Windows asset
        windows_asset = GitHubAPI.find_windows_asset(release_data)
        
        print()
        UIWidgets.print_colored(f"Latest Version: ", Colors.BRIGHT_WHITE, end="")
        UIWidgets.print_colored(f"v{version}", Colors.BRIGHT_GREEN)
        
        UIWidgets.print_colored(f"Release Name: ", Colors.BRIGHT_WHITE, end="")
        UIWidgets.print_colored(release_data.get('name', 'N/A'), Colors.CYAN)
        
        UIWidgets.print_colored(f"Published: ", Colors.BRIGHT_WHITE, end="")
        UIWidgets.print_colored(release_data.get('published_at', 'N/A')[:10], Colors.YELLOW)
        
        if windows_asset:
            UIWidgets.print_colored(f"Windows Package: ", Colors.BRIGHT_WHITE, end="")
            UIWidgets.print_colored(f"{windows_asset['name']} ({SystemUtils.format_size(windows_asset['size'])})", Colors.CYAN)
            
            UIWidgets.print_colored(f"Downloads: ", Colors.BRIGHT_WHITE, end="")
            UIWidgets.print_colored(str(windows_asset['download_count']), Colors.BRIGHT_MAGENTA)
        
        print()
        UIWidgets.print_colored("Release Notes:", Colors.BRIGHT_WHITE)
        body = release_data.get('body', 'No release notes available.')
        # Truncate if too long
        if len(body) > 500:
            body = body[:500] + "..."
        
        for line in body.split('\n')[:10]:  # Limit to 10 lines
            UIWidgets.print_colored(f"  {line}", Colors.WHITE)
    
    def install_intenserp(self) -> None:
        """Install IntenseRP Next to a specified directory"""
        UIWidgets.print_section("Install IntenseRP Next")
        
        if not self.check_system_compatibility():
            return
        
        # Get installation directory
        install_dir = UIWidgets.prompt_input("Enter installation directory path")
        install_path = Path(install_dir).resolve()
        
        # Validate directory
        if install_path.exists() and any(install_path.iterdir()):
            if not UIWidgets.prompt_confirm(
                f"Directory '{install_path}' is not empty. Continue anyway?", 
                default=False
            ):
                UIWidgets.print_warning("Installation cancelled")
                return
        
        # Create directory if it doesn't exist
        try:
            install_path.mkdir(parents=True, exist_ok=True)
            UIWidgets.print_success(f"Installation directory: {install_path}")
        except Exception as e:
            UIWidgets.print_error(f"Failed to create directory: {e}")
            return
        
        # Fetch release information
        UIWidgets.print_info("Fetching release information...")
        release_data = GitHubAPI.get_latest_release()
        if not release_data:
            return
        
        # Find Windows asset
        windows_asset = GitHubAPI.find_windows_asset(release_data)
        if not windows_asset:
            UIWidgets.print_error("Windows package not found in latest release")
            return
        
        version = GitHubAPI.get_latest_version() or "unknown"
        UIWidgets.print_info(f"Installing IntenseRP Next v{version}")
        UIWidgets.print_info(f"Package size: {SystemUtils.format_size(windows_asset['size'])}")
        
        # Download
        download_url = windows_asset['browser_download_url']
        zip_path = Path(self.temp_dir) / WIN_ZIP_NAME
        
        UIWidgets.print_step(1, "Downloading package...")
        
        def download_progress(current, total):
            UIWidgets.print_progress_bar(current, total, prefix="  Download: ")
        
        if not GitHubAPI.download_file(download_url, zip_path, download_progress):
            return
        
        UIWidgets.print_success("Download completed")
        
        # Extract
        UIWidgets.print_step(2, "Extracting package...")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                total_files = len(zip_ref.namelist())
                
                for i, file in enumerate(zip_ref.namelist()):
                    zip_ref.extract(file, self.temp_dir)
                    UIWidgets.print_progress_bar(i + 1, total_files, prefix="  Extract: ")
            
            UIWidgets.print_success("Extraction completed")
        except Exception as e:
            UIWidgets.print_error(f"Extraction failed: {e}")
            return
        
        # Find extracted folder
        extracted_folder = None
        for item in Path(self.temp_dir).iterdir():
            if item.is_dir() and item.name.startswith("intenserp-next"):
                extracted_folder = item
                break
        
        if not extracted_folder:
            UIWidgets.print_error("Could not find extracted IntenseRP folder")
            return
        
        # Move to installation directory
        UIWidgets.print_step(3, "Installing to target directory...")
        
        try:
            # Copy all contents to install directory
            for item in extracted_folder.iterdir():
                dest = install_path / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)
            
            UIWidgets.print_success("Installation completed")
        except Exception as e:
            UIWidgets.print_error(f"Installation failed: {e}")
            return
        
        # Cleanup
        UIWidgets.print_step(4, "Cleaning up temporary files...")
        
        try:
            zip_path.unlink()
            UIWidgets.print_success("Cleanup completed")
        except:
            pass  # Non-critical
        
        # Final success message
        print()
        UIWidgets.print_success(f"IntenseRP Next v{version} installed successfully!")
        UIWidgets.print_info(f"Installation location: {install_path}")
        exe_path = install_path / EXECUTABLE_NAME
        if exe_path.exists():
            UIWidgets.print_info(f"Run with: {exe_path}")
        
    def update_intenserp(self) -> None:
        """Update an existing IntenseRP Next installation"""
        UIWidgets.print_section("Update IntenseRP Next")
        
        if not self.check_system_compatibility():
            return
        
        # Get executable path
        exe_path_str = UIWidgets.prompt_input(f"Enter path to {EXECUTABLE_NAME}")
        exe_path = Path(exe_path_str).resolve()
        
        # Validate executable
        if not exe_path.exists() or exe_path.name != EXECUTABLE_NAME:
            UIWidgets.print_error(f"File not found or not named '{EXECUTABLE_NAME}'")
            return
        
        install_dir = exe_path.parent
        UIWidgets.print_success(f"Found installation: {install_dir}")
        
        # Check current version (if version.txt exists)
        current_version_file = install_dir / "version.txt"
        current_version = "unknown"
        if current_version_file.exists():
            try:
                current_version = current_version_file.read_text().strip()
            except:
                pass
        
        UIWidgets.print_info(f"Current version: {current_version}")
        
        # Get latest version
        UIWidgets.print_info("Checking for updates...")
        latest_version = GitHubAPI.get_latest_version()
        if not latest_version:
            UIWidgets.print_error("Unable to check for updates")
            return
        
        UIWidgets.print_info(f"Latest version: {latest_version}")
        
        # Check if update is needed
        if current_version == latest_version:
            UIWidgets.print_warning("You already have the latest version installed")
            if not UIWidgets.prompt_confirm("Continue with reinstall anyway?", default=False):
                return
        
        # Confirm update
        if not UIWidgets.prompt_confirm(
            f"Update from v{current_version} to v{latest_version}?", 
            default=True
        ):
            UIWidgets.print_warning("Update cancelled")
            return
        
        # Check if application is running
        UIWidgets.print_step(1, "Checking if IntenseRP Next is running...")
        
        if SystemUtils.is_process_running(EXECUTABLE_NAME):
            UIWidgets.print_warning("IntenseRP Next is currently running")
            if UIWidgets.prompt_confirm("Attempt to close it automatically?", default=True):
                if SystemUtils.kill_process(EXECUTABLE_NAME):
                    UIWidgets.print_success("Application closed successfully")
                    time.sleep(2)  # Wait for process to fully terminate
                else:
                    UIWidgets.print_error("Failed to close application automatically")
                    UIWidgets.print_error("Please close IntenseRP Next manually and try again")
                    return
            else:
                UIWidgets.print_error("Please close IntenseRP Next and try again")
                return
        else:
            UIWidgets.print_success("IntenseRP Next is not running")
        
        # Backup save directory
        save_dir = install_dir / SAVE_DIR_NAME
        backup_save_dir = None
        
        if save_dir.exists():
            UIWidgets.print_step(2, "Backing up save directory...")
            backup_save_dir = Path(self.temp_dir) / SAVE_DIR_NAME
            try:
                shutil.copytree(save_dir, backup_save_dir)
                UIWidgets.print_success("Save directory backed up")
            except Exception as e:
                UIWidgets.print_error(f"Failed to backup save directory: {e}")
                if not UIWidgets.prompt_confirm("Continue without backup?", default=False):
                    return
                backup_save_dir = None
        else:
            UIWidgets.print_info("No save directory found (this is normal for new installations)")
        
        # Get release data and download
        UIWidgets.print_step(3, "Downloading update...")
        
        release_data = GitHubAPI.get_latest_release()
        if not release_data:
            return
        
        windows_asset = GitHubAPI.find_windows_asset(release_data)
        if not windows_asset:
            UIWidgets.print_error("Windows package not found in latest release")
            return
        
        download_url = windows_asset['browser_download_url']
        zip_path = Path(self.temp_dir) / WIN_ZIP_NAME
        
        def download_progress(current, total):
            UIWidgets.print_progress_bar(current, total, prefix="  Download: ")
        
        if not GitHubAPI.download_file(download_url, zip_path, download_progress):
            return
        
        UIWidgets.print_success("Download completed")
        
        # Remove old installation (except save directory)
        UIWidgets.print_step(4, "Removing old installation...")
        
        try:
            for item in install_dir.iterdir():
                if item.name == SAVE_DIR_NAME:
                    continue  # Skip save directory
                
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            
            UIWidgets.print_success("Old installation removed")
        except Exception as e:
            UIWidgets.print_error(f"Failed to remove old installation: {e}")
            return
        
        # Extract new version
        UIWidgets.print_step(5, "Installing new version...")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                total_files = len(zip_ref.namelist())
                
                for i, file in enumerate(zip_ref.namelist()):
                    zip_ref.extract(file, self.temp_dir)
                    UIWidgets.print_progress_bar(i + 1, total_files, prefix="  Extract: ")
            
            UIWidgets.print_success("Extraction completed")
        except Exception as e:
            UIWidgets.print_error(f"Extraction failed: {e}")
            return
        
        # Find extracted folder and move contents
        extracted_folder = None
        for item in Path(self.temp_dir).iterdir():
            if item.is_dir() and item.name.startswith("intenserp-next"):
                extracted_folder = item
                break
        
        if not extracted_folder:
            UIWidgets.print_error("Could not find extracted IntenseRP folder")
            return
        
        # Copy new files to installation directory
        try:
            for item in extracted_folder.iterdir():
                dest = install_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)
            
            UIWidgets.print_success("New version installed")
        except Exception as e:
            UIWidgets.print_error(f"Installation failed: {e}")
            return
        
        # Restore save directory
        if backup_save_dir and backup_save_dir.exists():
            UIWidgets.print_step(6, "Restoring save directory...")
            
            try:
                final_save_dir = install_dir / SAVE_DIR_NAME
                if final_save_dir.exists():
                    shutil.rmtree(final_save_dir)
                
                shutil.copytree(backup_save_dir, final_save_dir)
                UIWidgets.print_success("Save directory restored")
            except Exception as e:
                UIWidgets.print_error(f"Failed to restore save directory: {e}")
                UIWidgets.print_warning("Your save data backup is located at: " + str(backup_save_dir))
        
        # Cleanup
        UIWidgets.print_step(7, "Cleaning up...")
        
        try:
            zip_path.unlink()
            UIWidgets.print_success("Cleanup completed")
        except:
            pass
        
        # Final success message
        print()
        UIWidgets.print_success(f"IntenseRP Next updated to v{latest_version}!")
        UIWidgets.print_info(f"Installation location: {install_dir}")
        UIWidgets.print_info("You can now run the updated application")

# ============================================================================
# Main Application Entry Point
# ============================================================================

def main():
    """Main application entry point"""
    try:
        # Enable Windows terminal color support
        if platform.system() == "Windows":
            os.system("color")
        
        with IntenseRPUpdater() as updater:
            while True:
                choice = updater.show_welcome()
                
                if choice == 1:  # Install
                    updater.install_intenserp()
                elif choice == 2:  # Update
                    updater.update_intenserp()
                elif choice == 3:  # Latest Release Info
                    updater.show_latest_release_info()
                elif choice == 4:  # Exit
                    UIWidgets.print_info("Thank you for using IntenseRP Next Updater!")
                    break
                
                print()
                UIWidgets.prompt_input("Press Enter to continue", required=False)
                
                # Clear screen for next iteration
                if platform.system() == "Windows":
                    os.system("cls")
                else:
                    os.system("clear")
    
    except KeyboardInterrupt:
        print()
        UIWidgets.print_warning("Operation cancelled by user")
    except Exception as e:
        UIWidgets.print_error(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()