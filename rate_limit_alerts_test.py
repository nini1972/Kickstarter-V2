#!/usr/bin/env python3
import requests
import json
import time
import uuid
from datetime import datetime, timedelta
import logging
import sys
import random
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("rate_limit_alerts_test")

# Backend API URL
BACKEND_URL = "https://225b3faa-e25a-46f6-8dd9-d92508eb5e44.preview.emergentagent.com/api"

# Test results tracking
test_results = {
    "total_tests": 0,
    "passed_tests": 0,
    "failed_tests": 0,
    "skipped_tests": 0,
    "rate_limiting": {
        "health_check": {
            "limit": "30/minute",
            "tested": False,
            "working": False
        },
        "project_creation": {
            "limit": "20/minute",
            "tested": False,
            "working": False
        },
        "batch_processing": {
            "limit": "10/hour",
            "tested": False,
            "working": False
        },
        "recommendations": {
            "limit": "50/minute",
            "tested": False,
            "working": False
        }
    },
    "enhanced_alerts": {
        "tested": False,
        "working": False,
        "priority_scoring": False,
        "action_items": False,
        "confidence_level": False
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

# Function to generate test projects with different data
def generate_test_project(index):
    categories = ["Technology", "Games", "Design", "Film", "Music", "Food"]
    statuses = ["live", "successful", "failed"]
    
    return {
        "name": f"Test Project {index} - {uuid.uuid4()}",
        "creator": f"Creator {index}",
        "url": f"https://www.kickstarter.com/test-project-{index}",
        "description": f"This is test project {index} with a detailed description that includes various features and goals. The project aims to create innovative solutions for modern problems.",
        "category": random.choice(categories),
        "goal_amount": random.randint(5000, 50000),
        "pledged_amount": random.randint(1000, 60000),
        "backers_count": random.randint(10, 500),
        "deadline": (datetime.utcnow() + timedelta(days=random.randint(5, 60))).isoformat(),
        "launched_date": (datetime.utcnow() - timedelta(days=random.randint(5, 30))).isoformat(),
        "status": random.choice(statuses)
    }

def test_health_check_rate_limiting():
    """Test rate limiting on the health check endpoint (30/minute)"""
    logger.info("\n🧪 Testing Health Check Rate Limiting (30/minute)")
    
    try:
        # Make 35 requests to exceed the rate limit (30/minute)
        successful_requests = 0
        rate_limited_requests = 0
        rate_limit_headers = {}
        
        logger.info(f"Making 35 requests to health check endpoint (limit: 30/minute)...")
        
        for i in range(35):
            response = requests.get(f"{BACKEND_URL}/health")
            
            # Check for rate limit headers
            if 'X-RateLimit-Limit' in response.headers:
                rate_limit_headers = {
                    'X-RateLimit-Limit': response.headers.get('X-RateLimit-Limit'),
                    'X-RateLimit-Remaining': response.headers.get('X-RateLimit-Remaining'),
                    'X-RateLimit-Reset': response.headers.get('X-RateLimit-Reset')
                }
            
            if response.status_code == 200:
                successful_requests += 1
            elif response.status_code == 429:  # Too Many Requests
                rate_limited_requests += 1
                logger.info(f"Request {i+1}: Rate limited (429 Too Many Requests)")
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.1)
        
        # Check if rate limiting is working
        rate_limiting_working = rate_limited_requests > 0
        
        log_test_result("Health Check Rate Limiting", 
                       rate_limiting_working, 
                       f"Successful requests: {successful_requests}, Rate limited requests: {rate_limited_requests}")
        
        # Check if rate limit headers are present
        headers_present = bool(rate_limit_headers)
        
        log_test_result("Health Check Rate Limit Headers", 
                       headers_present, 
                       f"Rate limit headers: {rate_limit_headers}")
        
        # Update test results
        test_results["rate_limiting"]["health_check"]["tested"] = True
        test_results["rate_limiting"]["health_check"]["working"] = rate_limiting_working
        
        return rate_limiting_working
        
    except Exception as e:
        log_test_result("Health Check Rate Limiting", False, f"Error: {str(e)}")
        return False

def test_project_creation_rate_limiting():
    """Test rate limiting on project creation endpoint (20/minute)"""
    logger.info("\n🧪 Testing Project Creation Rate Limiting (20/minute)")
    
    created_project_ids = []
    
    try:
        # Make 25 requests to exceed the rate limit (20/minute)
        successful_requests = 0
        rate_limited_requests = 0
        rate_limit_headers = {}
        
        logger.info(f"Making 25 requests to project creation endpoint (limit: 20/minute)...")
        
        for i in range(25):
            project_data = generate_test_project(i)
            response = requests.post(f"{BACKEND_URL}/projects", json=project_data)
            
            # Check for rate limit headers
            if 'X-RateLimit-Limit' in response.headers:
                rate_limit_headers = {
                    'X-RateLimit-Limit': response.headers.get('X-RateLimit-Limit'),
                    'X-RateLimit-Remaining': response.headers.get('X-RateLimit-Remaining'),
                    'X-RateLimit-Reset': response.headers.get('X-RateLimit-Reset')
                }
            
            if response.status_code == 200:
                successful_requests += 1
                project_id = response.json().get("id")
                if project_id:
                    created_project_ids.append(project_id)
                    logger.info(f"Created project {i+1} with ID: {project_id}")
            elif response.status_code == 429:  # Too Many Requests
                rate_limited_requests += 1
                logger.info(f"Request {i+1}: Rate limited (429 Too Many Requests)")
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.1)
        
        # Check if rate limiting is working
        rate_limiting_working = rate_limited_requests > 0
        
        log_test_result("Project Creation Rate Limiting", 
                       rate_limiting_working, 
                       f"Successful requests: {successful_requests}, Rate limited requests: {rate_limited_requests}")
        
        # Check if rate limit headers are present
        headers_present = bool(rate_limit_headers)
        
        log_test_result("Project Creation Rate Limit Headers", 
                       headers_present, 
                       f"Rate limit headers: {rate_limit_headers}")
        
        # Update test results
        test_results["rate_limiting"]["project_creation"]["tested"] = True
        test_results["rate_limiting"]["project_creation"]["working"] = rate_limiting_working
        
        # Clean up created projects
        logger.info("Cleaning up created projects...")
        for project_id in created_project_ids:
            try:
                requests.delete(f"{BACKEND_URL}/projects/{project_id}")
                logger.info(f"Deleted project with ID: {project_id}")
            except Exception as e:
                logger.warning(f"Failed to delete project {project_id}: {e}")
        
        return rate_limiting_working
        
    except Exception as e:
        log_test_result("Project Creation Rate Limiting", False, f"Error: {str(e)}")
        
        # Clean up any created projects
        for project_id in created_project_ids:
            try:
                requests.delete(f"{BACKEND_URL}/projects/{project_id}")
            except:
                pass
                
        return False

