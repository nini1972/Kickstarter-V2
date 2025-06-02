"""
🚀 Database Query Optimization Service
MongoDB aggregation pipelines and streaming for enhanced performance
"""

import logging
from typing import List, Dict, Any, Optional, AsyncGenerator, Tuple
from datetime import datetime, timedelta
import asyncio
from motor.motor_asyncio import AsyncIOMotorCollection

logger = logging.getLogger(__name__)

class DatabaseOptimizationService:
    """Service for optimized database queries with streaming and aggregation pipelines"""
    
    def __init__(self, database):
        self.db = database
        self.projects_collection = database.projects
        self.investments_collection = database.investments
        self.users_collection = database.users
        
        # Performance monitoring
        self.query_stats = {
            "total_queries": 0,
            "optimized_queries": 0,
            "streaming_queries": 0,
            "aggregation_pipelines": 0,
            "performance_improvements": []
        }
    
    async def get_optimized_dashboard_analytics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get dashboard analytics using optimized aggregation pipeline"""
        try:
            logger.info("🚀 Running optimized dashboard analytics...")
            start_time = datetime.utcnow()
            
            # Build base match query
            match_query = {"user_id": user_id} if user_id else {}
            
            # Single aggregation pipeline for all project analytics
            project_pipeline = [
                {"$match": match_query},
                {"$group": {
                    "_id": None,
                    "total_projects": {"$sum": 1},
                    "successful_projects": {"$sum": {"$cond": [{"$eq": ["$status", "successful"]}, 1, 0]}},
                    "failed_projects": {"$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}},
                    "live_projects": {"$sum": {"$cond": [{"$eq": ["$status", "live"]}, 1, 0]}},
                    "total_funding": {"$sum": "$pledged_amount"},
                    "avg_funding": {"$avg": "$pledged_amount"},
                    "total_backers": {"$sum": "$backers_count"},
                    "total_goal_amount": {"$sum": "$goal_amount"},
                    
                    # Risk distribution
                    "low_risk_count": {"$sum": {"$cond": [{"$eq": ["$risk_level", "low"]}, 1, 0]}},
                    "medium_risk_count": {"$sum": {"$cond": [{"$eq": ["$risk_level", "medium"]}, 1, 0]}},
                    "high_risk_count": {"$sum": {"$cond": [{"$eq": ["$risk_level", "high"]}, 1, 0]}},
                    
                    # Category distribution (top 5)
                    "categories": {"$push": "$category"},
                    
                    # Funding velocity data
                    "funding_velocities": {"$push": {
                        "$divide": ["$pledged_amount", {"$max": [1, {"$dateDiff": {"startDate": "$created_at", "endDate": "$$NOW", "unit": "day"}}]}]
                    }}
                }},
                {"$addFields": {
                    "success_rate": {"$multiply": [{"$divide": ["$successful_projects", {"$max": [1, "$total_projects"]}]}, 100]},
                    "funding_percentage": {"$multiply": [{"$divide": ["$total_funding", {"$max": [1, "$total_goal_amount"]}]}, 100]},
                    "avg_funding_velocity": {"$avg": "$funding_velocities"}
                }}
            ]
            
            # Single aggregation pipeline for investment analytics
            investment_pipeline = [
                {"$match": match_query},
                {"$group": {
                    "_id": None,
                    "total_investments": {"$sum": 1},
                    "total_invested": {"$sum": "$amount"},
                    "total_current_value": {"$sum": {"$ifNull": ["$current_value", "$amount"]}},
                    "delivered_count": {"$sum": {"$cond": [{"$eq": ["$delivery_status", "delivered"]}, 1, 0]}},
                    "pending_count": {"$sum": {"$cond": [{"$eq": ["$delivery_status", "pending"]}, 1, 0]}},
                    "in_production_count": {"$sum": {"$cond": [{"$eq": ["$delivery_status", "in_production"]}, 1, 0]}},
                    "profitable_count": {"$sum": {"$cond": [{"$gt": [{"$ifNull": ["$current_value", "$amount"]}, "$amount"]}, 1, 0]}}
                }},
                {"$addFields": {
                    "avg_investment": {"$divide": ["$total_invested", {"$max": [1, "$total_investments"]}]},
                    "overall_roi": {"$multiply": [
                        {"$divide": [
                            {"$subtract": ["$total_current_value", "$total_invested"]},
                            {"$max": [1, "$total_invested"]}
                        ]}, 100
                    ]},
                    "delivery_rate": {"$multiply": [{"$divide": ["$delivered_count", {"$max": [1, "$total_investments"]}]}, 100]}
                }}
            ]
            
            # Execute pipelines in parallel
            project_results, investment_results = await asyncio.gather(
                self.projects_collection.aggregate(project_pipeline).to_list(length=1),
                self.investments_collection.aggregate(investment_pipeline).to_list(length=1),
                return_exceptions=True
            )
            
            # Process results
            project_data = project_results[0] if project_results and not isinstance(project_results, Exception) else {}
            investment_data = investment_results[0] if investment_results and not isinstance(investment_results, Exception) else {}
            
            # Calculate category distribution from aggregated data
            categories = project_data.get("categories", [])
            category_distribution = {}
            for category in categories:
                category_distribution[category] = category_distribution.get(category, 0) + 1
            
            # Sort and limit to top 5 categories
            top_categories = dict(sorted(category_distribution.items(), key=lambda x: x[1], reverse=True)[:5])
            
            # Build comprehensive analytics response
            analytics = {
                "overview": {
                    "total_projects": project_data.get("total_projects", 0),
                    "total_investments": investment_data.get("total_investments", 0),
                    "total_invested": round(investment_data.get("total_invested", 0.0), 2),
                    "total_current_value": round(investment_data.get("total_current_value", 0.0), 2),
                    "overall_roi": round(investment_data.get("overall_roi", 0.0), 2),
                    "success_rate": round(project_data.get("success_rate", 0.0), 2),
                    "avg_investment": round(investment_data.get("avg_investment", 0.0), 2),
                    "delivery_rate": round(investment_data.get("delivery_rate", 0.0), 2)
                },
                "projects": {
                    "total_projects": project_data.get("total_projects", 0),
                    "successful_projects": project_data.get("successful_projects", 0),
                    "failed_projects": project_data.get("failed_projects", 0),
                    "live_projects": project_data.get("live_projects", 0),
                    "success_rate": round(project_data.get("success_rate", 0.0), 2),
                    "total_funding": round(project_data.get("total_funding", 0.0), 2),
                    "avg_funding": round(project_data.get("avg_funding", 0.0), 2),
                    "avg_funding_velocity": round(project_data.get("avg_funding_velocity", 0.0), 2),
                    "category_distribution": top_categories,
                    "risk_distribution": {
                        "low": project_data.get("low_risk_count", 0),
                        "medium": project_data.get("medium_risk_count", 0),
                        "high": project_data.get("high_risk_count", 0)
                    }
                },
                "investments": {
                    "total_investments": investment_data.get("total_investments", 0),
                    "total_invested": round(investment_data.get("total_invested", 0.0), 2),
                    "total_current_value": round(investment_data.get("total_current_value", 0.0), 2),
                    "overall_roi": round(investment_data.get("overall_roi", 0.0), 2),
                    "avg_investment": round(investment_data.get("avg_investment", 0.0), 2),
                    "profitable_investments": investment_data.get("profitable_count", 0),
                    "delivery_status": {
                        "delivered": investment_data.get("delivered_count", 0),
                        "pending": investment_data.get("pending_count", 0),
                        "in_production": investment_data.get("in_production_count", 0)
                    }
                },
                "performance": {
                    "optimization_enabled": True,
                    "query_method": "aggregation_pipeline",
                    "processing_time": (datetime.utcnow() - start_time).total_seconds()
                }
            }
            
            # Record performance improvement
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self._record_performance_improvement("dashboard_analytics", processing_time, "aggregation_pipeline")
            
            logger.info(f"✅ Optimized dashboard analytics completed in {processing_time:.3f}s")
            return analytics
            
        except Exception as e:
            logger.error(f"❌ Optimized dashboard analytics failed: {e}")
            return {}
    
    async def stream_market_insights(self, user_id: Optional[str] = None, batch_size: int = 1000) -> Dict[str, Any]:
        """Stream market insights processing for large datasets"""
        try:
            logger.info("🌊 Streaming market insights analysis...")
            start_time = datetime.utcnow()
            
            # Use streaming aggregation for category performance
            category_performance = await self._stream_category_performance(batch_size)
            
            # Use streaming for competitive landscape
            competitive_landscape = await self._stream_competitive_landscape(batch_size)
            
            # Use optimized aggregation for success factors
            success_factors = await self._get_optimized_success_factors()
            
            # Use aggregation pipeline for timing insights
            timing_insights = await self._get_optimized_timing_insights()
            
            # Parallel processing for efficiency
            emerging_trends, market_opportunities = await asyncio.gather(
                self._get_optimized_emerging_trends(),
                self._get_optimized_market_opportunities(user_id),
                return_exceptions=True
            )
            
            if isinstance(emerging_trends, Exception):
                emerging_trends = []
            if isinstance(market_opportunities, Exception):
                market_opportunities = []
            
            insights = {
                "category_performance": category_performance,
                "competitive_landscape": competitive_landscape,
                "success_factors": success_factors,
                "timing_insights": timing_insights,
                "emerging_trends": emerging_trends,
                "market_opportunities": market_opportunities,
                "optimization_info": {
                    "streaming_enabled": True,
                    "batch_size": batch_size,
                    "processing_time": (datetime.utcnow() - start_time).total_seconds(),
                    "method": "streaming_aggregation"
                }
            }
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self._record_performance_improvement("market_insights_streaming", processing_time, "streaming_aggregation")
            
            logger.info(f"✅ Streaming market insights completed in {processing_time:.3f}s")
            return insights
            
        except Exception as e:
            logger.error(f"❌ Streaming market insights failed: {e}")
            return {}
    
    async def _stream_category_performance(self, batch_size: int = 1000) -> Dict[str, Any]:
        """Stream category performance analysis to handle large datasets"""
        try:
            # Optimized aggregation pipeline for category performance
            pipeline = [
                {"$group": {
                    "_id": "$category",
                    "total_projects": {"$sum": 1},
                    "successful_projects": {"$sum": {"$cond": [{"$eq": ["$status", "successful"]}, 1, 0]}},
                    "total_funding": {"$sum": "$pledged_amount"},
                    "avg_funding": {"$avg": "$pledged_amount"},
                    "avg_goal": {"$avg": "$goal_amount"},
                    "total_backers": {"$sum": "$backers_count"}
                }},
                {"$addFields": {
                    "success_rate": {"$multiply": [{"$divide": ["$successful_projects", {"$max": [1, "$total_projects"]}]}, 100]},
                    "avg_funding_per_project": "$avg_funding"
                }},
                {"$sort": {"success_rate": -1}},
                {"$limit": 20}  # Top 20 categories
            ]
            
            category_stats = {}
            async for doc in self.projects_collection.aggregate(pipeline):
                category = doc["_id"]
                category_stats[category] = {
                    "total_projects": doc["total_projects"],
                    "successful_projects": doc["successful_projects"],
                    "success_rate": round(doc["success_rate"], 2),
                    "total_funding": round(doc["total_funding"], 2),
                    "avg_funding_per_project": round(doc["avg_funding_per_project"], 2),
                    "avg_goal": round(doc["avg_goal"], 2),
                    "total_backers": doc["total_backers"]
                }
            
            # Sort by success rate for top performing categories
            top_performing = dict(sorted(category_stats.items(), key=lambda x: x[1]["success_rate"], reverse=True)[:10])
            
            return {
                "top_performing_categories": top_performing,
                "total_categories_analyzed": len(category_stats),
                "optimization_method": "streaming_aggregation"
            }
            
        except Exception as e:
            logger.error(f"Category performance streaming failed: {e}")
            return {}
    
    async def _stream_competitive_landscape(self, batch_size: int = 1000) -> Dict[str, Any]:
        """Stream competitive landscape analysis"""
        try:
            # Market concentration analysis with aggregation
            pipeline = [
                {"$group": {
                    "_id": "$category",
                    "category_funding": {"$sum": "$pledged_amount"},
                    "project_count": {"$sum": 1},
                    "avg_funding": {"$avg": "$pledged_amount"}
                }},
                {"$sort": {"category_funding": -1}},
                {"$group": {
                    "_id": None,
                    "categories": {"$push": {
                        "category": "$_id",
                        "funding": "$category_funding",
                        "projects": "$project_count",
                        "avg_funding": "$avg_funding"
                    }},
                    "total_market_funding": {"$sum": "$category_funding"},
                    "total_categories": {"$sum": 1}
                }}
            ]
            
            result = await self.projects_collection.aggregate(pipeline).to_list(length=1)
            if not result:
                return {}
            
            data = result[0]
            total_funding = data["total_market_funding"]
            categories = data["categories"]
            
            # Calculate market share and HHI index
            market_leaders = {}
            hhi_index = 0
            
            for cat_data in categories[:10]:  # Top 10 categories
                category = cat_data["category"]
                funding = cat_data["funding"]
                market_share = (funding / total_funding * 100) if total_funding > 0 else 0
                
                market_leaders[category] = {
                    "market_share": round(market_share, 2),
                    "total_funding": round(funding, 2),
                    "project_count": cat_data["projects"],
                    "avg_funding": round(cat_data["avg_funding"], 2)
                }
                
                # Calculate HHI contribution
                hhi_index += (market_share / 100) ** 2
            
            return {
                "market_leaders": market_leaders,
                "market_concentration": {
                    "total_funding": round(total_funding, 2),
                    "total_categories": data["total_categories"],
                    "hhi_index": round(hhi_index, 4)  # Herfindahl-Hirschman Index
                },
                "optimization_method": "aggregation_pipeline"
            }
            
        except Exception as e:
            logger.error(f"Competitive landscape streaming failed: {e}")
            return {}
    
    async def _get_optimized_success_factors(self) -> List[Dict[str, Any]]:
        """Get success factors using optimized aggregation"""
        try:
            # Single aggregation pipeline for success factors analysis
            pipeline = [
                {"$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "avg_goal": {"$avg": "$goal_amount"},
                    "avg_funding": {"$avg": "$pledged_amount"},
                    "avg_duration": {"$avg": {"$dateDiff": {"startDate": "$created_at", "endDate": "$deadline", "unit": "day"}}},
                    "categories": {"$push": "$category"}
                }}
            ]
            
            results = await self.projects_collection.aggregate(pipeline).to_list(length=None)
            
            factors = []
            successful_data = next((r for r in results if r["_id"] == "successful"), None)
            failed_data = next((r for r in results if r["_id"] == "failed"), None)
            
            if successful_data and failed_data:
                # Goal amount factor
                factors.append({
                    "factor": "optimal_goal_amount",
                    "successful_avg": round(successful_data["avg_goal"], 2),
                    "failed_avg": round(failed_data["avg_goal"], 2),
                    "insight": f"Successful projects average ${successful_data['avg_goal']:,.0f} goals vs ${failed_data['avg_goal']:,.0f} for failed"
                })
                
                # Duration factor
                if successful_data.get("avg_duration") and failed_data.get("avg_duration"):
                    factors.append({
                        "factor": "campaign_duration",
                        "successful_avg": round(successful_data["avg_duration"], 0),
                        "failed_avg": round(failed_data["avg_duration"], 0),
                        "insight": f"Successful campaigns average {successful_data['avg_duration']:.0f} days vs {failed_data['avg_duration']:.0f} days"
                    })
            
            return factors
            
        except Exception as e:
            logger.error(f"Success factors optimization failed: {e}")
            return []
    
    async def _get_optimized_timing_insights(self) -> Dict[str, Any]:
        """Get timing insights using aggregation pipeline"""
        try:
            # Monthly success rate analysis
            pipeline = [
                {"$addFields": {
                    "launch_month": {"$month": "$created_at"}
                }},
                {"$group": {
                    "_id": "$launch_month",
                    "total_projects": {"$sum": 1},
                    "successful_projects": {"$sum": {"$cond": [{"$eq": ["$status", "successful"]}, 1, 0]}}
                }},
                {"$addFields": {
                    "success_rate": {"$multiply": [{"$divide": ["$successful_projects", {"$max": [1, "$total_projects"]}]}, 100]}
                }},
                {"$sort": {"success_rate": -1}}
            ]
            
            monthly_data = await self.projects_collection.aggregate(pipeline).to_list(length=None)
            
            # Convert month numbers to names
            month_names = ["", "January", "February", "March", "April", "May", "June",
                          "July", "August", "September", "October", "November", "December"]
            
            monthly_success_rates = {}
            for data in monthly_data:
                month_name = month_names[data["_id"]]
                monthly_success_rates[month_name] = round(data["success_rate"], 1)
            
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
                "optimization_method": "aggregation_pipeline"
            }
            
        except Exception as e:
            logger.error(f"Timing insights optimization failed: {e}")
            return {}
    
    async def _get_optimized_emerging_trends(self) -> List[Dict[str, Any]]:
        """Get emerging trends using time-based aggregation"""
        try:
            # Compare recent vs older projects using aggregation
            six_months_ago = datetime.utcnow() - timedelta(days=180)
            
            pipeline = [
                {"$addFields": {
                    "is_recent": {"$gte": ["$created_at", six_months_ago]}
                }},
                {"$group": {
                    "_id": {
                        "category": "$category",
                        "is_recent": "$is_recent"
                    },
                    "count": {"$sum": 1},
                    "avg_funding": {"$avg": "$pledged_amount"}
                }},
                {"$group": {
                    "_id": "$_id.category",
                    "recent_count": {"$sum": {"$cond": ["$_id.is_recent", "$count", 0]}},
                    "older_count": {"$sum": {"$cond": [{"$not": "$_id.is_recent"}, "$count", 0]}}
                }},
                {"$addFields": {
                    "growth_rate": {
                        "$multiply": [
                            {"$divide": [
                                {"$subtract": ["$recent_count", "$older_count"]},
                                {"$max": [1, "$older_count"]}
                            ]}, 100
                        ]
                    }
                }},
                {"$match": {"growth_rate": {"$gt": 50}}},  # Significant growth
                {"$sort": {"growth_rate": -1}},
                {"$limit": 5}
            ]
            
            trends = []
            async for doc in self.projects_collection.aggregate(pipeline):
                trends.append({
                    "type": "category_growth",
                    "category": doc["_id"],
                    "growth_rate": round(doc["growth_rate"], 1),
                    "description": f"{doc['_id']} projects showing {doc['growth_rate']:.1f}% growth"
                })
            
            return trends
            
        except Exception as e:
            logger.error(f"Emerging trends optimization failed: {e}")
            return []
    
    async def _get_optimized_market_opportunities(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get market opportunities using optimized queries"""
        try:
            opportunities = []
            
            # Underserved categories with high success rates
            pipeline = [
                {"$group": {
                    "_id": "$category",
                    "project_count": {"$sum": 1},
                    "successful_count": {"$sum": {"$cond": [{"$eq": ["$status", "successful"]}, 1, 0]}},
                    "avg_funding": {"$avg": "$pledged_amount"}
                }},
                {"$addFields": {
                    "success_rate": {"$multiply": [{"$divide": ["$successful_count", {"$max": [1, "$project_count"]}]}, 100]}
                }},
                {"$match": {
                    "project_count": {"$lt": 100},  # Underserved (fewer projects)
                    "success_rate": {"$gt": 60}     # High success rate
                }},
                {"$sort": {"success_rate": -1}},
                {"$limit": 5}
            ]
            
            async for doc in self.projects_collection.aggregate(pipeline):
                opportunities.append({
                    "type": "underserved_category",
                    "category": doc["_id"],
                    "project_count": doc["project_count"],
                    "success_rate": round(doc["success_rate"], 1),
                    "avg_funding": round(doc["avg_funding"], 2),
                    "description": f"{doc['_id']} is underserved ({doc['project_count']} projects) with high success rate ({doc['success_rate']:.1f}%)"
                })
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Market opportunities optimization failed: {e}")
            return []
    
    async def get_streaming_project_list(self, query: Dict[str, Any], batch_size: int = 100) -> AsyncGenerator[List[Dict], None]:
        """Stream project list for large result sets"""
        try:
            cursor = self.projects_collection.find(query)
            batch = []
            
            async for document in cursor:
                batch.append(document)
                
                if len(batch) >= batch_size:
                    yield batch
                    batch = []
                    # Small delay to prevent overwhelming the system
                    await asyncio.sleep(0.01)
            
            # Yield remaining documents
            if batch:
                yield batch
            
            self._record_performance_improvement("streaming_project_list", 0, "streaming_cursor")
            
        except Exception as e:
            logger.error(f"Streaming project list failed: {e}")
            yield []
    
    def _record_performance_improvement(self, operation: str, processing_time: float, method: str):
        """Record performance improvement for monitoring"""
        try:
            self.query_stats["total_queries"] += 1
            if method in ["aggregation_pipeline", "streaming_aggregation", "streaming_cursor"]:
                self.query_stats["optimized_queries"] += 1
            
            if "streaming" in method:
                self.query_stats["streaming_queries"] += 1
            if "aggregation" in method:
                self.query_stats["aggregation_pipelines"] += 1
            
            improvement = {
                "operation": operation,
                "processing_time": processing_time,
                "method": method,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.query_stats["performance_improvements"].append(improvement)
            
            # Keep only last 100 improvements
            if len(self.query_stats["performance_improvements"]) > 100:
                self.query_stats["performance_improvements"] = self.query_stats["performance_improvements"][-100:]
            
        except Exception as e:
            logger.error(f"Failed to record performance improvement: {e}")
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get database optimization statistics"""
        total = self.query_stats["total_queries"]
        optimized = self.query_stats["optimized_queries"]
        optimization_rate = (optimized / total * 100) if total > 0 else 0
        
        recent_improvements = self.query_stats["performance_improvements"][-10:]
        avg_processing_time = sum(imp["processing_time"] for imp in recent_improvements) / len(recent_improvements) if recent_improvements else 0
        
        return {
            "total_queries": total,
            "optimized_queries": optimized,
            "optimization_rate": round(optimization_rate, 2),
            "streaming_queries": self.query_stats["streaming_queries"],
            "aggregation_pipelines": self.query_stats["aggregation_pipelines"],
            "avg_processing_time": round(avg_processing_time, 3),
            "recent_improvements": recent_improvements
        }


# Global optimization service instance
db_optimization_service = None

def initialize_db_optimization_service(database):
    """Initialize the database optimization service"""
    global db_optimization_service
    db_optimization_service = DatabaseOptimizationService(database)
    return db_optimization_service
