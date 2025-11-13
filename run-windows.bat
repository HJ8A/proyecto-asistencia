@echo off
chcp 65001 >nul
title Sistema de Asistencias Automáticas - Docker

echo ========================================
echo  SISTEMA DE ASISTENCIAS AUTOMÁTICAS
echo ========================================
echo.
echo Iniciando sistema...
echo.
echo IMPORTANTE:
echo - La aplicación estará en: http://localhost:8501
echo - Para detener: Presiona Ctrl+C
echo - Esta ventana debe mantenerse abierta
echo.
echo [INICIANDO... Esto puede tomar unos segundos]
echo.

timeout /t 3 /nobreak >nul

docker-compose up

echo.
echo Sistema detenido.
echo Presiona cualquier tecla para cerrar...
pause >nul