"""
Message dump comparison utility for Clean Regeneration feature
Handles storage, comparison and cleanup of message dump files
"""

import os
import hashlib
from typing import Optional


class MessageDumpManager:
    """Manages message dump files for Clean Regeneration feature"""
    
    def __init__(self, base_path: str = None):
        """Initialize the dump manager
        
        Args:
            base_path: Base path for the application (if None, uses current directory)
        """
        if base_path is None:
            # Try to get base path from storage manager if available
            try:
                from utils.storage_manager import StorageManager
                storage_manager = StorageManager()
                self.base_path = storage_manager.get_base_path()
            except Exception:
                # Fallback to current directory
                self.base_path = os.getcwd()
        else:
            self.base_path = base_path
            
        self.msgdump_dir = os.path.join(self.base_path, "msgdump")
        self.old_dump_file = os.path.join(self.msgdump_dir, "olddump.txt")
        self.new_dump_file = os.path.join(self.msgdump_dir, "newdump.txt")
    
    def _ensure_dump_directory_exists(self) -> None:
        """Create the msgdump directory if it doesn't exist"""
        try:
            if not os.path.exists(self.msgdump_dir):
                os.makedirs(self.msgdump_dir, exist_ok=True)
        except Exception as e:
            print(f"[color:red]Error creating msgdump directory: {e}")
            raise
    
    def _read_dump_file(self, filepath: str) -> Optional[str]:
        """Read content from a dump file
        
        Args:
            filepath: Path to the dump file
            
        Returns:
            File content as string, or None if file doesn't exist or error occurs
        """
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            return None
        except Exception as e:
            print(f"[color:yellow]Warning: Could not read dump file {filepath}: {e}")
            return None
    
    def _write_dump_file(self, filepath: str, content: str) -> bool:
        """Write content to a dump file
        
        Args:
            filepath: Path to the dump file
            content: Content to write
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._ensure_dump_directory_exists()
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"[color:red]Error writing dump file {filepath}: {e}")
            return False
    
    def get_old_dump_content(self) -> Optional[str]:
        """Get the content of the old dump file
        
        Returns:
            Content of olddump.txt or None if not found
        """
        return self._read_dump_file(self.old_dump_file)
    
    def set_new_dump_content(self, content: str) -> bool:
        """Set the content of the new dump file
        
        Args:
            content: Message content to store
            
        Returns:
            True if successful, False otherwise
        """
        return self._write_dump_file(self.new_dump_file, content)
    
    def get_new_dump_content(self) -> Optional[str]:
        """Get the content of the new dump file
        
        Returns:
            Content of newdump.txt or None if not found
        """
        return self._read_dump_file(self.new_dump_file)
    
    def compare_dumps(self, new_content: str) -> bool:
        """Compare new content with old dump content
        
        Args:
            new_content: New message content to compare
            
        Returns:
            True if contents are identical, False otherwise
        """
        try:
            # Write new content to newdump.txt
            if not self.set_new_dump_content(new_content):
                return False
            
            # Get old content
            old_content = self.get_old_dump_content()
            
            # If no old content exists, they can't be identical
            if old_content is None:
                return False
            
            # Compare contents (strip whitespace for accurate comparison)
            new_content_normalized = new_content.strip()
            old_content_normalized = old_content.strip()
            
            return new_content_normalized == old_content_normalized
            
        except Exception as e:
            print(f"[color:red]Error comparing dumps: {e}")
            return False
    
    def update_dumps_after_success(self) -> bool:
        """Update dump files after successful generation
        
        This moves newdump.txt content to olddump.txt for next comparison
        
        Returns:
            True if successful, False otherwise
        """
        try:
            new_content = self.get_new_dump_content()
            if new_content is None:
                print("[color:yellow]Warning: No new dump content to update")
                return False
            
            # Move new content to old dump for next comparison
            success = self._write_dump_file(self.old_dump_file, new_content)
            if success:
                print("[color:cyan]Message dumps updated successfully")
            
            return success
            
        except Exception as e:
            print(f"[color:red]Error updating dumps after success: {e}")
            return False
    
    def cleanup_dump_directory(self) -> bool:
        """Clean up the entire msgdump directory
        
        This removes all dump files and the directory itself
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(self.msgdump_dir):
                # Remove all files in the directory
                for filename in os.listdir(self.msgdump_dir):
                    file_path = os.path.join(self.msgdump_dir, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                    except Exception as e:
                        print(f"[color:yellow]Warning: Could not remove {file_path}: {e}")
                
                # Remove the directory itself
                try:
                    os.rmdir(self.msgdump_dir)
                    print("[color:green]Message dump directory cleaned successfully")
                except Exception as e:
                    print(f"[color:yellow]Warning: Could not remove msgdump directory: {e}")
            
            return True
            
        except Exception as e:
            print(f"[color:red]Error cleaning dump directory: {e}")
            return False
    
    def get_dump_status(self) -> dict:
        """Get status information about dump files
        
        Returns:
            Dictionary with dump file status information
        """
        try:
            return {
                'msgdump_dir_exists': os.path.exists(self.msgdump_dir),
                'msgdump_dir_path': self.msgdump_dir,
                'old_dump_exists': os.path.exists(self.old_dump_file),
                'new_dump_exists': os.path.exists(self.new_dump_file),
                'old_dump_size': os.path.getsize(self.old_dump_file) if os.path.exists(self.old_dump_file) else 0,
                'new_dump_size': os.path.getsize(self.new_dump_file) if os.path.exists(self.new_dump_file) else 0,
            }
        except Exception as e:
            return {
                'error': str(e),
                'msgdump_dir_path': self.msgdump_dir
            }
    
    def generate_content_hash(self, content: str) -> str:
        """Generate MD5 hash of content for debugging/logging
        
        Args:
            content: Content to hash
            
        Returns:
            MD5 hash as hex string
        """
        try:
            return hashlib.md5(content.encode('utf-8')).hexdigest()
        except Exception:
            return "error_generating_hash"


# Singleton instance for global access
_dump_manager_instance = None

def get_dump_manager(base_path: str = None) -> MessageDumpManager:
    """Get the global message dump manager instance
    
    Args:
        base_path: Base path for the application (only used on first call)
        
    Returns:
        MessageDumpManager instance
    """
    global _dump_manager_instance
    
    if _dump_manager_instance is None:
        _dump_manager_instance = MessageDumpManager(base_path)
    
    return _dump_manager_instance


def reset_dump_manager() -> None:
    """Reset the global dump manager instance (mainly for testing)"""
    global _dump_manager_instance
    _dump_manager_instance = None