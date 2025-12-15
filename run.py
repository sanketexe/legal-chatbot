"""
LegalAssist Pro - Startup Script
Simple script to run the application
"""

from app import app, config

if __name__ == '__main__':
    print("=" * 60)
    print("LegalAssist Pro - AI Legal Consultation Platform")
    print("=" * 60)
    print(f"Server: http://{config.HOST}:{config.PORT}")
    print(f"AI Provider: {config.get_active_provider().upper()}")
    print("=" * 60)
    print("\nPress CTRL+C to stop the server\n")
    
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG,
        use_reloader=False  # Disable auto-reload to prevent request interruption
    )
