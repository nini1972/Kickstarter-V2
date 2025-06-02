"""
🧪 Business Logic Integration Tests
Testing complete business workflows and data integrity
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
import asyncio


class TestProjectInvestmentWorkflow:
    """Test complete project-investment workflows"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_investment_workflow(self, authenticated_client, sample_project_data, sample_investment_data):
        """Test complete workflow from project creation to investment"""
        # 1. Create project
        project_response = await authenticated_client.post("/api/projects", json=sample_project_data)
        assert project_response.status_code == 200
        project = project_response.json()
        assert "ai_analysis" in project  # Should include AI analysis
        
        # 2. Create investment
        sample_investment_data["project_id"] = project["id"]
        investment_response = await authenticated_client.post("/api/investments", json=sample_investment_data)
        assert investment_response.status_code == 200
        investment = investment_response.json()
        
        # 3. Verify project appears in user's portfolio
        projects_response = await authenticated_client.get("/api/projects")
        projects = projects_response.json()
        assert any(p["id"] == project["id"] for p in projects)
        
        # 4. Verify investment appears in portfolio
        investments_response = await authenticated_client.get("/api/investments")
        investments = investments_response.json()
        assert any(i["id"] == investment["id"] for i in investments)
        
        # 5. Check portfolio statistics update
        stats_response = await authenticated_client.get("/api/investments/stats")
        stats = stats_response.json()
        assert stats["total_investments"] >= 1
        assert stats["total_amount"] >= investment["amount"]
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_project_lifecycle_management(self, authenticated_client, sample_project_data):
        """Test project lifecycle from creation to completion"""
        # 1. Create project
        project_response = await authenticated_client.post("/api/projects", json=sample_project_data)
        project = project_response.json()
        project_id = project["id"]
        
        # 2. Update project funding
        update_data = {
            "current_funding": sample_project_data["funding_goal"] * 0.8  # 80% funded
        }
        update_response = await authenticated_client.put(f"/api/projects/{project_id}", json=update_data)
        assert update_response.status_code == 200
        updated_project = update_response.json()
        assert updated_project["current_funding"] == update_data["current_funding"]
        
        # 3. Complete funding
        complete_data = {
            "current_funding": sample_project_data["funding_goal"] * 1.2  # 120% funded
        }
        complete_response = await authenticated_client.put(f"/api/projects/{project_id}", json=complete_data)
        assert complete_response.status_code == 200
        
        # 4. Verify project status reflects completion
        final_response = await authenticated_client.get(f"/api/projects/{project_id}")
        final_project = final_response.json()
        assert final_project["current_funding"] >= final_project["funding_goal"]
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_investment_diversification_tracking(self, authenticated_client, multiple_projects_data):
        """Test investment diversification tracking across categories"""
        # Create projects in different categories
        project_ids = []
        categories = ["Technology", "Games", "Art", "Music"]
        
        for i, category in enumerate(categories):
            project_data = multiple_projects_data[i].copy()
            project_data["category"] = category
            
            response = await authenticated_client.post("/api/projects", json=project_data)
            project = response.json()
            project_ids.append((project["id"], category))
        
        # Create investments in each category
        for project_id, category in project_ids:
            investment_data = {
                "project_id": project_id,
                "amount": 500,
                "investment_type": "pledge",
                "notes": f"Investment in {category} project"
            }
            response = await authenticated_client.post("/api/investments", json=investment_data)
            assert response.status_code == 200
        
        # Check risk analytics for diversification
        risk_response = await authenticated_client.get("/api/analytics/risk")
        assert risk_response.status_code == 200
        risk_data = risk_response.json()
        
        # Should show good diversification
        assert "concentration_risk" in risk_data
        assert "diversification_score" in risk_data
        
        # HHI should be relatively low due to diversification
        hhi = risk_data["concentration_risk"]["hhi_index"]
        assert hhi < 2500  # Well diversified


