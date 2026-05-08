@echo off
title Fiyat Hafizasi - Haftalik Ozet Karti
cd /d "%~dp0"

echo.
echo  ==============================================
echo   FİYAT HAFIZASI ^| Haftalık Özet (Cumartesi)
echo  ==============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi. Lutfen Python 3.10+ yukleyin.
    echo        https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/2] Bagimliliklar kontrol ediliyor...
python -m pip install -r requirements.txt -q --disable-pip-version-check
if errorlevel 1 (
    echo [HATA] Bagimliliklar yuklenemedi.
    pause
    exit /b 1
)

echo [2/2] Kart olusturuluyor...
echo.
python run_weekly.py
if errorlevel 1 (
    echo.
    echo [HATA] Kart olusturulurken hata olustu. Yukaridaki mesaji inceleyin.
    pause
    exit /b 1
)

echo.
echo  Kart basariyla olusturuldu: output\live\
echo.
pause
