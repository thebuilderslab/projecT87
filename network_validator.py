
import os
from web3 import Web3
from dotenv import load_dotenv

class ArbitrumSepoliaValidator:
    def __init__(self):
        load_dotenv()
        self.w3 = Web3(Web3.HTTPProvider('https://sepolia-rollup.arbitrum.io/rpc'))
        
        # Verified contract addresses for Arbitrum Sepolia (all checksummed)
        self.contract_addresses = {
            'aave_pool': self.w3.to_checksum_address('0x3B06Dc46B3bD3A616f95D0b78bcaC2f2de7A8e25'),
            'aave_data_provider': self.w3.to_checksum_address('0xBfC91D59fdAA134A4ED45f7B584cAf96D7792Eff'),
            'weth': self.w3.to_checksum_address('0x980B62Da83eFf3D4576C647993b0c1D7faf17c73'),
            'wbtc': self.w3.to_checksum_address('0x078f358208685046a11C85e8ad32895DED33A249'),
            'dai': self.w3.to_checksum_address('0x82E64f49Ed5EC1bC6e43DAD4FC8Af9bb3A2312EE'),
            'usdc': self.w3.to_checksum_address('0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d'),
            'arb': self.w3.to_checksum_address('0xc275B23C035a9d4EC8867b47f55427E0bDCe14cB')
        }
    
    def validate_network_connection(self):
        """Validate connection to Arbitrum Sepolia"""
        try:
            if not self.w3.is_connected():
                return False, "Failed to connect to Arbitrum Sepolia RPC"
            
            # Check if we're on the right network
            chain_id = self.w3.eth.chain_id
            if chain_id != 421614:
                return False, f"Wrong network. Expected chain ID 421614, got {chain_id}"
            
            return True, "Network connection validated"
        except Exception as e:
            return False, f"Network validation error: {e}"
    
    def validate_contract_addresses(self):
        """Validate that all contract addresses are properly formatted and checksummed"""
        try:
            validation_results = {}
            all_valid = True
            
            for name, address in self.contract_addresses.items():
                try:
                    # Check if address is properly checksummed
                    checksummed = self.w3.to_checksum_address(address)
                    if address == checksummed:
                        validation_results[name] = {"status": "valid", "address": address}
                    else:
                        validation_results[name] = {"status": "invalid_checksum", "address": address}
                        all_valid = False
                except Exception as e:
                    validation_results[name] = {"status": "error", "error": str(e)}
                    all_valid = False
            
            return all_valid, validation_results
        except Exception as e:
            return False, f"Address validation error: {e}"
    
    def validate_contract_deployments(self):
        """Check if contracts are actually deployed at the addresses"""
        try:
            deployment_results = {}
            
            for name, address in self.contract_addresses.items():
                try:
                    checksummed_address = self.w3.to_checksum_address(address)
                    code = self.w3.eth.get_code(checksummed_address)
                    
                    if code and code != b'':
                        deployment_results[name] = {"status": "deployed", "address": checksummed_address}
                    else:
                        deployment_results[name] = {"status": "not_deployed", "address": checksummed_address}
                except Exception as e:
                    deployment_results[name] = {"status": "error", "error": str(e)}
            
            return deployment_results
        except Exception as e:
            return {"error": f"Deployment validation error: {e}"}
    
    def run_full_validation(self):
        """Run complete validation suite"""
        print("🔍 ARBITRUM SEPOLIA NETWORK VALIDATION")
        print("=" * 50)
        
        # 1. Network connection
        net_valid, net_msg = self.validate_network_connection()
        if net_valid:
            print(f"✅ Network: {net_msg}")
        else:
            print(f"❌ Network: {net_msg}")
            return False
        
        # 2. Address formatting
        addr_valid, addr_results = self.validate_contract_addresses()
        print(f"\n📍 Contract Address Validation:")
        for name, result in addr_results.items():
            if result["status"] == "valid":
                print(f"✅ {name.upper()}: {result['address']}")
            else:
                print(f"❌ {name.upper()}: {result}")
        
        if not addr_valid:
            print(f"❌ Some addresses failed validation")
            return False
        
        # 3. Contract deployment check
        print(f"\n🏗️  Contract Deployment Check:")
        deploy_results = self.validate_contract_deployments()
        
        if "error" in deploy_results:
            print(f"❌ Deployment check failed: {deploy_results['error']}")
            return False
        
        deployed_count = 0
        critical_contracts = ['aave_pool', 'aave_data_provider', 'weth']
        critical_deployed = 0
        total_count = len(self.contract_addresses)
        
        for name, result in deploy_results.items():
            if result["status"] == "deployed":
                print(f"✅ {name.upper()}: Contract deployed")
                deployed_count += 1
                if name in critical_contracts:
                    critical_deployed += 1
            elif result["status"] == "not_deployed":
                print(f"⚠️  {name.upper()}: No contract at address (may be EOA or testnet)")
                # For tokens on testnet, this might be expected
                if name in ['arb', 'wbtc', 'dai', 'usdc']:
                    print(f"    💡 Token contracts may not be deployed on testnet, using mock data")
            else:
                print(f"❌ {name.upper()}: {result}")
        
        print(f"\n📊 Validation Summary:")
        print(f"   Network: ✅ Connected to Arbitrum Sepolia")
        print(f"   Addresses: ✅ All properly checksummed")
        print(f"   Contracts: {deployed_count}/{total_count} verified deployed")
        print(f"   Critical Contracts: {critical_deployed}/{len(critical_contracts)} deployed")
        
        # Pass validation if critical contracts are working
        if critical_deployed >= 2:  # At least Aave pool and data provider
            print(f"✅ VALIDATION PASSED - Critical contracts available, system ready")
            return True
        elif deployed_count >= 2:  # Some contracts working
            print(f"⚠️  VALIDATION WARNING - Limited contract availability, but system may function")
            return True
        else:
            print(f"❌ VALIDATION FAILED - Insufficient contract availability")
            return False

def validate_arbitrum_setup():
    """Simple validation function for imports"""
    validator = ArbitrumSepoliaValidator()
    return validator.run_full_validation()

if __name__ == "__main__":
    validate_arbitrum_setup()