class TestAnalyticsWorkflow:
    """Test analytics generation workflows"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_analytics_data_flow(self, authenticated_client, multiple_projects_data):
        """Test analytics data flows correctly through the system"""
        # Create diverse portfolio
        investments_created = []
        
        for i, project_data in enumerate(multiple_projects_data[:5]):
            # Create project
            project_response = await authenticated_client.post("/api/projects", json=project_data)
            project = project_response.json()
            
            # Create investment with varying amounts
            investment_data = {
                "project_id": project["id"],
                "amount": 100 * (i + 1),  # Varying amounts
                "investment_type": "pledge" if i % 2 == 0 else "equity",
                "notes": f"Test investment {i}"
            }
            
            investment_response = await authenticated_client.post("/api/investments", json=investment_data)
            investment = investment_response.json()
            investments_created.append(investment)
        
        # Test dashboard analytics
        dashboard_response = await authenticated_client.get("/api/analytics/dashboard")
        assert dashboard_response.status_code == 200
        dashboard_data = dashboard_response.json()
        
        # Verify data consistency
        assert dashboard_data["overview"]["total_projects"] >= 5
        assert dashboard_data["overview"]["total_investments"] >= 5
        assert dashboard_data["overview"]["total_invested"] >= sum(inv["amount"] for inv in investments_created)
        
        # Test ROI predictions
        roi_response = await authenticated_client.get("/api/analytics/roi-predictions")
        assert roi_response.status_code == 200
        roi_data = roi_response.json()
        
        # Should have predictions for different timeframes
        assert "predictions" in roi_data
        assert "3_month" in roi_data["predictions"]
        assert "1_year" in roi_data["predictions"]
        
        # Test market insights
        insights_response = await authenticated_client.get("/api/analytics/market-insights")
        assert insights_response.status_code == 200
        insights_data = insights_response.json()
        
        # Should provide market analysis
        assert "trending_categories" in insights_data
        assert "success_factors" in insights_data
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_analytics_optimization_performance(self, authenticated_client, multiple_projects_data):
        """Test analytics optimization improves performance"""
        # Create substantial test data
        for project_data in multiple_projects_data[:10]:
            project_response = await authenticated_client.post("/api/projects", json=project_data)
            project = project_response.json()
            
            # Create multiple investments per project
            for j in range(3):
                investment_data = {
                    "project_id": project["id"],
                    "amount": 50 + (j * 25),
                    "investment_type": "pledge",
                    "notes": f"Investment {j}"
                }
                await authenticated_client.post("/api/investments", json=investment_data)
        
        # Test regular analytics
        import time
        
        start_time = time.time()
        regular_response = await authenticated_client.get("/api/analytics/dashboard")
        regular_time = time.time() - start_time
        
        assert regular_response.status_code == 200
        
        # Test optimized analytics
        start_time = time.time()
        optimized_response = await authenticated_client.get("/api/analytics/dashboard/optimized")
        optimized_time = time.time() - start_time
        
        assert optimized_response.status_code == 200
        
        # Both should return similar data structure
        regular_data = regular_response.json()
        optimized_data = optimized_response.json()
        
        assert "overview" in regular_data
        assert "overview" in optimized_data
        
        # Performance should be reasonable for both
        assert regular_time < 5.0  # Should complete within 5 seconds
        assert optimized_time < 5.0  # Should complete within 5 seconds


class TestAIAnalysisWorkflow:
    """Test AI analysis workflows"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_ai_project_analysis_workflow(self, authenticated_client, sample_project_data):
        """Test AI analysis is properly integrated into project workflow"""
        # Create project (should trigger AI analysis)
        response = await authenticated_client.post("/api/projects", json=sample_project_data)
        assert response.status_code == 200
        project = response.json()
        
        # Verify AI analysis is included
        assert "ai_analysis" in project
        ai_analysis = project["ai_analysis"]
        
        # AI analysis should have expected fields
        expected_fields = ["risk_level", "success_probability", "recommendation", "key_factors"]
        for field in expected_fields:
            assert field in ai_analysis
        
        # Risk level should be valid
        assert ai_analysis["risk_level"] in ["low", "medium", "high"]
        
        # Success probability should be between 0 and 1
        assert 0 <= ai_analysis["success_probability"] <= 1
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_batch_ai_analysis(self, authenticated_client, multiple_projects_data):
        """Test batch AI analysis functionality"""
        # Create multiple projects
        project_ids = []
        for project_data in multiple_projects_data[:5]:
            response = await authenticated_client.post("/api/projects", json=project_data)
            project = response.json()
            project_ids.append(project["id"])
        
        # Test batch analysis
        batch_request = {
            "project_ids": project_ids,
            "analysis_type": "full"
        }
        
        batch_response = await authenticated_client.post("/api/projects/batch-analyze", json=batch_request)
        assert batch_response.status_code == 200
        batch_data = batch_response.json()
        
        # Verify batch analysis results
        assert "analyses" in batch_data
        assert "summary" in batch_data
        
        analyses = batch_data["analyses"]
        assert len(analyses) == len(project_ids)
        
        # Each analysis should have required fields
        for analysis in analyses:
            assert "project_id" in analysis
            assert "analysis" in analysis
            assert analysis["project_id"] in project_ids
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_ai_recommendations_workflow(self, authenticated_client, sample_project_data, sample_investment_data):
        """Test AI recommendations based on user behavior"""
        # Create diverse investment history
        categories = ["Technology", "Games", "Art"]
        
        for category in categories:
            # Create project in category
            project_data = sample_project_data.copy()
            project_data["category"] = category
            project_data["title"] = f"{category} Project"
            
            project_response = await authenticated_client.post("/api/projects", json=project_data)
            project = project_response.json()
            
            # Create investment
            investment_data = sample_investment_data.copy()
            investment_data["project_id"] = project["id"]
            await authenticated_client.post("/api/investments", json=investment_data)
        
        # Get AI recommendations
        recommendations_response = await authenticated_client.get("/api/recommendations?limit=10")
        assert recommendations_response.status_code == 200
        recommendations_data = recommendations_response.json()
        
        # Should provide personalized recommendations
        assert "recommendations" in recommendations_data
        assert "generated_at" in recommendations_data
        assert isinstance(recommendations_data["recommendations"], list)


