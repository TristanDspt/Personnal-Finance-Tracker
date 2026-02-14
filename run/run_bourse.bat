:: Lance le script

@echo off
:: On remonte d'un dossier pour être à la racine du projet
cd /d "%~dp0.."

:: On lance avec ton Venv (Chemin absolu pour ton PC)
"E:\Venvs\pft_env\scripts\python.exe" "scripts\update_price.py"