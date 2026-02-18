@echo off
chcp 1251 > nul
title Установка Регистратуры поликлиники
color 0A

echo ==================================================
echo    УСТАНОВЩИК РЕГИСТРАТУРЫ ПОЛИКЛИНИКИ
echo    Для Windows
echo ==================================================
echo.

:: Проверяем наличие Python
echo.
echo 🔍 Проверка Python...

python --version > tmp.txt 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python не найден!
    echo.
    echo Скачайте Python с официального сайта:
    echo https://www.python.org/downloads/
    echo.
    echo При установке ОБЯЗАТЕЛЬНО отметьте:
    echo ✓ Add Python to PATH
    echo.
    pause
    exit
) else (
    set /p python_version=<tmp.txt
    echo ✅ Найден %python_version%
)
del tmp.txt 2>nul

:: Создаем папку для программы в AppData
set APPDATA_DIR=%APPDATA%\Poliklinika
echo.
echo 📁 Создание папки программы: %APPDATA_DIR%
if not exist "%APPDATA_DIR%" mkdir "%APPDATA_DIR%"
if not exist "%APPDATA_DIR%\backups" mkdir "%APPDATA_DIR%\backups"

:: Копируем файлы программы
echo.
echo 📦 Копирование файлов программы...
copy main.py "%APPDATA_DIR%" /Y >nul
copy gui.py "%APPDATA_DIR%" /Y >nul
copy database.py "%APPDATA_DIR%" /Y >nul

:: Если есть готовая база данных, копируем
if exist clinic.db (
    copy clinic.db "%APPDATA_DIR%" /Y >nul
    echo ✅ База данных скопирована
)

:: Создаем файл аудита
if not exist "%APPDATA_DIR%\audit.log" (
    echo # Журнал аудита создан %date% %time% > "%APPDATA_DIR%\audit.log"
)

:: Создаем BAT-файл для запуска
echo.
echo 📝 Создание файла запуска...
echo @echo off > "%APPDATA_DIR%\Запустить_поликлинику.bat"
echo cd /d "%APPDATA_DIR%" >> "%APPDATA_DIR%\Запустить_поликлинику.bat"
echo python main.py >> "%APPDATA_DIR%\Запустить_поликлинику.bat"
echo pause >> "%APPDATA_DIR%\Запустить_поликлинику.bat"

:: Создаем ярлык на рабочем столе
echo.
echo 🔗 Создание ярлыка на рабочем столе...

:: Создаем VBS скрипт для создания ярлыка
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\create_shortcut.vbs"
echo sLinkFile = oWS.ExpandEnvironmentStrings("%USERPROFILE%\Desktop\Поликлиника.lnk") >> "%TEMP%\create_shortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\create_shortcut.vbs"
echo oLink.TargetPath = "%APPDATA_DIR%\Запустить_поликлинику.bat" >> "%TEMP%\create_shortcut.vbs"
echo oLink.WorkingDirectory = "%APPDATA_DIR%" >> "%TEMP%\create_shortcut.vbs"
echo oLink.Description = "Регистратура поликлиники" >> "%TEMP%\create_shortcut.vbs"
echo oLink.Save >> "%TEMP%\create_shortcut.vbs"

cscript //nologo "%TEMP%\create_shortcut.vbs"
del "%TEMP%\create_shortcut.vbs"

:: Создаем инструкцию
echo.
echo 📝 Создание инструкции...

(
echo ================================================
echo    РЕГИСТРАТУРА ПОЛИКЛИНИКИ - ИНСТРУКЦИЯ
echo ================================================
echo.
echo ✅ УСТАНОВКА ЗАВЕРШЕНА!
echo.
echo 🚀 КАК ЗАПУСТИТЬ:
echo.
echo   1. Дважды щёлкните ярлык "Поликлиника" на рабочем столе
echo   2. Или запустите файл: %APPDATA_DIR%\Запустить_поликлинику.bat
echo.
echo 📁 ГДЕ ХРАНЯТСЯ ДАННЫЕ:
echo.
echo   • База данных: %APPDATA_DIR%\clinic.db
echo   • Журнал аудита: %APPDATA_DIR%\audit.log
echo   • Резервные копии: %APPDATA_DIR%\backups\
echo.
echo 🔐 БЕЗОПАСНОСТЬ:
echo.
echo   ✓ Защита от SQL-инъекций
echo   ✓ Валидация всех данных
echo   ✓ Логирование действий
echo   ✓ Автоматические бэкапы
echo.
echo ================================================
) > "%APPDATA_DIR%\ИНСТРУКЦИЯ.txt"

:: Финальное сообщение
echo.
echo ==================================================
echo ✅ УСТАНОВКА УСПЕШНО ЗАВЕРШЕНА!
echo ==================================================
echo.
echo 🚀 Ярлык создан на рабочем столе
echo 📖 Инструкция: %APPDATA_DIR%\ИНСТРУКЦИЯ.txt
echo.
echo Нажмите любую клавишу для выхода...
pause > nul