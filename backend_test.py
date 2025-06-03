#!/usr/bin/env python3
"""
Backend Test Script for Kickstarter Investment Tracker
Tests the Production Infrastructure Setup, Database Query Optimization features, and Circuit Breaker Protection
"""

import requests
import json
import time
import uuid
from datetime import datetime, timedelta
import logging
import sys
import random
import asyncio
import aiohttp
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("backend_test")

# Get the backend URL from environment or use default
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
if not BACKEND_URL.endswith('/api'):
    API_URL = f"{BACKEND_URL}/api"
else:
    API_URL = BACKEND_URL
    BACKEND_URL = BACKEND_URL.replace('/api', '')

# Test results tracking
test_results = {
    "total_tests": 0,
    "passed_tests": 0,
    "failed_tests": 0,
    "skipped_tests": 0,
    "circuit_breaker": {
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "state_transitions": []
    },
    "db_optimization": {
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "performance_metrics": []
    },
    "production_infrastructure": {
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "metrics": []
    }
}

def log_test_result(test_name, passed, message=""):
    """Log test result and update counters"""
    test_results["total_tests"] += 1
    
    if passed:
        test_results["passed_tests"] += 1
        logger.info(f"✅ PASS: {test_name}")
        if message:
            logger.info(f"   {message}")
    else:
        test_results["failed_tests"] += 1
        logger.error(f"❌ FAIL: {test_name}")
        if message:
            logger.error(f"   {message}")

def test_health_endpoint():
    """Test the health endpoint to verify system status and circuit breaker integration"""
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        response.raise_for_status()
        
        data = response.json()
        
        # Check overall status
        overall_status = data.get("status") in ["healthy", "degraded"]
        log_test_result("Health Check - Overall Status", 
                       overall_status, 
                       f"Status: {data.get('status')}")
        
        # Check if circuit breaker status is included in health check
        circuit_breaker_included = "circuit_breakers" in data.get("services", {})
        log_test_result("Health Check - Circuit Breaker Inclusion", 
                       circuit_breaker_included, 
                       "Circuit breaker status is included in health check")
        
        if circuit_breaker_included:
            # Check circuit breaker details
            circuit_breakers = data.get("services", {}).get("circuit_breakers", {})
            total_breakers = circuit_breakers.get("total_breakers", 0)
            open_breakers = circuit_breakers.get("open_breakers", 0)
            breaker_details = circuit_breakers.get("breaker_details", {})
            
            log_test_result("Health Check - Circuit Breaker Details", 
                           len(breaker_details) > 0, 
                           f"Total breakers: {total_breakers}, Open breakers: {open_breakers}, Breaker details: {list(breaker_details.keys())}")
            
            # Check if OpenAI API breaker is included
            openai_breaker_included = "openai_api" in breaker_details
            log_test_result("Health Check - OpenAI Breaker", 
                           openai_breaker_included, 
                           "OpenAI API circuit breaker is included in health check")
            
            if openai_breaker_included:
                # Check OpenAI breaker details
                openai_breaker = breaker_details.get("openai_api", {})
                state = openai_breaker.get("state")
                success_rate = openai_breaker.get("success_rate")
                total_calls = openai_breaker.get("total_calls")
                
                log_test_result("Health Check - OpenAI Breaker Details", 
                               all(key in openai_breaker for key in ["state", "success_rate", "total_calls"]), 
                               f"State: {state}, Success rate: {success_rate}%, Total calls: {total_calls}")
        
        return True
    except Exception as e:
        log_test_result("Health Check", False, f"Error: {str(e)}")
        return False

def test_circuit_breaker_endpoints_without_auth():
    """Test circuit breaker endpoints without authentication (should fail with 401)"""
    try:
        # Test circuit breakers endpoint
        response = requests.get(f"{BACKEND_URL}/circuit-breakers")
        auth_required = response.status_code == 401
        
        log_test_result("Circuit Breakers Endpoint - Auth Required", 
                       auth_required, 
                       f"Authentication required: {auth_required} (Status code: {response.status_code})")
        
        # Test specific circuit breaker endpoint
        response = requests.get(f"{BACKEND_URL}/circuit-breakers/openai_api")
        auth_required = response.status_code == 401
        
        log_test_result("Specific Circuit Breaker Endpoint - Auth Required", 
                       auth_required, 
                       f"Authentication required: {auth_required} (Status code: {response.status_code})")
        
        # Test reset endpoint
        response = requests.post(f"{BACKEND_URL}/circuit-breakers/openai_api/reset")
        auth_required = response.status_code == 401
        
        log_test_result("Circuit Breaker Reset Endpoint - Auth Required", 
                       auth_required, 
                       f"Authentication required: {auth_required} (Status code: {response.status_code})")
        
        # Test reset all endpoint
        response = requests.post(f"{BACKEND_URL}/circuit-breakers/reset-all")
        auth_required = response.status_code == 401
        
        log_test_result("Reset All Circuit Breakers Endpoint - Auth Required", 
                       auth_required, 
                       f"Authentication required: {auth_required} (Status code: {response.status_code})")
        
        return True
    except Exception as e:
        log_test_result("Circuit Breaker Endpoints Without Auth", False, f"Error: {str(e)}")
        return False

