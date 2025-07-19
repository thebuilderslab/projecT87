
#!/usr/bin/env python3
"""
Optimized Autonomous Sequence Manager
Handles efficient execution of autonomous DeFi operations with enhanced error recovery
"""

import time
import json
from datetime import datetime
from config_constants import MIN_ETH_FOR_OPERATIONS

class OptimizedSequenceManager:
    def __init__(self, agent):
        self.agent = agent
        self.sequence_history = []
        self.last_execution_time = 0
        self.min_execution_interval = 300  # 5 minutes between executions
        
    def can_execute_sequence(self):
        """Check if we can execute a new sequence"""
        time_since_last = time.time() - self.last_execution_time
        
        if time_since_last < self.min_execution_interval:
            remaining = self.min_execution_interval - time_since_last
            print(f"⏰ Sequence cooldown: {remaining:.0f}s remaining")
            return False
            
        return True
    
    def execute_optimized_sequence(self, collateral_growth):
        """Execute optimized autonomous sequence with smart error recovery"""
        if not self.can_execute_sequence():
            return 0.5  # Moderate score for waiting
            
        print(f"🚀 OPTIMIZED SEQUENCE STARTING")
        print(f"💡 Growth detected: ${collateral_growth:.2f}")
        
        sequence_id = f"seq_{int(time.time())}"
        sequence_log = {
            'sequence_id': sequence_id,
            'start_time': time.time(),
            'collateral_growth': collateral_growth,
            'steps': [],
            'success': False,
            'performance_score': 0.0
        }
        
        try:
            # Step 1: Validate conditions
            validation_result = self._validate_execution_conditions()
            sequence_log['steps'].append({
                'step': 'validation',
                'success': validation_result['success'],
                'details': validation_result
            })
            
            if not validation_result['success']:
                print(f"❌ Validation failed: {validation_result.get('reason', 'Unknown')}")
                sequence_log['performance_score'] = 0.1
                return 0.1
            
            # Step 2: Calculate optimal borrow amount
            optimal_borrow = self._calculate_optimal_borrow(collateral_growth, validation_result)
            sequence_log['steps'].append({
                'step': 'borrow_calculation',
                'success': True,
                'amount': optimal_borrow
            })
            
            # Step 3: Execute borrow with enhanced error handling
            borrow_result = self._execute_smart_borrow(optimal_borrow)
            sequence_log['steps'].append({
                'step': 'borrow_execution',
                'success': borrow_result['success'],
                'details': borrow_result
            })
            
            if borrow_result['success']:
                # Update execution tracking
                self.last_execution_time = time.time()
                
                # Update baseline after successful operation
                self.agent.update_baseline_after_success()
                
                sequence_log['success'] = True
                sequence_log['performance_score'] = 0.9
                print(f"✅ OPTIMIZED SEQUENCE COMPLETED SUCCESSFULLY")
                return 0.9
            else:
                sequence_log['performance_score'] = 0.3
                print(f"❌ Sequence failed at borrow step")
                return 0.3
                
        except Exception as e:
            sequence_log['error'] = str(e)
            sequence_log['performance_score'] = 0.1
            print(f"❌ Sequence execution error: {e}")
            return 0.1
            
        finally:
            # Log sequence for analysis
            sequence_log['end_time'] = time.time()
            sequence_log['duration'] = sequence_log['end_time'] - sequence_log['start_time']
            self.sequence_history.append(sequence_log)
            self._save_sequence_log(sequence_log)
    
    def _validate_execution_conditions(self):
        """Validate all conditions before execution"""
        try:
            # Check health factor
            if hasattr(self.agent, 'health_monitor') and self.agent.health_monitor:
                health_data = self.agent.health_monitor.get_current_health_factor()
                if health_data and health_data.get('health_factor', 0) < 2.0:
                    return {
                        'success': False,
                        'reason': f"Health factor too low: {health_data.get('health_factor', 0):.2f}"
                    }
            
            # Check available borrows
            dashboard_data = self.agent.get_enhanced_dashboard_data()
            if not dashboard_data or dashboard_data.get('available_borrows_usdc', 0) < 5.0:
                return {
                    'success': False,
                    'reason': f"Insufficient borrowing capacity: ${dashboard_data.get('available_borrows_usdc', 0):.2f}"
                }
            
            # Check ETH balance for gas
            eth_balance = self.agent.get_eth_balance()
            if eth_balance < MIN_ETH_FOR_OPERATIONS:
                return {
                    'success': False,
                    'reason': f"Insufficient ETH for gas: {eth_balance:.6f} ETH"
                }
            
            return {
                'success': True,
                'health_factor': health_data.get('health_factor', 0) if health_data else 0,
                'available_borrows': dashboard_data.get('available_borrows_usdc', 0),
                'eth_balance': eth_balance
            }
            
        except Exception as e:
            return {
                'success': False,
                'reason': f"Validation error: {e}"
            }
    
    def _calculate_optimal_borrow(self, growth, validation_data):
        """Calculate optimal borrow amount based on conditions"""
        # Conservative approach: 40% of growth, max $6, min $2
        base_amount = min(6.0, max(2.0, growth * 0.4))
        
        # Adjust based on available capacity
        available = validation_data.get('available_borrows', 0)
        capacity_limit = available * 0.8  # Use only 80% of available
        
        optimal = min(base_amount, capacity_limit)
        
        print(f"💰 Optimal borrow calculation:")
        print(f"   Base amount (40% growth): ${base_amount:.2f}")
        print(f"   Available capacity: ${available:.2f}")
        print(f"   Capacity limit (80%): ${capacity_limit:.2f}")
        print(f"   Final optimal amount: ${optimal:.2f}")
        
        return optimal
    
    def _execute_smart_borrow(self, amount):
        """Execute borrow with smart retry and error handling"""
        try:
            print(f"🏦 Executing smart borrow: ${amount:.2f} USDC")
            
            # Use the agent's enhanced borrow method
            result = self.agent.execute_enhanced_borrow_with_retry(amount)
            
            return {
                'success': result,
                'amount': amount,
                'method': 'enhanced_retry'
            }
            
        except Exception as e:
            print(f"❌ Smart borrow failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'amount': amount
            }
    
    def _save_sequence_log(self, sequence_log):
        """Save sequence log for analysis"""
        try:
            log_file = 'sequence_execution_log.json'
            
            # Append to log file
            with open(log_file, 'a') as f:
                f.write(json.dumps(sequence_log) + '\n')
                
        except Exception as e:
            print(f"⚠️ Failed to save sequence log: {e}")
    
    def get_performance_stats(self):
        """Get performance statistics for the sequence manager"""
        if not self.sequence_history:
            return {'total_sequences': 0, 'success_rate': 0.0}
        
        total = len(self.sequence_history)
        successful = sum(1 for seq in self.sequence_history if seq.get('success', False))
        success_rate = successful / total if total > 0 else 0.0
        
        avg_performance = sum(seq.get('performance_score', 0) for seq in self.sequence_history) / total
        
        return {
            'total_sequences': total,
            'successful_sequences': successful,
            'success_rate': success_rate,
            'average_performance': avg_performance,
            'last_execution': self.last_execution_time
        }
