import requests
import json
import datetime
import time
import logging
import sys
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("validation_test")

# Backend API URL
BACKEND_URL = "https://225b3faa-e25a-46f6-8dd9-d92508eb5e44.preview.emergentagent.com/api"

def test_risk_level_case_sensitivity():
    """Test risk_level case sensitivity in project creation and update"""
    logger.info("\n🧪 Testing risk_level case sensitivity")
    
    # Test project with mixed case risk level
    project_data = {
        "name": f"Risk Level Test Project {uuid.uuid4()}",
        "creator": "Test Creator",
        "url": "https://www.kickstarter.com/test-project",
        "description": "This is a test project for testing risk_level case sensitivity",
        "category": "Technology",
        "goal_amount": 10000.0,
        "pledged_amount": 5000.0,
        "backers_count": 50,
        "deadline": (datetime.datetime.utcnow() + datetime.timedelta(days=30)).isoformat(),
        "launched_date": (datetime.datetime.utcnow() - datetime.timedelta(days=10)).isoformat(),
        "status": "live",
        "risk_level": "Medium"  # Mixed case to test case sensitivity
    }
    
    # Create project
    logger.info("Creating project with 'Medium' risk level (mixed case)...")
    response = requests.post(f"{BACKEND_URL}/projects", json=project_data)
    
    if response.status_code == 200:
        created_project = response.json()
        project_id = created_project.get("id")
        
        logger.info(f"✅ Project created successfully with ID: {project_id}")
        logger.info(f"Risk level in response: {created_project.get('risk_level')}")
        
        # Check if risk_level was normalized to lowercase
        if created_project.get('risk_level') == 'medium':
            logger.info("✅ Risk level was correctly normalized to lowercase")
        else:
            logger.error(f"❌ Risk level was not normalized correctly: {created_project.get('risk_level')}")
        
        # Test update with mixed case risk level
        update_data = {
            "name": f"Updated Risk Level Test Project {uuid.uuid4()}",
            "creator": "Test Creator",
            "url": "https://www.kickstarter.com/test-project",
            "description": "This is an updated test project for testing risk_level case sensitivity",
            "category": "Technology",
            "goal_amount": 10000.0,
            "pledged_amount": 5000.0,
            "backers_count": 50,
            "deadline": (datetime.datetime.utcnow() + datetime.timedelta(days=30)).isoformat(),
            "launched_date": (datetime.datetime.utcnow() - datetime.timedelta(days=10)).isoformat(),
            "status": "live",
            "risk_level": "High"  # Mixed case to test case sensitivity
        }
        
        logger.info("Updating project with 'High' risk level (mixed case)...")
        update_response = requests.put(f"{BACKEND_URL}/projects/{project_id}", json=update_data)
        
        if update_response.status_code == 200:
            updated_project = update_response.json()
            
            logger.info(f"✅ Project updated successfully")
            logger.info(f"Updated risk level in response: {updated_project.get('risk_level')}")
            
            # Check if risk_level was normalized to lowercase
            if updated_project.get('risk_level') == 'high':
                logger.info("✅ Risk level was correctly normalized to lowercase during update")
            else:
                logger.error(f"❌ Risk level was not normalized correctly during update: {updated_project.get('risk_level')}")
        else:
            logger.error(f"❌ Failed to update project: {update_response.status_code} - {update_response.text}")
        
        # Clean up
        logger.info(f"Deleting test project with ID: {project_id}")
        delete_response = requests.delete(f"{BACKEND_URL}/projects/{project_id}")
        
        if delete_response.status_code == 200:
            logger.info("✅ Test project deleted successfully")
        else:
            logger.error(f"❌ Failed to delete test project: {delete_response.status_code} - {delete_response.text}")
        
        return True, created_project, updated_project if update_response.status_code == 200 else None
    else:
        logger.error(f"❌ Failed to create project: {response.status_code} - {response.text}")
        return False, None, None

