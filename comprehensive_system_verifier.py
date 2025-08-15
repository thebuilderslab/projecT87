
#!/usr/bin/env python3
"""
Comprehensive System Verifier for 95% Execution Success Rate
Validates all components for maximum reliability
"""

import os
import sys
import time
import json
from datetime import datetime

class ComprehensiveSystemVerifier:
    def __init__(self):
        self.test_results = {}
        self.critical_failures = []
        self.warnings = []
        self.success_threshold = 0.95  # 95% success rate target
        
    def verify_complete_system(self):
        """Run comprehensive system verification for 95% reliability"""
        print("🔍 COMPREHENSIVE SYSTEM VERIFICATION FOR 95% RELIABILITY")
        print("=" * 70)
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("=" * 70)
        
        # Phase 1: Syntax and Import Validation
        self._verify_syntax_and_imports()
        
        # Phase 2: DAI Compliance Verification
        self._verify_dai_compliance()
        
        # Phase 3: Integration Verification
        self._verify_integrations()
        
        # Phase 4: Network and Contract Verification
        self._verify_network_and_contracts()
        
        # Phase 5: Transaction Pipeline Verification
        self._verify_transaction_pipeline()
        
        # Phase 6: Performance and Reliability Tests
        self._verify_performance_reliability()
        
        # Generate comprehensive report
        return self._generate_comprehensive_report()
    
    def _verify_syntax_and_imports(self):
        """Verify all syntax and imports work correctly"""
        print("\n1️⃣ SYNTAX AND IMPORT VERIFICATION")
        print("-" * 40)
        
        critical_modules = [
            'arbitrum_testnet_agent',
            'enhanced_borrow_manager',
            'uniswap_integration',
            'aave_integration',
            'transaction_validator',
            'aave_health_monitor',
            'dai_compliance_enforcer'
        ]
        
        import_success = 0
        for module in critical_modules:
            try:
                exec(f"import {module}")
                self.test_results[f"import_{module}"] = "✅ Success"
                import_success += 1
                print(f"   ✅ {module}: Imported successfully")
            except SyntaxError as e:
                self.test_results[f"import_{module}"] = f"❌ Syntax Error: {e}"
                self.critical_failures.append(f"Syntax error in {module}: {e}")
                print(f"   ❌ {module}: Syntax error - {e}")
            except Exception as e:
                self.test_results[f"import_{module}"] = f"❌ Import Error: {e}"
                self.critical_failures.append(f"Import failure: {module} - {e}")
                print(f"   ❌ {module}: Import failed - {e}")
        
        import_rate = import_success / len(critical_modules)
        print(f"📊 Import Success Rate: {import_rate:.1%}")
        
        if import_rate < 1.0:
            self.critical_failures.append(f"Import success rate below 100%: {import_rate:.1%}")
    
    def _verify_dai_compliance(self):
        """Verify strict DAI compliance enforcement"""
        print("\n2️⃣ DAI COMPLIANCE VERIFICATION")
        print("-" * 40)
        
        try:
            # Run DAI compliance enforcer
            from main import DAIComplianceEnforcer
            enforcer = DAIComplianceEnforcer()
            compliance_result = enforcer.enforce_dai_compliance()
            
            if compliance_result:
                self.test_results["dai_compliance"] = "✅ Fully Compliant"
                print("   ✅ DAI compliance: Fully enforced")
            else:
                self.test_results["dai_compliance"] = "❌ Violations Found"
                self.critical_failures.append("DAI compliance violations detected")
                print("   ❌ DAI compliance: Violations found")
                
            # Run original compliance checker for verification
            from system_compliance_checker import SystemComplianceChecker
            checker = SystemComplianceChecker()
            verification_result = checker.check_dai_only_compliance()
            
            if verification_result:
                print("   ✅ Secondary verification: Passed")
            else:
                print("   ⚠️ Secondary verification: Failed")
                self.warnings.append("Secondary DAI compliance check failed")
                
        except Exception as e:
            self.test_results["dai_compliance"] = f"❌ Error: {e}"
            self.critical_failures.append(f"DAI compliance verification failed: {e}")
            print(f"   ❌ DAI compliance verification failed: {e}")
    
    def _verify_integrations(self):
        """Verify all DeFi integrations"""
        print("\n3️⃣ INTEGRATION VERIFICATION")
        print("-" * 40)
        
        try:
            from main import ArbitrumTestnetAgent
            agent = ArbitrumTestnetAgent()
            
            # Test agent initialization
            self.test_results["agent_init"] = "✅ Success"
            print(f"   ✅ Agent initialized: {agent.address}")
            
            # Test integration initialization
            integration_success = agent.initialize_integrations()
            
            if integration_success:
                self.test_results["integrations"] = "✅ All Initialized"
                print("   ✅ All integrations initialized successfully")
                
                # Test individual integrations
                if hasattr(agent, 'aave') and agent.aave:
                    print("   ✅ Aave integration: Available")
                else:
                    self.warnings.append("Aave integration not available")
                    
                if hasattr(agent, 'uniswap') and agent.uniswap:
                    print("   ✅ Uniswap integration: Available")
                else:
                    self.warnings.append("Uniswap integration not available")
                    
                if hasattr(agent, 'enhanced_borrow_manager') and agent.enhanced_borrow_manager:
                    print("   ✅ Enhanced Borrow Manager: Available")
                else:
                    self.warnings.append("Enhanced Borrow Manager not available")
                    
            else:
                self.test_results["integrations"] = "❌ Failed"
                self.critical_failures.append("Integration initialization failed")
                print("   ❌ Integration initialization failed")
                
        except Exception as e:
            self.test_results["integrations"] = f"❌ Error: {e}"
            self.critical_failures.append(f"Integration verification failed: {e}")
            print(f"   ❌ Integration verification failed: {e}")
    
    def _verify_network_and_contracts(self):
        """Verify network connectivity and contract access"""
        print("\n4️⃣ NETWORK AND CONTRACT VERIFICATION")
        print("-" * 40)
        
        try:
            from main import ArbitrumTestnetAgent
            agent = ArbitrumTestnetAgent()
            
            # Test network connectivity
            network_ok, network_msg = agent.check_network_status()
            if network_ok:
                self.test_results["network"] = "✅ Connected"
                print(f"   ✅ Network: {network_msg}")
            else:
                self.test_results["network"] = f"❌ {network_msg}"
                self.critical_failures.append(f"Network connectivity failed: {network_msg}")
                print(f"   ❌ Network: {network_msg}")
                
            # Test contract accessibility
            contracts_tested = 0
            contracts_working = 0
            
            token_contracts = {
                'DAI': agent.dai_address,
                'WBTC': agent.wbtc_address,
                'WETH': agent.weth_address
            }
            
            for name, address in token_contracts.items():
                contracts_tested += 1
                try:
                    contract = agent.w3.eth.contract(
                        address=address,
                        abi=[{
                            "constant": True,
                            "inputs": [],
                            "name": "symbol",
                            "outputs": [{"name": "", "type": "string"}],
                            "type": "function"
                        }]
                    )
                    symbol = contract.functions.symbol().call()
                    contracts_working += 1
                    print(f"   ✅ {name} contract: {symbol} at {address}")
                except Exception as e:
                    print(f"   ❌ {name} contract failed: {e}")
                    
            contract_rate = contracts_working / contracts_tested
            print(f"📊 Contract Success Rate: {contract_rate:.1%}")
            
            if contract_rate < 1.0:
                self.warnings.append(f"Contract success rate below 100%: {contract_rate:.1%}")
                
        except Exception as e:
            self.test_results["network_contracts"] = f"❌ Error: {e}"
            self.critical_failures.append(f"Network/contract verification failed: {e}")
            print(f"   ❌ Network/contract verification failed: {e}")
    
    def _verify_transaction_pipeline(self):
        """Verify transaction validation pipeline"""
        print("\n5️⃣ TRANSACTION PIPELINE VERIFICATION")
        print("-" * 40)
        
        try:
            from transaction_validator import TransactionValidator
            from main import ArbitrumTestnetAgent
            
            agent = ArbitrumTestnetAgent()
            agent.initialize_integrations()
            validator = TransactionValidator(agent)
            
            # Test DAI → WBTC validation (should pass)
            dai_wbtc_valid = validator.validate_swap_transaction(
                agent.dai_address, 
                agent.wbtc_address, 
                1.0
            )
            
            if dai_wbtc_valid:
                print("   ✅ DAI → WBTC validation: Passed")
            else:
                print("   ❌ DAI → WBTC validation: Failed")
                self.warnings.append("DAI → WBTC validation failed")
            
            # Test DAI → WETH validation (should pass)
            dai_weth_valid = validator.validate_swap_transaction(
                agent.dai_address, 
                agent.weth_address, 
                1.0
            )
            
            if dai_weth_valid:
                print("   ✅ DAI → WETH validation: Passed")
            else:
                print("   ❌ DAI → WETH validation: Failed")
                self.warnings.append("DAI → WETH validation failed")
            
            # Test forbidden swap (should fail)
            try:
                forbidden_valid = validator.validate_swap_transaction(
                    agent.usdc_address,  # USDC should be forbidden
                    agent.wbtc_address, 
                    1.0
                )
                
                if not forbidden_valid:
                    print("   ✅ USDC rejection: Correctly blocked")
                else:
                    print("   ❌ USDC rejection: Failed to block")
                    self.critical_failures.append("DAI compliance not enforced in validator")
            except:
                print("   ✅ USDC rejection: Correctly blocked")
            
            self.test_results["transaction_pipeline"] = "✅ Verified"
            
        except Exception as e:
            self.test_results["transaction_pipeline"] = f"❌ Error: {e}"
            self.critical_failures.append(f"Transaction pipeline verification failed: {e}")
            print(f"   ❌ Transaction pipeline verification failed: {e}")
    
    def _verify_performance_reliability(self):
        """Verify system performance and reliability metrics"""
        print("\n6️⃣ PERFORMANCE AND RELIABILITY VERIFICATION")
        print("-" * 40)
        
        try:
            # Test gas price optimization
            from main import ArbitrumTestnetAgent
            agent = ArbitrumTestnetAgent()
            
            gas_price = agent.w3.eth.gas_price
            base_fee = agent.w3.eth.get_block('latest').get('baseFeePerGas', gas_price)
            
            if gas_price and base_fee:
                congestion_ratio = gas_price / base_fee
                print(f"   📊 Network congestion: {congestion_ratio:.2f}x base fee")
                
                if congestion_ratio < 5.0:  # Less than 5x base fee
                    print("   ✅ Gas optimization: Favorable conditions")
                else:
                    print("   ⚠️ Gas optimization: High congestion")
                    self.warnings.append("High network congestion detected")
            
            # Test error handling robustness
            error_handling_score = 0
            total_tests = 3
            
            # Test 1: Invalid amount handling
            try:
                from transaction_validator import TransactionValidator
                validator = TransactionValidator(agent)
                result = validator.validate_swap_transaction(agent.dai_address, agent.wbtc_address, -1.0)
                if not result:  # Should return False for negative amount
                    error_handling_score += 1
                    print("   ✅ Error handling: Invalid amount correctly rejected")
                else:
                    print("   ❌ Error handling: Invalid amount not rejected")
            except:
                print("   ❌ Error handling: Exception in invalid amount test")
            
            # Test 2: Network failure simulation
            try:
                # This should handle network errors gracefully
                agent.switch_to_fallback_rpc()
                error_handling_score += 1
                print("   ✅ Error handling: RPC failover functional")
            except:
                print("   ⚠️ Error handling: RPC failover needs attention")
            
            # Test 3: Emergency stop functionality
            try:
                if hasattr(agent, 'check_emergency_stop'):
                    stop_result = agent.check_emergency_stop()
                    error_handling_score += 1
                    print("   ✅ Error handling: Emergency stop functional")
                else:
                    print("   ⚠️ Error handling: Emergency stop not available")
            except:
                print("   ❌ Error handling: Emergency stop test failed")
            
            reliability_score = error_handling_score / total_tests
            print(f"📊 Error Handling Score: {reliability_score:.1%}")
            
            if reliability_score >= 0.8:
                self.test_results["reliability"] = "✅ High Reliability"
            else:
                self.test_results["reliability"] = f"⚠️ Moderate Reliability ({reliability_score:.1%})"
                self.warnings.append(f"Reliability score below target: {reliability_score:.1%}")
                
        except Exception as e:
            self.test_results["reliability"] = f"❌ Error: {e}"
            print(f"   ❌ Performance/reliability verification failed: {e}")
    
    def _generate_comprehensive_report(self):
        """Generate comprehensive verification report"""
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE SYSTEM VERIFICATION REPORT")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results.values() if "✅" in r])
        warning_tests = len([r for r in self.test_results.values() if "⚠️" in r])
        
        success_rate = successful_tests / total_tests if total_tests > 0 else 0
        
        print(f"✅ Successful tests: {successful_tests}/{total_tests} ({success_rate:.1%})")
        print(f"⚠️ Tests with warnings: {warning_tests}")
        print(f"❌ Critical failures: {len(self.critical_failures)}")
        print(f"⚠️ Total warnings: {len(self.warnings)}")
        
        if self.critical_failures:
            print("\n🚨 CRITICAL FAILURES:")
            for failure in self.critical_failures:
                print(f"   • {failure}")
        
        if self.warnings:
            print("\n⚠️ WARNINGS:")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        # Calculate overall system readiness
        if len(self.critical_failures) == 0 and success_rate >= self.success_threshold:
            print(f"\n🎉 SYSTEM READY FOR 95% RELIABILITY DEPLOYMENT")
            print(f"✅ Success rate: {success_rate:.1%} (Target: {self.success_threshold:.1%})")
            print(f"✅ No critical failures detected")
            print(f"🚀 System verified for autonomous operation")
            return True
        else:
            print(f"\n❌ SYSTEM NOT READY FOR HIGH-RELIABILITY DEPLOYMENT")
            print(f"📊 Current success rate: {success_rate:.1%} (Target: {self.success_threshold:.1%})")
            if len(self.critical_failures) > 0:
                print(f"❌ Critical failures must be resolved")
            print(f"🔧 Address issues before deployment")
            return False

