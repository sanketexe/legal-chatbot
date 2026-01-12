"""
Enhanced LegalAssist Pro Application with Database and Authentication
"""

from flask import Flask, render_template, request, jsonify, session, Response
from flask_cors import CORS
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    LIMITER_AVAILABLE = True
except ImportError:
    LIMITER_AVAILABLE = False
    print("WARN: flask-limiter not available, rate limiting disabled")
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
try:
    from src.simple_legal_engine import LegalReasoningEngine
    LEGAL_ENGINE_AVAILABLE = True
except ImportError:
    print("WARN: LegalReasoningEngine not available, using fallback")
    LEGAL_ENGINE_AVAILABLE = False
    LegalReasoningEngine = None
from models import db, init_db, User, ChatSession, Message, create_sample_data
try:
    from auth import init_auth, auth_required, optional_auth, register_user, login_user, logout_user, get_current_user
    AUTH_AVAILABLE = True
except ImportError:
    print("WARN: Auth module not fully available")
    AUTH_AVAILABLE = False

# Import ML-powered legal engine
try:
    from legal_engine_ml import get_legal_engine
    ML_ENGINE_AVAILABLE = True
except ImportError:
    print("WARN: ML legal engine not available")
    ML_ENGINE_AVAILABLE = False

# Import document analyzer (for in-memory document analysis)
try:
    from document_analyzer import get_document_analyzer
    DOCUMENT_ANALYZER_AVAILABLE = True
except ImportError:
    print("WARN: Document analyzer not available")
    DOCUMENT_ANALYZER_AVAILABLE = False

# Import document generator
try:
    from document_generator import LegalDocumentGenerator, get_document_fields
    DOCUMENT_GENERATOR_AVAILABLE = True
except ImportError:
    print("WARN: Document generator not available")
    DOCUMENT_GENERATOR_AVAILABLE = False

# Import translation service for Hindi support
try:
    from ml_legal_system.translators import get_translation_service, create_bilingual_response
    TRANSLATION_AVAILABLE = True
except ImportError:
    print("WARN: Translation service not available")
    TRANSLATION_AVAILABLE = False
from logging_config import get_logger

logger = get_logger(__name__)

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
        logger.info("Rate limiting enabled")
    else:
        # Create a dummy decorator that does nothing
        class DummyLimiter:
            def limit(self, *args, **kwargs):
                def decorator(f):
                    return f
                return decorator
        limiter = DummyLimiter()
    logger.warning("Rate limiting disabled (flask-limiter not installed)")
    
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
            # Chat endpoint - 10 per minute (NO API key required for better UX)
            app.view_functions['chat'] = limiter.limit("10 per minute")(app.view_functions['chat'])
            # Document analysis endpoint - 5 per minute (NO API key required for better UX)
            app.view_functions['analyze_document'] = limiter.limit("5 per minute")(app.view_functions['analyze_document'])
            logger.info("Rate limits applied to endpoints")
    
    # Store the function for later use
    app.apply_rate_limits = apply_rate_limits
    
    # Initialize database and authentication
    init_db(app)
    init_auth(app)
    
    # Initialize ML-powered legal engine (with fallback to basic)
    try:
        legal_engine = get_legal_engine()
        logger.info("Legal engine initialized successfully")
    except Exception as e:
        logger.warning(f"Could not initialize ML engine: {e}")
        logger.info("System will use basic responses as fallback")
        legal_engine = None
    
    # Store engine in app config for access in routes
    app.legal_engine = legal_engine
    
    # Initialize document analyzer
    try:
        app.document_analyzer = get_document_analyzer()
        logger.info("Document analyzer initialized")
    except Exception as e:
        logger.warning(f"Could not initialize document analyzer: {e}")
        app.document_analyzer = None
    
    # Global error handler
    @app.errorhandler(Exception)
    def handle_error(error):
        """Global error handler with graceful degradation"""
        error_message = str(error)
        error_type = type(error).__name__
        # Log the error (in production, use proper logging)
        logger.error(f"{error_type}: {error_message}")

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

# Startup info
config = Config()
logger.info("Legal Assistant Starting...")
logger.info(f"AI Provider: {config.get_active_provider().upper()}")
logger.info(f"Server: http://{config.HOST}:{config.PORT}")
logger.info(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
logger.info("-" * 40)

# ============================================================================
# ADMIN DASHBOARD
# ============================================================================

# Register admin blueprint
from admin_blueprint import admin_bp
app.register_blueprint(admin_bp)
logger.info("Admin dashboard registered at /admin")

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Safely extract and clean input data
        username = (data.get('username') or '').strip()
        email = (data.get('email') or '').strip()
        password = data.get('password') or ''
        full_name = (data.get('full_name') or '').strip()
        
        # Convert empty string to None for optional full_name
        if not full_name:
            full_name = None
        
        # Validate required fields
        if not username or not email or not password:
            return jsonify({
                'success': False, 
                'error': 'Username, email, and password are required'
            }), 400
        
        # Log for debugging
        logger.info(f"Registration attempt - username: {username}, email: {email}")
        
        result = register_user(username, email, password, full_name)
        
        if result['success']:
            logger.info(f"User registered successfully: {username}")
            return jsonify(result), 201
        else:
            logger.warning(f"Registration failed: {result.get('error')}")
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False, 
            'error': f'Registration failed: {str(e)}'
        }), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        username = (data.get('username') or '').strip()
        password = data.get('password') or ''
        
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
# USER PREFERENCES ROUTES
# ============================================================================

@app.route('/api/user/preferences', methods=['GET', 'POST', 'PUT'])
@auth_required
def user_preferences(current_user):
    """Get or update user preferences"""
    from models import UserPreference
    
    if request.method == 'GET':
        # Get preferences
        pref = UserPreference.query.filter_by(user_id=current_user.id).first()
        if not pref:
            # Create default preferences if not exist
            pref = UserPreference(user_id=current_user.id)
            db.session.add(pref)
            db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': pref.to_dict()
        }), 200
    
    elif request.method in ['POST', 'PUT']:
        # Update preferences
        data = request.json or {}
        pref = UserPreference.query.filter_by(user_id=current_user.id).first()
        
        if not pref:
            pref = UserPreference(user_id=current_user.id)
            db.session.add(pref)
        
        # Update only provided fields
        if 'preferred_language' in data:
            pref.preferred_language = data['preferred_language']
            print(f"OK: Updated language to {data['preferred_language']}")
        
        if 'response_detail_level' in data:
            pref.response_detail_level = int(data['response_detail_level'])
            print(f"OK: Updated detail level to {data['response_detail_level']}")
        
        if 'jurisdiction_preference' in data:
            pref.jurisdiction_preference = data['jurisdiction_preference']
        
        if 'legal_domains' in data:
            pref.legal_domains = data['legal_domains']
        
        if 'include_case_summaries' in data:
            pref.include_case_summaries = bool(data['include_case_summaries'])
        
        if 'include_act_references' in data:
            pref.include_act_references = bool(data['include_act_references'])
        
        if 'notification_enabled' in data:
            pref.notification_enabled = bool(data['notification_enabled'])
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Preferences updated',
            'data': pref.to_dict()
        }), 200

@app.route('/api/user/preferences/<field>', methods=['GET'])
@auth_required
def get_preference_field(current_user, field):
    """Get specific preference field"""
    from models import UserPreference
    
    pref = UserPreference.query.filter_by(user_id=current_user.id).first()
    
    if not pref:
        return jsonify({'status': 'error', 'message': 'Preferences not found'}), 404
    
    pref_dict = pref.to_dict()
    if field not in pref_dict:
        return jsonify({'status': 'error', 'message': f'Unknown field: {field}'}), 400
    
    value = getattr(pref, field)
    return jsonify({
        'status': 'success',
        'field': field,
        'value': value
    }), 200


# ============================================================================
# RATING ROUTES
# ============================================================================

