"""
Test script to verify the RAG system is working correctly
"""

import requests
import json
from datetime import datetime

# Server URL
BASE_URL = "http://localhost:5000"

def test_health():
    """Test health endpoint to check ML system status"""
    print("\n" + "="*60)
    print("🔍 Testing System Health")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/api/health")
    data = response.json()
    
    print(f"\n✅ Status: {data['status']}")
    print(f"📡 AI Provider: {data['ai_provider']}")
    print(f"💾 Database: {data['database']}")
    print(f"\n🤖 ML System Status:")
    print(f"  - ML Available: {data['ml_system']['ml_available']}")
    print(f"  - RAG Initialized: {data['ml_system']['rag_initialized']}")
    print(f"\n🎯 Features:")
    for feature, enabled in data['features'].items():
        status = "✅" if enabled else "❌"
        print(f"  {status} {feature}")
    
    return data['ml_system']['rag_initialized']

def test_chat(question):
    """Test chat endpoint with a legal question"""
    print(f"\n📝 Question: {question}")
    print("-" * 60)
    
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={"message": question},
        headers={"Content-Type": "application/json"}
    )
    
    data = response.json()
    
    if data.get('success'):
        print(f"\n💬 Response:")
        print(data['response'][:500] + "..." if len(data['response']) > 500 else data['response'])
        
        sources = data.get('sources', [])
        if sources:
            print(f"\n📚 Case Citations ({len(sources)} cases):")
            for i, source in enumerate(sources[:3], 1):
                print(f"\n{i}. {source['title']}")
                print(f"   Court: {source['court']}")
                print(f"   Date: {source['date']}")
                print(f"   Relevance: {source['relevance']}")
        else:
            print("\n⚠️  No case citations (using basic fallback)")
        
        return True
    else:
        print(f"\n❌ Error: {data.get('error')}")
        return False

def test_case_search(query):
    """Test direct case search endpoint"""
    print(f"\n🔍 Searching cases for: {query}")
    print("-" * 60)
    
    response = requests.post(
        f"{BASE_URL}/api/search-cases",
        json={"query": query},
        headers={"Content-Type": "application/json"}
    )
    
    data = response.json()
    
    if data.get('success'):
        results = data.get('results', [])
        print(f"\n✅ Found {len(results)} matching cases:")
        
        for i, case in enumerate(results[:5], 1):
            print(f"\n{i}. {case['title']}")
            print(f"   Court: {case['court']}")
            print(f"   Date: {case['date']}")
            print(f"   Relevance: {case.get('relevance', 'N/A')}")
            print(f"   Excerpt: {case.get('excerpt', '')[:150]}...")
        
        return len(results) > 0
    else:
        print(f"\n❌ Search failed: {data.get('error')}")
        return False

def main():
    """Run all tests"""
    print("\n🚀 LegalCounsel AI - RAG System Test Suite")
    print("="*60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test 1: Health check
        rag_initialized = test_health()
        
        if not rag_initialized:
            print("\n⚠️  RAG system not initialized. Tests may use fallback responses.")
        
        # Test 2: Contract law question
        print("\n" + "="*60)
        print("📋 Test 1: Contract Breach Question")
        print("="*60)
        test_chat("What are the remedies for breach of contract under Indian law?")
        
        # Test 3: Property law question
        print("\n" + "="*60)
        print("📋 Test 2: Property Rights Question")
        print("="*60)
        test_chat("What are the rights of a tenant in India regarding eviction?")
        
        # Test 4: Constitutional rights
        print("\n" + "="*60)
        print("📋 Test 3: Constitutional Rights Question")
        print("="*60)
        test_chat("What are my fundamental rights under the Indian Constitution?")
        
        # Test 5: Direct case search (if ML available)
        if rag_initialized:
            print("\n" + "="*60)
            print("📋 Test 4: Direct Case Search")
            print("="*60)
            test_case_search("contract breach compensation")
        
        print("\n" + "="*60)
        print("✅ All Tests Completed!")
        print("="*60)
        print(f"⏰ Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
