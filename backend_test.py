#!/usr/bin/env python3
import requests
import json
import time
import uuid
from datetime import datetime, timedelta
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
logger = logging.getLogger("backend_test")

# Backend API URL from environment
BACKEND_URL = "https://d339d4fa-17fe-472f-aa53-c381cf22961a.preview.emergentagent.com/api"

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
        db_status = data.get("checks", {}).get("database", {}).get("status") == "healthy"
        log_test_result("Health Check - Database Connectivity", 
                       db_status, 
                       f"Database status: {data.get('checks', {}).get('database', {}).get('status')}")
        
        # Check indexes
        indexes = data.get("checks", {}).get("indexes", {})
        projects_indexes = indexes.get("projects_indexes", 0)
        investments_indexes = indexes.get("investments_indexes", 0)
        
        # Verify expected index counts (12 for projects, 6 for investments)
        projects_indexes_valid = projects_indexes == 12
        investments_indexes_valid = investments_indexes == 6
        
        log_test_result("Health Check - Projects Indexes", 
                       projects_indexes_valid, 
                       f"Projects indexes: {projects_indexes}/12")
        
        log_test_result("Health Check - Investments Indexes", 
                       investments_indexes_valid, 
                       f"Investments indexes: {investments_indexes}/6")
        
        # Check collections
        collections = data.get("checks", {}).get("collections", {})
        log_test_result("Health Check - Collections", 
                       collections.get("status") == "healthy", 
                       f"Projects: {collections.get('projects_count')}, Investments: {collections.get('investments_count')}")
        
        # Check Redis cache status
        redis_status = data.get("checks", {}).get("redis_cache", {}).get("status")
        redis_connected = redis_status == "connected"
        
        log_test_result("Health Check - Redis Cache", 
                       redis_connected, 
                       f"Redis status: {redis_status}")
        
        return True
    except Exception as e:
        log_test_result("Health Check", False, f"Error: {str(e)}")
        return False

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
        db_status = data.get("checks", {}).get("database", {}).get("status") == "healthy"
        log_test_result("Health Check - Database Connectivity", 
                       db_status, 
                       f"Database status: {data.get('checks', {}).get('database', {}).get('status')}")
        
        # Check indexes
        indexes = data.get("checks", {}).get("indexes", {})
        projects_indexes = indexes.get("projects_indexes", 0)
        investments_indexes = indexes.get("investments_indexes", 0)
        
        # Verify expected index counts (12 for projects, 6 for investments)
        projects_indexes_valid = projects_indexes == 12
        investments_indexes_valid = investments_indexes == 6
        
        log_test_result("Health Check - Projects Indexes", 
                       projects_indexes_valid, 
                       f"Projects indexes: {projects_indexes}/12")
        
        log_test_result("Health Check - Investments Indexes", 
                       investments_indexes_valid, 
                       f"Investments indexes: {investments_indexes}/6")
        
        # Check collections
        collections = data.get("checks", {}).get("collections", {})
        log_test_result("Health Check - Collections", 
                       collections.get("status") == "healthy", 
                       f"Projects: {collections.get('projects_count')}, Investments: {collections.get('investments_count')}")
        
        return True
    except Exception as e:
        log_test_result("Health Check", False, f"Error: {str(e)}")
        return False

