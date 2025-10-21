"""
Data Migration Script: SQLite to AWS RDS PostgreSQL
Migrates your existing legal chatbot data to AWS RDS
"""

import sqlite3
import psycopg2
import os
import sys
from datetime import datetime
from urllib.parse import urlparse

def get_database_config():
    """Get database configuration from environment or user input"""
    
    # Try to get from environment first
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("🔗 Enter your AWS RDS PostgreSQL connection details:")
        host = input("Host (RDS endpoint): ")
        port = input("Port (default 5432): ") or "5432"
        database = input("Database name (default legalchatbot): ") or "legalchatbot"
        username = input("Username: ")
        password = input("Password: ")
        
        database_url = f"postgresql://{username}:{password}@{host}:{port}/{database}"
    
    # Parse the URL
    parsed = urlparse(database_url)
    
    return {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'database': parsed.path[1:],  # Remove leading '/'
        'username': parsed.username,
        'password': parsed.password
    }

def connect_sqlite():
    """Connect to SQLite database"""
    sqlite_path = 'instance/legal_chatbot.db'
    
    if not os.path.exists(sqlite_path):
        print(f"❌ SQLite database not found at {sqlite_path}")
        return None
    
    try:
        conn = sqlite3.connect(sqlite_path)
        print(f"✅ Connected to SQLite database: {sqlite_path}")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to SQLite: {e}")
        return None

def connect_postgresql(config):
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['username'],
            password=config['password']
        )
        print(f"✅ Connected to PostgreSQL: {config['host']}")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        print("Make sure your AWS RDS instance is running and accessible.")
        return None

def create_postgresql_tables(pg_conn):
    """Create PostgreSQL tables with the same structure as SQLite"""
    
    cursor = pg_conn.cursor()
    
    # Create tables
    tables = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR(36) PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(128) NOT NULL,
            full_name VARCHAR(200),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title VARCHAR(200),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS messages (
            id VARCHAR(36) PRIMARY KEY,
            session_id VARCHAR(36) NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
            role VARCHAR(20) NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tokens_used INTEGER,
            model_used VARCHAR(50)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS user_sessions (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token_hash VARCHAR(128) NOT NULL,
            ip_address VARCHAR(45),
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            is_revoked BOOLEAN DEFAULT FALSE
        )
        """
    ]
    
    for table_sql in tables:
        cursor.execute(table_sql)
    
    # Create indexes
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
        "CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id)"
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)
    
    pg_conn.commit()
    print("✅ PostgreSQL tables created successfully")

def migrate_data(sqlite_conn, pg_conn):
    """Migrate data from SQLite to PostgreSQL"""
    
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    # Migration order: users -> chat_sessions -> messages -> user_sessions
    tables = ['users', 'chat_sessions', 'messages', 'user_sessions']
    
    for table in tables:
        print(f"📦 Migrating {table}...")
        
        # Get all data from SQLite
        sqlite_cursor.execute(f"SELECT * FROM {table}")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print(f"  📝 No data in {table}")
            continue
        
        # Get column names
        sqlite_cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in sqlite_cursor.fetchall()]
        
        # Prepare INSERT statement
        placeholders = ', '.join(['%s'] * len(columns))
        columns_str = ', '.join(columns)
        insert_sql = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
        
        # Insert data
        try:
            pg_cursor.executemany(insert_sql, rows)
            pg_conn.commit()
            print(f"  ✅ Migrated {len(rows)} records from {table}")
        except Exception as e:
            print(f"  ❌ Error migrating {table}: {e}")
            pg_conn.rollback()
            continue
    
    print("🎉 Data migration completed!")

def verify_migration(sqlite_conn, pg_conn):
    """Verify that migration was successful"""
    
    print("\n📊 Migration Verification:")
    print("=" * 40)
    
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    tables = ['users', 'chat_sessions', 'messages', 'user_sessions']
    
    for table in tables:
        # Count in SQLite
        sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        sqlite_count = sqlite_cursor.fetchone()[0]
        
        # Count in PostgreSQL
        pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        pg_count = pg_cursor.fetchone()[0]
        
        status = "✅" if sqlite_count == pg_count else "❌"
        print(f"{status} {table}: SQLite={sqlite_count}, PostgreSQL={pg_count}")

def main():
    """Main migration function"""
    
    print("🚀 Legal Chatbot Data Migration: SQLite → AWS RDS PostgreSQL")
    print("=" * 60)
    
    # Get database configuration
    print("\n🔧 Database Configuration")
    db_config = get_database_config()
    
    # Connect to databases
    print("\n🔗 Connecting to databases...")
    sqlite_conn = connect_sqlite()
    if not sqlite_conn:
        return
    
    pg_conn = connect_postgresql(db_config)
    if not pg_conn:
        sqlite_conn.close()
        return
    
    try:
        # Create PostgreSQL tables
        print("\n🏗️  Creating PostgreSQL tables...")
        create_postgresql_tables(pg_conn)
        
        # Migrate data
        print("\n📦 Starting data migration...")
        migrate_data(sqlite_conn, pg_conn)
        
        # Verify migration
        verify_migration(sqlite_conn, pg_conn)
        
        print("\n🎉 Migration completed successfully!")
        print("\n📝 Next steps:")
        print("1. Update your environment variables:")
        print("   DATABASE_URL=postgresql://username:password@host:5432/database")
        print("2. Deploy your application with app_with_db.py")
        print("3. Test the application to ensure everything works")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
    
    finally:
        # Close connections
        sqlite_conn.close()
        pg_conn.close()
        print("\n🔐 Database connections closed")

if __name__ == "__main__":
    main()