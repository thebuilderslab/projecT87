
#!/usr/bin/env python3
"""
Live Data Monitor - Real-time monitoring of blockchain data fetching
Tracks success rates, performance, and identifies issues
"""

import time
import requests
import json
from datetime import datetime
import threading

class LiveDataMonitor:
    def __init__(self):
        self.monitoring_active = False
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0,
            'rpc_failures': 0,
            'aave_failures': 0,
            'price_failures': 0,
            'last_success': None,
            'last_failure': None
        }
        
    def start_monitoring(self, dashboard_url="http://localhost:5000"):
        """Start real-time monitoring of the dashboard"""
        self.monitoring_active = True
        self.dashboard_url = dashboard_url
        
        print("🔍 Starting Live Data Monitor...")
        print(f"📊 Monitoring dashboard at: {dashboard_url}")
        print("=" * 60)
        
        monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()
        
        return monitor_thread
        
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                start_time = time.time()
                
                # Test wallet status endpoint
                response = requests.get(f"{self.dashboard_url}/api/wallet-status", timeout=10)
                response_time = time.time() - start_time
                
                self.stats['total_requests'] += 1
                
                if response.status_code == 200:
                    data = response.json()
                    self._analyze_response(data, response_time)
                    self.stats['successful_requests'] += 1
                    self.stats['last_success'] = datetime.now().isoformat()
                else:
                    self.stats['failed_requests'] += 1
                    self.stats['last_failure'] = datetime.now().isoformat()
                    print(f"❌ HTTP Error: {response.status_code}")
                    
            except Exception as e:
                self.stats['failed_requests'] += 1
                self.stats['last_failure'] = datetime.now().isoformat()
                print(f"❌ Monitor Error: {e}")
                
            # Update average response time
            if self.stats['successful_requests'] > 0:
                success_rate = (self.stats['successful_requests'] / self.stats['total_requests']) * 100
                print(f"📊 Success Rate: {success_rate:.1f}% | Avg Response: {self.stats['avg_response_time']:.2f}s")
                
            time.sleep(15)  # Monitor every 15 seconds
            
    def _analyze_response(self, data, response_time):
        """Analyze dashboard response for issues"""
        
        # Update response time
        total_time = self.stats['avg_response_time'] * (self.stats['successful_requests'] - 1)
        self.stats['avg_response_time'] = (total_time + response_time) / self.stats['successful_requests']
        
        # Check data quality
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if data.get('success'):
            enhanced_manager = data.get('enhanced_contract_manager', {})
            
            # Check RPC status
            if enhanced_manager.get('rpc_endpoint'):
                print(f"✅ {timestamp} | RPC: {enhanced_manager['rpc_endpoint'][:30]}... | Response: {response_time:.2f}s")
            else:
                self.stats['rpc_failures'] += 1
                print(f"❌ {timestamp} | RPC: FAILED")
                
            # Check Aave data
            aave_data = data.get('aave_positions', {})
            if aave_data.get('data_source') == 'live_aave_contract_enhanced':
                health_factor = aave_data.get('health_factor', 0)
                print(f"🏦 {timestamp} | Aave: LIVE | Health: {health_factor:.2f}")
            else:
                self.stats['aave_failures'] += 1
                print(f"⚠️ {timestamp} | Aave: {aave_data.get('data_source', 'UNKNOWN')}")
                
            # Check prices
            prices = data.get('prices', {})
            if prices.get('ETH', 0) > 0:
                eth_price = prices['ETH']
                print(f"💰 {timestamp} | Prices: LIVE | ETH: ${eth_price:.2f}")
            else:
                self.stats['price_failures'] += 1
                print(f"❌ {timestamp} | Prices: FAILED")
                
            # Portfolio summary
            portfolio_usd = data.get('total_portfolio_usd', 0)
            print(f"📊 {timestamp} | Portfolio: ${portfolio_usd:.2f}")
            
        else:
            print(f"❌ {timestamp} | Dashboard Error: {data.get('error', 'Unknown')}")
            
        print("-" * 60)
        
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_active = False
        print("⏹️ Live Data Monitor stopped")
        
    def get_report(self):
        """Generate monitoring report"""
        if self.stats['total_requests'] == 0:
            return "No monitoring data available"
            
        success_rate = (self.stats['successful_requests'] / self.stats['total_requests']) * 100
        failure_rate = (self.stats['failed_requests'] / self.stats['total_requests']) * 100
        
        report = f"""
🔍 LIVE DATA MONITORING REPORT
{'=' * 50}
Total Requests: {self.stats['total_requests']}
Successful: {self.stats['successful_requests']} ({success_rate:.1f}%)
Failed: {self.stats['failed_requests']} ({failure_rate:.1f}%)
Avg Response Time: {self.stats['avg_response_time']:.2f}s

📊 COMPONENT FAILURES:
RPC Failures: {self.stats['rpc_failures']}
Aave Failures: {self.stats['aave_failures']}
Price Failures: {self.stats['price_failures']}

⏰ TIMESTAMPS:
Last Success: {self.stats['last_success'] or 'None'}
Last Failure: {self.stats['last_failure'] or 'None'}
"""
        return report

if __name__ == "__main__":
    monitor = LiveDataMonitor()
    
    try:
        print("🚀 Starting Live Data Monitor...")
        print("Press Ctrl+C to stop monitoring")
        
        monitor_thread = monitor.start_monitoring()
        
        # Keep main thread alive
        while True:
            time.sleep(60)
            print("\n" + monitor.get_report())
            
    except KeyboardInterrupt:
        monitor.stop_monitoring()
        print("\n📋 Final Report:")
        print(monitor.get_report())
