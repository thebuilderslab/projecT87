
#!/usr/bin/env python3
"""
RPC Health Monitor - Continuous monitoring and automatic failover
"""

import time
import threading
from collections import defaultdict
from datetime import datetime, timedelta
from web3 import Web3
from enhanced_rpc_manager import EnhancedRPCManager

class RPCHealthMonitor:
    def __init__(self, agent_instance):
        self.agent = agent_instance
        self.rpc_manager = EnhancedRPCManager()
        self.health_scores = defaultdict(float)
        self.failure_counts = defaultdict(int)
        self.last_success = defaultdict(lambda: datetime.now())
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Health thresholds
        self.min_health_score = 0.7
        self.max_failures = 3
        self.health_check_interval = 30  # seconds
        
    def start_monitoring(self):
        """Start continuous RPC health monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            print("🔍 RPC Health Monitor started")
    
    def stop_monitoring(self):
        """Stop RPC health monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("🛑 RPC Health Monitor stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                self._check_current_rpc_health()
                self._evaluate_rpc_performance()
                time.sleep(self.health_check_interval)
            except Exception as e:
                print(f"⚠️ Health monitor error: {e}")
                time.sleep(5)
    
    def _check_current_rpc_health(self):
        """Check health of current RPC endpoint"""
        if not hasattr(self.agent, 'w3') or not self.agent.w3:
            return
        
        try:
            start_time = time.time()
            
            # Quick health checks
            block_number = self.agent.w3.eth.block_number
            gas_price = self.agent.w3.eth.gas_price
            
            response_time = time.time() - start_time
            
            # Calculate health score
            health_score = self._calculate_health_score(response_time, True)
            self.health_scores[self.agent.rpc_url] = health_score
            self.last_success[self.agent.rpc_url] = datetime.now()
            self.failure_counts[self.agent.rpc_url] = 0
            
            print(f"✅ RPC Health Check: {health_score:.2f} ({response_time:.2f}s)")
            
        except Exception as e:
            self._handle_rpc_failure(str(e))
    
    def _calculate_health_score(self, response_time, success):
        """Calculate health score based on performance metrics"""
        if not success:
            return 0.0
        
        # Base score
        score = 1.0
        
        # Penalize slow responses
        if response_time > 5:
            score *= 0.5
        elif response_time > 2:
            score *= 0.8
        elif response_time > 1:
            score *= 0.9
        
        return max(0.0, min(1.0, score))
    
    def _handle_rpc_failure(self, error_msg):
        """Handle RPC failure and trigger failover if needed"""
        current_rpc = self.agent.rpc_url
        self.failure_counts[current_rpc] += 1
        self.health_scores[current_rpc] *= 0.5  # Reduce health score
        
        print(f"❌ RPC Failure #{self.failure_counts[current_rpc]}: {error_msg}")
        
        if (self.failure_counts[current_rpc] >= self.max_failures or 
            self.health_scores[current_rpc] < self.min_health_score):
            print(f"🔄 Triggering RPC failover due to poor health")
            self._trigger_failover()
    
    def _trigger_failover(self):
        """Trigger immediate RPC failover"""
        print("🚨 Initiating emergency RPC failover...")
        
        # Try to switch to backup RPC
        if hasattr(self.agent, 'switch_to_fallback_rpc'):
            success = self.agent.switch_to_fallback_rpc()
            if success:
                print(f"✅ Successfully failed over to: {self.agent.rpc_url}")
                # Reset failure count for new RPC
                self.failure_counts[self.agent.rpc_url] = 0
                return True
        
        # If agent doesn't have failover, try manual switch
        if self.rpc_manager.find_working_rpc():
            try:
                self.agent.w3 = self.rpc_manager.w3
                self.agent.rpc_url = self.rpc_manager.working_rpc
                print(f"✅ Manual failover successful: {self.agent.rpc_url}")
                return True
            except Exception as e:
                print(f"❌ Manual failover failed: {e}")
        
        print("❌ All RPC failover attempts failed")
        return False
    
    def _evaluate_rpc_performance(self):
        """Evaluate overall RPC performance and suggest optimizations"""
        if not self.health_scores:
            return
        
        avg_health = sum(self.health_scores.values()) / len(self.health_scores)
        total_failures = sum(self.failure_counts.values())
        
        if avg_health < 0.5:
            print(f"⚠️ Poor RPC performance detected (avg health: {avg_health:.2f})")
        
        if total_failures > 10:
            print(f"⚠️ High failure count detected ({total_failures} total failures)")
    
    def get_health_report(self):
        """Get comprehensive health report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'current_rpc': getattr(self.agent, 'rpc_url', 'Unknown'),
            'health_scores': dict(self.health_scores),
            'failure_counts': dict(self.failure_counts),
            'average_health': sum(self.health_scores.values()) / len(self.health_scores) if self.health_scores else 0,
            'total_failures': sum(self.failure_counts.values()),
            'monitoring_active': self.monitoring_active
        }
        return report
