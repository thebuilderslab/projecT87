#!/usr/bin/env python3
"""
Market Data Scheduler for Hybrid Monitoring Architecture
Manages intelligent API usage while maintaining responsive monitoring
"""

import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class DataSource(Enum):
    ONCHAIN = "onchain"  # Free/cheap on-chain sources
    PAID_API = "paid_api"  # CoinAPI, CoinMarketCap
    CACHED = "cached"  # Previously fetched data

class RiskLevel(Enum):
    LOW = "low"      # Far from thresholds, stable
    MEDIUM = "medium"  # Moderate distance to thresholds
    HIGH = "high"    # Near thresholds, needs frequent updates

@dataclass
class AssetSchedule:
    symbol: str
    last_paid_fetch: float
    last_onchain_fetch: float
    risk_level: RiskLevel
    volatility_score: float
    threshold_proximity: float  # 0.0 = far, 1.0 = at threshold
    next_paid_allowed: float
    consecutive_cached_uses: int

class MarketDataScheduler:
    def __init__(self, cost_manager):
        """Initialize scheduler with cost optimization manager"""
        self.cost_manager = cost_manager
        self.asset_schedules: Dict[str, AssetSchedule] = {}
        
        # Base intervals for different risk levels (seconds)
        self.intervals = {
            RiskLevel.LOW: {
                "onchain": 300,      # 5 minutes for low-risk on-chain
                "paid_api": 1800,    # 30 minutes for low-risk paid
            },
            RiskLevel.MEDIUM: {
                "onchain": 120,      # 2 minutes for medium-risk on-chain
                "paid_api": 600,     # 10 minutes for medium-risk paid
            },
            RiskLevel.HIGH: {
                "onchain": 30,       # 30 seconds for high-risk on-chain
                "paid_api": 300,     # 5 minutes for high-risk paid
            }
        }
        
        # Risk thresholds
        self.proximity_thresholds = {
            "high": 0.05,     # Within 5% of trigger threshold
            "medium": 0.15,   # Within 15% of trigger threshold
            "low": 1.0        # Everything else
        }
        
        logger.info("✅ MarketDataScheduler initialized with hybrid architecture")
    
    def initialize_asset(self, symbol: str, current_price: float = 0.0):
        """Initialize scheduling for a new asset"""
        if symbol not in self.asset_schedules:
            self.asset_schedules[symbol] = AssetSchedule(
                symbol=symbol,
                last_paid_fetch=0.0,
                last_onchain_fetch=0.0,
                risk_level=RiskLevel.MEDIUM,
                volatility_score=0.5,
                threshold_proximity=0.0,
                next_paid_allowed=time.time(),
                consecutive_cached_uses=0
            )
            logger.info(f"📊 Initialized scheduler for {symbol}")
    
    def update_risk_assessment(self, symbol: str, 
                             current_price: float,
                             threshold_value: float,
                             volatility: Optional[float] = None):
        """Update risk level based on current market conditions"""
        if symbol not in self.asset_schedules:
            self.initialize_asset(symbol, current_price)
        
        schedule = self.asset_schedules[symbol]
        
        # Calculate threshold proximity
        if threshold_value > 0:
            proximity = abs(current_price - threshold_value) / threshold_value
            schedule.threshold_proximity = min(1.0, proximity)
        
        # Update volatility score if provided
        if volatility is not None:
            schedule.volatility_score = min(1.0, max(0.0, volatility))
        
        # Determine risk level
        if schedule.threshold_proximity <= self.proximity_thresholds["high"]:
            schedule.risk_level = RiskLevel.HIGH
        elif schedule.threshold_proximity <= self.proximity_thresholds["medium"]:
            schedule.risk_level = RiskLevel.MEDIUM
        else:
            schedule.risk_level = RiskLevel.LOW
        
        logger.debug(f"📊 {symbol} risk: {schedule.risk_level.value}, proximity: {schedule.threshold_proximity:.3f}")
    
    def should_fetch_data(self, symbol: str, source: DataSource) -> Tuple[bool, str]:
        """Determine if we should fetch new data for an asset"""
        if symbol not in self.asset_schedules:
            self.initialize_asset(symbol)
        
        schedule = self.asset_schedules[symbol]
        current_time = time.time()
        
        if source == DataSource.ONCHAIN:
            # On-chain data is cheap, check interval based on risk
            interval = self.intervals[schedule.risk_level]["onchain"]
            elapsed = current_time - schedule.last_onchain_fetch
            
            should_fetch = elapsed >= interval
            reason = f"onchain interval {interval}s {'met' if should_fetch else 'not met'} (elapsed: {elapsed:.0f}s)"
            
            return should_fetch, reason
        
        elif source == DataSource.PAID_API:
            # Paid API requires budget checking
            budget_check = self.cost_manager.can_make_api_call('coinapi')
            
            if not budget_check['allowed']:
                return False, f"budget exceeded: {budget_check['hourly_usage']}/{budget_check['hourly_limit']}"
            
            # Check if enough time has passed based on risk level
            interval = self.intervals[schedule.risk_level]["paid_api"]
            elapsed = current_time - schedule.last_paid_fetch
            
            # Allow override for high-risk situations
            if schedule.risk_level == RiskLevel.HIGH and elapsed >= 60:  # Minimum 1 minute for high risk
                should_fetch = True
                reason = "high risk override"
            else:
                should_fetch = elapsed >= interval
                reason = f"paid interval {interval}s {'met' if should_fetch else 'not met'} (elapsed: {elapsed:.0f}s)"
            
            return should_fetch, reason
        
        else:  # CACHED
            # Use cached data if we can't fetch fresh data
            return True, "using cached data"
    
    def record_fetch(self, symbol: str, source: DataSource, success: bool = True):
        """Record that data was fetched for an asset"""
        if symbol not in self.asset_schedules:
            self.initialize_asset(symbol)
        
        schedule = self.asset_schedules[symbol]
        current_time = time.time()
        
        if source == DataSource.ONCHAIN and success:
            schedule.last_onchain_fetch = current_time
            schedule.consecutive_cached_uses = 0  # Reset cache counter
            logger.debug(f"📊 Recorded on-chain fetch for {symbol}")
        
        elif source == DataSource.PAID_API and success:
            schedule.last_paid_fetch = current_time
            schedule.consecutive_cached_uses = 0  # Reset cache counter
            # Record with cost manager
            self.cost_manager.record_api_call('coinapi', success=True)
            logger.debug(f"💰 Recorded paid API fetch for {symbol}")
        
        elif source == DataSource.CACHED:
            schedule.consecutive_cached_uses += 1
            logger.debug(f"📋 Using cached data for {symbol} (#{schedule.consecutive_cached_uses})")
    
    def get_recommended_source(self, symbol: str) -> DataSource:
        """Get the recommended data source for an asset"""
        if symbol not in self.asset_schedules:
            self.initialize_asset(symbol)
        
        schedule = self.asset_schedules[symbol]
        
        # Check if we should use paid API
        should_paid, paid_reason = self.should_fetch_data(symbol, DataSource.PAID_API)
        if should_paid:
            return DataSource.PAID_API
        
        # Check if we should use on-chain
        should_onchain, onchain_reason = self.should_fetch_data(symbol, DataSource.ONCHAIN)
        if should_onchain:
            return DataSource.ONCHAIN
        
        # Fall back to cached data
        # But warn if we've been using cache too long
        if schedule.consecutive_cached_uses > 10:
            logger.warning(f"⚠️ {symbol} using cached data for {schedule.consecutive_cached_uses} cycles")
        
        return DataSource.CACHED
    
    def get_batch_fetch_symbols(self) -> List[str]:
        """Get list of symbols that should be fetched in a batch API call"""
        batch_symbols = []
        
        for symbol, schedule in self.asset_schedules.items():
            should_fetch, _ = self.should_fetch_data(symbol, DataSource.PAID_API)
            if should_fetch:
                batch_symbols.append(symbol)
        
        return batch_symbols
    
    def get_schedule_summary(self) -> Dict:
        """Get summary of current scheduling status"""
        summary = {
            "total_assets": len(self.asset_schedules),
            "by_risk": {"low": 0, "medium": 0, "high": 0},
            "data_freshness": {},
            "budget_status": self.cost_manager.get_usage_summary()
        }
        
        current_time = time.time()
        
        for symbol, schedule in self.asset_schedules.items():
            # Count by risk level
            summary["by_risk"][schedule.risk_level.value] += 1
            
            # Calculate data freshness
            paid_age = current_time - schedule.last_paid_fetch
            onchain_age = current_time - schedule.last_onchain_fetch
            
            summary["data_freshness"][symbol] = {
                "risk_level": schedule.risk_level.value,
                "paid_data_age_seconds": paid_age,
                "onchain_data_age_seconds": onchain_age,
                "consecutive_cached_uses": schedule.consecutive_cached_uses,
                "threshold_proximity": schedule.threshold_proximity
            }
        
        return summary
    
    def force_refresh_high_risk(self) -> List[str]:
        """Force refresh for all high-risk assets (emergency use)"""
        high_risk_symbols = []
        
        for symbol, schedule in self.asset_schedules.items():
            if schedule.risk_level == RiskLevel.HIGH:
                # Reset last fetch times to force refresh
                schedule.last_paid_fetch = 0.0
                schedule.last_onchain_fetch = 0.0
                high_risk_symbols.append(symbol)
        
        if high_risk_symbols:
            logger.warning(f"🚨 Force refresh triggered for high-risk assets: {high_risk_symbols}")
        
        return high_risk_symbols
    
    def optimize_for_budget_remaining(self, hours_remaining: int):
        """Adjust scheduling based on remaining daily budget"""
        budget_summary = self.cost_manager.get_usage_summary()
        remaining_credits = budget_summary['daily_limit'] - budget_summary['daily_usage']
        
        if remaining_credits <= 0:
            logger.warning("⚠️ Daily budget exhausted - switching to on-chain only mode")
            return
        
        credits_per_hour = remaining_credits / max(1, hours_remaining)
        
        # Adjust intervals if budget is tight
        if credits_per_hour < 10:  # Conservative mode
            logger.info(f"💰 Budget conservation mode: {credits_per_hour:.1f} credits/hour remaining")
            for symbol in self.asset_schedules:
                schedule = self.asset_schedules[symbol]
                # Increase paid API intervals by 50%
                if schedule.risk_level != RiskLevel.HIGH:
                    schedule.next_paid_allowed = time.time() + 900  # 15 minute delay