
#!/usr/bin/env python3
"""
Standalone debug script to diagnose token balance issues
"""

import logging
import sys
from datetime import datetime

# Set up comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("debug_log_phase1_step1_1.txt")
    ]
)

def debug_token_balances():
    """Debug token balance retrieval with detailed logging"""
    print("\n💰 STANDALONE TOKEN BALANCE DIAGNOSTIC")
    print("=" * 50)
    
    try:
        # Initialize the agent
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        logging.debug("DEBUG: Initializing ArbitrumTestnetAgent")
        agent = ArbitrumTestnetAgent()
        logging.debug(f"DEBUG: Agent initialized with address: {agent.address}")
        
        # Initialize DeFi integrations
        if not hasattr(agent, 'aave') or agent.aave is None:
            logging.debug("DEBUG: Initializing DeFi integrations")
            success = agent.initialize_integrations()
            logging.debug(f"DEBUG: DeFi integrations initialized: {success}")
        
        # Check ETH balance
        logging.debug(f"DEBUG: Checking ETH balance for wallet {agent.address}")
        eth_balance = agent.get_eth_balance()
        logging.debug(f"DEBUG: Raw ETH balance: {eth_balance:.10f} ETH")
        print(f"   ETH Balance: {eth_balance:.6f} ETH")
        
        # Define tokens to check
        tokens_to_check = [
            ("WBTC", agent.wbtc_address),
            ("WETH", agent.weth_address),
            ("USDC", agent.usdc_address)
        ]
        
        # aToken addresses for direct checking
        atoken_addresses = {
            "WBTC": "0x6533afac2E7BCCB20dca161449A13A2D2d5B739A",  # aWBTC
            "WETH": "0xe50fA9b4c56454E2edF6BFf7c81b50c5F05aBE61",  # aWETH
            "USDC": "0x724dc807b04555b71ed48a6896b6F41593b8C637"   # aUSDC
        }
        
        logging.debug(f"DEBUG: aToken addresses: {atoken_addresses}")
        
        # Check supplied balances using both methods
        for token_name, token_address in tokens_to_check:
            logging.debug(f"DEBUG: ===== Checking {token_name} =====")
            logging.debug(f"DEBUG: Underlying token address: {token_address}")
            logging.debug(f"DEBUG: Expected aToken address: {atoken_addresses[token_name]}")
            
            # Method 1: Use agent's aave integration
            try:
                logging.debug(f"DEBUG: Method 1 - Using agent.aave.get_supplied_balance")
                supplied_balance = agent.aave.get_supplied_balance(token_address)
                logging.debug(f"DEBUG: Method 1 result: {supplied_balance}")
                print(f"   {token_name} Supplied (Method 1): {supplied_balance:.6f}")
            except Exception as e:
                logging.error(f"ERROR: Method 1 failed for {token_name}: {e}")
                print(f"   {token_name} Supplied (Method 1): ERROR")
            
            # Method 2: Direct aToken contract call
            try:
                logging.debug(f"DEBUG: Method 2 - Direct aToken contract call")
                from web3 import Web3
                
                atoken_abi = [{
                    "inputs": [{"name": "account", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                }, {
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "stateMutability": "view",
                    "type": "function"
                }]
                
                atoken_address = atoken_addresses[token_name]
                logging.debug(f"DEBUG: Creating contract for aToken: {atoken_address}")
                
                atoken_contract = agent.w3.eth.contract(
                    address=Web3.to_checksum_address(atoken_address),
                    abi=atoken_abi
                )
                
                logging.debug(f"DEBUG: Calling balanceOf({agent.address})")
                balance_wei = atoken_contract.functions.balanceOf(agent.address).call()
                logging.debug(f"DEBUG: Raw balance_wei: {balance_wei}")
                
                logging.debug(f"DEBUG: Calling decimals()")
                decimals = atoken_contract.functions.decimals().call()
                logging.debug(f"DEBUG: Decimals: {decimals}")
                
                balance = balance_wei / (10 ** decimals)
                logging.debug(f"DEBUG: Method 2 result: {balance}")
                print(f"   {token_name} Supplied (Method 2): {balance:.6f}")
                
            except Exception as e:
                logging.error(f"ERROR: Method 2 failed for {token_name}: {e}")
                print(f"   {token_name} Supplied (Method 2): ERROR")
        
        print("\n✅ Standalone diagnostic completed")
        
    except Exception as e:
        logging.error(f"ERROR: Standalone diagnostic failed: {e}", exc_info=True)
        print(f"❌ Diagnostic failed: {e}")

if __name__ == "__main__":
    debug_token_balances()
