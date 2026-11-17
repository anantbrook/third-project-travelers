@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating the project virtual environment...
    where python >nul 2>&1
    if errorlevel 1 goto :python_missing
    python -m venv .venv
    if errorlevel 1 goto :setup_failed
)

echo Installing or checking project dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :setup_failed

echo Starting the Travel Planning Assistant...
".venv\Scripts\python.exe" -m streamlit run app.py
if errorlevel 1 goto :app_failed
goto :end

:python_missing
echo Python was not found. Install Python 3.10 or newer and add it to PATH.
pause
exit /b 1

:setup_failed
echo Setup failed. Review the message above, then try again.
pause
exit /b 1

:app_failed
echo The app stopped with an error. Review the message above.
pause
exit /b 1

:end
endlocal
