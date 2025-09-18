#!/usr/bin/env python3
"""
Atomic Mainnet Swap Workflow with Aave Integration
Executes: Borrow 10 DAI → Swap DAI→ARB → Wait 5min → Swap ARB→DAI → Repay DAI
"""

import time
import sys
import os
import json
from decimal import Decimal
from web3 import Web3

# Add current directory to path
sys.path.append('.')

from arbitrum_testnet_agent import ArbitrumTestnetAgent

class AaveAtomicSwapWorkflow:
    def __init__(self):
        """Initialize the atomic swap workflow with Aave integration"""
        print("🚀 Initializing Aave Atomic Swap Workflow on Arbitrum Mainnet")
        # Force mainnet mode
        os.environ['NETWORK_MODE'] = 'mainnet'
        self.agent = ArbitrumTestnetAgent()
        
        # Wait for full initialization
        if not self.agent.initialize_integrations():
            raise Exception("Failed to initialize DeFi integrations")
            
        # Uniswap V3 Router on Arbitrum
        self.uniswap_router = "0xE592427A0AEce92De3Edee1F18E0157C05861564"
        
        # Token addresses on Arbitrum
        self.dai_address = "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1"
        self.arb_address = "0x912CE59144191C1204E64559FE8253a0e49E6548"
        
        # Swap amount
        self.borrow_amount = 10.0  # 10 DAI to borrow and swap
        self.swap_amount_dai = Web3.to_wei(self.borrow_amount, 'ether')
        
        # Results storage
        self.results = {
            'initial_health_factor': 0,
            'initial_balances': {},
            'borrow_details': {},
            'swap1_details': {},
            'wait_period': 300,  # 5 minutes
            'swap2_details': {},
            'repay_details': {},
            'final_balances': {},
            'final_health_factor': 0,
            'transaction_hashes': []
        }
        
        print(f"✅ Agent initialized with wallet: {self.agent.address}")
        print(f"📊 Connected to Chain ID: {self.agent.w3.eth.chain_id}")
        
    def get_current_balances(self):
        """Get current token balances"""
        # Use the agent's built-in balance methods
        eth_balance = self.agent.get_eth_balance()
        
        # Get DAI balance directly from contract
        dai_balance = self.get_token_balance(self.dai_address)
        
        # Get ARB balance directly from contract  
        arb_balance = self.get_token_balance(self.arb_address)
        
        return {
            'DAI': dai_balance,
            'ARB': arb_balance,
            'ETH': eth_balance
        }
    
    def get_token_balance(self, token_address):
        """Get token balance from contract"""
        try:
            token_contract = self.agent.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=[{
                    "inputs": [{"name": "account", "type": "address"}],
                    "name": "balanceOf", 
                    "outputs": [{"name": "", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                }]
            )
            balance_wei = token_contract.functions.balanceOf(self.agent.address).call()
            return Web3.from_wei(balance_wei, 'ether')
        except Exception as e:
            print(f"Error getting token balance: {e}")
            return 0.0
    
    def get_health_factor(self):
        """Get current health factor from Aave"""
        try:
            health_data = self.agent.health_monitor.get_current_health_factor()
            if health_data:
                return health_data.get('health_factor', 0)
            return 0
        except Exception as e:
            print(f"Error getting health factor: {e}")
            return 0
    
    def borrow_dai_from_aave(self, amount):
        """Borrow DAI from Aave"""
        print(f"💰 Borrowing {amount} DAI from Aave")
        
        try:
            # Use the agent's Aave integration to borrow
            if hasattr(self.agent, 'aave_integration'):
                result = self.agent.aave_integration.borrow_dai(amount)
                if result and 'transaction_hash' in result:
                    print(f"✅ Borrowed {amount} DAI successfully")
                    return result['transaction_hash'], True
                else:
                    print(f"❌ Failed to borrow DAI: {result}")
                    return None, False
            else:
                print("❌ Aave integration not available")
                return None, False
        except Exception as e:
            print(f"❌ Error borrowing DAI: {e}")
            return None, False
    
    def approve_token(self, token_address, spender, amount):
        """Approve token spending"""
        print(f"📝 Approving {Web3.from_wei(amount, 'ether'):.6f} tokens for {spender}")
        
        # ERC20 approve function
        erc20_abi = [
            {
                "inputs": [
                    {"name": "spender", "type": "address"},
                    {"name": "amount", "type": "uint256"}
                ],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            }
        ]
        
        try:
            contract = self.agent.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=erc20_abi
            )
            
            # Build transaction
            txn = contract.functions.approve(
                Web3.to_checksum_address(spender),
                amount
            ).build_transaction({
                'from': self.agent.address,
                'gas': 100000,
                'gasPrice': self.agent.w3.eth.gas_price,
                'nonce': self.agent.w3.eth.get_transaction_count(self.agent.address)
            })
            
            # Sign and send
            signed_txn = self.agent.w3.eth.account.sign_transaction(txn, self.agent.private_key)
            tx_hash = self.agent.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for confirmation
            receipt = self.agent.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            print(f"✅ Approval confirmed: {tx_hash.hex()}")
            return tx_hash.hex(), receipt
        except Exception as e:
            print(f"❌ Error approving token: {e}")
            return None, None
    
    def execute_uniswap_swap(self, token_in, token_out, amount_in, minimum_amount_out=0):
        """Execute swap via Uniswap V3"""
        print(f"🔄 Executing swap: {Web3.from_wei(amount_in, 'ether'):.6f} {token_in} -> {token_out}")
        
        # Uniswap V3 Router ABI (exactInputSingle)
        router_abi = [
            {
                "inputs": [
                    {
                        "components": [
                            {"name": "tokenIn", "type": "address"},
                            {"name": "tokenOut", "type": "address"},
                            {"name": "fee", "type": "uint24"},
                            {"name": "recipient", "type": "address"},
                            {"name": "deadline", "type": "uint256"},
                            {"name": "amountIn", "type": "uint256"},
                            {"name": "amountOutMinimum", "type": "uint256"},
                            {"name": "sqrtPriceLimitX96", "type": "uint160"}
                        ],
                        "name": "params",
                        "type": "tuple"
                    }
                ],
                "name": "exactInputSingle",
                "outputs": [{"name": "amountOut", "type": "uint256"}],
                "type": "function"
            }
        ]
        
        try:
            router_contract = self.agent.w3.eth.contract(
                address=Web3.to_checksum_address(self.uniswap_router),
                abi=router_abi
            )
            
            # Get token addresses
            token_in_addr = self.dai_address if token_in == 'DAI' else self.arb_address
            token_out_addr = self.arb_address if token_out == 'ARB' else self.dai_address
            
            # Swap parameters
            deadline = int(time.time()) + 300  # 5 minutes
            params = {
                'tokenIn': Web3.to_checksum_address(token_in_addr),
                'tokenOut': Web3.to_checksum_address(token_out_addr),
                'fee': 3000,  # 0.3% fee tier
                'recipient': self.agent.address,
                'deadline': deadline,
                'amountIn': amount_in,
                'amountOutMinimum': minimum_amount_out,
                'sqrtPriceLimitX96': 0
            }
            
            # Build transaction
            txn = router_contract.functions.exactInputSingle(params).build_transaction({
                'from': self.agent.address,
                'gas': 300000,
                'gasPrice': self.agent.w3.eth.gas_price,
                'nonce': self.agent.w3.eth.get_transaction_count(self.agent.address)
            })
            
            # Sign and send
            signed_txn = self.agent.w3.eth.account.sign_transaction(txn, self.agent.private_key)
            tx_hash = self.agent.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for confirmation
            receipt = self.agent.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            print(f"✅ Swap completed: {tx_hash.hex()}")
            print(f"📊 Gas used: {receipt['gasUsed']:,}")
            print(f"📊 Status: {'Success' if receipt['status'] == 1 else 'Failed'}")
            
            return tx_hash.hex(), receipt
        except Exception as e:
            print(f"❌ Error executing swap: {e}")
            return None, None
    
    def repay_dai_to_aave(self, amount):
        """Repay DAI to Aave"""
        print(f"💰 Repaying {amount:.6f} DAI to Aave")
        
        try:
            # Use the agent's Aave integration to repay
            if hasattr(self.agent, 'aave_integration'):
                result = self.agent.aave_integration.repay_dai(amount)
                if result and 'transaction_hash' in result:
                    print(f"✅ Repaid {amount:.6f} DAI successfully")
                    return result['transaction_hash'], True
                else:
                    print(f"❌ Failed to repay DAI: {result}")
                    return None, False
            else:
                print("❌ Aave integration not available")
                return None, False
        except Exception as e:
            print(f"❌ Error repaying DAI: {e}")
            return None, False
    
    def run_workflow(self):
        """Execute the complete atomic swap workflow"""
        print("=" * 60)
        print("🚀 STARTING AAVE ATOMIC MAINNET SWAP WORKFLOW")
        print("=" * 60)
        
        try:
            # Step 1: Get initial status
            print("\n📊 Step 1: Recording initial status")
            self.results['initial_balances'] = self.get_current_balances()
            self.results['initial_health_factor'] = self.get_health_factor()
            
            print(f"Initial DAI: {self.results['initial_balances']['DAI']:.6f}")
            print(f"Initial ARB: {self.results['initial_balances']['ARB']:.6f}")
            print(f"Initial ETH: {self.results['initial_balances']['ETH']:.6f}")
            print(f"Initial Health Factor: {self.results['initial_health_factor']:.4f}")
            
            # Step 2: Borrow DAI from Aave
            print(f"\n💰 Step 2: Borrowing {self.borrow_amount} DAI from Aave")
            borrow_hash, borrow_success = self.borrow_dai_from_aave(self.borrow_amount)
            
            if not borrow_success:
                raise Exception("Failed to borrow DAI from Aave")
            
            self.results['borrow_details'] = {
                'transaction_hash': borrow_hash,
                'amount': self.borrow_amount
            }
            if borrow_hash:
                self.results['transaction_hashes'].append(borrow_hash)
            
            # Verify DAI balance after borrowing
            updated_balances = self.get_current_balances()
            dai_available = updated_balances['DAI']
            print(f"✅ DAI balance after borrowing: {dai_available:.6f}")
            
            if dai_available < self.borrow_amount:
                print(f"⚠️ Warning: Expected {self.borrow_amount} DAI, got {dai_available:.6f}")
            
            # Step 3: Approve DAI for Uniswap
            print("\n📝 Step 3: Approving DAI for Uniswap Router")
            approve_hash, approve_receipt = self.approve_token(
                self.dai_address, 
                self.uniswap_router, 
                self.swap_amount_dai
            )
            if approve_hash:
                self.results['transaction_hashes'].append(approve_hash)
            
            # Step 4: Execute DAI -> ARB swap
            print("\n🔄 Step 4: Executing DAI -> ARB swap")
            swap1_hash, swap1_receipt = self.execute_uniswap_swap(
                'DAI', 'ARB', self.swap_amount_dai
            )
            
            if not swap1_hash:
                raise Exception("Failed to execute DAI -> ARB swap")
            
            # Get balances after first swap
            balances_after_swap1 = self.get_current_balances()
            arb_received = balances_after_swap1['ARB'] - self.results['initial_balances']['ARB']
            
            self.results['swap1_details'] = {
                'transaction_hash': swap1_hash,
                'gas_used': swap1_receipt['gasUsed'] if swap1_receipt else 0,
                'status': 'success' if swap1_receipt and swap1_receipt['status'] == 1 else 'failed',
                'input_token': 'DAI',
                'output_token': 'ARB',
                'input_amount': self.borrow_amount,
                'output_amount': arb_received
            }
            self.results['transaction_hashes'].append(swap1_hash)
            
            print(f"✅ Received {arb_received:.6f} ARB")
            
            # Step 5: Wait 5 minutes
            print(f"\n⏰ Step 5: Waiting {self.results['wait_period']} seconds (5 minutes)")
            for i in range(self.results['wait_period'], 0, -30):
                print(f"⏳ {i} seconds remaining...")
                time.sleep(30)
            print("✅ Wait period completed")
            
            # Step 6: Get ARB balance and approve for swap back
            current_arb_balance = self.get_current_balances()['ARB']
            arb_amount_to_swap = Web3.to_wei(current_arb_balance, 'ether')
            
            print(f"\n📝 Step 6: Approving {current_arb_balance:.6f} ARB for swap back")
            approve2_hash, approve2_receipt = self.approve_token(
                self.arb_address, 
                self.uniswap_router, 
                arb_amount_to_swap
            )
            if approve2_hash:
                self.results['transaction_hashes'].append(approve2_hash)
            
            # Step 7: Execute ARB -> DAI swap
            print(f"\n🔄 Step 7: Executing ARB -> DAI swap")
            swap2_hash, swap2_receipt = self.execute_uniswap_swap(
                'ARB', 'DAI', arb_amount_to_swap
            )
            
            if not swap2_hash:
                raise Exception("Failed to execute ARB -> DAI swap")
            
            # Get balances after second swap
            balances_after_swap2 = self.get_current_balances()
            dai_received = balances_after_swap2['DAI'] - balances_after_swap1['DAI']
            
            self.results['swap2_details'] = {
                'transaction_hash': swap2_hash,
                'gas_used': swap2_receipt['gasUsed'] if swap2_receipt else 0,
                'status': 'success' if swap2_receipt and swap2_receipt['status'] == 1 else 'failed',
                'input_token': 'ARB',
                'output_token': 'DAI',
                'input_amount': current_arb_balance,
                'output_amount': dai_received
            }
            self.results['transaction_hashes'].append(swap2_hash)
            
            print(f"✅ Received {dai_received:.6f} DAI back")
            
            # Step 8: Repay DAI to Aave (optional based on amount received)
            final_dai_balance = balances_after_swap2['DAI']
            if final_dai_balance >= self.borrow_amount:
                print(f"\n💰 Step 8: Repaying {self.borrow_amount} DAI to Aave")
                repay_hash, repay_success = self.repay_dai_to_aave(self.borrow_amount)
                
                self.results['repay_details'] = {
                    'transaction_hash': repay_hash,
                    'amount': self.borrow_amount,
                    'success': repay_success
                }
                if repay_hash:
                    self.results['transaction_hashes'].append(repay_hash)
            else:
                print(f"\n⚠️ Step 8: Insufficient DAI to repay full amount")
                print(f"Available: {final_dai_balance:.6f}, Needed: {self.borrow_amount}")
                self.results['repay_details'] = {
                    'transaction_hash': None,
                    'amount': 0,
                    'success': False,
                    'reason': 'insufficient_balance'
                }
            
            # Step 9: Get final status
            print("\n📊 Step 9: Recording final status")
            self.results['final_balances'] = self.get_current_balances()
            self.results['final_health_factor'] = self.get_health_factor()
            
            print("\n" + "=" * 60)
            print("🎉 AAVE ATOMIC SWAP WORKFLOW COMPLETED")
            print("=" * 60)
            
            return self.results
            
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def print_final_report(self):
        """Print comprehensive final report"""
        print("\n📋 FINAL EXECUTION REPORT")
        print("=" * 60)
        
        # Source address
        print(f"🏠 Source Address: {self.agent.address}")
        
        # Swap protocol
        print(f"🔄 Swap Protocol: Uniswap V3 Router + Aave")
        print(f"📍 Router Address: {self.uniswap_router}")
        
        # Borrow details
        if 'borrow_details' in self.results:
            print(f"\n💰 AAVE BORROW:")
            print(f"   Amount: {self.results['borrow_details']['amount']:.6f} DAI")
            print(f"   Hash: {self.results['borrow_details'].get('transaction_hash', 'N/A')}")
        
        # Swap 1 details
        if 'swap1_details' in self.results:
            print(f"\n🔄 SWAP 1: DAI -> ARB")
            print(f"   Input: {self.results['swap1_details']['input_amount']:.6f} DAI")
            print(f"   Output: {self.results['swap1_details']['output_amount']:.6f} ARB")
            print(f"   Hash: {self.results['swap1_details']['transaction_hash']}")
            print(f"   Status: {self.results['swap1_details']['status']}")
            print(f"   Gas: {self.results['swap1_details']['gas_used']:,}")
        
        # Wait period
        print(f"\n⏰ WAIT PERIOD: {self.results['wait_period']} seconds")
        
        # Swap 2 details
        if 'swap2_details' in self.results:
            print(f"\n🔄 SWAP 2: ARB -> DAI")
            print(f"   Input: {self.results['swap2_details']['input_amount']:.6f} ARB")
            print(f"   Output: {self.results['swap2_details']['output_amount']:.6f} DAI")
            print(f"   Hash: {self.results['swap2_details']['transaction_hash']}")
            print(f"   Status: {self.results['swap2_details']['status']}")
            print(f"   Gas: {self.results['swap2_details']['gas_used']:,}")
        
        # Repay details
        if 'repay_details' in self.results:
            print(f"\n💰 AAVE REPAY:")
            repay = self.results['repay_details']
            if repay['success']:
                print(f"   Amount: {repay['amount']:.6f} DAI")
                print(f"   Hash: {repay['transaction_hash']}")
                print(f"   Status: Success")
            else:
                print(f"   Status: Failed ({repay.get('reason', 'unknown')})")
        
        # All transaction hashes
        print(f"\n📋 ALL TRANSACTION HASHES:")
        for i, tx_hash in enumerate(self.results['transaction_hashes'], 1):
            print(f"   {i}. {tx_hash}")
        
        # Health factor comparison
        print(f"\n❤️ HEALTH FACTOR:")
        print(f"   Initial: {self.results['initial_health_factor']:.4f}")
        print(f"   Final:   {self.results['final_health_factor']:.4f}")
        print(f"   Change:  {self.results['final_health_factor'] - self.results['initial_health_factor']:+.4f}")
        
        # Balance comparison
        print(f"\n💰 BALANCE COMPARISON:")
        for token in ['DAI', 'ARB', 'ETH']:
            initial = self.results['initial_balances'][token]
            final = self.results['final_balances'][token]
            change = final - initial
            print(f"   {token}: {initial:.6f} → {final:.6f} ({change:+.6f})")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    try:
        # Initialize and run workflow
        workflow = AaveAtomicSwapWorkflow()
        results = workflow.run_workflow()
        
        if results:
            # Print final report
            workflow.print_final_report()
            
            # Save results to file
            with open('aave_atomic_swap_results.json', 'w') as f:
                # Convert Decimal objects to float for JSON serialization
                json_results = json.loads(json.dumps(results, default=float))
                json.dump(json_results, f, indent=2)
            
            print(f"\n💾 Results saved to: aave_atomic_swap_results.json")
        else:
            print("\n❌ Workflow failed to complete")
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)