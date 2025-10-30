"""
Legal RAG (Retrieval-Augmented Generation) System
Combines case retrieval with LLM for accurate legal advice
"""

import os
import json
from typing import List, Dict, Optional
from datetime import datetime

from vector_db import LegalVectorDatabase


class LegalRAG:
    """
    RAG system for legal question answering
    Retrieves relevant cases and generates responses with citations
    """
    
    def __init__(self, use_openai: bool = False, vector_db=None):
        """
        Initialize Legal RAG system
        
        Args:
            use_openai: If True, use OpenAI. Otherwise use free alternatives (Gemini)
            vector_db: Optional vector database instance (defaults to ChromaDB)
        """
        self.use_openai = use_openai
        self.vector_db = vector_db if vector_db is not None else LegalVectorDatabase(use_cloud=False)
        self.llm = None
        
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
        """Initialize Google Gemini (Free)"""
        try:
            import google.generativeai as genai
            from dotenv import load_dotenv
            
            # Load environment variables
            load_dotenv()
            
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment variables")
            
            genai.configure(api_key=api_key)
            
            # Use the latest Gemini model
            self.model = genai.GenerativeModel('models/gemini-2.5-flash')
            self.llm = 'gemini'
            print("✅ Google Gemini initialized")
            
        except Exception as e:
            print(f"❌ Gemini initialization error: {e}")
            self.llm = None
    
    def retrieve_relevant_cases(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Retrieve relevant cases for the query
        
        Args:
            query: User's legal question
            top_k: Number of cases to retrieve
            
        Returns:
            List of relevant cases with metadata
        """
        try:
            # Search vector database
            results = self.vector_db.search_similar_cases(query, top_k=top_k)
            
            # Format results
            relevant_cases = []
            for case in results:
                relevant_cases.append({
                    'title': case['metadata']['title'],
                    'court': case['metadata']['court'],
                    'date': case['metadata']['date'],
                    'judges': case['metadata']['judges'],
                    'url': case['metadata'].get('url', ''),
                    'relevance_score': 1 - case.get('distance', 0),
                    'excerpt': case.get('document', '')[:500]
                })
            
            return relevant_cases
            
        except Exception as e:
            print(f"❌ Error retrieving cases: {e}")
            return []
    
    def format_context(self, cases: List[Dict]) -> str:
        """
        Format retrieved cases as context for LLM
        
        Args:
            cases: List of relevant cases
            
        Returns:
            Formatted context string
        """
        if not cases:
            return "No relevant precedents found."
        
        context = "**Relevant Legal Precedents:**\n\n"
        
        for i, case in enumerate(cases, 1):
            context += f"**Case {i}: {case['title']}**\n"
            context += f"- Court: {case['court']}\n"
            context += f"- Date: {case['date']}\n"
            context += f"- Judges: {case['judges']}\n"
            context += f"- Relevance: {case['relevance_score']:.2%}\n"
            context += f"- Excerpt: {case['excerpt'][:300]}...\n\n"
        
        return context
    
    def generate_response_openai(self, query: str, context: str) -> str:
        """Generate response using OpenAI GPT"""
        try:
            import openai
            
            system_prompt = """You are an expert Indian legal assistant. 
            Use the provided case precedents to answer questions accurately.
            Always cite specific cases and rulings.
            If uncertain, acknowledge limitations.
            Provide clear, actionable legal guidance."""
            
            user_prompt = f"""Query: {query}

{context}

Based on the above precedents, provide a comprehensive legal answer with citations."""
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ OpenAI generation error: {e}")
            return "Error generating response."
    
    def generate_response_gemini(self, query: str, context: str) -> str:
        """Generate response using Google Gemini"""
        try:
            prompt = f"""You are an expert Indian legal assistant with deep knowledge of Indian law.

Query: {query}

{context}

Instructions:
1. Analyze the provided case precedents carefully
2. Provide a comprehensive legal answer citing specific cases
3. Include relevant legal principles and precedents
4. Mention applicable laws and sections if relevant
5. Be clear, accurate, and professional
6. If precedents are insufficient, acknowledge limitations

Provide your expert legal analysis:"""
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            print(f"❌ Gemini generation error: {e}")
            return "Error generating response."
    
    def answer_legal_query(self, query: str, top_k: int = 5) -> Dict:
        """
        Complete RAG pipeline: retrieve cases and generate answer
        
        Args:
            query: User's legal question
            top_k: Number of cases to retrieve
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        print(f"🔍 Processing query: {query}")
        
        # Step 1: Retrieve relevant cases
        relevant_cases = self.retrieve_relevant_cases(query, top_k=top_k)
        
        if not relevant_cases:
            return {
                'answer': "I couldn't find relevant legal precedents for your query. Please try rephrasing or provide more context.",
                'sources': [],
                'timestamp': datetime.now().isoformat()
            }
        
        print(f"📚 Found {len(relevant_cases)} relevant cases")
        
        # Step 2: Format context
        context = self.format_context(relevant_cases)
        
        # Step 3: Generate response
        if self.llm == 'openai':
            answer = self.generate_response_openai(query, context)
        elif self.llm == 'gemini':
            answer = self.generate_response_gemini(query, context)
        else:
            answer = "LLM not initialized. Please check configuration."
        
        print("✅ Generated response with citations")
        
        # Step 4: Return complete response
        return {
            'answer': answer,
            'sources': relevant_cases,
            'query': query,
            'timestamp': datetime.now().isoformat()
        }
    
    def batch_process_queries(self, queries: List[str], output_file: str = 'legal_qa_results.json'):
        """
        Process multiple queries in batch
        
        Args:
            queries: List of legal questions
            output_file: File to save results
        """
        results = []
        
        for i, query in enumerate(queries, 1):
            print(f"\n{'='*60}")
            print(f"Processing query {i}/{len(queries)}")
            
            result = self.answer_legal_query(query)
            results.append(result)
        
        # Save results
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 Batch processing complete! Results saved to {output_file}")


def main():
    """
    Test the Legal RAG system
    """
    print("🧪 Testing Legal RAG System")
    print("=" * 60)
    
    # Initialize RAG
    rag = LegalRAG(use_openai=False)
    
    # Test queries
    test_queries = [
        "What is the penalty for breach of contract in India?",
        "Can I claim damages for a delayed property possession?",
        "What are the grounds for divorce under Indian law?",
        "How long does a trademark registration last in India?",
        "What is the liability in a motor accident case?"
    ]
    
    print("\n📝 Testing sample legal queries...\n")
    
    for query in test_queries[:2]:  # Test first 2 queries
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print("=" * 60)
        
        result = rag.answer_legal_query(query, top_k=3)
        
        print(f"\n💡 Answer:\n{result['answer']}")
        
        print(f"\n📚 Sources ({len(result['sources'])} cases):")
        for i, source in enumerate(result['sources'], 1):
            print(f"\n{i}. {source['title']}")
            print(f"   {source['court']} | {source['date']}")
            print(f"   Relevance: {source['relevance_score']:.2%}")
    
    print("\n" + "=" * 60)
    print("✅ RAG system test complete!")


if __name__ == "__main__":
    main()