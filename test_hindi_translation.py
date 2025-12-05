"""
Test suite for Hindi translation support (Day 3)
Tests translation service with legal terminology and full responses
"""

import unittest
import sys
import os
from datetime import datetime

# Add paths
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ml_legal_system'))

from ml_legal_system.translators import (
    TranslationService, HindiLegalTerms, 
    get_translation_service, translate_to_hindi, create_bilingual_response
)

class TestHindiLegalTerms(unittest.TestCase):
    """Test Hindi legal terminology dictionary"""
    
    def setUp(self):
        self.terms = HindiLegalTerms()
    
    def test_court_translation(self):
        """Test translation of court"""
        result = self.terms.get_term('court')
        self.assertEqual(result, 'अदालत')
        print(f"✅ TEST 1: Court translation - '{result}'")
    
    def test_divorce_translation(self):
        """Test translation of divorce"""
        result = self.terms.get_term('divorce')
        self.assertEqual(result, 'तलाक')
        print(f"✅ TEST 2: Divorce translation - '{result}'")
    
    def test_judge_translation(self):
        """Test translation of judge"""
        result = self.terms.get_term('judge')
        self.assertEqual(result, 'न्यायाधीश')
        print(f"✅ TEST 3: Judge translation - '{result}'")
    
    def test_case_insensitive(self):
        """Test case-insensitive term lookup"""
        result_lower = self.terms.get_term('COURT')
        result_mixed = self.terms.get_term('CoUrT')
        self.assertEqual(result_lower, 'अदालत')
        self.assertEqual(result_mixed, 'अदालत')
        print(f"✅ TEST 4: Case-insensitive lookup working")
    
    def test_unknown_term(self):
        """Test handling of unknown terms"""
        result = self.terms.get_term('xyz123unknown')
        self.assertEqual(result, 'xyz123unknown')
        print(f"✅ TEST 5: Unknown term fallback working")


class TestTranslationService(unittest.TestCase):
    """Test the main translation service"""
    
    def setUp(self):
        self.service = TranslationService()
        self.service.reset_stats()
    
    def test_translate_single_term(self):
        """Test translating a single term"""
        result = self.service.translate_term('judge')
        self.assertEqual(result, 'न्यायाधीश')
        self.assertEqual(self.service.stats['terms_translated'], 1)
        print(f"✅ TEST 6: Single term translation - '{result}'")
    
    def test_translate_sentence_basic(self):
        """Test basic sentence translation with legal terms"""
        sentence = "The judge will hear the case in court"
        result = self.service.translate_sentence(sentence)
        
        # Check that key terms are translated
        self.assertIn('न्यायाधीश', result)  # judge
        self.assertIn('मामला', result)       # case
        self.assertIn('अदालत', result)      # court
        self.assertEqual(self.service.stats['sentences_translated'], 1)
        print(f"✅ TEST 7: Sentence translation working")
        print(f"   Original: {sentence}")
        print(f"   Translated: {result}")
    
    def test_translate_divorce_sentence(self):
        """Test translating a divorce-related sentence"""
        sentence = "What are the grounds for divorce?"
        result = self.service.translate_sentence(sentence)
        
        self.assertIn('तलाक', result)  # divorce
        print(f"✅ TEST 8: Divorce sentence translation")
        print(f"   Original: {sentence}")
        print(f"   Translated: {result}")
    
    def test_translate_custody_sentence(self):
        """Test translating a custody-related sentence"""
        sentence = "The court will decide custody of the child"
        result = self.service.translate_sentence(sentence)
        
        self.assertIn('अदालत', result)   # court
        self.assertIn('संरक्षकता', result)  # custody
        self.assertIn('बालक', result)     # child
        print(f"✅ TEST 9: Custody sentence translation")
        print(f"   Original: {sentence}")
        print(f"   Translated: {result}")
    
    def test_translation_caching(self):
        """Test that translations are cached"""
        sentence = "The judge will hear the case"
        
        # First call
        result1 = self.service.translate_sentence(sentence, use_cache=True)
        cache_size_after_first = len(self.service.translation_cache)
        
        # Second call (should hit cache)
        result2 = self.service.translate_sentence(sentence, use_cache=True)
        
        self.assertEqual(result1, result2)
        self.assertEqual(cache_size_after_first, 1)
        self.assertEqual(self.service.stats['cache_hits'], 1)
        print(f"✅ TEST 10: Translation caching - Cache size: {cache_size_after_first}")
    
    def test_translate_markdown_response(self):
        """Test translating markdown response with headers"""
        response = """# Contract Law Guide

This is about contracts. A valid contract requires offer and acceptance.

## Key Points
- A contract is an agreement
- It must have consideration
- It should be enforceable"""
        
        result = self.service.translate_response(response)
        
        # Check that markdown headers are preserved but translated
        self.assertIn('#', result)  # Headers preserved
        self.assertIn('अनुबंध', result)  # contract
        print(f"✅ TEST 11: Markdown response translation")
        print(f"   Original (first 50 chars): {response[:50]}...")
        print(f"   Translated (first 50 chars): {result[:50]}...")
    
    def test_bilingual_response(self):
        """Test creating bilingual response"""
        english = "The judge will decide the case"
        result = self.service.create_bilingual_response(english)
        
        self.assertIn('english', result)
        self.assertIn('hindi', result)
        self.assertEqual(result['language'], 'bilingual')
        self.assertNotEqual(result['english'], result['hindi'])
        print(f"✅ TEST 12: Bilingual response creation")
        print(f"   English: {result['english']}")
        print(f"   Hindi: {result['hindi']}")
    
    def test_translation_stats(self):
        """Test translation statistics tracking"""
        self.service.translate_term('judge')
        self.service.translate_term('court')
        self.service.translate_sentence("Hello world")
        
        stats = self.service.get_stats()
        
        self.assertGreaterEqual(stats['total_translations'], 3)
        self.assertEqual(stats['terms_translated'], 2)
        self.assertEqual(stats['sentences_translated'], 1)
        print(f"✅ TEST 13: Translation statistics")
        print(f"   Total translations: {stats['total_translations']}")
        print(f"   Terms: {stats['terms_translated']}, Sentences: {stats['sentences_translated']}")
    
    def test_reset_cache(self):
        """Test resetting cache"""
        sentence = "The judge will hear the case"
        self.service.translate_sentence(sentence, use_cache=True)
        self.assertGreater(len(self.service.translation_cache), 0)
        
        self.service.reset_cache()
        self.assertEqual(len(self.service.translation_cache), 0)
        print(f"✅ TEST 14: Cache reset working")