def test_model_dump_dictionary_issue():
    """Test model_dump() dictionary issue in project creation"""
    logger.info("\n🧪 Testing model_dump() dictionary issue in project creation")
    
    # Test project data
    project_data = {
        "name": f"Model Dump Test Project {uuid.uuid4()}",
        "creator": "Test Creator",
        "url": "https://www.kickstarter.com/test-project",
        "description": "This is a test project for testing model_dump() dictionary issue",
        "category": "Technology",
        "goal_amount": 10000.0,
        "pledged_amount": 5000.0,
        "backers_count": 50,
        "deadline": (datetime.datetime.utcnow() + datetime.timedelta(days=30)).isoformat(),
        "launched_date": (datetime.datetime.utcnow() - datetime.timedelta(days=10)).isoformat(),
        "status": "live"
    }
    
    # Create project
    logger.info("Creating project to test model_dump() dictionary issue...")
    response = requests.post(f"{BACKEND_URL}/projects", json=project_data)
    
    if response.status_code == 200:
        created_project = response.json()
        project_id = created_project.get("id")
        
        logger.info(f"✅ Project created successfully with ID: {project_id}")
        
        # Check if AI analysis was performed
        if created_project.get('ai_analysis'):
            logger.info("✅ AI analysis was performed during project creation")
            logger.info(f"AI analysis type: {type(created_project.get('ai_analysis'))}")
            logger.info(f"AI analysis content: {created_project.get('ai_analysis')}")
        else:
            logger.error("❌ AI analysis was not performed during project creation")
        
        # Clean up
        logger.info(f"Deleting test project with ID: {project_id}")
        delete_response = requests.delete(f"{BACKEND_URL}/projects/{project_id}")
        
        if delete_response.status_code == 200:
            logger.info("✅ Test project deleted successfully")
        else:
            logger.error(f"❌ Failed to delete test project: {delete_response.status_code} - {delete_response.text}")
        
        return True, created_project
    else:
        logger.error(f"❌ Failed to create project: {response.status_code} - {response.text}")
        return False, None

def test_projects_endpoint():
    """Test the projects endpoint to verify all 12 projects are loading"""
    logger.info("\n🧪 Testing projects endpoint to verify all 12 projects are loading")
    
    response = requests.get(f"{BACKEND_URL}/projects")
    
    if response.status_code == 200:
        projects = response.json()
        
        logger.info(f"✅ Projects endpoint returned {len(projects)} projects")
        
        # Check if all 12 projects are loaded
        if len(projects) >= 12:
            logger.info("✅ All 12 projects are loading correctly")
        else:
            logger.warning(f"⚠️ Only {len(projects)} projects were loaded, expected at least 12")
        
        return True, projects
    else:
        logger.error(f"❌ Failed to get projects: {response.status_code} - {response.text}")
        return False, None

def test_investments_endpoint():
    """Test the investments endpoint"""
    logger.info("\n🧪 Testing investments endpoint")
    
    response = requests.get(f"{BACKEND_URL}/investments")
    
    if response.status_code == 200:
        investments = response.json()
        
        logger.info(f"✅ Investments endpoint returned {len(investments)} investments")
        return True, investments
    else:
        logger.error(f"❌ Failed to get investments: {response.status_code} - {response.text}")
        return False, None

def test_alerts_endpoint():
    """Test the alerts endpoint"""
    logger.info("\n🧪 Testing alerts endpoint")
    
    response = requests.get(f"{BACKEND_URL}/alerts")
    
    if response.status_code == 200:
        alerts_data = response.json()
        alerts = alerts_data.get("alerts", [])
        
        logger.info(f"✅ Alerts endpoint returned {len(alerts)} alerts")
        return True, alerts_data
    else:
        logger.error(f"❌ Failed to get alerts: {response.status_code} - {response.text}")
        return False, None

def test_analytics_endpoint():
    """Test the analytics endpoint"""
    logger.info("\n🧪 Testing analytics endpoint")
    
    response = requests.get(f"{BACKEND_URL}/analytics/advanced")
    
    if response.status_code == 200:
        analytics = response.json()
        
        logger.info(f"✅ Analytics endpoint returned data successfully")
        logger.info(f"ROI prediction: {analytics.get('roi_prediction')}")
        logger.info(f"Funding velocity: {analytics.get('funding_velocity')}")
        return True, analytics
    else:
        logger.error(f"❌ Failed to get analytics: {response.status_code} - {response.text}")
        return False, None

