#!/usr/bin/env pwsh
# ===========================================================================
# IntenseRP Next - PyInstaller Build Script
# ===========================================================================
# This script builds the IntenseRP Next application using PyInstaller
# with all required assets and data files included.
# ===========================================================================

# Enable colors in PowerShell
$Host.UI.RawUI.ForegroundColor = "White"

# Function to write colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    $originalColor = $Host.UI.RawUI.ForegroundColor
    $Host.UI.RawUI.ForegroundColor = $Color
    Write-Host $Message
    $Host.UI.RawUI.ForegroundColor = $originalColor
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
        Write-ColorOutput "✓ Found: $Description ($Path)" "Green"
        return $true
    } else {
        Write-ColorOutput "✗ Missing: $Description ($Path)" "Red"
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
        Write-ColorOutput "✓ Found: $Description ($Path)" "Green"
        return $true
    } else {
        Write-ColorOutput "✗ Missing: $Description ($Path)" "Red"
        return $false
    }
}

# Main script execution
try {
    Write-SectionHeader "IntenseRP Next - PyInstaller Build Script"
    
    # Get the script directory and project root
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $projectRoot = Split-Path -Parent $scriptDir
    
    Write-ColorOutput "Script Directory: $scriptDir" "Yellow"
    Write-ColorOutput "Project Root: $projectRoot" "Yellow"
    
    # Change to project root directory
    Set-Location $projectRoot
    Write-ColorOutput "Working Directory: $(Get-Location)" "Yellow"
    
    Write-SectionHeader "Checking Dependencies"
    
    # Check if PyInstaller is installed
    Write-ColorOutput "Checking PyInstaller installation..." "Yellow"
    try {
        $pyinstallerVersion = & pyinstaller --version 2>$null
        Write-ColorOutput "✓ PyInstaller is installed (version: $pyinstallerVersion)" "Green"
    } catch {
        Write-ColorOutput "✗ PyInstaller is not installed or not in PATH" "Red"
        Write-ColorOutput "Please install PyInstaller: pip install pyinstaller" "Red"
        exit 1
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
    
    if (-not $allFilesExist) {
        Write-ColorOutput "" "Red"
        Write-ColorOutput "✗ Some required files or directories are missing!" "Red"
        Write-ColorOutput "Please ensure all files are in place before building." "Red"
        exit 1
    }
    
    Write-ColorOutput "" "Green"
    Write-ColorOutput "✓ All required files and directories found!" "Green"
    
    Write-SectionHeader "Preparing Build Environment"
    
    # Clean previous build if it exists
    $distDir = "dist"
    $buildDir = "build"
    $specFile = "main.spec"
    
    if (Test-Path $distDir) {
        Write-ColorOutput "Cleaning previous dist directory..." "Yellow"
        Remove-Item -Recurse -Force $distDir
        Write-ColorOutput "✓ Previous dist directory cleaned" "Green"
    }
    
    if (Test-Path $buildDir) {
        Write-ColorOutput "Cleaning previous build directory..." "Yellow"
        Remove-Item -Recurse -Force $buildDir
        Write-ColorOutput "✓ Previous build directory cleaned" "Green"
    }
    
    if (Test-Path $specFile) {
        Write-ColorOutput "Cleaning previous spec file..." "Yellow"
        Remove-Item -Force $specFile
        Write-ColorOutput "✓ Previous spec file cleaned" "Green"
    }
    
    Write-SectionHeader "Building Application with PyInstaller"
    
    # Build the PyInstaller command
    $pyinstallerCmd = @(
        "pyinstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--icon", $iconFile,
        "--add-data", "$extensionDir;extension/",
        "--add-data", "$assetsDir;assets/",
        "--add-data", "$licenseFile;.",
        "--add-data", "$logoPngFile;.",
        "--hidden-import", "tkextrafont",
        "--collect-data", "tkextrafont",
        $mainFile
    )
    
    Write-ColorOutput "Executing PyInstaller command:" "Yellow"
    Write-ColorOutput ($pyinstallerCmd -join " ") "Cyan"
    Write-Host ""
    
    # Execute PyInstaller
    Write-ColorOutput "Building application... This may take a few minutes." "Yellow"
    Write-ColorOutput "Please wait..." "Yellow"
    Write-Host ""
    
    $buildProcess = Start-Process -FilePath "pyinstaller" -ArgumentList @(
        "--noconfirm",
        "--onedir", 
        "--windowed",
        "--icon", $iconFile,
        "--add-data", "$extensionDir;extension/",
        "--add-data", "$assetsDir;assets/",
        "--add-data", "$licenseFile;.",
        "--add-data", "$logoPngFile;.",
        "--hidden-import", "tkextrafont",
        "--collect-data", "tkextrafont",
        $mainFile
    ) -NoNewWindow -Wait -PassThru
    
    if ($buildProcess.ExitCode -eq 0) {
        Write-SectionHeader "Build Completed Successfully!"
        
        # Check if the executable was created
        $exePath = "dist\main\main.exe"
        if (Test-Path $exePath) {
            Write-ColorOutput "✓ Executable created: $exePath" "Green"
            
            # Get file size
            $fileSize = (Get-Item $exePath).Length
            $fileSizeMB = [math]::Round($fileSize / 1MB, 2)
            Write-ColorOutput "✓ Executable size: $fileSizeMB MB" "Green"
            
            # Count files in dist directory
            $distFiles = Get-ChildItem "dist\main" -Recurse | Measure-Object
            Write-ColorOutput "✓ Total files in distribution: $($distFiles.Count)" "Green"
            
            Write-SectionHeader "Packaging and Finalizing"
            
            # Copy assets to root directory for easier access
            Write-ColorOutput "Copying assets to distribution root..." "Yellow"
            try {
                # Create assets directory in dist/main
                $assetsTargetDir = "dist\main\assets"
                if (-not (Test-Path $assetsTargetDir)) {
                    New-Item -ItemType Directory -Path $assetsTargetDir -Force | Out-Null
                }
                
                # Copy fonts directory
                $fontsTargetDir = "$assetsTargetDir\fonts"
                if (-not (Test-Path $fontsTargetDir)) {
                    New-Item -ItemType Directory -Path $fontsTargetDir -Force | Out-Null
                }
                
                # Copy all font files
                $fontFiles = Get-ChildItem "$assetsDir\fonts\*.ttf"
                foreach ($fontFile in $fontFiles) {
                    Copy-Item -Path $fontFile.FullName -Destination $fontsTargetDir -Force
                    Write-ColorOutput "✓ Copied font: $($fontFile.Name)" "Green"
                }
                
                # Copy contributors.json
                Copy-Item -Path "$assetsDir\contributors.json" -Destination $assetsTargetDir -Force
                Write-ColorOutput "✓ Copied contributors.json" "Green"
                
                # Copy logo files to root
                Copy-Item -Path $logoPngFile -Destination "dist\main\" -Force
                Write-ColorOutput "✓ Copied newlogo.png to root" "Green"
                
                # Icon file is already used by PyInstaller, but copy it too for consistency
                Copy-Item -Path $iconFile -Destination "dist\main\" -Force
                Write-ColorOutput "✓ Copied newlogo.ico to root" "Green"
                
                Write-ColorOutput "✓ All assets copied successfully" "Green"
                
            } catch {
                Write-ColorOutput "✗ Failed to copy assets: $($_.Exception.Message)" "Red"
                exit 1
            }
            
            # Rename the executable
            $newExeName = "IntenseRP Next.exe"
            $newExePath = "dist\main\$newExeName"
            
            Write-ColorOutput "Renaming executable to '$newExeName'..." "Yellow"
            try {
                Rename-Item -Path $exePath -NewName $newExeName
                Write-ColorOutput "✓ Executable renamed successfully" "Green"
            } catch {
                Write-ColorOutput "✗ Failed to rename executable: $($_.Exception.Message)" "Red"
                exit 1
            }
            
            # Rename the main folder
            $oldFolderPath = "dist\main"
            $newFolderName = "intenserp-next-win64"
            $newFolderPath = "dist\$newFolderName"
            
            Write-ColorOutput "Renaming distribution folder to '$newFolderName'..." "Yellow"
            try {
                # Add a small delay to ensure file operations are complete
                Start-Sleep -Milliseconds 500
                
                # Use Move-Item instead of Rename-Item for better error handling
                Move-Item -Path $oldFolderPath -Destination $newFolderPath -Force
                
                # Verify the rename was successful
                if (Test-Path $newFolderPath) {
                    Write-ColorOutput "✓ Distribution folder renamed successfully" "Green"
                } else {
                    Write-ColorOutput "✗ Distribution folder rename failed - destination not found" "Red"
                    exit 1
                }
            } catch {
                Write-ColorOutput "✗ Failed to rename distribution folder: $($_.Exception.Message)" "Red"
                Write-ColorOutput "  This might be due to file locks or permissions. Try closing any file explorers viewing the dist folder." "Yellow"
                exit 1
            }
            
            # Create zip file
            $zipFileName = "$newFolderName.zip"
            $zipPath = "dist\$zipFileName"
            
            Write-ColorOutput "Creating zip archive '$zipFileName'..." "Yellow"
            try {
                # Remove existing zip if it exists
                if (Test-Path $zipPath) {
                    Remove-Item -Path $zipPath -Force
                }
                
                # Create the zip archive
                Compress-Archive -Path $newFolderPath -DestinationPath $zipPath -CompressionLevel Optimal
                
                # Get zip file size
                $zipSize = (Get-Item $zipPath).Length
                $zipSizeMB = [math]::Round($zipSize / 1MB, 2)
                
                Write-ColorOutput "✓ Zip archive created successfully ($zipSizeMB MB)" "Green"
            } catch {
                Write-ColorOutput "✗ Failed to create zip archive: $($_.Exception.Message)" "Red"
                exit 1
            }
            
            Write-Host ""
            Write-ColorOutput "🎉 Build and packaging completed successfully!" "Green"
            Write-ColorOutput "Distribution folder:" "Green"
            Write-ColorOutput "  $(Resolve-Path $newFolderPath)" "Cyan"
            Write-ColorOutput "Zip archive:" "Green"
            Write-ColorOutput "  $(Resolve-Path $zipPath)" "Cyan"
            Write-ColorOutput "Run the application with:" "Green"
            Write-ColorOutput "  .\dist\$newFolderName\$newExeName" "Cyan"
            
        } else {
            Write-ColorOutput "✗ Executable not found at expected location!" "Red"
            Write-ColorOutput "Check the build output for errors." "Red"
            exit 1
        }
        
    } else {
        Write-ColorOutput "✗ Build failed with exit code: $($buildProcess.ExitCode)" "Red"
        Write-ColorOutput "Check the output above for error details." "Red"
        exit 1
    }
    
} catch {
    Write-ColorOutput "" "Red"
    Write-ColorOutput "✗ An error occurred during the build process:" "Red"
    Write-ColorOutput $_.Exception.Message "Red"
    Write-ColorOutput $_.ScriptStackTrace "Red"
    exit 1
}

Write-SectionHeader "Build Process Complete"
Write-ColorOutput "Script execution finished." "Green"