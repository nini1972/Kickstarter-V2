#!/usr/bin/env python3
"""
NoSQL Injection Test Script
Tests the NoSQL injection prevention capabilities of the SecurityValidationMiddleware
"""

import requests
import json
import logging
import sys
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("nosql_test")

# Backend API URL
BACKEND_URL = "http://localhost:8001/api"

# Test results tracking
test_results = {
    "total_tests": 0,
    "passed_tests": 0,
    "failed_tests": 0
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

def test_nosql_injection_query_params():
    """Test NoSQL injection in query parameters"""
    logger.info("\n🧪 Testing NoSQL Injection in Query Parameters")
    
    # MongoDB operators to test
    mongo_operators = [
        "$where", "$regex", "$ne", "$gt", "$gte", "$lt", "$lte", "$in", 
        "$nin", "$exists", "$type", "$mod", "$all"
    ]
    
    # NoSQL injection patterns
    nosql_patterns = [
        "this.password.match(/.*/)=true",
        "{$where: 'sleep(10000)'}", 
        "db.collection.find({$where: function() { return 1; }})",
        "'; return '' == '",
        "'; return this.password == 'password' || '1'=='1"
    ]
    
    # Test endpoints that accept query parameters
    endpoints = [
        "/projects", 
        "/investments",
        "/health"
    ]
    
    try:
        # Test MongoDB operators
        for i, operator in enumerate(mongo_operators):
            endpoint = random.choice(endpoints)
            test_url = f"{BACKEND_URL}{endpoint}?query={operator}"
            
            response = requests.get(test_url)
            
            log_test_result(
                f"NoSQL Injection - MongoDB Operator {i+1}: '{operator}'", 
                response.status_code == 400,
                f"Status code: {response.status_code}, Response: {response.text[:100]}..."
            )
        
        # Test NoSQL injection patterns
        for i, pattern in enumerate(nosql_patterns):
            endpoint = random.choice(endpoints)
            test_url = f"{BACKEND_URL}{endpoint}?query={pattern}"
            
            response = requests.get(test_url)
            
            log_test_result(
                f"NoSQL Injection - Pattern {i+1}: '{pattern[:20]}...'", 
                response.status_code == 400,
                f"Status code: {response.status_code}, Response: {response.text[:100]}..."
            )
        
        return True
    except Exception as e:
        log_test_result(
            "NoSQL Injection - Query Parameters", 
            False, 
            f"Error: {str(e)}"
        )
        return False

def test_nosql_injection_json_body():
    """Test NoSQL injection in JSON request body"""
    logger.info("\n🧪 Testing NoSQL Injection in JSON Body")
    
    # MongoDB operators to test in JSON keys and values
    mongo_operators = [
        "$where", "$regex", "$ne", "$gt", "$gte", "$lt", "$lte"
    ]
    
    # NoSQL injection patterns for values
    nosql_patterns = [
        "this.password.match(/.*/)=true",
        "function() { return 1; }",
        "'; return '' == '",
        "'; return this.password == 'password' || '1'=='1"
    ]
    
    try:
        # Test MongoDB operators in JSON keys
        for i, operator in enumerate(mongo_operators):
            test_data = {
                "name": "Test Project",
                f"{operator}": "This is a test with MongoDB operator in key"
            }
            
            response = requests.post(
                f"{BACKEND_URL}/projects", 
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            log_test_result(
                f"NoSQL Injection - JSON Key {i+1}: '{operator}'", 
                response.status_code == 400,
                f"Status code: {response.status_code}, Response: {response.text[:100]}..."
            )
        
        # Test MongoDB operators in JSON values
        for i, operator in enumerate(mongo_operators):
            test_data = {
                "name": f"Test Project with {operator}",
                "description": f"This is a test with MongoDB operator {operator} in value"
            }
            
            response = requests.post(
                f"{BACKEND_URL}/projects", 
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            log_test_result(
                f"NoSQL Injection - JSON Value {i+1}: '{operator}'", 
                response.status_code == 400,
                f"Status code: {response.status_code}, Response: {response.text[:100]}..."
            )
        
        # Test NoSQL injection patterns in JSON values
        for i, pattern in enumerate(nosql_patterns):
            test_data = {
                "name": "Test Project",
                "description": pattern
            }
            
            response = requests.post(
                f"{BACKEND_URL}/projects", 
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            log_test_result(
                f"NoSQL Injection - JSON Pattern {i+1}: '{pattern[:20]}...'", 
                response.status_code == 400,
                f"Status code: {response.status_code}, Response: {response.text[:100]}..."
            )
        
        # Test nested JSON with MongoDB operators
        test_data = {
            "name": "Test Project",
            "metadata": {
                "$where": "function() { return 1; }"
            }
        }
        
        response = requests.post(
            f"{BACKEND_URL}/projects", 
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        log_test_result(
            "NoSQL Injection - Nested JSON with MongoDB Operator", 
            response.status_code == 400,
            f"Status code: {response.status_code}, Response: {response.text[:100]}..."
        )
        
        return True
    except Exception as e:
        log_test_result(
            "NoSQL Injection - JSON Body", 
            False, 
            f"Error: {str(e)}"
        )
        return False

def run_nosql_tests():
    """Run NoSQL injection tests"""
    logger.info("🚀 Starting NoSQL Injection Tests")
    logger.info(f"🔗 Testing API at: {BACKEND_URL}")
    
    test_nosql_injection_query_params()
    test_nosql_injection_json_body()
    
    # Print test summary
    logger.info("\n📊 NOSQL TEST SUMMARY")
    logger.info(f"Total Tests: {test_results['total_tests']}")
    logger.info(f"Passed: {test_results['passed_tests']}")
    logger.info(f"Failed: {test_results['failed_tests']}")
    
    # Overall success rate
    success_rate = (test_results['passed_tests'] / test_results['total_tests']) * 100 if test_results['total_tests'] > 0 else 0
    logger.info(f"Success Rate: {success_rate:.2f}%")
    
    if test_results['failed_tests'] == 0:
        logger.info("✅ All NoSQL injection tests passed successfully!")
    else:
        logger.error(f"❌ {test_results['failed_tests']} tests failed.")

if __name__ == "__main__":
    run_nosql_tests()
