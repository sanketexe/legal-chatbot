"""
Multi-language Translation Service
Supports 10+ Indian regional languages with bidirectional translation
"""

from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime

try:
    from googletrans import Translator
    GOOGLETRANS_AVAILABLE = True
except ImportError:
    print("⚠️  googletrans not available. Install: pip install googletrans==4.0.0rc1")
    GOOGLETRANS_AVAILABLE = False


class LanguageService:
    """
    Multi-language translation and detection service
    Supports Indian regional languages
    """
    
    # Supported Indian languages
    SUPPORTED_LANGUAGES = {
        'en': {'name': 'English', 'native': 'English', 'rtl': False},
        'hi': {'name': 'Hindi', 'native': 'हिन्दी', 'rtl': False},
        'ta': {'name': 'Tamil', 'native': 'தமிழ்', 'rtl': False},
        'te': {'name': 'Telugu', 'native': 'తెలుగు', 'rtl': False},
        'bn': {'name': 'Bengali', 'native': 'বাংলা', 'rtl': False},
        'mr': {'name': 'Marathi', 'native': 'मराठी', 'rtl': False},
        'gu': {'name': 'Gujarati', 'native': 'ગુજરાતી', 'rtl': False},
        'kn': {'name': 'Kannada', 'native': 'ಕನ್ನಡ', 'rtl': False},
        'ml': {'name': 'Malayalam', 'native': 'മലയാളം', 'rtl': False},
        'pa': {'name': 'Punjabi', 'native': 'ਪੰਜਾਬੀ', 'rtl': False},
        'or': {'name': 'Odia', 'native': 'ଓଡ଼ିଆ', 'rtl': False},
        'ur': {'name': 'Urdu', 'native': 'اردو', 'rtl': True},
    }
    
    # Legal terminology mapping (English -> Hindi/other languages)
    LEGAL_TERMS = {
        'en': {
            'plaintiff': 'plaintiff',
            'defendant': 'defendant',
            'court': 'court',
            'judgment': 'judgment',
            'appeal': 'appeal',
            'bail': 'bail',
            'petition': 'petition',
            'advocate': 'advocate',
            'judge': 'judge',
            'supreme_court': 'Supreme Court',
            'high_court': 'High Court',
            'district_court': 'District Court',
        },
        'hi': {
            'plaintiff': 'वादी',
            'defendant': 'प्रतिवादी',
            'court': 'न्यायालय',
            'judgment': 'निर्णय',
            'appeal': 'अपील',
            'bail': 'जमानत',
            'petition': 'याचिका',
            'advocate': 'अधिवक्ता',
            'judge': 'न्यायाधीश',
            'supreme_court': 'सर्वोच्च न्यायालय',
            'high_court': 'उच्च न्यायालय',
            'district_court': 'जिला न्यायालय',
        }
    }
    
    def __init__(self):
        """Initialize translation service"""
        self.translator = None
        self.available = False
        
        if GOOGLETRANS_AVAILABLE:
            try:
                self.translator = Translator()
                self.available = True
                print("✅ Multi-language translation service initialized")
            except Exception as e:
                print(f"⚠️  Translation service initialization failed: {e}")
        else:
            print("📝 Using basic translation (install googletrans for full features)")
    
    def translate(self, text: str, dest_lang: str = 'en', src_lang: str = 'auto') -> Dict:
        """
        Translate text to target language
        
        Args:
            text: Text to translate
            dest_lang: Destination language code (e.g., 'hi', 'ta')
            src_lang: Source language code ('auto' for detection)
            
        Returns:
            Dictionary with translation results
        """
        if not text or not text.strip():
            return {
                'success': False,
                'error': 'Empty text provided',
                'original_text': text,
                'translated_text': text,
                'src_lang': src_lang,
                'dest_lang': dest_lang
            }
        
        # Validate destination language
        if dest_lang not in self.SUPPORTED_LANGUAGES:
            return {
                'success': False,
                'error': f'Unsupported language: {dest_lang}',
                'supported_languages': list(self.SUPPORTED_LANGUAGES.keys())
            }
        
        try:
            if not self.available:
                # Fallback: Return original text
                return {
                    'success': False,
                    'error': 'Translation service not available',
                    'original_text': text,
                    'translated_text': text,
                    'src_lang': src_lang,
                    'dest_lang': dest_lang,
                    'note': 'Install googletrans: pip install googletrans==4.0.0rc1'
                }
            
            # Perform translation
            result = self.translator.translate(text, dest=dest_lang, src=src_lang)
            
            # Get legal term replacements
            translated_with_terms = self._enhance_legal_translation(
                result.text, 
                dest_lang
            )
            
            return {
                'success': True,
                'original_text': text,
                'translated_text': translated_with_terms,
                'raw_translation': result.text,
                'src_lang': result.src,
                'dest_lang': result.dest,
                'confidence': getattr(result, 'confidence', None),
                'pronunciation': getattr(result, 'pronunciation', None),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'original_text': text,
                'translated_text': text,
                'src_lang': src_lang,
                'dest_lang': dest_lang
            }
    
    def detect_language(self, text: str) -> Dict:
        """
        Detect language of text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with detected language
        """
        if not text or not text.strip():
            return {
                'success': False,
                'error': 'Empty text provided'
            }
        
        try:
            if not self.available:
                return {
                    'success': False,
                    'error': 'Detection service not available',
                    'note': 'Install googletrans for language detection'
                }
            
            result = self.translator.detect(text)
            
            lang_code = result.lang
            lang_info = self.SUPPORTED_LANGUAGES.get(
                lang_code, 
                {'name': 'Unknown', 'native': 'Unknown', 'rtl': False}
            )
            
            return {
                'success': True,
                'detected_lang': lang_code,
                'language_name': lang_info['name'],
                'native_name': lang_info['native'],
                'confidence': result.confidence,
                'is_supported': lang_code in self.SUPPORTED_LANGUAGES,
                'is_rtl': lang_info['rtl']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def batch_translate(self, texts: List[str], dest_lang: str = 'hi', 
                       src_lang: str = 'auto') -> List[Dict]:
        """
        Translate multiple texts
        
        Args:
            texts: List of texts to translate
            dest_lang: Destination language
            src_lang: Source language
            
        Returns:
            List of translation results
        """
        results = []
        for text in texts:
            result = self.translate(text, dest_lang, src_lang)
            results.append(result)
        
        return results
    
    def get_supported_languages(self) -> Dict:
        """
        Get list of supported languages
        
        Returns:
            Dictionary of supported languages
        """
        return {
            'success': True,
            'languages': self.SUPPORTED_LANGUAGES,
            'total_count': len(self.SUPPORTED_LANGUAGES)
        }
    
    def translate_legal_response(self, response: str, dest_lang: str = 'hi') -> Dict:
        """
        Translate legal response with preserved formatting
        
        Args:
            response: Legal response text (may contain markdown)
            dest_lang: Target language
            
        Returns:
            Translated response with preserved formatting
        """
        if dest_lang == 'en':
            return {
                'success': True,
                'original_text': response,
                'translated_text': response,
                'dest_lang': 'en',
                'note': 'No translation needed'
            }
        
        try:
            # Split into sections (preserve markdown headings)
            lines = response.split('\n')
            translated_lines = []
            
            for line in lines:
                if not line.strip():
                    translated_lines.append(line)
                    continue
                
                # Preserve markdown formatting
                if line.startswith('**') and line.endswith('**'):
                    # Bold heading
                    text = line.strip('*')
                    trans = self.translate(text, dest_lang)
                    translated_lines.append(f"**{trans['translated_text']}**")
                elif line.startswith('- ') or line.startswith('• '):
                    # Bullet point
                    text = line[2:].strip()
                    trans = self.translate(text, dest_lang)
                    translated_lines.append(f"{line[:2]}{trans['translated_text']}")
                elif line.startswith('#'):
                    # Heading
                    level = len(line) - len(line.lstrip('#'))
                    text = line.lstrip('#').strip()
                    trans = self.translate(text, dest_lang)
                    translated_lines.append(f"{'#' * level} {trans['translated_text']}")
                else:
                    # Regular text
                    trans = self.translate(line, dest_lang)
                    translated_lines.append(trans['translated_text'])
            
            translated_response = '\n'.join(translated_lines)
            
            return {
                'success': True,
                'original_text': response,
                'translated_text': translated_response,
                'dest_lang': dest_lang,
                'line_count': len(lines)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'original_text': response,
                'translated_text': response
            }
    
    def _enhance_legal_translation(self, text: str, dest_lang: str) -> str:
        """
        Enhance translation with proper legal terminology
        
        Args:
            text: Translated text
            dest_lang: Destination language
            
        Returns:
            Enhanced text with legal terms
        """
        if dest_lang not in self.LEGAL_TERMS:
            return text
        
        # Replace common legal terms with proper translations
        enhanced_text = text
        
        # Get English and target language terms
        en_terms = self.LEGAL_TERMS['en']
        target_terms = self.LEGAL_TERMS[dest_lang]
        
        # Replace terms (case-insensitive)
        for en_key, en_value in en_terms.items():
            if en_value.lower() in enhanced_text.lower():
                target_value = target_terms[en_key]
                # Simple replacement (can be improved with regex)
                enhanced_text = enhanced_text.replace(en_value, target_value)
                enhanced_text = enhanced_text.replace(en_value.lower(), target_value)
        
        return enhanced_text
    
    def transliterate(self, text: str, script: str = 'devanagari') -> Dict:
        """
        Transliterate text to different script
        
        Args:
            text: Text to transliterate
            script: Target script (devanagari, roman)
            
        Returns:
            Transliterated text
        """
        # Basic transliteration (can be enhanced with indic-transliteration library)
        return {
            'success': False,
            'error': 'Transliteration not yet implemented',
            'note': 'Install indic-transliteration for full support',
            'original_text': text
        }


# Global instance
_language_service = None


def get_language_service() -> LanguageService:
    """Get or create language service instance"""
    global _language_service
    
    if _language_service is None:
        _language_service = LanguageService()
    
    return _language_service


# Quick access functions
def translate_text(text: str, dest_lang: str = 'hi', src_lang: str = 'auto') -> Dict:
    """Quick translate function"""
    service = get_language_service()
    return service.translate(text, dest_lang, src_lang)


def detect_language(text: str) -> Dict:
    """Quick language detection"""
    service = get_language_service()
    return service.detect_language(text)


def get_supported_languages() -> Dict:
    """Get supported languages"""
    service = get_language_service()
    return service.get_supported_languages()


if __name__ == '__main__':
    # Test the service
    print("=" * 80)
    print("LANGUAGE SERVICE TEST")
    print("=" * 80)
    
    service = LanguageService()
    
    # Test 1: Translation
    print("\n1. Translation Test:")
    result = service.translate("What is the law for property partition?", dest_lang='hi')
    if result['success']:
        print(f"   Original: {result['original_text']}")
        print(f"   Translated: {result['translated_text']}")
        print(f"   Detected source: {result['src_lang']}")
    else:
        print(f"   Error: {result.get('error', 'Unknown error')}")
    
    # Test 2: Language Detection
    print("\n2. Language Detection Test:")
    hindi_text = "संपत्ति विभाजन के लिए कानून क्या है?"
    detect_result = service.detect_language(hindi_text)
    if detect_result['success']:
        print(f"   Text: {hindi_text}")
        print(f"   Detected: {detect_result['language_name']} ({detect_result['detected_lang']})")
        print(f"   Confidence: {detect_result.get('confidence', 'N/A')}")
    
    # Test 3: Supported Languages
    print("\n3. Supported Languages:")
    langs = service.get_supported_languages()
    for code, info in langs['languages'].items():
        print(f"   {code}: {info['name']} ({info['native']})")
    
    print("\n" + "=" * 80)
