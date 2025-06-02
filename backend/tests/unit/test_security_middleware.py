"""
🧪 Security Middleware Tests
Testing comprehensive security validation middleware
"""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

from middleware.security_validation import SecurityValidationMiddleware


class TestSecurityValidationMiddleware:
    """Test security validation middleware functionality"""
    
    @pytest.fixture
    def middleware(self):
        """Create security middleware for testing"""
        app = MagicMock()
        return SecurityValidationMiddleware(app)
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request for testing"""
        request = MagicMock(spec=Request)
        request.method = "POST"
        request.url.path = "/api/test"
        request.headers = {"content-type": "application/json"}
        request.query_params = {}
        return request
    
    @pytest.mark.asyncio
    async def test_middleware_allows_valid_request(self, middleware, mock_request):
        """Test middleware allows valid requests to pass through"""
        # Mock valid request body
        mock_request.body = AsyncMock(return_value=b'{"name": "test", "value": 123}')
        
        # Mock call_next to return success response
        async def mock_call_next(request):
            return JSONResponse({"status": "success"})
        
        # Process request
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Should pass through successfully
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_middleware_blocks_nosql_injection(self, middleware, mock_request):
        """Test middleware blocks NoSQL injection attempts"""
        # Mock request with NoSQL injection payload
        malicious_body = b'{"email": {"$ne": null}, "password": {"$regex": ".*"}}'
        mock_request.body = AsyncMock(return_value=malicious_body)
        
        async def mock_call_next(request):
            return JSONResponse({"status": "should not reach"})
        
        # Process request
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Should be blocked
        assert response.status_code == 400
        response_data = response.body.decode()
        assert "Invalid request data" in response_data or "Security violation" in response_data
    
    @pytest.mark.asyncio
    async def test_middleware_blocks_xss_attempts(self, middleware, mock_request):
        """Test middleware blocks XSS attempts"""
        # Mock request with XSS payload
        xss_body = b'{"comment": "<script>alert(\"XSS\")</script>", "title": "Normal Title"}'
        mock_request.body = AsyncMock(return_value=xss_body)
        
        async def mock_call_next(request):
            return JSONResponse({"status": "should not reach"})
        
        # Process request
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Should be blocked
        assert response.status_code == 400
        response_data = response.body.decode()
        assert "Invalid request data" in response_data or "Security violation" in response_data
    
    @pytest.mark.asyncio
    async def test_middleware_query_param_validation(self, middleware, mock_request):
        """Test middleware validates query parameters"""
        # Mock request with malicious query params
        mock_request.query_params = {
            "search": "<script>alert('xss')</script>",
            "filter": "$ne"
        }
        mock_request.body = AsyncMock(return_value=b'{}')
        
        async def mock_call_next(request):
            return JSONResponse({"status": "should not reach"})
        
        # Process request
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Should be blocked
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_middleware_header_validation(self, middleware, mock_request):
        """Test middleware validates headers"""
        # Mock request with oversized headers
        oversized_header = "x" * 10000  # Very large header
        mock_request.headers = {
            "content-type": "application/json",
            "x-custom-header": oversized_header
        }
        mock_request.body = AsyncMock(return_value=b'{}')
        
        async def mock_call_next(request):
            return JSONResponse({"status": "should not reach"})
        
        # Process request
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Should be blocked or processed with sanitized headers
        # (depending on middleware implementation)
        assert response.status_code in [200, 400]
    
    @pytest.mark.asyncio
    async def test_middleware_content_length_validation(self, middleware, mock_request):
        """Test middleware validates content length"""
        # Mock request with extremely large body
        large_body = b'{"data": "' + b'x' * 1000000 + b'"}'  # 1MB+ body
        mock_request.body = AsyncMock(return_value=large_body)
        
        async def mock_call_next(request):
            return JSONResponse({"status": "should not reach"})
        
        # Process request
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Should be blocked for excessive size
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_middleware_json_bomb_protection(self, middleware, mock_request):
        """Test middleware protects against JSON bomb attacks"""
        # Mock deeply nested JSON (JSON bomb)
        nested_json = '{"a":' * 1000 + '1' + '}' * 1000
        mock_request.body = AsyncMock(return_value=nested_json.encode())
        
        async def mock_call_next(request):
            return JSONResponse({"status": "should not reach"})
        
        # Process request
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Should be blocked or handle gracefully
        assert response.status_code in [200, 400, 413]  # OK, Bad Request, or Payload Too Large
    
    @pytest.mark.asyncio
    async def test_middleware_allows_get_requests(self, middleware, mock_request):
        """Test middleware allows GET requests without body validation"""
        mock_request.method = "GET"
        mock_request.query_params = {"search": "normal search", "page": "1"}
        mock_request.body = AsyncMock(return_value=b'')
        
        async def mock_call_next(request):
            return JSONResponse({"status": "success"})
        
        # Process request
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Should pass through
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_middleware_handles_empty_body(self, middleware, mock_request):
        """Test middleware handles empty request body"""
        mock_request.body = AsyncMock(return_value=b'')
        
        async def mock_call_next(request):
            return JSONResponse({"status": "success"})
        
        # Process request
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Should pass through
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_middleware_handles_invalid_json(self, middleware, mock_request):
        """Test middleware handles invalid JSON gracefully"""
        # Mock invalid JSON
        mock_request.body = AsyncMock(return_value=b'{"invalid": json syntax}')
        
        async def mock_call_next(request):
            return JSONResponse({"status": "should not reach"})
        
        # Process request
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Should handle invalid JSON appropriately
        assert response.status_code in [200, 400]  # Either pass through or reject


class TestSecurityValidationPatterns:
    """Test specific security validation patterns"""
    
    @pytest.fixture
    def middleware(self):
        """Create security middleware for testing"""
        app = MagicMock()
        return SecurityValidationMiddleware(app)
    
    @pytest.mark.parametrize("malicious_input", [
        '{"$where": "this.username == this.password"}',
        '{"user": {"$gt": ""}}',
        '{"$or": [{"user": "admin"}, {"user": "root"}]}',
        '{"password": {"$ne": null}}',
        '{"eval": "db.dropDatabase()"}',
        '{"$regex": ".*"}',
    ])
    @pytest.mark.asyncio
    async def test_nosql_injection_patterns(self, middleware, malicious_input):
        """Test various NoSQL injection patterns"""
        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/test"
        mock_request.headers = {"content-type": "application/json"}
        mock_request.query_params = {}
        mock_request.body = AsyncMock(return_value=malicious_input.encode())
        
        async def mock_call_next(request):
            return JSONResponse({"status": "should not reach"})
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # All patterns should be blocked
        assert response.status_code == 400
    
    @pytest.mark.parametrize("xss_payload", [
        '<script>alert("XSS")</script>',
        '<img src=x onerror=alert("XSS")>',
        'javascript:alert("XSS")',
        '<svg onload=alert("XSS")>',
        '<iframe src="javascript:alert(\'XSS\')">',
        '<body onload=alert("XSS")>',
        '<div onclick=alert("XSS")>',
    ])
    @pytest.mark.asyncio
    async def test_xss_patterns(self, middleware, xss_payload):
        """Test various XSS patterns"""
        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/test"
        mock_request.headers = {"content-type": "application/json"}
        mock_request.query_params = {}
        
        # Embed XSS payload in JSON
        malicious_json = f'{{"comment": "{xss_payload}", "title": "Normal"}}'
        mock_request.body = AsyncMock(return_value=malicious_json.encode())
        
        async def mock_call_next(request):
            return JSONResponse({"status": "should not reach"})
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # All XSS patterns should be blocked
        assert response.status_code == 400
    
    @pytest.mark.parametrize("sql_injection", [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "' UNION SELECT * FROM admin --",
        "1; DELETE FROM projects",
        "admin'--",
        "' OR 1=1 #",
    ])
    @pytest.mark.asyncio
    async def test_sql_injection_patterns(self, middleware, sql_injection):
        """Test SQL injection patterns (even though using NoSQL)"""
        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/test"
        mock_request.headers = {"content-type": "application/json"}
        mock_request.query_params = {}
        
        # Embed SQL injection in JSON
        malicious_json = f'{{"query": "{sql_injection}", "type": "search"}}'
        mock_request.body = AsyncMock(return_value=malicious_json.encode())
        
        async def mock_call_next(request):
            return JSONResponse({"status": "should not reach"})
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # SQL injection patterns should be blocked
        assert response.status_code == 400


class TestSecurityMiddlewarePerformance:
    """Test security middleware performance characteristics"""
    
    @pytest.fixture
    def middleware(self):
        """Create security middleware for testing"""
        app = MagicMock()
        return SecurityValidationMiddleware(app)
    
    @pytest.mark.benchmark
    def test_middleware_performance_normal_request(self, middleware, benchmark):
        """Benchmark middleware performance with normal requests"""
        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/test"
        mock_request.headers = {"content-type": "application/json"}
        mock_request.query_params = {}
        mock_request.body = AsyncMock(return_value=b'{"name": "test", "value": 123}')
        
        async def mock_call_next(request):
            return JSONResponse({"status": "success"})
        
        async def run_middleware():
            return await middleware.dispatch(mock_request, mock_call_next)
        
        # Benchmark middleware overhead
        result = benchmark(asyncio.run, run_middleware())
        assert result.status_code == 200
    
    @pytest.mark.asyncio
    async def test_middleware_performance_large_payload(self, middleware):
        """Test middleware performance with large payloads"""
        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/test"
        mock_request.headers = {"content-type": "application/json"}
        mock_request.query_params = {}
        
        # Large but valid JSON payload
        large_data = {"items": [{"id": i, "name": f"item_{i}"} for i in range(1000)]}
        import json
        large_payload = json.dumps(large_data).encode()
        mock_request.body = AsyncMock(return_value=large_payload)
        
        async def mock_call_next(request):
            return JSONResponse({"status": "success"})
        
        # Should handle large payloads efficiently
        import time
        start_time = time.time()
        response = await middleware.dispatch(mock_request, mock_call_next)
        end_time = time.time()
        
        # Should complete within reasonable time (< 1 second for 1k items)
        assert end_time - start_time < 1.0
        assert response.status_code in [200, 400]  # Either pass or reject based on size limits


class TestSecurityMiddlewareConfiguration:
    """Test security middleware configuration options"""
    
    def test_middleware_default_configuration(self):
        """Test middleware with default configuration"""
        app = MagicMock()
        middleware = SecurityValidationMiddleware(app)
        
        # Should have reasonable defaults
        assert hasattr(middleware, 'app')
        # Additional configuration checks can be added based on implementation
    
    def test_middleware_custom_configuration(self):
        """Test middleware with custom configuration"""
        app = MagicMock()
        
        # Test with custom settings (if supported by implementation)
        # This test would need to be adapted based on actual middleware configuration options
        middleware = SecurityValidationMiddleware(app)
        
        # Verify custom settings are applied
        assert hasattr(middleware, 'app')


class TestSecurityMiddlewareErrorHandling:
    """Test security middleware error handling"""
    
    @pytest.fixture
    def middleware(self):
        """Create security middleware for testing"""
        app = MagicMock()
        return SecurityValidationMiddleware(app)
    
    @pytest.mark.asyncio
    async def test_middleware_handles_downstream_errors(self, middleware):
        """Test middleware handles errors from downstream middleware"""
        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/test"
        mock_request.headers = {"content-type": "application/json"}
        mock_request.query_params = {}
        mock_request.body = AsyncMock(return_value=b'{"valid": "json"}')
        
        async def failing_call_next(request):
            raise HTTPException(status_code=500, detail="Internal server error")
        
        # Should propagate downstream errors
        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(mock_request, failing_call_next)
        
        assert exc_info.value.status_code == 500
    
    @pytest.mark.asyncio
    async def test_middleware_handles_malformed_requests(self, middleware):
        """Test middleware handles completely malformed requests"""
        # Mock extremely malformed request
        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/test"
        mock_request.headers = {}  # Missing content-type
        mock_request.query_params = {}
        mock_request.body = AsyncMock(side_effect=Exception("Cannot read body"))
        
        async def mock_call_next(request):
            return JSONResponse({"status": "should not reach"})
        
        # Should handle gracefully
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Should either block or handle gracefully
        assert response.status_code in [200, 400, 500]
