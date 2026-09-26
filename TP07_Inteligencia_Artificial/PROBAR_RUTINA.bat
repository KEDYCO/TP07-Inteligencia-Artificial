@echo off
REM Prueba la funcionalidad agregada: ordenes compuestas (rutina de visita).
REM Abri antes INICIAR_SIMULADOR (elegi 1 = G1). Sin simulador: agrega --sin-robot
cd /d "%~dp0"
py -3 mi_desarrollo\probar_rutina.py %*
echo.
pause
