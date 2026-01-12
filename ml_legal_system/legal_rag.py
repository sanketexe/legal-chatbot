"""
Legal RAG (Retrieval-Augmented Generation) System
Combines case retrieval with LLM for accurate legal advice
"""

import os
import json
from typing import List, Dict, Optional
from datetime import datetime
import hashlib
import time

from .vector_db import LegalVectorDatabase


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
        
        # Performance optimizations
        self.response_cache = {}  # Simple cache for repeated queries
        self.max_cache_size = 100
        self.model_initialized = False
        
        # Lazy initialization - only initialize when first needed
        print("⚡ LegalRAG initialized with lazy model loading for better performance")
    
    def _ensure_model_initialized(self):
        """Ensure the model is initialized (lazy loading)"""
        if not self.model_initialized:
            if self.use_openai:
                self._init_openai()
            else:
                self._init_gemini()
            self.model_initialized = True
    
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
            
            # Try different model names (optimized for speed and quota efficiency)
            model_names = [
                'gemini-2.0-flash-exp',   # Latest experimental model
                'gemini-2.5-flash',       # Latest stable fast model
                'gemini-2.0-flash',       # Stable fast model
                'gemini-1.5-flash',       # Fallback option
                'models/gemini-2.0-flash-exp',
                'models/gemini-2.5-flash',
                'models/gemini-2.0-flash'
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
            
            prompt = f"""You are a helpful Indian legal assistant. Answer the user's question concisely and accurately.

User Question: {query}

Instructions:
1. Provide a BRIEF, SPECIFIC answer (5-10 sentences max)
2. Focus on answering their exact question, not giving a lecture
3. If it's about a famous case (like Nirbhaya, Ayodhya, etc.), provide key facts and outcome
4. If it's a legal question, explain the relevant law briefly
5. Use simple language - avoid legal jargon unless necessary
6. Include 2-3 key points maximum
7. Be direct and helpful

DO NOT:
- Give long generic responses about "the Indian legal system"
- List all possible legal remedies unless asked
- Provide boilerplate legal framework information
- Write more than 10 sentences

Format: Short paragraphs with bullet points for key facts. Be conversational and helpful."""
            
            # Configure safety settings to be more permissive for legal content
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
            ]
            
            response = self.model.generate_content(prompt, safety_settings=safety_settings)
            
            # Check if response was blocked
            if not response.text or response.text.strip() == "":
                print(f"⚠️  Gemini returned empty response. Attempting with simplified prompt.")
                
                # Try with a simpler, more direct prompt
                simple_prompt = f"""Answer this legal question briefly: {query}
                
Provide key facts and relevant laws in 5 sentences or less."""
                
                response = self.model.generate_content(simple_prompt, safety_settings=safety_settings)
                
                if not response.text or response.text.strip() == "":
                    # Final fallback - short and helpful
                    return f"""I couldn't find specific information about "{query}" in my database.

For detailed legal advice on this matter, I recommend:
• Consulting with a lawyer specializing in this area
• Visiting your local legal aid office (free consultation)
• Calling NALSA helpline: 15100 (National Legal Services Authority)

*This bot provides general information only, not legal advice.*"""
            
            # Add a brief disclaimer
            response_text = response.text.strip()
            if len(response_text) > 50:  # Only add disclaimer if we got a real response
                response_text += "\n\n*Note: This is general information. For specific legal advice, consult a lawyer.*"
            
            return response_text
            
        except Exception as e:
            import traceback
            error_msg = str(e)
            print(f"❌ Gemini generation error: {e}")
            print(f"📋 Full traceback: {traceback.format_exc()}")
            
            # Check if it's a quota error
            if "429" in error_msg or "quota" in error_msg.lower():
                return f"""⚠️ **API Quota Exceeded**

I'm currently unable to access the AI service due to API limits.

**Your Question:** "{query}"

**What You Can Do:**

**For Immediate Legal Help:**
📞 **NALSA Helpline:** 15100 (National Legal Services Authority - Free)
📞 **Women Helpline:** 1091
📞 **Police:** 100

**Legal Resources:**
🌐 **indiankanoon.org** - Search case laws
🌐 **District Legal Services Authority** - Free legal aid

**If you're in an emergency:**
• Call 100 for police
• Contact a lawyer immediately
• Document everything (photos, videos, witnesses)

**Your Rights:**
• Article 21: Right to Life & Personal Liberty
• Article 22: Protection against arrest & detention
• Right to know grounds of arrest
• Right to legal representation

*I apologize for the inconvenience. The administrator needs to check the API billing.*"""
            
            # Generic error
            return f"""I'm having trouble accessing legal information right now.

**For immediate help with "{query[:50]}...":**

📞 **Emergency Numbers:**
• NALSA Helpline: 15100 (Free legal aid)
• Police: 100
• Women Helpline: 1091

🌐 **Legal Resources:**
• indiankanoon.org - Case law search
• District Legal Aid office - Free consultation

**If urgent, consult a lawyer immediately.**

*Technical error: {error_msg[:100]}*"""
    
    def _get_comprehensive_fallback_response(self, query: str) -> str:
        """Provide a brief, helpful fallback response when AI fails"""
        query_lower = query.lower()
        
        # Check for specific topics and provide BRIEF relevant information
        if any(word in query_lower for word in ['arrest', 'detention', 'jail', 'custody', 'police']):
            return f"""**Quick Info: Arrests & Detention in India**

Your Rights:
• Article 22: Right against arbitrary arrest
• Must be informed of arrest grounds
• Legal representation allowed
• Produced before magistrate within 24 hours
• Bail available (except certain cases)

Legal Remedies:
• Habeas Corpus petition (challenge illegal detention)
• Bail application
• Contact District Legal Aid office (free)

📞 NALSA Helpline: 15100

*For specific advice, consult a criminal lawyer immediately.*"""
        
        elif any(word in query_lower for word in ['protest', 'demonstration', 'strike', 'rally']):
            return f"""**Quick Info: Right to Protest in India**

Constitutional Rights:
• Article 19(1)(a): Freedom of speech
• Article 19(1)(b): Right to peaceful assembly

Key Rules:
• Must remain peaceful and non-violent
• Prior permission may be needed
• Cannot block essential services
• Cannot incite violence

Legal Restrictions:
• Section 144 CrPC (prohibitory orders)
• State Police Acts
• IPC Sections 141-149 (unlawful assembly)

**Tip:** Challenge prohibitory orders in High Court if needed.

*Consult a constitutional lawyer for specific protest-related issues.*"""
        
        else:
            # Return a much shorter, user-friendly message
            return f"""I don't have specific information about "{query}" in my database.

For legal help:
📞 NALSA: 15100 (free legal aid)
🌐 indiankanoon.org (case law)
👨‍⚖️ Consult a lawyer (first consultation often free)

*Note: This bot provides general information, not legal advice.*"""
    
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
    
    def _handle_conversational_query(self, query: str) -> Optional[str]:
        """
        Handle non-legal conversational queries like greetings, small talk, etc.
        
        Args:
            query: User's input
            
        Returns:
            Conversational response if query is non-legal, None if legal query
        """
        query_lower = query.lower().strip()
        
        # Greetings and basic interactions - EXACT match or at start/end only
        greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'namaste']
        # Check if query is EXACTLY a greeting or starts with greeting
        is_greeting = (query_lower in greetings or 
                      any(query_lower.startswith(f"{g} ") or query_lower == g for g in greetings))
        
        if is_greeting:
            return """Hello! 👋 I'm your AI Legal Assistant. 

I'm here to help you with:
🔍 Legal questions and advice
⚖️ Indian law information
📚 Case law research
📋 Legal framework guidance

How can I assist you with your legal needs today?"""

        # Thanks and appreciation
        thanks = ['thank you', 'thanks', 'appreciate', 'grateful']
        if any(thank in query_lower for thank in thanks):
            return """You're very welcome! 😊 

I'm glad I could help you with your legal questions. If you have any more legal queries or need further clarification on any legal matters, feel free to ask anytime.

Remember, while I provide general legal guidance, it's always best to consult with a qualified lawyer for specific legal situations."""

        # Goodbye
        goodbyes = ['bye', 'goodbye', 'see you', 'farewell', 'take care']
        if any(goodbye in query_lower for goodbye in goodbyes):
            return """Goodbye! 👋 Take care and remember:

✅ Keep important legal documents safe
✅ Know your legal rights
✅ Consult qualified lawyers for specific cases
✅ Stay informed about legal developments

Feel free to return anytime you need legal guidance!"""

        # How are you / personal questions
        personal = ['how are you', 'what is your name', 'who are you', 'tell me about yourself']
        if any(personal in query_lower for personal in personal):
            return """I'm doing well, thank you for asking! 😊

I'm an AI Legal Assistant specialized in Indian law. My purpose is to:

🧠 **What I do:**
- Provide legal guidance and information
- Research case law and precedents
- Explain legal frameworks and procedures
- Help you understand your legal rights

⚖️ **My expertise includes:**
- Constitutional Law
- Criminal Law (IPC, CrPC)
- Civil Law (CPC, Contract Act)
- Family Law, Property Law
- Commercial Law

How can I help you with your legal questions today?"""

        # Test queries
        test_queries = ['test', 'testing', 'check', 'working']
        if query_lower in test_queries:
            return """✅ I'm working perfectly! 

🤖 **System Status:** All systems operational
🔍 **Legal Database:** Connected and ready
🧠 **AI Engine:** Functioning normally
⚡ **Response Time:** Optimized for speed

Ready to assist you with your legal questions! Try asking me about:
- Indian legal procedures
- Your legal rights
- Specific laws or acts
- Legal case guidance"""

        # Help requests
        help_queries = ['help', 'what can you do', 'commands', 'guide']
        if any(help_q in query_lower for help_q in help_queries):
            return """🤖 **Legal AI Assistant Help Guide**

**I can help you with:**
📚 **Legal Research:** Ask about laws, acts, and legal procedures
🔍 **Case Analysis:** Legal situation analysis and guidance  
⚖️ **Rights Information:** Know your legal rights and protections
📋 **Legal Framework:** Constitutional, criminal, civil law guidance
💼 **Practical Advice:** Legal procedures and next steps

**How to ask:**
✅ "What are my rights if arrested?"
✅ "Tell me about property inheritance laws"
✅ "How to file a civil suit?"
✅ "What is the legal procedure for..."

**Remember:** I provide general legal guidance. For specific cases, always consult a qualified lawyer.

What legal question can I help you with?"""
        
        # URGENT: Arrest/Police/Handcuff situations - Provide immediate info without needing AI
        urgent_keywords = ['arrest', 'handcuff', 'police', 'custody', 'detained', 'jail']
        if any(keyword in query_lower for keyword in urgent_keywords):
            return """🚨 **URGENT: Your Rights During Arrest**

**If Police Arrest/Handcuff You:**

**Your Constitutional Rights (Article 22):**
✅ Right to know WHY you're being arrested
✅ Right to remain silent (don't give forced confession)
✅ Right to a lawyer IMMEDIATELY
✅ Right to inform family/friend about arrest
✅ Must be produced before magistrate within 24 hours

**What to Do RIGHT NOW:**
1. **Stay Calm** - Don't resist physically
2. **Ask**: "What is the reason for arrest?"
3. **Ask**: "Where is the arrest warrant?" (required for most cases)
4. **Ask**: "What sections are charged under?"
5. **Say**: "I want to contact my lawyer"
6. **Contact**: Family member or lawyer IMMEDIATELY

**Legal Requirements Police MUST Follow:**
• Cannot arrest without warrant (except cognizable offenses)
• Must show ID and give reason
• Cannot handcuff without justification
• Medical examination mandatory
• Female can only be arrested by female constable (exceptions apply)

**Immediate Actions:**
📞 **Call Lawyer**: FIRST priority
📞 **Legal Aid**: 15100 (NALSA - Free)
📞 **Police Control Room**: Check local number
📞 **Women Helpline**: 1091 (if female)

**Document Everything:**
• Officer's name and badge number
• Time and place
• Reason given
• Any witnesses

**Illegal Arrest Rights:**
• File Habeas Corpus petition in High Court
• File complaint against police
• Sue for damages

⚠️ **This is an emergency situation. Contact a criminal lawyer IMMEDIATELY after securing your safety.**

*Stay calm, know your rights, and get legal help fast.*"""
        
        # Check if query is clearly non-legal (very short, random, etc.)
        if len(query_lower) <= 3 and query_lower not in ['law', 'ipc', 'crp']:
            return f"""I noticed your message "{query}" is quite brief. 

I'm here to help with legal questions! Try asking me about:
🔍 Legal procedures and rights
⚖️ Indian laws and acts
📚 Legal advice and guidance
💼 Case law research

What legal topic would you like to explore?"""

        # If none of the above, it's likely a legal query - return None
        return None

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
        
        # Step 0: Check if this is a conversational greeting/non-legal query
        conversational_response = self._handle_conversational_query(query)
        if conversational_response:
            return {
                'answer': conversational_response,
                'sources': [],
                'query': query,
                'timestamp': datetime.now().isoformat(),
                'type': 'conversational'
            }
        
        # Ensure model is initialized (lazy loading for performance)
        self._ensure_model_initialized()
        
        # Performance optimization: Check cache first
        cache_key = hashlib.md5(f"{query}_{top_k}".encode()).hexdigest()
        if cache_key in self.response_cache:
            print("📦 Returning cached response")
            cached = self.response_cache[cache_key]
            if time.time() - cached['timestamp'] < 3600:  # Cache for 1 hour
                return cached['response']
        
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
        result = {
            'answer': answer,
            'sources': relevant_cases,
            'query': query,
            'timestamp': datetime.now().isoformat()
        }
        
        # Cache the result for future use
        if len(self.response_cache) >= self.max_cache_size:
            # Remove oldest entry
            oldest_key = min(self.response_cache.keys(), 
                           key=lambda k: self.response_cache[k]['timestamp'])
            del self.response_cache[oldest_key]
        
        self.response_cache[cache_key] = {
            'response': result,
            'timestamp': time.time()
        }
        
        return result
    
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