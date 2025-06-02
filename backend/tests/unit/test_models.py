"""
🧪 Model Tests
Testing Pydantic models and data validation
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from models.projects import (
    KickstarterProject, ProjectCreate, ProjectUpdate, 
    ProjectFilters, ProjectStats, BatchAnalyzeRequest
)
from models.investments import (
    Investment, InvestmentCreate, InvestmentUpdate,
    InvestmentFilters, PortfolioStats, PortfolioAnalytics
)
from models.auth import (
    User, UserCreate, UserLogin, UserResponse, 
    UserUpdate, Token, TokenRefresh, PasswordResetRequest
)


class TestProjectModels:
    """Test project-related models"""
    
    def test_project_create_valid_data(self, sample_project_data):
        """Test creating a project with valid data"""
        # Remove risk_level for ProjectCreate as it's not in that model
        test_data = sample_project_data.copy()
        test_data.pop('risk_level', None)
        
        project = ProjectCreate(**test_data)
        assert project.name == test_data["name"]
        assert project.category == test_data["category"]
        assert project.status == "live"  # Default status
    
    def test_project_create_invalid_status(self, sample_project_data):
        """Test validation fails with invalid status"""
        test_data = sample_project_data.copy()
        test_data.pop('risk_level', None)
        test_data["status"] = "invalid"
        
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(**test_data)
        
        assert "status" in str(exc_info.value)
    
    def test_project_create_invalid_funding_goal(self, sample_project_data):
        """Test validation fails with negative funding goal"""
        sample_project_data["goal_amount"] = -1000
        
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(**sample_project_data)
        
        assert "greater than or equal to 0" in str(exc_info.value)
    
    def test_project_create_invalid_current_funding(self, sample_project_data):
        """Test validation fails with negative current funding"""
        sample_project_data["pledged_amount"] = -500
        
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(**sample_project_data)
        
        assert "greater than or equal to 0" in str(exc_info.value)
    
    def test_project_filters_default_values(self):
        """Test project filters with default values"""
        filters = ProjectFilters()
        assert filters.page == 1
        assert filters.page_size == 20
        assert filters.search is None
        assert filters.category is None
    
    def test_project_filters_custom_values(self):
        """Test project filters with custom values"""
        filters = ProjectFilters(
            search="tech",
            category="Technology",
            risk_level="low",
            page=2,
            page_size=50
        )
        assert filters.search == "tech"
        assert filters.category == "Technology"
        assert filters.risk_level == "low"
        assert filters.page == 2
        assert filters.page_size == 50
    
    def test_batch_analyze_request_valid(self):
        """Test batch analyze request with valid data"""
        request = BatchAnalyzeRequest(
            project_ids=["id1", "id2", "id3"],
            analysis_type="full"
        )
        assert len(request.project_ids) == 3
        assert request.analysis_type == "full"
    
    def test_batch_analyze_request_empty_list(self):
        """Test batch analyze request validation with empty list"""
        with pytest.raises(ValidationError) as exc_info:
            BatchAnalyzeRequest(project_ids=[], analysis_type="full")
        
        assert "at least 1 item" in str(exc_info.value)


class TestInvestmentModels:
    """Test investment-related models"""
    
    def test_investment_create_valid_data(self, sample_investment_data):
        """Test creating an investment with valid data"""
        # Add required project_id
        sample_investment_data["project_id"] = "test_project_id"
        
        investment = InvestmentCreate(**sample_investment_data)
        assert investment.amount == sample_investment_data["amount"]
        assert investment.project_id == "test_project_id"
        assert investment.investment_type in ["pledge", "equity"]
    
    def test_investment_create_invalid_amount(self, sample_investment_data):
        """Test validation fails with invalid amount"""
        sample_investment_data["project_id"] = "test_project_id"
        sample_investment_data["amount"] = 0
        
        with pytest.raises(ValidationError) as exc_info:
            InvestmentCreate(**sample_investment_data)
        
        assert "greater than 0" in str(exc_info.value)
    
    def test_investment_create_invalid_type(self, sample_investment_data):
        """Test validation fails with invalid investment type"""
        sample_investment_data["project_id"] = "test_project_id"
        sample_investment_data["investment_type"] = "invalid_type"
        
        with pytest.raises(ValidationError) as exc_info:
            InvestmentCreate(**sample_investment_data)
        
        assert "investment_type" in str(exc_info.value)
    
    def test_investment_filters_default_values(self):
        """Test investment filters with default values"""
        filters = InvestmentFilters()
        assert filters.page == 1
        assert filters.page_size == 20
        assert filters.project_id is None
        assert filters.status is None
    
    def test_portfolio_stats_model(self):
        """Test portfolio stats model"""
        stats = PortfolioStats(
            total_investments=10,
            total_amount=5000.0,
            average_investment=500.0,
            active_investments=8,
            completed_investments=2,
            success_rate=80.0
        )
        assert stats.total_investments == 10
        assert stats.success_rate == 80.0


class TestAuthModels:
    """Test authentication-related models"""
    
    def test_user_create_valid_data(self, sample_user_data):
        """Test creating a user with valid data"""
        user = UserCreate(**sample_user_data)
        assert user.email == sample_user_data["email"]
        assert user.full_name == sample_user_data["full_name"]
        # Password should be present but we don't want to expose it
        assert hasattr(user, 'password')
    
    def test_user_create_invalid_email(self, sample_user_data):
        """Test validation fails with invalid email"""
        sample_user_data["email"] = "invalid_email"
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**sample_user_data)
        
        assert "email" in str(exc_info.value).lower()
    
    def test_user_create_weak_password(self, sample_user_data):
        """Test validation fails with weak password"""
        sample_user_data["password"] = "weak"
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**sample_user_data)
        
        assert "at least 8 characters" in str(exc_info.value)
    
    def test_user_login_valid_data(self):
        """Test user login model with valid data"""
        login = UserLogin(
            email="test@example.com",
            password="ValidPassword123!"
        )
        assert login.email == "test@example.com"
        assert login.password == "ValidPassword123!"
    
    def test_user_response_excludes_password(self, sample_user_data):
        """Test user response model excludes password"""
        # Create a user dict with password
        user_dict = {
            "id": "user_id_123",
            "email": sample_user_data["email"],
            "full_name": sample_user_data["full_name"],
            "password": "should_not_be_included",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        user_response = UserResponse(**user_dict)
        assert user_response.email == sample_user_data["email"]
        assert user_response.full_name == sample_user_data["full_name"]
        # Password should not be present in response model
        assert not hasattr(user_response, 'password')
    
    def test_token_model(self):
        """Test token model"""
        token = Token(
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            token_type="bearer",
            expires_in=3600
        )
        assert token.access_token == "test_access_token"
        assert token.token_type == "bearer"
        assert token.expires_in == 3600
    
    def test_password_reset_request(self):
        """Test password reset request model"""
        reset_request = PasswordResetRequest(email="test@example.com")
        assert reset_request.email == "test@example.com"


class TestModelEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_project_very_long_title(self, sample_project_data):
        """Test project with maximum length title"""
        sample_project_data["name"] = "A" * 200  # Assuming max length is 200
        project = ProjectCreate(**sample_project_data)
        assert len(project.name) == 200
    
    def test_project_empty_description(self, sample_project_data):
        """Test project with empty description"""
        sample_project_data["description"] = ""
        project = ProjectCreate(**sample_project_data)
        assert project.description == ""
    
    def test_investment_maximum_amount(self, sample_investment_data):
        """Test investment with very large amount"""
        sample_investment_data["project_id"] = "test_project_id"
        sample_investment_data["amount"] = 1000000.0
        
        investment = InvestmentCreate(**sample_investment_data)
        assert investment.amount == 1000000.0
    
    def test_filters_maximum_page_size(self):
        """Test filters with maximum page size"""
        filters = ProjectFilters(page_size=100)
        assert filters.page_size == 100
    
    def test_filters_invalid_page_size(self):
        """Test filters with invalid page size"""
        with pytest.raises(ValidationError) as exc_info:
            ProjectFilters(page_size=0)
        
        assert "greater than 0" in str(exc_info.value)
    
    def test_user_update_partial_data(self):
        """Test user update with partial data"""
        update = UserUpdate(full_name="New Name")
        assert update.full_name == "New Name"
        assert update.email is None  # Should be optional
        assert update.password is None  # Should be optional


class TestModelSerialization:
    """Test model serialization and deserialization"""
    
    def test_project_json_serialization(self, sample_project_data):
        """Test project model JSON serialization"""
        project = ProjectCreate(**sample_project_data)
        json_data = project.model_dump()
        
        # Verify all fields are present
        assert "name" in json_data
        assert "category" in json_data
        assert "goal_amount" in json_data
        
        # Test deserialization
        new_project = ProjectCreate(**json_data)
        assert new_project.name == project.name
        assert new_project.category == project.category
    
    def test_investment_json_serialization(self, sample_investment_data):
        """Test investment model JSON serialization"""
        sample_investment_data["project_id"] = "test_project_id"
        investment = InvestmentCreate(**sample_investment_data)
        json_data = investment.model_dump()
        
        # Verify required fields are present
        assert "project_id" in json_data
        assert "amount" in json_data
        assert "investment_type" in json_data
        
        # Test deserialization
        new_investment = InvestmentCreate(**json_data)
        assert new_investment.project_id == investment.project_id
        assert new_investment.amount == investment.amount
    
    def test_user_json_serialization_security(self, sample_user_data):
        """Test user model serialization excludes sensitive data"""
        user_dict = {
            "id": "user_123",
            "email": sample_user_data["email"],
            "full_name": sample_user_data["full_name"],
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        user_response = UserResponse(**user_dict)
        json_data = user_response.model_dump()
        
        # Verify password is not in serialized data
        assert "password" not in json_data
        assert "email" in json_data
        assert "full_name" in json_data
