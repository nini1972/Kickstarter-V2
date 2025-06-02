#!/usr/bin/env python3
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
logger = logging.getLogger("backend_test")

# Backend API URL from environment
BACKEND_URL = "https://d912fcb5-ed95-465d-b2ca-71ab01b8d494.preview.emergentagent.com/api"

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
        
        # Check batch processing status
        batch_status = data.get("checks", {}).get("batch_processing", {}).get("status")
        batch_available = batch_status == "available"
        
        log_test_result("Health Check - Batch Processing", 
                       batch_available, 
                       f"Batch processing status: {batch_status}")
        
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
    
    # Prepare test investment data
    investment_data = test_investment.copy()
    investment_data["project_id"] = project_id
    
    # CREATE
    try:
        response = requests.post(f"{BACKEND_URL}/investments", json=investment_data)
        response.raise_for_status()
        
        data = response.json()
        created_investment_id = data.get("id")
        
        log_test_result("Investment Creation", 
                       bool(created_investment_id), 
                       f"Created investment with ID: {created_investment_id}")
    except Exception as e:
        log_test_result("Investment Creation", False, f"Error: {str(e)}")
        return False
    
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
        log_test_result("Get Project Investments", 
                       isinstance(project_investments, list) and len(project_investments) > 0, 
                       f"Retrieved {len(project_investments)} investments for project")
    except Exception as e:
        log_test_result("Investment Read Operations", False, f"Error: {str(e)}")
    
    return True

def test_redis_cache_with_recommendations():
    """Test Redis cache functionality for recommendations endpoint"""
    logger.info("\n🧪 Testing Redis Cache Functionality with Recommendations")
    
    try:
        # Get initial cache stats
        response = requests.get(f"{BACKEND_URL}/health")
        response.raise_for_status()
        initial_stats = response.json()
        initial_cache_hits = initial_stats.get("checks", {}).get("redis_cache", {}).get("hits", 0)
        initial_cache_misses = initial_stats.get("checks", {}).get("redis_cache", {}).get("misses", 0)
        
        logger.info(f"Initial cache stats - Hits: {initial_cache_hits}, Misses: {initial_cache_misses}")
        
        # First request should be a cache MISS
        logger.info("Making first request to recommendations (should be cache MISS)...")
        start_time_miss = time.time()
        response = requests.get(f"{BACKEND_URL}/recommendations")
        response.raise_for_status()
        miss_duration = time.time() - start_time_miss
        
        # Second request should be a cache HIT
        logger.info("Making second request to recommendations (should be cache HIT)...")
        start_time_hit = time.time()
        response = requests.get(f"{BACKEND_URL}/recommendations")
        response.raise_for_status()
        hit_duration = time.time() - start_time_hit
        
        # Get updated cache stats
        response = requests.get(f"{BACKEND_URL}/health")
        response.raise_for_status()
        updated_stats = response.json()
        updated_cache_hits = updated_stats.get("checks", {}).get("redis_cache", {}).get("hits", 0)
        updated_cache_misses = updated_stats.get("checks", {}).get("redis_cache", {}).get("misses", 0)
        
        # Calculate differences
        new_hits = updated_cache_hits - initial_cache_hits
        new_misses = updated_cache_misses - initial_cache_misses
        
        logger.info(f"Updated cache stats - Hits: {updated_cache_hits}, Misses: {updated_cache_misses}")
        logger.info(f"New hits: {new_hits}, New misses: {new_misses}")
        
        # Performance comparison
        logger.info(f"Cache MISS request time: {miss_duration:.4f}s")
        logger.info(f"Cache HIT request time: {hit_duration:.4f}s")
        performance_improvement = ((miss_duration - hit_duration) / miss_duration) * 100 if miss_duration > 0 else 0
        logger.info(f"Performance improvement: {performance_improvement:.2f}%")
        
        # Test if cache hit is faster than cache miss (should be)
        cache_performance_ok = hit_duration < miss_duration
        log_test_result("Cache Performance", 
                       cache_performance_ok, 
                       f"Cache HIT is {performance_improvement:.2f}% faster than MISS")
        
        # Update test_results with cache stats
        test_results["cache_stats"]["hits"] = new_hits
        test_results["cache_stats"]["misses"] = new_misses
        
        return True
        
    except Exception as e:
        log_test_result("Redis Cache Testing", False, f"Error: {str(e)}")
        return False

