import os
import google.generativeai as genai
from typing import List, Dict, Any
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Import configuration
sys_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys
sys.path.append(sys_path)
from config import Config

class LegalReasoningEngine:
    """
    Simple legal reasoning engine for legal assistance.
    """
    
    def __init__(self):
        """Initialize the legal reasoning engine"""
        # Get configuration
        self.config = Config()
        self.active_provider = self.config.get_active_provider()
        
        # Initialize Gemini AI
        self._init_gemini()
        
        print(f"Legal Engine initialized with provider: {self.active_provider}")
    
    def _init_gemini(self):
        """Initialize Gemini client with automatic model detection"""
        if self.config.GEMINI_API_KEY:
            try:
                genai.configure(api_key=self.config.GEMINI_API_KEY)
                
                # Try to get available models and find the best one
                try:
                    models = genai.list_models()
                    available_models = []
                    for model in models:
                        if 'generateContent' in model.supported_generation_methods:
                            available_models.append(model.name)
                    
                    # Preferred model order (updated with current available models)
                    preferred_models = [
                        'models/gemini-2.5-flash',
                        'models/gemini-2.5-pro',
                        'models/gemini-2.0-flash',
                        'models/gemini-flash-latest',
                        'models/gemini-pro-latest'
                    ]
                    
                    # Find the first available preferred model
                    selected_model = None
                    for preferred in preferred_models:
                        if preferred in available_models:
                            selected_model = preferred
                            break
                    
                    if not selected_model and available_models:
                        selected_model = available_models[0]  # Use first available
                    
                    if selected_model:
                        self.gemini_model = genai.GenerativeModel(selected_model)
                        print(f"✅ Gemini AI initialized with model: {selected_model}")
                    else:
                        print(f"⚠️ No compatible Gemini models found - using fallback mode")
                        self.gemini_model = None
                        
                except Exception as model_error:
                    # Fallback to default model name
                    try:
                        self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
                        print(f"✅ Gemini AI initialized with fallback model: gemini-2.5-flash")
                    except:
                        try:
                            self.gemini_model = genai.GenerativeModel('gemini-flash-latest')
                            print(f"✅ Gemini AI initialized with latest flash model")
                        except:
                            print(f"⚠️ Gemini model initialization failed: {model_error}")
                            self.gemini_model = None
                        
            except Exception as e:
                print(f"⚠️ Gemini API configuration failed: {e}")
                self.gemini_model = None
        else:
            print(f"⚠️ No Gemini API key found - using fallback mode")
            self.gemini_model = None

    def get_legal_response(self, user_query: str, chat_history: List[Dict], user_context: Dict[str, Any]) -> str:
        """
        Generate a legal response based on user query
        """
        try:
            # Enhanced system prompt for better formatting
            system_prompt = """You are a helpful legal assistant AI. You provide legal information and guidance, but NOT legal advice.

CRITICAL FORMATTING RULES FOR READABILITY:

1. **Use plenty of white space** - Add blank lines between sections
2. **Start with a clear summary** in 1-2 sentences
3. **Use section headers** with clear formatting
4. **Break up dense text** into digestible chunks
5. **Use bullet points and numbered lists** frequently
6. **Bold key terms** and important points

REQUIRED RESPONSE STRUCTURE:

📋 **Quick Answer:**
[1-2 sentence summary]

🔍 **Detailed Explanation:**
[Main content with clear paragraphs and spacing]

⚖️ **Your Options:**
• Option 1: [Brief description]
• Option 2: [Brief description]
• Option 3: [Brief description]

📞 **Next Steps:**
1. [First action]
2. [Second action]
3. [Third action]

⚠️ **Important Notes:**
[Key warnings or considerations]

Make responses scannable and easy to read. Use emojis for section headers. Break up long paragraphs. Use spacing generously."""

            # Prepare conversation
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add recent chat history (last 10 messages)
            recent_history = chat_history[-10:] if len(chat_history) > 10 else chat_history
            for message in recent_history:
                if message["role"] in ["user", "assistant"]:
                    messages.append({
                        "role": message["role"],
                        "content": message["content"]
                    })
            
            # Add current query
            messages.append({"role": "user", "content": user_query})
            
            # Generate response
            if self.active_provider == 'gemini' and self.gemini_model:
                response = self._get_gemini_response(messages)
            else:
                response = self._get_fallback_response(user_query)
            
            # Add disclaimer
            response = self._add_disclaimer(response)
            
            return response
            
        except Exception as e:
            return f"I apologize, but I encountered an error while processing your legal question. Error: {str(e)}\\n\\nFor urgent legal matters, please consult with a qualified attorney immediately."

    def _get_gemini_response(self, messages: List[Dict]) -> str:
        """Get response from Google Gemini API"""
        try:
            # Check if Gemini model is available
            if not self.gemini_model:
                return "I'm currently unable to access the Gemini AI service. Using fallback mode."
            
            # Convert messages to Gemini format
            prompt_parts = []
            for msg in messages:
                if msg["role"] == "system":
                    prompt_parts.append(f"System: {msg['content']}")
                elif msg["role"] == "user":
                    prompt_parts.append(f"User: {msg['content']}")
                elif msg["role"] == "assistant":
                    prompt_parts.append(f"Assistant: {msg['content']}")
            
            full_prompt = "\\n\\n".join(prompt_parts)
            
            response = self.gemini_model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=self.config.GEMINI_MAX_TOKENS,
                    temperature=self.config.GEMINI_TEMPERATURE,
                )
            )
            
            if response.text:
                return response.text
            else:
                return "I received an empty response from the AI service. Please try rephrasing your question."
            
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                return f"The Gemini AI model is currently unavailable. Please try again later."
            else:
                return f"I'm experiencing technical difficulties. Please try again later."

    def _get_fallback_response(self, user_query: str) -> str:
        """Provide fallback response when AI is not available"""
        return f'''📋 **Quick Answer:**
I'm currently unable to access the AI service, but I can provide general guidance for your question: "{user_query}"

🔍 **General Legal Guidance:**

**For Most Legal Issues:**
• Contact your local bar association for lawyer referrals
• Check if you qualify for legal aid services  
• Research using reliable legal resources
• Consider consulting with a qualified attorney

**For Criminal Matters:**
• Exercise your right to remain silent
• Request an attorney immediately
• Do not provide statements without legal representation
• Contact a criminal defense attorney

**For Civil Issues:**
• Document all relevant information
• Keep records of all communications
• Research applicable laws and regulations
• Consider mediation before litigation

📞 **Emergency Resources:**
1. **Immediate Danger**: Contact emergency services (911)
2. **Legal Aid Hotlines**: Search "[your state] legal aid"
3. **Court Information**: Contact the court clerk for procedures
4. **Bar Association**: Find local attorney referrals

⚠️ **Important Notes:**
This is general information only. Every legal situation is unique and requires professional analysis.'''

    def _add_disclaimer(self, response: str) -> str:
        """Add legal disclaimer to response"""
        if "legal advice" not in response.lower() and "disclaimer" not in response.lower():
            disclaimer = "\n\n---\n\n🚨 **Legal Disclaimer**\n\nThis information is for educational purposes only and does not constitute legal advice. Laws vary by jurisdiction and circumstances. \n\n**Please consult with a qualified attorney** for advice specific to your situation."
            response += disclaimer
        
        return response