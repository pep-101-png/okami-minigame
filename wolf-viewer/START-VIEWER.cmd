@echo off
setlocal
cd /d "%~dp0"

rem Reuse Node if installed, or find the portable Desktop download.
where npm.cmd >nul 2>nul
if errorlevel 1 (
  for /d %%D in ("%USERPROFILE%\Desktop\node-v*-win-x64") do (
    if exist "%%~fD\npm.cmd" set "PATH=%%~fD;%PATH%"
  )
)
where npm.cmd >nul 2>nul
if errorlevel 1 (
  echo Node.js was not found. Install Node.js LTS, then run this file again.
  pause
  exit /b 1
)

if not exist "node_modules\three\package.json" (
  echo Installing the viewer dependencies...
  call npm ci
  if errorlevel 1 (
    echo Installation failed. Keep this window open and copy the error above.
    pause
    exit /b 1
  )
)

rem Some newer npm versions hold esbuild's verified package setup script.
node -e "require('esbuild').transformSync('let ready = true')" >nul 2>nul
if errorlevel 1 (
  call npm install-scripts approve esbuild >nul 2>nul
  call npm rebuild esbuild
  if errorlevel 1 (
    echo The build tool could not finish setup. Copy the error above.
    pause
    exit /b 1
  )
)

echo.
echo Open the Local address printed below in your browser.
echo Keep this window open while viewing. Press Ctrl+C to stop.
echo.
call npm run dev
pause
