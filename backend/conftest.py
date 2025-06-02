"""
🧪 Test Configuration and Fixtures
Comprehensive testing infrastructure for the Kickstarter Investment Tracker
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Dict, Any
from unittest.mock import AsyncMock, MagicMock
import os
import tempfile
from httpx import AsyncClient
from faker import Faker
from mongomock_motor import AsyncMongoMockClient

# Import application components
from server import app
from database.connection import DatabaseManager
from services.cache_service import CacheService
from services.ai_service import AIAnalysisService
from services.circuit_breaker import CircuitBreakerRegistry
from config.settings import (
    db_config, redis_config, openai_config, auth_config
)

# Initialize test data generator
fake = Faker()
Faker.seed(12345)  # For reproducible test data

# Test Environment Configuration
TEST_ENV_VARS = {
    'MONGO_URL': 'mongodb://localhost:27017',
    'REDIS_URL': 'redis://localhost:6379',
    'JWT_SECRET': 'test_jwt_secret_key_that_is_exactly_64_characters_long_for_testing',
    'OPENAI_API_KEY': 'test-openai-key-sk-123456789',
    'ENVIRONMENT': 'testing'
}

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment variables"""
    original_env = {}
    for key, value in TEST_ENV_VARS.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    # Restore original environment
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def mock_database():
    """Mock MongoDB database for testing"""
    client = AsyncMongoMockClient()
    database = client.get_database("test_kickstarter_db")
    
    # Create indexes similar to production
    projects_collection = database.get_collection("projects")
    investments_collection = database.get_collection("investments")
    users_collection = database.get_collection("users")
    
    # Create basic indexes
    await projects_collection.create_index("title")
    await projects_collection.create_index("category")
    await projects_collection.create_index("user_id")
    await investments_collection.create_index("user_id")
    await investments_collection.create_index("project_id")
    await users_collection.create_index("email")
    
    yield database
    
    # Cleanup
    await client.close()

@pytest_asyncio.fixture
async def mock_cache_service():
    """Mock Redis cache service for testing"""
    cache_service = MagicMock(spec=CacheService)
    cache_service.redis_client = MagicMock()
    
    # Mock cache methods
    cache_service.get = AsyncMock(return_value=None)
    cache_service.set = AsyncMock(return_value=True)
    cache_service.delete = AsyncMock(return_value=True)
    cache_service.exists = AsyncMock(return_value=False)
    cache_service.initialize = AsyncMock()
    cache_service.close = AsyncMock()
    cache_service.health_check = AsyncMock(return_value={"status": "healthy"})
    
    yield cache_service

@pytest_asyncio.fixture
async def mock_ai_service():
    """Mock AI service for testing"""
    ai_service = MagicMock(spec=AIAnalysisService)
    
    # Mock AI analysis response
    mock_analysis = {
        "risk_level": "medium",
        "success_probability": 0.75,
        "recommendation": "Consider investing with caution",
        "key_factors": ["Strong team", "Market demand", "Competition risk"],
        "analysis_score": 7.5,
        "detailed_analysis": "This project shows promise but has some risks."
    }
    
    ai_service.analyze_project = AsyncMock(return_value=mock_analysis)
    ai_service.get_recommendations = AsyncMock(return_value=[])
    ai_service.batch_analyze_projects = AsyncMock(return_value={"analyses": []})
    
    yield ai_service

@pytest_asyncio.fixture
async def mock_circuit_breaker_registry():
    """Mock circuit breaker registry for testing"""
    registry = MagicMock(spec=CircuitBreakerRegistry)
    
    # Mock circuit breaker methods
    registry.get_breaker = MagicMock()
    registry.get_all_stats = MagicMock(return_value={})
    registry.reset_all = AsyncMock()
    
    # Mock individual circuit breaker
    mock_breaker = MagicMock()
    mock_breaker.get_state.return_value = MagicMock(value="closed")
    mock_breaker.get_stats.return_value = {
        "state": "closed",
        "stats": {
            "success_rate": 100.0,
            "total_calls": 10,
            "failure_count": 0
        }
    }
    mock_breaker.reset = AsyncMock()
    
    registry.get_breaker.return_value = mock_breaker
    registry.breakers = {"openai_api": mock_breaker}
    
    yield registry

