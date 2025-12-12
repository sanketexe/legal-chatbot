"""
LangChain-Enhanced Legal Assistant App
Simplified version with LangChain integration
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

# Import configuration
from config import Config

# LangChain integration
try:
    from langchain_legal_assistant import create_langchain_legal_assistant, LegalChatConfig
    LANGCHAIN_AVAILABLE = True
    print("✅ LangChain integration loaded successfully")
except ImportError as e:
    LANGCHAIN_AVAILABLE = False
    print(f"⚠️ LangChain not available: {e}")

def create_app():
    """Create Flask application with LangChain integration"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = Config.SECRET_KEY or 'legal-assistant-secret'
    
    # Enable CORS
    CORS(app)
    
    # Initialize LangChain assistant
    langchain_assistant = None
    
    if LANGCHAIN_AVAILABLE and Config.GEMINI_API_KEY:
        try:
            config = LegalChatConfig(
                model_name="gemini-pro",
                temperature=0.7,
                max_tokens=1000,
                chunk_size=1000,
                chunk_overlap=200,
                memory_window=10,
                vector_db_path="./data/langchain_vectordb"
            )
            langchain_assistant = create_langchain_legal_assistant(Config.GEMINI_API_KEY, config)
            print("🔗 LangChain Legal Assistant initialized")
        except Exception as e:
            print(f"❌ Failed to initialize LangChain: {e}")
    
    # Routes
    @app.route('/')
    def index():
        return render_template('legal_interface.html')
    
    @app.route('/api/chat', methods=['POST'])
    def chat():
        try:
            data = request.get_json()
            message = data.get('message', '').strip()
            
            if not message:
                return jsonify({'error': 'Message is required'}), 400
            
            # Use LangChain if available
            if langchain_assistant:
                session_id = session.get('session_id')
                if not session_id:
                    session_id = str(uuid.uuid4())
                    session['session_id'] = session_id
                
                response = langchain_assistant.legal_chat(message, session_id)
                
                return jsonify({
                    'response': response['answer'],
                    'sources': response.get('source_documents', []),
                    'enhanced': True,
                    'timestamp': response.get('timestamp')
                })
            else:
                # Fallback response
                return jsonify({
                    'response': get_fallback_response(message),
                    'enhanced': False,
                    'timestamp': datetime.now().isoformat()
                })
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/langchain/status')
    def langchain_status():
        return jsonify({
            'langchain_available': LANGCHAIN_AVAILABLE,
            'gemini_configured': Config.GEMINI_API_KEY is not None,
            'assistant_ready': langchain_assistant is not None,
            'vector_db_path': "./data/langchain_vectordb"
        })
    
    @app.route('/api/langchain/chat', methods=['POST'])
    def langchain_chat():
        if not langchain_assistant:
            return jsonify({'error': 'LangChain assistant not available'}), 503
        
        try:
            data = request.get_json()
            message = data.get('message', '').strip()
            
            if not message:
                return jsonify({'error': 'Message is required'}), 400
            
            session_id = session.get('langchain_session_id')
            if not session_id:
                session_id = str(uuid.uuid4())
                session['langchain_session_id'] = session_id
            
            response = langchain_assistant.legal_chat(message, session_id)
            
            return jsonify({
                'response': response['answer'],
                'sources': response.get('source_documents', []),
                'session_id': session_id,
                'timestamp': response.get('timestamp'),
                'enhanced': True
            })
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/langchain/document/analyze', methods=['POST'])
    def analyze_document():
        if not langchain_assistant:
            return jsonify({'error': 'LangChain assistant not available'}), 503
        
        try:
            data = request.get_json()
            content = data.get('content', '')
            query = data.get('query', 'Analyze this legal document')
            
            if not content:
                return jsonify({'error': 'Document content is required'}), 400
            
            analysis = langchain_assistant.analyze_document(content, query)
            
            return jsonify({
                'analysis': analysis,
                'query': query,
                'timestamp': datetime.now().isoformat()
            })
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return app

def get_fallback_response(message):
    """Provide fallback legal responses when LangChain is not available"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['contract', 'agreement', 'breach']):
        return """**Contract Law Information:**

A valid contract requires:
1. **Offer** - Clear proposal with definite terms
2. **Acceptance** - Unqualified agreement to the offer
3. **Consideration** - Something of value exchanged
4. **Capacity** - Legal ability to enter contracts
5. **Legality** - Lawful purpose and terms

**Common Issues:**
- Breach of contract remedies include damages, specific performance, or rescission
- Contracts must be clear and unambiguous
- Some contracts require written documentation

**Disclaimer:** This is general information, not legal advice. Consult a lawyer for specific cases."""

    elif any(word in message_lower for word in ['employment', 'job', 'workplace', 'salary']):
        return """**Employment Law Guidance:**

**Key Employment Rights:**
- Fair wages and timely payment
- Safe working conditions
- Protection from discrimination
- Notice period for termination

**Common Issues:**
- Wrongful termination
- Wage disputes
- Workplace harassment
- Contract violations

**Indian Labor Laws:**
- Industrial Disputes Act, 1947
- Payment of Wages Act, 1936
- Factories Act, 1948

**Disclaimer:** This is general information. Consult an employment lawyer for specific issues."""

    elif any(word in message_lower for word in ['property', 'real estate', 'rent', 'landlord']):
        return """**Property Law Information:**

**Property Rights:**
- Ownership and possession rights
- Transfer of property procedures
- Landlord-tenant regulations

**Key Considerations:**
- Proper documentation required
- Registration of property transactions
- Rent control laws vary by state

