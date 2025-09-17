#!/usr/bin/env python3
"""
Execute Debt Swap Sequence - Real Transaction
Executes actual 5 DAI → ARB debt swap using corrected system
"""

import os
import sys
import time
import json
import requests
from typing import Dict
from web3 import Web3
from eth_account.messages import encode_structured_data

def execute_debt_swap_sequence():
    """Execute the complete debt swap sequence"""
    
    print("🚀 EXECUTING DEBT SWAP SEQUENCE")
    print("=" * 60)
    print("⚠️  REAL TRANSACTION EXECUTION")
    print("   This will execute an actual debt swap on Arbitrum mainnet")
    print("   5 DAI debt → ARB debt")
    print("=" * 60)
    
    try:
        # Import existing agent with loaded private key
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        # Set mainnet mode
        os.environ['NETWORK_MODE'] = 'mainnet'
        
        print("⏳ Initializing agent...")
        agent = ArbitrumTestnetAgent()
        
        print(f"✅ Agent ready:")
        print(f"   Address: {agent.address}")
        print(f"   Network: Arbitrum (Chain {agent.w3.eth.chain_id})")
        
        # Step 1: Verify current debt position
        print(f"\n📊 STEP 1: Verify Current Position")
        
        data_provider_abi = [{
            'inputs': [
                {'name': 'asset', 'type': 'address'}, 
                {'name': 'user', 'type': 'address'}
            ],
            'name': 'getUserReserveData',
            'outputs': [
                {'name': 'currentATokenBalance', 'type': 'uint256'},
                {'name': 'currentStableDebt', 'type': 'uint256'},
                {'name': 'currentVariableDebt', 'type': 'uint256'},
                {'name': 'principalStableDebt', 'type': 'uint256'},
                {'name': 'scaledVariableDebt', 'type': 'uint256'},
                {'name': 'stableBorrowRate', 'type': 'uint256'},
                {'name': 'liquidityRate', 'type': 'uint256'},
                {'name': 'stableRateLastUpdated', 'type': 'uint40'},
                {'name': 'usageAsCollateralEnabled', 'type': 'bool'}
            ],
            'stateMutability': 'view',
            'type': 'function'
        }]
        
        data_provider = agent.w3.eth.contract(
            address='0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654',
            abi=data_provider_abi
        )
        
        # Check DAI debt with corrected parameter order
        dai_data = data_provider.functions.getUserReserveData(
            '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1',  # DAI
            agent.address
        ).call()
        
        dai_variable_debt = dai_data[2] / 1e18
        print(f"   Current DAI Variable Debt: {dai_variable_debt:.6f}")
        
        if dai_variable_debt < 5.0:
            print(f"   ❌ Insufficient DAI debt for 5 DAI swap")
            return False
        
        print(f"   ✅ Sufficient DAI debt confirmed")
        
        # Step 2: Get ARB debt token address
        print(f"\n🔍 STEP 2: Get ARB Debt Token Address")
        
        reserve_tokens_abi = [{
            "inputs": [{"name": "asset", "type": "address"}],
            "name": "getReserveTokensAddresses",
            "outputs": [
                {"name": "aTokenAddress", "type": "address"},
                {"name": "stableDebtTokenAddress", "type": "address"},
                {"name": "variableDebtTokenAddress", "type": "address"}
            ],
            "stateMutability": "view",
            "type": "function"
        }]
        
        data_provider_tokens = agent.w3.eth.contract(
            address='0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654',
            abi=reserve_tokens_abi
        )
        
        # Get ARB debt token
        arb_tokens = data_provider_tokens.functions.getReserveTokensAddresses(
            '0x912CE59144191C1204E64559FE8253a0e49E6548'  # ARB
        ).call()
        
        arb_variable_debt_token = arb_tokens[2]
        print(f"   ARB Variable Debt Token: {arb_variable_debt_token}")
        
        # Step 3: Create credit delegation permit
        print(f"\n📝 STEP 3: Create Credit Delegation Permit")
        
        # EIP-712 domain for ARB variable debt token
        domain = {
            'name': 'Aave variable debt bearing ARB',
            'version': '1',
            'chainId': 42161,
            'verifyingContract': arb_variable_debt_token
        }
        
        deadline = int(time.time()) + 3600  # 1 hour
        delegation_amount = agent.w3.to_wei(20, 'ether')  # 20 ARB delegation
        
        # Get nonce from debt token (simplified - use 0)
        nonce = 0
        
        # EIP-712 message
        message = {
            'delegatee': '0xAE9f94BD98eC2831a1330e0418bE0fDb5C95C2B9',  # Debt swap adapter
            'value': delegation_amount,
            'nonce': nonce,
            'deadline': deadline
        }
        
        # EIP-712 types
        types = {
            'EIP712Domain': [
                {'name': 'name', 'type': 'string'},
                {'name': 'version', 'type': 'string'},
                {'name': 'chainId', 'type': 'uint256'},
                {'name': 'verifyingContract', 'type': 'address'}
            ],
            'DelegationWithSig': [
                {'name': 'delegatee', 'type': 'address'},
                {'name': 'value', 'type': 'uint256'},
                {'name': 'nonce', 'type': 'uint256'},
                {'name': 'deadline', 'type': 'uint256'}
            ]
        }
        
        # Create structured data
        structured_data = {
            'types': types,
            'primaryType': 'DelegationWithSig',
            'domain': domain,
            'message': message
        }
        
        # Sign the permit
        user_account = agent.w3.eth.account.from_key(agent.private_key)
        encoded = encode_structured_data(structured_data)
        signature = user_account.sign_message(encoded)
        
        print(f"   ✅ Credit delegation permit created")
        print(f"   Delegatee: {message['delegatee']}")
        print(f"   Amount: {delegation_amount / 1e18:.2f} ARB")
        
        # Step 4: Get ParaSwap calldata
        print(f"\n🔄 STEP 4: Get ParaSwap Swap Data")
        
        swap_amount_wei = agent.w3.to_wei(5, 'ether')  # 5 DAI
        
        # Price route (ARB → DAI for debt swap)
        price_params = {
            'srcToken': '0x912CE59144191C1204E64559FE8253a0e49E6548',  # ARB
            'destToken': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1',  # DAI
            'amount': str(swap_amount_wei),
            'srcDecimals': 18,
            'destDecimals': 18,
            'side': 'BUY',
            'network': 42161,
            'partner': 'aave',
            'maxImpact': '15'
        }
        
        print(f"   Getting ParaSwap price route...")
        price_response = requests.get(
            'https://apiv5.paraswap.io/prices',
            params=price_params,
            timeout=10
        )
        
        if price_response.status_code != 200:
            print(f"   ❌ ParaSwap price API failed: {price_response.status_code}")
            return False
        
        price_data = price_response.json()
        
        if 'priceRoute' not in price_data:
            print(f"   ❌ No price route found")
            return False
        
        arb_needed = int(price_data['priceRoute']['srcAmount']) / 1e18
        dai_out = int(price_data['priceRoute']['destAmount']) / 1e18
        
        print(f"   ✅ Price route obtained:")
        print(f"   ARB needed: {arb_needed:.6f}")
        print(f"   DAI output: {dai_out:.6f}")
        
        # Get transaction data
        tx_url = "https://apiv5.paraswap.io/transactions/42161"
        
        tx_payload = {
            'srcToken': '0x912CE59144191C1204E64559FE8253a0e49E6548',
            'destToken': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1',
            'srcAmount': price_data['priceRoute']['srcAmount'],
            'destAmount': price_data['priceRoute']['destAmount'],
            'priceRoute': price_data['priceRoute'],
            'userAddress': '0xAE9f94BD98eC2831a1330e0418bE0fDb5C95C2B9',  # Adapter
            'receiver': '0xAE9f94BD98eC2831a1330e0418bE0fDb5C95C2B9',    # Adapter
            'partner': 'aave'
        }
        
        tx_params = {
            'deadline': str(int(time.time()) + 1800),
            'ignoreChecks': 'true'
        }
        
        print(f"   Getting ParaSwap transaction data...")
        tx_response = requests.post(
            tx_url,
            params=tx_params,
            json=tx_payload,
            timeout=15,
            headers={'Content-Type': 'application/json'}
        )
        
        if tx_response.status_code != 200:
            print(f"   ❌ ParaSwap transaction API failed: {tx_response.status_code}")
            return False
        
        tx_data = tx_response.json()
        paraswap_calldata = tx_data.get('data', '0x')
        
        print(f"   ✅ ParaSwap transaction data obtained")
        print(f"   Calldata length: {len(paraswap_calldata)} chars")
        
        # Step 5: Execute debt swap transaction
        print(f"\n🚀 STEP 5: Execute Debt Swap Transaction")
        
        swap_debt_abi = [{
            "inputs": [
                {"name": "assetToSwapFrom", "type": "address"},
                {"name": "assetToSwapTo", "type": "address"},
                {"name": "amountToSwap", "type": "uint256"},
                {"name": "paraswapData", "type": "bytes"},
                {
                    "components": [
                        {"name": "token", "type": "address"},
                        {"name": "delegatee", "type": "address"},
                        {"name": "value", "type": "uint256"},
                        {"name": "deadline", "type": "uint256"},
                        {"name": "v", "type": "uint8"},
                        {"name": "r", "type": "bytes32"},
                        {"name": "s", "type": "bytes32"}
                    ],
                    "name": "creditDelegationPermit",
                    "type": "tuple"
                }
            ],
            "name": "swapDebt",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }]
        
        debt_swap_contract = agent.w3.eth.contract(
            address='0xAE9f94BD98eC2831a1330e0418bE0fDb5C95C2B9',
            abi=swap_debt_abi
        )
        
        # Build transaction
        print(f"   Building swapDebt transaction...")
        
        tx_params = debt_swap_contract.functions.swapDebt(
            '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1',  # assetToSwapFrom (DAI)
            '0x912CE59144191C1204E64559FE8253a0e49E6548',  # assetToSwapTo (ARB)
            swap_amount_wei,                               # amountToSwap (5 DAI)
            paraswap_calldata,                            # paraswapData
            (
                arb_variable_debt_token,                  # permit.token
                '0xAE9f94BD98eC2831a1330e0418bE0fDb5C95C2B9',  # permit.delegatee
                delegation_amount,                        # permit.value
                deadline,                                 # permit.deadline
                signature.v,                              # permit.v
                signature.r.to_bytes(32, 'big'),          # permit.r
                signature.s.to_bytes(32, 'big')           # permit.s
            )
        ).build_transaction({
            'from': agent.address,
            'gas': 1500000,  # High gas limit for complex transaction
            'gasPrice': agent.w3.to_wei(0.1, 'gwei'),
            'nonce': agent.w3.eth.get_transaction_count(agent.address)
        })
        
        print(f"   ✅ Transaction built successfully")
        print(f"   Gas limit: {tx_params['gas']:,}")
        print(f"   Gas price: {agent.w3.from_wei(tx_params['gasPrice'], 'gwei')} gwei")
        
        # Sign and send transaction
        print(f"\n💰 EXECUTING DEBT SWAP...")
        
        signed_tx = agent.w3.eth.account.sign_transaction(tx_params, agent.private_key)
        
        print(f"   Sending transaction to mempool...")
        tx_hash = agent.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        print(f"   ✅ Transaction sent!")
        print(f"   Hash: {tx_hash.hex()}")
        print(f"   https://arbiscan.io/tx/{tx_hash.hex()}")
        
        # Wait for confirmation
        print(f"\n⏳ Waiting for confirmation...")
        
        receipt = agent.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        
        if receipt.status == 1:
            print(f"   🎉 DEBT SWAP SUCCESSFUL!")
            print(f"   Block: {receipt.blockNumber}")
            print(f"   Gas used: {receipt.gasUsed:,}")
            
            # Verify new position
            print(f"\n📊 VERIFYING NEW POSITION...")
            
            # Check DAI debt after swap
            new_dai_data = data_provider.functions.getUserReserveData(
                '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1',
                agent.address
            ).call()
            
            new_dai_debt = new_dai_data[2] / 1e18
            
            # Check ARB debt after swap
            new_arb_data = data_provider.functions.getUserReserveData(
                '0x912CE59144191C1204E64559FE8253a0e49E6548',
                agent.address
            ).call()
            
            new_arb_debt = new_arb_data[2] / 1e18
            
            print(f"   New DAI debt: {new_dai_debt:.6f} (was {dai_variable_debt:.6f})")
            print(f"   New ARB debt: {new_arb_debt:.6f}")
            print(f"   DAI debt reduced by: {dai_variable_debt - new_dai_debt:.6f}")
            
            return True
            
        else:
            print(f"   ❌ Transaction failed!")
            print(f"   Receipt: {receipt}")
            return False
        
    except Exception as e:
        print(f"❌ Execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚨 EXECUTING DEBT SWAP SEQUENCE")
    print("=" * 60)
    print("Executing REAL debt swap transaction:")
    print("• Convert 5 DAI debt → ARB debt") 
    print("• Uses ~10 ARB to repay 5 DAI")
    print("• Real transaction with gas costs")
    print("=" * 60)
    
    success = execute_debt_swap_sequence()
    
    if success:
        print(f"\n🎉 DEBT SWAP EXECUTION: SUCCESS!")
        print(f"Your debt position has been successfully modified!")
    else:
        print(f"\n❌ DEBT SWAP EXECUTION: FAILED")
        print(f"Check logs for details")