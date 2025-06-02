#!/usr/bin/env python3
"""
Security Validation Middleware Test Script
Tests the newly integrated SecurityValidationMiddleware in the FastAPI backend
"""

import requests
import json
import logging
import sys
import time
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
logger = logging.getLogger("security_test")

# Backend API URL
BACKEND_URL = "http://localhost:8001/api"

# Test results tracking
test_results = {
    "total_tests": 0,
    "passed_tests": 0,
    "failed_tests": 0,
    "skipped_tests": 0,
    "categories": {
        "nosql_injection": {"passed": 0, "failed": 0},
        "xss_prevention": {"passed": 0, "failed": 0},
        "header_validation": {"passed": 0, "failed": 0},
        "input_validation": {"passed": 0, "failed": 0},
        "general_security": {"passed": 0, "failed": 0}
    }
}

def log_test_result(test_name, category, passed, message=""):
    """Log test result and update counters"""
    test_results["total_tests"] += 1
    
    if passed:
        test_results["passed_tests"] += 1
        test_results["categories"][category]["passed"] += 1
        logger.info(f"✅ PASS: {test_name}")
        if message:
            logger.info(f"   {message}")
    else:
        test_results["failed_tests"] += 1
        test_results["categories"][category]["failed"] += 1
        logger.error(f"❌ FAIL: {test_name}")
        if message:
            logger.error(f"   {message}")

def generate_random_string(length):
    """Generate a random string of specified length"""
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

def test_legitimate_request():
    """Test that legitimate requests still work properly"""
    logger.info("\n🧪 Testing Legitimate Request")
    
    try:
        # Make a simple GET request to the health endpoint
        response = requests.get(f"{BACKEND_URL}/health")
        
        log_test_result(
            "Legitimate GET Request", 
            "general_security",
            response.status_code == 200,
            f"Status code: {response.status_code}, Response: {response.text[:100]}..."
        )
        
        # Make a legitimate POST request with valid JSON
        valid_data = {
            "name": "Test Project",
            "description": "This is a legitimate test project",
            "category": "Technology",
            "goal_amount": 10000
        }
        
        response = requests.post(
            f"{BACKEND_URL}/projects", 
            json=valid_data,
            headers={"Content-Type": "application/json"}
        )
        
        # We don't care about the actual response code (could be 401 if auth is required)
        # We just want to make sure it's not a 400 Bad Request from the security middleware
        log_test_result(
            "Legitimate POST Request", 
            "general_security",
            response.status_code != 400,
            f"Status code: {response.status_code}, Response: {response.text[:100]}..."
        )
        
        return True
    except Exception as e:
        log_test_result(
            "Legitimate Request", 
            "general_security",
            False, 
            f"Error: {str(e)}"
        )
        return False

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
        for operator in mongo_operators:
            endpoint = random.choice(endpoints)
            test_url = f"{BACKEND_URL}{endpoint}?query={operator}"
            
            response = requests.get(test_url)
            
            log_test_result(
                f"NoSQL Injection - MongoDB Operator '{operator}'", 
                "nosql_injection",
                response.status_code == 400,
                f"Status code: {response.status_code}, Response: {response.text[:100]}..."
            )
        
        # Test NoSQL injection patterns
        for pattern in nosql_patterns:
            endpoint = random.choice(endpoints)
            test_url = f"{BACKEND_URL}{endpoint}?query={pattern}"
            
            response = requests.get(test_url)
            
            log_test_result(
                f"NoSQL Injection - Pattern '{pattern[:20]}...'", 
                "nosql_injection",
                response.status_code == 400,
                f"Status code: {response.status_code}, Response: {response.text[:100]}..."
            )
        
        return True
    except Exception as e:
        log_test_result(
            "NoSQL Injection - Query Parameters", 
            "nosql_injection",
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
        for operator in mongo_operators:
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
                f"NoSQL Injection - JSON Key with '{operator}'", 
                "nosql_injection",
                response.status_code == 400,
                f"Status code: {response.status_code}, Response: {response.text[:100]}..."
            )
        
        # Test MongoDB operators in JSON values
        for operator in mongo_operators:
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
                f"NoSQL Injection - JSON Value with '{operator}'", 
                "nosql_injection",
                response.status_code == 400,
                f"Status code: {response.status_code}, Response: {response.text[:100]}..."
            )
        
        # Test NoSQL injection patterns in JSON values
        for pattern in nosql_patterns:
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
                f"NoSQL Injection - JSON Value with Pattern '{pattern[:20]}...'", 
                "nosql_injection",
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
            "nosql_injection",
            response.status_code == 400,
            f"Status code: {response.status_code}, Response: {response.text[:100]}..."
        )
        
        return True
    except Exception as e:
        log_test_result(
            "NoSQL Injection - JSON Body", 
            "nosql_injection",
            False, 
            f"Error: {str(e)}"
        )
        return False

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
    
    try:
        # Test XSS patterns in JSON values
        for pattern in xss_patterns:
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
                f"XSS Prevention - Pattern '{pattern[:20]}...'", 
                "xss_prevention",
                response.status_code == 400,
                f"Status code: {response.status_code}, Response: {response.text[:100]}..."
            )
        
        # Test XSS patterns in query parameters
        for pattern in xss_patterns[:3]:  # Test a subset to avoid too many requests
            test_url = f"{BACKEND_URL}/projects?description={pattern}"
            
            response = requests.get(test_url)
            
            log_test_result(
                f"XSS Prevention - Query Parameter '{pattern[:20]}...'", 
                "xss_prevention",
                response.status_code == 400,
                f"Status code: {response.status_code}, Response: {response.text[:100]}..."
            )
        
        return True
    except Exception as e:
        log_test_result(
            "XSS Prevention", 
            "xss_prevention",
            False, 
            f"Error: {str(e)}"
        )
        return False

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
            "header_validation",
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
                "header_validation",
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
                "header_validation",
                response.status_code == 400,
                f"Status code: {response.status_code}, Response: {response.text[:100]}..."
            )
        
        return True
    except Exception as e:
        log_test_result(
            "Header Validation", 
            "header_validation",
            False, 
            f"Error: {str(e)}"
        )
        return False

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
            "input_validation",
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
            "input_validation",
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
        
        for pattern in sql_injection_patterns:
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
                f"Input Validation - SQL Injection '{pattern}'", 
                "input_validation",
                response.status_code == 400,
                f"Status code: {response.status_code}, Response: {response.text[:100]}..."
            )
        
        # Test invalid parameter names
        test_url = f"{BACKEND_URL}/projects?invalid-param!@#$%^&*()=value"
        
        response = requests.get(test_url)
        
        log_test_result(
            "Input Validation - Invalid Parameter Name", 
            "input_validation",
            response.status_code == 400,
            f"Status code: {response.status_code}, Response: {response.text[:100]}..."
        )
        
        return True
    except Exception as e:
        log_test_result(
            "Input Validation", 
            "input_validation",
            False, 
            f"Error: {str(e)}"
        )
        return False

