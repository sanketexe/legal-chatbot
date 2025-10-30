"""
Load scraped cases into vector database
Run this after scraping to make cases searchable
"""

import json
import os
from vector_db import LegalVectorDatabase


def load_cases_to_db():
    """Load all scraped cases into vector database"""
    
    print("📚 Loading Cases into Vector Database")
    print("=" * 60)
    
    # Path to complete cases dataset
    cases_file = 'data/legal_cases/indian_legal_cases_complete.json'
    
    if not os.path.exists(cases_file):
        print(f"❌ Case file not found: {cases_file}")
        print("💡 Run case_scraper.py first to collect cases")
        return
    
    # Load cases
    print(f"📖 Reading cases from: {cases_file}")
    with open(cases_file, 'r', encoding='utf-8') as f:
        cases = json.load(f)
    
    print(f"✅ Loaded {len(cases)} cases")
    
    # Initialize vector database
    print("\n🔄 Initializing vector database...")
    db = LegalVectorDatabase(use_cloud=False)
    
    # Add cases to database
    print(f"\n📊 Adding {len(cases)} cases to vector database...")
    print("⏱️  This will take 5-10 minutes...")
    
    db.add_cases(cases, batch_size=50)
    
    print("\n" + "=" * 60)
    print("🎉 Successfully loaded all cases into vector database!")
    print("\n📝 Next steps:")
    print("1. Test RAG: python ml_legal_system\\legal_rag.py")
    print("2. Test integration: python legal_engine_ml.py")
    print("3. Start chatbot: python app_with_db.py")
    print("=" * 60)


if __name__ == "__main__":
    load_cases_to_db()