def test_batch_processing_rate_limiting():
    """Test rate limiting on batch processing endpoint (10/hour)"""
    logger.info("\n🧪 Testing Batch Processing Rate Limiting (10/hour)")
    
    created_project_ids = []
    
    try:
        # Create 5 test projects for batch processing
        logger.info("Creating test projects for batch processing...")
        for i in range(5):
            project_data = generate_test_project(i)
            response = requests.post(f"{BACKEND_URL}/projects", json=project_data)
            if response.status_code == 200:
                project_id = response.json().get("id")
                created_project_ids.append(project_id)
                logger.info(f"Created test project {i+1} with ID: {project_id}")
            else:
                logger.warning(f"Failed to create test project {i+1}: {response.text}")
        
        if not created_project_ids:
            logger.error("❌ Failed to create any test projects for batch processing")
            log_test_result("Batch Processing Rate Limiting - Project Creation", False, "Failed to create test projects")
            return False
        
        # Make 12 requests to exceed the rate limit (10/hour)
        successful_requests = 0
        rate_limited_requests = 0
        rate_limit_headers = {}
        
        logger.info(f"Making 12 requests to batch processing endpoint (limit: 10/hour)...")
        
        for i in range(12):
            response = requests.post(
                f"{BACKEND_URL}/projects/batch-analyze", 
                json={
                    "project_ids": created_project_ids,
                    "batch_size": len(created_project_ids)
                }
            )
            
            # Check for rate limit headers
            if 'X-RateLimit-Limit' in response.headers:
                rate_limit_headers = {
                    'X-RateLimit-Limit': response.headers.get('X-RateLimit-Limit'),
                    'X-RateLimit-Remaining': response.headers.get('X-RateLimit-Remaining'),
                    'X-RateLimit-Reset': response.headers.get('X-RateLimit-Reset')
                }
            
            if response.status_code == 200:
                successful_requests += 1
                logger.info(f"Batch request {i+1}: Successful")
            elif response.status_code == 429:  # Too Many Requests
                rate_limited_requests += 1
                logger.info(f"Batch request {i+1}: Rate limited (429 Too Many Requests)")
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.2)
        
        # Check if rate limiting is working
        rate_limiting_working = rate_limited_requests > 0
        
        log_test_result("Batch Processing Rate Limiting", 
                       rate_limiting_working, 
                       f"Successful requests: {successful_requests}, Rate limited requests: {rate_limited_requests}")
        
        # Check if rate limit headers are present
        headers_present = bool(rate_limit_headers)
        
        log_test_result("Batch Processing Rate Limit Headers", 
                       headers_present, 
                       f"Rate limit headers: {rate_limit_headers}")
        
        # Update test results
        test_results["rate_limiting"]["batch_processing"]["tested"] = True
        test_results["rate_limiting"]["batch_processing"]["working"] = rate_limiting_working
        
        # Clean up created projects
        logger.info("Cleaning up created projects...")
        for project_id in created_project_ids:
            try:
                requests.delete(f"{BACKEND_URL}/projects/{project_id}")
                logger.info(f"Deleted project with ID: {project_id}")
            except Exception as e:
                logger.warning(f"Failed to delete project {project_id}: {e}")
        
        return rate_limiting_working
        
    except Exception as e:
        log_test_result("Batch Processing Rate Limiting", False, f"Error: {str(e)}")
        
        # Clean up any created projects
        for project_id in created_project_ids:
            try:
                requests.delete(f"{BACKEND_URL}/projects/{project_id}")
            except:
                pass
                
        return False

