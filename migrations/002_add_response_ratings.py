"""
Database migration: Add ResponseRating table
Creates the response_ratings table for storing user ratings of AI responses
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app_with_db import app
from models import db, ResponseRating

def upgrade():
    """Create ResponseRating table"""
    with app.app_context():
        # Create the table
        db.create_all()
        
        # Verify table was created
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'response_ratings' in tables:
            print("✅ ResponseRating table created successfully")
            
            # Show table schema
            columns = inspector.get_columns('response_ratings')
            print("\n📋 Table Schema:")
            for col in columns:
                print(f"  • {col['name']}: {col['type']}")
            
            return True
        else:
            print("❌ Failed to create ResponseRating table")
            return False

def downgrade():
    """Drop ResponseRating table"""
    with app.app_context():
        ResponseRating.__table__.drop(db.engine)
        print("✅ ResponseRating table dropped")

if __name__ == '__main__':
    print("="*60)
    print("🔧 Database Migration: Add ResponseRating Table")
    print("="*60)
    
    success = upgrade()
    
    if success:
        print("\n✅ Migration completed successfully")
    else:
        print("\n❌ Migration failed")
        sys.exit(1)
