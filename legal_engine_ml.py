"""
Integration layer between Flask app and ML Legal System
Provides API endpoints for RAG-powered legal assistance
"""

import os
import sys
from typing import Dict, List, Optional

# Add ml_legal_system to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ml_legal_system'))

try:
    from ml_legal_system.legal_rag import LegalRAG
    from ml_legal_system.vector_db import LegalVectorDatabase
    from ml_legal_system.pinecone_vector_db import PineconeVectorDB
    from ml_legal_system.config import get_config
    ML_SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  ML system not available: {e}")
    ML_SYSTEM_AVAILABLE = False


class LegalEngine:
    """
    Enhanced legal engine with RAG capabilities
    Falls back to basic responses if ML system unavailable
    """
    
    def __init__(self):
        """Initialize legal engine"""
        self.ml_available = ML_SYSTEM_AVAILABLE
        self.rag = None
        self.use_pinecone = os.getenv('PINECONE_API_KEY') is not None
        
        if self.ml_available:
            try:
                # Use Pinecone in production, ChromaDB for local dev
                if self.use_pinecone:
                    print("🌐 Using Pinecone cloud vector database")
                    vector_db = PineconeVectorDB()
                else:
                    print("💻 Using ChromaDB local vector database")
                    vector_db = LegalVectorDatabase()
                
                self.rag = LegalRAG(use_openai=False, vector_db=vector_db)
                print("✅ ML-powered Legal Engine initialized")
            except Exception as e:
                print(f"⚠️  Could not initialize RAG: {e}")
                self.ml_available = False
                print("📝 Using basic legal responses")
    
    def get_legal_response(self, query: str, user_context: Dict = None) -> Dict:
        """
        Get legal response for query
        
        Args:
            query: User's legal question
            user_context: Optional user context (history, preferences)
            
        Returns:
            Dictionary with response, sources, and metadata
        """
        if self.ml_available and self.rag:
            return self._get_rag_response(query)
        else:
            return self._get_basic_response(query)
    
    def _get_rag_response(self, query: str) -> Dict:
        """Get RAG-powered response with case citations"""
        try:
            result = self.rag.answer_legal_query(query, top_k=5)
            
            # Format response
            return {
                'response': result['answer'],
                'sources': [
                    {
                        'title': case['title'],
                        'court': case['court'],
                        'date': case['date'],
                        'url': case.get('url', ''),
                        'relevance': f"{case['relevance_score']:.0%}"
                    }
                    for case in result['sources']
                ],
                'type': 'rag',
                'timestamp': result['timestamp']
            }
            
        except Exception as e:
            print(f"❌ RAG error: {e}")
            return self._get_basic_response(query)
    
    def _get_basic_response(self, query: str) -> Dict:
        """Fallback basic response without ML"""
        
        # Simple keyword-based responses
        query_lower = query.lower()
        
        if 'contract' in query_lower:
            response = """**Contract Law in India:**

Under the Indian Contract Act, 1872:
- A contract must have offer, acceptance, consideration, and lawful object
- Breach of contract can lead to compensation for losses
- Specific performance may be ordered by courts
- Damages are calculated based on actual loss

**Relevant Sections:**
- Section 73: Compensation for loss
- Section 74: Compensation for breach
- Section 10: Valid contract requirements

For specific advice, please consult a lawyer with your contract details."""

        elif 'property' in query_lower or 'real estate' in query_lower:
            response = """**Property Law in India:**

Key Points:
- Property transactions governed by Transfer of Property Act, 1882
- Registration is mandatory under Registration Act, 1908
- Property inheritance follows personal laws (Hindu, Muslim, Christian)
- Adverse possession after 12 years continuous possession

**Important Acts:**
- Transfer of Property Act, 1882
- Registration Act, 1908
- Real Estate (Regulation and Development) Act, 2016

Consult a property lawyer for specific cases."""

        elif 'divorce' in query_lower or 'marriage' in query_lower:
            response = """**Family Law in India:**

Divorce Grounds (vary by religion):
- Hindu Marriage Act, 1955: Adultery, cruelty, desertion, conversion
- Special Marriage Act, 1954: Similar grounds
- Muslim Personal Law: Talaq, Khula
- Christian Marriage Act: Similar to Hindu law

**Child Custody:**
- Best interest of child is paramount
- Mother usually preferred for young children

Seek family law expert advice."""

        elif 'criminal' in query_lower:
            response = """**Criminal Law in India:**

Governed by Indian Penal Code, 1860:
- Criminal offenses defined with punishments
- Criminal Procedure Code, 1973 for procedures
- Evidence Act, 1872 for evidence rules

**Key Rights:**
- Right to legal representation
- Right against self-incrimination
- Right to bail (in bailable offenses)
- Right to fair trial

Contact a criminal lawyer immediately."""

        else:
            response = """**General Legal Information:**

I can help with questions about:
- Contract law
- Property disputes
- Family law (divorce, custody)
- Criminal law
- Consumer rights
- Employment law
- Intellectual property

Please provide more specific details about your legal issue.

**Disclaimer:** This is general information, not legal advice. Consult a qualified lawyer for your specific case."""

        return {
            'response': response,
            'sources': [],
            'type': 'basic',
            'timestamp': None
        }
    
    def search_cases(self, query: str, filters: Dict = None) -> List[Dict]:
        """
        Search legal cases directly
        
        Args:
            query: Search query
            filters: Optional filters (court, date, etc.)
            
        Returns:
            List of matching cases
        """
        if not self.ml_available:
            return []
        
        try:
            db = LegalVectorDatabase(use_cloud=False)
            results = db.search_similar_cases(query, top_k=10, filters=filters)
            
            return [
                {
                    'title': case['metadata']['title'],
                    'court': case['metadata']['court'],
                    'date': case['metadata']['date'],
                    'excerpt': case.get('document', '')[:300],
                    'relevance': 1 - case.get('distance', 0)
                }
                for case in results
            ]
            
        except Exception as e:
            print(f"❌ Case search error: {e}")
            return []
    
    def get_system_status(self) -> Dict:
        """Get status of ML system"""
        return {
            'ml_available': self.ml_available,
            'rag_initialized': self.rag is not None,
            'features': {
                'case_search': self.ml_available,
                'rag_responses': self.ml_available and self.rag is not None,
                'citations': self.ml_available
            }
        }


