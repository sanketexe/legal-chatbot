"""
Vector Database Manager for Legal Cases
Handles embeddings and similarity search for RAG system
"""

import os
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
import numpy as np

@dataclass
class LegalCase:
    """Data class for a legal case"""
    id: str
    title: str
    court: str
    date: str
    judges: str
    full_text: str
    summary: str
    legal_acts: List[str]
    citations: List[str]
    embedding: Optional[np.ndarray] = None


class LegalVectorDatabase:
    """
    Vector database for legal cases using embeddings
    Supports semantic search and case retrieval
    """
    
    def __init__(self, use_cloud: bool = False):
        """
        Initialize vector database
        
        Args:
            use_cloud: If True, use Pinecone. If False, use local ChromaDB
        """
        self.use_cloud = use_cloud
        self.cases = []
        self.embeddings_model = None
        
        if use_cloud:
            self._init_pinecone()
        else:
            self._init_chromadb()
    
    def _init_pinecone(self):
        """Initialize Pinecone cloud vector database"""
        try:
            import pinecone
            
            api_key = os.getenv('PINECONE_API_KEY')
            environment = os.getenv('PINECONE_ENVIRONMENT', 'us-east-1-aws')
            
            pinecone.init(api_key=api_key, environment=environment)
            
            # Create index if doesn't exist
            index_name = "indian-legal-cases"
            if index_name not in pinecone.list_indexes():
                pinecone.create_index(
                    name=index_name,
                    dimension=1536,  # OpenAI embedding dimension
                    metric='cosine'
                )
            
            self.index = pinecone.Index(index_name)
            print("✅ Pinecone vector database initialized")
            
        except Exception as e:
            print(f"❌ Error initializing Pinecone: {e}")
            print("💡 Falling back to local ChromaDB")
            self._init_chromadb()
    
    def _init_chromadb(self):
        """Initialize local ChromaDB"""
        try:
            import chromadb
            
            # Create persistent client (new API)
            self.client = chromadb.PersistentClient(
                path="./data/chromadb"
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name="indian_legal_cases",
                metadata={"description": "Indian Supreme Court and High Court cases"}
            )
            
            print("✅ ChromaDB local vector database initialized")
            
        except Exception as e:
            print(f"❌ Error initializing ChromaDB: {e}")
            raise
    
    def create_embeddings(self, texts: List[str], use_openai: bool = True) -> List[List[float]]:
        """
        Create embeddings for text using OpenAI or free alternatives
        
        Args:
            texts: List of texts to embed
            use_openai: If True, use OpenAI. Otherwise use sentence-transformers
            
        Returns:
            List of embedding vectors
        """
        if use_openai:
            return self._create_openai_embeddings(texts)
        else:
            return self._create_local_embeddings(texts)
    
    def _create_openai_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings using OpenAI API"""
        try:
            import openai
            openai.api_key = os.getenv('OPENAI_API_KEY')
            
            embeddings = []
            batch_size = 100
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                
                response = openai.Embedding.create(
                    model="text-embedding-ada-002",
                    input=batch
                )
                
                batch_embeddings = [item['embedding'] for item in response['data']]
                embeddings.extend(batch_embeddings)
                
                print(f"📊 Created embeddings: {len(embeddings)}/{len(texts)}")
            
            return embeddings
            
        except Exception as e:
            print(f"❌ OpenAI embedding error: {e}")
            print("💡 Falling back to local embeddings")
            return self._create_local_embeddings(texts)
    
    def _create_local_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings using hybrid approach (sentence-transformers or lightweight TF-IDF)"""
        try:
            # Use the new lightweight embedding system
            from .lightweight_embeddings import get_embedding_model
            
            embedding_model = get_embedding_model()
            
            print("🔄 Creating embeddings...")
            embeddings = embedding_model.encode(texts, show_progress=True)
            
            return embeddings.tolist()
            
        except Exception as e:
            # Ultimate fallback: deterministic hash-based embeddings
            print(f"❌ Embedding error: {e}")
            print("💡 Using fallback hash-based embeddings")

            import hashlib
            import numpy as _np

            def _deterministic_embedding(text: str, dim: int = 384):
                # Create a stable seed from the text
                h = hashlib.sha256(text.encode('utf-8')).hexdigest()
                seed = int(h[:16], 16) % (2**32)
                rng = _np.random.RandomState(seed)
                vec = rng.normal(size=(dim,)).astype(_np.float32)
                # Normalize to unit vector
                norm = _np.linalg.norm(vec)
                if norm > 0:
                    vec = vec / norm
                return vec.tolist()

            dim = 384
            embeddings = [_deterministic_embedding(t, dim=dim) for t in texts]
            return embeddings
    
    def add_cases(self, cases: List[Dict], batch_size: int = 100):
        """
        Add cases to vector database
        
        Args:
            cases: List of case dictionaries from scraper
            batch_size: Number of cases to process at once
        """
        print(f"📚 Adding {len(cases)} cases to vector database...")
        
        for i in range(0, len(cases), batch_size):
            batch = cases[i:i+batch_size]
            
            # Prepare texts for embedding
            texts = []
            metadatas = []
            ids = []
            
            for j, case in enumerate(batch):
                # Create searchable text from full_text and search_query
                full_text = case.get('full_text', '')
                search_query = case.get('search_query', '')
                case_text = f"{search_query} {full_text}"
                texts.append(case_text)
                
                # Extract title from full_text (first line or first 100 chars)
                title = ''
                if full_text:
                    lines = full_text.split('\n')
                    # Find the first meaningful line (not just whitespace or common headers)
                    for line in lines:
                        line = line.strip()
                        if line and len(line) > 10 and 'Virtual Legal Assistant' not in line:
                            title = line[:100]
                            break
                    if not title:
                        title = full_text[:100].strip()
                
                # Store metadata with available fields
                metadatas.append({
                    'title': title,
                    'court': '',  # Not available in scraped data
                    'date': '',   # Not available in scraped data
                    'judges': '', # Not available in scraped data
                    'url': case.get('url', ''),
                    'search_query': search_query,
                    'scraped_at': case.get('scraped_at', ''),
                    'legal_acts': json.dumps(case.get('legal_acts', [])),
                    'citations': json.dumps(case.get('citations', []))
                })
                
                # Generate ID
                ids.append(f"case_{i+j}")
            
            # Create embeddings
            embeddings = self.create_embeddings(texts, use_openai=False)
            
            # Add to database
            if self.use_cloud:
                # Pinecone format
                vectors = [(ids[k], embeddings[k], metadatas[k]) 
                          for k in range(len(ids))]
                self.index.upsert(vectors=vectors)
            else:
                # ChromaDB format
                self.collection.add(
                    documents=texts,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    ids=ids
                )
            
            print(f"✅ Added batch {i//batch_size + 1}/{(len(cases)-1)//batch_size + 1}")
        
        print(f"🎉 Successfully added {len(cases)} cases to vector database!")
    
    def search_similar_cases(self, query: str, top_k: int = 10, 
                           filters: Dict = None) -> List[Dict]:
        """
        Search for similar cases using semantic search with advanced filters
        
        Args:
            query: User's legal query
            top_k: Number of results to return
            filters: Optional filters dictionary:
                - courts: List of court names
                - from_year: Start year (string)
                - to_year: End year (string)
                - jurisdiction: Jurisdiction/state
                - Other metadata filters
            
        Returns:
            List of relevant cases with similarity scores
        """
        # Create query embedding
        query_embedding = self.create_embeddings([query], use_openai=False)[0]
        
        if self.use_cloud:
            # Pinecone search with filters
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=self._convert_to_pinecone_filter(filters) if filters else None
            )
            
            return [{
                'id': match.id,
                'score': match.score,
                'metadata': match.metadata
            } for match in results.matches]
            
        else:
            # ChromaDB search with filters
            chroma_filter = self._convert_to_chroma_filter(filters) if filters else None
            
            try:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    where=chroma_filter
                )
                
                similar_cases = []
                for i in range(len(results['ids'][0])):
                    similar_cases.append({
                        'id': results['ids'][0][i],
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i]
                    })
                
                return similar_cases
                
            except Exception as e:
                print(f"⚠️  ChromaDB filter error: {e}")
                # Fallback to unfiltered search
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k
                )
                
                similar_cases = []
                for i in range(len(results['ids'][0])):
                    similar_cases.append({
                        'id': results['ids'][0][i],
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i]
                    })
                
                return similar_cases
    
    def _convert_to_chroma_filter(self, filters: Dict) -> Dict:
        """
        Convert filter dictionary to ChromaDB where clause format
        
        Args:
            filters: Filter dictionary with various criteria
            
        Returns:
            ChromaDB compatible where clause
        """
        if not filters:
            return None
        
        where_clauses = []
        
        # Court filter (list of courts)
        if 'courts' in filters and filters['courts']:
            if len(filters['courts']) == 1:
                where_clauses.append({
                    "court": {"$eq": filters['courts'][0]}
                })
            else:
                where_clauses.append({
                    "court": {"$in": filters['courts']}
                })
        
        # Date range filter (year-based)
        if 'from_year' in filters:
            # Extract year from date field
            # Note: This requires dates to be in YYYY or YYYY-MM-DD format
            where_clauses.append({
                "date": {"$gte": filters['from_year']}
            })
        
        if 'to_year' in filters:
            where_clauses.append({
                "date": {"$lte": filters['to_year'] + "-12-31"}  # End of year
            })
        
        # Jurisdiction filter
        if 'jurisdiction' in filters and filters['jurisdiction']:
            where_clauses.append({
                "jurisdiction": {"$eq": filters['jurisdiction']}
            })
        
        # Combine filters with AND logic
        if not where_clauses:
            return None
        elif len(where_clauses) == 1:
            return where_clauses[0]
        else:
            return {"$and": where_clauses}
    
    def _convert_to_pinecone_filter(self, filters: Dict) -> Dict:
        """
        Convert filter dictionary to Pinecone filter format
        
        Args:
            filters: Filter dictionary
            
        Returns:
            Pinecone compatible filter
        """
        if not filters:
            return None
        
        pinecone_filter = {}
        
        # Court filter
        if 'courts' in filters and filters['courts']:
            if len(filters['courts']) == 1:
                pinecone_filter['court'] = {'$eq': filters['courts'][0]}
            else:
                pinecone_filter['court'] = {'$in': filters['courts']}
        
        # Date filters
        if 'from_year' in filters:
            pinecone_filter['year'] = {'$gte': int(filters['from_year'])}
        
        if 'to_year' in filters:
            if 'year' in pinecone_filter:
                pinecone_filter['year']['$lte'] = int(filters['to_year'])
            else:
                pinecone_filter['year'] = {'$lte': int(filters['to_year'])}
        
        # Jurisdiction
        if 'jurisdiction' in filters:
            pinecone_filter['jurisdiction'] = {'$eq': filters['jurisdiction']}
        
        return pinecone_filter if pinecone_filter else None
    
    def get_case_by_id(self, case_id: str) -> Optional[Dict]:
        """Retrieve a specific case by ID"""
        try:
            if self.use_cloud:
                result = self.index.fetch(ids=[case_id])
                return result.vectors[case_id] if case_id in result.vectors else None
            else:
                result = self.collection.get(ids=[case_id])
                if result['ids']:
                    return {
                        'id': result['ids'][0],
                        'document': result['documents'][0],
                        'metadata': result['metadatas'][0]
                    }
                return None
        except Exception as e:
            print(f"❌ Error fetching case: {e}")
            return None


def main():
    """
    Test the vector database
    """
    print("🧪 Testing Legal Vector Database")
    print("=" * 60)
    
    # Initialize database
    db = LegalVectorDatabase(use_cloud=False)
    
    # Load sample cases
    try:
        with open('data/legal_cases/indian_legal_cases_complete.json', 'r', encoding='utf-8') as f:
            cases = json.load(f)
        
        print(f"📚 Loaded {len(cases)} cases")
        
        # Add to vector database
        db.add_cases(cases[:100])  # Start with 100 cases for testing
        
        # Test search
        test_query = "What is the law regarding contract breach?"
        print(f"\n🔍 Testing search: '{test_query}'")
        
        results = db.search_similar_cases(test_query, top_k=5)
        
        print(f"\n📊 Found {len(results)} relevant cases:")
        for i, case in enumerate(results, 1):
            print(f"\n{i}. {case['metadata']['title']}")
            print(f"   Court: {case['metadata']['court']}")
            print(f"   Similarity: {1 - case.get('distance', 0):.2%}")
        
    except FileNotFoundError:
        print("⚠️  No case data found. Run case_scraper.py first!")


if __name__ == "__main__":
    main()