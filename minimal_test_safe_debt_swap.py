#!/usr/bin/env python3
"""
MINIMAL TEST SAFE DEBT SWAP EXECUTOR
Enhanced implementation with safety improvements for $0.50 test execution
"""

import os
import time
import json
import requests
from datetime import datetime
from typing import Dict, Optional, Tuple
from web3 import Web3
from web3.exceptions import ContractLogicError
from eth_account.messages import encode_structured_data
from decimal import Decimal

class MinimalTestSafeDebtSwapExecutor:
    """Safe debt swap executor with bounded delegation and revocation features"""
    
    def __init__(self):
        print("🔒 MINIMAL TEST SAFE DEBT SWAP EXECUTOR")
        print("=" * 60)
        print("🛡️  ENHANCED WITH SAFETY IMPROVEMENTS:")
        print("   ✅ Bounded delegation (swap amount + buffer)")
        print("   ✅ Automatic delegation revocation after test")
        print("   ✅ Preflight validation with eth_call")
        print("   ✅ Comprehensive error handling")
        print("=" * 60)
        
        # Initialize Web3 connection
        self.private_key = os.getenv('PRIVATE_KEY')
        if not self.private_key:
            raise Exception("PRIVATE_KEY not found in environment")
        
        # Try multiple RPC endpoints for reliability
        self.rpc_urls = [
            "https://arbitrum-one.public.blastapi.io",
            "https://arb1.arbitrum.io/rpc",
            "https://arbitrum-mainnet.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161"
        ]
        
        self.w3 = None
        self._connect_to_arbitrum()
        
        self.account = self.w3.eth.account.from_key(self.private_key)
        self.user_address = self.account.address
        
        # Contract addresses
        self.paraswap_debt_swap_adapter = "0xAE9f94BD98eC2831a1330e0418bE0fDb5C95C2B9"
        self.aave_pool = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
        self.aave_data_provider = "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654"
        
        # Token addresses
        self.tokens = {
            'DAI': "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
            'ARB': "0x912CE59144191C1204E64559FE8253a0e49E6548"
        }
        
        # VERIFIED debt token addresses and parameters from mainnet verification
        self.verified_debt_tokens = {
            'DAI': {
                'debt_token_address': "0x8619d80FB0141ba7F184CbF22fd724116D9f7ffC",
                'eip712_domain': {
                    'name': "Aave Arbitrum Variable Debt DAI",
                    'version': "1",
                    'chainId': 42161,
                    'verifyingContract': "0x8619d80FB0141ba7F184CbF22fd724116D9f7ffC"
                },
                'nonce_method': 'nonces'
            },
            'ARB': {
                'debt_token_address': "0x44705f578135cC5d703b4c9c122528C73Eb87145",
                'eip712_domain': {
                    'name': "Aave Arbitrum Variable Debt ARB",
                    'version': "1",
                    'chainId': 42161,
                    'verifyingContract': "0x44705f578135cC5d703b4c9c122528C73Eb87145"
                },
                'nonce_method': 'nonces'
            }
        }
        
        # VERIFIED EIP-712 types from mainnet contract verification
        self.eip712_types = {
            'EIP712Domain': [
                {'name': 'name', 'type': 'string'},
                {'name': 'version', 'type': 'string'},
                {'name': 'chainId', 'type': 'uint256'},
                {'name': 'verifyingContract', 'type': 'address'}
            ],
            # CRITICAL FIX: NO "delegator" field - verified from contract typehash
            'DelegationWithSig': [
                {'name': 'delegatee', 'type': 'address'},
                {'name': 'value', 'type': 'uint256'},
                {'name': 'nonce', 'type': 'uint256'},
                {'name': 'deadline', 'type': 'uint256'}
            ]
        }
        
        # Debt swap adapter ABI
        self.debt_swap_abi = [{
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
        
        # Credit delegation ABI for revocation
        self.credit_delegation_abi = [{
            "inputs": [
                {"name": "delegatee", "type": "address"},
                {"name": "amount", "type": "uint256"}
            ],
            "name": "approveDelegation",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }]
        
        print(f"✅ Initialized with wallet: {self.user_address}")
        print(f"   Chain ID: {self.w3.eth.chain_id}")
        print(f"   Block: {self.w3.eth.block_number}")
        print(f"   Connected via: {self.w3.provider.endpoint_uri}")
        print()
    
    def _connect_to_arbitrum(self):
        """Connect to Arbitrum with fallback RPCs"""
        for rpc_url in self.rpc_urls:
            try:
                w3 = Web3(Web3.HTTPProvider(rpc_url))
                if w3.is_connected() and w3.eth.chain_id == 42161:
                    self.w3 = w3
                    print(f"✅ Connected to Arbitrum via {rpc_url}")
                    return
            except Exception as e:
                print(f"⚠️ Failed to connect to {rpc_url}: {e}")
                continue
        
        raise Exception("Failed to connect to Arbitrum mainnet")
    
    def calculate_bounded_delegation(self, swap_amount: int, buffer_percent: float = 5.0) -> int:
        """Calculate bounded delegation amount with safety buffer"""
        buffer = int(swap_amount * (buffer_percent / 100))
        bounded_amount = swap_amount + buffer
        
        print(f"🧮 BOUNDED DELEGATION CALCULATION:")
        print(f"   Swap Amount: {swap_amount / 1e18:.6f} tokens")
        print(f"   Buffer ({buffer_percent}%): {buffer / 1e18:.6f} tokens")
        print(f"   Total Delegation: {bounded_amount / 1e18:.6f} tokens")
        
        return bounded_amount
    
    def create_safe_credit_delegation_permit(self, asset_symbol: str, swap_amount: int) -> Dict:
        """Create safe credit delegation permit with bounded delegation"""
        print(f"🔐 CREATING SAFE CREDIT DELEGATION PERMIT FOR {asset_symbol}")
        print("=" * 60)
        
        # Get verified parameters
        if asset_symbol.upper() not in self.verified_debt_tokens:
            raise ValueError(f"No verified parameters for {asset_symbol}")
        
        debt_token_info = self.verified_debt_tokens[asset_symbol.upper()]
        debt_token_address = debt_token_info['debt_token_address']
        domain = debt_token_info['eip712_domain']
        
        # Calculate bounded delegation amount
        bounded_amount = self.calculate_bounded_delegation(swap_amount)
        
        print(f"📋 Using verified parameters:")
        print(f"   Debt token: {debt_token_address}")
        print(f"   Domain name: '{domain['name']}'")
        print(f"   Domain version: '{domain['version']}'")
        print(f"   Chain ID: {domain['chainId']}")
        print()
        
        try:
            # Get current nonce using verified method
            nonce_method = debt_token_info['nonce_method']
            debt_token_abi = [{
                "inputs": [{"name": "owner", "type": "address"}],
                "name": nonce_method,
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }]
            
            debt_token_contract = self.w3.eth.contract(address=debt_token_address, abi=debt_token_abi)
            current_nonce = getattr(debt_token_contract.functions, nonce_method)(self.user_address).call()
            
            print(f"🔢 Current nonce ({nonce_method}): {current_nonce}")
            
            # Create EIP-712 message with VERIFIED structure and bounded delegation
            deadline = int(time.time()) + 3600  # 1 hour
            
            message = {
                'delegatee': self.paraswap_debt_swap_adapter,
                'value': bounded_amount,  # SAFE: Bounded delegation instead of unlimited
                'nonce': current_nonce,
                'deadline': deadline
            }
            
            print(f"📝 EIP-712 Message (SAFE BOUNDED):")
            print(f"   delegatee: {message['delegatee']}")
            print(f"   value: {message['value']} ({message['value'] / 1e18:.6f} tokens)")
            print(f"   nonce: {message['nonce']}")
            print(f"   deadline: {message['deadline']}")
            print()
            
            # Create EIP-712 structured data
            structured_data = {
                'types': self.eip712_types,
                'primaryType': 'DelegationWithSig',
                'domain': domain,
                'message': message
            }
            
            print(f"🏗️  EIP-712 Structured Data:")
            print(f"   Primary Type: DelegationWithSig")
            print(f"   Domain: {domain}")
            print()
            
            # Sign the message
            encoded_data = encode_structured_data(structured_data)
            signature = self.account.sign_message(encoded_data)
            
            print(f"✍️  EIP-712 Signature Generated:")
            print(f"   v: {signature.v}")
            print(f"   r: {hex(signature.r)}")
            print(f"   s: {hex(signature.s)}")
            print()
            
            # Return permit data with properly formatted signature
            permit_data = {
                'token': debt_token_address,
                'delegatee': self.paraswap_debt_swap_adapter,
                'value': message['value'],
                'deadline': deadline,
                'v': signature.v,
                'r': signature.r.to_bytes(32, byteorder='big'),  # Convert to bytes32
                's': signature.s.to_bytes(32, byteorder='big'),  # Convert to bytes32
                'swap_amount': swap_amount,
                'bounded_amount': bounded_amount
            }
            
            print(f"✅ Safe credit delegation permit created successfully!")
            return permit_data
            
        except Exception as e:
            print(f"❌ Error creating safe credit delegation permit: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def get_paraswap_calldata(self, from_asset: str, to_asset: str, amount: int) -> Dict:
        """Get ParaSwap calldata with reverse routing for debt swaps"""
        print(f"🌐 GETTING PARASWAP DATA: {from_asset} → {to_asset}")
        print("=" * 50)
        
        try:
            # For debt swaps: DAI→ARB debt requires ARB→DAI routing
            if from_asset.upper() == 'DAI' and to_asset.upper() == 'ARB':
                src_token = self.tokens['ARB']
                dest_token = self.tokens['DAI']
                print(f"🔄 REVERSE ROUTING: ARB → DAI (for DAI debt → ARB debt)")
            elif from_asset.upper() == 'ARB' and to_asset.upper() == 'DAI':
                src_token = self.tokens['DAI']
                dest_token = self.tokens['ARB']
                print(f"🔄 REVERSE ROUTING: DAI → ARB (for ARB debt → DAI debt)")
            else:
                raise ValueError(f"Unsupported swap: {from_asset} → {to_asset}")
            
            # Get price quote from ParaSwap
            price_url = "https://apiv5.paraswap.io/prices"
            price_params = {
                'srcToken': src_token,
                'destToken': dest_token,
                'amount': str(amount),
                'srcDecimals': 18,
                'destDecimals': 18,
                'side': 'BUY',
                'network': 42161,
                'partner': 'aave',
                'maxImpact': '15'
            }
            
            print(f"📊 Requesting price quote...")
            price_response = requests.get(price_url, params=price_params, timeout=10)
            
            if price_response.status_code != 200:
                error_text = price_response.text
                raise Exception(f"ParaSwap price API failed: {price_response.status_code} - {error_text}")
            
            price_data = price_response.json()
            
            if 'priceRoute' not in price_data:
                raise Exception("No price route found")
            
            print(f"✅ Price route obtained")
            print(f"   Source amount needed: {price_data['priceRoute']['srcAmount']}")
            print(f"   Destination amount: {price_data['priceRoute']['destAmount']}")
            
            # Get transaction data
            tx_url = "https://apiv5.paraswap.io/transactions/42161"
            tx_params = {
                'deadline': str(int(time.time()) + 1800),
                'ignoreChecks': 'true'
            }
            
            tx_payload = {
                'srcToken': src_token,
                'destToken': dest_token,
                'srcAmount': price_data['priceRoute']['srcAmount'],
                'destAmount': price_data['priceRoute']['destAmount'],
                'priceRoute': price_data['priceRoute'],
                'userAddress': self.w3.to_checksum_address(self.paraswap_debt_swap_adapter),
                'receiver': self.w3.to_checksum_address(self.paraswap_debt_swap_adapter),
                'partner': 'aave',
                'partnerAddress': self.w3.to_checksum_address(self.paraswap_debt_swap_adapter),
                'partnerFeeBps': '0',
                'takeSurplus': False
            }
            
            print(f"🔨 Requesting transaction data...")
            tx_response = requests.post(tx_url, params=tx_params, json=tx_payload, timeout=15)
            
            if tx_response.status_code != 200:
                error_text = tx_response.text
                raise Exception(f"ParaSwap transaction API failed: {tx_response.status_code} - {error_text}")
            
            tx_data = tx_response.json()
            
            if 'data' not in tx_data:
                raise Exception("No transaction data returned")
            
            print(f"✅ Transaction data obtained")
            print(f"   Data length: {len(tx_data['data'])} characters")
            
            return {
                'calldata': tx_data['data'],
                'price_route': price_data['priceRoute'],
                'src_amount': price_data['priceRoute']['srcAmount'],
                'dest_amount': price_data['priceRoute']['destAmount']
            }
            
        except Exception as e:
            print(f"❌ Error getting ParaSwap data: {e}")
            return {}
    
    def preflight_validation(self, debt_swap_adapter, asset_from: str, asset_to: str, amount: int, 
                           paraswap_data: Dict, permit_data: Dict) -> bool:
        """Validate transaction with eth_call before sending"""
        print(f"🔍 PREFLIGHT VALIDATION")
        print("=" * 40)
        
        try:
            # Build transaction for eth_call
            tx_data = debt_swap_adapter.functions.swapDebt(
                asset_from,    # assetToSwapFrom
                asset_to,      # assetToSwapTo
                amount,        # amountToSwap
                paraswap_data['calldata'],  # paraswapData
                (              # creditDelegationPermit
                    permit_data['token'],
                    permit_data['delegatee'],
                    permit_data['value'],
                    permit_data['deadline'],
                    permit_data['v'],
                    permit_data['r'],
                    permit_data['s']
                )
            )
            
            # Perform eth_call
            print("🧪 Testing with eth_call...")
            tx_data.call({'from': self.user_address})
            
            print("✅ Preflight validation passed!")
            return True
            
        except ContractLogicError as e:
            print(f"❌ Preflight validation failed - Contract Error: {e}")
            if "0x8baa579f" in str(e):
                print("   💀 SIGNATURE VALIDATION ERROR (0x8baa579f)")
                print("   🔧 This indicates EIP-712 signature issues")
            return False
            
        except Exception as e:
            print(f"❌ Preflight validation failed - General Error: {e}")
            return False
    
    def revoke_delegation(self, asset_symbol: str) -> bool:
        """Revoke credit delegation for security"""
        print(f"🔒 REVOKING DELEGATION FOR {asset_symbol}")
        print("=" * 50)
        
        try:
            debt_token_info = self.verified_debt_tokens[asset_symbol.upper()]
            debt_token_address = debt_token_info['debt_token_address']
            
            # Create contract instance
            debt_token_contract = self.w3.eth.contract(
                address=debt_token_address,
                abi=self.credit_delegation_abi
            )
            
            # Build revocation transaction
            revoke_tx = debt_token_contract.functions.approveDelegation(
                self.paraswap_debt_swap_adapter,
                0  # Set delegation to 0
            ).build_transaction({
                'from': self.user_address,
                'gas': 100000,
                'gasPrice': self.w3.to_wei('0.1', 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(self.user_address)
            })
            
            # Sign and send revocation
            signed_revoke_tx = self.account.sign_transaction(revoke_tx)
            revoke_hash = self.w3.eth.send_raw_transaction(signed_revoke_tx.rawTransaction)
            
            print(f"📡 Revocation transaction sent: {revoke_hash.hex()}")
            
            # Wait for confirmation
            revoke_receipt = self.w3.eth.wait_for_transaction_receipt(revoke_hash, timeout=120)
            
            if revoke_receipt['status'] == 1:
                print(f"✅ DELEGATION REVOKED SUCCESSFULLY!")
                print(f"   Block: {revoke_receipt['blockNumber']}")
                return True
            else:
                print(f"❌ Delegation revocation failed")
                return False
                
        except Exception as e:
            print(f"⚠️ Error revoking delegation: {e}")
            return False
    
    def execute_minimal_test_swap(self) -> Optional[str]:
        """Execute minimal $0.50 DAI debt → ARB debt swap with safety features"""
        print(f"\n🚀 EXECUTING MINIMAL TEST SWAP")
        print("=" * 60)
        
        # Test parameters
        from_asset = 'DAI'
        to_asset = 'ARB'
        test_amount = int(0.5 * 1e18)  # $0.50 worth
        
        print(f"🔄 SWAP: {from_asset} debt → {to_asset} debt")
        print(f"💰 AMOUNT: {test_amount / 1e18:.6f} tokens ($0.50)")
        print("=" * 60)
        
        permit_data = None
        
        try:
            # Step 1: Create safe bounded credit delegation permit
            permit_data = self.create_safe_credit_delegation_permit(from_asset, test_amount)
            if not permit_data:
                raise Exception("Failed to create safe credit delegation permit")
            
            # Step 2: Get ParaSwap calldata
            paraswap_data = self.get_paraswap_calldata(from_asset, to_asset, test_amount)
            if not paraswap_data:
                raise Exception("Failed to get ParaSwap data")
            
            # Step 3: Prepare transaction
            debt_swap_adapter = self.w3.eth.contract(
                address=self.paraswap_debt_swap_adapter,
                abi=self.debt_swap_abi
            )
            
            asset_from = self.tokens[from_asset.upper()]
            asset_to = self.tokens[to_asset.upper()]
            
            print(f"🔨 PREPARING TRANSACTION:")
            print(f"   From Asset: {asset_from}")
            print(f"   To Asset: {asset_to}")
            print(f"   Amount: {test_amount}")
            print(f"   ParaSwap Data: {len(paraswap_data['calldata'])} bytes")
            print(f"   Permit Token: {permit_data['token']}")
            print(f"   Permit Delegatee: {permit_data['delegatee']}")
            print(f"   Permit Value: {permit_data['value']} ({permit_data['value'] / 1e18:.6f} tokens)")
            print()
            
            # Step 4: Preflight validation
            if not self.preflight_validation(debt_swap_adapter, asset_from, asset_to, 
                                           test_amount, paraswap_data, permit_data):
                raise Exception("Preflight validation failed - signature or contract error")
            
            # Step 5: Build and send transaction
            tx = debt_swap_adapter.functions.swapDebt(
                asset_from,    # assetToSwapFrom
                asset_to,      # assetToSwapTo
                test_amount,   # amountToSwap
                paraswap_data['calldata'],  # paraswapData
                (              # creditDelegationPermit
                    permit_data['token'],
                    permit_data['delegatee'],
                    permit_data['value'],
                    permit_data['deadline'],
                    permit_data['v'],
                    permit_data['r'],
                    permit_data['s']
                )
            ).build_transaction({
                'from': self.user_address,
                'gas': 500000,
                'gasPrice': self.w3.to_wei('0.1', 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(self.user_address)
            })
            
            print(f"📋 TRANSACTION BUILT:")
            print(f"   Gas: {tx['gas']}")
            print(f"   Gas Price: {tx['gasPrice']} wei ({self.w3.from_wei(tx['gasPrice'], 'gwei')} gwei)")
            print(f"   Nonce: {tx['nonce']}")
            
            # Sign and send transaction
            signed_tx = self.account.sign_transaction(tx)
            
            print(f"\n📡 SENDING TRANSACTION...")
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            
            print(f"✅ TRANSACTION SENT!")
            print(f"   Hash: {tx_hash_hex}")
            print(f"   Explorer: https://arbiscan.io/tx/{tx_hash_hex}")
            
            # Wait for confirmation
            print(f"\n⏳ Waiting for confirmation...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt['status'] == 1:
                print(f"✅ DEBT SWAP TEST SUCCESSFUL!")
                print(f"   Block: {receipt['blockNumber']}")
                print(f"   Gas Used: {receipt['gasUsed']}")
                
                # Step 6: Post-test cleanup - revoke delegation
                print(f"\n🔒 POST-TEST CLEANUP:")
                self.revoke_delegation(from_asset)
                
                return tx_hash_hex
            else:
                print(f"❌ TRANSACTION FAILED!")
                print(f"   Receipt: {receipt}")
                return None
                
        except Exception as e:
            print(f"❌ DEBT SWAP EXECUTION FAILED: {e}")
            import traceback
            traceback.print_exc()
            
            # Attempt delegation cleanup even on failure
            if permit_data:
                print(f"\n🔒 CLEANUP ON FAILURE:")
                try:
                    self.revoke_delegation(from_asset)
                except:
                    print(f"⚠️ Could not revoke delegation - manual cleanup may be required")
            
            return None
    
    def generate_test_report(self, tx_hash: Optional[str]):
        """Generate comprehensive test report"""
        print(f"\n📊 MINIMAL TEST EXECUTION REPORT")
        print("=" * 60)
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        if tx_hash:
            print(f"✅ TEST STATUS: SUCCESS")
            print(f"🎯 OBJECTIVE: Execute $0.50 DAI debt → ARB debt swap")
            print(f"📅 EXECUTED: {current_time}")
            print(f"🔗 TRANSACTION: {tx_hash}")
            print(f"🌐 EXPLORER: https://arbiscan.io/tx/{tx_hash}")
            print()
            
            print(f"🛡️  SAFETY FEATURES APPLIED:")
            print(f"   ✅ Bounded delegation (swap amount + 5% buffer)")
            print(f"   ✅ Preflight validation with eth_call")
            print(f"   ✅ EIP-712 signature structure corrected (no delegator)")
            print(f"   ✅ Verified domain parameters from mainnet contracts")
            print(f"   ✅ Post-test delegation revocation")
            print()
            
            print(f"🎉 CONCLUSION:")
            print(f"   The verified EIP-712 implementation works correctly!")
            print(f"   Signature validation error (0x8baa579f) has been resolved.")
            print(f"   Safe debt swap execution confirmed on Arbitrum mainnet.")
            
        else:
            print(f"❌ TEST STATUS: FAILED")
            print(f"🎯 OBJECTIVE: Execute $0.50 DAI debt → ARB debt swap")
            print(f"📅 ATTEMPTED: {current_time}")
            print()
            
            print(f"💔 FAILURE ANALYSIS:")
            print(f"   The transaction failed to execute successfully.")
            print(f"   Check the logs above for specific error details.")
            print(f"   Common issues: insufficient balance, signature validation, gas issues")
            print()
            
            print(f"🔧 NEXT STEPS:")
            print(f"   1. Review error logs for specific failure reason")
            print(f"   2. Verify wallet has sufficient DAI debt position")
            print(f"   3. Check ParaSwap API availability")
            print(f"   4. Validate EIP-712 signature parameters")

def main():
    """Main execution function for minimal test"""
    try:
        print("🎯 STARTING MINIMAL TEST EXECUTION")
        print("=" * 60)
        
        # Initialize executor
        executor = MinimalTestSafeDebtSwapExecutor()
        
        # Execute minimal test
        tx_hash = executor.execute_minimal_test_swap()
        
        # Generate report
        executor.generate_test_report(tx_hash)
        
        return tx_hash
        
    except Exception as e:
        print(f"💥 MINIMAL TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()