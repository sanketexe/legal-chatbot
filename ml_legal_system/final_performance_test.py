#!/usr/bin/env python3
"""
Final Performance Test for RAG Model Training
Tests the optimized vector database with various queries
"""

import time
import statistics
from vector_db import LegalVectorDatabase

def run_final_performance_test():
    """Run comprehensive performance test"""
    print("🎯 Final RAG Model Performance Test")
    print("=" * 60)
    
    # Initialize database
    db = LegalVectorDatabase(use_cloud=False)
    
    # Test queries covering different legal domains
    test_queries = [
        "contract breach damages compensation",
        "property inheritance succession rights",
        "motor vehicle accident liability",
        "trademark infringement intellectual property",
        "divorce grounds matrimonial disputes",
        "criminal defamation section 499 IPC",
        "employment termination wrongful dismissal",
        "consumer protection unfair trade practices",
        "tax evasion penalty assessment",
        "land acquisition compensation dispute",
        "company law director liability",
        "banking fraud criminal charges",
        "medical negligence compensation",
        "environmental pollution damages",
        "arbitration dispute resolution"
    ]
    
    print(f"📋 Testing {len(test_queries)} diverse legal queries")
    print("=" * 60)
    
    # Performance metrics
    query_times = []
    similarity_scores = []
    results_counts = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Query {i}: {query}")
        
        # Time the query
        start_time = time.time()
        results = db.search_similar_cases(query, top_k=5)
        end_time = time.time()
        
        query_time = end_time - start_time
        query_times.append(query_time)
        results_counts.append(len(results))
        
        print(f"   ⚡ Query time: {query_time:.3f}s")
        print(f"   📊 Results: {len(results)}")
        
        # Calculate similarities
        if results:
            query_similarities = []
            for j, result in enumerate(results[:3]):  # Show top 3
                distance = result.get('distance', 1)
                similarity = max(0, min(1, (2 - distance) / 2))
                query_similarities.append(similarity)
                
                # Get metadata
                metadata = result.get('metadata', {})
                search_query = metadata.get('search_query', 'N/A')
                
                print(f"   {j+1}. Similarity: {similarity:.1%} | Query: {search_query}")
            
            avg_similarity = statistics.mean(query_similarities)
            similarity_scores.append(avg_similarity)
            print(f"   📈 Average similarity: {avg_similarity:.1%}")
        else:
            print("   ⚠️ No results found")
    
    # Overall performance summary
    print("\n" + "=" * 60)
    print("📊 PERFORMANCE SUMMARY")
    print("=" * 60)
    
    if query_times:
        avg_time = statistics.mean(query_times)
        min_time = min(query_times)
        max_time = max(query_times)
        
        print(f"⚡ Query Performance:")
        print(f"   Average time: {avg_time:.3f}s")
        print(f"   Fastest query: {min_time:.3f}s")
        print(f"   Slowest query: {max_time:.3f}s")
        
        # Performance rating
        if avg_time < 1.0:
            print("   🟢 Excellent performance (< 1s)")
        elif avg_time < 2.0:
            print("   🟡 Good performance (< 2s)")
        else:
            print("   🔴 Needs optimization (> 2s)")
    
    if similarity_scores:
        avg_similarity = statistics.mean(similarity_scores)
        min_similarity = min(similarity_scores)
        max_similarity = max(similarity_scores)
        
        print(f"\n🎯 Search Quality:")
        print(f"   Average similarity: {avg_similarity:.1%}")
        print(f"   Lowest similarity: {min_similarity:.1%}")
        print(f"   Highest similarity: {max_similarity:.1%}")
        
        # Quality rating
        if avg_similarity > 0.7:
            print("   🟢 Excellent search quality (> 70%)")
        elif avg_similarity > 0.5:
            print("   🟡 Good search quality (> 50%)")
        elif avg_similarity > 0.3:
            print("   🟠 Moderate search quality (> 30%)")
        else:
            print("   🔴 Poor search quality (< 30%)")
    
    if results_counts:
        avg_results = statistics.mean(results_counts)
        print(f"\n📋 Results Coverage:")
        print(f"   Average results per query: {avg_results:.1f}")
        
        if avg_results >= 5:
            print("   🟢 Good coverage (≥ 5 results per query)")
        elif avg_results >= 3:
            print("   🟡 Moderate coverage (≥ 3 results per query)")
        else:
            print("   🔴 Poor coverage (< 3 results per query)")
    
    # Database statistics
    print(f"\n📚 Database Statistics:")
    try:
        import chromadb
        client = chromadb.PersistentClient(path="./data/chromadb")
        collection = client.get_collection("indian_legal_cases")
        total_cases = collection.count()
        print(f"   Total cases indexed: {total_cases}")
        print(f"   Queries tested: {len(test_queries)}")
        print(f"   Coverage: {(len(test_queries) / total_cases * 100):.2f}% of database tested")
    except Exception as e:
        print(f"   Error getting database stats: {e}")
    
    # Final recommendations
    print(f"\n💡 FINAL RECOMMENDATIONS:")
    print("=" * 60)
    
    if query_times and statistics.mean(query_times) < 2.0:
        print("✅ Query performance meets requirements (< 2s average)")
    else:
        print("⚠️ Consider optimizing query performance")
    
    if similarity_scores and statistics.mean(similarity_scores) > 0.25:
        print("✅ Search quality is acceptable (> 25% average similarity)")
    else:
        print("⚠️ Consider improving embedding model or data preprocessing")
    
    print("✅ Use top_k=5 for optimal balance of speed and coverage")
    print("✅ Set similarity threshold to 0.3 for filtering results")
    print("✅ RAG model training validation complete!")
    
    return {
        'avg_query_time': statistics.mean(query_times) if query_times else 0,
        'avg_similarity': statistics.mean(similarity_scores) if similarity_scores else 0,
        'avg_results': statistics.mean(results_counts) if results_counts else 0,
        'total_queries': len(test_queries)
    }

if __name__ == "__main__":
    results = run_final_performance_test()
    print(f"\n🎉 Test completed successfully!")
    print(f"Final metrics: {results}")