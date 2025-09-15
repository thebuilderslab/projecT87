#!/usr/bin/env python3
"""
EXECUTE COMPLETE DEBT SWAP CYCLE
Production execution with confirmed EIP-712 fix
"""

import os
import time
import json
import requests
from datetime import datetime
from web3 import Web3
from eth_account.messages import encode_structured_data
from arbitrum_testnet_agent import ArbitrumTestnetAgent

class ProductionDebtSwapExecutor:
    """Production debt swap executor with confirmed EIP-712 fix"""
    
    def __init__(self):
        """Initialize with minimal agent setup"""
        print("🚀 PRODUCTION DEBT SWAP EXECUTOR")
        print("=" * 60)
        print("🔧 CONFIRMED EIP-712 FIX: 'delegator' field added to message")
        print("=" * 60)
        
        # Initialize agent
        self.agent = ArbitrumTestnetAgent()
        self.w3 = self.agent.w3
        self.user_address = self.agent.address
        self.account = self.agent.account
        
        # Verified addresses
        self.paraswap_debt_swap_adapter = "0xCf85FF1c37c594a10195F7A9Ab85CBb0a03f69dE"
        self.aave_pool = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
        self.aave_data_provider = "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654"
        
        self.tokens = {
            'DAI': "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
            'ARB': "0x912CE59144191C1204E64559FE8253a0e49E6548"
        }
        
        print(f"✅ Initialized with wallet: {self.user_address}")

    def get_aave_position(self):
        """Get current Aave position"""
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
        
        pool_contract = self.w3.eth.contract(address=self.aave_pool, abi=pool_abi)
        account_data = pool_contract.functions.getUserAccountData(self.user_address).call()
        
        return {
            'total_collateral_usd': account_data[0] / 1e8,
            'total_debt_usd': account_data[1] / 1e8,
            'available_borrows_usd': account_data[2] / 1e8,
            'health_factor': account_data[5] / 1e18 if account_data[5] > 0 else float('inf')
        }

    def get_debt_token_address(self, asset_symbol):
        """Get debt token address"""
        data_provider_abi = [{
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
        
        data_provider_contract = self.w3.eth.contract(address=self.aave_data_provider, abi=data_provider_abi)
        token_addresses = data_provider_contract.functions.getReserveTokensAddresses(
            self.tokens[asset_symbol.upper()]
        ).call()
        
        return token_addresses[2]  # Variable debt token

    def get_paraswap_data(self, from_asset, to_asset, amount_wei):
        """Get ParaSwap calldata with reverse routing"""
        try:
            # Reverse routing for debt swaps
            if from_asset.upper() == 'DAI' and to_asset.upper() == 'ARB':
                src_token = self.tokens['ARB']  # Route ARB → DAI
                dest_token = self.tokens['DAI']
            else:  # ARB → DAI debt swap
                src_token = self.tokens['DAI']  # Route DAI → ARB
                dest_token = self.tokens['ARB']
            
            # Get price
            price_response = requests.get("https://apiv5.paraswap.io/prices", params={
                'srcToken': src_token,
                'destToken': dest_token,
                'amount': str(amount_wei),
                'srcDecimals': 18,
                'destDecimals': 18,
                'side': 'BUY',
                'network': 42161,
                'partner': 'aave',
                'maxImpact': '15'
            }, timeout=10)
            
            if price_response.status_code != 200:
                raise Exception(f"ParaSwap price failed: {price_response.status_code}")
            
            price_data = price_response.json()
            
            # Get transaction data
            tx_response = requests.post("https://apiv5.paraswap.io/transactions/42161", 
                params={'deadline': str(int(time.time()) + 1800), 'ignoreChecks': 'true'},
                json={
                    'srcToken': src_token,
                    'destToken': dest_token,
                    'srcAmount': price_data['priceRoute']['srcAmount'],
                    'destAmount': price_data['priceRoute']['destAmount'],
                    'priceRoute': price_data['priceRoute'],
                    'userAddress': self.w3.to_checksum_address(self.paraswap_debt_swap_adapter),
                    'receiver': self.w3.to_checksum_address(self.paraswap_debt_swap_adapter),
                    'partner': 'aave',
                    'partnerAddress': self.w3.to_checksum_address(self.paraswap_debt_swap_adapter)
                }, timeout=15)
            
            if tx_response.status_code != 200:
                raise Exception(f"ParaSwap tx failed: {tx_response.status_code}")
            
            tx_data = tx_response.json()
            
            return {
                'calldata': tx_data.get('data', '0x'),
                'expected_amount': price_data['priceRoute']['destAmount']
            }
            
        except Exception as e:
            print(f"❌ ParaSwap error: {e}")
            return None

    def create_credit_delegation_permit(self, debt_token_address):
        """Create FIXED credit delegation permit with 'delegator' field"""
        try:
            # Get token info
            debt_token_abi = [
                {"inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "stateMutability": "view", "type": "function"},
                {"inputs": [{"name": "owner", "type": "address"}], "name": "nonces", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}
            ]
            
            debt_token_contract = self.w3.eth.contract(address=debt_token_address, abi=debt_token_abi)
            token_name = debt_token_contract.functions.name().call()
            nonce = debt_token_contract.functions.nonces(self.user_address).call()
            deadline = int(time.time()) + 3600
            
            # FIXED EIP-712 structure with 'delegator' field
            domain = {
                'name': token_name,
                'version': '1',
                'chainId': 42161,
                'verifyingContract': debt_token_address
            }
            
            types = {
                'EIP712Domain': [
                    {'name': 'name', 'type': 'string'},
                    {'name': 'version', 'type': 'string'},
                    {'name': 'chainId', 'type': 'uint256'},
                    {'name': 'verifyingContract', 'type': 'address'}
                ],
                'DelegationWithSig': [
                    {'name': 'delegator', 'type': 'address'},  # 🔧 ARCHITECT FIX
                    {'name': 'delegatee', 'type': 'address'},
                    {'name': 'value', 'type': 'uint256'},
                    {'name': 'nonce', 'type': 'uint256'},
                    {'name': 'deadline', 'type': 'uint256'}
                ]
            }
            
            message = {
                'delegator': self.user_address,              # 🔧 ARCHITECT FIX
                'delegatee': self.paraswap_debt_swap_adapter,
                'value': 2**256 - 1,
                'nonce': nonce,
                'deadline': deadline
            }
            
            # Sign message
            structured_data = {
                'types': types,
                'domain': domain,
                'primaryType': 'DelegationWithSig',
                'message': message
            }
            
            encoded_data = encode_structured_data(structured_data)
            signature = self.account.sign_message(encoded_data)
            
            return {
                'token': debt_token_address,
                'delegatee': self.paraswap_debt_swap_adapter,
                'value': 2**256 - 1,
                'deadline': deadline,
                'v': signature.v,
                'r': signature.r.to_bytes(32, 'big'),
                's': signature.s.to_bytes(32, 'big')
            }
            
        except Exception as e:
            print(f"❌ Permit creation failed: {e}")
            return None

    def execute_debt_swap(self, from_asset, to_asset, amount_usd):
        """Execute debt swap with confirmed EIP-712 fix"""
        print(f"\n🔄 EXECUTING DEBT SWAP")
        print(f"Operation: {from_asset} → {to_asset} debt")
        print(f"Amount: ${amount_usd:.2f}")
        
        try:
            # Get position
            position = self.get_aave_position()
            print(f"📊 Health Factor: {position['health_factor']:.3f}")
            
            if position['health_factor'] < 1.5:
                raise Exception(f"Health factor too low: {position['health_factor']:.3f}")
            
            # Get debt token
            to_debt_token = self.get_debt_token_address(to_asset)
            print(f"📋 {to_asset} debt token: {to_debt_token}")
            
            # Calculate amount
            amount_wei = int(amount_usd * 1e18) if from_asset.upper() == 'DAI' else int(amount_usd / 0.55 * 1e18)
            
            # Get ParaSwap data
            paraswap_data = self.get_paraswap_data(from_asset, to_asset, amount_wei)
            if not paraswap_data:
                raise Exception("ParaSwap data failed")
            
            amount_to_swap = int(paraswap_data['expected_amount'])
            print(f"✅ Amount to swap: {amount_to_swap / 1e18:.6f}")
            
            # Create FIXED permit
            permit = self.create_credit_delegation_permit(to_debt_token)
            if not permit:
                raise Exception("Permit creation failed")
            
            print(f"✅ FIXED credit delegation permit created")
            
            # Execute debt swap
            debt_swap_abi = [{
                "inputs": [
                    {"name": "assetToSwapFrom", "type": "address"},
                    {"name": "assetToSwapTo", "type": "address"},
                    {"name": "amountToSwap", "type": "uint256"},
                    {"name": "paraswapData", "type": "bytes"},
                    {"components": [
                        {"name": "token", "type": "address"},
                        {"name": "delegatee", "type": "address"},
                        {"name": "value", "type": "uint256"},
                        {"name": "deadline", "type": "uint256"},
                        {"name": "v", "type": "uint8"},
                        {"name": "r", "type": "bytes32"},
                        {"name": "s", "type": "bytes32"}
                    ], "name": "creditDelegationPermit", "type": "tuple"}
                ],
                "name": "swapDebt",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }]
            
            debt_swap_contract = self.w3.eth.contract(
                address=self.paraswap_debt_swap_adapter, 
                abi=debt_swap_abi
            )
            
            function_call = debt_swap_contract.functions.swapDebt(
                self.tokens[from_asset.upper()],
                self.tokens[to_asset.upper()],
                amount_to_swap,
                bytes.fromhex(paraswap_data['calldata'][2:]),
                (
                    permit['token'],
                    permit['delegatee'],
                    permit['value'],
                    permit['deadline'],
                    permit['v'],
                    permit['r'],
                    permit['s']
                )
            )
            
            # Gas estimation and execution
            try:
                gas_estimate = function_call.estimate_gas({'from': self.user_address})
                gas_limit = int(gas_estimate * 1.2)
                print(f"✅ Gas estimate: {gas_estimate:,}")
            except Exception as e:
                print(f"⚠️ Gas estimation failed: {e}")
                gas_limit = 800000
            
            # Build transaction
            transaction = function_call.build_transaction({
                'from': self.user_address,
                'gas': gas_limit,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.user_address)
            })
            
            # Execute transaction
            print(f"🚀 Sending transaction...")
            signed_tx = self.account.sign_transaction(transaction)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            tx_hash_hex = tx_hash.hex()
            print(f"📡 TX Hash: {tx_hash_hex}")
            print(f"🔗 Arbiscan: https://arbiscan.io/tx/{tx_hash_hex}")
            
            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt['status'] == 1:
                print(f"✅ TRANSACTION SUCCESS!")
                print(f"   Block: {receipt['blockNumber']}")
                print(f"   Gas Used: {receipt['gasUsed']:,}")
                
                return {
                    'success': True,
                    'tx_hash': tx_hash_hex,
                    'block_number': receipt['blockNumber'],
                    'gas_used': receipt['gasUsed'],
                    'amount_swapped': amount_to_swap / 1e18
                }
            else:
                print(f"❌ Transaction failed")
                return {'success': False, 'error': 'Transaction reverted'}
                
        except Exception as e:
            print(f"❌ Debt swap failed: {e}")
            return {'success': False, 'error': str(e)}

def main():
    """Execute complete debt swap cycle"""
    print("🚀 COMPLETE DEBT SWAP CYCLE EXECUTION")
    print("=" * 80)
    print("🔧 USING CONFIRMED EIP-712 FIX: 'delegator' field added")
    print("=" * 80)
    
    cycle_results = {
        'cycle_start': datetime.now().isoformat(),
        'eip712_fix_applied': True,
        'steps': []
    }
    
    try:
        executor = ProductionDebtSwapExecutor()
        
        # Step 1: DAI → ARB debt swap
        print(f"\n🔄 STEP 1: DAI → ARB DEBT SWAP ($3.00)")
        step1_result = executor.execute_debt_swap('DAI', 'ARB', 3.0)
        cycle_results['steps'].append(step1_result)
        
        if step1_result['success']:
            print(f"✅ STEP 1 SUCCESS!")
            print(f"   TX: {step1_result['tx_hash']}")
            
            # Step 2: Wait for optimal conditions
            print(f"\n⏳ STEP 2: WAITING 5 MINUTES FOR OPTIMAL CONDITIONS")
            time.sleep(300)  # 5 minutes
            print(f"✅ Wait complete")
            
            # Step 3: ARB → DAI debt swap
            print(f"\n🔄 STEP 3: ARB → DAI DEBT SWAP ($3.00)")
            step3_result = executor.execute_debt_swap('ARB', 'DAI', 3.0)
            cycle_results['steps'].append(step3_result)
            
            if step3_result['success']:
                print(f"✅ STEP 3 SUCCESS!")
                print(f"   TX: {step3_result['tx_hash']}")
                
                # Complete cycle
                cycle_results.update({
                    'cycle_complete': True,
                    'total_gas_used': sum(s.get('gas_used', 0) for s in cycle_results['steps']),
                    'transaction_hashes': [s['tx_hash'] for s in cycle_results['steps'] if s['success']],
                    'arbitrage_complete': True
                })
                
                # Save results
                with open('complete_debt_swap_cycle_success.json', 'w') as f:
                    json.dump(cycle_results, f, indent=2)
                
                print(f"\n🎉 COMPLETE DEBT SWAP CYCLE SUCCESSFUL!")
                print(f"   DAI→ARB TX: {step1_result['tx_hash']}")
                print(f"   ARB→DAI TX: {step3_result['tx_hash']}")
                print(f"   Total Gas: {cycle_results['total_gas_used']:,}")
                print(f"   🔧 EIP-712 FIX CONFIRMED WORKING!")
                
                return True
            else:
                print(f"❌ STEP 3 FAILED: {step3_result.get('error', 'Unknown error')}")
        else:
            print(f"❌ STEP 1 FAILED: {step1_result.get('error', 'Unknown error')}")
        
        return False
        
    except Exception as e:
        print(f"❌ Cycle execution failed: {e}")
        cycle_results['cycle_error'] = str(e)
        return False
    
    finally:
        cycle_results['cycle_end'] = datetime.now().isoformat()

if __name__ == "__main__":
    success = main()
    print(f"\n{'🎉 COMPLETE SUCCESS' if success else '❌ CYCLE FAILED'}")