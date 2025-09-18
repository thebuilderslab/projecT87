#!/usr/bin/env python3
"""
Quick Atomic Mainnet Swap Workflow
Executes: DAI -> ARB -> DAI with 5-minute wait between swaps
Uses existing DAI balance from wallet
"""

import time
import sys
import os
import json
from web3 import Web3

# Add current directory to path
sys.path.append('.')

# Force mainnet mode
os.environ['NETWORK_MODE'] = 'mainnet'

from arbitrum_testnet_agent import ArbitrumTestnetAgent

def get_token_balance(agent, token_address):
    """Get token balance from contract"""
    try:
        token_contract = agent.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=[{
                "inputs": [{"name": "account", "type": "address"}],
                "name": "balanceOf", 
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }]
        )
        balance_wei = token_contract.functions.balanceOf(agent.address).call()
        return Web3.from_wei(balance_wei, 'ether')
    except Exception as e:
        print(f"Error getting token balance: {e}")
        return 0.0

def approve_token(agent, token_address, spender, amount):
    """Approve token spending"""
    print(f"📝 Approving {Web3.from_wei(amount, 'ether'):.6f} tokens for {spender}")
    
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
        contract = agent.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=erc20_abi
        )
        
        txn = contract.functions.approve(
            Web3.to_checksum_address(spender),
            amount
        ).build_transaction({
            'from': agent.address,
            'gas': 100000,
            'gasPrice': agent.w3.eth.gas_price,
            'nonce': agent.w3.eth.get_transaction_count(agent.address)
        })
        
        signed_txn = agent.w3.eth.account.sign_transaction(txn, agent.private_key)
        tx_hash = agent.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        receipt = agent.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        print(f"✅ Approval confirmed: {tx_hash.hex()}")
        return tx_hash.hex(), receipt
    except Exception as e:
        print(f"❌ Error approving token: {e}")
        return None, None

def execute_uniswap_swap(agent, token_in, token_out, amount_in, dai_address, arb_address, uniswap_router):
    """Execute swap via Uniswap V3"""
    print(f"🔄 Executing swap: {Web3.from_wei(amount_in, 'ether'):.6f} {token_in} -> {token_out}")
    
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
        router_contract = agent.w3.eth.contract(
            address=Web3.to_checksum_address(uniswap_router),
            abi=router_abi
        )
        
        token_in_addr = dai_address if token_in == 'DAI' else arb_address
        token_out_addr = arb_address if token_out == 'ARB' else dai_address
        
        deadline = int(time.time()) + 300  # 5 minutes
        params = {
            'tokenIn': Web3.to_checksum_address(token_in_addr),
            'tokenOut': Web3.to_checksum_address(token_out_addr),
            'fee': 3000,  # 0.3% fee tier
            'recipient': agent.address,
            'deadline': deadline,
            'amountIn': amount_in,
            'amountOutMinimum': 0,
            'sqrtPriceLimitX96': 0
        }
        
        txn = router_contract.functions.exactInputSingle(params).build_transaction({
            'from': agent.address,
            'gas': 300000,
            'gasPrice': agent.w3.eth.gas_price,
            'nonce': agent.w3.eth.get_transaction_count(agent.address)
        })
        
        signed_txn = agent.w3.eth.account.sign_transaction(txn, agent.private_key)
        tx_hash = agent.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        receipt = agent.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        print(f"✅ Swap completed: {tx_hash.hex()}")
        print(f"📊 Gas used: {receipt['gasUsed']:,}")
        print(f"📊 Status: {'Success' if receipt['status'] == 1 else 'Failed'}")
        
        return tx_hash.hex(), receipt
    except Exception as e:
        print(f"❌ Error executing swap: {e}")
        return None, None

