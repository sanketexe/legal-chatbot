# QUICK START: Personalization & RAG Improvements

## 🚀 5-Day Implementation Plan

This guide shows exactly what to implement first to make your chatbot more user-friendly and deployable for Indian users.

---

## DAY 1: User Preference System

### Step 1: Update Database Schema

Create a new migration file: `add_user_preferences.py`

```python
"""
Migration script to add user preferences table
Run: python add_user_preferences.py
"""

from app_with_db import create_app, db
from sqlalchemy import Column, String, Integer, JSON, DateTime, ForeignKey
from datetime import datetime

app = create_app()

class UserPreference(db.Model):
    """Store user preferences for personalization"""
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Language and presentation
    preferred_language = db.Column(db.String(10), default='en')  # en, hi, ta, te, etc
    response_detail_level = db.Column(db.Integer, default=2)     # 1-5 (1=brief, 5=detailed)
    
    # Legal interests
    legal_domains = db.Column(db.JSON, default=[])              # ["family", "property", "criminal"]
    jurisdiction_preference = db.Column(db.String(50), default='all')  # "supreme_court", "high_court", "all"
    
    # Settings
    include_case_summaries = db.Column(db.Boolean, default=True)
    include_act_references = db.Column(db.Boolean, default=True)
    notification_enabled = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'preferred_language': self.preferred_language,
            'response_detail_level': self.response_detail_level,
            'legal_domains': self.legal_domains,
            'jurisdiction_preference': self.jurisdiction_preference,
            'include_case_summaries': self.include_case_summaries,
            'include_act_references': self.include_act_references,
        }

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ User preferences table created")
```

### Step 2: Update Routes to Support Preferences

Add to `app_with_db.py` in the routes section:

```python
@app.route('/api/preferences', methods=['GET', 'POST'])
@auth_required
def preferences():
    """Get or update user preferences"""
    current_user = get_current_user()
    
    if request.method == 'GET':
        # Get preferences
        pref = UserPreference.query.filter_by(user_id=current_user.id).first()
        if not pref:
            # Create default preferences
            pref = UserPreference(user_id=current_user.id)
            db.session.add(pref)
            db.session.commit()
        
        return jsonify(pref.to_dict()), 200
    
    elif request.method == 'POST':
        # Update preferences
        data = request.json
        pref = UserPreference.query.filter_by(user_id=current_user.id).first()
        
        if not pref:
            pref = UserPreference(user_id=current_user.id)
        
        # Update fields
        if 'preferred_language' in data:
            pref.preferred_language = data['preferred_language']
        if 'response_detail_level' in data:
            pref.response_detail_level = int(data['response_detail_level'])
        if 'legal_domains' in data:
            pref.legal_domains = data['legal_domains']
        if 'jurisdiction_preference' in data:
            pref.jurisdiction_preference = data['jurisdiction_preference']
        
        db.session.add(pref)
        db.session.commit()
        
        return jsonify({
            'message': 'Preferences updated',
            'preferences': pref.to_dict()
        }), 200
```

### Step 3: Update Frontend to Capture Preferences

Update `templates/simple.html` - Add settings panel:

