
#!/usr/bin/env python3
"""
WALLET FUNDING VALIDATOR
Comprehensive validation and funding guidance for DeFi operations
"""

import os
import time
from arbitrum_testnet_agent import ArbitrumTestnetAgent
from web3 import Web3

class WalletFundingValidator:
    def __init__(self):
        self.min_eth_for_gas = 0.005
        self.min_usdc_for_swap = 1.0
        self.recommended_eth = 0.01
        self.recommended_usdc = 50.0
        
    def check_wallet_funding(self, agent):
        """Check if wallet has sufficient funding for operations"""
        print("💰 WALLET FUNDING VALIDATION")
        print("=" * 50)
        
        funding_status = {
            'eth_balance': 0,
            'usdc_balance': 0,
            'eth_sufficient': False,
            'usdc_sufficient': False,
            'ready_for_operations': False,
            'issues': [],
            'recommendations': []
        }
        
        try:
            # Check ETH balance
            eth_balance = agent.get_eth_balance()
            funding_status['eth_balance'] = eth_balance
            
            print(f"⚡ ETH Balance: {eth_balance:.6f} ETH")
            
            if eth_balance >= self.min_eth_for_gas:
                funding_status['eth_sufficient'] = True
                print(f"✅ ETH sufficient for gas (minimum: {self.min_eth_for_gas} ETH)")
            else:
                funding_status['eth_sufficient'] = False
                funding_status['issues'].append(f"Insufficient ETH: need {self.min_eth_for_gas} ETH, have {eth_balance:.6f} ETH")
                print(f"❌ Insufficient ETH for gas (need: {self.min_eth_for_gas} ETH)")
            
            # Check USDC balance
            try:
                if hasattr(agent, 'aave') and agent.aave:
                    usdc_balance = agent.aave.get_token_balance(agent.usdc_address)
                    funding_status['usdc_balance'] = usdc_balance
                    
                    print(f"💵 USDC Balance: {usdc_balance:.6f} USDC")
                    
                    if usdc_balance >= self.min_usdc_for_swap:
                        funding_status['usdc_sufficient'] = True
                        print(f"✅ USDC sufficient for swap (minimum: {self.min_usdc_for_swap} USDC)")
                    else:
                        funding_status['usdc_sufficient'] = False
                        funding_status['issues'].append(f"Insufficient USDC: need {self.min_usdc_for_swap} USDC, have {usdc_balance:.6f} USDC")
                        print(f"❌ Insufficient USDC for swap (need: {self.min_usdc_for_swap} USDC)")
                else:
                    funding_status['issues'].append("Cannot check USDC balance - Aave integration not available")
                    print("⚠️ Cannot check USDC balance - Aave integration not available")
            
            except Exception as e:
                funding_status['issues'].append(f"USDC balance check failed: {str(e)}")
                print(f"❌ USDC balance check failed: {e}")
            
            # Overall readiness
            funding_status['ready_for_operations'] = funding_status['eth_sufficient'] and funding_status['usdc_sufficient']
            
            if funding_status['ready_for_operations']:
                print("\n🎉 WALLET READY FOR DEFI OPERATIONS!")
            else:
                print(f"\n❌ WALLET NOT READY - {len(funding_status['issues'])} ISSUE(S) FOUND")
                
                # Generate recommendations
                funding_status['recommendations'] = self.generate_funding_recommendations(
                    funding_status, agent.address, agent.w3.eth.chain_id
                )
                
                self.display_funding_guidance(funding_status, agent.address, agent.w3.eth.chain_id)
            
            return funding_status
            
        except Exception as e:
            print(f"❌ Wallet validation failed: {e}")
            funding_status['issues'].append(f"Validation error: {str(e)}")
            return funding_status
    
    def generate_funding_recommendations(self, funding_status, wallet_address, chain_id):
        """Generate specific funding recommendations"""
        recommendations = []
        
        if not funding_status['eth_sufficient']:
            eth_needed = self.recommended_eth - funding_status['eth_balance']
            recommendations.append({
                'type': 'ETH',
                'amount_needed': eth_needed,
                'priority': 'HIGH',
                'purpose': 'Gas fees for transactions'
            })
        
        if not funding_status['usdc_sufficient']:
            usdc_needed = self.recommended_usdc - funding_status['usdc_balance']
            recommendations.append({
                'type': 'USDC',
                'amount_needed': usdc_needed,
                'priority': 'HIGH',
                'purpose': 'Token swaps and DeFi operations'
            })
        
        return recommendations
    
    def display_funding_guidance(self, funding_status, wallet_address, chain_id):
        """Display detailed funding guidance"""
        print("\n💡 FUNDING GUIDANCE")
        print("=" * 50)
        
        network_name = "Arbitrum Mainnet" if chain_id == 42161 else "Arbitrum Sepolia"
        print(f"🌐 Network: {network_name}")
        print(f"📍 Wallet Address: {wallet_address}")
        
        print(f"\n📋 ISSUES FOUND:")
        for i, issue in enumerate(funding_status['issues'], 1):
            print(f"   {i}. {issue}")
        
        print(f"\n💰 RECOMMENDED FUNDING:")
        for rec in funding_status['recommendations']:
            print(f"   • {rec['type']}: {rec['amount_needed']:.6f} ({rec['purpose']})")
        
        print(f"\n🔗 FUNDING OPTIONS:")
        
        if chain_id == 42161:  # Mainnet
            print("   1. 🏦 CENTRALIZED EXCHANGES:")
            print("      • Binance → Withdraw to Arbitrum")
            print("      • Coinbase → Send to Arbitrum")
            print("      • Kraken → Withdraw to Arbitrum")
            print("      • Gate.io → Direct Arbitrum withdrawal")
            
            print("   2. 🌉 BRIDGE FROM OTHER CHAINS:")
            print("      • Arbitrum Bridge: https://bridge.arbitrum.io")
            print("      • Hop Protocol: https://hop.exchange")
            print("      • Across: https://across.to")
            
            print("   3. 🔄 DEX SWAP (if you have other tokens on Arbitrum):")
            print("      • Uniswap V3: https://app.uniswap.org")
            print("      • 1inch: https://app.1inch.io")
            print("      • Camelot: https://app.camelot.exchange")
            
        else:  # Testnet
            print("   1. 🚰 TESTNET FAUCETS:")
            print("      • Arbitrum Sepolia Faucet: https://faucet.quicknode.com/arbitrum/sepolia")
            print("      • Chainlink Faucet: https://faucets.chain.link/arbitrum-sepolia")
            print("      • Alchemy Faucet: https://sepoliafaucet.com")
            
            print("   2. 🌉 BRIDGE FROM SEPOLIA:")
            print("      • Arbitrum Sepolia Bridge: https://bridge.arbitrum.io")
        
        print(f"\n⚠️ IMPORTANT NOTES:")
        print("   • Always double-check the network (Arbitrum) before sending funds")
        print("   • Start with small amounts to test")
        print("   • Keep some ETH for gas fees")
        print("   • Transaction fees are much lower on Arbitrum than Ethereum mainnet")
        
        if chain_id == 42161:
            print("   • 🚨 MAINNET: You are using real money!")
        else:
            print("   • 🧪 TESTNET: These are test tokens with no real value")

