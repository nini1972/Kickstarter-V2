"""
💰 Investment Service
Business logic for investment tracking and portfolio management
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid

from models.investments import (
    Investment, InvestmentCreate, InvestmentUpdate, InvestmentResponse,
    InvestmentFilters, PortfolioStats, PortfolioAnalytics
)
from services.cache_service import cache_service

logger = logging.getLogger(__name__)

class InvestmentService:
    """Service layer for investment management operations"""
    
    def __init__(self, database):
        self.db = database
        self.collection = database.investments
        self.projects_collection = database.projects
    
    async def create_investment(self, investment_data: InvestmentCreate, user_id: Optional[str] = None) -> Investment:
        """Create a new investment record"""
        try:
            # Create investment instance
            investment = Investment(
                **investment_data.model_dump(),
                user_id=user_id,
                id=str(uuid.uuid4())
            )
            
            # Save to database
            investment_dict = investment.model_dump()
            result = await self.collection.insert_one(investment_dict)
            
            if not result.inserted_id:
                raise Exception("Failed to insert investment into database")
            
            # Invalidate relevant caches
            await self._invalidate_portfolio_cache(user_id)
            
            logger.info(f"✅ Investment created: {investment.project_name} - ${investment.amount}")
            return investment
            
        except Exception as e:
            logger.error(f"❌ Failed to create investment: {e}")
            raise
    
    async def get_investment(self, investment_id: str) -> Optional[Investment]:
        """Get investment by ID"""
        try:
            investment_data = await self.collection.find_one({"id": investment_id})
            if not investment_data:
                return None
            
            return Investment(**investment_data)
            
        except Exception as e:
            logger.error(f"❌ Failed to get investment {investment_id}: {e}")
            return None
    
    async def update_investment(self, investment_id: str, update_data: InvestmentUpdate, user_id: Optional[str] = None) -> Optional[Investment]:
        """Update investment record"""
        try:
            # Build update dict
            update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
            update_dict["updated_at"] = datetime.utcnow()
            
            # Update in database
            result = await self.collection.update_one(
                {"id": investment_id},
                {"$set": update_dict}
            )
            
            if result.matched_count == 0:
                return None
            
            # Invalidate caches
            await self._invalidate_portfolio_cache(user_id)
            
            # Return updated investment
            return await self.get_investment(investment_id)
            
        except Exception as e:
            logger.error(f"❌ Failed to update investment {investment_id}: {e}")
            return None
    
    async def delete_investment(self, investment_id: str, user_id: Optional[str] = None) -> bool:
        """Delete investment record"""
        try:
            result = await self.collection.delete_one({"id": investment_id})
            
            if result.deleted_count > 0:
                # Invalidate caches
                await self._invalidate_portfolio_cache(user_id)
                logger.info(f"✅ Investment deleted: {investment_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to delete investment {investment_id}: {e}")
            return False
    
    async def list_investments(self, filters: InvestmentFilters, user_id: Optional[str] = None) -> List[Investment]:
        """List investments with filtering and pagination"""
        try:
            # Build query
            query = self._build_query(filters, user_id)
            
            # Build sort
            sort_field = filters.sort_by
            sort_direction = -1 if filters.sort_order == "desc" else 1
            
            # Calculate pagination
            skip = (filters.page - 1) * filters.page_size
            
            # Execute query
            cursor = self.collection.find(query).sort(sort_field, sort_direction).skip(skip).limit(filters.page_size)
            investments_data = await cursor.to_list(length=None)
            
            # Convert to models
            investments = [Investment(**data) for data in investments_data]
            
            return investments
            
        except Exception as e:
            logger.error(f"❌ Failed to list investments: {e}")
            return []
    
    async def get_portfolio_stats(self, user_id: Optional[str] = None) -> PortfolioStats:
        """Get comprehensive portfolio statistics"""
        try:
            # Check cache
            cache_key = f"portfolio_stats_{user_id or 'all'}"
            cached_stats = await cache_service.get(cache_key)
            if cached_stats:
                return PortfolioStats(**cached_stats)
            
            # Build query
            query = {"user_id": user_id} if user_id else {}
            
            # Get all investments
            investments_data = await self.collection.find(query).to_list(length=None)
            
            if not investments_data:
                return self._empty_portfolio_stats()
            
            investments = [Investment(**data) for data in investments_data]
            
            # Calculate basic statistics
            total_investments = len(investments)
            total_invested = sum(inv.amount + inv.fees for inv in investments)
            total_current_value = sum(inv.current_value or inv.amount for inv in investments)
            total_roi = total_current_value - total_invested
            total_roi_percentage = (total_roi / total_invested * 100) if total_invested > 0 else 0
            
            # Count by status
            active_investments = sum(1 for inv in investments if inv.status == "active")
            delivered_investments = sum(1 for inv in investments if inv.delivery_status == "delivered")
            overdue_investments = sum(1 for inv in investments if inv.is_overdue())
            profitable_investments = sum(1 for inv in investments if inv.is_profitable())
            
            # Calculate averages and extremes
            average_investment = total_invested / total_investments if total_investments > 0 else 0
            largest_investment = max(inv.amount for inv in investments) if investments else 0
            
            # Find best and worst performing investments
            best_performing = max(investments, key=lambda x: x.roi_percentage or 0, default=None)
            worst_performing = min(investments, key=lambda x: x.roi_percentage or 0, default=None)
            
            # Distribution statistics
            investment_by_type = self._calculate_distribution(investments, "investment_type")
            investment_by_status = self._calculate_distribution(investments, "status")
            investment_by_risk = self._calculate_distribution(investments, "risk_rating", default="medium")
            
            # Monthly trend
            monthly_trend = await self._calculate_monthly_trend(investments)
            
            stats = PortfolioStats(
                total_investments=total_investments,
                total_invested=total_invested,
                total_current_value=total_current_value,
                total_roi=total_roi,
                total_roi_percentage=total_roi_percentage,
                active_investments=active_investments,
                delivered_investments=delivered_investments,
                overdue_investments=overdue_investments,
                profitable_investments=profitable_investments,
                average_investment=average_investment,
                largest_investment=largest_investment,
                best_performing_investment=self._investment_to_dict(best_performing) if best_performing else None,
                worst_performing_investment=self._investment_to_dict(worst_performing) if worst_performing else None,
                investment_by_type=investment_by_type,
                investment_by_status=investment_by_status,
                investment_by_risk=investment_by_risk,
                monthly_investment_trend=monthly_trend
            )
            
            # Cache for 30 minutes
            await cache_service.set(cache_key, stats.model_dump(), 1800)
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get portfolio stats: {e}")
            return self._empty_portfolio_stats()
    
    async def get_portfolio_analytics(self, user_id: Optional[str] = None) -> PortfolioAnalytics:
        """Get advanced portfolio analytics"""
        try:
            # Check cache
            cache_key = f"portfolio_analytics_{user_id or 'all'}"
            cached_analytics = await cache_service.get(cache_key)
            if cached_analytics:
                return PortfolioAnalytics(**cached_analytics)
            
            # Get investments and projects data
            query = {"user_id": user_id} if user_id else {}
            investments_data = await self.collection.find(query).to_list(length=None)
            
            if not investments_data:
                return self._empty_portfolio_analytics()
            
            investments = [Investment(**data) for data in investments_data]
            
            # Calculate advanced metrics
            diversification_score = await self._calculate_diversification_score(investments)
            risk_score = self._calculate_risk_score(investments)
            performance_score = self._calculate_performance_score(investments)
            recommended_actions = await self._generate_recommendations(investments)
            risk_distribution = self._calculate_risk_distribution(investments)
            category_exposure = await self._calculate_category_exposure(investments)
            temporal_distribution = self._calculate_temporal_distribution(investments)
            projected_returns = self._calculate_projected_returns(investments)
            
            analytics = PortfolioAnalytics(
                diversification_score=diversification_score,
                risk_score=risk_score,
                performance_score=performance_score,
                recommended_actions=recommended_actions,
                risk_distribution=risk_distribution,
                category_exposure=category_exposure,
                temporal_distribution=temporal_distribution,
                projected_returns=projected_returns
            )
            
            # Cache for 1 hour
            await cache_service.set(cache_key, analytics.model_dump(), 3600)
            
            return analytics
            
        except Exception as e:
            logger.error(f"❌ Failed to get portfolio analytics: {e}")
            return self._empty_portfolio_analytics()
    
    async def get_investment_performance(self, investment_id: str) -> Dict[str, Any]:
        """Get detailed performance metrics for a specific investment"""
        try:
            investment = await self.get_investment(investment_id)
            if not investment:
                return {}
            
            # Get project data for additional context
            project_data = await self.projects_collection.find_one({"id": investment.project_id})
            
            performance = {
                "investment_id": investment.id,
                "project_name": investment.project_name,
                "amount_invested": investment.amount,
                "fees_paid": investment.fees,
                "total_cost": investment.total_cost or (investment.amount + investment.fees),
                "current_value": investment.current_value,
                "roi_amount": (investment.current_value - investment.amount) if investment.current_value else 0,
                "roi_percentage": investment.roi_percentage,
                "days_since_investment": investment.days_since_investment(),
                "is_profitable": investment.is_profitable(),
                "is_overdue": investment.is_overdue(),
                "risk_rating": investment.risk_rating,
                "confidence_level": investment.confidence_level,
                "status": investment.status,
                "delivery_status": investment.delivery_status
            }
            
            # Add project context if available
            if project_data:
                project_performance = {
                    "project_status": project_data.get("status"),
                    "project_funding_percentage": (
                        project_data.get("pledged_amount", 0) / project_data.get("goal_amount", 1) * 100
                        if project_data.get("goal_amount", 0) > 0 else 0
                    ),
                    "project_success_probability": project_data.get("ai_analysis", {}).get("success_probability"),
                    "project_risk_level": project_data.get("risk_level")
                }
                performance.update(project_performance)
            
            return performance
            
        except Exception as e:
            logger.error(f"❌ Failed to get investment performance for {investment_id}: {e}")
            return {}
    
    # Helper methods
    
    def _build_query(self, filters: InvestmentFilters, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Build MongoDB query from filters"""
        query = {}
        
        # User filter
        if user_id:
            query["user_id"] = user_id
        
        # Project filters
        if filters.project_id:
            query["project_id"] = filters.project_id
        
        if filters.project_name:
            query["project_name"] = {"$regex": filters.project_name, "$options": "i"}
        
        # Type and status filters
        if filters.investment_type:
            query["investment_type"] = filters.investment_type
        
        if filters.status:
            query["status"] = filters.status
        
        if filters.delivery_status:
            query["delivery_status"] = filters.delivery_status
        
        if filters.risk_rating:
            query["risk_rating"] = filters.risk_rating
        
        # Amount range
        if filters.min_amount is not None or filters.max_amount is not None:
            amount_query = {}
            if filters.min_amount is not None:
                amount_query["$gte"] = filters.min_amount
            if filters.max_amount is not None:
                amount_query["$lte"] = filters.max_amount
            query["amount"] = amount_query
        
        # ROI range
        if filters.min_roi is not None or filters.max_roi is not None:
            roi_query = {}
            if filters.min_roi is not None:
                roi_query["$gte"] = filters.min_roi
            if filters.max_roi is not None:
                roi_query["$lte"] = filters.max_roi
            query["roi_percentage"] = roi_query
        
        # Date range
        if filters.date_from or filters.date_to:
            date_query = {}
            if filters.date_from:
                date_query["$gte"] = filters.date_from
            if filters.date_to:
                date_query["$lte"] = filters.date_to
            query["investment_date"] = date_query
        
        # Tags filter
        if filters.tags:
            query["tags"] = {"$in": filters.tags}
        
        return query
    
    def _calculate_distribution(self, investments: List[Investment], field: str, default: Optional[str] = None) -> Dict[str, int]:
        """Calculate distribution for a specific field"""
        distribution = {}
        for investment in investments:
            value = getattr(investment, field, default) or default or "unknown"
            distribution[value] = distribution.get(value, 0) + 1
        return distribution
    
    async def _calculate_monthly_trend(self, investments: List[Investment]) -> List[Dict[str, Any]]:
        """Calculate monthly investment trend"""
        monthly_data = {}
        
        for investment in investments:
            month_key = investment.investment_date.strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {"month": month_key, "count": 0, "amount": 0}
            
            monthly_data[month_key]["count"] += 1
            monthly_data[month_key]["amount"] += investment.amount
        
        return sorted(monthly_data.values(), key=lambda x: x["month"])
    
    def _investment_to_dict(self, investment: Investment) -> Dict[str, Any]:
        """Convert investment to dictionary for stats"""
        return {
            "id": investment.id,
            "project_name": investment.project_name,
            "amount": investment.amount,
            "roi_percentage": investment.roi_percentage,
            "investment_date": investment.investment_date.isoformat()
        }
    
    async def _invalidate_portfolio_cache(self, user_id: Optional[str]):
        """Invalidate all portfolio-related cache entries"""
        patterns = [
            f"portfolio_stats_{user_id or 'all'}",
            f"portfolio_analytics_{user_id or 'all'}",
            "recommendations_*"  # Investment changes might affect recommendations
        ]
        
        for pattern in patterns:
            await cache_service.delete_pattern(pattern)
    
    def _empty_portfolio_stats(self) -> PortfolioStats:
        """Return empty portfolio stats"""
        return PortfolioStats(
            total_investments=0, total_invested=0.0, total_current_value=0.0,
            total_roi=0.0, total_roi_percentage=0.0, active_investments=0,
            delivered_investments=0, overdue_investments=0, profitable_investments=0,
            average_investment=0.0, largest_investment=0.0,
            best_performing_investment=None, worst_performing_investment=None,
            investment_by_type={}, investment_by_status={}, investment_by_risk={},
            monthly_investment_trend=[]
        )
    
    def _empty_portfolio_analytics(self) -> PortfolioAnalytics:
        """Return empty portfolio analytics"""
        return PortfolioAnalytics(
            diversification_score=0.0, risk_score=0.0, performance_score=0.0,
            recommended_actions=[], risk_distribution={}, category_exposure={},
            temporal_distribution={}, projected_returns={}
        )
    
    # Advanced analytics calculation methods
    
    async def _calculate_diversification_score(self, investments: List[Investment]) -> float:
        """Calculate portfolio diversification score (0-100)"""
        if not investments:
            return 0.0
        
        # Get project categories for investments
        project_ids = [inv.project_id for inv in investments]
        projects_data = await self.projects_collection.find(
            {"id": {"$in": project_ids}}, {"id": 1, "category": 1}
        ).to_list(length=None)
        
        project_categories = {proj["id"]: proj.get("category", "unknown") for proj in projects_data}
        
        # Calculate category distribution
        category_amounts = {}
        total_amount = sum(inv.amount for inv in investments)
        
        for investment in investments:
            category = project_categories.get(investment.project_id, "unknown")
            category_amounts[category] = category_amounts.get(category, 0) + investment.amount
        
        # Calculate Herfindahl-Hirschman Index (HHI) for diversification
        if total_amount == 0:
            return 0.0
        
        hhi = sum((amount / total_amount) ** 2 for amount in category_amounts.values())
        
        # Convert to diversification score (inverse of concentration)
        max_hhi = 1.0  # Completely concentrated
        diversification_score = (1 - hhi) * 100
        
        return min(max(diversification_score, 0), 100)
    
    def _calculate_risk_score(self, investments: List[Investment]) -> float:
        """Calculate overall portfolio risk score (0-100)"""
        if not investments:
            return 50.0  # Neutral risk
        
        risk_weights = {"low": 25, "medium": 50, "high": 75}
        total_amount = sum(inv.amount for inv in investments)
        
        if total_amount == 0:
            return 50.0
        
        weighted_risk = sum(
            risk_weights.get(inv.risk_rating or "medium", 50) * inv.amount
            for inv in investments
        )
        
        return weighted_risk / total_amount
    
    def _calculate_performance_score(self, investments: List[Investment]) -> float:
        """Calculate portfolio performance score (0-100)"""
        if not investments:
            return 50.0  # Neutral performance
        
        profitable_count = sum(1 for inv in investments if inv.is_profitable())
        delivered_count = sum(1 for inv in investments if inv.delivery_status == "delivered")
        total_count = len(investments)
        
        # Base score from profitability and delivery
        base_score = ((profitable_count + delivered_count) / (total_count * 2)) * 100
        
        # Adjust for average ROI
        avg_roi = sum(inv.roi_percentage or 0 for inv in investments) / total_count
        roi_bonus = min(max(avg_roi, -50), 50)  # Cap ROI impact
        
        performance_score = base_score + roi_bonus
        return min(max(performance_score, 0), 100)
    
    async def _generate_recommendations(self, investments: List[Investment]) -> List[str]:
        """Generate actionable recommendations for portfolio"""
        recommendations = []
        
        if not investments:
            return ["Start building your investment portfolio"]
        
        # Check diversification
        diversification = await self._calculate_diversification_score(investments)
        if diversification < 30:
            recommendations.append("Consider diversifying across more project categories")
        
        # Check risk distribution
        high_risk_count = sum(1 for inv in investments if inv.risk_rating == "high")
        if high_risk_count / len(investments) > 0.5:
            recommendations.append("Consider reducing exposure to high-risk investments")
        
        # Check overdue investments
        overdue_count = sum(1 for inv in investments if inv.is_overdue())
        if overdue_count > 0:
            recommendations.append(f"Follow up on {overdue_count} overdue investments")
        
        # Check performance
        unprofitable_count = sum(1 for inv in investments if inv.roi_percentage and inv.roi_percentage < -20)
        if unprofitable_count > 0:
            recommendations.append("Review underperforming investments for lessons learned")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _calculate_risk_distribution(self, investments: List[Investment]) -> Dict[str, float]:
        """Calculate risk distribution as percentages"""
        if not investments:
            return {}
        
        total_amount = sum(inv.amount for inv in investments)
        if total_amount == 0:
            return {}
        
        risk_amounts = {}
        for investment in investments:
            risk = investment.risk_rating or "medium"
            risk_amounts[risk] = risk_amounts.get(risk, 0) + investment.amount
        
        return {risk: (amount / total_amount) * 100 for risk, amount in risk_amounts.items()}
    
    async def _calculate_category_exposure(self, investments: List[Investment]) -> Dict[str, float]:
        """Calculate category exposure as percentages"""
        if not investments:
            return {}
        
        # Get project categories
        project_ids = [inv.project_id for inv in investments]
        projects_data = await self.projects_collection.find(
            {"id": {"$in": project_ids}}, {"id": 1, "category": 1}
        ).to_list(length=None)
        
        project_categories = {proj["id"]: proj.get("category", "unknown") for proj in projects_data}
        
        total_amount = sum(inv.amount for inv in investments)
        if total_amount == 0:
            return {}
        
        category_amounts = {}
        for investment in investments:
            category = project_categories.get(investment.project_id, "unknown")
            category_amounts[category] = category_amounts.get(category, 0) + investment.amount
        
        return {cat: (amount / total_amount) * 100 for cat, amount in category_amounts.items()}
    
    def _calculate_temporal_distribution(self, investments: List[Investment]) -> Dict[str, float]:
        """Calculate temporal distribution of investments"""
        if not investments:
            return {}
        
        # Group by quarters
        quarters = {}
        total_amount = sum(inv.amount for inv in investments)
        
        for investment in investments:
            quarter = f"Q{((investment.investment_date.month - 1) // 3) + 1} {investment.investment_date.year}"
            quarters[quarter] = quarters.get(quarter, 0) + investment.amount
        
        if total_amount == 0:
            return {}
        
        return {quarter: (amount / total_amount) * 100 for quarter, amount in quarters.items()}
    
    def _calculate_projected_returns(self, investments: List[Investment]) -> Dict[str, float]:
        """Calculate projected returns based on current performance"""
        if not investments:
            return {}
        
        # Simple projections based on current ROI trends
        current_roi = sum(inv.roi_percentage or 0 for inv in investments) / len(investments)
        
        return {
            "3_month": current_roi * 0.25,
            "6_month": current_roi * 0.5,
            "1_year": current_roi,
            "2_year": current_roi * 1.5
        }