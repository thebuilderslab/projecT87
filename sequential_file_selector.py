#!/usr/bin/env python3
"""
Sequential File Selection System for DeFi Automation
Implements 5-approach framework for intelligent file selection with comprehensive audit trails.

CORE SELECTION APPROACHES:
1. Latest Modified File Approach - Select most recently modified files in each category
2. Last Used Per Log Approach - Select files based on historical usage logs
3. Config-Declared Preferred File Approach - Use pre-configured preferred files
4. Majority Active in Recent Runs Approach - Select most frequently used files
5. Manual Override/Fallback Approach - Manual selection and fallback mechanisms

Generates both human-readable (Markdown) and machine-readable (JSON) audit reports.
"""

import os
import json
import time
import glob
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import importlib.util

class SequentialFileSelector:
    """
    Comprehensive file selection system implementing 5-approach framework
    for DeFi automation with full audit trail generation.
    """
    
    def __init__(self, base_directory: str = "."):
        """Initialize the sequential file selector"""
        self.base_directory = Path(base_directory)
        self.usage_log_file = self.base_directory / "file_usage_log.json"
        self.config_file = self.base_directory / "file_selection_config.json"
        self.audit_log = []
        
        # File category mappings
        self.file_categories = {
            'monitoring': [
                'aave_health_monitor.py',
                'check_wallet_balance.py', 
                'check_balances.py',
                'debug_agent_position.py',
                'enhanced_market_analyzer.py',
                'accurate_debank_fetcher.py',
                'wallet_diagnostics.py'
            ],
            'transaction': [
                'production_debt_swap_executor.py',
                'comprehensive_debt_swap_executor.py',
                'transaction_verifier.py',
                'mainnet_transaction_decoder.py',
                'enhanced_debt_swap_with_verification.py',
                'final_debt_swap_executor.py',
                'real_debt_swap_executor.py'
            ],
            'validation': [
                'comprehensive_transaction_validator.py',
                'contract_validator.py',
                'validation_integration_demo.py',
                'contract_validation_tool.py',
                'comprehensive_system_verifier.py',
                'confidence_validator.py',
                'enhanced_system_validator.py'
            ],
            'wallet': [
                'wallet_diagnostics.py',
                'check_wallet_value.py',
                'check_wallet_balance.py',
                'arbitrum_testnet_agent.py'
            ],
            'balance': [
                'check_balances.py',
                'check_wallet_balance.py',
                'accurate_debank_fetcher.py'
            ],
            'gas_optimization': [
                'gas_optimization.py',
                'gas_fee_calculator.py'
            ]
        }
        
        # Initialize logs and configuration
        self._initialize_logs()
        self._load_config()
        
        print("🎯 Sequential File Selector initialized")
        print(f"   Base Directory: {self.base_directory}")
        print(f"   Categories: {list(self.file_categories.keys())}")
        print(f"   Usage Log: {self.usage_log_file}")

    def _initialize_logs(self):
        """Initialize usage logs if they don't exist"""
        if not self.usage_log_file.exists():
            initial_log = {
                'created': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'usage_history': {},
                'selection_history': []
            }
            with open(self.usage_log_file, 'w') as f:
                json.dump(initial_log, f, indent=2)
        
        with open(self.usage_log_file, 'r') as f:
            self.usage_logs = json.load(f)

    def _load_config(self):
        """Load configuration file with preferred files"""
        default_config = {
            'preferred_files': {
                'monitoring': 'aave_health_monitor.py',
                'transaction': 'production_debt_swap_executor.py',
                'validation': 'comprehensive_transaction_validator.py',
                'wallet': 'wallet_diagnostics.py',
                'balance': 'check_wallet_balance.py',
                'gas_optimization': 'gas_optimization.py'
            },
            'fallback_files': {
                'monitoring': 'check_wallet_balance.py',
                'transaction': 'comprehensive_debt_swap_executor.py',
                'validation': 'contract_validator.py',
                'wallet': 'arbitrum_testnet_agent.py',
                'balance': 'check_balances.py',
                'gas_optimization': 'gas_fee_calculator.py'
            },
            'selection_weights': {
                'latest_modified': 0.25,
                'last_used_per_log': 0.25,
                'config_preferred': 0.25,
                'majority_active': 0.15,
                'manual_override': 0.10
            }
        }
        
        if not self.config_file.exists():
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
        
        with open(self.config_file, 'r') as f:
            self.config = json.load(f)

    def scan_available_files(self) -> Dict[str, List[Dict]]:
        """
        Scan project directory for all available files in each category
        Returns detailed file information including modification times and existence
        """
        print(f"\n📂 SCANNING AVAILABLE FILES")
        print("=" * 50)
        
        available_files = {}
        
        for category, file_list in self.file_categories.items():
            available_files[category] = []
            
            print(f"\n📁 Category: {category.upper()}")
            print("-" * 30)
            
            for filename in file_list:
                file_path = self.base_directory / filename
                
                file_info = {
                    'filename': filename,
                    'path': str(file_path),
                    'exists': file_path.exists(),
                    'last_modified': None,
                    'size_bytes': None,
                    'is_importable': False
                }
                
                if file_path.exists():
                    try:
                        stat = file_path.stat()
                        file_info['last_modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                        file_info['size_bytes'] = stat.st_size
                        
                        # Test if file is importable
                        try:
                            spec = importlib.util.spec_from_file_location("test_module", file_path)
                            if spec is not None:
                                file_info['is_importable'] = True
                        except:
                            file_info['is_importable'] = False
                        
                        print(f"   ✅ {filename:<35} | Modified: {file_info['last_modified'][:16]} | Size: {file_info['size_bytes']:,} bytes")
                    except Exception as e:
                        print(f"   ⚠️  {filename:<35} | Error reading file info: {str(e)}")
                else:
                    print(f"   ❌ {filename:<35} | File not found")
                
                available_files[category].append(file_info)
        
        return available_files

    def approach_1_latest_modified(self, available_files: Dict) -> Dict[str, str]:
        """
        Approach 1: Latest Modified File Selection
        Select the most recently modified file in each category
        """
        print(f"\n🕒 APPROACH 1: LATEST MODIFIED FILE SELECTION")
        print("=" * 55)
        
        selected_files = {}
        
        for category, files in available_files.items():
            valid_files = [f for f in files if f['exists'] and f['last_modified']]
            
            if valid_files:
                # Sort by modification time (most recent first)
                latest_file = max(valid_files, key=lambda x: x['last_modified'])
                selected_files[category] = latest_file['filename']
                
                print(f"   {category:<18} → {latest_file['filename']:<35} | {latest_file['last_modified'][:16]}")
                
                self.audit_log.append({
                    'approach': 'latest_modified',
                    'category': category,
                    'selected_file': latest_file['filename'],
                    'reason': f"Most recent modification: {latest_file['last_modified'][:16]}",
                    'alternatives': len(valid_files) - 1
                })
            else:
                print(f"   {category:<18} → No valid files found")
                self.audit_log.append({
                    'approach': 'latest_modified',
                    'category': category,
                    'selected_file': None,
                    'reason': 'No valid files available',
                    'alternatives': 0
                })
        
        return selected_files

    def approach_2_last_used_per_log(self, available_files: Dict) -> Dict[str, str]:
        """
        Approach 2: Last Used Per Log Selection
        Select files based on historical usage patterns from logs
        """
        print(f"\n📊 APPROACH 2: LAST USED PER LOG SELECTION")
        print("=" * 50)
        
        selected_files = {}
        
        for category, files in available_files.items():
            valid_files = [f for f in files if f['exists']]
            
            if valid_files:
                # Check usage history for this category
                category_usage = self.usage_logs.get('usage_history', {}).get(category, {})
                
                if category_usage:
                    # Find most recently used file
                    most_recent_file = None
                    most_recent_time = None
                    
                    for file_info in valid_files:
                        filename = file_info['filename']
                        if filename in category_usage:
                            last_used = category_usage[filename].get('last_used')
                            if last_used and (most_recent_time is None or last_used > most_recent_time):
                                most_recent_time = last_used
                                most_recent_file = filename
                    
                    if most_recent_file:
                        selected_files[category] = most_recent_file
                        print(f"   {category:<18} → {most_recent_file:<35} | Last used: {most_recent_time[:16]}")
                        
                        self.audit_log.append({
                            'approach': 'last_used_per_log',
                            'category': category,
                            'selected_file': most_recent_file,
                            'reason': f"Most recently used: {most_recent_time[:16]}",
                            'usage_count': category_usage[most_recent_file].get('usage_count', 0)
                        })
                        continue
                
                # No usage history, select first valid file
                selected_files[category] = valid_files[0]['filename']
                print(f"   {category:<18} → {valid_files[0]['filename']:<35} | No usage history")
                
                self.audit_log.append({
                    'approach': 'last_used_per_log',
                    'category': category,
                    'selected_file': valid_files[0]['filename'],
                    'reason': 'No usage history available, selected first valid file',
                    'usage_count': 0
                })
            else:
                print(f"   {category:<18} → No valid files found")
                self.audit_log.append({
                    'approach': 'last_used_per_log',
                    'category': category,
                    'selected_file': None,
                    'reason': 'No valid files available',
                    'usage_count': 0
                })
        
        return selected_files

    def approach_3_config_preferred(self, available_files: Dict) -> Dict[str, str]:
        """
        Approach 3: Config-Declared Preferred File Selection
        Use pre-configured preferred files with fallback options
        """
        print(f"\n⚙️  APPROACH 3: CONFIG-DECLARED PREFERRED FILE SELECTION")
        print("=" * 60)
        
        selected_files = {}
        
        for category, files in available_files.items():
            valid_files = [f for f in files if f['exists']]
            
            if valid_files:
                preferred_file = self.config['preferred_files'].get(category)
                fallback_file = self.config['fallback_files'].get(category)
                
                # Check if preferred file exists and is valid
                preferred_exists = any(f['filename'] == preferred_file for f in valid_files)
                
                if preferred_exists:
                    selected_files[category] = preferred_file
                    print(f"   {category:<18} → {preferred_file:<35} | ✅ Preferred file")
                    
                    self.audit_log.append({
                        'approach': 'config_preferred',
                        'category': category,
                        'selected_file': preferred_file,
                        'reason': 'Configured preferred file available',
                        'had_fallback': fallback_file is not None
                    })
                else:
                    # Try fallback file
                    fallback_exists = any(f['filename'] == fallback_file for f in valid_files)
                    
                    if fallback_exists:
                        selected_files[category] = fallback_file
                        print(f"   {category:<18} → {fallback_file:<35} | 🔄 Fallback file")
                        
                        self.audit_log.append({
                            'approach': 'config_preferred',
                            'category': category,
                            'selected_file': fallback_file,
                            'reason': f'Preferred file ({preferred_file}) not available, used fallback',
                            'preferred_file': preferred_file
                        })
                    else:
                        # Use first valid file
                        selected_files[category] = valid_files[0]['filename']
                        print(f"   {category:<18} → {valid_files[0]['filename']:<35} | ⚠️  Default selection")
                        
                        self.audit_log.append({
                            'approach': 'config_preferred',
                            'category': category,
                            'selected_file': valid_files[0]['filename'],
                            'reason': f'Neither preferred ({preferred_file}) nor fallback ({fallback_file}) available',
                            'preferred_file': preferred_file,
                            'fallback_file': fallback_file
                        })
            else:
                print(f"   {category:<18} → No valid files found")
                self.audit_log.append({
                    'approach': 'config_preferred',
                    'category': category,
                    'selected_file': None,
                    'reason': 'No valid files available',
                    'preferred_file': self.config['preferred_files'].get(category)
                })
        
        return selected_files

    def approach_4_majority_active(self, available_files: Dict) -> Dict[str, str]:
        """
        Approach 4: Majority Active in Recent Runs Selection
        Select files most frequently used in recent operations (last 30 days)
        """
        print(f"\n📈 APPROACH 4: MAJORITY ACTIVE IN RECENT RUNS SELECTION")
        print("=" * 60)
        
        selected_files = {}
        cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()
        
        for category, files in available_files.items():
            valid_files = [f for f in files if f['exists']]
            
            if valid_files:
                # Count recent usage for each file
                recent_usage = {}
                category_usage = self.usage_logs.get('usage_history', {}).get(category, {})
                
                for file_info in valid_files:
                    filename = file_info['filename']
                    if filename in category_usage:
                        file_usage = category_usage[filename]
                        # Count recent usage
                        recent_count = 0
                        for usage_date in file_usage.get('usage_dates', []):
                            if usage_date >= cutoff_date:
                                recent_count += 1
                        recent_usage[filename] = recent_count
                    else:
                        recent_usage[filename] = 0
                
                # Select file with highest recent usage
                if any(count > 0 for count in recent_usage.values()):
                    most_active_file = max(recent_usage, key=recent_usage.get)
                    selected_files[category] = most_active_file
                    print(f"   {category:<18} → {most_active_file:<35} | Used {recent_usage[most_active_file]} times (30d)")
                    
                    self.audit_log.append({
                        'approach': 'majority_active',
                        'category': category,
                        'selected_file': most_active_file,
                        'reason': f'Most active in recent runs: {recent_usage[most_active_file]} uses',
                        'recent_usage_count': recent_usage[most_active_file],
                        'analysis_period': '30 days'
                    })
                else:
                    # No recent usage, select first valid file
                    selected_files[category] = valid_files[0]['filename']
                    print(f"   {category:<18} → {valid_files[0]['filename']:<35} | No recent activity")
                    
                    self.audit_log.append({
                        'approach': 'majority_active',
                        'category': category,
                        'selected_file': valid_files[0]['filename'],
                        'reason': 'No recent usage data, selected first valid file',
                        'recent_usage_count': 0,
                        'analysis_period': '30 days'
                    })
            else:
                print(f"   {category:<18} → No valid files found")
                self.audit_log.append({
                    'approach': 'majority_active',
                    'category': category,
                    'selected_file': None,
                    'reason': 'No valid files available',
                    'recent_usage_count': 0
                })
        
        return selected_files

    def approach_5_manual_override(self, available_files: Dict, manual_selections: Optional[Dict] = None) -> Dict[str, str]:
        """
        Approach 5: Manual Override/Fallback Selection
        Allow manual file selection with intelligent fallback mechanisms
        """
        print(f"\n🎛️  APPROACH 5: MANUAL OVERRIDE/FALLBACK SELECTION")
        print("=" * 55)
        
        selected_files = {}
        manual_selections = manual_selections or {}
        
        for category, files in available_files.items():
            valid_files = [f for f in files if f['exists']]
            
            if valid_files:
                # Check for manual override
                manual_choice = manual_selections.get(category)
                
                if manual_choice:
                    # Validate manual choice exists
                    manual_exists = any(f['filename'] == manual_choice for f in valid_files)
                    
                    if manual_exists:
                        selected_files[category] = manual_choice
                        print(f"   {category:<18} → {manual_choice:<35} | 👤 Manual selection")
                        
                        self.audit_log.append({
                            'approach': 'manual_override',
                            'category': category,
                            'selected_file': manual_choice,
                            'reason': 'Manual override selection',
                            'override_type': 'user_specified'
                        })
                    else:
                        print(f"   {category:<18} → ❌ Manual choice '{manual_choice}' not found")
                        # Fall back to intelligent selection
                        fallback_file = self._intelligent_fallback_selection(category, valid_files)
                        selected_files[category] = fallback_file
                        print(f"   {category:<18} → {fallback_file:<35} | 🤖 Intelligent fallback")
                        
                        self.audit_log.append({
                            'approach': 'manual_override',
                            'category': category,
                            'selected_file': fallback_file,
                            'reason': f'Manual choice "{manual_choice}" not available, used intelligent fallback',
                            'override_type': 'intelligent_fallback'
                        })
                else:
                    # No manual override, use intelligent fallback
                    fallback_file = self._intelligent_fallback_selection(category, valid_files)
                    selected_files[category] = fallback_file
                    print(f"   {category:<18} → {fallback_file:<35} | 🤖 Intelligent fallback")
                    
                    self.audit_log.append({
                        'approach': 'manual_override',
                        'category': category,
                        'selected_file': fallback_file,
                        'reason': 'No manual override, used intelligent fallback',
                        'override_type': 'intelligent_fallback'
                    })
            else:
                print(f"   {category:<18} → No valid files found")
                self.audit_log.append({
                    'approach': 'manual_override',
                    'category': category,
                    'selected_file': None,
                    'reason': 'No valid files available',
                    'override_type': 'none'
                })
        
        return selected_files

    def _intelligent_fallback_selection(self, category: str, valid_files: List[Dict]) -> str:
        """
        Intelligent fallback selection combining multiple criteria
        """
        if not valid_files:
            return None
        
        # Scoring system for intelligent fallback
        scores = {}
        
        for file_info in valid_files:
            filename = file_info['filename']
            score = 0
            
            # Factor 1: File size (larger files might be more comprehensive)
            if file_info.get('size_bytes', 0) > 10000:  # > 10KB
                score += 2
            
            # Factor 2: Recent modification (more recent = better)
            if file_info.get('last_modified'):
                mod_time = datetime.fromisoformat(file_info['last_modified'])
                days_old = (datetime.now() - mod_time).days
                if days_old < 7:
                    score += 3
                elif days_old < 30:
                    score += 1
            
            # Factor 3: Importability
            if file_info.get('is_importable', False):
                score += 2
            
            # Factor 4: Preferred/fallback file bonus
            if filename == self.config['preferred_files'].get(category):
                score += 5
            elif filename == self.config['fallback_files'].get(category):
                score += 3
            
            # Factor 5: Usage history
            category_usage = self.usage_logs.get('usage_history', {}).get(category, {})
            if filename in category_usage:
                usage_count = category_usage[filename].get('usage_count', 0)
                score += min(usage_count, 5)  # Cap at 5 points
            
            scores[filename] = score
        
        # Return file with highest score
        best_file = max(scores, key=scores.get)
        return best_file

    def consolidate_selections(self, approach_results: Dict[str, Dict[str, str]]) -> Dict[str, str]:
        """
        Consolidate results from all 5 approaches using weighted scoring system
        """
        print(f"\n🎯 CONSOLIDATING SELECTIONS FROM ALL APPROACHES")
        print("=" * 60)
        
        weights = self.config['selection_weights']
        final_selections = {}
        
        for category in self.file_categories.keys():
            # Count votes for each file in this category
            file_votes = {}
            
            for approach, selections in approach_results.items():
                selected_file = selections.get(category)
                if selected_file:
                    weight = weights.get(approach, 0.1)
                    file_votes[selected_file] = file_votes.get(selected_file, 0) + weight
            
            if file_votes:
                # Select file with highest weighted score
                winning_file = max(file_votes, key=file_votes.get)
                final_selections[category] = winning_file
                
                print(f"   {category:<18} → {winning_file:<35} | Score: {file_votes[winning_file]:.2f}")
                
                # Log consolidation decision
                self.audit_log.append({
                    'step': 'consolidation',
                    'category': category,
                    'selected_file': winning_file,
                    'weighted_score': file_votes[winning_file],
                    'all_votes': file_votes,
                    'decision_basis': 'weighted_approach_scoring'
                })
            else:
                print(f"   {category:<18} → No valid selections found")
                self.audit_log.append({
                    'step': 'consolidation',
                    'category': category,
                    'selected_file': None,
                    'weighted_score': 0,
                    'all_votes': {},
                    'decision_basis': 'no_valid_selections'
                })
        
        return final_selections

    def log_file_usage(self, category: str, filename: str, operation: str, result: str):
        """
        Log file usage for future selection decisions
        """
        current_time = datetime.now().isoformat()
        
        # Initialize category if doesn't exist
        if 'usage_history' not in self.usage_logs:
            self.usage_logs['usage_history'] = {}
        if category not in self.usage_logs['usage_history']:
            self.usage_logs['usage_history'][category] = {}
        if filename not in self.usage_logs['usage_history'][category]:
            self.usage_logs['usage_history'][category][filename] = {
                'usage_count': 0,
                'usage_dates': [],
                'operations': [],
                'results': []
            }
        
        # Update usage data
        file_usage = self.usage_logs['usage_history'][category][filename]
        file_usage['usage_count'] += 1
        file_usage['usage_dates'].append(current_time)
        file_usage['operations'].append(operation)
        file_usage['results'].append(result)
        file_usage['last_used'] = current_time
        
        # Keep only last 100 entries to prevent log bloat
        for key in ['usage_dates', 'operations', 'results']:
            if len(file_usage[key]) > 100:
                file_usage[key] = file_usage[key][-100:]
        
        # Update overall log metadata
        self.usage_logs['last_updated'] = current_time
        
        # Save to file
        with open(self.usage_log_file, 'w') as f:
            json.dump(self.usage_logs, f, indent=2)

    def execute_file_selection_sequence(self, manual_overrides: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute the complete 5-approach file selection sequence
        Returns comprehensive results with audit trail
        """
        print(f"\n🚀 EXECUTING SEQUENTIAL FILE SELECTION SYSTEM")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Base Directory: {self.base_directory}")
        print(f"Manual Overrides: {manual_overrides or 'None'}")
        
        # Reset audit log for this execution
        self.audit_log = []
        execution_start = time.time()
        
        # Step 1: Scan available files
        available_files = self.scan_available_files()
        
        # Step 2: Execute all 5 approaches
        approach_results = {}
        
        approach_results['latest_modified'] = self.approach_1_latest_modified(available_files)
        approach_results['last_used_per_log'] = self.approach_2_last_used_per_log(available_files)
        approach_results['config_preferred'] = self.approach_3_config_preferred(available_files)
        approach_results['majority_active'] = self.approach_4_majority_active(available_files)
        approach_results['manual_override'] = self.approach_5_manual_override(available_files, manual_overrides)
        
        # Step 3: Consolidate selections
        final_selections = self.consolidate_selections(approach_results)
        
        # Step 4: Generate comprehensive result
        execution_time = time.time() - execution_start
        
        result = {
            'execution_metadata': {
                'timestamp': datetime.now().isoformat(),
                'execution_time_seconds': execution_time,
                'base_directory': str(self.base_directory),
                'manual_overrides': manual_overrides or {}
            },
            'available_files': available_files,
            'approach_results': approach_results,
            'final_selections': final_selections,
            'audit_log': self.audit_log,
            'statistics': self._generate_selection_statistics(approach_results, final_selections)
        }
        
        print(f"\n✅ File selection sequence completed in {execution_time:.2f} seconds")
        print(f"   Final selections: {len([f for f in final_selections.values() if f])} files selected")
        
        return result

    def _generate_selection_statistics(self, approach_results: Dict, final_selections: Dict) -> Dict:
        """Generate statistics about the selection process"""
        stats = {
            'total_categories': len(self.file_categories),
            'successful_selections': len([f for f in final_selections.values() if f]),
            'failed_selections': len([f for f in final_selections.values() if not f]),
            'approach_agreement': {},
            'selection_confidence': {}
        }
        
        # Calculate approach agreement
        for category in self.file_categories.keys():
            agreement_count = 0
            final_file = final_selections.get(category)
            
            if final_file:
                for approach_selections in approach_results.values():
                    if approach_selections.get(category) == final_file:
                        agreement_count += 1
                
                stats['approach_agreement'][category] = agreement_count / len(approach_results)
                stats['selection_confidence'][category] = 'high' if agreement_count >= 3 else 'medium' if agreement_count >= 2 else 'low'
            else:
                stats['approach_agreement'][category] = 0
                stats['selection_confidence'][category] = 'none'
        
        return stats

    def generate_markdown_report(self, selection_result: Dict) -> str:
        """
        Generate human-readable Markdown audit report
        """
        report = []
        report.append("# Sequential File Selection Audit Report")
        report.append(f"**Generated:** {selection_result['execution_metadata']['timestamp']}")
        report.append(f"**Execution Time:** {selection_result['execution_metadata']['execution_time_seconds']:.2f} seconds")
        report.append("")
        
        # Summary table
        report.append("## Final File Selection Summary")
        report.append("")
        report.append("| Step        | File Name           | Action      | Last Modified      | Used/Skipped | Result/Issue        |")
        report.append("|-------------|---------------------|-------------|--------------------|--------------|---------------------|")
        
        for category, filename in selection_result['final_selections'].items():
            if filename:
                # Find file details
                file_info = None
                for file_data in selection_result['available_files'].get(category, []):
                    if file_data['filename'] == filename:
                        file_info = file_data
                        break
                
                if file_info:
                    last_modified = file_info.get('last_modified', 'Unknown')[:16] if file_info.get('last_modified') else 'Unknown'
                    action = f"{category.title()} Check"
                    used_skipped = "✅ Used"
                    result = f"Selected via weighted approach scoring"
                else:
                    last_modified = "Unknown"
                    action = f"{category.title()} Check"
                    used_skipped = "⚠️ Unknown"
                    result = "File details not found"
                
                report.append(f"| {action:<11} | {filename:<19} | Execute     | {last_modified:<18} | {used_skipped:<12} | {result:<19} |")
            else:
                action = f"{category.title()} Check"
                report.append(f"| {action:<11} | No file selected   | Skip        | N/A                | ❌ Skipped   | No valid files      |")
        
        report.append("")
        
        # Detailed approach results
        report.append("## Approach-by-Approach Results")
        report.append("")
        
        for approach_name, selections in selection_result['approach_results'].items():
            report.append(f"### {approach_name.replace('_', ' ').title()}")
            report.append("")
            
            for category, filename in selections.items():
                if filename:
                    report.append(f"- **{category}**: {filename}")
                else:
                    report.append(f"- **{category}**: No selection")
            report.append("")
        
        # Statistics
        stats = selection_result['statistics']
        report.append("## Selection Statistics")
        report.append("")
        report.append(f"- **Total Categories**: {stats['total_categories']}")
        report.append(f"- **Successful Selections**: {stats['successful_selections']}")
        report.append(f"- **Failed Selections**: {stats['failed_selections']}")
        report.append("")
        
        report.append("### Selection Confidence by Category")
        report.append("")
        for category, confidence in stats['selection_confidence'].items():
            agreement = stats['approach_agreement'][category]
            report.append(f"- **{category}**: {confidence} confidence ({agreement:.1%} agreement)")
        
        return "\n".join(report)

    def generate_json_report(self, selection_result: Dict) -> str:
        """
        Generate machine-readable JSON audit report
        """
        return json.dumps(selection_result, indent=2, default=str)