# Singleton instance
_legal_engine = None


def get_legal_engine() -> LegalEngine:
    """Get or create legal engine instance"""
    global _legal_engine
    
    if _legal_engine is None:
        _legal_engine = LegalEngine()
    
    return _legal_engine


# For backward compatibility with existing app_with_db.py
def get_legal_response(query: str) -> str:
    """
    Get legal response (backward compatible)
    
    Args:
        query: User's legal question
        
    Returns:
        Response text
    """
    engine = get_legal_engine()
    result = engine.get_legal_response(query)
    
    response_text = result['response']
    
    # Add citations if available
    if result['sources']:
        response_text += "\n\n**📚 Cited Cases:**\n"
        for i, source in enumerate(result['sources'][:3], 1):
            response_text += f"\n{i}. {source['title']}"
            response_text += f"\n   {source['court']} | {source['date']}"
            response_text += f"\n   Relevance: {source['relevance']}\n"
    
    return response_text


if __name__ == "__main__":
    """Test the legal engine"""
    print("🧪 Testing Legal Engine Integration")
    print("=" * 60)
    
    engine = get_legal_engine()
    
    # Check status
    status = engine.get_system_status()
    print(f"\n📊 System Status:")
    print(f"  ML Available: {status['ml_available']}")
    print(f"  RAG Initialized: {status['rag_initialized']}")
    
    # Test query
    test_query = "What is the penalty for breach of contract in India?"
    print(f"\n🔍 Test Query: {test_query}")
    print("-" * 60)
    
    result = engine.get_legal_response(test_query)
    
    print(f"\n💡 Response:")
    print(result['response'][:500] + "...")
    
    if result['sources']:
        print(f"\n📚 Sources: {len(result['sources'])} cases")
        for source in result['sources'][:2]:
            print(f"  - {source['title']}")
    
    print("\n" + "=" * 60)
    print("✅ Integration test complete!")