from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai
import os
from dotenv import load_dotenv
from datetime import datetime
from mysql_manager import MySQLManager
from language_handler import LanguageHandler

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
db = MySQLManager()
lang_handler = LanguageHandler()

# Initialize Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-pro')
conversation_history = {}  # Use a dict to track conversations per user

# Serve static files
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/')
def home():
    return render_template('index.html', resources=db.get_resources())

@app.route('/chat', methods=['POST'])
def chat():
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
            
        user_message = request.json.get('message', '')
        if not user_message and request.json.get('intent', '') not in ['check_availability', 'book_appointment']:
            return jsonify({'error': 'Message is required'}), 400
            
        intent = request.json.get('intent', '')
        user_id = request.json.get('user_id', 'default')
        
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
        
        # Check for emergency keywords in both original message and English translation
        emergency_keywords = [
            # English
            'suicide', 'kill myself', 'want to die', 'end my life',
            # Telugu
            'ఆత్మహత్య', 'చనిపోవాలనుకుంటున్నాను', 'చావాలనుకుంటున్నాను', 'బ్రతకాలనిపించడంలేదు', 
            'నేను చనిపోతాను', 'నేను చనిపోతాన్ను', 'నేను సచ్చిపోతున్నాను', 'ప్రాణం తీసుకుంటా', 
            'నాకు బ్రతకాలనిపించడంలేదు', 'నేను చావాలనుకుంటున్నాను', 'సచ్చిపోతా', 'చచ్చిపోతా', 
            'చావాలని ఉంది', 'చావాలి', 'బతకలేను', 'బతకాలనిపించడంలేదు'
        ]
        
        is_emergency = any(keyword.lower() in user_message.lower() or 
                         keyword.lower() in english_message.lower() 
                         for keyword in emergency_keywords)
        
        if is_emergency:
            emergency_response = lang_handler.get_default_response('emergency', detected_lang)
            return jsonify({'response': emergency_response, 'is_emergency': True})
        
        # Add message to conversation history
        conversation_history[user_id].append(english_message)
        
        # Format conversation history for context
        context = "\n".join([f"{'User' if i%2==0 else 'Assistant'}: {msg}" 
                           for i, msg in enumerate(conversation_history[user_id][-6:])])
        
        # Get response from Gemini
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

Available counselors and their specialties:
{str(db.get_counselors())}

User message: {english_message}

Respond with empathy and care."""

            response = model.generate_content(prompt).text.strip()
            conversation_history[user_id].append(response)
            
            # Translate response back to user's language if not English
            if detected_lang != 'en':
                try:
                    response = lang_handler.translate_from_english(response, detected_lang)
                except Exception as e:
                    print(f"Translation error: {str(e)}")
                    # If translation fails, return the English response
                    pass
            
            return jsonify({
                'response': response,
                'language_info': lang_info,
                'is_emergency': False
            })
            
        except Exception as e:
            print(f"Gemini API error: {str(e)}")
            return jsonify({'error': 'Could not generate response. Please try again.'}), 500
            
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/counselors', methods=['GET'])
def get_counselors():
    return jsonify(db.get_counselors())

if __name__ == '__main__':
    app.run(debug=True)