@app.route('/api/rate', methods=['POST'])
@optional_auth
def rate_response(current_user):
    """Rate a chat response with 1-5 stars"""
    try:
        # Check if user is authenticated
        if not current_user:
            return jsonify({
                'status': 'info',
                'message': 'Please sign up to rate responses and help us improve!',
                'authenticated': False,
                'feature': 'rating'
            }), 200
        
        data = request.get_json()
        message_id = data.get('message_id')
        rating = data.get('rating')
        feedback = data.get('feedback', '')
        
        # Validate rating
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return jsonify({
                'status': 'error',
                'message': 'Rating must be an integer between 1 and 5'
            }), 400
        
        if not message_id:
            return jsonify({
                'status': 'error',
                'message': 'message_id is required'
            }), 400
        
        # Verify message exists
        from models import Message, ResponseRating
        message = Message.query.filter_by(id=message_id).first()
        if not message:
            return jsonify({
                'status': 'error',
                'message': 'Message not found'
            }), 404
        
        # Check if user already rated this message
        existing_rating = ResponseRating.query.filter_by(
            user_id=current_user.id,
            message_id=message_id
        ).first()
        
        if existing_rating:
            # Update existing rating
            existing_rating.rating = rating
            existing_rating.feedback = feedback[:500] if feedback else None
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Rating updated successfully',
                'rating': existing_rating.to_dict()
            }), 200
        else:
            # Create new rating
            rating_obj = ResponseRating(
                user_id=current_user.id,
                message_id=message_id,
                rating=rating,
                feedback=feedback[:500] if feedback else None
            )
            
            db.session.add(rating_obj)
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Rating submitted successfully',
                'rating': rating_obj.to_dict()
            }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }), 500


@app.route('/api/ratings/stats', methods=['GET'])
@auth_required
def get_rating_stats(current_user):
    """Get user's rating statistics"""
    try:
        from models import ResponseRating
        ratings = ResponseRating.query.filter_by(user_id=current_user.id).all()
        
        if not ratings:
            return jsonify({
                'status': 'success',
                'total_ratings': 0,
                'average_rating': 0,
                'distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            }), 200
        
        # Calculate statistics
        total = len(ratings)
        total_score = sum(r.rating for r in ratings)
        average = total_score / total
        
        # Distribution by star rating (return as list so JSON preserves numeric indices)
        dist_list = [0] * 6  # index 0 unused; indices 1-5 correspond to star ratings
        for r in ratings:
            if 1 <= r.rating <= 5:
                dist_list[r.rating] += 1
        
        return jsonify({
            'status': 'success',
            'total_ratings': total,
            'average_rating': round(average, 2),
            'distribution': dist_list,
            'user_id': current_user.id
        }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }), 500


@app.route('/api/ratings', methods=['GET'])
@auth_required
def get_user_ratings(current_user):
    """Get all ratings by the current user"""
    try:
        from models import ResponseRating
        ratings = ResponseRating.query.filter_by(
            user_id=current_user.id
        ).order_by(ResponseRating.created_at.desc()).all()
        
        return jsonify({
            'status': 'success',
            'count': len(ratings),
            'ratings': [r.to_dict() for r in ratings]
        }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }), 500


# ============================================================================
# CHAT ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main chat interface"""
    return render_template('simple.html')

@app.route('/dashboard')
@auth_required
def dashboard():
    """User dashboard with analytics"""
    return render_template('dashboard.html')

@app.route('/search')
def search_chats():
    """Search chats interface - find past conversations"""
    return render_template('search.html')

@app.route('/conversation')
def conversation_interface():
    """Conversation interface with context preservation"""
    return render_template('conversation_chat.html')

@app.route('/advanced-search')
def advanced_search():
    """Advanced case search interface with filters"""
    return render_template('advanced_search.html')

@app.route('/multilingual')
def multilingual_chat():
    """Multilingual chat interface with voice support"""
    return render_template('multilingual_chat.html')

@app.route('/citations')
def citation_network_ui():
    """Citation network visualization interface"""
    return render_template('citation_network.html')

@app.route('/case-summarization')
def case_summarization_ui():
    """Case summarization interface"""
    return render_template('case_summarization.html')

@app.route('/case-predictor')
def case_predictor_ui():
    """Case outcome predictor interface"""
    return render_template('case_predictor.html')

