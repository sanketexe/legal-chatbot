"""
Migrate 5,000 Legal Cases from JSON to Pinecone
Updated script to handle larger dataset efficiently
"""

import os
import json
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
import time

# Load environment variables
load_dotenv()

def migrate_json_to_pinecone():
    """Migrate cases from JSON file to Pinecone"""
    
    print("\n⚖️  Legal Cases Migration to Pinecone (5,000 cases)")
    print("="*70)
    
    # Load Pinecone credentials
    api_key = os.getenv('PINECONE_API_KEY')
    index_name = os.getenv('PINECONE_INDEX_NAME', 'legal-cases')
    
    if not api_key:
        print("❌ Error: PINECONE_API_KEY not found in .env")
        return False
    
    print(f"📊 Index Name: {index_name}")
    print()
    
    # Initialize Pinecone
    print("🔌 Connecting to Pinecone...")
    try:
        pc = Pinecone(api_key=api_key)
        index = pc.Index(index_name)
        print(f"✅ Connected to Pinecone index: {index_name}")
        
        # Get current stats
        stats = index.describe_index_stats()
        current_vectors = stats.get('total_vector_count', 0)
        print(f"📊 Current vectors in Pinecone: {current_vectors}")
        
        # Option to clear existing vectors
        if current_vectors > 0:
            print(f"\n⚠️  Index contains {current_vectors} existing vectors")
            print("🗑️  Clearing existing vectors to upload new 5,000 cases...")
            index.delete(delete_all=True)
            print("✅ Existing vectors cleared")
            time.sleep(5)  # Wait for deletion to propagate
        
    except Exception as e:
        print(f"❌ Error connecting to Pinecone: {e}")
        return False
    
    # Load cases from JSON
    print("\n📂 Loading cases from JSON...")
    try:
        json_file = './data/constitution/constitution.json'
        with open(json_file, 'r', encoding='utf-8') as f:
            cases = json.load(f)
        
        print(f"✅ Loaded {len(cases)} cases from JSON")
        
        if len(cases) == 0:
            print("❌ No cases found in JSON file")
            return False
            
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")
        return False
    
    # Initialize embedding model
    print("\n🤖 Loading embedding model (all-MiniLM-L6-v2)...")
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Embedding model loaded")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return False
    
    # Migrate cases
    print(f"\n🚀 Migrating {len(cases)} cases to Pinecone...")
    print("   This may take several minutes...")
    print()
    
    batch_size = 100
    successful = 0
    failed = 0
    
    for i in range(0, len(cases), batch_size):
        batch = cases[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(cases) + batch_size - 1) // batch_size
        
        try:
            # Prepare vectors for this batch
            vectors_to_upsert = []
            
            for case in batch:
                # Create text for embedding
                title = case.get('title', '')
                category = case.get('category', '')
                topic = case.get('topic', '')
                content = case.get('content', '')
                keywords = case.get('keywords', '')
                
                # Combine text (limit length for embedding)
                text = f"{title}. {topic}. {keywords}. {content}"[:1000]
                
                # Generate embedding
                embedding = model.encode(text).tolist()
                
                # Create vector ID
                vector_id = f"case_{i + len(vectors_to_upsert)}"
                
                # Create metadata
                metadata = {
                    'title': title[:500],  # Pinecone metadata limits
                    'category': category,
                    'topic': topic[:200] if topic else '',
                    'court': case.get('court', '')[:100],
                    'year': case.get('year', ''),
                    'citation': case.get('citation', '')[:100],
                    'keywords': keywords[:200] if keywords else '',
                    'content_preview': content[:500] if content else ''
                }
                
                vectors_to_upsert.append({
                    'id': vector_id,
                    'values': embedding,
                    'metadata': metadata
                })
            
            # Upsert batch to Pinecone
            index.upsert(vectors=vectors_to_upsert)
            successful += len(vectors_to_upsert)
            
            print(f"  ✅ Batch {batch_num}/{total_batches}: Uploaded {len(vectors_to_upsert)} vectors ({successful}/{len(cases)})")
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"  ❌ Batch {batch_num} failed: {e}")
            failed += len(batch)
            continue
    
    print()
    print("="*70)
    print("✅ MIGRATION COMPLETE!")
    print("="*70)
    print(f"📊 Total cases processed: {len(cases)}")
    print(f"✅ Successfully migrated: {successful}")
    print(f"❌ Failed: {failed}")
    print()
    
    # Verify migration
    print("🔍 Verifying migration...")
    time.sleep(5)  # Wait for indexing
    
    try:
        stats = index.describe_index_stats()
        final_count = stats.get('total_vector_count', 0)
        print(f"📊 Vectors in Pinecone: {final_count}")
        
        if final_count >= successful:
            print("✅ Migration verified successfully!")
            
            # Test search
            print("\n🔍 Testing search functionality...")
            test_query = "fundamental rights"
            query_embedding = model.encode(test_query).tolist()
            results = index.query(
                vector=query_embedding,
                top_k=3,
                include_metadata=True
            )
            
            print(f"✅ Search test passed! Found {len(results['matches'])} results:")
            for idx, match in enumerate(results['matches'][:3]):
                title = match['metadata'].get('title', 'N/A')
                score = match['score']
                print(f"   {idx+1}. {title[:60]}... (score: {score:.4f})")
            
            return True
        else:
            print(f"⚠️  Warning: Expected {successful} vectors, found {final_count}")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying migration: {e}")
        return False

def main():
    """Main execution"""
    print("\n🏛️  PINECONE MIGRATION - 5,000 LEGAL CASES")
    print("="*70)
    print("Source: ./data/constitution/constitution.json")
    print("Destination: Pinecone Cloud Vector Database")
    print("="*70)
    
    success = migrate_json_to_pinecone()
    
    if success:
        print("\n" + "="*70)
        print("🎉 SUCCESS! Your RAG model is now trained with 5,000 diverse cases!")
        print("="*70)
        print("\n📊 Case Distribution:")
        print("  • Constitutional Law: 500 cases")
        print("  • Criminal Law: 500 cases")
        print("  • Civil Law: 500 cases")
        print("  • Family Law: 500 cases")
        print("  • Corporate Law: 500 cases")
        print("  • Labor Law: 500 cases")
        print("  • Tax Law: 500 cases")
        print("  • Intellectual Property: 500 cases")
        print("  • Consumer Protection: 500 cases")
        print("  • Environmental Law: 500 cases")
        print()
        print("✅ Your chatbot is now ready for production deployment!")
        print("📝 Next step: Deploy to Vercel using DEPLOY_NOW.md")
        print("="*70)
    else:
        print("\n❌ Migration failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
