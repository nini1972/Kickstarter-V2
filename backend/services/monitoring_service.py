"""
📊 Production Monitoring Service
Enterprise-grade monitoring, health checks, and observability
"""

import asyncio
import logging
import time
import psutil
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import aioredis
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health check status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class ServiceHealth:
    """Service health status data class"""
    name: str
    status: HealthStatus
    response_time_ms: float
    message: str
    timestamp: datetime
    metadata: Dict[str, Any] = None

@dataclass
class SystemMetrics:
    """System performance metrics data class"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    active_connections: int
    timestamp: datetime

class MonitoringService:
    """Comprehensive monitoring service for production deployment"""
    
    def __init__(self, database=None, redis_client=None):
        self.database = database
        self.redis_client = redis_client
        self.health_checks = {}
        self.metrics_history = []
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0,
            "response_time_ms": 5000.0,
            "error_rate": 5.0
        }
        
    async def check_database_health(self) -> ServiceHealth:
        """
        Check MongoDB database health and performance
        
        Returns:
            ServiceHealth object with database status
        """
        start_time = time.time()
        
        try:
            if not self.database:
                return ServiceHealth(
                    name="database",
                    status=HealthStatus.UNKNOWN,
                    response_time_ms=0,
                    message="Database connection not configured",
                    timestamp=datetime.utcnow()
                )
            
            # Perform health check query
            health_collection = self.database.get_collection("health_check")
            test_doc = {"test": "health_check", "timestamp": datetime.utcnow()}
            
            # Insert and retrieve test document
            result = await health_collection.insert_one(test_doc)
            retrieved = await health_collection.find_one({"_id": result.inserted_id})
            await health_collection.delete_one({"_id": result.inserted_id})
            
            response_time = (time.time() - start_time) * 1000
            
            if retrieved:
                return ServiceHealth(
                    name="database",
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    message="Database connection successful",
                    timestamp=datetime.utcnow(),
                    metadata={
                        "write_successful": True,
                        "read_successful": True,
                        "cleanup_successful": True
                    }
                )
            else:
                return ServiceHealth(
                    name="database",
                    status=HealthStatus.DEGRADED,
                    response_time_ms=response_time,
                    message="Database write successful but read failed",
                    timestamp=datetime.utcnow()
                )
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Database health check failed: {e}")
            
            return ServiceHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message=f"Database health check failed: {str(e)}",
                timestamp=datetime.utcnow()
            )
    
    async def check_redis_health(self) -> ServiceHealth:
        """
        Check Redis cache health and performance
        
        Returns:
            ServiceHealth object with Redis status
        """
        start_time = time.time()
        
        try:
            if not self.redis_client:
                return ServiceHealth(
                    name="redis",
                    status=HealthStatus.UNKNOWN,
                    response_time_ms=0,
                    message="Redis connection not configured",
                    timestamp=datetime.utcnow()
                )
            
            # Test Redis operations
            test_key = "health_check:test"
            test_value = f"health_check_{int(time.time())}"
            
            # Set, get, and delete test key
            await self.redis_client.set(test_key, test_value, ex=60)
            retrieved_value = await self.redis_client.get(test_key)
            await self.redis_client.delete(test_key)
            
            response_time = (time.time() - start_time) * 1000
            
            if retrieved_value and retrieved_value.decode() == test_value:
                return ServiceHealth(
                    name="redis",
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    message="Redis cache operations successful",
                    timestamp=datetime.utcnow(),
                    metadata={
                        "set_successful": True,
                        "get_successful": True,
                        "delete_successful": True
                    }
                )
            else:
                return ServiceHealth(
                    name="redis",
                    status=HealthStatus.DEGRADED,
                    response_time_ms=response_time,
                    message="Redis operations partially failed",
                    timestamp=datetime.utcnow()
                )
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Redis health check failed: {e}")
            
            return ServiceHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message=f"Redis health check failed: {str(e)}",
                timestamp=datetime.utcnow()
            )
    
    async def check_external_apis_health(self) -> List[ServiceHealth]:
        """
        Check external API dependencies health
        
        Returns:
            List of ServiceHealth objects for external services
        """
        health_checks = []
        
        # OpenAI API health check
        start_time = time.time()
        try:
            # Simple health check - just verify API key format
            import os
            api_key = os.environ.get('OPENAI_API_KEY', '')
            
            if api_key.startswith('sk-') and len(api_key) > 20:
                response_time = (time.time() - start_time) * 1000
                health_checks.append(ServiceHealth(
                    name="openai_api",
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    message="OpenAI API key configured",
                    timestamp=datetime.utcnow(),
                    metadata={"api_key_valid": True}
                ))
            else:
                health_checks.append(ServiceHealth(
                    name="openai_api",
                    status=HealthStatus.DEGRADED,
                    response_time_ms=0,
                    message="OpenAI API key not properly configured",
                    timestamp=datetime.utcnow(),
                    metadata={"api_key_valid": False}
                ))
                
        except Exception as e:
            health_checks.append(ServiceHealth(
                name="openai_api",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                message=f"OpenAI API check failed: {str(e)}",
                timestamp=datetime.utcnow()
            ))
        
        return health_checks
    
    def get_system_metrics(self) -> SystemMetrics:
        """
        Get current system performance metrics
        
        Returns:
            SystemMetrics object with current system status
        """
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Network connections (approximate active connections)
            connections = len(psutil.net_connections())
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                active_connections=connections,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return SystemMetrics(
                cpu_percent=0,
                memory_percent=0,
                disk_percent=0,
                active_connections=0,
                timestamp=datetime.utcnow()
            )
    
    async def perform_comprehensive_health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check of all services
        
        Returns:
            Comprehensive health status report
        """
        start_time = time.time()
        
        # Run all health checks in parallel
        database_health_task = self.check_database_health()
        redis_health_task = self.check_redis_health()
        external_apis_task = self.check_external_apis_health()
        
        # Wait for all health checks to complete
        database_health = await database_health_task
        redis_health = await redis_health_task
        external_apis_health = await external_apis_task
        
        # Get system metrics
        system_metrics = self.get_system_metrics()
        
        # Compile health report
        services = {
            "database": asdict(database_health),
            "redis": asdict(redis_health),
            "system": asdict(system_metrics)
        }
        
        # Add external APIs
        for api_health in external_apis_health:
            services[api_health.name] = asdict(api_health)
        
        # Determine overall health status
        overall_status = self._determine_overall_health(
            [database_health, redis_health] + external_apis_health
        )
        
        # Check for alerts
        alerts = self._check_alert_conditions(system_metrics, services)
        
        total_time = (time.time() - start_time) * 1000
        
        health_report = {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "response_time_ms": total_time,
            "services": services,
            "alerts": alerts,
            "summary": {
                "total_services": len(services),
                "healthy_services": len([s for s in services.values() 
                                       if s.get('status') == HealthStatus.HEALTHY.value]),
                "degraded_services": len([s for s in services.values() 
                                        if s.get('status') == HealthStatus.DEGRADED.value]),
                "unhealthy_services": len([s for s in services.values() 
                                         if s.get('status') == HealthStatus.UNHEALTHY.value])
            }
        }
        
        # Store health check result
        await self._store_health_check_result(health_report)
        
        return health_report
    
    def _determine_overall_health(self, health_checks: List[ServiceHealth]) -> HealthStatus:
        """
        Determine overall system health based on individual service health
        
        Args:
            health_checks: List of service health checks
            
        Returns:
            Overall health status
        """
        if not health_checks:
            return HealthStatus.UNKNOWN
        
        unhealthy_count = sum(1 for h in health_checks if h.status == HealthStatus.UNHEALTHY)
        degraded_count = sum(1 for h in health_checks if h.status == HealthStatus.DEGRADED)
        
        # If any critical service is unhealthy, overall is unhealthy
        if unhealthy_count > 0:
            return HealthStatus.UNHEALTHY
        
        # If any service is degraded, overall is degraded
        if degraded_count > 0:
            return HealthStatus.DEGRADED
        
        # All services healthy
        return HealthStatus.HEALTHY
    
    def _check_alert_conditions(self, metrics: SystemMetrics, services: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check for alert conditions based on metrics and thresholds
        
        Args:
            metrics: System metrics
            services: Service health data
            
        Returns:
            List of active alerts
        """
        alerts = []
        
        # CPU usage alert
        if metrics.cpu_percent > self.alert_thresholds["cpu_percent"]:
            alerts.append({
                "type": "high_cpu_usage",
                "severity": "warning",
                "message": f"CPU usage is {metrics.cpu_percent:.1f}%",
                "threshold": self.alert_thresholds["cpu_percent"],
                "current_value": metrics.cpu_percent
            })
        
        # Memory usage alert
        if metrics.memory_percent > self.alert_thresholds["memory_percent"]:
            alerts.append({
                "type": "high_memory_usage",
                "severity": "warning",
                "message": f"Memory usage is {metrics.memory_percent:.1f}%",
                "threshold": self.alert_thresholds["memory_percent"],
                "current_value": metrics.memory_percent
            })
        
        # Disk usage alert
        if metrics.disk_percent > self.alert_thresholds["disk_percent"]:
            alerts.append({
                "type": "high_disk_usage",
                "severity": "critical",
                "message": f"Disk usage is {metrics.disk_percent:.1f}%",
                "threshold": self.alert_thresholds["disk_percent"],
                "current_value": metrics.disk_percent
            })
        
        # Service response time alerts
        for service_name, service_data in services.items():
            response_time = service_data.get('response_time_ms', 0)
            if response_time > self.alert_thresholds["response_time_ms"]:
                alerts.append({
                    "type": "slow_service_response",
                    "severity": "warning",
                    "service": service_name,
                    "message": f"{service_name} response time is {response_time:.1f}ms",
                    "threshold": self.alert_thresholds["response_time_ms"],
                    "current_value": response_time
                })
        
        return alerts
    
    async def _store_health_check_result(self, health_report: Dict[str, Any]) -> None:
        """
        Store health check result for historical analysis
        
        Args:
            health_report: Health check report to store
        """
        try:
            if self.database:
                health_collection = self.database.get_collection("health_checks")
                
                # Store with TTL of 7 days
                health_report["expires_at"] = datetime.utcnow() + timedelta(days=7)
                
                await health_collection.insert_one(health_report)
                
        except Exception as e:
            logger.error(f"Failed to store health check result: {e}")
    
    async def get_health_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get health check history for the specified time period
        
        Args:
            hours: Number of hours of history to retrieve
            
        Returns:
            List of historical health check results
        """
        try:
            if not self.database:
                return []
            
            health_collection = self.database.get_collection("health_checks")
            since = datetime.utcnow() - timedelta(hours=hours)
            
            cursor = health_collection.find(
                {"timestamp": {"$gte": since.isoformat()}},
                {"_id": 0}
            ).sort("timestamp", -1)
            
            history = await cursor.to_list(length=1000)
            return history
            
        except Exception as e:
            logger.error(f"Failed to get health history: {e}")
            return []

# Global monitoring service instance
monitoring_service = MonitoringService()
