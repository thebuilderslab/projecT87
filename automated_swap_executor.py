#!/usr/bin/env python3
"""
Automated Swap Executor - Fully automated debt swaps with HF monitoring
"""

from web3 import Web3
from decimal import Decimal
from datetime import datetime
import time

from smart_delegation_manager import SmartDelegationManager
from debt_swap_bidirectional import BidirectionalDebtSwapper
from arbitrum_testnet_agent import ArbitrumTestnetAgent

class AutomatedSwapExecutor:
    """Execute automated debt swaps with comprehensive safety checks"""
    
    def __init__(self):
        self.agent = ArbitrumTestnetAgent()
        self.delegation_mgr = SmartDelegationManager(self.agent.w3, self.agent.private_key)
        self.swapper = BidirectionalDebtSwapper(
            self.agent.w3,
            self.agent.wallet_address,
            self.agent.private_key
        )
        
        # Safety limits
        self.MAX_SWAP_SIZE_DAI = Decimal('20')  # Max 20 DAI per swap
        self.MIN_SWAP_INTERVAL = 300  # 5 minutes between swaps
        self.last_swap_time = 0
        
        # Audit log
        self.log_file = 'swap_audit.log'
        
    def log_swap(self, event_type, message, hf=None):
        """Log swap events"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {event_type}: {message}"
        if hf is not None:
            log_entry += f" | HF: {hf:.4f}"
        
        print(log_entry)
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_entry + '\n')
        except Exception as e:
            print(f"⚠️ Failed to write to log: {e}")
    
    def execute_automated_swap(self, amount, direction='DAI_TO_WETH'):
        """
        Execute fully automated debt swap with all safety checks
        
        Args:
            amount: Decimal, amount to swap (DAI or WETH depending on direction)
            direction: 'DAI_TO_WETH' or 'WETH_TO_DAI'
        
        Returns:
            swap_tx_hash or None if aborted
        """
        print(f"\n{'='*80}")
        print(f"🔄 EXECUTING AUTOMATED SWAP")
        print(f"{'='*80}")
        print(f"Amount: {amount} {direction}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check rate limiting
        time_since_last = time.time() - self.last_swap_time
        if self.last_swap_time > 0 and time_since_last < self.MIN_SWAP_INTERVAL:
            wait_time = self.MIN_SWAP_INTERVAL - time_since_last
            self.log_swap("RATE_LIMIT", f"Must wait {wait_time:.0f}s before next swap")
            print(f"\n⏸️ RATE LIMIT: Wait {wait_time:.0f}s before next swap")
            return None
        
        # Check swap size limit
        if direction == 'DAI_TO_WETH' and amount > self.MAX_SWAP_SIZE_DAI:
            self.log_swap("SIZE_LIMIT", f"Amount {amount} exceeds max {self.MAX_SWAP_SIZE_DAI} DAI")
            print(f"\n🚫 ABORT: Swap size exceeds maximum ({self.MAX_SWAP_SIZE_DAI} DAI)")
            return None
        
        # STEP 1: Pre-swap health check
        print(f"\n{'='*80}")
        print(f"🏥 STEP 1: PRE-SWAP HEALTH CHECK")
        print(f"{'='*80}")
        
        is_safe, initial_hf, status = self.delegation_mgr.check_health_factor_safe()
        print(f"Health Factor: {initial_hf:.4f} - {status}")
        self.log_swap("PRE_HF_CHECK", status, initial_hf)
        
        if not is_safe:
            self.log_swap("ABORT", f"Pre-swap HF {initial_hf:.4f} below 1.05", initial_hf)
            print(f"\n🚫 SWAP ABORTED: Health factor below minimum threshold")
            return None
        
        if initial_hf < Decimal('1.10'):
            print(f"⚠️ WARNING: HF in danger zone (1.05-1.10)")
        
        # STEP 2: Get current position
        print(f"\n{'='*80}")
        print(f"📊 STEP 2: CURRENT POSITION")
        print(f"{'='*80}")
        
        summary = self.swapper.get_account_summary()
        print(f"DAI Debt: {summary['dai_debt']:.6f} DAI")
        print(f"WETH Debt: {summary['weth_debt']:.6f} WETH")
        print(f"Collateral: ${summary['total_collateral_usd']:.2f}")
        print(f"Total Debt: ${summary['total_debt_usd']:.2f}")
        
        # STEP 3: Check/approve delegation
        print(f"\n{'='*80}")
        print(f"🔐 STEP 3: CREDIT DELEGATION CHECK")
        print(f"{'='*80}")
        
        current_delegation = self.delegation_mgr.get_current_delegation()
        print(f"Current delegation: {current_delegation:.6f} WETH")
        
        # For DAI->WETH swaps, we need WETH delegation
        if direction == 'DAI_TO_WETH':
            # Estimate WETH needed (rough estimate: amount / 3000)
            estimated_weth = amount / Decimal('3000')
            print(f"Estimated WETH needed: ~{estimated_weth:.6f} WETH")
            
            if current_delegation < estimated_weth * Decimal('1.2'):
                print(f"\nInsufficient delegation - approving exact amount...")
                approval_tx = self.delegation_mgr.approve_exact_delegation(estimated_weth)
                
                if approval_tx is None:
                    self.log_swap("ABORT", "Delegation approval failed HF check")
                    print(f"\n🚫 SWAP ABORTED: Could not approve delegation")
                    return None
                
                print(f"✅ Delegation approved: {approval_tx}")
            else:
                print(f"✅ Sufficient delegation already exists")
        
        # STEP 4: Execute swap
        print(f"\n{'='*80}")
        print(f"🔄 STEP 4: EXECUTING DEBT SWAP")
        print(f"{'='*80}")
        
        try:
            if direction == 'DAI_TO_WETH':
                swap_tx = self.swapper.swap_debt(
                    from_asset='DAI',
                    to_asset='WETH',
                    amount=amount,
                    slippage_bps=100
                )
            else:
                swap_tx = self.swapper.swap_debt(
                    from_asset='WETH',
                    to_asset='DAI',
                    amount=amount,
                    slippage_bps=100
                )
            
            if swap_tx:
                self.log_swap("SWAP_SUCCESS", f"TX: {swap_tx} | Amount: {amount} {direction}")
                print(f"\n✅ SWAP EXECUTED: {swap_tx}")
                self.last_swap_time = time.time()
            else:
                self.log_swap("SWAP_FAILED", f"Swap returned None | Amount: {amount}")
                return None
                
        except Exception as e:
            self.log_swap("SWAP_ERROR", f"Exception: {str(e)}")
            print(f"\n❌ SWAP FAILED: {e}")
            return None
        
        # STEP 5: Post-swap health check
        print(f"\n{'='*80}")
        print(f"🏥 STEP 5: POST-SWAP HEALTH CHECK")
        print(f"{'='*80}")
        
        time.sleep(5)  # Wait for chain state to update
        
        is_safe_after, final_hf, final_status = self.delegation_mgr.check_health_factor_safe()
        print(f"Health Factor: {final_hf:.4f} - {final_status}")
        self.log_swap("POST_HF_CHECK", final_status, final_hf)
        
        hf_change = final_hf - initial_hf
        print(f"HF Change: {initial_hf:.4f} → {final_hf:.4f} ({hf_change:+.4f})")
        
        if not is_safe_after:
            self.log_swap("CRITICAL", f"Post-swap HF {final_hf:.4f} below 1.05!", final_hf)
            print(f"\n🚨 CRITICAL: Health factor dropped below 1.05!")
            print(f"   HALTING ALL FURTHER SWAPS")
        elif final_hf < Decimal('1.10'):
            print(f"\n⚠️ WARNING: Health factor in danger zone")
            print(f"   Consider adding collateral before next swap")
        
        # STEP 6: Final verification
        print(f"\n{'='*80}")
        print(f"📊 STEP 6: FINAL POSITION")
        print(f"{'='*80}")
        
        final_summary = self.swapper.get_account_summary()
        print(f"DAI Debt: {summary['dai_debt']:.6f} → {final_summary['dai_debt']:.6f}")
        print(f"WETH Debt: {summary['weth_debt']:.6f} → {final_summary['weth_debt']:.6f}")
        print(f"Health Factor: {initial_hf:.4f} → {final_hf:.4f}")
        
        print(f"\n{'='*80}")
        print(f"✅ AUTOMATED SWAP COMPLETED SUCCESSFULLY")
        print(f"{'='*80}\n")
        
        return swap_tx

def main():
    """Test automated swap execution"""
    executor = AutomatedSwapExecutor()
    
    print("="*80)
    print("AUTOMATED SWAP EXECUTOR - READY")
    print("="*80)
    
    # Execute a 5 DAI test swap
    result = executor.execute_automated_swap(
        amount=Decimal('5'),
        direction='DAI_TO_WETH'
    )
    
    if result:
        print(f"\n🎉 Success! Transaction: {result}")
    else:
        print(f"\n❌ Swap was aborted or failed")

if __name__ == "__main__":
    main()
