# LegalAssist Pro - Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env` and update with your API keys:
```bash
cp .env.example .env
```

Edit `.env`:
```env
GEMINI_API_KEY=your_api_key_here
GOOGLE_API_KEY=your_api_key_here
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret
```

### 3. Run the Application
```bash
python run.py
```

Visit: http://localhost:5000

## Getting API Keys

### Google Gemini API Key
1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key (starts with `AIzaSy...`)

## Default Admin Account

After first run, use these credentials:
- Username: `admin`
- Password: `admin123`

**Important**: Change the password after first login!

## Troubleshooting

### Database Issues
If you encounter database errors, delete the database and restart:
```bash
rm legal_chatbot.db
python run.py
```

### API Key Issues
Verify your API key is correctly set in `.env` file and has no extra spaces.

### Port Already in Use
Change the port in `.env`:
```env
PORT=8000
```

## Production Deployment

For production, use a WSGI server:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Features

- AI-powered legal consultation
- Document analysis (PDF, DOCX, TXT)
- Case law citations
- Hindi language support
- User authentication
- Chat history
- Response ratings

## Support

For issues or questions, refer to README.md or contact support.
