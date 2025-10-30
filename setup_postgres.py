#!/usr/bin/env python3
"""
One-time script to create PostgreSQL database tables
Run this after updating DATABASE_URL in .env
"""

from app_with_db import create_app
from models import db, User, ChatSession, Message

def setup_database():
    """Create all database tables"""
    app = create_app()
    
    with app.app_context():
        print("🔄 Creating database tables...")
        try:
            db.create_all()
            print("✅ All tables created successfully!")
            
            # Verify tables exist
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"\n📊 Tables created: {', '.join(tables)}")
            
            # Show table details
            for table in tables:
                columns = inspector.get_columns(table)
                print(f"\n  {table}:")
                for col in columns:
                    print(f"    - {col['name']} ({col['type']})")
                    
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == '__main__':
    import os
    
    # Check if DATABASE_URL is set
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ ERROR: DATABASE_URL not found in environment variables")
        print("   Please add it to your .env file")
        exit(1)
    
    # Show which database we're connecting to
    if 'sqlite' in db_url:
        print("⚠️  WARNING: Still using SQLite")
        print(f"   Connection: {db_url}")
    else:
        # Hide password in output
        if '@' in db_url:
            safe_url = db_url.split('@')[1] if '@' in db_url else db_url
            print(f"🔗 Connecting to PostgreSQL: {safe_url}")
        else:
            print(f"🔗 Connecting to PostgreSQL")
    
    # Setup database
    if setup_database():
        print("\n✅ Database setup complete!")
        print("   You can now run: python app_with_db.py")
    else:
        print("\n❌ Database setup failed!")
        exit(1)