def test_redis_health_check():
    """Test Redis health check endpoint"""
    logger.info("\n🧪 Testing Redis Health Check")
    
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        response.raise_for_status()
        
        data = response.json()
        
        # Check Redis cache status
        redis_status = data.get("checks", {}).get("redis_cache", {}).get("status")
        redis_connected = redis_status == "connected"
        
        log_test_result("Redis Connection Status", 
                       redis_connected, 
                       f"Redis status: {redis_status}")
        
        # Check cache statistics
        cache_stats = data.get("checks", {}).get("redis_cache", {})
        
        expected_stats = ["total_keys", "memory_used", "hits", "misses"]
        stats_present = all(stat in cache_stats for stat in expected_stats)
        
        log_test_result("Redis Cache Statistics", 
                       stats_present, 
                       f"Cache stats: Keys: {cache_stats.get('total_keys')}, Memory: {cache_stats.get('memory_used')}, Hits: {cache_stats.get('hits')}, Misses: {cache_stats.get('misses')}")
        
        return redis_connected
        
    except Exception as e:
        log_test_result("Redis Health Check", False, f"Error: {str(e)}")
        return False

def test_batch_processing_endpoint():
    """Test the batch processing endpoint with different batch sizes"""
    logger.info("\n🧪 Testing Batch AI Processing Endpoint")
    
    # Create test projects for batch processing
    project_ids = []
    
    try:
        # Create 5 test projects for batch processing
        logger.info("Creating test projects for batch processing...")
        for i in range(5):
            project_data = generate_test_project(i)
            response = requests.post(f"{BACKEND_URL}/projects", json=project_data)
            if response.status_code == 200:
                project_id = response.json().get("id")
                project_ids.append(project_id)
                logger.info(f"Created test project {i+1} with ID: {project_id}")
            else:
                logger.warning(f"Failed to create test project {i+1}: {response.text}")
        
        if not project_ids:
            logger.error("❌ Failed to create any test projects for batch processing")
            log_test_result("Batch Processing - Project Creation", False, "Failed to create test projects")
            return False
        
        log_test_result("Batch Processing - Project Creation", 
                       len(project_ids) > 0, 
                       f"Created {len(project_ids)} test projects for batch processing")
        
        # Test batch processing with different batch sizes
        batch_sizes = [1, 3, 5]
        
        for batch_size in batch_sizes:
            test_results["batch_processing"]["total_batches"] += 1
            
            # Select subset of projects based on batch size
            test_batch = project_ids[:min(batch_size, len(project_ids))]
            
            logger.info(f"Testing batch processing with batch size {batch_size}...")
            start_time = time.time()
            
            response = requests.post(
                f"{BACKEND_URL}/projects/batch-analyze", 
                json={
                    "project_ids": test_batch,
                    "batch_size": batch_size
                }
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if batch processing was successful
                success = data.get("success", False)
                stats = data.get("stats", {})
                results = data.get("results", [])
                
                # Log performance metrics
                test_results["batch_processing"]["performance_metrics"].append({
                    "batch_size": batch_size,
                    "processing_time": processing_time,
                    "projects_count": len(test_batch),
                    "time_per_project": processing_time / len(test_batch) if test_batch else 0
                })
                
                if success:
                    test_results["batch_processing"]["successful_batches"] += 1
                    
                    log_test_result(f"Batch Processing - Size {batch_size}", 
                                   True, 
                                   f"Processed {len(test_batch)} projects in {processing_time:.2f}s " +
                                   f"({stats.get('successful_analyses', 0)} successful, " +
                                   f"{stats.get('failed_analyses', 0)} failed)")
                    
                    # Verify that all projects have batch processing metadata
                    batch_metadata_present = all("batch_processed" in result for result in results)
                    batch_timestamp_present = all("batch_timestamp" in result for result in results)
                    
                    log_test_result(f"Batch Processing - Metadata for Size {batch_size}", 
                                   batch_metadata_present and batch_timestamp_present, 
                                   f"Batch metadata present in all {len(results)} results")
                    
                else:
                    test_results["batch_processing"]["failed_batches"] += 1
                    log_test_result(f"Batch Processing - Size {batch_size}", 
                                   False, 
                                   f"Batch processing failed: {data.get('message', 'Unknown error')}")
            else:
                test_results["batch_processing"]["failed_batches"] += 1
                log_test_result(f"Batch Processing - Size {batch_size}", 
                               False, 
                               f"API error: {response.status_code} - {response.text}")
        
        # Test batch status endpoint
        logger.info("Testing batch status endpoint...")
        
        # Use a random UUID as batch_id since we don't have real batch IDs
        test_batch_id = str(uuid.uuid4())
        
        response = requests.get(f"{BACKEND_URL}/projects/batch-status/{test_batch_id}")
        
        if response.status_code == 200:
            data = response.json()
            
            log_test_result("Batch Status Endpoint", 
                           "status" in data, 
                           f"Batch status endpoint returned: {data.get('status', 'unknown')}")
        else:
            log_test_result("Batch Status Endpoint", 
                           False, 
                           f"API error: {response.status_code} - {response.text}")
        
        # Clean up test projects
        logger.info("Cleaning up test projects...")
        for project_id in project_ids:
            try:
                requests.delete(f"{BACKEND_URL}/projects/{project_id}")
                logger.info(f"Deleted test project with ID: {project_id}")
            except Exception as e:
                logger.warning(f"Failed to delete test project {project_id}: {e}")
        
        return True
        
    except Exception as e:
        log_test_result("Batch Processing", False, f"Error: {str(e)}")
        
        # Try to clean up any created projects
        for project_id in project_ids:
            try:
                requests.delete(f"{BACKEND_URL}/projects/{project_id}")
            except:
                pass
                
        return False

def test_batch_vs_individual_performance():
    """Compare performance between batch processing and individual processing"""
    logger.info("\n🧪 Testing Batch vs Individual Processing Performance")
    
    project_ids = []
    
    try:
        # Create 5 test projects
        logger.info("Creating test projects for performance comparison...")
        for i in range(5):
            project_data = generate_test_project(i)
            response = requests.post(f"{BACKEND_URL}/projects", json=project_data)
            if response.status_code == 200:
                project_id = response.json().get("id")
                project_ids.append(project_id)
                logger.info(f"Created test project {i+1} with ID: {project_id}")
            else:
                logger.warning(f"Failed to create test project {i+1}: {response.text}")
        
        if len(project_ids) < 3:
            logger.error("❌ Failed to create enough test projects for performance comparison")
            log_test_result("Performance Comparison - Project Creation", False, "Failed to create enough test projects")
            return False
        
        log_test_result("Performance Comparison - Project Creation", 
                       len(project_ids) >= 3, 
                       f"Created {len(project_ids)} test projects for performance comparison")
        
        # Measure individual processing time
        logger.info("Testing individual processing performance...")
        individual_start_time = time.time()
        
        individual_results = []
        for project_id in project_ids:
            # Get project
            project_response = requests.get(f"{BACKEND_URL}/projects/{project_id}")
            if project_response.status_code == 200:
                project = project_response.json()
                
                # Update project to trigger AI analysis
                update_data = {
                    "name": project["name"],
                    "creator": project["creator"],
                    "url": project["url"],
                    "description": project["description"],
                    "category": project["category"],
                    "goal_amount": project["goal_amount"],
                    "pledged_amount": project["pledged_amount"] + 100,  # Change to trigger update
                    "backers_count": project["backers_count"],
                    "deadline": project["deadline"],
                    "launched_date": project["launched_date"],
                    "status": project["status"]
                }
                
                update_response = requests.put(f"{BACKEND_URL}/projects/{project_id}", json=update_data)
                if update_response.status_code == 200:
                    individual_results.append(update_response.json())
        
        individual_time = time.time() - individual_start_time
        
        # Measure batch processing time
        logger.info("Testing batch processing performance...")
        batch_start_time = time.time()
        
        batch_response = requests.post(
            f"{BACKEND_URL}/projects/batch-analyze", 
            json={
                "project_ids": project_ids,
                "batch_size": len(project_ids)
            }
        )
        
        batch_time = time.time() - batch_start_time
        
        # Calculate performance difference
        if individual_time > 0 and batch_time > 0:
            performance_improvement = ((individual_time - batch_time) / individual_time) * 100
            
            log_test_result("Performance Comparison", 
                           batch_time < individual_time, 
                           f"Individual processing: {individual_time:.2f}s, Batch processing: {batch_time:.2f}s, " +
                           f"Improvement: {performance_improvement:.2f}%")
            
            # Check if batch processing is at least 20% faster
            significant_improvement = performance_improvement >= 20
            
            log_test_result("Significant Performance Improvement", 
                           significant_improvement, 
                           f"Batch processing is {performance_improvement:.2f}% faster than individual processing")
        else:
            log_test_result("Performance Comparison", 
                           False, 
                           "Failed to measure performance accurately")
        
        # Clean up test projects
        logger.info("Cleaning up test projects...")
        for project_id in project_ids:
            try:
                requests.delete(f"{BACKEND_URL}/projects/{project_id}")
                logger.info(f"Deleted test project with ID: {project_id}")
            except Exception as e:
                logger.warning(f"Failed to delete test project {project_id}: {e}")
        
        return True
        
    except Exception as e:
        log_test_result("Performance Comparison", False, f"Error: {str(e)}")
        
        # Try to clean up any created projects
        for project_id in project_ids:
            try:
                requests.delete(f"{BACKEND_URL}/projects/{project_id}")
            except:
                pass
                
        return False

def test_batch_processing_error_handling():
    """Test error handling in batch processing"""
    logger.info("\n🧪 Testing Batch Processing Error Handling")
    
    try:
        # Test with invalid project IDs
        invalid_ids = [str(uuid.uuid4()) for _ in range(3)]
        
        logger.info("Testing batch processing with invalid project IDs...")
        response = requests.post(
            f"{BACKEND_URL}/projects/batch-analyze", 
            json={
                "project_ids": invalid_ids,
                "batch_size": 3
            }
        )
        
        # Check if the API handles invalid IDs gracefully
        if response.status_code == 404:
            log_test_result("Batch Processing - Invalid IDs", 
                           True, 
                           "API correctly returned 404 for invalid project IDs")
        else:
            data = response.json()
            error_handled = "No valid projects found" in data.get("detail", "") or "No valid projects" in data.get("message", "")
            
            log_test_result("Batch Processing - Invalid IDs", 
                           error_handled, 
                           f"API response: {response.status_code} - {response.text}")
        
        # Test with mixed valid and invalid data
        # First create one valid project
        valid_project_id = None
        project_data = generate_test_project(0)
        
        create_response = requests.post(f"{BACKEND_URL}/projects", json=project_data)
        if create_response.status_code == 200:
            valid_project_id = create_response.json().get("id")
            logger.info(f"Created valid test project with ID: {valid_project_id}")
            
            # Test with mixed valid and invalid IDs
            mixed_ids = [valid_project_id, str(uuid.uuid4()), str(uuid.uuid4())]
            
            logger.info("Testing batch processing with mixed valid and invalid project IDs...")
            response = requests.post(
                f"{BACKEND_URL}/projects/batch-analyze", 
                json={
                    "project_ids": mixed_ids,
                    "batch_size": 3
                }
            )
            
            # Check if the API processes the valid ID and ignores invalid ones
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                log_test_result("Batch Processing - Mixed IDs", 
                               len(results) > 0, 
                               f"API processed {len(results)} valid projects out of {len(mixed_ids)} total IDs")
            else:
                log_test_result("Batch Processing - Mixed IDs", 
                               False, 
                               f"API error: {response.status_code} - {response.text}")
            
            # Clean up the valid project
            try:
                requests.delete(f"{BACKEND_URL}/projects/{valid_project_id}")
                logger.info(f"Deleted test project with ID: {valid_project_id}")
            except Exception as e:
                logger.warning(f"Failed to delete test project {valid_project_id}: {e}")
        else:
            log_test_result("Batch Processing - Error Handling", 
                           False, 
                           "Failed to create valid test project for error handling tests")
        
        return True
        
    except Exception as e:
        log_test_result("Batch Processing Error Handling", False, f"Error: {str(e)}")
        return False

def test_batch_processing_cache_integration():
    """Test integration between batch processing and cache"""
    logger.info("\n🧪 Testing Batch Processing Cache Integration")
    
    project_ids = []
    
    try:
        # Create 3 test projects
        logger.info("Creating test projects for cache integration testing...")
        for i in range(3):
            project_data = generate_test_project(i)
            response = requests.post(f"{BACKEND_URL}/projects", json=project_data)
            if response.status_code == 200:
                project_id = response.json().get("id")
                project_ids.append(project_id)
                logger.info(f"Created test project {i+1} with ID: {project_id}")
            else:
                logger.warning(f"Failed to create test project {i+1}: {response.text}")
        
        if not project_ids:
            logger.error("❌ Failed to create test projects for cache integration testing")
            log_test_result("Cache Integration - Project Creation", False, "Failed to create test projects")
            return False
        
        # Get initial cache stats
        response = requests.get(f"{BACKEND_URL}/health")
        initial_stats = response.json()
        initial_cache_keys = initial_stats.get("checks", {}).get("redis_cache", {}).get("total_keys", 0)
        
        logger.info(f"Initial cache keys: {initial_cache_keys}")
        
        # Run batch processing first time (should create cache entries)
        logger.info("Running first batch processing (should create cache entries)...")
        first_response = requests.post(
            f"{BACKEND_URL}/projects/batch-analyze", 
            json={
                "project_ids": project_ids,
                "batch_size": len(project_ids)
            }
        )
        
        if first_response.status_code != 200:
            log_test_result("Cache Integration - First Batch", False, f"API error: {first_response.status_code} - {first_response.text}")
            return False
        
        # Get cache stats after first batch
        response = requests.get(f"{BACKEND_URL}/health")
        mid_stats = response.json()
        mid_cache_keys = mid_stats.get("checks", {}).get("redis_cache", {}).get("total_keys", 0)
        
        logger.info(f"Cache keys after first batch: {mid_cache_keys}")
        
        # Check if cache keys increased
        cache_keys_increased = mid_cache_keys > initial_cache_keys
        
        log_test_result("Cache Integration - Cache Creation", 
                       cache_keys_increased, 
                       f"Cache keys before: {initial_cache_keys}, after: {mid_cache_keys}")
        
        # Run batch processing second time (should use cache)
        logger.info("Running second batch processing (should use cache)...")
        start_time = time.time()
        second_response = requests.post(
            f"{BACKEND_URL}/projects/batch-analyze", 
            json={
                "project_ids": project_ids,
                "batch_size": len(project_ids)
            }
        )
        second_time = time.time() - start_time
        
        if second_response.status_code != 200:
            log_test_result("Cache Integration - Second Batch", False, f"API error: {second_response.status_code} - {second_response.text}")
            return False
        
        # Get cache stats after second batch
        response = requests.get(f"{BACKEND_URL}/health")
        final_stats = response.json()
        final_cache_hits = final_stats.get("checks", {}).get("redis_cache", {}).get("hits", 0)
        
        # Check if second batch was faster (indicating cache usage)
        first_time = first_response.json().get("stats", {}).get("processing_time", 0)
        
        if first_time > 0 and second_time > 0:
            cache_performance = ((first_time - second_time) / first_time) * 100
            
            log_test_result("Cache Integration - Performance", 
                           second_time < first_time, 
                           f"First batch: {first_time:.2f}s, Second batch: {second_time:.2f}s, " +
                           f"Improvement: {cache_performance:.2f}%")
        
        # Test cache invalidation after project update
        if project_ids:
            # Update one project
            project_id = project_ids[0]
            logger.info(f"Testing cache invalidation by updating project {project_id}...")
            
            # Get current project data
            project_response = requests.get(f"{BACKEND_URL}/projects/{project_id}")
            if project_response.status_code == 200:
                project = project_response.json()
                
                # Update project
                update_data = {
                    "name": project["name"],
                    "creator": project["creator"],
                    "url": project["url"],
                    "description": project["description"] + " Updated!",  # Change description
                    "category": project["category"],
                    "goal_amount": project["goal_amount"],
                    "pledged_amount": project["pledged_amount"] + 200,  # Change pledged amount
                    "backers_count": project["backers_count"] + 2,  # Change backers count
                    "deadline": project["deadline"],
                    "launched_date": project["launched_date"],
                    "status": project["status"]
                }
                
                update_response = requests.put(f"{BACKEND_URL}/projects/{project_id}", json=update_data)
                
                if update_response.status_code == 200:
                    logger.info(f"Updated project {project_id}")
                    
                    # Run batch processing again after update
                    logger.info("Running batch processing after update (should invalidate cache)...")
                    third_response = requests.post(
                        f"{BACKEND_URL}/projects/batch-analyze", 
                        json={
                            "project_ids": [project_id],
                            "batch_size": 1
                        }
                    )
                    
                    if third_response.status_code == 200:
                        # Check if analysis changed after update
                        third_results = third_response.json().get("results", [])
                        
                        if third_results:
                            log_test_result("Cache Integration - Invalidation", 
                                           True, 
                                           "Successfully processed updated project after cache invalidation")
                        else:
                            log_test_result("Cache Integration - Invalidation", 
                                           False, 
                                           "Failed to get results after cache invalidation")
                    else:
                        log_test_result("Cache Integration - Invalidation", 
                                       False, 
                                       f"API error: {third_response.status_code} - {third_response.text}")
                else:
                    log_test_result("Cache Integration - Project Update", 
                                   False, 
                                   f"Failed to update project: {update_response.status_code} - {update_response.text}")
            else:
                log_test_result("Cache Integration - Project Retrieval", 
                               False, 
                               f"Failed to retrieve project: {project_response.status_code} - {project_response.text}")
        
        # Clean up test projects
        logger.info("Cleaning up test projects...")
        for project_id in project_ids:
            try:
                requests.delete(f"{BACKEND_URL}/projects/{project_id}")
                logger.info(f"Deleted test project with ID: {project_id}")
            except Exception as e:
                logger.warning(f"Failed to delete test project {project_id}: {e}")
        
        return True
        
    except Exception as e:
        log_test_result("Cache Integration", False, f"Error: {str(e)}")
        
        # Try to clean up any created projects
        for project_id in project_ids:
            try:
                requests.delete(f"{BACKEND_URL}/projects/{project_id}")
            except:
                pass
                
        return False

def run_all_tests():
    """Run all backend API tests"""
    logger.info("🚀 Starting Kickstarter Investment Tracker Backend Tests")
    logger.info(f"🔗 Testing API at: {BACKEND_URL}")
    
    # Test health endpoint first
    health_ok = test_health_endpoint()
    
    if health_ok:
        # Test Redis health check
        redis_ok = test_redis_health_check()
        
        # Test batch processing functionality
        logger.info("\n🧪 Testing Batch AI Processing Functionality")
        test_batch_processing_endpoint()
        
        # Test batch vs individual performance
        test_batch_vs_individual_performance()
        
        # Test batch processing error handling
        test_batch_processing_error_handling()
        
        # Test batch processing cache integration
        test_batch_processing_cache_integration()
    else:
        logger.error("❌ Health check failed. Skipping remaining tests.")
        test_results["skipped_tests"] += 5
    
    # Print test summary
    logger.info("\n📊 TEST SUMMARY")
    logger.info(f"Total Tests: {test_results['total_tests']}")
    logger.info(f"Passed: {test_results['passed_tests']}")
    logger.info(f"Failed: {test_results['failed_tests']}")
    logger.info(f"Skipped: {test_results['skipped_tests']}")
    
    # Print batch processing statistics
    if test_results["batch_processing"]["total_batches"] > 0:
        logger.info("\n📊 BATCH PROCESSING STATISTICS")
        logger.info(f"Total Batches: {test_results['batch_processing']['total_batches']}")
        logger.info(f"Successful Batches: {test_results['batch_processing']['successful_batches']}")
        logger.info(f"Failed Batches: {test_results['batch_processing']['failed_batches']}")
        
        # Print performance metrics
        if test_results["batch_processing"]["performance_metrics"]:
            logger.info("\n📊 BATCH PERFORMANCE METRICS")
            for metric in test_results["batch_processing"]["performance_metrics"]:
                logger.info(f"Batch Size {metric['batch_size']}: {metric['processing_time']:.2f}s total, " +
                           f"{metric['time_per_project']:.4f}s per project")
    
    success_rate = (test_results['passed_tests'] / test_results['total_tests']) * 100 if test_results['total_tests'] > 0 else 0
    logger.info(f"Success Rate: {success_rate:.2f}%")
    
    if test_results['failed_tests'] == 0:
        logger.info("✅ All tests passed successfully!")
    else:
        logger.error(f"❌ {test_results['failed_tests']} tests failed.")

def test_rate_limiting_and_enhanced_alerts():
    """Test rate limiting and enhanced smart alerts system"""
    logger.info("\n🧪 Testing Rate Limiting and Enhanced Smart Alerts")
    
    # Test rate limiting on health endpoint (30/minute)
    try:
        logger.info("Testing health endpoint rate limiting (30/minute)...")
        
        # Make 35 requests to exceed the rate limit
        successful_requests = 0
        rate_limited_requests = 0
        
        for i in range(35):
            response = requests.get(f"{BACKEND_URL}/health")
            
            if response.status_code == 200:
                successful_requests += 1
            elif response.status_code == 429:  # Too Many Requests
                rate_limited_requests += 1
                logger.info(f"Request {i+1}: Rate limited (429 Too Many Requests)")
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.1)
        
        # Check if rate limiting is working
        rate_limiting_working = rate_limited_requests > 0
        
        log_test_result("Health Endpoint Rate Limiting (30/minute)", 
                       rate_limiting_working, 
                       f"Successful requests: {successful_requests}, Rate limited requests: {rate_limited_requests}")
    except Exception as e:
        log_test_result("Health Endpoint Rate Limiting", False, f"Error: {str(e)}")
    
    # Test rate limiting on projects endpoint (20/minute)
    try:
        logger.info("Testing projects endpoint rate limiting (20/minute)...")
        
        # Make 25 requests to exceed the rate limit
        successful_requests = 0
        rate_limited_requests = 0
        
        for i in range(25):
            response = requests.get(f"{BACKEND_URL}/projects")
            
            if response.status_code == 200:
                successful_requests += 1
            elif response.status_code == 429:  # Too Many Requests
                rate_limited_requests += 1
                logger.info(f"Request {i+1}: Rate limited (429 Too Many Requests)")
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.1)
        
        # Check if rate limiting is working
        rate_limiting_working = rate_limited_requests > 0
        
        log_test_result("Projects Endpoint Rate Limiting (20/minute)", 
                       rate_limiting_working, 
                       f"Successful requests: {successful_requests}, Rate limited requests: {rate_limited_requests}")
    except Exception as e:
        log_test_result("Projects Endpoint Rate Limiting", False, f"Error: {str(e)}")
    
    # Test rate limiting on batch endpoint (10/hour)
    created_project_ids = []
    try:
        # Create test projects for batch processing
        logger.info("Creating test projects for batch processing rate limit testing...")
        for i in range(3):
            project_data = generate_test_project(i)
            response = requests.post(f"{BACKEND_URL}/projects", json=project_data)
            if response.status_code == 200:
                project_id = response.json().get("id")
                created_project_ids.append(project_id)
                logger.info(f"Created test project {i+1} with ID: {project_id}")
        
        # Make 12 requests to exceed the rate limit (10/hour)
        successful_requests = 0
        rate_limited_requests = 0
        
        for i in range(12):
            response = requests.post(
                f"{BACKEND_URL}/projects/batch-analyze", 
                json={
                    "project_ids": created_project_ids,
                    "batch_size": len(created_project_ids)
                }
            )
            
            if response.status_code == 200:
                successful_requests += 1
            elif response.status_code == 429:  # Too Many Requests
                rate_limited_requests += 1
                logger.info(f"Request {i+1}: Rate limited (429 Too Many Requests)")
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.2)
        
        # Check if rate limiting is working
        rate_limiting_working = rate_limited_requests > 0
        
        log_test_result("Batch Processing Rate Limiting (10/hour)", 
                       rate_limiting_working, 
                       f"Successful requests: {successful_requests}, Rate limited requests: {rate_limited_requests}")
    except Exception as e:
        log_test_result("Batch Processing Rate Limiting", False, f"Error: {str(e)}")
    finally:
        # Clean up test projects
        for project_id in created_project_ids:
            try:
                requests.delete(f"{BACKEND_URL}/projects/{project_id}")
            except:
                pass
    
    # Test rate limiting on alerts endpoint (50/minute)
    try:
        logger.info("Testing alerts endpoint rate limiting (50/minute)...")
        
        # Make 55 requests to exceed the rate limit
        successful_requests = 0
        rate_limited_requests = 0
        
        for i in range(55):
            response = requests.get(f"{BACKEND_URL}/alerts")
            
            if response.status_code == 200:
                successful_requests += 1
            elif response.status_code == 429:  # Too Many Requests
                rate_limited_requests += 1
                logger.info(f"Request {i+1}: Rate limited (429 Too Many Requests)")
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.05)
        
        # Check if rate limiting is working
        rate_limiting_working = rate_limited_requests > 0
        
        log_test_result("Alerts Endpoint Rate Limiting (50/minute)", 
                       rate_limiting_working, 
                       f"Successful requests: {successful_requests}, Rate limited requests: {rate_limited_requests}")
    except Exception as e:
        log_test_result("Alerts Endpoint Rate Limiting", False, f"Error: {str(e)}")
    
    # Test enhanced smart alerts
    created_project_ids = []
    try:
        # Create test projects with specific characteristics to trigger different alerts
        logger.info("Creating test projects for enhanced alerts testing...")
        
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
        
        # Wait a moment for the projects to be processed
        logger.info("Waiting for projects to be processed...")
        time.sleep(2)
        
        # Get alerts
        logger.info("Retrieving alerts...")
        response = requests.get(f"{BACKEND_URL}/alerts")
        
        if response.status_code == 200:
            alerts_data = response.json()
            alerts = alerts_data.get("alerts", [])
            
            # Check if alerts were generated
            alerts_generated = len(alerts) > 0
            
            log_test_result("Enhanced Alerts - Generation", 
                           alerts_generated, 
                           f"Generated {len(alerts)} alerts")
            
            if alerts_generated:
                # Check for priority levels in alerts
                priority_levels = set(alert.get("priority", "").upper() for alert in alerts)
                has_multiple_priorities = len(priority_levels) > 1
                
                log_test_result("Enhanced Alerts - Priority Levels", 
                               has_multiple_priorities, 
                               f"Priority levels found: {priority_levels}")
                
                # Check for action items in alerts
                has_action_items = any("action_items" in alert for alert in alerts)
                
                if has_action_items:
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
                    sample_confidence = next((alert.get("confidence_level", "") for alert in alerts if "confidence_level" in alert), "")
                    log_test_result("Enhanced Alerts - Confidence Levels", 
                                   True, 
                                   f"Confidence level found: {sample_confidence}")
                else:
                    log_test_result("Enhanced Alerts - Confidence Levels", 
                                   False, 
                                   "No confidence levels found in alerts")
        else:
            log_test_result("Enhanced Alerts - Retrieval", 
                           False, 
                           f"Failed to retrieve alerts: {response.status_code} - {response.text}")
    except Exception as e:
        log_test_result("Enhanced Smart Alerts", False, f"Error: {str(e)}")
    finally:
        # Clean up test projects
        for project_id in created_project_ids:
            try:
                requests.delete(f"{BACKEND_URL}/projects/{project_id}")
            except:
                pass

