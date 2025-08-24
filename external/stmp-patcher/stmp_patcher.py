#!/usr/bin/env python3
"""
STMP IRP-Next Username Patcher - Standalone CLI Tool
====================================================

A standalone CLI tool for patching STMP's api-calls.js file to inject 'irp-next' username 
parameters into Chat Completion message objects. This tool provides a step-by-step patching 
process with progress indicators and colored output.

The patcher uses pattern-based text analysis to identify specific code structures
and applies surgical modifications without understanding the semantic meaning of the code.

Though in reality, this surgical approach is to avoid licensing issues because of
embedding code from STMP directly.
"""

import os
import re
import sys
import json
import shutil
import time
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

# Set console encoding for Windows compatibility
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python < 3.7
        pass

# ============================================================================
# Color and Styling System
# ============================================================================

class Colors:
    """ANSI color codes for terminal styling"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    
    # Background colors
    BG_RED = '\033[101m'
    BG_GREEN = '\033[102m'
    BG_YELLOW = '\033[103m'
    BG_BLUE = '\033[104m'

class ProgressBar:
    """Simple tqdm-style progress bar without external dependencies"""
    
    def __init__(self, total: int, desc: str = "", width: int = 50):
        self.total = total
        self.current = 0
        self.desc = desc
        self.width = width
        self.start_time = time.time()
        
    def update(self, n: int = 1):
        """Update progress by n steps"""
        self.current = min(self.current + n, self.total)
        self._display()
        
    def set_description(self, desc: str):
        """Update the description"""
        self.desc = desc
        self._display()
        
    def _display(self):
        """Display the progress bar"""
        if self.total == 0:
            return
            
        progress = self.current / self.total
        filled_width = int(self.width * progress)
        
        bar = '█' * filled_width + '░' * (self.width - filled_width)
        percentage = progress * 100
        
        elapsed = time.time() - self.start_time
        if progress > 0:
            eta = elapsed / progress * (1 - progress)
            eta_str = f"{eta:.1f}s"
        else:
            eta_str = "?s"
            
        # Clear the line and print the progress bar
        print(f'\r{Colors.CYAN}{self.desc}{Colors.RESET} |{Colors.GREEN}{bar}{Colors.RESET}| '
              f'{Colors.BOLD}{percentage:5.1f}%{Colors.RESET} '
              f'[{self.current}/{self.total}, ETA: {eta_str}]', end='', flush=True)
        
        if self.current >= self.total:
            print()  # New line when complete

def print_colored(text: str, color: str = Colors.WHITE, bold: bool = False, dim: bool = False):
    """Print colored text to terminal"""
    style = ""
    if bold:
        style += Colors.BOLD
    if dim:
        style += Colors.DIM
    
    print(f"{style}{color}{text}{Colors.RESET}")

def print_header(text: str):
    """Print a header with styling"""
    print_colored("=" * 60, Colors.CYAN, bold=True)
    print_colored(f" {text} ", Colors.WHITE, bold=True)
    print_colored("=" * 60, Colors.CYAN, bold=True)

def print_step(step: int, text: str):
    """Print a numbered step"""
    print_colored(f"[{step}] {text}", Colors.YELLOW, bold=True)

def print_success(text: str):
    """Print success message"""
    print_colored(f"✓ {text}", Colors.GREEN, bold=True)

def print_error(text: str):
    """Print error message"""
    print_colored(f"✗ {text}", Colors.RED, bold=True)

def print_warning(text: str):
    """Print warning message"""
    print_colored(f"⚠ {text}", Colors.YELLOW, bold=True)

def print_info(text: str):
    """Print info message"""
    print_colored(f"ℹ {text}", Colors.BLUE)

# ============================================================================
# CLI Interface Functions
# ============================================================================

def prompt_for_stmp_path() -> Optional[Path]:
    """Interactive prompt for STMP installation directory"""
    print_header("STMP Directory Detection")
    
    print_info("Please specify the path to your STMP installation directory.")
    print_info("This should be the directory containing 'server.js' and a 'src' folder.")
    print()
    
    while True:
        try:
            path_input = input(f"{Colors.CYAN}Enter STMP directory path: {Colors.RESET}").strip()
            
            if not path_input:
                print_error("Path cannot be empty. Please try again.")
                continue
                
            path = Path(path_input).resolve()
            
            if not path.exists():
                print_error(f"Directory does not exist: {path}")
                continue
                
            # Check for server.js
            server_js = path / "server.js"
            if not server_js.exists():
                print_warning(f"server.js not found in {path}")
                response = input(f"{Colors.YELLOW}Continue anyway? (y/n): {Colors.RESET}").strip().lower()
                if response not in ['y', 'yes']:
                    continue
                    
            # Check for src directory
            src_dir = path / "src"
            if not src_dir.exists():
                print_error(f"'src' directory not found in {path}")
                continue
                
            # Check for api-calls.js
            api_calls = src_dir / "api-calls.js"
            if not api_calls.exists():
                print_error(f"api-calls.js not found in {src_dir}")
                continue
                
            print_success(f"Valid STMP installation found at: {path}")
            return path
            
        except KeyboardInterrupt:
            print("\n")
            print_error("Operation cancelled by user.")
            return None
        except Exception as e:
            print_error(f"Error processing path: {e}")

def confirm_operation(operation: str) -> bool:
    """Confirm a potentially destructive operation"""
    print_warning(f"About to {operation}")
    response = input(f"{Colors.YELLOW}Continue? (y/n): {Colors.RESET}").strip().lower()
    return response in ['y', 'yes']


class STMPPatcher:
    """
    Complex pattern-based source code patcher for STMP integration.
    
    Uses multi-stage pattern matching and text transformation to inject
    username tracking parameters into message construction code.
    """
    
    def __init__(self, stmp_path: str = None, dry_run: bool = False):
        self.stmp_path = Path(stmp_path) if stmp_path else None
        self.dry_run = dry_run
        self.backup_suffix = ".irp-backup"
        self.modifications_made = []
    
    def validate_target_file(self, file_path: Path) -> bool:
        """
        Validate that the target file contains expected STMP patterns.
        """
        print_info(f"Validating target file: {file_path.name}")
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Check for STMP-specific markers
            required_patterns = [
                (r'function\s+addCharDefsToPrompt', 'addCharDefsToPrompt function'),
                (r'CCMessageObj\s*=\s*\[\]', 'CCMessageObj array'),
                (r'role:\s*[\'"]user[\'"]', 'user role pattern'),
                (r'role:\s*[\'"]assistant[\'"]', 'assistant role pattern')
            ]
            
            progress = ProgressBar(len(required_patterns), "Validating patterns")
            
            for pattern, description in required_patterns:
                if not re.search(pattern, content):
                    print_error(f"Required pattern not found: {description}")
                    return False
                progress.update(1)
                    
            print_success("All required patterns found - valid STMP file")
            return True
        except Exception as e:
            print_error(f"Error validating target file: {e}")
            return False
    
    def analyze_newobj_patterns(self, content: str) -> List[Dict[str, Any]]:
        """
        Phase 1: Complex pattern analysis for newObj assignments.
        
        Searches for patterns matching:
        1. 'newObj' identifier
        2. Whitespace + '=' assignment operator  
        3. Whitespace + '{' object literal start
        4. Content property existence
        5. Line ending analysis
        6. Closing brace detection
        """
        lines = content.split('\n')
        patterns = []
        
        for i, line in enumerate(lines):
            # Stage 1: Look for 'newObj' identifier
            newobj_match = re.search(r'\bnewObj\b', line)
            if not newobj_match:
                continue
                
            # Stage 2: Check for whitespace + '=' after newObj
            post_newobj = line[newobj_match.end():]
            equals_match = re.search(r'\s*=', post_newobj)
            if not equals_match:
                continue
                
            # Stage 3: Check for whitespace + '{' after '='
            post_equals = post_newobj[equals_match.end():]
            brace_match = re.search(r'\s*\{', post_equals)
            if not brace_match:
                continue
                
            # Stage 4: Analyze the object structure
            pattern_info = self._analyze_object_structure(lines, i)
            if pattern_info:
                pattern_info['line_number'] = i
                pattern_info['original_line'] = line
                patterns.append(pattern_info)
                
        return patterns
    
    def _analyze_object_structure(self, lines: List[str], start_line: int) -> Optional[Dict[str, Any]]:
        """
        Phase 2: Deep structure analysis of object literals.
        
        Examines object properties and structure to determine if this is
        a Chat Completion message object that needs patching.
        """
        structure_info = {
            'has_role_property': False,
            'has_content_property': False,
            'content_line': -1,
            'content_ends_with_comma': False,
            'closing_brace_line': -1,
            'is_user_or_assistant': False
        }
        
        # Scan forward from the newObj line to analyze structure
        brace_count = 0
        found_opening_brace = False
        
        for i in range(start_line, min(start_line + 20, len(lines))):
            line = lines[i].strip()
            
            # Count braces to track object boundaries
            brace_count += line.count('{') - line.count('}')
            
            if '{' in line and not found_opening_brace:
                found_opening_brace = True
                
            # Look for role property
            role_match = re.search(r'role:\s*[\'\"](user|assistant)[\'\"]', line)
            if role_match:
                structure_info['has_role_property'] = True
                structure_info['is_user_or_assistant'] = True
                
            # Look for content property
            content_match = re.search(r'content:', line)
            if content_match:
                structure_info['has_content_property'] = True
                structure_info['content_line'] = i
                
                # Check if content line ends with comma
                content_end = line.strip()
                if content_end.endswith(','):
                    structure_info['content_ends_with_comma'] = True
                    
            # Look for closing brace
            if found_opening_brace and brace_count == 0 and '}' in line:
                structure_info['closing_brace_line'] = i
                break
                
        # Validate that this is a CC message object we should patch
        if (structure_info['has_role_property'] and 
            structure_info['has_content_property'] and 
            structure_info['is_user_or_assistant'] and
            structure_info['closing_brace_line'] > structure_info['content_line']):
            return structure_info
            
        return None
    
    def generate_patch_insertions(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Phase 3: Generate precise insertion points and content.
        
        Creates patch instructions for each identified pattern.
        """
        insertions = []
        
        for pattern in patterns:
            content_line = pattern['content_line']
            closing_brace_line = pattern['closing_brace_line']
            
            # Determine insertion strategy
            if pattern['content_ends_with_comma']:
                # Content already has comma, insert after content line
                insertion_line = content_line + 1
                insertion_content = "                    'irp-next': obj.username"
            else:
                # Need to add comma to content line and insert after
                insertion_line = content_line + 1
                insertion_content = "                    'irp-next': obj.username"
                
            insertions.append({
                'line_number': insertion_line,
                'content': insertion_content,
                'needs_content_comma': not pattern['content_ends_with_comma'],
                'content_line': content_line,
                'pattern_info': pattern
            })
            
        return insertions
    
    def apply_content_comma_fixes(self, lines: List[str], insertions: List[Dict[str, Any]]) -> List[str]:
        """
        Phase 4: Apply comma corrections to content lines.

        JavaScript syntax requires commas between properties in object literals.
        """
        modified_lines = lines.copy()
        
        # Sort by line number in reverse to avoid index shifting
        for insertion in sorted(insertions, key=lambda x: x['content_line'], reverse=True):
            if insertion['needs_content_comma']:
                content_line_idx = insertion['content_line']
                line = modified_lines[content_line_idx]
                
                # Add comma if line doesn't end with one
                if not line.rstrip().endswith(','):
                    # Find the last non-whitespace character and add comma
                    stripped = line.rstrip()
                    trailing_ws = line[len(stripped):]
                    modified_lines[content_line_idx] = stripped + ',' + trailing_ws
                    
        return modified_lines
    
    def apply_irp_insertions(self, lines: List[str], insertions: List[Dict[str, Any]]) -> List[str]:
        """
        Phase 5: Insert 'irp-next' parameter lines.
        
        Performs the actual text insertion while maintaining proper formatting.
        """
        modified_lines = lines.copy()
        
        # Sort by line number in reverse to avoid index shifting during insertion
        for insertion in sorted(insertions, key=lambda x: x['line_number'], reverse=True):
            insertion_line = insertion['line_number']
            insertion_content = insertion['content']
            
            # Insert the new line
            modified_lines.insert(insertion_line, insertion_content)
            
            # Track modification for reporting
            self.modifications_made.append({
                'type': 'irp_parameter_insertion',
                'line': insertion_line,
                'content': insertion_content.strip()
            })
            
        return modified_lines
    
    def patch_stmp_api_calls(self, stmp_path: str = None, dry_run: bool = None) -> Dict[str, Any]:
        """
        Main entry point for STMP patching operation.
        
        Orchestrates the multi-phase patching process with comprehensive
        validation and error handling.
        
        Args:
            stmp_path: Path to STMP installation directory
            dry_run: If True, analyze only without making changes
            
        Returns:
            Dictionary containing patch results and statistics
        """
        if dry_run is not None:
            self.dry_run = dry_run
            
        if stmp_path:
            self.stmp_path = Path(stmp_path)
            
        if not self.stmp_path:
            return {
                'success': False,
                'error': 'Could not locate STMP installation directory',
                'suggestions': [
                    'Make sure you have installed STMP correctly',
                    'Provide explicit path to STMP installation',
                    'Check that src/api-calls.js exists in STMP directory'
                ]
            }
            
        target_file = self.stmp_path / "src" / "api-calls.js"
        
        if not target_file.exists():
            return {
                'success': False,
                'error': f'Target file not found: {target_file}',
                'stmp_path': str(self.stmp_path)
            }
            
        if not self.validate_target_file(target_file):
            return {
                'success': False,
                'error': 'Target file does not appear to be a valid STMP api-calls.js file',
                'file_path': str(target_file)
            }
            
        try:
            # Read original content
            original_content = target_file.read_text(encoding='utf-8')
            
            # Phase 1: Pattern analysis
            print_step(1, "Analyzing newObj assignment patterns")
            patterns = self.analyze_newobj_patterns(original_content)
            
            if not patterns:
                print_error("No patchable newObj patterns found in target file")
                print_info("File may already be patched or have different structure")
                return {
                    'success': False,
                    'error': 'No patchable newObj patterns found in target file',
                    'analysis': 'File may already be patched or have different structure'
                }
                
            print_success(f"Found {len(patterns)} patchable patterns")
            
            # Phase 2: Generate insertion points
            print_step(2, "Generating patch insertion points")
            insertions = self.generate_patch_insertions(patterns)
            print_success(f"Generated {len(insertions)} insertion points")
            
            # Phase 3: Apply modifications
            print_step(3, "Applying modifications")
            lines = original_content.split('\n')
            
            # Apply comma fixes first
            lines = self.apply_content_comma_fixes(lines, insertions)
            
            # Apply IRP parameter insertions
            lines = self.apply_irp_insertions(lines, insertions)
            
            modified_content = '\n'.join(lines)
            
            if self.dry_run:
                return {
                    'success': True,
                    'dry_run': True,
                    'patterns_found': len(patterns),
                    'insertions_planned': len(insertions),
                    'modifications': self.modifications_made,
                    'preview': self._generate_diff_preview(original_content, modified_content)
                }
            
            # Create backup
            backup_file = target_file.with_suffix(target_file.suffix + self.backup_suffix)
            shutil.copy2(target_file, backup_file)
            
            # Write modified content
            target_file.write_text(modified_content, encoding='utf-8')
            
            return {
                'success': True,
                'patterns_patched': len(patterns),
                'insertions_made': len(insertions),
                'modifications': self.modifications_made,
                'backup_created': str(backup_file),
                'target_file': str(target_file)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Patching failed: {str(e)}',
                'exception_type': type(e).__name__
            }
    
    def _generate_diff_preview(self, original: str, modified: str) -> List[str]:
        """Generate a preview of changes that would be made."""
        orig_lines = original.split('\n')
        mod_lines = modified.split('\n')
        
        preview = []
        for i, (orig, mod) in enumerate(zip(orig_lines, mod_lines)):
            if orig != mod:
                preview.append(f"Line {i+1}:")
                preview.append(f"  - {orig}")
                preview.append(f"  + {mod}")
                
        # Handle case where modified has more lines
        if len(mod_lines) > len(orig_lines):
            for i in range(len(orig_lines), len(mod_lines)):
                preview.append(f"Line {i+1} (new):")
                preview.append(f"  + {mod_lines[i]}")
                
        return preview[:20]  # Limit preview length
    
    def restore_backup(self, stmp_path: str = None) -> Dict[str, Any]:
        """
        Restore original file from backup.
        """
        if stmp_path:
            self.stmp_path = Path(stmp_path)
            
        if not self.stmp_path:
            return {'success': False, 'error': 'Could not locate STMP installation'}
            
        target_file = self.stmp_path / "src" / "api-calls.js"
        backup_file = target_file.with_suffix(target_file.suffix + self.backup_suffix)
        
        if not backup_file.exists():
            return {'success': False, 'error': 'No backup file found'}
            
        try:
            shutil.copy2(backup_file, target_file)
            return {
                'success': True,
                'restored_from': str(backup_file),
                'target_file': str(target_file)
            }
        except Exception as e:
            return {'success': False, 'error': f'Restore failed: {str(e)}'}


