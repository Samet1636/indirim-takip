@echo off
REM Beslenme plani sunucusunu baslatir (FastAPI, port 8000).
REM Hangi klasorden calistirilirsa calistirilsin once proje klasorune gecer.
REM Telefon ayni Wi-Fi'dan baglanabilsin diye 0.0.0.0 uzerinden dinler.
REM Durdurmak icin: Ctrl+C
cd /d "%~dp0"
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir api --reload-dir beslenme
