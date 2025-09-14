#!/usr/bin/env python3
"""
REAL TRADING IMPLEMENTATION - DAI↔ARB Micro Swaps
Phase 2: Live on-chain execution with Uniswap V3 integration
"""

import os
import time
import json
import traceback
from datetime import datetime
from typing import Dict, Optional, Tuple

def initialize_arb_token_contract(agent):
    """Initialize ARB ERC-20 token contract integration"""
    print("🔧 INITIALIZING ARB ERC-20 TOKEN INTEGRATION...")
    
    try:
        # ARB token address on Arbitrum mainnet
        arb_address = "0x912CE59144191C1204E64559FE8253a0e49E6548"
        
        # Standard ERC-20 ABI for basic operations
        erc20_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            },
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
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "symbol",
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "name",
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            }
        ]
        
        # Create ARB contract instance
        arb_contract = agent.w3.eth.contract(address=arb_address, abi=erc20_abi)
        
        # Verify contract by getting basic info
        arb_symbol = arb_contract.functions.symbol().call()
        arb_decimals = arb_contract.functions.decimals().call()
        arb_name = arb_contract.functions.name().call()
        
        print(f"✅ ARB Contract Initialized:")
        print(f"   Address: {arb_address}")
        print(f"   Symbol: {arb_symbol}")
        print(f"   Name: {arb_name}")
        print(f"   Decimals: {arb_decimals}")
        
        # Get current ARB balance
        arb_balance_raw = arb_contract.functions.balanceOf(agent.address).call()
        arb_balance = arb_balance_raw / (10 ** arb_decimals)
        
        print(f"   Current ARB Balance: {arb_balance:.6f} ARB")
        
        return arb_contract, arb_decimals
        
    except Exception as e:
        print(f"❌ Failed to initialize ARB contract: {e}")
        print(f"   Error details: {traceback.format_exc()}")
        return None, None

def initialize_dai_token_contract(agent):
    """Initialize DAI token contract integration"""
    print("🔧 INITIALIZING DAI TOKEN INTEGRATION...")
    
    try:
        # DAI token address on Arbitrum mainnet
        dai_address = "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1"
        
        # Standard ERC-20 ABI
        erc20_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            },
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
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function"
            }
        ]
        
        # Create DAI contract instance
        dai_contract = agent.w3.eth.contract(address=dai_address, abi=erc20_abi)
        
        # Get DAI info
        dai_decimals = dai_contract.functions.decimals().call()
        dai_balance_raw = dai_contract.functions.balanceOf(agent.address).call()
        dai_balance = dai_balance_raw / (10 ** dai_decimals)
        
        print(f"✅ DAI Contract Initialized:")
        print(f"   Address: {dai_address}")
        print(f"   Decimals: {dai_decimals}")
        print(f"   Current DAI Balance: {dai_balance:.6f} DAI")
        
        return dai_contract, dai_decimals
        
    except Exception as e:
        print(f"❌ Failed to initialize DAI contract: {e}")
        return None, None

def get_comprehensive_balances(agent, dai_contract, arb_contract, weth_contract) -> Dict[str, float]:
    """Get comprehensive token balances including native ETH, DAI, ARB, and WETH"""
    try:
        balances = {}
        
        # Native ETH balance
        eth_balance = agent.w3.eth.get_balance(agent.address) / 1e18
        balances['ETH'] = eth_balance
        
        # DAI balance
        if dai_contract:
            dai_balance_raw = dai_contract.functions.balanceOf(agent.address).call()
            balances['DAI'] = dai_balance_raw / 1e18
        
        # ARB balance (ERC-20, not native)
        if arb_contract:
            arb_balance_raw = arb_contract.functions.balanceOf(agent.address).call()
            balances['ARB'] = arb_balance_raw / 1e18
        
        # WETH balance
        if weth_contract:
            weth_balance_raw = weth_contract.functions.balanceOf(agent.address).call()
            balances['WETH'] = weth_balance_raw / 1e18
        
        return balances
        
    except Exception as e:
        print(f"❌ Error getting comprehensive balances: {e}")
        return {}