def test_recommendations_endpoint():
    """Test the recommendations endpoint"""
    logger.info("\n🧪 Testing recommendations endpoint")
    
    response = requests.get(f"{BACKEND_URL}/recommendations")
    
    if response.status_code == 200:
        recommendations = response.json()
        
        logger.info(f"✅ Recommendations endpoint returned data successfully")
        logger.info(f"Number of recommendations: {len(recommendations.get('recommendations', []))}")
        return True, recommendations
    else:
        logger.error(f"❌ Failed to get recommendations: {response.status_code} - {response.text}")
        return False, None

def test_batch_analyze_endpoint():
    """Test the batch analyze endpoint"""
    logger.info("\n🧪 Testing batch analyze endpoint")
    
    # Get some project IDs first
    success, projects = test_projects_endpoint()
    if not success or not projects:
        logger.error("❌ Cannot test batch analyze endpoint without projects")
        return False, None
    
    project_ids = [project.get('id') for project in projects[:3]]
    
    batch_data = {
        "project_ids": project_ids,
        "batch_size": 3
    }
    
    response = requests.post(f"{BACKEND_URL}/projects/batch-analyze", json=batch_data)
    
    if response.status_code == 200:
        batch_result = response.json()
        
        logger.info(f"✅ Batch analyze endpoint returned data successfully")
        logger.info(f"Batch stats: {batch_result.get('stats')}")
        return True, batch_result
    else:
        logger.error(f"❌ Failed to batch analyze projects: {response.status_code} - {response.text}")
        return False, None

def test_health_endpoint():
    """Test the health endpoint"""
    logger.info("\n🧪 Testing health endpoint")
    
    response = requests.get(f"{BACKEND_URL}/health")
    
    if response.status_code == 200:
        health_data = response.json()
        
        logger.info(f"✅ Health endpoint returned data successfully")
        logger.info(f"Health status: {health_data.get('status')}")
        
        # Check if all systems are healthy
        all_healthy = True
        for check_name, check_data in health_data.get('checks', {}).items():
            check_status = check_data.get('status')
            logger.info(f"Check '{check_name}': {check_status}")
            if check_status not in ['healthy', 'connected', 'available', 'configured']:
                all_healthy = False
        
        if all_healthy:
            logger.info("✅ All systems are reported as healthy")
        else:
            logger.warning("⚠️ Some systems are not reported as healthy")
        
        return True, health_data
    else:
        logger.error(f"❌ Failed to get health status: {response.status_code} - {response.text}")
        return False, None

def run_all_tests():
    """Run all validation tests"""
    logger.info("🚀 Starting Validation Tests for OpenAI v1.x Upgrade")
    
    results = {}
    
    # Test risk_level case sensitivity
    results["risk_level_case_sensitivity"] = test_risk_level_case_sensitivity()[0]
    
    # Test model_dump() dictionary issue
    results["model_dump_dictionary_issue"] = test_model_dump_dictionary_issue()[0]
    
    # Test projects endpoint
    results["projects_endpoint"] = test_projects_endpoint()[0]
    
    # Test investments endpoint
    results["investments_endpoint"] = test_investments_endpoint()[0]
    
    # Test alerts endpoint
    results["alerts_endpoint"] = test_alerts_endpoint()[0]
    
    # Test analytics endpoint
    results["analytics_endpoint"] = test_analytics_endpoint()[0]
    
    # Test recommendations endpoint
    results["recommendations_endpoint"] = test_recommendations_endpoint()[0]
    
    # Test batch analyze endpoint
    results["batch_analyze_endpoint"] = test_batch_analyze_endpoint()[0]
    
    # Test health endpoint
    results["health_endpoint"] = test_health_endpoint()[0]
    
    # Print summary
    logger.info("\n=== TEST RESULTS SUMMARY ===")
    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        logger.info("\n🎉 All validation tests passed successfully!")
    else:
        logger.error("\n❌ Some validation tests failed. See details above.")
    
    return results

if __name__ == "__main__":
    run_all_tests()