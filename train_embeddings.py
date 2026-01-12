"""
Train Lightweight Embeddings on Legal Corpus
Prepares the TF-IDF + SVD embedding model for production use
"""

import json
import os
from pathlib import Path
from ml_legal_system.lightweight_embeddings import LightweightEmbeddings


def load_all_legal_cases():
    """Load all legal cases from enhanced_cases directory"""
    cases_dir = Path("./data/enhanced_cases")
    all_texts = []
    file_count = 0
    
    print("📚 Loading legal cases for training...")
    
    # Load all JSON files in enhanced_cases
    for json_file in cases_dir.glob("*.json"):
        if json_file.stem == "tech_law_training_report":
            continue  # Skip reports
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Handle different JSON structures
            if isinstance(data, list):
                cases = data
            elif isinstance(data, dict) and 'cases' in data:
                cases = data['cases']
            else:
                continue
            
            # Extract text from each case
            for case in cases:
                case_text = extract_case_text(case)
                if case_text:
                    all_texts.append(case_text)
            
            file_count += 1
            print(f"  ✓ Loaded {len(cases)} cases from {json_file.name}")
            
        except Exception as e:
            print(f"  ⚠️  Error loading {json_file.name}: {e}")
    
    print(f"\n✅ Total: {len(all_texts)} cases from {file_count} files")
    return all_texts


def extract_case_text(case: dict) -> str:
    """Extract searchable text from a case dictionary"""
    text_parts = []
    
    # Add different fields based on case structure
    fields_to_extract = [
        'case_name', 'title', 'summary', 'facts', 'scenario',
        'judgment', 'legal_issues', 'applicable_laws', 
        'key_principles', 'practical_advice', 'full_text',
        'search_query', 'category', 'subcategory'
    ]
    
    for field in fields_to_extract:
        if field in case:
            value = case[field]
            if isinstance(value, str):
                text_parts.append(value)
            elif isinstance(value, list):
                text_parts.extend([str(v) for v in value])
    
    return " ".join(text_parts)


def train_embeddings():
    """Main training function"""
    print("=" * 80)
    print("LIGHTWEIGHT EMBEDDINGS TRAINING")
    print("Training TF-IDF + SVD model on legal corpus")
    print("=" * 80)
    
    # Load all cases
    texts = load_all_legal_cases()
    
    if not texts:
        print("❌ No texts found to train on!")
        return False
    
    # Initialize and train embedding model
    print(f"\n🔧 Initializing lightweight embeddings...")
    embedder = LightweightEmbeddings(embedding_dim=384)
    
    print(f"\n🎓 Training on {len(texts)} documents...")
    embedder.fit(texts)
    
    # Save training info
    embedder.save_corpus_for_training("./ml_models/embedding_training_info.json")
    
    # Test the embeddings
    print("\n🧪 Testing embeddings...")
    test_queries = [
        "Can my employer enforce a non-compete clause?",
        "What are my rights regarding intellectual property?",
        "How to file a sexual harassment complaint?"
    ]
    
    test_embeddings = embedder.encode(test_queries)
    print(f"✅ Test embeddings shape: {test_embeddings.shape}")
    print(f"   Embedding dimension: {test_embeddings.shape[1]}")
    print(f"   Number of test queries: {test_embeddings.shape[0]}")
    
    # Verify embeddings are normalized
    norms = [sum(x**2)**0.5 for x in test_embeddings]
    print(f"   Vector norms: {[f'{n:.4f}' for n in norms]} (should be ~1.0)")
    
    print("\n" + "=" * 80)
    print("✅ TRAINING COMPLETED SUCCESSFULLY!")
    print("💾 Models saved to ./ml_models/")
    print("🚀 Embedding system ready for production use")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    success = train_embeddings()
    exit(0 if success else 1)
