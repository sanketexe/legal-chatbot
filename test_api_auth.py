"""
Test script for API authentication and rate limiting
"""
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv('API_SECRET_KEY')
BASE_URL = "http://localhost:5000"

def test_without_api_key():
    """Test chat endpoint WITHOUT API key - should return 401"""
    print("\n🧪 Test 1: Chat without API key (expect 401)...")
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={"message": "test"},
        headers={"Content-Type": "application/json"}
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 401, "Expected 401 Unauthorized"
    print("   ✅ PASSED: Correctly rejected request without API key")

def test_with_invalid_api_key():
    """Test chat endpoint with INVALID API key - should return 403"""
    print("\n🧪 Test 2: Chat with invalid API key (expect 403)...")
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={"message": "test"},
        headers={
            "Content-Type": "application/json",
            "X-API-Key": "invalid-key-12345"
        }
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 403, "Expected 403 Forbidden"
    print("   ✅ PASSED: Correctly rejected invalid API key")

def test_with_valid_api_key():
    """Test chat endpoint with VALID API key - should work"""
    print("\n🧪 Test 3: Chat with valid API key (expect 200)...")
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={"message": "What is Indian law?"},
        headers={
            "Content-Type": "application/json",
            "X-API-Key": API_KEY
        }
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Bot Response: {data.get('bot_response', 'No response')[:100]}...")
        print("   ✅ PASSED: Successfully authenticated and got response")
    else:
        print(f"   Response: {response.json()}")

def test_rate_limiting():
    """Test rate limiting - should hit 10/minute limit"""
    print("\n🧪 Test 4: Rate limiting (expect 429 after 10 requests)...")
    for i in range(12):
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": f"test {i}"},
            headers={
                "Content-Type": "application/json",
                "X-API-Key": API_KEY
            }
        )
        if response.status_code == 429:
            print(f"   ⏱️  Hit rate limit at request #{i + 1}")
            print(f"   Response: {response.json() if response.headers.get('content-type') == 'application/json' else response.text}")
            print("   ✅ PASSED: Rate limiting works correctly")
            return
        elif i < 10:
            print(f"   Request #{i + 1}: {response.status_code}")
    
    print("   ⚠️  WARNING: Did not hit rate limit after 12 requests")

if __name__ == "__main__":
    print("=" * 60)
    print("🔐 API AUTHENTICATION & RATE LIMITING TESTS")
    print("=" * 60)
    print(f"Testing against: {BASE_URL}")
    print(f"API Key: {API_KEY[:20]}... (truncated)")
    
    try:
        # Test 1: No API key
        test_without_api_key()
        
        # Test 2: Invalid API key
        test_with_invalid_api_key()
        
        # Test 3: Valid API key
        test_with_valid_api_key()
        
        # Test 4: Rate limiting
        test_rate_limiting()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to server")
        print("   Make sure the Flask app is running on http://localhost:5000")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
