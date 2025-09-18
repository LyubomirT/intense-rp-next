#!/usr/bin/env pwsh
# ===========================================================================
# IntenseRP Next - PyInstaller Build Script (Fixed Version)
# ===========================================================================
# This script builds the IntenseRP Next application using PyInstaller
# with all required assets and data files included.
# ===========================================================================

# Configuration Section
$Config = @{
    AppName = "IntenseRP Next"
    ExeName = "IntenseRP Next.exe"
    MaxRetries = 5
    RetryDelay = 2
}

# Enable colors in PowerShell (with error handling)
try {
    $Host.UI.RawUI.ForegroundColor = "White"
} catch {
    # Console doesn't support colors, continue without them
}

# Function to write colored output with error handling
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    try {
        if ($Host.UI.RawUI) {
            $originalColor = $Host.UI.RawUI.ForegroundColor
            $Host.UI.RawUI.ForegroundColor = $Color
            Write-Host $Message
            $Host.UI.RawUI.ForegroundColor = $originalColor
        } else {
            Write-Host $Message
        }
    } catch {
        # Fallback to plain output if color setting fails
        Write-Host $Message
    }
}

# Function to write section headers
function Write-SectionHeader {
    param([string]$Title)
    Write-Host ""
    Write-ColorOutput ("=" * 60) "Cyan"
    Write-ColorOutput " $Title" "Cyan"
    Write-ColorOutput ("=" * 60) "Cyan"
    Write-Host ""
}

# Function to check if file exists
function Test-RequiredFile {
    param(
        [string]$Path,
        [string]$Description
    )
    if (Test-Path $Path) {
        Write-ColorOutput "OK Found: $Description ($Path)" "Green"
        return $true
    } else {
        Write-ColorOutput "X Missing: $Description ($Path)" "Red"
        return $false
    }
}

# Function to check if directory exists
function Test-RequiredDirectory {
    param(
        [string]$Path,
        [string]$Description
    )
    if (Test-Path $Path -PathType Container) {
        Write-ColorOutput "OK Found: $Description ($Path)" "Green"
        return $true
    } else {
        Write-ColorOutput "X Missing: $Description ($Path)" "Red"
        return $false
    }
}

# Function to get system architecture
function Get-SystemArchitecture {
    if ([Environment]::Is64BitOperatingSystem) {
        return "amd64"
    } else {
        return "x86"
    }
}

# Function to retry file operations with delay
function Invoke-RetryOperation {
    param(
        [scriptblock]$Operation,
        [string]$Description,
        [int]$MaxRetries = $Config.MaxRetries,
        [int]$RetryDelay = $Config.RetryDelay
    )

    $retryCount = 0
    while ($retryCount -lt $MaxRetries) {
        try {
            & $Operation
            return $true
        } catch {
            $retryCount++
            if ($retryCount -eq $MaxRetries) {
                Write-ColorOutput "X Failed after $MaxRetries attempts: $Description" "Red"
                Write-ColorOutput "  Error: $($_.Exception.Message)" "Red"
                return $false
            }
            Write-ColorOutput "  Retry $retryCount/$MaxRetries for: $Description" "Yellow"
            Start-Sleep -Seconds $RetryDelay
        }
    }
}