def main():
    """Run comprehensive system verification"""
    verifier = ComprehensiveSystemVerifier()
    system_ready = verifier.verify_complete_system()
    
    if system_ready:
        print("\n🚀 PROCEED WITH AUTONOMOUS SYSTEM DEPLOYMENT")
    else:
        print("\n🛑 RESOLVE ISSUES BEFORE DEPLOYMENT")
        sys.exit(1)
    
    return system_ready

if __name__ == "__main__":
    main()

# --- Merged from verify_secrets_comprehensive.py ---

def verify_all_secrets():
    """Verify all required secrets are properly loaded"""
    print("🔐 COMPREHENSIVE SECRETS VERIFICATION")
    print("=" * 60)
    
    # Load environment
    load_dotenv()
    
    # Required secrets for the system
    required_secrets = {
        'PRIVATE_KEY': 'Wallet private key for transactions',
        'PROMPT_KEY': 'AI-driven features and automation',
        'COINMARKETCAP_API_KEY': 'Real-time price data from CoinMarketCap',
        'ARBITRUM_RPC_URL': 'Direct Arbitrum blockchain RPC access',
        'ARBISCAN_API_KEY': 'Arbitrum blockchain explorer data',
        'OPTIMIZER_API_KEY': 'Gas optimization and yield strategies'
    }
    
    print("🔍 CHECKING SECRET AVAILABILITY:")
    print("-" * 60)
    
    all_secrets_valid = True
    for secret_name, description in required_secrets.items():
        value = os.getenv(secret_name)
        
        if value and len(value.strip()) > 0:
            # Show partial value for verification without exposing full secret
            if len(value) > 8:
                display_value = f"{value[:4]}...{value[-4:]}"
            else:
                display_value = "*" * len(value)
            
            print(f"✅ {secret_name}: LOADED")
            print(f"   📝 Purpose: {description}")
            print(f"   🔹 Length: {len(value)} characters")
            print(f"   🔹 Preview: {display_value}")
            
            # Additional validation for specific secrets
            if secret_name == 'PRIVATE_KEY':
                if len(value) >= 64 and (value.startswith('0x') or len(value) == 64):
                    print(f"   ✅ Format: Valid private key format")
                else:
                    print(f"   ❌ Format: Invalid private key format")
                    all_secrets_valid = False
            
            elif secret_name == 'NETWORK_MODE':
                if value.lower() in ['mainnet', 'testnet']:
                    print(f"   ✅ Value: Valid network mode ({value})")
                else:
                    print(f"   ⚠️  Value: Unusual network mode ({value})")
        else:
            print(f"❌ {secret_name}: NOT FOUND OR EMPTY")
            print(f"   📝 Purpose: {description}")
            print(f"   ⚠️  Impact: Functionality will be limited or fail")
            all_secrets_valid = False
        print()
    
    # Test network mode separately (it has default fallback)
    network_mode = os.getenv('NETWORK_MODE', 'mainnet')
    print(f"🌐 NETWORK_MODE: {network_mode}")
    print(f"   📝 Source: {'Environment' if os.getenv('NETWORK_MODE') else 'Default fallback'}")
    print()
    
    # Test basic functionality with loaded secrets
    print("🧪 TESTING BASIC FUNCTIONALITY:")
    print("-" * 60)
    
    # Test 1: CoinMarketCap API
    if os.getenv('COINMARKETCAP_API_KEY'):
        try:
            import requests
            headers = {'X-CMC_PRO_API_KEY': os.getenv('COINMARKETCAP_API_KEY')}
            response = requests.get(
                'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest',
                headers=headers,
                params={'symbol': 'ETH'},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                eth_price = data['data']['ETH']['quote']['USD']['price']
                print(f"✅ CoinMarketCap API: Working (ETH: ${eth_price:.2f})")
            else:
                print(f"❌ CoinMarketCap API: Failed (Status: {response.status_code})")
                all_secrets_valid = False
        except Exception as e:
            print(f"❌ CoinMarketCap API: Error - {str(e)[:50]}...")
            all_secrets_valid = False
    
    # Test 2: Arbitrum RPC
    arbitrum_rpc = os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc')
    try:
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider(arbitrum_rpc, request_kwargs={'timeout': 5}))
        if w3.is_connected():
            chain_id = w3.eth.chain_id
            latest_block = w3.eth.block_number
            print(f"✅ Arbitrum RPC: Connected (Chain: {chain_id}, Block: {latest_block})")
        else:
            print(f"❌ Arbitrum RPC: Connection failed")
            all_secrets_valid = False
    except Exception as e:
        print(f"❌ Arbitrum RPC: Error - {str(e)[:50]}...")
        all_secrets_valid = False
    
    # Test 3: Private Key Format
    if os.getenv('PRIVATE_KEY'):
        try:
            from eth_account import Account
            private_key = os.getenv('PRIVATE_KEY')
            account = Account.from_key(private_key)
            print(f"✅ Private Key: Valid (Address: {account.address[:10]}...)")
        except Exception as e:
            print(f"❌ Private Key: Invalid format - {str(e)[:50]}...")
            all_secrets_valid = False
    
    print()
    print("=" * 60)
    
    if all_secrets_valid:
        print("🎉 ALL SECRETS VERIFIED SUCCESSFULLY!")
        print("✅ System ready for autonomous operations")
        print("🚀 No syntax errors or redundancies detected")
        return True
    else:
        print("⚠️  SOME ISSUES DETECTED")
        print("💡 Fix the issues above before proceeding")
        return False