def initialize_uniswap_v3_router(agent):
    """Initialize Uniswap V3 Router for token swaps"""
    print("🔧 INITIALIZING UNISWAP V3 ROUTER...")
    
    try:
        # Uniswap V3 Router address on Arbitrum
        router_address = "0xE592427A0AEce92De3Edee1F18E0157C05861564"
        
        # Minimal Uniswap V3 Router ABI for exactInputSingle
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
                "stateMutability": "payable",
                "type": "function"
            }
        ]
        
        # Create router contract instance
        router_contract = agent.w3.eth.contract(address=router_address, abi=router_abi)
        
        print(f"✅ Uniswap V3 Router Initialized:")
        print(f"   Address: {router_address}")
        
        return router_contract
        
    except Exception as e:
        print(f"❌ Failed to initialize Uniswap V3 router: {e}")
        return None

def get_current_health_factor(agent) -> float:
    """Get current health factor from Aave"""
    try:
        pool_address = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
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
        
        pool_contract = agent.w3.eth.contract(address=pool_address, abi=pool_abi)
        raw_data = pool_contract.functions.getUserAccountData(agent.address).call()
        health_factor = raw_data[5] / 1e18 if raw_data[5] > 0 else float('inf')
        
        return health_factor
        
    except Exception as e:
        print(f"❌ Error getting health factor: {e}")
        return 0.0

def approve_token_if_needed(agent, token_contract, spender_address, amount_wei: int, token_symbol: str) -> bool:
    """Approve token spending if allowance is insufficient"""
    try:
        print(f"🔐 CHECKING {token_symbol} APPROVAL...")
        
        # Check current allowance
        current_allowance = token_contract.functions.allowance(agent.address, spender_address).call()
        
        print(f"   Current allowance: {current_allowance / 1e18:.6f} {token_symbol}")
        print(f"   Required amount: {amount_wei / 1e18:.6f} {token_symbol}")
        
        if current_allowance >= amount_wei:
            print(f"   ✅ Sufficient allowance already exists")
            return True
        
        print(f"   📝 Approving {token_symbol} spending...")
        
        # Build approval transaction with maximum allowance for efficiency
        max_allowance = 2**256 - 1  # Max uint256
        
        approve_txn = token_contract.functions.approve(spender_address, max_allowance).build_transaction({
            'from': agent.address,
            'nonce': agent.w3.eth.get_transaction_count(agent.address),
            'gasPrice': agent.w3.eth.gas_price
        })
        
        # Estimate gas
        try:
            gas_estimate = agent.w3.eth.estimate_gas(approve_txn)
            approve_txn['gas'] = int(gas_estimate * 1.2)
        except Exception as e:
            approve_txn['gas'] = 100000  # Default gas limit for approval
        
        # Sign and send
        signed_approve = agent.w3.eth.account.sign_transaction(approve_txn, agent.private_key)
        approve_tx_hash = agent.w3.eth.send_raw_transaction(signed_approve.rawTransaction)
        
        print(f"   📤 Approval transaction sent: {approve_tx_hash.hex()}")
        
        # Wait for confirmation
        approve_receipt = agent.w3.eth.wait_for_transaction_receipt(approve_tx_hash, timeout=120)
        
        if approve_receipt['status'] == 1:
            print(f"   ✅ {token_symbol} approval successful!")
            print(f"   🔗 Arbiscan: https://arbiscan.io/tx/{approve_tx_hash.hex()}")
            return True
        else:
            print(f"   ❌ {token_symbol} approval failed")
            return False
        
    except Exception as e:
        print(f"❌ Error approving {token_symbol}: {e}")
        return False

