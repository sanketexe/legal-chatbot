from flask import Flask, render_template, request, jsonify, session
import os
import sys
import json
from datetime import datetime
import uuid

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import configuration
from config import Config
from simple_legal_engine import LegalReasoningEngine

app = Flask(__name__)
config = Config()
app.secret_key = config.SECRET_KEY

# Initialize only the core legal engine
legal_engine = LegalReasoningEngine()

# Print startup info
print(f"\n⚖️ Legal Assistant Starting...")
print(f"📡 AI Provider: {config.get_active_provider().upper()}")
print(f"🌐 Server: http://{config.HOST}:{config.PORT}")
print("-" * 40)

@app.route('/')
def index():
    """Simple chat interface"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        session['messages'] = []
    
    return render_template('simple.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle simple chat messages"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Initialize session if needed
        if 'messages' not in session:
            session['messages'] = []
        
        # Add user message to session
        user_msg = {
            'role': 'user',
            'content': user_message,
            'timestamp': datetime.now().isoformat()
        }
        session['messages'].append(user_msg)
        
        # Get legal response (simplified - no complex context)
        response_content = legal_engine.get_legal_response(
            user_message, 
            session['messages'],
            {}  # Empty context - no jurisdiction/experience complexity
        )
        
        # Add assistant response to session
        assistant_msg = {
            'role': 'assistant',
            'content': response_content,
            'timestamp': datetime.now().isoformat()
        }
        session['messages'].append(assistant_msg)
        
        # Update session
        session.modified = True
        
        return jsonify({
            'response': response_content,
            'timestamp': assistant_msg['timestamp']
        })
        
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/api/chat/clear', methods=['POST'])
def clear_chat():
    """Clear chat history"""
    session['messages'] = []
    session.modified = True
    return jsonify({'status': 'Chat history cleared'})

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'ai_provider': config.get_active_provider(),
        'available_providers': config.get_available_providers()
    })

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    print("⚖️ Legal Assistant Starting...")
    print(f"📡 AI Provider: {config.get_active_provider().upper()}")
    print("🌐 Server: http://0.0.0.0:5000")
    print("-" * 40)
    
    # Run the Flask app
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug_mode, host='0.0.0.0', port=port, use_reloader=False)