from langdetect import detect
from typing import Dict, Any
from translate import Translator

class LanguageHandler:
    def __init__(self):
        self.supported_languages = {
            'en': 'English',
            'es': 'Spanish',
            'hi': 'Hindi',
            'te': 'Telugu',
            'ta': 'Tamil',
            'ml': 'Malayalam',
            'kn': 'Kannada',
            'fr': 'French',
            'de': 'German',
            'zh-cn': 'Chinese (Simplified)',
            'ja': 'Japanese',
            'ko': 'Korean',
            'ar': 'Arabic'
        }
        
        # Default responses in different languages
        self.default_responses = {
            'en': {
                'emergency': "If you're having thoughts of self-harm or suicide, please immediately contact emergency services at 911 or the crisis hotline at 1-800-273-8255. You're not alone, and help is available.",
                'welcome': "I'm here to help. How are you feeling today?",
                'appointment': "Would you like to schedule an appointment with a counselor?",
            },
            'te': {
                'emergency': """మీ భావనలు చాలా ముఖ్యమైనవి. మీరు ఒంటరిగా లేరు. వెంటనే సహాయం అందుబాటులో ఉంది:

1. తక్షణ సహాయానికి: 100 (పోలీస్) లేదా 108 (అత్యవసర సేవలు)
2. AASRA సూసైడ్ ప్రివెన్షన్: 91-9820466726 (24x7)
3. రోజు 24 గంటలు అందుబాటులో ఉన్న సహాయ వాణి: 91-40-66202000

దయచేసి వెంటనే సహాయం తీసుకోండి. మీ జీవితం చాలా విలువైనది. మేము మీకు సహాయం చేయగలము.""",
                'welcome': "నేను మీకు సహాయం చేయడానికి ఇక్కడ ఉన్నాను. మీరు ఎలా ఫీల్ అవుతున్నారు?",
                'appointment': "కౌన్సెలర్‌తో అపాయింట్‌మెంట్ షెడ్యూల్ చేయాలనుకుంటున్నారా?",
            },
            'hi': {
                'emergency': "यदि आपके मन में आत्मघाती विचार आ रहे हैं, तो कृपया तुरंत 911 या क्राइसिस हॉटलाइन 1-800-273-8255 पर संपर्क करें। आप अकेले नहीं हैं, मदद उपलब्ध है।",
                'welcome': "मैं आपकी मदद करने के लिए यहां हूं। आप कैसा महसूस कर रहे हैं?",
                'appointment': "क्या आप काउंसलर के साथ अपॉइंटमेंट शेड्यूल करना चाहेंगे?",
            }
        }
    
    def detect_language(self, text: str) -> str:
        """Detect the language of the input text."""
        try:
            # Special case for Telugu characters
            if any('\u0C00' <= c <= '\u0C7F' for c in text):
                return 'te'
            return detect(text)
        except Exception as e:
            print(f"Language detection error: {str(e)}")
            return 'en'  # Default to English if detection fails
    
    def translate_to_english(self, text: str, source_lang: str = None) -> str:
        """Translate the input text to English."""
        if source_lang is None:
            source_lang = self.detect_language(text)
        if source_lang == 'en':
            return text
        try:
            translator = Translator(from_lang=source_lang, to_lang='en')
            return translator.translate(text)
        except Exception as e:
            print(f"Translation error: {str(e)}")
            return text  # Return original text if translation fails
    
    def translate_from_english(self, text: str, dest_lang: str) -> str:
        """Translate English text to the target language."""
        if dest_lang == 'en':
            return text
        try:
            translator = Translator(from_lang='en', to_lang=dest_lang)
            return translator.translate(text)
        except Exception as e:
            print(f"Translation error: {str(e)}")
            return text  # Return original text if translation fails
    
    def get_default_response(self, key: str, lang: str) -> str:
        """Get a default response in the specified language."""
        if lang in self.default_responses and key in self.default_responses[lang]:
            return self.default_responses[lang][key]
        elif 'en' in self.default_responses and key in self.default_responses['en']:
            # Translate from English if the language is not available
            return self.translate_from_english(self.default_responses['en'][key], lang)
        return ""
    
    def process_message(self, message: str) -> Dict[str, Any]:
        """Process a user message and return language information and translations."""
        detected_lang = self.detect_language(message)
        english_text = self.translate_to_english(message, detected_lang)
        
        return {
            'original_text': message,
            'detected_language': detected_lang,
            'english_translation': english_text,
            'language_name': self.supported_languages.get(detected_lang, 'Unknown')
        }