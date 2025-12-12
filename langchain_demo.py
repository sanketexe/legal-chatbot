"""
LangChain Legal Assistant Demo
Demonstrates enhanced capabilities with LangChain integration
"""

import requests
import json
import time
from typing import Dict, Any

class LangChainLegalDemo:
    """Demo client for LangChain Legal Assistant"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def check_status(self) -> Dict[str, Any]:
        """Check LangChain integration status"""
        try:
            response = self.session.get(f"{self.base_url}/api/langchain/status")
            return response.json()
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    def enhanced_chat(self, message: str) -> Dict[str, Any]:
        """Send message to enhanced LangChain chat"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/langchain/chat",
                json={"message": message}
            )
            return response.json()
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    def analyze_document_text(self, content: str, query: str = "Analyze this legal document") -> Dict[str, Any]:
        """Analyze document content with LangChain"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/langchain/document/analyze",
                json={"content": content, "query": query}
            )
            return response.json()
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    def research_case_law(self, query: str) -> Dict[str, Any]:
        """Research case law using LangChain"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/langchain/research/case-law",
                json={"query": query}
            )
            return response.json()
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    def get_legal_advice(self, query: str) -> Dict[str, Any]:
        """Get comprehensive legal advice"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/langchain/advice",
                json={"query": query}
            )
            return response.json()
        except Exception as e:
            return {"error": str(e), "status": "error"}

def demo_enhanced_features():
    """Demonstrate LangChain enhanced features"""
    print("🔗 LangChain Legal Assistant Demo")
    print("=" * 60)
    
    # Initialize demo client
    demo = LangChainLegalDemo()
    
    # Check status
    print("📊 Checking LangChain Status...")
    status = demo.check_status()
    print(f"Status: {status}")
    print()
    
    if status.get("status") == "error":
        print("❌ LangChain not available. Please:")
        print("1. Run: python setup_langchain.py")
        print("2. Restart your application")
        print("3. Ensure Gemini API key is configured")
        return
    
    print("✅ LangChain is ready!")
    print()
    
    # Demo 1: Enhanced Legal Chat
    print("🤖 Demo 1: Enhanced Legal Chat with Memory")
    print("-" * 40)
    
    legal_questions = [
        "What are the essential elements of a valid contract?",
        "Can you explain breach of contract remedies?",
        "What about the contract we just discussed - what are the damages?"
    ]
    
    for i, question in enumerate(legal_questions, 1):
        print(f"Question {i}: {question}")
        response = demo.enhanced_chat(question)
        
        if response.get("status") == "success":
            print(f"Answer: {response['response'][:200]}...")
            if response.get('sources'):
                print(f"Sources: {len(response['sources'])} legal references found")
        else:
            print(f"Error: {response.get('error')}")
        
        print()
        time.sleep(1)  # Avoid rate limiting
    
    # Demo 2: Document Analysis
    print("📄 Demo 2: Document Analysis")
    print("-" * 40)
    
    sample_contract = """
    EMPLOYMENT AGREEMENT
    
    This Employment Agreement is made between ABC Company and John Doe.
    
    1. Position: Software Developer
    2. Salary: $75,000 per year
    3. Term: 2 years from start date
    4. Confidentiality: Employee agrees to maintain confidentiality
    5. Termination: Either party may terminate with 30 days notice
    
    The employee agrees to work exclusively for the company during employment.
    """
    
    print("Analyzing sample employment contract...")
    analysis = demo.analyze_document_text(
        sample_contract,
        "What are the key terms and potential issues in this employment agreement?"
    )
    
    if analysis.get("status") == "success":
        print(f"Analysis: {analysis['analysis'][:300]}...")
    else:
        print(f"Error: {analysis.get('error')}")
    
    print()
    
    # Demo 3: Case Law Research
    print("⚖️ Demo 3: Case Law Research")
    print("-" * 40)
    
    print("Researching contract law precedents...")
    research = demo.research_case_law("breach of contract remedies Indian law")
    
    if research.get("status") == "success":
        print(f"Research Results: {research['research'][:300]}...")
    else:
        print(f"Error: {research.get('error')}")
    
    print()
    
    # Demo 4: Comprehensive Legal Advice
    print("💡 Demo 4: Comprehensive Legal Advice")
    print("-" * 40)
    
    print("Getting comprehensive advice on employment law...")
    advice = demo.get_legal_advice(
        "I want to start a tech company in India. What legal considerations should I be aware of?"
    )
    
    if advice.get("status") == "success":
        print(f"Legal Advice: {advice['advice'][:400]}...")
    else:
        print(f"Error: {advice.get('error')}")
    
    print()
    print("=" * 60)
    print("🎉 LangChain Demo Complete!")
    print()
    print("Key Benefits Demonstrated:")
    print("✅ Enhanced conversation memory")
    print("✅ Source-referenced responses")
    print("✅ Advanced document analysis")
    print("✅ Specialized case law research")
    print("✅ Comprehensive legal guidance")

if __name__ == "__main__":
    demo_enhanced_features()