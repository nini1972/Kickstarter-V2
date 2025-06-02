#!/usr/bin/env python3
"""
Header Validation Test Script
Tests the header validation capabilities of the SecurityValidationMiddleware
"""

import requests
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
logger = logging.getLogger("header_test")

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

def test_header_validation():
    """Test header validation"""
    logger.info("\n🧪 Testing Header Validation")
    
    try:
        # Test oversized headers
        oversized_header_value = generate_random_string(5000)  # 5KB header value
        
        response = requests.get(
            f"{BACKEND_URL}/health",
            headers={"X-Custom-Header": oversized_header_value}
        )
        
        log_test_result(
            "Header Validation - Oversized Header", 
            response.status_code == 400,
            f"Status code: {response.status_code}, Response: {response.text[:100]}..."
        )
        
        # Test suspicious forwarding headers
        suspicious_headers = {
            "X-Forwarded-Host": "malicious-site.com",
            "X-Originating-IP": "1.2.3.4",
            "X-Remote-IP": "5.6.7.8"
        }
        
        for header_name, header_value in suspicious_headers.items():
            response = requests.get(
                f"{BACKEND_URL}/health",
                headers={header_name: header_value}
            )
            
            # These headers might be logged but not blocked, so we're just checking if the request succeeds
            log_test_result(
                f"Header Validation - Suspicious Header '{header_name}'", 
                response.status_code != 500,  # Should not cause a server error
                f"Status code: {response.status_code}, Response: {response.text[:100]}..."
            )
        
        # Test dangerous characters in headers
        dangerous_headers = {
            "X-Custom-Header-1": "<script>alert('XSS')</script>",
            "X-Custom-Header-2": "javascript:alert('XSS')",
            "X-Custom-Header-3": "'; DROP TABLE users; --"
        }
        
        for header_name, header_value in dangerous_headers.items():
            response = requests.get(
                f"{BACKEND_URL}/health",
                headers={header_name: header_value}
            )
            
            log_test_result(
                f"Header Validation - Dangerous Header Value '{header_value[:20]}...'", 
                response.status_code == 400,
                f"Status code: {response.status_code}, Response: {response.text[:100]}..."
            )
        
        # Test very long header name
        long_header_name = "X-" + generate_random_string(200)
        
        response = requests.get(
            f"{BACKEND_URL}/health",
            headers={long_header_name: "test value"}
        )
        
        log_test_result(
            "Header Validation - Very Long Header Name", 
            response.status_code == 400,
            f"Status code: {response.status_code}, Response: {response.text[:100]}..."
        )
        
        return True
    except Exception as e:
        log_test_result(
            "Header Validation", 
            False, 
            f"Error: {str(e)}"
        )
        return False

def run_header_tests():
    """Run header validation tests"""
    logger.info("🚀 Starting Header Validation Tests")
    logger.info(f"🔗 Testing API at: {BACKEND_URL}")
    
    test_header_validation()
    
    # Print test summary
    logger.info("\n📊 HEADER TEST SUMMARY")
    logger.info(f"Total Tests: {test_results['total_tests']}")
    logger.info(f"Passed: {test_results['passed_tests']}")
    logger.info(f"Failed: {test_results['failed_tests']}")
    
    # Overall success rate
    success_rate = (test_results['passed_tests'] / test_results['total_tests']) * 100 if test_results['total_tests'] > 0 else 0
    logger.info(f"Success Rate: {success_rate:.2f}%")
    
    if test_results['failed_tests'] == 0:
        logger.info("✅ All header validation tests passed successfully!")
    else:
        logger.error(f"❌ {test_results['failed_tests']} tests failed.")

if __name__ == "__main__":
    run_header_tests()