def display_welcome():
    """Display welcome banner"""
    print()
    print_header("STMP IRP-Next Username Patcher")
    print()
    print_info("This tool patches STMP's api-calls.js file to inject 'irp-next' username")
    print_info("parameters into Chat Completion message objects.")
    print()

def show_menu() -> str:
    """Display main menu and get user choice"""
    print_header("Select Operation")
    print()
    print_colored("1. Patch STMP installation", Colors.GREEN, bold=True)
    print_colored("2. Restore from backup", Colors.YELLOW, bold=True)
    print_colored("3. Dry run (analyze only)", Colors.BLUE, bold=True)
    print_colored("4. Exit", Colors.RED, bold=True)
    print()
    
    while True:
        try:
            choice = input(f"{Colors.CYAN}Enter your choice (1-4): {Colors.RESET}").strip()
            if choice in ['1', '2', '3', '4']:
                return choice
            else:
                print_error("Invalid choice. Please enter 1, 2, 3, or 4.")
        except KeyboardInterrupt:
            print("\n")
            print_error("Operation cancelled by user.")
            sys.exit(0)

def run_patch_operation(stmp_path: Path, dry_run: bool = False):
    """Run the patching operation with progress feedback"""
    patcher = STMPPatcher(stmp_path=str(stmp_path), dry_run=dry_run)
    
    print_header("Starting Patch Operation")
    print()
    
    if not dry_run and not confirm_operation("patch the STMP installation"):
        print_info("Operation cancelled.")
        return
    
    # Progress tracking
    overall_progress = ProgressBar(5, "Overall progress")
    
    try:
        overall_progress.update(1)
        
        result = patcher.patch_stmp_api_calls()
        overall_progress.update(4)  # Complete remaining steps
        
        if result['success']:
            print()
            if dry_run:
                print_success("Dry run completed successfully!")
                print_info(f"Found {result.get('patterns_found', 0)} patchable patterns")
                print_info(f"Would make {result.get('insertions_planned', 0)} insertions")
                
                if 'modifications' in result:
                    print_info("Planned modifications:")
                    for mod in result['modifications']:
                        print_colored(f"  - {mod['type']}: {mod['content']}", Colors.DIM)
            else:
                print_success("STMP patching completed successfully!")
                print_success(f"Patched {result.get('patterns_patched', 0)} patterns")
                print_success(f"Made {result.get('insertions_made', 0)} insertions")
                print_success(f"Backup created: {result.get('backup_created', 'N/A')}")
        else:
            print_error(f"Patching failed: {result.get('error', 'Unknown error')}")
            if 'suggestions' in result:
                print_info("Suggestions:")
                for suggestion in result['suggestions']:
                    print_colored(f"  - {suggestion}", Colors.BLUE)
                    
    except Exception as e:
        print_error(f"Unexpected error during patching: {e}")

