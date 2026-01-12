"""
Database models for LegalAssist Pro
Handles user authentication and chat storage
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from logging_config import get_logger

logger = get_logger(__name__)

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


class UserPreference(db.Model):
    """Store user preferences for personalization"""
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, unique=True, index=True)
    
    # Language and presentation
    preferred_language = db.Column(db.String(10), default='en')  # en, hi, ta, te
    response_detail_level = db.Column(db.Integer, default=2)     # 1-5 (1=brief, 5=detailed)
    
    # Legal interests
    legal_domains = db.Column(db.JSON, default=dict)  # {"family": 0.8, "property": 0.2}
    jurisdiction_preference = db.Column(db.String(50), default='all')  # "delhi", "mumbai", "all"
    
    # Settings
    include_case_summaries = db.Column(db.Boolean, default=True)
    include_act_references = db.Column(db.Boolean, default=True)
    notification_enabled = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='preferences', uselist=False)
    
    def to_dict(self):
        """Convert to JSON-serializable dict"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'preferred_language': self.preferred_language,
            'response_detail_level': self.response_detail_level,
            'legal_domains': self.legal_domains,
            'jurisdiction_preference': self.jurisdiction_preference,
            'include_case_summaries': self.include_case_summaries,
            'include_act_references': self.include_act_references,
            'notification_enabled': self.notification_enabled,
        }


class ResponseRating(db.Model):
    """Store user ratings for chat responses"""
    __tablename__ = 'response_ratings'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    message_id = db.Column(db.String(36), db.ForeignKey('messages.id'), nullable=True, index=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    feedback = db.Column(db.Text, nullable=True)  # Optional feedback text
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = db.relationship('User', backref='ratings')
    message = db.relationship('Message', backref='ratings')
    
    def to_dict(self):
        """Convert rating to dictionary for JSON response"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'message_id': self.message_id,
            'rating': self.rating,
            'feedback': self.feedback,
            'created_at': self.created_at.isoformat() if self.created_at else None
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
        
        logger.info("Database tables created successfully")
        
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
            logger.info("Default admin user created (username: admin, password: admin123)")

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
        
    logger.info("Sample test data created")


class CaseSummary(db.Model):
    """Cache for generated case summaries"""
    __tablename__ = 'case_summaries'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = db.Column(db.String(100), nullable=False, index=True)
    case_title = db.Column(db.String(500), nullable=True)
    
    # Summary content
    summary_text = db.Column(db.Text, nullable=False)
    facts = db.Column(db.Text, nullable=True)
    issues = db.Column(db.Text, nullable=True)
    reasoning = db.Column(db.Text, nullable=True)
    judgment = db.Column(db.Text, nullable=True)
    key_points = db.Column(db.JSON, nullable=True)  # List of key points
    
    # Summary metadata
    summary_type = db.Column(db.String(20), nullable=False)  # 'extractive', 'abstractive', 'hybrid'
    length = db.Column(db.String(10), nullable=False)  # 'short', 'medium', 'long'
    word_count = db.Column(db.Integer, nullable=True)
    
    # Case metadata
    court = db.Column(db.String(200), nullable=True)
    year = db.Column(db.String(10), nullable=True)
    
    # Audit fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    
    # Relationship
    creator = db.relationship('User', backref='summaries', foreign_keys=[created_by])
    
    def to_dict(self, include_details=True):
        """Convert summary to dictionary for JSON response"""
        result = {
            'id': self.id,
            'case_id': self.case_id,
            'case_title': self.case_title,
            'summary': self.summary_text,
            'type': self.summary_type,
            'length': self.length,
            'word_count': self.word_count,
            'court': self.court,
            'year': self.year,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_details:
            result.update({
                'facts': self.facts,
                'issues': self.issues,
                'reasoning': self.reasoning,
                'judgment': self.judgment,
                'key_points': self.key_points or []
            })
        
        return result
    
    @classmethod
    def get_by_case_id(cls, case_id: str, length: str = None, summary_type: str = None):
        """
        Get cached summary for a case
        
        Args:
            case_id: Case identifier
            length: Optional length filter
            summary_type: Optional type filter
        
        Returns:
            CaseSummary object or None
        """
        query = cls.query.filter_by(case_id=case_id)
        
        if length:
            query = query.filter_by(length=length)
        if summary_type:
            query = query.filter_by(summary_type=summary_type)
        
        # Return most recent
        return query.order_by(cls.created_at.desc()).first()
    
    @classmethod
    def cache_summary(cls, summary_data: dict, user_id: str = None):
        """
        Cache a generated summary
        
        Args:
            summary_data: Dictionary with summary information
            user_id: Optional user ID who generated the summary
        
        Returns:
            Created CaseSummary object
        """
        summary = cls(
            case_id=summary_data.get('case_id'),
            case_title=summary_data.get('title'),
            summary_text=summary_data.get('summary'),
            facts=summary_data.get('facts'),
            issues=summary_data.get('issues'),
            reasoning=summary_data.get('reasoning'),
            judgment=summary_data.get('judgment'),
            key_points=summary_data.get('key_points'),
            summary_type=summary_data.get('method', 'hybrid'),
            length=summary_data.get('length', 'medium'),
            word_count=summary_data.get('word_count'),
            court=summary_data.get('court'),
            year=summary_data.get('year'),
            created_by=user_id
        )
        
        db.session.add(summary)
        db.session.commit()
        
        logger.info(f"Cached summary for case {summary_data.get('case_id')}")
        return summary


class CasePrediction(db.Model):
    """Store ML predictions for case outcomes"""
    __tablename__ = 'case_predictions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Input data
    case_facts = db.Column(db.Text, nullable=False)
    case_issues = db.Column(db.Text, nullable=True)
    case_charges = db.Column(db.Text, nullable=True)
    court_type = db.Column(db.String(50), nullable=True)
    case_type = db.Column(db.String(50), nullable=True)
    
    # Prediction results
    predicted_outcome = db.Column(db.String(50), nullable=False)  # 'favorable', 'unfavorable', 'partial'
    confidence_score = db.Column(db.Float, nullable=False)  # 0-100
    confidence_level = db.Column(db.String(20), nullable=True)  # 'High', 'Medium', 'Low'
    
    # Additional prediction data
    reasoning = db.Column(db.JSON, nullable=True)  # List of contributing factors
    similar_cases = db.Column(db.JSON, nullable=True)  # Similar historical cases
    all_probabilities = db.Column(db.JSON, nullable=True)  # Probabilities for all outcomes
    
    # Model metadata
    model_version = db.Column(db.String(50), default='v1.0')
    rf_accuracy = db.Column(db.Float, nullable=True)
    xgb_accuracy = db.Column(db.Float, nullable=True)
    
    # User feedback (for model improvement)
    user_rating = db.Column(db.Integer, nullable=True)  # 1-5 stars
    was_accurate = db.Column(db.Boolean, nullable=True)  # Did prediction match actual outcome?
    actual_outcome = db.Column(db.String(50), nullable=True)  # If user provides actual result
    feedback_notes = db.Column(db.Text, nullable=True)
    
    # Audit fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationship
    user = db.relationship('User', backref='predictions', foreign_keys=[user_id])
    
    def to_dict(self, include_details=True):
        """Convert prediction to dictionary for JSON response"""
        result = {
            'id': self.id,
            'predicted_outcome': self.predicted_outcome,
            'confidence_score': round(self.confidence_score, 2),
            'confidence_level': self.confidence_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user_rating': self.user_rating,
            'was_accurate': self.was_accurate
        }
        
        if include_details:
            result.update({
                'case_facts': self.case_facts,
                'case_issues': self.case_issues,
                'case_charges': self.case_charges,
                'court_type': self.court_type,
                'case_type': self.case_type,
                'reasoning': self.reasoning or [],
                'similar_cases': self.similar_cases or [],
                'all_probabilities': self.all_probabilities or {},
                'model_version': self.model_version,
                'feedback_notes': self.feedback_notes
            })
        
        return result
    
    @classmethod
    def save_prediction(cls, user_id: str, case_input: dict, prediction_result: dict):
        """
        Save a prediction to database
        
        Args:
            user_id: User who made the prediction
            case_input: Dictionary with case details
            prediction_result: Dictionary with prediction results
        
        Returns:
            Created CasePrediction object
        """
        prediction = cls(
            user_id=user_id,
            case_facts=case_input.get('facts', ''),
            case_issues=case_input.get('issues', ''),
            case_charges=case_input.get('charges', ''),
            court_type=case_input.get('court', ''),
            case_type=case_input.get('case_type', ''),
            predicted_outcome=prediction_result.get('outcome'),
            confidence_score=prediction_result.get('confidence', 0),
            confidence_level=prediction_result.get('confidence_level'),
            reasoning=prediction_result.get('reasoning', []),
            similar_cases=prediction_result.get('similar_cases', []),
            all_probabilities=prediction_result.get('all_probabilities', {}),
            model_version='v1.0'
        )
        
        # Extract model accuracy if available
        model_acc = prediction_result.get('model_accuracy', {})
        if model_acc:
            prediction.rf_accuracy = float(model_acc.get('random_forest', '0%').replace('%', ''))
            prediction.xgb_accuracy = float(model_acc.get('xgboost', '0%').replace('%', ''))
        
        db.session.add(prediction)
        db.session.commit()
        
        logger.info(f"Saved prediction {prediction.id} for user {user_id}")
        return prediction
    
    def update_feedback(self, rating: int = None, was_accurate: bool = None, 
                       actual_outcome: str = None, notes: str = None):
        """Update user feedback on prediction accuracy"""
        if rating is not None:
            self.user_rating = rating
        if was_accurate is not None:
            self.was_accurate = was_accurate
        if actual_outcome:
            self.actual_outcome = actual_outcome
        if notes:
            self.feedback_notes = notes
        
        db.session.commit()
        logger.info(f"Updated feedback for prediction {self.id}")


class Bookmark(db.Model):
    """User bookmarks for cases, queries, and conversations"""
    __tablename__ = 'bookmarks'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Bookmark types: 'case', 'query', 'conversation', 'document'
    bookmark_type = db.Column(db.String(20), nullable=False, index=True)
    
    # Reference to bookmarked item
    item_id = db.Column(db.String(100), nullable=False, index=True)  # case_id, session_id, etc.
    item_title = db.Column(db.String(500), nullable=True)
    item_preview = db.Column(db.Text, nullable=True)  # Short preview/snippet
    
    # Bookmark organization
    folder = db.Column(db.String(100), default='default')  # User-defined folders
    tags = db.Column(db.JSON, nullable=True)  # List of tags
    notes = db.Column(db.Text, nullable=True)  # User notes
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    access_count = db.Column(db.Integer, default=0)
    is_favorite = db.Column(db.Boolean, default=False)  # Star/favorite flag
    
    # Relationship
    user = db.relationship('User', backref='bookmarks', foreign_keys=[user_id])
    
    def to_dict(self):
        """Convert bookmark to dictionary"""
        return {
            'id': self.id,
            'type': self.bookmark_type,
            'item_id': self.item_id,
            'title': self.item_title,
            'preview': self.item_preview,
            'folder': self.folder,
            'tags': self.tags or [],
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'access_count': self.access_count,
            'is_favorite': self.is_favorite
        }
    
    def update_access(self):
        """Update last accessed time and increment count"""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1
        db.session.commit()
    
    @classmethod
    def create_bookmark(cls, user_id: str, bookmark_type: str, item_id: str, 
                       title: str = None, preview: str = None, folder: str = 'default',
                       tags: list = None, notes: str = None):
        """Create a new bookmark"""
        # Check if bookmark already exists
        existing = cls.query.filter_by(
            user_id=user_id,
            bookmark_type=bookmark_type,
            item_id=item_id
        ).first()
        
        if existing:
            logger.info(f"Bookmark already exists for {bookmark_type}:{item_id}")
            return existing
        
        bookmark = cls(
            user_id=user_id,
            bookmark_type=bookmark_type,
            item_id=item_id,
            item_title=title,
            item_preview=preview,
            folder=folder,
            tags=tags or [],
            notes=notes
        )
        
        db.session.add(bookmark)
        db.session.commit()
        
        logger.info(f"Created bookmark {bookmark.id} for user {user_id}")
        return bookmark
    
    @classmethod
    def get_user_bookmarks(cls, user_id: str, bookmark_type: str = None, 
                          folder: str = None, favorites_only: bool = False):
        """Get user's bookmarks with optional filters"""
        query = cls.query.filter_by(user_id=user_id)
        
        if bookmark_type:
            query = query.filter_by(bookmark_type=bookmark_type)
        if folder:
            query = query.filter_by(folder=folder)
        if favorites_only:
            query = query.filter_by(is_favorite=True)
        
        return query.order_by(cls.created_at.desc()).all()


class ExportHistory(db.Model):
    """Track document exports for users"""
    __tablename__ = 'export_history'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Export details
    export_type = db.Column(db.String(20), nullable=False)  # 'conversation', 'case', 'research', 'document'
    export_format = db.Column(db.String(10), nullable=False)  # 'pdf', 'docx', 'txt', 'json'
    
    # Content reference
    content_id = db.Column(db.String(100), nullable=True)  # session_id, case_id, etc.
    content_title = db.Column(db.String(500), nullable=True)
    
    # File details
    filename = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)  # Size in bytes
    file_path = db.Column(db.String(1000), nullable=True)  # Storage path if saved
    
    # Export status
    status = db.Column(db.String(20), default='pending')  # 'pending', 'completed', 'failed'
    error_message = db.Column(db.Text, nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    download_count = db.Column(db.Integer, default=0)
    last_downloaded = db.Column(db.DateTime, nullable=True)
    
    # Relationship
    user = db.relationship('User', backref='exports', foreign_keys=[user_id])
    
    def to_dict(self):
        """Convert export record to dictionary"""
        return {
            'id': self.id,
            'export_type': self.export_type,
            'export_format': self.export_format,
            'content_id': self.content_id,
            'content_title': self.content_title,
            'filename': self.filename,
            'file_size': self.file_size,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'download_count': self.download_count,
            'last_downloaded': self.last_downloaded.isoformat() if self.last_downloaded else None
        }
    
    def mark_completed(self, file_size: int = None, file_path: str = None):
        """Mark export as completed"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        if file_size:
            self.file_size = file_size
        if file_path:
            self.file_path = file_path
        db.session.commit()
    
    def mark_failed(self, error_message: str):
        """Mark export as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        db.session.commit()
    
    def record_download(self):
        """Record a download of this export"""
        self.download_count += 1
        self.last_downloaded = datetime.utcnow()
        db.session.commit()
    
    @classmethod
    def create_export(cls, user_id: str, export_type: str, export_format: str,
                     filename: str, content_id: str = None, content_title: str = None):
        """Create a new export record"""
        export = cls(
            user_id=user_id,
            export_type=export_type,
            export_format=export_format,
            filename=filename,
            content_id=content_id,
            content_title=content_title
        )
        
        db.session.add(export)
        db.session.commit()
        
        logger.info(f"Created export {export.id} for user {user_id}")
        return export
