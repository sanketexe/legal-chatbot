"""
Database migration: Add case_summaries table
Created: 2025-01-01
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db

def upgrade():
    """Create case_summaries table"""
    with app.app_context():
        print("Running migration: 003_add_case_summaries")
        
        # Create all tables (will only create if they don't exist)
        db.create_all()
        
        print("✅ Migration complete: case_summaries table created")

def downgrade():
    """Drop case_summaries table"""
    with app.app_context():
        print("Rolling back migration: 003_add_case_summaries")
        
        # Drop the case_summaries table
        from models import CaseSummary
        CaseSummary.__table__.drop(db.engine, checkfirst=True)
        
        print("✅ Rollback complete: case_summaries table dropped")

if __name__ == '__main__':
    # Run migration
    upgrade()
