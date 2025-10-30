# Design Document

## Overview

This design outlines the approach for training the RAG model on scraped Indian legal case data and cleaning up unnecessary project files. The system will process over 940 legal cases, create embeddings, store them in ChromaDB, and optimize the retrieval pipeline for accurate legal question answering.

## Architecture

### Current System Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                     User Legal Query                         │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Legal RAG System                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  1. Query Processing                                 │   │
│  │  2. Vector Search (retrieve_relevant_cases)          │   │
│  │  3. Context Formatting (format_context)              │   │
│  │  4. LLM Generation (Gemini/GPT)                      │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                ┌───────────┴────────────┐
                │                        │
                ▼                        ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│   Vector Database        │  │     LLM (Gemini/GPT)     │
│   (ChromaDB)             │  │                          │
│                          │  │  - Google Gemini (FREE)  │
│  - Local Storage         │  │  - OpenAI GPT (Paid)     │
│  - Semantic Search       │  │                          │
│  - Top-K Retrieval       │  │  Generates answers with  │
└──────────────────────────┘  │  citations                │
                │              └──────────────────────────┘
                ▼
┌──────────────────────────────────────────────────────────────┐
│              Case Database (JSON)                            │
│  - 940+ Indian legal cases                                   │
│  - Supreme Court & High Courts                               │
│  - Scraped from Indian Kanoon                                │
│  - Full text + metadata                                      │
└──────────────────────────────────────────────────────────────┘
```

### Training Pipeline Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Training Pipeline                         │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  1. Data Loading & Consolidation                             │
│     - Load indian_legal_cases_complete.json                  │
│     - Validate case data structure                           │
│     - Clean and preprocess text                              │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Embedding Generation                                     │
│     - Use sentence-transformers model                        │
│     - Process case text in chunks                            │
│     - Generate vector embeddings                             │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Vector Database Storage                                  │
│     - Store embeddings in ChromaDB                           │
│     - Index with metadata (court, date, judges)              │
│     - Create searchable collections                          │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Validation & Testing                                     │
│     - Test retrieval performance                             │
│     - Validate search accuracy                               │
│     - Benchmark query response times                         │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Data Consolidation Module

**Purpose:** Load and preprocess all scraped legal case data

**Key Components:**
- `DataLoader`: Loads JSON files and consolidates partial files
- `DataValidator`: Validates case data structure and completeness
- `TextPreprocessor`: Cleans and normalizes legal text

**Interface:**
```python
class DataConsolidator:
    def load_all_cases(self, data_dir: str) -> List[Dict]
    def validate_cases(self, cases: List[Dict]) -> List[Dict]
    def preprocess_text(self, text: str) -> str
    def get_training_stats(self) -> Dict
```

### 2. Embedding Training Module

**Purpose:** Generate embeddings for all legal cases

**Key Components:**
- `EmbeddingGenerator`: Creates vector embeddings using sentence-transformers
- `ChunkProcessor`: Handles large case texts by chunking
- `BatchProcessor`: Processes cases in batches for efficiency

**Interface:**
```python
class EmbeddingTrainer:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2')
    def generate_embeddings(self, cases: List[Dict]) -> List[np.ndarray]
    def process_in_batches(self, cases: List[Dict], batch_size: int = 32)
    def save_embeddings(self, embeddings: List, metadata: List[Dict])
```

### 3. Vector Database Manager

**Purpose:** Manage ChromaDB operations and indexing

**Key Components:**
- `DatabaseInitializer`: Sets up ChromaDB collections
- `IndexManager`: Handles embedding storage and indexing
- `SearchOptimizer`: Optimizes search parameters

**Interface:**
```python
class VectorDatabaseManager:
    def initialize_database(self, collection_name: str = 'indian_legal_cases')
    def add_embeddings(self, embeddings: List, metadata: List[Dict])
    def optimize_search_params(self)
    def validate_indexing(self) -> Dict
```

### 4. File Cleanup Module

**Purpose:** Remove unnecessary deployment and infrastructure files

**Key Components:**
- `FileScanner`: Identifies files to remove
- `SafeRemover`: Safely removes files with validation
- `ProjectCleaner`: Orchestrates cleanup process

**Interface:**
```python
class ProjectCleaner:
    def scan_for_cleanup(self) -> List[str]
    def validate_removal_safety(self, files: List[str]) -> List[str]
    def remove_files(self, files: List[str])
    def generate_cleanup_report(self) -> Dict
