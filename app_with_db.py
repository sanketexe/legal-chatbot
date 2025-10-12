"""
Enhanced LegalAssist Pro Application with Database and Authentication
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import os
import sys
import json
from datetime import datetime
import uuid

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import modules
from config import Config
from simple_legal_engine import LegalReasoningEngine
from models import db, init_db, User, ChatSession, Message, create_sample_data
from auth import init_auth, auth_required, optional_auth, register_user, login_user, logout_user, get_current_user

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    config = Config()
    app.secret_key = config.SECRET_KEY
    
    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 
        'sqlite:///legal_chatbot.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # JWT configuration for authentication
    app.config['JWT_SECRET_KEY'] = os.environ.get(
        'JWT_SECRET_KEY', 
        'your-jwt-secret-key-change-in-production'
    )
    
    # Enable CORS for browser extension and web access
    CORS(app, origins=['chrome-extension://*', 'moz-extension://*', '*'])
    
    # Initialize database and authentication
    init_db(app)
    init_auth(app)
    
    # Initialize legal engine
    legal_engine = LegalReasoningEngine()
    
    # Store engine in app config for access in routes
    app.legal_engine = legal_engine
    
    return app

app = create_app()

# Print startup info
config = Config()
print(f"\n⚖️ Legal Assistant Starting...")
print(f"📡 AI Provider: {config.get_active_provider().upper()}")
print(f"🌐 Server: http://{config.HOST}:{config.PORT}")
print(f"💾 Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
print("-" * 40)

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        full_name = data.get('full_name', '').strip()
        
        if not username or not email or not password:
            return jsonify({
                'success': False, 
                'error': 'Username, email, and password are required'
            }), 400
        
        result = register_user(username, email, password, full_name)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'Registration failed: {str(e)}'
        }), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({
                'success': False, 
                'error': 'Username and password are required'
            }), 400
        
        result = login_user(username, password)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 401
            
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'Login failed: {str(e)}'
        }), 500

@app.route('/api/auth/logout', methods=['POST'])
@auth_required
def logout(current_user):
    """User logout endpoint"""
    result = logout_user()
    return jsonify(result)

@app.route('/api/auth/profile', methods=['GET'])
@auth_required
def get_profile(current_user):
    """Get current user profile"""
    return jsonify({
        'success': True,
        'user': current_user.to_dict()
    })

# ============================================================================
# CHAT ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main chat interface"""
    return render_template('simple.html')

