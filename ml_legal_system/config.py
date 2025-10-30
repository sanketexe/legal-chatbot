"""
Configuration for ML Legal System
Manages settings for RAG, embeddings, and LLM
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Base configuration"""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///legalchat.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT settings
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    
    # LLM Settings
    USE_OPENAI = os.getenv('USE_OPENAI', 'false').lower() == 'true'
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    
    # Vector Database Settings
    USE_CLOUD_VECTOR_DB = os.getenv('USE_CLOUD_VECTOR_DB', 'false').lower() == 'true'
    PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
    PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENT', 'us-east-1-aws')
    
    # ChromaDB Settings (local)
    CHROMADB_PATH = './data/chromadb'
    
    # Embedding Settings
    USE_OPENAI_EMBEDDINGS = os.getenv('USE_OPENAI_EMBEDDINGS', 'false').lower() == 'true'
    EMBEDDING_MODEL = 'all-MiniLM-L6-v2'  # sentence-transformers model
    EMBEDDING_DIMENSION = 384  # for all-MiniLM-L6-v2
    # EMBEDDING_DIMENSION = 1536  # for OpenAI ada-002
    
    # RAG Settings
    TOP_K_RETRIEVAL = int(os.getenv('TOP_K_RETRIEVAL', '5'))
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', '0.7'))
    
    # Case Scraper Settings
    SCRAPER_DELAY = float(os.getenv('SCRAPER_DELAY', '2.0'))
    MAX_CASES_PER_QUERY = int(os.getenv('MAX_CASES_PER_QUERY', '200'))
    INDIAN_KANOON_BASE_URL = 'https://indiankanoon.org'
    
    # Data Paths
    DATA_DIR = './data'
    LEGAL_CASES_DIR = os.path.join(DATA_DIR, 'legal_cases')
    PROCESSED_CASES_FILE = os.path.join(LEGAL_CASES_DIR, 'indian_legal_cases_complete.json')
    
    # Legal Query Categories - Expanded to 50 categories for 10,000 cases
    LEGAL_CATEGORIES = [
        # Contract & Commercial Law (4 categories)
        "contract breach",
        "specific performance of contract",
        "arbitration and conciliation",
        "negotiable instruments cheque bounce",
        
        # Property & Real Estate (6 categories)
        "property dispute partition",
        "real estate RERA",
        "land acquisition compensation",
        "title dispute property",
        "tenancy rent control",
        "adverse possession",
        
        # Criminal Law (8 categories)
        "criminal negligence IPC",
        "theft robbery dacoity",
        "murder homicide culpable",
        "rape sexual assault POCSO",
        "fraud cheating 420",
        "dowry death 498A",
        "cybercrime IT Act",
        "NDPS drugs narcotics",
        
        # Family & Personal Law (5 categories)
        "divorce grounds Hindu Muslim",
        "child custody guardianship",
        "maintenance alimony",
        "adoption guardian wards",
        "domestic violence protection",
        
        # Consumer & Service (4 categories)
        "consumer protection deficiency",
        "medical negligence compensation",
        "insurance claim dispute",
        "banking services deficiency",
        
        # Employment & Labour (5 categories)
        "labour dispute industrial",
        "wrongful termination dismissal",
        "service law government employee",
        "workmen compensation injury",
        "sexual harassment workplace vishakha",
        
        # Constitutional & Administrative (6 categories)
        "writ petition habeas corpus",
        "fundamental rights Article 21",
        "PIL public interest litigation",
        "administrative law natural justice",
        "election law corrupt practices",
        "RTI right to information",
        
        # Tax & Finance (4 categories)
        "income tax assessment",
        "GST goods services tax",
        "customs excise duty",
        "penalty tax evasion",
        
        # Intellectual Property (3 categories)
        "trademark infringement passing off",
        "copyright piracy",
        "patent invention",
        
        # Tort & Compensation (3 categories)
        "motor accident claim compensation",
        "defamation libel slander",
        "negligence vicarious liability",
        
        # Corporate & Securities (2 categories)
        "company law oppression mismanagement",
        "SEBI securities fraud"
    ]


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Use AWS RDS PostgreSQL in production
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env='development'):
    """Get configuration based on environment"""
    return config.get(env, config['default'])