"""
Migration: Add user preferences table
Run: python migrations/001_add_user_preferences.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logging_config import get_logger

logger = get_logger(__name__)

# Import app and db
try:
    from app_with_db import create_app, db
except ImportError:
    logger.error("Could not import app_with_db")
    logger.info("Make sure you run this from the project root directory")
    sys.exit(1)

app = create_app()


def run_migration():
    """Run the migration"""
    with app.app_context():
        try:
            logger.info("%s", "=" * 60)
            logger.info("MIGRATION: Add UserPreference Table")
            logger.info("%s", "=" * 60)
            
            # Create table
            logger.info("Creating user_preferences table...")
            db.create_all()
            
            # List all tables
            inspector = db.inspect(db.engine)
            tables = sorted(inspector.get_table_names())
            
            logger.info("Migration successful!")
            logger.info("Tables in database (%d total):", len(tables))
            for table in tables:
                logger.info("   - %s", table)
            
            # Check if user_preferences table exists
            if 'user_preferences' in tables:
                logger.info("user_preferences table created successfully")
                
                # Get column info
                columns = inspector.get_columns('user_preferences')
                logger.info("user_preferences columns (%d total):", len(columns))
                for col in columns:
                    nullable = "nullable" if col['nullable'] else "NOT NULL"
                    logger.info("   - %s %s %s", col['name'], str(col['type']), nullable)
            else:
                logger.warning("user_preferences table not found")
                return False
            
            logger.info("%s", "\n" + "=" * 60)
            logger.info("MIGRATION COMPLETE")
            logger.info("%s", "=" * 60)
            return True
            
        except Exception as e:
            logger.error("Migration failed: %s", e)
            logger.error("Error type: %s", type(e).__name__)
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)

