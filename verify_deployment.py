#!/usr/bin/env python3
"""
Quick Deployment Script for Vercel
Validates environment and provides deployment checklist
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_env_var(var_name, description):
    """Check if environment variable is set"""
    value = os.getenv(var_name)
    if value:
        # Hide sensitive values
        if 'KEY' in var_name or 'PASSWORD' in var_name:
            display_value = value[:8] + '...' if len(value) > 8 else '***'
        else:
            display_value = value[:50] + '...' if len(value) > 50 else value
        print(f"✅ {var_name}: {display_value}")
        return True
    else:
        print(f"❌ {var_name}: NOT SET - {description}")
        return False

def main():
    print("=" * 70)
    print("🚀 LEGAL CHATBOT - VERCEL DEPLOYMENT VALIDATOR")
    print("=" * 70)
    print()
    
    all_checks_passed = True
    
    # Database Configuration
    print("📦 DATABASE CONFIGURATION")
    print("-" * 70)
    all_checks_passed &= check_env_var('DATABASE_URL', 'PostgreSQL connection string')
    print()
    
    # Pinecone Configuration
    print("🌲 PINECONE VECTOR DATABASE")
    print("-" * 70)
    all_checks_passed &= check_env_var('PINECONE_API_KEY', 'Pinecone API key')
    all_checks_passed &= check_env_var('PINECONE_INDEX_NAME', 'Pinecone index name')
    all_checks_passed &= check_env_var('PINECONE_REGION', 'Pinecone region')
    print()
    
    # Gemini AI Configuration
    print("🤖 GEMINI AI CONFIGURATION")
    print("-" * 70)
    all_checks_passed &= check_env_var('GEMINI_API_KEY', 'Google Gemini API key')
    check_env_var('GEMINI_MODEL', 'Gemini model name (optional)')
    print()
    
    # Security Configuration
    print("🔐 SECURITY CONFIGURATION")
    print("-" * 70)
    all_checks_passed &= check_env_var('API_SECRET_KEY', 'API authentication key')
    all_checks_passed &= check_env_var('SECRET_KEY', 'Flask secret key')
    print()
    
    # Application Settings
    print("⚙️  APPLICATION SETTINGS")
    print("-" * 70)
    check_env_var('PREFERRED_AI_PROVIDER', 'AI provider (should be "gemini")')
    check_env_var('DEBUG', 'Debug mode (should be "False" for production)')
    print()
    
    # Summary
    print("=" * 70)
    if all_checks_passed:
        print("✅ ALL REQUIRED ENVIRONMENT VARIABLES ARE SET!")
        print()
        print("📋 DEPLOYMENT CHECKLIST:")
        print("=" * 70)
        print()
        print("Step 1: Create Vercel Project")
        print("  1. Go to https://vercel.com/new")
        print("  2. Import your GitHub repository")
        print("  3. Framework preset: Other")
        print("  4. Click 'Deploy'")
        print()
        print("Step 2: Set Environment Variables in Vercel")
        print("  Go to: Project Settings → Environment Variables")
        print("  Add ALL the variables shown above ✅")
        print()
        print("Step 3: Redeploy")
        print("  After adding env vars, click 'Redeploy'")
        print()
        print("Step 4: Test Deployment")
        print("  Test your endpoints:")
        print("  - Health: https://your-app.vercel.app/api/health")
        print("  - Chat: Include X-API-Key header")
        print()
        print("🎉 You're ready to deploy!")
        print()
        print("📖 For detailed instructions, see: VERCEL_DEPLOYMENT_GUIDE.md")
        print("=" * 70)
        return 0
    else:
        print("❌ SOME REQUIRED ENVIRONMENT VARIABLES ARE MISSING!")
        print()
        print("Please set the missing variables in your .env file")
        print("Refer to .env.example or VERCEL_DEPLOYMENT_GUIDE.md for details")
        print("=" * 70)
        return 1

if __name__ == '__main__':
    sys.exit(main())
