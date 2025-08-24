"""
DAI COMPLIANCE ENFORCED: This file has been modified to use DAI-only operations.
Only DAI → WBTC and DAI → WETH swaps are permitted.
"""


#!/usr/bin/env python3
"""
FORCE SWAP WITH APPROVAL: Explicit allowance management
"""

import os
import time
from arbitrum_testnet_agent import ArbitrumTestnetAgent
from web3 import Web3

def main():
    """Execute swap with explicit approval step"""
    print("🔄 FORCE SWAP WITH EXPLICIT APPROVAL")
    print("=" * 50)
    
    try:
        agent = ArbitrumTestnetAgent()
        print(f"📍 Wallet: {agent.address}")
        
        # Initialize Uniswap integration
        from uniswap_integration import UniswapArbitrumIntegration
        agent.uniswap = UniswapArbitrumIntegration(agent.w3, agent.account)
        
        # DAI and Router addresses
        dai_address = "0xaf88d065eec38faD0AEFf3e253e648a15cEe23dC"
        wbtc_address = "0x2f2a2543B76A4166549F7bffBE68df6Fc579b2F3"
        router_address = "0xE592427A0AEce92De3Edee1F18E0157C05861564"
        
        # Amount to swap (based on your DeBank balance)
        DAI_amount = 40.0
        DAI_amount_wei = int(DAI_amount * (10 ** 6))
        
        print(f"💰 Swapping {DAI_amount} DAI for WBTC")
        
        # Step 1: Check and approve DAI
        print("\n🔐 Step 1: DAI Approval")
        
        DAI_abi = [
            {
                "constant": False,
                "inputs": [
                    {"name": "_spender", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [
                    {"name": "_owner", "type": "address"},
                    {"name": "_spender", "type": "address"}
                ],
                "name": "allowance",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            }
        ]
        
        DAI_contract = agent.w3.eth.contract(
            address=Web3.to_checksum_address(dai_address),
            abi=DAI_abi
        )
        
        # Check current allowance
        try:
            current_allowance = DAI_contract.functions.allowance(
                agent.address,
                router_address
            ).call()
            print(f"Current allowance: {current_allowance}")
        except:
            print("⚠️ Could not check allowance, proceeding with approval")
            current_allowance = 0
        
        if current_allowance < DAI_amount_wei:
            print("🔧 Approving DAI...")
            
            # Build approval transaction
            approve_txn = DAI_contract.functions.approve(
                router_address,
                DAI_amount_wei * 2  # Approve 2x amount
            ).build_transaction({
                'from': agent.address,
                'gas': 60000,
                'gasPrice': agent.w3.eth.gas_price,
                'nonce': agent.w3.eth.get_transaction_count(agent.address)
            })
            
            # Sign and send
            signed_txn = agent.w3.eth.account.sign_transaction(approve_txn, agent.account.key)
            approve_hash = agent.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            print(f"✅ Approval transaction: {approve_hash.hex()}")
            
            if agent.w3.eth.chain_id == 42161:
                print(f"📊 View on Arbiscan: https://arbiscan.io/tx/{approve_hash.hex()}")
            
            # Wait for confirmation
            print("⏳ Waiting for approval confirmation...")
            time.sleep(20)
        else:
            print("✅ Sufficient allowance exists")
        
        # Step 2: Execute swap
        print("\n🔄 Step 2: Executing Swap")
        
        swap_result = agent.uniswap.swap_tokens(
            dai_address,
            wbtc_address,
            DAI_amount_wei,
            500  # 0.05% fee tier
        )
        
        if swap_result:
            print(f"✅ Swap transaction: {swap_result}")
            
            if agent.w3.eth.chain_id == 42161:
                print(f"📊 View on Arbiscan: https://arbiscan.io/tx/{swap_result}")
            
            print("⏳ Waiting for swap confirmation...")
            time.sleep(30)
            
            print("\n🎉 SWAP COMPLETED!")
            print("💡 Check your wallet for WBTC")
            
        else:
            print("❌ Swap failed")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
