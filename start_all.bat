@echo off
REM FleetPredict Pro - Start everything on Windows
REM Run from dev folder: start_all.bat
REM Or double-click start_all.bat (must be run from dev folder)

cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0start_all.ps1"
pause
