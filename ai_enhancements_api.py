"""
Flask Blueprint for AI Enhancements (Task 12)
API endpoints for prediction, document drafting, and research
"""

from flask import Blueprint, request, jsonify, send_file
from ml_legal_system.enhanced_predictor import EnhancedCaseOutcomePredictor
from ml_legal_system.document_drafter import DocumentDrafter
from ml_legal_system.research_summarizer import LegalResearchSummarizer
from ml_legal_system.vector_db import VectorDatabase
import traceback
from datetime import datetime
import io

# Create blueprint
ai_enhancements_bp = Blueprint('ai_enhancements', __name__, url_prefix='/api/ai')

# Initialize systems
predictor = EnhancedCaseOutcomePredictor()
drafter = DocumentDrafter()
vector_db = VectorDatabase()
summarizer = LegalResearchSummarizer(vector_db=vector_db)


@ai_enhancements_bp.route('/predict', methods=['POST'])
def predict_case_outcome():
    """
    Predict case outcome
    
    Request body:
    {
        "case_text": "...",
        "metadata": {
            "category": "...",
            "subcategory": "...",
            "court": "...",
            "importance": 75
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'case_text' not in data:
            return jsonify({
                'error': 'Missing required field: case_text'
            }), 400
        
        case_text = data['case_text']
        metadata = data.get('metadata', {})
        
        # Make prediction
        result = predictor.predict_outcome(case_text, metadata)
        
        return jsonify({
            'success': True,
            'prediction': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@ai_enhancements_bp.route('/document/templates', methods=['GET'])
def list_document_templates():
    """Get list of available document templates"""
    try:
        templates = drafter.list_templates()
        
        return jsonify({
            'success': True,
            'templates': templates,
            'count': len(templates)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_enhancements_bp.route('/document/template/<template_id>', methods=['GET'])
def get_template_details(template_id):
    """Get details about a specific template"""
    try:
        if template_id not in drafter.templates:
            return jsonify({
                'success': False,
                'error': f'Template {template_id} not found',
                'available_templates': list(drafter.templates.keys())
            }), 404
        
        template = drafter.templates[template_id]
        
        return jsonify({
            'success': True,
            'template': {
                'id': template_id,
                'name': template['name'],
                'category': template['category'],
                'fields': template['fields']
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_enhancements_bp.route('/document/draft', methods=['POST'])
def draft_document():
    """
    Draft a legal document
    
    Request body:
    {
        "template_id": "nda",
        "fields": {
            "disclosing_party_name": "...",
            "receiving_party_name": "...",
            ...
        },
        "ai_enhance": false
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'template_id' not in data or 'fields' not in data:
            return jsonify({
                'error': 'Missing required fields: template_id, fields'
            }), 400
        
        template_id = data['template_id']
        fields = data['fields']
        ai_enhance = data.get('ai_enhance', False)
        
        # Generate document
        result = drafter.draft_document(template_id, fields, ai_enhance)
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error'],
                'details': result
            }), 400
        
        return jsonify({
            'success': True,
            'document': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@ai_enhancements_bp.route('/document/export', methods=['POST'])
def export_document():
    """
    Export document to file
    
    Request body:
    {
        "document_text": "...",
        "filename": "my_document",
        "format": "txt"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'document_text' not in data:
            return jsonify({
                'error': 'Missing required field: document_text'
            }), 400
        
        document_text = data['document_text']
        filename = data.get('filename', f'document_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        format_type = data.get('format', 'txt')
        
        # Export
        result = drafter.export_document(document_text, filename, format_type)
        
        if not result['success']:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
        
        # Send file
        return send_file(
            result['filepath'],
            as_attachment=True,
            download_name=f"{filename}.{format_type}"
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_enhancements_bp.route('/research/summarize', methods=['POST'])
def summarize_research():
    """
    Generate research summary from cases
    
    Request body:
    {
        "topic": "Wrongful Termination",
        "query": "employment termination without notice",
        "max_cases": 10
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'topic' not in data:
            return jsonify({
                'error': 'Missing required field: topic'
            }), 400
        
        topic = data['topic']
        query = data.get('query', topic)
        max_cases = data.get('max_cases', 10)
        
        # Search for relevant cases
        print(f"🔍 Searching for cases: {query}")
        search_results = vector_db.search(
            query=query,
            top_k=max_cases,
            collection_name='indian_legal_cases'
        )
        
        if not search_results or len(search_results) == 0:
            return jsonify({
                'success': False,
                'error': 'No relevant cases found',
                'suggestion': 'Try a different search query'
            }), 404
        
        # Format cases for summarizer
        cases = []
        for result in search_results:
            case = {
                'text': result.get('document', result.get('text', '')),
                'metadata': result.get('metadata', {})
            }
            cases.append(case)
        
        # Generate summary
        summary = summarizer.summarize_cases(cases, topic)
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@ai_enhancements_bp.route('/research/memo', methods=['POST'])
def generate_research_memo():
    """
    Generate formal legal research memo
    
    Request body:
    {
        "query": "Can IT employee be terminated without notice?",
        "max_cases": 5
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                'error': 'Missing required field: query'
            }), 400
        
        query = data['query']
        max_cases = data.get('max_cases', 5)
        
        # Search for relevant cases
        search_results = vector_db.search(
            query=query,
            top_k=max_cases,
            collection_name='indian_legal_cases'
        )
        
        if not search_results:
            return jsonify({
                'success': False,
                'error': 'No relevant cases found'
            }), 404
        
        # Format cases
        cases = []
        for result in search_results:
            case = {
                'text': result.get('document', ''),
                'metadata': result.get('metadata', {})
            }
            cases.append(case)
        
        # Generate memo
        memo = summarizer.generate_research_memo(query, cases)
        
        return jsonify({
            'success': True,
            'memo': memo,
            'cases_analyzed': len(cases)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@ai_enhancements_bp.route('/research/compare', methods=['POST'])
def compare_cases():
    """
    Compare specific cases side-by-side
    
    Request body:
    {
        "case_ids": ["case1", "case2"],
        "comparison_aspects": ["facts", "law", "outcome", "reasoning"]
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'case_ids' not in data:
            return jsonify({
                'error': 'Missing required field: case_ids'
            }), 400
        
        case_ids = data['case_ids']
        comparison_aspects = data.get('comparison_aspects', ['facts', 'law', 'outcome'])
        
        # Compare cases
        comparison = summarizer.compare_cases(case_ids, comparison_aspects)
        
        return jsonify({
            'success': True,
            'comparison': comparison
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_enhancements_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for AI services"""
    try:
        status = {
            'predictor': {
                'models_loaded': all([
                    predictor.rf_model,
                    predictor.xgb_model,
                    predictor.gb_model
                ]),
                'trained': bool(predictor.training_metrics)
            },
            'drafter': {
                'templates_available': len(drafter.templates)
            },
            'summarizer': {
                'available': True
            },
            'vector_db': {
                'connected': vector_db is not None
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Register blueprint in main app.py
def register_ai_enhancements(app):
    """Register AI enhancements blueprint"""
    app.register_blueprint(ai_enhancements_bp)
    print("✅ AI Enhancements API registered at /api/ai")
