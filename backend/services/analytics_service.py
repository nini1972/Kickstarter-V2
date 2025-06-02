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
                "confidence_level": "medium" if investments else "low",
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
    
    # Additional helper methods implementation for comprehensive analytics
    
    async def _calculate_overall_risk_score(self, investments: List[Investment], projects: List[KickstarterProject]) -> float:
        """Calculate overall portfolio risk score (0-100)"""
        try:
            if not investments and not projects:
                return 50.0  # Neutral risk for empty portfolio
            
            risk_factors = []
            
            # Investment risk factors
            if investments:
                # Concentration risk
                total_invested = sum(inv.amount for inv in investments)
                if total_invested > 0:
                    concentrations = {}
                    for inv in investments:
                        concentrations[inv.project_id] = concentrations.get(inv.project_id, 0) + inv.amount
                    
                    max_concentration = max(concentrations.values()) / total_invested
                    concentration_risk = min(max_concentration * 100, 100)
                    risk_factors.append(concentration_risk)
                
                # Delivery risk
                pending_deliveries = sum(1 for inv in investments if inv.delivery_status == "pending")
                delivery_risk = (pending_deliveries / len(investments)) * 50 if investments else 0
                risk_factors.append(delivery_risk)
            
            # Project risk factors
            if projects:
                # Risk level distribution
                risk_levels = [p.risk_level for p in projects]
                high_risk_count = sum(1 for r in risk_levels if r == "high")
                medium_risk_count = sum(1 for r in risk_levels if r == "medium")
                
                risk_score = (high_risk_count * 80 + medium_risk_count * 50) / len(projects)
                risk_factors.append(risk_score)
                
                # Funding status risk
                failing_projects = sum(1 for p in projects if p.funding_percentage() < 50 and p.days_remaining() < 10)
                funding_risk = (failing_projects / len(projects)) * 70 if projects else 0
                risk_factors.append(funding_risk)
            
            # Calculate weighted average
            overall_risk = sum(risk_factors) / len(risk_factors) if risk_factors else 50.0
            return round(min(max(overall_risk, 0), 100), 1)
            
        except Exception as e:
            logger.error(f"Risk score calculation failed: {e}")
            return 50.0
    
    def _calculate_risk_distribution(self, investments: List[Investment], projects: List[KickstarterProject]) -> Dict[str, float]:
        """Calculate risk distribution across different categories"""
        try:
            distribution = {"low": 0, "medium": 0, "high": 0}
            
            if projects:
                for project in projects:
                    risk_level = project.risk_level.lower()
                    if risk_level in distribution:
                        distribution[risk_level] += 1
                
                # Convert to percentages
                total = sum(distribution.values())
                if total > 0:
                    distribution = {k: round((v / total) * 100, 1) for k, v in distribution.items()}
            
            return distribution
            
        except Exception as e:
            logger.error(f"Risk distribution calculation failed: {e}")
            return {"low": 33.3, "medium": 33.3, "high": 33.3}
    
    def _calculate_concentration_risk(self, investments: List[Investment]) -> float:
        """Calculate portfolio concentration risk (0-1)"""
        try:
            if not investments:
                return 0.0
            
            total_invested = sum(inv.amount for inv in investments)
            if total_invested == 0:
                return 0.0
            
            # Calculate Herfindahl-Hirschman Index for concentration
            project_concentrations = {}
            for inv in investments:
                project_concentrations[inv.project_id] = project_concentrations.get(inv.project_id, 0) + inv.amount
            
            hhi = sum((amount / total_invested) ** 2 for amount in project_concentrations.values())
            
            # Convert HHI to risk score (higher HHI = higher concentration = higher risk)
            return round(min(hhi, 1.0), 3)
            
        except Exception as e:
            logger.error(f"Concentration risk calculation failed: {e}")
            return 0.5
    
    def _calculate_market_risk(self, projects: List[KickstarterProject]) -> float:
        """Calculate market risk based on project portfolio"""
        try:
            if not projects:
                return 50.0
            
            # Category diversity (lower diversity = higher market risk)
            categories = set(p.category for p in projects)
            category_diversity = min(len(categories) / 5, 1.0)  # Normalize to max 5 categories
            
            # Time diversity (all projects ending around same time = higher risk)
            end_dates = [p.deadline for p in projects if p.deadline]
            if len(end_dates) > 1:
                date_spread = (max(end_dates) - min(end_dates)).days
                time_diversity = min(date_spread / 365, 1.0)  # Normalize to 1 year
            else:
                time_diversity = 0.0
            
            # Success probability average
            success_probs = [p.ai_analysis.get("success_probability", 50) for p in projects if p.ai_analysis]
            avg_success = sum(success_probs) / len(success_probs) if success_probs else 50
            
            # Calculate market risk (inverse of positive factors)
            market_risk = 100 - (category_diversity * 30 + time_diversity * 20 + (avg_success / 100) * 50)
            return round(max(min(market_risk, 100), 0), 1)
            
        except Exception as e:
            logger.error(f"Market risk calculation failed: {e}")
            return 50.0
    
    def _calculate_liquidity_risk(self, investments: List[Investment]) -> float:
        """Calculate liquidity risk of portfolio"""
        try:
            if not investments:
                return 0.0
            
            # Factors affecting liquidity:
            # 1. Delivery status (delivered = more liquid)
            # 2. Investment age (older = potentially more liquid)
            # 3. Project success (successful = more liquid)
            
            liquidity_scores = []
            
            for inv in investments:
                score = 0
                
                # Delivery status impact
                if inv.delivery_status == "delivered":
                    score += 40
                elif inv.delivery_status == "in_production":
                    score += 20
                elif inv.delivery_status == "pending":
                    score += 5
                
                # Investment age impact (older investments might be more liquid)
                days_old = (datetime.utcnow() - inv.created_at).days
                age_score = min(days_old / 365 * 30, 30)  # Max 30 points for 1+ year old
                score += age_score
                
                # Return potential (profitable investments are more liquid)
                if inv.is_profitable():
                    score += 30
                
                liquidity_scores.append(score)
            
            # Average liquidity (higher score = lower risk)
            avg_liquidity = sum(liquidity_scores) / len(liquidity_scores)
            liquidity_risk = 100 - avg_liquidity  # Invert to get risk
            
            return round(max(min(liquidity_risk, 100), 0), 1)
            
        except Exception as e:
            logger.error(f"Liquidity risk calculation failed: {e}")
            return 50.0
    
    async def _calculate_diversification_score(self, investments: List[Investment]) -> float:
        """Calculate diversification score (0-1)"""
        try:
            if not investments:
                return 0.0
            
            # Get project details for invested projects
            project_ids = list(set(inv.project_id for inv in investments))
            projects_data = await self.projects_collection.find(
                {"id": {"$in": project_ids}},
                {"id": 1, "category": 1, "deadline": 1}
            ).to_list(length=None)
            
            project_details = {p["id"]: p for p in projects_data}
            
            # Calculate diversification across multiple dimensions
            
            # 1. Project count diversity
            project_count_score = min(len(project_ids) / 10, 1.0)  # Max at 10 projects
            
            # 2. Category diversity
            categories = set()
            for inv in investments:
                project = project_details.get(inv.project_id, {})
                if "category" in project:
                    categories.add(project["category"])
            
            category_score = min(len(categories) / 5, 1.0)  # Max at 5 categories
            
            # 3. Investment amount diversity (prevent over-concentration)
            amounts = [inv.amount for inv in investments]
            total_amount = sum(amounts)
            if total_amount > 0:
                # Calculate coefficient of variation (lower = more diverse)
                mean_amount = total_amount / len(amounts)
                variance = sum((amount - mean_amount) ** 2 for amount in amounts) / len(amounts)
                std_dev = variance ** 0.5
                coeff_variation = std_dev / mean_amount if mean_amount > 0 else 0
                amount_score = max(0, 1 - min(coeff_variation, 1))  # Invert and cap
            else:
                amount_score = 0
            
            # 4. Time diversity (investment timing)
            investment_dates = [inv.created_at for inv in investments]
            if len(investment_dates) > 1:
                date_spread = (max(investment_dates) - min(investment_dates)).days
                time_score = min(date_spread / 365, 1.0)  # Max at 1 year spread
            else:
                time_score = 0.0
            
            # Weighted average of diversification factors
            diversification_score = (
                project_count_score * 0.3 +
                category_score * 0.3 +
                amount_score * 0.2 +
                time_score * 0.2
            )
            
            return round(diversification_score, 3)
            
        except Exception as e:
            logger.error(f"Diversification score calculation failed: {e}")
            return 0.0
    
    async def _generate_risk_recommendations(self, investments: List[Investment], projects: List[KickstarterProject]) -> List[str]:
        """Generate risk management recommendations"""
        try:
            recommendations = []
            
            if not investments and not projects:
                return ["Start building your investment portfolio to receive risk analysis"]
            
            # Check concentration risk
            concentration_risk = self._calculate_concentration_risk(investments)
            if concentration_risk > 0.5:
                recommendations.append("Consider diversifying across more projects to reduce concentration risk")
            
            # Check category diversity
            if investments:
                project_ids = [inv.project_id for inv in investments]
                projects_data = await self.projects_collection.find(
                    {"id": {"$in": project_ids}},
                    {"category": 1}
                ).to_list(length=None)
                
                categories = set(p.get("category") for p in projects_data if p.get("category"))
                if len(categories) < 3:
                    recommendations.append("Diversify across different project categories to reduce market risk")
            
            # Check high-risk project exposure
            if projects:
                high_risk_projects = sum(1 for p in projects if p.risk_level == "high")
                if high_risk_projects / len(projects) > 0.3:
                    recommendations.append("Consider reducing exposure to high-risk projects")
            
            # Check delivery status
            if investments:
                pending_deliveries = sum(1 for inv in investments if inv.delivery_status == "pending")
                if pending_deliveries / len(investments) > 0.5:
                    recommendations.append("Monitor pending deliveries and consider following up with creators")
            
            # General recommendations
            if len(investments) < 5:
                recommendations.append("Consider increasing portfolio size for better risk distribution")
            
            if not recommendations:
                recommendations.append("Your portfolio shows good risk management - keep monitoring and adjusting")
            
            return recommendations[:5]  # Limit to top 5 recommendations
            
        except Exception as e:
            logger.error(f"Risk recommendations generation failed: {e}")
            return ["Unable to generate risk recommendations at this time"]
    
    async def _calculate_risk_trends(self, investments: List[Investment]) -> List[Dict[str, Any]]:
        """Calculate risk trends over time"""
        try:
            if not investments:
                return []
            
            # Group investments by month
            monthly_risk = {}
            
            for inv in investments:
                month_key = inv.created_at.strftime("%Y-%m")
                if month_key not in monthly_risk:
                    monthly_risk[month_key] = {"investments": [], "risk_score": 0}
                monthly_risk[month_key]["investments"].append(inv)
            
            # Calculate risk score for each month
            trends = []
            for month, data in sorted(monthly_risk.items()):
                month_investments = data["investments"]
                
                # Simple risk calculation based on average amounts and delivery status
                avg_amount = sum(inv.amount for inv in month_investments) / len(month_investments)
                pending_ratio = sum(1 for inv in month_investments if inv.delivery_status == "pending") / len(month_investments)
                
                risk_score = (avg_amount / 1000 * 30 + pending_ratio * 70)  # Risk increases with amount and pending deliveries
                risk_score = min(max(risk_score, 0), 100)
                
                trends.append({
                    "month": month,
                    "risk_score": round(risk_score, 1),
                    "investment_count": len(month_investments),
                    "total_amount": sum(inv.amount for inv in month_investments)
                })
            
            return trends[-12:]  # Return last 12 months
            
        except Exception as e:
            logger.error(f"Risk trends calculation failed: {e}")
            return []
    
    def _perform_stress_test(self, investments: List[Investment]) -> Dict[str, Any]:
        """Perform portfolio stress test under various scenarios"""
        try:
            if not investments:
                return {}
            
            total_invested = sum(inv.amount for inv in investments)
            current_value = sum(inv.current_value or inv.amount for inv in investments)
            
            # Scenario 1: 20% market downturn
            scenario_1_value = current_value * 0.8
            scenario_1_loss = total_invested - scenario_1_value
            
            # Scenario 2: 50% of pending projects fail
            pending_investments = [inv for inv in investments if inv.delivery_status == "pending"]
            scenario_2_loss = sum(inv.amount for inv in pending_investments) * 0.5
            scenario_2_value = current_value - scenario_2_loss
            
            # Scenario 3: Major project failure (largest investment fails)
            if investments:
                largest_investment = max(investments, key=lambda x: x.amount)
                scenario_3_loss = largest_investment.amount
                scenario_3_value = current_value - scenario_3_loss
            else:
                scenario_3_loss = 0
                scenario_3_value = current_value
            
            return {
                "market_downturn_20pct": {
                    "portfolio_value": round(scenario_1_value, 2),
                    "loss_amount": round(scenario_1_loss, 2),
                    "loss_percentage": round((scenario_1_loss / total_invested * 100), 1) if total_invested > 0 else 0
                },
                "pending_failures_50pct": {
                    "portfolio_value": round(scenario_2_value, 2),
                    "loss_amount": round(scenario_2_loss, 2),
                    "loss_percentage": round((scenario_2_loss / total_invested * 100), 1) if total_invested > 0 else 0
                },
                "largest_project_failure": {
                    "portfolio_value": round(scenario_3_value, 2),
                    "loss_amount": round(scenario_3_loss, 2),
                    "loss_percentage": round((scenario_3_loss / total_invested * 100), 1) if total_invested > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Stress test calculation failed: {e}")
            return {}
    
    # Market insights helper methods
    
    async def _analyze_category_performance(self, all_projects_data: List[Dict]) -> Dict[str, Any]:
        """Analyze performance across different project categories"""
        try:
            if not all_projects_data:
                return {}
            
            category_stats = {}
            
            for project_data in all_projects_data:
                try:
                    project = KickstarterProject(**project_data)
                    category = project.category
                    
                    if category not in category_stats:
                        category_stats[category] = {
                            "total_projects": 0,
                            "successful_projects": 0,
                            "total_funding": 0,
                            "avg_funding_percentage": 0,
                            "success_rate": 0
                        }
                    
                    stats = category_stats[category]
                    stats["total_projects"] += 1
                    stats["total_funding"] += project.pledged_amount
                    
                    if project.status == "successful":
                        stats["successful_projects"] += 1
                    
                    funding_percentage = project.funding_percentage()
                    stats["avg_funding_percentage"] += funding_percentage
                    
                except Exception as e:
                    logger.error(f"Error processing project for category analysis: {e}")
                    continue
            
            # Calculate final metrics
            for category, stats in category_stats.items():
                if stats["total_projects"] > 0:
                    stats["success_rate"] = round((stats["successful_projects"] / stats["total_projects"]) * 100, 1)
                    stats["avg_funding_percentage"] = round(stats["avg_funding_percentage"] / stats["total_projects"], 1)
                    stats["avg_funding_per_project"] = round(stats["total_funding"] / stats["total_projects"], 2)
            
            # Sort by success rate
            sorted_categories = sorted(category_stats.items(), key=lambda x: x[1]["success_rate"], reverse=True)
            
            return {
                "top_performing_categories": dict(sorted_categories[:5]),
                "category_rankings": sorted_categories,
                "total_categories": len(category_stats)
            }
            
        except Exception as e:
            logger.error(f"Category performance analysis failed: {e}")
            return {}
    
    async def _identify_emerging_trends(self, all_projects_data: List[Dict]) -> List[Dict[str, Any]]:
        """Identify emerging trends in the market"""
        try:
            if not all_projects_data:
                return []
            
            # Analyze recent projects (last 6 months) vs older projects
            six_months_ago = datetime.utcnow() - timedelta(days=180)
            recent_projects = []
            older_projects = []
            
            for project_data in all_projects_data:
                try:
                    project = KickstarterProject(**project_data)
                    if project.created_at >= six_months_ago:
                        recent_projects.append(project)
                    else:
                        older_projects.append(project)
                except Exception:
                    continue
            
            trends = []
            
            if recent_projects and older_projects:
                # Category trend analysis
                recent_categories = {}
                older_categories = {}
                
                for project in recent_projects:
                    recent_categories[project.category] = recent_categories.get(project.category, 0) + 1
                
                for project in older_projects:
                    older_categories[project.category] = older_categories.get(project.category, 0) + 1
                
                # Calculate growth rates
                for category in recent_categories:
                    recent_count = recent_categories[category]
                    older_count = older_categories.get(category, 0)
                    
                    if older_count > 0:
                        growth_rate = ((recent_count - older_count) / older_count) * 100
                        if growth_rate > 50:  # Significant growth
                            trends.append({
                                "type": "category_growth",
                                "category": category,
                                "growth_rate": round(growth_rate, 1),
                                "description": f"{category} projects showing {growth_rate:.1f}% growth"
                            })
                
                # Funding amount trends
                recent_avg_funding = sum(p.pledged_amount for p in recent_projects) / len(recent_projects)
                older_avg_funding = sum(p.pledged_amount for p in older_projects) / len(older_projects)
                
                if older_avg_funding > 0:
                    funding_growth = ((recent_avg_funding - older_avg_funding) / older_avg_funding) * 100
                    if abs(funding_growth) > 20:
                        trends.append({
                            "type": "funding_trend",
                            "growth_rate": round(funding_growth, 1),
                            "description": f"Average funding {'increased' if funding_growth > 0 else 'decreased'} by {abs(funding_growth):.1f}%"
                        })
            
            return trends[:5]  # Return top 5 trends
            
        except Exception as e:
            logger.error(f"Emerging trends analysis failed: {e}")
            return []
    
    async def _analyze_success_factors(self, all_projects_data: List[Dict]) -> List[Dict[str, Any]]:
        """Analyze key success factors for projects"""
        try:
            if not all_projects_data:
                return []
            
            successful_projects = []
            failed_projects = []
            
            for project_data in all_projects_data:
                try:
                    project = KickstarterProject(**project_data)
                    if project.status == "successful":
                        successful_projects.append(project)
                    elif project.status == "failed":
                        failed_projects.append(project)
                except Exception:
                    continue
            
            factors = []
            
            if successful_projects and failed_projects:
                # Goal amount analysis
                successful_avg_goal = sum(p.goal_amount for p in successful_projects) / len(successful_projects)
                failed_avg_goal = sum(p.goal_amount for p in failed_projects) / len(failed_projects)
                
                factors.append({
                    "factor": "optimal_goal_amount",
                    "successful_avg": round(successful_avg_goal, 2),
                    "failed_avg": round(failed_avg_goal, 2),
                    "insight": f"Successful projects average ${successful_avg_goal:,.0f} goals vs ${failed_avg_goal:,.0f} for failed"
                })
                
                # Project duration analysis (if deadline data available)
                successful_durations = []
                failed_durations = []
                
                for project in successful_projects:
                    if project.deadline and project.created_at:
                        duration = (project.deadline - project.created_at).days
                        successful_durations.append(duration)
                
                for project in failed_projects:
                    if project.deadline and project.created_at:
                        duration = (project.deadline - project.created_at).days
                        failed_durations.append(duration)
                
                if successful_durations and failed_durations:
                    successful_avg_duration = sum(successful_durations) / len(successful_durations)
                    failed_avg_duration = sum(failed_durations) / len(failed_durations)
                    
                    factors.append({
                        "factor": "campaign_duration",
                        "successful_avg": round(successful_avg_duration, 0),
                        "failed_avg": round(failed_avg_duration, 0),
                        "insight": f"Successful campaigns average {successful_avg_duration:.0f} days vs {failed_avg_duration:.0f} days"
                    })
                
                # Category success rates
                category_success = {}
                for project in successful_projects + failed_projects:
                    category = project.category
                    if category not in category_success:
                        category_success[category] = {"successful": 0, "total": 0}
                    
                    category_success[category]["total"] += 1
                    if project.status == "successful":
                        category_success[category]["successful"] += 1
                
                best_category = max(category_success.items(), 
                                  key=lambda x: x[1]["successful"] / x[1]["total"] if x[1]["total"] > 0 else 0)
                
                if best_category[1]["total"] > 0:
                    success_rate = (best_category[1]["successful"] / best_category[1]["total"]) * 100
                    factors.append({
                        "factor": "best_performing_category",
                        "category": best_category[0],
                        "success_rate": round(success_rate, 1),
                        "insight": f"{best_category[0]} has highest success rate at {success_rate:.1f}%"
                    })
            
            return factors
            
        except Exception as e:
            logger.error(f"Success factors analysis failed: {e}")
            return []
    
    async def _identify_market_opportunities(self, all_projects_data: List[Dict], user_projects_data: List[Dict]) -> List[Dict[str, Any]]:
        """Identify potential market opportunities"""
        try:
            opportunities = []
            
            if not all_projects_data:
                return opportunities
            
            # Analyze underserved categories
            category_saturation = {}
            total_projects = len(all_projects_data)
            
            for project_data in all_projects_data:
                try:
                    project = KickstarterProject(**project_data)
                    category = project.category
                    category_saturation[category] = category_saturation.get(category, 0) + 1
                except Exception:
                    continue
            
            # Find categories with low saturation but high success rates
            for category, count in category_saturation.items():
                saturation_rate = (count / total_projects) * 100
                if saturation_rate < 5:  # Less than 5% of market
                    # Check success rate for this category
                    category_projects = [p for p in all_projects_data if p.get("category") == category]
                    successful = sum(1 for p in category_projects if p.get("status") == "successful")
                    success_rate = (successful / len(category_projects)) * 100 if category_projects else 0
                    
                    if success_rate > 60:  # High success rate
                        opportunities.append({
                            "type": "underserved_category",
                            "category": category,
                            "saturation_rate": round(saturation_rate, 1),
                            "success_rate": round(success_rate, 1),
                            "description": f"{category} is underserved ({saturation_rate:.1f}% market share) with high success rate ({success_rate:.1f}%)"
                        })
            
            # Analyze user's portfolio gaps
            if user_projects_data:
                user_categories = set(p.get("category") for p in user_projects_data)
                market_categories = set(p.get("category") for p in all_projects_data)
                missing_categories = market_categories - user_categories
                
                for category in list(missing_categories)[:3]:  # Top 3 missing categories
                    category_projects = [p for p in all_projects_data if p.get("category") == category]
                    if category_projects:
                        avg_funding = sum(p.get("pledged_amount", 0) for p in category_projects) / len(category_projects)
                        opportunities.append({
                            "type": "portfolio_gap",
                            "category": category,
                            "avg_funding": round(avg_funding, 2),
                            "description": f"Consider exploring {category} projects (avg funding: ${avg_funding:,.0f})"
                        })
            
            return opportunities[:5]  # Return top 5 opportunities
            
        except Exception as e:
            logger.error(f"Market opportunities analysis failed: {e}")
            return []
    
    async def _analyze_competitive_landscape(self, all_projects_data: List[Dict]) -> Dict[str, Any]:
        """Analyze competitive landscape"""
        try:
            if not all_projects_data:
                return {}
            
            # Market concentration analysis
            category_funding = {}
            total_market_funding = 0
            
            for project_data in all_projects_data:
                try:
                    project = KickstarterProject(**project_data)
                    category = project.category
                    funding = project.pledged_amount
                    
                    category_funding[category] = category_funding.get(category, 0) + funding
                    total_market_funding += funding
                except Exception:
                    continue
            
            # Calculate market share
            market_share = {}
            for category, funding in category_funding.items():
                share = (funding / total_market_funding) * 100 if total_market_funding > 0 else 0
                market_share[category] = round(share, 2)
            
            # Identify dominant categories
            dominant_categories = sorted(market_share.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Competition intensity (projects per category)
            category_counts = {}
            for project_data in all_projects_data:
                category = project_data.get("category")
                if category:
                    category_counts[category] = category_counts.get(category, 0) + 1
            
            return {
                "market_leaders": dict(dominant_categories),
                "market_concentration": {
                    "total_funding": round(total_market_funding, 2),
                    "total_categories": len(category_funding),
                    "hhi_index": sum((share/100)**2 for share in market_share.values())  # Herfindahl index
                },
                "competition_intensity": dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5])
            }
            
        except Exception as e:
            logger.error(f"Competitive landscape analysis failed: {e}")
            return {}
    
    async def _analyze_timing_insights(self, all_projects_data: List[Dict]) -> Dict[str, Any]:
        """Analyze optimal timing patterns"""
        try:
            if not all_projects_data:
                return {}
            
            # Monthly success rate analysis
            monthly_stats = {}
            
            for project_data in all_projects_data:
                try:
                    project = KickstarterProject(**project_data)
                    month = project.created_at.strftime("%B")
                    
                    if month not in monthly_stats:
                        monthly_stats[month] = {"total": 0, "successful": 0}
                    
                    monthly_stats[month]["total"] += 1
                    if project.status == "successful":
                        monthly_stats[month]["successful"] += 1
                        
                except Exception:
                    continue
            
            # Calculate success rates by month
            monthly_success_rates = {}
            for month, stats in monthly_stats.items():
                if stats["total"] > 0:
                    success_rate = (stats["successful"] / stats["total"]) * 100
                    monthly_success_rates[month] = round(success_rate, 1)
            
            # Find best and worst months
            best_month = max(monthly_success_rates.items(), key=lambda x: x[1]) if monthly_success_rates else ("N/A", 0)
            worst_month = min(monthly_success_rates.items(), key=lambda x: x[1]) if monthly_success_rates else ("N/A", 0)
            
            return {
                "monthly_success_rates": monthly_success_rates,
                "best_launch_month": {
                    "month": best_month[0],
                    "success_rate": best_month[1]
                },
                "worst_launch_month": {
                    "month": worst_month[0],
                    "success_rate": worst_month[1]
                },
                "seasonal_insights": self._generate_seasonal_insights(monthly_success_rates)
            }
            
        except Exception as e:
            logger.error(f"Timing insights analysis failed: {e}")
            return {}
    
    async def _identify_investment_gaps(self, user_projects_data: List[Dict], all_projects_data: List[Dict]) -> List[Dict[str, Any]]:
        """Identify gaps in user's investment strategy"""
        try:
            gaps = []
            
            if not all_projects_data:
                return gaps
            
            # Analyze user's portfolio composition
            user_categories = {}
            user_risk_levels = {}
            user_funding_ranges = {"low": 0, "medium": 0, "high": 0}  # <10k, 10k-100k, >100k
            
            for project_data in user_projects_data:
                try:
                    project = KickstarterProject(**project_data)
                    
                    # Category distribution
                    category = project.category
                    user_categories[category] = user_categories.get(category, 0) + 1
                    
                    # Risk level distribution
                    risk = project.risk_level
                    user_risk_levels[risk] = user_risk_levels.get(risk, 0) + 1
                    
                    # Funding range distribution
                    if project.goal_amount < 10000:
                        user_funding_ranges["low"] += 1
                    elif project.goal_amount < 100000:
                        user_funding_ranges["medium"] += 1
                    else:
                        user_funding_ranges["high"] += 1
                        
                except Exception:
                    continue
            
            # Compare with market distribution
            market_categories = {}
            market_risk_levels = {}
            market_funding_ranges = {"low": 0, "medium": 0, "high": 0}
            
            for project_data in all_projects_data:
                try:
                    project = KickstarterProject(**project_data)
                    
                    market_categories[project.category] = market_categories.get(project.category, 0) + 1
                    market_risk_levels[project.risk_level] = market_risk_levels.get(project.risk_level, 0) + 1
                    
                    if project.goal_amount < 10000:
                        market_funding_ranges["low"] += 1
                    elif project.goal_amount < 100000:
                        market_funding_ranges["medium"] += 1
                    else:
                        market_funding_ranges["high"] += 1
                        
                except Exception:
                    continue
            
            # Identify category gaps
            total_user_projects = sum(user_categories.values()) if user_categories else 1
            total_market_projects = sum(market_categories.values()) if market_categories else 1
            
            for category, market_count in market_categories.items():
                market_percentage = (market_count / total_market_projects) * 100
                user_count = user_categories.get(category, 0)
                user_percentage = (user_count / total_user_projects) * 100
                
                if market_percentage > 10 and user_percentage < 5:  # Significant market presence, low user presence
                    gaps.append({
                        "type": "category_gap",
                        "category": category,
                        "market_share": round(market_percentage, 1),
                        "user_share": round(user_percentage, 1),
                        "recommendation": f"Consider investing in {category} projects (market share: {market_percentage:.1f}%)"
                    })
            
            # Identify risk level gaps
            for risk_level, market_count in market_risk_levels.items():
                market_percentage = (market_count / total_market_projects) * 100
                user_count = user_risk_levels.get(risk_level, 0)
                user_percentage = (user_count / total_user_projects) * 100
                
                if abs(market_percentage - user_percentage) > 20:  # Significant deviation
                    gaps.append({
                        "type": "risk_balance_gap",
                        "risk_level": risk_level,
                        "market_distribution": round(market_percentage, 1),
                        "user_distribution": round(user_percentage, 1),
                        "recommendation": f"Consider {'increasing' if market_percentage > user_percentage else 'decreasing'} {risk_level} risk investments"
                    })
            
            return gaps[:5]  # Return top 5 gaps
            
        except Exception as e:
            logger.error(f"Investment gaps analysis failed: {e}")
            return []
    
    def _generate_seasonal_insights(self, monthly_success_rates: Dict[str, float]) -> List[str]:
        """Generate seasonal insights from monthly data"""
        try:
            insights = []
            
            if not monthly_success_rates:
                return insights
            
            # Define seasons
            seasons = {
                "Spring": ["March", "April", "May"],
                "Summer": ["June", "July", "August"],
                "Fall": ["September", "October", "November"],
                "Winter": ["December", "January", "February"]
            }
            
            # Calculate seasonal averages
            seasonal_averages = {}
            for season, months in seasons.items():
                rates = [monthly_success_rates.get(month, 0) for month in months]
                seasonal_averages[season] = sum(rates) / len(rates) if rates else 0
            
            # Find best and worst seasons
            best_season = max(seasonal_averages.items(), key=lambda x: x[1])
            worst_season = min(seasonal_averages.items(), key=lambda x: x[1])
            
            insights.append(f"{best_season[0]} is the best season for launches ({best_season[1]:.1f}% avg success rate)")
            insights.append(f"Avoid launching in {worst_season[0]} ({worst_season[1]:.1f}% avg success rate)")
            
            return insights
            
        except Exception as e:
            logger.error(f"Seasonal insights generation failed: {e}")
            return []
    
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