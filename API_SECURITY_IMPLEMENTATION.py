# API Endpoint Security Implementation
# Add this code to app_with_db.py to protect your API endpoints

import os
from functools import wraps
from flask import request, jsonify

# ============================================
# SECURITY MIDDLEWARE - Add after imports
# ============================================

def require_api_key(f):
    """
    Decorator to require API key for protected endpoints
    Usage: @require_api_key above any route
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get API key from header
        api_key = request.headers.get('X-API-Key')
        
        # Get expected key from environment variable
        expected_key = os.getenv('API_SECRET_KEY')
        
        # Verify API key
        if not expected_key:
            return jsonify({
                'error': 'API authentication not configured',
                'status': 'error'
            }), 500
            
        if not api_key:
            return jsonify({
                'error': 'API key required',
                'status': 'error',
                'message': 'Include X-API-Key header in your request'
            }), 401
            
        if api_key != expected_key:
            return jsonify({
                'error': 'Invalid API key',
                'status': 'error'
            }), 403
            
        return f(*args, **kwargs)
    return decorated_function


# ============================================
# RATE LIMITING - Install: pip install flask-limiter
# ============================================

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Add after app initialization
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"  # Use Redis in production: "redis://localhost:6379"
)


# ============================================
# APPLY TO EXISTING ROUTES
# ============================================

# Example 1: Protect /api/chat
@app.route('/api/chat', methods=['POST'])
@require_api_key  # Add this line
@limiter.limit("10 per minute")  # Add this line
def chat():
    # ... existing code ...
    pass


# Example 2: Protect /api/analyze-document
@app.route('/api/analyze-document', methods=['POST'])
@require_api_key  # Add this line
@limiter.limit("5 per minute")  # Add this line (lower limit for document processing)
def analyze_document():
    # ... existing code ...
    pass


# Example 3: Protect /api/register (prevent spam accounts)
@app.route('/api/register', methods=['POST'])
@limiter.limit("3 per hour")  # Add this line
def register():
    # ... existing code ...
    pass


# ============================================
# UPDATE FRONTEND TO SEND API KEY
# ============================================

# In templates/simple.html, update fetch calls:
"""
// Add API key to all fetch requests
const apiKey = 'YOUR_CLIENT_API_KEY';  // Store securely, NOT in code

fetch('/api/chat', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey  // Add this header
    },
    body: JSON.stringify(data)
})
"""


# ============================================
# ENVIRONMENT VARIABLES TO ADD IN VERCEL
# ============================================

"""
Add these in Vercel Dashboard → Settings → Environment Variables:

1. API_SECRET_KEY=your_secure_random_key_here
   (Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")

2. GEMINI_API_KEY=your_gemini_api_key
   (Already in your .env, move to Vercel)

3. SECRET_KEY=your_flask_secret_key
   (Already in your .env, move to Vercel)

4. DATABASE_URL=postgresql://user:pass@host:5432/dbname
   (Required for production - SQLite won't work)
"""


# ============================================
# TESTING PROTECTED ENDPOINTS
# ============================================

"""
# Without API key (should fail):
curl -X POST https://your-app.vercel.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'

# With API key (should work):
curl -X POST https://your-app.vercel.app/api/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_secret_key" \
  -d '{"message": "test"}'
"""


# ============================================
# OPTIONAL: IP WHITELISTING
# ============================================

def require_whitelisted_ip(f):
    """
    Only allow specific IP addresses
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get whitelisted IPs from environment
        whitelist = os.getenv('ALLOWED_IPS', '').split(',')
        
        # Get client IP
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        if client_ip not in whitelist:
            return jsonify({
                'error': 'Access denied',
                'status': 'error'
            }), 403
            
        return f(*args, **kwargs)
    return decorated_function


# Usage:
# @app.route('/admin/endpoint')
# @require_whitelisted_ip
# def admin_endpoint():
#     pass
