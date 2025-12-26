"""
Enhanced Security and Input Validation System
"""

import re
import html
import time
from flask import request, jsonify
from functools import wraps
import secrets
import hashlib

class SecurityValidator:
    """Comprehensive security validation"""
    
    # Security patterns
    SQL_INJECTION_PATTERNS = [
        r"(\bunion\b.*\bselect\b)",
        r"(\bselect\b.*\bfrom\b)",
        r"(\binsert\b.*\binto\b)",
        r"(\bdelete\b.*\bfrom\b)",
        r"(\bdrop\b.*\btable\b)",
        r"(\bexec\b|\bexecute\b)",
        r"(\bscript\b.*>)",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<object",
        r"<embed"
    ]
    
    @classmethod
    def sanitize_input(cls, text):
        """Sanitize user input"""
        if not isinstance(text, str):
            return text
        
        # HTML escape
        sanitized = html.escape(text)
        
        # Remove potentially dangerous patterns
        for pattern in cls.XSS_PATTERNS:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
        
        return sanitized.strip()
    
    @classmethod
    def validate_legal_query(cls, query):
        """Validate legal query input"""
        if not query or len(query.strip()) == 0:
            return False, "Query cannot be empty"
        
        if len(query) > 5000:
            return False, "Query too long (max 5000 characters)"
        
        # Check for SQL injection patterns
        query_lower = query.lower()
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, query_lower):
                return False, "Invalid characters detected"
        
        return True, "Valid"
    
    @classmethod
    def validate_file_upload(cls, file):
        """Validate uploaded files"""
        if not file:
            return False, "No file provided"
        
        # Check file size (max 10MB)
        file.seek(0, 2)  # Go to end
        size = file.tell()
        file.seek(0)     # Go back to start
        
        if size > 10 * 1024 * 1024:  # 10MB
            return False, "File too large (max 10MB)"
        
        # Check file extension
        allowed_extensions = {'.pdf', '.docx', '.txt', '.doc'}
        filename = file.filename.lower()
        
        if not any(filename.endswith(ext) for ext in allowed_extensions):
            return False, f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        
        return True, "Valid"
    
    @classmethod
    def generate_session_token(cls):
        """Generate secure session token"""
        return secrets.token_urlsafe(32)

def require_auth(f):
    """Simple authentication decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Add your authentication logic here
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def rate_limit(max_requests=100, window=3600):
    """Simple rate limiting decorator"""
    request_counts = {}
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.remote_addr
            current_time = time.time()
            
            # Clean old entries
            request_counts[client_ip] = [
                timestamp for timestamp in request_counts.get(client_ip, [])
                if current_time - timestamp < window
            ]
            
            # Check rate limit
            if len(request_counts.get(client_ip, [])) >= max_requests:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': window
                }), 429
            
            # Add current request
            request_counts.setdefault(client_ip, []).append(current_time)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Input validation schemas
LEGAL_QUERY_SCHEMA = {
    'message': {'type': str, 'required': True, 'max_length': 5000},
    'context': {'type': str, 'required': False, 'max_length': 2000},
    'language': {'type': str, 'required': False, 'allowed': ['en', 'hi']}
}

DOCUMENT_ANALYSIS_SCHEMA = {
    'content': {'type': str, 'required': True, 'max_length': 50000},
    'analysis_type': {'type': str, 'required': False, 'allowed': ['contract', 'agreement', 'general']},
    'focus_areas': {'type': list, 'required': False}
}

def validate_schema(schema):
    """Validate request data against schema"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            data = request.get_json()
            errors = []
            
            for field, rules in schema.items():
                value = data.get(field)
                
                # Check required fields
                if rules.get('required', False) and not value:
                    errors.append(f"Field '{field}' is required")
                    continue
                
                if value is None:
                    continue
                
                # Check type
                expected_type = rules.get('type')
                if expected_type and not isinstance(value, expected_type):
                    errors.append(f"Field '{field}' must be of type {expected_type.__name__}")
                    continue
                
                # Check string length
                if isinstance(value, str):
                    max_length = rules.get('max_length')
                    if max_length and len(value) > max_length:
                        errors.append(f"Field '{field}' too long (max {max_length} characters)")
                
                # Check allowed values
                allowed = rules.get('allowed')
                if allowed and value not in allowed:
                    errors.append(f"Field '{field}' must be one of: {', '.join(allowed)}")
            
            if errors:
                return jsonify({'error': 'Validation failed', 'details': errors}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator