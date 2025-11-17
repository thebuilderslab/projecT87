#!/usr/bin/env python3
"""
Smart Delegation Manager - Auto-approves exact WETH delegation with HF monitoring
"""

from web3 import Web3
from decimal import Decimal
import json
import time
from datetime import datetime

class SmartDelegationManager:
    """Manages WETH credit delegation with health factor safety checks"""
    
    def __init__(self, w3, private_key):
        self.w3 = w3
        self.account = w3.eth.account.from_key(private_key)
        self.wallet_address = self.account.address
        
        # Contract addresses - Verified from manual MetaMask swaps
        self.weth_debt_token = "0x0c84331e39d6658Cd6e6b9ba04736cC4c4734351"
        self.paraswap_adapter = "0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4"
        self.aave_pool = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
        
        # Safety parameters - Aggressive mode for experienced DeFi
        self.SAFETY_BUFFER = Decimal('1.15')  # 15% buffer on needed amount
        self.MAX_DELEGATION_PER_SWAP = Decimal('1.0')  # Max 1 WETH per swap
        self.MIN_HEALTH_FACTOR = Decimal('1.05')  # CRITICAL: Abort below 1.05
        self.WARNING_HEALTH_FACTOR = Decimal('1.10')  # Warning zone
        
        # Logging
        self.log_file = 'delegation_audit.log'
        
    def log_event(self, event_type, message, hf=None):
        """Log delegation events to audit trail"""
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
    
    def get_current_delegation(self):
        """Check current WETH credit delegation allowance"""
        weth_debt_abi = [{
            "inputs": [{"name": "fromUser", "type": "address"}, {"name": "toUser", "type": "address"}],
            "name": "borrowAllowance",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }]
        
        weth_debt = self.w3.eth.contract(
            address=self.weth_debt_token,
            abi=weth_debt_abi
        )
        
        allowance = weth_debt.functions.borrowAllowance(
            self.wallet_address,
            self.paraswap_adapter
        ).call()
        
        return Decimal(allowance) / Decimal(10**18)
    
    def check_health_factor_safe(self):
        """
        Check if health factor is safe for swap execution
        
        Returns:
            (is_safe: bool, health_factor: Decimal, status: str)
        """
        pool_abi = [{
            "inputs": [{"name": "user", "type": "address"}],
            "name": "getUserAccountData",
            "outputs": [
                {"name": "totalCollateralBase", "type": "uint256"},
                {"name": "totalDebtBase", "type": "uint256"},
                {"name": "availableBorrowsBase", "type": "uint256"},
                {"name": "currentLiquidationThreshold", "type": "uint256"},
                {"name": "ltv", "type": "uint256"},
                {"name": "healthFactor", "type": "uint256"}
            ],
            "stateMutability": "view",
            "type": "function"
        }]
        
        pool = self.w3.eth.contract(address=self.aave_pool, abi=pool_abi)
        user_data = pool.functions.getUserAccountData(self.wallet_address).call()
        health_factor = Decimal(user_data[5]) / Decimal(10**18)
        
        if health_factor < self.MIN_HEALTH_FACTOR:
            return (False, health_factor, "CRITICAL - Below 1.05 threshold")
        elif health_factor < self.WARNING_HEALTH_FACTOR:
            return (True, health_factor, "WARNING - Between 1.05-1.10")
        else:
            return (True, health_factor, "SAFE - Above 1.10")
    
    def approve_exact_delegation(self, weth_amount_needed):
        """
        Approve exact WETH delegation needed for upcoming swap
        WITH MANDATORY HEALTH FACTOR CHECK
        
        Args:
            weth_amount_needed: Decimal, amount of WETH needed (in WETH, not wei)
        
        Returns:
            tx_hash: Transaction hash of approval, or None if aborted
        """
        # CRITICAL: Pre-check health factor
        is_safe, hf, status = self.check_health_factor_safe()
        self.log_event("HF_CHECK", f"Pre-delegation check - {status}", hf)
        
        if not is_safe:
            self.log_event("ABORT", f"Health factor {hf:.4f} below minimum {self.MIN_HEALTH_FACTOR}", hf)
            print(f"\n🚫 ABORT: Health factor {hf:.4f} is below minimum threshold {self.MIN_HEALTH_FACTOR}")
            return None
        
        # Add safety buffer
        safe_amount = weth_amount_needed * self.SAFETY_BUFFER
        
        # Cap at maximum per-swap limit
        if safe_amount > self.MAX_DELEGATION_PER_SWAP:
            self.log_event("WARNING", f"Requested {safe_amount} WETH exceeds max {self.MAX_DELEGATION_PER_SWAP}")
            print(f"⚠️ WARNING: Capping at {self.MAX_DELEGATION_PER_SWAP} WETH")
            safe_amount = self.MAX_DELEGATION_PER_SWAP
        
        # Convert to wei
        amount_wei = int(safe_amount * Decimal(10**18))
        
        self.log_event("DELEGATION", f"Approving {safe_amount:.6f} WETH ({amount_wei} wei)", hf)
        print(f"📝 Approving delegation: {safe_amount:.6f} WETH")
        
        # Build approval transaction
        weth_debt_abi = [{
            "inputs": [{"name": "delegatee", "type": "address"}, {"name": "amount", "type": "uint256"}],
            "name": "approveDelegation",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }]
        
        weth_debt = self.w3.eth.contract(
            address=self.weth_debt_token,
            abi=weth_debt_abi
        )
        
        base_fee = self.w3.eth.gas_price
        
        tx = weth_debt.functions.approveDelegation(
            self.paraswap_adapter,
            amount_wei
        ).build_transaction({
            'from': self.wallet_address,
            'nonce': self.w3.eth.get_transaction_count(self.wallet_address),
            'gas': 100000,
            'maxFeePerGas': int(base_fee * 2),
            'maxPriorityFeePerGas': self.w3.to_wei('0.01', 'gwei'),
            'chainId': 42161
        })
        
        # Sign and send
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_hash_hex = tx_hash.hex()
        
        self.log_event("TX_SENT", f"Delegation tx: {tx_hash_hex}")
        print(f"✅ Delegation approval sent: {tx_hash_hex}")
        print(f"   Arbiscan: https://arbiscan.io/tx/{tx_hash_hex}")
        
        # Wait for confirmation
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt['status'] == 1:
            self.log_event("SUCCESS", f"Delegation approved - Gas used: {receipt['gasUsed']}")
            print(f"✅ Delegation approved successfully (block {receipt['blockNumber']})")
            return tx_hash_hex
        else:
            self.log_event("FAILED", "Delegation transaction reverted")
            raise Exception("Delegation approval failed")
    
    def reset_delegation(self):
        """Reset delegation to 0 after swap (optional security measure)"""
        self.log_event("RESET", "Resetting delegation to 0")
        return self.approve_exact_delegation(Decimal('0'))

if __name__ == "__main__":
    # Test the delegation manager
    from arbitrum_testnet_agent import ArbitrumTestnetAgent
    
    print("="*80)
    print("SMART DELEGATION MANAGER TEST")
    print("="*80)
    
    agent = ArbitrumTestnetAgent()
    manager = SmartDelegationManager(agent.w3, agent.private_key)
    
    # Check current delegation
    current = manager.get_current_delegation()
    print(f"\n📊 Current delegation: {current:.6f} WETH")
    
    # Check health factor
    is_safe, hf, status = manager.check_health_factor_safe()
    print(f"❤️ Health Factor: {hf:.4f} - {status}")
    
    if is_safe:
        print(f"✅ System ready for automated swaps")
    else:
        print(f"❌ System NOT safe - add collateral")
