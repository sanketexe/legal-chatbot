"""
Setup script for ML Legal System
Initializes directories, downloads models, and sets up database
"""

import os
import json
import sys
from pathlib import Path

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = [
        'data',
        'data/legal_cases',
        'data/chromadb',
        'data/processed',
        'ml_legal_system/models'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✅ {directory}")
    
    print("✅ Directories created successfully!\n")


def check_dependencies():
    """Check if required packages are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = {
        'flask': 'Flask',
        'bs4': 'beautifulsoup4',
        'chromadb': 'chromadb',
        'sentence_transformers': 'sentence-transformers',
        'numpy': 'numpy',
        'google.generativeai': 'google-generativeai'
    }
    
    missing_packages = []
    
    for package, pip_name in required_packages.items():
        try:
            __import__(package)
            print(f"  ✅ {pip_name}")
        except ImportError:
            print(f"  ❌ {pip_name} - NOT INSTALLED")
            missing_packages.append(pip_name)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print(f"\n💡 Install with: pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ All dependencies installed!\n")
    return True


def download_embedding_model():
    """Download sentence-transformers model"""
    print("📥 Downloading embedding model...")
    
    try:
        from sentence_transformers import SentenceTransformer
        
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Embedding model downloaded successfully!\n")
        return True
        
    except Exception as e:
        print(f"❌ Error downloading model: {e}\n")
        return False


def create_env_file():
    """Create .env file template if it doesn't exist"""
    print("📝 Checking .env configuration...")
    
    env_file = '.env'
    
    if os.path.exists(env_file):
        print("✅ .env file already exists\n")
        return
    
    env_template = """# LegalCounsel AI Configuration

# Flask Settings
SECRET_KEY=your-secret-key-change-this
JWT_SECRET_KEY=your-jwt-secret-key-change-this

# Database
DATABASE_URL=sqlite:///legalchat.db

# LLM Settings (Choose one)
USE_OPENAI=false
OPENAI_API_KEY=your-openai-api-key-here

# Google Gemini (FREE - Recommended)
GOOGLE_API_KEY=your-google-api-key-here

# Vector Database Settings
USE_CLOUD_VECTOR_DB=false
# PINECONE_API_KEY=your-pinecone-api-key-here
# PINECONE_ENVIRONMENT=us-east-1-aws

# Embedding Settings
USE_OPENAI_EMBEDDINGS=false

# RAG Settings
TOP_K_RETRIEVAL=5
SIMILARITY_THRESHOLD=0.7

# Scraper Settings
SCRAPER_DELAY=2.0
MAX_CASES_PER_QUERY=50
"""
    
    with open(env_file, 'w') as f:
        f.write(env_template)
    
    print(f"✅ Created {env_file} template")
    print("⚠️  Please update with your API keys!\n")


def setup_database():
    """Initialize SQLite database"""
    print("🗄️  Setting up database...")
    
    try:
        from app_with_db import db, app
        
        with app.app_context():
            db.create_all()
        
        print("✅ Database initialized successfully!\n")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}\n")
        return False


def main():
    """Run complete setup"""
    print("🚀 LegalCounsel AI - ML System Setup")
    print("=" * 60 + "\n")
    
    steps = [
        ("Creating directories", create_directories),
        ("Checking dependencies", check_dependencies),
        ("Creating .env template", create_env_file),
        ("Downloading embedding model", download_embedding_model),
        ("Setting up database", setup_database)
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        try:
            result = step_func()
            if result is False:
                failed_steps.append(step_name)
        except Exception as e:
            print(f"❌ Error in {step_name}: {e}\n")
            failed_steps.append(step_name)
    
    print("=" * 60)
    
    if not failed_steps:
        print("🎉 Setup completed successfully!")
        print("\n📝 Next steps:")
        print("1. Update .env file with your API keys")
        print("2. Run: python ml_legal_system/case_scraper.py (to collect cases)")
        print("3. Run: python ml_legal_system/legal_rag.py (to test RAG system)")
        print("4. Start Flask app: python app_with_db.py")
    else:
        print(f"⚠️  Setup completed with {len(failed_steps)} issue(s):")
        for step in failed_steps:
            print(f"  - {step}")
        print("\n💡 Please resolve these issues and run setup again.")
    
    print("=" * 60)


if __name__ == "__main__":
    main()