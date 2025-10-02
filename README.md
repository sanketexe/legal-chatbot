# LegalAssist Pro - Professional AI Legal Assistant

## 🏛️ Overview
LegalAssist Pro is a professional AI-powered legal assistant providing instant guidance on legal matters. Built with a clean, enterprise-grade interface suitable for legal professionals and individuals seeking legal information.

## ✨ Features
- **🎯 Instant Legal Guidance**: Get immediate answers to legal questions
- **⚖️ Multi-Practice Areas**: Criminal law, civil matters, contracts, personal injury, IP protection
- **🛡️ Professional Interface**: Enterprise-grade design with trust indicators
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
4. **Run the Application**:
   ```bash
   python simple_app.py
   ```
5. **Open Browser**: Go to `http://localhost:5000`

### Get Free Gemini API Key
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with Google account
3. Create new API key
4. Copy key to `.env` file

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
└── data/
    └── constitution/         # Legal reference documents
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

## 🔧 API Integration
Uses Google Gemini 2.5 Flash model:
- **Free Tier**: 1,500 requests per day
- **Fast Response**: Optimized for legal queries
- **Smart Formatting**: Auto-bold important legal terms
- **Structured Responses**: Professional legal guidance format

## 📱 Deployment Options

### Local Development
```bash
python simple_app.py
```

### AWS Deployment
**Option 1: Elastic Beanstalk (Recommended)**
- Easy deployment with auto-scaling
- Estimated cost: $10-30/month

**Option 2: AWS Lambda (Serverless)**
- Pay-per-use pricing
- Estimated cost: $1-10/month

**Option 3: EC2 Instance**
- Full control over environment
- Estimated cost: $8-15/month

### Production Deployment
For production use:
1. Use WSGI server (Gunicorn)
2. Set up SSL certificate
3. Configure proper logging
4. Set up monitoring
5. Use environment variables for API keys

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
3. **Port conflicts**: Change port in `config.py`
4. **Import errors**: Run `pip install -r requirements.txt`

### Getting Help
- Check console for error messages
- Verify API key is valid
- Ensure internet connection
- Review configuration settings

## 📄 License
This project is for educational and informational purposes only. Not intended as a substitute for professional legal advice.

## 🙏 Acknowledgments
- Google Gemini AI for natural language processing
- Flask framework for web application
- Font Awesome for professional icons
- Google Fonts for typography

---

**⚠️ Legal Disclaimer**: This AI provides legal information only, not legal advice. Laws vary by jurisdiction and circumstances. For specific legal matters, consult with a qualified attorney.