def test_recommendations_rate_limiting():
    """Test rate limiting on recommendations endpoint (50/minute)"""
    logger.info("\n🧪 Testing Recommendations Rate Limiting (50/minute)")
    
    try:
        # Make 55 requests to exceed the rate limit (50/minute)
        successful_requests = 0
        rate_limited_requests = 0
        rate_limit_headers = {}
        
        logger.info(f"Making 55 requests to recommendations endpoint (limit: 50/minute)...")
        
        # Use ThreadPoolExecutor to make requests in parallel
        def make_request(i):
            try:
                response = requests.get(f"{BACKEND_URL}/recommendations")
                
                # Check for rate limit headers
                headers = {}
                if 'X-RateLimit-Limit' in response.headers:
                    headers = {
                        'X-RateLimit-Limit': response.headers.get('X-RateLimit-Limit'),
                        'X-RateLimit-Remaining': response.headers.get('X-RateLimit-Remaining'),
                        'X-RateLimit-Reset': response.headers.get('X-RateLimit-Reset')
                    }
                
                return {
                    'index': i,
                    'status_code': response.status_code,
                    'headers': headers
                }
            except Exception as e:
                logger.error(f"Error in request {i}: {e}")
                return {
                    'index': i,
                    'status_code': 0,
                    'error': str(e)
                }
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(make_request, range(55)))
        
        # Process results
        for result in results:
            if result['status_code'] == 200:
                successful_requests += 1
            elif result['status_code'] == 429:  # Too Many Requests
                rate_limited_requests += 1
                logger.info(f"Request {result['index']+1}: Rate limited (429 Too Many Requests)")
            
            # Capture rate limit headers from any request that has them
            if result.get('headers') and not rate_limit_headers:
                rate_limit_headers = result['headers']
        
        # Check if rate limiting is working
        rate_limiting_working = rate_limited_requests > 0
        
        log_test_result("Recommendations Rate Limiting", 
                       rate_limiting_working, 
                       f"Successful requests: {successful_requests}, Rate limited requests: {rate_limited_requests}")
        
        # Check if rate limit headers are present
        headers_present = bool(rate_limit_headers)
        
        log_test_result("Recommendations Rate Limit Headers", 
                       headers_present, 
                       f"Rate limit headers: {rate_limit_headers}")
        
        # Update test results
        test_results["rate_limiting"]["recommendations"]["tested"] = True
        test_results["rate_limiting"]["recommendations"]["working"] = rate_limiting_working
        
        return rate_limiting_working
        
    except Exception as e:
        log_test_result("Recommendations Rate Limiting", False, f"Error: {str(e)}")
        return False

