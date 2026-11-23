@echo off
title NEXUS Desktop Workspace
echo ====================================================
echo   Starting NEXUS Local AI Desktop Workspace...
echo ====================================================
echo.

:: Clear IDE node worker environment override if present
set ELECTRON_RUN_AS_NODE=

cd /d "%~dp0desktop"
npm start
