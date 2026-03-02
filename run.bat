@echo off
chcp 65001 > nul
title Регистратура поликлиники

echo ===================================================
echo      ЗАПУСК РЕГИСТРАТУРЫ ПОЛИКЛИНИКИ
echo ===================================================
echo.

:: Устанавливаем пути
set PYTHONPATH=%~dp0app
set PATH=%~dp0python\pythoncore-3.14-64;%PATH%

:: Запускаем программу
"%~dp0python\pythoncore-3.14-64\python.exe" "%~dp0app\main.py"

if %errorlevel% neq 0 (
    echo.
    echo ОШИБКА: Программа завершилась с ошибкой %errorlevel%
    echo Нажмите любую клавишу для выхода...
    pause > nul
) else (
    echo.
    echo Программа завершена.
    timeout /t 2 /nobreak > nul
)