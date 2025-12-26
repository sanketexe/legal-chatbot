"""Modern LangChain-based Legal Assistant
This module supports a LangChain-powered assistant when the langchain
packages are installed. If langchain (or related providers) are not
available, the class will fall back to the repository's existing RAG
functions (so importing this module won't crash the app).
"""

import os
from typing import Dict, List, Optional, Iterator
import asyncio
from datetime import datetime
import logging

# Setup logger
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Try to import LangChain pieces lazily. If imports fail, we set HAS_LANGCHAIN=False
HAS_LANGCHAIN = True
try:
    from langchain_openai import ChatOpenAI  # type: ignore
    from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage  # type: ignore
    from langchain_core.prompts import ChatPromptTemplate  # type: ignore
    print("✅ LangChain core imports successful")
except Exception as e:
    print(f"DEBUG: LangChain import failed: {e}")
    HAS_LANGCHAIN = False

class ModernLegalAssistant:
    """
    Advanced Legal Assistant using LangChain with:
    - Conversation memory
    - Streaming responses  
    - Tool integration
    - Error recovery
    - Context awareness
    """
    
    def __init__(self):
        if HAS_LANGCHAIN:
            try:
                self.setup_llm()
                self.setup_memory()
                self.setup_tools()
                self.setup_prompts()
            except Exception as e:
                # If any LangChain setup step fails, fall back to non-langchain mode
                print(f"WARN: LangChain setup failed: {e}")
                self._set_fallback_state()
        else:
            print("WARN: LangChain packages not available. Running in fallback mode.")
            self._set_fallback_state()

    def _set_fallback_state(self):
        """Set attributes for safe fallback operation when LangChain isn't present."""
        self.llm = None
        self.memory = None
        self.tools = []
        self.system_prompt = ""
        self.prompt_template = None
        
    def setup_llm(self):
        """Initialize chat models - simplified version"""
        if not HAS_LANGCHAIN:
            raise RuntimeError("LangChain not available")

        # Primary: Gemini (cost-effective)
        if os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY'):
            api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                google_api_key=api_key,
                temperature=0.7
            )
            print("✅ Using Gemini Chat Model (LangChain)")

        # Fallback: OpenAI
        elif os.getenv('OPENAI_API_KEY'):
            self.llm = ChatOpenAI(
                model="gpt-4",
                openai_api_key=os.getenv('OPENAI_API_KEY'),
                temperature=0.7
            )
            print("✅ Using OpenAI Chat Model (LangChain)")
        else:
            raise ValueError("No API keys found for LLM")
    
    def setup_memory(self):
        """Setup conversation memory with session-based storage"""
        # Session-based memory storage for multi-user support
        self.session_memories = {}  # session_id -> conversation history
        self.max_memory_messages = 20  # Limit memory to prevent token overflow
        
        # Import database models for persistent storage
        try:
            from models import ChatSession, Message, db
            self.db_available = True
        except ImportError:
            self.db_available = False
            logger.info("Database models not available, using in-memory storage only")
        
    def setup_tools(self):
        """Setup legal tools - simplified approach for now"""
        # For now, we'll use these as helper methods rather than LangChain tools
        # This can be enhanced later when we need full agent functionality
        self.tools = []
    
    def setup_prompts(self):
        """Setup sophisticated prompts"""
        self.system_prompt = """You are an expert Indian Legal Assistant with comprehensive knowledge of:

**Core Expertise:**
- Indian Constitution (Articles, Fundamental Rights, DPSPs)
- Indian Penal Code (IPC), Criminal Procedure Code (CrPC)
- Civil Procedure Code (CPC), Evidence Act
- Preventive detention laws (NSA, PSA, UAPA)
- Commercial laws, Family laws, Property laws
- Current legal developments and landmark judgments

**Response Guidelines:**
1. **Be Conversational**: Maintain context from previous messages
2. **Be Educational**: Explain legal concepts clearly
3. **Be Current**: Address contemporary legal issues
4. **Be Practical**: Provide actionable legal guidance
5. **Be Comprehensive**: Cover relevant laws, procedures, and remedies
6. **Be Accurate**: Cite specific legal provisions when applicable

**For Detention/Arrest Cases:**
- Explain applicable laws (NSA, PSA, UAPA, CrPC)
- Constitutional provisions (Articles 19, 21, 22)
- Legal remedies (habeas corpus, bail, legal aid)
- Rights of the accused and due process

**Conversation Style:**
- Remember previous context
- Ask clarifying questions when needed
- Provide step-by-step guidance
- Suggest next steps or follow-up questions

Always include appropriate legal disclaimers."""

        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "{input}")
        ])
    
    def _search_legal_database(self, query: str) -> str:
        """Search legal database (integrate with existing RAG)"""
        try:
            # Import and use existing RAG system
            from ml_legal_system.legal_rag import answer_legal_query
            result = answer_legal_query(query)

            # Normalize various return shapes
            if isinstance(result, dict):
                sources = result.get('sources', [])
                answer_text = result.get('response') or result.get('answer') or ''
            else:
                sources = []
                answer_text = str(result)

            if sources:
                return f"Found {len(sources)} relevant cases:\n{answer_text}"
            else:
                return "No specific precedents found in database."
        except Exception as e:
            return f"Database search unavailable: {str(e)}"
    
    def _lookup_legal_framework(self, query: str) -> str:
        """Look up legal acts and provisions"""
        # This could be enhanced with a comprehensive legal database
        frameworks = {
            'constitution': 'Indian Constitution - Fundamental Rights, DPSPs, Emergency provisions',
            'ipc': 'Indian Penal Code - Criminal offenses and punishments',
            'crpc': 'Criminal Procedure Code - Criminal trial procedures',
            'cpc': 'Civil Procedure Code - Civil litigation procedures',
            'nsa': 'National Security Act - Preventive detention for national security',
            'psa': 'Public Safety Act - Preventive detention in J&K and other states',
            'uapa': 'Unlawful Activities Prevention Act - Anti-terrorism law'
        }
        
        query_lower = query.lower()
        relevant = [f"**{k.upper()}**: {v}" for k, v in frameworks.items() if k in query_lower]
        
        if relevant:
            return "Relevant Legal Framework:\n" + "\n".join(relevant)
        else:
            return "Please specify which legal framework you're interested in (Constitution, IPC, CrPC, etc.)"
    
    def _get_current_legal_info(self, query: str) -> str:
        """Get current legal information (could integrate with news APIs)"""
        return "For current legal developments, please check recent Supreme Court and High Court judgments, or consult legal news sources."
    
    def get_session_memory(self, session_id: str) -> List[Dict]:
        """Get conversation memory for a specific session"""
        if self.db_available:
            return self._get_db_memory(session_id)
        else:
            return self.session_memories.get(session_id, [])
    
    def _get_db_memory(self, session_id: str) -> List[Dict]:
        """Retrieve conversation history from database"""
        try:
            from models import Message
            messages = Message.query.filter_by(
                session_id=session_id
            ).order_by(Message.timestamp.asc()).limit(self.max_memory_messages).all()
            
            return [{'role': msg.role, 'content': msg.content} for msg in messages]
        except Exception as e:
            logger.warning(f"Could not retrieve DB memory: {e}")
            return self.session_memories.get(session_id, [])
    
    def add_to_session_memory(self, session_id: str, role: str, content: str):
        """Add message to session memory"""
        message = {'role': role, 'content': content}
        
        # Add to in-memory store
        if session_id not in self.session_memories:
            self.session_memories[session_id] = []
        
        self.session_memories[session_id].append(message)
        
        # Keep only recent messages to prevent memory overflow
        if len(self.session_memories[session_id]) > self.max_memory_messages:
            self.session_memories[session_id] = self.session_memories[session_id][-self.max_memory_messages:]
    
    def clear_session_memory(self, session_id: str):
        """Clear memory for a specific session"""
        if session_id in self.session_memories:
            del self.session_memories[session_id]
    
    def build_conversation_context(self, session_id: str, current_message: str) -> List:
        """Build conversation context with memory for LangChain"""
        if not HAS_LANGCHAIN:
            return []
            
        messages = [SystemMessage(content=self.system_prompt)]
        
        # Add conversation history
        history = self.get_session_memory(session_id)
        for msg in history[-10:]:  # Use only last 10 messages for context
            if msg['role'] == 'user':
                messages.append(HumanMessage(content=msg['content']))
            elif msg['role'] == 'assistant':
                messages.append(AIMessage(content=msg['content']))
        
        # Add current message
        messages.append(HumanMessage(content=current_message))
        
        return messages
    
    async def chat_stream(self, message: str, session_id: str = "default"):
        """Enhanced streaming chat with session-based conversation memory"""
        # If LangChain isn't available, fallback to non-streaming
        if not HAS_LANGCHAIN:
            try:
                from ml_legal_system.legal_rag import answer_legal_query
                out = answer_legal_query(message)
                response = out.get('response') or out.get('answer') or str(out) if isinstance(out, dict) else str(out)
                yield response
                return
            except Exception as e:
                yield f"I apologize, but I encountered an error: {str(e)}. Please try rephrasing your question."
                return

        try:
            # Build conversation context with session memory
            messages = self.build_conversation_context(session_id, message)
            
            # Add user message to memory before streaming
            self.add_to_session_memory(session_id, 'user', message)
            
            # Stream response from LLM
            full_response = ""
            async for chunk in self.llm.astream(messages):
                if chunk.content:
                    full_response += chunk.content
                    yield chunk.content
            
            # Add complete assistant response to memory
            if full_response:
                self.add_to_session_memory(session_id, 'assistant', full_response)

        except Exception as e:
            error_msg = f"I apologize, but I encountered an error: {str(e)}. Please try rephrasing your question."
            self.add_to_session_memory(session_id, 'user', message)
            self.add_to_session_memory(session_id, 'assistant', error_msg)
            yield error_msg
    
    def chat_stream_sync(self, message: str, session_id: str = "default"):
        """Synchronous streaming chat (for Flask Server-Sent Events)"""
        # If LangChain isn't available, fallback to non-streaming
        if not HAS_LANGCHAIN:
            try:
                from ml_legal_system.legal_rag import answer_legal_query
                out = answer_legal_query(message)
                response = out.get('response') or out.get('answer') or str(out) if isinstance(out, dict) else str(out)
                yield response
                return
            except Exception as e:
                yield f"I apologize, but I encountered an error: {str(e)}. Please try rephrasing your question."
                return

        try:
            # Build conversation context with session memory
            messages = self.build_conversation_context(session_id, message)
            
            # Add user message to memory before streaming
            self.add_to_session_memory(session_id, 'user', message)
            
            # Stream response from LLM (synchronous)
            full_response = ""
            for chunk in self.llm.stream(messages):
                if chunk.content:
                    full_response += chunk.content
                    yield chunk.content
            
            # Add complete assistant response to memory
            if full_response:
                self.add_to_session_memory(session_id, 'assistant', full_response)

        except Exception as e:
            error_msg = f"I apologize, but I encountered an error: {str(e)}. Please try rephrasing your question."
            self.add_to_session_memory(session_id, 'user', message)
            self.add_to_session_memory(session_id, 'assistant', error_msg)
            yield error_msg
    
    def chat(self, message: str, session_id: str = "default") -> str:
        """Enhanced chat with session-based conversation memory"""
        # If LangChain isn't available, route to existing RAG implementation
        if not HAS_LANGCHAIN:
            try:
                from ml_legal_system.legal_rag import answer_legal_query
                out = answer_legal_query(message)
                if isinstance(out, dict):
                    return out.get('response') or out.get('answer') or str(out)
                return str(out)
            except Exception as e:
                # If RAG fails, try a simpler fallback
                try:
                    # Import basic fallback function from app
                    import sys
                    import os
                    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                    from app import get_basic_fallback_response
                    return get_basic_fallback_response(message)
                except Exception:
                    return f"I apologize, but I encountered an error: {str(e)}. Please try rephrasing your question."

        try:
            # Build conversation context with session memory
            messages = self.build_conversation_context(session_id, message)
            
            # Get response from LLM
            response = self.llm.invoke(messages)
            response_content = response.content
            
            # Add to conversation memory
            self.add_to_session_memory(session_id, 'user', message)
            self.add_to_session_memory(session_id, 'assistant', response_content)
            
            return response_content

        except Exception as e:
            error_msg = f"I apologize, but I encountered an error: {str(e)}. Please try rephrasing your question."
            # Still add the user message to memory for context
            self.add_to_session_memory(session_id, 'user', message)
            self.add_to_session_memory(session_id, 'assistant', error_msg)
            return error_msg
    
    def generate_answer(self, query: str, user_id: str = None, conversation: list = None, stream: bool = False, session_id: str = None) -> Dict[str, any]:
        """Main interface method expected by Flask endpoint with enhanced memory support.
        Returns a dict: { 'response': str, 'sources': list } or generator if stream=True
        """
        try:
            # Use provided session_id or generate from user_id
            effective_session_id = session_id or user_id or "default"
            
            # Handle streaming mode
            if stream:
                return self._generate_streaming_answer(query, effective_session_id)
            
            # Non-streaming mode
            response_text = self.chat(query, session_id=effective_session_id)
            
            # Try to extract sources if we used the RAG fallback path
            sources = []
            if not HAS_LANGCHAIN:
                # When falling back to RAG, try to get sources from the last call
                try:
                    from ml_legal_system.legal_rag import answer_legal_query
                    result = answer_legal_query(query)
                    if isinstance(result, dict):
                        sources = result.get('sources', [])
                except Exception:
                    pass
            
            return {
                'response': response_text,
                'sources': sources,
                'session_id': effective_session_id
            }
        except Exception as e:
            return {
                'response': f"I apologize, but I encountered an error: {str(e)}. Please try rephrasing your question.",
                'sources': [],
                'session_id': session_id or user_id or "default"
            }
    
    def _generate_streaming_answer(self, query: str, session_id: str):
        """Generator function for streaming responses"""
        try:
            full_response = ""
            sources = []
            
            # Stream the response
            for chunk in self.chat_stream_sync(query, session_id):
                full_response += chunk
                yield {
                    'chunk': chunk,
                    'type': 'content',
                    'session_id': session_id
                }
            
            # Send final completion signal
            yield {
                'chunk': '',
                'type': 'complete',
                'session_id': session_id,
                'full_response': full_response,
                'sources': sources
            }
            
        except Exception as e:
            yield {
                'chunk': f"I apologize, but I encountered an error: {str(e)}",
                'type': 'error',
                'session_id': session_id
            }
    
    def clear_memory(self, session_id: str = "default"):
        """Clear conversation memory for backward compatibility"""
        self.clear_session_memory(session_id)
    
    def get_conversation_summary(self, session_id: str = "default") -> str:
        """Get summary of conversation for a specific session"""
        history = self.get_session_memory(session_id)
        if not history:
            return "No conversation history."
        
        user_messages = len([msg for msg in history if msg['role'] == 'user'])
        assistant_messages = len([msg for msg in history if msg['role'] == 'assistant'])
        
        return f"Session {session_id}: {user_messages} user messages, {assistant_messages} assistant responses."
    
    def get_session_stats(self, session_id: str = "default") -> Dict:
        """Get detailed statistics for a session"""
        history = self.get_session_memory(session_id)
        
        if not history:
            return {
                'session_id': session_id,
                'total_messages': 0,
                'user_messages': 0,
                'assistant_messages': 0,
                'last_activity': None
            }
        
        user_messages = [msg for msg in history if msg['role'] == 'user']
        assistant_messages = [msg for msg in history if msg['role'] == 'assistant']
        
        return {
            'session_id': session_id,
            'total_messages': len(history),
            'user_messages': len(user_messages),
            'assistant_messages': len(assistant_messages),
            'last_user_message': user_messages[-1]['content'][:100] + "..." if user_messages else None,
            'conversation_active': len(history) > 0
        }

# Usage example
if __name__ == "__main__":
    assistant = ModernLegalAssistant()
    
    # Test conversation
    response1 = assistant.chat("What are the legal provisions for detention in India?")
    print("Response 1:", response1[:200] + "...")
    
    # Follow-up with context
    response2 = assistant.chat("Can you explain more about Article 22?")
    print("Response 2:", response2[:200] + "...")