"""
Prediction Service for Case Outcome Predictor
Handles loading models, making predictions, and finding similar cases
"""

import pickle
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
import chromadb
from datetime import datetime
import re


class PredictionService:
    """Service for making case outcome predictions"""
    
    def __init__(self, model_dir: str = "ml_models"):
        self.model_dir = Path(model_dir)
        self.models_loaded = False
        
        # Models and encoders
        self.rf_model = None
        self.xgb_model = None
        self.tfidf_vectorizer = None
        self.label_encoder = None
        self.feature_names = []
        self.metadata = {}
        
        # ChromaDB for finding similar cases
        self.chroma_client = None
        self.collection = None
        
    def load_models(self):
        """Load trained models from disk"""
        if self.models_loaded:
            return True
        
        try:
            print("📥 Loading prediction models...")
            
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
            
            with open(self.model_dir / 'model_metadata.json', 'r') as f:
                self.metadata = json.load(f)
            
            # Initialize ChromaDB
            self.chroma_client = chromadb.PersistentClient(path="./data/chromadb")
            self.collection = self.chroma_client.get_collection(name="legal_cases")
            
            self.models_loaded = True
            print("✅ Models loaded successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            return False
    
    def predict_outcome(self, case_input: Dict) -> Dict:
        """
        Make prediction for a new case
        
        Args:
            case_input: Dictionary with keys:
                - facts: str - Case facts
                - issues: str - Legal issues
                - charges: str - Charges/sections invoked
                - court: str - Court type (district/high/supreme)
                - case_type: str - Case type (criminal/civil/constitutional)
        
        Returns:
            Dictionary with prediction results
        """
        if not self.models_loaded:
            if not self.load_models():
                return {"error": "Models not available. Please train models first."}
        
        try:
            # Extract and prepare features
            features = self._prepare_features(case_input)
            
            # Get predictions from both models
            rf_pred = self.rf_model.predict(features)[0]
            rf_proba = self.rf_model.predict_proba(features)[0]
            
            xgb_pred = self.xgb_model.predict(features)[0]
            xgb_proba = self.xgb_model.predict_proba(features)[0]
            
            # Ensemble prediction (average probabilities)
            avg_proba = (rf_proba + xgb_proba) / 2
            final_pred = np.argmax(avg_proba)
            
            # Convert to outcome labels
            outcome = self.label_encoder.inverse_transform([final_pred])[0]
            confidence = float(avg_proba[final_pred]) * 100
            
            # Get feature importance for this prediction
            reasoning = self._explain_prediction(features[0])
            
            # Find similar cases
            similar_cases = self._find_similar_cases(case_input)
            
            # Generate outcome description
            outcome_desc = self._get_outcome_description(outcome, confidence)
            
            result = {
                "outcome": outcome,
                "outcome_label": self._format_outcome(outcome),
                "confidence": round(confidence, 2),
                "confidence_level": self._get_confidence_level(confidence),
                "description": outcome_desc,
                "reasoning": reasoning,
                "similar_cases": similar_cases,
                "model_accuracy": {
                    "random_forest": f"{self.metadata['accuracy_scores']['random_forest'] * 100:.1f}%",
                    "xgboost": f"{self.metadata['accuracy_scores']['xgboost'] * 100:.1f}%"
                },
                "all_probabilities": {
                    self.label_encoder.inverse_transform([i])[0]: round(float(avg_proba[i]) * 100, 2)
                    for i in range(len(avg_proba))
                },
                "timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            print(f"Prediction error: {e}")
            return {"error": f"Prediction failed: {str(e)}"}
    
    def _prepare_features(self, case_input: Dict) -> np.ndarray:
        """Prepare feature vector from case input"""
        # Combine text
        facts = case_input.get('facts', '')
        issues = case_input.get('issues', '')
        charges = case_input.get('charges', '')
        combined_text = f"{facts} {issues} {charges}"
        
        # TF-IDF features
        text_features = self.tfidf_vectorizer.transform([combined_text]).toarray()
        
        # Court type one-hot encoding
        court = case_input.get('court', 'other').lower()
        court_features = [
            1 if 'district' in court else 0,
            1 if 'high' in court else 0,
            1 if 'other' in court else 0,
            1 if 'supreme' in court else 0
        ]
        
        # Case type one-hot encoding
        case_type = case_input.get('case_type', 'other').lower()
        type_features = [
            1 if 'civil' in case_type else 0,
            1 if 'constitutional' in case_type else 0,
            1 if 'criminal' in case_type else 0,
            1 if 'other' in case_type else 0
        ]
        
        # Numeric features
        text_length = len(combined_text)
        num_sections = len(re.findall(r'Section \d+|IPC \d+|\d{3}', combined_text))
        num_precedents = len(re.findall(r'v\.|vs\.|versus', combined_text, re.IGNORECASE))
        
        numeric_features = [text_length, num_sections, num_precedents]
        
        # Combine all features
        features = np.hstack([
            text_features,
            court_features,
            type_features,
            numeric_features
        ])
        
        return features
    
    def _explain_prediction(self, features: np.ndarray) -> List[Dict]:
        """Explain prediction using feature importance"""
        # Get feature importance from Random Forest
        importance_dict = dict(self.metadata['feature_importance']['random_forest'])
        
        # Get top contributing features for this case
        reasoning = []
        
        for i, (feature_name, importance) in enumerate(importance_dict[:10]):
            try:
                feature_idx = self.feature_names.index(feature_name)
                feature_value = features[feature_idx]
                
                if feature_value > 0:
                    reasoning.append({
                        "factor": feature_name.replace('_', ' ').title(),
                        "importance": round(importance * 100, 1),
                        "description": self._get_feature_description(feature_name, feature_value)
                    })
            except:
                continue
        
        return reasoning[:5]  # Top 5 factors
    
    def _get_feature_description(self, feature_name: str, value: float) -> str:
        """Generate human-readable description for feature"""
        if 'court_' in feature_name:
            return f"Case in {feature_name.replace('court_', '')} court"
        elif 'type_' in feature_name:
            return f"{feature_name.replace('type_', '')} case type"
        elif feature_name == 'text_length':
            return f"Case complexity (length: {int(value)} chars)"
        elif feature_name == 'num_sections':
            return f"{int(value)} legal sections cited"
        elif feature_name == 'num_precedents':
            return f"{int(value)} precedents referenced"
        else:
            return f"Text pattern: '{feature_name}'"
    
    def _find_similar_cases(self, case_input: Dict, n_results: int = 5) -> List[Dict]:
        """Find similar cases using ChromaDB"""
        try:
            query_text = f"{case_input.get('facts', '')} {case_input.get('issues', '')}"
            
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            
            similar_cases = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    distance = results['distances'][0][i] if results['distances'] else 0
                    
                    # Calculate similarity percentage (inverse of distance)
                    similarity = max(0, (1 - distance) * 100)
                    
                    similar_cases.append({
                        "title": metadata.get('case_title', 'Unknown Case'),
                        "similarity": round(similarity, 1),
                        "summary": doc[:200] + "..." if len(doc) > 200 else doc,
                        "year": metadata.get('year', 'N/A'),
                        "court": metadata.get('court', 'N/A')
                    })
            
            return similar_cases
            
        except Exception as e:
            print(f"Error finding similar cases: {e}")
            return []
    
    def _format_outcome(self, outcome: str) -> str:
        """Format outcome for display"""
        labels = {
            'favorable': 'Favorable Outcome',
            'unfavorable': 'Unfavorable Outcome',
            'partial': 'Partial Outcome'
        }
        return labels.get(outcome, outcome.title())
    
    def _get_outcome_description(self, outcome: str, confidence: float) -> str:
        """Generate detailed outcome description"""
        descriptions = {
            'favorable': "Based on historical data, cases with similar characteristics tend to result in favorable outcomes (appeal allowed, acquittal, petition granted).",
            'unfavorable': "Based on historical data, cases with similar characteristics tend to result in unfavorable outcomes (appeal dismissed, conviction upheld).",
            'partial': "Based on historical data, cases with similar characteristics tend to result in partial outcomes (modified judgment, remanded for retrial)."
        }
        
        base_desc = descriptions.get(outcome, "Outcome prediction based on historical case analysis.")
        
        if confidence >= 80:
            confidence_note = " This prediction has high confidence due to strong precedent."
        elif confidence >= 60:
            confidence_note = " This prediction has moderate confidence with mixed precedents."
        else:
            confidence_note = " This prediction has lower confidence, suggesting a novel legal issue."
        
        return base_desc + confidence_note
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Get confidence level label"""
        if confidence >= 80:
            return "High"
        elif confidence >= 60:
            return "Medium"
        else:
            return "Low"
    
    def get_model_info(self) -> Dict:
        """Get information about loaded models"""
        if not self.models_loaded:
            self.load_models()
        
        return {
            "models_loaded": self.models_loaded,
            "accuracy": self.metadata.get('accuracy_scores', {}),
            "classes": self.metadata.get('classes', []),
            "top_features": self.metadata.get('feature_importance', {}).get('random_forest', [])[:10]
        }


# Singleton instance
_prediction_service = None

def get_prediction_service() -> PredictionService:
    """Get or create prediction service singleton"""
    global _prediction_service
    if _prediction_service is None:
        _prediction_service = PredictionService()
    return _prediction_service
