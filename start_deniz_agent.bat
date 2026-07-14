@echo off
cd /d "C:\Users\can.deniz\Desktop\Deniz Agent v0.1\DenizAgent"
call ".venv\Scripts\activate.bat"
start "" pythonw.exe app.py
exit