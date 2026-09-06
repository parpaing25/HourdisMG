@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Bot de veille Hourdis
echo.
echo   Demarrage du bot de veille Hourdis (port 8761)...
echo.
python demarrer.py
if errorlevel 1 (
  echo.
  echo   Le bot n a pas demarre. Verifiez que Python est installe,
  echo   puis lancez : pip install -r requirements.txt
  echo.
  pause
)
