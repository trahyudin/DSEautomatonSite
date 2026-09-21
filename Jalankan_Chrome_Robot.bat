@echo off
echo ===================================================
echo     MEMBUKA CHROME (PROFILE 1) UNTUK ROBOT
echo ===================================================
echo.
echo Pastikan semua jendela Chrome yang menggunakan Profile 1 
echo sudah ditutup sebelum menjalankan ini.
echo.

set "CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME_PATH%" (
    set "CHROME_PATH=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
)

if not exist "%CHROME_PATH%" (
    echo [ERROR] Google Chrome tidak ditemukan!
    pause
    exit /b
)

echo Membuka Chrome di Port 9222...
start "" "%CHROME_PATH%" --remote-debugging-port=9222 --user-data-dir="%LOCALAPPDATA%\Google\Chrome\User Data" --profile-directory="Profile 14" --no-first-run --no-default-browser-check

echo.
echo Selesai! Chrome sekarang siap dihubungkan oleh Robot Playwright.
echo Anda boleh membiarkan jendela Chrome ini terbuka saat robot bekerja.
echo.
pause
