"""
Voice Input/Output Service
Speech-to-Text and Text-to-Speech functionality
Supports multi-language voice recognition and synthesis
"""

from typing import Dict, Optional, BinaryIO
import os
from datetime import datetime
import tempfile

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    print("⚠️  gTTS not available. Install: pip install gtts")
    GTTS_AVAILABLE = False

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    print("⚠️  SpeechRecognition not available. Install: pip install SpeechRecognition")
    SR_AVAILABLE = False


class VoiceService:
    """
    Voice input/output service for legal chatbot
    Handles speech-to-text and text-to-speech
    """
    
    # Voice settings per language
    VOICE_SETTINGS = {
        'en': {'tld': 'com', 'slow': False},
        'hi': {'tld': 'co.in', 'slow': False},
        'ta': {'tld': 'co.in', 'slow': False},
        'te': {'tld': 'co.in', 'slow': False},
        'bn': {'tld': 'co.in', 'slow': False},
        'mr': {'tld': 'co.in', 'slow': False},
        'gu': {'tld': 'co.in', 'slow': False},
        'kn': {'tld': 'co.in', 'slow': False},
        'ml': {'tld': 'co.in', 'slow': False},
        'pa': {'tld': 'co.in', 'slow': False},
        'or': {'tld': 'co.in', 'slow': False},
        'ur': {'tld': 'com.pk', 'slow': False},
    }
    
    def __init__(self):
        """Initialize voice service"""
        self.tts_available = GTTS_AVAILABLE
        self.stt_available = SR_AVAILABLE
        
        if self.stt_available:
            self.recognizer = sr.Recognizer()
            # Configure recognizer
            self.recognizer.energy_threshold = 4000
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
        
        status = []
        if self.tts_available:
            status.append("Text-to-Speech (gTTS)")
        if self.stt_available:
            status.append("Speech-to-Text")
        
        if status:
            print(f"✅ Voice service initialized: {', '.join(status)}")
        else:
            print("⚠️  Voice service not fully available. Install required packages.")
    
    def text_to_speech(self, text: str, lang: str = 'en', slow: bool = False) -> Dict:
        """
        Convert text to speech audio
        
        Args:
            text: Text to convert
            lang: Language code (en, hi, ta, etc.)
            slow: Speak slowly
            
        Returns:
            Dictionary with audio file path and metadata
        """
        if not text or not text.strip():
            return {
                'success': False,
                'error': 'Empty text provided'
            }
        
        if not self.tts_available:
            return {
                'success': False,
                'error': 'Text-to-Speech not available',
                'note': 'Install gTTS: pip install gtts'
            }
        
        try:
            # Get voice settings for language
            settings = self.VOICE_SETTINGS.get(lang, {'tld': 'com', 'slow': False})
            tld = settings['tld']
            is_slow = slow or settings['slow']
            
            # Create speech object
            tts = gTTS(text=text, lang=lang, slow=is_slow, tld=tld)
            
            # Create temporary file
            temp_dir = tempfile.gettempdir()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"tts_{lang}_{timestamp}.mp3"
            filepath = os.path.join(temp_dir, filename)
            
            # Save audio file
            tts.save(filepath)
            
            # Get file size
            file_size = os.path.getsize(filepath)
            
            return {
                'success': True,
                'audio_file': filepath,
                'filename': filename,
                'language': lang,
                'text_length': len(text),
                'file_size': file_size,
                'slow': is_slow,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'text': text,
                'language': lang
            }
    
    def speech_to_text(self, audio_file: str, language: str = 'en-IN') -> Dict:
        """
        Convert speech audio file to text
        
        Args:
            audio_file: Path to audio file (WAV, FLAC, etc.)
            language: Language code (en-IN, hi-IN, ta-IN, etc.)
            
        Returns:
            Dictionary with transcribed text
        """
        if not self.stt_available:
            return {
                'success': False,
                'error': 'Speech-to-Text not available',
                'note': 'Install SpeechRecognition: pip install SpeechRecognition'
            }
        
        if not os.path.exists(audio_file):
            return {
                'success': False,
                'error': f'Audio file not found: {audio_file}'
            }
        
        try:
            # Load audio file
            with sr.AudioFile(audio_file) as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Record audio
                audio_data = self.recognizer.record(source)
            
            # Perform recognition using Google Speech Recognition
            try:
                text = self.recognizer.recognize_google(
                    audio_data,
                    language=language,
                    show_all=False
                )
                
                return {
                    'success': True,
                    'transcribed_text': text,
                    'language': language,
                    'audio_file': audio_file,
                    'confidence': 'high',  # Google doesn't provide confidence in free tier
                    'timestamp': datetime.now().isoformat()
                }
                
            except sr.UnknownValueError:
                return {
                    'success': False,
                    'error': 'Could not understand audio',
                    'audio_file': audio_file
                }
            except sr.RequestError as e:
                return {
                    'success': False,
                    'error': f'Recognition service error: {str(e)}',
                    'audio_file': audio_file
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'audio_file': audio_file
            }
    
    def speech_to_text_from_microphone(self, language: str = 'en-IN', 
                                      timeout: int = 5) -> Dict:
        """
        Convert speech from microphone to text (for testing)
        
        Args:
            language: Language code
            timeout: Recording timeout in seconds
            
        Returns:
            Dictionary with transcribed text
        """
        if not self.stt_available:
            return {
                'success': False,
                'error': 'Speech-to-Text not available'
            }
        
        try:
            with sr.Microphone() as source:
                print("🎤 Listening... Speak now!")
                
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                # Listen for speech
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
                
                print("🔄 Processing speech...")
            
            # Recognize speech
            try:
                text = self.recognizer.recognize_google(audio, language=language)
                
                return {
                    'success': True,
                    'transcribed_text': text,
                    'language': language,
                    'source': 'microphone',
                    'timestamp': datetime.now().isoformat()
                }
                
            except sr.UnknownValueError:
                return {
                    'success': False,
                    'error': 'Could not understand audio'
                }
            except sr.RequestError as e:
                return {
                    'success': False,
                    'error': f'Recognition service error: {str(e)}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_supported_languages_stt(self) -> Dict:
        """
        Get supported languages for speech-to-text
        
        Returns:
            Dictionary with supported languages
        """
        languages = {
            'en-IN': 'English (India)',
            'hi-IN': 'Hindi (India)',
            'ta-IN': 'Tamil (India)',
            'te-IN': 'Telugu (India)',
            'bn-IN': 'Bengali (India)',
            'mr-IN': 'Marathi (India)',
            'gu-IN': 'Gujarati (India)',
            'kn-IN': 'Kannada (India)',
            'ml-IN': 'Malayalam (India)',
            'pa-IN': 'Punjabi (India)',
            'ur-IN': 'Urdu (India)',
        }
        
        return {
            'success': True,
            'languages': languages,
            'total_count': len(languages)
        }
    
    def get_supported_languages_tts(self) -> Dict:
        """
        Get supported languages for text-to-speech
        
        Returns:
            Dictionary with supported languages
        """
        languages = {
            'en': 'English',
            'hi': 'Hindi',
            'ta': 'Tamil',
            'te': 'Telugu',
            'bn': 'Bengali',
            'mr': 'Marathi',
            'gu': 'Gujarati',
            'kn': 'Kannada',
            'ml': 'Malayalam',
            'pa': 'Punjabi',
            'or': 'Odia',
            'ur': 'Urdu',
        }
        
        return {
            'success': True,
            'languages': languages,
            'total_count': len(languages)
        }
    
    def convert_audio_format(self, input_file: str, output_format: str = 'wav') -> Dict:
        """
        Convert audio file to different format
        
        Args:
            input_file: Input audio file path
            output_format: Target format (wav, mp3, flac)
            
        Returns:
            Dictionary with converted file path
        """
        try:
            from pydub import AudioSegment
            
            # Load audio
            audio = AudioSegment.from_file(input_file)
            
            # Create output filename
            output_file = input_file.rsplit('.', 1)[0] + f'.{output_format}'
            
            # Export in new format
            audio.export(output_file, format=output_format)
            
            return {
                'success': True,
                'input_file': input_file,
                'output_file': output_file,
                'format': output_format,
                'file_size': os.path.getsize(output_file)
            }
            
        except ImportError:
            return {
                'success': False,
                'error': 'pydub not available. Install: pip install pydub'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'input_file': input_file
            }


# Global instance
_voice_service = None


def get_voice_service() -> VoiceService:
    """Get or create voice service instance"""
    global _voice_service
    
    if _voice_service is None:
        _voice_service = VoiceService()
    
    return _voice_service


# Quick access functions
def text_to_audio(text: str, lang: str = 'en') -> Dict:
    """Quick text-to-speech conversion"""
    service = get_voice_service()
    return service.text_to_speech(text, lang)


def audio_to_text(audio_file: str, lang: str = 'en-IN') -> Dict:
    """Quick speech-to-text conversion"""
    service = get_voice_service()
    return service.speech_to_text(audio_file, lang)


if __name__ == '__main__':
    # Test the service
    print("=" * 80)
    print("VOICE SERVICE TEST")
    print("=" * 80)
    
    service = VoiceService()
    
    # Test 1: Text-to-Speech (English)
    print("\n1. Text-to-Speech Test (English):")
    text = "The Supreme Court of India is the highest judicial court in India."
    result = service.text_to_speech(text, lang='en')
    if result['success']:
        print(f"   Text: {text}")
        print(f"   Audio file: {result['audio_file']}")
        print(f"   File size: {result['file_size']} bytes")
    else:
        print(f"   Error: {result.get('error', 'Unknown error')}")
    
    # Test 2: Text-to-Speech (Hindi)
    print("\n2. Text-to-Speech Test (Hindi):")
    hindi_text = "भारत का सर्वोच्च न्यायालय भारत में सर्वोच्च न्यायिक न्यायालय है।"
    result = service.text_to_speech(hindi_text, lang='hi')
    if result['success']:
        print(f"   Text: {hindi_text}")
        print(f"   Audio file: {result['audio_file']}")
        print(f"   File size: {result['file_size']} bytes")
    else:
        print(f"   Error: {result.get('error', 'Unknown error')}")
    
    # Test 3: Supported Languages
    print("\n3. Supported Languages:")
    
    print("\n   Speech-to-Text:")
    stt_langs = service.get_supported_languages_stt()
    for code, name in list(stt_langs['languages'].items())[:5]:
        print(f"   - {code}: {name}")
    print(f"   ... and {stt_langs['total_count'] - 5} more")
    
    print("\n   Text-to-Speech:")
    tts_langs = service.get_supported_languages_tts()
    for code, name in list(tts_langs['languages'].items())[:5]:
        print(f"   - {code}: {name}")
    print(f"   ... and {tts_langs['total_count'] - 5} more")
    
    print("\n" + "=" * 80)
    print("Note: Speech-to-Text requires audio files or microphone access")
    print("=" * 80)
