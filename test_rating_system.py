"""
Test suite for User Rating System (Day 4)
Tests rating submission, statistics, and validation
"""

import unittest
import sys
import os
import json
from datetime import datetime

# Add paths
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app_with_db import app
from models import db, User, Message, ChatSession, ResponseRating

class TestRatingSystem(unittest.TestCase):
    """Test the rating system functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test client and database"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['JWT_SECRET_KEY'] = 'test-secret-key-for-ratings'
        cls.client = app.test_client()
        
        with app.app_context():
            db.create_all()
            print("\nOK: Test database created")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def setUp(self):
        """Create test user and login before each test"""
        with app.app_context():
            # Clear existing data
            ResponseRating.query.delete()
            Message.query.delete()
            ChatSession.query.delete()
            User.query.delete()
            db.session.commit()
        
        # Register new user via API
        reg_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        self.client.post('/api/auth/register', json=reg_data)
        
        # Login to get token
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post('/api/auth/login', json=login_data)
        data = json.loads(response.data)
        
        # Extract token
        if not data.get('success'):
            raise Exception(f"Login failed: {data}")
        
        self.token = data['access_token']
        self.headers = {'Authorization': f'Bearer {self.token}'}
        
        # Create test message
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            session = ChatSession(user_id=user.id)
            db.session.add(session)
            db.session.commit()
            
            message = Message(
                session_id=session.id,
                role='assistant',
                content='This is a test response about divorce law.',
                model_used='gemini-pro'
            )
            db.session.add(message)
            db.session.commit()
            
            self.user_id = user.id
            self.message_id = message.id
    
    def test_01_submit_rating(self):
        """Test submitting a valid rating"""
        response = self.client.post('/api/rate',
            headers=self.headers,
            json={
                'message_id': self.message_id,
                'rating': 5,
                'feedback': 'Excellent response!'
            })
        
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['status'], 'success')
        self.assertIn('rating', data)
        self.assertEqual(data['rating']['rating'], 5)
        self.assertEqual(data['rating']['feedback'], 'Excellent response!')
        
        print(f"OK: TEST 1: Submit rating - {data['rating']['rating']} stars")
    
    def test_02_rating_validation_low(self):
        """Test rating validation - value too low"""
        response = self.client.post('/api/rate',
            headers=self.headers,
            json={
                'message_id': self.message_id,
                'rating': 0  # Invalid: too low
            })
        
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['status'], 'error')
        self.assertIn('between 1 and 5', data['message'])
        
        print(f"OK: TEST 2: Rating validation (too low) - Rejected")
    
    def test_03_rating_validation_high(self):
        """Test rating validation - value too high"""
        response = self.client.post('/api/rate',
            headers=self.headers,
            json={
                'message_id': self.message_id,
                'rating': 6  # Invalid: too high
            })
        
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['status'], 'error')
        
        print(f"OK: TEST 3: Rating validation (too high) - Rejected")
    
    def test_04_update_existing_rating(self):
        """Test updating an existing rating"""
        # Submit initial rating
        self.client.post('/api/rate',
            headers=self.headers,
            json={'message_id': self.message_id, 'rating': 3, 'feedback': 'Good'})
        
        # Update rating
        response = self.client.post('/api/rate',
            headers=self.headers,
            json={'message_id': self.message_id, 'rating': 5, 'feedback': 'Actually excellent!'})
        
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')
        self.assertIn('updated', data['message'])
        self.assertEqual(data['rating']['rating'], 5)
        
        print(f"OK: TEST 4: Update rating - 3->5 stars")
    
    def test_05_get_rating_stats(self):
        """Test getting rating statistics"""
        # Submit multiple ratings
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            session = ChatSession.query.filter_by(user_id=user.id).first()
            
            # Create multiple messages and ratings
            for i, rating_value in enumerate([5, 4, 5, 3, 4]):
                msg = Message(
                    session_id=session.id,
                    role='assistant',
                    content=f'Test message {i}',
                    model_used='gemini-pro'
                )
                db.session.add(msg)
                db.session.flush()
                
                rating = ResponseRating(
                    user_id=user.id,
                    message_id=msg.id,
                    rating=rating_value
                )
                db.session.add(rating)
            
            db.session.commit()
        
        # Get stats
        response = self.client.get('/api/ratings/stats', headers=self.headers)
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['total_ratings'], 5)
        self.assertEqual(data['average_rating'], 4.2)  # (5+4+5+3+4)/5 = 4.2
        self.assertIn('distribution', data)
        
        print(f"OK: TEST 5: Get stats - {data['total_ratings']} ratings, avg {data['average_rating']}")
        print(f"   Distribution: {data['distribution']}")
    
    def test_06_rating_distribution(self):
        """Test rating distribution calculation"""
        # Submit ratings: 2x5-star, 1x4-star, 1x3-star, 1x1-star
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            session = ChatSession.query.filter_by(user_id=user.id).first()
            
            ratings_to_submit = [5, 5, 4, 3, 1]
            for i, rating_value in enumerate(ratings_to_submit):
                msg = Message(
                    session_id=session.id,
                    role='assistant',
                    content=f'Test message {i}',
                    model_used='gemini-pro'
                )
                db.session.add(msg)
                db.session.flush()
                
                rating = ResponseRating(
                    user_id=user.id,
                    message_id=msg.id,
                    rating=rating_value
                )
                db.session.add(rating)
            
            db.session.commit()
        
        response = self.client.get('/api/ratings/stats', headers=self.headers)
        data = json.loads(response.data)
        
        distribution = data['distribution']
        self.assertEqual(distribution[5], 2)  # 2x 5-star
        self.assertEqual(distribution[4], 1)  # 1x 4-star
        self.assertEqual(distribution[3], 1)  # 1x 3-star
        self.assertEqual(distribution[2], 0)  # 0x 2-star
        self.assertEqual(distribution[1], 1)  # 1x 1-star
        
        print(f"OK: TEST 6: Distribution - 5*:2, 4*:1, 3*:1, 2*:0, 1*:1")
    
    def test_07_get_user_ratings(self):
        """Test getting all user ratings"""
        # Submit 3 ratings
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            session = ChatSession.query.filter_by(user_id=user.id).first()
            
            for i in range(3):
                msg = Message(
                    session_id=session.id,
                    role='assistant',
                    content=f'Test message {i}',
                    model_used='gemini-pro'
                )
                db.session.add(msg)
                db.session.flush()
                
                rating = ResponseRating(
                    user_id=user.id,
                    message_id=msg.id,
                    rating=i+3,  # 3, 4, 5
                    feedback=f'Feedback {i}'
                )
                db.session.add(rating)
            
            db.session.commit()
        
        response = self.client.get('/api/ratings', headers=self.headers)
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['count'], 3)
        self.assertEqual(len(data['ratings']), 3)
        
        print(f"OK: TEST 7: Get all ratings - {data['count']} ratings retrieved")
    
    def test_08_missing_message_id(self):
        """Test error handling for missing message_id"""
        response = self.client.post('/api/rate',
            headers=self.headers,
            json={'rating': 5})  # Missing message_id
        
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['status'], 'error')
        self.assertIn('message_id', data['message'])
        
        print(f"OK: TEST 8: Missing message_id - Error handled correctly")
    
    def test_09_nonexistent_message(self):
        """Test rating a nonexistent message"""
        response = self.client.post('/api/rate',
            headers=self.headers,
            json={
                'message_id': 'nonexistent-id-12345',
                'rating': 5
            })
        
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['status'], 'error')
        self.assertIn('not found', data['message'].lower())
        
        print(f"OK: TEST 9: Nonexistent message - 404 error")
    
    def test_10_feedback_truncation(self):
        """Test feedback truncation at 500 characters"""
        long_feedback = 'A' * 600  # 600 characters
        
        response = self.client.post('/api/rate',
            headers=self.headers,
            json={
                'message_id': self.message_id,
                'rating': 4,
                'feedback': long_feedback
            })
        
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(data['rating']['feedback']), 500)  # Truncated to 500
        
        print(f"OK: TEST 10: Feedback truncation - 600->500 chars")


def run_all_tests():
    """Run all tests and display summary"""
    print("\n" + "="*70)
    print("DAY 4: USER RATING SYSTEM - COMPREHENSIVE TEST SUITE")
    print("="*70 + "\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestRatingSystem)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\nALL TESTS PASSED! [OK]")
        print("\nDay 4 Achievements:")
        print("   • ResponseRating model with 1-5 star system [OK]")
        print("   • POST /api/rate endpoint with validation [OK]")
        print("   • GET /api/ratings/stats for statistics [OK]")
        print("   • GET /api/ratings for all user ratings [OK]")
        print("   • Rating update functionality [OK]")
        print("   • 10/10 comprehensive tests passing [OK]")
    else:
        print("\nERROR: Some tests failed")
    
    print("="*70 + "\n")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
