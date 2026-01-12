"""
Case Outcome Predictor - ML Model Training
Trains Random Forest and XGBoost models on legal case data to predict outcomes
"""

import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import xgboost as xgb
from collections import Counter
import re
import chromadb

class CaseOutcomePredictor:
    """ML model for predicting legal case outcomes"""
    
    def __init__(self, model_dir: str = "ml_models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        
        # Models and encoders
        self.rf_model = None
        self.xgb_model = None
        self.tfidf_vectorizer = None
        self.label_encoder = None
        self.feature_names = []
        
        # Training metrics
        self.accuracy_scores = {}
        self.feature_importance = {}
        
        # ChromaDB client
        self.chroma_client = chromadb.PersistentClient(path="./data/chromadb")
        self.collection = None
    
    def load_case_data(self) -> List[Dict]:
        """Load all legal cases from ChromaDB"""
        print("📂 Loading case data from ChromaDB...")
        
        try:
            self.collection = self.chroma_client.get_collection(name="legal_cases")
            count = self.collection.count()
            print(f"Found {count} cases in ChromaDB")
            
            if count == 0:
                return []
            
            # Get all cases
            # ChromaDB doesn't support getting all at once, so we'll use query with empty string
            results = self.collection.get(limit=count)
            
            cases = []
            if results and results['documents']:
                for i in range(len(results['documents'])):
                    doc = results['documents'][i]
                    metadata = results['metadatas'][i] if results['metadatas'] else {}
                    
                    # Create case dictionary
                    case = {
                        'document': doc,
                        'case_title': metadata.get('case_id', f'case_{i}'),
                        'court': metadata.get('court', 'unknown'),
                        'outcome': metadata.get('outcome', ''),
                        'legal_domain': metadata.get('legal_domain', ''),
                        'year': metadata.get('date', '')[:4] if metadata.get('date') else 'unknown'
                    }
                    cases.append(case)
            
            print(f"✅ Loaded {len(cases)} total cases")
            return cases
            
        except Exception as e:
            print(f"❌ Error loading from ChromaDB: {e}")
            return []
    
    def extract_features(self, cases: List[Dict]) -> pd.DataFrame:
        """Extract features from case data"""
        print("\n🔍 Extracting features from cases...")
        
        features_list = []
        
        for case in cases:
            try:
                # Extract text - now from document field
                document = case.get('document', '')
                
                # Extract outcome label from metadata
                outcome = self._standardize_outcome(case.get('outcome', ''))
                if not outcome:
                    continue  # Skip cases without clear outcome
                
                # Extract categorical features
                court_type = self._extract_court_type(case.get('court', ''))
                case_type = self._extract_case_type(case.get('legal_domain', ''))
                
                # Extract numeric features
                text_length = len(document)
                num_sections = len(re.findall(r'Section \d+', document))
                num_precedents = len(re.findall(r'v\.|vs\.|versus', document, re.IGNORECASE))
                
                features = {
                    'combined_text': document[:5000],  # Limit to prevent memory issues
                    'court_type': court_type,
                    'case_type': case_type,
                    'text_length': text_length,
                    'num_sections': num_sections,
                    'num_precedents': num_precedents,
                    'outcome': outcome
                }
                
                features_list.append(features)
                
            except Exception as e:
                print(f"Error processing case: {e}")
                continue
        
        df = pd.DataFrame(features_list)
        print(f"✅ Extracted features from {len(df)} cases")
        
        if len(df) > 0:
            print(f"\nOutcome distribution:\n{df['outcome'].value_counts()}")
        
        return df
    
    def _standardize_outcome(self, outcome: str) -> str:
        """Standardize outcome labels from ChromaDB metadata"""
        if not outcome:
            return None
        
        outcome_lower = outcome.lower()
        
        # Map various outcome strings to standard labels
        if any(word in outcome_lower for word in ['allow', 'grant', 'accept', 'acquit', 'favour', 'favor']):
            return 'favorable'
        elif any(word in outcome_lower for word in ['dismiss', 'reject', 'convict', 'against']):
            return 'unfavorable'
        elif any(word in outcome_lower for word in ['partial', 'modify', 'remand']):
            return 'partial'
        else:
            return None  # Unclear outcome
    
    def _extract_court_type(self, case_title: str) -> str:
        """Extract court type from case title"""
        title_lower = case_title.lower()
        
        if 'supreme court' in title_lower:
            return 'supreme'
        elif 'high court' in title_lower:
            return 'high'
        elif 'district' in title_lower or 'sessions' in title_lower:
            return 'district'
        else:
            return 'other'
    
    def _extract_case_type(self, legal_domain: str) -> str:
        """Extract case type from legal domain"""
        domain_lower = legal_domain.lower()
        
        if 'criminal' in domain_lower:
            return 'criminal'
        elif 'civil' in domain_lower or 'property' in domain_lower or 'contract' in domain_lower:
            return 'civil'
        elif 'constitution' in domain_lower or 'writ' in domain_lower:
            return 'constitutional'
        else:
            return 'other'
    
    def prepare_training_data(self, df: pd.DataFrame) -> Tuple:
        """Prepare features and labels for training"""
        print("\n🔧 Preparing training data...")
        
        # TF-IDF on combined text
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=100,
            ngram_range=(1, 2),
            stop_words='english'
        )
        
        text_features = self.tfidf_vectorizer.fit_transform(df['combined_text']).toarray()
        
        # Encode categorical features
        court_encoded = pd.get_dummies(df['court_type'], prefix='court')
        case_type_encoded = pd.get_dummies(df['case_type'], prefix='type')
        
        # Combine all features
        numeric_features = df[['text_length', 'num_sections', 'num_precedents']].values
        
        X = np.hstack([
            text_features,
            court_encoded.values,
            case_type_encoded.values,
            numeric_features
        ])
        
        # Store feature names
        self.feature_names = (
            list(self.tfidf_vectorizer.get_feature_names_out()) +
            list(court_encoded.columns) +
            list(case_type_encoded.columns) +
            ['text_length', 'num_sections', 'num_precedents']
        )
        
        # Encode labels
        self.label_encoder = LabelEncoder()
        y = self.label_encoder.fit_transform(df['outcome'])
        
        print(f"✅ Feature matrix shape: {X.shape}")
        print(f"✅ Label distribution: {Counter(y)}")
        
        return X, y
    
    def train_models(self, X, y):
        """Train Random Forest and XGBoost models"""
        print("\n🎯 Training ML models...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"Training set: {X_train.shape[0]} samples")
        print(f"Test set: {X_test.shape[0]} samples")
        
        # Train Random Forest
        print("\n🌲 Training Random Forest...")
        self.rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=15,
            min_samples_split=10,
            random_state=42,
            n_jobs=-1
        )
        self.rf_model.fit(X_train, y_train)
        
        rf_pred = self.rf_model.predict(X_test)
        rf_accuracy = accuracy_score(y_test, rf_pred)
        self.accuracy_scores['random_forest'] = rf_accuracy
        
        print(f"✅ Random Forest Accuracy: {rf_accuracy:.2%}")
        print("\nClassification Report:")
        print(classification_report(y_test, rf_pred, target_names=self.label_encoder.classes_))
        
        # Feature importance
        self.feature_importance['random_forest'] = dict(
            zip(self.feature_names, self.rf_model.feature_importances_)
        )
        
        # Train XGBoost
        print("\n🚀 Training XGBoost...")
        self.xgb_model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            use_label_encoder=False,
            eval_metric='mlogloss'
        )
        self.xgb_model.fit(X_train, y_train)
        
        xgb_pred = self.xgb_model.predict(X_test)
        xgb_accuracy = accuracy_score(y_test, xgb_pred)
        self.accuracy_scores['xgboost'] = xgb_accuracy
        
        print(f"✅ XGBoost Accuracy: {xgb_accuracy:.2%}")
        print("\nClassification Report:")
        print(classification_report(y_test, xgb_pred, target_names=self.label_encoder.classes_))
        
        return X_test, y_test
    
    def save_models(self):
        """Save trained models and encoders"""
        print("\n💾 Saving models...")
        
        # Save models
        with open(self.model_dir / 'rf_model.pkl', 'wb') as f:
            pickle.dump(self.rf_model, f)
        
        with open(self.model_dir / 'xgb_model.pkl', 'wb') as f:
            pickle.dump(self.xgb_model, f)
        
        # Save vectorizer and encoder
        with open(self.model_dir / 'tfidf_vectorizer.pkl', 'wb') as f:
            pickle.dump(self.tfidf_vectorizer, f)
        
        with open(self.model_dir / 'label_encoder.pkl', 'wb') as f:
            pickle.dump(self.label_encoder, f)
        
        # Save feature names
        with open(self.model_dir / 'feature_names.pkl', 'wb') as f:
            pickle.dump(self.feature_names, f)
        
        # Save metadata
        metadata = {
            'accuracy_scores': self.accuracy_scores,
            'feature_importance': {
                k: sorted(v.items(), key=lambda x: x[1], reverse=True)[:10]
                for k, v in self.feature_importance.items()
            },
            'classes': list(self.label_encoder.classes_)
        }
        
        with open(self.model_dir / 'model_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Models saved to {self.model_dir}")
        print(f"\nTop 10 Important Features (Random Forest):")
        for feat, score in metadata['feature_importance']['random_forest'][:10]:
            print(f"  {feat}: {score:.4f}")
    
    def load_models(self):
        """Load trained models from disk"""
        print("📥 Loading trained models...")
        
        with open(self.model_dir / 'rf_model.pkl', 'rb') as f:
            self.rf_model = pickle.load(f)
        
        with open(self.model_dir / 'xgb_model.pkl', 'rb') as f:
            self.xgb_model = pickle.load(f)
        
        with open(self.model_dir / 'tfidf_vectorizer.pkl', 'rb') as f:
            self.tfidf_vectorizer = pickle.load(f)
        
        with open(self.model_dir / 'label_encoder.pkl', 'rb') as f:
            self.label_encoder = pickle.load(f)
        
        with open(self.model_dir / 'feature_names.pkl', 'rb') as f:
            self.feature_names = pickle.load(f)
        
        print("✅ Models loaded successfully")


def main():
    """Train the case outcome predictor"""
    print("=" * 60)
    print("🎓 CASE OUTCOME PREDICTOR - MODEL TRAINING")
    print("=" * 60)
    
    predictor = CaseOutcomePredictor()
    
    # Load data
    cases = predictor.load_case_data()
    
    if len(cases) == 0:
        print("❌ No cases found. Please check data directory.")
        return
    
    # Extract features
    df = predictor.extract_features(cases)
    
    if len(df) < 50:
        print("❌ Not enough cases with clear outcomes for training.")
        return
    
    # Prepare training data
    X, y = predictor.prepare_training_data(df)
    
    # Train models
    X_test, y_test = predictor.train_models(X, y)
    
    # Save models
    predictor.save_models()
    
    print("\n" + "=" * 60)
    print("✅ MODEL TRAINING COMPLETE!")
    print("=" * 60)
    print(f"\nRandom Forest Accuracy: {predictor.accuracy_scores['random_forest']:.2%}")
    print(f"XGBoost Accuracy: {predictor.accuracy_scores['xgboost']:.2%}")
    print(f"\nModels saved to: {predictor.model_dir}")


if __name__ == "__main__":
    main()
