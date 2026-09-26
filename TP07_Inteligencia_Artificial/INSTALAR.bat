@echo off
REM ============================================================
REM   TP07 - Inteligencia Artificial - Humanoide Unitree G1
REM   INSTALADOR para una computadora con Windows sin nada instalado.
REM
REM   Deja esta carpeta completa (TP07_Inteligencia_Artificial) donde
REM   quieras y hace doble clic en este archivo. Se puede ejecutar
REM   varias veces: lo que ya esta instalado, lo saltea.
REM
REM   Instala: Python 3.12 (si no hay Python), Visual C++
REM   Redistributable (si falta), MuJoCo y NumPy.
REM ============================================================
setlocal
cd /d "%~dp0"
set "LOG=%~dp0instalacion_log.txt"
echo Instalacion TP07 - %DATE% %TIME% > "%LOG%"

echo ============================================================
echo    TP07 - Humanoide G1 en MuJoCo - Instalador
echo ============================================================
echo.

if not exist "%~dp0entorno\sim" (
  echo [X] Este archivo tiene que estar dentro de la carpeta TP07_Inteligencia_Artificial
  echo     ^(junto a las carpetas "entorno" y "mi_desarrollo"^).
  pause
  exit /b 1
)

REM ------------------------------------------------------------
REM   1. Python
REM ------------------------------------------------------------
echo ---- 1/4  Python ----
call :buscar_python
if defined PYTHON goto :python_ok

echo [..] No hay Python. Instalando Python 3.12 con winget...
where winget >nul 2>&1
if errorlevel 1 goto :sin_winget
winget install --id Python.Python.3.12 -e --silent --accept-source-agreements --accept-package-agreements >> "%LOG%" 2>&1
call :buscar_python
if defined PYTHON goto :python_ok

:sin_winget
echo.
echo [X] No pude instalar Python automaticamente.
echo     1. Bajalo de https://www.python.org/downloads/
echo     2. Durante la instalacion TILDA "Add python.exe to PATH"
echo     3. Volve a ejecutar este archivo.
pause
exit /b 1

:python_ok
"%PYTHON%" %PYARGS% -c "import sys;print('[OK] Python', sys.version.split()[0])"
"%PYTHON%" %PYARGS% -c "import sys;sys.exit(0 if sys.version_info>=(3,10) else 1)"
if errorlevel 1 (
  echo [X] Tu Python es muy viejo. Hace falta 3.10 o mas nuevo: https://www.python.org/downloads/
  pause
  exit /b 1
)

REM ------------------------------------------------------------
REM   2. Visual C++ Redistributable (MuJoCo lo necesita)
REM ------------------------------------------------------------
echo.
echo ---- 2/4  Visual C++ Redistributable ----
set "FALTA_VC="
if not exist "%SystemRoot%\System32\vcruntime140.dll" set "FALTA_VC=1"
if not exist "%SystemRoot%\System32\vcruntime140_1.dll" set "FALTA_VC=1"
if not exist "%SystemRoot%\System32\msvcp140.dll" set "FALTA_VC=1"
if not defined FALTA_VC (
  echo [OK] Ya estaba instalado.
  goto :vc_ok
)
echo [..] Falta. Instalando ^(puede pedir permiso de administrador^)...
where winget >nul 2>&1
if not errorlevel 1 winget install --id Microsoft.VCRedist.2015+.x64 -e --silent --accept-source-agreements --accept-package-agreements >> "%LOG%" 2>&1
if exist "%SystemRoot%\System32\vcruntime140_1.dll" goto :vc_instalado
curl -L -s -o "%TEMP%\vc_redist.x64.exe" https://aka.ms/vs/17/release/vc_redist.x64.exe >> "%LOG%" 2>&1
if exist "%TEMP%\vc_redist.x64.exe" "%TEMP%\vc_redist.x64.exe" /install /quiet /norestart
:vc_instalado
if exist "%SystemRoot%\System32\vcruntime140_1.dll" (echo [OK] Instalado.) else (echo [!!] No se pudo. Si MuJoCo falla, instalalo a mano: https://aka.ms/vs/17/release/vc_redist.x64.exe)
:vc_ok

REM ------------------------------------------------------------
REM   3. MuJoCo y NumPy
REM ------------------------------------------------------------
echo.
echo ---- 3/4  MuJoCo ----
set "PIPFLAGS=--trusted-host pypi.org --trusted-host files.pythonhosted.org"
echo [..] Instalando mujoco y numpy ^(un par de minutos^)...
"%PYTHON%" %PYARGS% -m pip install --upgrade pip %PIPFLAGS% >> "%LOG%" 2>&1
"%PYTHON%" %PYARGS% -m pip install mujoco numpy %PIPFLAGS% >> "%LOG%" 2>&1
"%PYTHON%" %PYARGS% -c "import mujoco; print('[OK] MuJoCo', mujoco.__version__)"
if errorlevel 1 (
  echo [X] MuJoCo no carga. Mira instalacion_log.txt
  echo     Si dice "DLL load failed", instala https://aka.ms/vs/17/release/vc_redist.x64.exe
  echo     cerra esta ventana y volve a ejecutar este archivo.
  pause
  exit /b 1
)

REM ------------------------------------------------------------
REM   4. Prueba del agente sin robot (los 25 casos)
REM ------------------------------------------------------------
echo.
echo ---- 4/4  Prueba del agente ^(sin robot^) ----
"%PYTHON%" %PYARGS% mi_desarrollo\mi_tp07.py --sin-robot

echo.
echo ============================================================
echo    INSTALACION COMPLETA
echo ============================================================
echo    Para usarlo:
echo      1. INICIAR_SIMULADOR.bat   ^(elegi 1 = G1 humanoide^)
echo      2. Con la ventana del robot abierta:
echo           PROBAR_RUTINA.bat       la rutina de visita
echo           EJECUTAR_MI_CODIGO.bat  los 25 casos + ordenes a mano
echo ============================================================
echo.
set "ABRIR=S"
set /p ABRIR="   Abrir el simulador ahora? [S/n]: "
if /i "%ABRIR%"=="n" goto :fin
echo    Se abre otra ventana: elegi 1 ^(G1^) y Enter.
start "" "%~dp0INICIAR_SIMULADOR.bat"
:fin
echo.
pause
endlocal
exit /b 0

REM ------------------------------------------------------------
REM   Busca Python: lanzador py, PATH (sin el atajo de la Store),
REM   y las carpetas donde lo deja el instalador.
REM ------------------------------------------------------------
:buscar_python
set "PYTHON="
set "PYARGS="
py -3 -c "import sys" >nul 2>&1 && set "PYTHON=py"
if defined PYTHON set "PYARGS=-3"
if defined PYTHON goto :eof
for /f "delims=" %%P in ('where python 2^>nul') do call :probar "%%P"
for %%V in (314 313 312 311 310) do call :probar "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
for %%V in (314 313 312 311 310) do call :probar "%ProgramFiles%\Python%%V\python.exe"
goto :eof

:probar
if defined PYTHON goto :eof
if not exist "%~1" goto :eof
echo %~1| find /i "WindowsApps" >nul
if not errorlevel 1 goto :eof
"%~1" -c "import sys" >nul 2>&1 && set "PYTHON=%~1"
goto :eof
