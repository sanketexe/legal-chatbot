#!/usr/bin/env python3
"""
Final Performance Test for RAG Model Training
Tests the optimized vector database with various queries
"""

import time
import statistics
from .vector_db import LegalVectorDatabase
from logging_config import get_logger

logger = get_logger(__name__)

def run_final_performance_test():
    """Run comprehensive performance test"""
    logger.info("Final RAG Model Performance Test")
    logger.info("%s", "=" * 60)

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
        "arbitration dispute resolution",
    ]

    logger.info("Testing %d diverse legal queries", len(test_queries))
    logger.info("%s", "=" * 60)

    # Performance metrics
    query_times = []
    similarity_scores = []
    results_counts = []

    for i, query in enumerate(test_queries, 1):
        logger.info("Query %d: %s", i, query)

        # Time the query
        start_time = time.time()
        results = db.search_similar_cases(query, top_k=5)
        end_time = time.time()

        query_time = end_time - start_time
        query_times.append(query_time)
        results_counts.append(len(results))

        logger.info("   Query time: %.3fs", query_time)
        logger.info("   Results: %d", len(results))

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

                logger.info("   %d. Similarity: %.1f%% | Query: %s", j + 1, similarity * 100, search_query)

            avg_similarity = statistics.mean(query_similarities)
            similarity_scores.append(avg_similarity)
            logger.info("   Average similarity: %.1f%%", avg_similarity * 100)
        else:
            logger.warning("No results found for query: %s", query)

    # Overall performance summary
    logger.info("%s", "\n" + "=" * 60)
    logger.info("PERFORMANCE SUMMARY")
    logger.info("%s", "=" * 60)

    if query_times:
        avg_time = statistics.mean(query_times)
        min_time = min(query_times)
        max_time = max(query_times)

        logger.info("Query Performance:")
        logger.info("   Average time: %.3fs", avg_time)
        logger.info("   Fastest query: %.3fs", min_time)
        logger.info("   Slowest query: %.3fs", max_time)

        # Performance rating
        if avg_time < 1.0:
            logger.info("   Excellent performance (< 1s)")
        elif avg_time < 2.0:
            logger.info("   Good performance (< 2s)")
        else:
            logger.info("   Needs optimization (> 2s)")

    if similarity_scores:
        avg_similarity = statistics.mean(similarity_scores)
        min_similarity = min(similarity_scores)
        max_similarity = max(similarity_scores)

        logger.info("\nSearch Quality:")
        logger.info("   Average similarity: %.1f%%", avg_similarity * 100)
        logger.info("   Lowest similarity: %.1f%%", min_similarity * 100)
        logger.info("   Highest similarity: %.1f%%", max_similarity * 100)

        # Quality rating
        if avg_similarity > 0.7:
            logger.info("   Excellent search quality (> 70%)")
        elif avg_similarity > 0.5:
            logger.info("   Good search quality (> 50%)")
        elif avg_similarity > 0.3:
            logger.info("   Moderate search quality (> 30%)")
        else:
            logger.info("   Poor search quality (< 30%)")

    if results_counts:
        avg_results = statistics.mean(results_counts)
        logger.info("\nResults Coverage:")
        logger.info("   Average results per query: %.1f", avg_results)

        if avg_results >= 5:
            logger.info("   Good coverage (>= 5 results per query)")
        elif avg_results >= 3:
            logger.info("   Moderate coverage (>= 3 results per query)")
        else:
            logger.info("   Poor coverage (< 3 results per query)")

    # Database statistics
    logger.info("\nDatabase Statistics:")
    try:
        import chromadb
        client = chromadb.PersistentClient(path="./data/chromadb")
        collection = client.get_collection("indian_legal_cases")
        total_cases = collection.count()

        logger.info("   Total cases indexed: %d", total_cases)
        logger.info("   Queries tested: %d", len(test_queries))
        logger.info("   Coverage: %.2f%% of database tested", (len(test_queries) / total_cases * 100))
    except Exception as e:
        logger.error("Error getting database stats: %s", e)

    # Final recommendations
    logger.info("\nFINAL RECOMMENDATIONS:")
    logger.info("%s", "=" * 60)

    if query_times and statistics.mean(query_times) < 2.0:
        logger.info("Query performance meets requirements (< 2s average)")
    else:
        logger.info("Consider optimizing query performance")

    if similarity_scores and statistics.mean(similarity_scores) > 0.25:
        logger.info("Search quality is acceptable (> 25% average similarity)")
    else:
        logger.info("Consider improving embedding model or data preprocessing")

    logger.info("Use top_k=5 for optimal balance of speed and coverage")
    logger.info("Set similarity threshold to 0.3 for filtering results")
    logger.info("RAG model training validation complete")

    return {
        'avg_query_time': statistics.mean(query_times) if query_times else 0,
        'avg_similarity': statistics.mean(similarity_scores) if similarity_scores else 0,
        'avg_results': statistics.mean(results_counts) if results_counts else 0,
        'total_queries': len(test_queries),
    }

if __name__ == "__main__":
    results = run_final_performance_test()
    logger.info("\nTest completed successfully")
    logger.info("Final metrics: %s", results)