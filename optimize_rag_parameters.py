"""
RAG System Parameter Optimization Script
Fine-tunes similarity thresholds and performance parameters
"""

import os
import sys
import json
import time
import numpy as np
from typing import List, Dict

# Add ml_legal_system to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ml_legal_system'))

from vector_db import LegalVectorDatabase
from optimized_legal_rag import OptimizedLegalRAG


def analyze_vector_database():
    """Analyze the vector database to understand data distribution"""
    print("\n" + "="*60)
    print("📊 Analyzing Vector Database")
    print("="*60)
    
    try:
        db = LegalVectorDatabase(use_cloud=False)
        
        # Test with various queries to understand similarity distribution
        test_queries = [
            "contract breach",
            "property rights",
            "divorce grounds",
            "motor accident",
            "constitutional rights",
            "criminal law",
            "employment law",
            "consumer protection"
        ]
        
        all_distances = []
        query_results = {}
        
        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            
            try:
                results = db.search_similar_cases(query, top_k=10)
                distances = [r.get('distance', 1.0) for r in results]
                similarities = [1 - d for d in distances]
                
                if similarities:
                    all_distances.extend(distances)
                    query_results[query] = {
                        'results_count': len(results),
                        'avg_similarity': np.mean(similarities),
                        'max_similarity': np.max(similarities),
                        'min_similarity': np.min(similarities),
                        'similarities': similarities[:5]  # Top 5
                    }
                    
                    print(f"   📈 Results: {len(results)}")
                    print(f"   📊 Avg similarity: {np.mean(similarities):.2%}")
                    print(f"   🎯 Max similarity: {np.max(similarities):.2%}")
                else:
                    query_results[query] = {'results_count': 0}
                    print(f"   ❌ No results found")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                query_results[query] = {'error': str(e)}
        
        # Analyze overall distribution
        if all_distances:
            all_similarities = [1 - d for d in all_distances]
            
            print(f"\n📊 OVERALL SIMILARITY ANALYSIS:")
            print(f"   📈 Total results analyzed: {len(all_similarities)}")
            print(f"   📊 Average similarity: {np.mean(all_similarities):.2%}")
            print(f"   📊 Median similarity: {np.median(all_similarities):.2%}")
            print(f"   🎯 Max similarity: {np.max(all_similarities):.2%}")
            print(f"   🎯 Min similarity: {np.min(all_similarities):.2%}")
            print(f"   📊 Std deviation: {np.std(all_similarities):.2%}")
            
            # Suggest optimal thresholds
            percentiles = [10, 25, 50, 75, 90]
            print(f"\n📊 SIMILARITY PERCENTILES:")
            for p in percentiles:
                value = np.percentile(all_similarities, p)
                print(f"   {p}th percentile: {value:.2%}")
            
            # Recommend threshold
            recommended_threshold = np.percentile(all_similarities, 25)  # 25th percentile
            print(f"\n💡 RECOMMENDED THRESHOLD: {recommended_threshold:.2%}")
            
            return {
                'recommended_threshold': recommended_threshold,
                'query_results': query_results,
                'overall_stats': {
                    'mean': np.mean(all_similarities),
                    'median': np.median(all_similarities),
                    'std': np.std(all_similarities),
                    'min': np.min(all_similarities),
                    'max': np.max(all_similarities)
                }
            }
        else:
            print("\n❌ No similarity data collected")
            return None
            
    except Exception as e:
        print(f"❌ Database analysis failed: {e}")
        return None


