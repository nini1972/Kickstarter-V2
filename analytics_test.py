#!/usr/bin/env python3
"""
Analytics Service Test Script for Kickstarter Investment Tracker
Tests the enhanced Analytics Service endpoints after Phase 2 Step 1 implementation
"""

import requests
import json
import time
import uuid
from datetime import datetime, timedelta
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
logger = logging.getLogger("analytics_test")

# Backend API URL
BACKEND_URL = "http://localhost:8001/api"

# Test results tracking
test_results = {
    "total_tests": 0,
    "passed_tests": 0,
    "failed_tests": 0,
    "skipped_tests": 0,
    "analytics_endpoints": {
        "dashboard": {"status": "untested", "response_time": 0},
        "funding_trends": {"status": "untested", "response_time": 0},
        "roi_predictions": {"status": "untested", "response_time": 0},
        "risk": {"status": "untested", "response_time": 0},
        "market_insights": {"status": "untested", "response_time": 0}
    }
}

# Authentication credentials for demo user
auth_data = {
    "username": "demo",
    "password": "demo123"
}

# Store auth token
auth_token = None

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

def authenticate():
    """Authenticate with the API to get a token"""
    global auth_token
    
    try:
        logger.info("Authenticating with demo credentials...")
        response = requests.post(f"{BACKEND_URL}/auth/demo-login")
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("access_token")
            
            if auth_token:
                logger.info("✅ Authentication successful")
                return True
            else:
                logger.error("❌ Authentication failed: No token received")
                return False
        else:
            logger.error(f"❌ Authentication failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Authentication error: {str(e)}")
        return False

def get_auth_headers():
    """Get authentication headers for API requests"""
    if auth_token:
        return {"Authorization": f"Bearer {auth_token}"}
    return {}

