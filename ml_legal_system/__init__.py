"""
ML Legal System - RAG-powered Legal Assistant
Provides case-based legal advice using Indian court precedents
"""

__version__ = "1.0.0"
__author__ = "LegalCounsel AI Team"

# Import main components
try:
    from .legal_rag import LegalRAG
    from .vector_db import LegalVectorDatabase
    from .case_scraper import IndianLegalCaseScraper
    from .config import get_config, Config
    
    __all__ = [
        'LegalRAG',
        'LegalVectorDatabase', 
        'IndianLegalCaseScraper',
        'get_config',
        'Config'
    ]
    
except ImportError:
    # Dependencies not installed yet
    pass
