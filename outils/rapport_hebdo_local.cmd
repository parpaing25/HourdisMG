@echo off
rem Rapport hebdo du site Hourdis depuis le PC (samedi 07:00, Planificateur de tâches).
rem Remplace le cron cPanel tant qu'il n'est pas posé ; les deux ne doivent PAS tourner ensemble.
set PYTHONIOENCODING=utf-8
cd /d "%~dp0.."
python outils\rapport_hebdo_local.py >> outils\rapport_hebdo_local.log 2>&1
