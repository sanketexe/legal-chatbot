#!/usr/bin/env python3
"""
Migration script to transfer vectors from local ChromaDB to Pinecone cloud
This will upload your 1,422 legal cases to Pinecone for production deployment
"""

import os
import sys
from dotenv import load_dotenv
import chromadb
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
import time

# Load environment variables
load_dotenv()

def migrate_chromadb_to_pinecone():
    """Migrate all vectors from ChromaDB to Pinecone"""
    
    print("🔄 Starting migration from ChromaDB to Pinecone...")
    print("=" * 60)
    
    # Get Pinecone credentials
    api_key = os.getenv('PINECONE_API_KEY')
    index_name = os.getenv('PINECONE_INDEX_NAME', 'legal-cases')
    region = os.getenv('PINECONE_REGION', 'us-east-1')
    
    if not api_key:
        print("❌ ERROR: PINECONE_API_KEY not found in .env file")
        return False
    
    print(f"📊 Index Name: {index_name}")
    print(f"🌍 Region: {region}")
    print()
    
    # Initialize Pinecone
    print("🔌 Connecting to Pinecone...")
    try:
        pc = Pinecone(api_key=api_key)
        
        # Check if index exists
        existing_indexes = pc.list_indexes()
        index_names = [idx['name'] for idx in existing_indexes]
        
        if index_name not in index_names:
            print(f"❌ ERROR: Index '{index_name}' not found in Pinecone")
            print(f"   Available indexes: {index_names}")
            return False
        
        # Connect to index
        index = pc.Index(index_name)
        print(f"✅ Connected to Pinecone index: {index_name}")
        
        # Get index stats
        stats = index.describe_index_stats()
        print(f"📊 Current vectors in Pinecone: {stats['total_vector_count']}")
        print()
        
    except Exception as e:
        print(f"❌ ERROR connecting to Pinecone: {e}")
        return False
    
    # Initialize ChromaDB
    print("📂 Loading ChromaDB...")
    try:
        chroma_client = chromadb.PersistentClient(path="./data/chromadb")
        collection = chroma_client.get_collection(name="indian_legal_cases")
        
        # Get all vectors from ChromaDB
        results = collection.get(include=['embeddings', 'documents', 'metadatas'])
        
        total_vectors = len(results['ids'])
        print(f"✅ Found {total_vectors} vectors in ChromaDB")
        print()
        
        if total_vectors == 0:
            print("⚠️  WARNING: No vectors found in ChromaDB")
            print("   Make sure you have loaded legal cases first")
            return False
        
    except Exception as e:
        print(f"❌ ERROR loading ChromaDB: {e}")
        print("   Make sure ChromaDB data exists in ./data/chromadb")
        return False
    
    # Migrate vectors to Pinecone
    print(f"🚀 Migrating {total_vectors} vectors to Pinecone...")
    print("   This may take a few minutes...")
    print()
    
    batch_size = 100
    successful = 0
    failed = 0
    
    try:
        for i in range(0, total_vectors, batch_size):
            batch_end = min(i + batch_size, total_vectors)
            batch_ids = results['ids'][i:batch_end]
            batch_embeddings = results['embeddings'][i:batch_end]
            batch_documents = results['documents'][i:batch_end]
            batch_metadatas = results['metadatas'][i:batch_end] if results['metadatas'] else [{}] * len(batch_ids)
            
            # Prepare vectors for Pinecone
            vectors_to_upsert = []
            for j, vec_id in enumerate(batch_ids):
                # Add document text to metadata
                metadata = batch_metadatas[j].copy() if batch_metadatas[j] else {}
                metadata['text'] = batch_documents[j][:1000]  # Limit text size
                
                vectors_to_upsert.append({
                    'id': vec_id,
                    'values': batch_embeddings[j],
                    'metadata': metadata
                })
            
            # Upsert to Pinecone
            try:
                index.upsert(vectors=vectors_to_upsert)
                successful += len(vectors_to_upsert)
                progress = (batch_end / total_vectors) * 100
                print(f"   ✓ Uploaded {batch_end}/{total_vectors} vectors ({progress:.1f}%)")
                
            except Exception as e:
                print(f"   ✗ Failed batch {i}-{batch_end}: {e}")
                failed += len(vectors_to_upsert)
            
            # Small delay to avoid rate limits
            time.sleep(0.1)
        
        print()
        print("=" * 60)
        print(f"✅ Migration complete!")
        print(f"   Successful: {successful} vectors")
        print(f"   Failed: {failed} vectors")
        print()
        
        # Verify migration
        print("🔍 Verifying migration...")
        time.sleep(2)  # Wait for Pinecone to update stats
        stats = index.describe_index_stats()
        print(f"📊 Total vectors in Pinecone: {stats['total_vector_count']}")
        
        if stats['total_vector_count'] >= total_vectors:
            print("✅ Migration verified successfully!")
            return True
        else:
            print(f"⚠️  WARNING: Expected {total_vectors} but found {stats['total_vector_count']}")
            return False
        
    except Exception as e:
        print(f"❌ ERROR during migration: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pinecone_search():
    """Test search functionality in Pinecone"""
    print()
    print("=" * 60)
    print("🧪 Testing Pinecone search...")
    
    try:
        # Initialize
        api_key = os.getenv('PINECONE_API_KEY')
        index_name = os.getenv('PINECONE_INDEX_NAME', 'legal-cases')
        
        pc = Pinecone(api_key=api_key)
        index = pc.Index(index_name)
        
        # Load embedding model
        print("📥 Loading embedding model...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Test query
        test_query = "contract breach"
        print(f"🔍 Searching for: '{test_query}'")
        
        query_embedding = model.encode(test_query).tolist()
        
        # Search
        results = index.query(
            vector=query_embedding,
            top_k=3,
            include_metadata=True
        )
        
        print(f"\n✅ Found {len(results['matches'])} results:")
        for i, match in enumerate(results['matches'], 1):
            print(f"\n{i}. Score: {match['score']:.4f}")
            print(f"   ID: {match['id']}")
            if 'metadata' in match and 'text' in match['metadata']:
                text_preview = match['metadata']['text'][:200]
                print(f"   Text: {text_preview}...")
        
        print("\n✅ Pinecone search is working!")
        return True
        
    except Exception as e:
        print(f"❌ ERROR testing search: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print()
    print("⚖️  Legal Cases Migration to Pinecone")
    print("=" * 60)
    print()
    
    # Check environment variables
    if not os.getenv('PINECONE_API_KEY'):
        print("❌ ERROR: PINECONE_API_KEY not set in .env file")
        sys.exit(1)
    
    # Run migration
    if migrate_chromadb_to_pinecone():
        print()
        # Test search
        test_pinecone_search()
        print()
        print("=" * 60)
        print("🎉 All done! Your vectors are now in Pinecone cloud!")
        print("   Next step: Update your code to use Pinecone instead of ChromaDB")
        print("=" * 60)
    else:
        print()
        print("=" * 60)
        print("❌ Migration failed. Please check the errors above.")
        print("=" * 60)
        sys.exit(1)
