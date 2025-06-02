#!/usr/bin/env python3
"""
Modular Architecture Test Script for Kickstarter Investment Tracker
Tests the new modular backend architecture and API endpoints
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("modular_test")

# Backend API URL
BASE_URL = "http://localhost:8001"
API_URL = f"{BASE_URL}/api"

# Test results
test_results = {
    "total_tests": 0,
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "tests": []
}

def run_test(test_name, test_func, *args, **kwargs):
    """Run a test and record the result"""
    test_results["total_tests"] += 1
    print(f"\n🧪 Running test: {test_name}")
    
    try:
        start_time = time.time()
        result = test_func(*args, **kwargs)
        end_time = time.time()
        
        if result:
            test_results["passed"] += 1
            status = "✅ PASSED"
        else:
            test_results["failed"] += 1
            status = "❌ FAILED"
            
        duration = round((end_time - start_time) * 1000, 2)
        print(f"{status} - {test_name} ({duration}ms)")
        
        test_results["tests"].append({
            "name": test_name,
            "status": "passed" if result else "failed",
            "duration_ms": duration
        })
        
        return result
    except Exception as e:
        test_results["failed"] += 1
        print(f"❌ FAILED - {test_name} - Exception: {str(e)}")
        
        test_results["tests"].append({
            "name": test_name,
            "status": "failed",
            "error": str(e)
        })
        
        return False

def test_root_endpoint():
    """Test the root endpoint"""
    try:
        response = requests.get(BASE_URL)
        data = response.json()
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert data["message"] == "Kickstarter Investment Tracker - Modular API", "Incorrect API message"
        assert data["version"] == "2.0.0", "Incorrect API version"
        assert "features" in data, "Features list missing"
        
        print(f"Root endpoint response: {json.dumps(data, indent=2)}")
        return True
    except Exception as e:
        print(f"Error testing root endpoint: {e}")
        return False

def test_health_check():
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{API_URL}/health")
        data = response.json()
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert "status" in data, "Status field missing"
        assert "services" in data, "Services field missing"
        assert "database" in data["services"], "Database service info missing"
        assert "cache" in data["services"], "Cache service info missing"
        
        print(f"Health check response: {json.dumps(data, indent=2)}")
        return True
    except Exception as e:
        print(f"Error testing health check: {e}")
        return False

def test_analytics_dashboard():
    """Test the analytics dashboard endpoint"""
    try:
        # Note: This would normally require authentication
        # For testing purposes, we're just checking if the endpoint responds
        response = requests.get(f"{API_URL}/analytics/dashboard")
        
        # Even if authentication fails, we should get a 401 not a 500
        assert response.status_code in [200, 401, 403], f"Unexpected status code {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            print(f"Analytics dashboard response: {json.dumps(data, indent=2)}")
        else:
            print(f"Authentication required: {response.status_code}")
            
        return True
    except Exception as e:
        print(f"Error testing analytics dashboard: {e}")
        return False

def test_analytics_funding_trends():
    """Test the funding trends endpoint"""
    try:
        response = requests.get(f"{API_URL}/analytics/funding-trends")
        
        assert response.status_code in [200, 401, 403], f"Unexpected status code {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            print(f"Funding trends response: {json.dumps(data, indent=2)}")
        else:
            print(f"Authentication required: {response.status_code}")
            
        return True
    except Exception as e:
        print(f"Error testing funding trends: {e}")
        return False

def test_analytics_roi_predictions():
    """Test the ROI predictions endpoint"""
    try:
        response = requests.get(f"{API_URL}/analytics/roi-predictions")
        
        assert response.status_code in [200, 401, 403], f"Unexpected status code {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            print(f"ROI predictions response: {json.dumps(data, indent=2)}")
        else:
            print(f"Authentication required: {response.status_code}")
            
        return True
    except Exception as e:
        print(f"Error testing ROI predictions: {e}")
        return False

def test_analytics_risk():
    """Test the risk analytics endpoint"""
    try:
        response = requests.get(f"{API_URL}/analytics/risk")
        
        assert response.status_code in [200, 401, 403], f"Unexpected status code {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            print(f"Risk analytics response: {json.dumps(data, indent=2)}")
        else:
            print(f"Authentication required: {response.status_code}")
            
        return True
    except Exception as e:
        print(f"Error testing risk analytics: {e}")
        return False

def test_analytics_market_insights():
    """Test the market insights endpoint"""
    try:
        response = requests.get(f"{API_URL}/analytics/market-insights")
        
        assert response.status_code in [200, 401, 403], f"Unexpected status code {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            print(f"Market insights response: {json.dumps(data, indent=2)}")
        else:
            print(f"Authentication required: {response.status_code}")
            
        return True
    except Exception as e:
        print(f"Error testing market insights: {e}")
        return False

def test_projects_endpoint():
    """Test the projects endpoint"""
    try:
        response = requests.get(f"{API_URL}/projects")
        
        assert response.status_code in [200, 401, 403], f"Unexpected status code {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            print(f"Projects response: {json.dumps(data, indent=2)}")
        else:
            print(f"Authentication required: {response.status_code}")
            
        return True
    except Exception as e:
        print(f"Error testing projects endpoint: {e}")
        return False

def test_investments_endpoint():
    """Test the investments endpoint"""
    try:
        response = requests.get(f"{API_URL}/investments")
        
        assert response.status_code in [200, 401, 403], f"Unexpected status code {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            print(f"Investments response: {json.dumps(data, indent=2)}")
        else:
            print(f"Authentication required: {response.status_code}")
            
        return True
    except Exception as e:
        print(f"Error testing investments endpoint: {e}")
        return False

def test_alerts_endpoint():
    """Test the alerts endpoint"""
    try:
        response = requests.get(f"{API_URL}/alerts")
        
        assert response.status_code in [200, 401, 403], f"Unexpected status code {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            print(f"Alerts response: {json.dumps(data, indent=2)}")
        else:
            print(f"Authentication required: {response.status_code}")
            
        return True
    except Exception as e:
        print(f"Error testing alerts endpoint: {e}")
        return False

def test_recommendations_endpoint():
    """Test the recommendations endpoint"""
    try:
        response = requests.get(f"{API_URL}/recommendations")
        
        assert response.status_code in [200, 401, 403], f"Unexpected status code {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            print(f"Recommendations response: {json.dumps(data, indent=2)}")
        else:
            print(f"Authentication required: {response.status_code}")
            
        return True
    except Exception as e:
        print(f"Error testing recommendations endpoint: {e}")
        return False

def print_summary():
    """Print test summary"""
    print("\n" + "="*50)
    print(f"🧪 TEST SUMMARY - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    print(f"Total Tests: {test_results['total_tests']}")
    print(f"✅ Passed: {test_results['passed']}")
    print(f"❌ Failed: {test_results['failed']}")
    print(f"⏭️ Skipped: {test_results['skipped']}")
    print("="*50)
    
    if test_results["failed"] > 0:
        print("\nFailed Tests:")
        for test in test_results["tests"]:
            if test["status"] == "failed":
                print(f"- {test['name']}")
                if "error" in test:
                    print(f"  Error: {test['error']}")
    
    print("\n")

def main():
    """Run all tests"""
    print("🚀 Starting Kickstarter Investment Tracker Modular Architecture Tests")
    print("Testing modular architecture and API endpoints")
    print("="*50)
    
    # Test root and health endpoints
    run_test("Root Endpoint", test_root_endpoint)
    run_test("Health Check", test_health_check)
    
    # Test analytics endpoints
    run_test("Analytics Dashboard", test_analytics_dashboard)
    run_test("Funding Trends", test_analytics_funding_trends)
    run_test("ROI Predictions", test_analytics_roi_predictions)
    run_test("Risk Analytics", test_analytics_risk)
    run_test("Market Insights", test_analytics_market_insights)
    
    # Test existing endpoints
    run_test("Projects Endpoint", test_projects_endpoint)
    run_test("Investments Endpoint", test_investments_endpoint)
    run_test("Alerts Endpoint", test_alerts_endpoint)
    run_test("Recommendations Endpoint", test_recommendations_endpoint)
    
    # Print summary
    print_summary()
    
    # Return exit code based on test results
    return 1 if test_results["failed"] > 0 else 0

if __name__ == "__main__":
    sys.exit(main())