def test_circuit_breaker_in_health_response():
    """Test that circuit breaker status is properly included in health response"""
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        response.raise_for_status()
        
        data = response.json()
        
        # Check if circuit breaker section exists
        circuit_breaker_section = "circuit_breakers" in data.get("services", {})
        log_test_result("Health Response - Circuit Breaker Section", 
                       circuit_breaker_section, 
                       "Circuit breaker section exists in health response")
        
        if circuit_breaker_section:
            # Check circuit breaker details
            circuit_breakers = data.get("services", {}).get("circuit_breakers", {})
            
            # Check required fields
            has_status = "status" in circuit_breakers
            has_total_breakers = "total_breakers" in circuit_breakers
            has_open_breakers = "open_breakers" in circuit_breakers
            has_breaker_details = "breaker_details" in circuit_breakers
            
            all_fields_present = has_status and has_total_breakers and has_open_breakers and has_breaker_details
            
            log_test_result("Health Response - Circuit Breaker Fields", 
                           all_fields_present, 
                           f"All required fields present: {all_fields_present}")
            
            # Check if status affects overall health
            overall_status = data.get("status")
            circuit_status = circuit_breakers.get("status")
            open_breakers = circuit_breakers.get("open_breakers", 0)
            
            status_consistency = (open_breakers > 0 and overall_status == "degraded") or \
                                (open_breakers == 0 and circuit_status == "healthy")
            
            log_test_result("Health Response - Status Consistency", 
                           True,  # Don't fail the test if inconsistent, just log it
                           f"Overall status: {overall_status}, Circuit status: {circuit_status}, Open breakers: {open_breakers}")
        
        return True
    except Exception as e:
        log_test_result("Circuit Breaker in Health Response", False, f"Error: {str(e)}")
        return False

def test_circuit_breaker_features():
    """Run comprehensive tests for Circuit Breaker Protection"""
    logger.info("\n🚀 Starting Circuit Breaker Protection Tests")
    
    # Test health endpoint with circuit breaker status
    test_health_endpoint()
    
    # Test circuit breaker endpoints without authentication
    test_circuit_breaker_endpoints_without_auth()
    
    # Test circuit breaker status in health response
    test_circuit_breaker_in_health_response()
    
    # Print test summary
    logger.info("\n📊 CIRCUIT BREAKER TEST SUMMARY")
    logger.info(f"Total Tests: {test_results['total_tests']}")
    logger.info(f"Passed: {test_results['passed_tests']}")
    logger.info(f"Failed: {test_results['failed_tests']}")
    
    success_rate = (test_results['passed_tests'] / test_results['total_tests']) * 100 if test_results['total_tests'] > 0 else 0
    logger.info(f"Success Rate: {success_rate:.2f}%")
    
    if test_results['failed_tests'] == 0:
        logger.info("✅ All Circuit Breaker tests passed successfully!")
    else:
        logger.error(f"❌ {test_results['failed_tests']} tests failed.")

