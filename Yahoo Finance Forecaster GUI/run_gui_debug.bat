@echo off
title Yahoo Finance Forecaster GUI (Console Mode)
cd /d "%~dp0"
echo Menjalankan Yahoo Finance Forecaster GUI dengan terminal output...
python app.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Terjadi kesalahan saat menjalankan aplikasi.
    pause
)
