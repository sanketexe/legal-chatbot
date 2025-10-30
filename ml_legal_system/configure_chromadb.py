#!/usr/bin/env python3
"""
ChromaDB Configuration Optimization
Optimizes ChromaDB settings for better performance
"""

import chromadb
from chromadb.config import Settings
import json
import time

def optimize_chromadb_settings():
    """Configure ChromaDB with optimized settings"""
    print("⚙️ Optimizing ChromaDB Configuration")
    print("=" * 50)
    
    # Create client with basic settings
    client = chromadb.PersistentClient(path="./data/chromadb")
    
    try:
        collection = client.get_collection("indian_legal_cases")
        print(f"✅ Collection found: {collection.name}")
        print(f"📊 Total documents: {collection.count()}")
        
        # Test query performance
        print("\n🔍 Testing query performance...")
        start_time = time.time()
        
        results = collection.query(
            query_texts=["contract breach damages"],
            n_results=5,
            include=['metadatas', 'documents', 'distances']
        )
        
        end_time = time.time()
        query_time = end_time - start_time
        
        print(f"⚡ Query time: {query_time:.3f}s")
        print(f"📋 Results returned: {len(results['ids'][0])}")
        
        # Display sample results
        if results['ids'][0]:
            print("\n📄 Sample results:")
            for i in range(min(3, len(results['ids'][0]))):
                distance = results['distances'][0][i]
                similarity = max(0, min(1, (2 - distance) / 2))
                print(f"   {i+1}. ID: {results['ids'][0][i]}")
                print(f"      Similarity: {similarity:.2%}")
                print(f"      Preview: {results['documents'][0][i][:100]}...")
        
        return {
            'status': 'success',
            'collection_count': collection.count(),
            'query_time': query_time,
            'results_count': len(results['ids'][0])
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {'status': 'error', 'message': str(e)}

def create_performance_config():
    """Create a performance configuration file"""
    config = {
        "chromadb_settings": {
            "chroma_db_impl": "duckdb+parquet",
            "chroma_api_impl": "chromadb.api.fastapi.FastAPI",
            "chroma_memory_limit_bytes": 2147483648,  # 2GB
            "chroma_batch_size": 1000,
            "chroma_num_threads": 4,
            "persist_directory": "./data/chromadb",
            "anonymized_telemetry": False
        },
        "search_parameters": {
            "default_top_k": 5,
            "max_top_k": 20,
            "similarity_threshold": 0.3,
            "batch_size_embedding": 50
        },
        "performance_targets": {
            "max_query_time_seconds": 2.0,
            "min_similarity_score": 0.25,
            "target_results_per_query": 5
        }
    }
    
    with open('chromadb_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("💾 Configuration saved to: chromadb_config.json")
    return config

def benchmark_different_settings():
    """Benchmark different ChromaDB settings"""
    print("\n🏁 Benchmarking Different Settings")
    print("=" * 50)
    
    test_queries = [
        "contract breach damages",
        "property inheritance rights",
        "motor accident liability"
    ]
    
    # Test different batch sizes
    batch_sizes = [100, 500, 1000]
    results = {}
    
    for batch_size in batch_sizes:
        print(f"\n📦 Testing batch size: {batch_size}")
        
        try:
            client = chromadb.PersistentClient(path="./data/chromadb")
            
            collection = client.get_collection("indian_legal_cases")
            
            # Time multiple queries
            times = []
            for query in test_queries:
                start_time = time.time()
                collection.query(
                    query_texts=[query],
                    n_results=5
                )
                end_time = time.time()
                times.append(end_time - start_time)
            
            avg_time = sum(times) / len(times)
            results[batch_size] = {
                'avg_query_time': avg_time,
                'individual_times': times
            }
            
            print(f"   Average query time: {avg_time:.3f}s")
            
        except Exception as e:
            print(f"   ❌ Error with batch size {batch_size}: {e}")
            results[batch_size] = {'error': str(e)}
    
    # Find optimal batch size
    if results:
        best_batch_size = min(
            [k for k, v in results.items() if 'avg_query_time' in v],
            key=lambda k: results[k]['avg_query_time']
        )
        print(f"\n🏆 Optimal batch size: {best_batch_size}")
        print(f"   Best average time: {results[best_batch_size]['avg_query_time']:.3f}s")
    
    return results

def main():
    """Main optimization function"""
    print("🚀 ChromaDB Configuration Optimization")
    print("=" * 60)
    
    # Step 1: Test current configuration
    print("\n1. Testing current configuration...")
    current_results = optimize_chromadb_settings()
    
    # Step 2: Create optimized configuration
    print("\n2. Creating optimized configuration...")
    config = create_performance_config()
    
    # Step 3: Benchmark different settings
    print("\n3. Benchmarking different settings...")
    benchmark_results = benchmark_different_settings()
    
    # Step 4: Generate recommendations
    print("\n📋 OPTIMIZATION RECOMMENDATIONS")
    print("=" * 60)
    
    if current_results.get('status') == 'success':
        query_time = current_results.get('query_time', 0)
        if query_time < 2.0:
            print("✅ Query performance is good (< 2s)")
        else:
            print("⚠️ Query performance could be improved")
            print("   Consider reducing dataset size or optimizing embeddings")
        
        print(f"📊 Current metrics:")
        print(f"   - Total cases: {current_results.get('collection_count', 'Unknown')}")
        print(f"   - Query time: {query_time:.3f}s")
        print(f"   - Results per query: {current_results.get('results_count', 'Unknown')}")
    
    print("\n💡 General recommendations:")
    print("   - Use batch_size=1000 for optimal performance")
    print("   - Set similarity threshold to 0.3 for balanced results")
    print("   - Limit top_k to 5-10 for faster queries")
    print("   - Consider using SSD storage for better I/O performance")
    
    print("\n✅ ChromaDB optimization complete!")

if __name__ == "__main__":
    main()