def test_enhanced_smart_alerts():
    """Test the enhanced smart alerts system"""
    logger.info("\n🧪 Testing Enhanced Smart Alerts System")
    
    created_project_ids = []
    
    try:
        # Create 10 test projects with varying data to trigger different alerts
        logger.info("Creating test projects for enhanced alerts testing...")
        
        # Create projects with specific characteristics to trigger different alerts
        projects_data = [
            # High funding project (should trigger high priority alert)
            {
                "name": f"High Funding Project {uuid.uuid4()}",
                "creator": "Test Creator",
                "url": "https://www.kickstarter.com/test-project-high-funding",
                "description": "This project has high funding and is likely to succeed",
                "category": "Technology",
                "goal_amount": 10000.0,
                "pledged_amount": 9000.0,  # 90% funded
                "backers_count": 200,
                "deadline": (datetime.utcnow() + timedelta(days=10)).isoformat(),
                "launched_date": (datetime.utcnow() - timedelta(days=5)).isoformat(),
                "status": "live"
            },
            # Deadline approaching project (should trigger medium priority alert)
            {
                "name": f"Deadline Approaching Project {uuid.uuid4()}",
                "creator": "Test Creator",
                "url": "https://www.kickstarter.com/test-project-deadline",
                "description": "This project has a deadline approaching soon",
                "category": "Games",
                "goal_amount": 20000.0,
                "pledged_amount": 12000.0,  # 60% funded
                "backers_count": 150,
                "deadline": (datetime.utcnow() + timedelta(days=3)).isoformat(),
                "launched_date": (datetime.utcnow() - timedelta(days=27)).isoformat(),
                "status": "live"
            },
            # Low risk project (should trigger medium/high priority alert)
            {
                "name": f"Low Risk Project {uuid.uuid4()}",
                "creator": "Test Creator",
                "url": "https://www.kickstarter.com/test-project-low-risk",
                "description": "This is a low risk project with good funding",
                "category": "Design",
                "goal_amount": 5000.0,
                "pledged_amount": 3500.0,  # 70% funded
                "backers_count": 100,
                "deadline": (datetime.utcnow() + timedelta(days=15)).isoformat(),
                "launched_date": (datetime.utcnow() - timedelta(days=15)).isoformat(),
                "status": "live"
            }
        ]
        
        # Create the test projects
        for i, project_data in enumerate(projects_data):
            response = requests.post(f"{BACKEND_URL}/projects", json=project_data)
            if response.status_code == 200:
                project_id = response.json().get("id")
                created_project_ids.append(project_id)
                logger.info(f"Created test project {i+1} with ID: {project_id}")
            else:
                logger.warning(f"Failed to create test project {i+1}: {response.text}")
        
        if not created_project_ids:
            logger.error("❌ Failed to create any test projects for enhanced alerts testing")
            log_test_result("Enhanced Alerts - Project Creation", False, "Failed to create test projects")
            return False
        
        # Wait a moment for the projects to be processed
        logger.info("Waiting for projects to be processed...")
        time.sleep(2)
        
        # Get alerts
        logger.info("Retrieving alerts...")
        response = requests.get(f"{BACKEND_URL}/alerts")
        
        if response.status_code != 200:
            log_test_result("Enhanced Alerts - Retrieval", False, f"Failed to retrieve alerts: {response.status_code} - {response.text}")
            return False
        
        alerts = response.json()
        
        # Check if alerts were generated
        alerts_generated = len(alerts) > 0
        
        log_test_result("Enhanced Alerts - Generation", 
                       alerts_generated, 
                       f"Generated {len(alerts)} alerts")
        
        if not alerts_generated:
            logger.warning("No alerts were generated. Cannot test enhanced alerts features.")
            test_results["enhanced_alerts"]["tested"] = True
            test_results["enhanced_alerts"]["working"] = False
            return False
        
        # Check for priority levels in alerts
        priority_levels = set(alert.get("priority", "").lower() for alert in alerts)
        has_multiple_priorities = len(priority_levels) > 1
        
        log_test_result("Enhanced Alerts - Priority Levels", 
                       has_multiple_priorities, 
                       f"Priority levels found: {priority_levels}")
        
        # Check for action items in alerts
        has_action_items = any("action_items" in alert for alert in alerts)
        
        if has_action_items:
            # Get a sample of action items
            sample_action_items = next((alert.get("action_items", []) for alert in alerts if "action_items" in alert), [])
            log_test_result("Enhanced Alerts - Action Items", 
                           True, 
                           f"Action items found: {sample_action_items[:2]}...")
        else:
            log_test_result("Enhanced Alerts - Action Items", 
                           False, 
                           "No action items found in alerts")
        
        # Check for confidence levels in alerts
        has_confidence_levels = any("confidence_level" in alert for alert in alerts)
        
        if has_confidence_levels:
            # Get a sample of confidence levels
            sample_confidence = next((alert.get("confidence_level", "") for alert in alerts if "confidence_level" in alert), "")
            log_test_result("Enhanced Alerts - Confidence Levels", 
                           True, 
                           f"Confidence level found: {sample_confidence}")
        else:
            log_test_result("Enhanced Alerts - Confidence Levels", 
                           False, 
                           "No confidence levels found in alerts")
        
        # Update test results
        test_results["enhanced_alerts"]["tested"] = True
        test_results["enhanced_alerts"]["working"] = alerts_generated
        test_results["enhanced_alerts"]["priority_scoring"] = has_multiple_priorities
        test_results["enhanced_alerts"]["action_items"] = has_action_items
        test_results["enhanced_alerts"]["confidence_level"] = has_confidence_levels
        
        # Clean up created projects
        logger.info("Cleaning up created projects...")
        for project_id in created_project_ids:
            try:
                requests.delete(f"{BACKEND_URL}/projects/{project_id}")
                logger.info(f"Deleted project with ID: {project_id}")
            except Exception as e:
                logger.warning(f"Failed to delete project {project_id}: {e}")
        
        return alerts_generated
        
    except Exception as e:
        log_test_result("Enhanced Smart Alerts", False, f"Error: {str(e)}")
        
        # Clean up any created projects
        for project_id in created_project_ids:
            try:
                requests.delete(f"{BACKEND_URL}/projects/{project_id}")
            except:
                pass
                
        return False

