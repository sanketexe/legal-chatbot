#!/usr/bin/env python3
"""
Vector Database Performance Optimization
Configures ChromaDB settings and tests retrieval performance
"""

import time
import json
import statistics
from typing import List, Dict, Tuple
from vector_db import LegalVectorDatabase

class PerformanceOptimizer:
    """Optimize vector database performance"""
    
    def __init__(self):
        self.db = LegalVectorDatabase(use_cloud=False)
        self.test_queries = [
            "contract breach damages compensation",
            "property inheritance rights succession",
            "motor accident liability insurance",
            "trademark infringement intellectual property",
            "divorce grounds matrimonial law",
            "criminal defamation section 499",
            "employment termination wrongful dismissal",
            "consumer protection unfair trade practices",
            "tax evasion penalty assessment",
            "land acquisition compensation dispute"
        ]
    
    def benchmark_search_performance(self, top_k_values: List[int] = [3, 5, 10, 15, 20]) -> Dict:
        """Benchmark search performance with different top_k values"""
        print("🔍 Benchmarking Search Performance")
        print("=" * 50)
        
        results = {}
        
        for top_k in top_k_values:
            print(f"\n📊 Testing with top_k = {top_k}")
            times = []
            
            for i, query in enumerate(self.test_queries):
                start_time = time.time()
                search_results = self.db.search_similar_cases(query, top_k=top_k)
                end_time = time.time()
                
                query_time = end_time - start_time
                times.append(query_time)
                
                print(f"   Query {i+1}: {query_time:.3f}s ({len(search_results)} results)")
            
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            
            results[top_k] = {
                'avg_time': avg_time,
                'min_time': min_time,
                'max_time': max_time,
                'times': times
            }
            
            print(f"   Average: {avg_time:.3f}s, Min: {min_time:.3f}s, Max: {max_time:.3f}s")
        
        return results
    
    def test_similarity_thresholds(self, thresholds: List[float] = [0.3, 0.5, 0.7, 0.8, 0.9]) -> Dict:
        """Test different similarity thresholds for result quality"""
        print("\n🎯 Testing Similarity Thresholds")
        print("=" * 50)
        
        test_query = "contract breach damages compensation"
        results = {}
        
        # Get base results without filtering
        base_results = self.db.search_similar_cases(test_query, top_k=20)
        
        for threshold in thresholds:
            # Filter results by similarity (convert distance to similarity)
            filtered_results = []
            for result in base_results:
                distance = result.get('distance', 1)
                similarity = max(0, min(1, (2 - distance) / 2))
                if similarity >= threshold:
                    filtered_results.append(result)
            
            results[threshold] = {
                'count': len(filtered_results),
                'avg_similarity': statistics.mean([max(0, min(1, (2 - r.get('distance', 1)) / 2)) for r in filtered_results]) if filtered_results else 0
            }
            
            print(f"   Threshold {threshold}: {len(filtered_results)} results, "
                  f"avg similarity: {results[threshold]['avg_similarity']:.2%}")
        
        return results
    
    def optimize_batch_size(self, batch_sizes: List[int] = [10, 25, 50, 100]) -> Dict:
        """Test different batch sizes for embedding generation"""
        print("\n⚡ Testing Batch Sizes for Embedding Generation")
        print("=" * 50)
        
        results = {}
        test_texts = self.test_queries * 10  # 100 texts total
        
        for batch_size in batch_sizes:
            print(f"\n📦 Testing batch size: {batch_size}")
            
            start_time = time.time()
            embeddings = self.db.create_embeddings(test_texts[:batch_size], use_openai=False)
            end_time = time.time()
            
            total_time = end_time - start_time
            time_per_text = total_time / batch_size
            
            results[batch_size] = {
                'total_time': total_time,
                'time_per_text': time_per_text,
                'texts_per_second': batch_size / total_time
            }
            
            print(f"   Total time: {total_time:.3f}s")
            print(f"   Time per text: {time_per_text:.3f}s")
            print(f"   Texts per second: {batch_size / total_time:.1f}")
        
        return results
    
    def analyze_search_quality(self, top_k: int = 10) -> Dict:
        """Analyze search result quality and relevance"""
        print("\n🔬 Analyzing Search Quality")
        print("=" * 50)
        
        quality_metrics = {
            'queries_tested': len(self.test_queries),
            'avg_results_per_query': 0,
            'avg_similarity': 0,
            'similarity_distribution': {'high': 0, 'medium': 0, 'low': 0}
        }
        
        all_similarities = []
        total_results = 0
        
        for i, query in enumerate(self.test_queries):
            print(f"\n🔍 Query {i+1}: {query}")
            results = self.db.search_similar_cases(query, top_k=top_k)
            
            if results:
                similarities = [max(0, min(1, (2 - r.get('distance', 1)) / 2)) for r in results]
                avg_sim = statistics.mean(similarities)
                
                print(f"   Results: {len(results)}")
                print(f"   Avg similarity: {avg_sim:.2%}")
                print(f"   Best match: {max(similarities):.2%}")
                
                all_similarities.extend(similarities)
                total_results += len(results)
                
                # Categorize similarities
                for sim in similarities:
                    if sim >= 0.8:
                        quality_metrics['similarity_distribution']['high'] += 1
                    elif sim >= 0.6:
                        quality_metrics['similarity_distribution']['medium'] += 1
                    else:
                        quality_metrics['similarity_distribution']['low'] += 1
        
        if all_similarities:
            quality_metrics['avg_results_per_query'] = total_results / len(self.test_queries)
            quality_metrics['avg_similarity'] = statistics.mean(all_similarities)
            quality_metrics['min_similarity'] = min(all_similarities)
            quality_metrics['max_similarity'] = max(all_similarities)
        
        return quality_metrics
    
    def generate_optimization_report(self) -> Dict:
        """Generate comprehensive optimization report"""
        print("\n📋 Generating Optimization Report")
        print("=" * 60)
        
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'database_stats': {},
            'performance_benchmarks': {},
            'quality_analysis': {},
            'recommendations': []
        }
        
        # Database statistics
        try:
            import chromadb
            client = chromadb.PersistentClient(path="./data/chromadb")
            collection = client.get_collection("indian_legal_cases")
            report['database_stats'] = {
                'total_cases': collection.count(),
                'collection_name': collection.name,
                'metadata': collection.metadata
            }
        except Exception as e:
            report['database_stats'] = {'error': str(e)}
        
        # Performance benchmarks
        print("\n1. Running performance benchmarks...")
        report['performance_benchmarks'] = self.benchmark_search_performance()
        
        # Quality analysis
        print("\n2. Analyzing search quality...")
        report['quality_analysis'] = self.analyze_search_quality()
        
        # Similarity threshold testing
        print("\n3. Testing similarity thresholds...")
        threshold_results = self.test_similarity_thresholds()
        report['similarity_thresholds'] = threshold_results
        
        # Generate recommendations
        report['recommendations'] = self._generate_recommendations(report)
        
        return report
    
    def _generate_recommendations(self, report: Dict) -> List[str]:
        """Generate optimization recommendations based on test results"""
        recommendations = []
        
        # Performance recommendations
        perf_data = report.get('performance_benchmarks', {})
        if perf_data:
            # Find optimal top_k
            best_top_k = min(perf_data.keys(), key=lambda k: perf_data[k]['avg_time'])
            if perf_data[best_top_k]['avg_time'] < 2.0:
                recommendations.append(f"✅ Current performance is good. Optimal top_k: {best_top_k}")
            else:
                recommendations.append(f"⚠️ Consider reducing top_k to {best_top_k} for better performance")
        
        # Quality recommendations
        quality_data = report.get('quality_analysis', {})
        if quality_data:
            avg_sim = quality_data.get('avg_similarity', 0)
            if avg_sim < 0.5:
                recommendations.append("⚠️ Low average similarity. Consider improving embedding model or data preprocessing")
            elif avg_sim > 0.8:
                recommendations.append("✅ High search quality achieved")
            else:
                recommendations.append("✅ Moderate search quality. Consider fine-tuning similarity thresholds")
        
        # Similarity threshold recommendations
        threshold_data = report.get('similarity_thresholds', {})
        if threshold_data:
            # Find threshold that gives good balance of quantity and quality
            balanced_threshold = 0.6
            for threshold, data in threshold_data.items():
                if data['count'] >= 5 and data['avg_similarity'] >= 0.7:
                    balanced_threshold = threshold
                    break
            recommendations.append(f"💡 Recommended similarity threshold: {balanced_threshold}")
        
        # Database recommendations
        db_stats = report.get('database_stats', {})
        total_cases = db_stats.get('total_cases', 0)
        if total_cases > 1000:
            recommendations.append("✅ Good dataset size for training")
        else:
            recommendations.append("⚠️ Consider expanding dataset for better coverage")
        
        return recommendations
    
    def save_report(self, report: Dict, filename: str = "performance_optimization_report.json"):
        """Save optimization report to file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Report saved to: {filename}")


def main():
    """Run performance optimization"""
    print("🚀 Vector Database Performance Optimization")
    print("=" * 60)
    
    optimizer = PerformanceOptimizer()
    
    # Generate comprehensive report
    report = optimizer.generate_optimization_report()
    
    # Print summary
    print("\n📊 OPTIMIZATION SUMMARY")
    print("=" * 60)
    
    # Database stats
    db_stats = report.get('database_stats', {})
    print(f"📚 Total cases indexed: {db_stats.get('total_cases', 'Unknown')}")
    
    # Performance summary
    perf_data = report.get('performance_benchmarks', {})
    if perf_data:
        avg_times = [data['avg_time'] for data in perf_data.values()]
        print(f"⚡ Average search time: {statistics.mean(avg_times):.3f}s")
    
    # Quality summary
    quality_data = report.get('quality_analysis', {})
    if quality_data:
        print(f"🎯 Average similarity: {quality_data.get('avg_similarity', 0):.2%}")
    
    # Recommendations
    recommendations = report.get('recommendations', [])
    print(f"\n💡 RECOMMENDATIONS:")
    for rec in recommendations:
        print(f"   {rec}")
    
    # Save report
    optimizer.save_report(report)
    
    print("\n✅ Performance optimization complete!")


if __name__ == "__main__":
    main()