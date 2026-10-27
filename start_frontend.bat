@echo off
echo Starting AICTE Dashboard Frontend...
echo.

cd /d "%~dp0frontend"

echo Installing dependencies (if needed)...
call npm install

echo.
echo Starting Vite dev server on http://localhost:5173
npm run dev