```html
<!-- Add this after the chat container -->
<div id="settingsPanel" style="display:none; position: fixed; right: 0; top: 0; width: 300px; height: 100vh; background: white; border-left: 1px solid #ddd; padding: 20px; overflow-y: auto;">
    <h3>⚙️ Preferences</h3>
    
    <label>Language</label>
    <select id="languageSelect" onchange="updatePreference('preferred_language', this.value)">
        <option value="en">English</option>
        <option value="hi">हिंदी (Hindi)</option>
        <option value="ta">தமிழ் (Tamil)</option>
    </select>
    
    <label>Response Detail Level</label>
    <input type="range" min="1" max="5" id="detailLevel" 
           onchange="updatePreference('response_detail_level', this.value)">
    <small id="detailLabel">Medium</small>
    
    <label>Legal Interests</label>
    <div>
        <input type="checkbox" value="family" onchange="updateDomains()"> Family Law
        <input type="checkbox" value="property" onchange="updateDomains()"> Property Law
        <input type="checkbox" value="criminal" onchange="updateDomains()"> Criminal Law
        <input type="checkbox" value="consumer" onchange="updateDomains()"> Consumer Rights
    </div>
    
    <button onclick="closeSettings()">Close</button>
</div>

<button id="settingsBtn" onclick="openSettings()" style="position: fixed; bottom: 20px; right: 20px; width: 50px; height: 50px; border-radius: 50%; background: #007bff; color: white; border: none; cursor: pointer; font-size: 18px;">⚙️</button>

<script>
function openSettings() {
    document.getElementById('settingsPanel').style.display = 'block';
    loadPreferences();
}

function closeSettings() {
    document.getElementById('settingsPanel').style.display = 'none';
}

function loadPreferences() {
    fetch('/api/preferences', {
        method: 'GET',
        headers: {'Authorization': 'Bearer ' + getCookie('auth_token')}
    })
    .then(r => r.json())
    .then(data => {
        document.getElementById('languageSelect').value = data.preferred_language;
        document.getElementById('detailLevel').value = data.response_detail_level;
        updateDetailLabel(data.response_detail_level);
    });
}

function updatePreference(key, value) {
    fetch('/api/preferences', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + getCookie('auth_token')
        },
        body: JSON.stringify({[key]: value})
    })
    .then(r => r.json())
    .then(data => console.log('✅ Preference updated'));
}

function updateDetailLabel(value) {
    const labels = {1: 'Very Brief', 2: 'Brief', 3: 'Medium', 4: 'Detailed', 5: 'Very Detailed'};
    document.getElementById('detailLabel').textContent = labels[value];
}
</script>
```

---

## DAY 2: Improve RAG with Hybrid Search

### Step 1: Create Hybrid Search Module

Create `ml_legal_system/hybrid_search.py`:

```python
"""
Hybrid search combining BM25 (keyword) + semantic search
Better results than semantic search alone
"""

import json
from typing import List, Dict
from rank_bm25 import BM25Okapi
import numpy as np

class HybridSearchEngine:
    """Combines BM25 keyword search with semantic embedding search"""
    
    def __init__(self, vector_db, use_bm25=True):
        """
        Args:
            vector_db: ChromaDB or Pinecone instance
            use_bm25: Whether to use BM25 keyword search
        """
        self.vector_db = vector_db
        self.use_bm25 = use_bm25
        self.bm25_index = None
        self.cases_corpus = []
        
        if use_bm25:
            self._build_bm25_index()
    
    def _build_bm25_index(self):
        """Build BM25 index from case corpus"""
        try:
            # Get all cases from vector DB
            collection = self.vector_db.collection
            results = collection.get()
            
            # Tokenize and build index
            corpus = []
            metadata_list = []
            
            for i, doc in enumerate(results['documents']):
                tokens = doc.lower().split()
                corpus.append(tokens)
                metadata_list.append(results['metadatas'][i])
            
            self.bm25_index = BM25Okapi(corpus)
            self.cases_corpus = results['documents']
            self.metadata_list = metadata_list
            
            print(f"✅ BM25 index built with {len(corpus)} cases")
            
        except Exception as e:
            print(f"⚠️ BM25 indexing failed: {e}")
            self.use_bm25 = False
    
    def hybrid_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Perform hybrid search combining BM25 and semantic similarity
        
        Args:
            query: Legal question
            top_k: Number of results to return
            
        Returns:
            List of relevant cases with scores
        """
        results = []
        
        # 1. Semantic search (embeddings)
        semantic_results = self.vector_db.search_similar_cases(query, top_k=top_k*2)
        semantic_scores = {
            case['metadata']['case_id']: 1 - case.get('distance', 0) 
            for case in semantic_results
        }
        
        # 2. BM25 keyword search
        bm25_scores = {}
        if self.use_bm25 and self.bm25_index:
            try:
                query_tokens = query.lower().split()
                bm25_ranking = self.bm25_index.get_scores(query_tokens)
                
                # Normalize BM25 scores to 0-1
                max_score = max(bm25_ranking) if max(bm25_ranking) > 0 else 1
                
                for i, score in enumerate(bm25_ranking):
                    case_id = self.metadata_list[i].get('case_id', f'case_{i}')
                    bm25_scores[case_id] = score / max_score
                    
            except Exception as e:
                print(f"⚠️ BM25 search failed: {e}")
        
        # 3. Combine scores: 60% semantic + 40% BM25
        combined_scores = {}
        all_case_ids = set(semantic_scores.keys()) | set(bm25_scores.keys())
        
        for case_id in all_case_ids:
            semantic = semantic_scores.get(case_id, 0)
            bm25 = bm25_scores.get(case_id, 0)
            
            # Weighted combination
            combined_score = 0.6 * semantic + 0.4 * bm25
            combined_scores[case_id] = combined_score
        
        # 4. Sort and return top K
        sorted_cases = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        
        for case_id, score in sorted_cases[:top_k]:
            results.append({
                'case_id': case_id,
                'score': score,
                'semantic_score': semantic_scores.get(case_id, 0),
                'bm25_score': bm25_scores.get(case_id, 0)
            })
        
        return results


# Usage Example:
# ├─ hybrid_engine = HybridSearchEngine(vector_db)
# └─ results = hybrid_engine.hybrid_search("divorce in India", top_k=5)
```

