@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
color 0F
title AutoRepCuentas - Generador de Reportes Marketing

REM ============================================================================
REM CONFIGURACIÓN DEL PROYECTO DJANGO
REM ============================================================================
REM Obtener ruta del directorio del backend (3 niveles arriba)
set "BACKEND_DIR=%~dp0..\..\..\"
cd /d "%BACKEND_DIR%"

REM Crear carpeta de LOGS si no existe
if not exist "LOGS" mkdir "LOGS"

REM Crear archivo de log con timestamp
set "LOG_FILE=LOGS\autorepcuentas_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log"
set "LOG_FILE=%LOG_FILE: =0%"

echo [%date% %time%] AutoRepCuentas INICIADO > "%LOG_FILE%"
echo [%date% %time%] Archivo de log: %LOG_FILE% >> "%LOG_FILE%"

REM ============================================================================
REM VERIFICAR PYTHON Y DJANGO
REM ============================================================================
echo 🔍 Verificando instalación de Python...
echo [%date% %time%] Verificando instalación de Python... >> "%LOG_FILE%"
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ❌ ERROR: Python no está instalado o no está en el PATH
    echo [%date% %time%] ERROR: Python no encontrado >> "%LOG_FILE%"
    echo 📋 Por favor instala Python 3.8 o superior
    echo.
    pause
    exit /b 1
) else (
    echo ✅ Python encontrado correctamente
    echo [%date% %time%] Python encontrado correctamente >> "%LOG_FILE%"
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do (
        echo    Versión: %%i
        echo [%date% %time%] Versión Python: %%i >> "%LOG_FILE%"
    )
    echo.
)

:menu_principal
cls
echo.
echo ████████████████████████████████████████████████████████████████████
echo ██                                                              ██
echo ██          AutoRepCuentas - GENERADOR DE REPORTES EXCEL       ██
echo ██         Sistema de Reportes desde Supabase (Django)        ██
echo ██                                                              ██
echo ████████████████████████████████████████████████████████████████████
echo.
echo 📊 GENERADOR DE REPORTES EXCEL PARA EQUIPO DE MARKETING
echo.
echo ✅ Genera reportes desde datos almacenados en Supabase
echo ✅ Sin llamadas API - Datos en tiempo real desde BD
echo ✅ Filtros por cuenta y fecha personalizable
echo ✅ Reportes en formato Excel listos para análisis
echo.
echo ████████████████████████████████████████████████████████████████████
echo.
echo 📋 OPCIONES DE REPORTES:
echo.
echo    [1] 📋 Generar reporte por cuenta (Fecha personalizable)
echo        Tipos: Campaigns, Adsets, Ads o Consolidado
echo.
echo    [2] 📋 Generar reporte por cuenta (Últimos 30 días)
echo        Tipos: Campaigns, Adsets, Ads o Consolidado
echo.
echo    [0] ❌ Salir
echo.
echo ████████████████████████████████████████████████████████████████████
echo.
set /p opcion="👉 Selecciona una opción: "

if "%opcion%"=="1" (
    echo [%date% %time%] Usuario seleccionó reporte con fecha personalizable >> "%LOG_FILE%"
    goto seleccionar_tipo_reporte_fecha
)
if "%opcion%"=="2" (
    echo [%date% %time%] Usuario seleccionó reporte últimos 30 días >> "%LOG_FILE%"
    goto seleccionar_tipo_reporte_ultimos30
)
if "%opcion%"=="0" (
    echo [%date% %time%] Usuario salió del programa >> "%LOG_FILE%"
    exit
)

echo ❌ Opción inválida
pause
goto menu_principal

:seleccionar_tipo_reporte_fecha
cls
echo.
echo ████████████████████████████████████████████████████████████████████
echo ██                                                              ██
echo ██                    SELECCIONAR TIPO DE REPORTE              ██
echo ██                                                              ██
echo ████████████████████████████████████████████████████████████████████
echo.
echo 📊 TIPOS DE REPORTE DISPONIBLES:
echo.
echo    [1] 📈 Campaigns (Campañas)
echo    [2] 📊 Adsets (Conjuntos de anuncios)
echo    [3] 📢 Ads (Anuncios)
echo    [4] 📋 Consolidado (Campaigns + Adsets + Ads)
echo.
echo    [0] 🔙 Volver al menú principal
echo.
echo ████████████████████████████████████████████████████████████████████
echo.
set /p tipo_opcion="👉 Selecciona el tipo de reporte: "

if "%tipo_opcion%"=="1" set "tipo_reporte=campaigns" & goto seleccionar_cuenta_fecha
if "%tipo_opcion%"=="2" set "tipo_reporte=adsets" & goto seleccionar_cuenta_fecha
if "%tipo_opcion%"=="3" set "tipo_reporte=ads" & goto seleccionar_cuenta_fecha
if "%tipo_opcion%"=="4" set "tipo_reporte=consolidado" & goto seleccionar_cuenta_fecha
if "%tipo_opcion%"=="0" goto menu_principal

echo ❌ Opción inválida
pause
goto seleccionar_tipo_reporte_fecha

