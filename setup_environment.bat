@echo off
echo ========================================
echo Smith & Williams Trucking - Setup Script
echo ========================================
echo.

REM Check if virtual environment exists
if exist "venv" (
    echo Virtual environment already exists.
    echo Activating existing environment...
    call venv\Scripts\activate
) else (
    echo Creating virtual environment...
    python -m venv venv
    
    echo Activating virtual environment...
    call venv\Scripts\activate
    
    echo Upgrading pip...
    python -m pip install --upgrade pip
)

echo.
echo Installing required packages...
pip install streamlit pandas pillow reportlab

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To run the application:
echo 1. Activate virtual environment: venv\Scripts\activate
echo 2. Run the app: streamlit run app_v2_fixed.py
echo.
pause