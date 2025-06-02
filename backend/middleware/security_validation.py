"""
🛡️ Input Validation and Security Middleware
Comprehensive protection against injection attacks and malicious input
"""

import re
import os
import json
import time
import logging
from typing import Any, Dict, List, Optional, Set
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import bleach
from urllib.parse import unquote

logger = logging.getLogger(__name__)

class SecurityValidationMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware for input validation and sanitization
    Prevents NoSQL injection, XSS, and data corruption attacks
    """
    
    # Dangerous MongoDB operators that could be used in NoSQL injection
    DANGEROUS_MONGO_OPERATORS = {
        '$where', '$regex', '$ne', '$gt', '$gte', '$lt', '$lte', '$in', '$nin',
        '$exists', '$type', '$mod', '$all', '$size', '$elemMatch', '$slice',
        '$comment', '$meta', '$natural', '$hint', '$maxScan', '$max', '$min',
        '$orderby', '$query', '$returnKey', '$showDiskLoc', '$snapshot', '$explain'
    }
    
    # Dangerous keywords that might indicate SQL/NoSQL injection attempts
    DANGEROUS_KEYWORDS = {
        'javascript:', 'vbscript:', 'onload', 'onerror', 'onclick', 'onmouseover',
        'eval(', 'setTimeout(', 'setInterval(', 'Function(', 'constructor',
        'prototype', '__proto__', 'script', 'iframe', 'object', 'embed',
        'drop', 'delete', 'truncate', 'alter', 'create', 'insert', 'update',
        'union', 'select', 'from', 'where', 'having', 'group by', 'order by'
    }
    
    # Paths that require special handling
    EXCLUDED_PATHS = {
        '/docs', '/redoc', '/openapi.json', '/api/health'
    }
    
    def __init__(self, app, max_content_length: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_content_length = max_content_length
        
    async def dispatch(self, request: Request, call_next):
        """Main middleware dispatcher with comprehensive security checks"""
        
        # Skip validation for excluded paths
        if any(request.url.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return await call_next(request)
        
        start_time = time.time()
        client_ip = self.get_client_ip(request)
        
        try:
            # Step 1: Basic request validation
            await self._validate_request_basics(request, client_ip)
            
            # Step 2: Validate and sanitize headers
            await self._validate_headers(request, client_ip)
            
            # Step 3: Validate and sanitize query parameters
            await self._validate_query_params(request, client_ip)
            
            # Step 4: Validate and sanitize request body
            request = await self._validate_request_body(request, client_ip)
            
            # Process the request
            response = await call_next(request)
            
            # Log successful request
            processing_time = time.time() - start_time
            logger.info(f"✅ Request validated successfully: {request.method} {request.url.path} "
                       f"from {client_ip} in {processing_time:.3f}s")
            
            return response
            
        except HTTPException as e:
            logger.warning(f"🚨 Security validation failed: {e.detail} from {client_ip}")
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": "Validation Failed",
                    "message": e.detail,
                    "type": "security_validation_error"
                }
            )
        except Exception as e:
            logger.error(f"❌ Validation middleware error: {e} from {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal Security Error",
                    "message": "Request validation failed"
                }
            )
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address with proxy support"""
        # Check for forwarded headers first (common in production)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    async def _validate_request_basics(self, request: Request, client_ip: str):
        """Basic request validation (method, content length, etc.)"""
        
        # Validate HTTP method
        allowed_methods = {"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"}
        if request.method not in allowed_methods:
            raise HTTPException(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                detail=f"Method {request.method} not allowed"
            )
        
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_content_length:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Request body too large. Maximum allowed: {self.max_content_length} bytes"
            )
    
    async def _validate_headers(self, request: Request, client_ip: str):
        """Validate and sanitize HTTP headers"""
        
        # Check for suspicious headers
        suspicious_headers = {
            "x-forwarded-host", "x-originating-ip", "x-remote-ip", 
            "x-remote-addr", "x-cluster-client-ip"
        }
        
        for header_name, header_value in request.headers.items():
            header_name_lower = header_name.lower()
            
            # Basic header validation
            if len(header_name) > 100 or len(header_value) > 4096:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Header too long"
                )
            
            # Check for injection attempts in headers
            if self._contains_dangerous_patterns(header_value):
                logger.warning(f"🚨 Dangerous pattern in header {header_name}: {header_value[:100]}... from {client_ip}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid characters in header {header_name}"
                )
            
            # Check for suspicious headers that might indicate spoofing
            if header_name_lower in suspicious_headers:
                logger.warning(f"⚠️  Suspicious header {header_name} from {client_ip}")
    
    async def _validate_query_params(self, request: Request, client_ip: str):
        """Validate and sanitize query parameters"""
        
        query_params = dict(request.query_params)
        
        for param_name, param_value in query_params.items():
            # Validate parameter names
            if not re.match(r'^[a-zA-Z0-9_\-\.]+$', param_name):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid parameter name: {param_name}"
                )
            
            # Decode URL-encoded values
            try:
                decoded_value = unquote(param_value)
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid URL encoding in parameter: {param_name}"
                )
            
            # Check for NoSQL injection patterns
            if self._contains_nosql_injection(decoded_value):
                logger.warning(f"🚨 NoSQL injection attempt in query param {param_name}: {decoded_value[:100]}... from {client_ip}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid query parameter: {param_name}"
                )
            
            # Check for dangerous patterns
            if self._contains_dangerous_patterns(decoded_value):
                logger.warning(f"🚨 Dangerous pattern in query param {param_name}: {decoded_value[:100]}... from {client_ip}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid characters in parameter: {param_name}"
                )
    
    async def _validate_request_body(self, request: Request, client_ip: str) -> Request:
        """Validate and sanitize request body"""
        
        # Skip body validation for GET requests
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return request
        
        content_type = request.headers.get("content-type", "").lower()
        
        # Only validate JSON content
        if not content_type.startswith("application/json"):
            return request
        
        try:
            # Read and parse body
            body = await request.body()
            if not body:
                return request
            
            # Parse JSON
            try:
                json_data = json.loads(body.decode('utf-8'))
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid JSON: {str(e)}"
                )
            
            # Validate and sanitize JSON data
            sanitized_data = self._validate_json_data(json_data, client_ip)
            
            # Create new request with sanitized body
            sanitized_body = json.dumps(sanitized_data).encode('utf-8')
            
            # Replace the request body
            async def receive():
                return {"type": "http.request", "body": sanitized_body}
            
            request._receive = receive
            
            return request
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Body validation error: {e} from {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid request body"
            )
    
    def _validate_json_data(self, data: Any, client_ip: str, path: str = "root") -> Any:
        """Recursively validate and sanitize JSON data"""
        
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                # Validate key names
                if not isinstance(key, str):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid key type at {path}.{key}"
                    )
                
                # Check for dangerous key patterns
                if self._contains_nosql_injection(key):
                    logger.warning(f"🚨 NoSQL injection in key {path}.{key}: {key} from {client_ip}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid key name: {key}"
                    )
                
                # Validate key length and pattern
                if len(key) > 100 or not re.match(r'^[a-zA-Z0-9_\-\.@\s]+$', key):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid key format: {key}"
                    )
                
                # Recursively validate value
                sanitized[key] = self._validate_json_data(value, client_ip, f"{path}.{key}")
            
            return sanitized
            
        elif isinstance(data, list):
            return [self._validate_json_data(item, client_ip, f"{path}[{i}]") 
                   for i, item in enumerate(data)]
            
        elif isinstance(data, str):
            return self._sanitize_string(data, client_ip, path)
            
        elif isinstance(data, (int, float, bool)) or data is None:
            return data
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported data type at {path}: {type(data)}"
            )
    
    def _sanitize_string(self, value: str, client_ip: str, path: str = "") -> str:
        """Sanitize string values"""
        
        # Check length limits
        if len(value) > 10000:  # 10KB limit for strings
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"String too long at {path}: maximum 10000 characters"
            )
        
        # Check for NoSQL injection
        if self._contains_nosql_injection(value):
            logger.warning(f"🚨 NoSQL injection in string at {path}: {value[:100]}... from {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid string content at {path}"
            )
        
        # Check for dangerous patterns
        if self._contains_dangerous_patterns(value):
            logger.warning(f"🚨 Dangerous pattern in string at {path}: {value[:100]}... from {client_ip}")
            # For HTML content, use bleach to sanitize
            if any(tag in value.lower() for tag in ['<script', '<iframe', '<object', '<embed']):
                sanitized = bleach.clean(value, tags=[], attributes={}, strip=True)
                if sanitized != value:
                    logger.warning(f"🧹 HTML sanitized at {path} from {client_ip}")
                return sanitized
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid characters in string at {path}"
                )
        
        return value
    
    def _contains_nosql_injection(self, value: str) -> bool:
        """Check if string contains NoSQL injection patterns"""
        value_lower = value.lower()
        
        # Check for MongoDB operators
        for operator in self.DANGEROUS_MONGO_OPERATORS:
            if operator in value_lower:
                return True
        
        # Check for JSON-like injection patterns
        nosql_patterns = [
            r'\$[a-zA-Z]+\s*:',           # MongoDB operators like $where:
            r'\{\s*\$[a-zA-Z]+',          # {$operator
            r'"\s*\$[a-zA-Z]+\s*"',       # "$operator"
            r'this\.',                     # JavaScript 'this.' references
            r'return\s+',                  # JavaScript return statements
            r'function\s*\(',              # JavaScript functions
            r'/.*?/[gimuy]*',              # Regular expressions
        ]
        
        for pattern in nosql_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        
        return False
    
    def _contains_dangerous_patterns(self, value: str) -> bool:
        """Check if string contains dangerous patterns"""
        value_lower = value.lower()
        
        # Check for dangerous keywords
        for keyword in self.DANGEROUS_KEYWORDS:
            if keyword in value_lower:
                return True
        
        # Check for suspicious patterns
        dangerous_patterns = [
            r'<\s*script[^>]*>',                    # Script tags
            r'javascript\s*:',                      # JavaScript protocol
            r'on\w+\s*=',                          # Event handlers
            r'(eval|setTimeout|setInterval)\s*\(',  # Dangerous JS functions
            r'[\'"]\s*\+\s*[\'"]',                 # String concatenation
            r'(union|select|from|where|drop|delete|insert|update)\s+', # SQL keywords
            r'\/\*.*?\*\/',                        # SQL comments
            r'--.*$',                              # SQL line comments
            r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', # Control characters
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, value, re.IGNORECASE | re.MULTILINE):
                return True
        
        return False


# Input validation utility functions
class InputValidator:
    """Utility class for additional input validation"""
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate and sanitize email addresses"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        return email.lower().strip()
    
    @staticmethod
    def validate_username(username: str) -> str:
        """Validate username format"""
        if not re.match(r'^[a-zA-Z0-9_-]{3,30}$', username):
            raise ValueError("Username must be 3-30 characters, alphanumeric, underscore, or hyphen only")
        return username.strip()
    
    @staticmethod
    def validate_password(password: str) -> None:
        """Validate password strength"""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r'[A-Z]', password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r'\d', password):
            raise ValueError("Password must contain at least one number")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError("Password must contain at least one special character")
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage"""
        # Remove dangerous characters
        sanitized = re.sub(r'[^\w\-_\.]', '_', filename)
        # Remove consecutive dots and underscores
        sanitized = re.sub(r'[._]{2,}', '_', sanitized)
        # Limit length
        if len(sanitized) > 255:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:255-len(ext)] + ext
        return sanitized

# Export the middleware and utilities
__all__ = ['SecurityValidationMiddleware', 'InputValidator']