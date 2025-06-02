"""
📊 Project Models
Core data models for Kickstarter project management
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import uuid

def normalize_datetime(dt):
    """Normalize datetime to remove timezone info for MongoDB compatibility"""
    if dt and hasattr(dt, 'replace'):
        return dt.replace(tzinfo=None)
    return dt

class KickstarterProject(BaseModel):
    """Main Kickstarter project model with comprehensive validation"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Basic Information
    name: str = Field(..., min_length=1, max_length=200)
    creator: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10)
    category: str = Field(..., min_length=1, max_length=50)
    
    # Financial Data
    goal_amount: float = Field(..., gt=0)
    pledged_amount: float = Field(default=0, ge=0)
    backers_count: int = Field(default=0, ge=0)
    
    # Timeline
    launched_date: datetime = Field(default_factory=datetime.utcnow)
    deadline: datetime
    
    # Status and Risk
    status: str = Field(default="live", pattern="^(upcoming|live|successful|failed|suspended)$")
    risk_level: str = Field(default="medium", pattern="^(low|medium|high)$")
    
    # URLs and Media
    project_url: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    
    # Analytics and AI
    ai_analysis: Optional[Dict[str, Any]] = None
    funding_velocity: Optional[float] = None  # Amount per day
    success_probability: Optional[float] = Field(None, ge=0, le=1)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    scraped_at: Optional[datetime] = None
    
    # User Association (for multi-user support)
    user_id: Optional[str] = None
    is_public: bool = True
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = Field(None, max_length=1000)

    @validator('deadline', 'launched_date', 'created_at', 'updated_at', 'scraped_at', pre=True)
    def validate_dates(cls, v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00')).replace(tzinfo=None)
            except ValueError:
                raise ValueError('Invalid datetime format')
        return normalize_datetime(v)
    
    @validator('risk_level', pre=True)
    def normalize_risk_level(cls, v):
        """Normalize risk level to lowercase"""
        if v:
            return v.lower()
        return 'medium'
    
    @validator('status', pre=True)
    def normalize_status(cls, v):
        """Normalize status to lowercase"""
        if v:
            return v.lower()
        return 'live'
    
    @validator('category')
    def validate_category(cls, v):
        """Validate and normalize category"""
        valid_categories = [
            'art', 'comics', 'crafts', 'dance', 'design', 'fashion', 'film & video',
            'food', 'games', 'journalism', 'music', 'photography', 'publishing',
            'technology', 'theater', 'innovation', 'sports', 'education'
        ]
        if v.lower() not in valid_categories:
            # Don't raise error, just normalize the category
            pass
        return v.title()
    
    @validator('pledged_amount')
    def validate_funding_logic(cls, v, values):
        """Ensure pledged amount logic is consistent"""
        if 'goal_amount' in values and v > values['goal_amount'] * 10:
            # Warn about potentially incorrect funding amounts
            pass
        return v

    def funding_percentage(self) -> float:
        """Calculate funding percentage"""
        if self.goal_amount <= 0:
            return 0.0
        return (self.pledged_amount / self.goal_amount) * 100

    def days_remaining(self) -> int:
        """Calculate days remaining until deadline"""
        if self.deadline <= datetime.utcnow():
            return 0
        return (self.deadline - datetime.utcnow()).days

    def is_fully_funded(self) -> bool:
        """Check if project is fully funded"""
        return self.pledged_amount >= self.goal_amount

    def is_active(self) -> bool:
        """Check if project is currently active"""
        return self.status in ['live', 'upcoming'] and self.days_remaining() > 0

class ProjectCreate(BaseModel):
    """Model for creating new projects"""
    name: str = Field(..., min_length=1, max_length=200)
    creator: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10)
    category: str = Field(..., min_length=1, max_length=50)
    goal_amount: float = Field(..., gt=0)
    pledged_amount: float = Field(default=0, ge=0)
    backers_count: int = Field(default=0, ge=0)
    launched_date: Optional[datetime] = None
    deadline: datetime
    status: Optional[str] = Field(default="live", pattern="^(upcoming|live|successful|failed|suspended)$")
    project_url: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = Field(None, max_length=1000)

class ProjectUpdate(BaseModel):
    """Model for updating existing projects"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    creator: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=10)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    goal_amount: Optional[float] = Field(None, gt=0)
    pledged_amount: Optional[float] = Field(None, ge=0)
    backers_count: Optional[int] = Field(None, ge=0)
    deadline: Optional[datetime] = None
    status: Optional[str] = Field(None, pattern="^(upcoming|live|successful|failed|suspended)$")
    risk_level: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    project_url: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = Field(None, max_length=1000)

class ProjectResponse(BaseModel):
    """Model for project API responses"""
    id: str
    name: str
    creator: str
    description: str
    category: str
    goal_amount: float
    pledged_amount: float
    backers_count: int
    launched_date: datetime
    deadline: datetime
    status: str
    risk_level: str
    project_url: Optional[str]
    image_url: Optional[str]
    video_url: Optional[str]
    ai_analysis: Optional[Dict[str, Any]]
    funding_velocity: Optional[float]
    success_probability: Optional[float]
    created_at: datetime
    updated_at: datetime
    user_id: Optional[str]
    tags: List[str]
    notes: Optional[str]
    
    # Computed fields
    funding_percentage: float
    days_remaining: int
    is_fully_funded: bool
    is_active: bool

class ProjectFilters(BaseModel):
    """Model for project filtering"""
    search: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    risk_level: Optional[str] = None
    min_funding: Optional[float] = Field(None, ge=0)
    max_funding: Optional[float] = Field(None, ge=0)
    min_goal: Optional[float] = Field(None, ge=0)
    max_goal: Optional[float] = Field(None, ge=0)
    has_ai_analysis: Optional[bool] = None
    user_id: Optional[str] = None
    tags: Optional[List[str]] = None
    
    # Sorting
    sort_by: Optional[str] = Field(default="created_at")
    sort_order: Optional[str] = Field(default="desc", pattern="^(asc|desc)$")
    
    # Pagination
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)

class BatchAnalyzeRequest(BaseModel):
    """Model for batch analysis requests"""
    project_ids: Optional[List[str]] = None
    batch_size: int = Field(default=5, ge=1, le=10)
    force_reanalysis: bool = False

class ProjectStats(BaseModel):
    """Model for project statistics"""
    total_projects: int
    active_projects: int
    successful_projects: int
    failed_projects: int
    total_funding: float
    average_funding: float
    total_backers: int
    categories_distribution: Dict[str, int]
    risk_distribution: Dict[str, int]
    status_distribution: Dict[str, int]