#!/usr/bin/env python
"""
Test script for UserPreference endpoints
Run: python test_preferences_api.py
"""

import requests
import json
from urllib.parse import urljoin

# Configuration
BASE_URL = "http://localhost:5000"
TEST_USERNAME = "testuser"
TEST_PASSWORD = "password123"

class PreferencesAPITester:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.token = None
        self.headers = {'Content-Type': 'application/json'}
    
    def _make_request(self, method, endpoint, data=None, expect_status=None):
        """Make HTTP request and return response"""
        url = urljoin(self.base_url, endpoint)
        headers = self.headers.copy()
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            print(f"  → {method} {endpoint}")
            print(f"    Status: {response.status_code}")
            
            if response.status_code != 200 and expect_status and response.status_code != expect_status:
                print(f"    ⚠️  Expected {expect_status}, got {response.status_code}")
            
            # Try to parse JSON response
            try:
                result = response.json()
                return result, response.status_code
            except:
                return response.text, response.status_code
        
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return None, None
    
    def login(self, username=TEST_USERNAME, password=TEST_PASSWORD):
        """Login and get token"""
        print(f"\n1️⃣  LOGGING IN as '{username}'")
        
        data = {
            'username': username,
            'password': password
        }
        
        result, status = self._make_request('POST', '/api/auth/login', data)
        
        if result and isinstance(result, dict) and 'token' in result:
            self.token = result['token']
            print(f"    ✅ Got token: {self.token[:20]}...")
            return True
        elif result and isinstance(result, dict) and 'access_token' in result:
            self.token = result['access_token']
            print(f"    ✅ Got token: {self.token[:20]}...")
            return True
        else:
            print(f"    ❌ Login failed")
            print(f"    Response: {result}")
            return False
    
    def test_get_preferences(self):
        """Test GET /api/user/preferences"""
        print(f"\n2️⃣  GET USER PREFERENCES")
        
        result, status = self._make_request('GET', '/api/user/preferences')
        
        if result and isinstance(result, dict) and 'data' in result:
            print(f"    ✅ Got preferences:")
            for key, value in result['data'].items():
                print(f"       • {key}: {value}")
            return result['data']
        else:
            print(f"    ❌ Failed to get preferences")
            print(f"    Response: {result}")
            return None
    
    def test_update_language(self):
        """Test PUT /api/user/preferences with language change"""
        print(f"\n3️⃣  UPDATE LANGUAGE PREFERENCE")
        
        data = {
            'preferred_language': 'hi'
        }
        
        result, status = self._make_request('PUT', '/api/user/preferences', data)
        
        if result and isinstance(result, dict) and 'data' in result:
            print(f"    ✅ Language updated:")
            print(f"       • preferred_language: {result['data'].get('preferred_language')}")
            return True
        else:
            print(f"    ❌ Failed to update language")
            print(f"    Response: {result}")
            return False
    
    def test_update_detail_level(self):
        """Test PUT /api/user/preferences with detail level"""
        print(f"\n4️⃣  UPDATE DETAIL LEVEL")
        
        data = {
            'response_detail_level': 4
        }
        
        result, status = self._make_request('PUT', '/api/user/preferences', data)
        
        if result and isinstance(result, dict) and 'data' in result:
            print(f"    ✅ Detail level updated:")
            print(f"       • response_detail_level: {result['data'].get('response_detail_level')}")
            return True
        else:
            print(f"    ❌ Failed to update detail level")
            print(f"    Response: {result}")
            return False
    
    def test_update_jurisdiction(self):
        """Test PUT /api/user/preferences with jurisdiction"""
        print(f"\n5️⃣  UPDATE JURISDICTION PREFERENCE")
        
        data = {
            'jurisdiction_preference': 'delhi'
        }
        
        result, status = self._make_request('PUT', '/api/user/preferences', data)
        
        if result and isinstance(result, dict) and 'data' in result:
            print(f"    ✅ Jurisdiction updated:")
            print(f"       • jurisdiction_preference: {result['data'].get('jurisdiction_preference')}")
            return True
        else:
            print(f"    ❌ Failed to update jurisdiction")
            print(f"    Response: {result}")
            return False
    
    def test_update_legal_domains(self):
        """Test PUT /api/user/preferences with legal domains"""
        print(f"\n6️⃣  UPDATE LEGAL DOMAINS")
        
        data = {
            'legal_domains': {
                'family': 0.8,
                'property': 0.6,
                'criminal': 0.3
            }
        }
        
        result, status = self._make_request('PUT', '/api/user/preferences', data)
        
        if result and isinstance(result, dict) and 'data' in result:
            print(f"    ✅ Legal domains updated:")
            print(f"       • legal_domains: {result['data'].get('legal_domains')}")
            return True
        else:
            print(f"    ❌ Failed to update legal domains")
            print(f"    Response: {result}")
            return False
    
    def test_get_single_field(self):
        """Test GET /api/user/preferences/<field>"""
        print(f"\n7️⃣  GET SINGLE PREFERENCE FIELD")
        
        result, status = self._make_request('GET', '/api/user/preferences/preferred_language')
        
        if result and isinstance(result, dict) and 'value' in result:
            print(f"    ✅ Got field value:")
            print(f"       • field: {result.get('field')}")
            print(f"       • value: {result.get('value')}")
            return True
        else:
            print(f"    ❌ Failed to get field")
            print(f"    Response: {result}")
            return False
    
    def test_verify_persistence(self):
        """Test that preferences persist after updates"""
        print(f"\n8️⃣  VERIFY PERSISTENCE")
        
        result, status = self._make_request('GET', '/api/user/preferences')
        
        if result and isinstance(result, dict) and 'data' in result:
            data = result['data']
            all_correct = (
                data.get('preferred_language') == 'hi' and
                data.get('response_detail_level') == 4 and
                data.get('jurisdiction_preference') == 'delhi'
            )
            
            if all_correct:
                print(f"    ✅ All preferences persisted correctly:")
                print(f"       • preferred_language: {data.get('preferred_language')} ✓")
                print(f"       • response_detail_level: {data.get('response_detail_level')} ✓")
                print(f"       • jurisdiction_preference: {data.get('jurisdiction_preference')} ✓")
                return True
            else:
                print(f"    ⚠️  Some preferences not persisted:")
                print(f"       • preferred_language: {data.get('preferred_language')} (expected: hi)")
                print(f"       • response_detail_level: {data.get('response_detail_level')} (expected: 4)")
                print(f"       • jurisdiction_preference: {data.get('jurisdiction_preference')} (expected: delhi)")
                return False
        else:
            print(f"    ❌ Failed to verify preferences")
            print(f"    Response: {result}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("=" * 70)
        print("USER PREFERENCES API TEST SUITE")
        print("=" * 70)
        
        results = {
            'login': self.login(),
            'get_preferences': self.test_get_preferences() is not None,
            'update_language': self.test_update_language(),
            'update_detail_level': self.test_update_detail_level(),
            'update_jurisdiction': self.test_update_jurisdiction(),
            'update_legal_domains': self.test_update_legal_domains(),
            'get_single_field': self.test_get_single_field(),
            'verify_persistence': self.test_verify_persistence(),
        }
        
        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status:8s} • {test_name}")
        
        print(f"\n📊 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n⚠️  {total - passed} tests failed")
        
        print("=" * 70)
        
        return passed == total


if __name__ == '__main__':
    tester = PreferencesAPITester()
    success = tester.run_all_tests()
    
    import sys
    sys.exit(0 if success else 1)
