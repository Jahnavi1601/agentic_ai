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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    print("[WARN] GEMINI_API_KEY/GOOGLE_API_KEY not set")
else:
    genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-1.5-flash"
model = genai.GenerativeModel(MODEL_NAME)

app = Flask(__name__,
            template_folder="templates",
            static_folder="static",
            static_url_path="/static")
CORS(app)

# Define default resources
default_resources = {
    "emergency": {
        "name": "Emergency Services",
        "description": "For immediate emergency assistance",
        "contact": "911"
    },
    "crisis": {
        "name": "Crisis Hotline",
        "description": "24/7 confidential support",
        "contact": "1-800-273-8255"
    },
    "counseling": {
        "name": "University Counseling Center",
        "description": "Professional counseling services for students",
        "contact": "Contact your university\'s counseling center"
    }
}

@app.route("/")
def home():
    return render_template("index.html", resources=default_resources)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")
    try:
        response = model.generate_content(user_message)
        return jsonify({"response": response.text})
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"response": "Could not generate response. Please try again."})

@app.route("/static/<path:path>")
def serve_static(path):
    return send_from_directory("static", path)

if __name__ == "__main__":
    app.run(debug=True)
