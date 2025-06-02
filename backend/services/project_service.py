"""
📊 Project Service
Business logic for project management with caching and AI integration
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from models.projects import (
    KickstarterProject, ProjectCreate, ProjectUpdate, ProjectResponse, 
    ProjectFilters, ProjectStats, BatchAnalyzeRequest
)
from services.ai_service import ai_service
from services.cache_service import cache_service

logger = logging.getLogger(__name__)

class ProjectService:
    """Service layer for project management operations"""
    
    def __init__(self, database):
        self.db = database
        self.collection = database.projects
    
    async def create_project(self, project_data: ProjectCreate, user_id: Optional[str] = None) -> KickstarterProject:
        """Create a new project with AI analysis"""
        try:
            # Create project instance
            project = KickstarterProject(
                **project_data.model_dump(),
                user_id=user_id,
                id=str(uuid.uuid4())
            )
            
            # Perform AI analysis
            ai_analysis = await ai_service.analyze_project(project)
            project.ai_analysis = ai_analysis
            project.risk_level = ai_analysis.get("risk_level", "medium")
            
            # Save to database
            project_dict = project.model_dump()
            result = await self.collection.insert_one(project_dict)
            
            if not result.inserted_id:
                raise Exception("Failed to insert project into database")
            
            # Cache the project
            await cache_service.cache_project(project.id, project_dict)
            
            logger.info(f"✅ Project created: {project.name} (ID: {project.id})")
            return project
            
        except Exception as e:
            logger.error(f"❌ Failed to create project: {e}")
            raise
    
    async def get_project(self, project_id: str) -> Optional[KickstarterProject]:
        """Get project by ID with caching"""
        try:
            # Check cache first
            cached_project = await cache_service.get_cached_project(project_id)
            if cached_project:
                return KickstarterProject(**cached_project)
            
            # Get from database
            project_data = await self.collection.find_one({"id": project_id})
            if not project_data:
                return None
            
            project = KickstarterProject(**project_data)
            
            # Cache for future requests
            await cache_service.cache_project(project_id, project_data)
            
            return project
            
        except Exception as e:
            logger.error(f"❌ Failed to get project {project_id}: {e}")
            return None
    
    async def update_project(self, project_id: str, update_data: ProjectUpdate, user_id: Optional[str] = None) -> Optional[KickstarterProject]:
        """Update project and invalidate cache"""
        try:
            # Build update dict
            update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
            update_dict["updated_at"] = datetime.utcnow()
            
            # Update in database
            result = await self.collection.update_one(
                {"id": project_id},
                {"$set": update_dict}
            )
            
            if result.matched_count == 0:
                return None
            
            # Invalidate cache
            await cache_service.invalidate_project(project_id)
            
            # Return updated project
            return await self.get_project(project_id)
            
        except Exception as e:
            logger.error(f"❌ Failed to update project {project_id}: {e}")
            return None
    
    async def delete_project(self, project_id: str, user_id: Optional[str] = None) -> bool:
        """Delete project and invalidate cache"""
        try:
            result = await self.collection.delete_one({"id": project_id})
            
            if result.deleted_count > 0:
                # Invalidate cache
                await cache_service.invalidate_project(project_id)
                logger.info(f"✅ Project deleted: {project_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to delete project {project_id}: {e}")
            return False
    
    async def list_projects(self, filters: ProjectFilters, user_id: Optional[str] = None) -> List[KickstarterProject]:
        """List projects with filtering and pagination"""
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
            projects_data = await cursor.to_list(length=None)
            
            # Convert to models
            projects = [KickstarterProject(**data) for data in projects_data]
            
            return projects
            
        except Exception as e:
            logger.error(f"❌ Failed to list projects: {e}")
            return []
    
    async def get_project_stats(self, user_id: Optional[str] = None) -> ProjectStats:
        """Get project statistics with caching"""
        try:
            # Check cache
            cache_key = f"project_stats_{user_id or 'all'}"
            cached_stats = await cache_service.get(cache_key)
            if cached_stats:
                return ProjectStats(**cached_stats)
            
            # Build query
            query = {"user_id": user_id} if user_id else {}
            
            # Aggregate statistics
            pipeline = [
                {"$match": query},
                {"$group": {
                    "_id": None,
                    "total_projects": {"$sum": 1},
                    "active_projects": {"$sum": {"$cond": [{"$eq": ["$status", "live"]}, 1, 0]}},
                    "successful_projects": {"$sum": {"$cond": [{"$eq": ["$status", "successful"]}, 1, 0]}},
                    "failed_projects": {"$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}},
                    "total_funding": {"$sum": "$pledged_amount"},
                    "average_funding": {"$avg": "$pledged_amount"},
                    "total_backers": {"$sum": "$backers_count"}
                }}
            ]
            
            result = await self.collection.aggregate(pipeline).to_list(length=1)
            base_stats = result[0] if result else {}
            
            # Get distribution statistics
            categories_dist = await self._get_distribution("category", query)
            risk_dist = await self._get_distribution("risk_level", query)
            status_dist = await self._get_distribution("status", query)
            
            stats = ProjectStats(
                total_projects=base_stats.get("total_projects", 0),
                active_projects=base_stats.get("active_projects", 0),
                successful_projects=base_stats.get("successful_projects", 0),
                failed_projects=base_stats.get("failed_projects", 0),
                total_funding=base_stats.get("total_funding", 0.0),
                average_funding=base_stats.get("average_funding", 0.0),
                total_backers=base_stats.get("total_backers", 0),
                categories_distribution=categories_dist,
                risk_distribution=risk_dist,
                status_distribution=status_dist
            )
            
            # Cache for 30 minutes
            await cache_service.set(cache_key, stats.model_dump(), 1800)
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get project stats: {e}")
            return ProjectStats(
                total_projects=0, active_projects=0, successful_projects=0,
                failed_projects=0, total_funding=0.0, average_funding=0.0,
                total_backers=0, categories_distribution={}, risk_distribution={},
                status_distribution={}
            )
    
    async def batch_analyze_projects(self, request: BatchAnalyzeRequest, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Perform batch AI analysis on projects"""
        try:
            # Get projects to analyze
            if request.project_ids:
                query = {"id": {"$in": request.project_ids}}
            else:
                query = {"user_id": user_id} if user_id else {}
                
            # Limit to reasonable batch size
            cursor = self.collection.find(query).limit(min(request.batch_size, 10))
            projects_data = await cursor.to_list(length=None)
            
            if not projects_data:
                return {
                    "success": True,
                    "message": "No projects found for analysis",
                    "results": [],
                    "stats": {"total_projects": 0, "successful_analyses": 0, "failed_analyses": 0}
                }
            
            projects = [KickstarterProject(**data) for data in projects_data]
            
            # Perform batch analysis
            start_time = datetime.utcnow()
            analysis_results = await ai_service.batch_analyze_projects(projects)
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Update projects with new analyses
            successful_updates = 0
            failed_updates = 0
            
            for i, result in enumerate(analysis_results):
                try:
                    project_id = projects[i].id
                    await self.collection.update_one(
                        {"id": project_id},
                        {
                            "$set": {
                                "ai_analysis": result,
                                "risk_level": result.get("risk_level", "medium"),
                                "updated_at": datetime.utcnow()
                            }
                        }
                    )
                    
                    # Invalidate cache
                    await cache_service.invalidate_project(project_id)
                    successful_updates += 1
                    
                except Exception as e:
                    logger.error(f"Failed to update project {projects[i].id}: {e}")
                    failed_updates += 1
            
            # Calculate statistics
            successful_analyses = sum(1 for r in analysis_results if not r.get("error"))
            failed_analyses = len(analysis_results) - successful_analyses
            
            stats = {
                "total_projects": len(projects),
                "successful_analyses": successful_analyses,
                "failed_analyses": failed_analyses,
                "successful_updates": successful_updates,
                "failed_updates": failed_updates,
                "processing_time": processing_time,
                "average_time_per_project": processing_time / len(projects) if projects else 0
            }
            
            logger.info(f"✅ Batch analysis completed: {stats}")
            
            return {
                "success": True,
                "message": f"Batch analysis completed for {len(projects)} projects",
                "results": analysis_results,
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"❌ Batch analysis failed: {e}")
            raise
    
    async def get_recommendations(self, limit: int = 10, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get AI-powered project recommendations"""
        try:
            # Check cache
            cache_key = f"recommendations_{user_id or 'all'}_{limit}"
            cached_recs = await cache_service.get(cache_key)
            if cached_recs:
                return cached_recs
            
            # Get projects with AI analysis
            query = {"ai_analysis": {"$exists": True}}
            if user_id:
                query["user_id"] = user_id
            
            cursor = self.collection.find(query).limit(50)  # Analyze top 50 projects
            projects_data = await cursor.to_list(length=None)
            projects = [KickstarterProject(**data) for data in projects_data]
            
            # Get recommendations from AI service
            recommendations = await ai_service.get_recommendations(projects, limit)
            
            # Cache for 15 minutes
            await cache_service.set(cache_key, recommendations, 900)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Failed to get recommendations: {e}")
            return []
    
    def _build_query(self, filters: ProjectFilters, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Build MongoDB query from filters"""
        query = {}
        
        # User filter
        if user_id:
            query["user_id"] = user_id
        
        # Text search
        if filters.search:
            query["$or"] = [
                {"name": {"$regex": filters.search, "$options": "i"}},
                {"creator": {"$regex": filters.search, "$options": "i"}},
                {"description": {"$regex": filters.search, "$options": "i"}}
            ]
        
        # Category filter
        if filters.category:
            query["category"] = {"$regex": f"^{filters.category}$", "$options": "i"}
        
        # Status filter
        if filters.status:
            query["status"] = filters.status
        
        # Risk level filter
        if filters.risk_level:
            query["risk_level"] = filters.risk_level
        
        # Funding range
        if filters.min_funding is not None or filters.max_funding is not None:
            funding_query = {}
            if filters.min_funding is not None:
                funding_query["$gte"] = filters.min_funding
            if filters.max_funding is not None:
                funding_query["$lte"] = filters.max_funding
            query["pledged_amount"] = funding_query
        
        # Goal range
        if filters.min_goal is not None or filters.max_goal is not None:
            goal_query = {}
            if filters.min_goal is not None:
                goal_query["$gte"] = filters.min_goal
            if filters.max_goal is not None:
                goal_query["$lte"] = filters.max_goal
            query["goal_amount"] = goal_query
        
        # AI analysis filter
        if filters.has_ai_analysis is not None:
            if filters.has_ai_analysis:
                query["ai_analysis"] = {"$exists": True}
            else:
                query["ai_analysis"] = {"$exists": False}
        
        # Tags filter
        if filters.tags:
            query["tags"] = {"$in": filters.tags}
        
        return query
    
    async def _get_distribution(self, field: str, base_query: Dict[str, Any]) -> Dict[str, int]:
        """Get distribution statistics for a field"""
        try:
            pipeline = [
                {"$match": base_query},
                {"$group": {"_id": f"${field}", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            
            result = await self.collection.aggregate(pipeline).to_list(length=None)
            return {item["_id"]: item["count"] for item in result if item["_id"]}
            
        except Exception as e:
            logger.error(f"Failed to get distribution for {field}: {e}")
            return {}