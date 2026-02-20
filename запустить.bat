@echo off
chcp 1251 > nul
title Поликлиника
echo Запуск программы...
"%~dp0Python\bin\python.exe" "%~dp0main.py"
pause