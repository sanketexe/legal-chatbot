# ⚖️ LegalAssist Pro# LegalAssist Pro - Professional AI Legal Assistant



A professional AI-powered legal chatbot that provides legal information and guidance. Available as both a web application and browser extension.## 🏛️ Overview

LegalAssist Pro is a professional AI-powered legal assistant providing instant guidance on legal matters. Built with a clean, enterprise-grade interface suitable for legal professionals and individuals seeking legal information.

## 🌐 Live Demo

## ✨ Features

**Web App**: https://legal-chatbot-ikpow5p6r-sankets-projects-34ae550b.vercel.app- **🎯 Instant Legal Guidance**: Get immediate answers to legal questions

- **⚖️ Multi-Practice Areas**: Criminal law, civil matters, contracts, personal injury, IP protection

## 🚀 Features- **🛡️ Professional Interface**: Enterprise-grade design with trust indicators

- **📱 Responsive Design**: Works on desktop, tablet, and mobile

- **Professional Legal Assistant**: Get legal information on criminal law, civil matters, rights, and procedures- **🌐 Browser Extension**: Quick access via Chrome/Firefox extension

- **Smart AI Integration**: Powered by Google Gemini 2.5 for intelligent responses- **🔒 Confidential**: Your conversations are private and secure

- **Readable Responses**: Well-formatted answers with clear sections and bullet points

- **Web App**: Accessible from any device with a browser## 🚀 Quick Start

- **Browser Extension**: Quick access from Chrome/Firefox toolbar

- **Professional UI**: Modern, responsive design with gradient styling### Prerequisites

- Python 3.8+

## 📁 Project Structure- Google Gemini API Key (free tier available)



```### Installation

LegalChatbot/1. **Clone or Download** this repository

├── simple_app.py              # Main Flask application2. **Install Dependencies**:

├── config.py                  # Configuration settings   ```bash

├── requirements.txt           # Python dependencies   pip install -r requirements.txt

├── src/                       # Source code   ```

│   └── simple_legal_engine.py # AI legal reasoning engine3. **Set API Key** in `.env` file:

├── templates/                 # Web interface   ```

│   └── simple.html           # Professional web UI   GEMINI_API_KEY=your_api_key_here

├── browser_extension/         # Chrome/Firefox extension   ```

│   ├── manifest.json         # Extension configuration4. **Run the Application**:

│   ├── simple_popup.html     # Extension popup UI   ```bash

│   ├── simple_popup.js       # Extension logic   python simple_app.py

│   └── icons/               # Extension icons   ```

└── vercel.json               # Deployment configuration5. **Open Browser**: Go to `http://localhost:5000`

```

### Get Free Gemini API Key

## 🛠️ Installation & Setup1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)

2. Sign in with Google account

### Prerequisites3. Create new API key

- Python 3.8+4. Copy key to `.env` file

- Google Gemini API key

## 📁 Project Structure

### Local Development```

LegalChatbot/

1. **Clone the repository**├── simple_app.py              # Main Flask application

   ```bash├── config.py                  # Configuration settings

   git clone https://github.com/sanketexe/legal-chatbot.git├── requirements.txt           # Python dependencies

   cd legal-chatbot├── .env                       # Environment variables (API keys)

   ```├── src/

│   └── simple_legal_engine.py # AI legal reasoning engine

2. **Install dependencies**├── templates/

   ```bash│   └── simple.html           # Professional web interface

   pip install -r requirements.txt├── browser_extension/

   ```│   ├── manifest.json         # Extension configuration

│   ├── simple_popup.html     # Extension popup interface

3. **Set up environment variables**│   ├── simple_popup.js       # Extension functionality

   ```bash│   └── icons/               # Extension icons

   cp .env.example .env└── data/

   # Edit .env and add your GEMINI_API_KEY    └── constitution/         # Legal reference documents

   ``````



4. **Run the application**## 🎨 Professional Design

   ```bash- **Premium Branding**: "LegalAssist Pro" with scale of justice logo

   python simple_app.py- **Professional Colors**: Deep blue, gold accents, clean design

   ```- **Typography**: Inter + Playfair Display fonts

- **Interactive Elements**: Quick topic cards, smooth animations

5. **Open your browser**- **Trust Indicators**: Confidentiality badges, professional disclaimers

   - Navigate to `http://localhost:5000`

