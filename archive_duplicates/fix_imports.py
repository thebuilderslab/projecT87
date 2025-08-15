
#!/usr/bin/env python3
"""
Fix Imports After Deduplication
Automatically update import statements to reference canonical files
"""

import os
import re
import subprocess
import sys

# Comprehensive mapping of archived files to their canonical replacements
IMPORT_MAPPINGS = {
    # Core agent files
    'arbitrum_testnet_agent': 'main',
    'collaborative_strategy_manager': 'main',
    'autonomous_launcher': 'main',
    'mainnet_launcher': 'main',
    'manual_controls': 'main',
    'strategy_manager': 'main',
    'config': 'main',
    
    # Emergency and safety systems
    'emergency_stop': 'emergency_funding_manager',
    'emergency_launch': 'emergency_funding_manager',
    'emergency_dashboard_launch': 'emergency_funding_manager',
    
    # Aave and DeFi integrations
    'enhanced_rpc_manager': 'aave_integration',
    'enhanced_borrow_manager': 'aave_integration',
    'enhanced_balance_fetcher': 'aave_integration',
    'optimized_balance_fetcher': 'aave_integration',
    'accurate_debank_fetcher': 'aave_integration',
    'health_monitor': 'aave_integration',
    'aave_health_monitor': 'aave_integration',
    'enhanced_contract_manager': 'aave_integration',
    'contract_validator': 'aave_integration',
    'network_validator': 'aave_integration',
    'gas_optimizer': 'aave_integration',
    'wallet_diagnostics': 'aave_integration',
    'debt_swap_manager': 'aave_integration',
    'uniswap_integration': 'aave_integration',
    'enhanced_collateral_validator': 'aave_integration',
    'enhanced_system_validator': 'aave_integration',
    'enhanced_web3_provider': 'aave_integration',
    'working_rpc_manager': 'aave_integration',
    
    # Market and trading strategies
    'market_signal_strategy': 'main',
    'market_strategy_config': 'main',
    'ml_strategy_optimizer': 'main',
    'advanced_trend_analyzer': 'main',
    
    # Dashboard and web interface
    'dashboard': 'web_dashboard',
    'improved_web_dashboard': 'web_dashboard',
    'launch_dashboard_clean': 'web_dashboard',
    'launch_improved_dashboard': 'web_dashboard',
    'quick_dashboard_fix': 'web_dashboard',
    
    # Diagnostic and validation tools
    'system_diagnostic': 'main',
    'comprehensive_diagnostic': 'main',
    'autonomous_system_diagnostic': 'main',
    'api_diagnostics': 'main',
    'dependency_validator': 'main',
    'environment_validator': 'main',
    'comprehensive_fix_validator': 'main',
    'contract_validation_tool': 'aave_integration',
    'borrow_diagnostic_tool': 'aave_integration',
    
    # Network and RPC management
    'enhanced_rpc_manager': 'aave_integration',
    'network_congestion_handler': 'aave_integration',
    'network_quality_detector': 'aave_integration',
    
    # Swap and transaction management
    'enhanced_swap_dai_for_wbtc': 'aave_integration',
    'enhanced_swap_dai_for_weth': 'aave_integration',
    'enhanced_swap_usdc_for_wbtc': 'aave_integration',
    'manual_balance_swap': 'aave_integration',
    'force_swap_with_approval': 'aave_integration',
    'force_swap_with_manual_amounts': 'aave_integration',
    
    # Configuration and utilities
    'config_constants': 'main',
    'env_handler': 'main',
    'prompt_interface': 'main',
    
    # Cross-chain and compound integration
    'cross_chain_manager': 'aave_integration',
    'compound_v3_integration': 'aave_integration',
    
    # Compliance and validation
    'dai_compliance_enforcer': 'main',
    'dai_compliance_final_validator': 'main',
    'final_execution_validator': 'main',
    
    # Monitoring and alerts
    'live_data_monitor': 'main',
    'alert_system': 'main',
    
    # Optimization and sequence management
    'optimized_sequence_manager': 'aave_integration',
    'funding_bypass_handler': 'emergency_funding_manager',
    
    # Testing and validation
    'integrated_system_test': 'main',
    'complete_system_validation': 'main',
    'comprehensive_api_test': 'main',
    'comprehensive_debt_swap_test': 'aave_integration',
    
    # Launchers and runners
    'complete_autonomous_launcher': 'main',
    'parallel_dashboard_launcher': 'web_dashboard',
    'verified_system_launcher': 'main',
    'run_autonomous': 'run_autonomous_mainnet',
    
    # Collaboration and interface
    'collaboration_interface': 'main',
    
    # Manual triggers and controls
    'manual_trigger': 'main',
    'create_and_activate': 'main',
    'create_position': 'aave_integration',
    'enable_debt_swaps': 'aave_integration',
    
    # Transaction and approval management
    'execute_debt_swap_network_approval': 'aave_integration',
    'execute_onetime_debt_swap': 'aave_integration',
    
    # Debugging and analysis tools
    'debug_agent_position': 'main',
    'debug_borrowing': 'aave_integration',
    'debug_swap_system': 'aave_integration',
    'debug_syntax': 'main',
    'debug_token_balances': 'aave_integration',
    'diagnose_borrow_failures': 'aave_integration',
    'diagnose_transaction_reverts': 'aave_integration',
    
    # API and function testing
    'direct_api_function_test': 'aave_integration',
    'aave_api_fallback': 'aave_integration',
    
    # Balance and wallet checking
    'check_agent_status': 'main',
    'check_wallet_balance': 'main',
    'check_wallet_value': 'main',
    'check_recent_operations': 'main',
    'check_syntax': 'main',
    
    # Integration checking
    'check_arbiscan_integration': 'aave_integration',
    'check_zapper_integration': 'aave_integration',
    
    # Operational and compliance
    'operational_checklist': 'main',
    'one_hour_confidence_validator': 'main',
    
    # Fix scripts (map to main for compatibility)
    'fix_aave_contract_calls': 'aave_integration',
    'fix_aave_integration': 'aave_integration',
    'fix_borrow_gas': 'aave_integration',
    'fix_critical_contract_issues': 'aave_integration',
    'fix_current_issues': 'main',
    'fix_defi_integration': 'aave_integration',
    'fix_json_serialization': 'main',
    'fix_private_key_issue': 'main',
    'fix_secrets': 'main',
    
    # Syntax and line checking
    'line_by_line_syntax_checker': 'main',
    
    # Deduplication scripts (keep self-referential)
    'deduplicate_codebase': 'main',
    'deduplicate_codebase_1': 'main',
}

