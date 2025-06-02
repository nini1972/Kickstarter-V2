"""
💰 Investment Models
Models for investment tracking and portfolio management
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

class Investment(BaseModel):
    """Investment tracking model"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Core Investment Data
    project_id: str = Field(..., min_length=1)
    project_name: str = Field(..., min_length=1, max_length=200)
    amount: float = Field(..., gt=0)
    investment_date: datetime = Field(default_factory=datetime.utcnow)
    
    # Investment Details
    reward_tier: Optional[str] = Field(None, max_length=200)
    expected_delivery: Optional[datetime] = None
    investment_type: str = Field(default="backing", pattern="^(backing|equity|debt|other)$")
    
    # Status Tracking
    status: str = Field(default="active", pattern="^(active|delivered|refunded|cancelled|disputed)$")
    delivery_status: str = Field(default="pending", pattern="^(pending|shipped|delivered|delayed|cancelled)$")
    
    # Financial Tracking
    fees: float = Field(default=0.0, ge=0)
    total_cost: Optional[float] = None  # amount + fees
    currency: str = Field(default="USD", max_length=3)
    
    # ROI and Performance
    current_value: Optional[float] = Field(None, ge=0)
    roi_percentage: Optional[float] = None
    notes: Optional[str] = Field(None, max_length=1000)
    
    # Risk Assessment
    risk_rating: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    confidence_level: Optional[int] = Field(None, ge=1, le=10)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None  # For multi-user support
    
    # Tracking Data
    tracking_number: Optional[str] = None
    supplier_info: Optional[Dict[str, Any]] = None
    tags: List[str] = Field(default_factory=list)

    @validator('total_cost', always=True)
    def calculate_total_cost(cls, v, values):
        """Auto-calculate total cost if not provided"""
        if v is None and 'amount' in values and 'fees' in values:
            return values['amount'] + values['fees']
        return v

    @validator('roi_percentage', always=True)
    def calculate_roi(cls, v, values):
        """Auto-calculate ROI if current_value is provided"""
        if (v is None and 'current_value' in values and 'amount' in values 
            and values['current_value'] is not None and values['amount'] > 0):
            roi = ((values['current_value'] - values['amount']) / values['amount']) * 100
            return round(roi, 2)
        return v

    def is_profitable(self) -> bool:
        """Check if investment is currently profitable"""
        return self.roi_percentage is not None and self.roi_percentage > 0

    def days_since_investment(self) -> int:
        """Calculate days since investment"""
        return (datetime.utcnow() - self.investment_date).days

    def is_overdue(self) -> bool:
        """Check if delivery is overdue"""
        if self.expected_delivery and self.delivery_status in ['pending', 'shipped']:
            return datetime.utcnow() > self.expected_delivery
        return False

class InvestmentCreate(BaseModel):
    """Model for creating new investments"""
    project_id: str = Field(..., min_length=1)
    project_name: str = Field(..., min_length=1, max_length=200)
    amount: float = Field(..., gt=0)
    investment_date: Optional[datetime] = None
    reward_tier: Optional[str] = Field(None, max_length=200)
    expected_delivery: Optional[datetime] = None
    investment_type: str = Field(default="backing", pattern="^(backing|equity|debt|other)$")
    fees: float = Field(default=0.0, ge=0)
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = Field(None, max_length=1000)
    risk_rating: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    confidence_level: Optional[int] = Field(None, ge=1, le=10)
    tags: List[str] = Field(default_factory=list)

class InvestmentUpdate(BaseModel):
    """Model for updating investments"""
    project_name: Optional[str] = Field(None, min_length=1, max_length=200)
    amount: Optional[float] = Field(None, gt=0)
    reward_tier: Optional[str] = Field(None, max_length=200)
    expected_delivery: Optional[datetime] = None
    investment_type: Optional[str] = Field(None, pattern="^(backing|equity|debt|other)$")
    status: Optional[str] = Field(None, pattern="^(active|delivered|refunded|cancelled|disputed)$")
    delivery_status: Optional[str] = Field(None, pattern="^(pending|shipped|delivered|delayed|cancelled)$")
    fees: Optional[float] = Field(None, ge=0)
    current_value: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=1000)
    risk_rating: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    confidence_level: Optional[int] = Field(None, ge=1, le=10)
    tracking_number: Optional[str] = None
    tags: Optional[List[str]] = None

class InvestmentResponse(BaseModel):
    """Model for investment API responses"""
    id: str
    project_id: str
    project_name: str
    amount: float
    investment_date: datetime
    reward_tier: Optional[str]
    expected_delivery: Optional[datetime]
    investment_type: str
    status: str
    delivery_status: str
    fees: float
    total_cost: Optional[float]
    currency: str
    current_value: Optional[float]
    roi_percentage: Optional[float]
    notes: Optional[str]
    risk_rating: Optional[str]
    confidence_level: Optional[int]
    created_at: datetime
    updated_at: datetime
    user_id: Optional[str]
    tracking_number: Optional[str]
    tags: List[str]
    
    # Computed fields
    is_profitable: bool
    days_since_investment: int
    is_overdue: bool

class InvestmentFilters(BaseModel):
    """Model for investment filtering"""
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    investment_type: Optional[str] = None
    status: Optional[str] = None
    delivery_status: Optional[str] = None
    risk_rating: Optional[str] = None
    min_amount: Optional[float] = Field(None, ge=0)
    max_amount: Optional[float] = Field(None, ge=0)
    min_roi: Optional[float] = None
    max_roi: Optional[float] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    is_profitable: Optional[bool] = None
    is_overdue: Optional[bool] = None
    user_id: Optional[str] = None
    tags: Optional[List[str]] = None
    
    # Sorting
    sort_by: Optional[str] = Field(default="investment_date")
    sort_order: Optional[str] = Field(default="desc", pattern="^(asc|desc)$")
    
    # Pagination
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)

class PortfolioStats(BaseModel):
    """Model for portfolio statistics"""
    total_investments: int
    total_invested: float
    total_current_value: float
    total_roi: float
    total_roi_percentage: float
    active_investments: int
    delivered_investments: int
    overdue_investments: int
    profitable_investments: int
    average_investment: float
    largest_investment: float
    best_performing_investment: Optional[Dict[str, Any]]
    worst_performing_investment: Optional[Dict[str, Any]]
    investment_by_type: Dict[str, int]
    investment_by_status: Dict[str, int]
    investment_by_risk: Dict[str, int]
    monthly_investment_trend: List[Dict[str, Any]]
    
class PortfolioAnalytics(BaseModel):
    """Advanced portfolio analytics"""
    diversification_score: float  # 0-100
    risk_score: float  # 0-100
    performance_score: float  # 0-100
    recommended_actions: List[str]
    risk_distribution: Dict[str, float]
    category_exposure: Dict[str, float]
    temporal_distribution: Dict[str, float]
    projected_returns: Dict[str, float]