def test_rate_limit_error_response():
    """Test the error response format when rate limit is exceeded"""
    logger.info("\n🧪 Testing Rate Limit Error Response Format")
    
    try:
        # First, make enough requests to trigger rate limiting on health check endpoint
        logger.info("Making requests to trigger rate limiting...")
        
        rate_limit_response = None
        for i in range(35):  # Health check limit is 30/minute
            response = requests.get(f"{BACKEND_URL}/health")
            
            if response.status_code == 429:  # Too Many Requests
                rate_limit_response = response
                logger.info(f"Rate limit triggered on request {i+1}")
                break
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.1)
        
        if not rate_limit_response:
            log_test_result("Rate Limit Error Response", False, "Failed to trigger rate limiting")
            return False
        
        # Check error response format
        try:
            error_data = rate_limit_response.json()
            
            # Check for expected fields in error response
            has_error_detail = "detail" in error_data
            has_retry_after = "Retry-After" in rate_limit_response.headers
            
            log_test_result("Rate Limit Error Response Format", 
                           has_error_detail, 
                           f"Error response: {error_data}")
            
            log_test_result("Rate Limit Retry-After Header", 
                           has_retry_after, 
                           f"Retry-After: {rate_limit_response.headers.get('Retry-After', 'Not present')}")
            
            return has_error_detail
            
        except json.JSONDecodeError:
            log_test_result("Rate Limit Error Response Format", 
                           False, 
                           f"Response is not valid JSON: {rate_limit_response.text}")
            return False
        
    except Exception as e:
        log_test_result("Rate Limit Error Response", False, f"Error: {str(e)}")
        return False

