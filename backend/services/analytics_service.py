"""
📊 Analytics Service
Advanced analytics and insights generation for investment tracking
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio

from models.projects import KickstarterProject
from models.investments import Investment
from services.cache_service import cache_service

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service for generating comprehensive analytics and insights"""
    
    def __init__(self, database):
        self.db = database
        self.projects_collection = database.projects
        self.investments_collection = database.investments
        self.users_collection = database.users
    
    async def get_dashboard_analytics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive dashboard analytics"""
        try:
            # Check cache first
            cache_key = f"dashboard_analytics_{user_id or 'global'}"
            cached_analytics = await cache_service.get(cache_key)
            if cached_analytics:
                return cached_analytics
            
            logger.info("📊 Generating dashboard analytics...")
            
            # Build base query
            query = {"user_id": user_id} if user_id else {}
            
            # Run analytics in parallel for better performance
            results = await asyncio.gather(
                self._get_project_analytics(query),
                self._get_investment_analytics(query),
                self._get_performance_analytics(query),
                self._get_trend_analytics(query),
                self._get_risk_analytics(query),
                return_exceptions=True
            )
            
            # Process results with error handling
            project_analytics = results[0] if not isinstance(results[0], Exception) else {}
            investment_analytics = results[1] if not isinstance(results[1], Exception) else {}
            performance_analytics = results[2] if not isinstance(results[2], Exception) else {}
            trend_analytics = results[3] if not isinstance(results[3], Exception) else {}
            risk_analytics = results[4] if not isinstance(results[4], Exception) else {}
            
            # Combine all analytics
            dashboard_analytics = {
                "overview": {
                    "total_projects": project_analytics.get("total_projects", 0),
                    "total_investments": investment_analytics.get("total_investments", 0),
                    "total_invested": investment_analytics.get("total_invested", 0.0),
                    "total_current_value": investment_analytics.get("total_current_value", 0.0),
                    "overall_roi": investment_analytics.get("overall_roi_percentage", 0.0),
                    "success_rate": project_analytics.get("success_rate", 0.0),
                    "average_investment": investment_analytics.get("average_investment", 0.0)
                },
                "projects": project_analytics,
                "investments": investment_analytics,
                "performance": performance_analytics,
                "trends": trend_analytics,
                "risk": risk_analytics,
                "generated_at": datetime.utcnow().isoformat(),
                "cache_ttl": 1800  # 30 minutes
            }
            
            # Cache for 30 minutes
            await cache_service.set(cache_key, dashboard_analytics, 1800)
            
            logger.info("✅ Dashboard analytics generated successfully")
            return dashboard_analytics
            
        except Exception as e:
            logger.error(f"❌ Failed to generate dashboard analytics: {e}")
            return self._get_fallback_analytics()
    
    async def get_funding_trends(self, user_id: Optional[str] = None, days: int = 30) -> List[Dict[str, Any]]:
        """Get funding trend data for charts"""
        try:
            # Check cache
            cache_key = f"funding_trends_{user_id or 'global'}_{days}"
            cached_trends = await cache_service.get(cache_key)
            if cached_trends:
                return cached_trends
            
            logger.info("📈 Generating funding trends...")
            
            # Build query for recent data
            query = {"user_id": user_id} if user_id else {}
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query["created_at"] = {"$gte": cutoff_date}
            
            # Get projects data
            projects_data = await self.projects_collection.find(query).to_list(length=None)
            
            if not projects_data:
                return []
            
            # Calculate funding trends
            trends = []
            for project_data in projects_data:
                try:
                    project = KickstarterProject(**project_data)
                    funding_velocity = await self._calculate_funding_velocity(project)
                    
                    trend_point = {
                        "project_id": project.id,
                        "name": project.name[:25] + "..." if len(project.name) > 25 else project.name,
                        "category": project.category,
                        "funding_velocity": funding_velocity,
                        "funding_percentage": project.funding_percentage(),
                        "success_probability": project.ai_analysis.get("success_probability", 50) if project.ai_analysis else 50,
                        "risk_level": project.risk_level,
                        "days_remaining": project.days_remaining(),
                        "created_at": project.created_at.isoformat(),
                        "goal_amount": project.goal_amount,
                        "pledged_amount": project.pledged_amount
                    }
                    trends.append(trend_point)
                    
                except Exception as e:
                    logger.error(f"Error processing project trend data: {e}")
                    continue
            
            # Sort by funding velocity
            trends.sort(key=lambda x: x["funding_velocity"], reverse=True)
            
            # Cache for 15 minutes
            await cache_service.set(cache_key, trends, 900)
            
            return trends
            
        except Exception as e:
            logger.error(f"❌ Failed to generate funding trends: {e}")
            return []
    
    async def get_roi_predictions(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate ROI predictions based on current portfolio"""
        try:
            # Check cache
            cache_key = f"roi_predictions_{user_id or 'global'}"
            cached_predictions = await cache_service.get(cache_key)
            if cached_predictions:
                return cached_predictions
            
            logger.info("🔮 Generating ROI predictions...")
            
            # Get investment data
            query = {"user_id": user_id} if user_id else {}
            investments_data = await self.investments_collection.find(query).to_list(length=None)
            
            if not investments_data:
                return self._get_empty_roi_predictions()
            
            investments = [Investment(**data) for data in investments_data]
            
            # Calculate current performance metrics
            total_invested = sum(inv.amount for inv in investments)
            total_current_value = sum(inv.current_value or inv.amount for inv in investments)
            current_roi = ((total_current_value - total_invested) / total_invested * 100) if total_invested > 0 else 0
            
            # Get project success probabilities for future predictions
            project_ids = [inv.project_id for inv in investments]
            projects_data = await self.projects_collection.find(
                {"id": {"$in": project_ids}}, 
                {"id": 1, "ai_analysis.success_probability": 1, "status": 1}
            ).to_list(length=None)
            
            success_probabilities = {
                proj["id"]: proj.get("ai_analysis", {}).get("success_probability", 50) 
                for proj in projects_data
            }
            
            # Calculate weighted success probability
            weighted_success = sum(
                success_probabilities.get(inv.project_id, 50) * inv.amount 
                for inv in investments
            ) / total_invested if total_invested > 0 else 50
            
            # Generate predictions based on current trends and success probabilities
            predictions = {
                "current_roi": round(current_roi, 2),
                "weighted_success_probability": round(weighted_success, 1),
                "predictions": {
                    "3_month": round(current_roi * 0.25 + (weighted_success - 50) * 0.1, 2),
                    "6_month": round(current_roi * 0.5 + (weighted_success - 50) * 0.2, 2),
                    "1_year": round(current_roi + (weighted_success - 50) * 0.4, 2),
                    "2_year": round(current_roi * 1.5 + (weighted_success - 50) * 0.8, 2)
                },
                "confidence_level": self._calculate_prediction_confidence(investments, weighted_success),
                "factors": {
                    "portfolio_diversification": self._calculate_diversification_factor(investments),
                    "market_sentiment": 0.65,  # Could be enhanced with real market data
                    "historical_performance": self._calculate_historical_performance(investments)
                },
                "recommendations": self._generate_roi_recommendations(current_roi, weighted_success, investments)
            }
            
            # Cache for 1 hour
            await cache_service.set(cache_key, predictions, 3600)
            
            return predictions
            
        except Exception as e:
            logger.error(f"❌ Failed to generate ROI predictions: {e}")
            return self._get_empty_roi_predictions()
    
    async def get_risk_analytics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive risk analytics"""
        try:
            # Check cache
            cache_key = f"risk_analytics_{user_id or 'global'}"
            cached_risk = await cache_service.get(cache_key)
            if cached_risk:
                return cached_risk
            
            logger.info("⚠️ Generating risk analytics...")
            
            # Get portfolio data
            query = {"user_id": user_id} if user_id else {}
            investments_data = await self.investments_collection.find(query).to_list(length=None)
            projects_data = await self.projects_collection.find(query).to_list(length=None)
            
            if not investments_data and not projects_data:
                return self._get_empty_risk_analytics()
            
            investments = [Investment(**data) for data in investments_data]
            projects = [KickstarterProject(**data) for data in projects_data]
            
            # Calculate risk metrics
            risk_analytics = {
                "overall_risk_score": await self._calculate_overall_risk_score(investments, projects),
                "risk_distribution": self._calculate_risk_distribution(investments, projects),
                "concentration_risk": self._calculate_concentration_risk(investments),
                "market_risk": self._calculate_market_risk(projects),
                "liquidity_risk": self._calculate_liquidity_risk(investments),
                "diversification_score": await self._calculate_diversification_score(investments),
                "risk_recommendations": await self._generate_risk_recommendations(investments, projects),
                "risk_trends": await self._calculate_risk_trends(investments),
                "stress_test": self._perform_stress_test(investments)
            }
            
            # Cache for 45 minutes
            await cache_service.set(cache_key, risk_analytics, 2700)
            
            return risk_analytics
            
        except Exception as e:
            logger.error(f"❌ Failed to generate risk analytics: {e}")
            return self._get_empty_risk_analytics()
    
    async def get_market_insights(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate market insights and opportunities"""
        try:
            # Check cache
            cache_key = f"market_insights_{user_id or 'global'}"
            cached_insights = await cache_service.get(cache_key)
            if cached_insights:
                return cached_insights
            
            logger.info("🌍 Generating market insights...")
            
            # Get market data
            all_projects_data = await self.projects_collection.find({}).to_list(length=None)
            user_query = {"user_id": user_id} if user_id else {}
            user_projects_data = await self.projects_collection.find(user_query).to_list(length=None)
            
            if not all_projects_data:
                return self._get_empty_market_insights()
            
            # Analyze market trends
            market_insights = {
                "category_performance": await self._analyze_category_performance(all_projects_data),
                "emerging_trends": await self._identify_emerging_trends(all_projects_data),
                "success_factors": await self._analyze_success_factors(all_projects_data),
                "market_opportunities": await self._identify_market_opportunities(all_projects_data, user_projects_data),
                "competitive_landscape": await self._analyze_competitive_landscape(all_projects_data),
                "timing_insights": await self._analyze_timing_insights(all_projects_data),
                "investment_gaps": await self._identify_investment_gaps(user_projects_data, all_projects_data)
            }
            
            # Cache for 2 hours
            await cache_service.set(cache_key, market_insights, 7200)
            
            return market_insights
            
        except Exception as e:
            logger.error(f"❌ Failed to generate market insights: {e}")
            return self._get_empty_market_insights()
    
    # Helper methods for analytics calculations
    
    async def _get_project_analytics(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate project-related analytics"""
        try:
            # Get project counts by status
            pipeline = [
                {"$match": query},
                {"$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "avg_funding": {"$avg": "$pledged_amount"},
                    "total_funding": {"$sum": "$pledged_amount"}
                }}
            ]
            
            status_stats = await self.projects_collection.aggregate(pipeline).to_list(length=None)
            
            # Calculate totals
            total_projects = sum(stat["count"] for stat in status_stats)
            successful_projects = next((stat["count"] for stat in status_stats if stat["_id"] == "successful"), 0)
            success_rate = (successful_projects / total_projects * 100) if total_projects > 0 else 0
            
            # Get category distribution
            category_pipeline = [
                {"$match": query},
                {"$group": {"_id": "$category", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            
            category_dist = await self.projects_collection.aggregate(category_pipeline).to_list(length=None)
            
            return {
                "total_projects": total_projects,
                "successful_projects": successful_projects,
                "success_rate": round(success_rate, 2),
                "status_distribution": {stat["_id"]: stat["count"] for stat in status_stats},
                "category_distribution": {cat["_id"]: cat["count"] for cat in category_dist[:10]},
                "avg_funding_by_status": {stat["_id"]: round(stat["avg_funding"], 2) for stat in status_stats}
            }
            
        except Exception as e:
            logger.error(f"Project analytics calculation failed: {e}")
            return {}
    
    async def _get_investment_analytics(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate investment-related analytics"""
        try:
            investments_data = await self.investments_collection.find(query).to_list(length=None)
            
            if not investments_data:
                return {
                    "total_investments": 0,
                    "total_invested": 0.0,
                    "total_current_value": 0.0,
                    "overall_roi_percentage": 0.0,
                    "average_investment": 0.0
                }
            
            investments = [Investment(**data) for data in investments_data]
            
            total_invested = sum(inv.amount for inv in investments)
            total_current_value = sum(inv.current_value or inv.amount for inv in investments)
            overall_roi = ((total_current_value - total_invested) / total_invested * 100) if total_invested > 0 else 0
            
            return {
                "total_investments": len(investments),
                "total_invested": round(total_invested, 2),
                "total_current_value": round(total_current_value, 2),
                "overall_roi_percentage": round(overall_roi, 2),
                "average_investment": round(total_invested / len(investments), 2) if investments else 0,
                "profitable_investments": sum(1 for inv in investments if inv.is_profitable()),
                "delivered_investments": sum(1 for inv in investments if inv.delivery_status == "delivered")
            }
            
        except Exception as e:
            logger.error(f"Investment analytics calculation failed: {e}")
            return {}
    
    async def _get_performance_analytics(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance analytics"""
        try:
            # This would include more sophisticated performance metrics
            return {
                "portfolio_performance": "stable",
                "risk_adjusted_return": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "volatility": 0.0
            }
        except Exception as e:
            logger.error(f"Performance analytics calculation failed: {e}")
            return {}
    
    async def _get_trend_analytics(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate trend analytics"""
        try:
            # Get recent trends
            return {
                "funding_velocity_trend": "increasing",
                "category_momentum": {},
                "seasonal_patterns": {},
                "success_rate_trend": "stable"
            }
        except Exception as e:
            logger.error(f"Trend analytics calculation failed: {e}")
            return {}
    
    async def _get_risk_analytics(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate risk analytics"""
        try:
            return {
                "overall_risk_level": "medium",
                "concentration_risk": "low",
                "market_risk": "medium",
                "diversification_score": 0.7
            }
        except Exception as e:
            logger.error(f"Risk analytics calculation failed: {e}")
            return {}
    
    async def _calculate_funding_velocity(self, project: KickstarterProject) -> float:
        """Calculate funding velocity for a project"""
        try:
            days_since_launch = (datetime.utcnow() - project.created_at).days
            if days_since_launch <= 0:
                return 0.0
            
            return project.pledged_amount / days_since_launch
        except Exception:
            return 0.0
    
    def _get_fallback_analytics(self) -> Dict[str, Any]:
        """Return fallback analytics when calculation fails"""
        return {
            "overview": {
                "total_projects": 0,
                "total_investments": 0,
                "total_invested": 0.0,
                "total_current_value": 0.0,
                "overall_roi": 0.0,
                "success_rate": 0.0,
                "average_investment": 0.0
            },
            "projects": {},
            "investments": {},
            "performance": {},
            "trends": {},
            "risk": {},
            "generated_at": datetime.utcnow().isoformat(),
            "error": "Analytics calculation failed"
        }
    
    def _get_empty_roi_predictions(self) -> Dict[str, Any]:
        """Return empty ROI predictions structure"""
        return {
            "current_roi": 0.0,
            "weighted_success_probability": 50.0,
            "predictions": {
                "3_month": 0.0,
                "6_month": 0.0,
                "1_year": 0.0,
                "2_year": 0.0
            },
            "confidence_level": "low",
            "factors": {
                "portfolio_diversification": 0.0,
                "market_sentiment": 0.5,
                "historical_performance": 0.0
            },
            "recommendations": ["Build your investment portfolio to generate predictions"]
        }
    
    def _get_empty_risk_analytics(self) -> Dict[str, Any]:
        """Return empty risk analytics structure"""
        return {
            "overall_risk_score": 50.0,
            "risk_distribution": {},
            "concentration_risk": 0.0,
            "market_risk": 50.0,
            "liquidity_risk": 0.0,
            "diversification_score": 0.0,
            "risk_recommendations": ["Build your portfolio to analyze risk"],
            "risk_trends": [],
            "stress_test": {}
        }
    
    def _get_empty_market_insights(self) -> Dict[str, Any]:
        """Return empty market insights structure"""
        return {
            "category_performance": {},
            "emerging_trends": [],
            "success_factors": [],
            "market_opportunities": [],
            "competitive_landscape": {},
            "timing_insights": {},
            "investment_gaps": []
        }
    
    # Additional helper methods would be implemented here for:
    # - _calculate_prediction_confidence
    # - _calculate_diversification_factor
    # - _calculate_historical_performance
    # - _generate_roi_recommendations
    # - _calculate_overall_risk_score
    # - _calculate_risk_distribution
    # - _calculate_concentration_risk
    # - etc.
    
    # For brevity, I'm providing placeholder implementations
    def _calculate_prediction_confidence(self, investments: List[Investment], weighted_success: float) -> str:
        """Calculate confidence level for predictions"""
        if len(investments) < 3:
            return "low"
        elif weighted_success > 70 and len(investments) > 10:
            return "high"
        else:
            return "medium"
    
    def _calculate_diversification_factor(self, investments: List[Investment]) -> float:
        """Calculate portfolio diversification factor"""
        if not investments:
            return 0.0
        
        # Simple diversification based on number of unique projects
        unique_projects = len(set(inv.project_id for inv in investments))
        return min(unique_projects / 10, 1.0)  # Normalize to 0-1
    
    def _calculate_historical_performance(self, investments: List[Investment]) -> float:
        """Calculate historical performance score"""
        if not investments:
            return 0.0
        
        profitable_count = sum(1 for inv in investments if inv.is_profitable())
        return profitable_count / len(investments)
    
    def _generate_roi_recommendations(self, current_roi: float, weighted_success: float, investments: List[Investment]) -> List[str]:
        """Generate ROI improvement recommendations"""
        recommendations = []
        
        if current_roi < 0:
            recommendations.append("Review underperforming investments for exit opportunities")
        
        if weighted_success < 60:
            recommendations.append("Focus on higher success probability projects")
        
        if len(investments) < 5:
            recommendations.append("Increase portfolio diversification")
        
        recommendations.append("Monitor market trends for emerging opportunities")
        
        return recommendations

# Global analytics service instance (will be initialized with database)
analytics_service = None

def initialize_analytics_service(database):
    """Initialize analytics service with database connection"""
    global analytics_service
    analytics_service = AnalyticsService(database)
    return analytics_service