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
            
            # List available models to debug
            try:
                import google.generativeai as genai_check
                models = genai_check.list_models()
                print(f"📋 Available models: {[m.name for m in models if 'generateContent' in m.supported_generation_methods][:5]}")
            except Exception as e:
                print(f"⚠️  Could not list models: {e}")
            
            # Try different model names (updated for 2025 - gemini-pro is deprecated)
            model_names = [
                'gemini-2.0-flash-exp',  # Latest experimental model
                'gemini-2.0-flash',       # Stable 2.0 flash
                'gemini-1.5-flash',       # Fallback to 1.5
                'models/gemini-2.0-flash-exp',
                'models/gemini-1.5-flash'
            ]
            
            for model_name in model_names:
                try:
                    self.model = genai.GenerativeModel(model_name)
                    self.llm = 'gemini'
                    print(f"✅ Google Gemini initialized with model: {model_name}")
                    break
                except Exception as e:
                    print(f"⚠️  Failed with {model_name}: {e}")
                    continue
            else:
                raise Exception("No working Gemini model found")
            
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
                metadata = case.get('metadata', {})
                relevant_cases.append({
                    'title': metadata.get('title', 'Untitled Case'),
                    'court': metadata.get('court', 'Unknown Court'),
                    'date': metadata.get('date', 'Date not available'),
                    'judges': metadata.get('judges', 'Judges not listed'),
                    'url': metadata.get('url', ''),
                    'relevance_score': 1 - case.get('distance', 0),
                    'excerpt': case.get('document', '')[:500]
                })
            
            return relevant_cases
            
        except Exception as e:
            print(f"❌ Error retrieving cases: {e}")
            import traceback
            traceback.print_exc()
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
            
            # Configure safety settings to be more permissive for legal content
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            response = self.model.generate_content(prompt, safety_settings=safety_settings)
            
            # Check if response was blocked or empty
            if not response.text or response.text.strip() == "":
                print(f"⚠️  Gemini returned empty response")
                return "I apologize, but I couldn't generate a proper response. This may be due to content filtering. Please try rephrasing your query."
            
            return response.text
            
        except Exception as e:
            import traceback
            print(f"❌ Gemini generation error: {e}")
            print(f"📋 Full traceback: {traceback.format_exc()}")
            return "Error generating response. Please check the logs for details."
    
    def _generate_general_legal_response(self, query: str) -> str:
        """Generate response using Gemini's general knowledge when no precedents found"""
        try:
            import google.generativeai as genai
            
            prompt = f"""You are an expert Indian legal assistant with deep knowledge of Indian law, including the Constitution of India, Indian Penal Code, Civil Procedure Code, and various special laws.

Query: {query}

NOTE: I could not find specific legal precedents in my database for this query. However, please provide a helpful legal response based on your general knowledge of Indian law.

Instructions:
1. Provide accurate information about relevant Indian laws, acts, and sections
2. Explain general legal principles that apply to this situation
3. Mention the legal framework and procedures if applicable
4. Be clear that this is general legal information, not specific case law
5. Suggest what type of legal professional they should consult if needed
6. Include a disclaimer that this is general information only

Provide your expert legal guidance:"""
            
            # Configure safety settings to be more permissive for legal content
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            response = self.model.generate_content(prompt, safety_settings=safety_settings)
            
            # Check if response was blocked
            if not response.text or response.text.strip() == "":
                print(f"⚠️  Gemini returned empty response. Prompt feedback: {response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'N/A'}")
                return f"""**General Legal Information:**

While I couldn't retrieve specific precedents from our database, I can provide general guidance:

For questions regarding "{query}", I recommend:

1. **Consult a Legal Professional**: For specific legal advice tailored to your situation, please consult a qualified lawyer specializing in the relevant area of law.

2. **Research Applicable Laws**: Look into relevant sections of:
   - The Indian Constitution
   - Indian Penal Code (IPC)
   - Code of Criminal Procedure (CrPC)
   - Code of Civil Procedure (CPC)
   - Specific laws applicable to your situation

3. **Legal Aid**: If cost is a concern, consider reaching out to legal aid services or pro bono legal clinics.

*Disclaimer: This is general information only and not legal advice. Please consult a qualified legal professional for advice specific to your situation.*"""
            
            return response.text
            
        except Exception as e:
            import traceback
            print(f"❌ Gemini generation error: {e}")
            print(f"📋 Full traceback: {traceback.format_exc()}")
            
            # Provide a helpful fallback response instead of generic error
            return f"""**Legal Information Request:**

I encountered a technical issue while generating a detailed response for your query: "{query}"

However, I can provide general guidance:

**Recommended Steps:**
1. **Consult a Qualified Lawyer**: For specific legal advice, please consult a lawyer who specializes in the relevant area of Indian law.

2. **Legal Resources**: You may want to research:
   - Relevant provisions of the Indian Constitution
   - Applicable acts and statutes
   - Rules and regulations specific to your concern

3. **Legal Aid Services**: Free or low-cost legal assistance may be available through:
   - District Legal Services Authority
   - State Legal Services Authority
   - National Legal Services Authority (NALSA)

*Disclaimer: This is general information only, not legal advice. For advice specific to your situation, please consult a qualified legal professional.*

*Technical Note: Please try rephrasing your query or contact support if the issue persists.*"""
    
    def _generate_general_legal_response_openai(self, query: str) -> str:
        """Generate response using OpenAI's general knowledge when no precedents found"""
        try:
            messages = [
                {"role": "system", "content": "You are an expert Indian legal assistant with deep knowledge of Indian law."},
                {"role": "user", "content": f"""Query: {query}

NOTE: No specific legal precedents were found in the database for this query. Please provide a helpful legal response based on your general knowledge of Indian law.

Instructions:
1. Provide accurate information about relevant Indian laws, acts, and sections
2. Explain general legal principles that apply
3. Mention the legal framework and procedures if applicable
4. Be clear this is general legal information
5. Suggest consulting appropriate legal professionals
6. Include a disclaimer

Provide your expert legal guidance:"""}
            ]
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ OpenAI generation error: {e}")
            return "I apologize, but I'm having trouble generating a response. Please try again."
    
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
            print("⚠️  No relevant cases found, generating response without precedents")
            # Still generate a response using Gemini's general knowledge
            if self.llm == 'gemini':
                answer = self._generate_general_legal_response(query)
            elif self.llm == 'openai':
                answer = self._generate_general_legal_response_openai(query)
            else:
                answer = "I couldn't find relevant legal precedents in our database for your query. Please try rephrasing or provide more context."
            
            return {
                'answer': answer,
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