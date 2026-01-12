"""
Admin Dashboard Blueprint
Provides administrative interface for monitoring and management
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import func
from models import db, User, ChatSession, Message, CaseSummary, ResponseRating, UserPreference
from logging_config import get_logger

logger = get_logger(__name__)

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Simple admin authentication decorator
def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Simple check - you can enhance this with proper JWT/session auth
        auth_token = request.headers.get('X-Admin-Token') or request.cookies.get('admin_token')
        if auth_token != 'admin_secret_2026':  # Change this to proper auth
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
def dashboard():
    """Main admin dashboard"""
    return render_template('admin/dashboard.html')


@admin_bp.route('/api/stats')
def get_stats():
    """Get system statistics"""
    try:
        # User statistics
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        users_today = User.query.filter(
            User.created_at >= datetime.utcnow() - timedelta(days=1)
        ).count()
        
        # Session statistics
        total_sessions = ChatSession.query.count()
        sessions_today = ChatSession.query.filter(
            ChatSession.created_at >= datetime.utcnow() - timedelta(days=1)
        ).count()
        
        # Message statistics
        total_messages = Message.query.count()
        messages_today = Message.query.filter(
            Message.timestamp >= datetime.utcnow() - timedelta(days=1)
        ).count()
        
        # Summary statistics
        total_summaries = CaseSummary.query.count()
        summaries_today = CaseSummary.query.filter(
            CaseSummary.created_at >= datetime.utcnow() - timedelta(days=1)
        ).count()
        
        # Summary type distribution
        summary_types = db.session.query(
            CaseSummary.summary_type,
            func.count(CaseSummary.id).label('count')
        ).group_by(CaseSummary.summary_type).all()
        
        # Rating statistics
        total_ratings = ResponseRating.query.count()
        avg_rating = db.session.query(func.avg(ResponseRating.rating)).scalar() or 0
        
        return jsonify({
            'success': True,
            'stats': {
                'users': {
                    'total': total_users,
                    'active': active_users,
                    'today': users_today
                },
                'sessions': {
                    'total': total_sessions,
                    'today': sessions_today
                },
                'messages': {
                    'total': total_messages,
                    'today': messages_today,
                    'avg_per_session': round(total_messages / total_sessions, 2) if total_sessions > 0 else 0
                },
                'summaries': {
                    'total': total_summaries,
                    'today': summaries_today,
                    'by_type': {st[0]: st[1] for st in summary_types}
                },
                'ratings': {
                    'total': total_ratings,
                    'average': round(float(avg_rating), 2)
                }
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/users')
def get_users():
    """Get list of users"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        users_query = User.query.order_by(User.created_at.desc())
        users_paginated = users_query.paginate(page=page, per_page=per_page, error_out=False)
        
        users_data = []
        for user in users_paginated.items:
            session_count = ChatSession.query.filter_by(user_id=user.id).count()
            message_count = db.session.query(func.count(Message.id)).join(
                ChatSession
            ).filter(ChatSession.user_id == user.id).scalar()
            
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'session_count': session_count,
                'message_count': message_count or 0
            })
        
        return jsonify({
            'success': True,
            'users': users_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': users_paginated.total,
                'pages': users_paginated.pages
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/summaries')
def get_summaries():
    """Get recent case summaries"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        summaries = CaseSummary.query.order_by(
            CaseSummary.created_at.desc()
        ).limit(limit).all()
        
        summaries_data = []
        for summary in summaries:
            summaries_data.append({
                'id': summary.id,
                'case_id': summary.case_id,
                'case_title': summary.case_title,
                'summary_type': summary.summary_type,
                'length': summary.length,
                'word_count': summary.word_count,
                'court': summary.court,
                'year': summary.year,
                'created_at': summary.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'summaries': summaries_data
        })
    
    except Exception as e:
        logger.error(f"Error getting summaries: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/activity')
def get_activity():
    """Get recent activity timeline"""
    try:
        limit = request.args.get('limit', 20, type=int)
        
        activities = []
        
        # Recent users
        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        for user in recent_users:
            activities.append({
                'type': 'user_registered',
                'timestamp': user.created_at.isoformat(),
                'description': f"New user registered: {user.username}",
                'icon': '👤'
            })
        
        # Recent sessions
        recent_sessions = ChatSession.query.order_by(ChatSession.created_at.desc()).limit(5).all()
        for session in recent_sessions:
            activities.append({
                'type': 'session_started',
                'timestamp': session.created_at.isoformat(),
                'description': f"Chat session started: {session.title or 'Untitled'}",
                'icon': '💬'
            })
        
        # Recent summaries
        recent_summaries = CaseSummary.query.order_by(CaseSummary.created_at.desc()).limit(5).all()
        for summary in recent_summaries:
            activities.append({
                'type': 'summary_generated',
                'timestamp': summary.created_at.isoformat(),
                'description': f"Case summary generated: {summary.case_title or summary.case_id}",
                'icon': '📝'
            })
        
        # Sort all activities by timestamp
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        activities = activities[:limit]
        
        return jsonify({
            'success': True,
            'activities': activities
        })
    
    except Exception as e:
        logger.error(f"Error getting activity: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/popular-cases')
def get_popular_cases():
    """Get most frequently summarized cases"""
    try:
        popular_cases = db.session.query(
            CaseSummary.case_id,
            CaseSummary.case_title,
            CaseSummary.court,
            CaseSummary.year,
            func.count(CaseSummary.id).label('count')
        ).group_by(
            CaseSummary.case_id,
            CaseSummary.case_title,
            CaseSummary.court,
            CaseSummary.year
        ).order_by(
            func.count(CaseSummary.id).desc()
        ).limit(10).all()
        
        cases_data = []
        for case in popular_cases:
            cases_data.append({
                'case_id': case.case_id,
                'case_title': case.case_title,
                'court': case.court,
                'year': case.year,
                'summary_count': case.count
            })
        
        return jsonify({
            'success': True,
            'cases': cases_data
        })
    
    except Exception as e:
        logger.error(f"Error getting popular cases: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/system-health')
def system_health():
    """Get system health metrics"""
    try:
        import psutil
        import sys
        
        # Database info
        db_size = 0
        try:
            import os
            db_path = 'instance/legal_chatbot.db'
            if os.path.exists(db_path):
                db_size = os.path.getsize(db_path)
        except:
            pass
        
        health_data = {
            'database': {
                'status': 'operational',
                'size_bytes': db_size,
                'size_mb': round(db_size / (1024*1024), 2)
            },
            'system': {
                'python_version': sys.version,
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent
            }
        }
        
        return jsonify({
            'success': True,
            'health': health_data
        })
    
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