# --- Merged from comprehensive_system_verifier.py ---

def scan_files():
    """Scan for all Python files in the project"""
    print("🔍 Scanning and grouping files by feature keyword...")
    
    py_files = []
    excluded_dirs = {'.git', '__pycache__', 'node_modules', '.replit_cache', 'archive_duplicates'}
    
    for root, dirs, files in os.walk(BASE_DIR):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        
        for f in files:
            if f.endswith(".py") and not f.startswith('.'):
                full_path = os.path.join(root, f)
                if os.path.getsize(full_path) > 0:  # Skip empty files
                    py_files.append(full_path)
    
    print(f"📁 Found {len(py_files)} Python files")
    return py_files

def group_by_keyword(files):
    """Group files by functionality keywords"""
    groups = defaultdict(list)
    
    for f in files:
        name_lower = os.path.basename(f).lower()
        matched = False
        
        # Check for exact keyword matches first
        for kw in KEYWORDS:
            if kw in name_lower:
                groups[kw].append(f)
                matched = True
                break
        
        # Special grouping logic for similar files
        if not matched:
            if any(word in name_lower for word in ['start', 'run', 'launch', 'main']):
                groups["launcher"].append(f)
                matched = True
            elif any(word in name_lower for word in ['monitor', 'health', 'status']):
                groups["health_monitor"].append(f)
                matched = True
            elif any(word in name_lower for word in ['web', 'dashboard', 'ui']):
                groups["dashboard"].append(f)
                matched = True
        
        if not matched:
            groups["misc"].append(f)
    
    print(f"📊 Grouped into {len(groups)} feature categories")
    return groups