@app.route('/api/upload-document', methods=['POST'])
def upload_document():
    """
    Upload and analyze legal documents (PDF, DOCX, TXT)
    Returns AI-powered analysis with key points and recommendations
    """
    try:
        # Check if file is present in request
        if 'document' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No file uploaded'
            }), 400
        
        file = request.files['document']
        
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No file selected'
            }), 400
        
        # Read file content into memory
        file_content = file.read()
        file_size = len(file_content)
        filename = file.filename
        
        # Import and use document analyzer
        from document_analyzer import DocumentAnalyzer
        analyzer = DocumentAnalyzer()
        
        # Validate file
        validation = analyzer.validate_file(filename, file_size)
        if not validation['valid']:
            return jsonify({
                'status': 'error',
                'message': validation['error']
            }), 400
        
        # Analyze document with AI
        logger.info(f"Analyzing document: {filename} ({file_size} bytes)")
        
        result = analyzer.analyze_document_smart(
            file_content,
            filename,
            analyze_with_ai=True
        )
        
        # Format response
        response_data = {
            'status': 'success',
            'analysis': {
                'document_type': result.get('document_type', 'Unknown'),
                'summary': result.get('summary', 'Analysis complete'),
                'key_points': result.get('key_points', []),
                'recommendations': result.get('recommendations', []),
                'legal_issues': result.get('legal_issues', []),
                'risk_level': result.get('risk_level', 'Unknown')
            }
        }
        
        logger.info(f"Document analysis successful for {filename}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Document upload error: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Analysis failed: {str(e)}'
        }), 500

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
        
        # Smart case name detection - searches existing ChromaDB database
        from smart_case_handler import get_case_query_handler
        
        case_handler = get_case_query_handler()
        
        if case_handler.is_case_query(user_message):
            # Extract case names from query
            case_names = case_handler.extract_case_names(user_message)
            
            if case_names:
                try:
                    # Search existing database with extracted names (no need for db parameter)
                    results, is_high_confidence = case_handler.search_database(
                        user_message, case_names, None
                    )
                    
                    if results and len(results) > 0:
                        # Check if we have any decent matches (relevance must be > 0.15 to be considered relevant)
                        top_case = results[0]
                        top_relevance = 1 - top_case.get('distance', 1)
                        
                        # Only return database result if we have a decent match OR it's explicitly high confidence
                        # Otherwise, let it fall through to Gemini API for better general knowledge
                        if top_relevance > 0.15 or is_high_confidence:
                            # Found a match - return immediately
                            response_text = case_handler.format_case_response(top_case, is_direct_match=is_high_confidence)
                            
                            # Format sources for analysis panel
                            sources = []
                            for case in results[:5]:  # Top 5 results
                                metadata = case.get('metadata', {})
                                doc = case.get('document', '')
                                
                                # Extract case title from document
                                title = doc.split('\n')[0] if doc else metadata.get('case_id', 'Unknown')
                                
                                sources.append({
                                    'case_name': metadata.get('case_id', 'Unknown'),
                                    'title': title[:150],
                                    'court': metadata.get('court', 'Unknown Court'),
                                    'date': metadata.get('date', 'Unknown'),
                                    'judges': [metadata.get('judge', '')] if metadata.get('judge') else [],
                                    'petitioner': 'See case details',
                                    'respondent': 'See case details',
                                    'judgment': doc[:500] if doc else '',
                                    'citations': [],
                                    'excerpt': doc[:300] if doc else '',
                                    'relevance': 1 - case.get('distance', 1),
                                    'outcome': metadata.get('outcome', 'Unknown'),
                                    'legal_domain': metadata.get('legal_domain', ''),
                                    'url': metadata.get('original_url', '')
                                })
                            
                            response_data = {
                                'response': response_text,
                                'sources': sources,
                                'is_direct_case_match': is_high_confidence,
                                'response_time': 0.2
                            }
                            response = jsonify(response_data)
                            response.headers['Access-Control-Allow-Origin'] = '*'
                            return response
                except Exception as e:
                    logger.warning(f"Smart case search failed: {e}")
                    # Continue to regular flow
        
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
                print(f"WARN: Attempt {retry_count}/{max_retries} failed: {e}")
                
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
        
        # Generate ML prediction if query seems to be about a legal case
        prediction_insight = None
        try:
            from prediction_service import get_prediction_service
            
            # Detect if user is asking about a case outcome (keywords: "what will happen", "outcome", "chances", "likely")
            outcome_keywords = ['what will happen', 'outcome', 'chances', 'likely', 'expect', 'result', 
                              'win', 'lose', 'succeed', 'dismissed', 'allowed', 'conviction', 'acquittal']
            
            query_lower = user_message.lower()
            is_outcome_query = any(keyword in query_lower for keyword in outcome_keywords)
            
            if is_outcome_query or len(sources) > 0:
                # Extract case facts from user message and sources
                facts_text = user_message
                if len(sources) > 0:
                    # Include context from similar cases
                    facts_text += " " + " ".join([s.get('snippet', '')[:100] for s in sources[:3]])
                
                # Create prediction input
                case_input = {
                    'facts': facts_text[:1000],  # Limit to 1000 chars
                    'issues': user_message[:500],
                    'charges': '',  # Extract if mentioned
                    'court': 'other',
                    'case_type': 'other'
                }
                
                # Try to detect court and case type from sources
                if len(sources) > 0:
                    first_source = sources[0]
                    court_str = first_source.get('court', '').lower()
                    if 'supreme' in court_str:
                        case_input['court'] = 'supreme'
                    elif 'high' in court_str:
                        case_input['court'] = 'high'
                    elif 'district' in court_str:
                        case_input['court'] = 'district'
                    
                    # Detect case type from legal domain or query
                    if 'criminal' in query_lower or 'theft' in query_lower or 'murder' in query_lower:
                        case_input['case_type'] = 'criminal'
                    elif 'civil' in query_lower or 'property' in query_lower or 'contract' in query_lower:
                        case_input['case_type'] = 'civil'
                
                # Get prediction
                predictor = get_prediction_service()
                prediction_result = predictor.predict_outcome(case_input)
                
                if 'error' not in prediction_result:
                    # Format prediction as natural language insight
                    outcome_label = prediction_result.get('outcome_label', 'Unknown')
                    confidence = prediction_result.get('confidence', 0)
                    
                    # Add prediction insight to response
                    prediction_text = f"\n\n🔮 **AI Prediction**: Based on {len(sources)} similar cases, "
                    prediction_text += f"the outcome is likely to be **{outcome_label}** "
                    prediction_text += f"(Confidence: {confidence}%). "
                    
                    if prediction_result.get('reasoning'):
                        top_factor = prediction_result['reasoning'][0]
                        prediction_text += f"Key factor: {top_factor.get('description', 'N/A')}"
                    
                    # Append to response
                    response_content += prediction_text
                    
                    # Store structured prediction for frontend
                    prediction_insight = {
                        'outcome': prediction_result.get('outcome'),
                        'outcome_label': outcome_label,
                        'confidence': confidence,
                        'confidence_level': prediction_result.get('confidence_level'),
                        'description': prediction_result.get('description', ''),
                        'top_factors': prediction_result.get('reasoning', [])[:2],
                        'similar_cases_count': len(prediction_result.get('similar_cases', []))
                    }
                    
        except Exception as e:
            logger.warning(f"Chat prediction generation failed: {e}")
        
        # Check user language preference for translation
        user_language = 'en'  # Default to English
        translations = {}
        
        if current_user and chat_session:
            user_prefs = current_user.preferences if hasattr(current_user, 'preferences') else None
            if user_prefs:
                user_language = user_prefs.preferred_language or 'en'
        
        # Apply translation if needed
        if user_language == 'hi':
            try:
                translation_service = get_translation_service()
                response_content = translation_service.translate_response(response_content)
                translations = {'from': 'en', 'to': 'hi'}
            except Exception as e:
                print(f"WARN: Translation to Hindi failed: {e}")
                # Fallback to English if translation fails
                translations = {'from': 'en', 'to': 'en', 'error': str(e)}
        elif user_language != 'en':
            print(f"WARN: Language '{user_language}' not yet supported, using English")
        
        # Save messages
        if current_user and chat_session:
            # Save original English response to database for audit trail
            user_msg = Message(
                session_id=chat_session.id,
                role='user',
                content=user_message,
                model_used=config.get_active_provider()
            )
            
            # Store the translated response if translation was applied
            db_response_content = response_content
            if user_language == 'hi':
                # For database, store both English and Hindi versions in metadata
                db_response_content = response_content
            
            assistant_msg = Message(
                session_id=chat_session.id,
                role='assistant',
                content=db_response_content,
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
                'prediction': prediction_insight,  # ML prediction insight
                'timestamp': assistant_msg.timestamp.isoformat(),
                'session_id': chat_session.id,
                'authenticated': True,
                'language': user_language,
                'translations': translations
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
                'prediction': prediction_insight,  # ML prediction insight
                'timestamp': assistant_msg['timestamp'],
                'authenticated': False,
                'language': 'en',
                'translations': {}
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

# ============================================================================
# DASHBOARD API ROUTES
# ============================================================================

@app.route('/api/dashboard/stats', methods=['GET'])
@auth_required
def get_dashboard_stats(current_user):
    """Get dashboard statistics for current user"""
    try:
        from datetime import timedelta
        from sqlalchemy import func
        
        # Get total sessions
        total_sessions = ChatSession.query.filter_by(user_id=current_user.id).count()
        
        # Get active sessions
        active_sessions = ChatSession.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).count()
        
        # Get total messages
        total_messages = db.session.query(func.count(Message.id)).join(
            ChatSession
        ).filter(ChatSession.user_id == current_user.id).scalar() or 0
        
        # Get average rating
        try:
            from models import ResponseRating
            avg_rating_result = db.session.query(func.avg(ResponseRating.rating)).join(
                Message
            ).join(ChatSession).filter(
                ChatSession.user_id == current_user.id
            ).scalar()
            avg_rating = float(avg_rating_result) if avg_rating_result else 0.0
        except:
            avg_rating = 0.0
        
        # Calculate change from last week
        last_week = datetime.utcnow() - timedelta(days=7)
        
        sessions_last_week = ChatSession.query.filter(
            ChatSession.user_id == current_user.id,
            ChatSession.created_at < last_week
        ).count()
        
        messages_last_week = db.session.query(func.count(Message.id)).join(
            ChatSession
        ).filter(
            ChatSession.user_id == current_user.id,
            Message.timestamp < last_week
        ).scalar() or 0
        
        # Calculate percentage changes
        chats_change = 0
        if sessions_last_week > 0:
            chats_change = round(((total_sessions - sessions_last_week) / sessions_last_week) * 100, 1)
        
        messages_change = 0
        if messages_last_week > 0:
            messages_change = round(((total_messages - messages_last_week) / messages_last_week) * 100, 1)
        
        return jsonify({
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'total_messages': total_messages,
            'avg_rating': round(avg_rating, 1),
            'chats_change': chats_change,
            'messages_change': messages_change
        })
        
    except Exception as e:
        logger.error(f"Dashboard stats error: {str(e)}")
        return jsonify({
            'total_sessions': 0,
            'active_sessions': 0,
            'total_messages': 0,
            'avg_rating': 0.0,
            'chats_change': 0,
            'messages_change': 0
        })

