"""
🚀 Kickstarter Investment Tracker - Modular Server
Enterprise-grade FastAPI application with clean architecture
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configuration and Core
from config.settings import (
    app_config, server_config, db_config, redis_config, 
    openai_config, auth_config, rate_limit_config, logging_config, validate_config
)

# Database and Cache
from database.connection import db_manager, get_database, get_client
from services.cache_service import cache_service

# Models
from models.projects import (
    KickstarterProject, ProjectCreate, ProjectUpdate, ProjectResponse, 
    ProjectFilters, ProjectStats, BatchAnalyzeRequest
)
from models.investments import (
    Investment, InvestmentCreate, InvestmentUpdate, InvestmentResponse,
    InvestmentFilters, PortfolioStats, PortfolioAnalytics
)
from models.auth import (
    User, UserCreate, UserLogin, UserResponse, UserUpdate,
    Token, TokenRefresh, PasswordResetRequest, TokenData
)

# Services
from services.ai_service import ai_service
from services.project_service import ProjectService
from services.investment_service import InvestmentService
from services.alert_service import AlertService
from services.analytics_service import initialize_analytics_service
from services.auth import get_current_user, jwt_service

# Routes
from routes.auth import auth_router

# Security Middleware
from middleware.security_validation import SecurityValidationMiddleware

# Setup logging
logging.basicConfig(
    level=getattr(logging, logging_config.LEVEL),
    format=logging_config.FORMAT
)
logger = logging.getLogger(__name__)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Global service instances
project_service: Optional[ProjectService] = None
investment_service: Optional[InvestmentService] = None  
alert_service: Optional[AlertService] = None
analytics_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("🚀 Starting Kickstarter Investment Tracker...")
    
    # Validate configuration
    if not validate_config():
        logger.warning("⚠️  Configuration validation failed - some features may not work")
    
    try:
        # Initialize database
        await db_manager.initialize(db_config.MONGO_URL, db_config.get_db_name())
        await db_manager.create_indexes()
        logger.info("✅ Database initialized")
        
        # Initialize cache
        await cache_service.initialize()
        logger.info("✅ Cache service initialized")
        
        # Initialize AI service with cache
        ai_service.redis_client = cache_service.redis_client
        logger.info("✅ AI service initialized")
        
        # Initialize business services
        database = await get_database()
        global project_service, investment_service, alert_service, analytics_service
        
        project_service = ProjectService(database)
        investment_service = InvestmentService(database)
        alert_service = AlertService(database)
        analytics_service = initialize_analytics_service(database)
        
        logger.info("✅ Business services initialized")
        logger.info("🎉 Application startup complete!")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    finally:
        # Cleanup
        await cache_service.close()
        await db_manager.close()
        logger.info("🔌 Application shutdown complete")

# Create FastAPI application
app = FastAPI(
    title=app_config.TITLE,
    description=app_config.DESCRIPTION,
    version=app_config.VERSION,
    lifespan=lifespan
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Make limiter available to auth routes
auth_router.state = app.state

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=server_config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=server_config.CORS_METHODS,
    allow_headers=server_config.CORS_HEADERS,
)

# Security Validation Middleware (processes requests before they reach routes)
app.add_middleware(SecurityValidationMiddleware)

# Health Check Endpoints
@app.get("/api/health")
@limiter.limit(rate_limit_config.HEALTH_CHECK_LIMIT)
async def health_check(request: Request):
    """Comprehensive health check endpoint"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": app_config.VERSION,
            "environment": "production" if not server_config.DEBUG else "development",
            "services": {}
        }
        
        # Database health
        db_health = await db_manager.health_check()
        health_status["services"]["database"] = db_health
        
        # Cache health
        cache_health = await cache_service.health_check()
        health_status["services"]["cache"] = cache_health
        
        # Overall status
        if db_health.get("status") != "healthy" or cache_health.get("status") != "healthy":
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )

