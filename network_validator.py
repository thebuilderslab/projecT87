
import os
import json
from web3 import Web3
from dotenv import load_dotenv

class NetworkValidator:
    def __init__(self):
        load_dotenv()
        self.rpc_url = os.getenv('ARBITRUM_SEPOLIA_RPC', 'https://sepolia-rollup.arbitrum.io/rpc')
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
    def validate_contracts(self):
        """Validate that all required contracts exist on the network"""
        contracts_to_check = {
            "Aave Pool": "0xBfC91D59fdAA134A4ED45f7B584cAf96D7792Eff",
            "Aave Data Provider": "0x2F9D57E97C3DFED8676e605BC504a48E0c5917E9", 
            "WETH": "0x980B62Da83eFf3D4576C647993b0c1D7faf17c73",
            "USDC": "0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d",
            "ARB": "0x912CE59144191C1204E64559FE8253a0e49E6548",
            "Uniswap Router": "0x101F443B4d1b059569D643917553c771E1b9663E"
        }
        
        print("🔍 VALIDATING ARBITRUM SEPOLIA CONTRACTS:")
        print("=" * 50)
        
        all_valid = True
        for name, address in contracts_to_check.items():
            try:
                checksummed = self.w3.to_checksum_address(address)
                code = self.w3.eth.get_code(checksummed)
                
                if code and code != b'':
                    print(f"✅ {name}: {checksummed}")
                else:
                    print(f"❌ {name}: {checksummed} (NO CONTRACT)")
                    all_valid = False
                    
            except Exception as e:
                print(f"❌ {name}: {address} (ERROR: {e})")
                all_valid = False
        
        return all_valid
    
    def get_wallet_balances(self, wallet_address):
        """Check wallet balances for key tokens"""
        try:
            wallet = self.w3.to_checksum_address(wallet_address)
            
            # ETH balance
            eth_balance = self.w3.eth.get_balance(wallet)
            eth_formatted = self.w3.from_wei(eth_balance, 'ether')
            
            print(f"\n💰 WALLET BALANCES: {wallet}")
            print("=" * 50)
            print(f"ETH: {eth_formatted:.6f}")
            
            # Check if we have enough for gas
            if eth_formatted < 0.01:
                print("⚠️  Low ETH balance - may not be enough for transactions")
                
            return float(eth_formatted)
            
        except Exception as e:
            print(f"❌ Error checking balances: {e}")
            return 0.0

if __name__ == "__main__":
    validator = NetworkValidator()
    
    print("🌐 ARBITRUM SEPOLIA NETWORK VALIDATION")
    print("=" * 50)
    
    # Check connection
    if validator.w3.is_connected():
        print(f"✅ Connected to Arbitrum Sepolia")
        print(f"📡 Chain ID: {validator.w3.eth.chain_id}")
        print(f"📦 Latest Block: {validator.w3.eth.get_block('latest').number}")
    else:
        print("❌ Failed to connect to network")
        exit(1)
    
    # Validate contracts
    contracts_valid = validator.validate_contracts()
    
    # Check wallet if .env exists
    if os.path.exists('.env'):
        from eth_account import Account
        private_key = os.getenv('PRIVATE_KEY')
        if private_key and private_key != 'your_private_key_here':
            account = Account.from_key(private_key)
            validator.get_wallet_balances(account.address)
    
    if contracts_valid:
        print("\n🎉 All systems ready for DeFi operations!")
    else:
        print("\n❌ Contract validation failed - please update addresses")
