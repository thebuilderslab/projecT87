
import os
import json
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

class AaveArbitrumIntegration:
    def __init__(self, w3, account):
        self.w3 = w3
        self.account = account
        self.address = account.address
        
        # Aave V3 Arbitrum Sepolia Contract Addresses (Updated working addresses)
        self.pool_address = self.w3.to_checksum_address("0x3B06Dc46B3bD3A616f95D0b78bcaC2f2de7A8e25")  # Aave V3 Pool (verified)
        self.pool_data_provider = self.w3.to_checksum_address("0x2F9D57E97C3DFED8676e605BC504a48E0c5917E9")  # Pool Data Provider (working)
        self.weth_address = self.w3.to_checksum_address("0x980B62Da83eFf3D4576C647993b0c1D7faf17c73")  # WETH on Arbitrum Sepolia (verified)
        self.usdc_address = self.w3.to_checksum_address("0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d")  # USDC on Arbitrum Sepolia (verified)
        
        # Load ABIs
        self.pool_abi = self._get_pool_abi()
        self.erc20_abi = self._get_erc20_abi()
        
        # Initialize contracts
        self.pool_contract = self.w3.eth.contract(
            address=self.pool_address, 
            abi=self.pool_abi
        )
        
        print(f"🏦 Aave integration initialized for {self.address}")
    
    def _get_pool_abi(self):
        """Aave V3 Pool ABI (simplified for key functions)"""
        return [
            {
                "inputs": [
                    {"internalType": "address", "name": "asset", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "address", "name": "onBehalfOf", "type": "address"},
                    {"internalType": "uint16", "name": "referralCode", "type": "uint16"}
                ],
                "name": "supply",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "address", "name": "asset", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "uint256", "name": "interestRateMode", "type": "uint256"},
                    {"internalType": "uint16", "name": "referralCode", "type": "uint16"},
                    {"internalType": "address", "name": "onBehalfOf", "type": "address"}
                ],
                "name": "borrow",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "address", "name": "asset", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "address", "name": "to", "type": "address"}
                ],
                "name": "withdraw",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "address", "name": "asset", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "uint256", "name": "interestRateMode", "type": "uint256"},
                    {"internalType": "address", "name": "onBehalfOf", "type": "address"}
                ],
                "name": "repay",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
    
    def _get_erc20_abi(self):
        """Standard ERC20 ABI for token operations"""
        return [
            {
                "inputs": [
                    {"internalType": "address", "name": "spender", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"}
                ],
                "name": "approve",
                "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "decimals",
                "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
    
    def get_token_balance(self, token_address):
        """Get token balance for the wallet"""
        try:
            # Ensure all addresses are properly checksummed
            token_address = self.w3.to_checksum_address(token_address)
            
            if hasattr(self.account, 'address'):
                user_address = self.w3.to_checksum_address(self.account.address)
            else:
                user_address = self.w3.to_checksum_address(self.account.address if hasattr(self.account, 'address') else str(self.account))
            
            if token_address == self.weth_address:
                # For WETH, check both ETH and WETH balance
                eth_balance = self.w3.eth.get_balance(user_address)
                return float(self.w3.from_wei(eth_balance, 'ether'))
            else:
                token_contract = self.w3.eth.contract(address=token_address, abi=self.erc20_abi)
                balance = token_contract.functions.balanceOf(user_address).call()
                decimals = token_contract.functions.decimals().call()
                return float(balance) / float(10 ** decimals)
        except Exception as e:
            print(f"❌ Failed to get token balance: {e}")
            return 0.0
    
    def approve_token(self, token_address, amount):
        """Approve token spending for Aave"""
        try:
            # Ensure all addresses are properly checksummed
            token_address = self.w3.to_checksum_address(token_address)
            
            if hasattr(self.account, 'address'):
                user_address = self.w3.to_checksum_address(self.account.address)
            else:
                user_address = self.w3.to_checksum_address(self.address)
                
            token_contract = self.w3.eth.contract(address=token_address, abi=self.erc20_abi)
            decimals = token_contract.functions.decimals().call()
            amount_wei = int(float(amount) * (10 ** decimals))
            
            # Build approval transaction
            nonce = self.w3.eth.get_transaction_count(user_address)
            transaction = token_contract.functions.approve(
                self.pool_address, 
                amount_wei
            ).build_transaction({
                'chainId': self.w3.eth.chain_id,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce,
            })
            
            # Sign and send
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            print(f"✅ Token approval sent: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            print(f"❌ Approval failed: {e}")
            return None
    
    def supply_to_aave(self, token_address, amount):
        """Supply assets to Aave for lending"""
        try:
            print(f"🏦 Supplying {amount} tokens to Aave...")
            
            # First approve token spending
            approval_tx = self.approve_token(token_address, amount)
            if not approval_tx:
                return None
            
            # Wait for approval (in production, you'd wait for confirmation)
            import time
            time.sleep(3)
            
            # Convert amount to wei
            if token_address == self.weth_address:
                amount_wei = self.w3.to_wei(amount, 'ether')
            else:
                token_contract = self.w3.eth.contract(address=token_address, abi=self.erc20_abi)
                decimals = token_contract.functions.decimals().call()
                amount_wei = int(amount * (10 ** decimals))
            
            # Build supply transaction
            user_address = self.w3.to_checksum_address(self.address)
            nonce = self.w3.eth.get_transaction_count(user_address)
            transaction = self.pool_contract.functions.supply(
                self.w3.to_checksum_address(token_address),    # asset
                amount_wei,       # amount
                user_address,     # onBehalfOf
                0                 # referralCode
            ).build_transaction({
                'chainId': self.w3.eth.chain_id,
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce,
            })
            
            # Sign and send
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            print(f"✅ Supply transaction sent: {tx_hash.hex()}")
            print(f"📊 Explorer: https://sepolia.arbiscan.io/tx/{tx_hash.hex()}")
            
            return tx_hash.hex()
            
        except Exception as e:
            print(f"❌ Supply failed: {e}")
            return None
    
    def borrow_from_aave(self, token_address, amount, interest_rate_mode=2):
        """Borrow assets from Aave (interest_rate_mode: 1=stable, 2=variable)"""
        try:
            print(f"💰 Borrowing {amount} tokens from Aave...")
            
            # Convert amount to wei
            if token_address == self.weth_address:
                amount_wei = self.w3.to_wei(amount, 'ether')
            else:
                token_contract = self.w3.eth.contract(address=token_address, abi=self.erc20_abi)
                decimals = token_contract.functions.decimals().call()
                amount_wei = int(amount * (10 ** decimals))
            
            # Build borrow transaction
            user_address = self.w3.to_checksum_address(self.address)
            nonce = self.w3.eth.get_transaction_count(user_address)
            transaction = self.pool_contract.functions.borrow(
                self.w3.to_checksum_address(token_address),         # asset
                amount_wei,           # amount
                interest_rate_mode,   # interestRateMode (2 = variable)
                0,                    # referralCode
                user_address          # onBehalfOf
            ).build_transaction({
                'chainId': self.w3.eth.chain_id,
                'gas': 400000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce,
            })
            
            # Sign and send
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            print(f"✅ Borrow transaction sent: {tx_hash.hex()}")
            print(f"📊 Explorer: https://sepolia.arbiscan.io/tx/{tx_hash.hex()}")
            
            return tx_hash.hex()
            
        except Exception as e:
            print(f"❌ Borrow failed: {e}")
            return None
    
    def repay_to_aave(self, token_address, amount, interest_rate_mode=2):
        """Repay borrowed assets to Aave"""
        try:
            print(f"💳 Repaying {amount} tokens to Aave...")
            
            # First approve token spending
            approval_tx = self.approve_token(token_address, amount)
            if not approval_tx:
                return None
            
            import time
            time.sleep(3)
            
            # Convert amount to wei
            if token_address == self.weth_address:
                amount_wei = self.w3.to_wei(amount, 'ether')
            else:
                token_contract = self.w3.eth.contract(address=token_address, abi=self.erc20_abi)
                decimals = token_contract.functions.decimals().call()
                amount_wei = int(amount * (10 ** decimals))
            
            # Build repay transaction
            user_address = self.w3.to_checksum_address(self.address)
            nonce = self.w3.eth.get_transaction_count(user_address)
            transaction = self.pool_contract.functions.repay(
                self.w3.to_checksum_address(token_address),         # asset
                amount_wei,           # amount
                interest_rate_mode,   # interestRateMode
                user_address          # onBehalfOf
            ).build_transaction({
                'chainId': self.w3.eth.chain_id,
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce,
            })
            
            # Sign and send
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            print(f"✅ Repay transaction sent: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            print(f"❌ Repay failed: {e}")
            return None
    
    def execute_yield_strategy(self, strategy_type="conservative"):
        """Execute automated yield farming strategies"""
        print(f"🚀 Executing {strategy_type} yield strategy...")
        
        eth_balance = self.get_token_balance(self.weth_address)
        
        if eth_balance < 0.01:
            print("❌ Insufficient ETH balance for yield strategy")
            return None
        
        if strategy_type == "conservative":
            # Supply 50% of ETH to Aave for lending yield
            supply_amount = eth_balance * 0.5
            return self.supply_to_aave(self.weth_address, supply_amount)
            
        elif strategy_type == "leveraged":
            # 1. Supply ETH as collateral
            supply_amount = eth_balance * 0.7
            supply_tx = self.supply_to_aave(self.weth_address, supply_amount)
            
            if supply_tx:
                # 2. Borrow USDC against ETH collateral (at 50% LTV)
                import time
                time.sleep(5)  # Wait for supply to confirm
                
                # Estimate USDC borrow amount (assuming 1 ETH = $2000, borrow 50% LTV)
                usdc_borrow_amount = supply_amount * 2000 * 0.5  # 50% LTV
                borrow_tx = self.borrow_from_aave(self.usdc_address, usdc_borrow_amount)
                
                return {"supply": supply_tx, "borrow": borrow_tx}
        
        return None
