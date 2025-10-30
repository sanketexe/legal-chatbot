"""
Optimized Legal RAG (Retrieval-Augmented Generation) System
Enhanced version with better performance and accuracy
"""

import os
import json
import time
from typing import List, Dict, Optional
from datetime import datetime
import numpy as np

from vector_db import LegalVectorDatabase


class OptimizedLegalRAG:
    """
    Optimized RAG system for legal question answering
    Features: Caching, better similarity thresholds, improved context formatting
    """
    
    def __init__(self, use_openai: bool = False):
        """
        Initialize Optimized Legal RAG system
        
        Args:
            use_openai: If True, use OpenAI. Otherwise use free alternatives (Gemini)
        """
        self.use_openai = use_openai
        self.vector_db = LegalVectorDatabase(use_cloud=False)
        self.llm = None
        
        # Performance optimizations
        self.query_cache = {}  # Cache for recent queries
        self.embedding_cache = {}  # Cache for embeddings
        self.max_cache_size = 100
        
        # Optimized parameters
        self.similarity_threshold = 0.3  # Lower threshold for better recall
        self.default_top_k = 5
        self.max_context_length = 2000  # Limit context to improve performance
        
        # Initialize LLM
        if use_openai:
            self._init_openai()
        else:
            self._init_gemini()
    
    def _init_openai(self):
        """Initialize OpenAI GPT"""
        try:
            import openai
            openai.api_key = os.getenv('OPENAI_API_KEY')
            self.llm = 'openai'
            print("✅ OpenAI GPT initialized")
        except Exception as e:
            print(f"❌ OpenAI initialization error: {e}")
            print("💡 Falling back to Gemini")
            self._init_gemini()
    
    def _init_gemini(self):
        """Initialize Google Gemini (Free) with fallback"""
        try:
            import google.generativeai as genai
            from dotenv import load_dotenv
            
            # Load environment variables
            load_dotenv()
            
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                print("⚠️  GOOGLE_API_KEY not found, using fallback responses")
                self.llm = 'fallback'
                return
            
            genai.configure(api_key=api_key)
            
            # Use the latest Gemini model
            self.model = genai.GenerativeModel('models/gemini-2.5-flash')
            self.llm = 'gemini'
            print("✅ Google Gemini initialized")
            
        except Exception as e:
            print(f"❌ Gemini initialization error: {e}")
            print("💡 Using fallback response system")
            self.llm = 'fallback'
    
    def _get_cached_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding if available"""
        text_hash = hash(text)
        return self.embedding_cache.get(text_hash)
    
    def _cache_embedding(self, text: str, embedding: List[float]):
        """Cache embedding for future use"""
        if len(self.embedding_cache) >= self.max_cache_size:
            # Remove oldest entry
            oldest_key = next(iter(self.embedding_cache))
            del self.embedding_cache[oldest_key]
        
        text_hash = hash(text)
        self.embedding_cache[text_hash] = embedding
    
    def retrieve_relevant_cases(self, query: str, top_k: int = None) -> List[Dict]:
        """
        Optimized case retrieval with caching and better filtering
        
        Args:
            query: User's legal question
            top_k: Number of cases to retrieve
            
        Returns:
            List of relevant cases with metadata
        """
        if top_k is None:
            top_k = self.default_top_k
        
        try:
            # Check cache first
            cache_key = f"{query}_{top_k}"
            if cache_key in self.query_cache:
                print("🚀 Using cached results")
                return self.query_cache[cache_key]
            
            # Search vector database with optimized parameters
            start_time = time.time()
            results = self.vector_db.search_similar_cases(query, top_k=top_k * 2)  # Get more results for filtering
            search_time = time.time() - start_time
            
            # Filter results by similarity threshold and improve relevance scoring
            relevant_cases = []
            for case in results:
                distance = case.get('distance', 1.0)
                relevance_score = 1 - distance
                
                # Apply similarity threshold
                if relevance_score >= self.similarity_threshold:
                    # Enhanced case information
                    case_info = {
                        'title': case['metadata'].get('title', 'Untitled Case')[:100],
                        'court': case['metadata'].get('court', 'Unknown Court'),
                        'date': case['metadata'].get('date', 'Unknown Date'),
                        'judges': case['metadata'].get('judges', 'Unknown Judges'),
                        'url': case['metadata'].get('url', ''),
                        'relevance_score': relevance_score,
                        'excerpt': case.get('document', '')[:400],  # Longer excerpt for better context
                        'search_query': case['metadata'].get('search_query', ''),
                        'legal_acts': case['metadata'].get('legal_acts', '[]')
                    }
                    relevant_cases.append(case_info)
            
            # Sort by relevance and limit to requested number
            relevant_cases.sort(key=lambda x: x['relevance_score'], reverse=True)
            relevant_cases = relevant_cases[:top_k]
            
            # Cache results
            if len(self.query_cache) >= self.max_cache_size:
                # Remove oldest entry
                oldest_key = next(iter(self.query_cache))
                del self.query_cache[oldest_key]
            
            self.query_cache[cache_key] = relevant_cases
            
            print(f"⚡ Search completed in {search_time:.2f}s, found {len(relevant_cases)} relevant cases")
            return relevant_cases
            
        except Exception as e:
            print(f"❌ Error retrieving cases: {e}")
            return []
    
    def format_optimized_context(self, cases: List[Dict], max_length: int = None) -> str:
        """
        Format retrieved cases as optimized context for LLM
        
        Args:
            cases: List of relevant cases
            max_length: Maximum context length
            
        Returns:
            Formatted context string
        """
        if not cases:
            return "No relevant legal precedents found in the database."
        
        if max_length is None:
            max_length = self.max_context_length
        
        context = "**Relevant Indian Legal Precedents:**\n\n"
        current_length = len(context)
        
        for i, case in enumerate(cases, 1):
            # Create concise case summary
            case_summary = f"**Case {i}: {case['title']}**\n"
            case_summary += f"- Relevance: {case['relevance_score']:.1%}\n"
            
            # Add court and date if available
            if case['court'] and case['court'] != 'Unknown Court':
                case_summary += f"- Court: {case['court']}\n"
            if case['date'] and case['date'] != 'Unknown Date':
                case_summary += f"- Date: {case['date']}\n"
            
            # Add excerpt with length control
            excerpt = case['excerpt'][:200] if case['excerpt'] else "No excerpt available"
            case_summary += f"- Key Points: {excerpt}...\n\n"
            
            # Check if adding this case would exceed max length
            if current_length + len(case_summary) > max_length:
                context += f"*[Additional {len(cases) - i + 1} cases available but truncated for brevity]*\n"
                break
            
            context += case_summary
            current_length += len(case_summary)
        
        return context
    
    def generate_fallback_response(self, query: str, context: str) -> str:
        """Generate intelligent fallback response when LLM is unavailable"""
        query_lower = query.lower()
        
        # Extract key legal concepts from context
        legal_concepts = []
        if 'contract' in query_lower or 'agreement' in query_lower:
            legal_concepts.append('Contract Law')
        if 'property' in query_lower or 'inheritance' in query_lower:
            legal_concepts.append('Property Law')
        if 'divorce' in query_lower or 'marriage' in query_lower:
            legal_concepts.append('Family Law')
        if 'accident' in query_lower or 'liability' in query_lower:
            legal_concepts.append('Tort Law')
        if 'constitution' in query_lower or 'fundamental' in query_lower:
            legal_concepts.append('Constitutional Law')
        
        response = f"**Legal Analysis for: {query}**\n\n"
        
        if legal_concepts:
            response += f"**Area of Law:** {', '.join(legal_concepts)}\n\n"
        
        response += "**Based on Available Legal Precedents:**\n\n"
        response += context + "\n"
        
        response += "**Important Note:** This analysis is based on available case precedents. "
        response += "For specific legal advice tailored to your situation, please consult with a qualified attorney.\n\n"
        
        response += "**Disclaimer:** This information is for educational purposes only and does not constitute legal advice."
        
        return response
    
    def generate_response_gemini(self, query: str, context: str) -> str:
        """Generate response using Google Gemini with error handling"""
        try:
            prompt = f"""You are an expert Indian legal assistant with deep knowledge of Indian law and legal precedents.