def execute_eth_to_arb_swap(agent, router_contract, arb_contract, swap_amount_eth: float) -> Dict:
    """Execute ETH to ARB swap via Uniswap V3"""
    print(f"\n🔄 EXECUTING ETH → ARB SWAP: {swap_amount_eth} ETH")
    print("=" * 70)
    
    swap_result = {
        'operation': 'ETH_TO_ARB_SWAP',
        'start_time': datetime.now().isoformat(),
        'input_amount_eth': swap_amount_eth,
        'success': False
    }
    
    try:
        # Get initial state
        initial_eth = agent.w3.eth.get_balance(agent.address) / 1e18
        initial_arb = arb_contract.functions.balanceOf(agent.address).call() / 1e18
        initial_hf = get_current_health_factor(agent)
        
        swap_result['initial_balances'] = {
            'ETH': initial_eth,
            'ARB': initial_arb
        }
        swap_result['initial_health_factor'] = initial_hf
        
        print(f"📊 INITIAL STATE:")
        print(f"   ETH Balance: {initial_eth:.6f}")
        print(f"   ARB Balance: {initial_arb:.6f}")
        print(f"   Health Factor: {initial_hf:.6f}")
        
        # Swap parameters
        swap_amount_wei = int(swap_amount_eth * 1e18)
        deadline = int(time.time()) + 1800  # 30 minutes from now
        
        # Token addresses
        weth_address = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"  # WETH on Arbitrum
        arb_address = "0x912CE59144191C1204E64559FE8253a0e49E6548"   # ARB on Arbitrum
        
        print(f"🎯 SWAP PARAMETERS:")
        print(f"   Input Amount: {swap_amount_eth} ETH")
        print(f"   Deadline: {deadline}")
        print(f"   Fee Tier: 3000 (0.3%)")
        
        # Build swap transaction (ETH is handled as WETH automatically by router)
        swap_params = {
            'tokenIn': weth_address,
            'tokenOut': arb_address,
            'fee': 3000,  # 0.3% fee tier
            'recipient': agent.address,
            'deadline': deadline,
            'amountIn': swap_amount_wei,
            'amountOutMinimum': 0,  # Accept any amount of ARB out (high slippage tolerance for test)
            'sqrtPriceLimitX96': 0
        }
        
        swap_txn = router_contract.functions.exactInputSingle(swap_params).build_transaction({
            'from': agent.address,
            'value': swap_amount_wei,  # Send ETH with transaction
            'nonce': agent.w3.eth.get_transaction_count(agent.address),
            'gasPrice': agent.w3.eth.gas_price
        })
        
        # Estimate gas
        try:
            gas_estimate = agent.w3.eth.estimate_gas(swap_txn)
            swap_txn['gas'] = int(gas_estimate * 1.2)
            print(f"   Gas Estimate: {gas_estimate:,} (using {swap_txn['gas']:,})")
        except Exception as e:
            print(f"   Gas estimation failed: {e}")
            swap_txn['gas'] = 200000  # Default gas for swap
        
        # Execute swap
        print(f"\n🔄 EXECUTING SWAP...")
        signed_swap = agent.w3.eth.account.sign_transaction(swap_txn, agent.private_key)
        swap_tx_hash = agent.w3.eth.send_raw_transaction(signed_swap.rawTransaction)
        
        print(f"📤 Swap transaction sent: {swap_tx_hash.hex()}")
        swap_result['transaction_hash'] = swap_tx_hash.hex()
        
        # Wait for confirmation
        print("⏳ Waiting for confirmation...")
        swap_receipt = agent.w3.eth.wait_for_transaction_receipt(swap_tx_hash, timeout=180)
        
        # Get final state
        final_eth = agent.w3.eth.get_balance(agent.address) / 1e18
        final_arb = arb_contract.functions.balanceOf(agent.address).call() / 1e18
        final_hf = get_current_health_factor(agent)
        
        swap_result['final_balances'] = {
            'ETH': final_eth,
            'ARB': final_arb
        }
        swap_result['final_health_factor'] = final_hf
        
        # Calculate results
        eth_spent = initial_eth - final_eth
        arb_received = final_arb - initial_arb
        
        swap_result['eth_spent'] = eth_spent
        swap_result['arb_received'] = arb_received
        swap_result['gas_used'] = swap_receipt['gasUsed']
        swap_result['gas_cost_eth'] = (swap_receipt['gasUsed'] * swap_receipt['effectiveGasPrice']) / 1e18
        
        if swap_receipt['status'] == 1 and arb_received > 0:
            swap_result['success'] = True
            
            print(f"\n✅ ETH → ARB SWAP SUCCESSFUL!")
            print(f"🔗 Arbiscan: https://arbiscan.io/tx/{swap_tx_hash.hex()}")
            print(f"📊 RESULTS:")
            print(f"   ETH Spent: {eth_spent:.6f}")
            print(f"   ARB Received: {arb_received:.6f}")
            print(f"   Exchange Rate: {arb_received/eth_spent if eth_spent > 0 else 0:.2f} ARB/ETH")
            print(f"   Gas Used: {swap_receipt['gasUsed']:,}")
            print(f"   Gas Cost: {swap_result['gas_cost_eth']:.8f} ETH")
            print(f"   Health Factor: {initial_hf:.6f} → {final_hf:.6f}")
        else:
            print(f"❌ Swap failed or no ARB received")
            swap_result['error'] = f"Transaction status: {swap_receipt['status']}, ARB received: {arb_received}"
        
        return swap_result
        
    except Exception as e:
        print(f"❌ ETH → ARB swap failed: {e}")
        swap_result['error'] = str(e)
        swap_result['error_details'] = traceback.format_exc()
        return swap_result
    
    finally:
        swap_result['end_time'] = datetime.now().isoformat()