def run_restore_operation(stmp_path: Path):
    """Run the restore operation"""
    patcher = STMPPatcher(stmp_path=str(stmp_path))
    
    print_header("Starting Restore Operation")
    print()
    
    if not confirm_operation("restore from backup (this will overwrite current api-calls.js)"):
        print_info("Operation cancelled.")
        return
    
    progress = ProgressBar(2, "Restoring backup")
    
    try:
        result = patcher.restore_backup()
        progress.update(2)
        
        if result['success']:
            print()
            print_success("Backup restored successfully!")
            print_success(f"Restored from: {result.get('restored_from', 'N/A')}")
        else:
            print_error(f"Restore failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print_error(f"Unexpected error during restore: {e}")

def main():
    """Main CLI interface"""
    try:
        display_welcome()
        
        while True:
            choice = show_menu()
            
            if choice == '4':  # Exit
                print_info("Goodbye!")
                sys.exit(0)
            
            # Get STMP path for all operations
            stmp_path = prompt_for_stmp_path()
            if not stmp_path:
                continue
                
            if choice == '1':  # Patch
                run_patch_operation(stmp_path, dry_run=False)
            elif choice == '2':  # Restore
                run_restore_operation(stmp_path)
            elif choice == '3':  # Dry run
                run_patch_operation(stmp_path, dry_run=True)
            
            print()
            input(f"{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
            print()
            
    except KeyboardInterrupt:
        print("\n")
        print_error("Operation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()