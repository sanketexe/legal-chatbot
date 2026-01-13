"""
Training Script for Tech Employment & Corporate Law Cases
Integrates specialized cases for Indian engineers and tech employees
"""

import json
import os
from pathlib import Path
from ml_legal_system.vector_db import LegalVectorDatabase
from ml_legal_system.legal_rag import LegalRAG


def load_tech_cases(data_dir='./data/enhanced_cases'):
    """Load all tech-specific legal cases"""
    tech_case_files = [
        'cases_tech_employment_law.json',
        'cases_tech_employment_law_part2.json',
        'cases_tech_corporate_law.json'
    ]
    
    all_cases = []
    for filename in tech_case_files:
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                cases = json.load(f)
                all_cases.extend(cases)
                print(f"✅ Loaded {len(cases)} cases from {filename}")
        else:
            print(f"⚠️  File not found: {filepath}")
    
    return all_cases


def prepare_case_documents(cases):
    """Convert cases to document format for vector database"""
    documents = []
    
    for case in cases:
        # Create comprehensive document text
        doc_text = f"""
Case: {case['case_name']}
Category: {case['category']} - {case['subcategory']}
ID: {case['id']}

SCENARIO:
{case['scenario']}

FACTS:
{case['facts']}

LEGAL ISSUES:
{' | '.join(case['legal_issues'])}

APPLICABLE LAWS:
{' | '.join(case['applicable_laws'])}

JUDGMENT:
{case['judgment']}

KEY LEGAL PRINCIPLES:
{' | '.join(case['key_principles'])}

PRECEDENTS CITED:
{' | '.join(case.get('precedents', []))}

PRACTICAL ADVICE FOR EMPLOYEES/ENGINEERS:
{' | '.join(case['practical_advice'])}
"""
        
        metadata = {
            'id': case['id'],
            'case_name': case['case_name'],
            'category': case['category'],
            'subcategory': case['subcategory'],
            'importance_score': case.get('importance_score', 80),
            'legal_domain': 'Tech Employment & Corporate Law'
        }
        
        documents.append({
            'text': doc_text.strip(),
            'metadata': metadata
        })
    
    return documents


def train_vector_database(documents, collection_name='tech_legal_cases'):
    """Add documents to vector database"""
    print(f"\n🚀 Training vector database with {len(documents)} tech law cases...")
    
    # Initialize vector database
    vector_db = LegalVectorDatabase(use_cloud=False)
    
    # Create or get collection
    try:
        collection = vector_db.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Tech employment and corporate law cases for Indian engineers"}
        )
        
        # Add documents in batches
        batch_size = 10
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            
            texts = [doc['text'] for doc in batch]
            metadatas = [doc['metadata'] for doc in batch]
            ids = [doc['metadata']['id'] for doc in batch]
            
            collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"✅ Added batch {i//batch_size + 1} ({len(batch)} cases)")
        
        print(f"\n✅ Successfully trained {len(documents)} cases in collection '{collection_name}'")
        print(f"📊 Total cases in database: {collection.count()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error training database: {e}")
        return False


def test_retrieval(vector_db, test_queries):
    """Test the trained model with sample queries"""
    print("\n🔍 Testing retrieval with sample queries...\n")
    
    rag = LegalRAG(use_openai=False, vector_db=vector_db)
    
    for query in test_queries:
        print(f"Query: {query}")
        # Ensure we query the collection that was used for training
        try:
            # If a collection named 'tech_legal_cases' exists, switch to it for querying
            vector_db.collection = vector_db.client.get_collection(name='tech_legal_cases')
        except Exception:
            # Fallback: continue using the default collection on the vector_db instance
            pass

        # Use the provided search API
        results = vector_db.search_similar_cases(query, top_k=3)
        
        if results:
            print(f"  Found {len(results)} relevant cases:")
            for i, result in enumerate(results[:2], 1):
                print(f"  {i}. {result['metadata'].get('case_name', 'Unknown')} "
                      f"(Relevance: {result.get('distance', 0):.2f})")
        else:
            print("  ⚠️  No results found")
        print()


