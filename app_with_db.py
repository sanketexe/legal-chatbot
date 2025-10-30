"""
Enhanced LegalAssist Pro Application with Database and Authentication
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    LIMITER_AVAILABLE = True
except ImportError:
    LIMITER_AVAILABLE = False
    print("⚠️  flask-limiter not available, rate limiting disabled")
from functools import wraps
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

# Import ML-powered legal engine
from legal_engine_ml import get_legal_engine

# Import document analyzer (for in-memory document analysis)
from document_analyzer import get_document_analyzer

def get_basic_fallback_response(query: str) -> str:
    """
    Provide a basic fallback response when ML system is unavailable
    """
    query_lower = query.lower()
    
    if any(word in query_lower for word in ['contract', 'agreement', 'breach']):
        return """**Contract Law Information:**

I can provide general information about contract law in India. However, our advanced AI system is temporarily unavailable.

**Basic Contract Principles:**
- Valid contracts require offer, acceptance, and consideration
- Breach of contract can lead to legal remedies
- The Indian Contract Act, 1872 governs most contracts

**For specific advice:** Please consult a qualified lawyer or try again in a few moments when our full system is back online.

*This is general information only, not legal advice.*"""
    
    elif any(word in query_lower for word in ['divorce', 'marriage', 'custody']):
        return """**Family Law Information:**

Our advanced AI system is temporarily unavailable, but I can provide basic information.

**Family Law in India:**
- Divorce laws vary by religion (Hindu, Muslim, Christian, Parsi, Special Marriage Act)
- Child custody decisions prioritize the child's best interests
- Consult a family law specialist for your specific situation

**Important:** Family law matters are complex and personal. Please consult a qualified family lawyer for proper guidance.

*This is general information only, not legal advice.*"""
    
    else:
        return """**Legal Information Service:**

Thank you for your question. Our advanced AI system with case citations is temporarily unavailable, but we're here to help.

**What You Can Do:**
1. **Try again shortly:** Our system should be back online soon
2. **Consult a lawyer:** For urgent matters, please contact a qualified attorney
3. **Reformulate your question:** Try asking in simpler terms

**Practice Areas We Cover:**
- Contract Law
- Property Law
- Family Law
- Criminal Law
- Consumer Rights
- Employment Law

**Disclaimer:** This chatbot provides general legal information, not legal advice. For specific legal matters, always consult with a qualified attorney.