### Step 2: Install BM25 Package

Update `requirements.txt`:

```txt
# Add this line
rank-bm25==0.2.2
```

### Step 3: Update Legal Engine to Use Hybrid Search

Update `legal_engine_ml.py`:

```python
# Add to imports
from ml_legal_system.hybrid_search import HybridSearchEngine

# Update LegalEngine initialization
def __init__(self):
    """Initialize legal engine"""
    # ... existing code ...
    
    if self.ml_available:
        try:
            vector_db = LegalVectorDatabase()
            # Use hybrid search instead of basic search
            self.rag = LegalRAG(
                use_openai=False, 
                vector_db=vector_db,
                use_hybrid_search=True  # NEW
            )
            print("✅ ML-powered Legal Engine with Hybrid Search initialized")
        except Exception as e:
            print(f"⚠️ Could not initialize RAG: {e}")
            self.ml_available = False
```

---

## DAY 3: Add Hindi Language Support

### Step 1: Create Translation Module

Create `ml_legal_system/translator.py`:

```python
"""
Multi-language support for Indian users
Supports: English, Hindi, Tamil, Telugu, Marathi
"""

import os
import json
from typing import Dict, Optional

class LegalTranslator:
    """Handle translation of legal responses"""
    
    def __init__(self):
        """Initialize translator with cached translations"""
        self.translations_cache = {}
        self.supported_languages = ['en', 'hi', 'ta', 'te', 'mr']
        
        # Try to import Google Translate (optional)
        try:
            from google.cloud import translate_v2
            self.translator = translate_v2.Client()
            self.has_google_translate = True
            print("✅ Google Cloud Translation API enabled")
        except:
            self.has_google_translate = False
            print("⚠️ Google Cloud Translation not available, using basic translation")
    
    def translate_response(self, text: str, target_language: str) -> str:
        """
        Translate response to target language
        
        Args:
            text: Response to translate
            target_language: Target language code (hi, ta, te, etc)
            
        Returns:
            Translated text
        """
        if target_language == 'en':
            return text
        
        # Check cache first
        cache_key = f"{text[:50]}_{target_language}"
        if cache_key in self.translations_cache:
            return self.translations_cache[cache_key]
        
        try:
            if self.has_google_translate:
                # Use Google Cloud Translation
                result = self.translator.translate_text(
                    text,
                    target_language_code=target_language
                )
                translated = result['translatedText']
            else:
                # Fallback: simple substitution for common legal terms
                translated = self._basic_translate(text, target_language)
            
            # Cache result
            self.translations_cache[cache_key] = translated
            return translated
            
        except Exception as e:
            print(f"Translation error: {e}")
            return text  # Return original if translation fails
    
    def _basic_translate(self, text: str, language: str) -> str:
        """
        Basic translation for common legal terms
        Useful when Google Translate is not available
        """
        legal_terms = {
            'hi': {
                'contract': 'संविदा',
                'divorce': 'तलाक',
                'property': 'संपत्ति',
                'court': 'अदालत',
                'judgment': 'फैसला',
                'appeal': 'अपील',
                'defendant': 'प्रतिवादी',
                'plaintiff': 'वादी',
            },
            'ta': {
                'contract': 'ஒப்பந்தம்',
                'divorce': 'விவாகரத்து',
                'property': 'சொத்து',
                'court': 'நீதிமன்றம்',
                'judgment': 'தீர்ப்பு',
            }
        }
        
        result = text
        if language in legal_terms:
            for english, translated in legal_terms[language].items():
                result = result.replace(english, translated)
        
        return result
    
    def get_language_name(self, code: str) -> str:
        """Get language name from code"""
        names = {
            'en': 'English',
            'hi': 'हिंदी',
            'ta': 'தமிழ்',
            'te': 'తెలుగు',
            'mr': 'मराठी'
        }
        return names.get(code, code)


# Usage:
# ├─ translator = LegalTranslator()
# └─ hindi_response = translator.translate_response(english_response, 'hi')
```

