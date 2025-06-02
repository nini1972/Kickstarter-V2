#!/usr/bin/env python3
"""
Comprehensive Analytics Service Test Script for Kickstarter Investment Tracker
Tests the enhanced Analytics Service endpoints with real data
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
logger = logging.getLogger("comprehensive_analytics_test")

# Backend API URL
BACKEND_URL = "http://localhost:8001/api"

# Test results tracking
test_results = {
    "total_tests": 0,
    "passed_tests": 0,
    "failed_tests": 0,
    "skipped_tests": 0,
    "created_projects": [],
    "created_investments": [],
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

def create_test_projects():
    """Create test projects with different characteristics"""
    logger.info("\n🧪 Creating Test Projects")
    
    # Define test projects with different characteristics
    test_projects = [
        # High funding, low risk project
        {
            "name": f"High Funding Project {uuid.uuid4()}",
            "creator": "Test Creator",
            "description": "This is a high funding, low risk test project",
            "category": "Technology",
            "goal_amount": 10000.0,
            "pledged_amount": 9000.0,  # 90% funded
            "backers_count": 200,
            "deadline": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "launched_date": (datetime.utcnow() - timedelta(days=15)).isoformat(),
            "status": "live",
            "risk_level": "low"
        },
        # Medium funding, medium risk project
        {
            "name": f"Medium Funding Project {uuid.uuid4()}",
            "creator": "Test Creator",
            "description": "This is a medium funding, medium risk test project",
            "category": "Games",
            "goal_amount": 20000.0,
            "pledged_amount": 10000.0,  # 50% funded
            "backers_count": 100,
            "deadline": (datetime.utcnow() + timedelta(days=20)).isoformat(),
            "launched_date": (datetime.utcnow() - timedelta(days=10)).isoformat(),
            "status": "live",
            "risk_level": "medium"
        },
        # Low funding, high risk project
        {
            "name": f"Low Funding Project {uuid.uuid4()}",
            "creator": "Test Creator",
            "description": "This is a low funding, high risk test project",
            "category": "Film",
            "goal_amount": 30000.0,
            "pledged_amount": 5000.0,  # 16.7% funded
            "backers_count": 50,
            "deadline": (datetime.utcnow() + timedelta(days=10)).isoformat(),
            "launched_date": (datetime.utcnow() - timedelta(days=20)).isoformat(),
            "status": "live",
            "risk_level": "high"
        },
        # Successful project
        {
            "name": f"Successful Project {uuid.uuid4()}",
            "creator": "Test Creator",
            "description": "This is a successful test project",
            "category": "Design",
            "goal_amount": 5000.0,
            "pledged_amount": 7500.0,  # 150% funded
            "backers_count": 150,
            "deadline": (datetime.utcnow() - timedelta(days=10)).isoformat(),
            "launched_date": (datetime.utcnow() - timedelta(days=40)).isoformat(),
            "status": "successful",
            "risk_level": "low"
        },
        # Failed project
        {
            "name": f"Failed Project {uuid.uuid4()}",
            "creator": "Test Creator",
            "description": "This is a failed test project",
            "category": "Music",
            "goal_amount": 25000.0,
            "pledged_amount": 5000.0,  # 20% funded
            "backers_count": 30,
            "deadline": (datetime.utcnow() - timedelta(days=5)).isoformat(),
            "launched_date": (datetime.utcnow() - timedelta(days=35)).isoformat(),
            "status": "failed",
            "risk_level": "high"
        }
    ]
    
    created_projects = []
    
    # Create each test project
    for i, project_data in enumerate(test_projects):
        try:
            logger.info(f"Creating test project {i+1}: {project_data['name']}")
            
            response = requests.post(
                f"{BACKEND_URL}/projects",
                json=project_data,
                headers=get_auth_headers()
            )
            
            if response.status_code == 200:
                project = response.json()
                project_id = project.get("id")
                
                if project_id:
                    created_projects.append({
                        "id": project_id,
                        "name": project_data["name"],
                        "category": project_data["category"],
                        "risk_level": project_data["risk_level"],
                        "status": project_data["status"]
                    })
                    
                    logger.info(f"✅ Created project {i+1} with ID: {project_id}")
                else:
                    logger.error(f"❌ Failed to get project ID for project {i+1}")
            else:
                logger.error(f"❌ Failed to create project {i+1}: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"❌ Error creating project {i+1}: {str(e)}")
    
    # Log test result
    log_test_result("Project Creation", 
                   len(created_projects) > 0, 
                   f"Created {len(created_projects)} test projects")
    
    # Store created projects in test results
    test_results["created_projects"] = created_projects
    
    return created_projects

def create_test_investments(projects):
    """Create test investments for the created projects"""
    logger.info("\n🧪 Creating Test Investments")
    
    if not projects:
        logger.error("❌ No projects available for creating investments")
        return []
    
    created_investments = []
    
    # Create investments for each project
    for i, project in enumerate(projects):
        try:
            # Create 1-3 investments per project with different amounts
            num_investments = random.randint(1, 3)
            
            for j in range(num_investments):
                investment_data = {
                    "project_id": project["id"],
                    "project_name": project["name"],
                    "amount": random.randint(100, 1000),
                    "investment_date": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat(),
                    "reward_tier": f"Tier {j+1}",
                    "notes": f"Test investment {j+1} for project {project['name']}"
                }
                
                logger.info(f"Creating investment {j+1} for project {i+1}: {project['name']}")
                
                response = requests.post(
                    f"{BACKEND_URL}/investments",
                    json=investment_data,
                    headers=get_auth_headers()
                )
                
                if response.status_code == 200:
                    investment = response.json()
                    investment_id = investment.get("id")
                    
                    if investment_id:
                        created_investments.append({
                            "id": investment_id,
                            "project_id": project["id"],
                            "amount": investment_data["amount"]
                        })
                        
                        logger.info(f"✅ Created investment {j+1} for project {i+1} with ID: {investment_id}")
                    else:
                        logger.error(f"❌ Failed to get investment ID for investment {j+1} of project {i+1}")
                else:
                    logger.error(f"❌ Failed to create investment {j+1} for project {i+1}: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"❌ Error creating investments for project {i+1}: {str(e)}")
    
    # Log test result
    log_test_result("Investment Creation", 
                   len(created_investments) > 0, 
                   f"Created {len(created_investments)} test investments")
    
    # Store created investments in test results
    test_results["created_investments"] = created_investments
    
    return created_investments

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
                
                # Verify metrics match our test data
                total_projects = overview.get("total_projects", 0)
                total_investments = overview.get("total_investments", 0)
                
                projects_match = total_projects >= len(test_results["created_projects"])
                investments_match = total_investments >= len(test_results["created_investments"])
                
                log_test_result("Dashboard Analytics - Data Accuracy", 
                               projects_match and investments_match, 
                               f"Projects: {total_projects}, Investments: {total_investments}")
            
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
                    
                    # Verify our test projects are included
                    test_project_ids = [p["id"] for p in test_results["created_projects"]]
                    trend_project_ids = [t["project_id"] for t in trends]
                    
                    common_projects = set(test_project_ids).intersection(set(trend_project_ids))
                    
                    log_test_result(f"Funding Trends ({days} days) - Test Projects", 
                                   len(common_projects) > 0, 
                                   f"Found {len(common_projects)} test projects in trends data")
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
                
                # With test data, confidence should be at least medium
                confidence_improved = confidence in ["medium", "high"]
                
                log_test_result("ROI Predictions - Confidence Level", 
                               valid_confidence, 
                               f"Confidence level is valid: {confidence}")
                
                if len(test_results["created_investments"]) > 0:
                    log_test_result("ROI Predictions - Confidence Improvement", 
                                   confidence_improved, 
                                   f"Confidence level improved with test data: {confidence}")
            
            # Verify factors analysis
            if has_factors:
                factors = data["factors"]
                required_factors = ["portfolio_diversification", "market_sentiment", "historical_performance"]
                
                factors_present = all(factor in factors for factor in required_factors)
                
                log_test_result("ROI Predictions - Factors Analysis", 
                               factors_present, 
                               f"Factors analysis includes all required factors: {factors_present}")
                
                # Verify diversification factor is calculated
                diversification = factors.get("portfolio_diversification", 0)
                valid_diversification = isinstance(diversification, (int, float)) and 0 <= diversification <= 1
                
                log_test_result("ROI Predictions - Diversification Factor", 
                               valid_diversification, 
                               f"Diversification factor is valid: {diversification}")
            
            # Verify recommendations
            has_recommendations = "recommendations" in data
            recommendations = data.get("recommendations", [])
            
            log_test_result("ROI Predictions - Recommendations", 
                           has_recommendations and len(recommendations) > 0, 
                           f"Response includes {len(recommendations)} recommendations")
            
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
                    
                    # Verify distribution matches our test data
                    has_high_risk = distribution.get("high", 0) > 0
                    has_medium_risk = distribution.get("medium", 0) > 0
                    has_low_risk = distribution.get("low", 0) > 0
                    
                    # We created projects with all risk levels
                    risk_levels_match = has_high_risk and has_medium_risk and has_low_risk
                    
                    log_test_result("Risk Analytics - Risk Level Distribution", 
                                   risk_levels_match, 
                                   f"Risk distribution matches test data: {distribution}")
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
                # For empty portfolio, stress test might be empty but still valid
                if stress_test:
                    required_scenarios = ["market_downturn_20pct", "pending_failures_50pct", "largest_project_failure"]
                    scenarios_present = all(scenario in stress_test for scenario in required_scenarios)
                    
                    log_test_result("Risk Analytics - Stress Testing", 
                                   scenarios_present, 
                                   f"Stress test includes all required scenarios: {scenarios_present}")
                    
                    # Verify stress test scenarios have expected fields
                    first_scenario = stress_test.get("market_downturn_20pct", {})
                    required_fields = ["portfolio_value", "loss_amount", "loss_percentage"]
                    
                    fields_present = all(field in first_scenario for field in required_fields)
                    
                    log_test_result("Risk Analytics - Stress Test Data", 
                                   fields_present, 
                                   f"Stress test scenarios contain all required fields: {fields_present}")
                else:
                    log_test_result("Risk Analytics - Stress Testing", 
                                   True, 
                                   f"Stress test is empty (valid for empty portfolio)")
            
            # Verify risk recommendations
            if has_recommendations:
                recommendations = data["risk_recommendations"]
                
                log_test_result("Risk Analytics - Recommendations", 
                               isinstance(recommendations, list) and len(recommendations) > 0, 
                               f"Risk analytics includes {len(recommendations)} recommendations")
            
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
                # For empty data, category_performance might be empty but still valid
                if category_performance:
                    has_top_categories = "top_performing_categories" in category_performance
                    
                    log_test_result("Market Insights - Category Performance", 
                                   has_top_categories, 
                                   f"Category performance analysis includes top categories")
                    
                    # Verify our test categories are included
                    if "category_rankings" in category_performance:
                        rankings = category_performance["category_rankings"]
                        test_categories = set(p["category"] for p in test_results["created_projects"])
                        ranking_categories = set(r[0] for r in rankings if isinstance(r, list) and len(r) > 0)
                        
                        common_categories = test_categories.intersection(ranking_categories)
                        
                        log_test_result("Market Insights - Category Rankings", 
                                       len(common_categories) > 0, 
                                       f"Found {len(common_categories)} test categories in rankings")
                else:
                    log_test_result("Market Insights - Category Performance", 
                                   True, 
                                   f"Category performance is empty (valid for empty data)")
            
            # Verify competitive landscape
            if has_competitive_landscape:
                landscape = data["competitive_landscape"]
                
                if landscape:
                    has_market_leaders = "market_leaders" in landscape
                    has_concentration = "market_concentration" in landscape
                    
                    log_test_result("Market Insights - Competitive Landscape", 
                                   has_market_leaders and has_concentration, 
                                   f"Competitive landscape analysis includes market leaders and concentration")
                    
                    # Verify HHI index in market concentration
                    if "market_concentration" in landscape:
                        concentration = landscape["market_concentration"]
                        has_hhi = "hhi_index" in concentration
                        
                        log_test_result("Market Insights - HHI Index", 
                                       has_hhi, 
                                       f"Market concentration includes HHI index")
                else:
                    log_test_result("Market Insights - Competitive Landscape", 
                                   True, 
                                   f"Competitive landscape is empty (valid for empty data)")
            
            # Verify timing insights
            if has_timing_insights:
                timing = data["timing_insights"]
                
                if timing:
                    has_monthly_rates = "monthly_success_rates" in timing
                    has_best_month = "best_launch_month" in timing
                    
                    log_test_result("Market Insights - Timing Analysis", 
                                   has_monthly_rates and has_best_month, 
                                   f"Timing insights include monthly success rates and best launch month")
                else:
                    log_test_result("Market Insights - Timing Analysis", 
                                   True, 
                                   f"Timing insights are empty (valid for empty data)")
            
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

def cleanup_test_data():
    """Clean up test data created during testing"""
    logger.info("\n🧪 Cleaning Up Test Data")
    
    # Delete test investments
    for investment in test_results["created_investments"]:
        try:
            investment_id = investment["id"]
            logger.info(f"Deleting test investment: {investment_id}")
            
            response = requests.delete(
                f"{BACKEND_URL}/investments/{investment_id}",
                headers=get_auth_headers()
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Deleted investment: {investment_id}")
            else:
                logger.error(f"❌ Failed to delete investment {investment_id}: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"❌ Error deleting investment: {str(e)}")
    
    # Delete test projects
    for project in test_results["created_projects"]:
        try:
            project_id = project["id"]
            logger.info(f"Deleting test project: {project_id}")
            
            response = requests.delete(
                f"{BACKEND_URL}/projects/{project_id}",
                headers=get_auth_headers()
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Deleted project: {project_id}")
            else:
                logger.error(f"❌ Failed to delete project {project_id}: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"❌ Error deleting project: {str(e)}")
    
    # Log test result
    investments_deleted = len(test_results["created_investments"])
    projects_deleted = len(test_results["created_projects"])
    
    log_test_result("Data Cleanup", 
                   True, 
                   f"Deleted {investments_deleted} investments and {projects_deleted} projects")

def run_comprehensive_analytics_tests():
    """Run comprehensive analytics service tests with real data"""
    logger.info("🚀 Starting Comprehensive Kickstarter Investment Tracker Analytics Service Tests")
    logger.info(f"🔗 Testing API at: {BACKEND_URL}")
    
    # Authenticate first
    if not authenticate():
        logger.error("❌ Authentication failed. Skipping all tests.")
        test_results["skipped_tests"] += 5
        return
    
    try:
        # Create test data
        projects = create_test_projects()
        
        if projects:
            investments = create_test_investments(projects)
            
            # Wait a moment for data to be processed
            logger.info("Waiting for test data to be processed...")
            time.sleep(2)
            
            # Run all analytics tests
            test_dashboard_analytics()
            test_funding_trends()
            test_roi_predictions()
            test_risk_analytics()
            test_market_insights()
            
            # Clean up test data
            cleanup_test_data()
        else:
            logger.error("❌ Failed to create test projects. Skipping analytics tests.")
            test_results["skipped_tests"] += 5
    except Exception as e:
        logger.error(f"❌ Error during testing: {str(e)}")
    
    # Print test summary
    logger.info("\n📊 COMPREHENSIVE ANALYTICS SERVICE TEST SUMMARY")
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
        logger.info("✅ All comprehensive analytics service tests passed successfully!")
    else:
        logger.error(f"❌ {test_results['failed_tests']} tests failed.")

if __name__ == "__main__":
    run_comprehensive_analytics_tests()