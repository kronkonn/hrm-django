@echo off
echo ============================================
echo   HRM System - Frontend (Vue.js)
echo ============================================

cd /d "%~dp0frontend"

echo Installing npm packages...
npm install

echo.
echo Frontend running at http://localhost:5173
echo.
npm run dev
