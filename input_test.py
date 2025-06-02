#!/usr/bin/env python3
"""
Input Validation Test Script
Tests the input validation capabilities of the SecurityValidationMiddleware
"""

import requests
import json
import logging
import sys
import random
import string

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("input_test")

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

def generate_random_string(length):
    """Generate a random string of specified length"""
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

def test_input_validation():
    """Test input validation for various types of inputs"""
    logger.info("\n🧪 Testing Input Validation")
    
    try:
        # Test extremely long strings
        long_string = generate_random_string(15000)  # 15KB string
        
        test_data = {
            "name": "Test Project",
            "description": long_string
        }
        
        response = requests.post(
            f"{BACKEND_URL}/projects", 
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        log_test_result(
            "Input Validation - Extremely Long String", 
            response.status_code == 400,
            f"Status code: {response.status_code}, Response: {response.text[:100]}..."
        )
        
        # Test unusual characters
        unusual_chars = "ÿØÿà\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00ÿÛ\x00C\x00"
        
        test_data = {
            "name": "Test Project",
            "description": unusual_chars
        }
        
        response = requests.post(
            f"{BACKEND_URL}/projects", 
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        log_test_result(
            "Input Validation - Unusual Characters", 
            response.status_code == 400,
            f"Status code: {response.status_code}, Response: {response.text[:100]}..."
        )
        
        # Test SQL injection patterns
        sql_injection_patterns = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "1'; INSERT INTO users VALUES ('hacker', 'password'); --",
            "1' UNION SELECT username, password FROM users; --",
            "1' OR 1=1; --"
        ]
        
        for i, pattern in enumerate(sql_injection_patterns):
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
                f"Input Validation - SQL Injection {i+1}: '{pattern}'", 
                response.status_code == 400,
                f"Status code: {response.status_code}, Response: {response.text[:100]}..."
            )
        
        # Test invalid parameter names
        test_url = f"{BACKEND_URL}/projects?invalid-param!@#$%^&*()=value"
        
        response = requests.get(test_url)
        
        log_test_result(
            "Input Validation - Invalid Parameter Name", 
            response.status_code == 400,
            f"Status code: {response.status_code}, Response: {response.text[:100]}..."
        )
        
        # Test extremely long parameter values
        long_param_value = generate_random_string(10000)  # 10KB parameter value
        test_url = f"{BACKEND_URL}/projects?description={long_param_value}"
        
        response = requests.get(test_url)
        
        log_test_result(
            "Input Validation - Extremely Long Parameter Value", 
            response.status_code == 400,
            f"Status code: {response.status_code}, Response: {response.text[:100]}..."
        )
        
        return True
    except Exception as e:
        log_test_result(
            "Input Validation", 
            False, 
            f"Error: {str(e)}"
        )
        return False

def run_input_tests():
    """Run input validation tests"""
    logger.info("🚀 Starting Input Validation Tests")
    logger.info(f"🔗 Testing API at: {BACKEND_URL}")
    
    test_input_validation()
    
    # Print test summary
    logger.info("\n📊 INPUT TEST SUMMARY")
    logger.info(f"Total Tests: {test_results['total_tests']}")
    logger.info(f"Passed: {test_results['passed_tests']}")
    logger.info(f"Failed: {test_results['failed_tests']}")
    
    # Overall success rate
    success_rate = (test_results['passed_tests'] / test_results['total_tests']) * 100 if test_results['total_tests'] > 0 else 0
    logger.info(f"Success Rate: {success_rate:.2f}%")
    
    if test_results['failed_tests'] == 0:
        logger.info("✅ All input validation tests passed successfully!")
    else:
        logger.error(f"❌ {test_results['failed_tests']} tests failed.")

if __name__ == "__main__":
    run_input_tests()
