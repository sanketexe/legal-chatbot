"""
Translation Module for LegalAssist Pro
Provides Hindi translation support with specialized legal terminology
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class HindiLegalTerms:
    """Hindi translation dictionary for legal terms"""
    
    # Core legal terms
    LEGAL_TERMS = {
        # Court and Legal System
        'court': 'अदालत',
        'judge': 'न्यायाधीश',
        'case': 'मामला',
        'law': 'कानून',
        'legal': 'कानूनी',
        'statute': 'अधिनियम',
        'act': 'अधिनियम',
        'lawyer': 'वकील',
        'attorney': 'अधिवक्ता',
        'plaintiff': 'वादी',
        'defendant': 'प्रतिवादी',
        'petition': 'याचिका',
        'appeal': 'अपील',
        'verdict': 'फैसला',
        'judgment': 'फैसला',
        'hearing': 'सुनवाई',
        'trial': 'मुकदमा',
        'evidence': 'साक्ष्य',
        'witness': 'गवाह',
        'testimony': 'गवाही',
        
        # Family Law
        'divorce': 'तलाक',
        'marriage': 'विवाह',
        'spouse': 'जीवनसाथी',
        'custody': 'संरक्षकता',
        'child': 'बालक',
        'maintenance': 'भरण-पोषण',
        'alimony': 'गुजारा भत्ता',
        'property': 'संपत्ति',
        'inheritance': 'विरासत',
        'will': 'वसीयत',
        'succession': 'उत्तराधिकार',
        
        # Civil Law
        'contract': 'अनुबंध',
        'agreement': 'समझौता',
        'breach': 'उल्लंघन',
        'compensation': 'मुआवजा',
        'damages': 'हर्जाना',
        'liability': 'दायित्व',
        'negligence': 'लापरवाही',
        'tort': 'कानूनी हानि',
        
        # Criminal Law
        'criminal': 'अपराधी',
        'crime': 'अपराध',
        'accused': 'अभियुक्त',
        'arrest': 'गिरफ्तारी',
        'bail': 'जमानत',
        'imprisonment': 'कारावास',
        'sentence': 'सजा',
        'punishment': 'दंड',
        'theft': 'चोरी',
        'fraud': 'धोखाधड़ी',
        'assault': 'हमला',
        
        # Legal Actions and Procedures
        'file': 'दाखिल करना',
        'submit': 'जमा करना',
        'document': 'दस्तावेज',
        'certificate': 'प्रमाण पत्र',
        'affidavit': 'शपथपत्र',
        'lawsuit': 'मुकदमा',
        'claim': 'दावा',
        'dispute': 'विवाद',
        'settlement': 'समझौता',
        'mediation': 'मध्यस्थता',
        'arbitration': 'पंचाट',
        
        # Indian Legal System
        'constitution': 'संविधान',
        'supreme court': 'सर्वोच्च न्यायालय',
        'high court': 'उच्च न्यायालय',
        'district court': 'जिला न्यायालय',
        'code': 'संहिता',
        'ipc': 'भारतीय दंड संहिता',
        'crpc': 'आपराधिक प्रक्रिया संहिता',
        'cpc': 'नागरिक प्रक्रिया संहिता',
        'indian penal code': 'भारतीय दंड संहिता',
        'criminal procedure code': 'आपराधिक प्रक्रिया संहिता',
        'civil procedure code': 'नागरिक प्रक्रिया संहिता',
        
        # Rights and Duties
        'right': 'अधिकार',
        'duty': 'कर्तव्य',
        'obligation': 'दायित्व',
        'rights': 'अधिकार',
        'constitution rights': 'संवैधानिक अधिकार',
        'human rights': 'मानव अधिकार',
        'property rights': 'संपत्ति अधिकार',
        
        # Common Legal Questions
        'valid': 'मान्य',
        'invalid': 'अमान्य',
        'legal': 'कानूनी',
        'illegal': 'गैरकानूनी',
        'procedure': 'प्रक्रिया',
        'jurisdiction': 'न्यायाधिकार',
        'applicable': 'लागू',
    }
    
    @classmethod
    def get_term(cls, english_term: str, default: Optional[str] = None) -> str:
        """Get Hindi translation for an English legal term"""
        hindi = cls.LEGAL_TERMS.get(english_term.lower())
        if hindi:
            return hindi
        return default if default else english_term

class TranslationService:
    """
    Service for translating legal content to Hindi
    Uses combination of legal term dictionary and basic sentence translation
    """
    
    def __init__(self):
        """Initialize translation service"""
        self.hindi_terms = HindiLegalTerms()
        self.translation_cache: Dict[str, str] = {}
        self.stats = {
            'total_translations': 0,
            'cache_hits': 0,
            'terms_translated': 0,
            'sentences_translated': 0,
            'errors': 0,
        }
        logger.info("TranslationService initialized")
    
    def translate_term(self, term: str) -> str:
        """Translate a single legal term to Hindi"""
        try:
            self.stats['total_translations'] += 1
            hindi = self.hindi_terms.get_term(term)
            self.stats['terms_translated'] += 1
            return hindi
        except Exception as e:
            logger.error(f"Error translating term '{term}': {str(e)}")
            self.stats['errors'] += 1
            return term
    
    def _translate_sentence_basic(self, sentence: str) -> str:
        """
        Basic sentence translation by replacing English legal terms with Hindi equivalents
        This is a fallback method - in production, would use Google Translate or similar
        """
        try:
            translated = sentence
            
            # Sort by length descending to replace longer phrases first
            sorted_terms = sorted(
                self.hindi_terms.LEGAL_TERMS.items(),
                key=lambda x: len(x[0]),
                reverse=True
            )
            
            for english, hindi in sorted_terms:
                # Case-insensitive replacement with word boundaries
                import re
                pattern = r'\b' + re.escape(english) + r'\b'
                translated = re.sub(pattern, hindi, translated, flags=re.IGNORECASE)
            
            return translated
        except Exception as e:
            logger.error(f"Error in sentence translation: {str(e)}")
            self.stats['errors'] += 1
            return sentence
    
    def translate_sentence(self, sentence: str, use_cache: bool = True) -> str:
        """
        Translate a sentence to Hindi using basic term replacement
        
        Args:
            sentence: English sentence to translate
            use_cache: Whether to use cache for previously translated sentences
            
        Returns:
            Translated sentence in Hindi
        """
        try:
            self.stats['total_translations'] += 1
            
            # Check cache
            if use_cache and sentence in self.translation_cache:
                self.stats['cache_hits'] += 1
                return self.translation_cache[sentence]
            
            # Translate
            translated = self._translate_sentence_basic(sentence)
            
            # Cache result
            if use_cache:
                self.translation_cache[sentence] = translated
            
            self.stats['sentences_translated'] += 1
            return translated
        except Exception as e:
            logger.error(f"Error translating sentence: {str(e)}")
            self.stats['errors'] += 1
            return sentence
    
    def translate_response(self, response: str) -> str:
        """
        Translate a full legal response to Hindi
        
        Args:
            response: Full response text (may contain markdown)
            
        Returns:
            Hindi translation of the response
        """
        try:
            self.stats['total_translations'] += 1
            
            # Split by paragraphs
            paragraphs = response.split('\n')
            translated_paragraphs = []
            
            for para in paragraphs:
                if para.strip():
                    # Check for markdown headers
                    if para.startswith('#'):
                        # Translate header but keep markdown
                        header_level = len(para) - len(para.lstrip('#'))
                        header_text = para.lstrip('#').strip()
                        translated_header = self.translate_sentence(header_text)
                        translated_paragraphs.append('#' * header_level + ' ' + translated_header)
                    else:
                        # Translate regular paragraph
                        translated = self.translate_sentence(para)
                        translated_paragraphs.append(translated)
                else:
                    translated_paragraphs.append('')
            
            return '\n'.join(translated_paragraphs)
        except Exception as e:
            logger.error(f"Error translating response: {str(e)}")
            self.stats['errors'] += 1
            return response
    
    def create_bilingual_response(self, english_response: str) -> Dict[str, str]:
        """
        Create a bilingual response with both English and Hindi versions
        
        Args:
            english_response: The English legal response
            
        Returns:
            Dictionary with 'english' and 'hindi' keys
        """
        try:
            hindi_response = self.translate_response(english_response)
            return {
                'english': english_response,
                'hindi': hindi_response,
                'language': 'bilingual',
            }
        except Exception as e:
            logger.error(f"Error creating bilingual response: {str(e)}")
            self.stats['errors'] += 1
            return {
                'english': english_response,
                'hindi': english_response,  # Fallback to English
                'language': 'english_only',
            }
    
    def translate_terms_in_text(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Translate key legal terms in text and return mapping
        
        Args:
            text: Text containing legal terms
            
        Returns:
            Tuple of (translated_text, term_mapping)
        """
        try:
            term_mapping = {}
            translated = text
            
            # Extract and translate legal terms
            import re
            words = re.findall(r'\b\w+\b', text.lower())
            
            for word in set(words):
                hindi = self.hindi_terms.get_term(word)
                if hindi != word:  # Found a translation
                    term_mapping[word] = hindi
                    # Replace in text (case-insensitive)
                    pattern = r'\b' + re.escape(word) + r'\b'
                    translated = re.sub(pattern, hindi, translated, flags=re.IGNORECASE)
            
            return translated, term_mapping
        except Exception as e:
            logger.error(f"Error in translate_terms_in_text: {str(e)}")
            self.stats['errors'] += 1
            return text, {}
    
    def get_stats(self) -> Dict:
        """Get translation statistics"""
        return {
            **self.stats,
            'cache_size': len(self.translation_cache),
            'timestamp': datetime.utcnow().isoformat(),
        }
    
    def reset_cache(self) -> None:
        """Clear the translation cache"""
        self.translation_cache.clear()
        logger.info("Translation cache cleared")
    
    def reset_stats(self) -> None:
        """Reset statistics"""
        self.stats = {
            'total_translations': 0,
            'cache_hits': 0,
            'terms_translated': 0,
            'sentences_translated': 0,
            'errors': 0,
        }
        logger.info("Translation statistics reset")


# Global instance
_translation_service = None

def get_translation_service() -> TranslationService:
    """Get or create global translation service instance"""
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
    return _translation_service

def translate_to_hindi(text: str) -> str:
    """Convenience function to translate text to Hindi"""
    service = get_translation_service()
    return service.translate_response(text)

def create_bilingual_response(english_text: str) -> Dict[str, str]:
    """Convenience function to create bilingual response"""
    service = get_translation_service()
    return service.create_bilingual_response(english_text)
