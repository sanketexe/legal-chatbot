"""
Pinecone-based vector database for production deployment
Replaces local ChromaDB with cloud-hosted Pinecone
"""

import os
from typing import List, Dict, Any, Optional
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

class PineconeVectorDB:
    """
    Vector database using Pinecone cloud service
    Compatible with the existing VectorDatabase interface
    """
    
    def __init__(self):
        """Initialize Pinecone connection"""
        self.model = None
        self.pc = None
        self.index = None
        self._initialize_pinecone()
    
    def _initialize_pinecone(self):
        """Connect to Pinecone index"""
        try:
            # Get credentials from environment
            api_key = os.getenv('PINECONE_API_KEY')
            index_name = os.getenv('PINECONE_INDEX_NAME', 'legal-cases')
            
            if not api_key:
                raise ValueError("PINECONE_API_KEY not found in environment variables")
            
            # Initialize Pinecone
            self.pc = Pinecone(api_key=api_key)
            
            # Connect to index
            self.index = self.pc.Index(index_name)
            
            # Load embedding model
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            
            print(f"✅ Pinecone initialized (index: {index_name})")
            
        except Exception as e:
            print(f"❌ Error initializing Pinecone: {e}")
            raise
    
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings for texts using sentence-transformers
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            print(f"❌ Error creating embeddings: {e}")
            return []
    
    def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> bool:
        """
        Add documents to Pinecone
        
        Args:
            texts: List of document texts
            metadatas: Optional list of metadata dicts
            ids: Optional list of document IDs
            
        Returns:
            True if successful
        """
        try:
            # Generate IDs if not provided
            if ids is None:
                ids = [f"doc_{i}" for i in range(len(texts))]
            
            # Generate embeddings
            embeddings = self.create_embeddings(texts)
            
            if not embeddings:
                return False
            
            # Prepare vectors for upsert
            vectors_to_upsert = []
            for i, doc_id in enumerate(ids):
                metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
                metadata['text'] = texts[i][:1000]  # Store text preview in metadata
                
                vectors_to_upsert.append({
                    'id': doc_id,
                    'values': embeddings[i],
                    'metadata': metadata
                })
            
            # Upsert to Pinecone in batches
            batch_size = 100
            for i in range(0, len(vectors_to_upsert), batch_size):
                batch = vectors_to_upsert[i:i + batch_size]
                self.index.upsert(vectors=batch)
            
            return True
            
        except Exception as e:
            print(f"❌ Error adding documents: {e}")
            return False
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        
        Args:
            query: Search query text
            top_k: Number of results to return
            filter_dict: Optional metadata filter
            
        Returns:
            List of matching documents with scores
        """
        try:
            # Generate query embedding
            query_embedding = self.model.encode([query])[0].tolist()
            
            # Search Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict if filter_dict else None
            )
            
            # Format results to match ChromaDB interface
            formatted_results = []
            for match in results['matches']:
                result = {
                    'id': match['id'],
                    'score': float(match['score']),
                    'metadata': match.get('metadata', {}),
                    'text': match.get('metadata', {}).get('text', '')
                }
                formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ Error searching: {e}")
            return []
    
    def get_collection_count(self) -> int:
        """
        Get number of vectors in the index
        
        Returns:
            Count of vectors
        """
        try:
            stats = self.index.describe_index_stats()
            return stats.get('total_vector_count', 0)
        except Exception as e:
            print(f"❌ Error getting count: {e}")
            return 0
    
    def delete_collection(self):
        """Delete all vectors from index"""
        try:
            # Pinecone doesn't have a direct "delete all" in free tier
            # This would need to delete by ID or recreate index
            print("⚠️ Delete collection not implemented for Pinecone")
            pass
        except Exception as e:
            print(f"❌ Error deleting collection: {e}")

def get_vector_db() -> PineconeVectorDB:
    """
    Factory function to get Pinecone vector database instance
    
    Returns:
        PineconeVectorDB instance
    """
    return PineconeVectorDB()