## 🌐 Browser Extension Setup

## 🧩 Browser Extension1. Open Chrome/Firefox

2. Go to Extensions page

### Install for Development3. Enable "Developer mode"

1. Open Chrome → `chrome://extensions/`4. Click "Load unpacked"

2. Enable "Developer mode"5. Select the `browser_extension` folder

3. Click "Load unpacked"6. Pin the extension to toolbar

4. Select the `browser_extension` folder

## ⚙️ Configuration

### FeaturesEdit `config.py` to customize:

- Quick access from browser toolbar- API settings (Gemini model, temperature, max tokens)

- Professional popup interface- Server settings (host, port, debug mode)

- Connects to deployed web app- Application behavior

- Works offline with graceful fallbacks

## 🔧 API Integration

## 🌍 DeploymentUses Google Gemini 2.5 Flash model:

- **Free Tier**: 1,500 requests per day

The app is automatically deployed to Vercel on every GitHub push.- **Fast Response**: Optimized for legal queries

- **Smart Formatting**: Auto-bold important legal terms

### Environment Variables (Vercel)- **Structured Responses**: Professional legal guidance format

- `GEMINI_API_KEY`: Your Google Gemini API key

## 📱 Deployment Options

## 🎯 Usage

### Local Development

### Web Application```bash

1. Visit the live URL or run locallypython simple_app.py

2. Type your legal question in the chat interface```

3. Get instant AI-powered legal guidance

4. Responses include sections like "Quick Answer", "Your Options", and "Next Steps"### AWS Deployment

**Option 1: Elastic Beanstalk (Recommended)**

### Browser Extension- Easy deployment with auto-scaling

1. Click the extension icon in your toolbar- Estimated cost: $10-30/month

2. Use quick action buttons for common questions

3. Chat directly with the legal assistant**Option 2: AWS Lambda (Serverless)**

4. Get the same professional responses as the web app- Pay-per-use pricing

- Estimated cost: $1-10/month

## 📝 Example Questions

**Option 3: EC2 Instance**

- "What are my rights if I'm arrested?"- Full control over environment

- "How do I file a small claims case?"- Estimated cost: $8-15/month

- "What should I do after a car accident?"

- "Can my landlord evict me without notice?"### Production Deployment

- "What constitutes workplace harassment?"For production use:

1. Use WSGI server (Gunicorn)

## ⚠️ Legal Disclaimer2. Set up SSL certificate

3. Configure proper logging

This software provides general legal information only and does not constitute legal advice. Laws vary by jurisdiction and circumstances. Users should consult with qualified attorneys for advice specific to their legal situations.4. Set up monitoring

5. Use environment variables for API keys

## 📄 License

## 🔒 Security & Legal

MIT License - see [LICENSE](LICENSE) file for details.- **Confidentiality**: Conversations are not stored

- **Legal Disclaimer**: Provides information, not legal advice

## 🤝 Contributing- **Data Privacy**: No personal data collection

- **Secure API**: HTTPS recommended for production

1. Fork the repository

2. Create a feature branch## 🤝 Usage Guidelines

3. Make your changes- **Information Only**: This provides legal information, not legal advice

4. Submit a pull request- **Consult Attorneys**: For specific legal matters, consult qualified attorneys

- **Educational Purpose**: Use for learning and general guidance

## 📞 Support- **No Liability**: AI responses should not replace professional legal counsel



For issues or questions:## 🛠️ Troubleshooting

- Open an issue on GitHub

- Check the extension installation guide in `EXTENSION_INSTALLATION_GUIDE.md`### Common Issues

1. **"Technical difficulties" error**: Update Gemini model names in config

---2. **API Key issues**: Verify key is correct and has quota

3. **Port conflicts**: Change port in `config.py`

**Built with ❤️ to make legal help accessible to everyone**4. **Import errors**: Run `pip install -r requirements.txt`

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