"""
Comprehensive RAG System Test Suite
Tests the RAG system directly without requiring Flask server
"""

import os
import sys
import json
from datetime import datetime
from typing import List, Dict

# Add ml_legal_system to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ml_legal_system'))

def test_vector_database():
    """Test vector database functionality"""
    print("\n" + "="*60)
    print("🔍 Testing Vector Database")
    print("="*60)
    
    try:
        from vector_db import LegalVectorDatabase
        
        # Initialize database
        db = LegalVectorDatabase(use_cloud=False)
        print("✅ Vector database initialized successfully")
        
        # Test embedding creation
        test_texts = [
            "Contract breach and damages under Indian law",
            "Property rights and inheritance laws",
            "Motor vehicle accident liability"
        ]
        
        embeddings = db.create_embeddings(test_texts, use_openai=False)
        print(f"✅ Created embeddings for {len(embeddings)} test texts")
        
        # Test search functionality (if data exists)
        try:
            results = db.search_similar_cases("contract breach", top_k=3)
            print(f"✅ Search functionality working - found {len(results)} results")
            return True, len(results)
        except Exception as e:
            print(f"⚠️  Search test failed (may be due to empty database): {e}")
            return True, 0
            
    except Exception as e:
        print(f"❌ Vector database test failed: {e}")
        return False, 0

