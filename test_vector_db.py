#!/usr/bin/env python3
"""
Test script to validate ChromaDB vector database functionality
"""

import sys
import os
sys.path.append('ml_legal_system')

from vector_db import LegalVectorDatabase

def test_database():
    """Test the vector database functionality"""
    print("🧪 Testing Vector Database")
    print("=" * 60)
    
    # Initialize database
    db = LegalVectorDatabase(use_cloud=False)
    
    # Test search with a legal query
    test_query = "contract breach damages"
    print(f"🔍 Testing search: '{test_query}'")
    
    results = db.search_similar_cases(test_query, top_k=5)
    
    print(f"\n📊 Found {len(results)} relevant cases:")
    
    for i, case in enumerate(results, 1):
        print(f"\n{i}. ID: {case.get('id', 'N/A')}")
        
        # Check if metadata exists
        metadata = case.get('metadata', {})
        if metadata:
            title = metadata.get('title', 'No title')[:100]
            court = metadata.get('court', 'No court')
            date = metadata.get('date', 'No date')
            print(f"   Title: {title}")
            print(f"   Court: {court}")
            print(f"   Date: {date}")
        else:
            print("   No metadata found")
            
        # Check document content
        document = case.get('document', '')
        if document:
            print(f"   Document preview: {document[:150]}...")
        else:
            print("   No document content")
            
        distance = case.get('distance', 0)
        # Convert distance to similarity (ChromaDB uses cosine distance)
        # For cosine distance, similarity = (2 - distance) / 2, clamped to [0, 1]
        similarity = max(0, min(1, (2 - distance) / 2))
        print(f"   Similarity: {similarity:.2%}")
    
    # Test database statistics
    print(f"\n📈 Database Statistics:")
    try:
        import chromadb
        client = chromadb.PersistentClient(path="./data/chromadb")
        collection = client.get_collection("indian_legal_cases")
        count = collection.count()
        print(f"   Total cases indexed: {count}")
        
        # Get a sample case to check structure
        sample = collection.get(limit=1, include=['metadatas', 'documents'])
        if sample['ids']:
            print(f"   Sample case ID: {sample['ids'][0]}")
            if sample['metadatas'] and sample['metadatas'][0]:
                print(f"   Sample metadata keys: {list(sample['metadatas'][0].keys())}")
            if sample['documents'] and sample['documents'][0]:
                print(f"   Sample document length: {len(sample['documents'][0])} chars")
        
    except Exception as e:
        print(f"   Error getting statistics: {e}")

if __name__ == "__main__":
    test_database()