def test_dashboard_analytics():
    """Test the dashboard analytics endpoint"""
    logger.info("\n🧪 Testing Dashboard Analytics Endpoint")
    
    try:
        # Make request to dashboard analytics endpoint
        start_time = time.time()
        response = requests.get(
            f"{BACKEND_URL}/analytics/dashboard",
            headers=get_auth_headers()
        )
        response_time = time.time() - start_time
        
        # Update response time in test results
        test_results["analytics_endpoints"]["dashboard"]["response_time"] = response_time
        
        if response.status_code == 200:
            data = response.json()
            test_results["analytics_endpoints"]["dashboard"]["status"] = "passed"
            
            # Verify data structure
            has_overview = "overview" in data
            has_projects = "projects" in data
            has_investments = "investments" in data
            has_performance = "performance" in data
            has_trends = "trends" in data
            has_risk = "risk" in data
            
            structure_valid = all([has_overview, has_projects, has_investments, has_performance, has_trends, has_risk])
            
            log_test_result("Dashboard Analytics - Data Structure", 
                           structure_valid, 
                           f"Response contains all required sections: {structure_valid}")
            
            # Verify overview metrics
            if has_overview:
                overview = data["overview"]
                required_metrics = ["total_projects", "total_investments", "total_invested", 
                                   "total_current_value", "overall_roi", "success_rate", 
                                   "average_investment"]
                
                metrics_present = all(metric in overview for metric in required_metrics)
                
                log_test_result("Dashboard Analytics - Overview Metrics", 
                               metrics_present, 
                               f"Overview contains all required metrics: {metrics_present}")
            
            # Verify caching information
            has_cache_info = "generated_at" in data and "cache_ttl" in data
            
            log_test_result("Dashboard Analytics - Cache Information", 
                           has_cache_info, 
                           f"Response includes cache information: {has_cache_info}")
            
            # Test caching functionality by making a second request
            logger.info("Testing caching functionality with second request...")
            second_start_time = time.time()
            second_response = requests.get(
                f"{BACKEND_URL}/analytics/dashboard",
                headers=get_auth_headers()
            )
            second_response_time = time.time() - second_start_time
            
            # Check if second request was faster (indicating cache hit)
            cache_working = second_response_time < response_time
            cache_improvement = ((response_time - second_response_time) / response_time) * 100 if response_time > 0 else 0
            
            log_test_result("Dashboard Analytics - Cache Performance", 
                           cache_working, 
                           f"Cache hit is {cache_improvement:.2f}% faster than cache miss")
            
            return True
        else:
            test_results["analytics_endpoints"]["dashboard"]["status"] = "failed"
            log_test_result("Dashboard Analytics", 
                           False, 
                           f"API error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        test_results["analytics_endpoints"]["dashboard"]["status"] = "error"
        log_test_result("Dashboard Analytics", False, f"Error: {str(e)}")
        return False

def test_funding_trends():
    """Test the funding trends endpoint with different time ranges"""
    logger.info("\n🧪 Testing Funding Trends Endpoint")
    
    try:
        # Test with different time ranges
        time_ranges = [30, 90, 180, 365]
        
        for days in time_ranges:
            logger.info(f"Testing funding trends with {days} days range...")
            
            start_time = time.time()
            response = requests.get(
                f"{BACKEND_URL}/analytics/funding-trends?days={days}",
                headers=get_auth_headers()
            )
            response_time = time.time() - start_time
            
            # Update response time in test results (use the first one)
            if days == 30:
                test_results["analytics_endpoints"]["funding_trends"]["response_time"] = response_time
            
            if response.status_code == 200:
                data = response.json()
                
                if days == 30:
                    test_results["analytics_endpoints"]["funding_trends"]["status"] = "passed"
                
                # Verify data structure
                has_trends = "trends" in data
                trends = data.get("trends", [])
                
                log_test_result(f"Funding Trends ({days} days) - Data Structure", 
                               has_trends, 
                               f"Response contains trends array with {len(trends)} items")
                
                # Verify trend data points if available
                if trends:
                    # Check first trend item for required fields
                    first_trend = trends[0]
                    required_fields = ["project_id", "name", "category", "funding_velocity", 
                                      "funding_percentage", "success_probability", "risk_level", 
                                      "days_remaining"]
                    
                    fields_present = all(field in first_trend for field in required_fields)
                    
                    log_test_result(f"Funding Trends ({days} days) - Trend Data", 
                                   fields_present, 
                                   f"Trend items contain all required fields: {fields_present}")
                    
                    # Verify funding velocity calculation
                    has_velocity = "funding_velocity" in first_trend
                    velocity_valid = isinstance(first_trend.get("funding_velocity"), (int, float))
                    
                    log_test_result(f"Funding Trends ({days} days) - Velocity Calculation", 
                                   has_velocity and velocity_valid, 
                                   f"Funding velocity is properly calculated")
            else:
                if days == 30:
                    test_results["analytics_endpoints"]["funding_trends"]["status"] = "failed"
                
                log_test_result(f"Funding Trends ({days} days)", 
                               False, 
                               f"API error: {response.status_code} - {response.text}")
        
        return True
    except Exception as e:
        test_results["analytics_endpoints"]["funding_trends"]["status"] = "error"
        log_test_result("Funding Trends", False, f"Error: {str(e)}")
        return False

def test_roi_predictions():
    """Test the ROI predictions endpoint"""
    logger.info("\n🧪 Testing ROI Predictions Endpoint")
    
    try:
        # Make request to ROI predictions endpoint
        start_time = time.time()
        response = requests.get(
            f"{BACKEND_URL}/analytics/roi-predictions",
            headers=get_auth_headers()
        )
        response_time = time.time() - start_time
        
        # Update response time in test results
        test_results["analytics_endpoints"]["roi_predictions"]["response_time"] = response_time
        
        if response.status_code == 200:
            data = response.json()
            test_results["analytics_endpoints"]["roi_predictions"]["status"] = "passed"
            
            # Verify data structure
            has_current_roi = "current_roi" in data
            has_predictions = "predictions" in data
            has_confidence = "confidence_level" in data
            has_factors = "factors" in data
            
            structure_valid = all([has_current_roi, has_predictions, has_confidence, has_factors])
            
            log_test_result("ROI Predictions - Data Structure", 
                           structure_valid, 
                           f"Response contains all required sections: {structure_valid}")
            
            # Verify prediction timeframes
            if has_predictions:
                predictions = data["predictions"]
                required_timeframes = ["3_month", "6_month", "1_year", "2_year"]
                
                timeframes_present = all(timeframe in predictions for timeframe in required_timeframes)
                
                log_test_result("ROI Predictions - Timeframes", 
                               timeframes_present, 
                               f"Predictions include all required timeframes: {timeframes_present}")
            
            # Verify confidence level
            if has_confidence:
                confidence = data["confidence_level"]
                valid_confidence = confidence in ["low", "medium", "high"]
                
                log_test_result("ROI Predictions - Confidence Level", 
                               valid_confidence, 
                               f"Confidence level is valid: {confidence}")
            
            # Verify factors analysis
            if has_factors:
                factors = data["factors"]
                required_factors = ["portfolio_diversification", "market_sentiment", "historical_performance"]
                
                factors_present = all(factor in factors for factor in required_factors)
                
                log_test_result("ROI Predictions - Factors Analysis", 
                               factors_present, 
                               f"Factors analysis includes all required factors: {factors_present}")
            
            # Verify recommendations
            has_recommendations = "recommendations" in data
            
            log_test_result("ROI Predictions - Recommendations", 
                           has_recommendations, 
                           f"Response includes recommendations: {has_recommendations}")
            
            return True
        else:
            test_results["analytics_endpoints"]["roi_predictions"]["status"] = "failed"
            log_test_result("ROI Predictions", 
                           False, 
                           f"API error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        test_results["analytics_endpoints"]["roi_predictions"]["status"] = "error"
        log_test_result("ROI Predictions", False, f"Error: {str(e)}")
        return False

def test_risk_analytics():
    """Test the risk analytics endpoint"""
    logger.info("\n🧪 Testing Risk Analytics Endpoint")
    
    try:
        # Make request to risk analytics endpoint
        start_time = time.time()
        response = requests.get(
            f"{BACKEND_URL}/analytics/risk",
            headers=get_auth_headers()
        )
        response_time = time.time() - start_time
        
        # Update response time in test results
        test_results["analytics_endpoints"]["risk"]["response_time"] = response_time
        
        if response.status_code == 200:
            data = response.json()
            test_results["analytics_endpoints"]["risk"]["status"] = "passed"
            
            # Verify data structure
            has_overall_score = "overall_risk_score" in data
            has_distribution = "risk_distribution" in data
            has_concentration = "concentration_risk" in data
            has_market_risk = "market_risk" in data
            has_liquidity = "liquidity_risk" in data
            has_diversification = "diversification_score" in data
            has_recommendations = "risk_recommendations" in data
            has_stress_test = "stress_test" in data
            
            structure_valid = all([
                has_overall_score, has_distribution, has_concentration, 
                has_market_risk, has_liquidity, has_diversification,
                has_recommendations, has_stress_test
            ])
            
            log_test_result("Risk Analytics - Data Structure", 
                           structure_valid, 
                           f"Response contains all required sections: {structure_valid}")
            
            # Verify risk scoring
            if has_overall_score:
                overall_score = data["overall_risk_score"]
                valid_score = isinstance(overall_score, (int, float)) and 0 <= overall_score <= 100
                
                log_test_result("Risk Analytics - Overall Score", 
                               valid_score, 
                               f"Overall risk score is valid: {overall_score}")
            
            # Verify risk distribution
            if has_distribution:
                distribution = data["risk_distribution"]
                # For empty portfolio, distribution might be empty but still valid
                if distribution:
                    required_levels = ["low", "medium", "high"]
                    levels_present = all(level in distribution for level in required_levels)
                    
                    log_test_result("Risk Analytics - Risk Distribution", 
                                   levels_present, 
                                   f"Risk distribution includes all risk levels: {levels_present}")
                else:
                    log_test_result("Risk Analytics - Risk Distribution", 
                                   True, 
                                   f"Risk distribution is empty (valid for empty portfolio)")
            
            # Verify concentration risk calculation (HHI index)
            if has_concentration:
                concentration = data["concentration_risk"]
                valid_concentration = isinstance(concentration, (int, float)) and 0 <= concentration <= 1
                
                log_test_result("Risk Analytics - Concentration Risk (HHI)", 
                               valid_concentration, 
                               f"Concentration risk is valid HHI index: {concentration}")
            
            # Verify stress testing
            if has_stress_test:
                stress_test = data["stress_test"]
                required_scenarios = ["market_downturn_20pct", "pending_failures_50pct", "largest_project_failure"]
                
                scenarios_present = all(scenario in stress_test for scenario in required_scenarios)
                
                log_test_result("Risk Analytics - Stress Testing", 
                               scenarios_present, 
                               f"Stress test includes all required scenarios: {scenarios_present}")
            
            return True
        else:
            test_results["analytics_endpoints"]["risk"]["status"] = "failed"
            log_test_result("Risk Analytics", 
                           False, 
                           f"API error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        test_results["analytics_endpoints"]["risk"]["status"] = "error"
        log_test_result("Risk Analytics", False, f"Error: {str(e)}")
        return False

def test_market_insights():
    """Test the market insights endpoint"""
    logger.info("\n🧪 Testing Market Insights Endpoint")
    
    try:
        # Make request to market insights endpoint
        start_time = time.time()
        response = requests.get(
            f"{BACKEND_URL}/analytics/market-insights",
            headers=get_auth_headers()
        )
        response_time = time.time() - start_time
        
        # Update response time in test results
        test_results["analytics_endpoints"]["market_insights"]["response_time"] = response_time
        
        if response.status_code == 200:
            data = response.json()
            test_results["analytics_endpoints"]["market_insights"]["status"] = "passed"
            
            # Verify data structure
            has_category_performance = "category_performance" in data
            has_emerging_trends = "emerging_trends" in data
            has_success_factors = "success_factors" in data
            has_market_opportunities = "market_opportunities" in data
            has_competitive_landscape = "competitive_landscape" in data
            has_timing_insights = "timing_insights" in data
            
            structure_valid = all([
                has_category_performance, has_emerging_trends, has_success_factors,
                has_market_opportunities, has_competitive_landscape, has_timing_insights
            ])
            
            log_test_result("Market Insights - Data Structure", 
                           structure_valid, 
                           f"Response contains all required sections: {structure_valid}")
            
            # Verify category performance analysis
            if has_category_performance:
                category_performance = data["category_performance"]
                has_top_categories = "top_performing_categories" in category_performance
                
                log_test_result("Market Insights - Category Performance", 
                               has_top_categories, 
                               f"Category performance analysis includes top categories")
            
            # Verify emerging trends
            if has_emerging_trends:
                emerging_trends = data["emerging_trends"]
                valid_trends = isinstance(emerging_trends, list)
                
                log_test_result("Market Insights - Emerging Trends", 
                               valid_trends, 
                               f"Emerging trends is a valid array with {len(emerging_trends)} items")
            
            # Verify success factors
            if has_success_factors:
                success_factors = data["success_factors"]
                valid_factors = isinstance(success_factors, list)
                
                log_test_result("Market Insights - Success Factors", 
                               valid_factors, 
                               f"Success factors is a valid array with {len(success_factors)} items")
            
            # Verify market opportunities
            if has_market_opportunities:
                opportunities = data["market_opportunities"]
                valid_opportunities = isinstance(opportunities, list)
                
                log_test_result("Market Insights - Market Opportunities", 
                               valid_opportunities, 
                               f"Market opportunities is a valid array with {len(opportunities)} items")
            
            return True
        else:
            test_results["analytics_endpoints"]["market_insights"]["status"] = "failed"
            log_test_result("Market Insights", 
                           False, 
                           f"API error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        test_results["analytics_endpoints"]["market_insights"]["status"] = "error"
        log_test_result("Market Insights", False, f"Error: {str(e)}")
        return False

def test_empty_portfolio():
    """Test analytics endpoints with an empty portfolio"""
    logger.info("\n🧪 Testing Analytics Endpoints with Empty Portfolio")
    
    # TODO: Implement this test by creating a new user with no portfolio
    # For now, we'll skip this test as it requires more complex setup
    test_results["skipped_tests"] += 1
    logger.info("⚠️ Empty portfolio test skipped - requires new user creation")

def run_all_analytics_tests():
    """Run all analytics service tests"""
    logger.info("🚀 Starting Kickstarter Investment Tracker Analytics Service Tests")
    logger.info(f"🔗 Testing API at: {BACKEND_URL}")
    
    # Authenticate first
    if not authenticate():
        logger.error("❌ Authentication failed. Skipping all tests.")
        test_results["skipped_tests"] += 5
        return
    
    # Run all analytics tests
    test_dashboard_analytics()
    test_funding_trends()
    test_roi_predictions()
    test_risk_analytics()
    test_market_insights()
    
    # Print test summary
    logger.info("\n📊 ANALYTICS SERVICE TEST SUMMARY")
    logger.info(f"Total Tests: {test_results['total_tests']}")
    logger.info(f"Passed: {test_results['passed_tests']}")
    logger.info(f"Failed: {test_results['failed_tests']}")
    logger.info(f"Skipped: {test_results['skipped_tests']}")
    
    # Print endpoint status summary
    logger.info("\n📊 ANALYTICS ENDPOINTS STATUS")
    for endpoint, data in test_results["analytics_endpoints"].items():
        status_emoji = "✅" if data["status"] == "passed" else "❌"
        logger.info(f"{status_emoji} {endpoint.replace('_', ' ').title()}: {data['status'].upper()} ({data['response_time']:.4f}s)")
    
    success_rate = (test_results['passed_tests'] / test_results['total_tests']) * 100 if test_results['total_tests'] > 0 else 0
    logger.info(f"Success Rate: {success_rate:.2f}%")
    
    if test_results['failed_tests'] == 0:
        logger.info("✅ All analytics service tests passed successfully!")
    else:
        logger.error(f"❌ {test_results['failed_tests']} tests failed.")

if __name__ == "__main__":
    run_all_analytics_tests()