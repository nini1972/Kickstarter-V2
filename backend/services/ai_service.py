"""
🤖 AI Analysis Service
OpenAI integration for intelligent project analysis with caching
"""

import logging
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI

from config.settings import openai_config
from models.projects import KickstarterProject

logger = logging.getLogger(__name__)

class AIAnalysisService:
    """AI-powered project analysis service with caching"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.openai_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client with error handling"""
        try:
            self.openai_client = AsyncOpenAI(
                api_key=openai_config.API_KEY,
                timeout=openai_config.TIMEOUT,
                max_retries=openai_config.MAX_RETRIES
            )
            logger.info("✅ AI service initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI service: {e}")
            self.openai_client = None
    
    def _generate_cache_key(self, project: KickstarterProject) -> str:
        """Generate cache key based on project content"""
        content = f"{project.name}_{project.description}_{project.category}_{project.goal_amount}_{project.pledged_amount}"
        content_hash = hashlib.md5(content.encode()).hexdigest()[:12]
        return f"ai_analysis:{project.id}:{content_hash}"
    
    async def get_cached_analysis(self, project: KickstarterProject) -> Optional[Dict[str, Any]]:
        """Retrieve cached analysis result"""
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key(project)
            cached_result = await self.redis_client.get(cache_key)
            
            if cached_result:
                logger.info(f"✅ Cache HIT for project {project.id}")
                data = json.loads(cached_result)
                return data.get("analysis", data)
            else:
                logger.info(f"❌ Cache MISS for project {project.id}")
                return None
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
            return None
    
    async def cache_analysis_result(self, project: KickstarterProject, analysis: Dict[str, Any]):
        """Cache analysis result with TTL"""
        if not self.redis_client:
            return
        
        try:
            cache_key = self._generate_cache_key(project)
            cache_data = {
                "analysis": analysis,
                "cached_at": datetime.utcnow().isoformat(),
                "project_id": project.id,
                "cache_version": "1.0"
            }
            
            await self.redis_client.setex(cache_key, 3600, json.dumps(cache_data))  # 1 hour TTL
            logger.info(f"✅ Cached analysis for project {project.id}")
        except Exception as e:
            logger.error(f"Cache storage error: {e}")
    
    async def invalidate_project_cache(self, project_id: str):
        """Invalidate all cached data for a project"""
        if not self.redis_client:
            return
        
        try:
            pattern = f"ai_analysis:{project_id}:*"
            keys = await self.redis_client.keys(pattern)
            
            if keys:
                await self.redis_client.delete(*keys)
                logger.info(f"✅ Invalidated {len(keys)} cache entries for project {project_id}")
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
    
    async def analyze_project(self, project: KickstarterProject) -> Dict[str, Any]:
        """Analyze a single project with AI"""
        try:
            # Check cache first
            cached_result = await self.get_cached_analysis(project)
            if cached_result:
                return cached_result
            
            if not self.openai_client:
                return self._get_fallback_analysis()
            
            logger.info(f"🤖 Performing AI analysis for project: {project.name}")
            
            # Calculate metrics
            funding_percentage = project.funding_percentage()
            days_remaining = project.days_remaining()
            
            # Prepare analysis prompt
            prompt = self._build_analysis_prompt(project, funding_percentage, days_remaining)
            
            # Make API call
            response = await self.openai_client.chat.completions.create(
                model=openai_config.MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert investment analyst specializing in crowdfunding projects. Provide detailed, objective analysis in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=openai_config.TEMPERATURE,
                max_tokens=openai_config.MAX_TOKENS
            )
            
            # Parse response
            content = response.choices[0].message.content
            analysis = self._parse_ai_response(content, project.name)
            
            # Add metadata
            analysis.update({
                "analyzed_at": datetime.utcnow().isoformat(),
                "funding_percentage": funding_percentage,
                "days_remaining": days_remaining,
                "analysis_version": "2.0",
                "model_used": openai_config.MODEL
            })
            
            # Cache result
            await self.cache_analysis_result(project, analysis)
            
            logger.info(f"✅ AI analysis completed for project: {project.name}")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ AI analysis failed for {project.name}: {e}")
            return self._get_fallback_analysis()
    
    async def batch_analyze_projects(self, projects: List[KickstarterProject]) -> List[Dict[str, Any]]:
        """Analyze multiple projects in parallel"""
        try:
            logger.info(f"🚀 Starting batch AI analysis for {len(projects)} projects")
            
            # Create analysis tasks
            import asyncio
            tasks = [self.analyze_project(project) for project in projects]
            
            # Execute in parallel with error handling
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            processed_results = []
            successful = 0
            failed = 0
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Batch analysis failed for project {projects[i].name}: {result}")
                    result = self._get_fallback_analysis()
                    failed += 1
                else:
                    successful += 1
                
                result["batch_processed"] = True
                result["batch_timestamp"] = datetime.utcnow().isoformat()
                processed_results.append(result)
            
            logger.info(f"✅ Batch analysis completed: {successful} successful, {failed} failed")
            return processed_results
            
        except Exception as e:
            logger.error(f"❌ Batch analysis failed: {e}")
            # Return fallback for all projects
            fallback_results = []
            for project in projects:
                analysis = self._get_fallback_analysis()
                analysis["batch_processed"] = True
                analysis["batch_timestamp"] = datetime.utcnow().isoformat()
                fallback_results.append(analysis)
            return fallback_results
    
    def _build_analysis_prompt(self, project: KickstarterProject, funding_percentage: float, days_remaining: int) -> str:
        """Build comprehensive analysis prompt"""
        return f"""
        Analyze this Kickstarter project and provide a detailed investment assessment:
        
        PROJECT DETAILS:
        Name: {project.name}
        Creator: {project.creator}
        Category: {project.category}
        Description: {project.description[:500]}...
        
        FINANCIAL METRICS:
        - Goal: ${project.goal_amount:,}
        - Raised: ${project.pledged_amount:,}
        - Funding: {funding_percentage:.1f}%
        - Days Remaining: {days_remaining}
        - Backers: {project.backers_count}
        - Status: {project.status}
        
        ANALYSIS REQUIREMENTS:
        Provide a comprehensive JSON response with these exact keys:
        1. "success_probability": Number (0-100) - likelihood of successful completion
        2. "risk_level": String ("low"/"medium"/"high") - investment risk assessment
        3. "strengths": Array of strings (3-5 items) - key project advantages
        4. "concerns": Array of strings (3-5 items) - potential risks or issues
        5. "recommendation": String ("strong_buy"/"buy"/"hold"/"avoid") - investment advice
        6. "roi_potential": String ("excellent"/"good"/"moderate"/"poor") - expected returns
        7. "market_analysis": String - brief market opportunity assessment
        8. "creator_credibility": String ("high"/"medium"/"low") - creator track record assessment
        9. "timeline_feasibility": String ("realistic"/"optimistic"/"concerning") - delivery timeline assessment
        10. "competitive_advantage": String - what sets this project apart
        
        Focus on data-driven insights, market viability, execution capability, and realistic risk assessment.
        """
    
    def _parse_ai_response(self, content: str, project_name: str) -> Dict[str, Any]:
        """Parse AI response with fallback handling"""
        try:
            # Try to extract JSON
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                
                # Validate required fields
                required_fields = ["success_probability", "risk_level", "strengths", "concerns", "recommendation", "roi_potential"]
                for field in required_fields:
                    if field not in analysis:
                        raise ValueError(f"Missing required field: {field}")
                
                return analysis
            else:
                raise ValueError("No JSON found in response")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse AI response for {project_name}: {e}")
            return self._get_fallback_analysis()
    
    def _get_fallback_analysis(self) -> Dict[str, Any]:
        """Provide fallback analysis when AI fails"""
        return {
            "success_probability": 50,
            "risk_level": "medium",
            "strengths": ["Analysis unavailable", "Requires manual review", "Standard crowdfunding project"],
            "concerns": ["AI service temporarily unavailable", "Limited automated assessment", "Manual analysis recommended"],
            "recommendation": "hold",
            "roi_potential": "moderate",
            "market_analysis": "Market analysis unavailable - AI service offline",
            "creator_credibility": "medium",
            "timeline_feasibility": "unknown",
            "competitive_advantage": "Analysis pending",
            "error": "AI analysis failed",
            "analyzed_at": datetime.utcnow().isoformat(),
            "is_fallback": True
        }
    
    async def get_recommendations(self, projects: List[KickstarterProject], limit: int = 10) -> List[Dict[str, Any]]:
        """Get AI-powered investment recommendations"""
        try:
            recommendations = []
            
            for project in projects:
                if project.ai_analysis:
                    analysis = project.ai_analysis
                    
                    # Calculate recommendation score
                    score = self._calculate_recommendation_score(analysis, project)
                    
                    if score >= 70:  # High threshold for recommendations
                        recommendations.append({
                            "project_id": project.id,
                            "project_name": project.name,
                            "category": project.category,
                            "recommendation_score": score,
                            "success_probability": analysis.get("success_probability", 0),
                            "risk_level": analysis.get("risk_level", "medium"),
                            "recommendation": analysis.get("recommendation", "hold"),
                            "roi_potential": analysis.get("roi_potential", "moderate"),
                            "funding_percentage": project.funding_percentage(),
                            "days_remaining": project.days_remaining(),
                            "strengths": analysis.get("strengths", [])[:3],  # Top 3 strengths
                            "reasoning": self._generate_recommendation_reasoning(analysis, project)
                        })
            
            # Sort by recommendation score
            recommendations.sort(key=lambda x: x["recommendation_score"], reverse=True)
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return []
    
    def _calculate_recommendation_score(self, analysis: Dict[str, Any], project: KickstarterProject) -> float:
        """Calculate recommendation score based on multiple factors"""
        score = 0
        
        # Success probability (40% weight)
        success_prob = analysis.get("success_probability", 0)
        score += (success_prob / 100) * 40
        
        # Risk level (20% weight)
        risk_level = analysis.get("risk_level", "medium")
        risk_scores = {"low": 20, "medium": 10, "high": 0}
        score += risk_scores.get(risk_level, 10)
        
        # Funding momentum (20% weight)
        funding_pct = project.funding_percentage()
        if funding_pct > 75:
            score += 20
        elif funding_pct > 50:
            score += 15
        elif funding_pct > 25:
            score += 10
        
        # Time factor (10% weight)
        days_remaining = project.days_remaining()
        if 5 <= days_remaining <= 30:
            score += 10
        elif days_remaining > 30:
            score += 5
        
        # Recommendation weight (10% weight)
        recommendation = analysis.get("recommendation", "hold")
        rec_scores = {"strong_buy": 10, "buy": 8, "hold": 5, "avoid": 0}
        score += rec_scores.get(recommendation, 5)
        
        return min(score, 100)  # Cap at 100
    
    def _generate_recommendation_reasoning(self, analysis: Dict[str, Any], project: KickstarterProject) -> str:
        """Generate human-readable reasoning for recommendation"""
        reasons = []
        
        success_prob = analysis.get("success_probability", 0)
        if success_prob > 80:
            reasons.append(f"High success probability ({success_prob}%)")
        
        risk_level = analysis.get("risk_level", "medium")
        if risk_level == "low":
            reasons.append("Low risk investment")
        
        funding_pct = project.funding_percentage()
        if funding_pct > 100:
            reasons.append("Successfully funded with strong momentum")
        elif funding_pct > 75:
            reasons.append("Strong funding progress")
        
        if project.days_remaining() <= 7:
            reasons.append("Final week opportunity")
        
        return "; ".join(reasons) if reasons else "Standard investment opportunity"

# Global AI service instance
ai_service = AIAnalysisService()