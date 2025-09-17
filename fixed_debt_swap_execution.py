#!/usr/bin/env python3
"""
Fixed Debt Swap Execution - Corrected ABI and Credit Delegation
Uses proper ParaSwapDebtSwapAdapter interface and credit delegation
"""

import os
import sys
import time
import requests
from web3 import Web3
from eth_account.messages import encode_typed_data

def execute_fixed_debt_swap():
    """Execute debt swap with corrected ABI and credit delegation"""
    
    print("🔧 FIXED DEBT SWAP EXECUTION")
    print("=" * 60)
    print("Using corrected contract ABI and credit delegation")
    print("=" * 60)
    
    try:
        # Import existing agent
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        os.environ['NETWORK_MODE'] = 'mainnet'
        
        print("⏳ Initializing agent...")
        agent = ArbitrumTestnetAgent()
        
        print(f"✅ Agent ready: {agent.address}")
        
        # Step 1: Check current position
        print(f"\n📊 STEP 1: Current Position Check")
        
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
        
        # Get current DAI debt
        dai_data = data_provider.functions.getUserReserveData(
            '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1',  # DAI
            agent.address
        ).call()
        
        dai_debt = dai_data[2] / 1e18
        print(f"   Current DAI debt: {dai_debt:.6f}")
        
        if dai_debt < 5.0:
            print(f"   ❌ Insufficient DAI debt")
            return False
        
        # Step 2: Get ARB debt token and read actual nonce
        print(f"\n🔍 STEP 2: Get ARB Debt Token and Nonce")
        
        # Get ARB debt token address
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
        
        arb_tokens = data_provider_tokens.functions.getReserveTokensAddresses(
            '0x912CE59144191C1204E64559FE8253a0e49E6548'  # ARB
        ).call()
        
        arb_debt_token = arb_tokens[2]
        print(f"   ARB debt token: {arb_debt_token}")
        
        # Get current nonce from debt token
        nonce_abi = [{
            "inputs": [{"name": "owner", "type": "address"}],
            "name": "nonces",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }]
        
        debt_token_contract = agent.w3.eth.contract(
            address=arb_debt_token,
            abi=nonce_abi
        )
        
        current_nonce = debt_token_contract.functions.nonces(agent.address).call()
        print(f"   Current nonce: {current_nonce}")
        
        # Step 3: Create PROPER credit delegation permit
        print(f"\n📝 STEP 3: Create Proper Credit Delegation Permit")
        
        # Correct EIP-712 domain for ARB variable debt token
        domain = {
            'name': 'Aave Variable Debt ARB',  # Simplified standard name
            'version': '1',
            'chainId': 42161,
            'verifyingContract': arb_debt_token
        }
        
        deadline = int(time.time()) + 3600
        delegation_amount = agent.w3.to_wei(20, 'ether')
        
        message = {
            'delegatee': '0xAE9f94BD98eC2831a1330e0418bE0fDb5C95C2B9',
            'value': delegation_amount,
            'nonce': current_nonce,
            'deadline': deadline
        }
        
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
        
        structured_data = {
            'types': types,
            'primaryType': 'DelegationWithSig',
            'domain': domain,
            'message': message
        }
        
        user_account = agent.w3.eth.account.from_key(agent.private_key)
        encoded = encode_typed_data(structured_data)
        signature = user_account.sign_message(encoded)
        
        print(f"   ✅ Permit created with nonce {current_nonce}")
        
        # Step 4: Get ParaSwap data with correct parameters
        print(f"\n🔄 STEP 4: Get ParaSwap Data")
        
        swap_amount_wei = agent.w3.to_wei(5, 'ether')
        
        # Price route
        price_params = {
            'srcToken': '0x912CE59144191C1204E64559FE8253a0e49E6548',  # ARB
            'destToken': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1',  # DAI
            'amount': str(swap_amount_wei),
            'srcDecimals': 18,
            'destDecimals': 18,
            'side': 'BUY',
            'network': 42161,
            'partner': 'aave',
            'slippage': '300'  # 3% slippage
        }
        
        price_response = requests.get(
            'https://apiv5.paraswap.io/prices',
            params=price_params,
            timeout=10
        )
        
        if price_response.status_code != 200:
            print(f"   ❌ ParaSwap price failed")
            return False
        
        price_data = price_response.json()
        
        # Transaction data
        tx_payload = {
            'srcToken': '0x912CE59144191C1204E64559FE8253a0e49E6548',
            'destToken': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1',
            'srcAmount': price_data['priceRoute']['srcAmount'],
            'slippage': '300',
            'priceRoute': price_data['priceRoute'],
            'userAddress': '0xAE9f94BD98eC2831a1330e0418bE0fDb5C95C2B9',
            'receiver': '0xAE9f94BD98eC2831a1330e0418bE0fDb5C95C2B9',
            'partner': 'aave'
        }
        
        tx_response = requests.post(
            'https://apiv5.paraswap.io/transactions/42161',
            json=tx_payload,
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        
        if tx_response.status_code != 200:
            print(f"   ❌ ParaSwap transaction failed")
            return False
        
        tx_data = tx_response.json()
        calldata = tx_data.get('data', '0x')
        
        print(f"   ✅ ParaSwap data obtained")
        print(f"   To address: {tx_data.get('to', 'N/A')}")
        
        # Step 5: Use CORRECTED swapDebt ABI with all required parameters
        print(f"\n🚀 STEP 5: Execute with Corrected ABI")
        
        # CORRECTED ABI based on actual ParaSwapDebtSwapAdapter contract
        corrected_swap_debt_abi = [{
            "inputs": [
                {"name": "assetToSwapFrom", "type": "address"},
                {"name": "assetToSwapTo", "type": "address"},
                {"name": "amountToSwap", "type": "uint256"},
                {"name": "minAmountToReceive", "type": "uint256"},
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
            abi=corrected_swap_debt_abi
        )
        
        # Calculate minimum amount (95% of expected)
        expected_dai = int(price_data['priceRoute']['destAmount'])
        min_amount = int(expected_dai * 0.95)  # 5% slippage
        
        print(f"   Expected DAI: {expected_dai / 1e18:.6f}")
        print(f"   Min amount: {min_amount / 1e18:.6f}")
        
        # Build transaction with CORRECTED parameters
        tx_params = debt_swap_contract.functions.swapDebt(
            '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1',  # assetToSwapFrom (DAI)
            '0x912CE59144191C1204E64559FE8253a0e49E6548',  # assetToSwapTo (ARB)
            swap_amount_wei,                               # amountToSwap (5 DAI)
            min_amount,                                    # minAmountToReceive
            calldata,                                      # paraswapData
            (
                arb_debt_token,                            # permit.token
                '0xAE9f94BD98eC2831a1330e0418bE0fDb5C95C2B9',  # permit.delegatee
                delegation_amount,                         # permit.value
                deadline,                                  # permit.deadline
                signature.v,                               # permit.v
                signature.r.to_bytes(32, 'big'),           # permit.r
                signature.s.to_bytes(32, 'big')            # permit.s
            )
        ).build_transaction({
            'from': agent.address,
            'gas': 2000000,  # Higher gas limit
            'gasPrice': agent.w3.to_wei(0.2, 'gwei'),
            'nonce': agent.w3.eth.get_transaction_count(agent.address)
        })
        
        print(f"   ✅ Transaction built with corrected ABI")
        print(f"   Gas: {tx_params['gas']:,}")
        
        # Execute transaction
        print(f"\n💰 EXECUTING FIXED DEBT SWAP...")
        
        signed_tx = agent.w3.eth.account.sign_transaction(tx_params, agent.private_key)
        tx_hash = agent.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        print(f"   Transaction sent: {tx_hash.hex()}")
        print(f"   https://arbiscan.io/tx/{tx_hash.hex()}")
        
        # Wait for confirmation
        print(f"\n⏳ Waiting for confirmation...")
        receipt = agent.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        
        if receipt.status == 1:
            print(f"   🎉 DEBT SWAP SUCCESSFUL!")
            print(f"   Block: {receipt.blockNumber}")
            print(f"   Gas used: {receipt.gasUsed:,}")
            
            # Verify new position
            new_dai_data = data_provider.functions.getUserReserveData(
                '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1',
                agent.address
            ).call()
            
            new_dai_debt = new_dai_data[2] / 1e18
            
            print(f"   📊 Position after swap:")
            print(f"   DAI debt: {new_dai_debt:.6f} (was {dai_debt:.6f})")
            print(f"   Reduction: {dai_debt - new_dai_debt:.6f} DAI")
            
            return True
        else:
            print(f"   ❌ Transaction failed!")
            print(f"   Gas used: {receipt.gasUsed:,}")
            return False
            
    except Exception as e:
        print(f"❌ Execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🔧 EXECUTING FIXED DEBT SWAP")
    print("Using corrected contract ABI and proper credit delegation")
    print("=" * 60)
    
    success = execute_fixed_debt_swap()
    
    if success:
        print(f"\n🎉 FIXED DEBT SWAP: SUCCESS!")
        print(f"Debt swap executed successfully with corrected implementation!")
    else:
        print(f"\n❌ FIXED DEBT SWAP: FAILED")
        print(f"Check transaction details for debugging")