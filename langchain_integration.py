"""
Flask LangChain Integration
Integrates LangChain Legal Assistant with existing Flask application
"""

from flask import Blueprint, request, jsonify, session, current_app
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

from langchain_legal_assistant import create_langchain_legal_assistant, LegalChatConfig
from config import Config

logger = logging.getLogger(__name__)

# Create Blueprint
langchain_bp = Blueprint('langchain', __name__, url_prefix='/api/langchain')

# Global LangChain assistant instance
_langchain_assistant = None

def init_langchain_assistant():
    """Initialize LangChain assistant"""
    global _langchain_assistant
    
    try:
        # Check if API key is available
        api_key = Config.GEMINI_API_KEY
        if not api_key:
            logger.error("Gemini API key not found")
            return None
        
        # Create configuration
        config = LegalChatConfig(
            model_name="gemini-pro",
            temperature=0.7,
            max_tokens=1000,
            chunk_size=1000,
            chunk_overlap=200,
            memory_window=10,
            vector_db_path="./data/langchain_vectordb"
        )
        
        # Initialize assistant
        _langchain_assistant = create_langchain_legal_assistant(api_key, config)
        logger.info("✅ LangChain Legal Assistant initialized")
        return _langchain_assistant
        
    except Exception as e:
        logger.error(f"Failed to initialize LangChain assistant: {e}")
        return None

def get_langchain_assistant():
    """Get or create LangChain assistant instance"""
    global _langchain_assistant
    
    if _langchain_assistant is None:
        _langchain_assistant = init_langchain_assistant()
    
    return _langchain_assistant

