"""
Test Hybrid RAG System
Run: python test_hybrid_rag.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_legal_system.hybrid_rag import HybridRAG
import json


class TestHybridRAG:
    """Test suite for hybrid RAG system"""
    
    def __init__(self):
        # Sample legal documents
        self.documents = [
            "Divorce proceedings require filing petition in family court with grounds under Indian Divorce Act 1869",
            "Supreme Court ruling on spousal maintenance and alimony obligations in matrimonial disputes",
            "Property division rules during divorce: separate property vs joint marital assets",
            "Marriage registration and validity under Hindu Marriage Act and Special Marriage Act",
            "Custody rights of children in family law matters and welfare considerations",
            "Criminal law enforcement procedures under Indian Penal Code and Criminal Procedure Code",
            "Property rights and ownership transfer in civil law matters",
            "Constitutional rights and fundamental freedoms in Indian Constitution",
            "Labor law regulations for employee rights and working conditions",
            "Tax law and GST regulations for businesses in India"
        ]
        
        # Create dummy semantic search
        def semantic_search(query: str, top_k: int = 5):
            """Simple semantic search - keyword matching"""
            query_words = query.lower().split()
            scores = []
            
            for doc in self.documents:
                doc_lower = doc.lower()
                score = sum(1 for word in query_words if word in doc_lower) / len(query_words) if query_words else 0
                scores.append((doc, score))
            
            return sorted(scores, key=lambda x: x[1], reverse=True)[:top_k]
        
        self.hybrid = HybridRAG(
            semantic_search_fn=semantic_search,
            bm25_corpus=self.documents
        )
    
    def test_basic_search(self):
        """Test basic hybrid search"""
        print("\n" + "="*70)
        print("TEST 1: Basic Hybrid Search")
        print("="*70)
        
        query = "What are divorce rights and procedures?"
        results = self.hybrid.hybrid_search(query, top_k=3)
        
        print(f"\n🔍 Query: '{query}'")
        print(f"\n📊 Results ({len(results)} found):")
        
        success = len(results) > 0
        for result in results:
            print(f"\n  Rank {result['rank']}: Score {result['score']:.3f}")
            print(f"  📄 {result['document'][:70]}...")
            print(f"     • Semantic Score: {result['semantic_score']:.3f}")
            print(f"     • Keyword Score: {result['keyword_score']:.3f}")
        
        return success
    
    def test_property_search(self):
        """Test search for property-related queries"""
        print("\n" + "="*70)
        print("TEST 2: Property Division Search")
        print("="*70)
        
        query = "How is property divided in divorce?"
        results = self.hybrid.hybrid_search(query, top_k=3)
        
        print(f"\n🔍 Query: '{query}'")
        print(f"\n📊 Results ({len(results)} found):")
        
        success = len(results) > 0
        for result in results:
            print(f"\n  {result['rank']}. {result['document'][:60]}...")
            print(f"     Score: {result['score']:.3f} (semantic: {result['semantic_score']:.3f}, keyword: {result['keyword_score']:.3f})")
        
        return success
    
    def test_custody_search(self):
        """Test search for custody-related queries"""
        print("\n" + "="*70)
        print("TEST 3: Custody Rights Search")
        print("="*70)
        
        query = "What are my custody rights?"
        results = self.hybrid.hybrid_search(query, top_k=3)
        
        print(f"\n🔍 Query: '{query}'")
        print(f"\n📊 Results ({len(results)} found):")
        
        success = len(results) > 0
        for result in results:
            print(f"\n  {result['rank']}. {result['document'][:60]}...")
            print(f"     Score: {result['score']:.3f}")
        
        return success
    
    def test_weights(self):
        """Test different weight combinations"""
        print("\n" + "="*70)
        print("TEST 4: Different Weight Combinations")
        print("="*70)
        
        query = "divorce proceedings"
        
        # Test 1: Semantic heavy
        results_semantic_heavy = self.hybrid.hybrid_search(query, top_k=1, semantic_weight=0.8, keyword_weight=0.2)
        
        # Test 2: Keyword heavy
        results_keyword_heavy = self.hybrid.hybrid_search(query, top_k=1, semantic_weight=0.2, keyword_weight=0.8)
        
        # Test 3: Balanced
        results_balanced = self.hybrid.hybrid_search(query, top_k=1, semantic_weight=0.5, keyword_weight=0.5)
        
        print(f"\n🔍 Query: '{query}'")
        
        print(f"\n1️⃣ Semantic Heavy (80:20):")
        if results_semantic_heavy:
            r = results_semantic_heavy[0]
            print(f"   Result: {r['document'][:50]}...")
            print(f"   Score: {r['score']:.3f}")
        
        print(f"\n2️⃣ Keyword Heavy (20:80):")
        if results_keyword_heavy:
            r = results_keyword_heavy[0]
            print(f"   Result: {r['document'][:50]}...")
            print(f"   Score: {r['score']:.3f}")
        
        print(f"\n3️⃣ Balanced (50:50):")
        if results_balanced:
            r = results_balanced[0]
            print(f"   Result: {r['document'][:50]}...")
            print(f"   Score: {r['score']:.3f}")
        
        return True
    
    def test_stats(self):
        """Test search statistics"""
        print("\n" + "="*70)
        print("TEST 5: Search Statistics")
        print("="*70)
        
        # Perform some searches
        queries = [
            "divorce procedures",
            "property division",
            "custody rights",
            "marriage registration"
        ]
        
        for query in queries:
            self.hybrid.hybrid_search(query, top_k=3)
        
        stats = self.hybrid.get_stats()
        
        print(f"\n📊 Statistics after {len(queries)} searches:")
        print(f"   Total Searches: {stats['total_searches']}")
        print(f"   Hybrid Searches: {stats['hybrid_searches']}")
        print(f"   Semantic Only: {stats['semantic_only']}")
        print(f"   BM25 Only: {stats['bm25_only']}")
        print(f"   Average Time: {stats['avg_time']:.4f}s")
        
        return stats['total_searches'] > 0
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*70)
        print("HYBRID RAG TEST SUITE")
        print("="*70)
        
        tests = [
            ("Basic Search", self.test_basic_search),
            ("Property Search", self.test_property_search),
            ("Custody Search", self.test_custody_search),
            ("Weight Combinations", self.test_weights),
            ("Statistics", self.test_stats)
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"\n❌ {test_name} FAILED: {e}")
                results[test_name] = False
        
        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status:8s} • {test_name}")
        
        print(f"\n📊 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED!")
        
        print("\n" + "="*70)
        
        return passed == total


if __name__ == '__main__':
    tester = TestHybridRAG()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)
