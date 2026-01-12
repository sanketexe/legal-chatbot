"""
Enhanced Case Outcome Predictor with Advanced ML
Improved prediction accuracy with feature engineering and ensemble methods
"""

import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix, f1_score
import xgboost as xgb
from datetime import datetime
import re


class EnhancedCaseOutcomePredictor:
    """
    Enhanced ML model for predicting legal case outcomes
    Features:
    - Advanced feature engineering
    - Ensemble methods (RF + XGBoost + GradientBoosting)
    - Confidence scores
    - Explainable predictions
    """
    
    def __init__(self, model_dir: str = "ml_models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        
        # Ensemble models
        self.rf_model = None
        self.xgb_model = None
        self.gb_model = None  # Gradient Boosting
        self.ensemble_weights = {'rf': 0.3, 'xgb': 0.4, 'gb': 0.3}
        
        # Feature processors
        self.tfidf_vectorizer = None
        self.label_encoder = None
        self.scaler = StandardScaler()
        
        # Feature names and importance
        self.feature_names = []
        self.feature_importance = {}
        
        # Training metrics
        self.training_metrics = {}
        
        self._load_models()
    
    def _load_models(self):
        """Load pre-trained models if available"""
        try:
            rf_path = self.model_dir / "rf_model_enhanced.pkl"
            xgb_path = self.model_dir / "xgb_model_enhanced.pkl"
            gb_path = self.model_dir / "gb_model_enhanced.pkl"
            
            if rf_path.exists():
                with open(rf_path, 'rb') as f:
                    self.rf_model = pickle.load(f)
                print("✅ Loaded Random Forest model")
            
            if xgb_path.exists():
                with open(xgb_path, 'rb') as f:
                    self.xgb_model = pickle.load(f)
                print("✅ Loaded XGBoost model")
            
            if gb_path.exists():
                with open(gb_path, 'rb') as f:
                    self.gb_model = pickle.load(f)
                print("✅ Loaded Gradient Boosting model")
                
            # Load vectorizer and encoders
            vectorizer_path = self.model_dir / "tfidf_vectorizer_predictor.pkl"
            if vectorizer_path.exists():
                with open(vectorizer_path, 'rb') as f:
                    self.tfidf_vectorizer = pickle.load(f)
            
            encoder_path = self.model_dir / "label_encoder_predictor.pkl"
            if encoder_path.exists():
                with open(encoder_path, 'rb') as f:
                    self.label_encoder = pickle.load(f)
                    
        except Exception as e:
            print(f"⚠️  Could not load models: {e}")
    
    def extract_advanced_features(self, case_text: str, metadata: Dict) -> Dict:
        """
        Extract advanced features from case text and metadata
        
        Returns:
            Dict of numerical and categorical features
        """
        features = {}
        
        # Text-based features
        features['text_length'] = len(case_text)
        features['word_count'] = len(case_text.split())
        features['sentence_count'] = len(re.split(r'[.!?]+', case_text))
        
        # Legal term density
        legal_terms = [
            'section', 'act', 'article', 'provision', 'clause', 'amendment',
            'plaintiff', 'defendant', 'petitioner', 'respondent', 'appellant',
            'evidence', 'witness', 'testimony', 'judgment', 'order', 'decree'
        ]
        legal_term_count = sum(case_text.lower().count(term) for term in legal_terms)
        features['legal_term_density'] = legal_term_count / max(features['word_count'], 1)
        
        # Citation analysis
        features['statute_citations'] = len(re.findall(r'section\s+\d+', case_text, re.IGNORECASE))
        features['case_citations'] = len(re.findall(r'\d{4}\s+\w+\s+\d+', case_text))
        
        # Sentiment indicators (simplified)
        positive_words = ['favor', 'grant', 'allow', 'accept', 'approve', 'uphold']
        negative_words = ['deny', 'reject', 'dismiss', 'refuse', 'overturn', 'reverse']
        
        features['positive_indicators'] = sum(case_text.lower().count(word) for word in positive_words)
        features['negative_indicators'] = sum(case_text.lower().count(word) for word in negative_words)
        
        # Metadata features
        features['category'] = metadata.get('category', 'Unknown')
        features['subcategory'] = metadata.get('subcategory', 'Unknown')
        features['importance'] = metadata.get('importance', 50)
        
        # Court level (if available)
        court = metadata.get('court', '').lower()
        if 'supreme' in court:
            features['court_level'] = 3
        elif 'high' in court:
            features['court_level'] = 2
        else:
            features['court_level'] = 1
        
        return features
    
    def prepare_training_data(self, cases: List[Dict]) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare training data from case list
        
        Args:
            cases: List of case dictionaries with 'text', 'metadata', 'outcome'
            
        Returns:
            Tuple of (features_df, labels_series)
        """
        print("🔧 Preparing training data with advanced features...")
        
        all_features = []
        all_labels = []
        
        for case in cases:
            case_text = case.get('text', case.get('document', ''))
            metadata = case.get('metadata', {})
            outcome = case.get('outcome', metadata.get('outcome', ''))
            
            if not outcome or not case_text:
                continue
            
            # Extract features
            features = self.extract_advanced_features(case_text, metadata)
            features['text'] = case_text  # Keep for TF-IDF
            
            all_features.append(features)
            all_labels.append(outcome)
        
        print(f"✅ Prepared {len(all_features)} cases for training")
        
        return pd.DataFrame(all_features), pd.Series(all_labels)
    
    def train_ensemble_models(self, X_train, y_train, X_test, y_test):
        """Train ensemble of models"""
        print("\n🎓 Training ensemble models...")
        
        # Encode labels
        if self.label_encoder is None:
            self.label_encoder = LabelEncoder()
            self.label_encoder.fit(y_train)
        
        y_train_encoded = self.label_encoder.transform(y_train)
        y_test_encoded = self.label_encoder.transform(y_test)
        
        # 1. Random Forest
        print("\n📊 Training Random Forest...")
        self.rf_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        self.rf_model.fit(X_train, y_train_encoded)
        rf_pred = self.rf_model.predict(X_test)
        rf_score = accuracy_score(y_test_encoded, rf_pred)
        print(f"   Accuracy: {rf_score:.3f}")
        
        # 2. XGBoost
        print("\n📊 Training XGBoost...")
        self.xgb_model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=10,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            use_label_encoder=False,
            eval_metric='mlogloss'
        )
        self.xgb_model.fit(X_train, y_train_encoded)
        xgb_pred = self.xgb_model.predict(X_test)
        xgb_score = accuracy_score(y_test_encoded, xgb_pred)
        print(f"   Accuracy: {xgb_score:.3f}")
        
        # 3. Gradient Boosting
        print("\n📊 Training Gradient Boosting...")
        self.gb_model = GradientBoostingClassifier(
            n_estimators=200,
            max_depth=8,
            learning_rate=0.1,
            subsample=0.8,
            random_state=42
        )
        self.gb_model.fit(X_train, y_train_encoded)
        gb_pred = self.gb_model.predict(X_test)
        gb_score = accuracy_score(y_test_encoded, gb_pred)
        print(f"   Accuracy: {gb_score:.3f}")
        
        # Ensemble prediction
        print("\n🎯 Ensemble Performance:")
        ensemble_pred = self._ensemble_predict(X_test)
        ensemble_score = accuracy_score(y_test_encoded, ensemble_pred)
        print(f"   Accuracy: {ensemble_score:.3f}")
        
        # Store metrics
        self.training_metrics = {
            'rf_accuracy': float(rf_score),
            'xgb_accuracy': float(xgb_score),
            'gb_accuracy': float(gb_score),
            'ensemble_accuracy': float(ensemble_score),
            'trained_on': datetime.now().isoformat(),
            'num_classes': len(self.label_encoder.classes_),
            'classes': self.label_encoder.classes_.tolist()
        }
        
        # Save models
        self._save_models()
        
        return ensemble_score
    
    def _ensemble_predict(self, X):
        """Make prediction using weighted ensemble"""
        rf_proba = self.rf_model.predict_proba(X)
        xgb_proba = self.xgb_model.predict_proba(X)
        gb_proba = self.gb_model.predict_proba(X)
        
        # Weighted average
        ensemble_proba = (
            self.ensemble_weights['rf'] * rf_proba +
            self.ensemble_weights['xgb'] * xgb_proba +
            self.ensemble_weights['gb'] * gb_proba
        )
        
        return np.argmax(ensemble_proba, axis=1)
    
    def predict_outcome(self, case_text: str, metadata: Dict) -> Dict:
        """
        Predict case outcome with confidence score
        
        Returns:
            Dict with prediction, confidence, probabilities, explanation
        """
        if not all([self.rf_model, self.xgb_model, self.gb_model]):
            return {
                'error': 'Models not trained yet',
                'prediction': None,
                'confidence': 0.0
            }
        
        # Extract features
        features = self.extract_advanced_features(case_text, metadata)
        features['text'] = case_text
        
        # Prepare features dataframe
        features_df = pd.DataFrame([features])
        
        # Transform features (same as training)
        X = self._transform_features(features_df)
        
        # Get predictions from all models
        rf_proba = self.rf_model.predict_proba(X)[0]
        xgb_proba = self.xgb_model.predict_proba(X)[0]
        gb_proba = self.gb_model.predict_proba(X)[0]
        
        # Ensemble probabilities
        ensemble_proba = (
            self.ensemble_weights['rf'] * rf_proba +
            self.ensemble_weights['xgb'] * xgb_proba +
            self.ensemble_weights['gb'] * gb_proba
        )
        
        # Get prediction
        predicted_class = np.argmax(ensemble_proba)
        predicted_outcome = self.label_encoder.inverse_transform([predicted_class])[0]
        confidence = float(ensemble_proba[predicted_class])
        
        # Get top 3 predictions
        top_3_indices = np.argsort(ensemble_proba)[-3:][::-1]
        top_3_predictions = [
            {
                'outcome': self.label_encoder.inverse_transform([idx])[0],
                'probability': float(ensemble_proba[idx])
            }
            for idx in top_3_indices
        ]
        
        # Generate explanation
        explanation = self._generate_explanation(features, predicted_outcome, confidence)
        
        return {
            'prediction': predicted_outcome,
            'confidence': confidence,
            'top_3_predictions': top_3_predictions,
            'model_agreement': self._check_model_agreement(rf_proba, xgb_proba, gb_proba),
            'explanation': explanation,
            'warning': self._generate_warning(confidence)
        }
    
    def _transform_features(self, features_df: pd.DataFrame):
        """Transform features for prediction (placeholder for now)"""
        # Extract numerical features
        numerical_features = [
            'text_length', 'word_count', 'sentence_count',
            'legal_term_density', 'statute_citations', 'case_citations',
            'positive_indicators', 'negative_indicators', 'importance', 'court_level'
        ]
        
        X_numerical = features_df[numerical_features].values
        
        # TODO: Add TF-IDF features if needed
        
        return X_numerical
    
    def _check_model_agreement(self, rf_proba, xgb_proba, gb_proba) -> float:
        """Check agreement between models"""
        rf_pred = np.argmax(rf_proba)
        xgb_pred = np.argmax(xgb_proba)
        gb_pred = np.argmax(gb_proba)
        
        agreement_count = sum([
            rf_pred == xgb_pred,
            rf_pred == gb_pred,
            xgb_pred == gb_pred
        ])
        
        return agreement_count / 3.0
    
    def _generate_explanation(self, features: Dict, prediction: str, confidence: float) -> str:
        """Generate human-readable explanation"""
        explanation_parts = []
        
        explanation_parts.append(
            f"Based on analysis of {features['word_count']} words and "
            f"{features['statute_citations']} statutory citations, "
        )
        
        if confidence > 0.8:
            explanation_parts.append(
                f"the model is highly confident (confidence: {confidence:.1%}) "
            )
        elif confidence > 0.6:
            explanation_parts.append(
                f"the model is moderately confident (confidence: {confidence:.1%}) "
            )
        else:
            explanation_parts.append(
                f"the model has low confidence (confidence: {confidence:.1%}) "
            )
        
        explanation_parts.append(f"that the likely outcome is: {prediction}.")
        
        # Add key factors
        if features['positive_indicators'] > features['negative_indicators']:
            explanation_parts.append(
                " Positive legal language suggests a favorable outcome."
            )
        elif features['negative_indicators'] > features['positive_indicators']:
            explanation_parts.append(
                " Negative legal language suggests an unfavorable outcome."
            )
        
        return "".join(explanation_parts)
    
    def _generate_warning(self, confidence: float) -> Optional[str]:
        """Generate warning if confidence is low"""
        if confidence < 0.5:
            return "⚠️ Very low confidence. This prediction should not be relied upon."
        elif confidence < 0.7:
            return "⚠️ Moderate confidence. Consider consulting legal experts."
        return None
    
    def _save_models(self):
        """Save trained models"""
        try:
            with open(self.model_dir / "rf_model_enhanced.pkl", 'wb') as f:
                pickle.dump(self.rf_model, f)
            
            with open(self.model_dir / "xgb_model_enhanced.pkl", 'wb') as f:
                pickle.dump(self.xgb_model, f)
            
            with open(self.model_dir / "gb_model_enhanced.pkl", 'wb') as f:
                pickle.dump(self.gb_model, f)
            
            with open(self.model_dir / "label_encoder_predictor.pkl", 'wb') as f:
                pickle.dump(self.label_encoder, f)
            
            # Save metrics
            with open(self.model_dir / "prediction_metrics.json", 'w') as f:
                json.dump(self.training_metrics, f, indent=2)
            
            print("✅ Models saved successfully")
            
        except Exception as e:
            print(f"❌ Error saving models: {e}")
