@echo off
chcp 65001 >nul
echo Остановка старых процессов Python...
taskkill /f /im python.exe >nul 2>&1
echo ====================================================
echo   Запуск AURA Voice Injector (Нано-кнопка 12px)
echo   Зажми СКРОЛЛ (колесико мыши) для диктовки
echo ====================================================
python "%~dp0app.py"
pause
