#!/usr/bin/env python3
"""
Corrected Debt Swap Execution
Using the proper ParaSwapDebtSwapAdapter contract with correct ABI
"""

import os
import sys
import requests
from web3 import Web3

def execute_corrected_debt_swap():
    """Execute debt swap using the correct ParaSwapDebtSwapAdapter contract"""
    
    print("🔧 CORRECTED DEBT SWAP EXECUTION")
    print("=" * 60)
    print("Using proper ParaSwapDebtSwapAdapter contract with correct ABI")
    print("=" * 60)
    
    try:
        # Import agent
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        os.environ['NETWORK_MODE'] = 'mainnet'
        
        print("⏳ Initializing agent...")
        agent = ArbitrumTestnetAgent()
        
        print(f"✅ Agent ready: {agent.address}")
        
        # Step 1: Verify current DAI debt
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
        
        dai_data = data_provider.functions.getUserReserveData(
            '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1',  # DAI
            agent.address
        ).call()
        
        dai_debt = dai_data[2] / 1e18
        print(f"   Current DAI debt: {dai_debt:.6f}")
        
        if dai_debt < 1.0:
            print(f"   ❌ Insufficient DAI debt for swap")
            return False
        
        # Step 2: Get ParaSwap route for debt swap
        print(f"\n🔄 STEP 2: Get ParaSwap Route")
        
        # Swap 5 DAI debt for ARB debt
        swap_amount = 5.0
        swap_amount_wei = agent.w3.to_wei(swap_amount, 'ether')
        
        # For debt swap, we need exactOut swap (specific amount of DAI out)
        price_params = {
            'srcToken': '0x912CE59144191C1204E64559FE8253a0e49E6548',  # ARB (what we'll owe)
            'destToken': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1',  # DAI (what we'll repay)
            'amount': str(swap_amount_wei),  # Exact amount of DAI to receive
            'srcDecimals': 18,
            'destDecimals': 18,
            'side': 'BUY',  # BUY means exact destToken amount
            'network': 42161,
            'slippage': '300'  # 3%
        }
        
        price_response = requests.get(
            'https://apiv5.paraswap.io/prices',
            params=price_params,
            timeout=10
        )
        
        if price_response.status_code != 200:
            print(f"   ❌ ParaSwap price failed: {price_response.text}")
            return False
        
        price_data = price_response.json()
        
        src_amount = int(price_data['priceRoute']['srcAmount'])
        arb_needed = src_amount / 1e18
        
        print(f"   ✅ Route: Need {arb_needed:.6f} ARB to repay {swap_amount} DAI")
        
        # Get ParaSwap transaction calldata for the debt swap adapter
        priceRoute = price_data['priceRoute']
        
        transaction_params = {
            'priceRoute': priceRoute,
            'srcToken': priceRoute['srcToken'],
            'destToken': priceRoute['destToken'],
            'srcAmount': priceRoute['srcAmount'],
            'destAmount': priceRoute['destAmount'],
            'userAddress': '0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4',  # Debt swap adapter
            'partner': 'aave',
            'ignoreChecks': True  # Bypass balance validation for flash loan flow
        }
        
        transaction_response = requests.post(
            'https://apiv5.paraswap.io/transactions/42161',
            json=transaction_params,
            timeout=10
        )
        
        if transaction_response.status_code != 200:
            print(f"   ❌ ParaSwap transaction failed: {transaction_response.text}")
            return False
        
        transaction_data = transaction_response.json()
        paraswap_data = transaction_data['data']  # Raw calldata bytes
        
        print(f"   ✅ ParaSwap calldata obtained for debt swap adapter")
        
        # Step 3: Create correct swapDebt transaction
        print(f"\n🚀 STEP 3: Execute Debt Swap")
        
        # Correct ParaSwapDebtSwapAdapter ABI
        debt_swap_abi = [{
            "inputs": [
                {
                    "components": [
                        {"name": "debtAsset", "type": "address"},
                        {"name": "debtRepayAmount", "type": "uint256"},
                        {"name": "debtRateMode", "type": "uint256"},
                        {"name": "newDebtAsset", "type": "address"},
                        {"name": "maxNewDebtAmount", "type": "uint256"},
                        {"name": "extraCollateralAsset", "type": "address"},
                        {"name": "extraCollateralAmount", "type": "uint256"},
                        {"name": "paraswapData", "type": "bytes"}
                    ],
                    "name": "debtSwapParams",
                    "type": "tuple"
                },
                {
                    "components": [
                        {"name": "debtToken", "type": "address"},
                        {"name": "value", "type": "uint256"},
                        {"name": "deadline", "type": "uint256"},
                        {"name": "v", "type": "uint8"},
                        {"name": "r", "type": "bytes32"},
                        {"name": "s", "type": "bytes32"}
                    ],
                    "name": "creditDelegationPermit",
                    "type": "tuple"
                },
                {
                    "components": [
                        {"name": "aToken", "type": "address"},
                        {"name": "value", "type": "uint256"},
                        {"name": "deadline", "type": "uint256"},
                        {"name": "v", "type": "uint8"},
                        {"name": "r", "type": "bytes32"},
                        {"name": "s", "type": "bytes32"}
                    ],
                    "name": "collateralATokenPermit",
                    "type": "tuple"
                }
            ],
            "name": "swapDebt",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }]
        
        # Correct contract address for ParaSwapDebtSwapAdapter
        debt_swap_adapter = agent.w3.eth.contract(
            address='0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4',
            abi=debt_swap_abi
        )
        
        # Create DebtSwapParams
        debt_swap_params = (
            '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1',  # debtAsset (DAI)
            swap_amount_wei,                                 # debtRepayAmount (5 DAI)
            2,                                               # debtRateMode (2 = variable)
            '0x912CE59144191C1204E64559FE8253a0e49E6548',  # newDebtAsset (ARB)
            src_amount + int(src_amount * 0.05),             # maxNewDebtAmount (5% slippage)
            '0x0000000000000000000000000000000000000000',  # extraCollateralAsset (none)
            0,                                               # extraCollateralAmount (0)
            paraswap_data                                    # paraswapData
        )
        
        # Empty credit delegation permit (assume pre-approved)
        credit_delegation_permit = (
            '0x0000000000000000000000000000000000000000',  # debtToken
            0,                                               # value
            0,                                               # deadline
            0,                                               # v
            b'\x00' * 32,                                    # r
            b'\x00' * 32                                     # s
        )
        
        # Empty collateral permit
        collateral_permit = (
            '0x0000000000000000000000000000000000000000',  # aToken
            0,                                               # value
            0,                                               # deadline
            0,                                               # v
            b'\x00' * 32,                                    # r
            b'\x00' * 32                                     # s
        )
        
        # Build transaction
        print(f"   Building swapDebt transaction...")
        
        function_call = debt_swap_adapter.functions.swapDebt(
            debt_swap_params,
            credit_delegation_permit,
            collateral_permit
        )
        
        # Get current gas price
        gas_price = agent.w3.eth.gas_price
        
        # Build transaction
        transaction = function_call.build_transaction({
            'from': agent.address,
            'gas': 2000000,  # Conservative gas limit
            'gasPrice': gas_price,
            'nonce': agent.w3.eth.get_transaction_count(agent.address)
        })
        
        print(f"   Transaction built:")
        print(f"      To: {transaction['to']}")
        print(f"      Gas: {transaction['gas']:,}")
        print(f"      Gas Price: {transaction['gasPrice'] / 1e9:.2f} gwei")
        
        # Sign and send transaction
        print(f"   Signing transaction...")
        signed_txn = agent.w3.eth.account.sign_transaction(transaction, agent.private_key)
        
        print(f"   Sending transaction...")
        txn_hash = agent.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        txn_hash_hex = txn_hash.hex()
        
        print(f"   ✅ Transaction sent: {txn_hash_hex}")
        print(f"   🔗 Arbiscan: https://arbiscan.io/tx/{txn_hash_hex}")
        
        # Wait for confirmation
        print(f"   ⏳ Waiting for confirmation...")
        receipt = agent.w3.eth.wait_for_transaction_receipt(txn_hash, timeout=300)
        
        if receipt['status'] == 1:
            print(f"   ✅ Transaction successful!")
            print(f"      Block: {receipt['blockNumber']}")
            print(f"      Gas used: {receipt['gasUsed']:,}")
            
            # Verify the debt swap
            print(f"\n📊 VERIFICATION: Checking new debt positions")
            
            # Check DAI debt (should be reduced)
            new_dai_data = data_provider.functions.getUserReserveData(
                '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1',  # DAI
                agent.address
            ).call()
            
            new_dai_debt = new_dai_data[2] / 1e18
            
            # Check ARB debt (should be new)
            arb_data = data_provider.functions.getUserReserveData(
                '0x912CE59144191C1204E64559FE8253a0e49E6548',  # ARB
                agent.address
            ).call()
            
            arb_debt = arb_data[2] / 1e18
            
            print(f"   New DAI debt: {new_dai_debt:.6f} (was {dai_debt:.6f})")
            print(f"   New ARB debt: {arb_debt:.6f}")
            print(f"   Debt swap amount: {dai_debt - new_dai_debt:.6f} DAI")
            
            return True
            
        else:
            print(f"   ❌ Transaction failed!")
            print(f"      Receipt: {receipt}")
            return False
        
    except Exception as e:
        print(f"❌ Execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = execute_corrected_debt_swap()
    
    if success:
        print(f"\n✅ DEBT SWAP SUCCESSFUL!")
        print(f"Successfully swapped DAI debt for ARB debt using correct adapter")
    else:
        print(f"\n❌ DEBT SWAP FAILED!")
        print(f"Check the error details above")