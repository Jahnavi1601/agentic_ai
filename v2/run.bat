@echo off
python -m venv .venv
call .venv\Scripts\activate.bat
pip install flask flask-cors google-generativeai python-dotenv mysql-connector-python langdetect translate
python app.py