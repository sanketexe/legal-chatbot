"""
Enhanced Error Handling and Health Check System
"""

from flask import Flask, jsonify, request
from functools import wraps
import logging
import traceback
import time
from datetime import datetime
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Centralized error handling system"""
    
    @staticmethod
    def handle_api_error(error):
        """Handle API errors gracefully"""
        error_id = f"ERR_{int(time.time())}"
        
        if hasattr(error, 'code'):
            status_code = error.code
        else:
            status_code = 500
            
        error_response = {
            'error': True,
            'error_id': error_id,
            'message': str(error),
            'timestamp': datetime.now().isoformat(),
            'status_code': status_code
        }
        
        # Log error for debugging
        logger.error(f"API Error {error_id}: {str(error)}")
        logger.error(traceback.format_exc())
        
        return jsonify(error_response), status_code
    
    @staticmethod
    def validate_input(required_fields):
        """Decorator for input validation"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not request.is_json:
                    return jsonify({
                        'error': True,
                        'message': 'Content-Type must be application/json'
                    }), 400
                
                data = request.get_json()
                missing_fields = []
                
                for field in required_fields:
                    if field not in data or not data[field]:
                        missing_fields.append(field)
                
                if missing_fields:
                    return jsonify({
                        'error': True,
                        'message': f'Missing required fields: {", ".join(missing_fields)}'
                    }), 400
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator

def create_health_endpoints(app):
    """Add health check endpoints"""
    
    @app.route('/health')
    def health_check():
        """Basic health check"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'uptime': time.time()
        })
    
    @app.route('/health/detailed')
    def detailed_health_check():
        """Detailed health check"""
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        # Check database connection
        try:
            # Add your database check here
            health_data['checks']['database'] = 'healthy'
        except Exception as e:
            health_data['checks']['database'] = f'error: {str(e)}'
            health_data['status'] = 'unhealthy'
        
        # Check AI service
        try:
            # Add AI service check here
            health_data['checks']['ai_service'] = 'healthy'
        except Exception as e:
            health_data['checks']['ai_service'] = f'error: {str(e)}'
            health_data['status'] = 'unhealthy'
        
        # Check file system
        try:
            os.makedirs('logs', exist_ok=True)
            health_data['checks']['filesystem'] = 'healthy'
        except Exception as e:
            health_data['checks']['filesystem'] = f'error: {str(e)}'
            health_data['status'] = 'unhealthy'
        
        status_code = 200 if health_data['status'] == 'healthy' else 503
        return jsonify(health_data), status_code

# Performance monitoring decorator
def monitor_performance(f):
    """Monitor API performance"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        try:
            result = f(*args, **kwargs)
            end_time = time.time()
            logger.info(f"{f.__name__} completed in {end_time - start_time:.2f}s")
            return result
        except Exception as e:
            end_time = time.time()
            logger.error(f"{f.__name__} failed after {end_time - start_time:.2f}s: {str(e)}")
            raise
    return decorated_function