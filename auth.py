"""
Authentication service for LegalAssist Pro
Handles user registration, login, and JWT token management
"""

from flask import request, jsonify, current_app
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from functools import wraps
import hashlib

from models import db, User, UserSession

jwt = JWTManager()

def init_auth(app):
    """Initialize authentication with Flask app"""
    
    # JWT Configuration
    app.config['JWT_SECRET_KEY'] = app.config.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['JWT_ALGORITHM'] = 'HS256'
    
    jwt.init_app(app)
    
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        """Check if JWT token is revoked"""
        jti = jwt_payload['jti']
        token_hash = hashlib.sha256(jti.encode()).hexdigest()
        
        session = UserSession.query.filter_by(token_hash=token_hash).first()
        return session is None or not session.is_valid()
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has expired', 'code': 'TOKEN_EXPIRED'}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': 'Invalid token', 'code': 'INVALID_TOKEN'}), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'error': 'Authorization token required', 'code': 'TOKEN_MISSING'}), 401

def register_user(username, email, password, full_name=None):
    """Register a new user"""
    try:
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return {'success': False, 'error': 'Username already exists'}
        
        if User.query.filter_by(email=email).first():
            return {'success': False, 'error': 'Email already registered'}
        
        # Validate password strength
        if len(password) < 6:
            return {'success': False, 'error': 'Password must be at least 6 characters long'}
        
        # Create new user
        user = User(
            username=username,
            email=email,
            full_name=full_name
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return {
            'success': True,
            'message': 'User registered successfully',
            'user': user.to_dict()
        }
        
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': f'Registration failed: {str(e)}'}

def login_user(username, password):
    """Authenticate user and create session"""
    try:
        # Find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user or not user.check_password(password):
            return {'success': False, 'error': 'Invalid credentials'}
        
        if not user.is_active:
            return {'success': False, 'error': 'Account is disabled'}
        
        # Update last login
        user.update_last_login()
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        # Create user session record
        session = create_user_session(user.id, access_token)
        
        return {
            'success': True,
            'message': 'Login successful',
            'access_token': access_token,
            'user': user.to_dict(),
            'session_id': session.id
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Login failed: {str(e)}'}

def create_user_session(user_id, access_token):
    """Create a new user session record"""
    # Hash the token for storage
    token_hash = hashlib.sha256(access_token.encode()).hexdigest()
    
    # Get client info
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    user_agent = request.headers.get('User-Agent', '')
    
    # Create session
    session = UserSession(
        user_id=user_id,
        token_hash=token_hash,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    
    db.session.add(session)
    db.session.commit()
    
    return session

def logout_user():
    """Logout current user and revoke session"""
    try:
        # Get current token
        token = get_jwt()
        jti = token['jti']
        token_hash = hashlib.sha256(jti.encode()).hexdigest()
        
        # Find and revoke session
        session = UserSession.query.filter_by(token_hash=token_hash).first()
        if session:
            session.revoke()
        
        return {'success': True, 'message': 'Logged out successfully'}
        
    except Exception as e:
        return {'success': False, 'error': f'Logout failed: {str(e)}'}

def get_current_user():
    """Get current authenticated user"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        return user
    except:
        return None

def auth_required(f):
    """Decorator for routes that require authentication"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found', 'code': 'USER_NOT_FOUND'}), 404
        
        if not current_user.is_active:
            return jsonify({'error': 'Account disabled', 'code': 'ACCOUNT_DISABLED'}), 403
        
        return f(current_user=current_user, *args, **kwargs)
    
    return decorated_function

def optional_auth(f):
    """Decorator for routes that work with or without authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user = None
        try:
            # Try to get user if token is provided
            from flask_jwt_extended import verify_jwt_in_request
            verify_jwt_in_request(optional=True)
            current_user = get_current_user()
        except:
            pass
        
        return f(current_user=current_user, *args, **kwargs)
    
    return decorated_function

def cleanup_expired_sessions():
    """Clean up expired sessions (run periodically)"""
    try:
        expired_count = UserSession.query.filter(
            UserSession.expires_at < datetime.utcnow()
        ).delete()
        
        db.session.commit()
        print(f"✅ Cleaned up {expired_count} expired sessions")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Session cleanup failed: {e}")

def get_user_sessions(user_id):
    """Get all active sessions for a user"""
    return UserSession.query.filter_by(
        user_id=user_id,
        is_revoked=False
    ).filter(
        UserSession.expires_at > datetime.utcnow()
    ).all()

def revoke_all_user_sessions(user_id):
    """Revoke all sessions for a user (useful for password changes)"""
    sessions = UserSession.query.filter_by(user_id=user_id).all()
    for session in sessions:
        session.revoke()
    
    db.session.commit()
    return len(sessions)