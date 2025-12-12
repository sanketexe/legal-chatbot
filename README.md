# LegalAssist Pro - AI-Powered Legal Consultation Platform

An intelligent legal consultation platform that provides AI-powered legal guidance based on Indian law, featuring case law citations, document analysis, and multilingual support.

## Features

### Core Functionality
- **AI-Powered Legal Consultation**: Get instant legal guidance powered by Google Gemini AI
- **Case Law Citations**: Responses include relevant Indian case law references and precedents
- **RAG System**: Retrieval-Augmented Generation with 940+ Indian legal cases
- **Document Analysis**: Upload and analyze legal documents (PDF, DOCX, TXT)
- **Multilingual Support**: English and Hindi language support with automatic translation

### User Features
- **User Authentication**: Secure JWT-based authentication system
- **Chat History**: Save and retrieve past consultations
- **User Preferences**: Customize language, response detail level, and legal domains
- **Response Rating**: Rate AI responses to improve service quality
- **Session Management**: Organize consultations into sessions

### Technical Features
- **Vector Database**: ChromaDB for efficient semantic search
- **Rate Limiting**: Protect API endpoints from abuse
- **CORS Support**: Browser extension and web access enabled
- **Database**: SQLite/PostgreSQL support with SQLAlchemy ORM
- **Responsive UI**: Modern, mobile-friendly interface

## Technology Stack

- **Backend**: Flask (Python)
- **AI/ML**: Google Gemini API, ChromaDB, Sentence Transformers
- **Enhanced AI**: LangChain framework for advanced document processing and RAG
- **Database**: SQLAlchemy (SQLite/PostgreSQL)
- **Authentication**: Flask-JWT-Extended
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Document Processing**: PyPDF2, python-docx, LangChain document loaders

## LangChain Integration 🔗

This project now supports **LangChain** for enhanced AI capabilities:

### Enhanced Features:
- **Advanced RAG System**: Sophisticated document retrieval and generation
- **Memory Management**: Conversation context across multiple interactions
- **Document Processing**: Better PDF and document analysis with chunking
- **Chain of Thought**: Multi-step legal reasoning
- **Source Attribution**: Responses include relevant document sources
- **Specialized Prompts**: Legal-specific prompt templates

### LangChain Endpoints:
- `POST /api/langchain/chat` - Enhanced AI chat with memory
- `POST /api/langchain/document/upload` - Process documents into vector store
- `POST /api/langchain/document/analyze` - Analyze document content
- `POST /api/langchain/research/case-law` - Research legal precedents
- `POST /api/langchain/advice` - Comprehensive legal guidance
- `GET /api/langchain/status` - Check LangChain integration status

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Google Gemini API key

### Setup Steps

1. **Clone the repository**
```bash
git clone <repository-url>
cd LegalChatbot
```

2. **Create virtual environment**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

Create a `.env` file in the root directory:
```env
# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_API_KEY=your_gemini_api_key_here

# AI Configuration
PREFERRED_AI_PROVIDER=gemini

# Security
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here

# Database (optional - defaults to SQLite)
DATABASE_URL=sqlite:///legal_chatbot.db

# Server Configuration
HOST=0.0.0.0
PORT=5000
```

5. **Initialize the database**
```bash
python -c "from app import app; from models import init_db; init_db(app)"
```

6. **Run the application**
```bash
python app.py
```

### LangChain Enhanced Setup (Optional but Recommended)

7. **Install LangChain dependencies**
```bash
python setup_langchain.py
```

8. **Test LangChain integration**
```bash
python langchain_demo.py
```

The application will be available at `http://localhost:5000`

**LangChain Features Available at:**
- Enhanced chat: `/api/langchain/chat`
- Document analysis: `/api/langchain/document/analyze`
- Case law research: `/api/langchain/research/case-law`

## Screenshots

### Application Interface

![Homepage](images/Screenshot%202025-12-10%20075108.png)
*Main landing page with legal consultation features*

![Chat Interface](images/Screenshot%202025-12-10%20075117.png)
*AI-powered legal chat interface*

![Document Analysis](images/Screenshot%202025-12-10%20075149.png)
*Document upload and analysis feature*

![Legal Results](images/Screenshot%202025-12-10%20075201.png)
*Legal consultation results with case law citations*

