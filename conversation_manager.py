#!/usr/bin/env python3
"""
Legal Conversation Memory Management System
Handles multi-turn conversations with context preservation for legal consultations.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import deque
import sqlite3
from pathlib import Path


@dataclass
class Message:
    """Represents a single message in a conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Convert message to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        """Create message from dictionary."""
        return cls(**data)


@dataclass
class ConversationContext:
    """Represents the context extracted from conversation history."""
    legal_domain: Optional[str] = None
    mentioned_cases: List[str] = None
    mentioned_statutes: List[str] = None
    user_intent: Optional[str] = None
    key_entities: List[str] = None
    previous_questions: List[str] = None
    
    def __post_init__(self):
        """Initialize empty lists if None."""
        if self.mentioned_cases is None:
            self.mentioned_cases = []
        if self.mentioned_statutes is None:
            self.mentioned_statutes = []
        if self.key_entities is None:
            self.key_entities = []
        if self.previous_questions is None:
            self.previous_questions = []
    
    def to_dict(self) -> Dict:
        """Convert context to dictionary."""
        return asdict(self)
    
    def get_context_summary(self) -> str:
        """Get a text summary of the conversation context."""
        parts = []
        
        if self.legal_domain:
            parts.append(f"Legal Domain: {self.legal_domain}")
        
        if self.mentioned_cases:
            parts.append(f"Referenced Cases: {', '.join(self.mentioned_cases[:3])}")
        
        if self.mentioned_statutes:
            parts.append(f"Referenced Laws: {', '.join(self.mentioned_statutes[:3])}")
        
        if self.previous_questions:
            parts.append(f"Previous Questions: {len(self.previous_questions)}")
        
        return " | ".join(parts) if parts else "New conversation"