def test_comprehensive_phase2a():
    """Run comprehensive tests for all Phase 2A components"""
    logger.info("\n🚀 Starting Comprehensive Phase 2A Testing")
    
    # Test database indexing
    test_health_endpoint()
    
    # Test Redis caching
    test_redis_cache_with_recommendations()
    test_redis_health_check()
    
    # Test batch AI processing
    test_batch_processing_endpoint()
    test_batch_vs_individual_performance()
    test_batch_processing_error_handling()
    test_batch_processing_cache_integration()
    
    # Test rate limiting and enhanced smart alerts
    test_rate_limiting_and_enhanced_alerts()
    
    # Test CRUD operations
    test_project_crud()
    
    # Print test summary
    logger.info("\n📊 PHASE 2A COMPREHENSIVE TEST SUMMARY")
    logger.info(f"Total Tests: {test_results['total_tests']}")
    logger.info(f"Passed: {test_results['passed_tests']}")
    logger.info(f"Failed: {test_results['failed_tests']}")
    logger.info(f"Skipped: {test_results['skipped_tests']}")
    
    success_rate = (test_results['passed_tests'] / test_results['total_tests']) * 100 if test_results['total_tests'] > 0 else 0
    logger.info(f"Success Rate: {success_rate:.2f}%")
    
    if test_results['failed_tests'] == 0:
        logger.info("✅ All Phase 2A tests passed successfully!")
    else:
        logger.error(f"❌ {test_results['failed_tests']} tests failed.")

if __name__ == "__main__":
    # Run comprehensive tests for all Phase 2A components
    test_comprehensive_phase2a()
