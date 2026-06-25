@echo off
setlocal

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0flujo_noticias_ela.ps1" %*
exit /b %ERRORLEVEL%
