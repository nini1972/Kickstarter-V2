"""
🧪 API Endpoints Integration Tests
Testing complete API functionality with authentication and business logic
"""

import pytest
from httpx import AsyncClient
import json
from datetime import datetime, timedelta


class TestAuthenticationEndpoints:
    """Test authentication endpoints"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_user_registration_success(self, unauthenticated_client, sample_user_data):
        """Test successful user registration"""
        response = await unauthenticated_client.post("/api/auth/register", json=sample_user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "user" in data
        assert "access_token" in data
        assert data["user"]["email"] == sample_user_data["email"]
        assert "password" not in data["user"]  # Password should not be returned
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_user_registration_duplicate_email(self, unauthenticated_client, sample_user_data):
        """Test registration with duplicate email"""
        # Register first user
        await unauthenticated_client.post("/api/auth/register", json=sample_user_data)
        
        # Try to register with same email
        response = await unauthenticated_client.post("/api/auth/register", json=sample_user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "email" in data["detail"].lower() or "already exists" in data["detail"].lower()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_user_login_success(self, unauthenticated_client, sample_user_data):
        """Test successful user login"""
        # Register user first
        await unauthenticated_client.post("/api/auth/register", json=sample_user_data)
        
        # Login with credentials
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        response = await unauthenticated_client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_user_login_invalid_credentials(self, unauthenticated_client, sample_user_data):
        """Test login with invalid credentials"""
        # Register user first
        await unauthenticated_client.post("/api/auth/register", json=sample_user_data)
        
        # Try login with wrong password
        login_data = {
            "email": sample_user_data["email"],
            "password": "wrong_password"
        }
        response = await unauthenticated_client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "invalid" in data["detail"].lower() or "incorrect" in data["detail"].lower()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_demo_login_success(self, unauthenticated_client):
        """Test demo login functionality"""
        response = await unauthenticated_client.post("/api/auth/demo-login")
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert "demo" in data["user"]["email"].lower()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_token_refresh(self, unauthenticated_client, sample_user_data):
        """Test token refresh functionality"""
        # Register and login
        await unauthenticated_client.post("/api/auth/register", json=sample_user_data)
        login_response = await unauthenticated_client.post("/api/auth/login", json={
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        })
        
        login_data = login_response.json()
        refresh_token = login_data["refresh_token"]
        
        # Refresh token
        response = await unauthenticated_client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data


class TestProjectEndpoints:
    """Test project management endpoints"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_project_success(self, authenticated_client, sample_project_data):
        """Test successful project creation"""
        response = await authenticated_client.post("/api/projects", json=sample_project_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == sample_project_data["title"]
        assert data["category"] == sample_project_data["category"]
        assert "id" in data
        assert "ai_analysis" in data  # Should include AI analysis
        assert "created_at" in data
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_project_invalid_data(self, authenticated_client):
        """Test project creation with invalid data"""
        invalid_data = {
            "title": "",  # Empty title
            "funding_goal": -1000,  # Negative goal
            "risk_level": "invalid"  # Invalid risk level
        }
        
        response = await authenticated_client.post("/api/projects", json=invalid_data)
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_projects_success(self, authenticated_client, multiple_projects_data):
        """Test listing projects"""
        # Create multiple projects
        created_projects = []
        for project_data in multiple_projects_data[:5]:  # Create 5 projects
            response = await authenticated_client.post("/api/projects", json=project_data)
            assert response.status_code == 200
            created_projects.append(response.json())
        
        # List projects
        response = await authenticated_client.get("/api/projects")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 5  # Should have at least the created projects
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_projects_with_filters(self, authenticated_client, multiple_projects_data):
        """Test listing projects with filters"""
        # Create projects with specific categories
        tech_projects = [p for p in multiple_projects_data if p["category"] == "Technology"][:3]
        for project_data in tech_projects:
            await authenticated_client.post("/api/projects", json=project_data)
        
        # Filter by category
        response = await authenticated_client.get("/api/projects?category=Technology")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All returned projects should be Technology category
        for project in data:
            assert project["category"] == "Technology"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_project_by_id(self, authenticated_client, sample_project_data):
        """Test getting project by ID"""
        # Create project
        create_response = await authenticated_client.post("/api/projects", json=sample_project_data)
        created_project = create_response.json()
        project_id = created_project["id"]
        
        # Get project by ID
        response = await authenticated_client.get(f"/api/projects/{project_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert data["title"] == sample_project_data["title"]
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_project_not_found(self, authenticated_client):
        """Test getting non-existent project"""
        response = await authenticated_client.get("/api/projects/nonexistent_id")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_update_project_success(self, authenticated_client, sample_project_data):
        """Test updating project"""
        # Create project
        create_response = await authenticated_client.post("/api/projects", json=sample_project_data)
        created_project = create_response.json()
        project_id = created_project["id"]
        
        # Update project
        update_data = {
            "title": "Updated Project Title",
            "current_funding": 15000
        }
        response = await authenticated_client.put(f"/api/projects/{project_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["current_funding"] == update_data["current_funding"]
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_delete_project_success(self, authenticated_client, sample_project_data):
        """Test deleting project"""
        # Create project
        create_response = await authenticated_client.post("/api/projects", json=sample_project_data)
        created_project = create_response.json()
        project_id = created_project["id"]
        
        # Delete project
        response = await authenticated_client.delete(f"/api/projects/{project_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data["message"].lower()
        
        # Verify project is deleted
        get_response = await authenticated_client.get(f"/api/projects/{project_id}")
        assert get_response.status_code == 404


class TestInvestmentEndpoints:
    """Test investment management endpoints"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_investment_success(self, authenticated_client, sample_project_data, sample_investment_data):
        """Test successful investment creation"""
        # Create project first
        project_response = await authenticated_client.post("/api/projects", json=sample_project_data)
        project = project_response.json()
        
        # Create investment
        sample_investment_data["project_id"] = project["id"]
        response = await authenticated_client.post("/api/investments", json=sample_investment_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project["id"]
        assert data["amount"] == sample_investment_data["amount"]
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_investment_invalid_project(self, authenticated_client, sample_investment_data):
        """Test creating investment for non-existent project"""
        sample_investment_data["project_id"] = "nonexistent_project_id"
        response = await authenticated_client.post("/api/investments", json=sample_investment_data)
        
        assert response.status_code in [400, 404]  # Bad request or not found
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_investments(self, authenticated_client, sample_project_data, sample_investment_data):
        """Test listing investments"""
        # Create project and investment
        project_response = await authenticated_client.post("/api/projects", json=sample_project_data)
        project = project_response.json()
        
        sample_investment_data["project_id"] = project["id"]
        investment_response = await authenticated_client.post("/api/investments", json=sample_investment_data)
        assert investment_response.status_code == 200
        
        # List investments
        response = await authenticated_client.get("/api/investments")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_investment_by_id(self, authenticated_client, sample_project_data, sample_investment_data):
        """Test getting investment by ID"""
        # Create project and investment
        project_response = await authenticated_client.post("/api/projects", json=sample_project_data)
        project = project_response.json()
        
        sample_investment_data["project_id"] = project["id"]
        investment_response = await authenticated_client.post("/api/investments", json=sample_investment_data)
        investment = investment_response.json()
        
        # Get investment by ID
        response = await authenticated_client.get(f"/api/investments/{investment['id']}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == investment["id"]
        assert data["amount"] == sample_investment_data["amount"]
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_portfolio_stats(self, authenticated_client, sample_project_data, sample_investment_data):
        """Test portfolio statistics endpoint"""
        # Create project and investment
        project_response = await authenticated_client.post("/api/projects", json=sample_project_data)
        project = project_response.json()
        
        sample_investment_data["project_id"] = project["id"]
        await authenticated_client.post("/api/investments", json=sample_investment_data)
        
        # Get portfolio stats
        response = await authenticated_client.get("/api/investments/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_investments" in data
        assert "total_amount" in data
        assert "average_investment" in data
        assert data["total_investments"] >= 1


class TestAnalyticsEndpoints:
    """Test analytics endpoints"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_dashboard_analytics(self, authenticated_client, sample_project_data, sample_investment_data):
        """Test dashboard analytics endpoint"""
        # Create some test data
        project_response = await authenticated_client.post("/api/projects", json=sample_project_data)
        project = project_response.json()
        
        sample_investment_data["project_id"] = project["id"]
        await authenticated_client.post("/api/investments", json=sample_investment_data)
        
        # Get dashboard analytics
        response = await authenticated_client.get("/api/analytics/dashboard")
        
        assert response.status_code == 200
        data = response.json()
        assert "overview" in data
        assert "performance_metrics" in data
        assert "portfolio_health" in data
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_funding_trends(self, authenticated_client):
        """Test funding trends endpoint"""
        response = await authenticated_client.get("/api/analytics/funding-trends?days=30")
        
        assert response.status_code == 200
        data = response.json()
        assert "trends" in data
        assert isinstance(data["trends"], list)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_roi_predictions(self, authenticated_client):
        """Test ROI predictions endpoint"""
        response = await authenticated_client.get("/api/analytics/roi-predictions")
        
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert "summary" in data
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_risk_analytics(self, authenticated_client):
        """Test risk analytics endpoint"""
        response = await authenticated_client.get("/api/analytics/risk")
        
        assert response.status_code == 200
        data = response.json()
        assert "concentration_risk" in data
        assert "diversification_score" in data
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_market_insights(self, authenticated_client):
        """Test market insights endpoint"""
        response = await authenticated_client.get("/api/analytics/market-insights")
        
        assert response.status_code == 200
        data = response.json()
        assert "trending_categories" in data
        assert "success_factors" in data


class TestBatchProcessingEndpoints:
    """Test batch processing endpoints"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_batch_analyze_projects(self, authenticated_client, multiple_projects_data):
        """Test batch project analysis"""
        # Create multiple projects
        project_ids = []
        for project_data in multiple_projects_data[:3]:
            response = await authenticated_client.post("/api/projects", json=project_data)
            project = response.json()
            project_ids.append(project["id"])
        
        # Batch analyze
        batch_request = {
            "project_ids": project_ids,
            "analysis_type": "full"
        }
        response = await authenticated_client.post("/api/projects/batch-analyze", json=batch_request)
        
        assert response.status_code == 200
        data = response.json()
        assert "analyses" in data
        assert "summary" in data
        assert len(data["analyses"]) == len(project_ids)


class TestAIEndpoints:
    """Test AI-powered endpoints"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_recommendations(self, authenticated_client, sample_project_data, sample_investment_data):
        """Test AI recommendations endpoint"""
        # Create some test data for recommendations
        project_response = await authenticated_client.post("/api/projects", json=sample_project_data)
        project = project_response.json()
        
        sample_investment_data["project_id"] = project["id"]
        await authenticated_client.post("/api/investments", json=sample_investment_data)
        
        # Get recommendations
        response = await authenticated_client.get("/api/recommendations?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert "generated_at" in data
        assert "count" in data
        assert isinstance(data["recommendations"], list)


class TestAlertsEndpoints:
    """Test smart alerts endpoints"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_alerts(self, authenticated_client):
        """Test getting smart alerts"""
        response = await authenticated_client.get("/api/alerts")
        
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        assert "summary" in data
        assert isinstance(data["alerts"], list)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_alert_preferences(self, authenticated_client):
        """Test alert preferences endpoints"""
        # Get current preferences
        get_response = await authenticated_client.get("/api/alerts/preferences")
        assert get_response.status_code == 200
        
        # Update preferences
        new_preferences = {
            "email_alerts": True,
            "risk_threshold": "medium",
            "funding_alerts": True
        }
        put_response = await authenticated_client.put("/api/alerts/preferences", json=new_preferences)
        assert put_response.status_code == 200
        
        # Verify update
        verify_response = await authenticated_client.get("/api/alerts/preferences")
        verify_data = verify_response.json()
        assert verify_data["email_alerts"] == new_preferences["email_alerts"]
        assert verify_data["risk_threshold"] == new_preferences["risk_threshold"]


class TestHealthAndMonitoringEndpoints:
    """Test health and monitoring endpoints"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_check(self, unauthenticated_client):
        """Test health check endpoint"""
        response = await unauthenticated_client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "services" in data
        
        # Should include database, cache, and circuit breaker status
        services = data["services"]
        assert "database" in services
        assert "cache" in services
        assert "circuit_breakers" in services
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_circuit_breaker_stats(self, authenticated_client):
        """Test circuit breaker statistics endpoint"""
        response = await authenticated_client.get("/api/circuit-breakers")
        
        assert response.status_code == 200
        data = response.json()
        # Should return circuit breaker statistics
        assert isinstance(data, dict)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_db_optimization_stats(self, authenticated_client):
        """Test database optimization statistics endpoint"""
        response = await authenticated_client.get("/api/db-optimization/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "optimization_stats" in data
        assert "service_status" in data


class TestSecurityEndpoints:
    """Test security features in endpoints"""
    
    @pytest.mark.integration
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_unauthorized_access(self, unauthenticated_client):
        """Test that protected endpoints require authentication"""
        protected_endpoints = [
            "/api/projects",
            "/api/investments", 
            "/api/analytics/dashboard",
            "/api/recommendations",
            "/api/alerts"
        ]
        
        for endpoint in protected_endpoints:
            response = await unauthenticated_client.get(endpoint)
            assert response.status_code == 401  # Unauthorized
    
    @pytest.mark.integration
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_xss_protection(self, authenticated_client):
        """Test XSS protection in input validation"""
        malicious_data = {
            "title": "<script>alert('XSS')</script>",
            "description": "<img src=x onerror=alert('XSS')>",
            "category": "Technology",
            "funding_goal": 10000,
            "deadline": datetime.utcnow().isoformat()
        }
        
        response = await authenticated_client.post("/api/projects", json=malicious_data)
        
        # Should either be blocked by middleware or sanitized
        if response.status_code == 200:
            data = response.json()
            # If accepted, should be sanitized
            assert "<script>" not in data["title"]
            assert "onerror" not in data["description"]
        else:
            # Should be blocked
            assert response.status_code == 400
    
    @pytest.mark.integration
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_nosql_injection_protection(self, authenticated_client):
        """Test NoSQL injection protection"""
        # This test depends on how the middleware handles query parameters
        response = await authenticated_client.get("/api/projects?search={\"$ne\": null}")
        
        # Should either handle safely or be blocked
        assert response.status_code in [200, 400]  # Either processed safely or blocked


class TestPerformanceEndpoints:
    """Test endpoint performance characteristics"""
    
    @pytest.mark.integration
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_endpoint_response_times(self, authenticated_client, performance_test_config):
        """Test that endpoints respond within acceptable time limits"""
        import time
        
        endpoints = [
            "/api/projects",
            "/api/investments",
            "/api/analytics/dashboard",
            "/api/health"
        ]
        
        max_response_time = performance_test_config["max_response_time"]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = await authenticated_client.get(endpoint)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Response should be successful and fast
            assert response.status_code == 200
            assert response_time < max_response_time, f"{endpoint} took {response_time:.2f}s (max: {max_response_time}s)"
    
    @pytest.mark.integration
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, authenticated_client, performance_test_config):
        """Test handling concurrent requests"""
        import asyncio
        
        num_requests = performance_test_config["concurrent_requests"]
        
        async def make_request():
            return await authenticated_client.get("/api/health")
        
        # Make concurrent requests
        tasks = [make_request() for _ in range(num_requests)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successful responses
        successful_responses = sum(
            1 for r in responses 
            if hasattr(r, 'status_code') and r.status_code == 200
        )
        
        success_rate = (successful_responses / num_requests) * 100
        target_success_rate = performance_test_config["target_success_rate"]
        
        assert success_rate >= target_success_rate, f"Success rate: {success_rate:.1f}% (target: {target_success_rate}%)"


class TestEndpointPagination:
    """Test pagination functionality"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_projects_pagination(self, authenticated_client, multiple_projects_data):
        """Test projects endpoint pagination"""
        # Create many projects
        for project_data in multiple_projects_data:
            await authenticated_client.post("/api/projects", json=project_data)
        
        # Test first page
        response1 = await authenticated_client.get("/api/projects?page=1&page_size=5")
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1) <= 5
        
        # Test second page
        response2 = await authenticated_client.get("/api/projects?page=2&page_size=5")
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Pages should be different (if enough data)
        if len(data1) == 5 and len(data2) > 0:
            project_ids_page1 = {p["id"] for p in data1}
            project_ids_page2 = {p["id"] for p in data2}
            assert project_ids_page1.isdisjoint(project_ids_page2)  # No overlap
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_investments_pagination(self, authenticated_client, sample_project_data, sample_investment_data):
        """Test investments endpoint pagination"""
        # Create project
        project_response = await authenticated_client.post("/api/projects", json=sample_project_data)
        project = project_response.json()
        
        # Create multiple investments
        for i in range(10):
            investment_data = sample_investment_data.copy()
            investment_data["project_id"] = project["id"]
            investment_data["amount"] = 100 + i  # Vary amount
            await authenticated_client.post("/api/investments", json=investment_data)
        
        # Test pagination
        response = await authenticated_client.get("/api/investments?page=1&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5