@app.route('/api/dashboard/charts', methods=['GET'])
@auth_required
def get_dashboard_charts(current_user):
    """Get chart data for dashboard"""
    try:
        from datetime import timedelta
        from sqlalchemy import func
        from collections import defaultdict
        
        # Activity data for last 7 days
        activity_data = []
        activity_labels = []
        
        for i in range(6, -1, -1):
            day = datetime.utcnow() - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            count = db.session.query(func.count(Message.id)).join(
                ChatSession
            ).filter(
                ChatSession.user_id == current_user.id,
                Message.timestamp >= day_start,
                Message.timestamp < day_end
            ).scalar() or 0
            
            activity_data.append(count)
            activity_labels.append(day.strftime('%a'))
        
        # Topics distribution (analyze message content for keywords)
        topics_labels = ['Family Law', 'Property', 'Criminal', 'Civil', 'Constitutional']
        topics_data = [0, 0, 0, 0, 0]
        
        # Get recent messages for topic analysis
        recent_messages = db.session.query(Message.content).join(
            ChatSession
        ).filter(
            ChatSession.user_id == current_user.id,
            Message.role == 'user'
        ).limit(100).all()
        
        # Simple keyword matching
        keywords = {
            0: ['family', 'marriage', 'divorce', 'custody', 'adoption', 'maintenance'],
            1: ['property', 'land', 'ownership', 'lease', 'rent', 'estate'],
            2: ['criminal', 'theft', 'assault', 'murder', 'ipc', 'police'],
            3: ['civil', 'contract', 'tort', 'negligence', 'damages', 'suit'],
            4: ['constitution', 'fundamental', 'rights', 'article', 'supreme court']
        }
        
        for msg in recent_messages:
            content = msg[0].lower()
            for topic_idx, words in keywords.items():
                if any(word in content for word in words):
                    topics_data[topic_idx] += 1
                    break
        
        # If no topics detected, use sample data
        if sum(topics_data) == 0:
            topics_data = [25, 20, 15, 25, 15]
        
        return jsonify({
            'activity_labels': activity_labels,
            'activity_data': activity_data,
            'topics_labels': topics_labels,
            'topics_data': topics_data
        })
        
    except Exception as e:
        logger.error(f"Dashboard charts error: {str(e)}")
        return jsonify({
            'activity_labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'activity_data': [0, 0, 0, 0, 0, 0, 0],
            'topics_labels': ['Family Law', 'Property', 'Criminal', 'Civil', 'Constitutional'],
            'topics_data': [25, 20, 15, 25, 15]
        })

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
# CONVERSATION MEMORY ROUTES (Multi-turn Conversations)
# ============================================================================

@app.route('/api/conversation/query', methods=['POST', 'OPTIONS'])
@optional_auth
def conversation_query(current_user):
    """
    Enhanced query endpoint with conversation memory support
    Enables multi-turn conversations with context preservation
    """
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        conv_session_id = data.get('session_id')  # Conversation session ID (different from chat session)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Build user context
        user_context = {}
        if current_user:
            user_context['user_id'] = current_user.id
        if conv_session_id:
            user_context['session_id'] = conv_session_id
        
        # Get response with conversation context
        if app.legal_engine is None:
            return jsonify({
                'error': 'Legal engine not available',
                'response': get_basic_fallback_response(query),
                'sources': [],
                'type': 'fallback'
            }), 503
        
        result = app.legal_engine.get_legal_response(query, user_context=user_context)
        
        response_data = {
            'success': True,
            'response': result['response'],
            'sources': result.get('sources', []),
            'session_id': result.get('session_id'),
            'conversation_context': result.get('conversation_context'),
            'type': result.get('type', 'rag'),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Conversation query error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'response': get_basic_fallback_response(query if 'query' in locals() else '')
        }), 500