@pytest_asyncio.fixture
async def authenticated_client(mock_database, mock_cache_service, mock_ai_service):
    """HTTP client with authentication for API testing"""
    # Override dependencies in the app
    from server import get_database
    from services.cache_service import cache_service
    from services.ai_service import ai_service
    
    app.dependency_overrides[get_database] = lambda: mock_database
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create test user and get authentication token
        test_user = {
            "email": fake.email(),
            "password": "TestPassword123!",
            "full_name": fake.name()
        }
        
        # Register user
        response = await client.post("/api/auth/register", json=test_user)
        assert response.status_code == 201
        
        # Login to get token
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"]
        }
        response = await client.post("/api/auth/login", json=login_data)
        assert response.status_code == 200
        
        # Set authentication headers
        token_data = response.json()
        client.headers.update({
            "Authorization": f"Bearer {token_data['access_token']}"
        })
        
        yield client
    
    # Clean up overrides
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def unauthenticated_client():
    """HTTP client without authentication for testing public endpoints"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def sample_project_data():
    """Generate sample project data for testing"""
    return {
        "title": fake.sentence(nb_words=4)[:-1],
        "description": fake.text(max_nb_chars=500),
        "category": fake.random_element(elements=("Technology", "Games", "Art", "Music", "Film")),
        "funding_goal": fake.random_int(min=1000, max=100000),
        "current_funding": fake.random_int(min=0, max=50000),
        "deadline": fake.future_datetime(end_date="+30d").isoformat(),
        "creator_name": fake.name(),
        "project_url": fake.url(),
        "risk_level": fake.random_element(elements=("low", "medium", "high"))
    }

@pytest.fixture
def sample_investment_data():
    """Generate sample investment data for testing"""
    return {
        "amount": fake.random_int(min=10, max=1000),
        "investment_type": fake.random_element(elements=("pledge", "equity")),
        "notes": fake.text(max_nb_chars=200)
    }

@pytest.fixture
def sample_user_data():
    """Generate sample user data for testing"""
    return {
        "email": fake.email(),
        "password": "TestPassword123!",
        "full_name": fake.name()
    }

@pytest.fixture
def multiple_projects_data():
    """Generate multiple project records for testing"""
    projects = []
    categories = ["Technology", "Games", "Art", "Music", "Film", "Design"]
    risk_levels = ["low", "medium", "high"]
    
    for _ in range(20):
        projects.append({
            "title": fake.sentence(nb_words=4)[:-1],
            "description": fake.text(max_nb_chars=500),
            "category": fake.random_element(elements=categories),
            "funding_goal": fake.random_int(min=1000, max=100000),
            "current_funding": fake.random_int(min=0, max=50000),
            "deadline": fake.future_datetime(end_date="+30d").isoformat(),
            "creator_name": fake.name(),
            "project_url": fake.url(),
            "risk_level": fake.random_element(elements=risk_levels)
        })
    
    return projects

@pytest.fixture
def performance_test_config():
    """Configuration for performance testing"""
    return {
        "num_requests": 100,
        "concurrent_requests": 10,
        "timeout": 30.0,
        "max_response_time": 2.0,
        "target_success_rate": 95.0
    }

# Database test data utilities
class TestDataFactory:
    """Factory for creating test data"""
    
    @staticmethod
    def create_project(overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a test project"""
        project = {
            "title": fake.sentence(nb_words=4)[:-1],
            "description": fake.text(max_nb_chars=500),
            "category": fake.random_element(elements=("Technology", "Games", "Art")),
            "funding_goal": fake.random_int(min=1000, max=100000),
            "current_funding": fake.random_int(min=0, max=50000),
            "deadline": fake.future_datetime(end_date="+30d").isoformat(),
            "creator_name": fake.name(),
            "project_url": fake.url(),
            "risk_level": fake.random_element(elements=("low", "medium", "high"))
        }
        
        if overrides:
            project.update(overrides)
        
        return project
    
    @staticmethod
    def create_investment(project_id: str, overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a test investment"""
        investment = {
            "project_id": project_id,
            "amount": fake.random_int(min=10, max=1000),
            "investment_type": fake.random_element(elements=("pledge", "equity")),
            "notes": fake.text(max_nb_chars=200)
        }
        
        if overrides:
            investment.update(overrides)
        
        return investment

@pytest.fixture
def test_data_factory():
    """Provide access to test data factory"""
    return TestDataFactory

# Async test utilities
async def wait_for_condition(condition_func, timeout=5.0, interval=0.1):
    """Wait for a condition to become true"""
    import asyncio
    import time
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        if await condition_func():
            return True
        await asyncio.sleep(interval)
    return False

@pytest.fixture
def wait_for():
    """Provide wait_for_condition utility"""
    return wait_for_condition