### Step 2: Update Chat Route to Support Languages

Update `app_with_db.py` chat endpoint:

```python
@app.route('/api/chat', methods=['POST'])
@auth_required
def chat():
    """Handle chat messages with multi-language support"""
    current_user = get_current_user()
    data = request.json
    query = data.get('query', '').strip()
    session_id = data.get('session_id')
    
    if not query:
        return jsonify({'error': 'Query cannot be empty'}), 400
    
    try:
        # Get user preferences
        user_pref = UserPreference.query.filter_by(user_id=current_user.id).first()
        target_language = user_pref.preferred_language if user_pref else 'en'
        detail_level = user_pref.response_detail_level if user_pref else 2
        
        # Get legal response
        legal_response = legal_engine.get_legal_response(
            query=query,
            user_context={
                'user_id': current_user.id,
                'detail_level': detail_level,
                'language': target_language,
                'domains': user_pref.legal_domains if user_pref else []
            }
        )
        
        # Translate if needed
        if target_language != 'en':
            from ml_legal_system.translator import LegalTranslator
            translator = LegalTranslator()
            legal_response['response'] = translator.translate_response(
                legal_response['response'],
                target_language
            )
        
        # Store in database
        if not session_id:
            session = ChatSession(user_id=current_user.id)
            db.session.add(session)
            db.session.flush()
            session_id = session.id
        
        # Save user message
        user_msg = Message(
            session_id=session_id,
            role='user',
            content=query
        )
        db.session.add(user_msg)
        
        # Save assistant response
        assistant_msg = Message(
            session_id=session_id,
            role='assistant',
            content=legal_response['response'],
            metadata={
                'sources': legal_response.get('sources', []),
                'language': target_language
            }
        )
        db.session.add(assistant_msg)
        db.session.commit()
        
        return jsonify({
            'response': legal_response['response'],
            'session_id': session_id,
            'language': target_language,
            'sources': legal_response.get('sources', [])
        }), 200
        
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({'error': str(e)}), 500
```

---

## DAY 4: Add User Satisfaction Rating

### Step 1: Create Interaction Tracking Table

Add to `models.py`:

```python
class InteractionRating(db.Model):
    """Track user satisfaction with responses"""
    __tablename__ = 'interaction_ratings'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    message_id = db.Column(db.String(36), db.ForeignKey('messages.id'), nullable=False)
    rating = db.Column(db.Integer)  # 1-5 star rating
    helpful = db.Column(db.Boolean)  # Was it helpful?
    feedback = db.Column(db.Text)  # Optional feedback
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'rating': self.rating,
            'helpful': self.helpful,
            'feedback': self.feedback,
            'timestamp': self.created_at.isoformat()
        }
```

### Step 2: Add Rating Endpoint

Add to `app_with_db.py`:

