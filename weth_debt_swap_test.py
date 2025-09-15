#!/usr/bin/env python3
"""
Simple WETH Debt Swap Test - Minimal Implementation
Test: $2 DAI debt → WETH debt (safer alternative)
"""

import os
import time
import json
from datetime import datetime
from corrected_debt_swap_executor import CorrectedDebtSwapExecutor

def test_weth_debt_swap():
    """Test DAI debt → WETH debt swap (should be more reliable)"""
    
    print("🧪 SIMPLE WETH DEBT SWAP TEST")
    print("=" * 50)
    print("Test: $2 DAI debt → WETH debt")
    print("=" * 50)
    
    # Initialize agent (simplified)
    import sys
    sys.path.append('.')
    
    # Import agent from the existing test
    import importlib.util
    spec = importlib.util.spec_from_file_location("agent_module", "onchain_debt_swap_test.py")
    agent_module = importlib.util.module_from_spec(spec)
    
    # Create a simple agent-like object
    from web3 import Web3
    import os
    
    class SimpleAgent:
        def __init__(self):
            self.w3 = Web3(Web3.HTTPProvider('https://arb-mainnet.g.alchemy.com/v2/6ZvYzOV1E80R-bM9XgIIU'))
            self.address = "0x5B823270e3719CDe8669e5e5326B455EaA8a350b"
    
    agent = SimpleAgent()
    executor = CorrectedDebtSwapExecutor(agent)
    
    # Test configuration
    test_amount_usd = 2.0
    amount_to_swap = int(test_amount_usd * 1e18)  # $2 DAI
    
    print(f"💰 Wallet: {agent.address}")
    print(f"💱 Amount: ${test_amount_usd} DAI debt → WETH debt")
    
    try:
        # Get WETH debt token address
        weth_debt_token = executor.get_debt_token_address('WETH')
        print(f"📋 WETH debt token: {weth_debt_token}")
        
        if not weth_debt_token:
            print("❌ Failed to get WETH debt token address")
            return False
        
        # Get ParaSwap calldata (WETH → DAI routing for DAI → WETH debt swap)
        print("🌐 Getting ParaSwap routing for WETH → DAI...")
        
        # Use executor's method but modify tokens
        original_tokens = executor.tokens.copy()
        executor.tokens['WETH'] = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"
        
        paraswap_data = executor.get_paraswap_calldata_reverse_routing(
            'DAI', 'WETH', amount_to_swap
        )
        
        # Restore original tokens
        executor.tokens = original_tokens
        
        if not paraswap_data:
            print("❌ Failed to get ParaSwap calldata")
            return False
        
        print(f"✅ ParaSwap calldata obtained: {len(paraswap_data.get('calldata', ''))} chars")
        
        # Create credit delegation permit for WETH debt
        private_key = os.getenv('AGENT_PRIVATE_KEY')
        if not private_key:
            print("❌ Private key not found")
            return False
        
        credit_permit = executor.create_correct_credit_delegation_permit(
            private_key, weth_debt_token
        )
        
        if not credit_permit:
            print("❌ Failed to create credit delegation permit")
            return False
        
        print("✅ Credit delegation permit created")
        
        # Build transaction
        debt_swap_contract = agent.w3.eth.contract(
            address=executor.paraswap_debt_swap_adapter,
            abi=executor.debt_swap_adapter_abi
        )
        
        function_call = debt_swap_contract.functions.swapDebt(
            executor.tokens['DAI'],    # assetToSwapFrom (DAI)
            executor.tokens['WETH'],   # assetToSwapTo (WETH)
            amount_to_swap,           # amountToSwap ($2 worth)
            bytes.fromhex(paraswap_data['calldata'][2:]),  # paraswapData
            (
                credit_permit['token'],       # token
                credit_permit['delegatee'],   # delegatee  
                credit_permit['value'],       # value
                credit_permit['deadline'],    # deadline
                credit_permit['v'],           # v
                credit_permit['r'],           # r
                credit_permit['s']            # s
            )
        )
        
        # Estimate gas
        try:
            gas_estimate = function_call.estimate_gas({'from': agent.address})
            gas_limit = int(gas_estimate * 1.3)  # 30% buffer
            print(f"⛽ Gas estimate: {gas_estimate:,}")
        except Exception as e:
            print(f"⚠️ Gas estimation failed: {e}")
            gas_limit = 800000  # Conservative fallback
        
        # Build transaction  
        transaction = function_call.build_transaction({
            'from': agent.address,
            'gas': gas_limit,
            'gasPrice': agent.w3.eth.gas_price,
            'nonce': agent.w3.eth.get_transaction_count(agent.address)
        })
        
        print(f"✅ Transaction built")
        print(f"   Gas limit: {gas_limit:,}")
        print(f"   Gas price: {agent.w3.eth.gas_price / 1e9:.2f} gwei")
        
        # Sign and send transaction
        signed_txn = agent.w3.eth.account.sign_transaction(transaction, private_key)
        
        print("\n🚀 SENDING WETH DEBT SWAP TRANSACTION...")
        tx_hash = agent.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_hash_hex = tx_hash.hex()
        
        print(f"✅ TRANSACTION SENT: {tx_hash_hex}")
        
        # Wait for confirmation
        print("⏳ Waiting for confirmation...")
        receipt = agent.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        
        if receipt.status == 1:
            print("🎉 WETH DEBT SWAP SUCCESS!")
            print(f"   Gas used: {receipt.gasUsed:,}")
            print(f"   Block: {receipt.blockNumber}")
            return True
        else:
            print("❌ WETH DEBT SWAP FAILED - Transaction reverted")
            return False
            
    except Exception as e:
        print(f"❌ WETH debt swap test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_weth_debt_swap()
    if success:
        print("\n🎉 WETH DEBT SWAP TEST: PASSED")
    else:
        print("\n❌ WETH DEBT SWAP TEST: FAILED")