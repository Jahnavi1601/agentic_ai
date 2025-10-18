from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai
import os
from dotenv import load_dotenv
from datetime import datetime
from database import DatabaseManager
from language_handler import LanguageHandler

# Load environment variables
load_dotenv()

# Configure Google Gemini API
# Support either GEMINI_API_KEY or GOOGLE_API_KEY from .env/environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    # Log a clear message; the server can still start for non-AI flows
    print("[WARN] GEMINI_API_KEY/GOOGLE_API_KEY not set. AI responses will use a basic fallback until configured in .env")
else:
    print("[INFO] Configuring Gemini with API key...")
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print("[INFO] Gemini configuration successful")
    except Exception as e:
        print(f"[ERROR] Failed to configure Gemini: {str(e)}")

# Use a current model name; adjust if you have access to a different tier
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
try:
    model = genai.GenerativeModel(MODEL_NAME)
    print(f"[INFO] Successfully initialized Gemini model: {MODEL_NAME}")
except Exception as e:
    print(f"[ERROR] Failed to initialize Gemini model: {str(e)}")
    model = None