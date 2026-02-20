@echo off
title Starter TruCar - Vemag
echo Iniciando o ecossistema TruCar...

:: --- FRONTEND ---
echo Iniciando Frontend Quasar...
start "Frontend - Quasar" cmd /k "cd /d C:\Users\vitor.lemes\Downloads\TruCar\src-client && quasar dev"

:: --- BACKEND ---
echo Iniciando Backend FastAPI...
start "Backend - FastAPI" cmd /k "cd /d C:\Users\vitor.lemes\Downloads\TruCar\src-py && .\venv\scripts\activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo Tudo pronto! As janelas estao rodando os processos.
pause