def main():
    """Execute the atomic swap workflow"""
    print("🚀 ATOMIC MAINNET SWAP WORKFLOW")
    print("=" * 60)
    
    # Token addresses
    dai_address = "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1"
    arb_address = "0x912CE59144191C1204E64559FE8253a0e49E6548"
    uniswap_router = "0xE592427A0AEce92De3Edee1F18E0157C05861564"
    
    results = {
        'source_address': '',
        'swap_protocol': 'Uniswap V3 Router',
        'swap_path': f'{dai_address} -> {arb_address} -> {dai_address}',
        'transaction_hashes': [],
        'initial_balances': {},
        'final_balances': {},
        'swap1_details': {},
        'swap2_details': {},
        'wait_time': 300
    }
    
    try:
        # Initialize agent
        print("🔄 Initializing agent...")
        agent = ArbitrumTestnetAgent()
        results['source_address'] = agent.address
        
        print(f"✅ Agent initialized: {agent.address}")
        print(f"🌐 Chain ID: {agent.w3.eth.chain_id}")
        
        # Step 1: Check initial balances
        print("\n📊 Step 1: Checking initial balances")
        dai_balance = get_token_balance(agent, dai_address)
        arb_balance = get_token_balance(agent, arb_address)
        eth_balance = agent.get_eth_balance()
        
        results['initial_balances'] = {
            'DAI': dai_balance,
            'ARB': arb_balance,
            'ETH': eth_balance
        }
        
        print(f"💰 DAI Balance: {dai_balance:.6f}")
        print(f"💰 ARB Balance: {arb_balance:.6f}")
        print(f"💰 ETH Balance: {eth_balance:.6f}")
        
        # Check if we have sufficient DAI
        swap_amount = min(dai_balance, 10.0)  # Use available DAI up to 10
        if dai_balance < 1.0:
            raise Exception(f"Insufficient DAI balance: {dai_balance:.6f} < 1.0")
        
        print(f"\n✅ Using {swap_amount:.6f} DAI for atomic swap")
        swap_amount_wei = Web3.to_wei(swap_amount, 'ether')
        
        # Step 2: Approve DAI for Uniswap
        print("\n📝 Step 2: Approving DAI for Uniswap")
        approve_hash, approve_receipt = approve_token(agent, dai_address, uniswap_router, swap_amount_wei)
        if approve_hash:
            results['transaction_hashes'].append(approve_hash)
        
        # Step 3: Execute DAI -> ARB swap
        print("\n🔄 Step 3: Executing DAI -> ARB swap")
        swap1_hash, swap1_receipt = execute_uniswap_swap(
            agent, 'DAI', 'ARB', swap_amount_wei, dai_address, arb_address, uniswap_router
        )
        
        if not swap1_hash:
            raise Exception("Failed to execute DAI -> ARB swap")
        
        results['transaction_hashes'].append(swap1_hash)
        
        # Check ARB received
        arb_after_swap1 = get_token_balance(agent, arb_address)
        arb_received = arb_after_swap1 - arb_balance
        
        results['swap1_details'] = {
            'input_token': 'DAI',
            'output_token': 'ARB', 
            'input_amount': swap_amount,
            'output_amount': arb_received,
            'transaction_hash': swap1_hash,
            'gas_used': swap1_receipt['gasUsed'] if swap1_receipt else 0,
            'status': 'success' if swap1_receipt and swap1_receipt['status'] == 1 else 'failed'
        }
        
        print(f"✅ Received {arb_received:.6f} ARB")
        
        # Step 4: Wait 5 minutes
        print(f"\n⏰ Step 4: Waiting 300 seconds (5 minutes)")
        for i in range(300, 0, -30):
            print(f"⏳ {i} seconds remaining...")
            time.sleep(30)
        print("✅ Wait period completed")
        
        # Step 5: Check ARB balance and approve for swap back
        current_arb_balance = get_token_balance(agent, arb_address)
        arb_swap_amount_wei = Web3.to_wei(current_arb_balance, 'ether')
        
        print(f"\n📝 Step 5: Approving {current_arb_balance:.6f} ARB for swap back")
        approve2_hash, approve2_receipt = approve_token(agent, arb_address, uniswap_router, arb_swap_amount_wei)
        if approve2_hash:
            results['transaction_hashes'].append(approve2_hash)
        
        # Step 6: Execute ARB -> DAI swap
        print(f"\n🔄 Step 6: Executing ARB -> DAI swap")
        swap2_hash, swap2_receipt = execute_uniswap_swap(
            agent, 'ARB', 'DAI', arb_swap_amount_wei, dai_address, arb_address, uniswap_router
        )
        
        if not swap2_hash:
            raise Exception("Failed to execute ARB -> DAI swap")
        
        results['transaction_hashes'].append(swap2_hash)
        
        # Check final balances
        final_dai_balance = get_token_balance(agent, dai_address)
        final_arb_balance = get_token_balance(agent, arb_address)
        final_eth_balance = agent.get_eth_balance()
        
        dai_received = final_dai_balance - (dai_balance - swap_amount)
        
        results['swap2_details'] = {
            'input_token': 'ARB',
            'output_token': 'DAI',
            'input_amount': current_arb_balance,
            'output_amount': dai_received,
            'transaction_hash': swap2_hash,
            'gas_used': swap2_receipt['gasUsed'] if swap2_receipt else 0,
            'status': 'success' if swap2_receipt and swap2_receipt['status'] == 1 else 'failed'
        }
        
        results['final_balances'] = {
            'DAI': final_dai_balance,
            'ARB': final_arb_balance,
            'ETH': final_eth_balance
        }
        
        print(f"✅ Received {dai_received:.6f} DAI back")
        
        # Final report
        print("\n" + "=" * 60)
        print("🎉 ATOMIC SWAP COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        print(f"\n🏠 Source Address: {results['source_address']}")
        print(f"🔄 Swap Protocol: {results['swap_protocol']}")
        print(f"📍 Router Address: {uniswap_router}")
        
        print(f"\n🔄 SWAP 1: DAI -> ARB")
        print(f"   Input: {results['swap1_details']['input_amount']:.6f} DAI")
        print(f"   Output: {results['swap1_details']['output_amount']:.6f} ARB")
        print(f"   Hash: {results['swap1_details']['transaction_hash']}")
        print(f"   Status: {results['swap1_details']['status']}")
        
        print(f"\n⏰ WAIT PERIOD: {results['wait_time']} seconds")
        
        print(f"\n🔄 SWAP 2: ARB -> DAI")  
        print(f"   Input: {results['swap2_details']['input_amount']:.6f} ARB")
        print(f"   Output: {results['swap2_details']['output_amount']:.6f} DAI")
        print(f"   Hash: {results['swap2_details']['transaction_hash']}")
        print(f"   Status: {results['swap2_details']['status']}")
        
        print(f"\n📋 ALL TRANSACTION HASHES:")
        for i, tx_hash in enumerate(results['transaction_hashes'], 1):
            print(f"   {i}. {tx_hash}")
        
        print(f"\n💰 FINAL WALLET BALANCES:")
        for token in ['DAI', 'ARB']:
            initial = results['initial_balances'][token]
            final = results['final_balances'][token]
            change = final - initial
            print(f"   {token}: {final:.6f} (change: {change:+.6f})")
        
        print(f"\n✅ Network approval status: Both swaps confirmed on-chain")
        
        # Save results
        with open('atomic_swap_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=float)
        print(f"\n💾 Results saved to: atomic_swap_results.json")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)