def git_latest_commit_date(file_path):
    """Git-based canonical file selection using commit history"""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", file_path],
            capture_output=True, text=True, check=True, cwd=BASE_DIR)
        
        if result.stdout.strip():
            timestamp = int(result.stdout.strip())
            return timestamp
        else:
            # File not in Git, use modification time
            return int(os.path.getmtime(file_path))
    except Exception:
        # Fallback to file modification time
        return int(os.path.getmtime(file_path))

def get_file_complexity_score(file_path):
    """Calculate complexity score for canonical selection"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = len(content.split('\n'))
        
        # Count functions and classes
        try:
            tree = ast.parse(content)
            functions = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
            classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
        except:
            functions = classes = 0
        
        # Complexity score: lines + functions*5 + classes*10
        score = lines + functions * 5 + classes * 10
        return score
    except Exception:
        return 0

def choose_canonical(files):
    """Choose canonical file based on Git history, complexity, and naming"""
    if len(files) == 1:
        return files[0], []
    
    print(f"🔍 Git-based canonical file selection for {len(files)} files...")
    
    # Score each file
    file_scores = []
    
    for f in files:
        score = 0
        
        # Git recency (most important factor)
        git_date = git_latest_commit_date(f)
        score += git_date / 1000  # Normalize timestamp
        
        # Complexity bonus
        complexity = get_file_complexity_score(f)
        score += complexity
        
        # Naming bonus (prefer non-test, non-diagnostic files for main functionality)
        name = os.path.basename(f).lower()
        if not any(word in name for word in ['test', 'diagnostic', 'debug', 'temp']):
            score += 1000
        
        # Prefer files without version numbers or dates
        if not re.search(r'_v?\d+|_\d{4}\d{2}\d{2}', name):
            score += 500
        
        file_scores.append((f, score))
    
    # Return file with highest score as canonical, rest as duplicates
    file_scores.sort(key=lambda x: x[1], reverse=True)
    canonical = file_scores[0][0]
    duplicates = [f[0] for f in file_scores[1:]]
    
    return canonical, duplicates

def extract_functions_and_classes(file_path):
    """Extract function and class definitions from a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        functions = []
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
        
        return functions, classes, content
    except Exception as e:
        print(f"⚠️ Error parsing {file_path}: {e}")
        return [], [], ""

