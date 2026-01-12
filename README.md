# LegalAssist Pro - AI-Powered Legal Consultation Platform

An intelligent legal consultation platform that provides AI-powered legal guidance based on Indian law, featuring case law citations, document analysis, and multilingual support with **integrated case analysis engine**.

## Features

### Core Functionality
- **AI-Powered Legal Consultation**: Get instant legal guidance powered by Google Gemini AI
- **Case Law Citations**: Responses include relevant Indian case law references and precedents
- **RAG System**: Retrieval-Augmented Generation with 940+ Indian legal cases
- **Document Analysis**: Upload and analyze legal documents (PDF, DOCX, TXT)
- **Multilingual Support**: English and Hindi language support with automatic translation
- **✨ Real-Time Case Analysis Panel** 🆕: Comprehensive case information sidebar
  - **Auto-Display**: Automatically opens when bot returns case sources
  - **Rich Metadata**: Court, date, judges, parties, case status
  - **Visual Timeline**: Animated case progression with key events
  - **Judgment Summary**: Color-coded decision highlights
  - **Citations & References**: Up to 5 citations with document links
  - **Responsive Design**: Adapts to mobile with full-screen overlay
  - **Purple Gradient Theme**: Professional, eye-catching design
- **✨ Famous Cases Database** 🆕: Instant responses for landmark Indian cases
  - **Intelligent Detection**: Multi-tier keyword matching system
  - **Instant Responses**: < 0.1s for famous case queries (vs 2-5s vector search)
  - **Comprehensive Info**: Full case details, timeline, impact, and legal sections
  - **Currently Includes**: Unnao Rape Case, Nirbhaya Case, Kesavananda Bharati, Vishaka
  - **Fallback Prevention**: No more "I don't know" for famous cases
  - **Auto-Analysis**: Case details appear in analysis panel automatically
- **✨ Citation Network Visualization**: Interactive graph-based visualization of case citations and precedents
  - **Fully Integrated**: Access from advanced search, chat interface, or direct URLs
  - **Deep Linking**: Share specific cases with URL parameters
  - **Auto-Detection**: Automatically identifies case references in chat conversations
  - **Interactive Graph**: Force-directed layout with zoom, pan, and filtering
  - **PageRank Analysis**: Identify most influential cases
  - **Path Finding**: Discover citation chains between cases
- **✨ Case Summarization** ⭐: AI-powered case summarization with multiple methods
  - **Three Methods**: Extractive (TF-IDF), Abstractive (Gemini AI), Hybrid (Best of both)
  - **Multiple Lengths**: Short (100-200 words), Medium (200-400 words), Long (400-800 words)
  - **Legal Components**: Structured extraction of Facts, Issues, Reasoning, and Judgment
  - **Key Points**: Highlights the 5 most important aspects of each case
  - **Smart Caching**: Instant loading of previously generated summaries
  - **Integrated Access**: Available in search results, chat responses, and standalone page
  - **Copy & Export**: Copy to clipboard or export as text file
- **✨ Case Outcome Predictor** 🔮: ML-powered prediction of case outcomes
  - **Integrated Predictions**: Automatically shows predictions in search results and chat responses
  - **Machine Learning Models**: Random Forest + XGBoost ensemble (66.67% accuracy)
  - **Training Data**: Trained on 315+ real legal cases from ChromaDB
  - **Predictions**: Favorable, Unfavorable, or Partial outcomes with confidence scores
  - **Reasoning**: Explains key factors influencing the prediction
  - **Similar Cases**: Shows 5 most similar historical cases with outcomes
  - **Historical Patterns**: Displays outcome distribution from search results
  - **Auto-Detection**: Triggers on outcome-related queries ("what will happen?", "chances of winning")
  - **Standalone Interface**: Dedicated UI at /case-predictor for detailed analysis
  - **User Feedback**: Track prediction accuracy and improve models over time

### User Features
- **User Authentication**: Secure JWT-based authentication system
- **Chat History**: Save and retrieve past consultations
- **Conversation Memory**: Context-aware responses with conversation tracking
- **Advanced Search Filters**: Filter cases by court, year, keywords, and legal concepts
  - **✨ Citation Network Access**: "View Network" button on every search result
  - **✨ Bulk Network View**: View entire result set in citation network