```

## Data Models

### Case Data Model
```python
@dataclass
class LegalCase:
    title: str
    court: str
    date: str
    judges: str
    full_text: str
    url: str
    citations: List[str]
    legal_acts: List[str]
    search_query: str
    scraped_at: str
    
    def to_embedding_text(self) -> str:
        """Convert case to text suitable for embedding"""
        
    def get_metadata(self) -> Dict:
        """Get metadata for vector database storage"""
```

### Training Configuration Model
```python
@dataclass
class TrainingConfig:
    embedding_model: str = 'all-MiniLM-L6-v2'
    batch_size: int = 32
    chunk_size: int = 512
    overlap_size: int = 50
    collection_name: str = 'indian_legal_cases'
    similarity_threshold: float = 0.7
    top_k_default: int = 5
```

### Training Results Model
```python
@dataclass
class TrainingResults:
    total_cases_processed: int
    total_embeddings_created: int
    processing_time: float
    average_case_length: int
    database_size_mb: float
    validation_accuracy: float
    sample_queries_tested: int
```

## Error Handling

### Data Loading Errors
- **Missing Files**: Graceful handling of missing partial files
- **Corrupted Data**: Skip corrupted cases and log issues
- **Memory Issues**: Process data in batches to handle large datasets

### Embedding Generation Errors
- **Model Loading**: Fallback to alternative embedding models
- **Text Processing**: Handle special characters and encoding issues
- **Batch Processing**: Retry failed batches with smaller sizes

### Database Errors
- **Connection Issues**: Retry logic with exponential backoff
- **Storage Limits**: Monitor disk space and provide warnings
- **Index Corruption**: Rebuild index if corruption detected

### File Cleanup Errors
- **Permission Issues**: Skip files that cannot be removed
- **Dependency Validation**: Ensure no critical files are removed
- **Rollback Capability**: Maintain list of removed files for potential rollback

## Testing Strategy

### Unit Testing
- Test data loading and validation functions
- Test embedding generation with sample cases
- Test vector database operations
- Test file cleanup logic

### Integration Testing
- End-to-end training pipeline testing
- RAG system testing with trained model
- Performance testing with full dataset
- Search accuracy validation

### Performance Testing
- Measure embedding generation speed
- Test query response times
- Monitor memory usage during training
- Validate search accuracy metrics

### Validation Testing
```python
# Sample test queries for validation
test_queries = [
    "What is the penalty for breach of contract in India?",
    "Grounds for divorce under Indian law",
    "Property inheritance rights",
    "Motor accident liability",
    "Trademark infringement cases"
]
```

## Implementation Approach

### Phase 1: Data Consolidation
1. Load all partial case files and the complete dataset
2. Validate data structure and remove duplicates
3. Preprocess text for optimal embedding generation
4. Generate training statistics and data quality report

### Phase 2: Embedding Training
1. Initialize sentence-transformers model
2. Process cases in batches to generate embeddings
3. Handle large texts through chunking strategy
4. Monitor progress and handle errors gracefully

### Phase 3: Vector Database Setup
1. Initialize ChromaDB with optimized settings
2. Create collection for Indian legal cases
3. Store embeddings with rich metadata
4. Validate indexing and search functionality

### Phase 4: File Cleanup
1. Scan project for unnecessary files (AWS, Docker, etc.)
2. Validate removal safety to avoid breaking dependencies
3. Remove identified files and generate cleanup report
4. Update project documentation if needed

### Phase 5: Validation & Testing
1. Test RAG system with trained model
2. Validate search accuracy with sample queries
3. Measure performance metrics
4. Generate comprehensive training report

## Performance Considerations

### Memory Management
- Process embeddings in batches of 32 cases
- Use memory-efficient data structures
- Clear intermediate data to prevent memory leaks

### Storage Optimization
- Use efficient vector storage formats
- Compress embeddings where possible
- Implement incremental indexing for large datasets

### Search Performance
- Optimize ChromaDB configuration for legal text
- Implement caching for frequently accessed cases
- Use appropriate similarity thresholds

## Security Considerations

- Validate all file paths before cleanup operations
- Ensure no sensitive data is exposed during processing
- Implement safe file removal with validation checks
- Log all operations for audit trail