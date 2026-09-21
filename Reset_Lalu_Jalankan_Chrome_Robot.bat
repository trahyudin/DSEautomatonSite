@echo off
echo ===================================================
echo     JALANKAN CHROME KHUSUS ROBOT (CDP MODE)
echo ===================================================
echo.
echo Catatan: Chrome ini menggunakan Profil khusus Robot (terpisah 
echo dari Chrome utama Anda) sehingga kebal dari pemblokiran keamanan.
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

set "BOT_PROFILE_DIR=%~dp0BotProfile"

echo Membuka Chrome di Port 9222...
start "" "%CHROME_PATH%" --remote-debugging-port=9222 --user-data-dir="%BOT_PROFILE_DIR%" --profile-directory="Default" --no-first-run --no-default-browser-check

echo.
echo Selesai! Chrome khusus Robot sudah terbuka.
echo Jika ini pertama kalinya Anda membukanya, SILAKAN LOGIN ke Pinterest/Website lain
echo di dalam jendela Chrome yang baru terbuka ini.
echo.
echo Setelah login, Robot bisa langsung dijalankan!
echo.
pause
