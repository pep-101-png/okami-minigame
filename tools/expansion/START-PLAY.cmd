@echo off
setlocal
cd /d "%~dp0"
where node.exe >nul 2>nul
if errorlevel 1 (
  for /d %%D in ("%USERPROFILE%\Desktop\node-v*-win-x64") do (
    if exist "%%~fD\node.exe" set "PATH=%%~fD;%PATH%"
  )
)
where node.exe >nul 2>nul
if errorlevel 1 (
  echo Node.js was not found. Install Node.js LTS, or put your portable Node folder on the Desktop.
  pause
  exit /b 1
)
echo Starting Sunward. No npm install or script approval is needed for this play build.
node server.mjs
pause
