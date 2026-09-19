@echo off
rem Programme les dernieres publications des trois series Hourdis, refusees le 18-19/09
rem parce qu'elles depassaient la fenetre d'environ 29 jours de Facebook :
rem   reel 18:00 du 18/10, photo 14:00 du 18/10, reels expliques 10:00 du 18/10 et du 19/10.
rem A lancer le dimanche 20/09/2026 APRES 10h00 (la fenetre atteint alors le 19/10).
rem Sans danger si on le relance : ce qui est deja programme n'est jamais renvoye.
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
echo === Reels de 18:00 ===
set HOURDIS_SERIE=serie
python programmer_reels.py --envoyer
echo.
echo === Publications photo de 14:00 ===
set HOURDIS_SERIE=serie14
python programmer_photos.py --envoyer
echo.
echo === Reels expliques de 10:00 ===
set HOURDIS_SERIE=serie_voix
python programmer_reels.py --envoyer
echo.
pause
