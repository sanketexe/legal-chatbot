# Legal RAG System - ML Module

This module implements a **Retrieval-Augmented Generation (RAG)** system for training and using Indian legal case data. The system provides accurate, citation-backed legal advice using semantic search through Supreme Court and High Court precedents.

## 🏗️ Architecture

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

## 📁 Module Structure

```
ml_legal_system/
├── optimized_legal_rag.py    # Main RAG system implementation
├── legal_rag.py             # Original RAG implementation
├── vector_db.py             # Vector database management
├── load_cases.py            # Case loading and training script
├── data_consolidator.py     # Data consolidation utilities
├── config.py                # Configuration settings
├── README.md                # This file
└── __pycache__/            # Python cache files
```

## 🚀 Local RAG Training and Usage

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `chromadb` - Vector database
- `sentence-transformers` - Embeddings
- `google-generativeai` - Gemini LLM (FREE)
- `numpy`, `pandas` - Data processing

### 2. Configure API Keys

Update `.env` file:

```env
# Google Gemini (FREE - Recommended)
GOOGLE_API_KEY=your-google-api-key-here
```

**Get FREE Google Gemini API Key:**
1. Go to https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy and paste into `.env`

### 3. Train RAG System with Legal Cases

```bash
python ml_legal_system/load_cases.py
```

This training process will:
- ✅ Load 940+ scraped legal cases from JSON files
- ✅ Generate embeddings using sentence-transformers
- ✅ Store embeddings in ChromaDB vector database
- ✅ Validate search functionality
- ⏱️ Takes ~2-3 minutes (one-time training)

### 4. Test Trained RAG System

```bash
python ml_legal_system/optimized_legal_rag.py
```

Test with sample legal queries:
- "What is the penalty for breach of contract in India?"
- "Can I claim damages for delayed property possession?"
- "What are the grounds for divorce under Indian law?"

## 📚 Components

### 1. Legal RAG System (`optimized_legal_rag.py`)

**Purpose:** Main RAG system for legal question answering

**Key Features:**
- Trained on 940+ Indian legal cases
- Optimized performance and accuracy
- Citation-backed responses
- Semantic search through case precedents

**Usage:**
```python
from optimized_legal_rag import OptimizedLegalRAG

rag = OptimizedLegalRAG()
result = rag.answer_legal_query("What is the penalty for breach of contract?")
print(result['answer'])
print(result['sources'])
```

### 2. Case Loading and Training (`load_cases.py`)

**Purpose:** Trains the RAG system by loading and processing legal case dataset

**Key Features:**
- Loads 940+ scraped cases from JSON files
- Generates embeddings using sentence-transformers
- Stores embeddings in ChromaDB with metadata
- Validates database integrity after training

**Usage:**
```python
# Run as script to train the system
python ml_legal_system/load_cases.py
```

### 3. Vector Database (`vector_db.py`)

**Purpose:** Manages ChromaDB operations for storing and retrieving embeddings

**Key Features:**
- Local ChromaDB storage
- Sentence embeddings (FREE)
- Top-K similarity search
- Metadata filtering

**Usage:**
```python
from vector_db import LegalVectorDatabase

db = LegalVectorDatabase()
results = db.search_similar_cases("contract dispute", top_k=5)
```

### 4. Data Consolidator (`data_consolidator.py`)

**Purpose:** Consolidates and validates legal case data

**Key Features:**
- Merges partial case files
- Validates data integrity
- Removes duplicates
- Generates quality reports

**Usage:**
```python
from data_consolidator import DataConsolidator

consolidator = DataConsolidator()
cases = consolidator.consolidate_all_cases()
```

## ⚙️ Configuration

### Environment Variables (`.env`)

```env
# LLM Settings (Required)
GOOGLE_API_KEY=AIza...              # Google Gemini key (FREE)

# RAG Settings (Optional - defaults provided)
TOP_K_RETRIEVAL=5                   # Number of cases to retrieve
SIMILARITY_THRESHOLD=0.7            # Minimum similarity score
EMBEDDING_MODEL=all-MiniLM-L6-v2    # Sentence transformer model
CHROMADB_PATH=data/chromadb         # Vector database path
```

### Configuration File (`config.py`)

```python
# Core RAG settings
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
CHROMADB_COLLECTION = 'indian_legal_cases'
TOP_K_DEFAULT = 5
SIMILARITY_THRESHOLD = 0.7

# Performance settings
BATCH_SIZE = 32
MAX_CONTEXT_LENGTH = 4000
RESPONSE_MAX_TOKENS = 1000
```

## 🎯 Usage Examples

### Example 1: Training and Using RAG System

