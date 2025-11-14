@echo off
echo ========================================
echo YouTube Shorts Uploader Setup
echo ========================================
echo.

REM Check if Python is installed
python --version > nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed.
    echo Please install Python 3.7 or later.
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python found
python --version
echo.

REM Check if virtual environment exists
if exist "venv\" (
    echo Virtual environment already exists.
    choice /C YN /M "Do you want to recreate it?"
    if errorlevel 2 goto :skip_venv_creation
    if errorlevel 1 (
        echo Removing existing virtual environment...
        rmdir /s /q venv
    )
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo Error: Failed to create virtual environment.
    pause
    exit /b 1
)
echo [OK] Virtual environment created
echo.

:skip_venv_creation

REM Activate virtual environment and install dependencies
echo Installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install dependencies.
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

REM Check if ffmpeg is installed
echo Checking for ffmpeg...
ffmpeg -version > nul 2>&1
if errorlevel 1 (
    echo [WARNING] ffmpeg is not installed.
    echo.
    echo ffmpeg is required for video validation.
    echo.

    REM Check if winget is available (Windows 10/11)
    winget --version > nul 2>&1
    if not errorlevel 1 (
        echo winget detected ^(Windows Package Manager^)!
        choice /C YN /M "Do you want to install ffmpeg using winget?"
        if not errorlevel 2 (
            echo Installing ffmpeg via winget...
            winget install -e --id Gyan.FFmpeg
            if not errorlevel 1 (
                echo [OK] ffmpeg installed successfully
                echo.
                echo IMPORTANT: Please close this terminal and open a new one
                echo to apply PATH changes. Then you can use video validation.
                echo.
            ) else (
                echo [WARNING] ffmpeg installation failed
                echo Trying alternative installation methods...
                echo.
                goto try_choco
            )
            goto ffmpeg_install_done
        )
    )

    :try_choco
    REM Check if Chocolatey is available
    choco --version > nul 2>&1
    if not errorlevel 1 (
        echo Chocolatey detected!
        choice /C YN /M "Do you want to install ffmpeg using Chocolatey?"
        if not errorlevel 2 (
            echo Installing ffmpeg via Chocolatey...
            choco install ffmpeg -y
            if not errorlevel 1 (
                echo [OK] ffmpeg installed successfully
                echo.
            ) else (
                echo [WARNING] ffmpeg installation failed
                echo.
            )
            goto ffmpeg_install_done
        )
    )

    REM No package manager available
    echo.
    echo No package manager detected.
    echo.
    echo Installation options:
    echo 1. Install portable version: run install_ffmpeg_portable.bat
    echo 2. Install via winget: winget install -e --id Gyan.FFmpeg
    echo 3. Install via Chocolatey: choco install ffmpeg
    echo 4. Manual: https://github.com/BtbN/FFmpeg-Builds/releases
    echo.
    echo Note: You can skip validation using --skip-validation option
    echo.
    goto ffmpeg_check_done
) else (
    echo [OK] ffmpeg found
    ffmpeg -version 2>&1 | findstr "ffmpeg version"
    echo.
)

:ffmpeg_install_done
:ffmpeg_check_done

REM Check for client_secret file
if not exist "client_secret*.json" (
    echo [WARNING] client_secret file not found.
    echo.
    echo Please download OAuth credentials from Google Cloud Console:
    echo 1. Visit https://console.cloud.google.com/
    echo 2. Select your project
    echo 3. Go to "APIs ^& Services" -^> "Credentials"
    echo 4. Download OAuth 2.0 Client ID
    echo 5. Place the JSON file in this directory
    echo.
) else (
    echo [OK] client_secret file found
    echo.
)

REM Create directory structure
if not exist "shorts_videos" mkdir shorts_videos
if not exist "logs" mkdir logs
echo [OK] Directory structure created
echo.

echo ========================================
echo Setup completed!
echo ========================================
echo.

REM Check if ffmpeg was just installed
ffmpeg -version > nul 2>&1
if errorlevel 1 (
    echo NOTE: If you just installed ffmpeg via winget,
    echo please close this terminal and open a new one
    echo before using video validation features.
    echo.
    echo You can still upload videos using --skip-validation option.
    echo.
)

echo Next steps:
echo.
echo 1. Place client_secret file if not already done
echo.
echo 2. If ffmpeg was just installed, close and reopen terminal
echo.
echo 3. Run authentication:
echo    run.bat auth --show-info
echo.
echo 4. Upload videos:
echo    run.bat upload shorts_videos\video.mp4 -t "Title"
echo.
echo For more details, see README.md
echo.
pause