def run_all_tests():
    """Run all rate limiting and enhanced alerts tests"""
    logger.info("🚀 Starting Rate Limiting & Enhanced Smart Alerts Tests")
    logger.info(f"🔗 Testing API at: {BACKEND_URL}")
    
    # Test rate limiting on different endpoints
    test_health_check_rate_limiting()
    test_project_creation_rate_limiting()
    test_batch_processing_rate_limiting()
    test_recommendations_rate_limiting()
    
    # Test rate limit error response format
    test_rate_limit_error_response()
    
    # Test enhanced smart alerts system
    test_enhanced_smart_alerts()
    
    # Print test summary
    logger.info("\n📊 TEST SUMMARY")
    logger.info(f"Total Tests: {test_results['total_tests']}")
    logger.info(f"Passed: {test_results['passed_tests']}")
    logger.info(f"Failed: {test_results['failed_tests']}")
    logger.info(f"Skipped: {test_results['skipped_tests']}")
    
    # Print rate limiting test results
    logger.info("\n📊 RATE LIMITING TEST RESULTS")
    for endpoint, results in test_results["rate_limiting"].items():
        status = "✅ WORKING" if results["working"] else "❌ NOT WORKING"
        if not results["tested"]:
            status = "⚠️ NOT TESTED"
        
        logger.info(f"{endpoint.replace('_', ' ').title()} ({results['limit']}): {status}")
    
    # Print enhanced alerts test results
    logger.info("\n📊 ENHANCED ALERTS TEST RESULTS")
    alerts_status = "✅ WORKING" if test_results["enhanced_alerts"]["working"] else "❌ NOT WORKING"
    if not test_results["enhanced_alerts"]["tested"]:
        alerts_status = "⚠️ NOT TESTED"
    
    logger.info(f"Enhanced Smart Alerts: {alerts_status}")
    
    if test_results["enhanced_alerts"]["tested"]:
        logger.info(f"Priority Scoring: {'✅ WORKING' if test_results['enhanced_alerts']['priority_scoring'] else '❌ NOT WORKING'}")
        logger.info(f"Action Items: {'✅ WORKING' if test_results['enhanced_alerts']['action_items'] else '❌ NOT WORKING'}")
        logger.info(f"Confidence Level: {'✅ WORKING' if test_results['enhanced_alerts']['confidence_level'] else '❌ NOT WORKING'}")
    
    success_rate = (test_results['passed_tests'] / test_results['total_tests']) * 100 if test_results['total_tests'] > 0 else 0
    logger.info(f"Success Rate: {success_rate:.2f}%")
    
    if test_results['failed_tests'] == 0:
        logger.info("✅ All tests passed successfully!")
    else:
        logger.error(f"❌ {test_results['failed_tests']} tests failed.")

if __name__ == "__main__":
    run_all_tests()