def generate_training_report(cases):
    """Generate a comprehensive training report"""
    report = {
        'total_cases': len(cases),
        'categories': {},
        'subcategories': {},
        'coverage': []
    }
    
    for case in cases:
        category = case['category']
        subcategory = case['subcategory']
        
        report['categories'][category] = report['categories'].get(category, 0) + 1
        report['subcategories'][subcategory] = report['subcategories'].get(subcategory, 0) + 1
    
    # Key areas covered
    report['coverage'] = [
        "Non-compete and non-solicitation agreements",
        "Intellectual property rights for engineers",
        "ESOP and equity compensation disputes",
        "Wrongful termination and PIPs",
        "Workplace harassment (POSH Act)",
        "Remote work and WFH rights",
        "Notice period and resignation",
        "Mental health and workplace stress",
        "Variable pay and bonus disputes",
        "Moonlighting and conflict of interest",
        "Startup acquisitions and employee rights",
        "Open source licensing compliance",
        "Data security and confidentiality",
        "Unpaid overtime and wage disputes",
        "Founder disputes and vesting"
    ]
    
    return report


def main():
    """Main training pipeline"""
    print("=" * 80)
    print("TECH EMPLOYMENT & CORPORATE LAW - TRAINING PIPELINE")
    print("Specialized for Indian Engineers & Tech Employees")
    print("=" * 80)
    
    # Step 1: Load cases
    print("\n📂 Step 1: Loading tech law cases...")
    cases = load_tech_cases()
    
    if not cases:
        print("❌ No cases found. Exiting.")
        return
    
    # Step 2: Prepare documents
    print("\n📝 Step 2: Preparing case documents...")
    documents = prepare_case_documents(cases)
    print(f"✅ Prepared {len(documents)} documents for training")
    
    # Step 3: Train vector database
    print("\n🎓 Step 3: Training vector database...")
    success = train_vector_database(documents)
    
    if not success:
        print("❌ Training failed. Exiting.")
        return
    
    # Step 4: Test retrieval
    test_queries = [
        "Can my company enforce non-compete agreement after I resign?",
        "Who owns the code I write at work?",
        "My company put me on PIP and wants to fire me, what are my rights?",
        "Is moonlighting illegal for software engineers in India?",
        "Can I refuse to return to office after working from home?",
        "My startup is being acquired, what happens to my ESOP?",
        "How to file sexual harassment complaint at IT company?",
        "Can employer refuse my notice period buyout?"
    ]
    
    vector_db = LegalVectorDatabase(use_cloud=False)
    test_retrieval(vector_db, test_queries)
    
    # Step 5: Generate report
    print("\n📊 Step 5: Generating training report...")
    report = generate_training_report(cases)
    
    print("\n" + "=" * 80)
    print("TRAINING SUMMARY")
    print("=" * 80)
    print(f"\n✅ Total Cases Trained: {report['total_cases']}")
    print(f"\n📁 Categories:")
    for category, count in report['categories'].items():
        print(f"  • {category}: {count} cases")
    
    print(f"\n🏷️  Subcategories:")
    for subcategory, count in report['subcategories'].items():
        print(f"  • {subcategory}: {count} cases")
    
    print(f"\n🎯 Key Areas Covered:")
    for area in report['coverage']:
        print(f"  ✓ {area}")
    
    print("\n" + "=" * 80)
    print("✅ TRAINING COMPLETED SUCCESSFULLY!")
    print("💡 The model is now ready to answer tech employment & corporate law questions")
    print("=" * 80)
    
    # Save report
    report_path = './data/enhanced_cases/tech_law_training_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n📄 Training report saved to: {report_path}")


if __name__ == "__main__":
    main()
