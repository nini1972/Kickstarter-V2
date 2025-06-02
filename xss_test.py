#!/usr/bin/env python3
"""
XSS Prevention Test Script
Tests the XSS prevention capabilities of the SecurityValidationMiddleware
"""

import requests
import json
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("xss_test")

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

def test_xss_prevention():
    """Test XSS prevention in request bodies"""
    logger.info("\n🧪 Testing XSS Prevention")
    
    # XSS attack patterns to test
    xss_patterns = [
        "<script>alert('XSS')</script>",
        "<img src='x' onerror='alert(\"XSS\")'>",
        "<body onload='alert(\"XSS\")'>",
        "<svg/onload=alert('XSS')>",
        "<iframe src='javascript:alert(\"XSS\")'></iframe>",
        "<a href='javascript:alert(\"XSS\")'>Click me</a>",
        "javascript:alert('XSS')",
        "<div style='background-image:url(javascript:alert(\"XSS\"))'></div>",
        "<input type='text' onfocus='alert(\"XSS\")' autofocus>",
        "<marquee onstart='alert(\"XSS\")'></marquee>"
    ]
    
    # Test XSS patterns in JSON values
    for i, pattern in enumerate(xss_patterns):
        try:
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
                f"XSS Prevention - Pattern {i+1}: '{pattern[:20]}...'", 
                response.status_code == 400,
                f"Status code: {response.status_code}, Response: {response.text[:100]}..."
            )
        except Exception as e:
            log_test_result(
                f"XSS Prevention - Pattern {i+1}: '{pattern[:20]}...'", 
                False, 
                f"Error: {str(e)}"
            )
    
    # Test XSS patterns in query parameters
    for i, pattern in enumerate(xss_patterns[:3]):  # Test a subset to avoid too many requests
        try:
            test_url = f"{BACKEND_URL}/projects?description={pattern}"
            
            response = requests.get(test_url)
            
            log_test_result(
                f"XSS Prevention - Query Parameter {i+1}: '{pattern[:20]}...'", 
                response.status_code == 400,
                f"Status code: {response.status_code}, Response: {response.text[:100]}..."
            )
        except Exception as e:
            log_test_result(
                f"XSS Prevention - Query Parameter {i+1}: '{pattern[:20]}...'", 
                False, 
                f"Error: {str(e)}"
            )

def run_xss_tests():
    """Run XSS prevention tests"""
    logger.info("🚀 Starting XSS Prevention Tests")
    logger.info(f"🔗 Testing API at: {BACKEND_URL}")
    
    test_xss_prevention()
    
    # Print test summary
    logger.info("\n📊 XSS TEST SUMMARY")
    logger.info(f"Total Tests: {test_results['total_tests']}")
    logger.info(f"Passed: {test_results['passed_tests']}")
    logger.info(f"Failed: {test_results['failed_tests']}")
    
    # Overall success rate
    success_rate = (test_results['passed_tests'] / test_results['total_tests']) * 100 if test_results['total_tests'] > 0 else 0
    logger.info(f"Success Rate: {success_rate:.2f}%")
    
    if test_results['failed_tests'] == 0:
        logger.info("✅ All XSS tests passed successfully!")
    else:
        logger.error(f"❌ {test_results['failed_tests']} tests failed.")

if __name__ == "__main__":
    run_xss_tests()
