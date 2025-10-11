# 🚀 LegalAssist Pro - Web App Deployment Guide

## 🎯 Deployment Options

### 1. 🌐 Vercel Deployment (Recommended - Free & Fast)

**Prerequisites:**
- GitHub account
- Vercel account (free at vercel.com)

**Steps:**

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/legalchatbot.git
   git push -u origin main
   ```

2. **Deploy on Vercel:**
   - Go to [vercel.com](https://vercel.com)
   - Click "Import Git Repository"
   - Select your GitHub repository
   - Vercel will auto-detect the configuration from `vercel.json`

3. **Environment Variables:**
   - In Vercel dashboard → Settings → Environment Variables
   - Add: `GEMINI_API_KEY` = your_google_api_key
   - Redeploy the project

4. **Custom Domain (Optional):**
   - In Vercel dashboard → Settings → Domains
   - Add your custom domain

**✅ Your app will be live at:** `https://your-project.vercel.app`

---

### 2. 🌈 Netlify Deployment (Alternative)

**Prerequisites:**
- GitHub account
- Netlify account (free at netlify.com)

**Steps:**

1. **Push to GitHub** (same as above)

2. **Deploy on Netlify:**
   - Go to [netlify.com](https://netlify.com)
   - Click "New site from Git"
   - Connect to GitHub and select repository
   - Build settings are auto-configured from `netlify.toml`

3. **Environment Variables:**
   - Site settings → Environment variables
   - Add: `GEMINI_API_KEY` = your_google_api_key

4. **Functions Setup:**
   - Netlify will automatically detect Python functions
   - Your Flask app runs as serverless function

**✅ Your app will be live at:** `https://your-project.netlify.app`

---

### 3. 🐳 Heroku Deployment (Free Tier)

**Prerequisites:**
- Heroku account
- Heroku CLI installed

**Steps:**

1. **Install Heroku CLI:**
   ```bash
   # Windows (using Chocolatey)
   choco install heroku-cli
   ```

2. **Login and Create App:**
   ```bash
   heroku login
   heroku create your-legalchatbot-app
   ```

3. **Set Environment Variables:**
   ```bash
   heroku config:set GEMINI_API_KEY=your_google_api_key
   ```

4. **Deploy:**
   ```bash
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

**✅ Your app will be live at:** `https://your-legalchatbot-app.herokuapp.com`

---

## ⚙️ Configuration Requirements

### Required Files (Already Created):
- ✅ `vercel.json` - Vercel configuration
- ✅ `netlify.toml` - Netlify configuration  
- ✅ `Procfile` - Heroku configuration
- ✅ `requirements.txt` - Python dependencies
- ✅ `simple_app.py` - Production-ready Flask app

### Environment Variables Needed:
```
GEMINI_API_KEY=your_google_gemini_api_key_here
```

### Dependencies (Auto-installed):
```
Flask==3.0.0
google-generativeai==0.8.3
python-dotenv==1.0.0
gunicorn==21.2.0
```

---

## 🔧 Post-Deployment Steps

1. **Test Your Deployment:**
   - Visit your deployed URL
   - Test the chat functionality
   - Verify AI responses work

2. **Update Browser Extension:**
   - Edit `browser_extension/simple_popup.js`
   - Replace `'https://your-app.vercel.app'` with your actual URL
   - Reinstall extension in browser

3. **Monitor Performance:**
   - Check deployment logs
   - Monitor response times
   - Set up error tracking if needed

---

## 🎉 You're Live!

Your legal chatbot is now accessible worldwide! Share your URL:
- **Vercel**: `https://your-project.vercel.app`
- **Netlify**: `https://your-project.netlify.app` 
- **Heroku**: `https://your-app.herokuapp.com`

## 📱 Next Steps:
- Deploy browser extension to Chrome Web Store
- Set up custom domain
- Add analytics tracking
- Implement user authentication (if needed)