Query: {query}

{context}

Instructions:
1. Analyze the provided case precedents carefully
2. Provide a comprehensive legal answer citing specific cases by name
3. Include relevant legal principles and precedents
4. Mention applicable laws and sections if relevant
5. Be clear, accurate, and professional
6. Structure your response with clear headings
7. If precedents are insufficient, acknowledge limitations

Provide your expert legal analysis with proper citations:"""
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            print(f"❌ Gemini generation error: {e}")
            return self.generate_fallback_response(query, context)
    
    def generate_response_openai(self, query: str, context: str) -> str:
        """Generate response using OpenAI GPT with error handling"""
        try:
            import openai
            
            system_prompt = """You are an expert Indian legal assistant with comprehensive knowledge of Indian law.
            Use the provided case precedents to answer questions accurately.
            Always cite specific cases and rulings.
            Structure your responses clearly with headings.
            If uncertain, acknowledge limitations.
            Provide clear, actionable legal guidance."""
            
            user_prompt = f"""Query: {query}

{context}

Based on the above precedents, provide a comprehensive legal answer with proper citations and structure."""
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ OpenAI generation error: {e}")
            return self.generate_fallback_response(query, context)
    
    def answer_legal_query(self, query: str, top_k: int = None) -> Dict:
        """
        Optimized RAG pipeline with performance monitoring
        
        Args:
            query: User's legal question
            top_k: Number of cases to retrieve
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        start_time = time.time()
        print(f"🔍 Processing optimized query: {query}")
        
        if top_k is None:
            top_k = self.default_top_k
        
        # Step 1: Retrieve relevant cases (with caching)
        retrieval_start = time.time()
        relevant_cases = self.retrieve_relevant_cases(query, top_k=top_k)
        retrieval_time = time.time() - retrieval_start
        
        if not relevant_cases:
            return {
                'answer': "I couldn't find relevant legal precedents for your query. Please try rephrasing or provide more context.",
                'sources': [],
                'timestamp': datetime.now().isoformat(),
                'performance': {
                    'total_time': time.time() - start_time,
                    'retrieval_time': retrieval_time,
                    'generation_time': 0
                }
            }
        
        print(f"📚 Found {len(relevant_cases)} relevant cases (avg relevance: {np.mean([c['relevance_score'] for c in relevant_cases]):.1%})")
        
        # Step 2: Format optimized context
        context_start = time.time()
        context = self.format_optimized_context(relevant_cases)
        context_time = time.time() - context_start
        
        # Step 3: Generate response with fallback
        generation_start = time.time()
        if self.llm == 'openai':
            answer = self.generate_response_openai(query, context)
        elif self.llm == 'gemini':
            answer = self.generate_response_gemini(query, context)
        else:
            answer = self.generate_fallback_response(query, context)
        generation_time = time.time() - generation_start
        
        total_time = time.time() - start_time
        
        print(f"✅ Generated optimized response in {total_time:.2f}s")
        
        # Step 4: Return complete response with performance metrics
        return {
            'answer': answer,
            'sources': relevant_cases,
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'performance': {
                'total_time': total_time,
                'retrieval_time': retrieval_time,
                'context_time': context_time,
                'generation_time': generation_time,
                'cache_hits': len([k for k in self.query_cache.keys() if query in k])
            },
            'optimization_info': {
                'similarity_threshold': self.similarity_threshold,
                'cases_retrieved': len(relevant_cases),
                'context_length': len(context),
                'llm_used': self.llm
            }
        }
    
    def batch_test_performance(self, test_queries: List[str]) -> Dict:
        """
        Test performance across multiple queries
        
        Args:
            test_queries: List of test queries
            
        Returns:
            Performance statistics
        """
        print(f"\n⚡ Running performance test on {len(test_queries)} queries...")
        
        results = []
        total_start = time.time()
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Test {i}/{len(test_queries)}: {query[:50]}...")
            
            result = self.answer_legal_query(query)
            results.append(result)
            
            perf = result['performance']
            print(f"   ⏱️  Total: {perf['total_time']:.2f}s | Retrieval: {perf['retrieval_time']:.2f}s | Generation: {perf['generation_time']:.2f}s")
        
        total_time = time.time() - total_start
        
        # Calculate statistics
        response_times = [r['performance']['total_time'] for r in results]
        retrieval_times = [r['performance']['retrieval_time'] for r in results]
        generation_times = [r['performance']['generation_time'] for r in results]
        
        stats = {
            'total_queries': len(test_queries),
            'total_time': total_time,
            'avg_response_time': np.mean(response_times),
            'min_response_time': np.min(response_times),
            'max_response_time': np.max(response_times),
            'avg_retrieval_time': np.mean(retrieval_times),
            'avg_generation_time': np.mean(generation_times),
            'queries_under_2s': sum(1 for t in response_times if t < 2.0),
            'performance_score': (sum(1 for t in response_times if t < 2.0) / len(response_times)) * 100
        }
        
        print(f"\n📊 PERFORMANCE SUMMARY:")
        print(f"⚡ Average response time: {stats['avg_response_time']:.2f}s")
        print(f"🚀 Fastest response: {stats['min_response_time']:.2f}s")
        print(f"🐌 Slowest response: {stats['max_response_time']:.2f}s")
        print(f"🎯 Queries under 2s: {stats['queries_under_2s']}/{stats['total_queries']} ({stats['performance_score']:.1f}%)")
        
        return stats
    
    def optimize_similarity_threshold(self, test_queries: List[str], target_sources: int = 5) -> float:
        """
        Optimize similarity threshold for better accuracy
        
        Args:
            test_queries: Sample queries for testing
            target_sources: Target number of sources per query
            
        Returns:
            Optimized similarity threshold
        """
        print(f"\n🎯 Optimizing similarity threshold...")
        
        thresholds = [0.1, 0.2, 0.3, 0.4, 0.5]
        best_threshold = self.similarity_threshold
        best_score = 0
        
        for threshold in thresholds:
            print(f"\n🔍 Testing threshold: {threshold}")
            self.similarity_threshold = threshold
            
            total_sources = 0
            valid_queries = 0
            
            for query in test_queries[:3]:  # Test with subset for speed
                cases = self.retrieve_relevant_cases(query, top_k=target_sources)
                if cases:
                    total_sources += len(cases)
                    valid_queries += 1
            
            if valid_queries > 0:
                avg_sources = total_sources / valid_queries
                # Score based on how close to target and number of valid queries
                score = (valid_queries / len(test_queries[:3])) * min(avg_sources / target_sources, 1.0)
                
                print(f"   📊 Avg sources: {avg_sources:.1f}, Valid queries: {valid_queries}, Score: {score:.2f}")
                
                if score > best_score:
                    best_score = score
                    best_threshold = threshold
        
        self.similarity_threshold = best_threshold
        print(f"\n✅ Optimized similarity threshold: {best_threshold} (score: {best_score:.2f})")
        
        return best_threshold