def test_project_crud():
    """Test CRUD operations for projects"""
    created_project_id = None
    
    # CREATE
    try:
        response = requests.post(f"{BACKEND_URL}/projects", json=test_project)
        response.raise_for_status()
        
        data = response.json()
        created_project_id = data.get("id")
        
        log_test_result("Project Creation", 
                       bool(created_project_id), 
                       f"Created project with ID: {created_project_id}")
    except Exception as e:
        log_test_result("Project Creation", False, f"Error: {str(e)}")
        return False
    
    # READ
    try:
        # Get all projects
        response = requests.get(f"{BACKEND_URL}/projects")
        response.raise_for_status()
        
        projects = response.json()
        log_test_result("Get All Projects", 
                       isinstance(projects, list), 
                       f"Retrieved {len(projects)} projects")
        
        # Get specific project
        response = requests.get(f"{BACKEND_URL}/projects/{created_project_id}")
        response.raise_for_status()
        
        project = response.json()
        log_test_result("Get Project by ID", 
                       project.get("id") == created_project_id, 
                       f"Retrieved project: {project.get('name')}")
        
        # Test filtering by category
        response = requests.get(f"{BACKEND_URL}/projects?category=Technology")
        response.raise_for_status()
        
        filtered_projects = response.json()
        log_test_result("Filter Projects by Category", 
                       isinstance(filtered_projects, list), 
                       f"Retrieved {len(filtered_projects)} technology projects")
        
        # Test filtering by risk level
        response = requests.get(f"{BACKEND_URL}/projects?risk_level=medium")
        response.raise_for_status()
        
        risk_filtered_projects = response.json()
        log_test_result("Filter Projects by Risk Level", 
                       isinstance(risk_filtered_projects, list), 
                       f"Retrieved {len(risk_filtered_projects)} medium-risk projects")
        
        # Test pagination
        response = requests.get(f"{BACKEND_URL}/projects?page=1&page_size=10")
        response.raise_for_status()
        
        paginated_projects = response.json()
        log_test_result("Project Pagination", 
                       isinstance(paginated_projects, list) and len(paginated_projects) <= 10, 
                       f"Retrieved {len(paginated_projects)} projects with pagination")
        
    except Exception as e:
        log_test_result("Project Read Operations", False, f"Error: {str(e)}")
    
    # UPDATE
    try:
        # Update the project
        updated_data = test_project.copy()
        updated_data["name"] = f"Updated Project {uuid.uuid4()}"
        updated_data["pledged_amount"] = 7500.0
        
        response = requests.put(f"{BACKEND_URL}/projects/{created_project_id}", json=updated_data)
        response.raise_for_status()
        
        updated_project = response.json()
        log_test_result("Update Project", 
                       updated_project.get("name") == updated_data["name"], 
                       f"Updated project name to: {updated_project.get('name')}")
    except Exception as e:
        log_test_result("Project Update", False, f"Error: {str(e)}")
    
    # Test investment CRUD with the created project
    if created_project_id:
        test_investment_crud(created_project_id)
    
    # DELETE
    try:
        response = requests.delete(f"{BACKEND_URL}/projects/{created_project_id}")
        response.raise_for_status()
        
        log_test_result("Delete Project", 
                       response.status_code == 200, 
                       f"Deleted project with ID: {created_project_id}")
        
        # Verify deletion
        response = requests.get(f"{BACKEND_URL}/projects/{created_project_id}")
        deletion_verified = response.status_code == 404
        
        log_test_result("Verify Project Deletion", 
                       deletion_verified, 
                       "Project no longer exists")
    except Exception as e:
        log_test_result("Project Deletion", False, f"Error: {str(e)}")
    
    return True

def test_investment_crud(project_id):
    """Test CRUD operations for investments"""
    created_investment_id = None
    
    # Add project_id to the test investment
    test_investment["project_id"] = project_id
    
    # CREATE
    try:
        response = requests.post(f"{BACKEND_URL}/investments", json=test_investment)
        response.raise_for_status()
        
        data = response.json()
        created_investment_id = data.get("id")
        
        log_test_result("Investment Creation", 
                       bool(created_investment_id), 
                       f"Created investment with ID: {created_investment_id}")
    except Exception as e:
        log_test_result("Investment Creation", False, f"Error: {str(e)}")
        return
    
    # READ
    try:
        # Get all investments
        response = requests.get(f"{BACKEND_URL}/investments")
        response.raise_for_status()
        
        investments = response.json()
        log_test_result("Get All Investments", 
                       isinstance(investments, list), 
                       f"Retrieved {len(investments)} investments")
        
        # Get investments for specific project
        response = requests.get(f"{BACKEND_URL}/investments?project_id={project_id}")
        response.raise_for_status()
        
        project_investments = response.json()
        log_test_result("Get Investments by Project ID", 
                       isinstance(project_investments, list) and len(project_investments) > 0, 
                       f"Retrieved {len(project_investments)} investments for project")
    except Exception as e:
        log_test_result("Investment Read Operations", False, f"Error: {str(e)}")

def test_dashboard_stats():
    """Test dashboard statistics endpoint"""
    try:
        response = requests.get(f"{BACKEND_URL}/dashboard/stats")
        response.raise_for_status()
        
        stats = response.json()
        
        # Check if all expected fields are present
        expected_fields = [
            'total_projects', 'total_investments', 'total_invested',
            'risk_distribution', 'category_distribution', 'success_rate', 'avg_investment'
        ]
        
        all_fields_present = all(field in stats for field in expected_fields)
        
        log_test_result("Dashboard Statistics", 
                       all_fields_present, 
                       f"Retrieved dashboard stats with {len(expected_fields)} metrics")
    except Exception as e:
        log_test_result("Dashboard Statistics", False, f"Error: {str(e)}")

