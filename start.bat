@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PY=%USERPROFILE%\.venvs\mahni-app\Scripts\python.exe"
if not exist "%PY%" (
  echo Virtual muhit tapilmadi: %PY%
  pause
  exit /b 1
)
echo ilkmusic isleyir: http://localhost:8000
echo Dayandirmaq ucun bu pencereni bagla ve ya Ctrl+C bas.
"%PY%" run.py
pause
