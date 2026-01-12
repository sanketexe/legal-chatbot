"""
Lightweight Embedding System for Legal RAG
Uses TF-IDF + dimensionality reduction instead of heavy transformer models
Avoids TensorFlow/protobuf dependency conflicts
"""

import pickle
import hashlib
from pathlib import Path
from typing import List, Dict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
import json


class LightweightEmbeddings:
    """
    Lightweight embedding system using TF-IDF + SVD
    Fast, no heavy dependencies, good for legal text
    """
    
    def __init__(self, embedding_dim: int = 384, cache_dir: str = "./ml_models"):
        """
        Initialize lightweight embeddings
        
        Args:
            embedding_dim: Target embedding dimension (default 384 to match sentence-transformers)
            cache_dir: Directory to cache the trained models
        """
        self.embedding_dim = embedding_dim
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.vectorizer = None
        self.svd = None
        self.is_fitted = False
        
        # Load cached models if available
        self._load_models()
    
    def _load_models(self):
        """Load pre-trained vectorizer and SVD from cache"""
        vectorizer_path = self.cache_dir / "tfidf_embedder.pkl"
        svd_path = self.cache_dir / "svd_embedder.pkl"
        
        try:
            if vectorizer_path.exists() and svd_path.exists():
                with open(vectorizer_path, 'rb') as f:
                    self.vectorizer = pickle.load(f)
                with open(svd_path, 'rb') as f:
                    self.svd = pickle.load(f)
                self.is_fitted = True
                print("✅ Loaded cached embedding models")
        except Exception as e:
            print(f"⚠️  Could not load cached models: {e}")
            self.is_fitted = False
    
    def _save_models(self):
        """Save trained models to cache"""
        try:
            vectorizer_path = self.cache_dir / "tfidf_embedder.pkl"
            svd_path = self.cache_dir / "svd_embedder.pkl"
            
            with open(vectorizer_path, 'wb') as f:
                pickle.dump(self.vectorizer, f)
            with open(svd_path, 'wb') as f:
                pickle.dump(self.svd, f)
            
            print("✅ Saved embedding models to cache")
        except Exception as e:
            print(f"⚠️  Could not save models: {e}")
    
    def fit(self, texts: List[str]):
        """
        Train the embedding model on a corpus of texts
        
        Args:
            texts: List of text documents to train on
        """
        print(f"🔧 Training lightweight embeddings on {len(texts)} documents...")
        
        # Initialize TF-IDF vectorizer with legal-specific settings
        self.vectorizer = TfidfVectorizer(
            max_features=10000,  # Limit vocabulary size
            ngram_range=(1, 3),  # Unigrams, bigrams, trigrams
            min_df=2,            # Ignore very rare terms
            max_df=0.8,          # Ignore very common terms
            stop_words='english',
            lowercase=True,
            strip_accents='unicode'
        )
        
        # Fit vectorizer and transform texts
        tfidf_matrix = self.vectorizer.fit_transform(texts)
        print(f"📊 TF-IDF matrix shape: {tfidf_matrix.shape}")
        
        # Use SVD to reduce dimensionality
        n_components = min(self.embedding_dim, tfidf_matrix.shape[0], tfidf_matrix.shape[1])
        self.svd = TruncatedSVD(n_components=n_components, random_state=42)
        self.svd.fit(tfidf_matrix)
        
        print(f"✅ Embedding model trained (dimension: {n_components})")
        
        self.is_fitted = True
        self._save_models()
    
    def encode(self, texts: List[str], show_progress: bool = False) -> np.ndarray:
        """
        Create embeddings for texts
        
        Args:
            texts: List of texts to embed
            show_progress: Whether to show progress (for compatibility)
            
        Returns:
            Array of embeddings with shape (len(texts), embedding_dim)
        """
        if not self.is_fitted:
            # If not fitted, use fallback method
            print("⚠️  Model not fitted, using fallback embeddings")
            return self._fallback_embeddings(texts)
        
        try:
            # Transform texts to TF-IDF
            tfidf_matrix = self.vectorizer.transform(texts)
            
            # Reduce dimensionality with SVD
            embeddings = self.svd.transform(tfidf_matrix)
            
            # Normalize to unit vectors
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1  # Avoid division by zero
            embeddings = embeddings / norms
            
            return embeddings
            
        except Exception as e:
            print(f"❌ Encoding error: {e}")
            return self._fallback_embeddings(texts)
    
    def _fallback_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Fallback embedding method using deterministic hashing
        Used when model is not fitted or encoding fails
        """
        print("💡 Using deterministic hash-based embeddings")
        
        def hash_embedding(text: str, dim: int) -> np.ndarray:
            # Create stable embedding from text hash
            h = hashlib.sha256(text.encode('utf-8')).hexdigest()
            
            # Create multiple hash values for higher dimensions
            embeddings = []
            for i in range(0, dim, 8):
                # Use different parts of hash for different dimensions
                segment = h[i*2:(i+2)*2] if (i+2)*2 <= len(h) else h[-4:]
                val = int(segment, 16) / 65535.0  # Normalize to [0, 1]
                embeddings.append(val * 2 - 1)  # Scale to [-1, 1]
            
            vec = np.array(embeddings[:dim])
            
            # Normalize to unit vector
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            
            return vec
        
        embeddings = np.array([hash_embedding(text, self.embedding_dim) for text in texts])
        return embeddings
    
    def save_corpus_for_training(self, output_path: str):
        """
        Save training corpus metadata
        
        Args:
            output_path: Path to save corpus info
        """
        info = {
            'embedding_dim': self.embedding_dim,
            'is_fitted': self.is_fitted,
            'vocab_size': len(self.vectorizer.vocabulary_) if self.vectorizer else 0,
            'explained_variance': float(np.sum(self.svd.explained_variance_ratio_)) if self.svd else 0
        }
        
        with open(output_path, 'w') as f:
            json.dump(info, f, indent=2)
        
        print(f"📄 Saved corpus info to {output_path}")


class HybridEmbeddings:
    """
    Hybrid approach: Try sentence-transformers, fallback to lightweight
    """
    
    def __init__(self, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim
        self.use_transformers = False
        self.transformer_model = None
        self.lightweight_model = LightweightEmbeddings(embedding_dim)
        
        self._try_load_transformers()
    
    def _try_load_transformers(self):
        """Try to load sentence-transformers, fallback to lightweight"""
        try:
            # Try importing without triggering tensorflow
            import os
            os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TF logs
            
            from sentence_transformers import SentenceTransformer
            
            # Use a model that doesn't require tensorflow
            self.transformer_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
            self.use_transformers = True
            print("✅ Using sentence-transformers embeddings")
            
        except Exception as e:
            print(f"⚠️  Sentence-transformers unavailable: {str(e)[:100]}")
            print("💡 Using lightweight TF-IDF embeddings")
            self.use_transformers = False
    
    def fit(self, texts: List[str]):
        """Fit the lightweight model (transformers don't need fitting)"""
        if not self.use_transformers:
            self.lightweight_model.fit(texts)
    
    def encode(self, texts: List[str], show_progress: bool = False) -> np.ndarray:
        """Create embeddings using best available method"""
        if self.use_transformers and self.transformer_model is not None:
            try:
                embeddings = self.transformer_model.encode(
                    texts, 
                    show_progress_bar=show_progress,
                    convert_to_numpy=True
                )
                return embeddings
            except Exception as e:
                print(f"❌ Transformer encoding failed: {e}")
                print("💡 Falling back to lightweight embeddings")
                self.use_transformers = False
        
        return self.lightweight_model.encode(texts, show_progress)


# Global singleton instance
_embedding_model = None

def get_embedding_model(embedding_dim: int = 384) -> HybridEmbeddings:
    """Get or create global embedding model instance"""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = HybridEmbeddings(embedding_dim)
    return _embedding_model
