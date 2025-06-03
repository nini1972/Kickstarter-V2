"""
📊 Metrics API Endpoints
Production monitoring and metrics collection for Prometheus
"""

import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse

from database.connection import get_database
from services.monitoring_service import monitoring_service
from services.backup_service import backup_service
from middleware.auth_middleware import verify_admin_token

router = APIRouter(prefix="/api", tags=["metrics"])

# Prometheus metrics storage
metrics_data = {
    "requests_total": 0,
    "requests_duration_sum": 0.0,
    "auth_failures_total": 0,
    "security_violations_total": 0,
    "circuit_breaker_states": {},
    "last_backup_timestamp": 0,
    "database_health": 1,
    "redis_health": 1
}

@router.get("/metrics", response_class=PlainTextResponse)
async def get_prometheus_metrics():
    """
    Prometheus metrics endpoint in the expected format
    
    Returns:
        Prometheus-formatted metrics
    """
    # Get current system metrics
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Get application metrics
    current_time = time.time()
    
    # Format metrics for Prometheus
    metrics_lines = [
        "# HELP cpu_usage_percent Current CPU usage percentage",
        "# TYPE cpu_usage_percent gauge",
        f"cpu_usage_percent {cpu_percent}",
        "",
        "# HELP memory_usage_percent Current memory usage percentage", 
        "# TYPE memory_usage_percent gauge",
        f"memory_usage_percent {memory.percent}",
        "",
        "# HELP disk_usage_percent Current disk usage percentage",
        "# TYPE disk_usage_percent gauge", 
        f"disk_usage_percent {disk.percent}",
        "",
        "# HELP api_requests_total Total number of API requests",
        "# TYPE api_requests_total counter",
        f"api_requests_total {metrics_data['requests_total']}",
        "",
        "# HELP api_request_duration_seconds API request duration",
        "# TYPE api_request_duration_seconds histogram",
        f"api_request_duration_seconds_sum {metrics_data['requests_duration_sum']}",
        f"api_request_duration_seconds_count {metrics_data['requests_total']}",
        "",
        "# HELP auth_failures_total Total authentication failures",
        "# TYPE auth_failures_total counter",
        f"auth_failures_total {metrics_data['auth_failures_total']}",
        "",
        "# HELP security_violations_total Total security violations",
        "# TYPE security_violations_total counter", 
        f"security_violations_total {metrics_data['security_violations_total']}",
        "",
        "# HELP database_health_status Database health status (1=healthy, 0=unhealthy)",
        "# TYPE database_health_status gauge",
        f"database_health_status {metrics_data['database_health']}",
        "",
        "# HELP redis_health_status Redis health status (1=healthy, 0=unhealthy)",
        "# TYPE redis_health_status gauge",
        f"redis_health_status {metrics_data['redis_health']}",
        "",
        "# HELP active_connections Current number of active connections",
        "# TYPE active_connections gauge",
        f"active_connections {len(psutil.net_connections())}",
        "",
        "# HELP last_backup_timestamp Unix timestamp of last successful backup",
        "# TYPE last_backup_timestamp gauge",
        f"last_backup_timestamp {metrics_data['last_backup_timestamp']}",
        ""
    ]
    
    # Add circuit breaker metrics
    for service, state in metrics_data["circuit_breaker_states"].items():
        metrics_lines.extend([
            f"# HELP circuit_breaker_state Circuit breaker state for {service} (0=closed, 1=open, 2=half-open)",
            f"# TYPE circuit_breaker_state gauge",
            f'circuit_breaker_state{{service="{service}"}} {state}',
            ""
        ])
    
    return "\n".join(metrics_lines)

@router.get("/admin/metrics", dependencies=[Depends(verify_admin_token)])
async def get_detailed_metrics(database=Depends(get_database)):
    """
    Get detailed application metrics for monitoring dashboards
    
    Returns:
        Comprehensive metrics data
    """
    # Get comprehensive health check
    health_data = await monitoring_service.perform_comprehensive_health_check()
    
    # Get system metrics
    system_metrics = monitoring_service.get_system_metrics()
    
    # Get backup history
    backup_history = await backup_service.get_backup_history(limit=10)
    
    # Get database statistics
    db_stats = await _get_database_statistics(database)
    
    # Compile detailed metrics
    detailed_metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "system": {
            "cpu_percent": system_metrics.cpu_percent,
            "memory_percent": system_metrics.memory_percent,
            "disk_percent": system_metrics.disk_percent,
            "active_connections": system_metrics.active_connections,
            "uptime_seconds": time.time() - psutil.boot_time()
        },
        "health": health_data,
        "database": db_stats,
        "backups": {
            "last_backup": backup_history[0] if backup_history else None,
            "backup_count": len(backup_history),
            "backup_history": backup_history
        },
        "application": {
            "requests_total": metrics_data["requests_total"],
            "average_response_time": (
                metrics_data["requests_duration_sum"] / metrics_data["requests_total"]
                if metrics_data["requests_total"] > 0 else 0
            ),
            "auth_failures": metrics_data["auth_failures_total"],
            "security_violations": metrics_data["security_violations_total"]
        },
        "circuit_breakers": metrics_data["circuit_breaker_states"]
    }
    
    return detailed_metrics