# Project Management Endpoints
@app.post("/api/projects", response_model=KickstarterProject)
@limiter.limit(rate_limit_config.API_LIMIT)
async def create_project(
    request: Request,
    project_data: ProjectCreate,
    current_user: TokenData = Depends(get_current_user)
):
    """Create a new project with AI analysis"""
    try:
        project = await project_service.create_project(project_data, current_user.user_id)
        return project
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects", response_model=List[KickstarterProject])
@limiter.limit(rate_limit_config.API_LIMIT)
async def list_projects(
    request: Request,
    search: Optional[str] = None,
    category: Optional[str] = None,
    risk_level: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(app_config.DEFAULT_PAGE_SIZE, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user)
):
    """List projects with filtering"""
    try:
        filters = ProjectFilters(
            search=search,
            category=category,
            risk_level=risk_level,
            status=status,
            page=page,
            page_size=page_size
        )
        projects = await project_service.list_projects(filters, current_user.user_id)
        return projects
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}", response_model=KickstarterProject)
async def get_project(project_id: str, current_user: TokenData = Depends(get_current_user)):
    """Get project by ID"""
    try:
        project = await project_service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/projects/{project_id}", response_model=KickstarterProject)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    current_user: TokenData = Depends(get_current_user)
):
    """Update project"""
    try:
        project = await project_service.update_project(project_id, project_data, current_user.user_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str, current_user: TokenData = Depends(get_current_user)):
    """Delete project"""
    try:
        success = await project_service.delete_project(project_id, current_user.user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"message": "Project deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/stats", response_model=ProjectStats)
