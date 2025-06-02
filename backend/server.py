from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import json
from pathlib import Path
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta, timezone
import openai
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import requests
import re

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Environment variable validation
REQUIRED_ENV_VARS = ['MONGO_URL', 'DB_NAME', 'OPENAI_API_KEY']
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# OpenAI client
openai.api_key = os.environ['OPENAI_API_KEY']
openai_client = openai.OpenAI(api_key=os.environ['OPENAI_API_KEY'])

# Create the main app without a prefix
app = FastAPI(title="Kickstarter Investment Tracker", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configuration constants
MAX_PROJECTS_LIMIT = 1000
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100

# Utility Functions
def normalize_datetime(dt: datetime) -> datetime:
    """Normalize datetime to UTC, handling timezone-aware and naive datetimes"""
    if dt.tzinfo is None:
        return dt
    return dt.replace(tzinfo=None)

def get_utc_now() -> datetime:
    """Get current UTC datetime"""
    return datetime.utcnow()

def calculate_days_difference(end_date: datetime, start_date: datetime = None) -> int:
    """Calculate days between two dates, handling timezones properly"""
    if start_date is None:
        start_date = get_utc_now()
    
    end_normalized = normalize_datetime(end_date)
    start_normalized = normalize_datetime(start_date)
    
    return (end_normalized - start_normalized).days

# Define Models
class KickstarterProject(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1, max_length=200)
    creator: str = Field(..., min_length=1, max_length=100)
    url: str = Field(..., pattern=r'^https?://')
    description: str = Field(..., min_length=10, max_length=2000)
    category: str = Field(..., min_length=1, max_length=50)
    goal_amount: float = Field(..., gt=0)
    pledged_amount: float = Field(default=0, ge=0)
    backers_count: int = Field(default=0, ge=0)
    deadline: datetime
    launched_date: datetime
    status: str = Field(..., pattern=r'^(live|successful|failed|cancelled)$')
    risk_level: str = Field(default='medium', pattern=r'^(low|medium|high)$')
    ai_analysis: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=get_utc_now)
    updated_at: datetime = Field(default_factory=get_utc_now)
    
    @validator('deadline', 'launched_date')
    def validate_dates(cls, v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00')).replace(tzinfo=None)
            except ValueError:
                raise ValueError('Invalid datetime format')
        return normalize_datetime(v)

class Investment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    amount: float
    investment_date: datetime
    expected_return: Optional[float] = None
    notes: Optional[str] = None
    reward_tier: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ProjectCreate(BaseModel):
    name: str
    creator: str
    url: str
    description: str
    category: str
    goal_amount: float
    pledged_amount: float = 0
    backers_count: int = 0
    deadline: datetime
    launched_date: datetime
    status: str = 'live'

class InvestmentCreate(BaseModel):
    project_id: str
    amount: float
    investment_date: datetime
    expected_return: Optional[float] = None
    notes: Optional[str] = None
    reward_tier: Optional[str] = None

class AIAnalysisResult(BaseModel):
    risk_level: str
    sentiment_score: float
    success_probability: float
    key_factors: List[str]
    recommendations: List[str]
    funding_velocity: float
    creator_credibility: float

class AlertSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default_user"  # For future multi-user support
    notification_frequency: str = "instant"  # 'instant', 'daily', 'weekly'
    min_funding_velocity: float = 0.1  # Minimum funding speed threshold
    preferred_categories: List[str] = ["Technology"]
    max_risk_level: str = "medium"  # 'low', 'medium', 'high'
    min_success_probability: float = 0.6
    browser_notifications: bool = True
    email_notifications: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ProjectAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    alert_type: str  # 'high_potential', 'funding_surge', 'deadline_approaching'
    message: str
    priority: str = "medium"  # 'low', 'medium', 'high'
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AnalyticsData(BaseModel):
    roi_prediction: float
    funding_velocity: float
    market_sentiment: float
    diversification_score: float
    risk_adjusted_return: float
    recommended_actions: List[str]

async def calculate_funding_velocity(project: KickstarterProject) -> float:
    """Calculate funding velocity as percentage of goal per day"""
    try:
        days_since_launch = calculate_days_difference(get_utc_now(), project.launched_date)
        
        if days_since_launch <= 0:
            return 0.0
        
        if project.goal_amount <= 0:
            return 0.0
            
        funding_percentage = (project.pledged_amount / project.goal_amount) * 100
        velocity = funding_percentage / days_since_launch
        return round(max(0.0, velocity), 2)
    except (AttributeError, TypeError, ZeroDivisionError) as e:
        logging.error(f"Error calculating funding velocity for project {project.id}: {e}")
        return 0.0

async def generate_project_alerts(project: KickstarterProject, settings: AlertSettings) -> List[ProjectAlert]:
    """Generate alerts for promising projects based on user settings"""
    alerts = []
    
    try:
        # Check funding velocity
        velocity = await calculate_funding_velocity(project)
        if velocity >= settings.min_funding_velocity * 100:  # Convert to percentage
            alerts.append(ProjectAlert(
                project_id=project.id,
                alert_type="funding_surge",
                message=f"🚀 {project.name} is funding at {velocity}% per day! This shows strong market interest.",
                priority="high"
            ))
        
        # Check success probability
        if project.ai_analysis and project.ai_analysis.get('success_probability', 0) >= settings.min_success_probability:
            alerts.append(ProjectAlert(
                project_id=project.id,
                alert_type="high_potential",
                message=f"⭐ {project.name} has {project.ai_analysis['success_probability']*100:.0f}% success probability - Consider investing!",
                priority="medium"
            ))
        
        # Check deadline approaching
        days_remaining = calculate_days_difference(project.deadline, get_utc_now())
        
        if days_remaining <= 7 and days_remaining >= 0 and project.status == 'live':
            alerts.append(ProjectAlert(
                project_id=project.id,
                alert_type="deadline_approaching",
                message=f"⏰ {project.name} ends in {days_remaining} days! Last chance to invest.",
                priority="medium"
            ))
    except Exception as e:
        logging.error(f"Error generating alerts for project {project.id}: {e}")
    
    return alerts

async def calculate_portfolio_analytics(projects: List[KickstarterProject], investments: List[Investment]) -> AnalyticsData:
    """Generate advanced analytics for the investment portfolio"""
    if not projects or not investments:
        return AnalyticsData(
            roi_prediction=0.0,
            funding_velocity=0.0,
            market_sentiment=0.5,
            diversification_score=0.0,
            risk_adjusted_return=0.0,
            recommended_actions=["Add more projects to enable analytics"]
        )
    
    # Calculate average success probability
    success_probs = [p.ai_analysis.get('success_probability', 0.5) if p.ai_analysis else 0.5 for p in projects]
    avg_success_prob = sum(success_probs) / len(success_probs)
    
    # Calculate funding velocity average
    velocities = []
    for project in projects:
        velocity = await calculate_funding_velocity(project)
        velocities.append(velocity)
    avg_velocity = sum(velocities) / len(velocities) if velocities else 0.0
    
    # Calculate diversification score (based on categories)
    categories = [p.category for p in projects]
    unique_categories = len(set(categories))
    diversification_score = min(unique_categories / 5.0, 1.0)  # Max score for 5+ categories
    
    # Calculate risk distribution
    risk_levels = [p.risk_level for p in projects]
    high_risk_ratio = risk_levels.count('high') / len(risk_levels)
    medium_risk_ratio = risk_levels.count('medium') / len(risk_levels)
    low_risk_ratio = risk_levels.count('low') / len(risk_levels)
    
    # Risk-adjusted return prediction
    total_invested = sum(inv.amount for inv in investments)
    expected_returns = sum(inv.expected_return or inv.amount * 1.2 for inv in investments)
    roi_prediction = ((expected_returns - total_invested) / total_invested * 100) if total_invested > 0 else 0.0
    
    # Adjust for risk
    risk_adjustment = 1.0 - (high_risk_ratio * 0.3) + (low_risk_ratio * 0.1)
    risk_adjusted_return = roi_prediction * risk_adjustment
    
    # Generate recommendations
    recommendations = []
    if high_risk_ratio > 0.4:
        recommendations.append("Consider reducing high-risk investments to balance portfolio")
    if diversification_score < 0.6:
        recommendations.append("Diversify across more categories to reduce sector risk")
    if avg_velocity < 5.0:
        recommendations.append("Look for projects with faster funding momentum")
    if avg_success_prob < 0.6:
        recommendations.append("Focus on projects with higher AI-predicted success rates")
    
    return AnalyticsData(
        roi_prediction=round(roi_prediction, 2),
        funding_velocity=round(avg_velocity, 2),
        market_sentiment=round(avg_success_prob, 2),
        diversification_score=round(diversification_score, 2),
        risk_adjusted_return=round(risk_adjusted_return, 2),
        recommended_actions=recommendations or ["Portfolio looks well-balanced!"]
    )
async def analyze_project_with_ai(project: KickstarterProject) -> AIAnalysisResult:
    """Analyze project using GPT-4 for qualitative insights"""
    try:
        days_remaining = calculate_days_difference(project.deadline, get_utc_now())
        
        prompt = f"""
        Analyze this Kickstarter project for investment risk:
        
        Project: {project.name}
        Creator: {project.creator}
        Description: {project.description}
        Category: {project.category}
        Goal: ${project.goal_amount:,.2f}
        Pledged: ${project.pledged_amount:,.2f}
        Backers: {project.backers_count}
        Status: {project.status}
        Days remaining: {max(0, days_remaining)}
        
        Provide analysis in this JSON format:
        {{
            "risk_level": "low|medium|high",
            "sentiment_score": 0.0-1.0,
            "success_probability": 0.0-1.0,
            "key_factors": ["factor1", "factor2", "factor3"],
            "recommendations": ["rec1", "rec2", "rec3"],
            "funding_velocity": 0.0-1.0,
            "creator_credibility": 0.0-1.0
        }}
        
        Consider: project description quality, creator experience, funding progress, time remaining, category trends.
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800
        )
        
        analysis_text = response.choices[0].message.content
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
        if json_match:
            analysis_data = json.loads(json_match.group())
            return AIAnalysisResult(**analysis_data)
        else:
            # Fallback analysis
            return AIAnalysisResult(
                risk_level="medium",
                sentiment_score=0.5,
                success_probability=0.5,
                key_factors=["Analysis pending"],
                recommendations=["Manual review required"],
                funding_velocity=0.5,
                creator_credibility=0.5
            )
    except (openai.OpenAIError, json.JSONDecodeError, KeyError) as e:
        logging.error(f"AI analysis failed for project {project.id}: {e}")
        return AIAnalysisResult(
            risk_level="medium",
            sentiment_score=0.5,
            success_probability=0.5,
            key_factors=["Analysis failed"],
            recommendations=["Manual review required"],
            funding_velocity=0.5,
            creator_credibility=0.5
        )
    except Exception as e:
        logging.error(f"Unexpected error in AI analysis for project {project.id}: {e}")
        return AIAnalysisResult(
            risk_level="medium",
            sentiment_score=0.5,
            success_probability=0.5,
            key_factors=["Analysis error"],
            recommendations=["Manual review required"],
            funding_velocity=0.5,
            creator_credibility=0.5
        )

async def scrape_kickstarter_project(url: str) -> Dict[str, Any]:
    """Basic Kickstarter project data extraction"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract basic project data (simplified)
                    title = soup.find('h1', class_='type-28')
                    creator = soup.find('a', class_='grey-dark')
                    
                    return {
                        'name': title.text.strip() if title else 'Unknown Project',
                        'creator': creator.text.strip() if creator else 'Unknown Creator',
                        'description': 'Extracted from live project',
                        'category': 'Technology',
                        'scraped': True
                    }
    except Exception as e:
        logging.error(f"Scraping failed for {url}: {e}")
        return {}

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Kickstarter Investment Tracker API"}

@api_router.post("/projects", response_model=KickstarterProject)
async def create_project(project_data: ProjectCreate):
    project = KickstarterProject(**project_data.model_dump())
    
    # Perform AI analysis
    ai_analysis = await analyze_project_with_ai(project)
    project.ai_analysis = ai_analysis.model_dump()
    project.risk_level = ai_analysis.risk_level
    
    # Insert into database
    result = await db.projects.insert_one(project.model_dump())
    return project

@api_router.get("/projects", response_model=List[KickstarterProject])
async def get_projects(
    category: Optional[str] = None, 
    risk_level: Optional[str] = None,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Items per page")
):
    query = {}
    if category:
        query['category'] = category
    if risk_level:
        query['risk_level'] = risk_level
    
    skip = (page - 1) * page_size
    projects = await db.projects.find(query).skip(skip).limit(page_size).to_list(page_size)
    return [KickstarterProject(**project) for project in projects]

@api_router.get("/projects/{project_id}", response_model=KickstarterProject)
async def get_project(project_id: str):
    project = await db.projects.find_one({'id': project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return KickstarterProject(**project)

@api_router.put("/projects/{project_id}", response_model=KickstarterProject)
async def update_project(project_id: str, project_data: ProjectCreate):
    existing_project = await db.projects.find_one({'id': project_id})
    if not existing_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update project
    updated_project = KickstarterProject(**project_data.model_dump())
    updated_project.id = project_id
    updated_project.updated_at = get_utc_now()
    
    # Re-analyze with AI
    ai_analysis = await analyze_project_with_ai(updated_project)
    updated_project.ai_analysis = ai_analysis.model_dump()
    updated_project.risk_level = ai_analysis.risk_level
    
    await db.projects.replace_one({'id': project_id}, updated_project.model_dump())
    return updated_project

@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    result = await db.projects.delete_one({'id': project_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Also delete related investments
    await db.investments.delete_many({'project_id': project_id})
    return {"message": "Project deleted successfully"}

@api_router.post("/investments", response_model=Investment)
async def create_investment(investment_data: InvestmentCreate):
    # Verify project exists
    project = await db.projects.find_one({'id': investment_data.project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    investment = Investment(**investment_data.model_dump())
    await db.investments.insert_one(investment.model_dump())
    return investment

@api_router.get("/investments", response_model=List[Investment])
async def get_investments(project_id: Optional[str] = None):
    query = {}
    if project_id:
        query['project_id'] = project_id
    
    investments = await db.investments.find(query).to_list(100)
    return [Investment(**investment) for investment in investments]

@api_router.get("/dashboard/stats")
async def get_dashboard_stats():
    # Calculate portfolio statistics
    total_projects = await db.projects.count_documents({})
    total_investments = await db.investments.count_documents({})
    
    # Investment amounts
    investments = await db.investments.find({}).to_list(1000)
    total_invested = sum(inv['amount'] for inv in investments)
    
    # Risk distribution
    risk_pipeline = [
        {"$group": {"_id": "$risk_level", "count": {"$sum": 1}}}
    ]
    risk_distribution = await db.projects.aggregate(risk_pipeline).to_list(10)
    
    # Category distribution
    category_pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ]
    category_distribution = await db.projects.aggregate(category_pipeline).to_list(10)
    
    # Success rate
    successful_projects = await db.projects.count_documents({'status': 'successful'})
    success_rate = (successful_projects / total_projects * 100) if total_projects > 0 else 0
    
    return {
        'total_projects': total_projects,
        'total_investments': total_investments,
        'total_invested': total_invested,
        'risk_distribution': risk_distribution,
        'category_distribution': category_distribution,
        'success_rate': success_rate,
        'avg_investment': total_invested / total_investments if total_investments > 0 else 0
    }

@api_router.post("/projects/scrape")
async def scrape_project_data(request: Dict[str, str]):
    """Scrape basic project data from Kickstarter URL"""
    url = request.get('url', '').strip()
    
    # Validate URL
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    if not re.match(r'^https?://(?:www\.)?kickstarter\.com/', url):
        raise HTTPException(status_code=400, detail="Invalid Kickstarter URL")
    
    try:
        scraped_data = await scrape_kickstarter_project(url)
        if scraped_data:
            return {"message": "Project data scraped successfully", "data": scraped_data}
        else:
            raise HTTPException(status_code=400, detail="Failed to scrape project data")
    except Exception as e:
        logging.error(f"Scraping error for URL {url}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during scraping")

@api_router.get("/recommendations")
async def get_ai_recommendations():
    """Get AI-powered investment recommendations"""
    try:
        # Get recent projects for analysis
        projects = await db.projects.find({}).limit(10).to_list(10)
        investments = await db.investments.find({}).to_list(100)
        
        # Create portfolio analysis prompt
        portfolio_summary = f"""
        Current Portfolio:
        - Total Projects: {len(projects)}
        - Total Investments: {len(investments)}
        - Total Invested: ${sum(inv['amount'] for inv in investments):,.2f}
        
        Recent Projects:
        {[f"- {p['name']} ({p['category']}, Risk: {p['risk_level']})" for p in projects[:5]]}
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{
                "role": "user", 
                "content": f"""Based on this Kickstarter investment portfolio, provide 5 actionable recommendations for portfolio optimization and risk management:
                
                {portfolio_summary}
                
                Focus on: diversification, risk balance, emerging opportunities, and exit strategies.
                """
            }],
            temperature=0.7,
            max_tokens=600
        )
        
        recommendations = response.choices[0].message.content.split('\n')
        return {
            "recommendations": [rec.strip() for rec in recommendations if rec.strip()],
            "generated_at": datetime.utcnow()
        }
    except Exception as e:
        return {"recommendations": ["Unable to generate recommendations at this time"], "error": str(e)}

@api_router.get("/alerts", response_model=List[ProjectAlert])
async def get_smart_alerts():
    """Get smart alerts for promising projects"""
    try:
        # Get default alert settings (in a real app, this would be user-specific)
        default_settings = AlertSettings()
        
        # Get active projects
        projects = await db.projects.find({"status": "live"}).to_list(100)
        
        all_alerts = []
        for project in projects:
            project_obj = KickstarterProject(**project)
            alerts = await generate_project_alerts(project_obj, default_settings)
            all_alerts.extend(alerts)
        
        # Sort by priority and creation time
        priority_order = {"high": 3, "medium": 2, "low": 1}
        all_alerts.sort(key=lambda x: (priority_order.get(x.priority, 0), x.created_at), reverse=True)
        
        return all_alerts[:10]  # Return top 10 alerts
    except Exception as e:
        logging.error(f"Failed to generate alerts: {e}")
        return []

@api_router.get("/analytics/advanced", response_model=AnalyticsData)
async def get_advanced_analytics():
    """Get advanced portfolio analytics with ROI predictions"""
    try:
        # Get all projects and investments
        projects = await db.projects.find({}).to_list(100)
        investments = await db.investments.find({}).to_list(100)
        
        # Convert to Pydantic models
        project_objects = [KickstarterProject(**p) for p in projects]
        investment_objects = [Investment(**i) for i in investments]
        
        # Calculate analytics
        analytics = await calculate_portfolio_analytics(project_objects, investment_objects)
        return analytics
    except Exception as e:
        logging.error(f"Failed to calculate analytics: {e}")
        return AnalyticsData(
            roi_prediction=0.0,
            funding_velocity=0.0,
            market_sentiment=0.5,
            diversification_score=0.0,
            risk_adjusted_return=0.0,
            recommended_actions=["Analytics calculation failed"]
        )

@api_router.get("/analytics/funding-trends")
async def get_funding_trends():
    """Get funding trend data for charts"""
    try:
        projects = await db.projects.find({}).to_list(100)
        
        # Calculate funding velocities for trend analysis
        trend_data = []
        for project in projects:
            project_obj = KickstarterProject(**project)
            velocity = await calculate_funding_velocity(project_obj)
            
            trend_data.append({
                "name": project["name"][:20] + "..." if len(project["name"]) > 20 else project["name"],
                "velocity": velocity,
                "success_probability": project.get("ai_analysis", {}).get("success_probability", 0.5) * 100,
                "pledged_percentage": (project["pledged_amount"] / project["goal_amount"]) * 100,
                "risk_level": project["risk_level"],
                "category": project["category"]
            })
        
        return {"trends": trend_data}
    except Exception as e:
        return {"trends": [], "error": str(e)}

@api_router.post("/alerts/settings", response_model=AlertSettings)
async def update_alert_settings(settings: AlertSettings):
    """Update user alert preferences"""
    try:
        # In a real app, this would be user-specific
        await db.alert_settings.replace_one(
            {"user_id": settings.user_id}, 
            settings.model_dump(), 
            upsert=True
        )
        return settings
    except Exception as e:
        logging.error(f"Failed to update alert settings: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to update settings: {e}")

@api_router.get("/alerts/settings", response_model=AlertSettings)
async def get_alert_settings():
    """Get current alert settings"""
    try:
        settings = await db.alert_settings.find_one({"user_id": "default_user"})
        if settings:
            return AlertSettings(**settings)
        else:
            # Return default settings
            return AlertSettings()
    except Exception as e:
        return AlertSettings()

# Include the router in the main app
app.include_router(api_router)

# Configure CORS - Restrict in production
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://d339d4fa-17fe-472f-aa53-c381cf22961a.preview.emergentagent.com",
    # Add your production domain here
]

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=ALLOWED_ORIGINS,  # Restricted origins for security
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def create_database_indexes():
    """Create MongoDB indexes for optimal query performance"""
    try:
        logger.info("Creating database indexes for optimal performance...")
        
        # Projects collection indexes
        await db.projects.create_index([("category", 1), ("risk_level", 1)], background=True)
        await db.projects.create_index([("status", 1), ("deadline", 1)], background=True)
        await db.projects.create_index([("id", 1)], unique=True, background=True)
        await db.projects.create_index([("status", 1)], background=True)
        await db.projects.create_index([("risk_level", 1)], background=True)
        await db.projects.create_index([("category", 1)], background=True)
        await db.projects.create_index([("deadline", 1)], background=True)
        await db.projects.create_index([("created_at", -1)], background=True)
        await db.projects.create_index([("updated_at", -1)], background=True)
        
        # Compound index for common dashboard queries
        await db.projects.create_index([
            ("status", 1), 
            ("category", 1), 
            ("risk_level", 1)
        ], background=True)
        
        # Index for AI analysis queries
        await db.projects.create_index([
            ("ai_analysis.success_probability", -1),
            ("status", 1)
        ], background=True)
        
        # Investments collection indexes
        await db.investments.create_index([("id", 1)], unique=True, background=True)
        await db.investments.create_index([("project_id", 1)], background=True)
        await db.investments.create_index([("investment_date", -1)], background=True)
        await db.investments.create_index([("created_at", -1)], background=True)
        
        # Compound index for investment analytics
        await db.investments.create_index([
            ("project_id", 1),
            ("investment_date", -1)
        ], background=True)
        
        # Alert settings collection indexes
        await db.alert_settings.create_index([("user_id", 1)], unique=True, background=True)
        
        logger.info("✅ Database indexes created successfully!")
        
        # Log index information for monitoring
        projects_indexes = await db.projects.list_indexes().to_list(length=None)
        investments_indexes = await db.investments.list_indexes().to_list(length=None)
        
        logger.info(f"📊 Projects collection has {len(projects_indexes)} indexes")
        logger.info(f"📊 Investments collection has {len(investments_indexes)} indexes")
        
    except Exception as e:
        logger.error(f"❌ Failed to create database indexes: {e}")
        # Don't fail startup if indexes fail, just log the error

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()