def test_ai_analysis():
    """Test AI analysis endpoints"""
    try:
        # Test recommendations endpoint
        response = requests.get(f"{BACKEND_URL}/recommendations")
        response.raise_for_status()
        
        recommendations = response.json()
        
        log_test_result("AI Recommendations", 
                       "recommendations" in recommendations, 
                       f"Retrieved {len(recommendations.get('recommendations', []))} AI recommendations")
    except Exception as e:
        log_test_result("AI Recommendations", False, f"Error: {str(e)}")
    
    try:
        # Test advanced analytics
        response = requests.get(f"{BACKEND_URL}/analytics/advanced")
        response.raise_for_status()
        
        analytics = response.json()
        
        expected_fields = [
            'roi_prediction', 'funding_velocity', 'market_sentiment',
            'diversification_score', 'risk_adjusted_return', 'recommended_actions'
        ]
        
        all_fields_present = all(field in analytics for field in expected_fields)
        
        log_test_result("Advanced Analytics", 
                       all_fields_present, 
                       f"Retrieved advanced analytics with {len(expected_fields)} metrics")
    except Exception as e:
        log_test_result("Advanced Analytics", False, f"Error: {str(e)}")
    
    try:
        # Test funding trends
        response = requests.get(f"{BACKEND_URL}/analytics/funding-trends")
        response.raise_for_status()
        
        trends = response.json()
        
        log_test_result("Funding Trends", 
                       "trends" in trends, 
                       f"Retrieved funding trends data")
    except Exception as e:
        log_test_result("Funding Trends", False, f"Error: {str(e)}")

def test_alerts():
    """Test alerts endpoints"""
    try:
        # Test get alerts
        response = requests.get(f"{BACKEND_URL}/alerts")
        response.raise_for_status()
        
        alerts = response.json()
        
        log_test_result("Smart Alerts", 
                       isinstance(alerts, list), 
                       f"Retrieved {len(alerts)} smart alerts")
    except Exception as e:
        log_test_result("Smart Alerts", False, f"Error: {str(e)}")
    
    try:
        # Test alert settings
        response = requests.get(f"{BACKEND_URL}/alerts/settings")
        response.raise_for_status()
        
        settings = response.json()
        
        expected_fields = [
            'id', 'user_id', 'notification_frequency', 'min_funding_velocity',
            'preferred_categories', 'max_risk_level', 'min_success_probability',
            'browser_notifications', 'email_notifications'
        ]
        
        all_fields_present = all(field in settings for field in expected_fields)
        
        log_test_result("Alert Settings", 
                       all_fields_present, 
                       f"Retrieved alert settings")
        
        # Test updating alert settings
        new_settings = settings.copy()
        new_settings["min_funding_velocity"] = 0.2
        new_settings["preferred_categories"] = ["Technology", "Games"]
        
        response = requests.post(f"{BACKEND_URL}/alerts/settings", json=new_settings)
        response.raise_for_status()
        
        updated_settings = response.json()
        
        settings_updated = (
            updated_settings["min_funding_velocity"] == 0.2 and
            "Games" in updated_settings["preferred_categories"]
        )
        
        log_test_result("Update Alert Settings", 
                       settings_updated, 
                       f"Updated alert settings successfully")
    except Exception as e:
        log_test_result("Alert Settings Operations", False, f"Error: {str(e)}")

def run_all_tests():
    """Run all backend API tests"""
    logger.info("🚀 Starting Kickstarter Investment Tracker Backend Tests")
    logger.info(f"🔗 Testing API at: {BACKEND_URL}")
    
    # Test health endpoint first
    health_ok = test_health_endpoint()
    
    if health_ok:
        # Run all other tests
        test_project_crud()
        test_dashboard_stats()
        test_ai_analysis()
        test_alerts()
    else:
        logger.error("❌ Health check failed. Skipping remaining tests.")
        test_results["skipped_tests"] += 1
    
    # Print test summary
    logger.info("\n📊 TEST SUMMARY")
    logger.info(f"Total Tests: {test_results['total_tests']}")
    logger.info(f"Passed: {test_results['passed_tests']}")
    logger.info(f"Failed: {test_results['failed_tests']}")
    logger.info(f"Skipped: {test_results['skipped_tests']}")
    
    success_rate = (test_results['passed_tests'] / test_results['total_tests']) * 100 if test_results['total_tests'] > 0 else 0
    logger.info(f"Success Rate: {success_rate:.2f}%")
    
    if test_results['failed_tests'] == 0:
        logger.info("✅ All tests passed successfully!")
    else:
        logger.error(f"❌ {test_results['failed_tests']} tests failed.")

if __name__ == "__main__":
    run_all_tests()
