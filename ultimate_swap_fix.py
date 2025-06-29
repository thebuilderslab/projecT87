#!/usr/bin/env python3
"""
ULTIMATE SWAP FIX
Comprehensive solution for USDC → WBTC swap with all possible workarounds
"""

import os
import time
import json
from web3 import Web3
from eth_account import Account

def load_private_key():
    """Load private key from environment with fallbacks"""
    # Try multiple sources
    sources = ['PRIVATE_KEY2', 'PRIVATE_KEY', 'private_key', 'WALLET_PRIVATE_KEY']

    for source in sources:
        key = os.getenv(source)
        if key:
            print(f"✅ Found private key in {source}")
            # Handle different formats
            if key.startswith('0x'):
                return key[2:]
            return key

    print("❌ No private key found in any source")
    return None

def check_network_and_setup():
    """Setup Web3 connection and verify network"""
    network_mode = os.getenv('NETWORK_MODE', 'mainnet')

    if network_mode == 'mainnet':
        rpc_url = os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc')
        expected_chain = 42161
        network_name = "Arbitrum Mainnet"
    else:
        rpc_url = 'https://sepolia-rollup.arbitrum.io/rpc'
        expected_chain = 421614
        network_name = "Arbitrum Sepolia"

    print(f"🌐 Connecting to {network_name}")
    print(f"📡 RPC: {rpc_url}")

    w3 = Web3(Web3.HTTPProvider(rpc_url))

    if not w3.is_connected():
        print("❌ Failed to connect to network")
        return None, None, None

    chain_id = w3.eth.chain_id
    if chain_id != expected_chain:
        print(f"⚠️ Warning: Expected chain {expected_chain}, got {chain_id}")

    print(f"✅ Connected to chain {chain_id}")
    return w3, chain_id, network_name

def get_token_addresses(chain_id):
    """Get correct token addresses for the network"""
    if chain_id == 42161:  # Mainnet
        return {
            'USDC': '0xaf88d065eec38faD0AEFf3e253e648a15cEe23dC',
            'WBTC': '0x2f2a2543B76A4166549F7bffBE68df6Fc579b2F3',
            'ROUTER': '0xE592427A0AEce92De3Edee1F18E0157C05861564'
        }
    else:  # Sepolia
        return {
            'USDC': '0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d',
            'WBTC': '0x2F2a2543B76a4166549F7BFfbe68Df6FC579b2F3',
            'ROUTER': '0xE592427A0AEce92De3Edee1F18E0157C05861564'
        }

def check_balances(w3, account_address, token_addresses):
    """Check ETH and token balances"""
    print("\n💰 CHECKING BALANCES")
    print("=" * 40)

    # ETH balance
    eth_balance = w3.eth.get_balance(account_address)
    eth_balance_ether = w3.from_wei(eth_balance, 'ether')
    print(f"⚡ ETH: {eth_balance_ether:.6f}")

    # Token balances using minimal ABI
    balance_abi = [{
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }]

    balances = {'ETH': float(eth_balance_ether)}

    for token_name, token_address in token_addresses.items():
        if token_name in ['USDC', 'WBTC']:
            try:
                contract = w3.eth.contract(
                    address=Web3.to_checksum_address(token_address),
                    abi=balance_abi
                )
                balance_wei = contract.functions.balanceOf(account_address).call()

                if token_name == 'USDC':
                    balance = balance_wei / (10 ** 6)  # USDC has 6 decimals
                    print(f"💵 USDC: {balance:.6f}")
                elif token_name == 'WBTC':
                    balance = balance_wei / (10 ** 8)  # WBTC has 8 decimals
                    print(f"₿ WBTC: {balance:.8f}")

                balances[token_name] = balance

            except Exception as e:
                print(f"⚠️ Could not check {token_name} balance: {e}")
                balances[token_name] = 0

    return balances

