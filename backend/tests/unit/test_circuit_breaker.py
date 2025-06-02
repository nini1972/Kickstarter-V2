"""
🧪 Circuit Breaker Tests
Testing enterprise-grade circuit breaker protection for external APIs
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from services.circuit_breaker import (
    CircuitBreaker, CircuitBreakerRegistry, CircuitBreakerState,
    ExponentialBackoff, CircuitBreakerError
)


class TestCircuitBreaker:
    """Test core circuit breaker functionality"""
    
    @pytest.fixture
    def circuit_breaker(self):
        """Create a circuit breaker for testing"""
        return CircuitBreaker(
            name="test_service",
            failure_threshold=3,
            success_threshold=2,
            timeout_duration=60,
            call_timeout=10
        )
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state_success(self, circuit_breaker):
        """Test circuit breaker in closed state with successful calls"""
        async def successful_operation():
            return "success"
        
        # Circuit breaker should start in closed state
        assert circuit_breaker.get_state() == CircuitBreakerState.CLOSED
        
        # Successful call should work normally
        result = await circuit_breaker.call(successful_operation)
        assert result == "success"
        
        # State should remain closed
        assert circuit_breaker.get_state() == CircuitBreakerState.CLOSED
        
        # Statistics should reflect success
        stats = circuit_breaker.get_stats()
        assert stats["stats"]["total_calls"] == 1
        assert stats["stats"]["success_count"] == 1
        assert stats["stats"]["failure_count"] == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_failure_threshold(self, circuit_breaker):
        """Test circuit breaker opens after reaching failure threshold"""
        async def failing_operation():
            raise Exception("Service unavailable")
        
        # Make failures up to threshold
        for i in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_operation)
            
            if i < 2:  # Not yet at threshold
                assert circuit_breaker.get_state() == CircuitBreakerState.CLOSED
            else:  # At threshold, should open
                assert circuit_breaker.get_state() == CircuitBreakerState.OPEN
        
        # Verify statistics
        stats = circuit_breaker.get_stats()
        assert stats["stats"]["failure_count"] == 3
        assert stats["stats"]["success_rate"] == 0.0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_open_state_rejection(self, circuit_breaker):
        """Test circuit breaker rejects calls when open"""
        # Force circuit breaker to open state
        circuit_breaker._state = CircuitBreakerState.OPEN
        circuit_breaker._failure_count = 3
        circuit_breaker._last_failure_time = datetime.utcnow()
        
        async def any_operation():
            return "should not execute"
        
        # Call should be rejected immediately
        with pytest.raises(CircuitBreakerError) as exc_info:
            await circuit_breaker.call(any_operation)
        
        assert "Circuit breaker is OPEN" in str(exc_info.value)
        
        # Statistics should show rejection
        stats = circuit_breaker.get_stats()
        assert stats["stats"]["rejected_calls"] == 1
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_transition(self, circuit_breaker):
        """Test circuit breaker transitions to half-open after timeout"""
        # Force circuit breaker to open state with past failure time
        circuit_breaker._state = CircuitBreakerState.OPEN
        circuit_breaker._failure_count = 3
        circuit_breaker._last_failure_time = datetime.utcnow() - timedelta(seconds=61)
        
        async def test_operation():
            return "test success"
        
        # First call after timeout should transition to half-open
        result = await circuit_breaker.call(test_operation)
        assert result == "test success"
        assert circuit_breaker.get_state() == CircuitBreakerState.HALF_OPEN
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_to_closed(self, circuit_breaker):
        """Test circuit breaker transitions from half-open to closed on success"""
        # Set to half-open state
        circuit_breaker._state = CircuitBreakerState.HALF_OPEN
        circuit_breaker._success_count = 1  # Need 2 successes total
        
        async def successful_operation():
            return "success"
        
        # One more success should close the circuit
        result = await circuit_breaker.call(successful_operation)
        assert result == "success"
        assert circuit_breaker.get_state() == CircuitBreakerState.CLOSED
        
        # Counters should be reset
        stats = circuit_breaker.get_stats()
        assert stats["stats"]["failure_count"] == 0
        assert stats["stats"]["success_count"] == 2
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_to_open(self, circuit_breaker):
        """Test circuit breaker transitions from half-open to open on failure"""
        # Set to half-open state
        circuit_breaker._state = CircuitBreakerState.HALF_OPEN
        
        async def failing_operation():
            raise Exception("Still failing")
        
        # Failure should immediately open the circuit
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_operation)
        
        assert circuit_breaker.get_state() == CircuitBreakerState.OPEN
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_call_timeout(self, circuit_breaker):
        """Test circuit breaker enforces call timeout"""
        async def slow_operation():
            await asyncio.sleep(15)  # Longer than 10s timeout
            return "should timeout"
        
        # Call should timeout and be treated as failure
        with pytest.raises(asyncio.TimeoutError):
            await circuit_breaker.call(slow_operation)
        
        # Should count as failure
        stats = circuit_breaker.get_stats()
        assert stats["stats"]["failure_count"] == 1
        assert stats["stats"]["timeout_count"] == 1
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_manual_reset(self, circuit_breaker):
        """Test manual circuit breaker reset"""
        # Force to open state
        circuit_breaker._state = CircuitBreakerState.OPEN
        circuit_breaker._failure_count = 5
        
        # Reset should return to closed state
        await circuit_breaker.reset()
        
        assert circuit_breaker.get_state() == CircuitBreakerState.CLOSED
        stats = circuit_breaker.get_stats()
        assert stats["stats"]["failure_count"] == 0
        assert stats["stats"]["success_count"] == 0


class TestExponentialBackoff:
    """Test exponential backoff functionality"""
    
    @pytest.fixture
    def backoff(self):
        """Create exponential backoff for testing"""
        return ExponentialBackoff(
            initial_delay=1.0,
            max_delay=60.0,
            multiplier=2.0,
            jitter=True
        )
    
    def test_exponential_backoff_progression(self, backoff):
        """Test exponential backoff delay progression"""
        delays = []
        
        # Calculate several backoff delays
        for i in range(5):
            delay = backoff.calculate_delay(i)
            delays.append(delay)
        
        # Delays should generally increase (with jitter, may not be exact)
        assert delays[0] >= 0.5 and delays[0] <= 1.5  # Around 1.0 with jitter
        assert delays[1] >= 1.5 and delays[1] <= 2.5  # Around 2.0 with jitter
        assert delays[4] >= 8.0 and delays[4] <= 16.5  # Around 16.0 with jitter
    
    def test_exponential_backoff_max_delay(self, backoff):
        """Test exponential backoff respects maximum delay"""
        # High attempt number should cap at max_delay
        delay = backoff.calculate_delay(10)  # Very high attempt
        assert delay <= 60.0  # Should not exceed max_delay
    
    def test_exponential_backoff_no_jitter(self):
        """Test exponential backoff without jitter"""
        backoff = ExponentialBackoff(
            initial_delay=2.0,
            max_delay=32.0,
            multiplier=2.0,
            jitter=False
        )
        
        # Without jitter, delays should be exact
        assert backoff.calculate_delay(0) == 2.0
        assert backoff.calculate_delay(1) == 4.0
        assert backoff.calculate_delay(2) == 8.0
        assert backoff.calculate_delay(3) == 16.0
        assert backoff.calculate_delay(4) == 32.0  # Capped at max
        assert backoff.calculate_delay(5) == 32.0  # Still capped


class TestCircuitBreakerRegistry:
    """Test circuit breaker registry functionality"""
    
    @pytest.fixture
    def registry(self):
        """Create circuit breaker registry for testing"""
        return CircuitBreakerRegistry()
    
    def test_registry_create_breaker(self, registry):
        """Test creating circuit breaker through registry"""
        breaker = registry.create_breaker(
            name="test_api",
            failure_threshold=5,
            success_threshold=3,
            timeout_duration=120
        )
        
        assert breaker.name == "test_api"
        assert breaker.failure_threshold == 5
        assert breaker.success_threshold == 3
        assert breaker.timeout_duration == 120
        
        # Should be stored in registry
        assert "test_api" in registry.breakers
        assert registry.get_breaker("test_api") == breaker
    
    def test_registry_get_nonexistent_breaker(self, registry):
        """Test getting non-existent circuit breaker"""
        breaker = registry.get_breaker("nonexistent")
        assert breaker is None
    
    def test_registry_get_all_stats(self, registry):
        """Test getting statistics for all circuit breakers"""
        # Create multiple breakers
        breaker1 = registry.create_breaker("api1", failure_threshold=3)
        breaker2 = registry.create_breaker("api2", failure_threshold=5)
        
        # Simulate some activity
        breaker1._success_count = 10
        breaker1._failure_count = 2
        breaker2._success_count = 5
        breaker2._failure_count = 1
        
        stats = registry.get_all_stats()
        
        assert "api1" in stats
        assert "api2" in stats
        assert stats["api1"]["stats"]["success_count"] == 10
        assert stats["api2"]["stats"]["failure_count"] == 1
    
    @pytest.mark.asyncio
    async def test_registry_reset_all(self, registry):
        """Test resetting all circuit breakers"""
        # Create breakers and force them to open state
        breaker1 = registry.create_breaker("api1", failure_threshold=2)
        breaker2 = registry.create_breaker("api2", failure_threshold=2)
        
        breaker1._state = CircuitBreakerState.OPEN
        breaker1._failure_count = 5
        breaker2._state = CircuitBreakerState.OPEN
        breaker2._failure_count = 3
        
        # Reset all
        await registry.reset_all()
        
        # Both should be closed with reset stats
        assert breaker1.get_state() == CircuitBreakerState.CLOSED
        assert breaker2.get_state() == CircuitBreakerState.CLOSED
        assert breaker1._failure_count == 0
        assert breaker2._failure_count == 0


class TestCircuitBreakerIntegration:
    """Test circuit breaker integration scenarios"""
    
    @pytest.fixture
    def mock_external_service(self):
        """Mock external service for testing"""
        service = MagicMock()
        
        # Configure service behavior
        service.call_count = 0
        service.should_fail = False
        service.response_delay = 0.1
        
        async def mock_call():
            service.call_count += 1
            await asyncio.sleep(service.response_delay)
            
            if service.should_fail:
                raise Exception(f"Service error #{service.call_count}")
            
            return f"Success #{service.call_count}"
        
        service.call = mock_call
        return service
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_service_recovery(self, mock_external_service):
        """Test circuit breaker handles service recovery"""
        circuit_breaker = CircuitBreaker(
            name="recovery_test",
            failure_threshold=2,
            success_threshold=2,
            timeout_duration=1  # Short timeout for quick recovery
        )
        
        # 1. Service starts failing
        mock_external_service.should_fail = True
        
        # Trigger failures to open circuit
        for _ in range(2):
            with pytest.raises(Exception):
                await circuit_breaker.call(mock_external_service.call)
        
        assert circuit_breaker.get_state() == CircuitBreakerState.OPEN
        
        # 2. Service recovers
        mock_external_service.should_fail = False
        
        # Wait for timeout (circuit should go half-open)
        await asyncio.sleep(1.1)
        
        # 3. Test service recovery through half-open state
        result1 = await circuit_breaker.call(mock_external_service.call)
        assert "Success" in result1
        assert circuit_breaker.get_state() == CircuitBreakerState.HALF_OPEN
        
        # Second success should close circuit
        result2 = await circuit_breaker.call(mock_external_service.call)
        assert "Success" in result2
        assert circuit_breaker.get_state() == CircuitBreakerState.CLOSED
        
        # Verify service was called correctly
        assert mock_external_service.call_count == 4  # 2 failures + 2 successes
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_with_retries(self, mock_external_service):
        """Test circuit breaker with retry logic"""
        circuit_breaker = CircuitBreaker(
            name="retry_test",
            failure_threshold=3,
            call_timeout=5
        )
        
        backoff = ExponentialBackoff(initial_delay=0.1, max_delay=1.0)
        
        async def service_with_retries():
            """Service call with exponential backoff retries"""
            max_retries = 3
            
            for attempt in range(max_retries):
                try:
                    return await circuit_breaker.call(mock_external_service.call)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    
                    delay = backoff.calculate_delay(attempt)
                    await asyncio.sleep(delay)
        
        # Test with intermittent failures
        mock_external_service.should_fail = True
        
        # First call should fail after retries
        with pytest.raises(Exception):
            await service_with_retries()
        
        # Service recovers
        mock_external_service.should_fail = False
        
        # Should succeed after retries
        result = await service_with_retries()
        assert "Success" in result
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_concurrent_calls(self, mock_external_service):
        """Test circuit breaker with concurrent calls"""
        circuit_breaker = CircuitBreaker(
            name="concurrent_test",
            failure_threshold=5,
            call_timeout=2
        )
        
        # Configure service for success
        mock_external_service.should_fail = False
        mock_external_service.response_delay = 0.5
        
        # Make concurrent calls
        tasks = []
        for i in range(10):
            task = asyncio.create_task(
                circuit_breaker.call(mock_external_service.call)
            )
            tasks.append(task)
        
        # Wait for all calls to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed
        success_count = sum(1 for r in results if isinstance(r, str) and "Success" in r)
        assert success_count == 10
        
        # Verify statistics
        stats = circuit_breaker.get_stats()
        assert stats["stats"]["total_calls"] == 10
        assert stats["stats"]["success_count"] == 10
        assert circuit_breaker.get_state() == CircuitBreakerState.CLOSED


class TestCircuitBreakerPerformance:
    """Test circuit breaker performance characteristics"""
    
    @pytest.mark.benchmark
    def test_circuit_breaker_overhead(self, benchmark):
        """Benchmark circuit breaker overhead"""
        circuit_breaker = CircuitBreaker(
            name="performance_test",
            failure_threshold=10
        )
        
        async def fast_operation():
            return "fast"
        
        async def run_operation():
            return await circuit_breaker.call(fast_operation)
        
        # Benchmark the overhead
        result = benchmark(asyncio.run, run_operation())
        assert result == "fast"
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_memory_usage(self):
        """Test circuit breaker memory usage with many operations"""
        circuit_breaker = CircuitBreaker(
            name="memory_test",
            failure_threshold=1000
        )
        
        async def dummy_operation():
            return "ok"
        
        # Perform many operations
        for _ in range(1000):
            await circuit_breaker.call(dummy_operation)
        
        # Statistics should be maintained efficiently
        stats = circuit_breaker.get_stats()
        assert stats["stats"]["total_calls"] == 1000
        assert stats["stats"]["success_count"] == 1000
        
        # Memory usage should be reasonable (no unbounded growth)
        # This is more of a sanity check than a precise measurement
        assert len(str(stats)) < 10000  # Reasonable serialized size


class TestCircuitBreakerErrorHandling:
    """Test circuit breaker error handling edge cases"""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_exception_types(self):
        """Test circuit breaker handles different exception types"""
        circuit_breaker = CircuitBreaker(
            name="exception_test",
            failure_threshold=1
        )
        
        # Test different exception types
        async def timeout_error():
            raise asyncio.TimeoutError("Operation timed out")
        
        async def value_error():
            raise ValueError("Invalid value")
        
        async def connection_error():
            raise ConnectionError("Cannot connect")
        
        # All exception types should be counted as failures
        for operation in [timeout_error, value_error, connection_error]:
            with pytest.raises(Exception):
                await circuit_breaker.call(operation)
        
        # Circuit should be open after multiple failures
        assert circuit_breaker.get_state() == CircuitBreakerState.OPEN
        
        # All should be counted as failures
        stats = circuit_breaker.get_stats()
        assert stats["stats"]["failure_count"] == 3
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_invalid_configuration(self):
        """Test circuit breaker with invalid configuration"""
        # Invalid failure threshold
        with pytest.raises(ValueError):
            CircuitBreaker(
                name="invalid_test",
                failure_threshold=0  # Must be positive
            )
        
        # Invalid timeout duration
        with pytest.raises(ValueError):
            CircuitBreaker(
                name="invalid_test",
                failure_threshold=3,
                timeout_duration=-1  # Must be positive
            )
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_state_consistency(self):
        """Test circuit breaker maintains state consistency"""
        circuit_breaker = CircuitBreaker(
            name="consistency_test",
            failure_threshold=2,
            success_threshold=2
        )
        
        # Simulate rapid state changes
        async def sometimes_failing_operation():
            # Randomly succeed or fail
            import random
            if random.random() < 0.5:
                raise Exception("Random failure")
            return "success"
        
        # Run many operations to test state consistency
        results = []
        for _ in range(100):
            try:
                result = await circuit_breaker.call(sometimes_failing_operation)
                results.append(("success", result))
            except CircuitBreakerError:
                results.append(("rejected", None))
            except Exception as e:
                results.append(("failed", str(e)))
        
        # Verify state is consistent with statistics
        stats = circuit_breaker.get_stats()
        success_count = len([r for r in results if r[0] == "success"])
        failed_count = len([r for r in results if r[0] == "failed"])
        rejected_count = len([r for r in results if r[0] == "rejected"])
        
        # Statistics should match actual results
        assert stats["stats"]["success_count"] == success_count
        assert stats["stats"]["rejected_calls"] == rejected_count
        
        # Total calls should exclude rejected calls
        expected_total = success_count + failed_count
        assert stats["stats"]["total_calls"] == expected_total