![User Dashboard](images/Screenshot%202025-12-10%20075219.png)
*User dashboard and chat history*

![Mobile View](images/Screenshot%202025-12-10%20075231.png)
*Mobile-responsive interface*

![Settings Panel](images/Screenshot%202025-12-10%20075238.png)
*Application settings and preferences*

## Usage

### Web Interface
1. Open your browser and navigate to `http://localhost:5000`
2. Register a new account or login
3. Start asking legal questions in the chat interface
4. Upload documents for analysis using the document upload feature

### API Endpoints

#### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/profile` - Get user profile

#### Chat
- `POST /api/chat` - Send message and get AI response
- `GET /api/chat/sessions` - Get user's chat sessions
- `GET /api/chat/sessions/<id>` - Get specific session with messages
- `DELETE /api/chat/sessions/<id>` - Delete a session

#### Document Analysis
- `POST /api/analyze-document` - Upload and analyze legal document

#### User Preferences
- `GET /api/user/preferences` - Get user preferences
- `POST /api/user/preferences` - Update user preferences

#### Ratings
- `POST /api/rate` - Rate an AI response
- `GET /api/ratings` - Get user's ratings
- `GET /api/ratings/stats` - Get rating statistics

## Project Structure

```
LegalChatbot/
├── app.py                      # Main application file
├── auth.py                     # Authentication logic
├── models.py                   # Database models
├── config.py                   # Configuration management
├── logging_config.py           # Logging configuration
├── document_analyzer.py        # Document analysis module
├── legal_engine_ml.py          # ML-powered legal engine
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
├── templates/
│   └── simple.html            # Main web interface
├── ml_legal_system/
│   ├── rag_system.py          # RAG implementation
│   ├── translators.py         # Translation services
│   └── embeddings.py          # Embedding models
├── data/
│   └── indian_legal_cases.json # Legal case database
└── migrations/                 # Database migrations
```

## Default Credentials

After initialization, a default admin account is created:
- **Username**: admin
- **Password**: admin123

**Important**: Change these credentials in production!

## Features in Detail

### RAG System
The Retrieval-Augmented Generation system uses:
- 940+ Indian legal cases indexed in ChromaDB
- Semantic search using sentence transformers
- Context-aware response generation
- Automatic case law citation

### Document Analysis
Supports multiple document formats:
- PDF documents
- Word documents (DOCX)
- Plain text files

Analysis includes:
- Document summarization
- Key point extraction
- Legal issue identification
- Relevant case law suggestions

### Multilingual Support
- English (default)
- Hindi (हिंदी)
- Automatic translation of AI responses
- Language preference saved per user

## Security Features

- JWT-based authentication
- Password hashing with Werkzeug
- Rate limiting on sensitive endpoints
- CORS configuration for browser extensions
- Session management and token revocation
- SQL injection protection via SQLAlchemy ORM

## Performance Optimization

- Connection pooling for database
- Vector database caching
- Lazy loading of ML models
- Response compression
- Efficient query optimization

## Browser Extension

The platform includes a Chrome/Firefox browser extension for quick access to legal consultation while browsing.

Extension features:
- Quick legal queries from any webpage
- Document analysis from browser
- Saved consultation history
- Seamless authentication

## Deployment

### Production Considerations

1. **Use a production WSGI server**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

2. **Use PostgreSQL for production**
```env
DATABASE_URL=postgresql://user:password@localhost/legalassist
```

3. **Enable HTTPS**
4. **Set strong secret keys**
5. **Configure proper CORS origins**
6. **Set up monitoring and logging**

### Environment Variables for Production
```env
FLASK_ENV=production
DEBUG=False
DATABASE_URL=postgresql://...
GEMINI_API_KEY=...
SECRET_KEY=<strong-random-key>
JWT_SECRET_KEY=<strong-random-key>
```

## Contributing

Contributions are welcome! Please follow these guidelines:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This application provides general legal information based on Indian law. It is not a substitute for professional legal advice. Always consult with a qualified attorney for specific legal matters.

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Contact: [your-email@example.com]

## Acknowledgments

- Google Gemini AI for powering the legal consultation
- ChromaDB for vector database capabilities
- Indian legal case database contributors
- Open source community

---

**Version**: 1.0.0  
**Last Updated**: December 2025
