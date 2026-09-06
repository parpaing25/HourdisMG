@echo off
rem Lanceur pour le Planificateur de tâches Windows (tous les jours 07:30).
rem Créer la tâche : Planificateur → Créer une tâche de base → « Hourdis - verification en ligne »
rem → Quotidien 07:30 → Démarrer un programme → ce fichier .cmd
set PYTHONIOENCODING=utf-8
cd /d "%~dp0.."
python outils\verifier_en_ligne.py >> outils\verifier_en_ligne.log 2>&1
