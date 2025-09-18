#!/usr/bin/env python3
"""
Atomic Mainnet Swap Workflow
Executes: DAI -> ARB -> DAI with 5-minute wait between swaps
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

class AtomicSwapWorkflow:
    def __init__(self):
        """Initialize the atomic swap workflow"""
        print("🚀 Initializing Atomic Swap Workflow on Arbitrum Mainnet")
        # Force mainnet mode
        os.environ['NETWORK_MODE'] = 'mainnet'
        self.agent = ArbitrumTestnetAgent()
        
        # Uniswap V3 Router on Arbitrum
        self.uniswap_router = "0xE592427A0AEce92De3Edee1F18E0157C05861564"
        
        # Token addresses on Arbitrum
        self.dai_address = "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1"
        self.arb_address = "0x912CE59144191C1204E64559FE8253a0e49E6548"
        
        # Swap amount
        self.swap_amount_dai = Web3.to_wei(10, 'ether')  # 10 DAI
        
        # Results storage
        self.results = {
            'initial_balances': {},
            'swap1_details': {},
            'wait_period': 300,  # 5 minutes
            'swap2_details': {},
            'final_balances': {},
            'transaction_hashes': []
        }
        
    def get_current_balances(self):
        """Get current token balances"""
        # Use the agent's built-in balance methods
        eth_balance = self.agent.get_eth_balance()
        
        # Get DAI balance directly from contract
        dai_balance = self.get_dai_balance_from_contract()
        
        # Get ARB balance directly from contract  
        arb_balance = self.get_arb_balance_from_contract()
        
        return {
            'DAI': dai_balance,
            'ARB': arb_balance,
            'ETH': eth_balance
        }
    
    def get_dai_balance_from_contract(self):
        """Get DAI balance from contract"""
        try:
            dai_contract = self.agent.w3.eth.contract(
                address=Web3.to_checksum_address(self.dai_address),
                abi=[{
                    "inputs": [{"name": "account", "type": "address"}],
                    "name": "balanceOf", 
                    "outputs": [{"name": "", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                }]
            )
            balance_wei = dai_contract.functions.balanceOf(self.agent.address).call()
            return Web3.from_wei(balance_wei, 'ether')
        except Exception as e:
            print(f"Error getting DAI balance: {e}")
            return 0.0
    
    def get_arb_balance_from_contract(self):
        """Get ARB balance from contract"""
        try:
            arb_contract = self.agent.w3.eth.contract(
                address=Web3.to_checksum_address(self.arb_address),
                abi=[{
                    "inputs": [{"name": "account", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "", "type": "uint256"}],
                    "stateMutability": "view", 
                    "type": "function"
                }]
            )
            balance_wei = arb_contract.functions.balanceOf(self.agent.address).call()
            return Web3.from_wei(balance_wei, 'ether')
        except Exception as e:
            print(f"Error getting ARB balance: {e}")
            return 0.0
    
    def approve_token(self, token_address, spender, amount):
        """Approve token spending"""
        print(f"📝 Approving {amount} tokens for {spender}")
        
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
    
    def execute_uniswap_swap(self, token_in, token_out, amount_in, minimum_amount_out=0):
        """Execute swap via Uniswap V3"""
        print(f"🔄 Executing swap: {amount_in} {token_in} -> {token_out}")
        
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
    
    def decode_swap_events(self, receipt):
        """Decode swap events from transaction receipt"""
        events = []
        for log in receipt['logs']:
            try:
                # Try to decode Transfer events
                if len(log['topics']) >= 3:
                    topics = [t.hex() for t in log['topics']]
                    # Transfer event signature
                    if topics[0] == '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef':
                        from_addr = '0x' + topics[1][-40:]
                        to_addr = '0x' + topics[2][-40:]
                        amount = int(log['data'], 16)
                        
                        events.append({
                            'type': 'Transfer',
                            'token': log['address'],
                            'from': from_addr,
                            'to': to_addr,
                            'amount': amount
                        })
            except:
                continue
        
        return events
    
    def run_workflow(self):
        """Execute the complete atomic swap workflow"""
        print("=" * 60)
        print("🚀 STARTING ATOMIC MAINNET SWAP WORKFLOW")
        print("=" * 60)
        
        # Step 1: Get initial balances
        print("\n📊 Step 1: Recording initial balances")
        self.results['initial_balances'] = self.get_current_balances()
        print(f"Initial DAI: {self.results['initial_balances']['DAI']:.6f}")
        print(f"Initial ARB: {self.results['initial_balances']['ARB']:.6f}")
        print(f"Initial ETH: {self.results['initial_balances']['ETH']:.6f}")
        
        # Verify sufficient DAI balance
        if self.results['initial_balances']['DAI'] < 10:
            raise ValueError(f"Insufficient DAI balance: {self.results['initial_balances']['DAI']:.6f} < 10.0")
        
        # Step 2: Approve DAI for Uniswap
        print("\n📝 Step 2: Approving DAI for Uniswap Router")
        approve_hash, approve_receipt = self.approve_token(
            self.dai_address, 
            self.uniswap_router, 
            self.swap_amount_dai
        )
        self.results['transaction_hashes'].append(approve_hash)
        
        # Step 3: Execute DAI -> ARB swap
        print("\n🔄 Step 3: Executing DAI -> ARB swap")
        swap1_hash, swap1_receipt = self.execute_uniswap_swap(
            'DAI', 'ARB', self.swap_amount_dai
        )
        
        # Decode swap events
        swap1_events = self.decode_swap_events(swap1_receipt)
        
        self.results['swap1_details'] = {
            'transaction_hash': swap1_hash,
            'gas_used': swap1_receipt['gasUsed'],
            'status': 'success' if swap1_receipt['status'] == 1 else 'failed',
            'events': swap1_events,
            'input_token': 'DAI',
            'output_token': 'ARB',
            'input_amount': Web3.from_wei(self.swap_amount_dai, 'ether'),
        }
        self.results['transaction_hashes'].append(swap1_hash)
        
        # Get balances after first swap
        balances_after_swap1 = self.get_current_balances()
        arb_received = balances_after_swap1['ARB'] - self.results['initial_balances']['ARB']
        self.results['swap1_details']['output_amount'] = arb_received
        
        print(f"✅ Received {arb_received:.6f} ARB")
        
        # Step 4: Wait 5 minutes
        print(f"\n⏰ Step 4: Waiting {self.results['wait_period']} seconds (5 minutes)")
        for i in range(self.results['wait_period'], 0, -30):
            print(f"⏳ {i} seconds remaining...")
            time.sleep(30)
        print("✅ Wait period completed")
        
        # Step 5: Get ARB balance and approve for swap back
        arb_balance = self.get_current_balances()['ARB']
        arb_amount_to_swap = Web3.to_wei(arb_balance, 'ether')
        
        print(f"\n📝 Step 5: Approving {arb_balance:.6f} ARB for swap back")
        approve2_hash, approve2_receipt = self.approve_token(
            self.arb_address, 
            self.uniswap_router, 
            arb_amount_to_swap
        )
        self.results['transaction_hashes'].append(approve2_hash)
        
        # Step 6: Execute ARB -> DAI swap
        print(f"\n🔄 Step 6: Executing ARB -> DAI swap")
        swap2_hash, swap2_receipt = self.execute_uniswap_swap(
            'ARB', 'DAI', arb_amount_to_swap
        )
        
        # Decode swap events
        swap2_events = self.decode_swap_events(swap2_receipt)
        
        self.results['swap2_details'] = {
            'transaction_hash': swap2_hash,
            'gas_used': swap2_receipt['gasUsed'],
            'status': 'success' if swap2_receipt['status'] == 1 else 'failed',
            'events': swap2_events,
            'input_token': 'ARB',
            'output_token': 'DAI',
            'input_amount': arb_balance,
        }
        self.results['transaction_hashes'].append(swap2_hash)
        
        # Step 7: Get final balances
        print("\n📊 Step 7: Recording final balances")
        self.results['final_balances'] = self.get_current_balances()
        dai_received = self.results['final_balances']['DAI'] - balances_after_swap1['DAI']
        self.results['swap2_details']['output_amount'] = dai_received
        
        print(f"✅ Received {dai_received:.6f} DAI back")
        
        # Calculate net result
        net_dai_change = self.results['final_balances']['DAI'] - self.results['initial_balances']['DAI']
        
        print("\n" + "=" * 60)
        print("🎉 ATOMIC SWAP WORKFLOW COMPLETED")
        print("=" * 60)
        
        return self.results
    
    def print_final_report(self):
        """Print comprehensive final report"""
        print("\n📋 FINAL EXECUTION REPORT")
        print("=" * 60)
        
        # Source address
        print(f"🏠 Source Address: {self.agent.address}")
        
        # Swap protocol
        print(f"🔄 Swap Protocol: Uniswap V3 Router")
        print(f"📍 Router Address: {self.uniswap_router}")
        
        # Swap 1 details
        print(f"\n🔄 SWAP 1: DAI -> ARB")
        print(f"   Input: {self.results['swap1_details']['input_amount']:.6f} DAI")
        print(f"   Output: {self.results['swap1_details']['output_amount']:.6f} ARB")
        print(f"   Hash: {self.results['swap1_details']['transaction_hash']}")
        print(f"   Status: {self.results['swap1_details']['status']}")
        print(f"   Gas: {self.results['swap1_details']['gas_used']:,}")
        
        # Wait period
        print(f"\n⏰ WAIT PERIOD: {self.results['wait_period']} seconds")
        
        # Swap 2 details
        print(f"\n🔄 SWAP 2: ARB -> DAI")
        print(f"   Input: {self.results['swap2_details']['input_amount']:.6f} ARB")
        print(f"   Output: {self.results['swap2_details']['output_amount']:.6f} DAI")
        print(f"   Hash: {self.results['swap2_details']['transaction_hash']}")
        print(f"   Status: {self.results['swap2_details']['status']}")
        print(f"   Gas: {self.results['swap2_details']['gas_used']:,}")
        
        # All transaction hashes
        print(f"\n📋 ALL TRANSACTION HASHES:")
        for i, tx_hash in enumerate(self.results['transaction_hashes'], 1):
            print(f"   {i}. {tx_hash}")
        
        # Balance comparison
        print(f"\n💰 BALANCE COMPARISON:")
        print(f"   Initial DAI: {self.results['initial_balances']['DAI']:.6f}")
        print(f"   Final DAI:   {self.results['final_balances']['DAI']:.6f}")
        print(f"   Net Change:  {self.results['final_balances']['DAI'] - self.results['initial_balances']['DAI']:+.6f}")
        
        print(f"\n   Initial ARB: {self.results['initial_balances']['ARB']:.6f}")
        print(f"   Final ARB:   {self.results['final_balances']['ARB']:.6f}")
        print(f"   Net Change:  {self.results['final_balances']['ARB'] - self.results['initial_balances']['ARB']:+.6f}")
        
        # Network confirmations
        print(f"\n✅ Network Approval Status:")
        print(f"   Swap 1 Receipt: {self.results['swap1_details']['status']}")
        print(f"   Swap 2 Receipt: {self.results['swap2_details']['status']}")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    try:
        # Initialize and run workflow
        workflow = AtomicSwapWorkflow()
        results = workflow.run_workflow()
        
        # Print final report
        workflow.print_final_report()
        
        # Save results to file
        with open('atomic_swap_results.json', 'w') as f:
            # Convert Decimal objects to float for JSON serialization
            json_results = json.loads(json.dumps(results, default=float))
            json.dump(json_results, f, indent=2)
        
        print(f"\n💾 Results saved to: atomic_swap_results.json")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)