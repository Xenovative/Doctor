@echo off
REM PM2 WhatsApp Server Management Script

if "%1"=="" goto usage

if "%1"=="start" goto start
if "%1"=="stop" goto stop
if "%1"=="restart" goto restart
if "%1"=="status" goto status
if "%1"=="logs" goto logs
if "%1"=="delete" goto delete
goto usage

:start
echo Starting WhatsApp server with PM2...
if not exist "logs" mkdir logs
pm2 start ecosystem.config.js --only whatsapp-server
goto end

:stop
echo Stopping WhatsApp server...
pm2 stop whatsapp-server
goto end

:restart
echo Restarting WhatsApp server...
pm2 restart whatsapp-server
goto end

:status
echo WhatsApp server status:
pm2 status whatsapp-server
goto end

:logs
echo Showing WhatsApp server logs (Ctrl+C to exit):
pm2 logs whatsapp-server
goto end

:delete
echo Deleting WhatsApp server process...
pm2 delete whatsapp-server
goto end

:usage
echo Usage: pm2-whatsapp.bat [command]
echo.
echo Commands:
echo   start    - Start WhatsApp server
echo   stop     - Stop WhatsApp server
echo   restart  - Restart WhatsApp server
echo   status   - Show server status
echo   logs     - Show server logs
echo   delete   - Delete server process
echo.
echo Examples:
echo   pm2-whatsapp.bat start
echo   pm2-whatsapp.bat logs
goto end

:end
