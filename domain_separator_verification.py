#!/usr/bin/env python3
"""
DOMAIN SEPARATOR VERIFICATION SCRIPT
Comprehensive verification of EIP-712 parameters for Aave debt tokens on Arbitrum mainnet
"""

import os
import json
import time
from typing import Dict, Tuple, Optional
from web3 import Web3
from eth_abi import encode
import hashlib

class DomainSeparatorVerifier:
    """Comprehensive verification of EIP-712 domain parameters for Aave debt tokens"""
    
    def __init__(self):
        print("🔍 DOMAIN SEPARATOR VERIFICATION SCRIPT")
        print("=" * 60)
        print("🎯 OBJECTIVE: Verify EIP-712 parameters for Aave debt tokens")
        print("📍 NETWORK: Arbitrum One (Chain ID: 42161)")
        print("=" * 60)
        
        # Connect to Arbitrum mainnet
        self.rpc_urls = [
            "https://arbitrum-one.public.blastapi.io",
            "https://arb1.arbitrum.io/rpc",
            "https://arbitrum-mainnet.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161"
        ]
        
        self.w3 = None
        self.chain_id = 42161
        
        # Initialize Web3 connection
        self._connect_to_arbitrum()
        
        # Aave contract addresses
        self.aave_data_provider = "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654"
        self.paraswap_debt_adapter = "0xAE9f94BD98eC2831a1330e0418bE0fDb5C95C2B9"
        
        # Test tokens
        self.tokens = {
            'DAI': "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
            'ARB': "0x912CE59144191C1204E64559FE8253a0e49E6548",
            'WETH': "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
            'USDC': "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
        }
        
        # EIP-712 domain type hash
        self.domain_type_hash = self.w3.keccak(text="EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)")
        
        print(f"✅ Connected to Arbitrum via {self.w3.provider.endpoint_uri}")
        print(f"   Block number: {self.w3.eth.block_number}")
        print(f"   Chain ID: {self.w3.eth.chain_id}")
        print()
    
    def _connect_to_arbitrum(self):
        """Connect to Arbitrum with fallback RPCs"""
        for rpc_url in self.rpc_urls:
            try:
                w3 = Web3(Web3.HTTPProvider(rpc_url))
                if w3.is_connected() and w3.eth.chain_id == self.chain_id:
                    self.w3 = w3
                    return
            except Exception as e:
                print(f"⚠️ Failed to connect to {rpc_url}: {e}")
                continue
        
        raise Exception("Failed to connect to Arbitrum mainnet")
    
    def get_debt_token_address(self, asset_symbol: str) -> str:
        """Get variable debt token address for an asset"""
        try:
            asset_address = self.tokens.get(asset_symbol.upper())
            if not asset_address:
                raise ValueError(f"Unknown asset: {asset_symbol}")
            
            # Aave Protocol Data Provider ABI
            data_provider_abi = [{
                "inputs": [{"name": "asset", "type": "address"}],
                "name": "getReserveTokensAddresses",
                "outputs": [
                    {"name": "aTokenAddress", "type": "address"},
                    {"name": "stableDebtTokenAddress", "type": "address"},
                    {"name": "variableDebtTokenAddress", "type": "address"}
                ],
                "stateMutability": "view",
                "type": "function"
            }]
            
            data_provider_contract = self.w3.eth.contract(
                address=self.aave_data_provider, 
                abi=data_provider_abi
            )
            
            # Get debt token addresses
            token_addresses = data_provider_contract.functions.getReserveTokensAddresses(asset_address).call()
            variable_debt_token = token_addresses[2]
            
            print(f"📋 {asset_symbol} variable debt token: {variable_debt_token}")
            return variable_debt_token
            
        except Exception as e:
            print(f"❌ Error getting debt token address for {asset_symbol}: {e}")
            return ""
    
    def query_debt_token_parameters(self, debt_token_address: str) -> Dict:
        """Query all EIP-712 relevant parameters from a debt token contract"""
        print(f"\n🔍 QUERYING DEBT TOKEN: {debt_token_address}")
        print("=" * 50)
        
        # Comprehensive debt token ABI for EIP-712 parameters
        debt_token_abi = [
            {"inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "stateMutability": "view", "type": "function"},
            {"inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "stateMutability": "view", "type": "function"},
            {"inputs": [], "name": "version", "outputs": [{"name": "", "type": "string"}], "stateMutability": "view", "type": "function"},
            {"inputs": [], "name": "DOMAIN_SEPARATOR", "outputs": [{"name": "", "type": "bytes32"}], "stateMutability": "view", "type": "function"},
            {"inputs": [{"name": "owner", "type": "address"}], "name": "nonces", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
            {"inputs": [{"name": "owner", "type": "address"}], "name": "delegationNonces", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
            {"inputs": [], "name": "DELEGATION_WITH_SIG_TYPEHASH", "outputs": [{"name": "", "type": "bytes32"}], "stateMutability": "view", "type": "function"}
        ]
        
        contract = self.w3.eth.contract(address=debt_token_address, abi=debt_token_abi)
        
        results = {
            'debt_token_address': debt_token_address,
            'chain_id': self.chain_id
        }
        
        # Query each parameter with error handling
        parameter_queries = [
            ('name', 'name'),
            ('symbol', 'symbol'),
            ('version', 'version'),
            ('domain_separator', 'DOMAIN_SEPARATOR'),
            ('delegation_typehash', 'DELEGATION_WITH_SIG_TYPEHASH')
        ]
        
        for key, method_name in parameter_queries:
            try:
                result = getattr(contract.functions, method_name)().call()
                results[key] = result
                
                if key == 'domain_separator':
                    print(f"   📝 {key}: {result.hex()}")
                elif key == 'delegation_typehash':
                    print(f"   🔗 {key}: {result.hex()}")
                else:
                    print(f"   📝 {key}: {result}")
                    
            except Exception as e:
                results[key] = None
                print(f"   ❌ {key}: Not available ({e})")
        
        # Test nonce methods
        test_address = "0x0000000000000000000000000000000000000001"
        nonce_methods = [
            ('nonces', 'nonces'),
            ('delegation_nonces', 'delegationNonces')
        ]
        
        print(f"\n🧪 Testing nonce methods with address {test_address}:")
        for key, method_name in nonce_methods:
            try:
                nonce = getattr(contract.functions, method_name)(test_address).call()
                results[key] = method_name
                print(f"   ✅ {key}: Method '{method_name}' works (returned: {nonce})")
            except Exception as e:
                results[key] = None
                print(f"   ❌ {key}: Method '{method_name}' failed ({e})")
        
        return results
    
    def calculate_domain_separator(self, name: str, version: str, chain_id: int, verifying_contract: str) -> bytes:
        """Calculate EIP-712 domain separator hash"""
        try:
            # Encode domain parameters
            name_hash = self.w3.keccak(text=name)
            version_hash = self.w3.keccak(text=version)
            
            # Pack domain separator
            domain_separator = self.w3.keccak(encode(
                ['bytes32', 'bytes32', 'bytes32', 'uint256', 'address'],
                [
                    self.domain_type_hash,
                    name_hash,
                    version_hash,
                    chain_id,
                    self.w3.to_checksum_address(verifying_contract)
                ]
            ))
            
            return domain_separator
            
        except Exception as e:
            print(f"❌ Error calculating domain separator: {e}")
            return b""
    
    def verify_domain_separator(self, token_params: Dict) -> Dict:
        """Verify our calculated domain separator against contract's"""
        print(f"\n🔬 DOMAIN SEPARATOR VERIFICATION")
        print("=" * 50)
        
        verification_results = {
            'token_address': token_params['debt_token_address'],
            'verification_passed': False,
            'parameter_matches': {},
            'calculated_domain_separator': None,
            'contract_domain_separator': token_params.get('domain_separator'),
            'recommended_parameters': {}
        }
        
        # Try different version values commonly used by Aave
        version_candidates = ['1', '2', '1.0', '2.0']
        
        if not token_params.get('name'):
            print("❌ Cannot verify: No token name available")
            return verification_results
        
        token_name = token_params['name']
        contract_domain_sep = token_params.get('domain_separator')
        
        print(f"📝 Token Name: {token_name}")
        print(f"📝 Contract Domain Separator: {contract_domain_sep.hex() if contract_domain_sep else 'Not available'}")
        print()
        
        # Test with known version from contract or try candidates
        if token_params.get('version'):
            version_candidates = [token_params['version']] + version_candidates
        
        for version in version_candidates:
            calculated = self.calculate_domain_separator(
                name=token_name,
                version=version,
                chain_id=self.chain_id,
                verifying_contract=token_params['debt_token_address']
            )
            
            if calculated:
                print(f"🧮 Calculated with version '{version}': {calculated.hex()}")
                
                if contract_domain_sep and calculated == contract_domain_sep:
                    print(f"✅ MATCH FOUND! Version '{version}' produces correct domain separator")
                    verification_results['verification_passed'] = True
                    verification_results['calculated_domain_separator'] = calculated
                    verification_results['recommended_parameters'] = {
                        'name': token_name,
                        'version': version,
                        'chainId': self.chain_id,
                        'verifyingContract': token_params['debt_token_address']
                    }
                    break
                else:
                    print(f"❌ No match with version '{version}'")
        
        if not verification_results['verification_passed'] and contract_domain_sep:
            print(f"\n⚠️ No matching domain separator found!")
            print(f"   Contract expects: {contract_domain_sep.hex()}")
            print(f"   Consider manual verification of domain parameters")
        elif not contract_domain_sep:
            print(f"\n⚠️ Cannot verify: Contract doesn't expose DOMAIN_SEPARATOR method")
            # Provide best guess parameters
            version = token_params.get('version', '1')
            verification_results['recommended_parameters'] = {
                'name': token_name,
                'version': version,
                'chainId': self.chain_id,
                'verifyingContract': token_params['debt_token_address']
            }
            verification_results['calculated_domain_separator'] = self.calculate_domain_separator(
                token_name, version, self.chain_id, token_params['debt_token_address']
            )
        
        return verification_results
    
    def verify_delegation_typehash(self, token_params: Dict) -> Dict:
        """Verify the DELEGATION_WITH_SIG_TYPEHASH"""
        print(f"\n🔗 DELEGATION TYPEHASH VERIFICATION")
        print("=" * 50)
        
        # Known DelegationWithSig type structures
        delegation_types = {
            'standard': "DelegationWithSig(address delegatee,uint256 value,uint256 nonce,uint256 deadline)",
            'with_delegator': "DelegationWithSig(address delegator,address delegatee,uint256 value,uint256 nonce,uint256 deadline)"
        }
        
        contract_typehash = token_params.get('delegation_typehash')
        
        if not contract_typehash:
            print("❌ Cannot verify: Contract doesn't expose DELEGATION_WITH_SIG_TYPEHASH")
            return {'typehash_verified': False, 'recommended_type': 'with_delegator'}
        
        print(f"📝 Contract DELEGATION_WITH_SIG_TYPEHASH: {contract_typehash.hex()}")
        print()
        
        for type_name, type_string in delegation_types.items():
            calculated_hash = self.w3.keccak(text=type_string)
            print(f"🧮 {type_name}: {type_string}")
            print(f"   Hash: {calculated_hash.hex()}")
            
            if calculated_hash == contract_typehash:
                print(f"   ✅ MATCH! Use '{type_name}' structure")
                return {
                    'typehash_verified': True, 
                    'recommended_type': type_name,
                    'type_string': type_string,
                    'calculated_hash': calculated_hash
                }
            else:
                print(f"   ❌ No match")
            print()
        
        print(f"⚠️ No matching delegation type found!")
        return {'typehash_verified': False, 'recommended_type': 'with_delegator'}
    
    def run_comprehensive_verification(self):
        """Run comprehensive verification for all supported tokens"""
        print("\n🚀 COMPREHENSIVE DOMAIN SEPARATOR VERIFICATION")
        print("=" * 70)
        
        results = {}
        
        # Test tokens to verify
        test_tokens = ['DAI', 'ARB']
        
        for token_symbol in test_tokens:
            print(f"\n{'='*20} {token_symbol} VERIFICATION {'='*20}")
            
            # Get debt token address
            debt_token_address = self.get_debt_token_address(token_symbol)
            if not debt_token_address:
                results[token_symbol] = {'error': 'Failed to get debt token address'}
                continue
            
            # Query token parameters
            token_params = self.query_debt_token_parameters(debt_token_address)
            
            # Verify domain separator
            domain_verification = self.verify_domain_separator(token_params)
            
            # Verify delegation typehash
            typehash_verification = self.verify_delegation_typehash(token_params)
            
            # Combine results
            results[token_symbol] = {
                'debt_token_address': debt_token_address,
                'token_parameters': token_params,
                'domain_verification': domain_verification,
                'typehash_verification': typehash_verification
            }
        
        # Generate final report
        self.generate_verification_report(results)
        
        return results
    
    def generate_verification_report(self, results: Dict):
        """Generate comprehensive verification report"""
        print(f"\n📊 FINAL VERIFICATION REPORT")
        print("=" * 70)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report = {
            'verification_timestamp': timestamp,
            'chain_id': self.chain_id,
            'results': results,
            'summary': {
                'total_tokens_tested': len(results),
                'successful_verifications': 0,
                'failed_verifications': 0
            }
        }
        
        print(f"🕐 Verification completed: {timestamp}")
        print(f"🌐 Network: Arbitrum One (Chain ID: {self.chain_id})")
        print()
        
        for token, data in results.items():
            if 'error' in data:
                print(f"❌ {token}: {data['error']}")
                report['summary']['failed_verifications'] += 1
                continue
            
            domain_verified = data['domain_verification']['verification_passed']
            typehash_verified = data['typehash_verification']['typehash_verified']
            
            status = "✅ VERIFIED" if domain_verified else "⚠️ PARTIAL"
            print(f"{status} {token}:")
            print(f"   📍 Debt Token: {data['debt_token_address']}")
            
            if domain_verified:
                rec_params = data['domain_verification']['recommended_parameters']
                print(f"   🔑 EIP-712 Domain Parameters:")
                print(f"      name: '{rec_params['name']}'")
                print(f"      version: '{rec_params['version']}'")
                print(f"      chainId: {rec_params['chainId']}")
                print(f"      verifyingContract: {rec_params['verifyingContract']}")
                report['summary']['successful_verifications'] += 1
            else:
                print(f"   ⚠️ Domain separator verification incomplete")
                report['summary']['failed_verifications'] += 1
            
            if typehash_verified:
                print(f"   🔗 Delegation Type: {data['typehash_verification']['recommended_type']}")
            else:
                print(f"   ⚠️ Delegation typehash verification incomplete")
            
            # Show nonce method availability
            token_params = data['token_parameters']
            if token_params.get('nonces'):
                print(f"   🔢 Nonce Method: {token_params['nonces']}")
            if token_params.get('delegation_nonces'):
                print(f"   🔢 Delegation Nonce Method: {token_params['delegation_nonces']}")
            
            print()
        
        # Save report to file
        report_filename = f"domain_verification_report_{timestamp}.json"
        try:
            with open(report_filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"💾 Report saved to: {report_filename}")
        except Exception as e:
            print(f"⚠️ Failed to save report: {e}")
        
        # Final summary
        print(f"\n📈 VERIFICATION SUMMARY:")
        print(f"   Total tokens tested: {report['summary']['total_tokens_tested']}")
        print(f"   Successful verifications: {report['summary']['successful_verifications']}")
        print(f"   Failed/partial verifications: {report['summary']['failed_verifications']}")
        
        if report['summary']['successful_verifications'] > 0:
            print(f"\n✅ RECOMMENDED USAGE:")
            print(f"   Use the verified EIP-712 parameters shown above in your debt swap implementation")
            print(f"   Ensure you use the correct nonce method for each token")
        else:
            print(f"\n⚠️ MANUAL VERIFICATION REQUIRED:")
            print(f"   Could not automatically verify all parameters")
            print(f"   Review the token parameters and try manual verification")

def main():
    """Main execution function"""
    try:
        verifier = DomainSeparatorVerifier()
        results = verifier.run_comprehensive_verification()
        
        return results
        
    except Exception as e:
        print(f"💥 VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()