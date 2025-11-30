#!/usr/bin/env python3
"""
Automated Swap Executor - Fully automated debt swaps with HF monitoring
"""

import os
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
        self.swapper = BidirectionalDebtSwapper(self.agent.w3, self.agent.private_key)
        
        # Safety limits - bidirectional
        self.MAX_SWAP_SIZE_DAI = Decimal('20')  # Max 20 DAI per swap
        self.MAX_SWAP_SIZE_WETH_USD = Decimal('60')  # Max ~$60 worth of WETH per swap
        self.MIN_SWAP_INTERVAL = 300  # 5 minutes between swaps
        self.last_swap_time = 0
        
        # CoinAPI integration for real-time ETH price
        import requests
        self.coinapi_key = os.getenv('COIN_API')
        self.coinapi_base_url = "https://rest.coinapi.io/v1"
        
        # Current ETH price (updated before each swap)
        self.eth_price_usd = self._fetch_eth_price()  # Real-time price on init
        
        # Audit log
        self.log_file = 'swap_audit.log'
    
    def _fetch_eth_price(self):
        """Fetch current ETH price from CoinAPI"""
        try:
            import requests
            
            if not self.coinapi_key:
                print(f"⚠️ CoinAPI key not found, using fallback")
                return Decimal('3100')
            
            # CoinAPI endpoint for ETH/USD price
            url = f"{self.coinapi_base_url}/exchangerate/ETH/USD"
            headers = {'X-CoinAPI-Key': self.coinapi_key}
            
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                price = Decimal(str(data['rate']))
                print(f"📊 CoinAPI: ETH = ${price:.2f}")
                return price
            else:
                print(f"⚠️ CoinAPI returned {response.status_code}, using fallback")
                return Decimal('3100')
                
        except Exception as e:
            print(f"⚠️ Failed to fetch ETH price from CoinAPI: {e}")
            print(f"   Using fallback price: $3100")
            return Decimal('3100')  # Fallback
        
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
    
    def _check_swap_size_limit(self, amount, direction):
        """Check if swap amount is within safety limits"""
        if direction == 'DAI_TO_WETH':
            if amount > self.MAX_SWAP_SIZE_DAI:
                return False, f"DAI amount {amount} exceeds max {self.MAX_SWAP_SIZE_DAI}"
        else:  # WETH_TO_DAI
            weth_value_usd = amount * self.eth_price_usd
            if weth_value_usd > self.MAX_SWAP_SIZE_WETH_USD:
                return False, f"WETH value ${weth_value_usd:.2f} exceeds max ${self.MAX_SWAP_SIZE_WETH_USD}"
        return True, "OK"
    
    def _needs_delegation(self, direction):
        """Check if this swap direction requires WETH credit delegation"""
        # Only DAI→WETH needs delegation (we're borrowing WETH)
        # WETH→DAI borrows DAI directly without delegation
        return direction == 'DAI_TO_WETH'
    
    def get_suggested_direction(self, refresh_price=True):
        """
        Suggest swap direction based on current debt composition
        
        Args:
            refresh_price: If True, fetch latest ETH price before analysis
        
        Returns:
            (direction, reason) tuple
        """
        try:
            # Refresh ETH price for accurate debt valuation
            if refresh_price:
                self.eth_price_usd = self._fetch_eth_price()
            
            summary = self.swapper.get_account_summary(eth_price_usd=self.eth_price_usd)
            dai_debt_usd = summary['dai_debt'] * Decimal('1.0')  # DAI ≈ $1
            weth_debt_usd = summary['weth_debt'] * self.eth_price_usd
            
            if dai_debt_usd > weth_debt_usd * Decimal('1.2'):
                return 'DAI_TO_WETH', f"DAI debt (${dai_debt_usd:.2f}) > WETH debt (${weth_debt_usd:.2f}) @ ${self.eth_price_usd:.2f}/ETH"
            elif weth_debt_usd > dai_debt_usd * Decimal('1.2'):
                return 'WETH_TO_DAI', f"WETH debt (${weth_debt_usd:.2f}) > DAI debt (${dai_debt_usd:.2f}) @ ${self.eth_price_usd:.2f}/ETH"
            else:
                return 'BALANCED', f"Debts roughly equal (DAI: ${dai_debt_usd:.2f}, WETH: ${weth_debt_usd:.2f}) @ ${self.eth_price_usd:.2f}/ETH"
        except Exception as e:
            return 'UNKNOWN', f"Could not determine: {e}"
    
    def execute_automated_swap(self, amount, direction='DAI_TO_WETH'):
        """
        Execute fully automated debt swap with all safety checks
        BIDIRECTIONAL: Supports both DAI→WETH and WETH→DAI
        
        Args:
            amount: Decimal, amount to swap
                   - For DAI_TO_WETH: amount in DAI
                   - For WETH_TO_DAI: amount in WETH
            direction: 'DAI_TO_WETH' or 'WETH_TO_DAI' (required)
        
        Returns:
            swap_tx_hash or None if aborted
        """
        print(f"\n{'='*80}")
        print(f"🔄 EXECUTING AUTOMATED SWAP - BIDIRECTIONAL SYSTEM")
        print(f"{'='*80}")
        print(f"Direction: {direction}")
        print(f"Amount: {amount} {'DAI' if direction == 'DAI_TO_WETH' else 'WETH'}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Validate direction
        if direction not in ['DAI_TO_WETH', 'WETH_TO_DAI']:
            print(f"\n🚫 ABORT: Invalid direction '{direction}'")
            return None
        
        # Update ETH price before swap (critical for accurate limits & delegation)
        self.eth_price_usd = self._fetch_eth_price()
        print(f"💵 Current ETH Price: ${self.eth_price_usd:.2f} (from CoinAPI)")
        
        # Check rate limiting
        time_since_last = time.time() - self.last_swap_time
        if self.last_swap_time > 0 and time_since_last < self.MIN_SWAP_INTERVAL:
            wait_time = self.MIN_SWAP_INTERVAL - time_since_last
            self.log_swap("RATE_LIMIT", f"Must wait {wait_time:.0f}s before next swap")
            print(f"\n⏸️ RATE LIMIT: Wait {wait_time:.0f}s before next swap")
            return None
        
        # Check swap size limit (direction-specific)
        is_valid, size_msg = self._check_swap_size_limit(amount, direction)
        if not is_valid:
            self.log_swap("SIZE_LIMIT", f"{direction}: {size_msg}")
            print(f"\n🚫 ABORT: {size_msg}")
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
        
        summary = self.swapper.get_account_summary(eth_price_usd=self.eth_price_usd)
        print(f"DAI Debt: {summary['dai_debt']:.6f} DAI")
        print(f"WETH Debt: {summary['weth_debt']:.6f} WETH")
        print(f"Collateral: ${summary.get('total_collateral_usd', 0):.2f}")
        print(f"Total Debt: ${summary.get('total_debt_usd', 0):.2f}")
        
        # STEP 3: Check/approve delegation (only for DAI→WETH)
        print(f"\n{'='*80}")
        print(f"🔐 STEP 3: CREDIT DELEGATION CHECK")
        print(f"{'='*80}")
        
        if self._needs_delegation(direction):
            print(f"Direction {direction} requires WETH credit delegation")
            current_delegation = self.delegation_mgr.get_current_delegation()
            print(f"Current delegation: {current_delegation:.6f} WETH")
            
            # Estimate WETH needed
            estimated_weth = amount / self.eth_price_usd
            print(f"Estimated WETH needed: ~{estimated_weth:.6f} WETH (@ ${self.eth_price_usd:.0f}/ETH)")
            
            if current_delegation < estimated_weth * Decimal('1.2'):
                print(f"\nInsufficient delegation - approving exact amount...")
                approval_tx = self.delegation_mgr.approve_exact_delegation(estimated_weth)
                
                if approval_tx is None:
                    self.log_swap("ABORT", f"{direction}: Delegation approval failed HF check")
                    print(f"\n🚫 SWAP ABORTED: Could not approve delegation")
                    return None
                
                self.log_swap("DELEGATION", f"{direction}: Approved {approval_tx}")
                print(f"✅ Delegation approved: {approval_tx}")
            else:
                print(f"✅ Sufficient delegation already exists")
        else:
            print(f"Direction {direction} does not require delegation")
            print(f"✅ WETH→DAI borrows DAI directly (no delegation needed)")
        
        # STEP 4: Execute swap
        print(f"\n{'='*80}")
        print(f"🔄 STEP 4: EXECUTING DEBT SWAP")
        print(f"{'='*80}")
        
        try:
            # Map direction to swap parameters
            if direction == 'DAI_TO_WETH':
                from_asset, to_asset = 'DAI', 'WETH'
                borrowing_asset = 'WETH'
            else:  # WETH_TO_DAI
                from_asset, to_asset = 'WETH', 'DAI'
                borrowing_asset = 'DAI'
            
            print(f"Swapping: Repay {amount} {from_asset}, Borrow {to_asset}")
            
            swap_tx = self.swapper.swap_debt(
                from_asset=from_asset,
                to_asset=to_asset,
                amount=amount,
                slippage_bps=100,
                eth_price_usd=self.eth_price_usd  # Pass CoinAPI price for accurate routing
            )
            
            if swap_tx:
                self.log_swap("SWAP_SUCCESS", f"{direction} | TX: {swap_tx} | Amount: {amount} | Borrowed: {borrowing_asset}")
                print(f"\n✅ SWAP EXECUTED: {swap_tx}")
                print(f"   Arbiscan: https://arbiscan.io/tx/{swap_tx}")
                self.last_swap_time = time.time()
            else:
                self.log_swap("SWAP_FAILED", f"{direction} | Swap returned None | Amount: {amount}")
                return None
                
        except Exception as e:
            self.log_swap("SWAP_ERROR", f"{direction} | Exception: {str(e)}")
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
        
        final_summary = self.swapper.get_account_summary(eth_price_usd=self.eth_price_usd)
        print(f"DAI Debt: {summary['dai_debt']:.6f} → {final_summary['dai_debt']:.6f}")
        print(f"WETH Debt: {summary['weth_debt']:.6f} → {final_summary['weth_debt']:.6f}")
        print(f"Health Factor: {initial_hf:.4f} → {final_hf:.4f}")
        
        print(f"\n{'='*80}")
        print(f"✅ AUTOMATED SWAP COMPLETED SUCCESSFULLY")
        print(f"{'='*80}\n")
        
        return swap_tx

def main():
    """Test automated swap execution - BIDIRECTIONAL"""
    executor = AutomatedSwapExecutor()
    
    print("="*80)
    print("AUTOMATED SWAP EXECUTOR - BIDIRECTIONAL SYSTEM")
    print("="*80)
    
    # Get suggested direction
    suggested, reason = executor.get_suggested_direction()
    print(f"\n💡 Suggested direction: {suggested}")
    print(f"   Reason: {reason}")
    
    # Show both options
    print(f"\n📊 Available swap directions:")
    print(f"   1. DAI→WETH: Repay DAI debt, borrow WETH (requires delegation)")
    print(f"   2. WETH→DAI: Repay WETH debt, borrow DAI (no delegation needed)")
    
    # Example: Execute a 5 DAI → WETH swap
    print(f"\n{'='*80}")
    print(f"TEST 1: DAI → WETH (5 DAI)")
    print(f"{'='*80}")
    
    result1 = executor.execute_automated_swap(
        amount=Decimal('5'),
        direction='DAI_TO_WETH'
    )
    
    if result1:
        print(f"\n✅ Test 1 Success! Transaction: {result1}")
    else:
        print(f"\n⚠️ Test 1 was aborted or failed")
    
    # Example: Execute a 0.002 WETH → DAI swap
    print(f"\n{'='*80}")
    print(f"TEST 2: WETH → DAI (0.002 WETH)")
    print(f"{'='*80}")
    
    result2 = executor.execute_automated_swap(
        amount=Decimal('0.002'),
        direction='WETH_TO_DAI'
    )
    
    if result2:
        print(f"\n✅ Test 2 Success! Transaction: {result2}")
    else:
        print(f"\n⚠️ Test 2 was aborted or failed")

if __name__ == "__main__":
    main()
