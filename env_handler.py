
import os
import subprocess
from dotenv import load_dotenv

def setup_environment():
    """Setup environment variables with fallbacks"""
    load_dotenv()
    
    # Critical secrets that must be linked from Replit Secrets
    critical_secrets = [
        'ZAPPER_API_KEY',
        'ARBITRUM_RPC_URL', 
        'PRIVATE_KEY',
        'PROMPT_KEY',
        'OPTIMIZER_API_KEY',
        'ARBISCAN_API_KEY',
        'NETWORK_MODE',
        'COINMARKETCAP_API_KEY',
        'PRIVATE_KEY2'
    ]
    
    # Force load from Replit secrets if in deployment
    if os.getenv('REPLIT_DEPLOYMENT'):
        try:
            result = subprocess.run(['printenv'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if '=' in line and line.strip():
                        key, value = line.split('=', 1)
                        if key in critical_secrets:
                            os.environ[key] = value
        except:
            pass

    # Set defaults for missing secrets
    if not os.getenv('NETWORK_MODE'):
        os.environ['NETWORK_MODE'] = 'mainnet'
    
    if os.getenv('TENDERLY_RPC_URL'):
        os.environ.setdefault('ARBITRUM_RPC_URL', os.environ['TENDERLY_RPC_URL'])
    elif not os.getenv('ARBITRUM_RPC_URL'):
        if os.getenv('NETWORK_MODE') == 'mainnet':
            os.environ['ARBITRUM_RPC_URL'] = 'https://arb1.arbitrum.io/rpc'
        else:
            os.environ['ARBITRUM_RPC_URL'] = 'https://sepolia-rollup.arbitrum.io/rpc'

    if not os.getenv('ARB_RPC_URL'):
        os.environ['ARB_RPC_URL'] = os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc')

def get_private_key():
    """Get private key with fallback logic"""
    setup_environment()
    return os.getenv('PRIVATE_KEY2') or os.getenv('PRIVATE_KEY') or '0x' + '0' * 64

def get_wallet_address():
    """Get wallet address from private key"""
    from eth_account import Account
    try:
        private_key = get_private_key()
        if private_key and len(private_key) >= 64:
            account = Account.from_key(private_key)
            return account.address
        return '0x' + '0' * 40
    except:
        return '0x' + '0' * 40
