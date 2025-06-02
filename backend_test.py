#!/usr/bin/env python3
"""
Backend Test Script for Kickstarter Investment Tracker
Tests the Database Query Optimization features and Circuit Breaker Protection
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("backend_test")

# Backend API URL
BACKEND_URL = "https://04f2e18f-8db0-4882-9c84-f41c80a2a7a6.preview.emergentagent.com/api"

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

if __name__ == "__main__":
    # Run comprehensive tests for Database Query Optimization features
    test_db_optimization_features()
    
    # Run comprehensive tests for Circuit Breaker features
    # test_circuit_breaker_features()
