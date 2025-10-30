# LegalAssist Pro - AI Legal Assistant with RAG System

## 🏛️ Overview
LegalAssist Pro is an AI-powered legal assistant that provides instant guidance on legal matters using a trained Retrieval-Augmented Generation (RAG) system. The system is trained on 940+ Indian legal cases from Supreme Court and High Courts, providing accurate, citation-backed legal advice.

## ✨ Features
- **🎯 RAG-Powered Legal Guidance**: Get answers backed by actual Indian legal precedents
- **⚖️ Comprehensive Case Database**: 940+ cases from Indian Supreme Court and High Courts
- **🔍 Semantic Search**: Advanced vector search through legal cases
- **📚 Citation-Backed Responses**: All answers include relevant case citations
- **🛡️ Professional Interface**: Clean, enterprise-grade design
- **📱 Responsive Design**: Works on desktop, tablet, and mobile
- **🌐 Browser Extension**: Quick access via Chrome/Firefox extension
- **🔒 Confidential**: Your conversations are private and secure

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Google Gemini API Key (free tier available)

### Installation
1. **Clone or Download** this repository
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Set API Key** in `.env` file:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```
4. **Initialize RAG System** (first time only):
   ```bash
   python ml_legal_system/load_cases.py
   ```
5. **Run the Application**:
   ```bash
   python simple_app.py
   ```
6. **Open Browser**: Go to `http://localhost:5000`

### Get Free Gemini API Key
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with Google account
3. Create new API key
4. Copy key to `.env` file

### RAG System Setup
The system comes with pre-trained embeddings for 940+ Indian legal cases. On first run, the system will:
- Load case embeddings into ChromaDB
- Initialize the vector database
- Validate search functionality

This process takes ~2-3 minutes and only needs to be done once.

## 📁 Project Structure
```
LegalChatbot/
├── simple_app.py              # Main Flask application
├── config.py                  # Configuration settings
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (API keys)
├── src/
│   └── simple_legal_engine.py # AI legal reasoning engine
├── templates/
│   └── simple.html           # Professional web interface
├── browser_extension/
│   ├── manifest.json         # Extension configuration
│   ├── simple_popup.html     # Extension popup interface
│   ├── simple_popup.js       # Extension functionality
│   └── icons/               # Extension icons
├── ml_legal_system/          # RAG system implementation
│   ├── legal_rag.py         # Main RAG system
│   ├── vector_db.py         # Vector database management
│   ├── load_cases.py        # Case loading script
│   └── optimized_legal_rag.py # Optimized RAG implementation
└── data/
    ├── legal_cases/         # Indian legal cases dataset
    └── chromadb/           # Vector database storage
```

## 🎨 Professional Design
- **Premium Branding**: "LegalAssist Pro" with scale of justice logo
- **Professional Colors**: Deep blue, gold accents, clean design
- **Typography**: Inter + Playfair Display fonts
- **Interactive Elements**: Quick topic cards, smooth animations
- **Trust Indicators**: Confidentiality badges, professional disclaimers

## 🌐 Browser Extension Setup
1. Open Chrome/Firefox
2. Go to Extensions page
3. Enable "Developer mode"
4. Click "Load unpacked"
5. Select the `browser_extension` folder
6. Pin the extension to toolbar

## ⚙️ Configuration
Edit `config.py` to customize:
- API settings (Gemini model, temperature, max tokens)
- Server settings (host, port, debug mode)
- Application behavior

## 🔧 RAG System Integration
The system uses a sophisticated RAG (Retrieval-Augmented Generation) pipeline:
- **Vector Database**: ChromaDB with 940+ legal case embeddings
- **Semantic Search**: sentence-transformers for case retrieval
- **LLM Generation**: Google Gemini 2.5 Flash model (free tier)
- **Citation System**: Automatic case citations with court details
- **Performance**: ~3-7 seconds per query with relevant case context

## 📱 Local Development

### Running the Application
```bash
# Start the RAG-powered legal assistant
python simple_app.py
```

### Testing the RAG System
```bash
# Test RAG system directly
python ml_legal_system/optimized_legal_rag.py
```

### Performance Testing
```bash
# Run comprehensive RAG tests
python test_rag_system.py
```

### Production Considerations
For production deployment:
1. Ensure ChromaDB data persistence
2. Configure proper logging for RAG operations
3. Set up monitoring for query performance
4. Use environment variables for API keys
5. Consider scaling vector database for high traffic

## 🔒 Security & Legal
- **Confidentiality**: Conversations are not stored
- **Legal Disclaimer**: Provides information, not legal advice
- **Data Privacy**: No personal data collection
- **Secure API**: HTTPS recommended for production

## 🤝 Usage Guidelines
- **Information Only**: This provides legal information, not legal advice
- **Consult Attorneys**: For specific legal matters, consult qualified attorneys
- **Educational Purpose**: Use for learning and general guidance
- **No Liability**: AI responses should not replace professional legal counsel

## 🛠️ Troubleshooting

### Common Issues
1. **"Technical difficulties" error**: Update Gemini model names in config
2. **API Key issues**: Verify key is correct and has quota
3. **RAG system not initialized**: Run `python ml_legal_system/load_cases.py`
4. **ChromaDB errors**: Delete `data/chromadb` folder and reinitialize
5. **Import errors**: Run `pip install -r requirements.txt`
6. **Slow responses**: Check vector database is properly loaded

### RAG System Issues
- **No case results**: Verify ChromaDB contains embeddings
- **Poor answer quality**: Check similarity thresholds in config
- **Memory issues**: Reduce batch size in case loading
- **Database corruption**: Reinitialize ChromaDB from scratch

### Getting Help
- Check console for error messages
- Verify API key is valid
- Ensure ChromaDB is properly initialized
- Review RAG system logs for debugging

## 📄 License
This project is for educational and informational purposes only. Not intended as a substitute for professional legal advice.

## 🙏 Acknowledgments
- Google Gemini AI for natural language processing
- Flask framework for web application
- Font Awesome for professional icons
- Google Fonts for typography

---

**⚠️ Legal Disclaimer**: This AI provides legal information only, not legal advice. Laws vary by jurisdiction and circumstances. For specific legal matters, consult with a qualified attorney.