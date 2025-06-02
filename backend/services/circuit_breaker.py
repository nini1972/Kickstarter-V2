"""
⚡ Circuit Breaker Implementation
Enterprise-grade circuit breaker pattern for external API resilience
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Callable, Any, Optional, Dict, List
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"        # Normal operation
    OPEN = "open"           # Circuit is open, failing fast
    HALF_OPEN = "half_open" # Testing if service has recovered

class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior"""
    
    def __init__(
        self,
        failure_threshold: int = 5,           # Failures before opening circuit
        success_threshold: int = 3,           # Successes before closing from half-open
        timeout_duration: int = 60,           # Seconds before trying half-open
        call_timeout: int = 30,               # Individual call timeout
        expected_exception: tuple = (Exception,)  # Exceptions that count as failures
    ):
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold  
        self.timeout_duration = timeout_duration
        self.call_timeout = call_timeout
        self.expected_exception = expected_exception

class CircuitBreakerStats:
    """Statistics for circuit breaker monitoring"""
    
    def __init__(self):
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.circuit_opens = 0
        self.timeouts = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None
        self.state_changes: List[Dict] = []
    
    def record_success(self):
        """Record a successful call"""
        self.total_calls += 1
        self.successful_calls += 1
        self.last_success_time = datetime.utcnow()
    
    def record_failure(self):
        """Record a failed call"""
        self.total_calls += 1
        self.failed_calls += 1
        self.last_failure_time = datetime.utcnow()
    
    def record_timeout(self):
        """Record a timeout"""
        self.timeouts += 1
        self.record_failure()
    
    def record_circuit_open(self):
        """Record circuit opening"""
        self.circuit_opens += 1
    
    def record_state_change(self, old_state: CircuitState, new_state: CircuitState, reason: str):
        """Record state change for monitoring"""
        self.state_changes.append({
            "timestamp": datetime.utcnow().isoformat(),
            "old_state": old_state.value,
            "new_state": new_state.value,
            "reason": reason
        })
        # Keep only last 50 state changes
        if len(self.state_changes) > 50:
            self.state_changes = self.state_changes[-50:]
    
    def get_success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_calls == 0:
            return 100.0
        return (self.successful_calls / self.total_calls) * 100
    
    def get_stats_dict(self) -> Dict[str, Any]:
        """Get statistics as dictionary"""
        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "success_rate": round(self.get_success_rate(), 2),
            "circuit_opens": self.circuit_opens,
            "timeouts": self.timeouts,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_success": self.last_success_time.isoformat() if self.last_success_time else None,
            "recent_state_changes": self.state_changes[-10:]  # Last 10 changes
        }

