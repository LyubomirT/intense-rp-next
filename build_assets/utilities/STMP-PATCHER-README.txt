STMP Patcher for IntenseRP Next
===============================

OVERVIEW:
=========
The STMP Patcher is a standalone CLI tool that modifies SillyTavern Multiplayer 
(STMP) installations to integrate with IntenseRP Next by injecting 'irp-next' 
username parameters into Chat Completion message objects.

WHAT IT DOES:
=============
- Locates and validates STMP's api-calls.js file
- Performs surgical code modifications using pattern-based analysis
- Adds 'irp-next': obj.username parameters to message objects
- Creates automatic backups before making changes
- Provides detailed progress feedback and error reporting

SYSTEM REQUIREMENTS:
===================
- Windows 10/11 (x64) or Modern Linux Distribution  
- Existing STMP (SillyTavern Multiplayer) installation
- File system write permissions for STMP directory

USAGE INSTRUCTIONS:
==================

Windows:
--------
1. Double-click STMP-Patcher.exe to start
2. Follow the interactive prompts to:
   - Locate your STMP installation directory
   - Choose patch/restore/dry-run operations
3. The tool will guide you through the process

Linux:
------
1. Open terminal in the utilities directory
2. Make executable: chmod +x stmp-patcher
3. Run: ./stmp-patcher
4. Follow the interactive prompts

OPERATION MODES:
===============

1. Patch STMP Installation
   - Locates STMP directory containing server.js and src/api-calls.js  
   - Validates file structure and required patterns
   - Creates backup with .irp-backup suffix
   - Applies username parameter injections
   - Reports success/failure with detailed feedback

2. Restore from Backup  
   - Locates existing .irp-backup file
   - Restores original api-calls.js from backup
   - Useful for undoing changes or troubleshooting

3. Dry Run (Analyze Only)
   - Performs full analysis without making changes
   - Shows what would be modified
   - Useful for testing before applying changes
   - Generates diff preview of planned modifications

TECHNICAL DETAILS:
==================

Pattern Detection:
- Searches for 'newObj' assignment patterns
- Analyzes JavaScript object literal structures  
- Identifies role and content properties
- Validates Chat Completion message objects

Code Modification:
- Adds comma separators where needed
- Injects 'irp-next': obj.username property
- Maintains proper JavaScript syntax
- Preserves original code structure and formatting

Safety Features:
- Automatic backup creation (.irp-backup suffix)
- Comprehensive validation before modification
- Pattern-based approach avoids semantic analysis
- Detailed error reporting and recovery suggestions

SUPPORTED STMP VERSIONS:
========================
This patcher is designed to work with standard STMP installations that contain:
- server.js file in root directory
- src/api-calls.js with standard message handling patterns
- Standard JavaScript object literal message construction

TROUBLESHOOTING:
===============

Common Issues:
--------------
1. "STMP directory not found"
   - Ensure you're pointing to the correct STMP installation
   - Directory should contain server.js and src/ folder

2. "Required patterns not found"  
   - STMP version may be unsupported or heavily modified
   - Try dry-run mode first to see what patterns exist

3. "Patching failed"
   - Check file permissions (write access to STMP directory)
   - Ensure STMP is not running during patching
   - Verify no antivirus interference

4. "No patchable patterns found"
   - File may already be patched
   - STMP version might have different code structure
   - Use restore operation if previously patched

Recovery:
---------
- Backup files are automatically created as [filename].irp-backup
- Use "Restore from backup" option to undo changes
- Manual recovery: rename .irp-backup file back to original

ADVANCED USAGE:
===============

Command Line Options:
- The tool is fully interactive and doesn't require command-line arguments
- All operations are guided through menu selections
- Progress is shown with colored output and progress bars

Integration with IntenseRP Next:
- After patching, STMP will send username information to IntenseRP Next
- This enables proper user identification in multiplayer scenarios  
- No additional configuration required after successful patching

SUPPORT:
========
- Report issues: https://github.com/LyubomirT/intense-rp-next/issues
- Include STMP version and error messages in bug reports
- Backup files can be shared for troubleshooting

LEGAL:
======
This tool performs surgical modifications to JavaScript source code using
pattern-based text analysis. It does not embed or redistribute STMP code.
The approach is designed to avoid licensing issues by treating files as
plain text and applying transformations without semantic understanding.

---
STMP Patcher - Part of IntenseRP Next Utilities
Build Date: {BUILD_DATE} | Version: {PATCHER_VERSION}