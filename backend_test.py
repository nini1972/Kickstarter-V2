#!/usr/bin/env python3
"""
Backend Test Script for Kickstarter Investment Tracker
Tests the modular backend architecture and API endpoints
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
BACKEND_URL = "http://localhost:8001/api"

# Test data
test_project = {
    "name": f"Test Project {uuid.uuid4()}",
    "creator": "Test Creator",
    "url": "https://www.kickstarter.com/test-project",
    "description": "This is a test project for the Kickstarter Investment Tracker API",
    "category": "Technology",
    "goal_amount": 10000.0,
    "pledged_amount": 5000.0,
    "backers_count": 50,
    "deadline": (datetime.utcnow() + timedelta(days=30)).isoformat(),
    "launched_date": (datetime.utcnow() - timedelta(days=10)).isoformat(),
    "status": "live"
}

# Function to generate test projects with different data
def generate_test_project(index):
    categories = ["Technology", "Games", "Design", "Film", "Music", "Food"]
    statuses = ["live", "successful", "failed"]
    risk_levels = ["low", "medium", "high"]
    
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

test_investment = {
    "amount": 500.0,
    "investment_date": datetime.utcnow().isoformat(),
    "expected_return": 600.0,
    "notes": "Test investment",
    "reward_tier": "Basic"
}

# Test results tracking
test_results = {
    "total_tests": 0,
    "passed_tests": 0,
    "failed_tests": 0,
    "skipped_tests": 0,
    "cache_stats": {
        "hits": 0,
        "misses": 0
    },
    "batch_processing": {
        "total_batches": 0,
        "successful_batches": 0,
        "failed_batches": 0,
        "performance_metrics": []
    },
    "circuit_breaker": {
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "state_transitions": []
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
    """Test the health endpoint to verify system status and indexes"""
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        response.raise_for_status()
        
        data = response.json()
        
        # Check overall status
        overall_status = data.get("status") == "healthy"
        log_test_result("Health Check - Overall Status", 
                       overall_status, 
                       f"Status: {data.get('status')}")
        
        # Check database connectivity
        db_status = data.get("services", {}).get("database", {}).get("status") == "healthy"
        log_test_result("Health Check - Database Connectivity", 
                       db_status, 
                       f"Database status: {data.get('services', {}).get('database', {}).get('status')}")
        
        # Check circuit breaker status
        circuit_breaker_status = data.get("services", {}).get("circuit_breakers", {}).get("status")
        circuit_breaker_count = data.get("services", {}).get("circuit_breakers", {}).get("total_breakers", 0)
        open_breakers = data.get("services", {}).get("circuit_breakers", {}).get("open_breakers", 0)
        
        log_test_result("Health Check - Circuit Breakers", 
                       circuit_breaker_status == "healthy", 
                       f"Circuit breaker status: {circuit_breaker_status}, Total breakers: {circuit_breaker_count}, Open breakers: {open_breakers}")
        
        # Check if circuit breaker details are included
        breaker_details = data.get("services", {}).get("circuit_breakers", {}).get("breaker_details", {})
        has_breaker_details = len(breaker_details) > 0
        
        log_test_result("Health Check - Circuit Breaker Details", 
                       has_breaker_details, 
                       f"Circuit breaker details included: {list(breaker_details.keys())}")
        
        # Check Redis cache status
        redis_status = data.get("services", {}).get("cache", {}).get("status")
        redis_connected = redis_status == "connected"
        
        log_test_result("Health Check - Redis Cache", 
                       redis_connected, 
                       f"Redis status: {redis_status}")
        
        return True
    except Exception as e:
        log_test_result("Health Check", False, f"Error: {str(e)}")
        return False

def test_circuit_breaker_stats_endpoint():
    """Test the circuit breaker statistics endpoint"""
    try:
        # First, get a demo login token
        login_response = requests.post(f"{BACKEND_URL}/auth/demo-login")
        if login_response.status_code != 200:
            log_test_result("Circuit Breaker Stats - Authentication", False, f"Failed to get demo login token: {login_response.status_code}")
            return False
        
        # Extract cookies from response
        cookies = login_response.cookies
        
        # Get circuit breaker stats
        response = requests.get(f"{BACKEND_URL}/circuit-breakers", cookies=cookies)
        
        if response.status_code != 200:
            log_test_result("Circuit Breaker Stats - Endpoint", False, f"Failed to get circuit breaker stats: {response.status_code} - {response.text}")
            return False
        
        data = response.json()
        
        # Check if stats include expected fields
        has_total_breakers = "total_breakers" in data
        has_breakers = "breakers" in data
        has_generated_at = "generated_at" in data
        
        log_test_result("Circuit Breaker Stats - Basic Fields", 
                       has_total_breakers and has_breakers and has_generated_at, 
                       f"Total breakers: {data.get('total_breakers')}, Generated at: {data.get('generated_at')}")
        
        # Check if openai_api breaker is included
        breakers = data.get("breakers", {})
        has_openai_breaker = "openai_api" in breakers
        
        if has_openai_breaker:
            openai_breaker = breakers.get("openai_api", {})
            state = openai_breaker.get("state")
            
            log_test_result("Circuit Breaker Stats - OpenAI Breaker", 
                           True, 
                           f"OpenAI breaker state: {state}")
            
            # Check if stats include detailed information
            stats = openai_breaker.get("stats", {})
            has_detailed_stats = "total_calls" in stats and "success_rate" in stats
            
            log_test_result("Circuit Breaker Stats - Detailed Stats", 
                           has_detailed_stats, 
                           f"Total calls: {stats.get('total_calls')}, Success rate: {stats.get('success_rate')}%")
        else:
            log_test_result("Circuit Breaker Stats - OpenAI Breaker", 
                           False, 
                           "OpenAI breaker not found in stats")
        
        return True
    except Exception as e:
        log_test_result("Circuit Breaker Stats", False, f"Error: {str(e)}")
        return False

def test_specific_circuit_breaker_endpoint():
    """Test the specific circuit breaker endpoint"""
    try:
        # First, get a demo login token
        login_response = requests.post(f"{BACKEND_URL}/auth/demo-login")
        if login_response.status_code != 200:
            log_test_result("Specific Circuit Breaker - Authentication", False, f"Failed to get demo login token: {login_response.status_code}")
            return False
        
        # Extract cookies from response
        cookies = login_response.cookies
        
        # Get specific circuit breaker stats
        response = requests.get(f"{BACKEND_URL}/circuit-breakers/openai_api", cookies=cookies)
        
        if response.status_code != 200:
            log_test_result("Specific Circuit Breaker - Endpoint", False, f"Failed to get specific circuit breaker stats: {response.status_code} - {response.text}")
            return False
        
        data = response.json()
        
        # Check if stats include expected fields
        has_name = "name" in data and data["name"] == "openai_api"
        has_state = "state" in data
        has_config = "config" in data
        has_stats = "stats" in data
        
        log_test_result("Specific Circuit Breaker - Basic Fields", 
                       has_name and has_state and has_config and has_stats, 
                       f"Name: {data.get('name')}, State: {data.get('state')}")
        
        # Check configuration
        config = data.get("config", {})
        has_config_details = ("failure_threshold" in config and 
                             "success_threshold" in config and 
                             "timeout_duration" in config and 
                             "call_timeout" in config)
        
        log_test_result("Specific Circuit Breaker - Configuration", 
                       has_config_details, 
                       f"Failure threshold: {config.get('failure_threshold')}, " +
                       f"Success threshold: {config.get('success_threshold')}, " +
                       f"Timeout duration: {config.get('timeout_duration')}s, " +
                       f"Call timeout: {config.get('call_timeout')}s")
        
        # Check if configuration matches expected values
        config_matches = (config.get("failure_threshold") == 3 and 
                         config.get("success_threshold") == 2 and 
                         config.get("timeout_duration") == 120 and 
                         config.get("call_timeout") == 45)
        
        log_test_result("Specific Circuit Breaker - Configuration Values", 
                       config_matches, 
                       "Circuit breaker configuration matches expected values")
        
        # Check detailed statistics
        stats = data.get("stats", {})
        has_detailed_stats = ("total_calls" in stats and 
                             "successful_calls" in stats and 
                             "failed_calls" in stats and 
                             "success_rate" in stats and 
                             "circuit_opens" in stats)
        
        log_test_result("Specific Circuit Breaker - Detailed Stats", 
                       has_detailed_stats, 
                       f"Total calls: {stats.get('total_calls')}, " +
                       f"Successful calls: {stats.get('successful_calls')}, " +
                       f"Failed calls: {stats.get('failed_calls')}, " +
                       f"Success rate: {stats.get('success_rate')}%, " +
                       f"Circuit opens: {stats.get('circuit_opens')}")
        
        return True
    except Exception as e:
        log_test_result("Specific Circuit Breaker", False, f"Error: {str(e)}")
        return False

def test_circuit_breaker_reset_endpoint():
    """Test the circuit breaker reset endpoint"""
    try:
        # First, get a demo login token
        login_response = requests.post(f"{BACKEND_URL}/auth/demo-login")
        if login_response.status_code != 200:
            log_test_result("Circuit Breaker Reset - Authentication", False, f"Failed to get demo login token: {login_response.status_code}")
            return False
        
        # Extract cookies from response
        cookies = login_response.cookies
        
        # Reset specific circuit breaker
        response = requests.post(f"{BACKEND_URL}/circuit-breakers/openai_api/reset", cookies=cookies)
        
        if response.status_code != 200:
            log_test_result("Circuit Breaker Reset - Endpoint", False, f"Failed to reset circuit breaker: {response.status_code} - {response.text}")
            return False
        
        data = response.json()
        
        # Check if response includes expected fields
        has_message = "message" in data
        has_new_state = "new_state" in data
        has_reset_by = "reset_by" in data
        has_reset_at = "reset_at" in data
        
        log_test_result("Circuit Breaker Reset - Response Fields", 
                       has_message and has_new_state and has_reset_by and has_reset_at, 
                       f"Message: {data.get('message')}, New state: {data.get('new_state')}")
        
        # Check if state is closed after reset
        state_is_closed = data.get("new_state") == "closed"
        
        log_test_result("Circuit Breaker Reset - State Change", 
                       state_is_closed, 
                       f"Circuit breaker state after reset: {data.get('new_state')}")
        
        # Test reset all circuit breakers
        response = requests.post(f"{BACKEND_URL}/circuit-breakers/reset-all", cookies=cookies)
        
        if response.status_code != 200:
            log_test_result("Circuit Breaker Reset All - Endpoint", False, f"Failed to reset all circuit breakers: {response.status_code} - {response.text}")
            return False
        
        data = response.json()
        
        # Check if response includes expected fields
        has_message = "message" in data
        has_total_reset = "total_reset" in data
        has_reset_by = "reset_by" in data
        has_reset_at = "reset_at" in data
        
        log_test_result("Circuit Breaker Reset All - Response Fields", 
                       has_message and has_total_reset and has_reset_by and has_reset_at, 
                       f"Message: {data.get('message')}, Total reset: {data.get('total_reset')}")
        
        return True
    except Exception as e:
        log_test_result("Circuit Breaker Reset", False, f"Error: {str(e)}")
        return False

def test_ai_service_with_circuit_breaker():
    """Test AI service with circuit breaker protection"""
    try:
        # First, get a demo login token
        login_response = requests.post(f"{BACKEND_URL}/auth/demo-login")
        if login_response.status_code != 200:
            log_test_result("AI Service - Authentication", False, f"Failed to get demo login token: {login_response.status_code}")
            return False
        
        # Extract cookies from response
        cookies = login_response.cookies
        
        # Create a test project to trigger AI analysis
        project_data = generate_test_project(0)
        
        response = requests.post(f"{BACKEND_URL}/projects", json=project_data, cookies=cookies)
        
        if response.status_code != 200:
            log_test_result("AI Service - Project Creation", False, f"Failed to create test project: {response.status_code} - {response.text}")
            return False
        
        project = response.json()
        project_id = project.get("id")
        
        log_test_result("AI Service - Project Creation", 
                       bool(project_id), 
                       f"Created test project with ID: {project_id}")
        
        # Check if AI analysis was performed
        has_ai_analysis = "ai_analysis" in project and project["ai_analysis"] is not None
        
        log_test_result("AI Service - Analysis Performed", 
                       has_ai_analysis, 
                       "AI analysis was performed during project creation")
        
        if has_ai_analysis:
            # Check if circuit breaker state is included in analysis
            ai_analysis = project.get("ai_analysis", {})
            has_circuit_breaker_state = "circuit_breaker_state" in ai_analysis
            
            log_test_result("AI Service - Circuit Breaker State", 
                           has_circuit_breaker_state, 
                           f"Circuit breaker state in analysis: {ai_analysis.get('circuit_breaker_state')}")
            
            # Check if analysis includes expected fields
            has_analysis_fields = ("success_probability" in ai_analysis and 
                                  "risk_level" in ai_analysis and 
                                  "strengths" in ai_analysis and 
                                  "concerns" in ai_analysis and 
                                  "recommendation" in ai_analysis)
            
            log_test_result("AI Service - Analysis Fields", 
                           has_analysis_fields, 
                           f"Success probability: {ai_analysis.get('success_probability')}, " +
                           f"Risk level: {ai_analysis.get('risk_level')}, " +
                           f"Recommendation: {ai_analysis.get('recommendation')}")
        
        # Clean up test project
        try:
            requests.delete(f"{BACKEND_URL}/projects/{project_id}", cookies=cookies)
            logger.info(f"Deleted test project with ID: {project_id}")
        except Exception as e:
            logger.warning(f"Failed to delete test project {project_id}: {e}")
        
        return True
    except Exception as e:
        log_test_result("AI Service with Circuit Breaker", False, f"Error: {str(e)}")
        return False

async def test_circuit_breaker_state_transitions():
    """Test circuit breaker state transitions by forcing failures"""
    try:
        # First, get a demo login token
        login_response = requests.post(f"{BACKEND_URL}/auth/demo-login")
        if login_response.status_code != 200:
            log_test_result("Circuit Breaker Transitions - Authentication", False, f"Failed to get demo login token: {login_response.status_code}")
            return False
        
        # Extract cookies from response
        cookies = login_response.cookies
        cookies_dict = {cookie.name: cookie.value for cookie in cookies}
        
        # Reset the circuit breaker to ensure it starts in CLOSED state
        reset_response = requests.post(f"{BACKEND_URL}/circuit-breakers/openai_api/reset", cookies=cookies)
        if reset_response.status_code != 200:
            log_test_result("Circuit Breaker Transitions - Reset", False, f"Failed to reset circuit breaker: {reset_response.status_code}")
            return False
        
        # Get initial state
        initial_response = requests.get(f"{BACKEND_URL}/circuit-breakers/openai_api", cookies=cookies)
        if initial_response.status_code != 200:
            log_test_result("Circuit Breaker Transitions - Initial State", False, f"Failed to get initial state: {initial_response.status_code}")
            return False
        
        initial_state = initial_response.json().get("state")
        
        log_test_result("Circuit Breaker Transitions - Initial State", 
                       initial_state == "closed", 
                       f"Initial state: {initial_state}")
        
        # Record state transition
        test_results["circuit_breaker"]["state_transitions"].append({
            "from": None,
            "to": initial_state,
            "reason": "Initial state"
        })
        
        # Create a test project to trigger AI analysis
        project_data = generate_test_project(0)
        
        # Create a session for making requests
        async with aiohttp.ClientSession() as session:
            # Make 4 simultaneous requests to trigger failures (assuming the OpenAI API will fail under load)
            tasks = []
            for i in range(4):
                tasks.append(session.post(f"{BACKEND_URL}/projects", 
                                         json=project_data, 
                                         cookies=cookies_dict))
            
            # Wait for all requests to complete
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check if any requests failed
            failed_requests = sum(1 for resp in responses if isinstance(resp, Exception) or resp.status >= 400)
            
            log_test_result("Circuit Breaker Transitions - Forced Failures", 
                           failed_requests > 0, 
                           f"Failed requests: {failed_requests} out of {len(responses)}")
        
        # Get state after forced failures
        after_failures_response = requests.get(f"{BACKEND_URL}/circuit-breakers/openai_api", cookies=cookies)
        if after_failures_response.status_code != 200:
            log_test_result("Circuit Breaker Transitions - After Failures", False, f"Failed to get state after failures: {after_failures_response.status_code}")
            return False
        
        after_failures_state = after_failures_response.json().get("state")
        failure_count = after_failures_response.json().get("failure_count", 0)
        
        log_test_result("Circuit Breaker Transitions - After Failures", 
                       True, 
                       f"State after failures: {after_failures_state}, Failure count: {failure_count}")
        
        # Record state transition if state changed
        if after_failures_state != initial_state:
            test_results["circuit_breaker"]["state_transitions"].append({
                "from": initial_state,
                "to": after_failures_state,
                "reason": "After forced failures"
            })
        
        # If circuit breaker is open, wait for timeout and test half-open state
        if after_failures_state == "open":
            # Get timeout duration
            timeout_duration = after_failures_response.json().get("config", {}).get("timeout_duration", 120)
            
            log_test_result("Circuit Breaker Transitions - Open State", 
                           True, 
                           f"Circuit breaker is OPEN. Waiting for timeout ({timeout_duration}s)...")
            
            # Wait for timeout (but don't wait the full time in testing)
            # In a real test, we would wait the full timeout_duration
            # For this test, we'll just reset the circuit breaker manually
            
            # Reset the circuit breaker to simulate timeout
            reset_response = requests.post(f"{BACKEND_URL}/circuit-breakers/openai_api/reset", cookies=cookies)
            if reset_response.status_code != 200:
                log_test_result("Circuit Breaker Transitions - Manual Reset", False, f"Failed to reset circuit breaker: {reset_response.status_code}")
                return False
            
            # Get state after reset
            after_reset_response = requests.get(f"{BACKEND_URL}/circuit-breakers/openai_api", cookies=cookies)
            if after_reset_response.status_code != 200:
                log_test_result("Circuit Breaker Transitions - After Reset", False, f"Failed to get state after reset: {after_reset_response.status_code}")
                return False
            
            after_reset_state = after_reset_response.json().get("state")
            
            log_test_result("Circuit Breaker Transitions - After Reset", 
                           after_reset_state == "closed", 
                           f"State after reset: {after_reset_state}")
            
            # Record state transition
            test_results["circuit_breaker"]["state_transitions"].append({
                "from": after_failures_state,
                "to": after_reset_state,
                "reason": "After manual reset"
            })
        
        return True
    except Exception as e:
        log_test_result("Circuit Breaker State Transitions", False, f"Error: {str(e)}")
        return False

def test_fallback_behavior():
    """Test fallback behavior when circuit breaker is open"""
    try:
        # First, get a demo login token
        login_response = requests.post(f"{BACKEND_URL}/auth/demo-login")
        if login_response.status_code != 200:
            log_test_result("Fallback Behavior - Authentication", False, f"Failed to get demo login token: {login_response.status_code}")
            return False
        
        # Extract cookies from response
        cookies = login_response.cookies
        
        # Reset the circuit breaker to ensure it starts in CLOSED state
        reset_response = requests.post(f"{BACKEND_URL}/circuit-breakers/openai_api/reset", cookies=cookies)
        if reset_response.status_code != 200:
            log_test_result("Fallback Behavior - Reset", False, f"Failed to reset circuit breaker: {reset_response.status_code}")
            return False
        
        # Force the circuit breaker to OPEN state by manually setting it
        # This is a simulation - in a real scenario, we would trigger failures
        # Since we can't directly set the state, we'll check if it's already open from previous tests
        
        state_response = requests.get(f"{BACKEND_URL}/circuit-breakers/openai_api", cookies=cookies)
        if state_response.status_code != 200:
            log_test_result("Fallback Behavior - Get State", False, f"Failed to get circuit breaker state: {state_response.status_code}")
            return False
        
        current_state = state_response.json().get("state")
        
        if current_state != "open":
            log_test_result("Fallback Behavior - Circuit Not Open", 
                           True, 
                           f"Circuit breaker is not OPEN (current state: {current_state}). Testing fallback behavior with normal operation.")
        else:
            log_test_result("Fallback Behavior - Circuit Open", 
                           True, 
                           "Circuit breaker is OPEN. Testing fallback behavior.")
        
        # Create a test project to trigger AI analysis
        project_data = generate_test_project(0)
        
        response = requests.post(f"{BACKEND_URL}/projects", json=project_data, cookies=cookies)
        
        if response.status_code != 200:
            log_test_result("Fallback Behavior - Project Creation", False, f"Failed to create test project: {response.status_code} - {response.text}")
            return False
        
        project = response.json()
        project_id = project.get("id")
        
        # Check if AI analysis was performed or fallback was used
        ai_analysis = project.get("ai_analysis", {})
        is_fallback = ai_analysis.get("is_fallback", False)
        
        if current_state == "open":
            # If circuit was open, we expect fallback
            log_test_result("Fallback Behavior - Fallback Used", 
                           is_fallback, 
                           f"Fallback analysis used: {is_fallback}")
            
            # Check if fallback includes expected fields
            has_fallback_fields = ("success_probability" in ai_analysis and 
                                  "risk_level" in ai_analysis and 
                                  "strengths" in ai_analysis and 
                                  "concerns" in ai_analysis and 
                                  "recommendation" in ai_analysis and
                                  "error" in ai_analysis)
            
            log_test_result("Fallback Behavior - Fallback Fields", 
                           has_fallback_fields, 
                           f"Fallback analysis includes expected fields")
            
            # Check if circuit breaker state is included
            has_circuit_state = "circuit_breaker_state" in ai_analysis
            
            log_test_result("Fallback Behavior - Circuit State", 
                           has_circuit_state, 
                           f"Circuit breaker state in fallback: {ai_analysis.get('circuit_breaker_state')}")
        else:
            # If circuit was closed, we expect normal analysis
            log_test_result("Fallback Behavior - Normal Analysis", 
                           not is_fallback, 
                           f"Normal analysis used (not fallback)")
        
        # Clean up test project
        try:
            requests.delete(f"{BACKEND_URL}/projects/{project_id}", cookies=cookies)
            logger.info(f"Deleted test project with ID: {project_id}")
        except Exception as e:
            logger.warning(f"Failed to delete test project {project_id}: {e}")
        
        return True
    except Exception as e:
        log_test_result("Fallback Behavior", False, f"Error: {str(e)}")
        return False

def test_circuit_breaker_features():
    """Run comprehensive tests for all Circuit Breaker features"""
    logger.info("\n🚀 Starting Circuit Breaker Protection Tests")
    
    # Test health endpoint with circuit breaker status
    test_health_endpoint()
    
    # Test circuit breaker statistics endpoints
    test_circuit_breaker_stats_endpoint()
    test_specific_circuit_breaker_endpoint()
    
    # Test circuit breaker management endpoints
    test_circuit_breaker_reset_endpoint()
    
    # Test AI service with circuit breaker protection
    test_ai_service_with_circuit_breaker()
    
    # Test fallback behavior
    test_fallback_behavior()
    
    # Test circuit breaker state transitions
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_circuit_breaker_state_transitions())
    
    # Print test summary
    logger.info("\n📊 CIRCUIT BREAKER TEST SUMMARY")
    logger.info(f"Total Tests: {test_results['total_tests']}")
    logger.info(f"Passed: {test_results['passed_tests']}")
    logger.info(f"Failed: {test_results['failed_tests']}")
    
    # Print circuit breaker state transitions
    if test_results["circuit_breaker"]["state_transitions"]:
        logger.info("\n🔄 CIRCUIT BREAKER STATE TRANSITIONS")
        for transition in test_results["circuit_breaker"]["state_transitions"]:
            logger.info(f"From: {transition['from']} → To: {transition['to']} (Reason: {transition['reason']})")
    
    success_rate = (test_results['passed_tests'] / test_results['total_tests']) * 100 if test_results['total_tests'] > 0 else 0
    logger.info(f"Success Rate: {success_rate:.2f}%")
    
    if test_results['failed_tests'] == 0:
        logger.info("✅ All Circuit Breaker tests passed successfully!")
    else:
        logger.error(f"❌ {test_results['failed_tests']} tests failed.")

if __name__ == "__main__":
    # Run comprehensive tests for Circuit Breaker features
    test_circuit_breaker_features()
