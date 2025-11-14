@echo off
echo ========================================
echo ffmpeg Portable Installation
echo ========================================
echo.

REM Check if ffmpeg is already installed
ffmpeg -version > nul 2>&1
if not errorlevel 1 (
    echo [OK] ffmpeg is already installed globally!
    ffmpeg -version 2>&1 | findstr "ffmpeg version"
    echo.
    pause
    exit /b 0
)

REM Check if local ffmpeg exists
if exist "ffmpeg\bin\ffmpeg.exe" (
    echo [OK] ffmpeg portable version is already installed!
    ffmpeg\bin\ffmpeg.exe -version 2>&1 | findstr "ffmpeg version"
    echo.
    pause
    exit /b 0
)

echo This script will download and install ffmpeg portable version.
echo The portable version will be placed in the project directory.
echo No system PATH modification required.
echo.

choice /C YN /M "Do you want to continue?"
if errorlevel 2 goto cancel

echo.
echo Downloading ffmpeg...
echo This may take a few minutes depending on your internet speed.
echo.

REM Create temporary directory
if not exist "temp" mkdir temp

REM Download ffmpeg using PowerShell
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip' -OutFile 'temp\ffmpeg.zip'"

if errorlevel 1 (
    echo.
    echo [ERROR] Download failed.
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

echo [OK] Download completed
echo.
echo Extracting ffmpeg...

REM Extract using PowerShell
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Path 'temp\ffmpeg.zip' -DestinationPath 'temp' -Force"

if errorlevel 1 (
    echo.
    echo [ERROR] Extraction failed.
    pause
    exit /b 1
)

echo [OK] Extraction completed
echo.
echo Installing ffmpeg...

REM Find the extracted folder
for /d %%i in (temp\ffmpeg-*) do set FFMPEG_DIR=%%i

REM Move to project directory
if not exist "ffmpeg" mkdir ffmpeg
xcopy /E /I /Y "%FFMPEG_DIR%\bin" "ffmpeg\bin" > nul
xcopy /E /I /Y "%FFMPEG_DIR%\doc" "ffmpeg\doc" > nul
xcopy /E /I /Y "%FFMPEG_DIR%\LICENSE.txt" "ffmpeg\" > nul
xcopy /E /I /Y "%FFMPEG_DIR%\README.txt" "ffmpeg\" > nul

REM Cleanup
rmdir /s /q temp

echo [OK] ffmpeg installed successfully!
echo.
echo Installation location: %CD%\ffmpeg\bin
echo.
echo Verifying installation...
ffmpeg\bin\ffmpeg.exe -version 2>&1 | findstr "ffmpeg version"
echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo ffmpeg is now available for this project.
echo You can now use video validation features.
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
