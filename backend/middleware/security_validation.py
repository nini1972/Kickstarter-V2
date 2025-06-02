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