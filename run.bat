@echo off
title AICTE Complaint Dashboard

echo.
echo  ==========================================
echo   AICTE Integrated Complaint Dashboard
echo   Starting backend and frontend...
echo  ==========================================
echo.

:: Kill any existing processes on ports 8000 and 5173
for /f "tokens=5" %%i in ('netstat -aon 2^>nul ^| findstr ":8000 "') do (
    taskkill /F /PID %%i >nul 2>&1
)
for /f "tokens=5" %%i in ('netstat -aon 2^>nul ^| findstr ":5173 "') do (
    taskkill /F /PID %%i >nul 2>&1
)

:: Start backend in a new window
echo  [1/2] Starting Backend (FastAPI)...
start "AICTE Backend - port 8000" /min cmd /c "cd /d %~dp0backend && C:\Users\meena\anaconda3\envs\ps2\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

:: Wait for backend to boot
timeout /t 5 /nobreak >nul

:: Start frontend in a new window
echo  [2/2] Starting Frontend (Vite)...
start "AICTE Frontend - port 5173" /min cmd /c "cd /d %~dp0frontend && npm run dev"

:: Wait for frontend to boot
timeout /t 6 /nobreak >nul

:: Verify and open browser
echo.
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel%==0 (
    echo  Backend  : http://localhost:8000    [OK]
) else (
    echo  Backend  : starting...
)

curl -s -o nul -w "%%{http_code}" http://localhost:5173 >nul 2>&1
if %errorlevel%==0 (
    echo  Frontend : http://localhost:5173    [OK]
) else (
    echo  Frontend : starting...
)

echo.
echo  API Docs : http://localhost:8000/api/docs
echo.
echo  Login with: admin@aicte.gov.in / Demo@1234
echo.

:: Open browser
start "" "http://localhost:5173"

echo  Both servers are running in background windows.
echo  Close those windows to stop the servers.
echo.
pause