:seleccionar_tipo_reporte_ultimos30
cls
echo.
echo ████████████████████████████████████████████████████████████████████
echo ██                                                              ██
echo ██                    SELECCIONAR TIPO DE REPORTE              ██
echo ██                                                              ██
echo ████████████████████████████████████████████████████████████████████
echo.
echo 📊 TIPOS DE REPORTE DISPONIBLES:
echo.
echo    [1] 📈 Campaigns (Campañas)
echo    [2] 📊 Adsets (Conjuntos de anuncios)
echo    [3] 📢 Ads (Anuncios)
echo    [4] 📋 Consolidado (Campaigns + Adsets + Ads)
echo.
echo    [0] 🔙 Volver al menú principal
echo.
echo ████████████████████████████████████████████████████████████████████
echo.
set /p tipo_opcion="👉 Selecciona el tipo de reporte: "

if "%tipo_opcion%"=="1" set "tipo_reporte=campaigns" & goto seleccionar_cuenta_ultimos30
if "%tipo_opcion%"=="2" set "tipo_reporte=adsets" & goto seleccionar_cuenta_ultimos30
if "%tipo_opcion%"=="3" set "tipo_reporte=ads" & goto seleccionar_cuenta_ultimos30
if "%tipo_opcion%"=="4" set "tipo_reporte=consolidado" & goto seleccionar_cuenta_ultimos30
if "%tipo_opcion%"=="0" goto menu_principal

echo ❌ Opción inválida
pause
goto seleccionar_tipo_reporte_ultimos30

:seleccionar_cuenta_fecha
cls
echo.
echo ████████████████████████████████████████████████████████████████████
echo ██                                                              ██
echo ██                    SELECCIONAR CUENTA                       ██
echo ██                                                              ██
echo ████████████████████████████████████████████████████████████████████
echo.
echo 📋 CUENTAS DISPONIBLES:
echo.

REM Obtener información de cuentas usando Django management command
for /f "tokens=1,2,3,4,5 delims=|" %%a in ('python manage.py listar_cuentas --formato info 2^>nul') do (
    echo    [%%a] %%b - %%d
    if "%%e"=="Si" echo        (Multimarca)
)

echo.
echo ████████████████████████████████████████████████████████████████████
echo.

set /p cuenta_sel="👉 Selecciona el número de cuenta: "

REM Obtener account_id de la cuenta seleccionada usando el comando especializado
for /f %%a in ('python manage.py listar_cuentas --formato account_id --numero %cuenta_sel% 2^>nul') do (
    set "account_id=%%a"
)

REM Obtener nombre de cuenta para mostrar
set "cuenta_encontrada=false"
for /f "tokens=1,2,3,4,5 delims=|" %%a in ('python manage.py listar_cuentas --formato info 2^>nul') do (
    if "%%a"=="%cuenta_sel%" (
        set "nombre_cuenta=%%b"
        set "cuenta_encontrada=true"
        goto solicitar_fecha_reporte
    )
)

if "!cuenta_encontrada!"=="false" (
    echo ❌ Selección inválida
    pause
    goto seleccionar_tipo_reporte_fecha
)

:solicitar_fecha_reporte
cls
echo.
echo ████████████████████████████████████████████████████████████████████
echo ██                                                              ██
echo ██                  CONFIGURAR FECHAS PARA REPORTE             ██
echo ██                                                              ██
echo ████████████████████████████████████████████████████████████████████
echo.
echo 📊 Cuenta seleccionada: !nombre_cuenta!
echo 📈 Tipo de reporte: !tipo_reporte!
echo.
echo 📅 CONFIGURACIÓN DE RANGO DE FECHAS:
echo.
echo ⚠️  FORMATO REQUERIDO: YYYY-MM-DD
echo 💡 Ejemplos válidos: 2025-01-01, 2025-08-20, 2025-12-31
echo.

:pedir_fecha_inicio
set /p fecha_inicio="👉 Fecha de INICIO (YYYY-MM-DD): "

if "!fecha_inicio!" == "" (
    echo ❌ Fecha vacía. Use: YYYY-MM-DD
    echo.
    goto pedir_fecha_inicio
)

:pedir_fecha_fin
set /p fecha_fin="👉 Fecha de FIN (YYYY-MM-DD): "

if "!fecha_fin!" == "" (
    echo ❌ Fecha vacía. Use: YYYY-MM-DD
    echo.
    goto pedir_fecha_fin
)

echo.
echo ✅ Rango de fechas configurado:
echo    📅 Desde: !fecha_inicio!
echo    📅 Hasta: !fecha_fin!
echo    📊 Tipo: !tipo_reporte!
echo    🏢 Cuenta: !nombre_cuenta!
echo.
set /p confirmar="¿Confirmas este rango de fechas? (S/N): "
if /i not "!confirmar!"=="S" goto solicitar_fecha_reporte

goto generar_reporte_con_fechas

:seleccionar_cuenta_ultimos30
cls
echo.
echo ████████████████████████████████████████████████████████████████████
echo ██                                                              ██
echo ██                    SELECCIONAR CUENTA                       ██
echo ██                                                              ██
echo ████████████████████████████████████████████████████████████████████
echo.
echo 📋 CUENTAS DISPONIBLES:
echo.