- **User Preferences**: Customize language, response detail level, and legal domains
- **Response Rating**: Rate AI responses to improve service quality
- **Session Management**: Organize consultations into sessions
- **Voice Input/Output**: Speech-to-text and text-to-speech for hands-free interaction

### Technical Features
- **Vector Database**: ChromaDB for efficient semantic search
- **Rate Limiting**: Protect API endpoints from abuse
- **CORS Support**: Browser extension and web access enabled
- **Database**: SQLite/PostgreSQL support with SQLAlchemy ORM
- **Responsive UI**: Modern, mobile-friendly interface

## Technology Stack

- **Backend**: Flask (Python)
- **AI/ML**: Google Gemini API, ChromaDB, Sentence Transformers, scikit-learn, XGBoost
- **Database**: SQLAlchemy (SQLite/PostgreSQL)
- **Authentication**: Flask-JWT-Extended
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Document Processing**: PyPDF2, python-docx

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

The application will be available at `http://localhost:5000`

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

#### Case Outcome Prediction 🔮
- `POST /api/predict-outcome` - Predict case outcome with ML models
- `GET /api/prediction-history` - Get user's prediction history
- `POST /api/prediction-feedback` - Submit feedback on prediction accuracy
- `GET /api/model-info` - Get ML model information and accuracy

#### Case Summarization
- `POST /api/summarize-case` - Generate case summary (extractive/abstractive/hybrid)
- `POST /api/batch-summarize` - Batch summarize multiple cases

## Project Structure

```
LegalChatbot/
├── app.py                      # Main application file
├── auth.py                     # Authentication logic
├── models.py                   # Database models (8 tables)
├── config.py                   # Configuration management
├── logging_config.py           # Logging configuration
├── document_analyzer.py        # Document analysis module
├── legal_engine_ml.py          # ML-powered legal engine
├── case_outcome_predictor.py   # ML model training script
├── prediction_service.py       # Prediction service (singleton)
├── admin_blueprint.py          # Admin dashboard backend
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
├── templates/
│   ├── simple.html            # Main web interface
│   ├── case_predictor.html    # Case outcome predictor UI
│   ├── case_summarization.html # Case summarization UI
│   ├── citation_network.html  # Citation network visualization
│   └── admin/
│       └── dashboard.html     # Admin dashboard
├── ml_models/                  # Trained ML models (auto-generated)
│   ├── rf_model.pkl           # Random Forest model
│   ├── xgb_model.pkl          # XGBoost model
│   ├── tfidf_vectorizer.pkl   # TF-IDF vectorizer
│   └── model_metadata.json    # Model accuracy & features
├── ml_legal_system/
│   ├── rag_system.py          # RAG implementation
│   ├── translators.py         # Translation services
│   └── embeddings.py          # Embedding models
├── data/
│   ├── chromadb/              # Vector database (315 cases)
│   └── legal_cases/           # Legal case JSON files
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

### Case Outcome Predictor 🔮
Machine learning system that predicts legal case outcomes with **automatic integration** in search and chat:

**Integrated User Experience:**
- **Search Results**: Predictions automatically appear when searching for cases
- **Chat Conversations**: Outcome predictions included when users ask "what will happen?" type questions
- **Standalone Tool**: Dedicated interface at `/case-predictor` for detailed analysis
- **Seamless Display**: Purple gradient cards with confidence meters, historical patterns, and key factors

**How It Works:**
1. **Training**: Models trained on 315 real legal cases from ChromaDB
2. **Features**: Extracts text patterns, court type, case type, legal sections, precedents
3. **Models**: Ensemble of Random Forest + XGBoost (66.67% accuracy)
4. **Output**: Predicts Favorable/Unfavorable/Partial with confidence score
5. **Integration**: Auto-triggers in search results and outcome-related chat queries

**To Train Models:**
```bash
python case_outcome_predictor.py
```

**Models Generated:**
- `ml_models/rf_model.pkl` - Random Forest classifier
- `ml_models/xgb_model.pkl` - XGBoost classifier  
- `ml_models/tfidf_vectorizer.pkl` - Text vectorizer
- `ml_models/model_metadata.json` - Accuracy metrics

**Prediction Includes:**
- Confidence score (0-100%)
- Key contributing factors with importance weights
- 5 most similar historical cases
- All outcome probabilities
- Legal disclaimer

**Access:**
- Web UI: http://localhost:5000/case-predictor
- API: POST /api/predict-outcome

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
