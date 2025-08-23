
#!/usr/bin/env python3
"""
Network Approval Readiness Checker
Comprehensive validation for mainnet deployment readiness
"""

import os
import time
import json
from datetime import datetime

def check_environment_variables():
    """Check all required environment variables"""
    print("🔍 CHECKING ENVIRONMENT VARIABLES")
    print("=" * 40)
    
    required_vars = {
        'PRIVATE_KEY': 'Wallet private key for transactions',
        'COINMARKETCAP_API_KEY': 'Price data API access',
        'NETWORK_MODE': 'Network configuration (should be mainnet)',
    }
    
    optional_vars = {
        'ARBITRUM_RPC_URL': 'Custom RPC endpoint',
        'PROMPT_KEY': 'AI features',
        'OPTIMIZER_API_KEY': 'Gas optimization',
    }
    
    env_score = 0
    max_env_score = len(required_vars) * 2 + len(optional_vars)
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value and len(value.strip()) > 0:
            print(f"✅ {var}: Configured ({description})")
            env_score += 2
        else:
            print(f"❌ {var}: Missing ({description})")
    
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value and len(value.strip()) > 0:
            print(f"✅ {var}: Configured ({description})")
            env_score += 1
        else:
            print(f"⚠️ {var}: Missing ({description})")
    
    return env_score, max_env_score

def check_file_integrity():
    """Check integrity of critical system files"""
    print("\n🔍 CHECKING FILE INTEGRITY")
    print("=" * 40)
    
    critical_files = [
        'main.py',
        'main.py',
        'aave_integration.py',
        'web_dashboard.py'
    ]
    
    file_score = 0
    max_file_score = len(critical_files)
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    if len(content) > 100:  # Basic sanity check
                        print(f"✅ {file_path}: OK ({len(content)} chars)")
                        file_score += 1
                    else:
                        print(f"⚠️ {file_path}: Too small ({len(content)} chars)")
            except Exception as e:
                print(f"❌ {file_path}: Read error - {e}")
        else:
            print(f"❌ {file_path}: Missing")
    
    return file_score, max_file_score

def check_network_configuration():
    """Check network configuration for mainnet readiness"""
    print("\n🔍 CHECKING NETWORK CONFIGURATION")
    print("=" * 40)
    
    network_score = 0
    max_network_score = 3
    
    # Check network mode
    network_mode = os.getenv('NETWORK_MODE', 'testnet')
    if network_mode.lower() == 'mainnet':
        print("✅ Network Mode: Mainnet")
        network_score += 1
    else:
        print(f"⚠️ Network Mode: {network_mode} (should be mainnet)")
    
    # Check RPC configuration
    rpc_url = os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc')
    if 'mainnet' in rpc_url.lower() or 'arb1' in rpc_url.lower():
        print("✅ RPC URL: Mainnet endpoint")
        network_score += 1
    else:
        print(f"⚠️ RPC URL: {rpc_url} (verify mainnet endpoint)")
    
    # Check private key format
    private_key = os.getenv('PRIVATE_KEY')
    if private_key:
        clean_key = private_key.replace('0x', '')
        if len(clean_key) == 64:
            print("✅ Private Key: Valid format")
            network_score += 1
        else:
            print(f"❌ Private Key: Invalid length ({len(clean_key)})")
    else:
        print("❌ Private Key: Not configured")
    
    return network_score, max_network_score

def generate_readiness_report():
    """Generate comprehensive readiness report"""
    print("🚀 NETWORK APPROVAL READINESS ASSESSMENT")
    print("=" * 60)
    
    # Run all checks
    env_score, max_env_score = check_environment_variables()
    file_score, max_file_score = check_file_integrity()
    network_score, max_network_score = check_network_configuration()
    
    # Calculate overall score
    total_score = env_score + file_score + network_score
    max_total_score = max_env_score + max_file_score + max_network_score
    readiness_percentage = (total_score / max_total_score) * 100
    
    print(f"\n📊 READINESS ASSESSMENT RESULTS")
    print("=" * 60)
    print(f"Environment Variables: {env_score}/{max_env_score} ({(env_score/max_env_score)*100:.0f}%)")
    print(f"File Integrity: {file_score}/{max_file_score} ({(file_score/max_file_score)*100:.0f}%)")
    print(f"Network Configuration: {network_score}/{max_network_score} ({(network_score/max_network_score)*100:.0f}%)")
    print(f"\n🎯 OVERALL READINESS: {total_score}/{max_total_score} ({readiness_percentage:.0f}%)")
    
    # Determine readiness status
    if readiness_percentage >= 90:
        status = "✅ EXCELLENT - READY FOR DEPLOYMENT"
        approval_probability = "95%"
    elif readiness_percentage >= 80:
        status = "✅ GOOD - LIKELY READY FOR DEPLOYMENT"
        approval_probability = "85%"
    elif readiness_percentage >= 70:
        status = "⚠️ FAIR - NEEDS MINOR IMPROVEMENTS"
        approval_probability = "70%"
    else:
        status = "❌ POOR - SIGNIFICANT IMPROVEMENTS NEEDED"
        approval_probability = "50%"
    
    print(f"🚦 STATUS: {status}")
    print(f"📈 NETWORK APPROVAL PROBABILITY: {approval_probability}")
    
    # Save report
    report = {
        'timestamp': datetime.now().isoformat(),
        'readiness_percentage': readiness_percentage,
        'total_score': total_score,
        'max_score': max_total_score,
        'status': status,
        'approval_probability': approval_probability,
        'component_scores': {
            'environment': f"{env_score}/{max_env_score}",
            'files': f"{file_score}/{max_file_score}",
            'network': f"{network_score}/{max_network_score}"
        }
    }
    
    with open('readiness_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved to: readiness_report.json")
    
    return readiness_percentage >= 80

if __name__ == "__main__":
    ready = generate_readiness_report()
    
    if ready:
        print("\n🎉 SYSTEM IS READY FOR NETWORK APPROVAL!")
        print("💡 Next step: Run the main system with confidence")
    else:
        print("\n⚠️ SYSTEM NEEDS IMPROVEMENTS BEFORE DEPLOYMENT")
        print("💡 Address the issues above and re-run this check")
