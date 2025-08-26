"""
Welcome screen utilities for IntenseRP Next
"""
import os
from typing import Optional


class WelcomeManager:
    """Manages welcome screen logic and first-start detection"""
    
    def __init__(self, storage_manager):
        """
        Initialize welcome manager with storage manager
        
        Args:
            storage_manager: StorageManager instance for file operations
        """
        self.storage_manager = storage_manager
        self.returning_file = "returning"
    
    def is_first_start(self) -> bool:
        """
        Check if this is the first start of the application
        
        Returns:
            bool: True if first start (no returning file), False if returning user
        """
        try:
            # Check if returning file exists in save directory
            returning_path = self.storage_manager.get_existing_path(
                path_root="base", 
                relative_path=os.path.join("save", self.returning_file)
            )
            return returning_path is None
        except Exception as e:
            print(f"Error checking first start: {e}")
            return False  # Default to not showing welcome screen on errors
    
    def mark_as_returning(self) -> bool:
        """
        Mark the user as a returning user by creating the returning file
        
        Returns:
            bool: True if successfully created, False otherwise
        """
        try:
            # Ensure save directory exists
            save_path = self.storage_manager.get_path("base", "save")
            if not save_path:
                raise ValueError("Could not get save path")
            
            os.makedirs(save_path, exist_ok=True)
            
            # Create returning file
            returning_file_path = os.path.join(save_path, self.returning_file)
            with open(returning_file_path, "w", encoding="utf-8") as f:
                f.write("This file indicates the user has used IntenseRP Next before.\n")
                f.write("Delete this file to show the welcome screen again on restart.\n")
            
            print(f"Created returning file: {returning_file_path}")
            return True
            
        except Exception as e:
            print(f"Error creating returning file: {e}")
            return False
    
    def reset_welcome(self) -> bool:
        """
        Reset welcome screen to show again (for debugging/testing)
        
        Returns:
            bool: True if successfully deleted, False otherwise
        """
        try:
            returning_path = self.storage_manager.get_existing_path(
                path_root="base",
                relative_path=os.path.join("save", self.returning_file)
            )
            
            if returning_path and os.path.exists(returning_path):
                os.remove(returning_path)
                print("Welcome screen reset - will show on next restart")
                return True
            else:
                print("No returning file found - welcome screen will show on next restart")
                return True
                
        except Exception as e:
            print(f"Error resetting welcome screen: {e}")
            return False