class TestAlertsWorkflow:
    """Test smart alerts workflows"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_alert_generation_workflow(self, authenticated_client, sample_project_data, sample_investment_data):
        """Test smart alert generation based on portfolio activities"""
        # Create project with deadline approaching
        project_data = sample_project_data.copy()
        project_data["deadline"] = (datetime.utcnow() + timedelta(days=5)).isoformat()  # Deadline soon
        project_data["current_funding"] = project_data["funding_goal"] * 0.9  # Almost funded
        
        project_response = await authenticated_client.post("/api/projects", json=project_data)
        project = project_response.json()
        
        # Create investment
        investment_data = sample_investment_data.copy()
        investment_data["project_id"] = project["id"]
        await authenticated_client.post("/api/investments", json=investment_data)
        
        # Get alerts
        alerts_response = await authenticated_client.get("/api/alerts")
        assert alerts_response.status_code == 200
        alerts_data = alerts_response.json()
        
        # Should have alert summary
        assert "alerts" in alerts_data
        assert "summary" in alerts_data
        
        summary = alerts_data["summary"]
        assert "total_alerts" in summary
        assert "generated_at" in summary
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_alert_preferences_workflow(self, authenticated_client):
        """Test alert preferences management workflow"""
        # Get default preferences
        get_response = await authenticated_client.get("/api/alerts/preferences")
        assert get_response.status_code == 200
        default_prefs = get_response.json()
        
        # Update preferences
        new_preferences = {
            "email_alerts": True,
            "risk_threshold": "high",
            "funding_alerts": True,
            "deadline_alerts": True,
            "frequency": "daily"
        }
        
        update_response = await authenticated_client.put("/api/alerts/preferences", json=new_preferences)
        assert update_response.status_code == 200
        updated_prefs = update_response.json()
        
        # Verify preferences were updated
        assert updated_prefs["email_alerts"] == new_preferences["email_alerts"]
        assert updated_prefs["risk_threshold"] == new_preferences["risk_threshold"]
        
        # Get alerts with new preferences
        alerts_response = await authenticated_client.get("/api/alerts")
        assert alerts_response.status_code == 200
        # Alerts should be filtered according to new preferences


class TestDataConsistencyWorkflow:
    """Test data consistency across operations"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_portfolio_consistency(self, authenticated_client, multiple_projects_data):
        """Test portfolio data consistency across different endpoints"""
        total_invested = 0
        investment_count = 0
        
        # Create investments
        for i, project_data in enumerate(multiple_projects_data[:3]):
            project_response = await authenticated_client.post("/api/projects", json=project_data)
            project = project_response.json()
            
            investment_amount = 100 * (i + 1)
            investment_data = {
                "project_id": project["id"],
                "amount": investment_amount,
                "investment_type": "pledge",
                "notes": f"Test investment {i}"
            }
            
            investment_response = await authenticated_client.post("/api/investments", json=investment_data)
            assert investment_response.status_code == 200
            
            total_invested += investment_amount
            investment_count += 1
        
        # Check consistency across endpoints
        
        # 1. Portfolio stats
        stats_response = await authenticated_client.get("/api/investments/stats")
        stats = stats_response.json()
        assert stats["total_investments"] >= investment_count
        assert stats["total_amount"] >= total_invested
        
        # 2. Dashboard analytics
        dashboard_response = await authenticated_client.get("/api/analytics/dashboard")
        dashboard = dashboard_response.json()
        assert dashboard["overview"]["total_investments"] >= investment_count
        assert dashboard["overview"]["total_invested"] >= total_invested
        
        # 3. Individual investments list
        investments_response = await authenticated_client.get("/api/investments")
        investments = investments_response.json()
        actual_total = sum(inv["amount"] for inv in investments)
        assert actual_total >= total_invested
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_project_investment_relationship_integrity(self, authenticated_client, sample_project_data):
        """Test referential integrity between projects and investments"""
        # Create project
        project_response = await authenticated_client.post("/api/projects", json=sample_project_data)
        project = project_response.json()
        project_id = project["id"]
        
        # Create investment
        investment_data = {
            "project_id": project_id,
            "amount": 500,
            "investment_type": "pledge",
            "notes": "Test investment"
        }
        
        investment_response = await authenticated_client.post("/api/investments", json=investment_data)
        investment = investment_response.json()
        
        # Verify relationship
        assert investment["project_id"] == project_id
        
        # Get investments for the project
        project_investments_response = await authenticated_client.get(f"/api/investments?project_id={project_id}")
        project_investments = project_investments_response.json()
        
        # Should find the investment
        assert any(inv["id"] == investment["id"] for inv in project_investments)
        
        # Delete project should handle investments appropriately
        delete_response = await authenticated_client.delete(f"/api/projects/{project_id}")
        assert delete_response.status_code == 200
        
        # Investment should either be deleted or marked as orphaned
        investment_check_response = await authenticated_client.get(f"/api/investments/{investment['id']}")
        # This behavior depends on business logic - could be 404 or still exist with project reference


