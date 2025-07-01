import os, re, time, random, string
from datetime import datetime
from typing import Optional, List

class LoggingManager:
    def __init__(self, storage_manager=None):
        self.storage_manager = storage_manager
        self.current_log_file = None
        self.enabled = False
        self.max_file_size = 1024 * 1024  # 1MB default
        self.max_files = 10  # 10 files default
        self.logs_dir = None
        
    def initialize(self, config: dict) -> None:
        """Initialize logging based on config settings"""
        try:
            logging_config = config.get("logging", {})
            self.enabled = logging_config.get("enabled", False)
            self.max_file_size = logging_config.get("max_file_size", 1024 * 1024)  # bytes
            self.max_files = logging_config.get("max_files", 10)
            
            if not self.enabled or not self.storage_manager:
                return
                
            # Create logs directory
            self.logs_dir = self.storage_manager.get_path("executable", "logs")
            if self.logs_dir:
                os.makedirs(self.logs_dir, exist_ok=True)
                self._create_new_log_file()
                self._cleanup_old_files()
                
        except Exception as e:
            print(f"Error initializing logging: {e}")
    
    def _generate_random_string(self, length: int = 6) -> str:
        """Generate a short random alphanumeric string"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    def _create_new_log_file(self) -> None:
        """Create a new log file with the specified naming format"""
        try:
            if not self.logs_dir:
                return
                
            # Format: log_file_{readable_date_time}_{short_random_alphanum_string}.txt
            now = datetime.now()
            readable_time = now.strftime("%Y%m%d_%H%M%S")
            random_string = self._generate_random_string()
            filename = f"log_file_{readable_time}_{random_string}.txt"
            
            self.current_log_file = os.path.join(self.logs_dir, filename)
            
            # Create the file with initial header
            with open(self.current_log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== INTENSE RP API LOG ===\n")
                f.write(f"Started: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"={'=' * 50}\n\n")
                
            print(f"Created new log file: {filename}")
            
        except Exception as e:
            print(f"Error creating log file: {e}")
            self.current_log_file = None
    
    def _cleanup_old_files(self) -> None:
        """Delete oldest log files if exceeding max_files limit"""
        try:
            if not self.logs_dir or not os.path.exists(self.logs_dir):
                return
                
            # Get all log files
            log_files = []
            for filename in os.listdir(self.logs_dir):
                if filename.startswith("log_file_") and filename.endswith(".txt"):
                    filepath = os.path.join(self.logs_dir, filename)
                    if os.path.isfile(filepath):
                        log_files.append((filepath, os.path.getctime(filepath)))
            
            # Sort by creation time (oldest first)
            log_files.sort(key=lambda x: x[1])
            
            # Remove excess files
            while len(log_files) > self.max_files:
                oldest_file = log_files.pop(0)
                try:
                    os.remove(oldest_file[0])
                    print(f"Deleted old log file: {os.path.basename(oldest_file[0])}")
                except Exception as e:
                    print(f"Error deleting log file: {e}")
                    
        except Exception as e:
            print(f"Error cleaning up log files: {e}")
    
    def _trim_log_file(self) -> None:
        """Trim lines from start of log file if it exceeds max size"""
        try:
            if not self.current_log_file or not os.path.exists(self.current_log_file):
                return
                
            file_size = os.path.getsize(self.current_log_file)
            if file_size <= self.max_file_size:
                return
                
            # Read all lines
            with open(self.current_log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Calculate how many lines to remove (roughly)
            avg_line_size = file_size / len(lines) if lines else 1
            lines_to_remove = int((file_size - self.max_file_size * 0.8) / avg_line_size)
            lines_to_remove = max(1, min(lines_to_remove, len(lines) // 2))
            
            # Keep the header and remove from after it
            header_end = 3  # Lines for header
            if len(lines) > header_end + lines_to_remove:
                # Remove lines after header
                remaining_lines = lines[:header_end] + lines[header_end + lines_to_remove:]
                
                # Add trimming notice
                remaining_lines.insert(header_end, f"[LOG TRIMMED - {lines_to_remove} lines removed at {datetime.now().strftime('%H:%M:%S')}]\n\n")
                
                # Write back to file
                with open(self.current_log_file, 'w', encoding='utf-8') as f:
                    f.writelines(remaining_lines)
                    
                print(f"Trimmed {lines_to_remove} lines from log file")
                
        except Exception as e:
            print(f"Error trimming log file: {e}")
    
    def _strip_color_codes(self, text: str) -> str:
        """Remove color codes from text for clean log output"""
        return re.sub(r'\[color:\w+\]', '', text)
    
    def log_message(self, text: str) -> None:
        """Log a message to the current log file"""
        try:
            if not self.enabled or not self.current_log_file:
                return
                
            # Check file size before writing
            if os.path.exists(self.current_log_file):
                if os.path.getsize(self.current_log_file) >= self.max_file_size:
                    self._trim_log_file()
            
            # Clean the text and add timestamp
            clean_text = self._strip_color_codes(text)
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {clean_text}\n"
            
            # Append to log file
            with open(self.current_log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
                
        except Exception as e:
            print(f"Error writing to log file: {e}")
    
    def get_log_files(self) -> List[str]:
        """Get list of existing log files"""
        try:
            if not self.logs_dir or not os.path.exists(self.logs_dir):
                return []
                
            log_files = []
            for filename in os.listdir(self.logs_dir):
                if filename.startswith("log_file_") and filename.endswith(".txt"):
                    log_files.append(filename)
                    
            return sorted(log_files, reverse=True)  # Ladies first, most recent right after
            
        except Exception as e:
            print(f"Error getting log files: {e}")
            return []