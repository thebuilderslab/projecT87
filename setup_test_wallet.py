
import os
from eth_account import Account
from web3 import Web3
from dotenv import load_dotenv

def generate_test_wallet():
    """Generate a new test wallet and display the details"""
    print("🔐 Generating new test wallet...")
    
    # Generate a new account
    account = Account.create()
    
    print(f"\n✅ Test Wallet Generated:")
    print(f"Address: {account.address}")
    print(f"Private Key: {account.key.hex()}")
    
    print(f"\n⚠️  IMPORTANT SECURITY NOTES:")
    print(f"1. This is for TESTNET ONLY - never use on mainnet")
    print(f"2. Copy the private key to your .env file")
    print(f"3. Never share or commit private keys to version control")
    print(f"4. Get test ETH from: https://sepoliafaucet.com/")
    
    return account

def test_arbitrum_connection():
    """Test connection to Arbitrum Sepolia testnet"""
    load_dotenv()
    
    # Arbitrum Sepolia RPC
    rpc_url = os.getenv('ARBITRUM_SEPOLIA_RPC', 'https://sepolia-rollup.arbitrum.io/rpc')
    
    try:
        print(f"\n🌐 Testing connection to Arbitrum Sepolia...")
        print(f"RPC URL: {rpc_url}")
        
        # Connect to the network
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Test connection
        if w3.is_connected():
            print("✅ Successfully connected to Arbitrum Sepolia!")
            
            # Get network info
            chain_id = w3.eth.chain_id
            latest_block = w3.eth.get_block('latest')
            
            print(f"Chain ID: {chain_id}")
            print(f"Latest Block: {latest_block.number}")
            print(f"Block Hash: {latest_block.hash.hex()}")
            
            return w3
        else:
            print("❌ Failed to connect to Arbitrum Sepolia")
            return None
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None

def test_wallet_connection():
    """Test wallet connection and balance check"""
    load_dotenv()
    
    private_key = os.getenv('PRIVATE_KEY')
    if not private_key or private_key == 'your_private_key_here':
        print("❌ Please set your PRIVATE_KEY in the .env file first")
        return None
    
    try:
        # Connect to network
        w3 = test_arbitrum_connection()
        if not w3:
            return None
        
        # Load account from private key
        account = Account.from_key(private_key)
        print(f"\n💰 Wallet Address: {account.address}")
        
        # Check ETH balance
        balance_wei = w3.eth.get_balance(account.address)
        balance_eth = w3.from_wei(balance_wei, 'ether')
        
        print(f"ETH Balance: {balance_eth:.6f} ETH")
        
        if balance_eth == 0:
            print("\n⚠️  Zero balance detected!")
            print("Get test ETH from: https://sepoliafaucet.com/")
            print("Then bridge to Arbitrum Sepolia: https://bridge.arbitrum.io/")
        else:
            print("✅ Wallet has test ETH - ready for transactions!")
        
        return w3, account
        
    except Exception as e:
        print(f"❌ Wallet connection error: {e}")
        return None

def main():
    """Main setup function"""
    print("🚀 Arbitrum Test Wallet Setup")
    print("=" * 40)
    
    choice = input("\nChoose an option:\n1. Generate new test wallet\n2. Test existing wallet connection\n3. Both\nEnter choice (1/2/3): ")
    
    if choice in ['1', '3']:
        generate_test_wallet()
        print(f"\n📝 Next steps:")
        print(f"1. Copy the private key to your .env file")
        print(f"2. Get test ETH from Sepolia faucet")
        print(f"3. Bridge to Arbitrum Sepolia")
        print(f"4. Run option 2 to test connection")
    
    if choice in ['2', '3']:
        print(f"\n" + "=" * 40)
        result = test_wallet_connection()
        if result:
            print("\n🎉 Setup complete! Ready for DeFi operations.")
        else:
            print("\n❌ Setup incomplete. Please check the steps above.")

if __name__ == "__main__":
    main()
