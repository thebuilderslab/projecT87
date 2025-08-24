
"""
Enhanced Borrow Manager with DAI-only compliance
Manages sophisticated borrowing strategies on Aave with strict DAI-only operations
"""

import time
import json
from decimal import Decimal
from datetime import datetime

class EnhancedBorrowManager:
    def __init__(self, agent):
        self.agent = agent
        self.w3 = agent.w3
        self.address = agent.address
        self.aave = agent.aave
        self.uniswap = agent.uniswap
        
        # DAI-only compliance settings
        self.dai_address = agent.dai_address
        self.wbtc_address = agent.wbtc_address
        self.weth_address = agent.weth_address
        
        # Enhanced borrowing parameters
        self.min_health_factor = 2.1
        self.target_health_factor = 3.5
        self.max_borrow_amount = 200.0  # USD
        self.min_borrow_amount = 10.0   # USD
        
        # Operation tracking
        self.last_operation_time = 0
        self.operation_cooldown = 60  # seconds
        
    def execute_enhanced_borrow_sequence(self, available_capacity):
        """Execute enhanced borrowing sequence with DAI-only compliance"""
        try:
            print(f"🚀 Enhanced Borrow Manager: Starting sequence with ${available_capacity:.2f} capacity")
            
            # Check cooldown
            if self._is_on_cooldown():
                print("⏰ Operation on cooldown, skipping")
                return False
                
            # Pre-flight safety checks
            if not self._pre_flight_checks():
                print("❌ Pre-flight checks failed")
                return False
                
            # Calculate optimal borrow amount
            borrow_amount = self._calculate_optimal_borrow_amount(available_capacity)
            if borrow_amount < self.min_borrow_amount:
                print(f"💰 Calculated borrow amount ${borrow_amount:.2f} below minimum ${self.min_borrow_amount}")
                return False
                
            print(f"💰 Calculated optimal borrow amount: ${borrow_amount:.2f}")
            
            # Step 1: Borrow DAI
            print("📈 Step 1: Borrowing DAI from Aave...")
            borrow_success = self.aave.borrow_asset(self.dai_address, borrow_amount)
            
            if not borrow_success:
                print("❌ DAI borrow failed")
                return False
                
            print("✅ DAI borrow successful")
            time.sleep(3)  # Wait for transaction confirmation
            
            # Step 2: Strategic swaps (DAI-only compliance)
            print("📈 Step 2: Executing strategic swaps...")
            swap_success = self._execute_strategic_swaps(borrow_amount)
            
            if not swap_success:
                print("⚠️ Swaps failed, but borrow was successful")
                # Don't return False - borrow still succeeded
                
            # Step 3: Supply new assets as collateral
            print("📈 Step 3: Supplying new assets as collateral...")
            supply_success = self._supply_new_collateral()
            
            if supply_success:
                print("✅ Enhanced borrow sequence completed successfully")
                self.last_operation_time = time.time()
                return True
            else:
                print("⚠️ Collateral supply had issues, but core operations succeeded")
                self.last_operation_time = time.time()
                return True
                
        except Exception as e:
            print(f"❌ Enhanced borrow sequence failed: {e}")
            return False
            
    def _is_on_cooldown(self):
        """Check if operation is on cooldown"""
        current_time = time.time()
        time_since_last = current_time - self.last_operation_time
        return time_since_last < self.operation_cooldown
        
    def _pre_flight_checks(self):
        """Perform pre-flight safety checks"""
        try:
            # Check health factor
            health_factor = self.aave.get_health_factor()
            if health_factor < self.min_health_factor:
                print(f"❌ Health factor too low: {health_factor}")
                return False
                
            # Check network connectivity
            if not self.w3.is_connected():
                print("❌ Network not connected")
                return False
                
            # Check gas balance
            eth_balance = self.w3.eth.get_balance(self.address)
            min_eth_needed = self.w3.to_wei(0.01, 'ether')  # 0.01 ETH minimum
            if eth_balance < min_eth_needed:
                print(f"❌ Insufficient ETH for gas: {self.w3.from_wei(eth_balance, 'ether'):.6f}")
                return False
                
            print("✅ Pre-flight checks passed")
            return True
            
        except Exception as e:
            print(f"❌ Pre-flight check error: {e}")
            return False
            
    def _calculate_optimal_borrow_amount(self, available_capacity):
        """Calculate optimal borrow amount based on capacity and risk"""
        try:
            # Base amount on available capacity
            base_amount = min(available_capacity * 0.6, self.max_borrow_amount)
            
            # Adjust based on current health factor
            health_factor = self.aave.get_health_factor()
            if health_factor > 4.0:
                multiplier = 1.2  # Can borrow more with high health factor
            elif health_factor > 3.0:
                multiplier = 1.0  # Standard amount
            else:
                multiplier = 0.7  # Reduce for lower health factor
                
            optimal_amount = base_amount * multiplier
            
            # Ensure within bounds
            return max(self.min_borrow_amount, min(optimal_amount, self.max_borrow_amount))
            
        except Exception as e:
            print(f"❌ Error calculating optimal borrow amount: {e}")
            return self.min_borrow_amount
            
    def _execute_strategic_swaps(self, borrowed_amount):
        """Execute strategic swaps with DAI-only compliance"""
        try:
            print("🔄 Executing DAI-only strategic swaps...")
            
            # Check current DAI balance
            dai_balance = self.aave.get_token_balance(self.dai_address)
            
            if dai_balance < 5.0:  # Need minimum DAI for swaps
                print(f"⚠️ Insufficient DAI balance for swaps: ${dai_balance:.2f}")
                return False
                
            swap_success = False
            
            # Swap 1: DAI → WETH (40% of available)
            weth_swap_amount = min(dai_balance * 0.4, 20.0)
            if weth_swap_amount >= 3.0:  # Minimum swap amount
                print(f"🔄 Swapping ${weth_swap_amount:.2f} DAI → WETH")
                weth_tx = self.uniswap.swap_tokens(
                    self.dai_address,
                    self.weth_address,
                    weth_swap_amount,
                    500  # 0.05% fee
                )
                if weth_tx:
                    print("✅ DAI → WETH swap successful")
                    swap_success = True
                    time.sleep(2)
                    
            # Swap 2: DAI → WBTC (20% of available)
            remaining_dai = self.aave.get_token_balance(self.dai_address)
            wbtc_swap_amount = min(remaining_dai * 0.2, 15.0)
            if wbtc_swap_amount >= 3.0:  # Minimum swap amount
                print(f"🔄 Swapping ${wbtc_swap_amount:.2f} DAI → WBTC")
                wbtc_tx = self.uniswap.swap_tokens(
                    self.dai_address,
                    self.wbtc_address,
                    wbtc_swap_amount,
                    500  # 0.05% fee
                )
                if wbtc_tx:
                    print("✅ DAI → WBTC swap successful")
                    swap_success = True
                    
            return swap_success
            
        except Exception as e:
            print(f"❌ Strategic swaps failed: {e}")
            return False
            
    def _supply_new_collateral(self):
        """Supply newly acquired assets as collateral"""
        try:
            print("🏦 Supplying new assets as collateral...")
            
            success_count = 0
            
            # Supply WETH if available
            weth_balance = self.aave.get_token_balance(self.weth_address)
            if weth_balance > 0.001:  # Minimum WETH to supply
                print(f"🏦 Supplying {weth_balance:.6f} WETH as collateral")
                if self.aave.supply_asset(self.weth_address, weth_balance):
                    print("✅ WETH supplied as collateral")
                    success_count += 1
                    time.sleep(2)
                    
            # Supply WBTC if available
            wbtc_balance = self.aave.get_token_balance(self.wbtc_address)
            if wbtc_balance > 0.00001:  # Minimum WBTC to supply
                print(f"🏦 Supplying {wbtc_balance:.8f} WBTC as collateral")
                if self.aave.supply_asset(self.wbtc_address, wbtc_balance):
                    print("✅ WBTC supplied as collateral")
                    success_count += 1
                    
            return success_count > 0
            
        except Exception as e:
            print(f"❌ Collateral supply failed: {e}")
            return False
            
    def execute_enhanced_borrow_with_retry(self, amount_usd):
        """Execute enhanced borrow with retry mechanism - DAI only"""
        try:
            print(f"🚀 Enhanced Borrow with Retry: ${amount_usd:.2f} DAI")
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    print(f"🔄 Borrow attempt {attempt + 1}/{max_retries}")
                    
                    # Use direct DAI borrow
                    success = self.aave.borrow(amount_usd, self.dai_address)
                    
                    if success:
                        print(f"✅ DAI borrow successful on attempt {attempt + 1}")
                        self.last_operation_time = time.time()
                        return True
                    else:
                        print(f"❌ DAI borrow failed on attempt {attempt + 1}")
                        if attempt < max_retries - 1:
                            time.sleep(2)  # Wait before retry
                            
                except Exception as e:
                    print(f"❌ Borrow attempt {attempt + 1} error: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(3)  # Wait longer on exception
                        
            print(f"❌ All {max_retries} borrow attempts failed")
            return False
            
        except Exception as e:
            print(f"❌ Enhanced borrow with retry failed: {e}")
            return False

    def get_operation_status(self):
        """Get current operation status"""
        try:
            current_time = time.time()
            time_since_last = current_time - self.last_operation_time
            cooldown_remaining = max(0, self.operation_cooldown - time_since_last)
            
            health_factor = self.aave.get_health_factor()
            
            return {
                'on_cooldown': cooldown_remaining > 0,
                'cooldown_remaining': cooldown_remaining,
                'health_factor': health_factor,
                'ready_for_operation': health_factor > self.min_health_factor and cooldown_remaining == 0,
                'last_operation': datetime.fromtimestamp(self.last_operation_time).strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            print(f"❌ Error getting operation status: {e}")
            return {'error': str(e)}