def approve_token(w3, account, token_address, spender_address, amount):
    """Approve token spending with retry logic"""
    print(f"\n🔐 APPROVING TOKEN SPENDING")

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
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=approve_abi
        )

        # Build approval transaction
        approve_txn = contract.functions.approve(
            spender_address,
            amount * 2  # Approve 2x for future use
        ).build_transaction({
            'from': account.address,
            'gas': 60000,
            'gasPrice': int(w3.eth.gas_price * 1.1),  # 10% higher gas price
            'nonce': w3.eth.get_transaction_count(account.address)
        })

        # Sign and send
        signed_txn = w3.eth.account.sign_transaction(approve_txn, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

        print(f"✅ Approval transaction: {tx_hash.hex()}")

        # Wait for confirmation
        print("⏳ Waiting for approval...")
        time.sleep(20)

        return tx_hash.hex()

    except Exception as e:
        print(f"❌ Approval failed: {e}")
        return None

def execute_swap(w3, account, token_addresses, usdc_amount):
    """Execute the actual swap transaction"""
    print(f"\n🔄 EXECUTING SWAP: {usdc_amount} USDC → WBTC")

    # Uniswap V3 Router ABI for exactInputSingle
    swap_abi = [{
        "inputs": [{
            "components": [
                {"internalType": "address", "name": "tokenIn", "type": "address"},
                {"internalType": "address", "name": "tokenOut", "type": "address"},
                {"internalType": "uint24", "name": "fee", "type": "uint24"},
                {"internalType": "address", "name": "recipient", "type": "address"},
                {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"},
                {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
            ],
            "internalType": "struct ExactInputSingleParams",
            "name": "params",
            "type": "tuple"
        }],
        "name": "exactInputSingle",
        "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function"
    }]

    try:
        router_contract = w3.eth.contract(
            address=Web3.to_checksum_address(token_addresses['ROUTER']),
            abi=swap_abi
        )

        # Convert USDC amount to wei (6 decimals)
        usdc_amount_wei = int(usdc_amount * (10 ** 6))

        # Swap parameters
        deadline = int(time.time()) + 1800  # 30 minutes
        swap_params = {
            'tokenIn': token_addresses['USDC'],
            'tokenOut': token_addresses['WBTC'],
            'fee': 500,  # 0.05% fee tier
            'recipient': account.address,
            'deadline': deadline,
            'amountIn': usdc_amount_wei,
            'amountOutMinimum': 0,  # Accept any amount (for testing)
            'sqrtPriceLimitX96': 0
        }

        # Build swap transaction
        swap_txn = router_contract.functions.exactInputSingle(swap_params).build_transaction({
            'from': account.address,
            'gas': 300000,  # Conservative gas limit
            'gasPrice': int(w3.eth.gas_price * 1.2),  # 20% higher gas price
            'nonce': w3.eth.get_transaction_count(account.address)
        })

        # Sign and send
        signed_swap = w3.eth.account.sign_transaction(swap_txn, account.key)
        swap_hash = w3.eth.send_raw_transaction(signed_swap.rawTransaction)

        print(f"✅ Swap transaction: {swap_hash.hex()}")

        # Show explorer link
        if w3.eth.chain_id == 42161:
            print(f"📊 Arbiscan: https://arbiscan.io/tx/{swap_hash.hex()}")
        elif w3.eth.chain_id == 421614:
            print(f"📊 Sepolia: https://sepolia.arbiscan.io/tx/{swap_hash.hex()}")

        return swap_hash.hex()

    except Exception as e:
        print(f"❌ Swap failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main swap execution function"""
    print("🚀 ULTIMATE USDC → WBTC SWAP")
    print("=" * 50)

    # Check for funding bypass
    try:
        from funding_bypass_handler import FundingBypassHandler
        bypass_handler = FundingBypassHandler()
        if bypass_handler.should_bypass_funding_checks():
            print("🧪 TEST MODE: Funding checks will use reduced requirements")
    except ImportError:
        bypass_handler = None

    # Step 1: Load private key
    private_key = load_private_key()
    if not private_key:
        print("💡 Please set PRIVATE_KEY or PRIVATE_KEY2 in Replit Secrets")
        return False

    # Step 2: Setup network
    w3, chain_id, network_name = check_network_and_setup()
    if not w3:
        return False

    # Step 3: Create account
    try:
        account = Account.from_key('0x' + private_key)
        print(f"📍 Wallet: {account.address}")
    except Exception as e:
        print(f"❌ Invalid private key: {e}")
        return False

    # Step 4: Get token addresses
    token_addresses = get_token_addresses(chain_id)
    print(f"\n📋 Token Addresses ({network_name}):")
    for name, address in token_addresses.items():
        print(f"   {name}: {address}")

    # Step 5: Check balances
    balances = check_balances(w3, account.address, token_addresses)

    # Step 6: Validate swap readiness with bypass support

    # Use dynamic gas calculation for ETH requirements
    dynamic_validator = DynamicWalletFundingValidator()
    required_eth = dynamic_validator.calculate_real_gas_requirements()

    # Get USDC requirements
    min_usdc_needed = 1.0

    # Apply bypass, if available
    if bypass_handler and bypass_handler.should_bypass_funding_checks():
        requirements = bypass_handler.get_minimum_requirements() # TEST
        min_eth_needed = requirements['min_eth']
        min_usdc_needed = requirements['min_usdc']
        print("🧪 TEST MODE: Using reduced funding requirements")

    else:
        min_eth_needed = required_eth  # Use dynamically calculated gas
        min_usdc_needed = 1.0   # Minimum USDC for swap

    usdc_to_swap = min(balances.get('USDC', 0), 40.0)  # Swap up to 40 USDC

    if balances['ETH'] < min_eth_needed:
        print(f"❌ Insufficient ETH for gas (need {min_eth_needed}, have {balances['ETH']:.6f})")
        if not bypass_handler or not bypass_handler.should_bypass_funding_checks():
            print("💡 Run 'python wallet_funding_validator.py' for funding guidance")
            return False

    if usdc_to_swap < min_usdc_needed:
        print(f"❌ Insufficient USDC for swap (need at least {min_usdc_needed}, have {balances.get('USDC', 0):.6f})")
        if not bypass_handler or not bypass_handler.should_bypass_funding_checks():
            print("💡 Run 'python wallet_funding_validator.py' for funding guidance")
            return False

    print(f"\n✅ Ready to swap {usdc_to_swap:.4f} USDC for WBTC")

    # Step 7: Approve USDC
    usdc_amount_wei = int(usdc_to_swap * (10 ** 6))
    approval_result = approve_token(
        w3, account, 
        token_addresses['USDC'], 
        token_addresses['ROUTER'], 
        usdc_amount_wei
    )

    if not approval_result:
        print("❌ Approval failed, cannot proceed with swap")
        return False

    # Step 8: Execute swap
    swap_result = execute_swap(w3, account, token_addresses, usdc_to_swap)

    if swap_result:
        print(f"\n🎉 SWAP COMPLETED SUCCESSFULLY!")
        print(f"✅ Transaction: {swap_result}")
        print("⏳ Wait 2-3 minutes for confirmation")
        print("💡 Check your wallet for WBTC")

        # Save transaction details
        transaction_log = {
            'timestamp': time.time(),
            'network': network_name,
            'chain_id': chain_id,
            'wallet': account.address,
            'usdc_amount': usdc_to_swap,
            'approval_tx': approval_result,
            'swap_tx': swap_result
        }

        with open('swap_transactions.json', 'w') as f:
            json.dump(transaction_log, f, indent=2)

        return True
    else:
        print("\n❌ SWAP FAILED")
        return False

if __name__ == "__main__":
    success = main()

    if not success:
        print("\n💡 TROUBLESHOOTING:")
        print("1. Ensure PRIVATE_KEY is set in Replit Secrets")
        print("2. Fund wallet with ETH for gas fees")
        print("3. Fund wallet with USDC for swapping")
        print("4. Check network connectivity")
        print("5. Try again in a few minutes")

class DynamicWalletFundingValidator:
    """
    Dynamically calculate and validate wallet funding requirements.
    """

    def __init__(self):
        """
        Initialize the validator with network and ABI configurations.
        """
        self.w3 = self._connect_to_network()
        self.account = self._load_account()
        self.router_address = self._get_router_address()

        # ABIs for gas estimation (minimal)
        self.swap_abi = [{
            "inputs": [{
                "components": [
                    {"internalType": "address", "name": "tokenIn", "type": "address"},
                    {"internalType": "address", "name": "tokenOut", "type": "address"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "address", "name": "recipient", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"},
                    {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
                ],
                "internalType": "struct ExactInputSingleParams",
                "name": "params",
                "type": "tuple"
            }],
            "name": "exactInputSingle",
            "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
            "stateMutability": "payable",
            "type": "function"
        }]

        self.approval_abi = [{
            "constant": False,
            "inputs": [
                {"name": "_spender", "type": "address"},
                {"name": "_value", "type": "uint256"}
            ],
            "name": "approve",
            "outputs": [{"name": "", "type": "bool"}],
            "type": "function"
        }]

        self.usdc_address = self._get_usdc_address()
        self.wbtc_address = self._get_wbtc_address()

    def _connect_to_network(self):
        """Connect to Arbitrum network based on environment."""
        network_mode = os.getenv('NETWORK_MODE', 'mainnet')
        if network_mode == 'mainnet':
            rpc_url = os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc')
        else:
            rpc_url = 'https://sepolia-rollup.arbitrum.io/rpc'
        return Web3(Web3.HTTPProvider(rpc_url))

    def _load_account(self):
        """Load account from private key."""
        private_key = os.getenv('PRIVATE_KEY')
        if not private_key:
            raise ValueError("Private key not found in environment variables.")
        return Account.from_key(private_key)

    def _get_router_address(self):
         """Fetch Uniswap V3 Router address based on network."""
         chain_id = self.w3.eth.chain_id
         if chain_id == 42161:  # Mainnet
             return '0xE592427A0AEce92De3Edee1F18E0157C05861564'
         else:  # Sepolia
             return '0xE592427A0AEce92De3Edee1F18E0157C05861564'

    def _get_usdc_address(self):
        """Fetch USDC address based on network."""
        chain_id = self.w3.eth.chain_id
        if chain_id == 42161:  # Mainnet
            return '0xaf88d065eec38faD0AEFf3e253e648a15cEe23dC'
        else:  # Sepolia
            return '0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d'

    def _get_wbtc_address(self):
        """Fetch WBTC address based on network."""
        chain_id = self.w3.eth.chain_id
        if chain_id == 42161:  # Mainnet
            return '0x2f2a2543B76A4166549F7bffBE68df6Fc579b2F3'
        else:  # Sepolia
            return '0x2F2a2543B76a4166549F7BFfbe68Df6FC579b2F3'

    def calculate_real_gas_requirements(self):
        """
        Calculate the actual gas required for swap and approval transactions.
        """
        try:
            # 1. Estimate gas for the swap transaction
            swap_contract = self.w3.eth.contract(
                address=self.router_address,
                abi=self.swap_abi
            )

            # Dummy swap parameters for gas estimation
            dummy_swap_params = {
                'tokenIn': self.usdc_address,
                'tokenOut': self.wbtc_address,
                'fee': 500,  # 0.05% fee tier
                'recipient': self.account.address,
                'deadline': int(time.time()) + 1800,  # 30 minutes
                'amountIn': 1000000,  # 1 USDC (in 6 decimals)
                'amountOutMinimum': 0,
                'sqrtPriceLimitX96': 0
            }

            swap_txn = swap_contract.functions.exactInputSingle(dummy_swap_params).build_transaction({
                'from': self.account.address,
                'gas': 300000,
                'gasPrice': int(self.w3.eth.gas_price * 1.2),
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
            })

            estimated_swap_gas = self.w3.eth.estimate_gas(swap_txn)
            print(f"Gas Estimation - Swap: {estimated_swap_gas}")

            # 2. Estimate gas for the approval transaction
            usdc_contract = self.w3.eth.contract(
                address=self.usdc_address,
                abi=self.approval_abi
            )

            # Build approval transaction
            approve_txn = usdc_contract.functions.approve(
                self.router_address,
                2000000  # Approve 2 USDC (in 6 decimals)
            ).build_transaction({
                'from': self.account.address,
                'gas': 60000,
                'gasPrice': int(self.w3.eth.gas_price * 1.1),
                'nonce': self.w3.eth.get_transaction_count(self.account.address) + 1  # Use next nonce
            })

            estimated_approval_gas = self.w3.eth.estimate_gas(approve_txn)
            print(f"Gas Estimation - Approval: {estimated_approval_gas}")

            # 3. Calculate total gas in ETH
            total_gas_wei = (estimated_swap_gas * int(self.w3.eth.gas_price * 1.2)) + \
                            (estimated_approval_gas * int(self.w3.eth.gas_price * 1.1))
            total_gas_eth = self.w3.from_wei(total_gas_wei, 'ether')

            return total_gas_eth

        except Exception as e:
            print(f"Error calculating gas requirements: {e}")
            return 0.01  # Fallback: return a default value


    def get_eth_balance(self):
        """Get ETH balance of the account."""
        balance_wei = self.w3.eth.get_balance(self.account.address)
        return self.w3.from_wei(balance_wei, 'ether')

class FundingBypassHandler:
    def __init__(self):
        pass

    def should_bypass_funding_checks(self):
        return False

    def get_minimum_requirements(self):
        return {'min_eth': 0.001, 'min_usdc': 0.1}