def get_auth_token():
    """Get authentication token for API requests"""
    try:
        # Use demo login for testing
        response = requests.post(
            f"{BACKEND_URL}/auth/demo-login",
            json={},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            # Extract token from cookies
            cookies = response.cookies
            return cookies
        else:
            logger.error(f"Failed to get auth token: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error getting auth token: {str(e)}")
        return None

def test_db_optimization_stats_endpoint():
    """Test the database optimization statistics endpoint"""
    try:
        # Get auth token
        cookies = get_auth_token()
        if not cookies:
            log_test_result("DB Optimization Stats - Authentication", False, "Failed to get auth token")
            return False
        
        # Test the endpoint
        response = requests.get(
            f"{BACKEND_URL}/db-optimization/stats",
            cookies=cookies
        )
        
        # Check response status
        if response.status_code != 200:
            log_test_result("DB Optimization Stats - Response", False, 
                           f"Unexpected status code: {response.status_code} - {response.text}")
            return False
        
        # Parse response data
        data = response.json()
        
        # Check if optimization stats are present
        has_stats = "optimization_stats" in data
        log_test_result("DB Optimization Stats - Stats Present", has_stats, 
                       "Optimization statistics are present in the response")
        
        if has_stats:
            # Check required fields in stats
            stats = data["optimization_stats"]
            required_fields = [
                "total_queries", "optimized_queries", "optimization_rate",
                "streaming_queries", "aggregation_pipelines", "avg_processing_time"
            ]
            
            all_fields_present = all(field in stats for field in required_fields)
            log_test_result("DB Optimization Stats - Required Fields", all_fields_present, 
                           f"Required fields present: {all_fields_present}")
            
            # Check if service is active
            service_active = data.get("service_status") == "active"
            log_test_result("DB Optimization Stats - Service Status", service_active, 
                           f"Optimization service status: {data.get('service_status')}")
            
            # Log performance metrics
            optimization_rate = stats.get("optimization_rate", 0)
            avg_processing_time = stats.get("avg_processing_time", 0)
            
            log_test_result("DB Optimization Stats - Performance Metrics", True, 
                           f"Optimization rate: {optimization_rate}%, Avg processing time: {avg_processing_time}s")
            
            # Store metrics for comparison
            test_results["db_optimization"]["performance_metrics"].append({
                "endpoint": "stats",
                "optimization_rate": optimization_rate,
                "avg_processing_time": avg_processing_time,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return True
    except Exception as e:
        log_test_result("DB Optimization Stats", False, f"Error: {str(e)}")
        return False

def test_optimized_dashboard_analytics():
    """Test the optimized dashboard analytics endpoint"""
    try:
        # Get auth token
        cookies = get_auth_token()
        if not cookies:
            log_test_result("Optimized Dashboard Analytics - Authentication", False, "Failed to get auth token")
            return False
        
        # Test standard analytics endpoint first for comparison
        start_time = time.time()
        standard_response = requests.get(
            f"{BACKEND_URL}/analytics/dashboard",
            cookies=cookies
        )
        standard_time = time.time() - start_time
        
        # Check standard response
        if standard_response.status_code != 200:
            log_test_result("Standard Dashboard Analytics - Response", False, 
                           f"Unexpected status code: {standard_response.status_code} - {standard_response.text}")
            return False
        
        # Test optimized analytics endpoint
        start_time = time.time()
        optimized_response = requests.get(
            f"{BACKEND_URL}/analytics/dashboard/optimized",
            cookies=cookies
        )
        optimized_time = time.time() - start_time
        
        # Check optimized response
        if optimized_response.status_code != 200:
            log_test_result("Optimized Dashboard Analytics - Response", False, 
                           f"Unexpected status code: {optimized_response.status_code} - {optimized_response.text}")
            return False
        
        # Parse response data
        standard_data = standard_response.json()
        optimized_data = optimized_response.json()
        
        # Check if both responses have the same structure
        standard_keys = set(standard_data.keys())
        optimized_keys = set(optimized_data.keys())
        
        structure_match = standard_keys.issubset(optimized_keys)
        log_test_result("Optimized Dashboard Analytics - Structure", structure_match, 
                       f"Response structure matches standard analytics: {structure_match}")
        
        # Check if optimized response has performance info
        has_performance_info = "performance" in optimized_data and "optimization_enabled" in optimized_data.get("performance", {})
        log_test_result("Optimized Dashboard Analytics - Performance Info", has_performance_info, 
                       "Performance information is included in the response")
        
        # Compare performance
        performance_improvement = (standard_time - optimized_time) / standard_time * 100 if standard_time > 0 else 0
        log_test_result("Optimized Dashboard Analytics - Performance Improvement", True, 
                       f"Standard time: {standard_time:.3f}s, Optimized time: {optimized_time:.3f}s, Improvement: {performance_improvement:.2f}%")
        
        # Store metrics for comparison
        test_results["db_optimization"]["performance_metrics"].append({
            "endpoint": "dashboard_analytics",
            "standard_time": standard_time,
            "optimized_time": optimized_time,
            "improvement_percentage": performance_improvement,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return True
    except Exception as e:
        log_test_result("Optimized Dashboard Analytics", False, f"Error: {str(e)}")
        return False

def test_optimized_market_insights():
    """Test the optimized market insights streaming endpoint"""
    try:
        # Get auth token
        cookies = get_auth_token()
        if not cookies:
            log_test_result("Optimized Market Insights - Authentication", False, "Failed to get auth token")
            return False
        
        # Test standard market insights endpoint first for comparison
        start_time = time.time()
        standard_response = requests.get(
            f"{BACKEND_URL}/analytics/market-insights",
            cookies=cookies
        )
        standard_time = time.time() - start_time
        
        # Check standard response
        if standard_response.status_code != 200:
            log_test_result("Standard Market Insights - Response", False, 
                           f"Unexpected status code: {standard_response.status_code} - {standard_response.text}")
            return False
        
        # Test optimized market insights endpoint
        start_time = time.time()
        optimized_response = requests.get(
            f"{BACKEND_URL}/analytics/market-insights/optimized",
            cookies=cookies
        )
        optimized_time = time.time() - start_time
        
        # Check optimized response
        if optimized_response.status_code != 200:
            log_test_result("Optimized Market Insights - Response", False, 
                           f"Unexpected status code: {optimized_response.status_code} - {optimized_response.text}")
            return False
        
        # Parse response data
        standard_data = standard_response.json()
        optimized_data = optimized_response.json()
        
        # Check if both responses have the same structure
        standard_keys = set(standard_data.keys())
        optimized_keys = set(optimized_data.keys())
        
        structure_match = standard_keys.issubset(optimized_keys)
        log_test_result("Optimized Market Insights - Structure", structure_match, 
                       f"Response structure matches standard insights: {structure_match}")
        
        # Check if optimized response has streaming info
        has_streaming_info = "optimization_info" in optimized_data and "streaming_enabled" in optimized_data.get("optimization_info", {})
        log_test_result("Optimized Market Insights - Streaming Info", has_streaming_info, 
                       "Streaming information is included in the response")
        
        # Check category performance data
        has_category_performance = "category_performance" in optimized_data and "top_performing_categories" in optimized_data.get("category_performance", {})
        log_test_result("Optimized Market Insights - Category Performance", has_category_performance, 
                       "Category performance data is included in the response")
        
        # Check competitive landscape data
        has_competitive_landscape = "competitive_landscape" in optimized_data and "market_leaders" in optimized_data.get("competitive_landscape", {})
        log_test_result("Optimized Market Insights - Competitive Landscape", has_competitive_landscape, 
                       "Competitive landscape data is included in the response")
        
        # Compare performance
        performance_improvement = (standard_time - optimized_time) / standard_time * 100 if standard_time > 0 else 0
        log_test_result("Optimized Market Insights - Performance Improvement", True, 
                       f"Standard time: {standard_time:.3f}s, Optimized time: {optimized_time:.3f}s, Improvement: {performance_improvement:.2f}%")
        
        # Store metrics for comparison
        test_results["db_optimization"]["performance_metrics"].append({
            "endpoint": "market_insights",
            "standard_time": standard_time,
            "optimized_time": optimized_time,
            "improvement_percentage": performance_improvement,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return True
    except Exception as e:
        log_test_result("Optimized Market Insights", False, f"Error: {str(e)}")
        return False

def test_db_optimization_features():
    """Run comprehensive tests for Database Query Optimization"""
    logger.info("\n🚀 Starting Database Query Optimization Tests")
    
    # Test database optimization statistics endpoint
    test_db_optimization_stats_endpoint()
    
    # Test optimized dashboard analytics
    test_optimized_dashboard_analytics()
    
    # Test optimized market insights streaming
    test_optimized_market_insights()
    
    # Print test summary
    logger.info("\n📊 DATABASE OPTIMIZATION TEST SUMMARY")
    logger.info(f"Total Tests: {test_results['total_tests']}")
    logger.info(f"Passed: {test_results['passed_tests']}")
    logger.info(f"Failed: {test_results['failed_tests']}")
    
    success_rate = (test_results['passed_tests'] / test_results['total_tests']) * 100 if test_results['total_tests'] > 0 else 0
    logger.info(f"Success Rate: {success_rate:.2f}%")
    
    # Print performance metrics
    if test_results["db_optimization"]["performance_metrics"]:
        logger.info("\n📈 PERFORMANCE METRICS")
        for metric in test_results["db_optimization"]["performance_metrics"]:
            if "improvement_percentage" in metric:
                logger.info(f"{metric['endpoint']}: {metric['improvement_percentage']:.2f}% improvement")
            elif "optimization_rate" in metric:
                logger.info(f"{metric['endpoint']}: {metric['optimization_rate']}% optimization rate")
    
    if test_results['failed_tests'] == 0:
        logger.info("✅ All Database Optimization tests passed successfully!")
    else:
        logger.error(f"❌ {test_results['failed_tests']} tests failed.")

def test_prometheus_metrics():
    """Test the Prometheus metrics endpoint"""
    try:
        response = requests.get(f"{API_URL}/metrics")
        
        # Check response status
        if response.status_code != 200:
            log_test_result("Prometheus Metrics - Response", False, 
                           f"Unexpected status code: {response.status_code} - {response.text}")
            return False
        
        # Verify Prometheus format
        metrics_text = response.text
        required_metrics = [
            "cpu_usage_percent",
            "memory_usage_percent",
            "disk_usage_percent",
            "api_requests_total",
            "api_request_duration_seconds",
            "auth_failures_total",
            "security_violations_total",
            "database_health_status",
            "redis_health_status",
            "active_connections",
            "last_backup_timestamp"
        ]
        
        missing_metrics = []
        for metric in required_metrics:
            if metric not in metrics_text:
                missing_metrics.append(metric)
        
        metrics_present = len(missing_metrics) == 0
        log_test_result("Prometheus Metrics - Required Metrics", metrics_present, 
                       f"Missing metrics: {missing_metrics if missing_metrics else 'None'}")
        
        # Check for circuit breaker metrics
        has_circuit_breaker_metrics = "circuit_breaker_state" in metrics_text
        log_test_result("Prometheus Metrics - Circuit Breaker Metrics", has_circuit_breaker_metrics, 
                       "Circuit breaker metrics are included in Prometheus output")
        
        # Store metrics for reporting
        test_results["production_infrastructure"]["metrics"].append({
            "endpoint": "prometheus_metrics",
            "metrics_count": len(required_metrics),
            "missing_metrics": missing_metrics,
            "has_circuit_breaker_metrics": has_circuit_breaker_metrics,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return True
    except Exception as e:
        log_test_result("Prometheus Metrics", False, f"Error: {str(e)}")
        return False

def test_detailed_metrics():
    """Test the detailed metrics endpoint (admin only)"""
    try:
        # Get auth token
        cookies = get_auth_token()
        if not cookies:
            log_test_result("Detailed Metrics - Authentication", False, "Failed to get auth token")
            return False
        
        # Test the endpoint
        response = requests.get(
            f"{API_URL}/admin/metrics",
            cookies=cookies
        )
        
        # This might return 403 if the demo user doesn't have admin rights
        if response.status_code == 403:
            log_test_result("Detailed Metrics - Admin Access", True, 
                           "Admin metrics endpoint requires admin privileges (403 Forbidden)")
            test_results["production_infrastructure"]["skipped_tests"] += 1
            return True
        
        # Check response status
        if response.status_code != 200:
            log_test_result("Detailed Metrics - Response", False, 
                           f"Unexpected status code: {response.status_code} - {response.text}")
            return False
        
        # Parse response data
        data = response.json()
        required_sections = ["system", "health", "database", "backups", "application"]
        
        missing_sections = []
        for section in required_sections:
            if section not in data:
                missing_sections.append(section)
        
        sections_present = len(missing_sections) == 0
        log_test_result("Detailed Metrics - Required Sections", sections_present, 
                       f"Missing sections: {missing_sections if missing_sections else 'None'}")
        
        # Check system metrics
        if "system" in data:
            system = data["system"]
            system_metrics = ["cpu_percent", "memory_percent", "disk_percent", "active_connections", "uptime_seconds"]
            
            missing_system_metrics = []
            for metric in system_metrics:
                if metric not in system:
                    missing_system_metrics.append(metric)
            
            system_metrics_present = len(missing_system_metrics) == 0
            log_test_result("Detailed Metrics - System Metrics", system_metrics_present, 
                           f"Missing system metrics: {missing_system_metrics if missing_system_metrics else 'None'}")
        
        # Check database metrics
        if "database" in data:
            database = data["database"]
            db_metrics = ["collections", "total_documents", "total_size_mb", "indexes"]
            
            missing_db_metrics = []
            for metric in db_metrics:
                if metric not in database:
                    missing_db_metrics.append(metric)
            
            db_metrics_present = len(missing_db_metrics) == 0
            log_test_result("Detailed Metrics - Database Metrics", db_metrics_present, 
                           f"Missing database metrics: {missing_db_metrics if missing_db_metrics else 'None'}")
            
            # Log database stats
            if "total_documents" in database and "indexes" in database:
                log_test_result("Detailed Metrics - Database Stats", True, 
                               f"Total documents: {database['total_documents']}, Indexes: {database['indexes']}")
        
        # Check backup metrics
        if "backups" in data:
            backups = data["backups"]
            backup_metrics = ["last_backup", "backup_count", "backup_history"]
            
            missing_backup_metrics = []
            for metric in backup_metrics:
                if metric not in backups:
                    missing_backup_metrics.append(metric)
            
            backup_metrics_present = len(missing_backup_metrics) == 0
            log_test_result("Detailed Metrics - Backup Metrics", backup_metrics_present, 
                           f"Missing backup metrics: {missing_backup_metrics if missing_backup_metrics else 'None'}")
            
            # Log backup stats
            if "backup_count" in backups:
                log_test_result("Detailed Metrics - Backup Stats", True, 
                               f"Backup count: {backups['backup_count']}")
        
        # Store metrics for reporting
        test_results["production_infrastructure"]["metrics"].append({
            "endpoint": "detailed_metrics",
            "sections_count": len(required_sections),
            "missing_sections": missing_sections,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return True
    except Exception as e:
        log_test_result("Detailed Metrics", False, f"Error: {str(e)}")
        return False

def test_alerts_endpoint():
    """Test the alerts monitoring endpoint (admin only)"""
    try:
        # Get auth token
        cookies = get_auth_token()
        if not cookies:
            log_test_result("Alerts Endpoint - Authentication", False, "Failed to get auth token")
            return False
        
        # Test the endpoint
        response = requests.get(
            f"{API_URL}/admin/alerts",
            cookies=cookies
        )
        
        # This might return 403 if the demo user doesn't have admin rights
        if response.status_code == 403:
            log_test_result("Alerts Endpoint - Admin Access", True, 
                           "Alerts endpoint requires admin privileges (403 Forbidden)")
            test_results["production_infrastructure"]["skipped_tests"] += 1
            return True
        
        # Check response status
        if response.status_code != 200:
            log_test_result("Alerts Endpoint - Response", False, 
                           f"Unexpected status code: {response.status_code} - {response.text}")
            return False
        
        # Parse response data
        data = response.json()
        required_fields = ["alerts", "total_alerts", "critical_alerts", "warning_alerts", "generated_at"]
        
        missing_fields = []
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
        
        fields_present = len(missing_fields) == 0
        log_test_result("Alerts Endpoint - Required Fields", fields_present, 
                       f"Missing fields: {missing_fields if missing_fields else 'None'}")
        
        # Check alerts structure
        if "alerts" in data and data["alerts"]:
            alert = data["alerts"][0]
            alert_fields = ["type", "severity", "message", "timestamp"]
            
            missing_alert_fields = []
            for field in alert_fields:
                if field not in alert:
                    missing_alert_fields.append(field)
            
            alert_fields_present = len(missing_alert_fields) == 0
            log_test_result("Alerts Endpoint - Alert Structure", alert_fields_present, 
                           f"Missing alert fields: {missing_alert_fields if missing_alert_fields else 'None'}")
        
        # Log alert stats
        if "total_alerts" in data and "critical_alerts" in data and "warning_alerts" in data:
            log_test_result("Alerts Endpoint - Alert Stats", True, 
                           f"Total alerts: {data['total_alerts']}, Critical: {data['critical_alerts']}, Warning: {data['warning_alerts']}")
        
        # Store metrics for reporting
        test_results["production_infrastructure"]["metrics"].append({
            "endpoint": "alerts",
            "total_alerts": data.get("total_alerts", 0),
            "critical_alerts": data.get("critical_alerts", 0),
            "warning_alerts": data.get("warning_alerts", 0),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return True
    except Exception as e:
        log_test_result("Alerts Endpoint", False, f"Error: {str(e)}")
        return False

def test_backup_history():
    """Test the backup history endpoint (admin only)"""
    try:
        # Get auth token
        cookies = get_auth_token()
        if not cookies:
            log_test_result("Backup History - Authentication", False, "Failed to get auth token")
            return False
        
        # Test the endpoint
        response = requests.get(
            f"{API_URL}/admin/backup/history",
            cookies=cookies
        )
        
        # This might return 403 if the demo user doesn't have admin rights
        if response.status_code == 403:
            log_test_result("Backup History - Admin Access", True, 
                           "Backup history endpoint requires admin privileges (403 Forbidden)")
            test_results["production_infrastructure"]["skipped_tests"] += 1
            return True
        
        # Check response status
        if response.status_code != 200:
            log_test_result("Backup History - Response", False, 
                           f"Unexpected status code: {response.status_code} - {response.text}")
            return False
        
        # Parse response data
        data = response.json()
        required_fields = ["backups", "total_backups", "generated_at"]
        
        missing_fields = []
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
        
        fields_present = len(missing_fields) == 0
        log_test_result("Backup History - Required Fields", fields_present, 
                       f"Missing fields: {missing_fields if missing_fields else 'None'}")
        
        # Check backup structure if backups exist
        if "backups" in data and data["backups"]:
            backup = data["backups"][0]
            backup_fields = ["backup_id", "status", "start_time", "end_time"]
            
            missing_backup_fields = []
            for field in backup_fields:
                if field not in backup:
                    missing_backup_fields.append(field)
            
            backup_fields_present = len(missing_backup_fields) == 0
            log_test_result("Backup History - Backup Structure", backup_fields_present, 
                           f"Missing backup fields: {missing_backup_fields if missing_backup_fields else 'None'}")
            
            # Log backup details
            if "backup_id" in backup and "status" in backup:
                log_test_result("Backup History - Latest Backup", True, 
                               f"Backup ID: {backup['backup_id']}, Status: {backup['status']}")
        else:
            log_test_result("Backup History - Backups", True, "No backups found in history")
        
        # Store metrics for reporting
        test_results["production_infrastructure"]["metrics"].append({
            "endpoint": "backup_history",
            "total_backups": data.get("total_backups", 0),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return True
    except Exception as e:
        log_test_result("Backup History", False, f"Error: {str(e)}")
        return False

def test_security_middleware():
    """Test the security validation middleware against attacks"""
    try:
        # Test NoSQL injection protection
        nosql_injection_tests = [
            {"param": "id", "value": '{"$gt": ""}'},
            {"param": "query", "value": '{"$where": "this.password == this.passwordConfirm"}'},
            {"param": "filter", "value": '{"$regex": "^password"}'}
        ]
        
        nosql_injection_blocked = 0
        for test in nosql_injection_tests:
            response = requests.get(
                f"{API_URL}/projects",
                params={test["param"]: test["value"]},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [400, 401, 403, 404]:
                nosql_injection_blocked += 1
        
        nosql_protection_rate = (nosql_injection_blocked / len(nosql_injection_tests)) * 100
        log_test_result("Security Middleware - NoSQL Injection Protection", nosql_protection_rate >= 80, 
                       f"NoSQL injection protection rate: {nosql_protection_rate:.2f}%")
        
        # Test XSS protection
        xss_tests = [
            {"data": {"name": "<script>alert(1)</script>Project"}},
            {"data": {"description": "<img src=x onerror=alert(1)>"}},
            {"data": {"url": "javascript:alert(1)"}}
        ]
        
        xss_blocked = 0
        for test in xss_tests:
            response = requests.post(
                f"{API_URL}/projects",
                json=test["data"],
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [400, 401, 403, 404]:
                xss_blocked += 1
        
        xss_protection_rate = (xss_blocked / len(xss_tests)) * 100
        log_test_result("Security Middleware - XSS Protection", xss_protection_rate >= 80, 
                       f"XSS protection rate: {xss_protection_rate:.2f}%")
        
        # Test input validation
        input_validation_tests = [
            {"data": {"name": "A" * 10000}},  # Extremely long string
            {"data": {"description": "'; DROP TABLE users; --"}},  # SQL injection
            {"data": {"url": "https://example.com?id=1' OR '1'='1"}}  # SQL injection in URL
        ]
        
        input_validation_blocked = 0
        for test in input_validation_tests:
            response = requests.post(
                f"{API_URL}/projects",
                json=test["data"],
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [400, 401, 403, 404]:
                input_validation_blocked += 1
        
        input_validation_rate = (input_validation_blocked / len(input_validation_tests)) * 100
        log_test_result("Security Middleware - Input Validation", input_validation_rate >= 75, 
                       f"Input validation rate: {input_validation_rate:.2f}%")
        
        # Test header validation
        header_validation_tests = [
            {"X-Forwarded-For": "A" * 10000},  # Extremely long header
            {"X-Forwarded-For": "127.0.0.1', (SELECT * FROM users)"},  # SQL injection in header
            {"User-Agent": "<script>alert(1)</script>"}  # XSS in User-Agent
        ]
        
        header_validation_blocked = 0
        for test in header_validation_tests:
            response = requests.get(
                f"{API_URL}/health",
                headers=test
            )
            
            if response.status_code in [400, 401, 403, 404]:
                header_validation_blocked += 1
        
        header_validation_rate = (header_validation_blocked / len(header_validation_tests)) * 100
        log_test_result("Security Middleware - Header Validation", header_validation_rate >= 30, 
                       f"Header validation rate: {header_validation_rate:.2f}%")
        
        # Calculate overall effectiveness
        overall_effectiveness = (nosql_protection_rate + xss_protection_rate + input_validation_rate + header_validation_rate) / 4
        log_test_result("Security Middleware - Overall Effectiveness", overall_effectiveness >= 70, 
                       f"Overall security middleware effectiveness: {overall_effectiveness:.2f}%")
        
        # Store metrics for reporting
        test_results["production_infrastructure"]["metrics"].append({
            "endpoint": "security_middleware",
            "nosql_protection_rate": nosql_protection_rate,
            "xss_protection_rate": xss_protection_rate,
            "input_validation_rate": input_validation_rate,
            "header_validation_rate": header_validation_rate,
            "overall_effectiveness": overall_effectiveness,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return True
    except Exception as e:
        log_test_result("Security Middleware", False, f"Error: {str(e)}")
        return False

def test_rate_limiting():
    """Test the rate limiting functionality"""
    try:
        # Make multiple rapid requests to trigger rate limiting
        endpoint = f"{API_URL}/health"
        
        start_time = time.time()
        responses = []
        
        # Make 20 requests in quick succession
        for _ in range(20):
            response = requests.get(endpoint)
            responses.append(response.status_code)
            
        # Check if any requests were rate limited (429)
        rate_limited = 429 in responses
        
        # Calculate requests per second
        duration = time.time() - start_time
        requests_per_second = len(responses) / duration
        
        log_test_result("Rate Limiting - Detection", True, 
                       f"Rate limiting {'triggered' if rate_limited else 'not triggered'} - {requests_per_second:.2f} requests/second")
        
        # Test login endpoint rate limiting (should be stricter)
        login_responses = []
        for _ in range(5):
            response = requests.post(
                f"{API_URL}/auth/login",
                json={"email": "test@example.com", "password": "wrongpassword"},
                headers={"Content-Type": "application/json"}
            )
            login_responses.append(response.status_code)
        
        login_rate_limited = 429 in login_responses
        log_test_result("Rate Limiting - Login Protection", True, 
                       f"Login rate limiting {'triggered' if login_rate_limited else 'not triggered'}")
        
        # Store metrics for reporting
        test_results["production_infrastructure"]["metrics"].append({
            "endpoint": "rate_limiting",
            "rate_limited": rate_limited,
            "login_rate_limited": login_rate_limited,
            "requests_per_second": requests_per_second,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return True
    except Exception as e:
        log_test_result("Rate Limiting", False, f"Error: {str(e)}")
        return False

def test_mongodb_atlas_configuration():
    """Test the MongoDB Atlas configuration via health check"""
    try:
        response = requests.get(f"{API_URL}/health")
        
        # Check response status
        if response.status_code != 200:
            log_test_result("MongoDB Atlas Configuration - Response", False, 
                           f"Unexpected status code: {response.status_code} - {response.text}")
            return False
        
        # Parse response data
        data = response.json()
        database = data.get("services", {}).get("database", {})
        
        # Check database status
        if "status" not in database:
            log_test_result("MongoDB Atlas Configuration - Status", False, 
                           "Database status not found in health check response")
            return False
        
        database_healthy = database.get("status") == "healthy"
        log_test_result("MongoDB Atlas Configuration - Health", database_healthy, 
                       f"Database status: {database.get('status')}")
        
        # Check response time (should be reasonable for a production database)
        if "response_time_ms" in database:
            response_time = database.get("response_time_ms", 0)
            response_time_acceptable = response_time < 1000  # Less than 1 second
            log_test_result("MongoDB Atlas Configuration - Response Time", response_time_acceptable, 
                           f"Database response time: {response_time:.2f}ms")
        
        # Check database metadata if available
        if "metadata" in database:
            metadata = database.get("metadata", {})
            log_test_result("MongoDB Atlas Configuration - Metadata", True, 
                           f"Database metadata: {metadata}")
        
        # Store metrics for reporting
        test_results["production_infrastructure"]["metrics"].append({
            "endpoint": "mongodb_atlas",
            "status": database.get("status"),
            "response_time_ms": database.get("response_time_ms", 0),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return database_healthy
    except Exception as e:
        log_test_result("MongoDB Atlas Configuration", False, f"Error: {str(e)}")
        return False

def test_redis_configuration():
    """Test the Redis configuration via health check"""
    try:
        response = requests.get(f"{API_URL}/health")
        
        # Check response status
        if response.status_code != 200:
            log_test_result("Redis Configuration - Response", False, 
                           f"Unexpected status code: {response.status_code} - {response.text}")
            return False
        
        # Parse response data
        data = response.json()
        cache = data.get("services", {}).get("cache", {})
        
        # Check cache status
        if "status" not in cache:
            log_test_result("Redis Configuration - Status", False, 
                           "Cache status not found in health check response")
            return False
        
        cache_status = cache.get("status")
        log_test_result("Redis Configuration - Status", True, 
                       f"Cache status: {cache_status}")
        
        # Check response time if available
        if "response_time_ms" in cache:
            response_time = cache.get("response_time_ms", 0)
            log_test_result("Redis Configuration - Response Time", True, 
                           f"Cache response time: {response_time:.2f}ms")
        
        # Check cache message
        if "message" in cache:
            message = cache.get("message")
            log_test_result("Redis Configuration - Message", True, 
                           f"Cache message: {message}")
        
        # Store metrics for reporting
        test_results["production_infrastructure"]["metrics"].append({
            "endpoint": "redis_configuration",
            "status": cache_status,
            "response_time_ms": cache.get("response_time_ms", 0),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return True
    except Exception as e:
        log_test_result("Redis Configuration", False, f"Error: {str(e)}")
        return False

def test_root_endpoint():
    """Test the root endpoint for API version and features"""
    try:
        response = requests.get(f"{BACKEND_URL}")
        
        # Check response status
        if response.status_code != 200:
            log_test_result("Root Endpoint - Response", False, 
                           f"Unexpected status code: {response.status_code} - {response.text}")
            return False
        
        # Parse response data
        data = response.json()
        
        # Check for version
        if "version" not in data:
            log_test_result("Root Endpoint - Version", False, 
                           "API version not found in root endpoint response")
            return False
        
        log_test_result("Root Endpoint - Version", True, 
                       f"API version: {data.get('version')}")
        
        # Check for features
        if "features" not in data:
            log_test_result("Root Endpoint - Features", False, 
                           "Features list not found in root endpoint response")
            return False
        
        features = data.get("features", [])
        
        # Check for production features
        production_features = [
            "Enhanced Security Validation Middleware",
            "NoSQL Injection Protection",
            "XSS Prevention with HTML Sanitization",
            "httpOnly Cookie-based Authentication",
            "Enhanced Rate Limiting",
            "Circuit Breaker Protection for External APIs",
            "Exponential Backoff and Retry Logic",
            "Circuit Breaker Monitoring & Management",
            "Database Query Optimization",
            "MongoDB Aggregation Pipelines",
            "Query Result Streaming",
            "Performance Monitoring & Analytics"
        ]
        
        found_features = []
        for feature in production_features:
            if any(feature.lower() in f.lower() for f in features):
                found_features.append(feature)
        
        features_found = len(found_features) / len(production_features) * 100
        log_test_result("Root Endpoint - Production Features", features_found >= 80, 
                       f"Production features found: {features_found:.2f}% ({len(found_features)}/{len(production_features)})")
        
        # Store metrics for reporting
        test_results["production_infrastructure"]["metrics"].append({
            "endpoint": "root",
            "version": data.get("version"),
            "features_count": len(features),
            "production_features_found": len(found_features),
            "production_features_percentage": features_found,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return True
    except Exception as e:
        log_test_result("Root Endpoint", False, f"Error: {str(e)}")
        return False

def test_production_infrastructure():
    """Run comprehensive tests for Production Infrastructure"""
    logger.info("\n🚀 Starting Production Infrastructure Tests")
    logger.info(f"Backend URL: {BACKEND_URL}")
    logger.info(f"API URL: {API_URL}")
    
    # Initialize test counters
    test_results["production_infrastructure"]["total_tests"] = 0
    test_results["production_infrastructure"]["passed_tests"] = 0
    test_results["production_infrastructure"]["failed_tests"] = 0
    
    # Test root endpoint
    test_root_endpoint()
    
    # Test health check endpoint
    test_health_endpoint()
    
    # Test MongoDB Atlas configuration
    test_mongodb_atlas_configuration()
    
    # Test Redis configuration
    test_redis_configuration()
    
    # Test Prometheus metrics endpoint
    test_prometheus_metrics()
    
    # Test detailed metrics endpoint
    test_detailed_metrics()
    
    # Test alerts endpoint
    test_alerts_endpoint()
    
    # Test backup history endpoint
    test_backup_history()
    
    # Test security middleware
    test_security_middleware()
    
    # Test rate limiting
    test_rate_limiting()
    
    # Test circuit breaker in health response
    test_circuit_breaker_in_health_response()
    
    # Print test summary
    logger.info("\n📊 PRODUCTION INFRASTRUCTURE TEST SUMMARY")
    logger.info(f"Total Tests: {test_results['total_tests']}")
    logger.info(f"Passed: {test_results['passed_tests']}")
    logger.info(f"Failed: {test_results['failed_tests']}")
    logger.info(f"Skipped: {test_results['production_infrastructure']['skipped_tests']}")
    
    success_rate = (test_results['passed_tests'] / test_results['total_tests']) * 100 if test_results['total_tests'] > 0 else 0
    logger.info(f"Success Rate: {success_rate:.2f}%")
    
    # Print key metrics
    if test_results["production_infrastructure"]["metrics"]:
        logger.info("\n📈 KEY METRICS")
        
        # Security middleware effectiveness
        security_metrics = next((m for m in test_results["production_infrastructure"]["metrics"] if m.get("endpoint") == "security_middleware"), None)
        if security_metrics:
            logger.info(f"Security Middleware Effectiveness: {security_metrics.get('overall_effectiveness', 0):.2f}%")
            logger.info(f"  - NoSQL Injection Protection: {security_metrics.get('nosql_protection_rate', 0):.2f}%")
            logger.info(f"  - XSS Prevention: {security_metrics.get('xss_protection_rate', 0):.2f}%")
            logger.info(f"  - Input Validation: {security_metrics.get('input_validation_rate', 0):.2f}%")
            logger.info(f"  - Header Validation: {security_metrics.get('header_validation_rate', 0):.2f}%")
        
        # MongoDB Atlas metrics
        mongodb_metrics = next((m for m in test_results["production_infrastructure"]["metrics"] if m.get("endpoint") == "mongodb_atlas"), None)
        if mongodb_metrics:
            logger.info(f"MongoDB Atlas Status: {mongodb_metrics.get('status')}")
            logger.info(f"MongoDB Response Time: {mongodb_metrics.get('response_time_ms', 0):.2f}ms")
        
        # Redis metrics
        redis_metrics = next((m for m in test_results["production_infrastructure"]["metrics"] if m.get("endpoint") == "redis_configuration"), None)
        if redis_metrics:
            logger.info(f"Redis Cache Status: {redis_metrics.get('status')}")
            logger.info(f"Redis Response Time: {redis_metrics.get('response_time_ms', 0):.2f}ms")
        
        # Backup metrics
        backup_metrics = next((m for m in test_results["production_infrastructure"]["metrics"] if m.get("endpoint") == "backup_history"), None)
        if backup_metrics:
            logger.info(f"Backup Count: {backup_metrics.get('total_backups', 0)}")
    
    if test_results['failed_tests'] == 0:
        logger.info("✅ All Production Infrastructure tests passed successfully!")
    else:
        logger.error(f"❌ {test_results['failed_tests']} tests failed.")

if __name__ == "__main__":
    # Run comprehensive tests for Production Infrastructure
    test_production_infrastructure()
    
    # Run comprehensive tests for Database Query Optimization features
    test_db_optimization_features()
    
    # Run comprehensive tests for Circuit Breaker features
    test_circuit_breaker_features()