@app.route('/api/chat', methods=['POST', 'OPTIONS'])
@optional_auth
def chat(current_user):
    """Enhanced chat endpoint with database persistence"""
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id')  # Optional: continue existing session
        
        if not user_message:
            response = jsonify({'error': 'Message is required'})
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 400
        
        # Handle chat session
        chat_session = None
        
        if current_user:
            # Authenticated user - use database
            if session_id:
                # Continue existing session
                chat_session = ChatSession.query.filter_by(
                    id=session_id, 
                    user_id=current_user.id
                ).first()
            
            if not chat_session:
                # Create new session
                chat_session = ChatSession(user_id=current_user.id)
                db.session.add(chat_session)
                db.session.commit()
            
            # Get recent message history for context
            recent_messages = Message.query.filter_by(
                session_id=chat_session.id
            ).order_by(Message.timestamp.desc()).limit(10).all()
            
            message_history = [
                {'role': msg.role, 'content': msg.content} 
                for msg in reversed(recent_messages)
            ]
        else:
            # Anonymous user - use session storage
            if 'messages' not in session:
                session['messages'] = []
            message_history = session['messages']
        
        # Get legal response
        response_content = app.legal_engine.get_legal_response(
            user_message, 
            message_history,
            {}  # Empty context for simplified version
        )
        
        # Save messages
        if current_user and chat_session:
            # Save to database
            user_msg = Message(
                session_id=chat_session.id,
                role='user',
                content=user_message,
                model_used=config.get_active_provider()
            )
            
            assistant_msg = Message(
                session_id=chat_session.id,
                role='assistant',
                content=response_content,
                model_used=config.get_active_provider()
            )
            
            db.session.add(user_msg)
            db.session.add(assistant_msg)
            db.session.commit()
            
            # Generate session title if this is the first message
            if not chat_session.title:
                chat_session.generate_title()
            
            response_data = {
                'success': True,
                'response': response_content,
                'timestamp': assistant_msg.timestamp.isoformat(),
                'session_id': chat_session.id,
                'authenticated': True
            }
        else:
            # Save to session
            user_msg = {
                'role': 'user',
                'content': user_message,
                'timestamp': datetime.now().isoformat()
            }
            
            assistant_msg = {
                'role': 'assistant',
                'content': response_content,
                'timestamp': datetime.now().isoformat()
            }
            
            session['messages'].append(user_msg)
            session['messages'].append(assistant_msg)
            session.modified = True
            
            response_data = {
                'success': True,
                'response': response_content,
                'timestamp': assistant_msg['timestamp'],
                'authenticated': False
            }
        
        response = jsonify(response_data)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
        
    except Exception as e:
        response = jsonify({'error': f'An error occurred: {str(e)}'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500

@app.route('/api/chat/sessions', methods=['GET'])
@auth_required
def get_chat_sessions(current_user):
    """Get user's chat sessions"""
    try:
        sessions = ChatSession.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).order_by(ChatSession.updated_at.desc()).all()
        
        return jsonify({
            'success': True,
            'sessions': [session.to_dict() for session in sessions]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch sessions: {str(e)}'
        }), 500

@app.route('/api/chat/sessions/<session_id>', methods=['GET'])
@auth_required
def get_chat_session(current_user, session_id):
    """Get specific chat session with messages"""
    try:
        chat_session = ChatSession.query.filter_by(
            id=session_id,
            user_id=current_user.id
        ).first()
        
        if not chat_session:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404
        
        return jsonify({
            'success': True,
            'session': chat_session.to_dict(include_messages=True)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch session: {str(e)}'
        }), 500

@app.route('/api/chat/sessions/<session_id>', methods=['DELETE'])
@auth_required
def delete_chat_session(current_user, session_id):
    """Delete a chat session"""
    try:
        chat_session = ChatSession.query.filter_by(
            id=session_id,
            user_id=current_user.id
        ).first()
        
        if not chat_session:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404
        
        # Soft delete by marking inactive
        chat_session.is_active = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Session deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to delete session: {str(e)}'
        }), 500

@app.route('/api/chat/sessions/<session_id>/messages', methods=['GET'])
@auth_required
def get_session_messages(current_user, session_id):
    """Get messages for a specific chat session"""
    try:
        chat_session = ChatSession.query.filter_by(
            id=session_id,
            user_id=current_user.id
        ).first()
        
        if not chat_session:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404
        
        messages = Message.query.filter_by(
            session_id=session_id
        ).order_by(Message.timestamp.asc()).all()
        
        return jsonify({
            'success': True,
            'messages': [message.to_dict() for message in messages]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch messages: {str(e)}'
        }), 500

@app.route('/api/chat/clear', methods=['POST'])
@optional_auth
def clear_chat(current_user):
    """Clear chat history"""
    if current_user:
        # For authenticated users, we don't clear database history
        # They can manage sessions via the sessions API
        return jsonify({
            'success': True,
            'message': 'Use session management to organize your chats'
        })
    else:
        # For anonymous users, clear session
        session['messages'] = []
        session.modified = True
        return jsonify({
            'success': True,
            'message': 'Chat history cleared'
        })

# ============================================================================
# UTILITY ROUTES
# ============================================================================

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    response = jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'ai_provider': config.get_active_provider(),
        'available_providers': config.get_available_providers(),
        'database': 'connected',
        'features': {
            'authentication': True,
            'chat_persistence': True,
            'session_management': True
        }
    })
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/api/init-sample-data', methods=['POST'])
def init_sample_data():
    """Initialize sample data (development only)"""
    if os.environ.get('FLASK_ENV') == 'production':
        return jsonify({'error': 'Not available in production'}), 403
    
    try:
        create_sample_data()
        return jsonify({
            'success': True,
            'message': 'Sample data created successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to create sample data: {str(e)}'
        }), 500

if __name__ == '__main__':
    with app.app_context():
        # Create database tables
        db.create_all()
        
        # Create sample data in development
        if os.environ.get('FLASK_ENV') != 'production':
            create_sample_data()
    
    print("⚖️ Legal Assistant Starting...")
    print(f"📡 AI Provider: {config.get_active_provider().upper()}")
    print("🌐 Server: http://0.0.0.0:5000")
    print("-" * 40)
    
    # Run the Flask app
    port = int(os.environ.get('PORT', 8080))  # AWS App Runner uses port 8080
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug_mode, host='0.0.0.0', port=port, use_reloader=False)