**Common Issues:**
- Property disputes
- Rental agreements
- Ownership verification

**Disclaimer:** Property laws vary significantly. Consult a property lawyer for specific advice."""

    else:
        return """**General Legal Guidance:**

I can help with various legal topics including:

- **Contract Law** - Agreements, breach, remedies
- **Employment Law** - Workplace rights, termination
- **Property Law** - Real estate, rental issues
- **Family Law** - Marriage, divorce, custody
- **Criminal Law** - Basic rights and procedures

Please ask specific questions about your legal situation for more detailed guidance.

**Important:** This chatbot provides general legal information, not legal advice. For specific legal matters, always consult with a qualified attorney."""

if __name__ == '__main__':
    # Create directories
    os.makedirs('data/langchain_vectordb', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    # Create simple template if it doesn't exist
    template_path = 'templates/legal_interface.html'
    if not os.path.exists(template_path):
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LangChain Legal Assistant</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; color: #2c3e50; margin-bottom: 30px; }
        .chat-container { border: 1px solid #ddd; border-radius: 10px; padding: 20px; margin-bottom: 20px; }
        .message { margin-bottom: 15px; padding: 10px; border-radius: 5px; }
        .user { background-color: #3498db; color: white; text-align: right; }
        .assistant { background-color: #ecf0f1; }
        .enhanced { border-left: 4px solid #27ae60; }
        .input-area { display: flex; gap: 10px; }
        input[type="text"] { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        button { padding: 10px 20px; background-color: #3498db; color: white; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background-color: #2980b9; }
        .status { text-align: center; margin-bottom: 20px; padding: 10px; border-radius: 5px; }
        .status.enhanced { background-color: #d5f4e6; color: #27ae60; }
        .status.fallback { background-color: #fff3cd; color: #856404; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔗 LangChain Legal Assistant</h1>
        <p>AI-Powered Legal Consultation with Enhanced Memory</p>
    </div>
    
    <div id="status" class="status">Checking LangChain status...</div>
    
    <div class="chat-container" id="chatContainer">
        <div class="message assistant">
            <strong>Legal Assistant:</strong> Hello! I'm your AI legal assistant enhanced with LangChain. 
            I can help with contract law, employment issues, property matters, and more. 
            How can I assist you today?
        </div>
    </div>
    
    <div class="input-area">
        <input type="text" id="messageInput" placeholder="Ask your legal question..." onkeypress="handleKeyPress(event)">
        <button onclick="sendMessage()">Send</button>
    </div>
    
    <script>
        let isLangChainReady = false;
        
        // Check LangChain status on load
        fetch('/api/langchain/status')
            .then(response => response.json())
            .then(data => {
                const statusDiv = document.getElementById('status');
                if (data.assistant_ready) {
                    statusDiv.textContent = '✅ LangChain Enhanced Mode Active';
                    statusDiv.className = 'status enhanced';
                    isLangChainReady = true;
                } else {
                    statusDiv.textContent = '⚠️ Fallback Mode - LangChain not available';
                    statusDiv.className = 'status fallback';
                }
            })
            .catch(error => {
                console.error('Status check failed:', error);
                document.getElementById('status').textContent = '❌ Unable to check status';
            });
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message
            addMessage(message, 'user');
            input.value = '';
            
            // Show thinking indicator
            const thinkingId = 'thinking-' + Date.now();
            addMessage('🤔 Thinking...', 'assistant', thinkingId);
            
            // Choose endpoint based on availability
            const endpoint = isLangChainReady ? '/api/langchain/chat' : '/api/chat';
            
            fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: message })
            })
            .then(response => response.json())
            .then(data => {
                // Remove thinking indicator
                document.getElementById(thinkingId).remove();
                
                if (data.error) {
                    addMessage('❌ Error: ' + data.error, 'assistant');
                } else {
                    const enhanced = data.enhanced ? ' enhanced' : '';
                    addMessage(data.response, 'assistant' + enhanced);
                    
                    // Show sources if available
                    if (data.sources && data.sources.length > 0) {
                        const sourceText = '\\n\\n📚 Sources: ' + data.sources.length + ' references found';
                        addMessage(sourceText, 'assistant sources');
                    }
                }
            })
            .catch(error => {
                document.getElementById(thinkingId).remove();
                addMessage('❌ Connection error: ' + error.message, 'assistant');
            });
        }
        
        function addMessage(text, type, id = null) {
            const container = document.getElementById('chatContainer');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + type;
            if (id) messageDiv.id = id;
            
            if (type === 'user') {
                messageDiv.innerHTML = '<strong>You:</strong> ' + text;
            } else {
                messageDiv.innerHTML = '<strong>Legal Assistant:</strong> ' + text.replace(/\\n/g, '<br>');
            }
            
            container.appendChild(messageDiv);
            container.scrollTop = container.scrollHeight;
        }
    </script>
</body>
</html>""")
    
    # Start the application
    app = create_app()
    config = Config()
    
    print("=" * 60)
    print("🔗 LangChain Legal Assistant")
    print("=" * 60)
    print(f"🌐 Server: http://{config.HOST}:{config.PORT}")
    print(f"🤖 AI Provider: {config.get_active_provider().upper()}")
    print(f"🔗 LangChain: {'✅ Available' if LANGCHAIN_AVAILABLE else '❌ Not Available'}")
    print("=" * 60)
    print("\\nPress CTRL+C to stop the server\\n")
    
    app.run(host=config.HOST, port=config.PORT, debug=True)