@router.get("/admin/alerts", dependencies=[Depends(verify_admin_token)])
async def get_active_alerts():
    """
    Get currently active alerts and warnings
    
    Returns:
        List of active alerts
    """
    alerts = []
    
    # Check system thresholds
    system_metrics = monitoring_service.get_system_metrics()
    
    if system_metrics.cpu_percent > 80:
        alerts.append({
            "type": "high_cpu_usage",
            "severity": "warning",
            "message": f"CPU usage is {system_metrics.cpu_percent:.1f}%",
            "value": system_metrics.cpu_percent,
            "threshold": 80,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    if system_metrics.memory_percent > 85:
        alerts.append({
            "type": "high_memory_usage", 
            "severity": "warning",
            "message": f"Memory usage is {system_metrics.memory_percent:.1f}%",
            "value": system_metrics.memory_percent,
            "threshold": 85,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    if system_metrics.disk_percent > 90:
        alerts.append({
            "type": "low_disk_space",
            "severity": "critical",
            "message": f"Disk usage is {system_metrics.disk_percent:.1f}%",
            "value": system_metrics.disk_percent,
            "threshold": 90,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # Check service health
    health_data = await monitoring_service.perform_comprehensive_health_check()
    
    for service_name, service_data in health_data.get("services", {}).items():
        if service_data.get("status") == "unhealthy":
            alerts.append({
                "type": "service_unhealthy",
                "severity": "critical",
                "service": service_name,
                "message": f"{service_name} service is unhealthy",
                "timestamp": datetime.utcnow().isoformat()
            })
        elif service_data.get("status") == "degraded":
            alerts.append({
                "type": "service_degraded",
                "severity": "warning", 
                "service": service_name,
                "message": f"{service_name} service is degraded",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    return {
        "alerts": alerts,
        "total_alerts": len(alerts),
        "critical_alerts": len([a for a in alerts if a["severity"] == "critical"]),
        "warning_alerts": len([a for a in alerts if a["severity"] == "warning"]),
        "generated_at": datetime.utcnow().isoformat()
    }

@router.post("/admin/backup", dependencies=[Depends(verify_admin_token)])
async def trigger_backup():
    """
    Manually trigger a full backup
    
    Returns:
        Backup operation result
    """
    try:
        backup_result = await backup_service.create_full_backup()
        
        # Update metrics
        if backup_result["status"] == "success":
            metrics_data["last_backup_timestamp"] = time.time()
        
        return backup_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")

@router.get("/admin/backup/history", dependencies=[Depends(verify_admin_token)])
async def get_backup_history():
    """
    Get backup history
    
    Returns:
        List of backup records
    """
    try:
        history = await backup_service.get_backup_history(limit=50)
        return {
            "backups": history,
            "total_backups": len(history),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get backup history: {str(e)}")

async def _get_database_statistics(database) -> Dict[str, Any]:
    """
    Get database statistics for monitoring
    
    Args:
        database: Database connection
        
    Returns:
        Database statistics
    """
    try:
        stats = {
            "collections": {},
            "total_documents": 0,
            "total_size_mb": 0,
            "indexes": 0
        }
        
        # Get collection names
        collection_names = await database.list_collection_names()
        
        for collection_name in collection_names:
            if collection_name.startswith('system.'):
                continue
                
            collection = database.get_collection(collection_name)
            
            # Get document count
            doc_count = await collection.count_documents({})
            
            # Get collection stats (if available)
            try:
                coll_stats = await database.command("collStats", collection_name)
                size_mb = coll_stats.get("size", 0) / (1024 * 1024)
                index_count = coll_stats.get("nindexes", 0)
            except:
                size_mb = 0
                index_count = 0
            
            stats["collections"][collection_name] = {
                "document_count": doc_count,
                "size_mb": round(size_mb, 2),
                "indexes": index_count
            }
            
            stats["total_documents"] += doc_count
            stats["total_size_mb"] += size_mb
            stats["indexes"] += index_count
        
        stats["total_size_mb"] = round(stats["total_size_mb"], 2)
        
        return stats
        
    except Exception as e:
        return {
            "error": f"Failed to get database statistics: {str(e)}",
            "collections": {},
            "total_documents": 0,
            "total_size_mb": 0,
            "indexes": 0
        }

# Middleware functions to update metrics
def increment_request_count():
    """Increment total request count"""
    metrics_data["requests_total"] += 1

def add_request_duration(duration: float):
    """Add request duration to metrics"""
    metrics_data["requests_duration_sum"] += duration

def increment_auth_failures():
    """Increment authentication failure count"""
    metrics_data["auth_failures_total"] += 1

def increment_security_violations():
    """Increment security violation count"""
    metrics_data["security_violations_total"] += 1

def update_circuit_breaker_state(service: str, state: int):
    """Update circuit breaker state (0=closed, 1=open, 2=half-open)"""
    metrics_data["circuit_breaker_states"][service] = state

def update_service_health(service: str, healthy: bool):
    """Update service health status"""
    if service == "database":
        metrics_data["database_health"] = 1 if healthy else 0
    elif service == "redis":
        metrics_data["redis_health"] = 1 if healthy else 0
