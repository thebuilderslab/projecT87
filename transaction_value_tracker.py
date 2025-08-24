
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

class TransactionValueTracker:
    def __init__(self):
        self.transactions = []
        self.cycles = []
        self.performance_metrics = {
            'total_volume': 0,
            'successful_cycles': 0,
            'failed_cycles': 0,
            'net_profit_loss': 0,
            'avg_cycle_duration': 0,
            'best_performing_cycle': None,
            'worst_performing_cycle': None
        }
    
    def track_borrow_transaction(self, amount_dai: float, health_factor_before: float, 
                               health_factor_after: float, tx_hash: str) -> str:
        """Track initial DAI borrow transaction"""
        tx_id = f"borrow_{int(time.time())}"
        
        transaction = {
            'id': tx_id,
            'type': 'borrow_dai',
            'amount_dai': amount_dai,
            'health_factor_before': health_factor_before,
            'health_factor_after': health_factor_after,
            'tx_hash': tx_hash,
            'timestamp': time.time(),
            'status': 'completed'
        }
        
        self.transactions.append(transaction)
        return tx_id
    
    def track_dai_to_arb_swap(self, amount_dai: float, amount_arb_received: float, 
                             dai_price: float, arb_price: float, tx_hash: str) -> str:
        """Track DAI to ARB swap with value metrics"""
        tx_id = f"dai_arb_{int(time.time())}"
        
        # Calculate swap efficiency
        expected_arb = amount_dai / arb_price
        swap_efficiency = (amount_arb_received / expected_arb) * 100
        
        transaction = {
            'id': tx_id,
            'type': 'dai_to_arb_swap',
            'amount_dai_in': amount_dai,
            'amount_arb_out': amount_arb_received,
            'dai_price_at_swap': dai_price,
            'arb_price_at_swap': arb_price,
            'swap_efficiency_pct': swap_efficiency,
            'value_usd_at_swap': amount_dai,  # DAI is ~$1
            'tx_hash': tx_hash,
            'timestamp': time.time(),
            'status': 'completed'
        }
        
        self.transactions.append(transaction)
        return tx_id
    
    def track_arb_to_dai_swap(self, amount_arb: float, amount_dai_received: float,
                             arb_price: float, dai_price: float, tx_hash: str,
                             cycle_start_tx_id: str) -> Dict:
        """Track ARB to DAI swap and calculate complete cycle metrics"""
        tx_id = f"arb_dai_{int(time.time())}"
        
        # Find the original DAI→ARB swap for this cycle
        original_swap = None
        for tx in reversed(self.transactions):
            if tx['type'] == 'dai_to_arb_swap' and tx['id'] == cycle_start_tx_id:
                original_swap = tx
                break
        
        if not original_swap:
            print(f"⚠️ Could not find original swap for cycle calculation")
            return {}
        
        # Calculate cycle performance
        original_dai_amount = original_swap['amount_dai_in']
        dai_profit_loss = amount_dai_received - original_dai_amount
        profit_loss_pct = (dai_profit_loss / original_dai_amount) * 100
        
        # Calculate ARB price change during hold period
        original_arb_price = original_swap['arb_price_at_swap']
        arb_price_change_pct = ((arb_price - original_arb_price) / original_arb_price) * 100
        
        # Calculate hold duration
        hold_duration_hours = (time.time() - original_swap['timestamp']) / 3600
        
        transaction = {
            'id': tx_id,
            'type': 'arb_to_dai_swap',
            'amount_arb_in': amount_arb,
            'amount_dai_out': amount_dai_received,
            'arb_price_at_swap': arb_price,
            'dai_price_at_swap': dai_price,
            'value_usd_at_swap': amount_arb * arb_price,
            'tx_hash': tx_hash,
            'timestamp': time.time(),
            'status': 'completed',
            'cycle_metrics': {
                'cycle_start_tx': cycle_start_tx_id,
                'original_dai_amount': original_dai_amount,
                'final_dai_amount': amount_dai_received,
                'dai_profit_loss': dai_profit_loss,
                'profit_loss_pct': profit_loss_pct,
                'arb_price_change_pct': arb_price_change_pct,
                'hold_duration_hours': hold_duration_hours,
                'cycle_success': dai_profit_loss > 0
            }
        }
        
        self.transactions.append(transaction)
        
        # Add to cycles tracking
        cycle_data = {
            'start_tx': cycle_start_tx_id,
            'end_tx': tx_id,
            'duration_hours': hold_duration_hours,
            'profit_loss_dai': dai_profit_loss,
            'profit_loss_pct': profit_loss_pct,
            'arb_performance_pct': arb_price_change_pct,
            'success': dai_profit_loss > 0,
            'timestamp': time.time()
        }
        
        self.cycles.append(cycle_data)
        self._update_performance_metrics()
        
        return transaction['cycle_metrics']
    
    def _update_performance_metrics(self):
        """Update overall performance metrics"""
        if not self.cycles:
            return
        
        successful_cycles = [c for c in self.cycles if c['success']]
        failed_cycles = [c for c in self.cycles if not c['success']]
        
        total_profit_loss = sum(c['profit_loss_dai'] for c in self.cycles)
        avg_duration = sum(c['duration_hours'] for c in self.cycles) / len(self.cycles)
        
        best_cycle = max(self.cycles, key=lambda x: x['profit_loss_dai'])
        worst_cycle = min(self.cycles, key=lambda x: x['profit_loss_dai'])
        
        self.performance_metrics.update({
            'total_cycles': len(self.cycles),
            'successful_cycles': len(successful_cycles),
            'failed_cycles': len(failed_cycles),
            'success_rate_pct': (len(successful_cycles) / len(self.cycles)) * 100,
            'net_profit_loss_dai': total_profit_loss,
            'avg_cycle_duration_hours': avg_duration,
            'best_cycle_profit_dai': best_cycle['profit_loss_dai'],
            'worst_cycle_loss_dai': worst_cycle['profit_loss_dai'],
            'total_volume_dai': sum(tx.get('amount_dai_in', 0) for tx in self.transactions if 'amount_dai_in' in tx)
        })
    
    def get_performance_report(self) -> Dict:
        """Generate comprehensive performance report"""
        return {
            'summary': self.performance_metrics,
            'recent_cycles': self.cycles[-10:],  # Last 10 cycles
            'recent_transactions': self.transactions[-20:],  # Last 20 transactions
            'generated_at': datetime.now().isoformat()
        }
    
    def save_tracking_data(self, filename: str = None):
        """Save tracking data to file"""
        if not filename:
            filename = f"transaction_tracking_{int(time.time())}.json"
        
        data = {
            'transactions': self.transactions,
            'cycles': self.cycles,
            'performance_metrics': self.performance_metrics,
            'saved_at': datetime.now().isoformat()
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            print(f"💾 Transaction tracking data saved: {filename}")
        except Exception as e:
            print(f"❌ Failed to save tracking data: {e}")

# Global tracker instance
transaction_tracker = TransactionValueTracker()
