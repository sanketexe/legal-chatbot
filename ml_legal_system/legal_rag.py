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
            
            prompt = f"""You are an expert Indian legal assistant with comprehensive knowledge of Indian law, current legal developments, and constitutional provisions. You should be helpful and informative while being accurate.

Query: {query}

Instructions:
1. Provide detailed, helpful information about the legal query, even if no specific precedents are available in the database
2. For current events/cases (like arrests, detentions, protests), explain the likely legal provisions that may apply
3. Reference relevant Indian laws, constitutional articles, acts, and sections that are applicable
4. Explain legal concepts in simple terms that a layperson can understand
5. Provide context about legal procedures and rights
6. If it's about a specific person or current event, explain the general legal framework that would apply to such situations
7. Be educational and informative - help the user understand the broader legal landscape
8. Always include appropriate disclaimers
9. Don't be overly rigid - provide substantive helpful information

For detention/arrest cases specifically:
- Explain preventive detention laws (like NSA, PSA)
- Constitutional provisions (Article 19, 21, 22)
- Fundamental rights and their limitations
- Legal remedies available (habeas corpus, bail, etc.)
- Due process requirements

Respond in a helpful, educational manner while maintaining accuracy. Don't give generic responses - provide real legal insight."""
            
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
                simple_prompt = f"""As an Indian legal expert, please explain the legal aspects of: {query}
                
Include relevant laws, constitutional provisions, and legal procedures that apply. Be helpful and educational."""
                
                response = self.model.generate_content(simple_prompt, safety_settings=safety_settings)
                
                if not response.text or response.text.strip() == "":
                    # Final fallback - but much more comprehensive
                    return self._get_comprehensive_fallback_response(query)
            
            return response.text + "\n\n*Disclaimer: This information is for educational purposes only and does not constitute legal advice. For specific legal guidance, please consult a qualified legal professional.*"
            
        except Exception as e:
            import traceback
            print(f"❌ Gemini generation error: {e}")
            print(f"📋 Full traceback: {traceback.format_exc()}")
            return self._get_comprehensive_fallback_response(query)
    
    def _get_comprehensive_fallback_response(self, query: str) -> str:
        """Provide a comprehensive fallback response when AI fails"""
        query_lower = query.lower()
        
        # Check for specific topics and provide relevant information
        if any(word in query_lower for word in ['arrest', 'detention', 'jail', 'custody', 'police']):
            return f"""**Legal Framework for Arrests and Detention in India**

Regarding your query about "{query}", here's the relevant legal framework:

**Constitutional Provisions:**
- **Article 21**: Right to Life and Personal Liberty
- **Article 22**: Right against arbitrary arrest and detention
- **Article 19**: Fundamental freedoms (subject to reasonable restrictions)

**Key Legal Provisions:**
1. **Code of Criminal Procedure (CrPC), 1973**: Governs arrest procedures
2. **Preventive Detention Laws**: 
   - National Security Act (NSA)
   - Public Safety Act (PSA) - in J&K and other states
   - Unlawful Activities (Prevention) Act (UAPA)

**Legal Rights During Arrest:**
- Right to know grounds of arrest (Article 22(1))
- Right to legal representation
- Right to be produced before magistrate within 24 hours
- Right to bail (except in specific circumstances)

**Remedies Available:**
- **Habeas Corpus Petition**: Challenge illegal detention
- **Bail Application**: Seek release pending trial
- **Quashing Petition**: Challenge FIR validity

**Legal Procedures:**
- Police must follow due process
- Medical examination mandatory
- Family notification required
- Detention beyond limits requires judicial approval

*For specific cases involving political activists or protesters, courts often examine whether detention is based on legitimate grounds or if fundamental rights are being violated.*

**Important Note:** This is general legal information. For specific advice about any individual case, please consult a qualified criminal lawyer.

**Legal Aid Resources:**
- District Legal Services Authority
- State Legal Services Authority  
- National Legal Services Authority (NALSA)
"""
        
        elif any(word in query_lower for word in ['protest', 'demonstration', 'strike', 'rally']):
            return f"""**Right to Protest in India - Legal Framework**

Regarding "{query}":

**Constitutional Rights:**
- **Article 19(1)(a)**: Freedom of speech and expression
- **Article 19(1)(b)**: Right to assemble peacefully and without arms
- **Article 19(1)(c)**: Right to form associations or unions

**Legal Restrictions (Article 19(2) & 19(3)):**
- Sovereignty and integrity of India
- Security of the State
- Friendly relations with foreign States
- Public order, decency, or morality

**Applicable Laws:**
1. **Police Act provisions** in various states
2. **Section 144 CrPC**: Prohibitory orders
3. **Indian Penal Code Sections**:
   - Section 141-149: Unlawful assembly
   - Section 153A: Promoting enmity
   - Section 124A: Sedition (under review by Supreme Court)

**Legal Requirements for Peaceful Protests:**
- Prior permission may be required in certain areas
- Must remain peaceful and non-violent
- Cannot block essential services
- Cannot incite violence or hatred

**When Protests Become Illegal:**
- Use of violence or force
- Damage to property
- Blocking essential services
- Hate speech or incitement

**Legal Remedies:**
- Challenge prohibitory orders in High Court
- Seek protection through fundamental rights petitions
- Approach Human Rights Commission

*Recent judicial trends favor protecting peaceful dissent while maintaining public order.*

**Disclaimer:** This is educational information only. For specific legal advice, consult a constitutional lawyer or civil rights advocate.
"""
        
        else:
            return f"""**Legal Guidance for Your Query**

While I couldn't access specific case precedents for "{query}", I can provide relevant legal guidance:

**General Legal Framework:**
The Indian legal system provides comprehensive coverage through:
- **The Constitution of India**: Fundamental rights and duties
- **Civil and Criminal Laws**: IPC, CrPC, CPC, and special acts
- **Personal Laws**: Based on religion and community
- **Commercial Laws**: For business and trade matters

**Common Legal Areas:**
1. **Constitutional Law**: Fundamental rights, state duties, judicial review
2. **Criminal Law**: Offenses, procedures, evidence, bail
3. **Civil Law**: Contracts, property, torts, family matters
4. **Administrative Law**: Government actions, public services
5. **Commercial Law**: Business, taxation, intellectual property

**Legal Remedies Available:**
- **High Courts**: Constitutional and civil matters
- **Supreme Court**: Final appellate authority
- **District Courts**: Trial courts for most matters
- **Special Tribunals**: Specific subject matters
- **Alternative Dispute Resolution**: Mediation, arbitration

**How to Proceed:**
1. **Identify the Legal Area**: Constitutional, criminal, civil, commercial
2. **Research Applicable Laws**: Specific acts and sections
3. **Consult Legal Experts**: Lawyers specializing in relevant area
4. **Understand Procedures**: Filing requirements, timelines, costs
5. **Know Your Rights**: Constitutional and statutory protections

**Legal Aid Resources:**
- **National Legal Services Authority (NALSA)**
- **State Legal Services Authority**
- **District Legal Services Authority**
- **Law University Legal Aid Clinics**
- **Bar Association Pro Bono Services**

*This is educational information to help you understand the legal framework. For specific advice about your situation, please consult a qualified lawyer who can analyze your case details.*
"""
    
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