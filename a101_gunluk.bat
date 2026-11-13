@echo off
REM A101'i bu bilgisayarda tarar ve sonucu GitHub'a gönderir.
REM Windows Görev Zamanlayıcı ile her sabah otomatik çalıştırılır.
cd /d "%~dp0"
if not exist logs mkdir logs
python run.py --only a101 --no-save --export data/imports/a101.json --upload >> logs\a101.log 2>&1