class CircuitBreaker:
    """
    Circuit breaker implementation for external service calls
    
    Implements the circuit breaker pattern to prevent cascade failures
    when external services are experiencing issues.
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()
        
        # State management
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.next_attempt_time: Optional[float] = None
        
        # Thread safety
        self._lock = asyncio.Lock()
        
        logger.info(f"🔧 Circuit breaker '{name}' initialized with config: "
                   f"failure_threshold={self.config.failure_threshold}, "
                   f"timeout_duration={self.config.timeout_duration}s")
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function call through the circuit breaker
        
        Args:
            func: Async function to execute
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function call
            
        Raises:
            CircuitBreakerOpenError: When circuit is open
            Exception: Original exception from the function call
        """
        async with self._lock:
            # Check if circuit should remain open
            if self.state == CircuitState.OPEN:
                if not self._should_attempt_reset():
                    self.stats.record_failure()
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is OPEN. "
                        f"Next attempt allowed at {datetime.fromtimestamp(self.next_attempt_time)}"
                    )
                else:
                    # Move to half-open state
                    await self._change_state(CircuitState.HALF_OPEN, "Timeout expired, testing service")
        
        # Execute the function call
        try:
            # Apply timeout to the call
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.call_timeout
            )
            
            # Call succeeded
            await self._on_success()
            return result
            
        except asyncio.TimeoutError:
            await self._on_timeout()
            raise CircuitBreakerTimeoutError(
                f"Call to '{self.name}' timed out after {self.config.call_timeout}s"
            )
        except self.config.expected_exception as e:
            await self._on_failure()
            raise e
    
    async def _on_success(self):
        """Handle successful call"""
        self.stats.record_success()
        
        async with self._lock:
            self.failure_count = 0
            
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    await self._change_state(CircuitState.CLOSED, "Success threshold reached")
            elif self.state == CircuitState.OPEN:
                # This shouldn't happen, but handle gracefully
                await self._change_state(CircuitState.HALF_OPEN, "Unexpected success in OPEN state")
    
    async def _on_failure(self):
        """Handle failed call"""
        self.stats.record_failure()
        
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                # Failed while testing, go back to open
                await self._change_state(CircuitState.OPEN, "Failure during half-open test")
                self._set_next_attempt_time()
            elif self.state == CircuitState.CLOSED:
                if self.failure_count >= self.config.failure_threshold:
                    await self._change_state(CircuitState.OPEN, "Failure threshold exceeded")
                    self.stats.record_circuit_open()
                    self._set_next_attempt_time()
    
    async def _on_timeout(self):
        """Handle timeout"""
        self.stats.record_timeout()
        await self._on_failure()  # Treat timeout as failure
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.next_attempt_time is None:
            return True
        return time.time() >= self.next_attempt_time
    
    def _set_next_attempt_time(self):
        """Set next attempt time based on configuration"""
        self.next_attempt_time = time.time() + self.config.timeout_duration
    
    async def _change_state(self, new_state: CircuitState, reason: str):
        """Change circuit state and log the change"""
        old_state = self.state
        self.state = new_state
        
        # Reset counters based on new state
        if new_state == CircuitState.CLOSED:
            self.failure_count = 0
            self.success_count = 0
            self.next_attempt_time = None
        elif new_state == CircuitState.HALF_OPEN:
            self.success_count = 0
        
        # Record state change
        self.stats.record_state_change(old_state, new_state, reason)
        
        # Log state change
        logger.warning(f"🔄 Circuit breaker '{self.name}' state changed: "
                      f"{old_state.value} → {new_state.value} ({reason})")
    
    def get_state(self) -> CircuitState:
        """Get current circuit state"""
        return self.state
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout_duration": self.config.timeout_duration,
                "call_timeout": self.config.call_timeout
            },
            "next_attempt_time": datetime.fromtimestamp(self.next_attempt_time).isoformat() if self.next_attempt_time else None,
            "stats": self.stats.get_stats_dict()
        }
    
    async def reset(self):
        """Manually reset circuit breaker to closed state"""
        async with self._lock:
            await self._change_state(CircuitState.CLOSED, "Manual reset")
            logger.info(f"🔄 Circuit breaker '{self.name}' manually reset")

class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    pass

class CircuitBreakerTimeoutError(Exception):
    """Exception raised when circuit breaker call times out"""
    pass

# Exponential backoff utility
class ExponentialBackoff:
    """Exponential backoff implementation for retry logic"""
    
    def __init__(
        self,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        multiplier: float = 2.0,
        jitter: bool = True
    ):
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.jitter = jitter
        self.attempt = 0
    
    def next_delay(self) -> float:
        """Calculate next delay with exponential backoff"""
        import random
        
        delay = min(self.initial_delay * (self.multiplier ** self.attempt), self.max_delay)
        
        if self.jitter:
            # Add jitter to prevent thundering herd
            delay = delay * (0.5 + random.random() * 0.5)
        
        self.attempt += 1
        return delay
    
    def reset(self):
        """Reset attempt counter"""
        self.attempt = 0

# Global circuit breaker registry for monitoring
class CircuitBreakerRegistry:
    """Registry for all circuit breakers in the application"""
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
    
    def register(self, circuit_breaker: CircuitBreaker):
        """Register a circuit breaker"""
        self.breakers[circuit_breaker.name] = circuit_breaker
        logger.info(f"📝 Registered circuit breaker: {circuit_breaker.name}")
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all registered circuit breakers"""
        return {
            "total_breakers": len(self.breakers),
            "breakers": {name: cb.get_stats() for name, cb in self.breakers.items()},
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def get_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name"""
        return self.breakers.get(name)
    
    async def reset_all(self):
        """Reset all circuit breakers"""
        for circuit_breaker in self.breakers.values():
            await circuit_breaker.reset()
        logger.info(f"🔄 Reset all {len(self.breakers)} circuit breakers")

# Global registry instance
circuit_registry = CircuitBreakerRegistry()
