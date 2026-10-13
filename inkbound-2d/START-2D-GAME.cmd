@echo off
setlocal
cd /d "%~dp0"
where node >nul 2>nul
if errorlevel 1 (
  for /d %%D in ("%USERPROFILE%\Desktop\node-v*-win-x64") do set "PATH=%%~D;%PATH%"
)
where node >nul 2>nul
if errorlevel 1 (
  echo Node.js was not found. Install Node LTS or put your portable Node folder on the Desktop.
  pause
  exit /b 1
)
if exist "dist\index.html" (
  node tools\serve.cjs
  pause
  exit /b
)
where npm >nul 2>nul
if errorlevel 1 (
  echo Node and npm were not found. Put your portable Node folder on the Desktop or install Node LTS.
  pause
  exit /b 1
)
if not exist node_modules (
  call npm ci
  if errorlevel 1 goto failure
)
node -e "require('esbuild').transformSync('let ready = true')" >nul 2>nul
if errorlevel 1 (
  call npm install-scripts approve esbuild >nul 2>nul
  call npm rebuild esbuild
  if errorlevel 1 goto failure
)
start "" http://localhost:5180
call npm run dev
pause
exit /b
:failure
echo Setup failed. Leave this window open and copy the error above.
pause
exit /b 1