class ConversationSession:
    """Manages a single conversation session."""
    
    def __init__(self, session_id: Optional[str] = None, max_history: int = 20):
        """
        Initialize conversation session.
        
        Args:
            session_id: Unique session identifier (generated if not provided)
            max_history: Maximum number of messages to keep in memory
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.created_at = datetime.now().isoformat()
        self.last_activity = datetime.now().isoformat()
        self.max_history = max_history
        
        # Message history as deque for efficient operations
        self.messages: deque[Message] = deque(maxlen=max_history)
        
        # Conversation context
        self.context = ConversationContext()
        
        # Session metadata
        self.metadata = {
            'message_count': 0,
            'total_tokens': 0,
            'user_satisfaction': None,
            'legal_domains_discussed': set()
        }
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        Add a message to the conversation.
        
        Args:
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional metadata (case references, legal domain, etc.)
        """
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {}
        )
        
        self.messages.append(message)
        self.last_activity = datetime.now().isoformat()
        self.metadata['message_count'] += 1
        
        # Update context based on message
        self._update_context(message)
    
    def get_history(self, limit: Optional[int] = None) -> List[Message]:
        """
        Get conversation history.
        
        Args:
            limit: Maximum number of recent messages to return
            
        Returns:
            List of messages
        """
        messages = list(self.messages)
        if limit:
            messages = messages[-limit:]
        return messages
    
    def get_formatted_history(self, limit: Optional[int] = None, include_metadata: bool = False) -> str:
        """
        Get formatted conversation history as text.
        
        Args:
            limit: Maximum number of recent messages
            include_metadata: Whether to include message metadata
            
        Returns:
            Formatted conversation history
        """
        messages = self.get_history(limit)
        formatted = []
        
        for msg in messages:
            role_label = "User" if msg.role == "user" else "Assistant"
            formatted.append(f"{role_label}: {msg.content}")
            
            if include_metadata and msg.metadata:
                formatted.append(f"  [Metadata: {json.dumps(msg.metadata)}]")
        
        return "\n".join(formatted)
    
    def get_context_for_query(self, current_query: str) -> str:
        """
        Build context string for enhancing current query.
        
        Args:
            current_query: The current user query
            
        Returns:
            Context-enhanced query string
        """
        context_parts = []
        
        # Add conversation summary
        if self.messages:
            context_parts.append("### Conversation Context ###")
            context_parts.append(self.context.get_context_summary())
            context_parts.append("")
        
        # Add relevant previous exchanges
        recent_messages = self.get_history(limit=4)
        if recent_messages:
            context_parts.append("### Recent Discussion ###")
            for msg in recent_messages:
                role_prefix = "Q:" if msg.role == "user" else "A:"
                context_parts.append(f"{role_prefix} {msg.content[:200]}")
            context_parts.append("")
        
        # Add current query
        context_parts.append("### Current Question ###")
        context_parts.append(current_query)
        
        return "\n".join(context_parts)
    
    def _update_context(self, message: Message):
        """Update conversation context based on new message."""
        content_lower = message.content.lower()
        
        # Detect legal domain
        domain_keywords = {
            'property': ['property', 'land', 'partition', 'inheritance', 'ownership'],
            'corporate': ['company', 'corporate', 'shareholder', 'director', 'merger'],
            'criminal': ['criminal', 'bail', 'conviction', 'fir', 'police'],
            'family': ['divorce', 'custody', 'marriage', 'maintenance', 'alimony'],
            'constitutional': ['constitutional', 'fundamental', 'rights', 'article', 'writ'],
            'labor': ['labor', 'employment', 'termination', 'union', 'worker']
        }
        
        for domain, keywords in domain_keywords.items():
            if any(kw in content_lower for kw in keywords):
                self.context.legal_domain = domain.title() + " Law"
                self.metadata['legal_domains_discussed'].add(domain)
                break
        
        # Extract case references
        # Look for patterns like "ABC vs XYZ", "Case No. 123"
        import re
        case_patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:vs?\.?|versus)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(?:Case|Appeal|Petition)\s+(?:No\.?)?\s*(\d+)',
        ]
        
        for pattern in case_patterns:
            matches = re.findall(pattern, message.content, re.IGNORECASE)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        case_ref = " vs ".join(match) if len(match) > 1 else match[0]
                    else:
                        case_ref = match
                    if case_ref not in self.context.mentioned_cases:
                        self.context.mentioned_cases.append(case_ref)
        
        # Extract statute references
        statute_patterns = [
            r'Section\s+(\d+(?:[A-Z])?)',
            r'Article\s+(\d+)',
            r'Act[,\s]+(\d{4})',
        ]
        
        for pattern in statute_patterns:
            matches = re.findall(pattern, message.content, re.IGNORECASE)
            for match in matches:
                statute_ref = f"Section {match}" if 'Section' in pattern else f"Article {match}"
                if statute_ref not in self.context.mentioned_statutes:
                    self.context.mentioned_statutes.append(statute_ref)
        
        # Track user questions
        if message.role == "user":
            self.context.previous_questions.append(message.content[:100])
    
    def clear_history(self):
        """Clear conversation history while preserving session."""
        self.messages.clear()
        self.context = ConversationContext()
        self.metadata['message_count'] = 0
    
    def to_dict(self) -> Dict:
        """Convert session to dictionary for storage."""
        return {
            'session_id': self.session_id,
            'created_at': self.created_at,
            'last_activity': self.last_activity,
            'messages': [msg.to_dict() for msg in self.messages],
            'context': self.context.to_dict(),
            'metadata': {
                **self.metadata,
                'legal_domains_discussed': list(self.metadata['legal_domains_discussed'])
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConversationSession':
        """Create session from dictionary."""
        session = cls(session_id=data['session_id'])
        session.created_at = data['created_at']
        session.last_activity = data['last_activity']
        
        # Restore messages
        for msg_data in data['messages']:
            session.messages.append(Message.from_dict(msg_data))
        
        # Restore context
        session.context = ConversationContext(**data['context'])
        
        # Restore metadata
        metadata = data['metadata']
        metadata['legal_domains_discussed'] = set(metadata.get('legal_domains_discussed', []))
        session.metadata = metadata
        
        return session


class ConversationManager:
    """Manages multiple conversation sessions with persistence."""
    
    def __init__(self, db_path: str = "instance/conversations.db"):
        """
        Initialize conversation manager.
        
        Args:
            db_path: Path to SQLite database for persistence
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # In-memory session cache
        self.sessions: Dict[str, ConversationSession] = {}
        
        # Session timeout (in hours)
        self.session_timeout = 24
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for conversation storage."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                last_activity TEXT NOT NULL,
                session_data TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        # Create messages table for quick queries
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        ''')
        
        # Create indices
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_activity ON sessions(last_activity)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)')
        
        conn.commit()
        conn.close()
    
    def create_session(self) -> ConversationSession:
        """
        Create a new conversation session.
        
        Returns:
            New ConversationSession instance
        """
        session = ConversationSession()
        self.sessions[session.session_id] = session
        self._save_session(session)
        return session
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """
        Get an existing session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            ConversationSession if found, None otherwise
        """
        # Check in-memory cache first
        if session_id in self.sessions:
            return self.sessions[session_id]
        
        # Load from database
        session = self._load_session(session_id)
        if session:
            self.sessions[session_id] = session
            return session
        
        return None
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> ConversationSession:
        """
        Get existing session or create new one.
        
        Args:
            session_id: Optional session identifier
            
        Returns:
            ConversationSession instance
        """
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session
        
        return self.create_session()
    
    def add_exchange(self, session_id: str, user_message: str, assistant_response: str,
                    metadata: Optional[Dict] = None) -> bool:
        """
        Add a complete exchange (user message + assistant response) to session.
        
        Args:
            session_id: Session identifier
            user_message: User's message
            assistant_response: Assistant's response
            metadata: Optional metadata
            
        Returns:
            True if successful, False otherwise
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        # Add user message
        session.add_message('user', user_message, metadata)
        
        # Add assistant response
        session.add_message('assistant', assistant_response, metadata)
        
        # Save to database
        self._save_session(session)
        
        return True
    
    def get_session_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict]:
        """
        Get session history as list of dictionaries.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages
            
        Returns:
            List of message dictionaries
        """
        session = self.get_session(session_id)
        if not session:
            return []
        
        messages = session.get_history(limit)
        return [msg.to_dict() for msg in messages]
    
    def get_active_sessions(self, hours: int = 24) -> List[Dict]:
        """
        Get list of active sessions within specified hours.
        
        Args:
            hours: Number of hours to consider as active
            
        Returns:
            List of session summaries
        """
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT session_id, created_at, last_activity, session_data
            FROM sessions
            WHERE last_activity > ? AND is_active = 1
            ORDER BY last_activity DESC
        ''', (cutoff,))
        
        sessions = []
        for row in cursor.fetchall():
            session_data = json.loads(row[3])
            sessions.append({
                'session_id': row[0],
                'created_at': row[1],
                'last_activity': row[2],
                'message_count': session_data.get('metadata', {}).get('message_count', 0),
                'legal_domain': session_data.get('context', {}).get('legal_domain')
            })
        
        conn.close()
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        # Remove from cache
        if session_id in self.sessions:
            del self.sessions[session_id]
        
        # Mark as inactive in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE sessions SET is_active = 0 WHERE session_id = ?
        ''', (session_id,))
        
        conn.commit()
        conn.close()
        
        return True
    
    def cleanup_old_sessions(self, days: int = 30):
        """
        Clean up sessions older than specified days.
        
        Args:
            days: Number of days to keep sessions
        """
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete old messages
        cursor.execute('''
            DELETE FROM messages WHERE session_id IN (
                SELECT session_id FROM sessions WHERE last_activity < ?
            )
        ''', (cutoff,))
        
        # Delete old sessions
        cursor.execute('''
            DELETE FROM sessions WHERE last_activity < ?
        ''', (cutoff,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        print(f"Cleaned up {deleted_count} old sessions")
    
    def _save_session(self, session: ConversationSession):
        """Save session to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        session_data = json.dumps(session.to_dict())
        
        cursor.execute('''
            INSERT OR REPLACE INTO sessions 
            (session_id, created_at, last_activity, session_data, is_active)
            VALUES (?, ?, ?, ?, 1)
        ''', (session.session_id, session.created_at, session.last_activity, session_data))
        
        conn.commit()
        conn.close()
    
    def _load_session(self, session_id: str) -> Optional[ConversationSession]:
        """Load session from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT session_data FROM sessions 
            WHERE session_id = ? AND is_active = 1
        ''', (session_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            session_data = json.loads(row[0])
            return ConversationSession.from_dict(session_data)
        
        return None
    
    def get_statistics(self) -> Dict:
        """Get conversation statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total sessions
        cursor.execute('SELECT COUNT(*) FROM sessions WHERE is_active = 1')
        total_sessions = cursor.fetchone()[0]
        
        # Total messages
        cursor.execute('SELECT COUNT(*) FROM messages')
        total_messages = cursor.fetchone()[0]
        
        # Active sessions (last 24 hours)
        cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
        cursor.execute('SELECT COUNT(*) FROM sessions WHERE last_activity > ? AND is_active = 1', (cutoff,))
        active_sessions = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_sessions': total_sessions,
            'total_messages': total_messages,
            'active_sessions_24h': active_sessions,
            'cached_sessions': len(self.sessions)
        }


# Global conversation manager instance
conversation_manager = ConversationManager()


if __name__ == "__main__":
    # Test the conversation manager
    print("🧪 Testing Conversation Manager")
    print("="*50)
    
    # Create a session
    manager = ConversationManager("test_conversations.db")
    session = manager.create_session()
    
    print(f"✅ Created session: {session.session_id}")
    
    # Add some messages
    manager.add_exchange(
        session.session_id,
        "What is the law regarding property partition in India?",
        "In India, property partition is governed by various laws including the Hindu Succession Act, 1956..."
    )
    
    manager.add_exchange(
        session.session_id,
        "Can a daughter claim partition of ancestral property?",
        "Yes, after the 2005 amendment to the Hindu Succession Act, daughters have equal rights..."
    )
    
    # Get history
    history = manager.get_session_history(session.session_id)
    print(f"\n📜 Conversation History ({len(history)} messages):")
    for msg in history:
        print(f"  {msg['role']}: {msg['content'][:80]}...")
    
    # Get context
    print(f"\n📊 Conversation Context:")
    print(f"  {session.context.get_context_summary()}")
    
    # Statistics
    stats = manager.get_statistics()
    print(f"\n📈 Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print(f"\n✅ Conversation Manager test complete!")
