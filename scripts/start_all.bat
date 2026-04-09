@echo off
REM FleetPredict Pro - Start everything on Windows
REM Run from dev folder: scripts\start_all.bat
REM Or double-click scripts\start_all.bat

cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0start_all.ps1"
pause