def execute_arb_to_eth_swap(agent, router_contract, arb_contract, swap_amount_arb: float) -> Dict:
    """Execute ARB to ETH swap via Uniswap V3"""
    print(f"\n🔄 EXECUTING ARB → ETH SWAP: {swap_amount_arb} ARB")
    print("=" * 70)
    
    swap_result = {
        'operation': 'ARB_TO_ETH_SWAP',
        'start_time': datetime.now().isoformat(),
        'input_amount_arb': swap_amount_arb,
        'success': False
    }
    
    try:
        # Get initial state
        initial_eth = agent.w3.eth.get_balance(agent.address) / 1e18
        initial_arb = arb_contract.functions.balanceOf(agent.address).call() / 1e18
        initial_hf = get_current_health_factor(agent)
        
        swap_result['initial_balances'] = {
            'ETH': initial_eth,
            'ARB': initial_arb
        }
        swap_result['initial_health_factor'] = initial_hf
        
        print(f"📊 INITIAL STATE:")
        print(f"   ETH Balance: {initial_eth:.6f}")
        print(f"   ARB Balance: {initial_arb:.6f}")
        print(f"   Health Factor: {initial_hf:.6f}")
        
        # Check ARB balance
        if initial_arb < swap_amount_arb:
            raise Exception(f"Insufficient ARB balance: {initial_arb:.6f} < {swap_amount_arb:.6f}")
        
        # Swap parameters
        swap_amount_wei = int(swap_amount_arb * 1e18)
        deadline = int(time.time()) + 1800
        
        # Token addresses  
        weth_address = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"
        arb_address = "0x912CE59144191C1204E64559FE8253a0e49E6548"
        router_address = "0xE592427A0AEce92De3Edee1F18E0157C05861564"
        
        # Approve ARB spending if needed
        if not approve_token_if_needed(agent, arb_contract, router_address, swap_amount_wei, "ARB"):
            raise Exception("Failed to approve ARB spending")
        
        # Build swap transaction
        swap_params = {
            'tokenIn': arb_address,
            'tokenOut': weth_address, 
            'fee': 3000,  # 0.3% fee tier
            'recipient': agent.address,
            'deadline': deadline,
            'amountIn': swap_amount_wei,
            'amountOutMinimum': 0,  # Accept any amount of WETH out
            'sqrtPriceLimitX96': 0
        }
        
        swap_txn = router_contract.functions.exactInputSingle(swap_params).build_transaction({
            'from': agent.address,
            'nonce': agent.w3.eth.get_transaction_count(agent.address),
            'gasPrice': agent.w3.eth.gas_price
        })
        
        # Estimate gas
        try:
            gas_estimate = agent.w3.eth.estimate_gas(swap_txn)
            swap_txn['gas'] = int(gas_estimate * 1.2)
        except Exception as e:
            swap_txn['gas'] = 250000
        
        # Execute swap
        print(f"\n🔄 EXECUTING SWAP...")
        signed_swap = agent.w3.eth.account.sign_transaction(swap_txn, agent.private_key)
        swap_tx_hash = agent.w3.eth.send_raw_transaction(signed_swap.rawTransaction)
        
        print(f"📤 Swap transaction sent: {swap_tx_hash.hex()}")
        swap_result['transaction_hash'] = swap_tx_hash.hex()
        
        # Wait for confirmation
        print("⏳ Waiting for confirmation...")
        swap_receipt = agent.w3.eth.wait_for_transaction_receipt(swap_tx_hash, timeout=180)
        
        # Get final state  
        final_eth = agent.w3.eth.get_balance(agent.address) / 1e18
        final_arb = arb_contract.functions.balanceOf(agent.address).call() / 1e18
        final_hf = get_current_health_factor(agent)
        
        swap_result['final_balances'] = {
            'ETH': final_eth,
            'ARB': final_arb
        }
        swap_result['final_health_factor'] = final_hf
        
        # Calculate results
        arb_spent = initial_arb - final_arb
        eth_received = final_eth - initial_eth
        
        swap_result['arb_spent'] = arb_spent
        swap_result['eth_received'] = eth_received
        swap_result['gas_used'] = swap_receipt['gasUsed']
        swap_result['gas_cost_eth'] = (swap_receipt['gasUsed'] * swap_receipt['effectiveGasPrice']) / 1e18
        
        if swap_receipt['status'] == 1 and arb_spent > 0:
            swap_result['success'] = True
            
            print(f"\n✅ ARB → ETH SWAP SUCCESSFUL!")
            print(f"🔗 Arbiscan: https://arbiscan.io/tx/{swap_tx_hash.hex()}")
            print(f"📊 RESULTS:")
            print(f"   ARB Spent: {arb_spent:.6f}")  
            print(f"   ETH Received: {eth_received:.6f}")
            print(f"   Exchange Rate: {eth_received/arb_spent if arb_spent > 0 else 0:.6f} ETH/ARB")
            print(f"   Gas Used: {swap_receipt['gasUsed']:,}")
            print(f"   Gas Cost: {swap_result['gas_cost_eth']:.8f} ETH")
            print(f"   Health Factor: {initial_hf:.6f} → {final_hf:.6f}")
        else:
            print(f"❌ Swap failed")
            swap_result['error'] = f"Transaction status: {swap_receipt['status']}"
        
        return swap_result
        
    except Exception as e:
        print(f"❌ ARB → ETH swap failed: {e}")
        swap_result['error'] = str(e)
        swap_result['error_details'] = traceback.format_exc()
        return swap_result
    
    finally:
        swap_result['end_time'] = datetime.now().isoformat()

