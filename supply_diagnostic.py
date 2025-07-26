
import os
import sys
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
import json
import time

def diagnose_supply_failure():
    """Comprehensive diagnostic for Aave supply failures"""
    print("🔍 AAVE SUPPLY FAILURE DIAGNOSTIC")
    print("=" * 50)
    
    try:
        load_dotenv()
        
        # Initialize connection
        network_mode = os.getenv('NETWORK_MODE', 'testnet')
        if network_mode == 'mainnet':
            w3 = Web3(Web3.HTTPProvider('https://arb1.arbitrum.io/rpc'))
            expected_chain = 42161
        else:
            w3 = Web3(Web3.HTTPProvider('https://sepolia-rollup.arbitrum.io/rpc'))
            expected_chain = 421614
            
        if not w3.is_connected():
            print("❌ CRITICAL: Cannot connect to Arbitrum network")
            return False
            
        chain_id = w3.eth.chain_id
        print(f"✅ Connected to Arbitrum (Chain ID: {chain_id})")
        
        if chain_id != expected_chain:
            print(f"⚠️  Chain ID mismatch! Expected {expected_chain}, got {chain_id}")
        
        # Initialize account
        private_key = os.getenv('PRIVATE_KEY')
        if not private_key:
            print("❌ CRITICAL: PRIVATE_KEY not found in environment")
            return False
            
        account = Account.from_key(private_key)
        print(f"✅ Wallet: {account.address}")
        
        # Check ETH balance
        eth_balance = w3.eth.get_balance(account.address) / 1e18
        print(f"💰 ETH Balance: {eth_balance:.6f} ETH")
        
        if eth_balance < 0.001:
            print("❌ CRITICAL: Insufficient ETH for gas fees")
            return False
            
        # Contract addresses based on network
        if network_mode == 'mainnet':
            dai_address = "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1"
            pool_address = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
        else:
            dai_address = "0x82E64f49Ed5EC1bC6e43DAD4FC8Af9bb3A2312EE"
            pool_address = "0x6Ae43d3271ff6888e7Fc43Fd7321a503ff738951"
        
        print(f"🏦 Aave Pool: {pool_address}")
        print(f"🪙 DAI Token: {dai_address}")
        
        # Check contract deployments
        pool_code = w3.eth.get_code(pool_address)
        dai_code = w3.eth.get_code(dai_address)
        
        if pool_code == b'':
            print("❌ CRITICAL: Aave Pool contract not deployed")
            return False
        else:
            print("✅ Aave Pool contract exists")
            
        if dai_code == b'':
            print("❌ CRITICAL: DAI token contract not deployed")
            return False
        else:
            print("✅ DAI token contract exists")
        
        # Check DAI balance
        dai_abi = [{
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        }]
        
        dai_contract = w3.eth.contract(address=dai_address, abi=dai_abi)
        dai_balance_wei = dai_contract.functions.balanceOf(account.address).call()
        dai_balance = dai_balance_wei / 1e18
        
        print(f"💰 DAI Balance: {dai_balance:.6f} DAI")
        
        if dai_balance == 0:
            print("❌ CRITICAL: No DAI tokens to supply")
            return False
        
        # Check current DAI allowance
        allowance_abi = [{
            "constant": True,
            "inputs": [
                {"name": "_owner", "type": "address"},
                {"name": "_spender", "type": "address"}
            ],
            "name": "allowance",
            "outputs": [{"name": "", "type": "uint256"}],
            "type": "function"
        }]
        
        try:
            dai_contract_full = w3.eth.contract(address=dai_address, abi=allowance_abi)
            current_allowance = dai_contract_full.functions.allowance(
                account.address, 
                pool_address
            ).call()
            
            allowance_formatted = current_allowance / 1e18
            print(f"🔐 Current DAI Allowance: {allowance_formatted:.6f} DAI")
            
            if current_allowance == 0:
                print("❌ ISSUE: No DAI allowance set for Aave pool")
                print("💡 SOLUTION: Must approve DAI spending before supply")
            else:
                print("✅ DAI allowance exists")
                
        except Exception as allowance_err:
            print(f"⚠️ Could not check allowance: {allowance_err}")
        
        # Test gas price
        gas_price = w3.eth.gas_price
        gas_price_gwei = gas_price / 1e9
        print(f"⛽ Current Gas Price: {gas_price_gwei:.2f} Gwei")
        
        if gas_price_gwei < 0.01:
            print("⚠️ Very low gas price - transactions may be slow")
        
        # Check latest block
        latest_block = w3.eth.block_number
        print(f"📦 Latest Block: {latest_block}")
        
        # Simulate approval transaction
        print("\n🧪 SIMULATING APPROVAL TRANSACTION:")
        
        approve_abi = [{
            "constant": False,
            "inputs": [
                {"name": "_spender", "type": "address"},
                {"name": "_value", "type": "uint256"}
            ],
            "name": "approve",
            "outputs": [{"name": "", "type": "bool"}],
            "type": "function"
        }]
        
        try:
            dai_approve_contract = w3.eth.contract(address=dai_address, abi=approve_abi)
            
            # Simulate approving 1 DAI
            test_amount = int(1 * 1e18)
            
            estimated_gas = dai_approve_contract.functions.approve(
                pool_address,
                test_amount
            ).estimate_gas({'from': account.address})
            
            print(f"✅ Approval simulation successful - Gas needed: {estimated_gas}")
            
        except Exception as approve_sim_err:
            print(f"❌ Approval simulation failed: {approve_sim_err}")
            
        # Simulate supply transaction
        print("\n🧪 SIMULATING SUPPLY TRANSACTION:")
        
        pool_abi = [{
            "inputs": [
                {"name": "asset", "type": "address"},
                {"name": "amount", "type": "uint256"},
                {"name": "onBehalfOf", "type": "address"},
                {"name": "referralCode", "type": "uint16"}
            ],
            "name": "supply",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }]
        
        try:
            pool_contract = w3.eth.contract(address=pool_address, abi=pool_abi)
            
            # Simulate supplying 1 DAI
            test_supply_amount = int(1 * 1e18)
            
            estimated_supply_gas = pool_contract.functions.supply(
                dai_address,
                test_supply_amount,
                account.address,
                0
            ).estimate_gas({'from': account.address})
            
            print(f"✅ Supply simulation successful - Gas needed: {estimated_supply_gas}")
            
        except Exception as supply_sim_err:
            print(f"❌ Supply simulation failed: {supply_sim_err}")
            if "insufficient allowance" in str(supply_sim_err).lower():
                print("💡 CAUSE: Token approval required before supply")
            elif "insufficient balance" in str(supply_sim_err).lower():
                print("💡 CAUSE: Insufficient token balance")
            else:
                print(f"💡 CAUSE: {supply_sim_err}")
        
        print("\n📋 DIAGNOSTIC SUMMARY:")
        print("=" * 30)
        
        issues = []
        if eth_balance < 0.001:
            issues.append("Insufficient ETH for gas")
        if dai_balance == 0:
            issues.append("No DAI tokens available")
        if 'current_allowance' in locals() and current_allowance == 0:
            issues.append("DAI approval required")
            
        if issues:
            print("❌ ISSUES FOUND:")
            for issue in issues:
                print(f"   • {issue}")
        else:
            print("✅ All checks passed - supply should work")
            
        return len(issues) == 0
        
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        return False

if __name__ == "__main__":
    diagnose_supply_failure()
