@echo off
title NEXUS Dev Workspace
echo ====================================================
echo   Starting NEXUS in Full Development Mode
echo   (Vite Hot-Reload + Electron Desktop Shell)
echo ====================================================
echo.

:: Clear IDE node worker environment override if present
set ELECTRON_RUN_AS_NODE=
set NODE_ENV=development

echo [1/2] Launching Vite Frontend Dev Server...
start "NEXUS Vite Dev Server" cmd /k "cd /d \"%~dp0frontend\" && npm run dev"

echo [2/2] Launching Electron Desktop Shell...
cd /d "%~dp0desktop"
npm start
