"""
Database models for LegalAssist Pro
Handles user authentication and chat storage
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

db = SQLAlchemy()

class User(db.Model):
    """User model for authentication and profile management"""
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship to chat sessions
    chat_sessions = db.relationship('ChatSession', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify the user's password"""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update the last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert user to dictionary for JSON response"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class ChatSession(db.Model):
    """Chat session model to group related messages"""
    __tablename__ = 'chat_sessions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=True)  # Auto-generated from first message
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship to messages
    messages = db.relationship('Message', backref='session', lazy=True, cascade='all, delete-orphan')
    
    def generate_title(self):
        """Generate session title from first user message"""
        first_message = Message.query.filter_by(
            session_id=self.id, 
            role='user'
        ).first()
        
        if first_message and first_message.content:
            # Take first 50 characters as title
            title = first_message.content[:50]
            if len(first_message.content) > 50:
                title += "..."
            self.title = title
            db.session.commit()
    
    def get_message_count(self):
        """Get total message count in this session"""
        return Message.query.filter_by(session_id=self.id).count()
    
    def to_dict(self, include_messages=False):
        """Convert session to dictionary for JSON response"""
        result = {
            'id': self.id,
            'title': self.title or 'New Chat',
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'message_count': self.get_message_count()
        }
        
        if include_messages:
            result['messages'] = [msg.to_dict() for msg in self.messages]
        
        return result

class Message(db.Model):
    """Individual chat message model"""
    __tablename__ = 'messages'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey('chat_sessions.id'), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Additional metadata
    tokens_used = db.Column(db.Integer, nullable=True)  # For API usage tracking
    model_used = db.Column(db.String(50), nullable=True)  # AI model version
    
    def to_dict(self):
        """Convert message to dictionary for JSON response"""
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'tokens_used': self.tokens_used,
            'model_used': self.model_used
        }

class UserSession(db.Model):
    """User session tracking for security"""
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    token_hash = db.Column(db.String(128), nullable=False)  # Hashed JWT token
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4/IPv6
    user_agent = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_revoked = db.Column(db.Boolean, default=False)
    
    # Relationship to user
    user = db.relationship('User', backref='sessions')
    
    def is_valid(self):
        """Check if session is still valid"""
        return not self.is_revoked and datetime.utcnow() < self.expires_at
    
    def revoke(self):
        """Revoke this session"""
        self.is_revoked = True
        db.session.commit()

def init_db(app):
    """Initialize database with app"""
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        print("✅ Database tables created successfully")
        
        # Create default admin user if doesn't exist
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@legalassist.pro',
                full_name='System Administrator'
            )
            admin_user.set_password('admin123')  # Change this in production!
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Default admin user created (username: admin, password: admin123)")

def create_sample_data():
    """Create sample data for testing"""
    # Create a test user
    test_user = User.query.filter_by(username='testuser').first()
    if not test_user:
        test_user = User(
            username='testuser',
            email='test@example.com',
            full_name='Test User'
        )
        test_user.set_password('password123')
        db.session.add(test_user)
        db.session.commit()
        
        # Create a sample chat session
        session = ChatSession(user_id=test_user.id)
        db.session.add(session)
        db.session.commit()
        
        # Add sample messages
        messages = [
            Message(
                session_id=session.id,
                role='user',
                content='What are my rights if I am arrested?'
            ),
            Message(
                session_id=session.id,
                role='assistant',
                content='When you are arrested, you have several important constitutional rights...'
            )
        ]
        
        for msg in messages:
            db.session.add(msg)
        
        db.session.commit()
        session.generate_title()
        
        print("✅ Sample test data created")