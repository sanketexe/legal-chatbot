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

# Try to import LangChain pieces lazily. If imports fail, we set HAS_LANGCHAIN=False
HAS_LANGCHAIN = True
try:
    from langchain.chat_models import ChatOpenAI  # type: ignore
    from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore
    from langchain.memory import ConversationBufferWindowMemory  # type: ignore
    from langchain.schema import HumanMessage, AIMessage, SystemMessage  # type: ignore
    from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler  # type: ignore
    from langchain.tools import Tool  # type: ignore
    from langchain.agents import initialize_agent, AgentType  # type: ignore
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder  # type: ignore
    from langchain.schema.runnable import RunnableLambda, RunnablePassthrough  # type: ignore
    from langchain.memory.chat_message_histories import ChatMessageHistory  # type: ignore
except Exception:
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
        """Initialize chat models with streaming"""
        if not HAS_LANGCHAIN:
            raise RuntimeError("LangChain not available")

        # Primary: Gemini (cost-effective)
        if os.getenv('GEMINI_API_KEY'):
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                google_api_key=os.getenv('GEMINI_API_KEY'),
                temperature=0.7,
                streaming=True,
                callbacks=[StreamingStdOutCallbackHandler()]
            )
            print("✅ Using Gemini Chat Model")

        # Fallback: OpenAI
        elif os.getenv('OPENAI_API_KEY'):
            self.llm = ChatOpenAI(
                model="gpt-4",
                openai_api_key=os.getenv('OPENAI_API_KEY'),
                temperature=0.7,
                streaming=True,
                callbacks=[StreamingStdOutCallbackHandler()]
            )
            print("✅ Using OpenAI Chat Model")
        else:
            raise ValueError("No API keys found for LLM")
    
    def setup_memory(self):
        """Setup conversation memory"""
        self.memory = ConversationBufferWindowMemory(
            k=10,  # Remember last 10 exchanges
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        
    def setup_tools(self):
        """Setup legal tools"""
        self.tools = [
            Tool(
                name="legal_database_search",
                description="Search legal cases and precedents in the database",
                func=self._search_legal_database
            ),
            Tool(
                name="legal_framework_lookup", 
                description="Look up legal acts, sections, and constitutional provisions",
                func=self._lookup_legal_framework
            ),
            Tool(
                name="current_legal_news",
                description="Get information about current legal events and cases",
                func=self._get_current_legal_info
            )
        ]
    
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
            MessagesPlaceholder(variable_name="chat_history"),
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
    
    async def chat_stream(self, message: str, session_id: str = "default"):
        """Stream response with conversation memory"""
        # If LangChain streaming is not available, fall back to a single non-streaming reply
        if not HAS_LANGCHAIN:
            try:
                from ml_legal_system.legal_rag import answer_legal_query
                out = answer_legal_query(message)
                if isinstance(out, dict):
                    text = out.get('response') or out.get('answer') or str(out)
                else:
                    text = str(out)
                yield text
            except Exception as e:
                # Try basic fallback
                try:
                    import sys
                    import os
                    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                    from app import get_basic_fallback_response
                    yield get_basic_fallback_response(message)
                except Exception:
                    yield f"I apologize, but I encountered an error: {str(e)}. Please try rephrasing your question."
            return

        try:
            # Build conversation chain
            chain = (
                RunnablePassthrough.assign(
                    chat_history=lambda x: self.memory.chat_memory.messages
                )
                | self.prompt_template
                | self.llm
            )

            # Stream response
            full_response = ""
            async for chunk in chain.astream({"input": message}):
                if hasattr(chunk, 'content'):
                    content = chunk.content
                    full_response += content
                    yield content

            # Save to memory
            if hasattr(self.memory, 'chat_memory'):
                self.memory.chat_memory.add_user_message(message)
                self.memory.chat_memory.add_ai_message(full_response)

        except Exception as e:
            error_msg = f"I apologize, but I encountered an error: {str(e)}. Please try rephrasing your question."
            yield error_msg
    
    def chat(self, message: str, session_id: str = "default") -> str:
        """Non-streaming chat for compatibility"""
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
            # Use the prompt template with memory
            messages = [
                SystemMessage(content=self.system_prompt),
                *self.memory.chat_memory.messages,
                HumanMessage(content=message)
            ]

            response = self.llm(messages)

            # Save to memory
            self.memory.chat_memory.add_user_message(message)
            self.memory.chat_memory.add_ai_message(response.content)

            return response.content

        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}. Please try rephrasing your question."
    
    def generate_answer(self, query: str, user_id: str = None, conversation: list = None, stream: bool = False) -> Dict[str, any]:
        """Main interface method expected by Flask endpoint. 
        Returns a dict: { 'response': str, 'sources': list }
        """
        try:
            response_text = self.chat(query, session_id=user_id or "default")
            
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
                'sources': sources
            }
        except Exception as e:
            return {
                'response': f"I apologize, but I encountered an error: {str(e)}. Please try rephrasing your question.",
                'sources': []
            }
    
    def clear_memory(self, session_id: str = "default"):
        """Clear conversation memory"""
        if self.memory:
            self.memory.clear()
    
    def get_conversation_summary(self) -> str:
        """Get summary of current conversation"""
        if not self.memory.chat_memory.messages:
            return "No conversation history."
        
        return f"Conversation has {len(self.memory.chat_memory.messages)} messages."

# Usage example
if __name__ == "__main__":
    assistant = ModernLegalAssistant()
    
    # Test conversation
    response1 = assistant.chat("What are the legal provisions for detention in India?")
    print("Response 1:", response1[:200] + "...")
    
    # Follow-up with context
    response2 = assistant.chat("Can you explain more about Article 22?")
    print("Response 2:", response2[:200] + "...")