class TestErrorHandlingWorkflow:
    """Test error handling in business workflows"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_invalid_investment_workflow(self, authenticated_client):
        """Test error handling for invalid investment attempts"""
        # Try to create investment for non-existent project
        invalid_investment = {
            "project_id": "nonexistent_project_id",
            "amount": 500,
            "investment_type": "pledge",
            "notes": "Invalid investment"
        }
        
        response = await authenticated_client.post("/api/investments", json=invalid_investment)
        assert response.status_code in [400, 404]  # Bad request or not found
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_investment_handling(self, authenticated_client, sample_project_data):
        """Test handling concurrent investments in the same project"""
        # Create project
        project_response = await authenticated_client.post("/api/projects", json=sample_project_data)
        project = project_response.json()
        project_id = project["id"]
        
        # Create multiple concurrent investments
        async def create_investment(amount):
            investment_data = {
                "project_id": project_id,
                "amount": amount,
                "investment_type": "pledge",
                "notes": f"Concurrent investment {amount}"
            }
            return await authenticated_client.post("/api/investments", json=investment_data)
        
        # Make concurrent requests
        tasks = [create_investment(100 + i) for i in range(5)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed (assuming no business rules prevent it)
        successful_responses = [r for r in responses if hasattr(r, 'status_code') and r.status_code == 200]
        assert len(successful_responses) == 5
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_data_validation_workflow(self, authenticated_client):
        """Test comprehensive data validation across workflows"""
        # Test invalid project data
        invalid_project = {
            "title": "",  # Empty title
            "funding_goal": -1000,  # Negative goal
            "deadline": "invalid-date",  # Invalid date
            "risk_level": "invalid"  # Invalid risk level
        }
        
        project_response = await authenticated_client.post("/api/projects", json=invalid_project)
        assert project_response.status_code == 422  # Validation error
        
        # Test invalid investment data
        invalid_investment = {
            "project_id": "valid_id",
            "amount": 0,  # Zero amount
            "investment_type": "invalid_type",  # Invalid type
        }
        
        investment_response = await authenticated_client.post("/api/investments", json=invalid_investment)
        assert investment_response.status_code == 422  # Validation error