@app.route('/api/conversation/history/<session_id>', methods=['GET', 'OPTIONS'])
@optional_auth
def get_conversation_history(current_user, session_id):
    """
    Get conversation history for a specific session
    """
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    try:
        format_type = request.args.get('format', 'dict')  # dict, formatted, or raw
        
        if app.legal_engine is None:
            return jsonify({'error': 'Legal engine not available'}), 503
        
        history = app.legal_engine.get_conversation_history(session_id, format_type=format_type)
        
        if history is None:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        logger.error(f"Get conversation history error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/conversation/context/<session_id>', methods=['GET', 'OPTIONS'])
@optional_auth
def get_conversation_context(current_user, session_id):
    """
    Get conversation context summary (legal domain, references, etc.)
    """
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    try:
        if app.legal_engine is None:
            return jsonify({'error': 'Legal engine not available'}), 503
        
        context = app.legal_engine.get_conversation_context(session_id)
        
        if context is None:
            return jsonify({
                'success': False,
                'error': 'Session not found or no context available'
            }), 404
        
        return jsonify({
            'success': True,
            'context': context
        })
        
    except Exception as e:
        logger.error(f"Get conversation context error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/conversation/session', methods=['POST', 'OPTIONS'])
@optional_auth
def create_conversation_session(current_user):
    """
    Create a new conversation session
    """
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    try:
        data = request.get_json() or {}
        metadata = data.get('metadata', {})
        
        if current_user:
            metadata['user_id'] = current_user.id
        
        if app.legal_engine is None:
            return jsonify({'error': 'Legal engine not available'}), 503
        
        session_id = app.legal_engine.create_conversation_session(metadata=metadata)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'New conversation session created'
        })
        
    except Exception as e:
        logger.error(f"Create conversation session error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/conversation/session/<session_id>', methods=['DELETE', 'OPTIONS'])
@optional_auth
def delete_conversation_session(current_user, session_id):
    """
    Delete a conversation session
    """
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    try:
        if app.legal_engine is None:
            return jsonify({'error': 'Legal engine not available'}), 503
        
        success = app.legal_engine.delete_conversation_session(session_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Session deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Session not found or could not be deleted'
            }), 404
        
    except Exception as e:
        logger.error(f"Delete conversation session error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/conversation/sessions', methods=['GET', 'OPTIONS'])
@optional_auth
def list_conversation_sessions(current_user):
    """
    Get list of active conversation sessions (statistics)
    """
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    try:
        if app.legal_engine is None:
            return jsonify({'error': 'Legal engine not available'}), 503
        
        sessions_info = app.legal_engine.list_active_sessions()
        
        return jsonify({
            'success': True,
            'sessions': sessions_info
        })
        
    except Exception as e:
        logger.error(f"List conversation sessions error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
            'conversation_memory': ml_status.get('conversation_manager', {}).get('available', False),
            'context_tracking': ml_status['features'].get('context_tracking', False),
            'document_analysis': app.document_analyzer is not None
        }
    })
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/api/search-cases', methods=['POST', 'OPTIONS'])
@optional_auth
def search_cases(current_user):
    """
    Search legal cases with advanced filters
    
    Request Body:
        {
            "query": "divorce rights",
            "filters": {
                "from_date": "2015",
                "to_date": "2024",
                "courts": ["Supreme Court of India", "Delhi High Court"],
                "jurisdiction": "Delhi",
                "legal_domain": "Family",
                "min_relevance": 0.5,
                "has_judges": true,
                "has_citations": false,
                "top_k": 20,
                "sort_by": "relevance",
                "sort_order": "desc"
            },
            "page": 1,
            "per_page": 10
        }
    
    Response:
        {
            "success": true,
            "query": "divorce rights",
            "results": [...],
            "total_count": 45,
            "filtered_count": 20,
            "page": 1,
            "per_page": 10,
            "total_pages": 2,
            "filters_applied": {...}
        }
    """
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query is required'
            }), 400
        
        # Get filters and pagination
        filters = data.get('filters', {})
        page = int(data.get('page', 1))
        per_page = int(data.get('per_page', 10))
        per_page = min(per_page, 50)  # Cap at 50 per page
        
        # Search cases with filters
        all_results = app.legal_engine.search_cases(query, filters=filters)
        
        # Generate outcome prediction based on search results
        prediction_summary = None
        try:
            from prediction_service import get_prediction_service
            
            # Analyze the query and top results to generate prediction
            if len(all_results) > 0:
                # Extract facts from query and top results
                top_results_text = " ".join([
                    r.get('summary', '')[:200] for r in all_results[:5]
                ])
                
                # Create case input from search context
                case_input = {
                    'facts': query + " " + top_results_text[:500],
                    'issues': query,
                    'charges': '',
                    'court': filters.get('courts', ['other'])[0] if filters.get('courts') else 'other',
                    'case_type': filters.get('legal_domain', 'other').lower() if filters.get('legal_domain') else 'other'
                }
                
                predictor = get_prediction_service()
                prediction_result = predictor.predict_outcome(case_input)
                
                if 'error' not in prediction_result:
                    # Count actual outcomes from search results
                    outcomes_count = {'favorable': 0, 'unfavorable': 0, 'partial': 0}
                    for result in all_results[:20]:
                        outcome = result.get('outcome', '').lower()
                        if 'allow' in outcome or 'grant' in outcome or 'favor' in outcome:
                            outcomes_count['favorable'] += 1
                        elif 'dismiss' in outcome or 'reject' in outcome:
                            outcomes_count['unfavorable'] += 1
                        elif 'partial' in outcome or 'modify' in outcome:
                            outcomes_count['partial'] += 1
                    
                    total_outcomes = sum(outcomes_count.values())
                    if total_outcomes > 0:
                        outcomes_percentage = {
                            k: round((v / total_outcomes) * 100, 1) 
                            for k, v in outcomes_count.items()
                        }
                    else:
                        outcomes_percentage = outcomes_count
                    
                    prediction_summary = {
                        'predicted_outcome': prediction_result.get('outcome_label'),
                        'confidence': prediction_result.get('confidence'),
                        'description': f"Based on {total_count} similar cases, the ML model predicts: {prediction_result.get('description', '')[:200]}",
                        'historical_pattern': outcomes_percentage,
                        'similar_cases_analyzed': min(total_count, 20),
                        'top_factors': prediction_result.get('reasoning', [])[:3]
                    }
        except Exception as e:
            logger.warning(f"Prediction generation failed: {e}")
        
        # Apply pagination
        total_count = len(all_results)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_results = all_results[start_idx:end_idx]
        
        # Calculate total pages
        total_pages = (total_count + per_page - 1) // per_page
        
        response = jsonify({
            'success': True,
            'query': query,
            'results': paginated_results,
            'prediction': prediction_summary,  # ML prediction based on search results
            'total_count': total_count,
            'filtered_count': len(all_results),
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'filters_applied': filters,
            'has_next': page < total_pages,
            'has_prev': page > 1
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        logger.error(f"Search cases error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        response = jsonify({
            'success': False,
            'error': f'Search failed: {str(e)}'
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500

@app.route('/api/search-filters', methods=['GET', 'OPTIONS'])
def get_search_filters():
    """
    Get available filter options for search
    
    Returns:
        {
            "success": true,
            "filters": {
                "courts": [...],
                "legal_domains": [...],
                "jurisdictions": [...],
                "date_range": {"min": "1950", "max": "2024"}
            }
        }
    """
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    try:
        # Define available filter options
        filters = {
            'courts': [
                'Supreme Court of India',
                'Delhi High Court',
                'Bombay High Court',
                'Calcutta High Court',
                'Madras High Court',
                'Karnataka High Court',
                'Gujarat High Court',
                'Rajasthan High Court',
                'Allahabad High Court',
                'Kerala High Court',
                'Punjab and Haryana High Court',
                'Patna High Court',
                'Madhya Pradesh High Court',
                'Orissa High Court',
                'Andhra Pradesh High Court',
                'Chattisgarh High Court',
                'Jharkhand High Court',
                'Uttarakhand High Court',
                'Himachal Pradesh High Court',
                'Jammu and Kashmir High Court',
                'Gauhati High Court',
                'Sikkim High Court',
                'Tripura High Court',
                'Meghalaya High Court',
                'Manipur High Court'
            ],
            'legal_domains': [
                'Criminal',
                'Civil',
                'Family',
                'Property',
                'Constitutional',
                'Corporate',
                'Tax',
                'Labor',
                'Consumer',
                'Environmental'
            ],
            'jurisdictions': [
                'Delhi',
                'Maharashtra',
                'West Bengal',
                'Tamil Nadu',
                'Karnataka',
                'Gujarat',
                'Rajasthan',
                'Uttar Pradesh',
                'Kerala',
                'Punjab',
                'Haryana',
                'Bihar',
                'Madhya Pradesh',
                'Odisha',
                'Andhra Pradesh',
                'Telangana',
                'Chhattisgarh',
                'Jharkhand',
                'Uttarakhand',
                'Himachal Pradesh',
                'Jammu and Kashmir',
                'Assam',
                'Sikkim',
                'Tripura',
                'Meghalaya',
                'Manipur',
                'Nagaland',
                'Mizoram',
                'Arunachal Pradesh',
                'Goa'
            ],
            'date_range': {
                'min': '1950',
                'max': '2024'
            },
            'sort_options': [
                {'value': 'relevance', 'label': 'Relevance'},
                {'value': 'date', 'label': 'Date'},
                {'value': 'court', 'label': 'Court'}
            ],
            'relevance_thresholds': [
                {'value': 0.0, 'label': 'All Results'},
                {'value': 0.3, 'label': 'Somewhat Relevant (30%)'},
                {'value': 0.5, 'label': 'Moderately Relevant (50%)'},
                {'value': 0.7, 'label': 'Highly Relevant (70%)'},
                {'value': 0.9, 'label': 'Very Highly Relevant (90%)'}
            ]
        }
        
        response = jsonify({
            'success': True,
            'filters': filters
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        logger.error(f"Get search filters error: {str(e)}")
        response = jsonify({
            'success': False,
            'error': str(e)
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

@app.route('/api/translate', methods=['POST', 'OPTIONS'])
def translate_text():
    """Translate text between supported languages"""
    # Handle OPTIONS for CORS
    if request.method == 'OPTIONS':
        response = jsonify({'success': True})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        from language_service import translate_text as do_translate
        
        data = request.get_json()
        text = data.get('text', '')
        dest_lang = data.get('dest_lang', 'en')
        src_lang = data.get('src_lang', 'auto')
        
        if not text:
            return jsonify({
                'success': False,
                'error': 'No text provided'
            }), 400
        
        result = do_translate(text, dest_lang, src_lang)
        
        response = jsonify(result)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        response = jsonify({
            'success': False,
            'error': f'Translation failed: {str(e)}'
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500

@app.route('/api/detect-language', methods=['POST', 'OPTIONS'])
def detect_language_api():
    """Detect language of text"""
    # Handle OPTIONS for CORS
    if request.method == 'OPTIONS':
        response = jsonify({'success': True})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        from language_service import detect_language
        
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({
                'success': False,
                'error': 'No text provided'
            }), 400
        
        result = detect_language(text)
        
        response = jsonify(result)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        logger.error(f"Language detection error: {str(e)}")
        response = jsonify({
            'success': False,
            'error': f'Detection failed: {str(e)}'
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500

@app.route('/api/supported-languages', methods=['GET', 'OPTIONS'])
def supported_languages():
    """Get list of supported languages"""
    # Handle OPTIONS for CORS
    if request.method == 'OPTIONS':
        response = jsonify({'success': True})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        from language_service import get_supported_languages
        
        result = get_supported_languages()
        
        response = jsonify(result)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        logger.error(f"Get languages error: {str(e)}")
        response = jsonify({
            'success': False,
            'error': f'Failed to get languages: {str(e)}'
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500

@app.route('/api/text-to-speech', methods=['POST', 'OPTIONS'])
def text_to_speech_api():
    """Convert text to speech audio"""
    # Handle OPTIONS for CORS
    if request.method == 'OPTIONS':
        response = jsonify({'success': True})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        from voice_service import text_to_audio
        import os
        
        data = request.get_json()
        text = data.get('text', '')
        lang = data.get('language', 'en')
        
        if not text:
            return jsonify({
                'success': False,
                'error': 'No text provided'
            }), 400
        
        # Generate audio
        result = text_to_audio(text, lang)
        
        if not result['success']:
            response = jsonify(result)
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 500
        
        # Read audio file
        audio_path = result['audio_file']
        
        with open(audio_path, 'rb') as audio_file:
            audio_data = audio_file.read()
        
        # Clean up temp file
        try:
            os.remove(audio_path)
        except:
            pass
        
        # Return audio file
        response = Response(audio_data, mimetype='audio/mpeg')
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Content-Disposition'] = f'inline; filename=speech.mp3'
        return response
        
    except Exception as e:
        logger.error(f"Text-to-speech error: {str(e)}")
        response = jsonify({
            'success': False,
            'error': f'Text-to-speech failed: {str(e)}'
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500

@app.route('/api/speech-to-text', methods=['POST', 'OPTIONS'])
def speech_to_text_api():
    """Convert speech audio to text"""
    # Handle OPTIONS for CORS
    if request.method == 'OPTIONS':
        response = jsonify({'success': True})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        from voice_service import audio_to_text
        import tempfile
        import os
        
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No audio file uploaded'
            }), 400
        
        file = request.files['file']
        language = request.form.get('language', 'en-IN')
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        file.save(temp_file.name)
        temp_file.close()
        
        # Convert to text
        result = audio_to_text(temp_file.name, language)
        
        # Clean up temp file
        try:
            os.remove(temp_file.name)
        except:
            pass
        
        response = jsonify(result)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        logger.error(f"Speech-to-text error: {str(e)}")
        response = jsonify({
            'success': False,
            'error': f'Speech-to-text failed: {str(e)}'
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500

@app.route('/api/citation-network', methods=['GET', 'OPTIONS'])
def get_citation_network():
    """Get full citation network data"""
    # Handle OPTIONS for CORS
    if request.method == 'OPTIONS':
        response = jsonify({'success': True})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        from citation_network import get_citation_network
        
        network = get_citation_network()
        
        # Get filter parameters
        court = request.args.get('court')
        year_from = request.args.get('year_from', type=int)
        year_to = request.args.get('year_to', type=int)
        top_n = request.args.get('top_n', 100, type=int)
        
        # Export network data
        data = network.export_network_data()
        
        # Apply filters if provided
        if court or year_from or year_to:
            filtered_nodes = data['nodes']
            
            if court:
                filtered_nodes = [n for n in filtered_nodes if n['court'] == court]
            
            if year_from:
                filtered_nodes = [n for n in filtered_nodes if n['year'] >= year_from]
            
            if year_to:
                filtered_nodes = [n for n in filtered_nodes if n['year'] <= year_to]
            
            # Filter edges to only include filtered nodes
            node_ids = {n['id'] for n in filtered_nodes}
            filtered_edges = [e for e in data['edges'] 
                            if e['source'] in node_ids and e['target'] in node_ids]
            
            data['nodes'] = filtered_nodes[:top_n]
            data['edges'] = filtered_edges
        else:
            data['nodes'] = data['nodes'][:top_n]
        
        response = jsonify({
            'success': True,
            **data
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        logger.error(f"Citation network error: {str(e)}")
        response = jsonify({
            'success': False,
            'error': f'Failed to get citation network: {str(e)}'
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500

@app.route('/api/case-citations/<case_id>', methods=['GET', 'OPTIONS'])
def get_case_citations(case_id):
    """Get citations for a specific case"""
    # Handle OPTIONS for CORS
    if request.method == 'OPTIONS':
        response = jsonify({'success': True})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        from citation_network import get_citation_network
        
        network = get_citation_network()
        direction = request.args.get('direction', 'both')
        
        result = network.get_case_citations(case_id, direction)
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404
        
        response = jsonify({
            'success': True,
            **result
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        logger.error(f"Get case citations error: {str(e)}")
        response = jsonify({
            'success': False,
            'error': f'Failed to get case citations: {str(e)}'
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500

@app.route('/api/citation-path', methods=['POST', 'OPTIONS'])
def find_citation_path():
    """Find shortest citation path between two cases"""
    # Handle OPTIONS for CORS
    if request.method == 'OPTIONS':
        response = jsonify({'success': True})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        from citation_network import get_citation_network
        
        data = request.get_json()
        source_id = data.get('source_id')
        target_id = data.get('target_id')
        max_depth = data.get('max_depth', 5)
        
        if not source_id or not target_id:
            return jsonify({
                'success': False,
                'error': 'source_id and target_id required'
            }), 400
        
        network = get_citation_network()
        path = network.find_citation_path(source_id, target_id, max_depth)
        
        if path is None:
            return jsonify({
                'success': False,
                'message': 'No citation path found',
                'path': None
            })
        
        # Get case details for each node in path
        path_details = []
        for case_id in path:
            if case_id in network.cases:
                path_details.append(network.cases[case_id].to_dict())
        
        response = jsonify({
            'success': True,
            'path': path,
            'path_details': path_details,
            'length': len(path) - 1  # Number of edges
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        logger.error(f"Citation path error: {str(e)}")
        response = jsonify({
            'success': False,
            'error': f'Failed to find citation path: {str(e)}'
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500

@app.route('/api/most-cited-cases', methods=['GET', 'OPTIONS'])
def get_most_cited_cases():
    """Get most cited cases"""
    # Handle OPTIONS for CORS
    if request.method == 'OPTIONS':
        response = jsonify({'success': True})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        from citation_network import get_citation_network
        
        network = get_citation_network()
        
        top_n = request.args.get('top_n', 10, type=int)
        court = request.args.get('court')
        year_from = request.args.get('year_from', type=int)
        year_to = request.args.get('year_to', type=int)
        
        year_range = None
        if year_from and year_to:
            year_range = (year_from, year_to)
        
        most_cited = network.get_most_cited_cases(top_n, court, year_range)
        
        response = jsonify({
            'success': True,
            'cases': most_cited,
            'total': len(most_cited)
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        logger.error(f"Most cited cases error: {str(e)}")
        response = jsonify({
            'success': False,
            'error': f'Failed to get most cited cases: {str(e)}'
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500

@app.route('/api/network-statistics', methods=['GET', 'OPTIONS'])
def get_network_statistics():
    """Get citation network statistics"""
    # Handle OPTIONS for CORS
    if request.method == 'OPTIONS':
        response = jsonify({'success': True})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        from citation_network import get_citation_network
        
        network = get_citation_network()
        stats = network.get_network_statistics()
        
        response = jsonify({
            'success': True,
            **stats
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        logger.error(f"Network statistics error: {str(e)}")
        response = jsonify({
            'success': False,
            'error': f'Failed to get network statistics: {str(e)}'
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500

# ==========================================
# Case Summarization API Endpoints
# ==========================================

@app.route('/api/summarize-case', methods=['POST', 'OPTIONS'])
def summarize_case():
    """
    Generate summary for a legal case
    
    Request body:
        - case_id: Case identifier (optional, for caching)
        - case_data: Case information (title, text, court, year, etc.)
        - length: 'short', 'medium', or 'long' (default: 'medium')
        - method: 'extractive', 'abstractive', or 'hybrid' (default: 'hybrid')
        - use_cache: Whether to use cached summary if available (default: true)
    """
    # Handle OPTIONS for CORS
    if request.method == 'OPTIONS':
        response = jsonify({'success': True})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        from case_summarizer import get_summarizer
        from models import CaseSummary
        
        data = request.get_json()
        if not data:
            response = jsonify({
                'success': False,
                'error': 'No data provided'
            })
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 400
        
        case_id = data.get('case_id')
        case_data = data.get('case_data', {})
        length = data.get('length', 'medium')
        method = data.get('method', 'hybrid')
        use_cache = data.get('use_cache', True)
        
        # Validate inputs
        if not case_data and not case_id:
            response = jsonify({
                'success': False,
                'error': 'Either case_id or case_data must be provided'
            })
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 400
        
        # Check cache first if enabled
        cached_summary = None
        if use_cache and case_id:
            cached_summary = CaseSummary.get_by_case_id(
                case_id, 
                length=length, 
                summary_type=method
            )
        
        if cached_summary:
            logger.info(f"Returning cached summary for case {case_id}")
            response = jsonify({
                'success': True,
                'cached': True,
                **cached_summary.to_dict()
            })
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response
        
        # If case_id provided but no case_data, fetch from ChromaDB
        if case_id and not case_data.get('text'):
            try:
                from legal_engine_ml import LegalEngine
                engine = LegalEngine()
                
                if engine.ml_available and engine.rag and engine.rag.vector_db:
                    case_result = engine.rag.vector_db.collection.get(
                        ids=[case_id],
                        include=['documents', 'metadatas']
                    )
                    
                    if case_result and case_result['ids']:
                        case_data = {
                            'case_id': case_id,
                            'title': case_result['metadatas'][0].get('title', 'Unknown'),
                            'text': case_result['documents'][0],
                            'court': case_result['metadatas'][0].get('court', 'Unknown'),
                            'year': case_result['metadatas'][0].get('year', 'Unknown'),
                        }
                    else:
                        response = jsonify({
                            'success': False,
                            'error': f'Case {case_id} not found in database'
                        })
                        response.headers['Access-Control-Allow-Origin'] = '*'
                        return response, 404
                else:
                    response = jsonify({
                        'success': False,
                        'error': 'Vector database not available'
                    })
                    response.headers['Access-Control-Allow-Origin'] = '*'
                    return response, 503
            except Exception as e:
                logger.error(f"Error fetching case data: {e}")
                response = jsonify({
                    'success': False,
                    'error': f'Failed to fetch case data: {str(e)}'
                })
                response.headers['Access-Control-Allow-Origin'] = '*'
                return response, 500
        
        # Add case_id to case_data if provided
        if case_id:
            case_data['case_id'] = case_id
        
        # Generate summary
        summarizer = get_summarizer()
        summary_result = summarizer.summarize_case(case_data, length, method)
        
        # Cache the summary if case_id provided and no error
        if case_id and not summary_result.get('error'):
            try:
                # Get user_id from JWT if available
                user_id = None
                auth_header = request.headers.get('Authorization')
                if auth_header:
                    try:
                        from flask_jwt_extended import get_jwt_identity
                        user_id = get_jwt_identity()
                    except:
                        pass
                
                CaseSummary.cache_summary(summary_result, user_id)
            except Exception as e:
                logger.warning(f"Failed to cache summary: {e}")
        
        response = jsonify({
            'success': True,
            'cached': False,
            **summary_result
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        logger.error(f"Case summarization error: {str(e)}", exc_info=True)
        response = jsonify({
            'success': False,
            'error': f'Summarization failed: {str(e)}'
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500


@app.route('/api/summary/<case_id>', methods=['GET', 'OPTIONS'])
def get_case_summary(case_id):
    """
    Get cached summary for a specific case
    
    Query parameters:
        - length: Filter by summary length
        - type: Filter by summary type
    """
    # Handle OPTIONS for CORS
    if request.method == 'OPTIONS':
        response = jsonify({'success': True})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        from models import CaseSummary
        
        length = request.args.get('length')
        summary_type = request.args.get('type')
        
        cached_summary = CaseSummary.get_by_case_id(
            case_id,
            length=length,
            summary_type=summary_type
        )
        
        if cached_summary:
            response = jsonify({
                'success': True,
                'found': True,
                **cached_summary.to_dict()
            })
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response
        else:
            response = jsonify({
                'success': True,
                'found': False,
                'message': f'No cached summary found for case {case_id}'
            })
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 404
            
    except Exception as e:
        logger.error(f"Get summary error: {str(e)}")
        response = jsonify({
            'success': False,
            'error': f'Failed to get summary: {str(e)}'
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500


@app.route('/api/batch-summarize', methods=['POST', 'OPTIONS'])
def batch_summarize_cases():
    """
    Generate summaries for multiple cases in batch
    
    Request body:
        - cases: List of case objects or case IDs
        - length: Summary length for all cases
        - method: Summarization method for all cases
        - use_cache: Whether to use cached summaries
    """
    # Handle OPTIONS for CORS
    if request.method == 'OPTIONS':
        response = jsonify({'success': True})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        from case_summarizer import get_summarizer
        from models import CaseSummary
        
        data = request.get_json()
        if not data or 'cases' not in data:
            response = jsonify({
                'success': False,
                'error': 'No cases provided'
            })
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 400
        
        cases = data.get('cases', [])
        length = data.get('length', 'medium')
        method = data.get('method', 'hybrid')
        use_cache = data.get('use_cache', True)
        
        if not cases:
            response = jsonify({
                'success': False,
                'error': 'Empty cases list'
            })
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 400
        
        # Limit batch size
        max_batch_size = 20
        if len(cases) > max_batch_size:
            response = jsonify({
                'success': False,
                'error': f'Batch size exceeds maximum ({max_batch_size})'
            })
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 400
        
        results = []
        summarizer = get_summarizer()
        
        for case in cases:
            try:
                # If case is just an ID string, fetch case data
                if isinstance(case, str):
                    case_id = case
                    case_data = None
                    
                    # Check cache first
                    if use_cache:
                        cached = CaseSummary.get_by_case_id(case_id, length, method)
                        if cached:
                            results.append({
                                'success': True,
                                'cached': True,
                                **cached.to_dict()
                            })
                            continue
                    
                    # Fetch from database
                    # (Implementation depends on your database structure)
                    results.append({
                        'success': False,
                        'case_id': case_id,
                        'error': 'Case data fetching not implemented for batch'
                    })
                else:
                    # Case is a full object
                    case_id = case.get('case_id', case.get('id'))
                    
                    # Check cache
                    if use_cache and case_id:
                        cached = CaseSummary.get_by_case_id(case_id, length, method)
                        if cached:
                            results.append({
                                'success': True,
                                'cached': True,
                                **cached.to_dict()
                            })
                            continue
                    
                    # Generate summary
                    summary = summarizer.summarize_case(case, length, method)
                    
                    # Cache if successful
                    if case_id and not summary.get('error'):
                        try:
                            CaseSummary.cache_summary(summary)
                        except Exception as e:
                            logger.warning(f"Failed to cache summary: {e}")
                    
                    results.append({
                        'success': True,
                        'cached': False,
                        **summary
                    })
                    
            except Exception as e:
                logger.error(f"Error summarizing case in batch: {e}")
                results.append({
                    'success': False,
                    'case_id': case.get('case_id', 'unknown') if isinstance(case, dict) else case,
                    'error': str(e)
                })
        
        response = jsonify({
            'success': True,
            'total': len(cases),
            'completed': sum(1 for r in results if r.get('success')),
            'results': results
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        logger.error(f"Batch summarization error: {str(e)}", exc_info=True)
        response = jsonify({
            'success': False,
            'error': f'Batch summarization failed: {str(e)}'
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500


# =============================================================================
# CASE OUTCOME PREDICTION API
# =============================================================================

from prediction_service import get_prediction_service
from models import CasePrediction

@app.route('/api/predict-outcome', methods=['POST', 'OPTIONS'])
def predict_case_outcome():
    """
    Predict case outcome using ML model
    
    Expected JSON:
    {
        "facts": "Case facts...",
        "issues": "Legal issues...",
        "charges": "IPC sections...",
        "court": "district/high/supreme",
        "case_type": "criminal/civil/constitutional"
    }
    """
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        return response
    
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('facts'):
            response = jsonify({
                'success': False,
                'error': 'Case facts are required'
            })
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 400
        
        # Prepare case input
        case_input = {
            'facts': data.get('facts', ''),
            'issues': data.get('issues', ''),
            'charges': data.get('charges', ''),
            'court': data.get('court', 'other'),
            'case_type': data.get('case_type', 'other')
        }
        
        # Get prediction service
        predictor = get_prediction_service()
        
        # Make prediction
        prediction_result = predictor.predict_outcome(case_input)
        
        if 'error' in prediction_result:
            response = jsonify({
                'success': False,
                'error': prediction_result['error'],
                'message': 'Models may need to be trained first. Run: python case_outcome_predictor.py'
            })
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 500
        
        # Save prediction to database (if user is authenticated)
        prediction_id = None
        user_id = None
        
        try:
            # Try to get user from JWT token
            from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
            
            if user_id:
                # Save prediction
                saved_prediction = CasePrediction.save_prediction(
                    user_id=user_id,
                    case_input=case_input,
                    prediction_result=prediction_result
                )
                prediction_id = saved_prediction.id
        except Exception as e:
            logger.warning(f"Could not save prediction: {e}")
        
        # Prepare response
        response_data = {
            'success': True,
            'prediction_id': prediction_id,
            **prediction_result
        }
        
        response = jsonify(response_data)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}", exc_info=True)
        response = jsonify({
            'success': False,
            'error': f'Prediction failed: {str(e)}'
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500


@app.route('/api/prediction-history', methods=['GET', 'OPTIONS'])
def get_prediction_history():
    """Get user's prediction history"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        return response
    
    try:
        # Get user from JWT token
        from flask_jwt_extended import jwt_required, get_jwt_identity
        
        try:
            jwt_required()(lambda: None)()
            user_id = get_jwt_identity()
        except:
            response = jsonify({
                'success': False,
                'error': 'Authentication required'
            })
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 401
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Get predictions
        predictions = CasePrediction.query.filter_by(user_id=user_id)\
            .order_by(CasePrediction.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        response_data = {
            'success': True,
            'predictions': [p.to_dict(include_details=False) for p in predictions.items],
            'total': predictions.total,
            'page': page,
            'per_page': per_page,
            'pages': predictions.pages
        }
        
        response = jsonify(response_data)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        logger.error(f"Error fetching prediction history: {str(e)}", exc_info=True)
        response = jsonify({
            'success': False,
            'error': f'Failed to fetch prediction history: {str(e)}'
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500


@app.route('/api/prediction/<prediction_id>', methods=['GET', 'OPTIONS'])
def get_prediction_details(prediction_id):
    """Get details of a specific prediction"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        return response
    
    try:
        prediction = CasePrediction.query.get(prediction_id)
        
        if not prediction:
            response = jsonify({
                'success': False,
                'error': 'Prediction not found'
            })
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 404
        
        response_data = {
            'success': True,
            'prediction': prediction.to_dict(include_details=True)
        }
        
        response = jsonify(response_data)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        logger.error(f"Error fetching prediction details: {str(e)}", exc_info=True)
        response = jsonify({
            'success': False,
            'error': f'Failed to fetch prediction: {str(e)}'
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500


@app.route('/api/prediction-feedback', methods=['POST', 'OPTIONS'])
def submit_prediction_feedback():
    """
    Submit feedback on prediction accuracy
    
    Expected JSON:
    {
        "prediction_id": "uuid",
        "rating": 4,
        "was_accurate": true,
        "actual_outcome": "favorable",
        "notes": "The prediction was correct!"
    }
    """
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        return response
    
    try:
        data = request.get_json()
        
        if not data or not data.get('prediction_id'):
            response = jsonify({
                'success': False,
                'error': 'Prediction ID is required'
            })
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 400
        
        # Get prediction
        prediction = CasePrediction.query.get(data['prediction_id'])
        
        if not prediction:
            response = jsonify({
                'success': False,
                'error': 'Prediction not found'
            })
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 404
        
        # Update feedback
        prediction.update_feedback(
            rating=data.get('rating'),
            was_accurate=data.get('was_accurate'),
            actual_outcome=data.get('actual_outcome'),
            notes=data.get('notes')
        )
        
        response_data = {
            'success': True,
            'message': 'Feedback submitted successfully',
            'prediction': prediction.to_dict(include_details=False)
        }
        
        response = jsonify(response_data)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}", exc_info=True)
        response = jsonify({
            'success': False,
            'error': f'Failed to submit feedback: {str(e)}'
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500


@app.route('/api/model-info', methods=['GET', 'OPTIONS'])
def get_model_info():
    """Get information about the loaded ML models"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        return response
    
    try:
        predictor = get_prediction_service()
        model_info = predictor.get_model_info()
        
        response_data = {
            'success': True,
            **model_info
        }
        
        response = jsonify(response_data)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        logger.error(f"Error fetching model info: {str(e)}", exc_info=True)
        response = jsonify({
            'success': False,
            'error': f'Failed to fetch model info: {str(e)}'
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

# ================== DOCUMENT GENERATOR ROUTES ==================

@app.route('/api/document/templates', methods=['GET'])
def get_document_templates():
    """Get available document templates"""
    try:
        if not DOCUMENT_GENERATOR_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Document generator not available'
            }), 503
        
        generator = LegalDocumentGenerator()
        templates = generator.get_available_templates()
        
        return jsonify({
            'success': True,
            'templates': templates
        })
    except Exception as e:
        logger.error(f"Error getting templates: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/document/fields/<doc_type>', methods=['GET'])
def get_template_fields(doc_type):
    """Get required fields for a document type"""
    try:
        if not DOCUMENT_GENERATOR_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Document generator not available'
            }), 503
        
        fields = get_document_fields(doc_type)
        
        if not fields:
            return jsonify({
                'success': False,
                'error': f'Unknown document type: {doc_type}'
            }), 404
        
        return jsonify({
            'success': True,
            'doc_type': doc_type,
            'fields': fields
        })
    except Exception as e:
        logger.error(f"Error getting fields: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/document/generate', methods=['POST'])
def generate_document():
    """Generate a legal document"""
    try:
        if not DOCUMENT_GENERATOR_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Document generator not available'
            }), 503
        
        data = request.get_json()
        doc_type = data.get('doc_type')
        doc_data = data.get('data', {})
        
        if not doc_type:
            return jsonify({
                'success': False,
                'error': 'Document type is required'
            }), 400
        
        generator = LegalDocumentGenerator()
        result = generator.generate_document(doc_type, doc_data)
        
        if result.get('success'):
            logger.info(f"Generated document: {doc_type}")
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error generating document: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ================== TEXT-TO-SPEECH ROUTE ==================

@app.route('/api/text-to-speech', methods=['POST'])
def text_to_speech():
    """Convert text to speech"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        language = data.get('language', 'en')
        
        if not text:
            return jsonify({
                'success': False,
                'error': 'Text is required'
            }), 400
        
        # Return configuration for client-side TTS
        return jsonify({
            'success': True,
            'message': 'Use browser Web Speech API for TTS',
            'config': {
                'text': text,
                'language': language,
                'voice_map': {
                    'en': 'en-US',
                    'hi': 'hi-IN',
                    'ta': 'ta-IN',
                    'te': 'te-IN',
                    'bn': 'bn-IN',
                    'mr': 'mr-IN'
                }
            }
        })
    except Exception as e:
        logger.error(f"Error in TTS: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Apply rate limiting to routes
    app.apply_rate_limits()
    
    print("Legal Assistant Starting...")

    print(f"AI Provider: {config.get_active_provider().upper()}")
    print("Server: http://0.0.0.0:5000")
    print("-" * 40)
    
    # Run the Flask app
    port = int(os.environ.get('PORT', 8080))  # AWS App Runner uses port 8080
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug_mode, host='0.0.0.0', port=port, use_reloader=False)