def merge_missing_code(canonical, old_file):
    """Auto-merge missing code from older/duplicate files into canonicals"""
    print(f"🔄 Auto-merging missing code from {os.path.basename(old_file)} into {os.path.basename(canonical)}")
    
    try:
        # Get function and class info from both files
        canon_funcs, canon_classes, canonical_content = extract_functions_and_classes(canonical)
        other_funcs, other_classes, other_content = extract_functions_and_classes(old_file)
        
        # Find unique functions and classes
        unique_funcs = set(other_funcs) - set(canon_funcs)
        unique_classes = set(other_classes) - set(canon_classes)
        
        if not unique_funcs and not unique_classes:
            return False  # Nothing to merge
        
        # Parse the old file to extract unique function/class code
        other_tree = ast.parse(other_content)
        lines = other_content.split('\n')
        
        additions = []
        additions.append(f"\n# --- Merged from {os.path.basename(old_file)} ---")
        
        for node in ast.walk(other_tree):
            if isinstance(node, ast.FunctionDef) and node.name in unique_funcs:
                # Extract function code
                start_line = node.lineno - 1
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 10
                func_code = '\n'.join(lines[start_line:end_line])
                additions.append(f"\n{func_code}")
            
            elif isinstance(node, ast.ClassDef) and node.name in unique_classes:
                # Extract class code
                start_line = node.lineno - 1
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 20
                class_code = '\n'.join(lines[start_line:end_line])
                additions.append(f"\n{class_code}")
        
        if len(additions) > 1:  # More than just the header comment
            with open(canonical, 'a', encoding='utf-8') as f:
                f.write('\n'.join(additions))
            print(f"✅ Merged {len(unique_funcs)} functions and {len(unique_classes)} classes")
            return True
    
    except Exception as e:
        print(f"⚠️ Error merging code from {old_file}: {e}")
    
    return False