def test_general_security():
    """Test general security features"""
    logger.info("\n🧪 Testing General Security Features")
    
    try:
        # Test invalid JSON
        invalid_json = "{name: 'Test Project', description: 'Invalid JSON'}"  # Missing quotes around keys
        
        response = requests.post(
            f"{BACKEND_URL}/projects", 
            data=invalid_json,
            headers={"Content-Type": "application/json"}
        )
        
        log_test_result(
            "General Security - Invalid JSON", 
            "general_security",
            response.status_code == 400,
            f"Status code: {response.status_code}, Response: {response.text[:100]}..."
        )
        
        # Test unsupported content type
        response = requests.post(
            f"{BACKEND_URL}/projects", 
            data="<project><name>Test Project</name></project>",
            headers={"Content-Type": "application/xml"}
        )
        
        # This might be handled by FastAPI before our middleware, so we're just checking if it doesn't cause a server error
        log_test_result(
            "General Security - Unsupported Content Type", 
            "general_security",
            response.status_code != 500,
            f"Status code: {response.status_code}, Response: {response.text[:100]}..."
        )
        
        # Test invalid HTTP method
        try:
            response = requests.request(
                "INVALID", 
                f"{BACKEND_URL}/health"
            )
            
            log_test_result(
                "General Security - Invalid HTTP Method", 
                "general_security",
                response.status_code == 405,
                f"Status code: {response.status_code}, Response: {response.text[:100]}..."
            )
        except requests.exceptions.InvalidSchema:
            # This is expected as 'INVALID' is not a valid HTTP method
            log_test_result(
                "General Security - Invalid HTTP Method", 
                "general_security",
                True,
                "Request library rejected invalid method as expected"
            )
        
        return True
    except Exception as e:
        log_test_result(
            "General Security", 
            "general_security",
            False, 
            f"Error: {str(e)}"
        )
        return False

def run_all_security_tests():
    """Run all security validation tests"""
    logger.info("🚀 Starting Security Validation Middleware Tests")
    logger.info(f"🔗 Testing API at: {BACKEND_URL}")
    
    # First test legitimate requests to make sure the middleware isn't blocking valid traffic
    test_legitimate_request()
    
    # Test NoSQL injection
    test_nosql_injection_query_params()
    test_nosql_injection_json_body()
    
    # Test XSS prevention
    test_xss_prevention()
    
    # Test header validation
    test_header_validation()
    
    # Test input validation
    test_input_validation()
    
    # Test general security features
    test_general_security()
    
    # Print test summary
    logger.info("\n📊 SECURITY TEST SUMMARY")
    logger.info(f"Total Tests: {test_results['total_tests']}")
    logger.info(f"Passed: {test_results['passed_tests']}")
    logger.info(f"Failed: {test_results['failed_tests']}")
    logger.info(f"Skipped: {test_results['skipped_tests']}")
    
    # Print category results
    logger.info("\n📊 CATEGORY RESULTS")
    for category, results in test_results["categories"].items():
        total = results["passed"] + results["failed"]
        success_rate = (results["passed"] / total) * 100 if total > 0 else 0
        logger.info(f"{category.replace('_', ' ').title()}: {results['passed']}/{total} passed ({success_rate:.2f}%)")
    
    # Overall success rate
    success_rate = (test_results['passed_tests'] / test_results['total_tests']) * 100 if test_results['total_tests'] > 0 else 0
    logger.info(f"Overall Success Rate: {success_rate:.2f}%")
    
    if test_results['failed_tests'] == 0:
        logger.info("✅ All security tests passed successfully!")
    else:
        logger.error(f"❌ {test_results['failed_tests']} tests failed.")

if __name__ == "__main__":
    run_all_security_tests()
