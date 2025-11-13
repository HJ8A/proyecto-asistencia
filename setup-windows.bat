@echo off
chcp 65001 >nul
echo ========================================
echo  CONFIGURACIÓN SISTEMA DE ASISTENCIAS
echo ========================================
echo.

echo 1. Verificando instalación de Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker no está instalado o no está ejecutándose.
    echo.
    echo Por favor:
    echo 1. Descarga Docker Desktop desde: https://www.docker.com/products/docker-desktop/
    echo 2. Instálalo y reinicia tu computadora
    echo 3. Abre Docker Desktop y espera a que esté listo
    echo 4. Ejecuta este script nuevamente
    echo.
    pause
    exit /b 1
)

echo ✓ Docker encontrado
echo.

echo 2. Construyendo el sistema de asistencias...
echo Esto puede tomar varios minutos la primera vez...
docker-compose build

if errorlevel 1 (
    echo ERROR: Falló la construcción del sistema.
    echo.
    echo Soluciones:
    echo - Verifica que Docker Desktop esté ejecutándose
    echo - Asegúrate de tener conexión a internet
    echo - Intenta ejecutar como administrador
    echo.
    pause
    exit /b 1
)

echo.
echo ✓ Construcción completada exitosamente!
echo.
echo 3. INSTRUCCIONES:
echo    - Para INICIAR el sistema: Ejecuta 'run-windows.bat'
echo    - Para DETENER el sistema: Presiona Ctrl+C en la ventana
echo    - Para ABRIR la aplicación: Ve a http://localhost:8501
echo.
echo Presiona cualquier tecla para cerrar...
pause >nul