# Main script execution
try {
    Write-SectionHeader "$($Config.AppName) - PyInstaller Build Script"

    # Get the script directory and project root
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $projectRoot = Split-Path -Parent $scriptDir

    Write-ColorOutput "Script Directory: $scriptDir" "Yellow"
    Write-ColorOutput "Project Root: $projectRoot" "Yellow"

    # Change to project root directory
    Set-Location $projectRoot
    Write-ColorOutput "Working Directory: $(Get-Location)" "Yellow"

    Write-SectionHeader "Checking Dependencies"

    # Check Python version
    Write-ColorOutput "Checking Python version..." "Yellow"
    try {
        $pythonVersion = & python --version 2>&1 | Out-String
        if ($pythonVersion -match "Python (\d+\.\d+)") {
            $version = [version]$matches[1]
            if ($version -ge [version]"3.7") {
                Write-ColorOutput "OK Python version: $pythonVersion" "Green"
            } else {
                Write-ColorOutput "X Python version too old: $pythonVersion (requires 3.7+)" "Red"
                exit 2
            }
        }
    } catch {
        Write-ColorOutput "X Python is not installed or not in PATH" "Red"
        exit 2
    }

    # Check if PyInstaller is installed (fixed version detection)
    Write-ColorOutput "Checking PyInstaller installation..." "Yellow"
    try {
        # PyInstaller outputs version to stderr, so capture both streams
        $pyinstallerVersion = & pyinstaller --version 2>&1 | Out-String
        if ($pyinstallerVersion) {
            Write-ColorOutput "OK PyInstaller is installed: $($pyinstallerVersion.Trim())" "Green"
        } else {
            throw "No version output"
        }
    } catch {
        Write-ColorOutput "X PyInstaller is not installed or not in PATH" "Red"
        Write-ColorOutput "Please install PyInstaller: pip install pyinstaller" "Red"
        exit 3
    }

    Write-SectionHeader "Verifying Required Files and Directories"

    # Define paths relative to project root
    $mainFile = "src\main.pyw"
    $iconFile = "src\newlogo.ico"
    $extensionDir = "src\extension"
    $assetsDir = "src\assets"
    $licenseFile = "LICENSE"
    $logoPngFile = "src\newlogo.png"

    # Check all required files and directories
    $allFilesExist = $true

    $allFilesExist = $allFilesExist -and (Test-RequiredFile $mainFile "Main Python file")
    $allFilesExist = $allFilesExist -and (Test-RequiredFile $iconFile "Application icon")
    $allFilesExist = $allFilesExist -and (Test-RequiredDirectory $extensionDir "Extension directory")
    $allFilesExist = $allFilesExist -and (Test-RequiredDirectory $assetsDir "Assets directory")
    $allFilesExist = $allFilesExist -and (Test-RequiredFile $licenseFile "License file")
    $allFilesExist = $allFilesExist -and (Test-RequiredFile $logoPngFile "Application logo PNG")

    # Additional validation for assets structure
    if ($allFilesExist) {
        if (-not (Test-Path "$assetsDir\fonts")) {
            Write-ColorOutput "Warning: No fonts directory found in assets" "Yellow"
        } elseif (-not (Test-Path "$assetsDir\fonts\*.ttf")) {
            Write-ColorOutput "Warning: No TTF font files found in $assetsDir\fonts" "Yellow"
        }

        if (-not (Test-Path "$assetsDir\contributors.json")) {
            Write-ColorOutput "Warning: contributors.json not found in assets" "Yellow"
        }
    }

    if (-not $allFilesExist) {
        Write-ColorOutput "" "Red"
        Write-ColorOutput "X Some required files or directories are missing!" "Red"
        Write-ColorOutput "Please ensure all files are in place before building." "Red"
        exit 4
    }

    Write-ColorOutput "" "Green"
    Write-ColorOutput "OK All required files and directories found!" "Green"

    Write-SectionHeader "Preparing Build Environment"

    # Clean previous build if it exists
    $distDir = "dist"
    $buildDir = "build"
    $specFile = "main.spec"

    if (Test-Path $distDir) {
        Write-ColorOutput "Cleaning previous dist directory..." "Yellow"
        try {
            Remove-Item -Recurse -Force $distDir
            Write-ColorOutput "OK Previous dist directory cleaned" "Green"
        } catch {
            Write-ColorOutput "Warning: Could not fully clean dist directory" "Yellow"
        }
    }

    if (Test-Path $buildDir) {
        Write-ColorOutput "Cleaning previous build directory..." "Yellow"
        try {
            Remove-Item -Recurse -Force $buildDir
            Write-ColorOutput "OK Previous build directory cleaned" "Green"
        } catch {
            Write-ColorOutput "Warning: Could not fully clean build directory" "Yellow"
        }
    }

    if (Test-Path $specFile) {
        Write-ColorOutput "Cleaning previous spec file..." "Yellow"
        try {
            Remove-Item -Force $specFile
            Write-ColorOutput "OK Previous spec file cleaned" "Green"
        } catch {
            Write-ColorOutput "Warning: Could not remove spec file" "Yellow"
        }
    }

    Write-SectionHeader "Building Application with PyInstaller"

    # Build the PyInstaller command with fixed path separators
    $pyinstallerArgs = @(
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--icon", $iconFile,
        "--add-data", "$($extensionDir);extension",
        "--add-data", "$($assetsDir);assets",
        "--add-data", "$($licenseFile);.",
        "--add-data", "$($logoPngFile);.",
        "--hidden-import", "tkextrafont",
        "--collect-data", "tkextrafont",
        $mainFile
    )

    Write-ColorOutput "Executing PyInstaller command:" "Yellow"
    Write-ColorOutput "pyinstaller $($pyinstallerArgs -join ' ')" "Cyan"
    Write-Host ""

    # Execute PyInstaller using the args array properly
    Write-ColorOutput "Building application... This may take a few minutes." "Yellow"
    Write-ColorOutput "Please wait..." "Yellow"
    Write-Host ""

    $buildProcess = Start-Process -FilePath "pyinstaller" -ArgumentList $pyinstallerArgs -NoNewWindow -Wait -PassThru

    if ($buildProcess.ExitCode -eq 0) {
        Write-SectionHeader "Build Completed Successfully!"

        # Check if the executable was created
        $exePath = "dist\main\main.exe"
        if (Test-Path $exePath) {
            Write-ColorOutput "OK Executable created: $exePath" "Green"

            # Get file size
            $fileSize = (Get-Item $exePath).Length
            $fileSizeMB = [math]::Round($fileSize / 1MB, 2)
            Write-ColorOutput "OK Executable size: $fileSizeMB MB" "Green"

            # Count files in dist directory
            $distFiles = Get-ChildItem "dist\main" -Recurse | Measure-Object
            Write-ColorOutput "OK Total files in distribution: $($distFiles.Count)" "Green"

            Write-SectionHeader "Packaging and Finalizing"

            # Copy assets to root directory for easier access
            Write-ColorOutput "Copying assets to distribution root..." "Yellow"

            # Create assets directory in dist/main
            $assetsTargetDir = "dist\main\assets"
            if (-not (Test-Path $assetsTargetDir)) {
                New-Item -ItemType Directory -Path $assetsTargetDir -Force | Out-Null
            }

            # Copy fonts directory if it exists
            if (Test-Path "$assetsDir\fonts") {
                $fontsTargetDir = "$assetsTargetDir\fonts"
                if (-not (Test-Path $fontsTargetDir)) {
                    New-Item -ItemType Directory -Path $fontsTargetDir -Force | Out-Null
                }

                # Copy all font files if they exist
                $fontFiles = Get-ChildItem "$assetsDir\fonts\*.ttf" -ErrorAction SilentlyContinue
                if ($fontFiles) {
                    foreach ($fontFile in $fontFiles) {
                        Copy-Item -Path $fontFile.FullName -Destination $fontsTargetDir -Force
                        Write-ColorOutput "OK Copied font: $($fontFile.Name)" "Green"
                    }
                } else {
                    Write-ColorOutput "  No TTF fonts to copy" "Yellow"
                }
            }

            # Copy contributors.json if it exists
            if (Test-Path "$assetsDir\contributors.json") {
                Copy-Item -Path "$assetsDir\contributors.json" -Destination $assetsTargetDir -Force
                Write-ColorOutput "OK Copied contributors.json" "Green"
            }

            # Copy logo files to root
            Copy-Item -Path $logoPngFile -Destination "dist\main\" -Force
            Write-ColorOutput "OK Copied newlogo.png to root" "Green"

            # Icon file is already used by PyInstaller, but copy it too for consistency
            Copy-Item -Path $iconFile -Destination "dist\main\" -Force
            Write-ColorOutput "OK Copied newlogo.ico to root" "Green"

            Write-ColorOutput "OK All assets copied successfully" "Green"

            # Rename the executable
            $newExeName = $Config.ExeName
            $newExePath = "dist\main\$newExeName"

            Write-ColorOutput "Renaming executable to '$newExeName'..." "Yellow"
            $renameSuccess = Invoke-RetryOperation -Operation {
                Rename-Item -Path $exePath -NewName $newExeName -ErrorAction Stop
            } -Description "Rename executable"

            if (-not $renameSuccess) {
                exit 6
            }
            Write-ColorOutput "OK Executable renamed successfully" "Green"

            # Detect architecture and create appropriate folder name
            $arch = Get-SystemArchitecture
            $newFolderName = "intenserp-next-win32-$arch"
            $oldFolderPath = "dist\main"
            $newFolderPath = "dist\$newFolderName"

            Write-ColorOutput "Renaming distribution folder to '$newFolderName'..." "Yellow"

            # Use retry logic for folder rename to handle potential file locks
            $renameFolderSuccess = Invoke-RetryOperation -Operation {
                # Ensure no existing folder with the new name
                if (Test-Path $newFolderPath) {
                    Remove-Item -Path $newFolderPath -Recurse -Force -ErrorAction Stop
                }
                Move-Item -Path $oldFolderPath -Destination $newFolderPath -Force -ErrorAction Stop
            } -Description "Rename distribution folder"

            if (-not $renameFolderSuccess) {
                Write-ColorOutput "  This might be due to file locks or permissions. Try closing any file explorers viewing the dist folder." "Yellow"
                exit 7
            }

            # Verify the rename was successful
            if (Test-Path $newFolderPath) {
                Write-ColorOutput "OK Distribution folder renamed successfully" "Green"
            } else {
                Write-ColorOutput "X Distribution folder rename failed - destination not found" "Red"
                exit 7
            }

            # Create zip file
            $zipFileName = "$newFolderName.zip"
            $zipPath = "dist\$zipFileName"

            Write-ColorOutput "Creating zip archive '$zipFileName'..." "Yellow"

            $zipSuccess = Invoke-RetryOperation -Operation {
                # Remove existing zip if it exists
                if (Test-Path $zipPath) {
                    Remove-Item -Path $zipPath -Force -ErrorAction Stop
                }

                # Create the zip archive
                Compress-Archive -Path $newFolderPath -DestinationPath $zipPath -CompressionLevel Optimal -ErrorAction Stop
            } -Description "Create zip archive"

            if (-not $zipSuccess) {
                exit 8
            }

            # Get zip file size
            $zipSize = (Get-Item $zipPath).Length
            $zipSizeMB = [math]::Round($zipSize / 1MB, 2)

            Write-ColorOutput "OK Zip archive created successfully ($zipSizeMB MB)" "Green"

            # Verify build output
            Write-SectionHeader "Build Verification"

            $verificationPassed = $true

            # Check executable exists
            if (Test-Path "$newFolderPath\$newExeName") {
                Write-ColorOutput "OK Executable verified" "Green"
            } else {
                Write-ColorOutput "X Executable not found in distribution" "Red"
                $verificationPassed = $false
            }

            # Check data directories
            if (Test-Path "$newFolderPath\extension") {
                Write-ColorOutput "OK Extension data verified" "Green"
            } else {
                Write-ColorOutput "X Extension data missing" "Red"
                $verificationPassed = $false
            }

            if (Test-Path "$newFolderPath\assets") {
                Write-ColorOutput "OK Assets data verified" "Green"
            } else {
                Write-ColorOutput "X Assets data missing" "Red"
                $verificationPassed = $false
            }

            if ($verificationPassed) {
                Write-Host ""
                Write-ColorOutput "SUCCESS! Build and packaging completed successfully!" "Green"
                Write-ColorOutput "Architecture: $arch" "Green"
                Write-ColorOutput "Distribution folder:" "Green"
                Write-ColorOutput "  $(Resolve-Path $newFolderPath)" "Cyan"
                Write-ColorOutput "Zip archive:" "Green"
                Write-ColorOutput "  $(Resolve-Path $zipPath)" "Cyan"
                Write-ColorOutput "Run the application with:" "Green"
                Write-ColorOutput "  .\$newFolderPath\$newExeName" "Cyan"
            } else {
                Write-ColorOutput "WARNING: Build completed but verification found issues" "Yellow"
                exit 9
            }

        } else {
            Write-ColorOutput "X Executable not found at expected location!" "Red"
            Write-ColorOutput "Check the build output for errors." "Red"
            exit 10
        }

    } else {
        Write-ColorOutput "X Build failed with exit code: $($buildProcess.ExitCode)" "Red"
        Write-ColorOutput "Check the output above for error details." "Red"
        exit 11
    }

} catch {
    Write-ColorOutput "" "Red"
    Write-ColorOutput "X An unexpected error occurred during the build process:" "Red"
    Write-ColorOutput $_.Exception.Message "Red"
    Write-ColorOutput $_.ScriptStackTrace "Red"
    exit 99
} finally {
    Write-SectionHeader "Build Process Complete"
    Write-ColorOutput "Script execution finished." "Green"
}

# Exit codes:
# 0  - Success
# 2  - Python not installed or version too old
# 3  - PyInstaller not installed
# 4  - Required files missing
# 5  - Asset copying failed
# 6  - Executable rename failed
# 7  - Folder rename failed
# 8  - Zip creation failed
# 9  - Build verification failed
# 10 - Executable not created
# 11 - PyInstaller build failed
# 99 - Unexpected error