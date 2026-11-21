@echo off
setlocal
cd /d "%~dp0"
title Trailwise first-time setup

if not exist "app.py" (
    echo Could not find app.py. Keep this batch file in the project folder.
    goto :failed
)
if not exist "requirements.txt" (
    echo Could not find requirements.txt. Keep this batch file in the project folder.
    goto :failed
)

rem Prefer the Python launcher, which can select an installed Python 3 version.
where py >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
) else (
    where python >nul 2>&1
    if errorlevel 1 goto :python_missing
    set "PYTHON_CMD=python"
)

%PYTHON_CMD% -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 goto :python_too_old

if not exist ".venv\Scripts\python.exe" (
    echo Creating the project virtual environment...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 goto :setup_failed
)

echo Updating pip and installing project dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :setup_failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :setup_failed

echo.
echo Setup is complete. Starting Trailwise...
echo Keep this window open while using the app. Press Ctrl+C to stop it.
echo.
".venv\Scripts\python.exe" -m streamlit run app.py
if errorlevel 1 goto :app_failed
goto :end

:python_missing
echo Python 3.10 or newer was not found.
echo Install Python from https://www.python.org/downloads/ and enable the Python launcher or PATH option.
goto :failed

:python_too_old
echo Trailwise requires Python 3.10 or newer. Install a current Python 3 version and run setup again.
goto :failed

:setup_failed
echo Setup failed. Check the error above and your internet connection, then run this file again.
goto :failed

:app_failed
echo The app stopped with an error. Check the message above.
goto :failed

:failed
echo.
pause
exit /b 1

:end
endlocal
