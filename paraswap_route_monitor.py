#!/usr/bin/env python3
"""
ParaSwap Route Monitoring & Analytics
Tracks routing success rates, method selectors, and performance metrics over time.

Features:
- Real-time route logging
- Success rate tracking by method selector
- Gas usage analytics
- Automated alerting on reliability drops
- Historical trend analysis

See PARASWAP_ROUTING_AUDIT.md for comprehensive routing analysis.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from decimal import Decimal

@dataclass
class RouteAttempt:
    """Record of a single ParaSwap routing attempt"""
    timestamp: str
    selector: str
    method_name: str
    calldata_size: int
    gas_used: Optional[int]
    success: bool
    tx_hash: Optional[str]
    from_token: str
    to_token: str
    amount: str

class ParaSwapRouteMonitor:
    """Track and analyze ParaSwap routing statistics over time"""
    
    # Known route selectors and their characteristics
    KNOWN_ROUTES = {
        '0xa76f4eb6': {
            'name': 'swapExactAmountOutOnUniswapV2',
            'adapter': 'UniswapV2Adapter (direct)',
            'expected_calldata': 484,
            'expected_gas': 729_485,
            'reliability': 'HIGH',
            'notes': '100% success rate - preferred route'
        },
        '0x7f457675': {
            'name': 'swapExactAmountOut',
            'adapter': 'GenericAdapter (missing wrapper)',
            'expected_calldata': 836,
            'expected_gas': 765_583,
            'reliability': 'FAILED',
            'notes': 'Missing GenericAdapter wrapper - always fails'
        },
        '0xd6ed22e6': {
            'name': 'swapExactAmountOutOnBalancerV2',
            'adapter': 'BalancerV2Adapter',
            'expected_calldata': 804,
            'expected_gas': None,  # Unknown
            'reliability': 'UNKNOWN',
            'notes': 'Newly discovered route - untested'
        }
    }
    
    def __init__(self, stats_file: str = 'paraswap_route_stats.json'):
        """Initialize monitor with persistent storage"""
        self.stats_file = Path(stats_file)
        self.stats = self._load_stats()
        self.alert_threshold = 0.75  # Alert if success rate drops below 75%
    
    def _load_stats(self) -> Dict:
        """Load statistics from persistent storage"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Error loading stats: {e}")
                return self._init_stats()
        else:
            return self._init_stats()
    
    def _init_stats(self) -> Dict:
        """Initialize empty statistics structure"""
        return {
            'routes': {},  # Statistics by selector
            'attempts': [],  # All attempts (limited to last 1000)
            'alerts': [],  # Alert history
            'metadata': {
                'created': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'version': '1.0'
            }
        }
    
    def _save_stats(self):
        """Save statistics to persistent storage"""
        self.stats['metadata']['last_updated'] = datetime.now().isoformat()
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            print(f"⚠️  Error saving stats: {e}")
    
    def log_attempt(
        self,
        selector: str,
        calldata_size: int,
        success: bool,
        from_token: str,
        to_token: str,
        amount: str,
        gas_used: Optional[int] = None,
        tx_hash: Optional[str] = None
    ):
        """Log a routing attempt"""
        # Get method name from known routes
        route_info = self.KNOWN_ROUTES.get(selector, {})
        method_name = route_info.get('name', 'Unknown')
        
        # Create attempt record
        attempt = RouteAttempt(
            timestamp=datetime.now().isoformat(),
            selector=selector,
            method_name=method_name,
            calldata_size=calldata_size,
            gas_used=gas_used,
            success=success,
            tx_hash=tx_hash,
            from_token=from_token,
            to_token=to_token,
            amount=amount
        )
        
        # Add to attempts history (keep last 1000)
        self.stats['attempts'].append(asdict(attempt))
        if len(self.stats['attempts']) > 1000:
            self.stats['attempts'] = self.stats['attempts'][-1000:]
        
        # Update route-specific statistics
        if selector not in self.stats['routes']:
            self.stats['routes'][selector] = {
                'method_name': method_name,
                'total_attempts': 0,
                'successes': 0,
                'failures': 0,
                'gas_total': 0,
                'gas_count': 0,
                'calldata_sizes': [],
                'first_seen': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat()
            }
        
        route = self.stats['routes'][selector]
        route['total_attempts'] += 1
        route['last_seen'] = datetime.now().isoformat()
        
        if success:
            route['successes'] += 1
        else:
            route['failures'] += 1
        
        if gas_used:
            route['gas_total'] += gas_used
            route['gas_count'] += 1
        
        # Track calldata size variance
        if calldata_size not in route['calldata_sizes']:
            route['calldata_sizes'].append(calldata_size)
        
        # Save updated stats
        self._save_stats()
        
        # Check if alert needed
        self._check_alert(selector)
    
    def get_success_rate(self, selector: str) -> float:
        """Get success rate for a specific route"""
        if selector not in self.stats['routes']:
            return 0.0
        
        route = self.stats['routes'][selector]
        if route['total_attempts'] == 0:
            return 0.0
        
        return route['successes'] / route['total_attempts']
    
    def get_overall_success_rate(self) -> float:
        """Get overall success rate across all routes"""
        total_attempts = sum(r['total_attempts'] for r in self.stats['routes'].values())
        total_successes = sum(r['successes'] for r in self.stats['routes'].values())
        
        if total_attempts == 0:
            return 0.0
        
        return total_successes / total_attempts
    
    def _check_alert(self, selector: str):
        """Check if success rate dropped below threshold"""
        success_rate = self.get_success_rate(selector)
        route = self.stats['routes'][selector]
        
        # Only alert if we have enough data (>5 attempts)
        if route['total_attempts'] < 5:
            return
        
        if success_rate < self.alert_threshold:
            alert = {
                'timestamp': datetime.now().isoformat(),
                'selector': selector,
                'method': route['method_name'],
                'success_rate': success_rate,
                'attempts': route['total_attempts'],
                'threshold': self.alert_threshold
            }
            
            self.stats['alerts'].append(alert)
            
            print(f"\n" + "⚠️ " * 40)
            print(f"ALERT: Success rate dropped below {self.alert_threshold * 100}%!")
            print(f"  Selector: {selector}")
            print(f"  Method: {route['method_name']}")
            print(f"  Success Rate: {success_rate * 100:.1f}%")
            print(f"  Attempts: {route['total_attempts']}")
            print("⚠️ " * 40 + "\n")
    
    def print_summary(self):
        """Print comprehensive routing statistics"""
        print("\n" + "=" * 80)
        print("PARASWAP ROUTING STATISTICS SUMMARY")
        print("=" * 80)
        
        overall_rate = self.get_overall_success_rate()
        total_attempts = sum(r['total_attempts'] for r in self.stats['routes'].values())
        
        print(f"\n📊 Overall Statistics:")
        print(f"   Total Attempts: {total_attempts}")
        print(f"   Overall Success Rate: {overall_rate * 100:.1f}%")
        print(f"   Unique Routes Discovered: {len(self.stats['routes'])}")
        print(f"   Alert Threshold: {self.alert_threshold * 100}%")
        
        print(f"\n📈 Route-by-Route Breakdown:")
        print("-" * 80)
        
        for selector, route in sorted(self.stats['routes'].items(), 
                                      key=lambda x: x[1]['total_attempts'], 
                                      reverse=True):
            success_rate = self.get_success_rate(selector)
            avg_gas = route['gas_total'] / route['gas_count'] if route['gas_count'] > 0 else 0
            
            # Get known route info
            known = self.KNOWN_ROUTES.get(selector, {})
            reliability = known.get('reliability', 'UNKNOWN')
            
            # Status indicator
            if reliability == 'HIGH':
                status = '🟢'
            elif reliability == 'FAILED':
                status = '🔴'
            else:
                status = '🟡'
            
            print(f"\n{status} Selector: {selector}")
            print(f"   Method: {route['method_name']}")
            print(f"   Attempts: {route['total_attempts']}")
            print(f"   Successes: {route['successes']}")
            print(f"   Failures: {route['failures']}")
            print(f"   Success Rate: {success_rate * 100:.1f}%")
            
            if avg_gas > 0:
                print(f"   Avg Gas: {avg_gas:,.0f}")
            else:
                print(f"   Avg Gas: N/A")
            
            print(f"   Calldata Sizes: {route['calldata_sizes']} bytes")
            print(f"   First Seen: {route['first_seen']}")
            print(f"   Last Seen: {route['last_seen']}")
            
            if selector in self.KNOWN_ROUTES:
                print(f"   Notes: {self.KNOWN_ROUTES[selector]['notes']}")
        
        if self.stats['alerts']:
            print(f"\n⚠️  Recent Alerts ({len(self.stats['alerts'])}):")
            print("-" * 80)
            for alert in self.stats['alerts'][-5:]:  # Show last 5
                print(f"   {alert['timestamp']}: {alert['method']} success rate dropped to {alert['success_rate'] * 100:.1f}%")
        
        print("\n" + "=" * 80)
    
    def get_route_recommendation(self, from_token: str, to_token: str) -> Dict:
        """Get routing recommendation based on historical data"""
        # Find best performing route for this pair
        pair_attempts = [
            a for a in self.stats['attempts']
            if a['from_token'] == from_token and a['to_token'] == to_token
        ]
        
        if not pair_attempts:
            return {
                'recommendation': 'Use default settings',
                'confidence': 'LOW',
                'reason': 'No historical data for this pair'
            }
        
        # Count success by selector
        selector_performance = {}
        for attempt in pair_attempts:
            selector = attempt['selector']
            if selector not in selector_performance:
                selector_performance[selector] = {'successes': 0, 'total': 0}
            
            selector_performance[selector]['total'] += 1
            if attempt['success']:
                selector_performance[selector]['successes'] += 1
        
        # Find best selector
        best_selector = None
        best_rate = 0
        for selector, perf in selector_performance.items():
            rate = perf['successes'] / perf['total']
            if rate > best_rate:
                best_rate = rate
                best_selector = selector
        
        if best_selector and best_rate > 0.8:
            route_name = self.stats['routes'][best_selector]['method_name']
            return {
                'recommendation': f'Prefer {route_name} ({best_selector})',
                'confidence': 'HIGH' if best_rate > 0.9 else 'MEDIUM',
                'success_rate': best_rate,
                'sample_size': selector_performance[best_selector]['total']
            }
        
        return {
            'recommendation': 'Use retry logic (no clear winner)',
            'confidence': 'MEDIUM',
            'reason': 'Multiple routes with similar performance'
        }

# Singleton instance
_monitor_instance = None

def get_monitor() -> ParaSwapRouteMonitor:
    """Get or create singleton monitor instance"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = ParaSwapRouteMonitor()
    return _monitor_instance

if __name__ == '__main__':
    # CLI for viewing statistics
    import sys
    
    monitor = get_monitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--summary':
        monitor.print_summary()
    else:
        print("ParaSwap Route Monitor")
        print("\nUsage:")
        print("  python paraswap_route_monitor.py --summary   Show routing statistics")
        print("\nOr import and use programmatically:")
        print("  from paraswap_route_monitor import get_monitor")
        print("  monitor = get_monitor()")
        print("  monitor.log_attempt(...)")
