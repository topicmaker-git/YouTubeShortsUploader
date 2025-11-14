@echo off
REM ============================================
REM YouTube Shorts Scheduled Upload
REM Windows Task Scheduler용 자동 업로드 스크립트
REM ============================================

REM Change to script directory
cd /d "%~dp0"

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run scheduled upload (5 videos per run)
python main.py scheduled -c upload_list.csv -n 5

REM Deactivate virtual environment
call deactivate

REM Exit with the same error code as Python script
exit /b %ERRORLEVEL%
