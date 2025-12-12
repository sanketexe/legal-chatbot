"""
LangChain Setup Script for Legal Chatbot
Installs and configures LangChain dependencies
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a Python package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False

def main():
    print("🔗 Setting up LangChain for Legal Chatbot")
    print("=" * 50)
    
    # LangChain packages
    packages = [
        "langchain==0.1.0",
        "langchain-community==0.0.13", 
        "langchain-core==0.1.10",
        "langchain-google-genai==0.0.6",
        "langchain-text-splitters==0.0.1",
        "langchain-chroma==0.1.0",
        "pypdf==3.17.4",
        "tiktoken==0.5.2",
        "faiss-cpu==1.7.4",
        "sentence-transformers",
        "transformers",
        "torch"
    ]
    
    print(f"📦 Installing {len(packages)} packages...")
    print()
    
    failed_packages = []
    
    for package in packages:
        print(f"Installing {package}...", end=" ")
        if install_package(package):
            print("✅")
        else:
            print("❌")
            failed_packages.append(package)
    
    print()
    print("=" * 50)
    
    if failed_packages:
        print("❌ Some packages failed to install:")
        for package in failed_packages:
            print(f"  - {package}")
        print()
        print("You can try installing them manually:")
        print(f"pip install {' '.join(failed_packages)}")
    else:
        print("✅ All LangChain packages installed successfully!")
        print()
        print("🚀 LangChain is now ready for your Legal Chatbot!")
        print()
        print("Next steps:")
        print("1. Restart your application")
        print("2. Access LangChain features at /api/langchain/")
        print("3. Upload legal documents for enhanced analysis")
    
    print()
    print("📚 LangChain Endpoints:")
    print("  - POST /api/langchain/chat - Enhanced AI chat")
    print("  - POST /api/langchain/document/upload - Process documents")
    print("  - POST /api/langchain/document/analyze - Analyze document content")
    print("  - POST /api/langchain/research/case-law - Research legal precedents")
    print("  - GET /api/langchain/status - Check LangChain status")

if __name__ == "__main__":
    main()