REM Obtener información de cuentas usando Django management command
for /f "tokens=1,2,3,4,5 delims=|" %%a in ('python manage.py listar_cuentas --formato info 2^>nul') do (
    echo    [%%a] %%b - %%d
    if "%%e"=="Si" echo        (Multimarca)
)

echo.
echo ████████████████████████████████████████████████████████████████████
echo.

set /p cuenta_sel="👉 Selecciona el número de cuenta: "

REM Obtener account_id de la cuenta seleccionada
for /f %%a in ('python manage.py listar_cuentas --formato account_id --numero %cuenta_sel% 2^>nul') do (
    set "account_id=%%a"
)

REM Obtener nombre de cuenta para mostrar
set "cuenta_encontrada=false"
for /f "tokens=1,2,3,4,5 delims=|" %%a in ('python manage.py listar_cuentas --formato info 2^>nul') do (
    if "%%a"=="%cuenta_sel%" (
        set "nombre_cuenta=%%b"
        set "cuenta_encontrada=true"
        goto generar_reporte_ultimos30
    )
)

if "!cuenta_encontrada!"=="false" (
    echo ❌ Selección inválida
    pause
    goto seleccionar_tipo_reporte_ultimos30
)

:generar_reporte_con_fechas
cls
echo.
echo ████████████████████████████████████████████████████████████████████
echo ██                                                              ██
echo ██      GENERANDO REPORTE: !tipo_reporte!                      ██
echo ██                                                              ██
echo ████████████████████████████████████████████████████████████████████
echo.
echo 📊 Generando reporte Excel desde Supabase
echo 🏢 Cuenta: !nombre_cuenta!
echo 📅 Desde: !fecha_inicio!
echo 📅 Hasta: !fecha_fin!
echo 📈 Tipo: !tipo_reporte!
echo.
echo ====================================================================
echo                    LOG DE GENERACIÓN EN TIEMPO REAL
echo ====================================================================
echo.

echo [%date% %time%] Generando reporte !tipo_reporte! - !fecha_inicio! a !fecha_fin! >> "%LOG_FILE%"

REM Generar reporte usando el account_id obtenido
python manage.py generar_reporte --tipo !tipo_reporte! --account_id "!account_id!" --fecha_inicio !fecha_inicio! --fecha_fin !fecha_fin!

if %errorlevel% neq 0 (
    echo.
    echo ❌ ERROR: La generación de reporte falló (Código de error: %errorlevel%)
    echo [%date% %time%] ERROR: Reporte falló con código %errorlevel% >> "%LOG_FILE%"
    echo.
    pause
    goto menu_principal
) else (
    echo.
    echo ====================================================================
    echo                    REPORTE GENERADO EXITOSAMENTE
    echo ====================================================================
    echo.
    echo ✅ Reporte Excel generado exitosamente: !nombre_cuenta!
    echo [%date% %time%] Reporte generado exitosamente >> "%LOG_FILE%"
    echo.
    echo 📁 Archivo Excel guardado en carpeta REPORTES_EXCEL
    echo 📊 Tipo: !tipo_reporte!
    echo 📅 Período: !fecha_inicio! a !fecha_fin!
    echo 🎯 Listo para análisis
    echo.
    pause
    goto menu_principal
)

:generar_reporte_ultimos30
cls
echo.
echo ████████████████████████████████████████████████████████████████████
echo ██                                                              ██
echo ██      GENERANDO REPORTE: !tipo_reporte!                      ██
echo ██                                                              ██
echo ████████████████████████████████████████████████████████████████████
echo.
echo 📊 Generando reporte Excel desde Supabase
echo 🏢 Cuenta: !nombre_cuenta!
echo 📅 Período: Últimos 30 días
echo 📈 Tipo: !tipo_reporte!
echo.
echo ====================================================================
echo                    LOG DE GENERACIÓN EN TIEMPO REAL
echo ====================================================================
echo.

echo [%date% %time%] Generando reporte !tipo_reporte! - últimos 30 días >> "%LOG_FILE%"

REM Generar reporte usando el account_id obtenido
python manage.py generar_reporte --tipo !tipo_reporte! --account_id "!account_id!" --ultimos30

if %errorlevel% neq 0 (
    echo.
    echo ❌ ERROR: La generación de reporte falló (Código de error: %errorlevel%)
    echo [%date% %time%] ERROR: Reporte falló con código %errorlevel% >> "%LOG_FILE%"
    echo.
    pause
    goto menu_principal
) else (
    echo.
    echo ====================================================================
    echo                    REPORTE GENERADO EXITOSAMENTE
    echo ====================================================================
    echo.
    echo ✅ Reporte Excel generado exitosamente: !nombre_cuenta!
    echo [%date% %time%] Reporte generado exitosamente >> "%LOG_FILE%"
    echo.
    echo 📁 Archivo Excel guardado en carpeta REPORTES_EXCEL
    echo 📊 Tipo: !tipo_reporte!
    echo 📅 Período: Últimos 30 días
    echo 🎯 Listo para análisis
    echo.
    pause
    goto menu_principal
)
