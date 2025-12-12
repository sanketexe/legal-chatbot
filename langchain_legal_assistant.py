"""
LangChain-Enhanced Legal Assistant
Integrates LangChain for improved document processing and RAG capabilities
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseRetriever

# Standard imports
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

@dataclass
class LegalChatConfig:
    """Configuration for LangChain legal chat system"""
    model_name: str = "gemini-pro"
    temperature: float = 0.7
    max_tokens: int = 1000
    chunk_size: int = 1000
    chunk_overlap: int = 200
    memory_window: int = 10
    vector_db_path: str = "./data/langchain_vectordb"

class LegalPromptTemplates:
    """Standardized prompt templates for legal queries"""
    
    LEGAL_ANALYSIS = """
    You are an expert legal advisor specializing in Indian law. Analyze the following legal query and provide comprehensive guidance.
    
    Context from Legal Database:
    {context}
    
    Chat History:
    {chat_history}
    
    Current Question: {question}
    
    Please provide:
    1. **Legal Analysis**: Detailed explanation of the legal issue
    2. **Relevant Laws**: Applicable statutes, regulations, and case law
    3. **Precedents**: Relevant legal precedents and court decisions
    4. **Practical Advice**: Step-by-step guidance
    5. **Disclaimers**: Important legal disclaimers
    
    Response:
    """
    
    DOCUMENT_ANALYSIS = """
    You are a legal document analyst. Analyze the following document content and provide insights.
    
    Document Content:
    {document_content}
    
    User Query: {query}
    
    Please provide:
    1. **Document Summary**: Key points and clauses
    2. **Legal Issues**: Potential legal concerns or risks
    3. **Recommendations**: Suggested actions or modifications
    4. **Compliance**: Regulatory compliance aspects
    
    Analysis:
    """
    
    CASE_RESEARCH = """
    You are a legal researcher. Based on the provided case law and legal precedents, answer the following query.
    
    Relevant Cases:
    {cases}
    
    Query: {query}
    
    Provide:
    1. **Case Summary**: Key findings from relevant cases
    2. **Legal Principles**: Established legal principles
    3. **Application**: How these apply to the current situation
    4. **Citations**: Proper legal citations
    
    Research Results:
    """

class LangChainLegalAssistant:
    """Enhanced Legal Assistant using LangChain"""
    
    def __init__(self, config: LegalChatConfig, api_key: str):
        self.config = config
        self.api_key = api_key
        
        # Initialize LLM
        self.llm = self._setup_llm()
        
        # Initialize embeddings
        self.embeddings = self._setup_embeddings()
        
        # Initialize vector store
        self.vectorstore = self._setup_vectorstore()
        
        # Initialize memory
        self.memory = self._setup_memory()
        
        # Initialize chains
        self.qa_chain = self._setup_qa_chain()
        
        logger.info("🔗 LangChain Legal Assistant initialized successfully")
    
    def _setup_llm(self) -> ChatGoogleGenerativeAI:
        """Setup Google Gemini LLM"""
        return ChatGoogleGenerativeAI(
            model=self.config.model_name,
            google_api_key=self.api_key,
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_tokens
        )
    
    def _setup_embeddings(self) -> HuggingFaceEmbeddings:
        """Setup embeddings for vector store"""
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    
    def _setup_vectorstore(self) -> Chroma:
        """Setup ChromaDB vector store"""
        return Chroma(
            persist_directory=self.config.vector_db_path,
            embedding_function=self.embeddings
        )
    
    def _setup_memory(self) -> ConversationBufferWindowMemory:
        """Setup conversation memory"""
        return ConversationBufferWindowMemory(
            k=self.config.memory_window,
            memory_key="chat_history",
            return_messages=True
        )
    
    def _setup_qa_chain(self) -> ConversationalRetrievalChain:
        """Setup the main QA chain"""
        return ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 5}),
            memory=self.memory,
            return_source_documents=True
        )
    
    def process_documents(self, file_paths: List[str]) -> List[Document]:
        """Process and add documents to vector store"""
        documents = []
        
        for file_path in file_paths:
            try:
                # Load document based on file type
                if file_path.endswith('.pdf'):
                    loader = PyPDFLoader(file_path)
                elif file_path.endswith('.docx'):
                    loader = Docx2txtLoader(file_path)
                else:
                    logger.warning(f"Unsupported file type: {file_path}")
                    continue
                
                # Load and split documents
                docs = loader.load()
                
                # Split documents into chunks
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=self.config.chunk_size,
                    chunk_overlap=self.config.chunk_overlap
                )
                
                split_docs = text_splitter.split_documents(docs)
                
                # Add metadata
                for doc in split_docs:
                    doc.metadata.update({
                        'source_file': file_path,
                        'processed_date': datetime.now().isoformat(),
                        'document_type': 'legal_document'
                    })
                
                documents.extend(split_docs)
                
            except Exception as e:
                logger.error(f"Error processing document {file_path}: {e}")
        
        # Add to vector store
        if documents:
            self.vectorstore.add_documents(documents)
            logger.info(f"Added {len(documents)} document chunks to vector store")
        
        return documents
    
    def legal_chat(self, query: str, session_id: str = None) -> Dict[str, Any]:
        """Main legal chat interface"""
        try:
            # Run the conversational chain
            result = self.qa_chain({
                "question": query,
                "chat_history": self.memory.chat_memory.messages
            })
            
            response = {
                "answer": result["answer"],
                "source_documents": [
                    {
                        "content": doc.page_content[:200] + "...",
                        "source": doc.metadata.get("source", "Unknown"),
                        "page": doc.metadata.get("page", "N/A")
                    }
                    for doc in result.get("source_documents", [])
                ],
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error in legal chat: {e}")
            return {
                "answer": "I apologize, but I'm having trouble processing your request. Please try again.",
                "error": str(e),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def analyze_document(self, document_content: str, query: str = "Analyze this document") -> str:
        """Analyze a specific document"""
        prompt = PromptTemplate(
            template=LegalPromptTemplates.DOCUMENT_ANALYSIS,
            input_variables=["document_content", "query"]
        )
        
        chain = prompt | self.llm | StrOutputParser()
        
        return chain.invoke({
            "document_content": document_content,
            "query": query
        })
    
    def research_case_law(self, query: str) -> str:
        """Research relevant case law"""
        # Retrieve relevant cases
        retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": 10, "filter": {"document_type": "case_law"}}
        )
        
        relevant_docs = retriever.get_relevant_documents(query)
        cases = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        prompt = PromptTemplate(
            template=LegalPromptTemplates.CASE_RESEARCH,
            input_variables=["cases", "query"]
        )
        
        chain = prompt | self.llm | StrOutputParser()
        
        return chain.invoke({
            "cases": cases,
            "query": query
        })
    
    def get_legal_advice(self, query: str, context_docs: List[str] = None) -> str:
        """Get comprehensive legal advice"""
        # Get context from vector store if not provided
        if not context_docs:
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": 5})
            relevant_docs = retriever.get_relevant_documents(query)
            context = "\n\n".join([doc.page_content for doc in relevant_docs])
        else:
            context = "\n\n".join(context_docs)
        
        chat_history = "\n".join([
            f"{msg.type}: {msg.content}"
            for msg in self.memory.chat_memory.messages[-6:]  # Last 3 exchanges
        ])
        
        prompt = PromptTemplate(
            template=LegalPromptTemplates.LEGAL_ANALYSIS,
            input_variables=["context", "chat_history", "question"]
        )
        
        chain = prompt | self.llm | StrOutputParser()
        
        return chain.invoke({
            "context": context,
            "chat_history": chat_history,
            "question": query
        })
    
    def clear_memory(self):
        """Clear conversation memory"""
        self.memory.clear()
        logger.info("Conversation memory cleared")
    
    def save_session(self, session_id: str, filename: str = None):
        """Save conversation session"""
        if not filename:
            filename = f"legal_session_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        session_data = {
            "session_id": session_id,
            "messages": [
                {
                    "type": msg.type,
                    "content": msg.content,
                    "timestamp": getattr(msg, 'timestamp', datetime.now().isoformat())
                }
                for msg in self.memory.chat_memory.messages
            ],
            "saved_at": datetime.now().isoformat()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Session saved to {filename}")
        return filename

# Factory function
def create_langchain_legal_assistant(api_key: str, config: LegalChatConfig = None) -> LangChainLegalAssistant:
    """Create and initialize LangChain Legal Assistant"""
    if not config:
        config = LegalChatConfig()
    
    return LangChainLegalAssistant(config, api_key)

# Example usage
if __name__ == "__main__":
    # Example configuration
    config = LegalChatConfig(
        model_name="gemini-pro",
        temperature=0.7,
        chunk_size=1000,
        memory_window=10
    )
    
    # Initialize assistant (replace with your API key)
    assistant = create_langchain_legal_assistant("your_api_key_here", config)
    
    # Example legal consultation
    response = assistant.legal_chat("What are the requirements for a valid contract in Indian law?")
    print(response["answer"])