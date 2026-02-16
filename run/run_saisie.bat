@echo off
title Finance Tracker : Module de saisie
:: Dossier de projet
cd /d "E:\OneDrive\Documents\Programmation\Projets\PFT\scripts"

:: Call le venv
call E:\Venvs\pft_env\Scripts\activate.bat

:: Le 'start /min' lance streamlit en icône dans la barre des tâches
start /min "" streamlit run saisie.py
