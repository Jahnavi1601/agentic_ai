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
    genai.configure(api_key=GEMINI_API_KEY)

# Use a current model name; adjust if you have access to a different tier
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
model = genai.GenerativeModel(MODEL_NAME)

app = Flask(__name__,
            template_folder='templates',
            static_folder='static',
            static_url_path='/static')
CORS(app)  # Enable CORS for all routes
db = DatabaseManager()
lang_handler = LanguageHandler()
conversation_history = {}  # Use a dict to track conversations per user


def generate_basic_response(user_text: str) -> str:
    """Heuristic fallback when Gemini isn't configured.
    Keeps tone supportive and under ~150 words.
    """
    text = user_text.lower()
    if any(g in text for g in ["hi", "hello", "hey"]):
        return (
            "Hi, I’m here to listen and help. How are you feeling today? "
            "If you’d like, I can also help you review resources or schedule a counselor appointment."
        )
    if any(w in text for w in ["stress", "anxious", "anxiety", "depress", "sad", "overwhelm"]):
        return (
            "I’m sorry you’re going through this. You’re not alone, and it’s okay to ask for help. "
            "A few quick steps that may help: slow, deep breaths, a short walk, and writing down what feels hardest. "
            "Would you like to see campus resources or check counselor availability?"
        )
    if "appoint" in text or "counsel" in text:
        return (
            "I can help you schedule a counseling appointment. In the sidebar, pick a counselor and date to check available times."
        )
    return (
        "Thanks for sharing. I’m here with you. Can you tell me a bit more about what’s been most challenging lately? "
        "If at any point you’d like resources or to book time with a counselor, I can help."
    )

@app.route('/health')
def health_check():
    return jsonify({'status': 'ok'})

@app.route('/')
def home():
    try:
        resources = db.get_resources()
        return render_template('index.html', resources=resources)
    except Exception as e:
        print(f"Error loading home page: {str(e)}")
        return jsonify({'error': 'Could not load the application. Please try again.'}), 500

@app.route('/chat', methods=['POST'])
def chat():
    print("Received chat request")
    try:
        if not request.is_json:
            print("Request is not JSON")
            return jsonify({'error': 'Request must be JSON'}), 400
            
        print("Request data:", request.json)
        user_message = request.json.get('message', '')
        if not user_message and request.json.get('intent', '') not in ['check_availability', 'book_appointment']:
            print("No message provided")
            return jsonify({'error': 'Message is required'}), 400
            
        intent = request.json.get('intent', '')
        user_id = request.json.get('user_id', 'default')
        print(f"Processing message: '{user_message}' from user: {user_id}")
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    
    # Initialize conversation history for new users
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    
    # Handle scheduling intents
    if intent == 'check_availability':
        counselor = request.json.get('counselor', '')
        date_str = request.json.get('date', '')
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            slots = db.get_available_slots(counselor, date)
            return jsonify({
                'type': 'availability',
                'slots': slots,
                'counselor': counselor
            })
        except ValueError:
            return jsonify({'error': 'Invalid date format'})
            
    elif intent == 'book_appointment':
        counselor = request.json.get('counselor', '')
        slot = request.json.get('slot', '')
        student_id = request.json.get('student_id', 'anonymous')
        success, result = db.book_appointment(counselor, slot, student_id)
        if success:
            return jsonify({
                'type': 'confirmation',
                'appointment': result
            })
        else:
            return jsonify({'error': result})
    
    # Process language
    try:
        lang_info = lang_handler.process_message(user_message)
        detected_lang = lang_info['detected_language']
        english_message = lang_info['english_translation']
        print(f"Detected language: {detected_lang}")
        print(f"English translation: {english_message}")
    except Exception as e:
        print(f"Language processing error: {str(e)}")
        return jsonify({'error': 'Could not process language. Please try again.'}), 500
    
    # Check for emergency keywords in English translation and other languages
    emergency_keywords = [
        # English
        'suicide', 'kill myself', 'want to die', 'end my life',
        # Telugu
        'ఆత్మహత్య', 'చనిపోవాలనుకుంటున్నాను', 'చావాలనుకుంటున్నాను', 'బ్రతకాలనిపించడంలేదు', 
        'నేను చనిపోతాను', 'నేను చనిపోతాన్ను', 'నేను సచ్చిపోతున్నాను', 'ప్రాణం తీసుకుంటా', 
        'నాకు బ్రతకాలనిపించడంలేదు', 'నేను చావాలనుకుంటున్నాను', 'సచ్చిపోతా', 'చచ్చిపోతా', 
        'చావాలని ఉంది', 'చావాలి', 'బతకలేను', 'బతకాలనిపించడంలేదు'
    ]
    is_emergency = any(keyword in english_message.lower() for keyword in emergency_keywords)
    
    if is_emergency:
        emergency_response = lang_handler.get_default_response('emergency', detected_lang)
        return jsonify({'response': emergency_response, 'is_emergency': True})
    
    # Add message to conversation history
    conversation_history[user_id].append(english_message)
    
    # Format conversation history for context
    context = "\n".join([f"{'User' if i%2==0 else 'Assistant'}: {msg}" 
                        for i, msg in enumerate(conversation_history[user_id][-6:])])
    
    # Get response from Gemini or fallback
    try:
        prompt = f"""You are a compassionate AI assistant helping students with mental health concerns.
Remember to:
1. Be supportive and non-judgmental
2. Suggest professional help when appropriate
3. Maintain confidentiality
4. Share relevant resources
5. Help schedule appointments when requested

Previous conversation:
{context}

User's message: {english_message}

Available counselors and their specialties:
{db.get_counselors()}

Important: Always respond in a helpful and empathetic way. Keep responses under 150 words."""

        print(f"Sending prompt to Gemini: {prompt}")
        if not GEMINI_API_KEY:
            assistant_english = generate_basic_response(english_message)
        else:
            response_obj = model.generate_content(prompt)
            if not response_obj:
                print("Gemini API returned empty response")
                return jsonify({'error': 'Could not generate response. Please try again.'}), 500
                
            assistant_text = (response_obj.text or '').strip()
            print(f"Received response from Gemini: {assistant_text}")
            if not assistant_text:
                print("Empty response text from Gemini")
                return jsonify({'error': 'Empty response received. Please try again.'}), 500
                
            assistant_english = assistant_text
    except Exception as e:
        print(f"Gemini API error: {str(e)}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        return jsonify({'error': 'Could not generate response. Please try again.'}), 500
    conversation_history[user_id].append(assistant_english)
    
    # Translate response back to user's language if not English
    final_text = assistant_english
    if detected_lang != 'en':
        final_text = lang_handler.translate_from_english(assistant_english, detected_lang)
    
    return jsonify({
        'response': final_text,
        'language_info': lang_info,
        'is_emergency': False
    })

@app.route('/counselors', methods=['GET'])
def get_counselors():
    return jsonify(db.get_counselors())

if __name__ == '__main__':
    app.run(debug=True)