```python
@app.route('/api/rate-response', methods=['POST'])
@auth_required
def rate_response():
    """Rate a response for quality feedback"""
    current_user = get_current_user()
    data = request.json
    
    message_id = data.get('message_id')
    rating = data.get('rating')  # 1-5
    helpful = data.get('helpful', rating >= 3)  # >= 3 stars = helpful
    feedback = data.get('feedback', '')
    
    try:
        rating_record = InteractionRating(
            user_id=current_user.id,
            message_id=message_id,
            rating=rating,
            helpful=helpful,
            feedback=feedback
        )
        db.session.add(rating_record)
        db.session.commit()
        
        return jsonify({
            'message': 'Thank you for your feedback!',
            'rating': rating_record.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### Step 3: Add Rating UI to Frontend

Update `templates/simple.html`:

```html
<!-- Add rating buttons after each assistant message -->
<div class="rating-container" id="rating-{message_id}">
    <small>Was this helpful?</small>
    <button class="rate-btn" onclick="rateResponse('{message_id}', 5)">👍</button>
    <button class="rate-btn" onclick="rateResponse('{message_id}', 1)">👎</button>
    <textarea placeholder="Optional feedback" id="feedback-{message_id}"></textarea>
    <button onclick="submitRating('{message_id}')">Submit</button>
</div>

<script>
function rateResponse(messageId, rating) {
    const feedback = document.getElementById(`feedback-${messageId}`).value;
    
    fetch('/api/rate-response', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + getCookie('auth_token')
        },
        body: JSON.stringify({
            message_id: messageId,
            rating: rating,
            helpful: rating >= 3,
            feedback: feedback
        })
    })
    .then(r => r.json())
    .then(data => {
        alert('Thank you for your feedback!');
        document.getElementById(`rating-${messageId}`).remove();
    });
}
</script>
```

---

## DAY 5: Caching Layer for Performance

### Step 1: Add Redis Caching

Update `requirements.txt`:

```txt
redis==4.5.4
```

### Step 2: Create Caching Module

Create `ml_legal_system/cache.py`:

```python
"""
Caching layer for improved performance
Cache common legal queries and responses
"""

import redis
import json
import hashlib
from datetime import timedelta
from typing import Optional, Dict, Any

class CacheManager:
    """Redis-based caching for legal responses"""
    
    def __init__(self, host='localhost', port=6379, db=0, ttl_hours=24):
        """
        Initialize Redis cache
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            ttl_hours: Time-to-live in hours
        """
        try:
            self.redis = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.redis.ping()
            self.available = True
            self.ttl = timedelta(hours=ttl_hours)
            print("✅ Redis cache connected")
        except:
            self.available = False
            print("⚠️ Redis cache unavailable, using memory only")
    
    def _get_cache_key(self, query: str, user_id: str, language: str) -> str:
        """Generate cache key from query"""
        key_string = f"{query}_{user_id}_{language}"
        return "legal_" + hashlib.md5(key_string.encode()).hexdigest()
    
    def get_cached_response(self, query: str, user_id: str, language: str = 'en') -> Optional[Dict]:
        """Get cached response if available"""
        if not self.available:
            return None
        
        try:
            cache_key = self._get_cache_key(query, user_id, language)
            cached = self.redis.get(cache_key)
            
            if cached:
                print(f"💾 Cache hit: {query[:30]}...")
                return json.loads(cached)
            
            return None
        except Exception as e:
            print(f"Cache retrieval error: {e}")
            return None
    
    def cache_response(self, query: str, response: Dict, user_id: str, language: str = 'en'):
        """Cache a response"""
        if not self.available:
            return
        
        try:
            cache_key = self._get_cache_key(query, user_id, language)
            self.redis.setex(
                cache_key,
                self.ttl,
                json.dumps(response)
            )
            print(f"💾 Cached response for: {query[:30]}...")
        except Exception as e:
            print(f"Cache storage error: {e}")
    
    def clear_cache(self):
        """Clear all legal cache"""
        if not self.available:
            return
        
        try:
            pattern = "legal_*"
            for key in self.redis.scan_iter(match=pattern):
                self.redis.delete(key)
            print("✅ Cache cleared")
        except Exception as e:
            print(f"Cache clear error: {e}")