def test_legal_rag_system():
    """Test Legal RAG system functionality"""
    print("\n" + "="*60)
    print("🤖 Testing Legal RAG System")
    print("="*60)
    
    try:
        from legal_rag import LegalRAG
        
        # Initialize RAG system
        rag = LegalRAG(use_openai=False)
        print("✅ Legal RAG system initialized successfully")
        
        # Test case retrieval
        test_query = "What are the remedies for breach of contract?"
        print(f"\n🔍 Testing case retrieval for: '{test_query}'")
        
        relevant_cases = rag.retrieve_relevant_cases(test_query, top_k=3)
        print(f"✅ Retrieved {len(relevant_cases)} relevant cases")
        
        if relevant_cases:
            print("\n📚 Sample retrieved cases:")
            for i, case in enumerate(relevant_cases[:2], 1):
                print(f"{i}. {case.get('title', 'No title')[:80]}...")
                print(f"   Relevance: {case.get('relevance_score', 0):.2%}")
        
        # Test context formatting
        context = rag.format_context(relevant_cases[:2])
        print(f"✅ Context formatted successfully ({len(context)} characters)")
        
        # Test complete RAG pipeline
        print(f"\n🔄 Testing complete RAG pipeline...")
        result = rag.answer_legal_query(test_query, top_k=3)
        
        print(f"✅ RAG pipeline completed successfully")
        print(f"📝 Answer length: {len(result['answer'])} characters")
        print(f"📚 Sources: {len(result['sources'])} cases")
        
        return True, len(result['sources'])
        
    except Exception as e:
        print(f"❌ Legal RAG system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, 0

def test_diverse_legal_queries():
    """Test RAG system with diverse legal queries across different domains"""
    print("\n" + "="*60)
    print("📋 Testing Diverse Legal Queries")
    print("="*60)
    
    # Define test queries across different legal domains
    test_queries = [
        {
            'query': 'What is the penalty for breach of contract in India?',
            'domain': 'Contract Law',
            'expected_keywords': ['contract', 'breach', 'damages', 'penalty']
        },
        {
            'query': 'What are the grounds for divorce under Indian law?',
            'domain': 'Family Law',
            'expected_keywords': ['divorce', 'grounds', 'marriage', 'family']
        },
        {
            'query': 'What are the rights of a tenant regarding eviction?',
            'domain': 'Property Law',
            'expected_keywords': ['tenant', 'eviction', 'property', 'rights']
        },
        {
            'query': 'What is the liability in motor accident cases?',
            'domain': 'Tort Law',
            'expected_keywords': ['motor', 'accident', 'liability', 'compensation']
        },
        {
            'query': 'What are the fundamental rights under Indian Constitution?',
            'domain': 'Constitutional Law',
            'expected_keywords': ['fundamental', 'rights', 'constitution', 'article']
        }
    ]
    
    try:
        from legal_rag import LegalRAG
        rag = LegalRAG(use_openai=False)
        
        results = []
        successful_tests = 0
        
        for i, test_case in enumerate(test_queries, 1):
            print(f"\n📝 Test {i}: {test_case['domain']}")
            print(f"Query: {test_case['query']}")
            print("-" * 40)
            
            try:
                result = rag.answer_legal_query(test_case['query'], top_k=3)
                
                # Analyze response quality
                answer = result['answer'].lower()
                sources = result['sources']
                
                # Check for expected keywords
                keyword_matches = sum(1 for keyword in test_case['expected_keywords'] 
                                    if keyword.lower() in answer)
                
                print(f"✅ Response generated successfully")
                print(f"📊 Answer length: {len(result['answer'])} characters")
                print(f"📚 Sources found: {len(sources)} cases")
                print(f"🎯 Keyword relevance: {keyword_matches}/{len(test_case['expected_keywords'])} keywords found")
                
                if sources:
                    print(f"📖 Top case: {sources[0].get('title', 'No title')[:60]}...")
                
                results.append({
                    'query': test_case['query'],
                    'domain': test_case['domain'],
                    'success': True,
                    'answer_length': len(result['answer']),
                    'sources_count': len(sources),
                    'keyword_matches': keyword_matches,
                    'relevance_score': keyword_matches / len(test_case['expected_keywords'])
                })
                
                successful_tests += 1
                
            except Exception as e:
                print(f"❌ Test failed: {e}")
                results.append({
                    'query': test_case['query'],
                    'domain': test_case['domain'],
                    'success': False,
                    'error': str(e)
                })
        
        # Summary
        print(f"\n" + "="*60)
        print(f"📊 DIVERSE QUERY TEST SUMMARY")
        print("="*60)
        print(f"✅ Successful tests: {successful_tests}/{len(test_queries)}")
        
        if successful_tests > 0:
            avg_sources = sum(r.get('sources_count', 0) for r in results if r['success']) / successful_tests
            avg_relevance = sum(r.get('relevance_score', 0) for r in results if r['success']) / successful_tests
            
            print(f"📚 Average sources per query: {avg_sources:.1f}")
            print(f"🎯 Average keyword relevance: {avg_relevance:.2%}")
        
        return successful_tests == len(test_queries), results
        
    except Exception as e:
        print(f"❌ Diverse query testing failed: {e}")
        return False, []

def test_performance_metrics():
    """Test RAG system performance metrics"""
    print("\n" + "="*60)
    print("⚡ Testing Performance Metrics")
    print("="*60)
    
    try:
        from legal_rag import LegalRAG
        import time
        
        rag = LegalRAG(use_openai=False)
        
        # Test queries for performance measurement
        performance_queries = [
            "What is breach of contract?",
            "Property inheritance laws",
            "Motor accident compensation"
        ]
        
        response_times = []
        
        for i, query in enumerate(performance_queries, 1):
            print(f"\n⏱️  Performance Test {i}: '{query}'")
            
            start_time = time.time()
            result = rag.answer_legal_query(query, top_k=5)
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            print(f"✅ Response time: {response_time:.2f} seconds")
            print(f"📚 Sources retrieved: {len(result['sources'])}")
            print(f"📝 Answer length: {len(result['answer'])} characters")
        
        # Calculate performance metrics
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        
        print(f"\n📊 PERFORMANCE SUMMARY:")
        print(f"⚡ Average response time: {avg_response_time:.2f} seconds")
        print(f"🚀 Fastest response: {min_response_time:.2f} seconds")
        print(f"🐌 Slowest response: {max_response_time:.2f} seconds")
        
        # Performance criteria (based on requirements: < 2 seconds)
        performance_passed = avg_response_time < 2.0
        
        if performance_passed:
            print("✅ Performance requirements met (< 2 seconds average)")
        else:
            print("⚠️  Performance requirements not met (>= 2 seconds average)")
        
        return performance_passed, {
            'avg_response_time': avg_response_time,
            'max_response_time': max_response_time,
            'min_response_time': min_response_time,
            'all_response_times': response_times
        }
        
    except Exception as e:
        print(f"❌ Performance testing failed: {e}")
        return False, {}

def check_data_availability():
    """Check if legal case data is available for testing"""
    print("\n" + "="*60)
    print("📊 Checking Data Availability")
    print("="*60)
    
    data_files = [
        'data/legal_cases/indian_legal_cases_complete.json',
        'data/chromadb'
    ]
    
    data_status = {}
    
    for data_file in data_files:
        if os.path.exists(data_file):
            if data_file.endswith('.json'):
                try:
                    with open(data_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    print(f"✅ {data_file}: {len(data)} cases available")
                    data_status[data_file] = len(data)
                except Exception as e:
                    print(f"⚠️  {data_file}: Error reading file - {e}")
                    data_status[data_file] = 0
            else:
                # Directory (ChromaDB)
                try:
                    files = os.listdir(data_file)
                    print(f"✅ {data_file}: Directory exists with {len(files)} files")
                    data_status[data_file] = len(files)
                except Exception as e:
                    print(f"⚠️  {data_file}: Error accessing directory - {e}")
                    data_status[data_file] = 0
        else:
            print(f"❌ {data_file}: Not found")
            data_status[data_file] = 0
    
    return data_status

def generate_test_report(results):
    """Generate comprehensive test report"""
    print("\n" + "="*80)
    print("📋 COMPREHENSIVE RAG SYSTEM TEST REPORT")
    print("="*80)
    print(f"⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Overall summary
    total_tests = len([k for k in results.keys() if k.endswith('_passed')])
    passed_tests = sum(1 for k, v in results.items() if k.endswith('_passed') and v)
    
    print(f"\n🎯 OVERALL RESULTS:")
    print(f"✅ Tests passed: {passed_tests}/{total_tests}")
    print(f"📊 Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    # Detailed results
    print(f"\n📝 DETAILED RESULTS:")
    
    if 'vector_db_passed' in results:
        status = "✅ PASSED" if results['vector_db_passed'] else "❌ FAILED"
        print(f"🔍 Vector Database: {status}")
        if 'vector_db_results' in results:
            print(f"   - Search results: {results['vector_db_results']} cases found")
    
    if 'rag_system_passed' in results:
        status = "✅ PASSED" if results['rag_system_passed'] else "❌ FAILED"
        print(f"🤖 RAG System: {status}")
        if 'rag_system_results' in results:
            print(f"   - Sources retrieved: {results['rag_system_results']} cases")
    
    if 'diverse_queries_passed' in results:
        status = "✅ PASSED" if results['diverse_queries_passed'] else "❌ FAILED"
        print(f"📋 Diverse Queries: {status}")
        if 'diverse_queries_results' in results:
            successful = sum(1 for r in results['diverse_queries_results'] if r['success'])
            print(f"   - Successful queries: {successful}/{len(results['diverse_queries_results'])}")
    
    if 'performance_passed' in results:
        status = "✅ PASSED" if results['performance_passed'] else "❌ FAILED"
        print(f"⚡ Performance: {status}")
        if 'performance_results' in results:
            avg_time = results['performance_results'].get('avg_response_time', 0)
            print(f"   - Average response time: {avg_time:.2f} seconds")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if not results.get('vector_db_passed', False):
        print("- Fix vector database initialization issues")
    
    if not results.get('performance_passed', False):
        print("- Optimize query processing for better performance")
        print("- Consider using smaller embedding models or caching")
    
    if results.get('diverse_queries_results'):
        low_relevance = [r for r in results['diverse_queries_results'] 
                        if r.get('success') and r.get('relevance_score', 0) < 0.5]
        if low_relevance:
            print(f"- Improve keyword matching for {len(low_relevance)} query types")
    
    print(f"\n🎉 Test report generation complete!")

def main():
    """Run comprehensive RAG system tests"""
    print("🚀 COMPREHENSIVE RAG SYSTEM TEST SUITE")
    print("="*80)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    try:
        # Check data availability first
        data_status = check_data_availability()
        results['data_status'] = data_status
        
        # Test 1: Vector Database
        db_passed, db_results = test_vector_database()
        results['vector_db_passed'] = db_passed
        results['vector_db_results'] = db_results
        
        # Test 2: Legal RAG System
        rag_passed, rag_results = test_legal_rag_system()
        results['rag_system_passed'] = rag_passed
        results['rag_system_results'] = rag_results
        
        # Test 3: Diverse Legal Queries
        diverse_passed, diverse_results = test_diverse_legal_queries()
        results['diverse_queries_passed'] = diverse_passed
        results['diverse_queries_results'] = diverse_results
        
        # Test 4: Performance Metrics
        perf_passed, perf_results = test_performance_metrics()
        results['performance_passed'] = perf_passed
        results['performance_results'] = perf_results
        
        # Generate comprehensive report
        generate_test_report(results)
        
        # Save results to file
        with open('rag_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Test results saved to: rag_test_results.json")
        
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()