
#!/usr/bin/env python3
"""
Network Quality Detector - Analyzes connection quality and optimizes settings
"""

import time
import statistics
import threading
from datetime import datetime

class NetworkQualityDetector:
    def __init__(self, agent_instance):
        self.agent = agent_instance
        self.latency_samples = []
        self.throughput_samples = []
        self.quality_score = 1.0
        
        # Quality thresholds
        self.excellent_latency = 0.5  # seconds
        self.good_latency = 1.0
        self.poor_latency = 3.0
        
    def measure_network_quality(self, num_tests=5):
        """Perform comprehensive network quality measurement"""
        print("🔍 Measuring network quality...")
        
        latencies = []
        throughputs = []
        
        for i in range(num_tests):
            try:
                # Measure latency
                start_time = time.time()
                block_num = self.agent.w3.eth.block_number
                latency = time.time() - start_time
                latencies.append(latency)
                
                # Measure throughput (approximate)
                start_time = time.time()
                for _ in range(3):
                    self.agent.w3.eth.gas_price
                throughput_time = time.time() - start_time
                throughputs.append(3 / throughput_time)  # requests per second
                
                time.sleep(0.5)  # Brief pause between tests
                
            except Exception as e:
                print(f"⚠️ Network test {i+1} failed: {e}")
                latencies.append(10.0)  # High penalty for failure
                throughputs.append(0.1)  # Low throughput for failure
        
        # Calculate statistics
        avg_latency = statistics.mean(latencies) if latencies else 10.0
        avg_throughput = statistics.mean(throughputs) if throughputs else 0.1
        
        # Update samples
        self.latency_samples.extend(latencies)
        self.throughput_samples.extend(throughputs)
        
        # Keep only recent samples
        if len(self.latency_samples) > 50:
            self.latency_samples = self.latency_samples[-50:]
        if len(self.throughput_samples) > 50:
            self.throughput_samples = self.throughput_samples[-50:]
        
        # Calculate quality score
        self.quality_score = self._calculate_quality_score(avg_latency, avg_throughput)
        
        print(f"📊 Network Quality Results:")
        print(f"   Average Latency: {avg_latency:.2f}s")
        print(f"   Average Throughput: {avg_throughput:.1f} req/s")
        print(f"   Quality Score: {self.quality_score:.2f}/1.0")
        
        return {
            'latency': avg_latency,
            'throughput': avg_throughput,
            'quality_score': self.quality_score,
            'recommendation': self._get_quality_recommendation()
        }
    
    def _calculate_quality_score(self, latency, throughput):
        """Calculate overall network quality score"""
        # Latency component (0-1, higher is better)
        if latency <= self.excellent_latency:
            latency_score = 1.0
        elif latency <= self.good_latency:
            latency_score = 0.8
        elif latency <= self.poor_latency:
            latency_score = 0.5
        else:
            latency_score = 0.2
        
        # Throughput component (0-1, higher is better)
        throughput_score = min(1.0, throughput / 5.0)  # Scale to max 5 req/s
        
        # Combined score (weighted average)
        return (latency_score * 0.7) + (throughput_score * 0.3)
    
    def _get_quality_recommendation(self):
        """Get recommendation based on network quality"""
        if self.quality_score >= 0.8:
            return "excellent"
        elif self.quality_score >= 0.6:
            return "good"
        elif self.quality_score >= 0.4:
            return "fair"
        else:
            return "poor"
    
    def optimize_connection_settings(self):
        """Optimize connection settings based on network quality"""
        recommendation = self._get_quality_recommendation()
        
        if recommendation == "poor":
            print("🔧 Applying poor network optimizations...")
            return {
                'timeout': 60,
                'retries': 5,
                'backoff_factor': 2.0,
                'pool_connections': 5,
                'max_retries_per_connection': 3
            }
        elif recommendation == "fair":
            print("🔧 Applying fair network optimizations...")
            return {
                'timeout': 45,
                'retries': 3,
                'backoff_factor': 1.5,
                'pool_connections': 10,
                'max_retries_per_connection': 2
            }
        else:
            print("🔧 Applying standard network settings...")
            return {
                'timeout': 30,
                'retries': 2,
                'backoff_factor': 1.0,
                'pool_connections': 15,
                'max_retries_per_connection': 1
            }
    
    def get_quality_report(self):
        """Get comprehensive quality report"""
        if not self.latency_samples:
            return None
        
        return {
            'timestamp': datetime.now().isoformat(),
            'current_quality_score': self.quality_score,
            'recommendation': self._get_quality_recommendation(),
            'statistics': {
                'avg_latency': statistics.mean(self.latency_samples),
                'median_latency': statistics.median(self.latency_samples),
                'max_latency': max(self.latency_samples),
                'min_latency': min(self.latency_samples),
                'avg_throughput': statistics.mean(self.throughput_samples),
                'sample_count': len(self.latency_samples)
            }
        }
