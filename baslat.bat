@echo off
chcp 65001 > nul
title Toplu Barkod - 10x10cm Termal Etiket Sistemi
echo ===================================================================
echo     TOPLU BARKOD ^| 10x10cm TERMAL ETIKET BASKI SISTEMI
echo ===================================================================
echo.
echo Program baslatiliyor, lutfen bekleyin...
echo Tarayiciniz otomatik olarak acilacaktir: http://127.0.0.1:5005
echo.

echo Port 5005 kontrol ediliyor...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5005 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1

cd /d "C:\Users\ugurk\OneDrive\Masaüstü\toplu_barkod"
"C:\Users\ugurk\AppData\Local\Programs\Python\Python312\python.exe" app.py

pause
