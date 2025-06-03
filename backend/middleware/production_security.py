"""
🛡️ Production Security Middleware
Enterprise-grade security hardening for production deployment
"""

import logging
import time
import hashlib
import json
from typing import Dict, Any, Optional, Set
from datetime import datetime, timedelta
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import ipaddress

logger = logging.getLogger(__name__)

class ProductionSecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive production security middleware with advanced threat protection
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.blocked_ips: Set[str] = set()
        self.rate_limit_cache: Dict[str, Dict[str, Any]] = {}
        self.security_events: Dict[str, int] = {}
        self.suspicious_patterns = [
            # SQL injection patterns
            r"union\s+select", r"drop\s+table", r"delete\s+from",
            # NoSQL injection patterns  
            r"\$ne", r"\$gt", r"\$lt", r"\$regex", r"\$where",
            # XSS patterns
            r"<script", r"javascript:", r"onload=", r"onerror=",
            # Path traversal
            r"\.\./", r"\.\.\\", r"etc/passwd", r"windows/system32",
            # Command injection
            r";cat\s", r"\|nc\s", r"&&curl", r";wget"
        ]
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Main security middleware dispatch with comprehensive protection
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            HTTP response with security headers applied
        """
        start_time = time.time()
        client_ip = self._get_client_ip(request)
        
        try:
            # 1. IP blocking check
            if self._is_ip_blocked(client_ip):
                logger.warning(f"🚫 Blocked IP attempted access: {client_ip}")
                return self._create_security_response("IP_BLOCKED", "Access denied")
            
            # 2. Rate limiting
            if not await self._check_rate_limits(request, client_ip):
                logger.warning(f"🚫 Rate limit exceeded: {client_ip} on {request.url.path}")
                return self._create_security_response("RATE_LIMITED", "Too many requests")
            
            # 3. Request validation
            security_check = await self._validate_request_security(request)
            if not security_check["valid"]:
                await self._log_security_violation(client_ip, security_check["reason"], request)
                return self._create_security_response("SECURITY_VIOLATION", security_check["reason"])
            
            # 4. Process request
            response = await call_next(request)
            
            # 5. Add security headers
            self._add_security_headers(response)
            
            # 6. Log successful request
            processing_time = (time.time() - start_time) * 1000
            await self._log_request(request, response, client_ip, processing_time)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Security middleware error: {e}")
            await self._log_security_violation(client_ip, f"Middleware error: {str(e)}", request)
            
            # Return secure error response
            return self._create_security_response("INTERNAL_ERROR", "Request processing failed")
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request headers
        
        Args:
            request: HTTP request object
            
        Returns:
            Client IP address
        """
        # Check various headers for real client IP
        ip_headers = [
            "CF-Connecting-IP",      # Cloudflare
            "X-Forwarded-For",       # Standard proxy header
            "X-Real-IP",             # Nginx
            "X-Client-IP",           # General
            "X-Forwarded",           # Older standard
            "Forwarded-For",         # RFC 7239
            "Forwarded"              # RFC 7239
        ]
        
        for header in ip_headers:
            header_value = request.headers.get(header)
            if header_value:
                # Handle comma-separated IPs (take first one)
                ip = header_value.split(',')[0].strip()
                if self._is_valid_ip(ip):
                    return ip
        
        # Fallback to direct connection IP
        return request.client.host if request.client else "unknown"
    
    def _is_valid_ip(self, ip: str) -> bool:
        """
        Validate IP address format
        
        Args:
            ip: IP address string
            
        Returns:
            True if valid IP address
        """
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def _is_ip_blocked(self, ip: str) -> bool:
        """
        Check if IP address is blocked
        
        Args:
            ip: Client IP address
            
        Returns:
            True if IP is blocked
        """
        return ip in self.blocked_ips
    
    async def _check_rate_limits(self, request: Request, client_ip: str) -> bool:
        """
        Check rate limits for client IP and endpoint
        
        Args:
            request: HTTP request
            client_ip: Client IP address
            
        Returns:
            True if within rate limits
        """
        current_time = time.time()
        window_size = 60  # 1 minute window
        
        # Different limits for different endpoints
        endpoint_limits = {
            "/api/auth/login": 3,        # 3 per minute
            "/api/auth/register": 2,     # 2 per minute
            "/api/auth/reset": 1,        # 1 per minute
            "/api/projects": 60,         # 60 per minute
            "/api/analytics": 30,        # 30 per minute
            "default": 100               # 100 per minute default
        }
        
        path = request.url.path
        limit = endpoint_limits.get(path, endpoint_limits["default"])
        
        # Create rate limit key
        rate_key = f"{client_ip}:{path}"
        
        # Initialize or update rate limit data
        if rate_key not in self.rate_limit_cache:
            self.rate_limit_cache[rate_key] = {
                "requests": [],
                "violations": 0
            }
        
        rate_data = self.rate_limit_cache[rate_key]
        
        # Remove old requests outside window
        rate_data["requests"] = [
            req_time for req_time in rate_data["requests"]
            if current_time - req_time < window_size
        ]
        
        # Check if within limit
        if len(rate_data["requests"]) >= limit:
            rate_data["violations"] += 1
            
            # Block IP after multiple violations
            if rate_data["violations"] > 5:
                self.blocked_ips.add(client_ip)
                logger.warning(f"🚫 IP blocked due to rate limit violations: {client_ip}")
            
            return False
        
        # Add current request
        rate_data["requests"].append(current_time)
        return True
    
    async def _validate_request_security(self, request: Request) -> Dict[str, Any]:
        """
        Comprehensive request security validation
        
        Args:
            request: HTTP request to validate
            
        Returns:
            Dictionary with validation result and reason
        """
        try:
            # 1. Validate headers
            header_check = self._validate_headers(request)
            if not header_check["valid"]:
                return header_check
            
            # 2. Validate URL/path
            path_check = self._validate_path(request.url.path)
            if not path_check["valid"]:
                return path_check
            
            # 3. Validate query parameters
            query_check = self._validate_query_params(request.query_params)
            if not query_check["valid"]:
                return query_check
            
            # 4. Validate request body for POST/PUT requests
            if request.method in ["POST", "PUT", "PATCH"]:
                body_check = await self._validate_request_body(request)
                if not body_check["valid"]:
                    return body_check
            
            return {"valid": True, "reason": "Request passed security validation"}
            
        except Exception as e:
            logger.error(f"❌ Security validation error: {e}")
            return {"valid": False, "reason": f"Security validation failed: {str(e)}"}
    
    def _validate_headers(self, request: Request) -> Dict[str, Any]:
        """
        Validate request headers for security threats
        
        Args:
            request: HTTP request
            
        Returns:
            Validation result
        """
        # Check for suspicious header values
        for header_name, header_value in request.headers.items():
            if self._contains_malicious_content(header_value):
                return {
                    "valid": False,
                    "reason": f"Malicious content detected in header: {header_name}"
                }
            
            # Check header size
            if len(header_value) > 4096:  # 4KB limit per header
                return {
                    "valid": False,
                    "reason": f"Header too large: {header_name}"
                }
        
        return {"valid": True, "reason": "Headers validated"}
    
    def _validate_path(self, path: str) -> Dict[str, Any]:
        """
        Validate URL path for security threats
        
        Args:
            path: URL path
            
        Returns:
            Validation result
        """
        # Check for path traversal
        if "../" in path or "..\\" in path:
            return {"valid": False, "reason": "Path traversal attempt detected"}
        
        # Check for malicious content in path
        if self._contains_malicious_content(path):
            return {"valid": False, "reason": "Malicious content in URL path"}
        
        return {"valid": True, "reason": "Path validated"}
    
    def _validate_query_params(self, query_params) -> Dict[str, Any]:
        """
        Validate query parameters for security threats
        
        Args:
            query_params: Request query parameters
            
        Returns:
            Validation result
        """
        for param_name, param_value in query_params.items():
            if self._contains_malicious_content(param_value):
                return {
                    "valid": False,
                    "reason": f"Malicious content in query parameter: {param_name}"
                }
            
            # Check parameter size
            if len(param_value) > 1000:  # 1KB limit per parameter
                return {
                    "valid": False,
                    "reason": f"Query parameter too large: {param_name}"
                }
        
        return {"valid": True, "reason": "Query parameters validated"}
    
    async def _validate_request_body(self, request: Request) -> Dict[str, Any]:
        """
        Validate request body for security threats
        
        Args:
            request: HTTP request
            
        Returns:
            Validation result
        """
        try:
            # Get request body
            body = await request.body()
            
            # Check body size (10MB limit)
            if len(body) > 10 * 1024 * 1024:
                return {"valid": False, "reason": "Request body too large"}
            
            if not body:
                return {"valid": True, "reason": "Empty body validated"}
            
            # Decode and validate body content
            body_str = body.decode('utf-8', errors='ignore')
            
            if self._contains_malicious_content(body_str):
                return {"valid": False, "reason": "Malicious content in request body"}
            
            # Additional JSON validation for JSON requests
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                json_check = self._validate_json_content(body_str)
                if not json_check["valid"]:
                    return json_check
            
            return {"valid": True, "reason": "Request body validated"}
            
        except Exception as e:
            logger.error(f"❌ Body validation error: {e}")
            return {"valid": False, "reason": f"Body validation failed: {str(e)}"}
    
    def _validate_json_content(self, json_str: str) -> Dict[str, Any]:
        """
        Validate JSON content for security threats
        
        Args:
            json_str: JSON string to validate
            
        Returns:
            Validation result
        """
        try:
            # Check for JSON bomb (deeply nested structures)
            if json_str.count('{') > 100 or json_str.count('[') > 100:
                return {"valid": False, "reason": "Deeply nested JSON structure detected"}
            
            # Parse JSON to ensure it's valid
            data = json.loads(json_str)
            
            # Check for NoSQL injection in JSON values
            if self._check_nosql_injection(data):
                return {"valid": False, "reason": "NoSQL injection attempt detected"}
            
            return {"valid": True, "reason": "JSON content validated"}
            
        except json.JSONDecodeError:
            return {"valid": False, "reason": "Invalid JSON format"}
        except Exception as e:
            return {"valid": False, "reason": f"JSON validation error: {str(e)}"}
    
    def _contains_malicious_content(self, content: str) -> bool:
        """
        Check if content contains malicious patterns
        
        Args:
            content: Content string to check
            
        Returns:
            True if malicious content detected
        """
        import re
        
        content_lower = content.lower()
        
        for pattern in self.suspicious_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return True
        
        return False
    
    def _check_nosql_injection(self, data: Any) -> bool:
        """
        Check for NoSQL injection in data structure
        
        Args:
            data: Data to check (dict, list, or primitive)
            
        Returns:
            True if NoSQL injection detected
        """
        if isinstance(data, dict):
            for key, value in data.items():
                # Check for MongoDB operator injection
                if isinstance(key, str) and key.startswith('$'):
                    return True
                
                # Recursively check values
                if self._check_nosql_injection(value):
                    return True
        
        elif isinstance(data, list):
            for item in data:
                if self._check_nosql_injection(item):
                    return True
        
        elif isinstance(data, str):
            # Check for injection patterns in string values
            if self._contains_malicious_content(data):
                return True
        
        return False
    
    def _add_security_headers(self, response: Response) -> None:
        """
        Add comprehensive security headers to response
        
        Args:
            response: HTTP response to modify
        """
        security_headers = {
            # Content Security Policy
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://vercel.live; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' https://api.openai.com;"
            ),
            
            # XSS Protection
            "X-XSS-Protection": "1; mode=block",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            
            # HSTS (HTTP Strict Transport Security)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            
            # Referrer Policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Permissions Policy
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            
            # Feature Policy (legacy)
            "Feature-Policy": "geolocation 'none'; microphone 'none'; camera 'none'",
            
            # Custom security headers
            "X-Robots-Tag": "noindex, nofollow",
            "X-Permitted-Cross-Domain-Policies": "none",
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin"
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
    
    def _create_security_response(self, violation_type: str, message: str) -> JSONResponse:
        """
        Create standardized security violation response
        
        Args:
            violation_type: Type of security violation
            message: Human-readable message
            
        Returns:
            JSON response with security headers
        """
        response_data = {
            "error": "Security violation",
            "message": message,
            "type": violation_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        response = JSONResponse(
            content=response_data,
            status_code=400
        )
        
        # Add security headers
        self._add_security_headers(response)
        
        return response
    
    async def _log_security_violation(self, client_ip: str, reason: str, request: Request) -> None:
        """
        Log security violation for monitoring and analysis
        
        Args:
            client_ip: Client IP address
            reason: Violation reason
            request: HTTP request object
        """
        violation_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "client_ip": client_ip,
            "reason": reason,
            "method": request.method,
            "path": request.url.path,
            "user_agent": request.headers.get("user-agent", "unknown"),
            "referer": request.headers.get("referer", "unknown")
        }
        
        # Log to application logs
        logger.warning(f"🚨 SECURITY VIOLATION: {json.dumps(violation_data)}")
        
        # Track violation count for IP
        violation_key = f"violations:{client_ip}"
        self.security_events[violation_key] = self.security_events.get(violation_key, 0) + 1
        
        # Block IP after multiple violations
        if self.security_events[violation_key] > 10:
            self.blocked_ips.add(client_ip)
            logger.error(f"🚫 IP BLOCKED due to repeated violations: {client_ip}")
    
    async def _log_request(self, request: Request, response: Response, 
                          client_ip: str, processing_time: float) -> None:
        """
        Log successful request for monitoring
        
        Args:
            request: HTTP request
            response: HTTP response
            client_ip: Client IP address
            processing_time: Request processing time in milliseconds
        """
        # Only log in debug mode or for important endpoints
        if request.url.path.startswith("/api/auth") or processing_time > 1000:
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "client_ip": client_ip,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "processing_time_ms": round(processing_time, 2),
                "user_agent": request.headers.get("user-agent", "unknown")[:100]
            }
            
            logger.info(f"📊 REQUEST: {json.dumps(log_data)}")
