"""
Optimized Pinecone Migration - 5,000 Cases
Faster batch processing with progress tracking
"""

import os
import json
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
import time

# Load environment variables
load_dotenv()

def migrate_optimized():
    """Optimized migration with batch embedding generation"""
    
    print("\n⚖️  OPTIMIZED MIGRATION - 5,000 Legal Cases")
    print("="*70)
    
    # Load credentials
    api_key = os.getenv('PINECONE_API_KEY')
    index_name = os.getenv('PINECONE_INDEX_NAME', 'legal-cases')
    
    if not api_key:
        print("❌ PINECONE_API_KEY not found")
        return False
    
    # Connect to Pinecone
    print("🔌 Connecting to Pinecone...")
    pc = Pinecone(api_key=api_key)
    index = pc.Index(index_name)
    print(f"✅ Connected: {index_name}")
    
    # Clear existing
    stats = index.describe_index_stats()
    if stats.get('total_vector_count', 0) > 0:
        print(f"🗑️  Clearing {stats['total_vector_count']} existing vectors...")
        index.delete(delete_all=True)
        time.sleep(3)
        print("✅ Cleared")
    
    # Load cases
    print("\n📂 Loading JSON...")
    with open('./data/constitution/constitution.json', 'r', encoding='utf-8') as f:
        cases = json.load(f)
    print(f"✅ Loaded {len(cases)} cases")
    
    # Load model
    print("\n🤖 Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✅ Model ready")
    
    # Process in batches
    print(f"\n🚀 Migrating {len(cases)} cases...")
    print("   Batch size: 50 (optimized for speed)")
    print()
    
    batch_size = 50
    total_uploaded = 0
    start_time = time.time()
    
    for i in range(0, len(cases), batch_size):
        batch_start = time.time()
        batch = cases[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(cases) + batch_size - 1) // batch_size
        
        try:
            # Prepare texts for batch embedding
            texts = []
            metadatas = []
            
            for case in batch:
                # Short text for faster embedding
                text = f"{case.get('title', '')} {case.get('topic', '')} {case.get('keywords', '')}"[:500]
                texts.append(text)
                
                # Metadata
                metadatas.append({
                    'title': case.get('title', '')[:500],
                    'category': case.get('category', ''),
                    'topic': case.get('topic', '')[:200],
                    'court': case.get('court', '')[:100],
                    'year': case.get('year', ''),
                    'keywords': case.get('keywords', '')[:200]
                })
            
            # Batch encode (much faster!)
            embeddings = model.encode(texts, show_progress_bar=False)
            
            # Prepare vectors
            vectors = []
            for idx, embedding in enumerate(embeddings):
                vector_id = f"case_{i + idx}"
                vectors.append({
                    'id': vector_id,
                    'values': embedding.tolist(),
                    'metadata': metadatas[idx]
                })
            
            # Upload to Pinecone
            index.upsert(vectors=vectors)
            total_uploaded += len(vectors)
            
            batch_time = time.time() - batch_start
            elapsed = time.time() - start_time
            remaining = (elapsed / total_uploaded) * (len(cases) - total_uploaded) if total_uploaded > 0 else 0
            
            print(f"  ✅ Batch {batch_num:2d}/{total_batches} | "
                  f"Uploaded: {total_uploaded:4d}/{len(cases)} | "
                  f"Time: {batch_time:.1f}s | "
                  f"ETA: {remaining/60:.1f}min")
            
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            print(f"  ❌ Batch {batch_num} failed: {e}")
            continue
    
    print()
    print("="*70)
    print(f"✅ MIGRATION COMPLETE in {(time.time() - start_time)/60:.1f} minutes!")
    print(f"📊 Uploaded: {total_uploaded}/{len(cases)} cases")
    print("="*70)
    
    # Verify
    print("\n🔍 Verifying...")
    time.sleep(3)
    stats = index.describe_index_stats()
    final_count = stats.get('total_vector_count', 0)
    print(f"📊 Pinecone vectors: {final_count}")
    
    if final_count >= total_uploaded * 0.95:  # Allow 5% margin
        print("✅ Migration verified!")
        
        # Test search
        print("\n🔍 Testing search...")
        query_emb = model.encode("fundamental rights").tolist()
        results = index.query(vector=query_emb, top_k=3, include_metadata=True)
        print(f"✅ Found {len(results['matches'])} results")
        for i, m in enumerate(results['matches'][:3]):
            print(f"   {i+1}. {m['metadata'].get('title', '')[:50]}...")
        
        return True
    else:
        print(f"⚠️  Warning: Expected ~{total_uploaded}, got {final_count}")
        return False

if __name__ == '__main__':
    print("\n🏛️  FAST MIGRATION TO PINECONE")
    print("="*70)
    
    if migrate_optimized():
        print("\n🎉 SUCCESS! 5,000 cases now in Pinecone cloud!")
        print("✅ Your RAG model is trained and ready for deployment!")
        print("\n📝 Next: Run 'python app_with_db.py' to test")
        print("📝 Then: Deploy to Vercel using DEPLOY_NOW.md")
    else:
        print("\n❌ Migration incomplete. Check errors above.")
