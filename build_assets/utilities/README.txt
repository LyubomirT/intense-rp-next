IntenseRP Next Utilities Package
=================================

This package contains utility tools for IntenseRP Next integration:

INCLUDED UTILITIES:
==================

STMP Patcher
   - Patch SillyTavern Multiplayer (STMP) for IntenseRP Next integration
   - Inject 'irp-next' username parameters into STMP's api-calls.js
   - Interactive CLI with backup/restore functionality
   - Executable: STMP-Patcher.exe (Windows) | stmp-patcher (Linux)

SYSTEM REQUIREMENTS:
==================
- Windows 10/11 (x64) or Modern Linux Distribution
- Python 3.12+ (Linux only - Windows executables are self-contained)
- Existing STMP (SillyTavern Multiplayer) installation

QUICK START:
============

Windows:
--------
1. Extract all files to a directory
2. Double-click STMP-Patcher.exe to patch STMP installations

Linux:
------
1. Extract all files to a directory
2. Run: chmod +x stmp-patcher
3. Run: ./stmp-patcher to patch STMP installations

UTILITY DETAILS:
===============

STMP Patcher:
-------------
- Pattern-based JavaScript code modification
- Safe backup and restore functionality
- Dry-run mode for testing changes
- Step-by-step patching process with validation
- Detailed error reporting and recovery

SUPPORT & DOCUMENTATION:
========================
- GitHub Repository: https://github.com/LyubomirT/intense-rp-next
- Issue Tracker: https://github.com/LyubomirT/intense-rp-next/issues
- Documentation: Available in the main repository

LICENSE:
========
All utilities are distributed under the MIT License.
See individual tool documentation for specific license information.

CHANGELOG:
==========
This utilities package is updated alongside IntenseRP Next releases.
Check the main repository for detailed version history and changes.

TROUBLESHOOTING:
===============
1. Make sure all executables have proper permissions (Linux: chmod +x)
2. Windows users: If Windows Defender blocks execution, add to exceptions
3. Linux users: Install Python 3.12+ if not already available
4. For connection issues, check firewall and internet connectivity
5. Report bugs through the GitHub issue tracker

---
IntenseRP Next Utilities - Build Date: {BUILD_DATE}
Package Version: {PACKAGE_VERSION}