*We apologize for the inconvenience and appreciate your patience.*"""

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    config = Config()
    app.secret_key = config.SECRET_KEY
    
    # Database configuration
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///legal_chatbot.db')
    
    # Fix for Heroku/Vercel DATABASE_URL (they use 'postgres://' but SQLAlchemy needs 'postgresql://')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    
    # PostgreSQL Connection Pool Settings (optional but recommended)
    app.config['SQLALCHEMY_POOL_SIZE'] = 10
    app.config['SQLALCHEMY_MAX_OVERFLOW'] = 20
    app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30
    app.config['SQLALCHEMY_POOL_RECYCLE'] = 1800  # Recycle connections after 30 minutes
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,  # Verify connections before using
    }
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # JWT configuration for authentication
    app.config['JWT_SECRET_KEY'] = os.environ.get(
        'JWT_SECRET_KEY', 
        'your-jwt-secret-key-change-in-production'
    )
    
    # Enable CORS for browser extension and web access
    CORS(app, origins=['chrome-extension://*', 'moz-extension://*', '*'])
    
    # Initialize rate limiter
    if LIMITER_AVAILABLE:
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=["200 per day", "50 per hour"],
            storage_uri="memory://"
        )
        print("✅ Rate limiting enabled")
    else:
        # Create a dummy decorator that does nothing
        class DummyLimiter:
            def limit(self, *args, **kwargs):
                def decorator(f):
                    return f
                return decorator
        limiter = DummyLimiter()
        print("⚠️  Rate limiting disabled (flask-limiter not installed)")
    
    # API Key Authentication Middleware
    def require_api_key(f):
        """Decorator to require API key for protected endpoints"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            api_key = request.headers.get('X-API-Key')
            expected_key = os.getenv('API_SECRET_KEY')
            
            # Skip API key check in development mode if not set
            if not expected_key:
                return f(*args, **kwargs)
            
            if not api_key:
                return jsonify({
                    'error': 'API key required',
                    'message': 'Include X-API-Key header in your request'
                }), 401
            
            if api_key != expected_key:
                return jsonify({
                    'error': 'Invalid API key',
                    'message': 'The provided API key is not valid'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    
    # Store limiter and auth decorator in app for access in routes
    app.limiter = limiter
    app.require_api_key = require_api_key
    
    # Function to apply rate limits to routes after they're defined
    def apply_rate_limits():
        """Apply rate limiting decorators to existing routes"""
        if LIMITER_AVAILABLE:
            # Register endpoint - 3 per hour
            app.view_functions['register'] = limiter.limit("3 per hour")(app.view_functions['register'])
            # Login endpoint - 10 per hour
            app.view_functions['login'] = limiter.limit("10 per hour")(app.view_functions['login'])
            # Chat endpoint - 10 per minute + API key
            app.view_functions['chat'] = require_api_key(limiter.limit("10 per minute")(app.view_functions['chat']))
            # Document analysis endpoint - 5 per minute + API key
            app.view_functions['analyze_document'] = require_api_key(limiter.limit("5 per minute")(app.view_functions['analyze_document']))
            print("✅ Rate limits applied to endpoints")
    
    # Store the function for later use
    app.apply_rate_limits = apply_rate_limits
    
    # Initialize database and authentication
    init_db(app)
    init_auth(app)
    
    # Initialize ML-powered legal engine (with fallback to basic)
    try:
        legal_engine = get_legal_engine()
        print("✅ Legal engine initialized successfully")
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize ML engine: {e}")
        print("📝 System will use basic responses as fallback")
        legal_engine = None
    
    # Store engine in app config for access in routes
    app.legal_engine = legal_engine
    
    # Initialize document analyzer
    try:
        app.document_analyzer = get_document_analyzer()
        print("✅ Document analyzer initialized")
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize document analyzer: {e}")
        app.document_analyzer = None
    
    # Global error handler
    @app.errorhandler(Exception)
    def handle_error(error):
        """Global error handler with graceful degradation"""
        error_message = str(error)
        error_type = type(error).__name__
        
        # Log the error (in production, use proper logging)
        print(f"❌ Error [{error_type}]: {error_message}")
        
        # Provide user-friendly error messages
        if isinstance(error, Exception):
            if "database" in error_message.lower():
                user_message = "We're experiencing database issues. Please try again shortly."
            elif "gemini" in error_message.lower() or "api" in error_message.lower():
                user_message = "AI service temporarily unavailable. Using backup system."
            elif "timeout" in error_message.lower():
                user_message = "Request timed out. Please try a simpler question."
            else:
                user_message = "An unexpected error occurred. Our team has been notified."
        else:
            user_message = "Something went wrong. Please refresh and try again."
        
        response = jsonify({
            'success': False,
            'error': user_message,
            'error_type': error_type if app.debug else None
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        
        return response, 500
    
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
        
        # Get ML-powered legal response with citations (with retry logic)
        max_retries = 3
        retry_count = 0
        result = None
        last_error = None
        
        while retry_count < max_retries and result is None:
            try:
                if app.legal_engine is None:
                    # Fallback to basic response if engine not available
                    result = {
                        'response': get_basic_fallback_response(user_message),
                        'sources': [],
                        'type': 'fallback'
                    }
                else:
                    result = app.legal_engine.get_legal_response(
                        user_message,
                        {'history': message_history}
                    )
                break  # Success, exit retry loop
                
            except Exception as e:
                last_error = e
                retry_count += 1
                print(f"⚠️  Attempt {retry_count}/{max_retries} failed: {e}")
                
                if retry_count >= max_retries:
                    # All retries exhausted, use fallback
                    print("❌ All retries exhausted, using fallback response")
                    result = {
                        'response': get_basic_fallback_response(user_message),
                        'sources': [],
                        'type': 'fallback'
                    }
        
        response_content = result['response']
        sources = result.get('sources', [])
        
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
                'sources': sources,  # Add case citations
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
                'sources': sources,  # Add case citations for anonymous users too
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
    ml_status = app.legal_engine.get_system_status()
    
    response = jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'ai_provider': config.get_active_provider(),
        'available_providers': config.get_available_providers(),
        'database': 'connected',
        'ml_system': ml_status,
        'document_analyzer': app.document_analyzer is not None,
        'features': {
            'authentication': True,
            'chat_persistence': True,
            'session_management': True,
            'case_search': ml_status['ml_available'],
            'rag_responses': ml_status['rag_initialized'],
            'citations': ml_status['ml_available'],
            'document_analysis': app.document_analyzer is not None
        }
    })
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/api/search-cases', methods=['POST'])
@optional_auth
def search_cases(current_user):
    """Search legal cases in vector database"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Search cases
        results = app.legal_engine.search_cases(query)
        
        response = jsonify({
            'success': True,
            'query': query,
            'results': results,
            'count': len(results)
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        response = jsonify({
            'error': f'Search failed: {str(e)}'
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500

@app.route('/api/analyze-document', methods=['POST', 'OPTIONS'])
@optional_auth
def analyze_document(current_user):
    """
    Analyze uploaded legal document in-memory (NO STORAGE)
    Supports: PDF, DOCX, TXT
    Max size: 10 MB
    """
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded. Please select a document.'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Get optional specific questions
        questions = request.form.get('questions', '')
        question_list = []
        if questions:
            import json
            try:
                question_list = json.loads(questions)
            except:
                # If not JSON, treat as single question
                question_list = [questions] if questions.strip() else []
        
        # Read file content (IN MEMORY ONLY - NOT STORED)
        file_content = file.read()
        
        if not app.document_analyzer:
            return jsonify({
                'success': False,
                'error': 'Document analyzer not available'
            }), 503
        
        # Analyze document (in-memory only, no database storage)
        result = app.document_analyzer.analyze_document(
            file.filename,
            file_content,
            question_list
        )
        
        # Clear file content from memory immediately after analysis
        file_content = None
        
        response = jsonify(result)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        response = jsonify({
            'success': False,
            'error': f'Document analysis failed: {str(e)}'
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500

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
    # Apply rate limiting to routes
    app.apply_rate_limits()
    
    print("⚖️ Legal Assistant Starting...")
    print(f"📡 AI Provider: {config.get_active_provider().upper()}")
    print("🌐 Server: http://0.0.0.0:5000")
    print("-" * 40)
    
    # Run the Flask app
    port = int(os.environ.get('PORT', 8080))  # AWS App Runner uses port 8080
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug_mode, host='0.0.0.0', port=port, use_reloader=False)