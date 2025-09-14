#!/usr/bin/env python3
"""
Health Factor Configuration Update Script
Changes minimum health factor requirement from 2.0 to 1.5 in all relevant files
"""

import os
import json
import re
import shutil
from datetime import datetime

def backup_file(file_path):
    """Create backup of file before modification"""
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    print(f"📁 Backup created: {backup_path}")
    return backup_path

def update_environmental_configuration():
    """Update environmental_configuration.py"""
    print("🔧 Updating environmental_configuration.py...")
    
    file_path = "environmental_configuration.py"
    backup_backup_path = backup_file(file_path)
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Update TARGET_HEALTH_FACTOR from 2.0 to 1.5
    content = re.sub(
        r"TARGET_HEALTH_FACTOR = float\(os\.getenv\('TARGET_HEALTH_FACTOR', '2\.0'\)\)",
        "TARGET_HEALTH_FACTOR = float(os.getenv('TARGET_HEALTH_FACTOR', '1.5'))",
        content
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    changes_made = original_content != content
    print(f"✅ environmental_configuration.py updated - Changes made: {changes_made}")
    
    return {
        'file': file_path,
        'backup': backup_backup_path,
        'changes_made': changes_made,
        'updates': ['TARGET_HEALTH_FACTOR: 2.0 → 1.5']
    }

def update_arbitrum_testnet_agent():
    """Update arbitrum_testnet_agent.py health factor thresholds"""
    print("🔧 Updating arbitrum_testnet_agent.py...")
    
    file_path = "arbitrum_testnet_agent.py"
    backup_path = backup_file(file_path)
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    updates_made = []
    
    # 1. Update growth_health_factor_threshold from 2.0 to 1.5
    old_pattern = r"self\.growth_health_factor_threshold = 2\.0"
    new_replacement = "self.growth_health_factor_threshold = 1.5"
    if re.search(old_pattern, content):
        content = re.sub(old_pattern, new_replacement, content)
        updates_made.append('growth_health_factor_threshold: 2.0 → 1.5')
    
    # 2. Update capacity_health_factor_threshold from 1.8 to 1.5  
    old_pattern = r"self\.capacity_health_factor_threshold = 1\.8"
    new_replacement = "self.capacity_health_factor_threshold = 1.5"
    if re.search(old_pattern, content):
        content = re.sub(old_pattern, new_replacement, content)
        updates_made.append('capacity_health_factor_threshold: 1.8 → 1.5')
    
    # 3. Update target_health_factor from 2.5 to 1.5 (this is the main target)
    old_pattern = r"self\.target_health_factor = 2\.5"
    new_replacement = "self.target_health_factor = 1.5"
    if re.search(old_pattern, content):
        content = re.sub(old_pattern, new_replacement, content)
        updates_made.append('target_health_factor: 2.5 → 1.5')
    
    # 4. Update health factor check from 1.8 to 1.5 in debt swap conditions
    old_pattern = r"if health_factor < 1\.8:"
    new_replacement = "if health_factor < 1.5:"
    content = re.sub(old_pattern, new_replacement, content)
    if old_pattern in original_content:
        updates_made.append('debt_swap health check: 1.8 → 1.5')
    
    # 5. Update the print statement that shows the threshold
    old_pattern = r"❌ Health factor .* below market signal threshold 1\.8"
    new_replacement = r"❌ Health factor {health_factor:.3f} below market signal threshold 1.5"
    content = re.sub(
        r'print\(f"❌ Health factor \{health_factor:.3f\} below market signal threshold 1\.8"\)',
        'print(f"❌ Health factor {health_factor:.3f} below market signal threshold 1.5")',
        content
    )
    if "threshold 1.8" in original_content:
        updates_made.append('market signal threshold message: 1.8 → 1.5')
    
    # 6. Update hardcoded 1.8 threshold checks to 1.5
    content = re.sub(
        r"if health_factor < 1\.8:",
        "if health_factor < 1.5:",
        content
    )
    
    # 7. Update return statements that reference 1.8 threshold
    content = re.sub(
        r'return False, f"Health factor too low: \{health_factor:.3f\} \(need >1\.8\)"',
        'return False, f"Health factor too low: {health_factor:.3f} (need >1.5)"',
        content
    )
    if "(need >1.8)" in original_content:
        updates_made.append('error messages: >1.8 → >1.5')
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    changes_made = original_content != content
    print(f"✅ arbitrum_testnet_agent.py updated - Changes made: {changes_made}")
    
    return {
        'file': file_path,
        'backup': backup_path,
        'changes_made': changes_made,
        'updates': updates_made
    }

def update_agent_config_json():
    """Update agent_config.json if it exists and contains health factor settings"""
    print("🔧 Checking agent_config.json...")
    
    file_path = "agent_config.json"
    
    if not os.path.exists(file_path):
        print(f"ℹ️ {file_path} does not exist - skipping")
        return {
            'file': file_path,
            'exists': False,
            'changes_made': False
        }
    
    backup_path = backup_file(file_path)
    
    try:
        with open(file_path, 'r') as f:
            config = json.load(f)
        
        original_config = config.copy()
        updates_made = []
        
        # Look for health factor related settings
        health_factor_keys = [
            'min_health_factor', 'target_health_factor', 'safe_health_factor',
            'growth_health_factor_threshold', 'capacity_health_factor_threshold'
        ]
        
        for key in health_factor_keys:
            if key in config and isinstance(config[key], (int, float)):
                if config[key] == 2.0:
                    config[key] = 1.5
                    updates_made.append(f'{key}: 2.0 → 1.5')
                elif config[key] == 1.8:
                    config[key] = 1.5
                    updates_made.append(f'{key}: 1.8 → 1.5')
                elif config[key] == 2.5:
                    config[key] = 1.5
                    updates_made.append(f'{key}: 2.5 → 1.5')
        
        # Save updated config
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        changes_made = original_config != config
        print(f"✅ agent_config.json updated - Changes made: {changes_made}")
        
        return {
            'file': file_path,
            'exists': True,
            'backup': backup_path,
            'changes_made': changes_made,
            'updates': updates_made
        }
        
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON in {file_path}: {e}")
        return {
            'file': file_path,
            'exists': True,
            'error': str(e),
            'changes_made': False
        }

def find_and_update_other_health_files():
    """Find and update other files that might contain health factor thresholds"""
    print("🔍 Searching for other health factor configuration files...")
    
    # List of potential files to check
    potential_files = [
        'aave_health_monitor.py',
        'enhanced_borrow_manager.py',
        'transaction_safety_checker.py',
        'config.py',
        'config_constants.py'
    ]
    
    results = []
    
    for file_path in potential_files:
        if os.path.exists(file_path):
            print(f"🔧 Checking {file_path}...")
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check if it contains health factor thresholds
            if re.search(r'health.*factor.*[>=<].*[12]\.[0-9]', content, re.IGNORECASE):
                backup_path = backup_file(file_path)
                original_content = content
                updates_made = []
                
                # Update common patterns
                # 2.0 -> 1.5
                if '2.0' in content and 'health' in content.lower():
                    content = re.sub(r'([Hh]ealth.*[Ff]actor.*[>=<]?\s*)2\.0', r'\g<1>1.5', content)
                    updates_made.append('2.0 → 1.5')
                
                # 1.8 -> 1.5  
                if '1.8' in content and 'health' in content.lower():
                    content = re.sub(r'([Hh]ealth.*[Ff]actor.*[>=<]?\s*)1\.8', r'\g<1>1.5', content)
                    updates_made.append('1.8 → 1.5')
                
                # 2.5 -> 1.5
                if '2.5' in content and 'health' in content.lower():
                    content = re.sub(r'([Hh]ealth.*[Ff]actor.*[>=<]?\s*)2\.5', r'\g<1>1.5', content)
                    updates_made.append('2.5 → 1.5')
                
                # Save if changes were made
                if content != original_content:
                    with open(file_path, 'w') as f:
                        f.write(content)
                    
                    results.append({
                        'file': file_path,
                        'backup': backup_path,
                        'changes_made': True,
                        'updates': updates_made
                    })
                    print(f"✅ {file_path} updated")
                else:
                    results.append({
                        'file': file_path,
                        'changes_made': False
                    })
                    print(f"ℹ️ {file_path} - no changes needed")
            else:
                print(f"ℹ️ {file_path} - no health factor thresholds found")
    
    return results

def verify_configuration_changes():
    """Verify that configuration changes were applied correctly"""
    print("\n🔍 VERIFYING CONFIGURATION CHANGES")
    print("=" * 50)
    
    verification_results = {}
    
    # 1. Check environmental_configuration.py
    if os.path.exists('environmental_configuration.py'):
        with open('environmental_configuration.py', 'r') as f:
            content = f.read()
        
        target_health_match = re.search(r"TARGET_HEALTH_FACTOR = float\(os\.getenv\('TARGET_HEALTH_FACTOR', '([^']+)'\)\)", content)
        if target_health_match:
            verification_results['environmental_config_target_health'] = target_health_match.group(1)
            print(f"📊 environmental_configuration.py - TARGET_HEALTH_FACTOR: {target_health_match.group(1)}")
        else:
            verification_results['environmental_config_target_health'] = 'NOT_FOUND'
            print("❌ environmental_configuration.py - TARGET_HEALTH_FACTOR not found")
    
    # 2. Check arbitrum_testnet_agent.py
    if os.path.exists('arbitrum_testnet_agent.py'):
        with open('arbitrum_testnet_agent.py', 'r') as f:
            content = f.read()
        
        # Check various thresholds
        growth_match = re.search(r'self\.growth_health_factor_threshold = ([0-9.]+)', content)
        capacity_match = re.search(r'self\.capacity_health_factor_threshold = ([0-9.]+)', content)
        target_match = re.search(r'self\.target_health_factor = ([0-9.]+)', content)
        
        verification_results['agent_growth_threshold'] = growth_match.group(1) if growth_match else 'NOT_FOUND'
        verification_results['agent_capacity_threshold'] = capacity_match.group(1) if capacity_match else 'NOT_FOUND'
        verification_results['agent_target_threshold'] = target_match.group(1) if target_match else 'NOT_FOUND'
        
        print(f"📊 arbitrum_testnet_agent.py:")
        print(f"   - growth_health_factor_threshold: {verification_results['agent_growth_threshold']}")
        print(f"   - capacity_health_factor_threshold: {verification_results['agent_capacity_threshold']}")
        print(f"   - target_health_factor: {verification_results['agent_target_threshold']}")
    
    return verification_results

def main():
    """Execute the health factor configuration update"""
    print("🔧 HEALTH FACTOR CONFIGURATION UPDATE SCRIPT")
    print("=" * 60)
    print("Changing minimum health factor requirement from 2.0 to 1.5")
    print("=" * 60)
    
    # Record start time
    start_time = datetime.now()
    
    # Store all results
    update_results = {
        'timestamp': start_time.isoformat(),
        'updates_performed': []
    }
    
    try:
        # 1. Update environmental_configuration.py
        env_result = update_environmental_configuration()
        update_results['updates_performed'].append(env_result)
        
        # 2. Update arbitrum_testnet_agent.py
        agent_result = update_arbitrum_testnet_agent()
        update_results['updates_performed'].append(agent_result)
        
        # 3. Update agent_config.json if it exists
        config_result = update_agent_config_json()
        update_results['updates_performed'].append(config_result)
        
        # 4. Find and update other health monitoring files
        other_results = find_and_update_other_health_files()
        update_results['updates_performed'].extend(other_results)
        
        # 5. Verify changes
        verification_results = verify_configuration_changes()
        update_results['verification'] = verification_results
        
        print("\n✅ CONFIGURATION UPDATE COMPLETE")
        print("=" * 60)
        
        # Summary of changes
        total_files_changed = sum(1 for result in update_results['updates_performed'] if result.get('changes_made', False))
        print(f"📊 Files Updated: {total_files_changed}")
        
        for result in update_results['updates_performed']:
            if result.get('changes_made', False):
                print(f"   ✅ {result['file']}")
                if 'updates' in result:
                    for update in result['updates']:
                        print(f"      - {update}")
        
        # Save results
        results_filename = f"health_factor_update_results_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_filename, 'w') as f:
            json.dump(update_results, f, indent=2, default=str)
        
        print(f"\n📁 Update results saved to: {results_filename}")
        
        return update_results
        
    except Exception as e:
        print(f"❌ Configuration update failed: {e}")
        import traceback
        traceback.print_exc()
        
        update_results['error'] = str(e)
        update_results['error_details'] = traceback.format_exc()
        
        return update_results

if __name__ == "__main__":
    main()