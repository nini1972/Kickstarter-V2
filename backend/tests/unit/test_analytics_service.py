"""
🧪 Analytics Service Tests
Testing the enterprise-grade analytics service with comprehensive algorithms
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List

from services.analytics_service import AnalyticsService
from models.projects import KickstarterProject
from models.investments import Investment


class TestAnalyticsService:
    """Test core analytics service functionality"""
    
    @pytest.fixture
    def mock_database(self):
        """Mock database for analytics testing"""
        mock_db = MagicMock()
        mock_db.get_collection = MagicMock()
        return mock_db
    
    @pytest.fixture
    def analytics_service(self, mock_database):
        """Create analytics service instance"""
        return AnalyticsService(mock_database)
    
    @pytest.fixture
    def sample_projects_data(self):
        """Sample projects data for analytics"""
        return [
            {
                "_id": "proj_1",
                "title": "AI Assistant App",
                "category": "Technology",
                "funding_goal": 50000,
                "current_funding": 35000,
                "deadline": datetime.utcnow() + timedelta(days=15),
                "risk_level": "medium",
                "created_at": datetime.utcnow() - timedelta(days=10),
                "user_id": "user_1"
            },
            {
                "_id": "proj_2", 
                "title": "Board Game Expansion",
                "category": "Games",
                "funding_goal": 25000,
                "current_funding": 30000,
                "deadline": datetime.utcnow() + timedelta(days=5),
                "risk_level": "low",
                "created_at": datetime.utcnow() - timedelta(days=20),
                "user_id": "user_1"
            },
            {
                "_id": "proj_3",
                "title": "Art Exhibition",
                "category": "Art",
                "funding_goal": 10000,
                "current_funding": 5000,
                "deadline": datetime.utcnow() - timedelta(days=5),
                "risk_level": "high",
                "created_at": datetime.utcnow() - timedelta(days=30),
                "user_id": "user_1"
            }
        ]
    
    @pytest.fixture
    def sample_investments_data(self):
        """Sample investments data for analytics"""
        return [
            {
                "_id": "inv_1",
                "project_id": "proj_1",
                "amount": 500,
                "investment_type": "pledge",
                "created_at": datetime.utcnow() - timedelta(days=5),
                "user_id": "user_1"
            },
            {
                "_id": "inv_2",
                "project_id": "proj_2", 
                "amount": 250,
                "investment_type": "equity",
                "created_at": datetime.utcnow() - timedelta(days=15),
                "user_id": "user_1"
            },
            {
                "_id": "inv_3",
                "project_id": "proj_3",
                "amount": 100,
                "investment_type": "pledge",
                "created_at": datetime.utcnow() - timedelta(days=25),
                "user_id": "user_1"
            }
        ]


class TestDashboardAnalytics:
    """Test dashboard analytics functionality"""
    
    @pytest.mark.asyncio
    async def test_get_dashboard_analytics_success(
        self, analytics_service, sample_projects_data, sample_investments_data
    ):
        """Test successful dashboard analytics retrieval"""
        # Mock database collections
        mock_projects_collection = MagicMock()
        mock_investments_collection = MagicMock()
        
        analytics_service.database.get_collection.side_effect = lambda name: {
            "projects": mock_projects_collection,
            "investments": mock_investments_collection
        }[name]
        
        # Mock aggregation pipeline results
        mock_projects_collection.aggregate.return_value.to_list = AsyncMock(return_value=[
            {"total_projects": 3, "active_projects": 2, "avg_funding_goal": 28333.33}
        ])
        
        mock_investments_collection.aggregate.return_value.to_list = AsyncMock(return_value=[
            {"total_investments": 3, "total_amount": 850, "avg_investment": 283.33}
        ])
        
        # Execute test
        result = await analytics_service.get_dashboard_analytics("user_1")
        
        # Verify results
        assert "overview" in result
        assert "performance_metrics" in result
        assert "portfolio_health" in result
        assert "recent_activity" in result
        
        overview = result["overview"]
        assert overview["total_projects"] == 3
        assert overview["active_projects"] == 2
        assert overview["total_investments"] == 3
        assert overview["total_invested"] == 850
    
    @pytest.mark.asyncio
    async def test_dashboard_analytics_empty_portfolio(self, analytics_service):
        """Test dashboard analytics with empty portfolio"""
        # Mock empty results
        mock_collection = MagicMock()
        mock_collection.aggregate.return_value.to_list = AsyncMock(return_value=[])
        
        analytics_service.database.get_collection.return_value = mock_collection
        
        result = await analytics_service.get_dashboard_analytics("user_1")
        
        # Verify fallback values
        assert result["overview"]["total_projects"] == 0
        assert result["overview"]["total_investments"] == 0
        assert result["portfolio_health"]["risk_score"] == 0
    
    @pytest.mark.asyncio
    async def test_dashboard_analytics_with_optimization(self, analytics_service):
        """Test dashboard analytics with optimization enabled"""
        # Mock optimized query
        with patch.object(analytics_service, '_get_optimized_dashboard_data') as mock_optimized:
            mock_optimized.return_value = {
                "overview": {"total_projects": 5},
                "performance_metrics": {},
                "portfolio_health": {},
                "recent_activity": []
            }
            
            result = await analytics_service.get_dashboard_analytics("user_1", use_optimization=True)
            
            mock_optimized.assert_called_once_with("user_1")
            assert result["overview"]["total_projects"] == 5


class TestROIPredictions:
    """Test ROI prediction algorithms"""
    
    @pytest.mark.asyncio
    async def test_get_roi_predictions_multiple_timeframes(self, analytics_service):
        """Test ROI predictions for multiple timeframes"""
        # Mock investment data
        mock_collection = MagicMock()
        mock_collection.aggregate.return_value.to_list = AsyncMock(return_value=[
            {
                "project_id": "proj_1",
                "amount": 500,
                "current_funding": 35000,
                "funding_goal": 50000,
                "risk_level": "medium",
                "category": "Technology"
            }
        ])
        
        analytics_service.database.get_collection.return_value = mock_collection
        
        result = await analytics_service.get_roi_predictions("user_1")
        
        # Verify prediction structure
        assert "predictions" in result
        assert "summary" in result
        assert "methodology" in result
        
        predictions = result["predictions"]
        assert "3_month" in predictions
        assert "6_month" in predictions
        assert "1_year" in predictions
        assert "2_year" in predictions
        
        # Verify prediction contains required fields
        for timeframe in ["3_month", "6_month", "1_year", "2_year"]:
            prediction = predictions[timeframe]
            assert "expected_return" in prediction
            assert "confidence_interval" in prediction
            assert "risk_adjusted_return" in prediction
    
    @pytest.mark.asyncio
    async def test_roi_predictions_risk_adjustment(self, analytics_service):
        """Test ROI predictions properly adjust for risk"""
        # Mock high-risk investment
        mock_collection = MagicMock()
        mock_collection.aggregate.return_value.to_list = AsyncMock(return_value=[
            {
                "project_id": "proj_1",
                "amount": 1000,
                "current_funding": 5000,
                "funding_goal": 10000,
                "risk_level": "high",
                "category": "Art"
            }
        ])
        
        analytics_service.database.get_collection.return_value = mock_collection
        
        result = await analytics_service.get_roi_predictions("user_1")
        
        # High-risk investments should have lower confidence and higher volatility
        predictions = result["predictions"]
        assert predictions["1_year"]["confidence_interval"]["lower"] < predictions["1_year"]["confidence_interval"]["upper"]
        assert result["summary"]["overall_risk_level"] == "high"
    
    @pytest.mark.asyncio
    async def test_roi_predictions_empty_portfolio(self, analytics_service):
        """Test ROI predictions with empty portfolio"""
        mock_collection = MagicMock()
        mock_collection.aggregate.return_value.to_list = AsyncMock(return_value=[])
        
        analytics_service.database.get_collection.return_value = mock_collection
        
        result = await analytics_service.get_roi_predictions("user_1")
        
        # Should return conservative fallback predictions
        assert result["summary"]["total_investments"] == 0
        assert result["predictions"]["1_year"]["expected_return"] == 0.0


class TestRiskAnalytics:
    """Test risk analytics and HHI concentration index"""
    
    @pytest.mark.asyncio
    async def test_get_risk_analytics_hhi_calculation(self, analytics_service):
        """Test risk analytics HHI (Herfindahl-Hirschman Index) calculation"""
        # Mock portfolio with concentration
        mock_collection = MagicMock()
        mock_collection.aggregate.return_value.to_list = AsyncMock(return_value=[
            {"category": "Technology", "total_amount": 800, "investment_count": 4},
            {"category": "Games", "total_amount": 150, "investment_count": 1},
            {"category": "Art", "total_amount": 50, "investment_count": 1}
        ])
        
        analytics_service.database.get_collection.return_value = mock_collection
        
        result = await analytics_service.get_risk_analytics("user_1")
        
        # Verify HHI calculation components
        assert "concentration_risk" in result
        assert "hhi_index" in result["concentration_risk"]
        assert "concentration_level" in result["concentration_risk"]
        assert "category_distribution" in result["concentration_risk"]
        
        # HHI should reflect high concentration in Technology
        hhi = result["concentration_risk"]["hhi_index"]
        assert hhi > 2500  # Highly concentrated threshold
        assert result["concentration_risk"]["concentration_level"] == "high"
    
    @pytest.mark.asyncio
    async def test_risk_analytics_diversification_score(self, analytics_service):
        """Test diversification scoring"""
        # Mock well-diversified portfolio
        mock_collection = MagicMock()
        mock_collection.aggregate.return_value.to_list = AsyncMock(return_value=[
            {"category": "Technology", "total_amount": 250, "investment_count": 2},
            {"category": "Games", "total_amount": 250, "investment_count": 2},
            {"category": "Art", "total_amount": 250, "investment_count": 2},
            {"category": "Music", "total_amount": 250, "investment_count": 2}
        ])
        
        analytics_service.database.get_collection.return_value = mock_collection
        
        result = await analytics_service.get_risk_analytics("user_1")
        
        # Well-diversified portfolio should have lower HHI
        hhi = result["concentration_risk"]["hhi_index"]
        assert hhi < 1500  # Well-diversified threshold
        assert result["concentration_risk"]["concentration_level"] == "low"
        
        # Should have high diversification score
        assert "diversification_score" in result
        diversification = result["diversification_score"]
        assert diversification["score"] > 75  # Good diversification
    
    @pytest.mark.asyncio
    async def test_risk_analytics_stress_testing(self, analytics_service):
        """Test portfolio stress testing scenarios"""
        mock_collection = MagicMock()
        mock_collection.aggregate.return_value.to_list = AsyncMock(return_value=[
            {"risk_level": "high", "total_amount": 500, "investment_count": 2},
            {"risk_level": "medium", "total_amount": 300, "investment_count": 3},
            {"risk_level": "low", "total_amount": 200, "investment_count": 5}
        ])
        
        analytics_service.database.get_collection.return_value = mock_collection
        
        result = await analytics_service.get_risk_analytics("user_1")
        
        # Verify stress testing scenarios
        assert "stress_testing" in result
        stress_tests = result["stress_testing"]
        
        assert "market_downturn" in stress_tests
        assert "category_collapse" in stress_tests
        assert "high_risk_failure" in stress_tests
        
        # Each scenario should have potential loss calculation
        for scenario in stress_tests.values():
            assert "potential_loss" in scenario
            assert "probability" in scenario
            assert "impact_description" in scenario


class TestMarketInsights:
    """Test market insights and trend analysis"""
    
    @pytest.mark.asyncio
    async def test_get_market_insights_trending_categories(self, analytics_service):
        """Test market insights trending categories analysis"""
        # Mock market data
        mock_collection = MagicMock()
        mock_collection.aggregate.return_value.to_list = AsyncMock(return_value=[
            {
                "category": "Technology",
                "total_projects": 150,
                "successful_projects": 120,
                "avg_funding_ratio": 1.25,
                "growth_rate": 0.15
            },
            {
                "category": "Games", 
                "total_projects": 80,
                "successful_projects": 60,
                "avg_funding_ratio": 1.10,
                "growth_rate": 0.08
            }
        ])
        
        analytics_service.database.get_collection.return_value = mock_collection
        
        result = await analytics_service.get_market_insights("user_1")
        
        # Verify trending categories analysis
        assert "trending_categories" in result
        trending = result["trending_categories"]
        
        # Should be sorted by some ranking criteria
        assert len(trending) >= 1
        for category in trending:
            assert "name" in category
            assert "success_rate" in category
            assert "avg_funding_ratio" in category
            assert "growth_rate" in category
            assert "recommendation_score" in category
    
    @pytest.mark.asyncio
    async def test_market_insights_success_factors(self, analytics_service):
        """Test market insights success factors analysis"""
        mock_collection = MagicMock()
        
        # Mock successful projects data
        mock_collection.aggregate.return_value.to_list = AsyncMock(return_value=[
            {"factor": "funding_goal_range", "value": "10000-50000", "success_rate": 0.85},
            {"factor": "campaign_duration", "value": "30-45_days", "success_rate": 0.78},
            {"factor": "description_length", "value": "400-800_chars", "success_rate": 0.72}
        ])
        
        analytics_service.database.get_collection.return_value = mock_collection
        
        result = await analytics_service.get_market_insights("user_1")
        
        # Verify success factors
        assert "success_factors" in result
        factors = result["success_factors"]
        
        assert "funding_goal_insights" in factors
        assert "timing_insights" in factors
        assert "content_insights" in factors
        
        # Each insight should have actionable recommendations
        for insight_category in factors.values():
            assert "recommendations" in insight_category
            assert len(insight_category["recommendations"]) > 0
    
    @pytest.mark.asyncio
    async def test_market_insights_with_optimization(self, analytics_service):
        """Test market insights with streaming optimization"""
        with patch.object(analytics_service, '_get_optimized_market_insights') as mock_optimized:
            mock_optimized.return_value = {
                "trending_categories": [],
                "success_factors": {},
                "emerging_trends": [],
                "recommendations": []
            }
            
            result = await analytics_service.get_market_insights("user_1", use_optimization=True)
            
            mock_optimized.assert_called_once_with("user_1")
            assert "trending_categories" in result


class TestFundingTrends:
    """Test funding trends and temporal analysis"""
    
    @pytest.mark.asyncio
    async def test_get_funding_trends_time_series(self, analytics_service):
        """Test funding trends time series analysis"""
        # Mock time series data
        base_date = datetime.utcnow() - timedelta(days=30)
        mock_data = []
        
        for i in range(30):
            mock_data.append({
                "date": base_date + timedelta(days=i),
                "total_funding": 1000 + (i * 50),  # Growing trend
                "project_count": 5 + (i // 5),
                "avg_funding": 200 + (i * 10)
            })
        
        mock_collection = MagicMock()
        mock_collection.aggregate.return_value.to_list = AsyncMock(return_value=mock_data)
        
        analytics_service.database.get_collection.return_value = mock_collection
        
        result = await analytics_service.get_funding_trends("user_1", days=30)
        
        # Verify time series structure
        assert len(result) == 30
        
        for trend_point in result:
            assert "date" in trend_point
            assert "total_funding" in trend_point
            assert "project_count" in trend_point
            assert "avg_funding" in trend_point
            assert "funding_velocity" in trend_point
    
    @pytest.mark.asyncio
    async def test_funding_trends_seasonal_analysis(self, analytics_service):
        """Test funding trends seasonal pattern detection"""
        # Mock seasonal data (simulating year-long trends)
        mock_data = []
        base_date = datetime.utcnow() - timedelta(days=365)
        
        for month in range(12):
            # Simulate seasonal patterns (higher in Q4, lower in Q1)
            seasonal_multiplier = 1.5 if month in [10, 11] else 0.8 if month in [0, 1] else 1.0
            
            mock_data.append({
                "month": month + 1,
                "total_funding": 10000 * seasonal_multiplier,
                "project_count": 50 * seasonal_multiplier,
                "success_rate": 0.6 + (0.2 * seasonal_multiplier - 0.2)
            })
        
        mock_collection = MagicMock()
        mock_collection.aggregate.return_value.to_list = AsyncMock(return_value=mock_data)
        
        analytics_service.database.get_collection.return_value = mock_collection
        
        # Test with longer period to trigger seasonal analysis
        result = await analytics_service.get_funding_trends("user_1", days=365)
        
        # Should detect seasonal patterns
        assert len(result) > 0
        
        # Verify trend includes seasonal indicators
        november_data = [point for point in result if point.get("month") == 11]
        january_data = [point for point in result if point.get("month") == 1]
        
        if november_data and january_data:
            # November should have higher funding than January (seasonal pattern)
            assert november_data[0]["total_funding"] > january_data[0]["total_funding"]


class TestAnalyticsPerformance:
    """Test analytics service performance and caching"""
    
    @pytest.mark.benchmark
    def test_dashboard_analytics_performance(self, analytics_service, benchmark):
        """Benchmark dashboard analytics performance"""
        # Mock fast database response
        mock_collection = MagicMock()
        mock_collection.aggregate.return_value.to_list = AsyncMock(return_value=[
            {"total_projects": 100, "total_investments": 50}
        ])
        
        analytics_service.database.get_collection.return_value = mock_collection
        
        async def run_analytics():
            return await analytics_service.get_dashboard_analytics("user_1")
        
        # Benchmark should complete within reasonable time
        result = benchmark(asyncio.run, run_analytics())
        assert "overview" in result
    
    @pytest.mark.asyncio
    async def test_analytics_caching_behavior(self, analytics_service):
        """Test analytics service caching behavior"""
        # Mock cache service
        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(return_value=None)  # Cache miss
        mock_cache.set = AsyncMock(return_value=True)
        
        analytics_service.cache_service = mock_cache
        
        # Mock database response
        mock_collection = MagicMock()
        mock_collection.aggregate.return_value.to_list = AsyncMock(return_value=[
            {"total_projects": 5}
        ])
        
        analytics_service.database.get_collection.return_value = mock_collection
        
        # First call should query database and cache result
        result1 = await analytics_service.get_dashboard_analytics("user_1")
        
        # Verify cache was checked and set
        mock_cache.get.assert_called()
        mock_cache.set.assert_called()
        
        # Second call with cache hit
        mock_cache.get.return_value = result1  # Cache hit
        result2 = await analytics_service.get_dashboard_analytics("user_1")
        
        # Results should be identical
        assert result1 == result2


class TestAnalyticsErrorHandling:
    """Test analytics service error handling and resilience"""
    
    @pytest.mark.asyncio
    async def test_dashboard_analytics_database_error(self, analytics_service):
        """Test dashboard analytics handles database errors gracefully"""
        # Mock database error
        mock_collection = MagicMock()
        mock_collection.aggregate.side_effect = Exception("Database connection error")
        
        analytics_service.database.get_collection.return_value = mock_collection
        
        # Should return fallback data instead of raising exception
        result = await analytics_service.get_dashboard_analytics("user_1")
        
        # Verify fallback structure
        assert "overview" in result
        assert result["overview"]["total_projects"] == 0
        assert "error" in result  # Should indicate error occurred
    
    @pytest.mark.asyncio
    async def test_roi_predictions_invalid_data(self, analytics_service):
        """Test ROI predictions handle invalid data gracefully"""
        # Mock invalid investment data
        mock_collection = MagicMock()
        mock_collection.aggregate.return_value.to_list = AsyncMock(return_value=[
            {
                "project_id": "proj_1",
                "amount": -100,  # Invalid negative amount
                "current_funding": None,  # Invalid null funding
                "funding_goal": 0,  # Invalid zero goal
                "risk_level": "invalid",  # Invalid risk level
                "category": ""  # Empty category
            }
        ])
        
        analytics_service.database.get_collection.return_value = mock_collection
        
        result = await analytics_service.get_roi_predictions("user_1")
        
        # Should handle invalid data and return conservative predictions
        assert "predictions" in result
        assert result["summary"]["data_quality_score"] < 50  # Should indicate poor data quality
    
    @pytest.mark.asyncio
    async def test_risk_analytics_hhi_division_by_zero(self, analytics_service):
        """Test risk analytics handle edge cases in HHI calculation"""
        # Mock edge case data (all zero amounts)
        mock_collection = MagicMock()
        mock_collection.aggregate.return_value.to_list = AsyncMock(return_value=[
            {"category": "Technology", "total_amount": 0, "investment_count": 1},
            {"category": "Games", "total_amount": 0, "investment_count": 1}
        ])
        
        analytics_service.database.get_collection.return_value = mock_collection
        
        result = await analytics_service.get_risk_analytics("user_1")
        
        # Should handle division by zero and return safe defaults
        assert "concentration_risk" in result
        assert result["concentration_risk"]["hhi_index"] == 0
        assert result["concentration_risk"]["concentration_level"] == "undefined"