def auto_fund_check_and_guidance():
    """Automated funding check with guidance"""
    print("🔍 AUTOMATED WALLET FUNDING CHECK")
    print("=" * 60)
    
    try:
        # Initialize agent
        agent = ArbitrumTestnetAgent()
        validator = WalletFundingValidator()
        
        # Run validation
        funding_status = validator.check_wallet_funding(agent)
        
        # Return status for other scripts to use
        return funding_status
        
    except Exception as e:
        print(f"❌ Auto funding check failed: {e}")
        return None

def create_funding_bypass_for_testing():
    """Create a test mode that bypasses funding requirements"""
    print("\n🧪 TEST MODE BYPASS")
    print("=" * 30)
    print("⚠️ This will create a test configuration that bypasses funding checks")
    print("🚨 ONLY USE FOR TESTING - NOT FOR REAL OPERATIONS")
    
    test_config = {
        'test_mode': True,
        'bypass_funding_checks': True,
        'min_eth_override': 0.001,
        'min_usdc_override': 0.1,
        'warning': 'TEST MODE ACTIVE - NOT FOR PRODUCTION USE'
    }
    
    import json
    with open('test_funding_config.json', 'w') as f:
        json.dump(test_config, f, indent=2)
    
    print("✅ Test configuration created: test_funding_config.json")
    print("💡 Scripts can check for this file to enable test mode")

if __name__ == "__main__":
    # Run automated funding check
    funding_status = auto_fund_check_and_guidance()
    
    if funding_status and not funding_status['ready_for_operations']:
        print("\n" + "=" * 60)
        print("❓ WHAT WOULD YOU LIKE TO DO?")
        print("1. 💰 Get detailed funding instructions")
        print("2. 🧪 Create test mode bypass (for development only)")
        print("3. 🔄 Check funding status again")
        print("4. ❌ Exit")
        
        try:
            choice = input("\nEnter choice (1-4): ").strip()
            
            if choice == "1":
                print("\n📋 DETAILED FUNDING INSTRUCTIONS")
                print("Copy your wallet address and visit the recommended funding sources above")
                
            elif choice == "2":
                create_funding_bypass_for_testing()
                
            elif choice == "3":
                print("\n🔄 Rechecking funding...")
                time.sleep(2)
                auto_fund_check_and_guidance()
                
            else:
                print("👋 Exiting funding validator")
                
        except KeyboardInterrupt:
            print("\n👋 Exiting funding validator")
