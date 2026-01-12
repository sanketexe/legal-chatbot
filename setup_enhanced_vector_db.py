"""
Enhanced Vector Database Setup
Creates multiple domain-specific collections for better retrieval
Uses the new lightweight embedding system
"""

import json
import os
from pathlib import Path
from typing import List, Dict
from ml_legal_system.vector_db import LegalVectorDatabase
from ml_legal_system.lightweight_embeddings import get_embedding_model


# Define legal domain collections
LEGAL_DOMAINS = {
    'tech_employment': {
        'name': 'tech_employment_law',
        'description': 'Tech employment law cases for engineers and IT professionals',
        'files': [
            'cases_tech_employment_law.json',
            'cases_tech_employment_law_part2.json'
        ],
        'categories': ['Employment Law - Tech Sector']
    },
    'tech_corporate': {
        'name': 'tech_corporate_law',
        'description': 'Tech corporate law cases for startups and companies',
        'files': ['cases_tech_corporate_law.json'],
        'categories': ['Corporate Law - Tech Sector']
    },
    'general_employment': {
        'name': 'general_employment_law',
        'description': 'General employment and labor law cases',
        'files': ['cases_labor_law.json'],
        'categories': ['Labor Law', 'Employment Law']
    },
    'corporate': {
        'name': 'corporate_law',
        'description': 'General corporate law cases',
        'files': ['cases_corporate_law.json'],
        'categories': ['Corporate Law', 'Business Law']
    },
    'constitutional': {
        'name': 'constitutional_law',
        'description': 'Constitutional law and fundamental rights',
        'files': ['cases_constitutional_law.json'],
        'categories': ['Constitutional Law']
    },
    'criminal': {
        'name': 'criminal_law',
        'description': 'Criminal law cases',
        'files': ['cases_criminal_law.json'],
        'categories': ['Criminal Law']
    },
    'family': {
        'name': 'family_law',
        'description': 'Family law and matrimonial disputes',
        'files': ['cases_family_law.json'],
        'categories': ['Family Law']
    },
    'property': {
        'name': 'property_law',
        'description': 'Property and real estate law',
        'files': ['cases_property_law.json'],
        'categories': ['Property Law']
    },
    'all_cases': {
        'name': 'indian_legal_cases',
        'description': 'All Indian legal cases - general collection',
        'files': ['enhanced_legal_cases.json', 'high_quality_cases.json'],
        'categories': ['All']
    }
}


def load_cases_from_files(files: List[str], base_dir: str = './data/enhanced_cases') -> List[Dict]:
    """Load cases from specified files"""
    all_cases = []
    
    for filename in files:
        filepath = os.path.join(base_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"  ⚠️  File not found: {filename}")
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                cases = data
            elif isinstance(data, dict) and 'cases' in data:
                cases = data['cases']
            else:
                continue
            
            all_cases.extend(cases)
            print(f"  ✓ Loaded {len(cases)} cases from {filename}")
            
        except Exception as e:
            print(f"  ❌ Error loading {filename}: {e}")
    
    return all_cases


def prepare_case_document(case: Dict) -> Dict:
    """Convert case to document format"""
    # Extract text fields
    text_parts = []
    
    fields = [
        'case_name', 'title', 'facts', 'scenario', 'summary',
        'judgment', 'legal_issues', 'applicable_laws',
        'key_principles', 'practical_advice'
    ]
    
    for field in fields:
        if field in case:
            value = case[field]
            if isinstance(value, str):
                text_parts.append(f"{field.upper()}: {value}")
            elif isinstance(value, list):
                text_parts.append(f"{field.upper()}: {' | '.join([str(v) for v in value])}")
    
    # Create metadata
    metadata = {
        'id': case.get('id', case.get('case_id', 'unknown')),
        'case_name': case.get('case_name', case.get('title', 'Unknown Case')),
        'category': case.get('category', 'General'),
        'subcategory': case.get('subcategory', ''),
        'importance': case.get('importance_score', case.get('importance', 50))
    }
    
    return {
        'text': '\n\n'.join(text_parts),
        'metadata': metadata
    }


def create_collection(vector_db: LegalVectorDatabase, domain_info: Dict, cases: List[Dict]):
    """Create and populate a domain-specific collection"""
    collection_name = domain_info['name']
    description = domain_info['description']
    
    print(f"\n📦 Creating collection: {collection_name}")
    print(f"   Description: {description}")
    print(f"   Cases to add: {len(cases)}")
    
    try:
        # Create or get collection
        collection = vector_db.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": description}
        )
        
        # Prepare documents
        documents = [prepare_case_document(case) for case in cases]
        
        # Add in batches
        batch_size = 50
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            
            texts = [doc['text'] for doc in batch]
            metadatas = [doc['metadata'] for doc in batch]
            ids = [doc['metadata']['id'] for doc in batch]
            
            # Use the new lightweight embeddings
            embedder = get_embedding_model()
            embeddings = embedder.encode(texts)
            
            collection.add(
                documents=texts,
                embeddings=embeddings.tolist(),
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"  ✅ Added batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
        
        print(f"✅ Collection '{collection_name}' created with {len(documents)} cases")
        return True
        
    except Exception as e:
        print(f"❌ Error creating collection: {e}")
        return False


def setup_enhanced_vector_database():
    """Main function to set up all domain-specific collections"""
    print("=" * 80)
    print("ENHANCED VECTOR DATABASE SETUP")
    print("Creating domain-specific collections with lightweight embeddings")
    print("=" * 80)
    
    # Initialize vector database
    print("\n🔧 Initializing vector database...")
    vector_db = LegalVectorDatabase(use_cloud=False)
    
    # Initialize embedding model
    print("\n🔧 Initializing embedding model...")
    embedder = get_embedding_model()
    
    # Process each domain
    success_count = 0
    total_cases = 0
    
    for domain_key, domain_info in LEGAL_DOMAINS.items():
        print(f"\n{'─' * 80}")
        print(f"Processing domain: {domain_key.upper()}")
        print(f"{'─' * 80}")
        
        # Load cases for this domain
        cases = load_cases_from_files(domain_info['files'])
        
        if not cases:
            print(f"  ⚠️  No cases found for {domain_key}, skipping...")
            continue
        
        # Create collection
        if create_collection(vector_db, domain_info, cases):
            success_count += 1
            total_cases += len(cases)
    
    # Summary
    print("\n" + "=" * 80)
    print("SETUP COMPLETE")
    print("=" * 80)
    print(f"✅ Successfully created {success_count}/{len(LEGAL_DOMAINS)} collections")
    print(f"📊 Total cases indexed: {total_cases}")
    print(f"🚀 Collections available:")
    for domain_info in LEGAL_DOMAINS.values():
        print(f"   • {domain_info['name']}: {domain_info['description']}")
    print("=" * 80)


if __name__ == "__main__":
    setup_enhanced_vector_database()
