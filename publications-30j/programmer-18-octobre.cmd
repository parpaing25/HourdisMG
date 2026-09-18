@echo off
rem Programme les deux publications du 18/10/2026 (reel 18:00 + photo 14:00) sur la page Hourdis.
rem Facebook refuse toute date a plus de ~29 jours : a lancer le 19/09/2026 APRES 18h00.
rem Sans danger si on le relance : ce qui est deja programme n'est jamais renvoye.
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
echo === Reels de 18:00 ===
python programmer_reels.py --envoyer
echo.
echo === Publications de 14:00 ===
set HOURDIS_SERIE=serie14
python programmer_photos.py --envoyer
echo.
pause
