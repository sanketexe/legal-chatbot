# Simple Configuration for Legal Chatbot
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Simple configuration for the Legal Assistant"""
    
    # API Keys - Only Gemini (free tier available)
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyAQMIOI9h0RJgnABVA1P1oX7tbaYUEe8lw')
    
    # AI Provider Settings (simplified)
    PREFERRED_AI_PROVIDER = 'gemini'  # Only gemini or fallback
    
    # Gemini Settings (updated with current available models)
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
    GEMINI_MAX_TOKENS = 1000
    GEMINI_TEMPERATURE = 0.7
    
    # Application Settings
    SECRET_KEY = 'legal-chatbot-secret'
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5000
    
    @classmethod
    def get_available_providers(cls):
        """Get list of available AI providers"""
        providers = []
        if cls.GEMINI_API_KEY:
            providers.append('gemini')
        providers.append('fallback')  # Always available
        return providers
    
    @classmethod
    def get_active_provider(cls):
        """Get the currently active AI provider"""
        if cls.GEMINI_API_KEY:
            return 'gemini'
        else:
            return 'fallback'