def fix_file_imports(file_path):
    """Fix imports in a single file"""
    if not file_path.endswith('.py'):
        return 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = 0
        
        # Fix import statements
        for old_module, new_module in IMPORT_MAPPINGS.items():
            # Pattern 1: from old_module import ...
            pattern1 = rf'\bfrom\s+{re.escape(old_module)}\s+import\b'
            replacement1 = f'from {new_module} import'
            content, count1 = re.subn(pattern1, replacement1, content)
            changes_made += count1
            
            # Pattern 2: import old_module
            pattern2 = rf'\bimport\s+{re.escape(old_module)}\b'
            replacement2 = f'import {new_module}'
            content, count2 = re.subn(pattern2, replacement2, content)
            changes_made += count2
            
            # Pattern 3: old_module.something (be careful not to break variables)
            pattern3 = rf'\b{re.escape(old_module)}\.'
            replacement3 = f'{new_module}.'
            content, count3 = re.subn(pattern3, replacement3, content)
            changes_made += count3
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            if changes_made > 0:
                print(f"✅ Fixed {changes_made} imports in {file_path}")
            return changes_made
        else:
            return 0
            
    except Exception as e:
        print(f"❌ Error fixing imports in {file_path}: {e}")
        return 0

def fix_all_imports():
    """Fix imports in all Python files"""
    print("🔧 Fixing imports after deduplication...")
    
    files_fixed = 0
    total_changes = 0
    
    # Process all Python files
    for root, dirs, files in os.walk('.'):
        # Skip archive directory
        if 'archive_duplicates' in dirs:
            dirs.remove('archive_duplicates')
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                changes = fix_file_imports(file_path)
                if changes > 0:
                    files_fixed += 1
                    total_changes += changes
    
    print(f"✅ Import fixing complete!")
    print(f"📁 Files modified: {files_fixed}")
    print(f"🔄 Total changes made: {total_changes}")
    
    return total_changes > 0

if __name__ == "__main__":
    success = fix_all_imports()
    
    # Also check for common import issues in main files
    critical_files = ['main.py', 'web_dashboard.py', 'aave_integration.py', 'emergency_funding_manager.py']
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for problematic imports that might still exist
                problematic_patterns = [
                    r'from\s+arbitrum_testnet_agent\s+import',
                    r'import\s+arbitrum_testnet_agent',
                    r'from\s+emergency_stop\s+import',
                    r'import\s+emergency_stop'
                ]
                
                for pattern in problematic_patterns:
                    if re.search(pattern, content):
                        print(f"⚠️  Found potential import issue in {file_path}: {pattern}")
                        
            except Exception as e:
                print(f"❌ Could not check {file_path}: {e}")
    
    if success:
        print("\n🔄 Re-running verification...")
        os.system("python verify_deduplication_complete.py")
    else:
        print("\n✅ No import changes needed")
        
    # Quick syntax check on critical files
    print("\n🔍 Quick syntax verification...")
    for file_path in critical_files:
        if os.path.exists(file_path):
            try:
                result = subprocess.run([sys.executable, '-m', 'py_compile', file_path], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ Syntax OK: {file_path}")
                else:
                    print(f"❌ Syntax error in {file_path}: {result.stderr}")
            except Exception as e:
                print(f"❌ Could not check syntax for {file_path}: {e}")
                
    print("\n✅ Import fixing process complete!")
