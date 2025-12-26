#!/usr/bin/env python3
"""
Interactive Demo: Enhanced Conversation Memory
Demonstrates the session-based memory system in the LegalChatbot.
"""

import time
from datetime import datetime

def demo_conversation_memory():
    """Interactive demonstration of conversation memory"""
    print("🤖 Legal Chatbot - Enhanced Conversation Memory Demo")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%B %d, %Y')}")
    print()
    print("This demo shows how the legal assistant maintains context")
    print("across different conversation sessions.")
    print()
    
    try:
        from langchain_legal_assistant import ModernLegalAssistant
        assistant = ModernLegalAssistant()
        
        print("✅ Legal Assistant loaded successfully")
        print()
        
        # Scenario 1: Legal Consultation Session
        print("🏛️ SCENARIO 1: Property Law Consultation")
        print("-" * 40)
        session_1 = "property_consultation"
        
        print("👤 Client: I need help with property inheritance laws")
        response_1a = assistant.chat(
            "I need help with property inheritance laws in India", 
            session_id=session_1
        )
        print(f"🤖 Assistant: {response_1a[:200]}...")
        print()
        
        time.sleep(1)  # Brief pause for readability
        
        print("👤 Client: What about joint property with my spouse?")
        response_1b = assistant.chat(
            "What about joint property ownership with my spouse?", 
            session_id=session_1
        )
        print(f"🤖 Assistant: {response_1b[:200]}...")
        print()
        
        # Show memory stats for session 1
        stats_1 = assistant.get_session_stats(session_1)
        print(f"💾 Session Memory: {stats_1['user_messages']} questions, {stats_1['assistant_messages']} responses")
        print()
        
        # Scenario 2: Criminal Law Session
        print("⚖️ SCENARIO 2: Criminal Law Consultation")
        print("-" * 40)
        session_2 = "criminal_consultation"
        
        print("👤 Client: I need advice on detention laws")
        response_2a = assistant.chat(
            "I need advice on detention laws under Article 22", 
            session_id=session_2
        )
        print(f"🤖 Assistant: {response_2a[:200]}...")
        print()
        
        time.sleep(1)
        
        print("👤 Client: What are the safeguards against arbitrary detention?")
        response_2b = assistant.chat(
            "What are the safeguards against arbitrary detention?", 
            session_id=session_2
        )
        print(f"🤖 Assistant: {response_2b[:200]}...")
        print()
        
        # Show memory stats for session 2
        stats_2 = assistant.get_session_stats(session_2)
        print(f"💾 Session Memory: {stats_2['user_messages']} questions, {stats_2['assistant_messages']} responses")
        print()
        
        # Demonstrate Context Isolation
        print("🔄 SCENARIO 3: Context Isolation Test")
        print("-" * 40)
        
        print("👤 Returning to Property Session: Tell me more about the documentation")
        response_3a = assistant.chat(
            "Tell me more about the documentation needed", 
            session_id=session_1  # Back to property session
        )
        print(f"🤖 Assistant (Property Context): {response_3a[:200]}...")
        print()
        
        print("👤 Returning to Criminal Session: What about bail procedures?")
        response_3b = assistant.chat(
            "What about bail procedures in detention cases?", 
            session_id=session_2  # Back to criminal session
        )
        print(f"🤖 Assistant (Criminal Context): {response_3b[:200]}...")
        print()
        
        # Final Memory Summary
        print("📊 FINAL MEMORY SUMMARY")
        print("-" * 40)
        
        # Get complete memory for both sessions
        memory_1 = assistant.get_session_memory(session_1)
        memory_2 = assistant.get_session_memory(session_2)
        
        print(f"🏠 Property Session ({session_1}):")
        print(f"   📝 Total messages: {len(memory_1)}")
        print(f"   💬 Last topic: Property documentation")
        
        print(f"⚖️ Criminal Session ({session_2}):")
        print(f"   📝 Total messages: {len(memory_2)}")
        print(f"   💬 Last topic: Bail procedures")
        print()
        
        # Demonstrate Memory Management
        print("🧹 MEMORY MANAGEMENT DEMO")
        print("-" * 40)
        
        print("🗑️ Clearing property session memory...")
        assistant.clear_session_memory(session_1)
        
        cleared_stats = assistant.get_session_stats(session_1)
        retained_stats = assistant.get_session_stats(session_2)
        
        print(f"✅ Property session: {cleared_stats['total_messages']} messages (cleared)")
        print(f"✅ Criminal session: {retained_stats['total_messages']} messages (retained)")
        print()
        
        # Key Benefits Summary
        print("🎯 KEY BENEFITS DEMONSTRATED")
        print("-" * 40)
        print("✅ Context Awareness: Assistant remembers conversation history")
        print("✅ Session Isolation: Different topics in separate sessions")
        print("✅ Memory Management: Clear sessions individually")
        print("✅ Scalability: Handle multiple concurrent consultations")
        print("✅ Persistence: Memory can be restored from database")
        print()
        
        print("🎉 Conversation Memory Demo Complete!")
        print("💡 The legal assistant now provides contextual responses")
        print("   while maintaining separation between different consultations.")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = demo_conversation_memory()
    print()
    if success:
        print("🎊 Demo completed successfully!")
    else:
        print("⚠️ Demo encountered issues - check the output above")