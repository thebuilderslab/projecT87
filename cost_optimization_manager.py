
#!/usr/bin/env python3
"""
Cost Optimization Manager for Starter Plan
Manages API usage to stay within budget constraints
"""

import os
import time
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class CostOptimizationManager:
    def __init__(self):
        """Initialize cost optimization for starter plan"""
        # Starter Plan Limits
        self.daily_credit_limit = 833  # $25/month ÷ 30 days = 833 credits/day
        self.hourly_credit_limit = 35   # 833 ÷ 24 hours ≈ 35 credits/hour
        
        # API Cost per call (based on CoinAPI pricing)
        self.coinapi_cost_per_call = 1  # 1 credit per API call
        self.coinmarketcap_cost_per_call = 1  # 1 credit per call
        
        # Usage tracking
        self.usage_file = 'api_usage_tracking.json'
        self.current_hour_usage = 0
        self.current_day_usage = 0
        self.last_reset_hour = int(time.time() // 3600)
        self.last_reset_day = int(time.time() // 86400)
        
        # Load existing usage data
        self._load_usage_data()
        
        # Adaptive intervals based on usage
        self.base_interval = 300  # 5 minutes base
        self.max_interval = 1800  # 30 minutes max
        self.current_interval = self.base_interval
        
        print(f"✅ Cost Optimization Manager initialized")
        print(f"   Daily limit: {self.daily_credit_limit} credits")
        print(f"   Hourly limit: {self.hourly_credit_limit} credits")
        print(f"   Current interval: {self.current_interval}s")
    
    def _load_usage_data(self):
        """Load usage tracking data"""
        try:
            if os.path.exists(self.usage_file):
                with open(self.usage_file, 'r') as f:
                    data = json.load(f)
                    self.current_hour_usage = data.get('current_hour_usage', 0)
                    self.current_day_usage = data.get('current_day_usage', 0)
                    self.last_reset_hour = data.get('last_reset_hour', self.last_reset_hour)
                    self.last_reset_day = data.get('last_reset_day', self.last_reset_day)
        except Exception as e:
            logger.warning(f"Could not load usage data: {e}")
    
    def _save_usage_data(self):
        """Save usage tracking data"""
        try:
            data = {
                'current_hour_usage': self.current_hour_usage,
                'current_day_usage': self.current_day_usage,
                'last_reset_hour': self.last_reset_hour,
                'last_reset_day': self.last_reset_day,
                'timestamp': time.time()
            }
            with open(self.usage_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save usage data: {e}")
    
    def can_make_api_call(self, api_type='coinapi') -> Dict:
        """Check if we can make an API call within budget"""
        current_time = time.time()
        current_hour = int(current_time // 3600)
        current_day = int(current_time // 86400)
        
        # Reset counters if needed
        if current_hour != self.last_reset_hour:
            self.current_hour_usage = 0
            self.last_reset_hour = current_hour
        
        if current_day != self.last_reset_day:
            self.current_day_usage = 0
            self.last_reset_day = current_day
        
        # Calculate cost
        cost = self.coinapi_cost_per_call if api_type == 'coinapi' else self.coinmarketcap_cost_per_call
        
        # Check limits
        hourly_ok = (self.current_hour_usage + cost) <= self.hourly_credit_limit
        daily_ok = (self.current_day_usage + cost) <= self.daily_credit_limit
        
        # Calculate next allowed time if limits exceeded
        next_allowed_time = None
        if not hourly_ok:
            next_allowed_time = (current_hour + 1) * 3600
        elif not daily_ok:
            next_allowed_time = (current_day + 1) * 86400
        
        return {
            'allowed': hourly_ok and daily_ok,
            'hourly_usage': self.current_hour_usage,
            'hourly_limit': self.hourly_credit_limit,
            'daily_usage': self.current_day_usage,
            'daily_limit': self.daily_credit_limit,
            'cost': cost,
            'next_allowed_time': next_allowed_time,
            'recommended_interval': self._calculate_optimal_interval()
        }
    
    def record_api_call(self, api_type='coinapi', success=True):
        """Record an API call for usage tracking"""
        if success:
            cost = self.coinapi_cost_per_call if api_type == 'coinapi' else self.coinmarketcap_cost_per_call
            self.current_hour_usage += cost
            self.current_day_usage += cost
            
            # Adjust interval based on usage
            self._adjust_interval()
            
            # Save usage data
            self._save_usage_data()
            
            logger.info(f"API call recorded: {api_type}, cost: {cost}, hourly: {self.current_hour_usage}/{self.hourly_credit_limit}")
    
    def _calculate_optimal_interval(self) -> int:
        """Calculate optimal interval based on current usage"""
        # Calculate remaining budget for the hour
        remaining_hourly = max(0, self.hourly_credit_limit - self.current_hour_usage)
        remaining_daily = max(0, self.daily_credit_limit - self.current_day_usage)
        
        if remaining_hourly == 0 or remaining_daily == 0:
            return self.max_interval
        
        # Calculate seconds per API call to stay within hourly limit
        seconds_remaining_in_hour = 3600 - (time.time() % 3600)
        if remaining_hourly > 0:
            optimal_interval = max(self.base_interval, int(seconds_remaining_in_hour / remaining_hourly))
        else:
            optimal_interval = self.max_interval
        
        return min(optimal_interval, self.max_interval)
    
    def _adjust_interval(self):
        """Adjust current interval based on usage patterns"""
        self.current_interval = self._calculate_optimal_interval()
    
    def get_usage_summary(self) -> Dict:
        """Get current usage summary"""
        usage_percentage_hourly = (self.current_hour_usage / self.hourly_credit_limit) * 100
        usage_percentage_daily = (self.current_day_usage / self.daily_credit_limit) * 100
        
        return {
            'hourly_usage': self.current_hour_usage,
            'hourly_limit': self.hourly_credit_limit,
            'hourly_percentage': usage_percentage_hourly,
            'daily_usage': self.current_day_usage,
            'daily_limit': self.daily_credit_limit,
            'daily_percentage': usage_percentage_daily,
            'current_interval': self.current_interval,
            'recommended_interval': self._calculate_optimal_interval(),
            'budget_status': 'healthy' if usage_percentage_hourly < 80 else 'warning' if usage_percentage_hourly < 95 else 'critical'
        }