def main():
    """Execute real trading implementation with DAI↔ARB micro swaps"""
    print("🚀 REAL TRADING IMPLEMENTATION - DAI↔ARB MICRO SWAPS")
    print("=" * 100)
    print("Phase 2: Live on-chain execution with Uniswap V3 integration")
    print("=" * 100)
    
    execution_results = {
        'implementation_phase': 'REAL_TRADING_DAI_ARB',
        'start_time': datetime.now().isoformat(),
        'operations': {},
        'overall_success': False
    }
    
    try:
        # Initialize agent
        print("🤖 INITIALIZING ENHANCED TRADING AGENT...")
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        agent = ArbitrumTestnetAgent()
        
        if not agent or not hasattr(agent, 'w3'):
            raise Exception("Agent initialization failed")
        
        print(f"✅ Agent initialized: {agent.address}")
        
        # Initialize all token contracts
        print(f"\n🔧 INITIALIZING TOKEN CONTRACTS...")
        
        # Initialize ARB token contract  
        arb_contract, arb_decimals = initialize_arb_token_contract(agent)
        if not arb_contract:
            raise Exception("Failed to initialize ARB contract")
        
        # Initialize DAI token contract
        dai_contract, dai_decimals = initialize_dai_token_contract(agent)
        if not dai_contract:
            raise Exception("Failed to initialize DAI contract")
        
        # Initialize WETH contract
        weth_address = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"
        weth_abi = [{"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}]
        weth_contract = agent.w3.eth.contract(address=weth_address, abi=weth_abi)
        
        # Initialize Uniswap V3 router
        router_contract = initialize_uniswap_v3_router(agent)
        if not router_contract:
            raise Exception("Failed to initialize Uniswap router")
        
        # Get comprehensive initial state
        initial_balances = get_comprehensive_balances(agent, dai_contract, arb_contract, weth_contract)
        initial_health_factor = get_current_health_factor(agent)
        
        execution_results['initial_state'] = {
            'balances': initial_balances,
            'health_factor': initial_health_factor
        }
        
        print(f"\n📊 INITIAL TRADING STATE:")
        for token, balance in initial_balances.items():
            print(f"   {token}: {balance:.6f}")
        print(f"   Health Factor: {initial_health_factor:.6f}")
        
        # Execute micro swap test: ETH → ARB
        swap_amount_eth = 0.0001  # $0.47 at current prices - minimal risk
        
        print(f"\n🎯 EXECUTING MICRO SWAP TEST:")
        print(f"   Test Amount: {swap_amount_eth} ETH (~$0.47)")
        print(f"   Route: ETH → ARB via Uniswap V3")
        print(f"   Purpose: Prove real trading capability")
        
        # Execute ETH to ARB swap
        eth_to_arb_result = execute_eth_to_arb_swap(agent, router_contract, arb_contract, swap_amount_eth)
        execution_results['operations']['eth_to_arb_swap'] = eth_to_arb_result
        
        # If successful, execute reverse swap with some of the ARB
        if eth_to_arb_result.get('success') and eth_to_arb_result.get('arb_received', 0) > 0:
            arb_received = eth_to_arb_result['arb_received']
            reverse_swap_amount = arb_received * 0.5  # Use 50% for reverse test
            
            print(f"\n🔄 EXECUTING REVERSE SWAP TEST:")
            print(f"   Reverse Amount: {reverse_swap_amount:.6f} ARB")
            print(f"   Route: ARB → ETH via Uniswap V3")
            
            # Wait a bit between swaps
            time.sleep(5)
            
            # Execute ARB to ETH swap
            arb_to_eth_result = execute_arb_to_eth_swap(agent, router_contract, arb_contract, reverse_swap_amount)
            execution_results['operations']['arb_to_eth_swap'] = arb_to_eth_result
        
        # Get final state
        final_balances = get_comprehensive_balances(agent, dai_contract, arb_contract, weth_contract)
        final_health_factor = get_current_health_factor(agent)
        
        execution_results['final_state'] = {
            'balances': final_balances,
            'health_factor': final_health_factor
        }
        
        # Calculate overall results
        successful_operations = sum(1 for op in execution_results['operations'].values() if op.get('success', False))
        total_operations = len(execution_results['operations'])
        
        execution_results['successful_operations'] = successful_operations
        execution_results['total_operations'] = total_operations
        execution_results['overall_success'] = successful_operations > 0
        
        # Calculate net changes
        net_changes = {}
        for token in initial_balances:
            initial = initial_balances[token]
            final = final_balances.get(token, 0)
            net_changes[token] = final - initial
        
        execution_results['net_balance_changes'] = net_changes
        
        print(f"\n🏆 REAL TRADING IMPLEMENTATION COMPLETED")
        print("=" * 100)
        print(f"✅ Overall Success: {'YES' if execution_results['overall_success'] else 'NO'}")
        print(f"✅ Successful Operations: {successful_operations}/{total_operations}")
        
        print(f"\n💰 NET BALANCE CHANGES:")
        for token, change in net_changes.items():
            change_symbol = "+" if change >= 0 else ""
            print(f"   {token}: {change_symbol}{change:.6f}")
        
        print(f"\n📊 HEALTH FACTOR: {initial_health_factor:.6f} → {final_health_factor:.6f}")
        
        return execution_results
        
    except Exception as e:
        print(f"❌ Real trading implementation failed: {e}")
        execution_results['error'] = str(e)
        execution_results['error_details'] = traceback.format_exc()
        return execution_results
    
    finally:
        execution_results['end_time'] = datetime.now().isoformat()
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"real_trading_execution_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(execution_results, f, indent=2, default=str)
        
        print(f"\n📁 Complete execution results saved to: {filename}")

if __name__ == "__main__":
    main()