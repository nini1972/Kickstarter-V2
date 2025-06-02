# 🧪 Kickstarter Investment Tracker - Test Makefile
# Comprehensive testing commands for development and CI/CD

.PHONY: help test test-unit test-integration test-security test-performance test-all test-quick
.PHONY: coverage lint format clean install-deps check-deps
.PHONY: test-reports test-summary

# Colors for output
GREEN = \033[32m
YELLOW = \033[33m
RED = \033[31m
BLUE = \033[34m
NC = \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)🧪 Kickstarter Investment Tracker - Test Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

install-deps: ## Install all test dependencies
	@echo "$(YELLOW)📦 Installing test dependencies...$(NC)"
	pip install -r requirements.txt

check-deps: ## Check if all dependencies are installed
	@echo "$(YELLOW)🔍 Checking dependencies...$(NC)"
	python run_tests.py --check-deps

test-quick: ## Run quick test suite for development
	@echo "$(YELLOW)🚀 Running quick tests...$(NC)"
	python run_tests.py --suite quick --verbose

test-unit: ## Run unit tests with coverage
	@echo "$(YELLOW)🔬 Running unit tests...$(NC)"
	python run_tests.py --suite unit --verbose

test-integration: ## Run integration tests
	@echo "$(YELLOW)🔗 Running integration tests...$(NC)"
	python run_tests.py --suite integration --verbose

test-security: ## Run security tests
	@echo "$(YELLOW)🛡️ Running security tests...$(NC)"
	python run_tests.py --suite security --verbose

test-performance: ## Run performance tests
	@echo "$(YELLOW)⚡ Running performance tests...$(NC)"
	python run_tests.py --suite performance --verbose

test-all: ## Run complete test suite
	@echo "$(YELLOW)🧪 Running all tests...$(NC)"
	python run_tests.py --suite all --verbose

test: test-quick ## Default test command (quick tests)

coverage: ## Generate coverage report
	@echo "$(YELLOW)📊 Generating coverage report...$(NC)"
	python run_tests.py --suite all --coverage

test-reports: ## Generate all test reports
	@echo "$(YELLOW)📋 Generating test reports...$(NC)"
	python run_tests.py --suite all --coverage --summary

test-summary: ## Generate test summary
	@echo "$(YELLOW)📋 Generating test summary...$(NC)"
	python run_tests.py --summary

lint: ## Run code linting
	@echo "$(YELLOW)🧹 Running linting...$(NC)"
	-flake8 . --exclude=venv,node_modules,__pycache__ --max-line-length=120
	-black --check . --exclude="/(venv|node_modules|__pycache__)/"

format: ## Format code
	@echo "$(YELLOW)✨ Formatting code...$(NC)"
	black . --exclude="/(venv|node_modules|__pycache__)/"
	isort . --skip-glob="*/venv/*" --skip-glob="*/node_modules/*"

clean: ## Clean test artifacts and cache
	@echo "$(YELLOW)🧹 Cleaning test artifacts...$(NC)"
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf reports/
	rm -rf .coverage
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "*~" -delete

# CI/CD Commands
ci-test: install-deps test-all coverage test-summary ## Run full CI test suite

# Development workflow commands
dev-test: test-quick ## Quick development test
dev-full: clean install-deps test-all coverage ## Full development test cycle

# Specific test categories
test-models: ## Run model tests only
	@echo "$(YELLOW)📊 Running model tests...$(NC)"
	python -m pytest tests/unit/test_models.py -v

test-analytics: ## Run analytics tests only
	@echo "$(YELLOW)📈 Running analytics tests...$(NC)"
	python -m pytest tests/unit/test_analytics_service.py -v

test-circuit-breaker: ## Run circuit breaker tests only
	@echo "$(YELLOW)⚡ Running circuit breaker tests...$(NC)"
	python -m pytest tests/unit/test_circuit_breaker.py -v

test-security-middleware: ## Run security middleware tests only
	@echo "$(YELLOW)🛡️ Running security middleware tests...$(NC)"
	python -m pytest tests/unit/test_security_middleware.py -v

test-api: ## Run API endpoint tests only
	@echo "$(YELLOW)🌐 Running API tests...$(NC)"
	python -m pytest tests/integration/test_api_endpoints.py -v

test-business: ## Run business logic tests only
	@echo "$(YELLOW)💼 Running business logic tests...$(NC)"
	python -m pytest tests/integration/test_business_logic.py -v

# Debug and troubleshooting
test-debug: ## Run tests with debug output
	@echo "$(YELLOW)🐛 Running tests in debug mode...$(NC)"
	python -m pytest tests/ -v -s --tb=long --log-cli-level=DEBUG

test-failed: ## Run only failed tests from last run
	@echo "$(YELLOW)🔄 Running failed tests...$(NC)"
	python -m pytest --lf -v

# Performance and benchmarking
benchmark: ## Run benchmark tests only
	@echo "$(YELLOW)⏱️ Running benchmarks...$(NC)"
	python -m pytest tests/ --benchmark-only --benchmark-sort=mean

# Test with different configurations
test-mysql: ## Run tests with MySQL (if configured)
	@echo "$(YELLOW)🐬 Running tests with MySQL...$(NC)"
	DATABASE_URL=mysql://test:test@localhost/test_db python -m pytest tests/

test-postgres: ## Run tests with PostgreSQL (if configured)
	@echo "$(YELLOW)🐘 Running tests with PostgreSQL...$(NC)"
	DATABASE_URL=postgresql://test:test@localhost/test_db python -m pytest tests/

# Documentation and reporting
test-docs: ## Generate test documentation
	@echo "$(YELLOW)📚 Generating test documentation...$(NC)"
	python -m pytest tests/ --collect-only --quiet > reports/test-inventory.txt

# Monitoring and health checks
test-health: ## Run health check tests only
	@echo "$(YELLOW)💚 Running health check tests...$(NC)"
	python -m pytest tests/integration/test_api_endpoints.py::TestHealthAndMonitoringEndpoints -v

# Environment setup
setup-test-env: ## Setup test environment
	@echo "$(YELLOW)🔧 Setting up test environment...$(NC)"
	cp .env.example .env.test
	@echo "$(GREEN)✅ Test environment setup complete$(NC)"

# Default target
.DEFAULT_GOAL := help
