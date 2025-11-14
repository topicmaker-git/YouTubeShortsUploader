@echo off
echo ========================================
echo ffmpeg Installation Helper
echo ========================================
echo.

REM Check if ffmpeg is already installed
ffmpeg -version > nul 2>&1
if not errorlevel 1 (
    echo [OK] ffmpeg is already installed!
    ffmpeg -version 2>&1 | findstr "ffmpeg version"
    echo.
    pause
    exit /b 0
)

echo ffmpeg is not installed.
echo.
echo This script will help you install ffmpeg.
echo.
echo Installation options:
echo 1. Install Chocolatey and then ffmpeg (recommended)
echo 2. Install Scoop and then ffmpeg
echo 3. Download ffmpeg manually (portable)
echo 4. Cancel
echo.

choice /C 1234 /M "Select an option"
set OPTION=%errorlevel%

if %OPTION%==1 goto install_choco
if %OPTION%==2 goto install_scoop
if %OPTION%==3 goto manual_download
if %OPTION%==4 goto cancel

:install_choco
echo.
echo Installing Chocolatey...
echo This requires administrator privileges.
echo.
pause

REM Install Chocolatey
powershell -NoProfile -ExecutionPolicy Bypass -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"

if errorlevel 1 (
    echo.
    echo [ERROR] Chocolatey installation failed.
    echo Please try another option or install manually.
    pause
    exit /b 1
)

echo.
echo [OK] Chocolatey installed successfully!
echo.
echo Installing ffmpeg via Chocolatey...
choco install ffmpeg -y

if errorlevel 1 (
    echo.
    echo [ERROR] ffmpeg installation failed.
    pause
    exit /b 1
)

echo.
echo [OK] ffmpeg installed successfully!
echo Please close and reopen your command prompt for changes to take effect.
pause
exit /b 0

:install_scoop
echo.
echo Installing Scoop...
echo.

REM Install Scoop
powershell -NoProfile -ExecutionPolicy Bypass -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser; Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression"

if errorlevel 1 (
    echo.
    echo [ERROR] Scoop installation failed.
    echo Please try another option or install manually.
    pause
    exit /b 1
)

echo.
echo [OK] Scoop installed successfully!
echo.
echo Installing ffmpeg via Scoop...
scoop install ffmpeg

if errorlevel 1 (
    echo.
    echo [ERROR] ffmpeg installation failed.
    pause
    exit /b 1
)

echo.
echo [OK] ffmpeg installed successfully!
echo Please close and reopen your command prompt for changes to take effect.
pause
exit /b 0

:manual_download
echo.
echo Manual Download Instructions:
echo.
echo 1. Visit: https://github.com/BtbN/FFmpeg-Builds/releases
echo 2. Download: ffmpeg-master-latest-win64-gpl.zip
echo 3. Extract the ZIP file
echo 4. Copy the 'bin' folder path (e.g., C:\ffmpeg\bin)
echo 5. Add it to your System PATH environment variable
echo.
echo Steps to add to PATH:
echo 1. Press Win+X and select "System"
echo 2. Click "Advanced system settings"
echo 3. Click "Environment Variables"
echo 4. Under "System variables", find "Path" and click "Edit"
echo 5. Click "New" and paste the bin folder path
echo 6. Click "OK" on all dialogs
echo 7. Restart your command prompt
echo.

choice /C YN /M "Open download page in browser?"
if not errorlevel 2 (
    start https://github.com/BtbN/FFmpeg-Builds/releases
)

echo.
pause
exit /b 0

:cancel
echo.
echo Installation cancelled.
echo.
echo Note: You can still use the uploader with --skip-validation option.
echo Example: run.bat upload video.mp4 -t "Title" --skip-validation
echo.
pause
exit /b 0
