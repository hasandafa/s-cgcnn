@echo off
REM =====================================
REM s-CGCNN v0.1 Windows Setup Script
REM Quick setup for Windows users
REM =====================================

echo.
echo ============================================
echo   s-CGCNN v0.1 - Windows Quick Setup
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.8-3.12 from https://www.python.org
    pause
    exit /b 1
)

echo [1/5] Python found
python --version

REM Create virtual environment
echo.
echo [2/5] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists, skipping...
) else (
    python -m venv venv
    echo Virtual environment created
)

REM Activate virtual environment
echo.
echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo [4/5] Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo.
echo [5/5] Installing dependencies...
echo This may take 5-10 minutes...
pip install -r requirements.txt

REM Create directory structure
echo.
echo Creating directory structure...
if not exist "data\raw" mkdir data\raw
if not exist "data\structures\cif" mkdir data\structures\cif
if not exist "data\structures\metadata" mkdir data\structures\metadata
if not exist "data\graphs" mkdir data\graphs
if not exist "data\processed" mkdir data\processed
if not exist "logs" mkdir logs
if not exist "results\figures" mkdir results\figures
if not exist "results\models" mkdir results\models
if not exist "notebooks" mkdir notebooks
if not exist "tests" mkdir tests

REM Create .gitkeep files (Windows equivalent)
type nul > data\.gitkeep
type nul > data\raw\.gitkeep
type nul > data\structures\.gitkeep
type nul > logs\.gitkeep
type nul > results\.gitkeep

echo.
echo ============================================
echo   Setup Complete!
echo ============================================
echo.
echo Next steps:
echo   1. Add your Materials Project API key:
echo      echo YOUR_API_KEY ^> config\mp_api_key.txt
echo.
echo   2. Run the test suite:
echo      python "1. Data Acquisition and Structure Interpolation Testing.py"
echo.
echo   3. Or explore with Jupyter:
echo      jupyter notebook
echo.
echo   4. Or run full pipeline:
echo      python run_version_0.1.py
echo.
pause