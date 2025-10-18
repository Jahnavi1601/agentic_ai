import re
from langdetect import detect, detect_langs
from typing import Dict, Any
from translate import Translator

# Map language codes from detectors to codes accepted by the translator lib
_LANG_CODE_NORMALIZE = {
    'zh-cn': 'zh',
    'zh-tw': 'zh',
}

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
            # Special case for Hindi (Devanagari) characters
            if any('\u0900' <= c <= '\u097F' for c in text):
                return 'hi'
            # Heuristics for English: ASCII text with common English words
            stripped = text.strip()
            ascii_only = all(ord(c) < 128 for c in stripped)
            tokens = re.findall(r"[a-zA-Z']+", stripped.lower())
            # Detect romanized Hindi: look for typical tokens
            romanized_hindi_words = {
                'mujhe','nahi','hai','kya','kyun','kyu','tum','aap','mera','meri','mere','dil','bahut','hain','hona','hota','hoti','karte','karti','karna','karu','kripya','dukh','rona','aata','aati','raat','dard','samajh','samjho','kyunki','par','lekin','bahut','zyaada','zindagi','khud','khushi','udaas','udasi','thak','thaka','thaki','preshan','pareshan','madad','kripa','shukriya','maafi','maaf','mujhse','mereko','apna','apni','apne'
            }
            if ascii_only and tokens and any(tok in romanized_hindi_words for tok in tokens):
                return 'hi'
            # Detect romanized Telugu
            romanized_telugu_words = {
                'nenu','naku','naa','meeru','neeku','nee','em','emi','enduku','ela','elaa','baga','bagunnanu','bagunnara','baadha','badha','chala','chaala','nuvvu','manam','mana','idi','inka','evaru','evaro','santosham','santhosham','dukham','dukkam','chinta','anandam','kopam','sahaya','sahayam','madad','cheppandi','cheppara','cheyyali','cheyali','undhi','undi','unna','ledu','lEdu','vunna','unnaanu','undanu','rojulu','manchi','kashtam','kastam','nenuu','naaku','baadhaaga','baadha ga','undi','unnadi'
            }
            if ascii_only and tokens and any(tok in romanized_telugu_words for tok in tokens):
                return 'te'
            english_hint_words = {
                'i','im','i\'m','am','is','are','you','the','and','to','for','with','my','me','today','feel','feeling','sad','hello','hi','help','please','sorry','because','but','so','if'
            }
            if ascii_only:
                if len(stripped) <= 2:
                    return 'en'
                if len(tokens) <= 2:
                    return 'en'
                if any(tok in english_hint_words for tok in tokens):
                    return 'en'

            # Use probabilistic detection; if confidence is low and ASCII, prefer English
            langs = detect_langs(text)
            if not langs:
                return 'en'
            best = max(langs, key=lambda l: getattr(l, 'prob', 0.0))
            # If best guess isn't English but confidence is low for ASCII text, default to English
            if ascii_only and getattr(best, 'prob', 0.0) < 0.85 and best.lang != 'en':
                return 'en'
            return best.lang
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
            src = _LANG_CODE_NORMALIZE.get(source_lang.lower(), source_lang)
            safe_text = text[:490]  # MyMemory free API limit ~500 chars
            # If text is ASCII but classified as Hindi, let the service auto-detect
            ascii_only = all(ord(c) < 128 for c in safe_text)
            from_lang = 'auto' if (src in ('hi','te') and ascii_only) else src
            translator = Translator(from_lang=from_lang, to_lang='en')
            translated = translator.translate(safe_text)
            # Guard against MyMemory error strings
            if isinstance(translated, str) and 'QUERY LENGTH LIMIT' in translated.upper():
                print('Translation service reported length limit; returning original text')
                return text
            return translated
        except Exception as e:
            print(f"Translation error: {str(e)}")
            return text  # Return original text if translation fails
    
    def translate_from_english(self, text: str, dest_lang: str) -> str:
        """Translate English text to the target language."""
        if dest_lang == 'en':
            return text
        try:
            dst = _LANG_CODE_NORMALIZE.get(dest_lang.lower(), dest_lang)
            safe_text = text[:490]
            translator = Translator(from_lang='en', to_lang=dst)
            translated = translator.translate(safe_text)
            if isinstance(translated, str) and 'QUERY LENGTH LIMIT' in translated.upper():
                print('Translation service reported length limit; returning original text')
                return text
            return translated
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