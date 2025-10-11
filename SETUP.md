# Deployment & Setup Guide

## 🚀 Quick Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Gemini API key in .env file
GEMINI_API_KEY=your_api_key_here

# 3. Run the application
python simple_app.py

# 4. Open browser to http://localhost:5000
```

## 🌐 Get Free Gemini API Key
1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Create new API key
4. Add to `.env` file

## 📱 Browser Extension Setup
1. Open Chrome/Firefox Extensions page
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `browser_extension` folder
5. Pin extension to toolbar

## ☁️ AWS Deployment Options

### Option 1: Elastic Beanstalk (Easiest)
- Upload project as ZIP file
- Auto-scaling and load balancing
- Cost: ~$10-30/month

### Option 2: Lambda (Serverless)
- Modify for serverless architecture
- Pay per request
- Cost: ~$1-10/month

### Option 3: EC2 (Full Control)
- Launch t3.micro instance
- Install Python and dependencies
- Cost: ~$8-15/month

## 🔧 Production Checklist
- [ ] Use WSGI server (Gunicorn)
- [ ] Set up SSL certificate
- [ ] Configure environment variables
- [ ] Set up monitoring
- [ ] Configure proper logging
- [ ] Set up backup procedures

## 🛠️ Troubleshooting
- **API Error**: Check Gemini API key and quota
- **Port 5000 in use**: Change port in config.py
- **Import errors**: Run `pip install -r requirements.txt`
- **Performance issues**: Consider using production WSGI server