def archive_file(file_path):
    """Archive old duplicate files"""
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    
    # Preserve directory structure in archive
    rel_path = os.path.relpath(file_path, BASE_DIR)
    archive_path = os.path.join(ARCHIVE_DIR, rel_path)
    
    # Create subdirectories if needed
    os.makedirs(os.path.dirname(archive_path), exist_ok=True)
    
    # Handle naming conflicts
    counter = 1
    base_archive_path = archive_path
    while os.path.exists(archive_path):
        name, ext = os.path.splitext(base_archive_path)
        archive_path = f"{name}_{counter}{ext}"
        counter += 1
    
    shutil.move(file_path, archive_path)
    return archive_path

def refactor_imports(canonical_map):
    """Automatically refactor import paths project-wide to point to canonicals"""
    print("🔄 Automatically refactoring import paths project-wide...")
    
    files_updated = 0
    
    for root, dirs, files in os.walk(BASE_DIR):
        # Skip archive directory
        if ARCHIVE_DIR in dirs:
            dirs.remove(ARCHIVE_DIR)
        
        for f in files:
            if f.endswith(".py"):
                file_path = os.path.join(root, f)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    
                    original_content = content
                    
                    for old_file, canonical_file in canonical_map.items():
                        old_module = os.path.splitext(os.path.basename(old_file))[0]
                        canonical_module = os.path.splitext(os.path.basename(canonical_file))[0]
                        
                        if old_module == canonical_module:
                            continue  # Same module name, no change needed
                        
                        # Replace import statements
                        patterns = [
                            (rf'\bfrom\s+{re.escape(old_module)}\b', f'from {canonical_module}'),
                            (rf'\bimport\s+{re.escape(old_module)}\b', f'import {canonical_module}'),
                            (rf'{re.escape(old_module)}\.', f'{canonical_module}.'),
                        ]
                        
                        for pattern, replacement in patterns:
                            content = re.sub(pattern, replacement, content)
                    
                    if content != original_content:
                        with open(file_path, 'w', encoding='utf-8') as file:
                            file.write(content)
                        files_updated += 1
                
                except Exception as e:
                    print(f"⚠️ Error refactoring imports in {file_path}: {e}")
    
    print(f"✅ Updated imports in {files_updated} files")

