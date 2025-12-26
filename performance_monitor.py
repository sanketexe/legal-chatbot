"""
Comprehensive Performance Monitoring and Analytics System
"""

import time
import json
import logging
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import sqlite3
import os

@dataclass
class PerformanceMetric:
    """Single performance metric"""
    timestamp: datetime
    metric_name: str
    value: float
    metadata: Dict[str, Any] = None

@dataclass
class SystemSnapshot:
    """System performance snapshot"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    active_connections: int

class PerformanceMonitor:
    """Comprehensive performance monitoring system"""
    
    def __init__(self, db_path: str = "performance_monitor.db"):
        """Initialize performance monitor"""
        self.db_path = db_path
        self.logger = self._setup_logging()
        
        # Metrics storage
        self.metrics_buffer = deque(maxlen=1000)
        self.system_snapshots = deque(maxlen=100)
        
        # Performance counters
        self.request_counters = defaultdict(int)
        self.response_times = defaultdict(list)
        self.error_counts = defaultdict(int)
        
        # Monitoring flags
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Thresholds for alerts
        self.thresholds = {
            'response_time_ms': 2000,
            'error_rate_percent': 5.0,
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_percent': 90.0
        }
        
        self._setup_database()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging"""
        logger = logging.getLogger('PerformanceMonitor')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler('performance_monitor.log')
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _setup_database(self):
        """Setup SQLite database for metrics storage"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    metadata TEXT
                )
            ''')
            
            # Create system snapshots table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    cpu_percent REAL NOT NULL,
                    memory_percent REAL NOT NULL,
                    memory_used_mb REAL NOT NULL,
                    disk_usage_percent REAL NOT NULL,
                    active_connections INTEGER
                )
            ''')
            
            # Create performance summary table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    avg_response_time REAL,
                    total_requests INTEGER,
                    error_rate REAL,
                    peak_cpu REAL,
                    peak_memory REAL
                )
            ''')
            
            conn.commit()
            conn.close()
            
            self.logger.info("Performance monitoring database initialized")
            
        except Exception as e:
            self.logger.error(f"Database setup failed: {e}")
    
    def start_monitoring(self, interval: int = 30):
        """Start background system monitoring"""
        if self.monitoring_active:
            self.logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        
        self.logger.info(f"Performance monitoring started (interval: {interval}s)")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring_active = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        self.logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self, interval: int):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                snapshot = self._collect_system_snapshot()
                self.system_snapshots.append(snapshot)
                
                # Store in database
                self._store_system_snapshot(snapshot)
                
                # Check for alerts
                self._check_alerts(snapshot)
                
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                time.sleep(interval)
    
    def _collect_system_snapshot(self) -> SystemSnapshot:
        """Collect current system performance snapshot"""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / (1024 * 1024)
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        
        # Network connections (approximate)
        connections = len(psutil.net_connections())
        
        return SystemSnapshot(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            disk_usage_percent=disk_percent,
            active_connections=connections
        )
    
    def _store_system_snapshot(self, snapshot: SystemSnapshot):
        """Store system snapshot in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO system_snapshots 
                (timestamp, cpu_percent, memory_percent, memory_used_mb, 
                 disk_usage_percent, active_connections)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                snapshot.timestamp.isoformat(),
                snapshot.cpu_percent,
                snapshot.memory_percent,
                snapshot.memory_used_mb,
                snapshot.disk_usage_percent,
                snapshot.active_connections
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to store system snapshot: {e}")
    
    def record_metric(
        self, 
        name: str, 
        value: float, 
        metadata: Dict[str, Any] = None
    ):
        """Record a custom performance metric"""
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            metric_name=name,
            value=value,
            metadata=metadata or {}
        )
        
        self.metrics_buffer.append(metric)
        self._store_metric(metric)
    
    def _store_metric(self, metric: PerformanceMetric):
        """Store metric in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO metrics (timestamp, metric_name, value, metadata)
                VALUES (?, ?, ?, ?)
            ''', (
                metric.timestamp.isoformat(),
                metric.metric_name,
                metric.value,
                json.dumps(metric.metadata) if metric.metadata else None
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to store metric: {e}")
    
    def track_request(
        self, 
        endpoint: str, 
        response_time: float, 
        status_code: int = 200
    ):
        """Track API request performance"""
        # Count requests
        self.request_counters[endpoint] += 1
        
        # Track response times
        self.response_times[endpoint].append(response_time)
        
        # Track errors
        if status_code >= 400:
            self.error_counts[endpoint] += 1
        
        # Record metrics
        self.record_metric(f"response_time_{endpoint}", response_time * 1000)  # Convert to ms
        
        if status_code >= 400:
            self.record_metric(f"error_{endpoint}", 1)
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for the last N hours"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            since_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            # Get system performance
            cursor.execute('''
                SELECT 
                    AVG(cpu_percent) as avg_cpu,
                    MAX(cpu_percent) as max_cpu,
                    AVG(memory_percent) as avg_memory,
                    MAX(memory_percent) as max_memory,
                    AVG(active_connections) as avg_connections
                FROM system_snapshots
                WHERE timestamp > ?
            ''', (since_time,))
            
            system_stats = cursor.fetchone()
            
            # Get response time metrics
            cursor.execute('''
                SELECT 
                    AVG(value) as avg_response_time,
                    MAX(value) as max_response_time,
                    COUNT(*) as total_requests
                FROM metrics
                WHERE metric_name LIKE 'response_time_%' 
                AND timestamp > ?
            ''', (since_time,))
            
            response_stats = cursor.fetchone()
            
            # Get error metrics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_errors
                FROM metrics
                WHERE metric_name LIKE 'error_%'
                AND timestamp > ?
            ''', (since_time,))
            
            error_stats = cursor.fetchone()
            
            conn.close()
            
            # Calculate derived metrics
            error_rate = 0
            if response_stats[2] > 0:  # total_requests
                error_rate = (error_stats[0] / response_stats[2]) * 100
            
            return {
                'period_hours': hours,
                'system_performance': {
                    'avg_cpu_percent': round(system_stats[0] or 0, 2),
                    'max_cpu_percent': round(system_stats[1] or 0, 2),
                    'avg_memory_percent': round(system_stats[2] or 0, 2),
                    'max_memory_percent': round(system_stats[3] or 0, 2),
                    'avg_connections': round(system_stats[4] or 0, 2)
                },
                'api_performance': {
                    'avg_response_time_ms': round(response_stats[0] or 0, 2),
                    'max_response_time_ms': round(response_stats[1] or 0, 2),
                    'total_requests': response_stats[2] or 0,
                    'total_errors': error_stats[0] or 0,
                    'error_rate_percent': round(error_rate, 2)
                },
                'health_status': self._get_health_status(system_stats, error_rate)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get performance summary: {e}")
            return {}
    
    def _get_health_status(self, system_stats: tuple, error_rate: float) -> str:
        """Determine overall system health status"""
        if not system_stats or any(stat is None for stat in system_stats[:4]):
            return 'unknown'
        
        avg_cpu, max_cpu, avg_memory, max_memory = system_stats[:4]
        
        # Check critical thresholds
        if (max_cpu > self.thresholds['cpu_percent'] or 
            max_memory > self.thresholds['memory_percent'] or
            error_rate > self.thresholds['error_rate_percent']):
            return 'critical'
        
        # Check warning thresholds
        if (avg_cpu > self.thresholds['cpu_percent'] * 0.8 or
            avg_memory > self.thresholds['memory_percent'] * 0.8 or
            error_rate > self.thresholds['error_rate_percent'] * 0.5):
            return 'warning'
        
        return 'healthy'
    
    def _check_alerts(self, snapshot: SystemSnapshot):
        """Check for performance alerts"""
        alerts = []
        
        # CPU alert
        if snapshot.cpu_percent > self.thresholds['cpu_percent']:
            alerts.append(f"High CPU usage: {snapshot.cpu_percent:.1f}%")
        
        # Memory alert
        if snapshot.memory_percent > self.thresholds['memory_percent']:
            alerts.append(f"High memory usage: {snapshot.memory_percent:.1f}%")
        
        # Disk alert
        if snapshot.disk_usage_percent > self.thresholds['disk_percent']:
            alerts.append(f"High disk usage: {snapshot.disk_usage_percent:.1f}%")
        
        # Log alerts
        if alerts:
            for alert in alerts:
                self.logger.warning(f"ALERT: {alert}")
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get current real-time metrics"""
        try:
            current_snapshot = self._collect_system_snapshot()
            
            # Recent response times (last 10)
            recent_response_times = []
            for response_list in self.response_times.values():
                recent_response_times.extend(response_list[-10:])
            
            avg_response_time = 0
            if recent_response_times:
                avg_response_time = sum(recent_response_times) / len(recent_response_times)
            
            return {
                'timestamp': current_snapshot.timestamp.isoformat(),
                'system': asdict(current_snapshot),
                'api': {
                    'avg_response_time_ms': round(avg_response_time * 1000, 2),
                    'total_requests': sum(self.request_counters.values()),
                    'total_errors': sum(self.error_counts.values())
                },
                'health_status': self._get_health_status(
                    (current_snapshot.cpu_percent, 
                     current_snapshot.cpu_percent,
                     current_snapshot.memory_percent, 
                     current_snapshot.memory_percent), 
                    0
                )
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get real-time metrics: {e}")
            return {}
    
    def export_metrics(self, output_file: str, hours: int = 24):
        """Export metrics to JSON file"""
        try:
            summary = self.get_performance_summary(hours)
            
            with open(output_file, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            
            self.logger.info(f"Metrics exported to {output_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to export metrics: {e}")
    
    def cleanup_old_data(self, days: int = 30):
        """Clean up old performance data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Clean metrics
            cursor.execute('DELETE FROM metrics WHERE timestamp < ?', (cutoff_date,))
            
            # Clean snapshots
            cursor.execute('DELETE FROM system_snapshots WHERE timestamp < ?', (cutoff_date,))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Cleaned up data older than {days} days")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")

# Flask integration decorator
def monitor_performance(monitor: PerformanceMonitor):
    """Decorator to monitor Flask route performance"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            endpoint = f.__name__
            status_code = 200
            
            try:
                result = f(*args, **kwargs)
                return result
            except Exception as e:
                status_code = 500
                raise
            finally:
                response_time = time.time() - start_time
                monitor.track_request(endpoint, response_time, status_code)
        
        return wrapper
    return decorator