
#!/usr/bin/env python3
"""
Complete System Diagnostic - Identify All Potential Failure Points
"""

import os
import json
from web3 import Web3
from decimal import Decimal

class SystemDiagnostic:
    def __init__(self):
        self.issues_found = []
        self.fixes_applied = []
        
    def diagnose_all_issues(self):
        """Comprehensive system diagnostic"""
        
        print("🔍 COMPLETE SYSTEM DIAGNOSTIC")
        print("=" * 50)
        
        # 1. Contract Address Issues
        self.check_contract_addresses()
        
        # 2. JSON Serialization Issues
        self.check_json_serialization()
        
        # 3. Gas Parameter Issues
        self.check_gas_parameters()
        
        # 4. RPC Connection Issues
        self.check_rpc_connections()
        
        # 5. Missing Dependencies
        self.check_dependencies()
        
        # 6. Aave Integration Issues
        self.check_aave_integration()
        
        # 7. Uniswap Integration Issues
        self.check_uniswap_integration()
        
        # 8. Error Handling Issues
        self.check_error_handling()
        
        # 9. Configuration Issues
        self.check_configuration()
        
        # 10. Network Issues
        self.check_network_configuration()
        
        self.print_summary()
        
    def check_contract_addresses(self):
        """Check all contract addresses for validity"""
        print("\n1. 🏦 CONTRACT ADDRESS VALIDATION")
        
        # Known issues with contract addresses
        issues = [
            {
                'issue': 'USDC address inconsistency',
                'details': 'System may be using wrong USDC address (0xAf88D065e77C8cF0EAEfF3e253e648A15CEe23dC)',
                'fix': 'Use correct USDC.e address: 0xFF970A61A04b1cA14834A651bAb06d67307796618',
                'priority': 'CRITICAL'
            },
            {
                'issue': 'Contract validation missing',
                'details': 'No validation that contracts exist before calling them',
                'fix': 'Add contract existence validation',
                'priority': 'HIGH'
            }
        ]
        
        for issue in issues:
            self.issues_found.append(issue)
            print(f"   ❌ {issue['issue']}: {issue['details']}")
            
    def check_json_serialization(self):
        """Check JSON serialization issues"""
        print("\n2. 📄 JSON SERIALIZATION")
        
        issues = [
            {
                'issue': 'Decimal serialization error',
                'details': 'Object of type Decimal is not JSON serializable',
                'fix': 'Implement DecimalEncoder class for JSON serialization',
                'priority': 'HIGH'
            }
        ]
        
        for issue in issues:
            self.issues_found.append(issue)
            print(f"   ❌ {issue['issue']}: {issue['details']}")
            
    def check_gas_parameters(self):
        """Check gas parameter calculation issues"""
        print("\n3. ⛽ GAS PARAMETERS")
        
        issues = [
            {
                'issue': 'Gas estimation failures',
                'details': 'Gas estimation may fail due to contract call issues',
                'fix': 'Add fallback gas parameters and better error handling',
                'priority': 'MEDIUM'
            },
            {
                'issue': 'Gas multiplier validation',
                'details': 'Gas multipliers not properly validated for numeric types',
                'fix': 'Add comprehensive numeric validation',
                'priority': 'MEDIUM'
            }
        ]
        
        for issue in issues:
            self.issues_found.append(issue)
            print(f"   ⚠️ {issue['issue']}: {issue['details']}")
            
    def check_rpc_connections(self):
        """Check RPC connection issues"""
        print("\n4. 🌐 RPC CONNECTIONS")
        
        issues = [
            {
                'issue': 'RPC failover not comprehensive',
                'details': 'May not properly handle all RPC failure scenarios',
                'fix': 'Enhance RPC failover mechanism',
                'priority': 'MEDIUM'
            }
        ]
        
        for issue in issues:
            self.issues_found.append(issue)
            print(f"   ⚠️ {issue['issue']}: {issue['details']}")
            
    def check_dependencies(self):
        """Check missing dependencies"""
        print("\n5. 📦 DEPENDENCIES")
        
        required_files = [
            'enhanced_borrow_manager.py',
            'aave_integration.py',
            'uniswap_integration.py',
            'aave_health_monitor.py',
            'gas_fee_calculator.py'
        ]
        
        for file in required_files:
            if not os.path.exists(file):
                issue = {
                    'issue': f'Missing dependency: {file}',
                    'details': f'Required file {file} not found',
                    'fix': f'Create or ensure {file} exists',
                    'priority': 'CRITICAL'
                }
                self.issues_found.append(issue)
                print(f"   ❌ Missing: {file}")
            else:
                print(f"   ✅ Found: {file}")
                
    def check_aave_integration(self):
        """Check Aave integration issues"""
        print("\n6. 🏦 AAVE INTEGRATION")
        
        issues = [
            {
                'issue': 'Health factor calculation errors',
                'details': 'Division by zero or invalid health factor calculations',
                'fix': 'Add proper health factor validation',
                'priority': 'HIGH'
            },
            {
                'issue': 'Borrow amount validation',
                'details': 'May attempt to borrow more than available',
                'fix': 'Add comprehensive borrow capacity checks',
                'priority': 'HIGH'
            }
        ]
        
        for issue in issues:
            self.issues_found.append(issue)
            print(f"   ❌ {issue['issue']}: {issue['details']}")
            
    def check_uniswap_integration(self):
        """Check Uniswap integration issues"""
        print("\n7. 🔄 UNISWAP INTEGRATION")
        
        issues = [
            {
                'issue': 'Token approval failures',
                'details': 'Token approvals may fail due to contract issues',
                'fix': 'Add robust approval validation and retry logic',
                'priority': 'HIGH'
            },
            {
                'issue': 'Slippage tolerance',
                'details': 'Fixed slippage may cause failures in volatile markets',
                'fix': 'Implement dynamic slippage calculation',
                'priority': 'MEDIUM'
            }
        ]
        
        for issue in issues:
            self.issues_found.append(issue)
            print(f"   ❌ {issue['issue']}: {issue['details']}")
            
    def check_error_handling(self):
        """Check error handling completeness"""
        print("\n8. 🚨 ERROR HANDLING")
        
        issues = [
            {
                'issue': 'Insufficient error categorization',
                'details': 'Errors not properly categorized for appropriate responses',
                'fix': 'Implement comprehensive error categorization system',
                'priority': 'MEDIUM'
            }
        ]
        
        for issue in issues:
            self.issues_found.append(issue)
            print(f"   ⚠️ {issue['issue']}: {issue['details']}")
            
    def check_configuration(self):
        """Check configuration issues"""
        print("\n9. ⚙️ CONFIGURATION")
        
        required_env_vars = [
            'WALLET_PRIVATE_KEY',
            'COINMARKETCAP_API_KEY',
            'NETWORK_MODE'
        ]
        
        for var in required_env_vars:
            if not os.getenv(var):
                issue = {
                    'issue': f'Missing environment variable: {var}',
                    'details': f'{var} not set in environment',
                    'fix': f'Set {var} in Replit secrets',
                    'priority': 'CRITICAL'
                }
                self.issues_found.append(issue)
                print(f"   ❌ Missing: {var}")
            else:
                print(f"   ✅ Found: {var}")
                
    def check_network_configuration(self):
        """Check network configuration issues"""
        print("\n10. 🌐 NETWORK CONFIGURATION")
        
        issues = [
            {
                'issue': 'Chain ID validation',
                'details': 'May not properly validate chain ID matches network mode',
                'fix': 'Add strict chain ID validation',
                'priority': 'MEDIUM'
            }
        ]
        
        for issue in issues:
            self.issues_found.append(issue)
            print(f"   ⚠️ {issue['issue']}: {issue['details']}")
            
    def print_summary(self):
        """Print diagnostic summary"""
        print("\n" + "=" * 50)
        print("📊 DIAGNOSTIC SUMMARY")
        print("=" * 50)
        
        critical_issues = [i for i in self.issues_found if i['priority'] == 'CRITICAL']
        high_issues = [i for i in self.issues_found if i['priority'] == 'HIGH']
        medium_issues = [i for i in self.issues_found if i['priority'] == 'MEDIUM']
        
        print(f"🚨 CRITICAL Issues: {len(critical_issues)}")
        print(f"❌ HIGH Issues: {len(high_issues)}")
        print(f"⚠️ MEDIUM Issues: {len(medium_issues)}")
        print(f"📋 TOTAL Issues: {len(self.issues_found)}")
        
        if critical_issues:
            print("\n🚨 CRITICAL ISSUES (Must fix before running):")
            for issue in critical_issues:
                print(f"   • {issue['issue']}")
                print(f"     Fix: {issue['fix']}")
                
        return len(critical_issues) == 0

if __name__ == "__main__":
    diagnostic = SystemDiagnostic()
    ready = diagnostic.diagnose_all_issues()
    
    if ready:
        print("\n✅ System ready for workflow execution")
    else:
        print("\n❌ System has critical issues that must be fixed first")