def main():
    """
    Test the Optimized Legal RAG system
    """
    print("🚀 Testing Optimized Legal RAG System")
    print("=" * 60)
    
    # Initialize optimized RAG
    rag = OptimizedLegalRAG(use_openai=False)
    
    # Test queries for optimization
    test_queries = [
        "What is the penalty for breach of contract in India?",
        "What are the grounds for divorce under Indian law?",
        "What are the rights of a tenant regarding eviction?",
        "What is the liability in motor accident cases?",
        "What are the fundamental rights under Indian Constitution?"
    ]
    
    print("\n🎯 Step 1: Optimizing similarity threshold...")
    rag.optimize_similarity_threshold(test_queries)
    
    print("\n⚡ Step 2: Performance testing...")
    performance_stats = rag.batch_test_performance(test_queries)
    
    print("\n📝 Step 3: Testing individual query with detailed output...")
    result = rag.answer_legal_query("What are the remedies for breach of contract?", top_k=3)
    
    print(f"\n💡 Sample Answer (first 300 chars):\n{result['answer'][:300]}...")
    print(f"\n📚 Sources ({len(result['sources'])} cases):")
    for i, source in enumerate(result['sources'], 1):
        print(f"{i}. {source['title'][:60]}... (Relevance: {source['relevance_score']:.1%})")
    
    print(f"\n⚡ Performance Details:")
    perf = result['performance']
    print(f"   Total Time: {perf['total_time']:.2f}s")
    print(f"   Retrieval: {perf['retrieval_time']:.2f}s")
    print(f"   Generation: {perf['generation_time']:.2f}s")
    
    print("\n" + "=" * 60)
    print("✅ Optimized RAG system test complete!")


if __name__ == "__main__":
    main()