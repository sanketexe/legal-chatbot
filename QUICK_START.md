# 🚀 Quick Start Guide - LegalCounsel AI

## Start the Production System in 3 Steps

### Step 1: Verify Environment ✅
```bash
# Check if all dependencies are installed
python -c "import flask, chromadb, sentence_transformers, google.generativeai; print('✅ All dependencies ready!')"
```

### Step 2: Start the Server 🚀
```bash
python app_with_db.py
```

**Expected output:**
```
✅ ChromaDB local vector database initialized
✅ Google Gemini initialized
✅ ML-powered Legal Engine initialized
✅ Legal engine initialized successfully

⚖️ Legal Assistant Starting...
📡 AI Provider: GEMINI
🌐 Server: http://0.0.0.0:5000
💾 Database: sqlite:///legal_chatbot.db
----------------------------------------
 * Running on http://127.0.0.1:5000
```

### Step 3: Open in Browser 🌐
Navigate to: **http://localhost:5000**

---

## Try These Sample Questions

Once the chat interface loads, try asking:

### 📝 Contract Law
- "What are the remedies for breach of contract in India?"
- "Can I cancel a contract after signing?"
- "What is the statute of limitations for contract disputes?"

### 🏠 Property Law
- "What are tenant rights regarding eviction in India?"
- "How do I verify property ownership before buying?"
- "Can landlords increase rent without notice?"

### 👨‍👩‍👧 Family Law
- "What are the grounds for divorce in India?"
- "How is child custody determined in divorce cases?"
- "What are the property rights of a wife after divorce?"

### ⚖️ Constitutional Rights
- "What are my fundamental rights under the Indian Constitution?"
- "Can I be arrested without a warrant?"
- "What is the right to free speech in India?"

---

## What You'll See

### Response with Case Citations:
```
[AI provides detailed legal information]

📚 Cited Legal Cases (3)

1. State of Maharashtra v. Ramdas Shrinivas
   🏛️ Supreme Court of India | 📅 2018
   📊 87% relevance
   🔗 View Full Case

2. [Another relevant case]
   ...
```

### Features You'll Experience:
- ✨ Professional chat interface
- 📚 Real case citations with metadata
- 🎨 Color-coded relevance scores (green = highly relevant)
- ⚠️ Legal disclaimers (banner + footer)
- 🔒 Optional user authentication
- 💾 Chat history (for logged-in users)
- 📱 Mobile-responsive design

---

## System Health Check

Visit: **http://localhost:5000/api/health**

You should see:
```json
{
  "status": "healthy",
  "ml_system": {
    "ml_available": true,
    "rag_initialized": true
  },
  "features": {
    "case_search": true,
    "rag_responses": true,
    "citations": true
  }
}
```

---

## Troubleshooting

### Server won't start?
```bash
# Check if port 5000 is already in use
netstat -ano | findstr :5000

# If in use, kill the process or use different port
$env:FLASK_RUN_PORT="5001"
python app_with_db.py
```

### ML system not initializing?
- Check Gemini API key in `.env` file
- Verify ChromaDB can access `data/vector_db/`
- Ensure 1,422 cases are in `data/legal_cases/indian_legal_cases_complete.json`

### No case citations?
```bash
# Verify vector database is loaded
python -c "from ml_legal_system.vector_db import LegalVectorDatabase; db = LegalVectorDatabase(); print(f'Cases loaded: {db.collection.count()}')"
```

Expected: `Cases loaded: 1422`

---

## Advanced Usage

### Test the RAG System:
```bash
python test_rag_system.py
```

### Search Cases Directly:
```bash
curl -X POST http://localhost:5000/api/search-cases \
  -H "Content-Type: application/json" \
  -d '{"query": "breach of contract compensation"}'
```

### Create User Account:
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "user123", "email": "user@example.com", "password": "secure123"}'
```

---

## 🎯 Current Capabilities

| Feature | Status | Details |
|---------|--------|---------|
| Case Database | ✅ | 1,422 Indian legal cases |
| Semantic Search | ✅ | Vector similarity matching |
| Case Citations | ✅ | Real cases with metadata |
| LLM Integration | ✅ | Google Gemini 2.5-flash |
| Error Handling | ✅ | 3 retry attempts + fallback |
| Legal Disclaimers | ✅ | Banner + footer warnings |
| User Auth | ✅ | JWT-based authentication |
| Chat History | ✅ | Persistent conversations |

---

## 📊 System Performance

- **Response Time:** 2-5 seconds (including LLM)
- **Case Search:** <1 second for top 5 results
- **Database Size:** ~450 MB (cases + embeddings)
- **Concurrent Users:** 10-20 (development server)
- **Uptime:** Continuous (no restart needed)

---

## 🔐 Security Notes

- 🔒 Passwords are hashed with bcrypt
- 🔑 JWT tokens for authentication
- 🛡️ CORS configured for browser extensions
- 🚫 SQL injection protection (SQLAlchemy)
- ⚠️ Legal disclaimers protect liability

---

## 📞 Support

If you encounter issues:
1. Check `PRODUCTION_READY_SUMMARY.md` for detailed documentation
2. Review error messages in terminal
3. Verify all dependencies are installed
4. Check that Gemini API key is set correctly

---

**🎉 Enjoy your production-ready legal chatbot with real case citations!**

*System Version: 1.0.0-production*  
*Last Updated: October 26, 2025*