# Usage in legal_engine_ml.py:
# ├─ cache = CacheManager()
# └─ cached = cache.get_cached_response(query, user_id)
```

### Step 3: Update Legal Engine to Use Cache

Update `legal_engine_ml.py`:

```python
from ml_legal_system.cache import CacheManager

class LegalEngine:
    def __init__(self):
        # ... existing code ...
        self.cache = CacheManager()
    
    def get_legal_response(self, query: str, user_context: Dict = None) -> Dict:
        """Get legal response with caching"""
        user_id = user_context.get('user_id', 'anonymous') if user_context else 'anonymous'
        language = user_context.get('language', 'en') if user_context else 'en'
        
        # Check cache first
        cached_response = self.cache.get_cached_response(query, user_id, language)
        if cached_response:
            return cached_response
        
        # Generate response
        if self.ml_available and self.rag:
            response = self._get_rag_response(query)
        else:
            response = self._get_basic_response(query)
        
        # Cache the response
        self.cache.cache_response(query, response, user_id, language)
        
        return response
```

---

## 📋 Implementation Checklist

### Day 1: User Preferences ✅
- [ ] Create migration script
- [ ] Create `user_preferences` table
- [ ] Add preferences API endpoints
- [ ] Update frontend with settings panel
- [ ] Test preference storage

### Day 2: Hybrid Search ✅
- [ ] Install `rank-bm25` package
- [ ] Create `hybrid_search.py` module
- [ ] Build BM25 index from cases
- [ ] Combine semantic + keyword search
- [ ] Test retrieval quality

### Day 3: Hindi Support ✅
- [ ] Create `translator.py` module
- [ ] Add translation logic
- [ ] Update chat endpoint for multi-language
- [ ] Add language selector to UI
- [ ] Test translations

### Day 4: Rating System ✅
- [ ] Create `InteractionRating` model
- [ ] Add rating endpoint
- [ ] Add UI buttons for ratings
- [ ] Store feedback in database
- [ ] Test rating submission

### Day 5: Caching ✅
- [ ] Install Redis (local or cloud)
- [ ] Create `cache.py` module
- [ ] Integrate cache into legal engine
- [ ] Test cache hits/misses
- [ ] Monitor cache performance

---

## 🧪 Testing Commands

```bash
# Test preferences API
curl -X GET http://localhost:5000/api/preferences \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test rating submission
curl -X POST http://localhost:5000/api/rate-response \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message_id": "msg123", "rating": 5, "helpful": true}'

# Test hybrid search
python -c "
from ml_legal_system.hybrid_search import HybridSearchEngine
from ml_legal_system.vector_db import LegalVectorDatabase

vdb = LegalVectorDatabase()
engine = HybridSearchEngine(vdb)
results = engine.hybrid_search('property rights', top_k=5)
for r in results:
    print(f'Score: {r[\"score\"]:.2f} | Semantic: {r[\"semantic_score\"]:.2f} | BM25: {r[\"bm25_score\"]:.2f}')
"
```

---

## 🚀 Next Steps After This Week

1. **Deploy to AWS Mumbai** (1 day)
2. **Expand case database** to 2,000+ cases (1 week)
3. **Add document upload** for legal analysis (2 days)
4. **Create lawyer directory** (3 days)
5. **Add offline support** with PWA (2 days)

---

## 📞 Support Resources

- **Redis Setup**: https://redis.io/docs/getting-started/
- **Google Translate API**: https://cloud.google.com/translate/docs
- **BM25 Algorithm**: https://en.wikipedia.org/wiki/Okapi_BM25
- **Flask Best Practices**: https://flask.palletsprojects.com/

---

**Duration**: ~8-10 hours total development  
**Difficulty**: 🟠 Medium  
**Impact**: 🚀 HIGH (Major UX improvement + personalization + deployment readiness)

Start with Day 1 & 2 for maximum impact!