def optimize_rag_system():
    """Optimize RAG system parameters based on analysis"""
    print("\n" + "="*60)
    print("🎯 Optimizing RAG System Parameters")
    print("="*60)
    
    # First analyze the database
    analysis = analyze_vector_database()
    
    if not analysis:
        print("❌ Cannot optimize without database analysis")
        return None
    
    # Initialize RAG with recommended threshold
    rag = OptimizedLegalRAG(use_openai=False)
    rag.similarity_threshold = analysis['recommended_threshold']
    
    print(f"\n🔧 Using optimized threshold: {rag.similarity_threshold:.2%}")
    
    # Test queries for comprehensive evaluation
    test_queries = [
        "What is the penalty for breach of contract in India?",
        "What are the grounds for divorce under Indian law?",
        "What are the rights of a tenant regarding eviction?",
        "What is the liability in motor accident cases?",
        "What are the fundamental rights under Indian Constitution?",
        "How to file a consumer complaint?",
        "What is the process for property registration?",
        "Employment termination laws in India"
    ]
    
    print(f"\n⚡ Testing with {len(test_queries)} diverse queries...")
    
    results = []
    total_start = time.time()
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}/{len(test_queries)}: {query[:50]}...")
        
        try:
            start_time = time.time()
            result = rag.answer_legal_query(query, top_k=5)
            end_time = time.time()
            
            response_time = end_time - start_time
            sources_count = len(result['sources'])
            
            # Calculate relevance score based on sources found
            if sources_count > 0:
                avg_relevance = np.mean([s['relevance_score'] for s in result['sources']])
                relevance_score = avg_relevance
            else:
                relevance_score = 0.0
            
            test_result = {
                'query': query,
                'response_time': response_time,
                'sources_count': sources_count,
                'relevance_score': relevance_score,
                'answer_length': len(result['answer']),
                'success': sources_count > 0
            }
            
            results.append(test_result)
            
            print(f"   ⏱️  Time: {response_time:.2f}s")
            print(f"   📚 Sources: {sources_count}")
            print(f"   🎯 Relevance: {relevance_score:.1%}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                'query': query,
                'error': str(e),
                'success': False
            })
    
    total_time = time.time() - total_start
    
    # Calculate optimization metrics
    successful_queries = [r for r in results if r.get('success', False)]
    
    if successful_queries:
        avg_response_time = np.mean([r['response_time'] for r in successful_queries])
        avg_sources = np.mean([r['sources_count'] for r in successful_queries])
        avg_relevance = np.mean([r['relevance_score'] for r in successful_queries])
        queries_under_2s = sum(1 for r in successful_queries if r['response_time'] < 2.0)
        
        optimization_results = {
            'total_queries': len(test_queries),
            'successful_queries': len(successful_queries),
            'success_rate': len(successful_queries) / len(test_queries),
            'avg_response_time': avg_response_time,
            'avg_sources_per_query': avg_sources,
            'avg_relevance_score': avg_relevance,
            'queries_under_2s': queries_under_2s,
            'performance_score': queries_under_2s / len(test_queries),
            'optimized_threshold': rag.similarity_threshold,
            'total_test_time': total_time
        }
        
        print(f"\n📊 OPTIMIZATION RESULTS:")
        print(f"✅ Success rate: {optimization_results['success_rate']:.1%}")
        print(f"⚡ Avg response time: {optimization_results['avg_response_time']:.2f}s")
        print(f"📚 Avg sources per query: {optimization_results['avg_sources_per_query']:.1f}")
        print(f"🎯 Avg relevance score: {optimization_results['avg_relevance_score']:.1%}")
        print(f"🚀 Queries under 2s: {optimization_results['queries_under_2s']}/{len(test_queries)} ({optimization_results['performance_score']:.1%})")
        print(f"🔧 Optimized threshold: {optimization_results['optimized_threshold']:.2%}")
        
        return optimization_results
    else:
        print("\n❌ No successful queries - optimization failed")
        return None


def create_optimized_config():
    """Create optimized configuration file"""
    print("\n" + "="*60)
    print("💾 Creating Optimized Configuration")
    print("="*60)
    
    # Run optimization
    results = optimize_rag_system()
    
    if not results:
        print("❌ Cannot create config without optimization results")
        return
    
    # Create optimized configuration
    config = {
        'rag_optimization': {
            'similarity_threshold': results['optimized_threshold'],
            'default_top_k': 5,
            'max_context_length': 2000,
            'cache_size': 100,
            'performance_target': {
                'max_response_time': 2.0,
                'min_success_rate': 0.8,
                'min_relevance_score': 0.3
            }
        },
        'optimization_results': results,
        'recommendations': []
    }
    
    # Add recommendations based on results
    if results['avg_response_time'] > 2.0:
        config['recommendations'].append("Consider using smaller embedding models or implementing better caching")
    
    if results['success_rate'] < 0.8:
        config['recommendations'].append("Lower similarity threshold or improve case data quality")
    
    if results['avg_relevance_score'] < 0.3:
        config['recommendations'].append("Improve embedding model or case preprocessing")
    
    if results['performance_score'] < 0.6:
        config['recommendations'].append("Optimize vector database configuration and query processing")
    
    # Save configuration
    config_file = 'rag_optimization_config.json'
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Configuration saved to: {config_file}")
    
    # Create summary report
    print(f"\n📋 OPTIMIZATION SUMMARY:")
    print(f"🎯 Optimized similarity threshold: {config['rag_optimization']['similarity_threshold']:.2%}")
    print(f"📊 Performance score: {results['performance_score']:.1%}")
    print(f"⚡ Average response time: {results['avg_response_time']:.2f}s")
    
    if config['recommendations']:
        print(f"\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(config['recommendations'], 1):
            print(f"{i}. {rec}")
    
    return config


def main():
    """Run complete RAG optimization process"""
    print("🚀 RAG SYSTEM OPTIMIZATION SUITE")
    print("="*80)
    print(f"⏰ Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Create optimized configuration
        config = create_optimized_config()
        
        if config:
            print(f"\n🎉 RAG system optimization complete!")
            print(f"📁 Check 'rag_optimization_config.json' for detailed results")
        else:
            print(f"\n❌ RAG system optimization failed")
            
    except Exception as e:
        print(f"\n❌ Optimization error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()