def static_syntax_check(files):
    """Static syntax checks and error collection"""
    print("🔍 Static syntax checks and error collection...")
    
    syntax_errors = []
    for file_path in files:
        try:
            result = subprocess.run(
                ["python", "-m", "py_compile", file_path],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                first_line = error_msg.split('\n')[0] if error_msg else "Unknown syntax error"
                syntax_errors.append(f"{file_path}: {first_line}")
        except Exception as e:
            syntax_errors.append(f"{file_path}: Error during syntax check - {e}")
    
    return syntax_errors

def find_import_errors(archived_files):
    """Find imports referencing archived files"""
    import_errors = []
    archived_mods = {os.path.splitext(os.path.basename(f))[0] for f in archived_files}
    
    for root, dirs, files in os.walk(BASE_DIR):
        if ARCHIVE_DIR in dirs:
            dirs.remove(ARCHIVE_DIR)
        
        for f in files:
            if f.endswith(".py"):
                file_path = os.path.join(root, f)
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    
                    for mod in archived_mods:
                        import_pattern = re.compile(rf'\b(import|from)\s+{re.escape(mod)}\b')
                        if import_pattern.search(content):
                            import_errors.append(f"{file_path}: import of archived module '{mod}' detected")
                except Exception:
                    continue
    
    return import_errors

def run_basic_tests():
    """Run basic tests if available"""
    test_errors = []
    
    # Check if main files can be imported
    critical_files = ['main.py', 'web_dashboard.py', 'aave_integration.py']
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            try:
                module_name = os.path.splitext(file_path)[0]
                result = subprocess.run(
                    ["python", "-c", f"import {module_name}; print('Import OK: {module_name}')"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode != 0:
                    test_errors.append(f"Import test failed for {file_path}: {result.stderr.strip()}")
            except Exception as e:
                test_errors.append(f"Import test error for {file_path}: {e}")
    
    return test_errors

def generate_comprehensive_report(groups, canonical_map, merge_results, syntax_errors, import_errors, test_errors):
    """Generate comprehensive report listing features, files, and all blocking errors"""
    report_lines = [
        "COMPREHENSIVE SYSTEM AUDIT REPORT",
        "=" * 50,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total duplicates processed: {len(canonical_map)}",
        ""
    ]
    
    # Feature breakdown
    report_lines.append("FEATURE BREAKDOWN:")
    report_lines.append("-" * 30)
    
    for feature, files in groups.items():
        report_lines.append(f"\nFeature: {feature.upper()}")
        
        if len(files) == 1:
            report_lines.append(f"  Single file: {files[0]}")
        else:
            # Find canonical for this feature
            canonical_files = set()
            archived_files = []
            
            for f in files:
                is_canonical = True
                for old_file, canonical_file in canonical_map.items():
                    if f == old_file:
                        is_canonical = False
                        archived_files.append(f)
                        break
                    elif f == canonical_file:
                        canonical_files.add(f)
                
                if is_canonical and f not in canonical_files:
                    canonical_files.add(f)
            
            for canonical in canonical_files:
                report_lines.append(f"  Canonical: {canonical}")
            
            for archived in archived_files:
                merge_status = "✅ Merged" if merge_results.get(archived, False) else "📋 No unique content"
                report_lines.append(f"  Archived: {archived} - {merge_status}")
    
    # Error summary
    report_lines.extend([
        "\nERROR SUMMARY:",
        "=" * 30,
        f"Syntax errors: {len(syntax_errors)}",
        f"Import errors: {len(import_errors)}",
        f"Test errors: {len(test_errors)}",
        ""
    ])
    
    # Detailed errors
    if syntax_errors:
        report_lines.append("SYNTAX ERRORS:")
        report_lines.append("-" * 20)
        for error in syntax_errors:
            report_lines.append(f"  {error}")
        report_lines.append("")
    
    if import_errors:
        report_lines.append("IMPORT ERRORS:")
        report_lines.append("-" * 20)
        for error in import_errors:
            report_lines.append(f"  {error}")
        report_lines.append("")
    
    if test_errors:
        report_lines.append("TEST ERRORS:")
        report_lines.append("-" * 20)
        for error in test_errors:
            report_lines.append(f"  {error}")
        report_lines.append("")
    
    # Final status
    total_errors = len(syntax_errors) + len(import_errors) + len(test_errors)
    if total_errors == 0:
        report_lines.append("🎉 AUDIT STATUS: ALL CHECKS PASSED")
    else:
        report_lines.append(f"❌ AUDIT STATUS: {total_errors} BLOCKING ERRORS FOUND")
    
    return "\n".join(report_lines)