async def get_project_stats(current_user: TokenData = Depends(get_current_user)):
    """Get project statistics"""
    try:
        stats = await project_service.get_project_stats(current_user.user_id)
        return stats
    except Exception as e:
        logger.error(f"Failed to get project stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Batch Processing Endpoints
@app.post("/api/projects/batch-analyze")
@limiter.limit(rate_limit_config.BATCH_LIMIT)
async def batch_analyze_projects(
    request: Request,
    batch_request: BatchAnalyzeRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """Batch analyze projects with AI"""
    try:
        result = await project_service.batch_analyze_projects(batch_request, current_user.user_id)
        return result
    except Exception as e:
        logger.error(f"Batch analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Investment Management Endpoints
@app.post("/api/investments", response_model=Investment)
@limiter.limit(rate_limit_config.API_LIMIT)
async def create_investment(
    request: Request,
    investment_data: InvestmentCreate,
    current_user: TokenData = Depends(get_current_user)
):
    """Create a new investment"""
    try:
        investment = await investment_service.create_investment(investment_data, current_user.user_id)
        return investment
    except Exception as e:
        logger.error(f"Failed to create investment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/investments", response_model=List[Investment])
@limiter.limit(rate_limit_config.API_LIMIT)
async def list_investments(
    request: Request,
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(app_config.DEFAULT_PAGE_SIZE, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user)
):
    """List investments with filtering"""
    try:
        filters = InvestmentFilters(
            project_id=project_id,
            status=status,
            page=page,
            page_size=page_size
        )
        investments = await investment_service.list_investments(filters, current_user.user_id)
        return investments
    except Exception as e:
        logger.error(f"Failed to list investments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/investments/{investment_id}", response_model=Investment)
async def get_investment(investment_id: str, current_user: TokenData = Depends(get_current_user)):
    """Get investment by ID"""
    try:
        investment = await investment_service.get_investment(investment_id)
        if not investment:
            raise HTTPException(status_code=404, detail="Investment not found")
        return investment
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get investment {investment_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/investments/{investment_id}", response_model=Investment)
async def update_investment(
    investment_id: str,
    investment_data: InvestmentUpdate,
    current_user: TokenData = Depends(get_current_user)
):
    """Update investment"""
    try:
        investment = await investment_service.update_investment(investment_id, investment_data, current_user.user_id)
        if not investment:
            raise HTTPException(status_code=404, detail="Investment not found")
        return investment
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update investment {investment_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/investments/{investment_id}")
async def delete_investment(investment_id: str, current_user: TokenData = Depends(get_current_user)):
    """Delete investment"""
    try:
        success = await investment_service.delete_investment(investment_id, current_user.user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Investment not found")
        return {"message": "Investment deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete investment {investment_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/investments/stats", response_model=PortfolioStats)
async def get_portfolio_stats(current_user: TokenData = Depends(get_current_user)):
    """Get portfolio statistics"""
    try:
        stats = await investment_service.get_portfolio_stats(current_user.user_id)
        return stats
    except Exception as e:
        logger.error(f"Failed to get portfolio stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/investments/analytics", response_model=PortfolioAnalytics)
async def get_portfolio_analytics(current_user: TokenData = Depends(get_current_user)):
    """Get portfolio analytics"""
    try:
        analytics = await investment_service.get_portfolio_analytics(current_user.user_id)
        return analytics
    except Exception as e:
        logger.error(f"Failed to get portfolio analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analytics Endpoints
@app.get("/api/analytics/dashboard")
@limiter.limit(rate_limit_config.API_LIMIT)
async def get_dashboard_analytics(
    request: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """Get comprehensive dashboard analytics"""
    try:
        analytics = await analytics_service.get_dashboard_analytics(current_user.user_id)
        return analytics
    except Exception as e:
        logger.error(f"Failed to get dashboard analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/funding-trends")
@limiter.limit(rate_limit_config.API_LIMIT)
async def get_funding_trends(
    request: Request,
    days: int = Query(30, ge=1, le=365),
    current_user: TokenData = Depends(get_current_user)
):
    """Get funding trend data"""
    try:
        trends = await analytics_service.get_funding_trends(current_user.user_id, days)
        return {"trends": trends}
    except Exception as e:
        logger.error(f"Failed to get funding trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/roi-predictions")
@limiter.limit(rate_limit_config.API_LIMIT)
async def get_roi_predictions(
    request: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """Get ROI predictions"""
    try:
        predictions = await analytics_service.get_roi_predictions(current_user.user_id)
        return predictions
    except Exception as e:
        logger.error(f"Failed to get ROI predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/risk")
@limiter.limit(rate_limit_config.API_LIMIT)
async def get_risk_analytics(
    request: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """Get risk analytics"""
    try:
        risk_analytics = await analytics_service.get_risk_analytics(current_user.user_id)
        return risk_analytics
    except Exception as e:
        logger.error(f"Failed to get risk analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/market-insights")
@limiter.limit(rate_limit_config.API_LIMIT)
async def get_market_insights(
    request: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """Get market insights"""
    try:
        insights = await analytics_service.get_market_insights(current_user.user_id)
        return insights
    except Exception as e:
        logger.error(f"Failed to get market insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Alert System Endpoints
@app.get("/api/alerts")
@limiter.limit(rate_limit_config.API_LIMIT)
async def get_alerts(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user)
):
    """Get smart alerts"""
    try:
        alerts = await alert_service.generate_smart_alerts(current_user.user_id, limit)
        return {
            "alerts": alerts,
            "summary": {
                "total_alerts": len(alerts),
                "high_priority": sum(1 for a in alerts if a.get("priority") == "HIGH"),
                "medium_priority": sum(1 for a in alerts if a.get("priority") == "MEDIUM"),
                "low_priority": sum(1 for a in alerts if a.get("priority") == "LOW"),
                "generated_at": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts/preferences")
async def get_alert_preferences(current_user: TokenData = Depends(get_current_user)):
    """Get user alert preferences"""
    try:
        preferences = await alert_service.get_user_alert_preferences(current_user.user_id)
        return preferences
    except Exception as e:
        logger.error(f"Failed to get alert preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/alerts/preferences")
async def update_alert_preferences(
    preferences: Dict[str, Any],
    current_user: TokenData = Depends(get_current_user)
):
    """Update user alert preferences"""
    try:
        updated_preferences = await alert_service.update_user_alert_preferences(current_user.user_id, preferences)
        return updated_preferences
    except Exception as e:
        logger.error(f"Failed to update alert preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# AI and Recommendations
@app.get("/api/recommendations")
@limiter.limit(rate_limit_config.API_LIMIT)
async def get_recommendations(
    request: Request,
    limit: int = Query(10, ge=1, le=50),
    current_user: TokenData = Depends(get_current_user)
):
    """Get AI-powered investment recommendations"""
    try:
        recommendations = await project_service.get_recommendations(limit, current_user.user_id)
        return {
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat(),
            "count": len(recommendations)
        }
    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Include authentication routes
app.include_router(auth_router, prefix="/api", tags=["Authentication"])

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Kickstarter Investment Tracker - Modular API",
        "version": app_config.VERSION,
        "status": "operational",
        "features": [
            "JWT Authentication with RBAC",
            "AI-powered Project Analysis",
            "Advanced Portfolio Analytics",
            "Smart Alert System",
            "Redis Caching",
            "Rate Limiting",
            "Comprehensive Health Monitoring"
        ]
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
            "path": str(request.url.path)
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server_modular:app",
        host=server_config.HOST,
        port=server_config.PORT,
        reload=server_config.RELOAD,
        log_level="info"
    )