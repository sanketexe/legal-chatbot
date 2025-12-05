"""
Migration: Add user preferences table
Run: python migrations/001_add_user_preferences.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import app and db
try:
    from app_with_db import create_app, db
except ImportError:
    print("❌ Error: Could not import app_with_db")
    print("   Make sure you run this from the project root directory")
    sys.exit(1)

app = create_app()


def run_migration():
    """Run the migration"""
    with app.app_context():
        try:
            print("=" * 60)
            print("MIGRATION: Add UserPreference Table")
            print("=" * 60)
            
            # Create table
            print("\n📝 Creating user_preferences table...")
            db.create_all()
            
            # List all tables
            inspector = db.inspect(db.engine)
            tables = sorted(inspector.get_table_names())
            
            print(f"\n✅ Migration successful!")
            print(f"\n📊 Tables in database ({len(tables)} total):")
            for table in tables:
                print(f"   • {table}")
            
            # Check if user_preferences table exists
            if 'user_preferences' in tables:
                print("\n✅ user_preferences table created successfully")
                
                # Get column info
                columns = inspector.get_columns('user_preferences')
                print(f"\n📋 user_preferences columns ({len(columns)} total):")
                for col in columns:
                    nullable = "nullable" if col['nullable'] else "NOT NULL"
                    print(f"   • {col['name']:25s} {str(col['type']):15s} {nullable}")
            else:
                print("\n⚠️ WARNING: user_preferences table not found")
                return False
            
            print("\n" + "=" * 60)
            print("✅ MIGRATION COMPLETE")
            print("=" * 60)
            return True
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            print(f"\nError type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)

