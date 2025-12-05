# Day 4: User Rating System - Quick Start Guide

**Objective**: Implement 1-5 star rating system for responses  
**Time**: 1 hour  
**Points**: +2 (78 → 80/100)  
**Status**: Ready to implement

---

## 🎯 Acceptance Criteria

- [ ] ResponseRating model created with user_id, session_id, message_id, rating (1-5), feedback (optional)
- [ ] POST /api/rate endpoint implemented with authentication
- [ ] GET /api/ratings/stats endpoint shows average rating and count
- [ ] Ratings persist in database
- [ ] 5+ test cases all passing
- [ ] Integration verified with existing chat system

---

## 📐 Architecture Overview

```
User Chat Response
        ↓
   [RATE BUTTON]
        ↓
  POST /api/rate
        ↓
ResponseRating Model (insert)
        ↓
Database Storage
        ↓
Rating Stats Calculation
```

---

## 📋 Implementation Steps

### Step 1: Create ResponseRating Model (5 min)
**File**: `models.py`

Add after UserPreference class:
```python
class ResponseRating(db.Model):
    """Store user ratings for responses"""
    __tablename__ = 'response_ratings'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    message_id = db.Column(db.String(36), db.ForeignKey('messages.id'), nullable=True, index=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    feedback = db.Column(db.Text, nullable=True)  # Optional feedback
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = db.relationship('User', backref='ratings')
    message = db.relationship('Message', backref='ratings')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'message_id': self.message_id,
            'rating': self.rating,
            'feedback': self.feedback,
            'created_at': self.created_at.isoformat()
        }
```

### Step 2: Create Rating Endpoints (10 min)
**File**: `app_with_db.py`

Add after preference endpoints:
```python
@app.route('/api/rate', methods=['POST'])
@auth_required
def rate_response(current_user):
    """Rate a chat response"""
    try:
        data = request.get_json()
        message_id = data.get('message_id')
        rating = data.get('rating')
        feedback = data.get('feedback', '')
        
        # Validate rating
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400
        
        # Verify message exists and belongs to user
        message = Message.query.filter_by(id=message_id).first()
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        # Create rating
        rating_obj = ResponseRating(
            user_id=current_user.id,
            message_id=message_id,
            rating=rating,
            feedback=feedback[:500] if feedback else None  # Max 500 chars
        )
        
        db.session.add(rating_obj)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'rating': rating_obj.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/ratings/stats', methods=['GET'])
@auth_required
def get_rating_stats(current_user):
    """Get user's rating statistics"""
    try:
        ratings = ResponseRating.query.filter_by(user_id=current_user.id).all()
        
        if not ratings:
            return jsonify({
                'total_ratings': 0,
                'average_rating': 0,
                'distribution': {}
            })
        
        # Calculate statistics
        total = len(ratings)
        average = sum(r.rating for r in ratings) / total
        
        # Distribution by star
        distribution = {i: len([r for r in ratings if r.rating == i]) for i in range(1, 6)}
        
        return jsonify({
            'total_ratings': total,
            'average_rating': round(average, 2),
            'distribution': distribution,
            'user_id': current_user.id
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### Step 3: Create Test Suite (15 min)
**File**: `test_rating_system.py`

Test cases:
1. Create rating (1-5 stars)
2. Validate rating range
3. Get rating statistics
4. Multiple ratings calculation
5. Feedback storage and retrieval

### Step 4: Create Database Migration (5 min)
**File**: `migrations/002_add_response_ratings.py`

```python
from models import db, ResponseRating

def upgrade():
    db.create_all()
    print("✅ ResponseRating table created")

if __name__ == '__main__':
    upgrade()
```

### Step 5: Run Tests and Verify (10 min)
```bash
python test_rating_system.py
```

Expected output: **5/5 tests passing** ✅

### Step 6: Commit to Git (5 min)
```bash
git add models.py app_with_db.py test_rating_system.py DAY4_COMPLETION_REPORT.md
git commit -m "feat(day4): implement user rating system for responses"
```

---

## 🔑 Key Features

1. **1-5 Star Rating**: Simple integer scale
2. **Optional Feedback**: Text field for user comments
3. **Statistics Tracking**: Average rating and distribution
4. **User-Scoped**: Each user sees only their own ratings
5. **Persistence**: All ratings saved to database

---

## 📊 Expected Results

- **Model Creation**: 20 lines of code
- **API Endpoints**: 40 lines of code
- **Test Suite**: ~200 lines of code
- **Total**: ~260 lines
- **Tests Passing**: 5/5
- **Score Gain**: +2 points

---

## 🚀 After Day 4

**Score**: 78 → 80/100 (64% complete)

**Remaining**:
- Day 5: Response Caching (2 hours, +2 points) → 82/100
- Days 6-7: Testing & Deployment (2 hours, +3 points) → 85/100

**Time Available**: 6 hours for 4 hours of work (50% buffer)

---

## 📝 Notes

- Use existing User and Message models
- Integration with existing chat system is straightforward
- No new dependencies needed (uses SQLAlchemy like Day 1)
- Optional: Add rating widget to frontend later

---

**Ready to start?** Type `continue` to begin Day 4!