@langchain_bp.route('/chat', methods=['POST'])
def langchain_chat():
    """Enhanced chat endpoint using LangChain"""
    try:
        data = request.get_json()
        query = data.get('message', '').strip()
        
        if not query:
            return jsonify({
                'error': 'Message is required',
                'status': 'error'
            }), 400
        
        # Get or create session ID
        session_id = session.get('langchain_session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            session['langchain_session_id'] = session_id
        
        # Get LangChain assistant
        assistant = get_langchain_assistant()
        if not assistant:
            return jsonify({
                'error': 'LangChain assistant not available',
                'status': 'error'
            }), 503
        
        # Process query with LangChain
        response = assistant.legal_chat(query, session_id)
        
        return jsonify({
            'response': response['answer'],
            'sources': response.get('source_documents', []),
            'session_id': session_id,
            'timestamp': response.get('timestamp'),
            'status': 'success',
            'enhanced': True  # Indicates LangChain enhancement
        })
        
    except Exception as e:
        logger.error(f"Error in LangChain chat: {e}")
        return jsonify({
            'error': 'Failed to process request with LangChain',
            'details': str(e),
            'status': 'error'
        }), 500

@langchain_bp.route('/document/upload', methods=['POST'])
def upload_document():
    """Upload and process document with LangChain"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'error': 'No file uploaded',
                'status': 'error'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'error': 'No file selected',
                'status': 'error'
            }), 400
        
        # Save uploaded file
        upload_dir = 'uploads'
        os.makedirs(upload_dir, exist_ok=True)
        
        filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Get LangChain assistant
        assistant = get_langchain_assistant()
        if not assistant:
            return jsonify({
                'error': 'LangChain assistant not available',
                'status': 'error'
            }), 503
        
        # Process document
        documents = assistant.process_documents([file_path])
        
        # Clean up uploaded file
        os.remove(file_path)
        
        return jsonify({
            'message': f'Document processed successfully. Added {len(documents)} chunks to knowledge base.',
            'chunks_added': len(documents),
            'filename': file.filename,
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        return jsonify({
            'error': 'Failed to process document',
            'details': str(e),
            'status': 'error'
        }), 500

@langchain_bp.route('/document/analyze', methods=['POST'])
def analyze_document():
    """Analyze document content with LangChain"""
    try:
        data = request.get_json()
        document_content = data.get('content', '')
        analysis_query = data.get('query', 'Analyze this legal document')
        
        if not document_content:
            return jsonify({
                'error': 'Document content is required',
                'status': 'error'
            }), 400
        
        # Get LangChain assistant
        assistant = get_langchain_assistant()
        if not assistant:
            return jsonify({
                'error': 'LangChain assistant not available',
                'status': 'error'
            }), 503
        
        # Analyze document
        analysis = assistant.analyze_document(document_content, analysis_query)
        
        return jsonify({
            'analysis': analysis,
            'query': analysis_query,
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Error analyzing document: {e}")
        return jsonify({
            'error': 'Failed to analyze document',
            'details': str(e),
            'status': 'error'
        }), 500

@langchain_bp.route('/research/case-law', methods=['POST'])
def research_case_law():
    """Research case law using LangChain"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({
                'error': 'Research query is required',
                'status': 'error'
            }), 400
        
        # Get LangChain assistant
        assistant = get_langchain_assistant()
        if not assistant:
            return jsonify({
                'error': 'LangChain assistant not available',
                'status': 'error'
            }), 503
        
        # Research case law
        research_results = assistant.research_case_law(query)
        
        return jsonify({
            'research': research_results,
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Error researching case law: {e}")
        return jsonify({
            'error': 'Failed to research case law',
            'details': str(e),
            'status': 'error'
        }), 500

@langchain_bp.route('/advice', methods=['POST'])
def get_legal_advice():
    """Get comprehensive legal advice using LangChain"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        context_docs = data.get('context', None)
        
        if not query:
            return jsonify({
                'error': 'Legal query is required',
                'status': 'error'
            }), 400
        
        # Get LangChain assistant
        assistant = get_langchain_assistant()
        if not assistant:
            return jsonify({
                'error': 'LangChain assistant not available',
                'status': 'error'
            }), 503
        
        # Get legal advice
        advice = assistant.get_legal_advice(query, context_docs)
        
        return jsonify({
            'advice': advice,
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Error getting legal advice: {e}")
        return jsonify({
            'error': 'Failed to get legal advice',
            'details': str(e),
            'status': 'error'
        }), 500

@langchain_bp.route('/session/clear', methods=['POST'])
def clear_session():
    """Clear LangChain conversation memory"""
    try:
        # Get LangChain assistant
        assistant = get_langchain_assistant()
        if not assistant:
            return jsonify({
                'error': 'LangChain assistant not available',
                'status': 'error'
            }), 503
        
        # Clear memory
        assistant.clear_memory()
        
        # Clear session
        session.pop('langchain_session_id', None)
        
        return jsonify({
            'message': 'Session cleared successfully',
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        return jsonify({
            'error': 'Failed to clear session',
            'details': str(e),
            'status': 'error'
        }), 500

@langchain_bp.route('/session/save', methods=['POST'])
def save_session():
    """Save current LangChain session"""
    try:
        data = request.get_json()
        session_name = data.get('name', f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        session_id = session.get('langchain_session_id')
        if not session_id:
            return jsonify({
                'error': 'No active session to save',
                'status': 'error'
            }), 400
        
        # Get LangChain assistant
        assistant = get_langchain_assistant()
        if not assistant:
            return jsonify({
                'error': 'LangChain assistant not available',
                'status': 'error'
            }), 503
        
        # Save session
        filename = assistant.save_session(session_id, f"sessions/{session_name}.json")
        
        return jsonify({
            'message': 'Session saved successfully',
            'filename': filename,
            'session_id': session_id,
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Error saving session: {e}")
        return jsonify({
            'error': 'Failed to save session',
            'details': str(e),
            'status': 'error'
        }), 500

@langchain_bp.route('/status', methods=['GET'])
def get_status():
    """Get LangChain integration status"""
    try:
        assistant = get_langchain_assistant()
        
        return jsonify({
            'langchain_available': assistant is not None,
            'gemini_configured': Config.GEMINI_API_KEY is not None,
            'vector_db_path': "./data/langchain_vectordb",
            'status': 'success' if assistant else 'unavailable'
        })
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({
            'error': 'Failed to get status',
            'details': str(e),
            'status': 'error'
        }), 500

# Initialize when blueprint is registered
def init_langchain_blueprint(app):
    """Initialize LangChain blueprint with app"""
    with app.app_context():
        init_langchain_assistant()
    
    app.register_blueprint(langchain_bp)