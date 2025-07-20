#!/usr/bin/env python3
"""
RPC Circuit Breaker - Prevents cascade failures in RPC calls
"""
import time
from typing import Dict, Any

class RPCCircuitBreaker:
    """Circuit breaker for RPC calls to prevent cascading failures"""

    def __init__(self, failure_threshold=3, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                print("🔄 Circuit breaker: Attempting recovery")
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
                print("✅ Circuit breaker: Recovered")
            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                print(f"⚠️ Circuit breaker: OPEN due to {self.failure_count} failures")

            raise e

    def reset(self):
        """Reset circuit breaker"""
        self.failure_count = 0
        self.state = "CLOSED"
        print("🔄 Circuit breaker: Reset")
"""
RPC Circuit Breaker for reliable blockchain connections
"""

import time
from typing import Dict, List, Optional

class RPCCircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time < self.recovery_timeout:
                raise Exception("Circuit breaker is OPEN")
            else:
                self.state = "HALF_OPEN"
        
        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise e
    
    def on_success(self):
        """Reset circuit breaker on successful call"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def on_failure(self):
        """Handle failure and potentially open circuit"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
    
    def is_open(self) -> bool:
        """Check if circuit breaker is open"""
        return self.state == "OPEN"
    
    def reset(self):
        """Manually reset circuit breaker"""
        self.failure_count = 0
        self.state = "CLOSED"
        self.last_failure_time = 0
