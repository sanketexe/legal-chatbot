"""
Integration layer between Flask app and ML Legal System
Provides API endpoints for RAG-powered legal assistance
"""

import os
import sys
from typing import Dict, List, Optional

# Add ml_legal_system to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ml_legal_system'))

# Import conversation manager for context-aware responses
from conversation_manager import ConversationManager

try:
    from ml_legal_system.legal_rag import LegalRAG
    from ml_legal_system.vector_db import LegalVectorDatabase
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
        # Force use of ChromaDB for now since Pinecone index appears empty
        self.use_pinecone = False  # Temporarily disabled
        
        # Initialize conversation manager
        self.conversation_manager = ConversationManager()
        
        if self.ml_available:
            try:
                # Use ChromaDB local vector database (has data)
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
        Get legal response for query with conversation context
        
        Args:
            query: User's legal question
            user_context: Optional context with:
                - session_id: Conversation session identifier
                - user_id: User identifier
                - other metadata
            
        Returns:
            Dictionary with response, sources, session_id, and metadata
        """
        # Extract or create session
        session_id = None
        session = None
        
        if user_context and 'session_id' in user_context:
            session_id = user_context['session_id']
            session = self.conversation_manager.get_session(session_id)
        
        # Create new session if needed
        if not session:
            session = self.conversation_manager.create_session()
            session_id = session.session_id
        
        # Get context-enhanced query for RAG
        enhanced_query = session.get_context_for_query(query) if session else query
        
        # Get response from RAG or basic system
        if self.ml_available and self.rag:
            result = self._get_rag_response(enhanced_query, original_query=query)
        else:
            result = self._get_basic_response(query)
        
        # Add conversation exchange to history
        if session:
            session.add_message('user', query)
            session.add_message('assistant', result['response'], metadata={
                'sources_count': len(result.get('sources', [])),
                'type': result.get('type', 'unknown')
            })
            # Save session after adding messages
            self.conversation_manager._save_session(session)
        
        # Add session_id to result
        result['session_id'] = session_id
        result['conversation_context'] = session.context.to_dict() if session and session.context else None
        
        return result
    
    def _get_rag_response(self, query: str, original_query: str = None) -> Dict:
        """
        Get RAG-powered response with case citations
        
        Args:
            query: Enhanced query with conversation context
            original_query: Original user query (for display)
        """
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
        Search legal cases with advanced filters
        
        Args:
            query: Search query string
            filters: Optional dictionary with filters:
                - from_date: Start date (YYYY-MM-DD or YYYY)
                - to_date: End date (YYYY-MM-DD or YYYY)
                - courts: List of court names to filter
                - jurisdiction: Specific jurisdiction/state
                - legal_domain: Legal category (Criminal, Civil, Family, Property, etc.)
                - min_relevance: Minimum relevance score (0.0 to 1.0)
                - has_judges: Boolean, only cases with judge information
                - has_citations: Boolean, only cases with citations
                - top_k: Number of results (default 10, max 100)
                - sort_by: Sort field (relevance, date, court)
                - sort_order: asc or desc
            
        Returns:
            List of matching cases with metadata
        """
        if not self.ml_available:
            return []
        
        try:
            # Parse and validate filters
            parsed_filters = self._parse_search_filters(filters or {})
            
            # Get top_k from filters or use default
            top_k = parsed_filters.pop('top_k', 10)
            top_k = min(top_k, 100)  # Cap at 100
            
            # Extract post-processing filters
            min_relevance = parsed_filters.pop('min_relevance', 0.0)
            has_judges = parsed_filters.pop('has_judges', None)
            has_citations = parsed_filters.pop('has_citations', None)
            sort_by = parsed_filters.pop('sort_by', 'relevance')
            sort_order = parsed_filters.pop('sort_order', 'desc')
            legal_domain = parsed_filters.pop('legal_domain', None)
            
            # Search with vector database filters
            db = LegalVectorDatabase(use_cloud=False)
            results = db.search_similar_cases(query, top_k=top_k * 2, filters=parsed_filters)
            
            # Format and filter results
            formatted_results = []
            for case in results:
                metadata = case.get('metadata', {})
                relevance = 1 - case.get('distance', 0)
                
                # Apply relevance filter
                if relevance < min_relevance:
                    continue
                
                # Apply judge filter
                if has_judges and not metadata.get('judges'):
                    continue
                
                # Apply citation filter
                if has_citations:
                    citations = metadata.get('citations', '[]')
                    if not citations or citations == '[]':
                        continue
                
                # Apply legal domain filter (keyword-based)
                if legal_domain:
                    text_content = case.get('document', '').lower()
                    title = metadata.get('title', '').lower()
                    domain_keywords = self._get_domain_keywords(legal_domain)
                    
                    if not any(keyword in text_content or keyword in title for keyword in domain_keywords):
                        continue
                
                formatted_results.append({
                    'title': metadata.get('title', 'Untitled Case'),
                    'court': metadata.get('court', 'Unknown Court'),
                    'date': metadata.get('date', 'Unknown Date'),
                    'judges': metadata.get('judges', 'Not specified'),
                    'url': metadata.get('url', ''),
                    'excerpt': case.get('document', '')[:300],
                    'relevance': round(relevance, 4),
                    'citations': metadata.get('citations', '[]'),
                    'legal_acts': metadata.get('legal_acts', '[]'),
                    'search_query': metadata.get('search_query', '')
                })
            
            # Sort results
            formatted_results = self._sort_results(formatted_results, sort_by, sort_order)
            
            # Return top_k results after filtering
            return formatted_results[:top_k]
            
        except Exception as e:
            print(f"❌ Case search error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_search_filters(self, filters: Dict) -> Dict:
        """
        Parse and validate search filters
        
        Args:
            filters: Raw filter dictionary
            
        Returns:
            Parsed filter dictionary for ChromaDB
        """
        from datetime import datetime
        import json
        
        parsed = {}
        
        # Date range filters
        if 'from_date' in filters:
            try:
                # Support YYYY or YYYY-MM-DD format
                date_str = str(filters['from_date'])
                if len(date_str) == 4:  # Year only
                    parsed['from_year'] = date_str
                else:
                    # Parse full date
                    dt = datetime.strptime(date_str, '%Y-%m-%d')
                    parsed['from_year'] = str(dt.year)
            except ValueError:
                print(f"⚠️  Invalid from_date format: {filters['from_date']}")
        
        if 'to_date' in filters:
            try:
                date_str = str(filters['to_date'])
                if len(date_str) == 4:
                    parsed['to_year'] = date_str
                else:
                    dt = datetime.strptime(date_str, '%Y-%m-%d')
                    parsed['to_year'] = str(dt.year)
            except ValueError:
                print(f"⚠️  Invalid to_date format: {filters['to_date']}")
        
        # Court filters (passed through for ChromaDB)
        if 'courts' in filters and filters['courts']:
            parsed['courts'] = filters['courts']
        
        # Jurisdiction filter
        if 'jurisdiction' in filters and filters['jurisdiction']:
            parsed['jurisdiction'] = filters['jurisdiction']
        
        # Pass through remaining filters
        for key in ['top_k', 'min_relevance', 'has_judges', 'has_citations', 
                    'sort_by', 'sort_order', 'legal_domain']:
            if key in filters:
                parsed[key] = filters[key]
        
        return parsed
    
    def _get_domain_keywords(self, domain: str) -> List[str]:
        """
        Get keywords for legal domain filtering
        
        Args:
            domain: Legal domain name
            
        Returns:
            List of keywords
        """
        domain_map = {
            'Criminal': ['criminal', 'penal', 'ipc', 'crpc', 'murder', 'theft', 'assault', 
                        'cheating', 'fraud', 'bail', 'conviction', 'accused', 'prosecution'],
            'Civil': ['civil', 'suit', 'plaintiff', 'defendant', 'damages', 'injunction', 
                     'decree', 'cpc', 'contract', 'breach'],
            'Family': ['family', 'marriage', 'divorce', 'custody', 'maintenance', 'adoption', 
                      'succession', 'inheritance', 'matrimonial', 'alimony', 'child'],
            'Property': ['property', 'land', 'real estate', 'partition', 'possession', 
                        'ownership', 'lease', 'tenancy', 'title', 'immovable'],
            'Constitutional': ['constitutional', 'fundamental rights', 'article', 'writ', 
                             'habeas corpus', 'mandamus', 'certiorari', 'prohibition', 'quo warranto'],
            'Corporate': ['corporate', 'company', 'director', 'shareholder', 'securities', 
                         'merger', 'acquisition', 'corporate law', 'companies act'],
            'Tax': ['tax', 'income tax', 'gst', 'customs', 'excise', 'taxation', 
                   'revenue', 'assessment', 'tribunal'],
            'Labor': ['labor', 'labour', 'employment', 'industrial', 'worker', 'wages', 
                     'dismissal', 'retrenchment', 'trade union', 'workmen'],
            'Consumer': ['consumer', 'product', 'service', 'complaint', 'deficiency', 
                        'compensation', 'consumer protection'],
            'Environmental': ['environment', 'pollution', 'forest', 'wildlife', 'green', 
                            'ecology', 'environmental law']
        }
        
        return domain_map.get(domain, [domain.lower()])
    
    def _sort_results(self, results: List[Dict], sort_by: str, sort_order: str) -> List[Dict]:
        """
        Sort search results
        
        Args:
            results: List of case dictionaries
            sort_by: Field to sort by (relevance, date, court)
            sort_order: asc or desc
            
        Returns:
            Sorted list
        """
        reverse = (sort_order.lower() == 'desc')
        
        if sort_by == 'relevance':
            return sorted(results, key=lambda x: x.get('relevance', 0), reverse=reverse)
        elif sort_by == 'date':
            # Sort by date (handle various date formats)
            def get_sort_key(case):
                date_str = case.get('date', '')
                try:
                    # Extract year from date string
                    if '-' in date_str:
                        year = date_str.split('-')[0]
                    elif '/' in date_str:
                        parts = date_str.split('/')
                        year = parts[-1] if len(parts[-1]) == 4 else parts[0]
                    else:
                        year = date_str[:4] if len(date_str) >= 4 else '0000'
                    return int(year) if year.isdigit() else 0
                except:
                    return 0
            
            return sorted(results, key=get_sort_key, reverse=reverse)
        elif sort_by == 'court':
            return sorted(results, key=lambda x: x.get('court', ''), reverse=reverse)
        else:
            return results
    
    # Conversation Management Methods
    
    def create_conversation_session(self, metadata: Dict = None) -> str:
        """
        Create a new conversation session
        
        Args:
            metadata: Optional metadata (user_id, source, etc.) - Currently not used but kept for API compatibility
            
        Returns:
            Session ID
        """
        session = self.conversation_manager.create_session()
        return session.session_id
    
    def get_conversation_history(self, session_id: str, format_type: str = 'dict') -> Optional[Dict]:
        """
        Get conversation history for a session
        
        Args:
            session_id: Session identifier
            format_type: 'dict', 'formatted', or 'raw'
            
        Returns:
            Conversation history or None
        """
        session = self.conversation_manager.get_session(session_id)
        if not session:
            return None
        
        if format_type == 'formatted':
            return {'history': session.get_formatted_history()}
        elif format_type == 'raw':
            return {'messages': [msg.__dict__ for msg in session.get_history()]}
        else:
            return {
                'session_id': session_id,
                'created_at': session.created_at,
                'messages': [msg.to_dict() for msg in session.get_history()],
                'context': session.context.to_dict() if session.context else None
            }
    
    def get_conversation_context(self, session_id: str) -> Optional[Dict]:
        """
        Get conversation context summary
        
        Args:
            session_id: Session identifier
            
        Returns:
            Context dictionary or None
        """
        session = self.conversation_manager.get_session(session_id)
        if not session and session.context:
            return session.context.to_dict()
        return None
    
    def delete_conversation_session(self, session_id: str) -> bool:
        """
        Delete a conversation session
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False otherwise
        """
        return self.conversation_manager.delete_session(session_id)
    
    def list_active_sessions(self) -> List[Dict]:
        """
        Get list of all active conversation sessions
        
        Returns:
            List of session summaries
        """
        stats = self.conversation_manager.get_statistics()
        return {
            'total_sessions': stats['total_sessions'],
            'active_sessions': stats['active_sessions_24h'],
            'cached_sessions': stats['cached_sessions']
        }
    
    def get_system_status(self) -> Dict:
        """Get status of ML system and conversation manager"""
        conv_stats = self.conversation_manager.get_statistics()
        
        return {
            'ml_available': self.ml_available,
            'rag_initialized': self.rag is not None,
            'conversation_manager': {
                'available': True,
                'total_sessions': conv_stats['total_sessions'],
                'active_sessions': conv_stats['active_sessions_24h']
            },
            'features': {
                'case_search': self.ml_available,
                'rag_responses': self.ml_available and self.rag is not None,
                'citations': self.ml_available,
                'conversation_memory': True,
                'context_tracking': True
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