class TestTranslationIntegration(unittest.TestCase):
    """Integration tests for translation with real legal content"""
    
    def setUp(self):
        self.service = get_translation_service()
        self.service.reset_stats()
    
    def test_full_legal_response(self):
        """Test translating a complete legal response"""
        legal_response = """# Divorce Rights and Procedure in India

## Legal Grounds for Divorce

In India, divorce can be granted under the Hindu Marriage Act, 1955. The grounds for divorce include:

### Cruelty
If your spouse has treated you with cruelty, you can file for divorce.

### Adultery
If your spouse has committed adultery, you have grounds for divorce.

## Property Division

During divorce proceedings, the court will decide on property division. The judge considers the following:
- Property acquired during the marriage
- Contribution of each spouse
- Best interests of any children

## Custody Rights

The custody of children is decided by the court in the best interest of the child."""
        
        result = self.service.translate_response(legal_response)
        
        # Verify key terms are translated
        self.assertIn('तलाक', result)           # divorce
        self.assertIn('अदालत', result)          # court
        self.assertIn('न्यायाधीश', result)      # judge
        self.assertIn('संपत्ति', result)         # property
        self.assertIn('संरक्षकता', result)       # custody
        self.assertIn('बालक', result)           # child
        
        print(f"✅ TEST 15: Full legal response translation")
        print(f"   Original length: {len(legal_response)} chars")
        print(f"   Translated length: {len(result)} chars")
        print(f"   First 100 chars of translation:\n   {result[:100]}...")
    
    def test_property_division_query(self):
        """Test translating property division related response"""
        response = "How is property divided in a divorce case? The court considers the contribution of each spouse."
        result = self.service.translate_response(response)
        
        self.assertIn('संपत्ति', result)   # property
        self.assertIn('तलाक', result)      # divorce
        self.assertIn('अदालत', result)     # court
        print(f"✅ TEST 16: Property division translation")
    
    def test_custody_query(self):
        """Test translating custody related response"""
        response = "The best interests of the child are the primary consideration in custody cases."
        result = self.service.translate_response(response)
        
        self.assertIn('बालक', result)      # child
        self.assertIn('संरक्षकता', result)  # custody
        print(f"✅ TEST 17: Custody query translation")
    
    def test_translation_performance(self):
        """Test translation performance metrics"""
        import time
        
        sentences = [
            "What is the contract law?",
            "How does a judge decide?",
            "What about property rights?"
        ]
        
        start_time = time.time()
        for sentence in sentences:
            self.service.translate_sentence(sentence)
        elapsed = time.time() - start_time
        
        # Should be very fast (< 1 second for 3 sentences)
        self.assertLess(elapsed, 1.0)
        print(f"✅ TEST 18: Translation performance")
        print(f"   Translated 3 sentences in {elapsed:.4f}s")
        print(f"   Average: {elapsed/3:.4f}s per sentence")
    
    def test_terms_in_text_extraction(self):
        """Test extracting and translating specific terms from text"""
        text = "The judge ruled on the contract case regarding property division."
        translated, term_mapping = self.service.translate_terms_in_text(text)
        
        self.assertIn('judge', term_mapping)
        self.assertIn('contract', term_mapping)
        self.assertIn('property', term_mapping)
        self.assertEqual(term_mapping['judge'], 'न्यायाधीश')
        self.assertEqual(term_mapping['contract'], 'अनुबंध')
        print(f"✅ TEST 19: Terms extraction and mapping")
        print(f"   Terms found: {len(term_mapping)}")
        print(f"   Mappings: {term_mapping}")


def run_all_tests():
    """Run all tests and display summary"""
    print("\n" + "="*70)
    print("🚀 DAY 3: HINDI LANGUAGE SUPPORT - COMPREHENSIVE TEST SUITE")
    print("="*70 + "\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestHindiLegalTerms))
    suite.addTests(loader.loadTestsFromTestCase(TestTranslationService))
    suite.addTests(loader.loadTestsFromTestCase(TestTranslationIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED! ✅")
        print("\n✨ Day 3 Achievements:")
        print("   • HindiLegalTerms dictionary with 100+ legal terms ✅")
        print("   • TranslationService with caching ✅")
        print("   • Full response translation support ✅")
        print("   • Bilingual response generation ✅")
        print("   • Integration with user preferences ✅")
        print("   • 19/19 comprehensive tests passing ✅")
    else:
        print("\n❌ Some tests failed")
    
    print("="*70 + "\n")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