```python
from optimized_legal_rag import OptimizedLegalRAG

# Initialize RAG system (ensure training is complete first)
rag = OptimizedLegalRAG()

# Ask a legal question
result = rag.answer_legal_query(
    "Can I terminate my employment contract without notice?"
)

print("Answer:", result['answer'])
print("\nRelevant Cases:")
for case in result['sources']:
    print(f"- {case['title']}")
    print(f"  {case['court']} | {case['date']}")
```

### Example 2: Direct Vector Search

```python
from vector_db import LegalVectorDatabase

# Search case database
db = LegalVectorDatabase()
results = db.search_similar_cases(
    query="trademark infringement",
    top_k=5
)

for case in results:
    print(f"Similarity: {case['similarity']:.3f}")
    print(f"Case: {case['title']}")
```

### Example 3: Training Validation

```python
# Test the RAG system after training
python test_rag_system.py

# Run performance benchmarks
python ml_legal_system/final_performance_test.py
```

## 🔧 Troubleshooting

### Issue: ChromaDB not initialized

**Solution:** Run training script to initialize database
```bash
python ml_legal_system/load_cases.py
```

### Issue: Import errors

**Solution:** Install missing packages
```bash
pip install chromadb sentence-transformers google-generativeai
```

### Issue: LLM generation fails

**Solution:** Check API key in `.env`
```bash
# For Gemini
GOOGLE_API_KEY=your-key-here
```

### Issue: No search results

**Solution:** Verify database is trained and loaded
```python
# Check if ChromaDB has data
from vector_db import LegalVectorDatabase
db = LegalVectorDatabase()
print(f"Cases in database: {db.get_collection_count()}")
```

### Issue: Poor answer quality

**Solution:** Adjust similarity threshold
```python
# In config.py - lower threshold for more results
SIMILARITY_THRESHOLD = 0.5  # Default: 0.7
```

## 📊 Performance

### Cost Analysis (Local System)

| Component | Setup | Cost |
|-----------|-------|------|
| Embeddings | sentence-transformers (local) | **FREE** |
| Vector DB | ChromaDB (local) | **FREE** |
| LLM | Google Gemini (API) | **FREE** (1,500 requests/day) |
| Training Data | 940+ cases (scraped) | **FREE** |
| **Total** | **Fully FREE** | **$0/month** |

**Benefits:** No ongoing costs, local processing, privacy-focused

### Performance (Local System)

- Case retrieval: ~0.3-0.8 seconds
- Vector search: ~0.1-0.3 seconds
- LLM response: ~2-4 seconds
- **Total:** ~2.5-5 seconds per query
- **Database size:** ~50MB (940+ cases + embeddings)
- **Memory usage:** ~200-400MB during operation

## 🔒 Security

- API keys stored in `.env` (never commit!)
- Rate limiting on scraper
- Input validation on queries
- SQL injection prevention (SQLAlchemy ORM)

## 🚀 Local Setup

### Setup Checklist

1. **Train System:**
   ```bash
   python ml_legal_system/load_cases.py
   ```

2. **Validate Training:**
   ```bash
   python test_rag_system.py
   ```

3. **Performance Test:**
   ```bash
   python ml_legal_system/final_performance_test.py
   ```

4. **Start Application:**
   ```bash
   python simple_app.py
   ```

### Data Persistence

- **ChromaDB:** Stored in `data/chromadb/` (persistent)
- **Case Data:** Located in `data/legal_cases/`
- **Embeddings:** Auto-generated and cached in ChromaDB
- **Backup:** Copy `data/` folder to preserve trained system

## 📈 Training Status

### After Training Completion
- ✅ **940+ Legal Cases** - Processed and embedded
- ✅ **ChromaDB Vector Database** - Indexed and ready
- ✅ **RAG Pipeline** - Trained and validated
- ✅ **Performance Optimized** - Sub-5 second responses
- ✅ **Citation System** - Automatic case references

### Expected Results After Training
- **Search Accuracy:** High relevance for legal queries
- **Response Quality:** Citation-backed answers
- **Performance:** Consistent sub-5 second responses
- **Coverage:** Supreme Court and High Court cases
- **Reliability:** Stable local operation

## 🤝 Extending the System

To add more cases to the system:

1. **Add new case data** to `data/legal_cases/`
2. **Re-run training:**
   ```bash
   python ml_legal_system/load_cases.py
   ```
3. **Validate updates:**
   ```bash
   python test_rag_system.py
   ```

## 📄 License

MIT License - See LICENSE file

## 🆘 Support

For issues:
1. Check troubleshooting section
2. Review error messages
3. Verify API keys in `.env`
4. Check data files exist

---

**Built with ❤️ for the Indian Legal Community**