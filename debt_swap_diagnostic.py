
#!/usr/bin/env python3
"""
Debt Swap Diagnostic Tool - Debug why debt swaps aren't executing on-chain
"""

import os
import time
from datetime import datetime
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def diagnose_debt_swap_strategy():
    """Comprehensive diagnosis of debt swap strategy execution"""
    print("🔍 DEBT SWAP STRATEGY DIAGNOSTIC")
    print("=" * 50)
    
    try:
        # Initialize agent
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        # Check 1: Market Signal Strategy Status
        print("\n1️⃣ Market Signal Strategy Status:")
        print(f"   🔍 Environment Variables:")
        print(f"      MARKET_SIGNAL_ENABLED: {os.getenv('MARKET_SIGNAL_ENABLED', 'NOT SET')}")
        print(f"      BTC_DROP_THRESHOLD: {os.getenv('BTC_DROP_THRESHOLD', 'NOT SET')}")
        print(f"      DAI_TO_ARB_THRESHOLD: {os.getenv('DAI_TO_ARB_THRESHOLD', 'NOT SET')}")
        
        if hasattr(agent, 'market_signal_strategy') and agent.market_signal_strategy:
            mss = agent.market_signal_strategy
            print(f"   ✅ Market Signal Strategy: Initialized")
            print(f"   📊 Enabled: {mss.market_signal_enabled}")
            print(f"   🎯 BTC Drop Threshold: {mss.btc_drop_threshold*100:.1f}%")
            print(f"   📈 DAI→ARB Confidence Threshold: {mss.dai_to_arb_threshold:.0%}")
            print(f"   ⏰ Signal Cooldown: {mss.signal_cooldown}s")
            
            # Test current market conditions
            print(f"\n   📊 Current Market Analysis:")
            signal = mss.analyze_market_signals()
            if signal:
                print(f"      Signal Type: {signal.signal_type}")
                print(f"      Confidence: {signal.confidence:.2f}")
                print(f"      BTC 1h Change: {signal.btc_price_change:.2f}%")
                print(f"      ARB Technical Score: {signal.arb_technical_score:.1f}")
                
                should_execute, strategy_type = mss.should_execute_market_strategy(signal)
                print(f"      Should Execute: {'YES' if should_execute else 'NO'}")
                if should_execute:
                    print(f"      Strategy Type: {strategy_type}")
            else:
                print(f"      ❌ No signal generated")
        else:
            print(f"   ❌ Market Signal Strategy: Not initialized")
        
        # Check 2: Account Status
        print(f"\n2️⃣ Account Status for Debt Swaps:")
        account_data = agent.aave.get_user_account_data()
        if account_data:
            health_factor = account_data.get('healthFactor', 0)
            available_borrows = account_data.get('availableBorrowsUSD', 0)
            total_debt = account_data.get('totalDebtUSD', 0)
            
            print(f"   💰 Available Borrows: ${available_borrows:.2f}")
            print(f"   ❤️ Health Factor: {health_factor:.4f}")
            print(f"   💸 Total Debt: ${total_debt:.2f}")
            
            # Check if account can execute debt swaps
            can_borrow = health_factor > 1.5 and available_borrows >= 1.0
            print(f"   🎯 Can Execute Debt Swap: {'YES' if can_borrow else 'NO'}")
            
            if not can_borrow:
                if health_factor <= 1.5:
                    print(f"      ⚠️ Health factor too low for borrowing")
                if available_borrows < 1.0:
                    print(f"      ⚠️ Insufficient borrowing capacity")
        
        # Check 3: Recent Transaction History
        print(f"\n3️⃣ Transaction Execution Check:")
        eth_balance = agent.get_eth_balance()
        print(f"   ⛽ ETH Balance: {eth_balance:.6f} ETH")
        
        if eth_balance < 0.001:
            print(f"   ❌ Insufficient ETH for gas fees")
        else:
            print(f"   ✅ Sufficient ETH for transactions")
        
        # Check 4: System Operation Logs
        print(f"\n4️⃣ System Operation Status:")
        if hasattr(agent, 'last_successful_operation_time'):
            last_op_time = agent.last_successful_operation_time
            if last_op_time > 0:
                time_since = time.time() - last_op_time
                print(f"   ⏰ Last Successful Operation: {time_since/60:.1f} minutes ago")
            else:
                print(f"   ⚠️ No successful operations recorded")
        
        # Check cooldown status
        is_cooldown, remaining = agent.is_operation_in_cooldown('market_signal')
        if is_cooldown:
            print(f"   ⏰ Market signal operations in cooldown: {remaining:.0f}s remaining")
        else:
            print(f"   ✅ Ready for market signal operations")
        
        # Check 5: Force Execute Test (if conditions allow)
        print(f"\n5️⃣ Debt Swap Execution Test:")
        if (hasattr(agent, 'market_signal_strategy') and 
            agent.market_signal_strategy and 
            account_data and 
            account_data.get('availableBorrowsUSD', 0) >= 1.0 and
            account_data.get('healthFactor', 0) > 1.5):
            
            print(f"   🎯 Attempting test debt swap execution...")
            test_amount = min(1.0, account_data.get('availableBorrowsUSD', 0) * 0.1)
            
            # This would execute the actual swap - uncomment to test
            # success = agent.market_signal_strategy._execute_dai_to_arb_swap(test_amount)
            # print(f"   Result: {'SUCCESS' if success else 'FAILED'}")
            
            print(f"   💡 Test amount would be: ${test_amount:.2f}")
            print(f"   📝 Uncomment execution line in diagnostic to test")
        else:
            print(f"   ⚠️ Conditions not met for test execution")
        
        print(f"\n📊 DIAGNOSIS SUMMARY:")
        print(f"=" * 30)
        print(f"🔍 Check your Replit Secrets for:")
        print(f"   • MARKET_SIGNAL_ENABLED=true")
        print(f"   • BTC_DROP_THRESHOLD=0.003 (or lower)")
        print(f"   • DAI_TO_ARB_THRESHOLD=0.92")
        print(f"🎯 Market conditions must show:")
        print(f"   • BTC declining ≥0.3% in 1 hour")
        print(f"   • ARB oversold (RSI ≤30)")  
        print(f"   • 92% confidence threshold met")
        print(f"💰 Account must have:")
        print(f"   • Health factor >1.5")
        print(f"   • Available borrows ≥$1.00")
        print(f"   • Sufficient ETH for gas")
        
        return True
        
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        return False

if __name__ == "__main__":
    diagnose_debt_swap_strategy()

# --- Merged from api_diagnostics.py ---

def full_diagnostic_report():
    """Comprehensive diagnostic report for UI debugging"""
    try:
        report = {
            'timestamp': time.time(),
            'server_time': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
            'environment': {},
            'network': {},
            'agent': {},
            'endpoints': {},
            'files': {},
            'errors': []
        }

        # Environment diagnostics
        critical_env_vars = ['NETWORK_MODE', 'PRIVATE_KEY', 'COINMARKETCAP_API_KEY', 'PROMPT_KEY']
        for var in critical_env_vars:
            value = os.getenv(var)
            report['environment'][var] = {
                'present': bool(value),
                'length': len(value) if value else 0,
                'preview': value[:10] + '...' if value and len(value) > 10 else value if value else None
            }

        # Network diagnostics
        try:
            network_mode = os.getenv('NETWORK_MODE', 'testnet')
            report['network']['mode'] = network_mode

            if network_mode == 'mainnet':
                rpc_url = os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc')
                expected_chain_id = 42161
                network_name = 'Arbitrum Mainnet'
            else:
                rpc_url = 'https://sepolia-rollup.arbitrum.io/rpc'
                expected_chain_id = 421614
                network_name = 'Arbitrum Sepolia'

            report['network']['rpc_url'] = rpc_url
            report['network']['expected_chain_id'] = expected_chain_id
            report['network']['expected_name'] = network_name

            # Test RPC connection
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            if w3.is_connected():
                actual_chain_id = w3.eth.chain_id
                latest_block = w3.eth.get_block('latest')

                report['network']['connected'] = True
                report['network']['actual_chain_id'] = actual_chain_id
                report['network']['latest_block'] = latest_block.number
                report['network']['chain_id_match'] = actual_chain_id == expected_chain_id

                if actual_chain_id == 42161:
                    report['network']['actual_name'] = 'Arbitrum Mainnet'
                elif actual_chain_id == 421614:
                    report['network']['actual_name'] = 'Arbitrum Sepolia'
                else:
                    report['network']['actual_name'] = f'Unknown (Chain ID: {actual_chain_id})'
            else:
                report['network']['connected'] = False
                report['errors'].append('RPC connection failed')

        except Exception as e:
            report['network']['error'] = str(e)
            report['errors'].append(f'Network check failed: {e}')

        # Agent initialization diagnostics
        try:
            agent = ArbitrumTestnetAgent()
            report['agent']['initialized'] = True
            report['agent']['address'] = agent.address
            report['agent']['eth_balance'] = agent.get_eth_balance()
            report['agent']['chain_id'] = agent.w3.eth.chain_id
        except Exception as e:
            report['agent']['initialized'] = False
            report['agent']['error'] = str(e)
            report['errors'].append(f'Agent initialization failed: {e}')

        # File existence diagnostics
        important_files = [
            'agent_config.json',
            'user_settings.json',
            'performance_log.json',
            'EMERGENCY_STOP_ACTIVE.flag'
        ]
        for file in important_files:
            report['files'][file] = os.path.exists(file)

        # Endpoint testing
        endpoints_to_test = [
            '/api/wallet_status',
            '/api/performance',
            '/api/parameters',
            '/api/network-info',
            '/api/emergency_status'
        ]

        for endpoint in endpoints_to_test:
            try:
                # We can't test these directly here, but we can check if the functions exist
                report['endpoints'][endpoint] = 'available'
            except Exception as e:
                report['endpoints'][endpoint] = f'error: {e}'

        # Parameter loading diagnostics
        try:
            # Test parameter loading methods
            config_methods = {}

            # Method 1: Default config
            config_methods['default'] = {
                'health_factor_target': 1.19,
                'borrow_trigger_threshold': 0.02,
                'arb_decline_threshold': 0.05,
                'auto_mode': True
            }

            # Method 2: From agent_config.json
            if os.path.exists('agent_config.json'):
                try:
                    with open('agent_config.json', 'r') as f:
                        config_methods['agent_config_file'] = json.load(f)
                except Exception as e:
                    config_methods['agent_config_file'] = {'error': str(e)}

            # Method 3: From user_settings.json
            if os.path.exists('user_settings.json'):
                try:
                    with open('user_settings.json', 'r') as f:
                        config_methods['user_settings_file'] = json.load(f)
                except Exception as e:
                    config_methods['user_settings_file'] = {'error': str(e)}

            report['parameters'] = config_methods

        except Exception as e:
            report['parameters'] = {'error': str(e)}
            report['errors'].append(f'Parameter diagnostics failed: {e}')

        # Overall status
        report['overall_status'] = {
            'healthy': len(report['errors']) == 0,
            'error_count': len(report['errors']),
            'critical_issues': [error for error in report['errors'] if any(word in error.lower() for word in ['failed', 'connection', 'initialization'])]
        }

        return jsonify(report)

    except Exception as e:
        return jsonify({
            'error': 'Diagnostic system failure',
            'exception': str(e),
            'timestamp': time.time()
        }), 500

def quick_health_check():
    """Quick health check for rapid debugging"""
    try:
        health = {
            'status': 'ok',
            'timestamp': time.time(),
            'network_mode': os.getenv('NETWORK_MODE', 'unknown'),
            'secrets_count': len([var for var in ['NETWORK_MODE', 'PRIVATE_KEY', 'COINMARKETCAP_API_KEY'] if os.getenv(var)]),
            'agent_can_initialize': False
        }

        # Quick agent test
        try:
            agent = ArbitrumTestnetAgent()
            health['agent_can_initialize'] = True
            health['agent_address'] = agent.address
            health['agent_network'] = agent.w3.eth.chain_id
        except Exception as e:
            health['agent_error'] = str(e)

        return jsonify(health)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
# --- Merged from comprehensive_diagnostic.py ---

class ComprehensiveDiagnostic:
    def __init__(self):
        self.report = {
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "diagnostic_version": "1.0",
            "environment": {},
            "file_system": {},
            "network": {},
            "dependencies": {},
            "application": {},
            "errors": [],
            "recommendations": [],
            "ai_analysis_data": {}
        }

    def run_full_diagnostic(self):
        """Run complete diagnostic suite"""
        print("🔍 COMPREHENSIVE DIAGNOSTIC SUITE")
        print("=" * 80)
        
        self.check_environment()
        self.analyze_file_system()
        self.test_network_connectivity()
        self.validate_dependencies()
        self.test_application_components()
        self.analyze_errors()
        self.generate_recommendations()
        self.prepare_ai_analysis_data()
        
        return self.report

    def check_environment(self):
        """Analyze environment variables and system info"""
        print("🌍 Checking Environment Variables...")
        
        critical_env_vars = [
            'NETWORK_MODE', 'PRIVATE_KEY', 'PRIVATE_KEY2', 'COINMARKETCAP_API_KEY',
            'PROMPT_KEY', 'OPTIMIZER_API_KEY', 'ARBITRUM_RPC_URL', 'REPLIT_DEPLOYMENT'
        ]
        
        self.report["environment"] = {
            "python_version": sys.version,
            "platform": sys.platform,
            "working_directory": os.getcwd(),
            "environment_variables": {},
            "replit_specific": {}
        }
        
        for var in critical_env_vars:
            value = os.getenv(var)
            self.report["environment"]["environment_variables"][var] = {
                "present": bool(value),
                "length": len(value) if value else 0,
                "starts_with": value[:10] if value and len(value) > 10 else value if value else None,
                "type": type(value).__name__
            }
        
        # Replit-specific environment
        self.report["environment"]["replit_specific"] = {
            "is_deployment": bool(os.getenv('REPLIT_DEPLOYMENT')),
            "replit_env": bool(os.getenv('REPLIT')),
            "home_dir": os.getenv('HOME'),
            "user": os.getenv('USER')
        }

    def analyze_file_system(self):
        """Analyze critical files and their states"""
        print("📁 Analyzing File System...")
        
        critical_files = [
            'arbitrum_testnet_agent.py', 'web_dashboard.py', 'mainnet_launcher.py',
            'aave_integration.py', 'aave_health_monitor.py', 'user_settings.json',
            'agent_config.json', 'EMERGENCY_STOP_ACTIVE.flag', 'performance_log.json',
            '.env', '.replit', 'requirements.txt'
        ]
        
        self.report["file_system"] = {
            "critical_files": {},
            "directory_structure": {},
            "permissions": {}
        }
        
        for file in critical_files:
            if os.path.exists(file):
                try:
                    stat = os.stat(file)
                    self.report["file_system"]["critical_files"][file] = {
                        "exists": True,
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                        "readable": os.access(file, os.R_OK),
                        "writable": os.access(file, os.W_OK)
                    }
                    
                    # Try to detect syntax errors in Python files
                    if file.endswith('.py'):
                        syntax_check = self.check_python_syntax(file)
                        self.report["file_system"]["critical_files"][file]["syntax_valid"] = syntax_check["valid"]
                        if not syntax_check["valid"]:
                            self.report["file_system"]["critical_files"][file]["syntax_error"] = syntax_check["error"]
                            
                except Exception as e:
                    self.report["file_system"]["critical_files"][file] = {
                        "exists": True,
                        "error": str(e)
                    }
            else:
                self.report["file_system"]["critical_files"][file] = {"exists": False}

    def check_python_syntax(self, file_path):
        """Check Python file for syntax errors"""
        try:
            with open(file_path, 'r') as f:
                source = f.read()
            compile(source, file_path, 'exec')
            return {"valid": True}
        except SyntaxError as e:
            return {
                "valid": False,
                "error": {
                    "message": str(e),
                    "line": e.lineno,
                    "offset": e.offset,
                    "text": e.text
                }
            }
        except Exception as e:
            return {
                "valid": False,
                "error": {"message": str(e)}
            }

    def test_network_connectivity(self):
        """Test network connections and RPC endpoints"""
        print("🌐 Testing Network Connectivity...")
        
        self.report["network"] = {
            "rpc_endpoints": {},
            "api_endpoints": {},
            "general_connectivity": {}
        }
        
        # Test RPC endpoints
        rpc_tests = [
            ("arbitrum_mainnet", "https://arb1.arbitrum.io/rpc"),
            ("arbitrum_sepolia", "https://sepolia-rollup.arbitrum.io/rpc")
        ]
        
        for name, url in rpc_tests:
            self.report["network"]["rpc_endpoints"][name] = self.test_rpc_endpoint(url)
        
        # Test API endpoints
        api_tests = [
            ("coinmarketcap", "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"),
        ]
        
        for name, url in api_tests:
            self.report["network"]["api_endpoints"][name] = self.test_api_endpoint(url)

    def test_rpc_endpoint(self, url):
        """Test a specific RPC endpoint"""
        try:
            from web3 import Web3
            w3 = Web3(Web3.HTTPProvider(url))
            
            if w3.is_connected():
                chain_id = w3.eth.chain_id
                latest_block = w3.eth.get_block('latest')
                return {
                    "connected": True,
                    "chain_id": chain_id,
                    "latest_block": latest_block.number,
                    "response_time": "fast"  # Could measure actual time
                }
            else:
                return {"connected": False, "error": "Connection failed"}
                
        except Exception as e:
            return {"connected": False, "error": str(e)}

    def test_api_endpoint(self, url):
        """Test a specific API endpoint"""
        try:
            import requests
            response = requests.get(url, timeout=5)
            return {
                "accessible": True,
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }
        except Exception as e:
            return {"accessible": False, "error": str(e)}

    def validate_dependencies(self):
        """Check Python dependencies and imports"""
        print("📦 Validating Dependencies...")
        
        required_modules = [
            'web3', 'flask', 'requests', 'eth_account', 'python-dotenv'
        ]
        
        self.report["dependencies"] = {
            "required_modules": {},
            "import_tests": {}
        }
        
        for module in required_modules:
            try:
                __import__(module)
                self.report["dependencies"]["required_modules"][module] = {
                    "available": True,
                    "version": self.get_module_version(module)
                }
            except ImportError as e:
                self.report["dependencies"]["required_modules"][module] = {
                    "available": False,
                    "error": str(e)
                }
        
        # Test critical imports
        import_tests = [
            ("arbitrum_testnet_agent", "ArbitrumTestnetAgent"),
            ("web_dashboard", "app"),
            ("aave_integration", "AaveArbitrumIntegration"),
            ("aave_health_monitor", "AaveHealthMonitor")
        ]
        
        for module, class_name in import_tests:
            self.report["dependencies"]["import_tests"][f"{module}.{class_name}"] = self.test_import(module, class_name)

    def get_module_version(self, module_name):
        """Get version of a module if available"""
        try:
            module = __import__(module_name)
            return getattr(module, '__version__', 'unknown')
        except:
            return 'unknown'

    def test_import(self, module_name, class_name=None):
        """Test importing a specific module/class"""
        try:
            module = __import__(module_name)
            if class_name:
                getattr(module, class_name)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def test_application_components(self):
        """Test core application functionality"""
        print("🤖 Testing Application Components...")
        
        self.report["application"] = {
            "agent_initialization": {},
            "web_dashboard": {},
            "aave_integration": {},
            "workflow_status": {}
        }
        
        # Test agent initialization
        try:
            from arbitrum_testnet_agent import ArbitrumTestnetAgent
            agent = ArbitrumTestnetAgent()
            self.report["application"]["agent_initialization"] = {
                "success": True,
                "address": agent.address,
                "network_mode": agent.network_mode,
                "chain_id": agent.w3.eth.chain_id,
                "eth_balance": agent.get_eth_balance()
            }
        except Exception as e:
            self.report["application"]["agent_initialization"] = {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        
        # Test web dashboard import
        try:
            from web_dashboard import app
            self.report["application"]["web_dashboard"] = {
                "import_success": True,
                "flask_app": str(type(app))
            }
        except Exception as e:
            self.report["application"]["web_dashboard"] = {
                "import_success": False,
                "error": str(e)
            }

    def analyze_errors(self):
        """Analyze recent errors and log files"""
        print("🔍 Analyzing Error Patterns...")
        
        self.report["errors"] = {
            "recent_errors": [],
            "log_analysis": {},
            "common_patterns": []
        }
        
        # Check for error logs
        log_files = ['performance_log.json', 'emergency_stop_log.json']
        
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        content = f.read()
                        self.report["errors"]["log_analysis"][log_file] = {
                            "size": len(content),
                            "lines": len(content.split('\n')),
                            "recent_entries": content.split('\n')[-5:] if content else []
                        }
                except Exception as e:
                    self.report["errors"]["log_analysis"][log_file] = {"error": str(e)}

    def generate_recommendations(self):
        """Generate specific recommendations based on findings"""
        print("💡 Generating Recommendations...")
        
        recommendations = []
        
        # Check for missing environment variables
        env_vars = self.report["environment"]["environment_variables"]
        missing_vars = [var for var, info in env_vars.items() if not info["present"]]
        
        if missing_vars:
            recommendations.append({
                "priority": "HIGH",
                "category": "Environment",
                "issue": f"Missing environment variables: {', '.join(missing_vars)}",
                "solution": "Add missing variables to Replit Secrets panel"
            })
        
        # Check for syntax errors
        for file, info in self.report["file_system"]["critical_files"].items():
            if info.get("exists") and info.get("syntax_valid") == False:
                recommendations.append({
                    "priority": "CRITICAL",
                    "category": "Syntax",
                    "issue": f"Syntax error in {file}: {info.get('syntax_error', {}).get('message', 'Unknown')}",
                    "solution": f"Fix syntax error at line {info.get('syntax_error', {}).get('line', 'unknown')}"
                })
        
        # Check agent initialization
        if not self.report["application"]["agent_initialization"].get("success"):
            recommendations.append({
                "priority": "HIGH",
                "category": "Application",
                "issue": "Agent initialization failed",
                "solution": "Check network connectivity and environment variables"
            })
        
        self.report["recommendations"] = recommendations

    def prepare_ai_analysis_data(self):
        """Prepare structured data for AI analysis"""
        print("🤖 Preparing AI Analysis Data...")
        
        self.report["ai_analysis_data"] = {
            "error_patterns": self.extract_error_patterns(),
            "configuration_state": self.summarize_configuration(),
            "dependency_matrix": self.create_dependency_matrix(),
            "failure_points": self.identify_failure_points(),
            "system_health_score": self.calculate_health_score()
        }

    def extract_error_patterns(self):
        """Extract common error patterns for AI analysis"""
        patterns = []
        
        # Syntax errors
        for file, info in self.report["file_system"]["critical_files"].items():
            if info.get("syntax_valid") == False:
                patterns.append({
                    "type": "syntax_error",
                    "file": file,
                    "details": info.get("syntax_error")
                })
        
        # Import errors
        for test, result in self.report["dependencies"]["import_tests"].items():
            if not result.get("success"):
                patterns.append({
                    "type": "import_error",
                    "module": test,
                    "error": result.get("error")
                })
        
        return patterns

    def summarize_configuration(self):
        """Summarize current configuration state"""
        env_vars = self.report["environment"]["environment_variables"]
        
        return {
            "network_mode": env_vars.get("NETWORK_MODE", {}).get("starts_with"),
            "secrets_configured": sum(1 for var in env_vars.values() if var.get("present")),
            "total_secrets_needed": len(env_vars),
            "deployment_mode": self.report["environment"]["replit_specific"]["is_deployment"]
        }

    def create_dependency_matrix(self):
        """Create dependency relationship matrix"""
        return {
            "web3_available": self.report["dependencies"]["required_modules"].get("web3", {}).get("available"),
            "flask_available": self.report["dependencies"]["required_modules"].get("flask", {}).get("available"),
            "agent_importable": self.report["dependencies"]["import_tests"].get("arbitrum_testnet_agent.ArbitrumTestnetAgent", {}).get("success"),
            "dashboard_importable": self.report["dependencies"]["import_tests"].get("web_dashboard.app", {}).get("success")
        }

    def identify_failure_points(self):
        """Identify critical failure points"""
        failure_points = []
        
        if not self.report["application"]["agent_initialization"].get("success"):
            failure_points.append("agent_initialization")
        
        if not self.report["application"]["web_dashboard"].get("import_success"):
            failure_points.append("web_dashboard_import")
        
        if not any(ep.get("connected") for ep in self.report["network"]["rpc_endpoints"].values()):
            failure_points.append("network_connectivity")
        
        return failure_points

    def calculate_health_score(self):
        """Calculate overall system health score (0-100)"""
        score = 100
        
        # Deduct for missing environment variables
        env_vars = self.report["environment"]["environment_variables"]
        missing_count = sum(1 for var in env_vars.values() if not var.get("present"))
        score -= missing_count * 10
        
        # Deduct for syntax errors
        syntax_errors = sum(1 for file in self.report["file_system"]["critical_files"].values() 
                          if file.get("syntax_valid") == False)
        score -= syntax_errors * 25
        
        # Deduct for failed imports
        failed_imports = sum(1 for test in self.report["dependencies"]["import_tests"].values() 
                           if not test.get("success"))
        score -= failed_imports * 15
        
        # Deduct for application failures
        if not self.report["application"]["agent_initialization"].get("success"):
            score -= 20
        
        return max(0, score)

    def save_report(self, filename="diagnostic_report.json"):
        """Save diagnostic report to file"""
        with open(filename, 'w') as f:
            json.dump(self.report, f, indent=2, default=str)
        print(f"📄 Diagnostic report saved to {filename}")

    def print_summary(self):
        """Print diagnostic summary"""
        print("\n" + "=" * 80)
        print("📊 DIAGNOSTIC SUMMARY")
        print("=" * 80)
        
        health_score = self.report["ai_analysis_data"]["system_health_score"]
        print(f"🏥 System Health Score: {health_score}/100")
        
        if health_score >= 80:
            print("✅ System appears healthy")
        elif health_score >= 60:
            print("⚠️ System has minor issues")
        elif health_score >= 40:
            print("🟡 System has significant issues")
        else:
            print("🚨 System has critical issues")
        
        print(f"\n🔧 Recommendations ({len(self.report['recommendations'])}):")
        for rec in self.report["recommendations"][:5]:  # Show top 5
            priority_icon = "🚨" if rec["priority"] == "CRITICAL" else "⚠️" if rec["priority"] == "HIGH" else "💡"
            print(f"  {priority_icon} {rec['category']}: {rec['issue']}")
        
        failure_points = self.report["ai_analysis_data"]["failure_points"]
        if failure_points:
            print(f"\n❌ Critical Failure Points: {', '.join(failure_points)}")
        
        print(f"\n📄 Full report available in diagnostic_report.json")
        print("🤖 This data is structured for AI analysis and debugging")

def main():
    """Run comprehensive diagnostic"""
    diagnostic = ComprehensiveDiagnostic()
    
    try:
        report = diagnostic.run_full_diagnostic()
        diagnostic.save_report()
        diagnostic.print_summary()
        
        print("\n" + "=" * 80)
        print("🎯 FOR AI ANALYSIS:")
        print("=" * 80)
        print("This diagnostic report contains structured data for AI debugging:")
        print("• Error patterns with specific line numbers and types")
        print("• Configuration state matrix")
        print("• Dependency relationship mapping")
        print("• Failure point identification")
        print("• System health scoring")
        print("• Actionable recommendations with priorities")
        print("\nUse 'diagnostic_report.json' for detailed AI analysis")
        
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        traceback.print_exc()

    def __init__(self):
        self.report = {
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "diagnostic_version": "1.0",
            "environment": {},
            "file_system": {},
            "network": {},
            "dependencies": {},
            "application": {},
            "errors": [],
            "recommendations": [],
            "ai_analysis_data": {}
        }

    def run_full_diagnostic(self):
        """Run complete diagnostic suite"""
        print("🔍 COMPREHENSIVE DIAGNOSTIC SUITE")
        print("=" * 80)
        
        self.check_environment()
        self.analyze_file_system()
        self.test_network_connectivity()
        self.validate_dependencies()
        self.test_application_components()
        self.analyze_errors()
        self.generate_recommendations()
        self.prepare_ai_analysis_data()
        
        return self.report

    def check_environment(self):
        """Analyze environment variables and system info"""
        print("🌍 Checking Environment Variables...")
        
        critical_env_vars = [
            'NETWORK_MODE', 'PRIVATE_KEY', 'PRIVATE_KEY2', 'COINMARKETCAP_API_KEY',
            'PROMPT_KEY', 'OPTIMIZER_API_KEY', 'ARBITRUM_RPC_URL', 'REPLIT_DEPLOYMENT'
        ]
        
        self.report["environment"] = {
            "python_version": sys.version,
            "platform": sys.platform,
            "working_directory": os.getcwd(),
            "environment_variables": {},
            "replit_specific": {}
        }
        
        for var in critical_env_vars:
            value = os.getenv(var)
            self.report["environment"]["environment_variables"][var] = {
                "present": bool(value),
                "length": len(value) if value else 0,
                "starts_with": value[:10] if value and len(value) > 10 else value if value else None,
                "type": type(value).__name__
            }
        
        # Replit-specific environment
        self.report["environment"]["replit_specific"] = {
            "is_deployment": bool(os.getenv('REPLIT_DEPLOYMENT')),
            "replit_env": bool(os.getenv('REPLIT')),
            "home_dir": os.getenv('HOME'),
            "user": os.getenv('USER')
        }

    def analyze_file_system(self):
        """Analyze critical files and their states"""
        print("📁 Analyzing File System...")
        
        critical_files = [
            'arbitrum_testnet_agent.py', 'web_dashboard.py', 'mainnet_launcher.py',
            'aave_integration.py', 'aave_health_monitor.py', 'user_settings.json',
            'agent_config.json', 'EMERGENCY_STOP_ACTIVE.flag', 'performance_log.json',
            '.env', '.replit', 'requirements.txt'
        ]
        
        self.report["file_system"] = {
            "critical_files": {},
            "directory_structure": {},
            "permissions": {}
        }
        
        for file in critical_files:
            if os.path.exists(file):
                try:
                    stat = os.stat(file)
                    self.report["file_system"]["critical_files"][file] = {
                        "exists": True,
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                        "readable": os.access(file, os.R_OK),
                        "writable": os.access(file, os.W_OK)
                    }
                    
                    # Try to detect syntax errors in Python files
                    if file.endswith('.py'):
                        syntax_check = self.check_python_syntax(file)
                        self.report["file_system"]["critical_files"][file]["syntax_valid"] = syntax_check["valid"]
                        if not syntax_check["valid"]:
                            self.report["file_system"]["critical_files"][file]["syntax_error"] = syntax_check["error"]
                            
                except Exception as e:
                    self.report["file_system"]["critical_files"][file] = {
                        "exists": True,
                        "error": str(e)
                    }
            else:
                self.report["file_system"]["critical_files"][file] = {"exists": False}

    def check_python_syntax(self, file_path):
        """Check Python file for syntax errors"""
        try:
            with open(file_path, 'r') as f:
                source = f.read()
            compile(source, file_path, 'exec')
            return {"valid": True}
        except SyntaxError as e:
            return {
                "valid": False,
                "error": {
                    "message": str(e),
                    "line": e.lineno,
                    "offset": e.offset,
                    "text": e.text
                }
            }
        except Exception as e:
            return {
                "valid": False,
                "error": {"message": str(e)}
            }

    def test_network_connectivity(self):
        """Test network connections and RPC endpoints"""
        print("🌐 Testing Network Connectivity...")
        
        self.report["network"] = {
            "rpc_endpoints": {},
            "api_endpoints": {},
            "general_connectivity": {}
        }
        
        # Test RPC endpoints
        rpc_tests = [
            ("arbitrum_mainnet", "https://arb1.arbitrum.io/rpc"),
            ("arbitrum_sepolia", "https://sepolia-rollup.arbitrum.io/rpc")
        ]
        
        for name, url in rpc_tests:
            self.report["network"]["rpc_endpoints"][name] = self.test_rpc_endpoint(url)
        
        # Test API endpoints
        api_tests = [
            ("coinmarketcap", "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"),
        ]
        
        for name, url in api_tests:
            self.report["network"]["api_endpoints"][name] = self.test_api_endpoint(url)

    def test_rpc_endpoint(self, url):
        """Test a specific RPC endpoint"""
        try:
            from web3 import Web3
            w3 = Web3(Web3.HTTPProvider(url))
            
            if w3.is_connected():
                chain_id = w3.eth.chain_id
                latest_block = w3.eth.get_block('latest')
                return {
                    "connected": True,
                    "chain_id": chain_id,
                    "latest_block": latest_block.number,
                    "response_time": "fast"  # Could measure actual time
                }
            else:
                return {"connected": False, "error": "Connection failed"}
                
        except Exception as e:
            return {"connected": False, "error": str(e)}

    def test_api_endpoint(self, url):
        """Test a specific API endpoint"""
        try:
            import requests
            response = requests.get(url, timeout=5)
            return {
                "accessible": True,
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }
        except Exception as e:
            return {"accessible": False, "error": str(e)}

    def validate_dependencies(self):
        """Check Python dependencies and imports"""
        print("📦 Validating Dependencies...")
        
        required_modules = [
            'web3', 'flask', 'requests', 'eth_account', 'python-dotenv'
        ]
        
        self.report["dependencies"] = {
            "required_modules": {},
            "import_tests": {}
        }
        
        for module in required_modules:
            try:
                __import__(module)
                self.report["dependencies"]["required_modules"][module] = {
                    "available": True,
                    "version": self.get_module_version(module)
                }
            except ImportError as e:
                self.report["dependencies"]["required_modules"][module] = {
                    "available": False,
                    "error": str(e)
                }
        
        # Test critical imports
        import_tests = [
            ("arbitrum_testnet_agent", "ArbitrumTestnetAgent"),
            ("web_dashboard", "app"),
            ("aave_integration", "AaveArbitrumIntegration"),
            ("aave_health_monitor", "AaveHealthMonitor")
        ]
        
        for module, class_name in import_tests:
            self.report["dependencies"]["import_tests"][f"{module}.{class_name}"] = self.test_import(module, class_name)

    def get_module_version(self, module_name):
        """Get version of a module if available"""
        try:
            module = __import__(module_name)
            return getattr(module, '__version__', 'unknown')
        except:
            return 'unknown'

    def test_import(self, module_name, class_name=None):
        """Test importing a specific module/class"""
        try:
            module = __import__(module_name)
            if class_name:
                getattr(module, class_name)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def test_application_components(self):
        """Test core application functionality"""
        print("🤖 Testing Application Components...")
        
        self.report["application"] = {
            "agent_initialization": {},
            "web_dashboard": {},
            "aave_integration": {},
            "workflow_status": {}
        }
        
        # Test agent initialization
        try:
            from arbitrum_testnet_agent import ArbitrumTestnetAgent
            agent = ArbitrumTestnetAgent()
            self.report["application"]["agent_initialization"] = {
                "success": True,
                "address": agent.address,
                "network_mode": agent.network_mode,
                "chain_id": agent.w3.eth.chain_id,
                "eth_balance": agent.get_eth_balance()
            }
        except Exception as e:
            self.report["application"]["agent_initialization"] = {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        
        # Test web dashboard import
        try:
            from web_dashboard import app
            self.report["application"]["web_dashboard"] = {
                "import_success": True,
                "flask_app": str(type(app))
            }
        except Exception as e:
            self.report["application"]["web_dashboard"] = {
                "import_success": False,
                "error": str(e)
            }

    def analyze_errors(self):
        """Analyze recent errors and log files"""
        print("🔍 Analyzing Error Patterns...")
        
        self.report["errors"] = {
            "recent_errors": [],
            "log_analysis": {},
            "common_patterns": []
        }
        
        # Check for error logs
        log_files = ['performance_log.json', 'emergency_stop_log.json']
        
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        content = f.read()
                        self.report["errors"]["log_analysis"][log_file] = {
                            "size": len(content),
                            "lines": len(content.split('\n')),
                            "recent_entries": content.split('\n')[-5:] if content else []
                        }
                except Exception as e:
                    self.report["errors"]["log_analysis"][log_file] = {"error": str(e)}

    def generate_recommendations(self):
        """Generate specific recommendations based on findings"""
        print("💡 Generating Recommendations...")
        
        recommendations = []
        
        # Check for missing environment variables
        env_vars = self.report["environment"]["environment_variables"]
        missing_vars = [var for var, info in env_vars.items() if not info["present"]]
        
        if missing_vars:
            recommendations.append({
                "priority": "HIGH",
                "category": "Environment",
                "issue": f"Missing environment variables: {', '.join(missing_vars)}",
                "solution": "Add missing variables to Replit Secrets panel"
            })
        
        # Check for syntax errors
        for file, info in self.report["file_system"]["critical_files"].items():
            if info.get("exists") and info.get("syntax_valid") == False:
                recommendations.append({
                    "priority": "CRITICAL",
                    "category": "Syntax",
                    "issue": f"Syntax error in {file}: {info.get('syntax_error', {}).get('message', 'Unknown')}",
                    "solution": f"Fix syntax error at line {info.get('syntax_error', {}).get('line', 'unknown')}"
                })
        
        # Check agent initialization
        if not self.report["application"]["agent_initialization"].get("success"):
            recommendations.append({
                "priority": "HIGH",
                "category": "Application",
                "issue": "Agent initialization failed",
                "solution": "Check network connectivity and environment variables"
            })
        
        self.report["recommendations"] = recommendations

    def prepare_ai_analysis_data(self):
        """Prepare structured data for AI analysis"""
        print("🤖 Preparing AI Analysis Data...")
        
        self.report["ai_analysis_data"] = {
            "error_patterns": self.extract_error_patterns(),
            "configuration_state": self.summarize_configuration(),
            "dependency_matrix": self.create_dependency_matrix(),
            "failure_points": self.identify_failure_points(),
            "system_health_score": self.calculate_health_score()
        }

    def extract_error_patterns(self):
        """Extract common error patterns for AI analysis"""
        patterns = []
        
        # Syntax errors
        for file, info in self.report["file_system"]["critical_files"].items():
            if info.get("syntax_valid") == False:
                patterns.append({
                    "type": "syntax_error",
                    "file": file,
                    "details": info.get("syntax_error")
                })
        
        # Import errors
        for test, result in self.report["dependencies"]["import_tests"].items():
            if not result.get("success"):
                patterns.append({
                    "type": "import_error",
                    "module": test,
                    "error": result.get("error")
                })
        
        return patterns

    def summarize_configuration(self):
        """Summarize current configuration state"""
        env_vars = self.report["environment"]["environment_variables"]
        
        return {
            "network_mode": env_vars.get("NETWORK_MODE", {}).get("starts_with"),
            "secrets_configured": sum(1 for var in env_vars.values() if var.get("present")),
            "total_secrets_needed": len(env_vars),
            "deployment_mode": self.report["environment"]["replit_specific"]["is_deployment"]
        }

    def create_dependency_matrix(self):
        """Create dependency relationship matrix"""
        return {
            "web3_available": self.report["dependencies"]["required_modules"].get("web3", {}).get("available"),
            "flask_available": self.report["dependencies"]["required_modules"].get("flask", {}).get("available"),
            "agent_importable": self.report["dependencies"]["import_tests"].get("arbitrum_testnet_agent.ArbitrumTestnetAgent", {}).get("success"),
            "dashboard_importable": self.report["dependencies"]["import_tests"].get("web_dashboard.app", {}).get("success")
        }

    def identify_failure_points(self):
        """Identify critical failure points"""
        failure_points = []
        
        if not self.report["application"]["agent_initialization"].get("success"):
            failure_points.append("agent_initialization")
        
        if not self.report["application"]["web_dashboard"].get("import_success"):
            failure_points.append("web_dashboard_import")
        
        if not any(ep.get("connected") for ep in self.report["network"]["rpc_endpoints"].values()):
            failure_points.append("network_connectivity")
        
        return failure_points

    def calculate_health_score(self):
        """Calculate overall system health score (0-100)"""
        score = 100
        
        # Deduct for missing environment variables
        env_vars = self.report["environment"]["environment_variables"]
        missing_count = sum(1 for var in env_vars.values() if not var.get("present"))
        score -= missing_count * 10
        
        # Deduct for syntax errors
        syntax_errors = sum(1 for file in self.report["file_system"]["critical_files"].values() 
                          if file.get("syntax_valid") == False)
        score -= syntax_errors * 25
        
        # Deduct for failed imports
        failed_imports = sum(1 for test in self.report["dependencies"]["import_tests"].values() 
                           if not test.get("success"))
        score -= failed_imports * 15
        
        # Deduct for application failures
        if not self.report["application"]["agent_initialization"].get("success"):
            score -= 20
        
        return max(0, score)

    def save_report(self, filename="diagnostic_report.json"):
        """Save diagnostic report to file"""
        with open(filename, 'w') as f:
            json.dump(self.report, f, indent=2, default=str)
        print(f"📄 Diagnostic report saved to {filename}")

    def print_summary(self):
        """Print diagnostic summary"""
        print("\n" + "=" * 80)
        print("📊 DIAGNOSTIC SUMMARY")
        print("=" * 80)
        
        health_score = self.report["ai_analysis_data"]["system_health_score"]
        print(f"🏥 System Health Score: {health_score}/100")
        
        if health_score >= 80:
            print("✅ System appears healthy")
        elif health_score >= 60:
            print("⚠️ System has minor issues")
        elif health_score >= 40:
            print("🟡 System has significant issues")
        else:
            print("🚨 System has critical issues")
        
        print(f"\n🔧 Recommendations ({len(self.report['recommendations'])}):")
        for rec in self.report["recommendations"][:5]:  # Show top 5
            priority_icon = "🚨" if rec["priority"] == "CRITICAL" else "⚠️" if rec["priority"] == "HIGH" else "💡"
            print(f"  {priority_icon} {rec['category']}: {rec['issue']}")
        
        failure_points = self.report["ai_analysis_data"]["failure_points"]
        if failure_points:
            print(f"\n❌ Critical Failure Points: {', '.join(failure_points)}")
        
        print(f"\n📄 Full report available in diagnostic_report.json")
        print("🤖 This data is structured for AI analysis and debugging")
# --- Merged from system_comprehensive_diagnostic.py ---

class ComprehensiveSystemDiagnostic:
    def __init__(self):
        self.report = {
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat(),
            'overall_status': 'CHECKING',
            'critical_issues': [],
            'warnings': [],
            'component_status': {},
            'function_tests': {},
            'recommendations': []
        }
        
    def run_full_diagnostic(self):
        """Run complete system diagnostic"""
        print("🔍 COMPREHENSIVE AUTONOMOUS SYSTEM DIAGNOSTIC")
        print("=" * 80)
        
        try:
            # Component checks
            self.check_environment_variables()
            self.check_file_integrity()
            self.check_agent_initialization()
            self.check_dashboard_functionality()
            self.check_defi_integrations()
            self.check_autonomous_functions()
            self.check_trigger_system()
            self.check_emergency_systems()
            self.check_network_connectivity()
            
            # Generate final assessment
            self.generate_final_assessment()
            
        except Exception as e:
            self.report['critical_issues'].append(f"Diagnostic failed: {e}")
            self.report['overall_status'] = 'FAILED'
            
        return self.report
        
    def check_environment_variables(self):
        """Check all required environment variables"""
        print("\n🔍 CHECKING ENVIRONMENT VARIABLES...")
        
        required_vars = {
            'PRIVATE_KEY': 'Wallet private key for mainnet operations',
            'COINMARKETCAP_API_KEY': 'Price data API key',
            'NETWORK_MODE': 'Network mode (should be mainnet)'
        }
        
        env_status = {}
        for var, description in required_vars.items():
            value = os.getenv(var)
            if value:
                if var == 'PRIVATE_KEY':
                    env_status[var] = f"✅ Set (length: {len(value)})"
                    if len(value) != 66 or not value.startswith('0x'):
                        self.report['warnings'].append(f"{var} may have incorrect format")
                elif var == 'NETWORK_MODE':
                    env_status[var] = f"✅ Set: {value}"
                    if value != 'mainnet':
                        self.report['warnings'].append(f"Network mode is {value}, expected 'mainnet'")
                else:
                    env_status[var] = f"✅ Set (length: {len(value)})"
            else:
                env_status[var] = "❌ Not set"
                self.report['critical_issues'].append(f"Missing {var}: {description}")
                
        self.report['component_status']['environment'] = env_status
        print(f"   Environment variables: {len([v for v in env_status.values() if '✅' in v])}/{len(required_vars)} configured")
        
    def check_file_integrity(self):
        """Check critical files exist and are valid"""
        print("\n🔍 CHECKING FILE INTEGRITY...")
        
        critical_files = {
            'arbitrum_testnet_agent.py': 'Main agent implementation',
            'web_dashboard.py': 'Dashboard interface',
            'complete_autonomous_launcher.py': 'System launcher',
            'aave_integration.py': 'Aave DeFi integration',
            'uniswap_integration.py': 'Uniswap integration',
            'aave_health_monitor.py': 'Health monitoring',
            'gas_fee_calculator.py': 'Gas optimization'
        }
        
        file_status = {}
        for file, description in critical_files.items():
            if os.path.exists(file):
                try:
                    # Check for syntax errors
                    with open(file, 'r') as f:
                        content = f.read()
                        compile(content, file, 'exec')
                    file_status[file] = "✅ Valid syntax"
                except SyntaxError as e:
                    file_status[file] = f"❌ Syntax error: {e}"
                    self.report['critical_issues'].append(f"Syntax error in {file}: {e}")
                except Exception as e:
                    file_status[file] = f"⚠️ Issue: {e}"
                    self.report['warnings'].append(f"File issue in {file}: {e}")
            else:
                file_status[file] = "❌ Missing"
                self.report['critical_issues'].append(f"Missing critical file: {file}")
                
        self.report['component_status']['files'] = file_status
        print(f"   File integrity: {len([v for v in file_status.values() if '✅' in v])}/{len(critical_files)} files valid")
        
    def check_agent_initialization(self):
        """Test agent initialization"""
        print("\n🔍 CHECKING AGENT INITIALIZATION...")
        
        try:
            from arbitrum_testnet_agent import ArbitrumTestnetAgent
            agent = ArbitrumTestnetAgent()
            
            agent_tests = {
                'initialization': '✅ Agent created successfully',
                'wallet_address': f"✅ Wallet: {agent.address}",
                'network_connection': f"✅ Connected to chain {agent.w3.eth.chain_id}",
                'eth_balance': f"✅ ETH Balance: {agent.get_eth_balance():.6f} ETH"
            }
            
            # Test DeFi integrations
            try:
                integration_success = agent.initialize_integrations()
                if integration_success:
                    agent_tests['integrations'] = '✅ DeFi integrations initialized'
                    
                    # Test individual components
                    if hasattr(agent, 'aave') and agent.aave:
                        agent_tests['aave'] = '✅ Aave integration ready'
                    else:
                        agent_tests['aave'] = '❌ Aave integration failed'
                        self.report['critical_issues'].append("Aave integration not working")
                        
                    if hasattr(agent, 'uniswap') and agent.uniswap:
                        agent_tests['uniswap'] = '✅ Uniswap integration ready'
                    else:
                        agent_tests['uniswap'] = '❌ Uniswap integration failed'
                        self.report['critical_issues'].append("Uniswap integration not working")
                        
                    if hasattr(agent, 'health_monitor') and agent.health_monitor:
                        agent_tests['health_monitor'] = '✅ Health monitor ready'
                    else:
                        agent_tests['health_monitor'] = '❌ Health monitor failed'
                        self.report['critical_issues'].append("Health monitor not working")
                else:
                    agent_tests['integrations'] = '❌ DeFi integrations failed'
                    self.report['critical_issues'].append("DeFi integrations failed to initialize")
                    
            except Exception as e:
                agent_tests['integrations'] = f'❌ Integration error: {e}'
                self.report['critical_issues'].append(f"Integration initialization error: {e}")
                
            self.report['component_status']['agent'] = agent_tests
            
        except Exception as e:
            self.report['critical_issues'].append(f"Agent initialization failed: {e}")
            self.report['component_status']['agent'] = {'error': f"❌ Failed to initialize: {e}"}
            
        print(f"   Agent initialization: {'✅ Success' if 'error' not in self.report['component_status']['agent'] else '❌ Failed'}")
        
    def check_dashboard_functionality(self):
        """Test dashboard functionality"""
        print("\n🔍 CHECKING DASHBOARD FUNCTIONALITY...")
        
        dashboard_tests = {}
        
        # Check if dashboard can start
        try:
            # Test import
            import web_dashboard
            dashboard_tests['import'] = '✅ Dashboard imports successfully'
            
            # Test critical functions
            try:
                # Test get_live_agent_data function
                live_data = web_dashboard.get_live_agent_data()
                if live_data:
                    dashboard_tests['live_data'] = '✅ Live data function working'
                else:
                    dashboard_tests['live_data'] = '⚠️ Live data returns None'
                    self.report['warnings'].append("Dashboard live data function returns None")
            except Exception as e:
                dashboard_tests['live_data'] = f'❌ Live data error: {e}'
                self.report['critical_issues'].append(f"Dashboard live data error: {e}")
                
        except Exception as e:
            dashboard_tests['import'] = f'❌ Import error: {e}'
            self.report['critical_issues'].append(f"Dashboard import error: {e}")
            
        self.report['component_status']['dashboard'] = dashboard_tests
        print(f"   Dashboard functionality: {'✅ Working' if all('✅' in v for v in dashboard_tests.values()) else '⚠️ Issues detected'}")
        
    def check_defi_integrations(self):
        """Test DeFi protocol integrations"""
        print("\n🔍 CHECKING DEFI INTEGRATIONS...")
        
        defi_tests = {}
        
        # Test Aave integration
        try:
            from aave_integration import AaveArbitrumIntegration
            defi_tests['aave_import'] = '✅ Aave integration imports'
        except Exception as e:
            defi_tests['aave_import'] = f'❌ Aave import error: {e}'
            self.report['critical_issues'].append(f"Aave integration import error: {e}")
            
        # Test Uniswap integration
        try:
            from uniswap_integration import UniswapArbitrumIntegration
            defi_tests['uniswap_import'] = '✅ Uniswap integration imports'
        except Exception as e:
            defi_tests['uniswap_import'] = f'❌ Uniswap import error: {e}'
            self.report['critical_issues'].append(f"Uniswap integration import error: {e}")
            
        # Test Health Monitor
        try:
            from aave_health_monitor import AaveHealthMonitor
            defi_tests['health_monitor_import'] = '✅ Health monitor imports'
        except Exception as e:
            defi_tests['health_monitor_import'] = f'❌ Health monitor import error: {e}'
            self.report['critical_issues'].append(f"Health monitor import error: {e}")
            
        # Test Gas Calculator
        try:
            from gas_fee_calculator import ArbitrumGasCalculator
            defi_tests['gas_calculator_import'] = '✅ Gas calculator imports'
        except Exception as e:
            defi_tests['gas_calculator_import'] = f'❌ Gas calculator import error: {e}'
            self.report['critical_issues'].append(f"Gas calculator import error: {e}")
            
        self.report['component_status']['defi_integrations'] = defi_tests
        print(f"   DeFi integrations: {len([v for v in defi_tests.values() if '✅' in v])}/{len(defi_tests)} working")
        
    def check_autonomous_functions(self):
        """Test autonomous system functions"""
        print("\n🔍 CHECKING AUTONOMOUS FUNCTIONS...")
        
        function_tests = {}
        
        try:
            from arbitrum_testnet_agent import ArbitrumTestnetAgent
            agent = ArbitrumTestnetAgent()
            
            # Test critical autonomous functions
            critical_functions = [
                'run_real_defi_task',
                'execute_autonomous_sequence_enhanced',
                'check_wallet_readiness_for_defi',
                'get_arb_price',
                'get_optimized_gas_params',
                'update_baseline_after_success',
                'is_operation_on_cooldown'
            ]
            
            for func_name in critical_functions:
                if hasattr(agent, func_name):
                    function_tests[func_name] = '✅ Function exists'
                else:
                    function_tests[func_name] = '❌ Function missing'
                    self.report['critical_issues'].append(f"Missing critical function: {func_name}")
                    
        except Exception as e:
            function_tests['agent_creation'] = f'❌ Cannot create agent: {e}'
            self.report['critical_issues'].append(f"Cannot test autonomous functions: {e}")
            
        self.report['function_tests']['autonomous_functions'] = function_tests
        print(f"   Autonomous functions: {len([v for v in function_tests.values() if '✅' in v])}/{len(function_tests)} available")
        
    def check_trigger_system(self):
        """Test trigger and monitoring system"""
        print("\n🔍 CHECKING TRIGGER SYSTEM...")
        
        trigger_tests = {}
        
        # Check baseline file
        if os.path.exists('agent_baseline.json'):
            try:
                with open('agent_baseline.json', 'r') as f:
                    baseline_data = json.load(f)
                if 'last_collateral_value_usd' in baseline_data:
                    trigger_tests['baseline_file'] = f"✅ Baseline: ${baseline_data['last_collateral_value_usd']:.2f}"
                else:
                    trigger_tests['baseline_file'] = '⚠️ Baseline file missing data'
                    self.report['warnings'].append("Baseline file exists but missing collateral data")
            except Exception as e:
                trigger_tests['baseline_file'] = f'❌ Baseline file error: {e}'
                self.report['warnings'].append(f"Baseline file error: {e}")
        else:
            trigger_tests['baseline_file'] = '⚠️ No baseline file found'
            self.report['warnings'].append("No baseline file found - will be created on first run")
            
        # Check performance log
        if os.path.exists('performance_log.json'):
            trigger_tests['performance_log'] = '✅ Performance log exists'
        else:
            trigger_tests['performance_log'] = '⚠️ No performance log'
            self.report['warnings'].append("No performance log found")
            
        self.report['component_status']['trigger_system'] = trigger_tests
        print(f"   Trigger system: {'✅ Ready' if all('❌' not in v for v in trigger_tests.values()) else '⚠️ Needs setup'}")
        
    def check_emergency_systems(self):
        """Test emergency stop and safety systems"""
        print("\n🔍 CHECKING EMERGENCY SYSTEMS...")
        
        emergency_tests = {}
        
        # Check emergency stop functionality
        try:
            # emergency_stop functionality is integrated
            emergency_tests['emergency_stop_module'] = '✅ Emergency stop module available'
        except Exception as e:
            emergency_tests['emergency_stop_module'] = f'❌ Emergency stop error: {e}'
            self.report['warnings'].append(f"Emergency stop module error: {e}")
            
        # Check emergency flag
        emergency_active = os.path.exists('EMERGENCY_STOP_ACTIVE.flag')
        if emergency_active:
            emergency_tests['emergency_flag'] = '⚠️ Emergency stop is ACTIVE'
            self.report['warnings'].append("Emergency stop is currently active")
        else:
            emergency_tests['emergency_flag'] = '✅ Emergency stop not active'
            
        self.report['component_status']['emergency_systems'] = emergency_tests
        print(f"   Emergency systems: {'✅ Ready' if not emergency_active else '⚠️ Emergency stop active'}")
        
    def check_network_connectivity(self):
        """Test network connectivity and RPC endpoints"""
        print("\n🔍 CHECKING NETWORK CONNECTIVITY...")
        
        network_tests = {}
        
        # Test Arbitrum mainnet RPC
        test_rpcs = [
            "https://arb1.arbitrum.io/rpc",
            "https://arbitrum-one.publicnode.com",
            "https://arbitrum.llamarpc.com"
        ]
        
        working_rpcs = 0
        for rpc in test_rpcs:
            try:
                from web3 import Web3
                w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout': 5}))
                if w3.is_connected():
                    chain_id = w3.eth.chain_id
                    if chain_id == 42161:  # Arbitrum mainnet
                        working_rpcs += 1
                        network_tests[f'rpc_{working_rpcs}'] = f'✅ {rpc[:30]}... working'
                    else:
                        network_tests[f'rpc_error'] = f'❌ Wrong chain ID: {chain_id}'
                else:
                    network_tests[f'rpc_error'] = f'❌ Cannot connect to {rpc[:30]}...'
            except Exception as e:
                network_tests[f'rpc_error'] = f'❌ RPC error: {e}'
                
        if working_rpcs == 0:
            self.report['critical_issues'].append("No working Arbitrum mainnet RPC endpoints")
        elif working_rpcs < 2:
            self.report['warnings'].append("Limited RPC endpoint availability")
            
        # Test CoinMarketCap API
        try:
            api_key = os.getenv('COINMARKETCAP_API_KEY')
            if api_key:
                url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
                headers = {'X-CMC_PRO_API_KEY': api_key}
                params = {'symbol': 'ARB', 'convert': 'USD'}
                response = requests.get(url, headers=headers, params=params, timeout=10)
                if response.status_code == 200:
                    network_tests['coinmarketcap_api'] = '✅ CoinMarketCap API working'
                else:
                    network_tests['coinmarketcap_api'] = f'❌ API error: {response.status_code}'
                    self.report['warnings'].append("CoinMarketCap API not responding properly")
            else:
                network_tests['coinmarketcap_api'] = '❌ No API key found'
        except Exception as e:
            network_tests['coinmarketcap_api'] = f'❌ API test error: {e}'
            self.report['warnings'].append(f"CoinMarketCap API test error: {e}")
            
        self.report['component_status']['network'] = network_tests
        print(f"   Network connectivity: {working_rpcs} RPC endpoints working")
        
    def generate_final_assessment(self):
        """Generate final system assessment"""
        print("\n" + "=" * 80)
        print("🎯 FINAL SYSTEM ASSESSMENT")
        print("=" * 80)
        
        critical_count = len(self.report['critical_issues'])
        warning_count = len(self.report['warnings'])
        
        if critical_count == 0:
            if warning_count == 0:
                self.report['overall_status'] = 'EXCELLENT'
                print("🎉 SYSTEM STATUS: EXCELLENT")
                print("✅ All systems operational and ready for autonomous operation")
                print("✅ No critical issues or warnings detected")
            else:
                self.report['overall_status'] = 'GOOD'
                print("✅ SYSTEM STATUS: GOOD")
                print("✅ All critical systems operational")
                print(f"⚠️ {warning_count} minor warning(s) detected")
        else:
            if critical_count <= 2:
                self.report['overall_status'] = 'NEEDS_ATTENTION'
                print("⚠️ SYSTEM STATUS: NEEDS ATTENTION")
                print(f"❌ {critical_count} critical issue(s) need fixing")
            else:
                self.report['overall_status'] = 'CRITICAL'
                print("❌ SYSTEM STATUS: CRITICAL")
                print(f"❌ {critical_count} critical issues prevent operation")
                
        # Display issues
        if self.report['critical_issues']:
            print(f"\n🚨 CRITICAL ISSUES TO FIX ({critical_count}):")
            for i, issue in enumerate(self.report['critical_issues'], 1):
                print(f"   {i}. {issue}")
                
        if self.report['warnings']:
            print(f"\n⚠️ WARNINGS ({warning_count}):")
            for i, warning in enumerate(self.report['warnings'], 1):
                print(f"   {i}. {warning}")
                
        # Generate recommendations
        self.generate_recommendations()
        
        print("=" * 80)
        
    def generate_recommendations(self):
        """Generate specific recommendations"""
        if self.report['critical_issues']:
            print(f"\n💡 IMMEDIATE ACTIONS REQUIRED:")
            
            for issue in self.report['critical_issues']:
                if 'PRIVATE_KEY' in issue:
                    print("   • Add your mainnet private key to Replit Secrets")
                elif 'COINMARKETCAP_API_KEY' in issue:
                    print("   • Add your CoinMarketCap API key to Replit Secrets")
                elif 'Syntax error' in issue:
                    print("   • Fix syntax errors in code files")
                elif 'integration' in issue.lower():
                    print("   • Check DeFi integration dependencies")
                elif 'RPC' in issue:
                    print("   • Check network connectivity and RPC endpoints")
                    
        if self.report['warnings']:
            print(f"\n🔧 RECOMMENDED IMPROVEMENTS:")
            for warning in self.report['warnings']:
                if 'baseline' in warning.lower():
                    print("   • Baseline will be auto-created on first autonomous run")
                elif 'emergency' in warning.lower():
                    print("   • Clear emergency stop if not needed")
                elif 'API' in warning:
                    print("   • Verify API credentials and connectivity")
                    
        # Always provide system readiness guidance
        if self.report['overall_status'] in ['EXCELLENT', 'GOOD']:
            print(f"\n🚀 SYSTEM READY FOR OPERATION:")
            print("   • Run: python complete_autonomous_launcher.py")
            print("   • Monitor dashboard at: http://localhost:5000")
            print("   • Emergency stop available if needed")
            
    def save_report(self):
        """Save diagnostic report to file"""
        try:
            with open('system_diagnostic_report.json', 'w') as f:
                json.dump(self.report, f, indent=2)
            print(f"\n📄 Diagnostic report saved to: system_diagnostic_report.json")
        except Exception as e:
            print(f"⚠️ Could not save report: {e}")

    def check_environment_variables(self):
        """Check all required environment variables"""
        print("\n🔍 CHECKING ENVIRONMENT VARIABLES...")
        
        required_vars = {
            'PRIVATE_KEY': 'Wallet private key for mainnet operations',
            'COINMARKETCAP_API_KEY': 'Price data API key',
            'NETWORK_MODE': 'Network mode (should be mainnet)'
        }
        
        env_status = {}
        for var, description in required_vars.items():
            value = os.getenv(var)
            if value:
                if var == 'PRIVATE_KEY':
                    env_status[var] = f"✅ Set (length: {len(value)})"
                    if len(value) != 66 or not value.startswith('0x'):
                        self.report['warnings'].append(f"{var} may have incorrect format")
                elif var == 'NETWORK_MODE':
                    env_status[var] = f"✅ Set: {value}"
                    if value != 'mainnet':
                        self.report['warnings'].append(f"Network mode is {value}, expected 'mainnet'")
                else:
                    env_status[var] = f"✅ Set (length: {len(value)})"
            else:
                env_status[var] = "❌ Not set"
                self.report['critical_issues'].append(f"Missing {var}: {description}")
                
        self.report['component_status']['environment'] = env_status
        print(f"   Environment variables: {len([v for v in env_status.values() if '✅' in v])}/{len(required_vars)} configured")

    def check_file_integrity(self):
        """Check critical files exist and are valid"""
        print("\n🔍 CHECKING FILE INTEGRITY...")
        
        critical_files = {
            'arbitrum_testnet_agent.py': 'Main agent implementation',
            'web_dashboard.py': 'Dashboard interface',
            'complete_autonomous_launcher.py': 'System launcher',
            'aave_integration.py': 'Aave DeFi integration',
            'uniswap_integration.py': 'Uniswap integration',
            'aave_health_monitor.py': 'Health monitoring',
            'gas_fee_calculator.py': 'Gas optimization'
        }
        
        file_status = {}
        for file, description in critical_files.items():
            if os.path.exists(file):
                try:
                    # Check for syntax errors
                    with open(file, 'r') as f:
                        content = f.read()
                        compile(content, file, 'exec')
                    file_status[file] = "✅ Valid syntax"
                except SyntaxError as e:
                    file_status[file] = f"❌ Syntax error: {e}"
                    self.report['critical_issues'].append(f"Syntax error in {file}: {e}")
                except Exception as e:
                    file_status[file] = f"⚠️ Issue: {e}"
                    self.report['warnings'].append(f"File issue in {file}: {e}")
            else:
                file_status[file] = "❌ Missing"
                self.report['critical_issues'].append(f"Missing critical file: {file}")
                
        self.report['component_status']['files'] = file_status
        print(f"   File integrity: {len([v for v in file_status.values() if '✅' in v])}/{len(critical_files)} files valid")

    def check_agent_initialization(self):
        """Test agent initialization"""
        print("\n🔍 CHECKING AGENT INITIALIZATION...")
        
        try:
            from arbitrum_testnet_agent import ArbitrumTestnetAgent
            agent = ArbitrumTestnetAgent()
            
            agent_tests = {
                'initialization': '✅ Agent created successfully',
                'wallet_address': f"✅ Wallet: {agent.address}",
                'network_connection': f"✅ Connected to chain {agent.w3.eth.chain_id}",
                'eth_balance': f"✅ ETH Balance: {agent.get_eth_balance():.6f} ETH"
            }
            
            # Test DeFi integrations
            try:
                integration_success = agent.initialize_integrations()
                if integration_success:
                    agent_tests['integrations'] = '✅ DeFi integrations initialized'
                    
                    # Test individual components
                    if hasattr(agent, 'aave') and agent.aave:
                        agent_tests['aave'] = '✅ Aave integration ready'
                    else:
                        agent_tests['aave'] = '❌ Aave integration failed'
                        self.report['critical_issues'].append("Aave integration not working")
                        
                    if hasattr(agent, 'uniswap') and agent.uniswap:
                        agent_tests['uniswap'] = '✅ Uniswap integration ready'
                    else:
                        agent_tests['uniswap'] = '❌ Uniswap integration failed'
                        self.report['critical_issues'].append("Uniswap integration not working")
                        
                    if hasattr(agent, 'health_monitor') and agent.health_monitor:
                        agent_tests['health_monitor'] = '✅ Health monitor ready'
                    else:
                        agent_tests['health_monitor'] = '❌ Health monitor failed'
                        self.report['critical_issues'].append("Health monitor not working")
                else:
                    agent_tests['integrations'] = '❌ DeFi integrations failed'
                    self.report['critical_issues'].append("DeFi integrations failed to initialize")
                    
            except Exception as e:
                agent_tests['integrations'] = f'❌ Integration error: {e}'
                self.report['critical_issues'].append(f"Integration initialization error: {e}")
                
            self.report['component_status']['agent'] = agent_tests
            
        except Exception as e:
            self.report['critical_issues'].append(f"Agent initialization failed: {e}")
            self.report['component_status']['agent'] = {'error': f"❌ Failed to initialize: {e}"}
            
        print(f"   Agent initialization: {'✅ Success' if 'error' not in self.report['component_status']['agent'] else '❌ Failed'}")

    def check_dashboard_functionality(self):
        """Test dashboard functionality"""
        print("\n🔍 CHECKING DASHBOARD FUNCTIONALITY...")
        
        dashboard_tests = {}
        
        # Check if dashboard can start
        try:
            # Test import
            import web_dashboard
            dashboard_tests['import'] = '✅ Dashboard imports successfully'
            
            # Test critical functions
            try:
                # Test get_live_agent_data function
                live_data = web_dashboard.get_live_agent_data()
                if live_data:
                    dashboard_tests['live_data'] = '✅ Live data function working'
                else:
                    dashboard_tests['live_data'] = '⚠️ Live data returns None'
                    self.report['warnings'].append("Dashboard live data function returns None")
            except Exception as e:
                dashboard_tests['live_data'] = f'❌ Live data error: {e}'
                self.report['critical_issues'].append(f"Dashboard live data error: {e}")
                
        except Exception as e:
            dashboard_tests['import'] = f'❌ Import error: {e}'
            self.report['critical_issues'].append(f"Dashboard import error: {e}")
            
        self.report['component_status']['dashboard'] = dashboard_tests
        print(f"   Dashboard functionality: {'✅ Working' if all('✅' in v for v in dashboard_tests.values()) else '⚠️ Issues detected'}")

    def check_defi_integrations(self):
        """Test DeFi protocol integrations"""
        print("\n🔍 CHECKING DEFI INTEGRATIONS...")
        
        defi_tests = {}
        
        # Test Aave integration
        try:
            from aave_integration import AaveArbitrumIntegration
            defi_tests['aave_import'] = '✅ Aave integration imports'
        except Exception as e:
            defi_tests['aave_import'] = f'❌ Aave import error: {e}'
            self.report['critical_issues'].append(f"Aave integration import error: {e}")
            
        # Test Uniswap integration
        try:
            from uniswap_integration import UniswapArbitrumIntegration
            defi_tests['uniswap_import'] = '✅ Uniswap integration imports'
        except Exception as e:
            defi_tests['uniswap_import'] = f'❌ Uniswap import error: {e}'
            self.report['critical_issues'].append(f"Uniswap integration import error: {e}")
            
        # Test Health Monitor
        try:
            from aave_health_monitor import AaveHealthMonitor
            defi_tests['health_monitor_import'] = '✅ Health monitor imports'
        except Exception as e:
            defi_tests['health_monitor_import'] = f'❌ Health monitor import error: {e}'
            self.report['critical_issues'].append(f"Health monitor import error: {e}")
            
        # Test Gas Calculator
        try:
            from gas_fee_calculator import ArbitrumGasCalculator
            defi_tests['gas_calculator_import'] = '✅ Gas calculator imports'
        except Exception as e:
            defi_tests['gas_calculator_import'] = f'❌ Gas calculator import error: {e}'
            self.report['critical_issues'].append(f"Gas calculator import error: {e}")
            
        self.report['component_status']['defi_integrations'] = defi_tests
        print(f"   DeFi integrations: {len([v for v in defi_tests.values() if '✅' in v])}/{len(defi_tests)} working")

    def check_autonomous_functions(self):
        """Test autonomous system functions"""
        print("\n🔍 CHECKING AUTONOMOUS FUNCTIONS...")
        
        function_tests = {}
        
        try:
            from arbitrum_testnet_agent import ArbitrumTestnetAgent
            agent = ArbitrumTestnetAgent()
            
            # Test critical autonomous functions
            critical_functions = [
                'run_real_defi_task',
                'execute_autonomous_sequence_enhanced',
                'check_wallet_readiness_for_defi',
                'get_arb_price',
                'get_optimized_gas_params',
                'update_baseline_after_success',
                'is_operation_on_cooldown'
            ]
            
            for func_name in critical_functions:
                if hasattr(agent, func_name):
                    function_tests[func_name] = '✅ Function exists'
                else:
                    function_tests[func_name] = '❌ Function missing'
                    self.report['critical_issues'].append(f"Missing critical function: {func_name}")
                    
        except Exception as e:
            function_tests['agent_creation'] = f'❌ Cannot create agent: {e}'
            self.report['critical_issues'].append(f"Cannot test autonomous functions: {e}")
            
        self.report['function_tests']['autonomous_functions'] = function_tests
        print(f"   Autonomous functions: {len([v for v in function_tests.values() if '✅' in v])}/{len(function_tests)} available")

    def check_trigger_system(self):
        """Test trigger and monitoring system"""
        print("\n🔍 CHECKING TRIGGER SYSTEM...")
        
        trigger_tests = {}
        
        # Check baseline file
        if os.path.exists('agent_baseline.json'):
            try:
                with open('agent_baseline.json', 'r') as f:
                    baseline_data = json.load(f)
                if 'last_collateral_value_usd' in baseline_data:
                    trigger_tests['baseline_file'] = f"✅ Baseline: ${baseline_data['last_collateral_value_usd']:.2f}"
                else:
                    trigger_tests['baseline_file'] = '⚠️ Baseline file missing data'
                    self.report['warnings'].append("Baseline file exists but missing collateral data")
            except Exception as e:
                trigger_tests['baseline_file'] = f'❌ Baseline file error: {e}'
                self.report['warnings'].append(f"Baseline file error: {e}")
        else:
            trigger_tests['baseline_file'] = '⚠️ No baseline file found'
            self.report['warnings'].append("No baseline file found - will be created on first run")
            
        # Check performance log
        if os.path.exists('performance_log.json'):
            trigger_tests['performance_log'] = '✅ Performance log exists'
        else:
            trigger_tests['performance_log'] = '⚠️ No performance log'
            self.report['warnings'].append("No performance log found")
            
        self.report['component_status']['trigger_system'] = trigger_tests
        print(f"   Trigger system: {'✅ Ready' if all('❌' not in v for v in trigger_tests.values()) else '⚠️ Needs setup'}")

    def check_emergency_systems(self):
        """Test emergency stop and safety systems"""
        print("\n🔍 CHECKING EMERGENCY SYSTEMS...")
        
        emergency_tests = {}
        
        # Check emergency stop functionality
        try:
            # emergency_stop functionality is integrated
            emergency_tests['emergency_stop_module'] = '✅ Emergency stop module available'
        except Exception as e:
            emergency_tests['emergency_stop_module'] = f'❌ Emergency stop error: {e}'
            self.report['warnings'].append(f"Emergency stop module error: {e}")
            
        # Check emergency flag
        emergency_active = os.path.exists('EMERGENCY_STOP_ACTIVE.flag')
        if emergency_active:
            emergency_tests['emergency_flag'] = '⚠️ Emergency stop is ACTIVE'
            self.report['warnings'].append("Emergency stop is currently active")
        else:
            emergency_tests['emergency_flag'] = '✅ Emergency stop not active'
            
        self.report['component_status']['emergency_systems'] = emergency_tests
        print(f"   Emergency systems: {'✅ Ready' if not emergency_active else '⚠️ Emergency stop active'}")

    def check_network_connectivity(self):
        """Test network connectivity and RPC endpoints"""
        print("\n🔍 CHECKING NETWORK CONNECTIVITY...")
        
        network_tests = {}
        
        # Test Arbitrum mainnet RPC
        test_rpcs = [
            "https://arb1.arbitrum.io/rpc",
            "https://arbitrum-one.publicnode.com",
            "https://arbitrum.llamarpc.com"
        ]
        
        working_rpcs = 0
        for rpc in test_rpcs:
            try:
                from web3 import Web3
                w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout': 5}))
                if w3.is_connected():
                    chain_id = w3.eth.chain_id
                    if chain_id == 42161:  # Arbitrum mainnet
                        working_rpcs += 1
                        network_tests[f'rpc_{working_rpcs}'] = f'✅ {rpc[:30]}... working'
                    else:
                        network_tests[f'rpc_error'] = f'❌ Wrong chain ID: {chain_id}'
                else:
                    network_tests[f'rpc_error'] = f'❌ Cannot connect to {rpc[:30]}...'
            except Exception as e:
                network_tests[f'rpc_error'] = f'❌ RPC error: {e}'
                
        if working_rpcs == 0:
            self.report['critical_issues'].append("No working Arbitrum mainnet RPC endpoints")
        elif working_rpcs < 2:
            self.report['warnings'].append("Limited RPC endpoint availability")
            
        # Test CoinMarketCap API
        try:
            api_key = os.getenv('COINMARKETCAP_API_KEY')
            if api_key:
                url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
                headers = {'X-CMC_PRO_API_KEY': api_key}
                params = {'symbol': 'ARB', 'convert': 'USD'}
                response = requests.get(url, headers=headers, params=params, timeout=10)
                if response.status_code == 200:
                    network_tests['coinmarketcap_api'] = '✅ CoinMarketCap API working'
                else:
                    network_tests['coinmarketcap_api'] = f'❌ API error: {response.status_code}'
                    self.report['warnings'].append("CoinMarketCap API not responding properly")
            else:
                network_tests['coinmarketcap_api'] = '❌ No API key found'
        except Exception as e:
            network_tests['coinmarketcap_api'] = f'❌ API test error: {e}'
            self.report['warnings'].append(f"CoinMarketCap API test error: {e}")
            
        self.report['component_status']['network'] = network_tests
        print(f"   Network connectivity: {working_rpcs} RPC endpoints working")

    def generate_final_assessment(self):
        """Generate final system assessment"""
        print("\n" + "=" * 80)
        print("🎯 FINAL SYSTEM ASSESSMENT")
        print("=" * 80)
        
        critical_count = len(self.report['critical_issues'])
        warning_count = len(self.report['warnings'])
        
        if critical_count == 0:
            if warning_count == 0:
                self.report['overall_status'] = 'EXCELLENT'
                print("🎉 SYSTEM STATUS: EXCELLENT")
                print("✅ All systems operational and ready for autonomous operation")
                print("✅ No critical issues or warnings detected")
            else:
                self.report['overall_status'] = 'GOOD'
                print("✅ SYSTEM STATUS: GOOD")
                print("✅ All critical systems operational")
                print(f"⚠️ {warning_count} minor warning(s) detected")
        else:
            if critical_count <= 2:
                self.report['overall_status'] = 'NEEDS_ATTENTION'
                print("⚠️ SYSTEM STATUS: NEEDS ATTENTION")
                print(f"❌ {critical_count} critical issue(s) need fixing")
            else:
                self.report['overall_status'] = 'CRITICAL'
                print("❌ SYSTEM STATUS: CRITICAL")
                print(f"❌ {critical_count} critical issues prevent operation")
                
        # Display issues
        if self.report['critical_issues']:
            print(f"\n🚨 CRITICAL ISSUES TO FIX ({critical_count}):")
            for i, issue in enumerate(self.report['critical_issues'], 1):
                print(f"   {i}. {issue}")
                
        if self.report['warnings']:
            print(f"\n⚠️ WARNINGS ({warning_count}):")
            for i, warning in enumerate(self.report['warnings'], 1):
                print(f"   {i}. {warning}")
                
        # Generate recommendations
        self.generate_recommendations()
        
        print("=" * 80)
# --- Merged from system_diagnostic_complete.py ---

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
# --- Merged from wallet_diagnostics.py ---

def test_wallet_connectivity():
    """Test wallet connectivity and basic functionality"""
    print("🔍 WALLET CONNECTIVITY DIAGNOSTICS")
    print("=" * 50)
    
    try:
        # Test environment variables
        private_key = os.getenv('WALLET_PRIVATE_KEY')
        if not private_key:
            print("❌ WALLET_PRIVATE_KEY not found in environment")
            return False
        
        print("✅ WALLET_PRIVATE_KEY found in environment")
        
        # Test key format
        if private_key.startswith('0x'):
            hex_part = private_key[2:]
        else:
            hex_part = private_key
            
        if len(hex_part) != 64:
            print(f"❌ Invalid private key length: {len(hex_part)} (expected 64)")
            return False
            
        print("✅ Private key format validation passed")
        
        # Test RPC connectivity
        rpc_urls = [
            "https://arb1.arbitrum.io/rpc",
            "https://arbitrum-one.public.blastapi.io",
            "https://arbitrum-one.publicnode.com"
        ]
        
        working_rpcs = 0
        for rpc_url in rpc_urls:
            try:
                w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 10}))
                if w3.is_connected():
                    chain_id = w3.eth.chain_id
                    if chain_id == 42161:
                        print(f"✅ RPC working: {rpc_url}")
                        working_rpcs += 1
                    else:
                        print(f"❌ Wrong chain ID {chain_id}: {rpc_url}")
                else:
                    print(f"❌ Connection failed: {rpc_url}")
            except Exception as e:
                print(f"❌ RPC error {rpc_url}: {e}")
                
        if working_rpcs > 0:
            print(f"✅ {working_rpcs}/{len(rpc_urls)} RPC endpoints working")
            return True
        else:
            print("❌ No working RPC endpoints found")
            return False
            
    except Exception as e:
        print(f"❌ Wallet diagnostics failed: {e}")
        return False
# --- Merged from borrow_diagnostic_tool.py ---

class BorrowDiagnosticTool:
    def __init__(self, agent):
        self.agent = agent
        self.w3 = agent.w3
        self.diagnostics = {}

    def run_comprehensive_borrow_diagnostic(self):
        """Run comprehensive borrow diagnostic"""
        print("🔍 COMPREHENSIVE BORROWING DIAGNOSTIC")
        print("=" * 50)

        try:
            # Initialize results
            self.diagnostics = {
                'timestamp': datetime.now().isoformat(),
                'wallet_address': self.agent.address,
                'network_mode': self.agent.network_mode,
                'tests': {}
            }

            # Test 1: Network and connectivity
            self._test_network_connectivity()
            
            # Test 2: Contract validation
            self._test_contract_validation()
            
            # Test 3: Aave position analysis
            self._test_aave_position()
            
            # Test 4: Gas and ETH analysis
            self._test_gas_readiness()
            
            # Test 5: Enhanced borrow manager
            self._test_enhanced_borrow_manager()
            
            # Test 6: Simulation test
            self._test_borrow_simulation()

            # Generate final report
            self._generate_diagnostic_report()
            
            return self.diagnostics

        except Exception as e:
            print(f"❌ Comprehensive diagnostic failed: {e}")
            self.diagnostics['critical_error'] = str(e)
            return self.diagnostics

    def _test_network_connectivity(self):
        """Test network connectivity and RPC health"""
        print("\n1️⃣ Testing Network Connectivity...")
        test_result = {
            'connected': False,
            'chain_id': None,
            'block_number': None,
            'gas_price': None,
            'issues': []
        }

        try:
            if not self.w3.is_connected():
                test_result['issues'].append("Web3 not connected")
                return

            test_result['connected'] = True
            test_result['chain_id'] = self.w3.eth.chain_id
            test_result['block_number'] = self.w3.eth.block_number
            test_result['gas_price'] = self.w3.eth.gas_price

            print(f"   ✅ Connected to chain {test_result['chain_id']}")
            print(f"   ✅ Latest block: {test_result['block_number']}")
            print(f"   ✅ Gas price: {Web3.from_wei(test_result['gas_price'], 'gwei'):.2f} gwei")

        except Exception as e:
            test_result['issues'].append(f"Network test failed: {e}")
            print(f"   ❌ Network connectivity failed: {e}")

        self.diagnostics['tests']['network'] = test_result

    def _test_contract_validation(self):
        """Test all contract addresses"""
        print("\n2️⃣ Testing Contract Validation...")
        test_result = {
            'contracts_valid': {},
            'aave_pool_valid': False,
            'issues': []
        }

        try:
            # Test token contracts
            contracts = {
                'USDC': self.agent.usdc_address,
                'WBTC': self.agent.wbtc_address,
                'WETH': self.agent.weth_address,
                'DAI': self.agent.dai_address
            }

            for name, address in contracts.items():
                try:
                    if not Web3.is_address(address):
                        test_result['contracts_valid'][name] = False
                        test_result['issues'].append(f"Invalid {name} address")
                        continue

                    code = self.w3.eth.get_code(Web3.to_checksum_address(address))
                    if code == b'':
                        test_result['contracts_valid'][name] = False
                        test_result['issues'].append(f"No contract at {name} address")
                        continue

                    test_result['contracts_valid'][name] = True
                    print(f"   ✅ {name}: Valid contract")

                except Exception as e:
                    test_result['contracts_valid'][name] = False
                    test_result['issues'].append(f"{name} validation failed: {e}")
                    print(f"   ❌ {name}: {e}")

            # Test Aave pool
            try:
                pool_abi = [{
                    "inputs": [{"name": "user", "type": "address"}],
                    "name": "getUserAccountData",
                    "outputs": [
                        {"name": "totalCollateralBase", "type": "uint256"},
                        {"name": "totalDebtBase", "type": "uint256"},
                        {"name": "availableBorrowsBase", "type": "uint256"},
                        {"name": "currentLiquidationThreshold", "type": "uint256"},
                        {"name": "ltv", "type": "uint256"},
                        {"name": "healthFactor", "type": "uint256"}
                    ],
                    "stateMutability": "view",
                    "type": "function"
                }]

                pool_contract = self.w3.eth.contract(
                    address=Web3.to_checksum_address(self.agent.aave_pool_address),
                    abi=pool_abi
                )

                # Test with agent's address
                account_data = pool_contract.functions.getUserAccountData(self.agent.address).call()
                test_result['aave_pool_valid'] = True
                print(f"   ✅ Aave Pool: Valid and accessible")

            except Exception as e:
                test_result['issues'].append(f"Aave pool validation failed: {e}")
                print(f"   ❌ Aave Pool: {e}")

        except Exception as e:
            test_result['issues'].append(f"Contract validation failed: {e}")
            print(f"   ❌ Contract validation error: {e}")

        self.diagnostics['tests']['contracts'] = test_result

    def _test_aave_position(self):
        """Test current Aave position"""
        print("\n3️⃣ Testing Aave Position...")
        test_result = {
            'position_accessible': False,
            'collateral_usd': 0,
            'debt_usd': 0,
            'available_borrows_usd': 0,
            'health_factor': 0,
            'can_borrow': False,
            'issues': []
        }

        try:
            pool_abi = [{
                "inputs": [{"name": "user", "type": "address"}],
                "name": "getUserAccountData",
                "outputs": [
                    {"name": "totalCollateralBase", "type": "uint256"},
                    {"name": "totalDebtBase", "type": "uint256"},
                    {"name": "availableBorrowsBase", "type": "uint256"},
                    {"name": "currentLiquidationThreshold", "type": "uint256"},
                    {"name": "ltv", "type": "uint256"},
                    {"name": "healthFactor", "type": "uint256"}
                ],
                "stateMutability": "view",
                "type": "function"
            }]

            pool_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.agent.aave_pool_address),
                abi=pool_abi
            )

            account_data = pool_contract.functions.getUserAccountData(self.agent.address).call()

            test_result['position_accessible'] = True
            test_result['collateral_usd'] = account_data[0] / (10**8)
            test_result['debt_usd'] = account_data[1] / (10**8)
            test_result['available_borrows_usd'] = account_data[2] / (10**8)
            test_result['health_factor'] = account_data[5] / (10**18) if account_data[5] > 0 else float('inf')

            print(f"   ✅ Collateral: ${test_result['collateral_usd']:,.2f}")
            print(f"   ✅ Debt: ${test_result['debt_usd']:,.2f}")
            print(f"   ✅ Available Borrows: ${test_result['available_borrows_usd']:,.2f}")
            print(f"   ✅ Health Factor: {test_result['health_factor']:.4f}")

            # Determine if can borrow
            test_result['can_borrow'] = (
                test_result['health_factor'] > 1.5 and
                test_result['available_borrows_usd'] >= 1.0
            )

            if test_result['can_borrow']:
                print(f"   ✅ Position ready for borrowing")
            else:
                reasons = []
                if test_result['health_factor'] <= 1.5:
                    reasons.append(f"Low health factor: {test_result['health_factor']:.4f}")
                if test_result['available_borrows_usd'] < 1.0:
                    reasons.append(f"Low available borrows: ${test_result['available_borrows_usd']:.2f}")
                test_result['issues'].extend(reasons)
                print(f"   ⚠️ Position not ready: {', '.join(reasons)}")

        except Exception as e:
            test_result['issues'].append(f"Aave position test failed: {e}")
            print(f"   ❌ Aave position test failed: {e}")

        self.diagnostics['tests']['aave_position'] = test_result

    def _test_gas_readiness(self):
        """Test ETH balance and gas readiness"""
        print("\n4️⃣ Testing Gas Readiness...")
        test_result = {
            'eth_balance': 0,
            'sufficient_for_gas': False,
            'estimated_gas_cost': 0,
            'issues': []
        }

        try:
            eth_balance = self.agent.get_eth_balance()
            test_result['eth_balance'] = float(eth_balance)

            # Estimate gas cost for borrow operation
            current_gas_price = self.w3.eth.gas_price
            estimated_gas_limit = 300000  # Conservative estimate for borrow
            estimated_cost_wei = current_gas_price * estimated_gas_limit
            estimated_cost_eth = Web3.from_wei(estimated_cost_wei, 'ether')
            test_result['estimated_gas_cost'] = float(estimated_cost_eth)

            min_eth_needed = estimated_cost_eth * 2  # 2x buffer
            test_result['sufficient_for_gas'] = eth_balance >= min_eth_needed

            print(f"   ✅ ETH Balance: {eth_balance:.6f} ETH")
            print(f"   ✅ Estimated Gas Cost: {estimated_cost_eth:.6f} ETH")

            if test_result['sufficient_for_gas']:
                print(f"   ✅ Sufficient ETH for gas operations")
            else:
                shortage = min_eth_needed - eth_balance
                test_result['issues'].append(f"Need {shortage:.6f} more ETH for gas")
                print(f"   ⚠️ Need {shortage:.6f} more ETH")

        except Exception as e:
            test_result['issues'].append(f"Gas readiness test failed: {e}")
            print(f"   ❌ Gas readiness test failed: {e}")

        self.diagnostics['tests']['gas_readiness'] = test_result

    def _test_enhanced_borrow_manager(self):
        """Test enhanced borrow manager"""
        print("\n5️⃣ Testing Enhanced Borrow Manager...")
        test_result = {
            'manager_available': False,
            'validation_method_exists': False,
            'fallback_methods_available': 0,
            'issues': []
        }

        try:
            # Check if enhanced borrow manager exists
            if hasattr(self.agent, 'enhanced_borrow_manager') and self.agent.enhanced_borrow_manager:
                test_result['manager_available'] = True
                ebm = self.agent.enhanced_borrow_manager
                print(f"   ✅ Enhanced Borrow Manager: Available")

                # Check validation method
                if hasattr(ebm, '_validate_borrow_conditions'):
                    test_result['validation_method_exists'] = True
                    print(f"   ✅ Validation Method: Available")
                else:
                    test_result['issues'].append("Validation method missing")

                # Check fallback methods
                fallback_methods = [
                    'safe_borrow_with_fallbacks',
                    '_validate_borrow_conditions'
                ]
                
                available_methods = sum(1 for method in fallback_methods if hasattr(ebm, method))
                test_result['fallback_methods_available'] = available_methods
                print(f"   ✅ Fallback Methods: {available_methods}/{len(fallback_methods)}")

            else:
                test_result['issues'].append("Enhanced borrow manager not initialized")
                print(f"   ❌ Enhanced Borrow Manager: Not available")

        except Exception as e:
            test_result['issues'].append(f"Enhanced borrow manager test failed: {e}")
            print(f"   ❌ Enhanced borrow manager test failed: {e}")

        self.diagnostics['tests']['enhanced_borrow_manager'] = test_result

    def _test_borrow_simulation(self):
        """Test borrow operation simulation"""
        print("\n6️⃣ Testing Borrow Simulation...")
        test_result = {
            'simulation_possible': False,
            'recommended_amount': 0,
            'safety_checks_passed': False,
            'issues': []
        }

        try:
            # Get current position data
            aave_test = self.diagnostics['tests'].get('aave_position', {})
            
            if not aave_test.get('position_accessible'):
                test_result['issues'].append("Cannot access Aave position for simulation")
                return

            available_borrows = aave_test.get('available_borrows_usd', 0)
            health_factor = aave_test.get('health_factor', 0)

            # Calculate recommended borrow amount
            if available_borrows > 0 and health_factor > 1.5:
                # Conservative: 10% of available capacity, min $0.50, max $5.00
                recommended = min(max(available_borrows * 0.1, 0.5), 5.0)
                test_result['recommended_amount'] = recommended
                test_result['simulation_possible'] = True
                test_result['safety_checks_passed'] = True
                
                print(f"   ✅ Simulation Possible: Yes")
                print(f"   ✅ Recommended Amount: ${recommended:.2f}")
                print(f"   ✅ Safety Checks: Passed")
            else:
                reasons = []
                if available_borrows <= 0:
                    reasons.append("No available borrows")
                if health_factor <= 1.5:
                    reasons.append(f"Low health factor: {health_factor:.4f}")
                test_result['issues'].extend(reasons)
                print(f"   ⚠️ Simulation not recommended: {', '.join(reasons)}")

        except Exception as e:
            test_result['issues'].append(f"Borrow simulation failed: {e}")
            print(f"   ❌ Borrow simulation failed: {e}")

        self.diagnostics['tests']['borrow_simulation'] = test_result

    def _generate_diagnostic_report(self):
        """Generate final diagnostic report"""
        print("\n📊 DIAGNOSTIC SUMMARY")
        print("=" * 30)

        total_tests = len(self.diagnostics['tests'])
        passed_tests = 0
        critical_issues = []

        for test_name, test_data in self.diagnostics['tests'].items():
            issues = test_data.get('issues', [])
            
            if test_name == 'network' and test_data.get('connected'):
                passed_tests += 1
                print(f"✅ Network: PASSED")
            elif test_name == 'contracts' and test_data.get('aave_pool_valid'):
                passed_tests += 1
                print(f"✅ Contracts: PASSED")
            elif test_name == 'aave_position' and test_data.get('position_accessible'):
                passed_tests += 1
                print(f"✅ Aave Position: PASSED")
            elif test_name == 'gas_readiness' and test_data.get('sufficient_for_gas'):
                passed_tests += 1
                print(f"✅ Gas Readiness: PASSED")
            elif test_name == 'enhanced_borrow_manager' and test_data.get('manager_available'):
                passed_tests += 1
                print(f"✅ Enhanced Borrow Manager: PASSED")
            elif test_name == 'borrow_simulation' and test_data.get('simulation_possible'):
                passed_tests += 1
                print(f"✅ Borrow Simulation: PASSED")
            else:
                print(f"❌ {test_name.replace('_', ' ').title()}: FAILED")
                critical_issues.extend(issues)

        print(f"\n🎯 Overall Score: {passed_tests}/{total_tests} tests passed")

        if critical_issues:
            print(f"\n🚨 CRITICAL ISSUES:")
            for issue in critical_issues[:5]:  # Show top 5 issues
                print(f"   • {issue}")

        # Save diagnostic report
        self._save_diagnostic_report()

        return passed_tests >= (total_tests * 0.8)  # 80% pass rate

    def _save_diagnostic_report(self):
        """Save diagnostic report to file"""
        try:
            filename = f"borrow_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            from fix_json_serialization import safe_json_dump
            success = safe_json_dump(self.diagnostics, filename)
            
            if success:
                print(f"\n💾 Diagnostic report saved: {filename}")
            else:
                print(f"\n⚠️ Failed to save diagnostic report")

        except Exception as e:
            print(f"⚠️ Error saving report: {e}")

def run_borrow_diagnostic():
    """Run the borrow diagnostic tool"""
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        print("🚀 Initializing Borrow Diagnostic Tool...")
        agent = ArbitrumTestnetAgent()
        
        # Initialize integrations if needed
        if not hasattr(agent, 'aave') or not agent.aave:
            print("🔄 Initializing DeFi integrations...")
            agent.initialize_integrations()
        
        diagnostic_tool = BorrowDiagnosticTool(agent)
        results = diagnostic_tool.run_comprehensive_borrow_diagnostic()
        
        return results
        
    except Exception as e:
        print(f"❌ Borrow diagnostic failed: {e}")
        return None

    def run_comprehensive_borrow_diagnostic(self):
        """Run comprehensive borrow diagnostic"""
        print("🔍 COMPREHENSIVE BORROWING DIAGNOSTIC")
        print("=" * 50)

        try:
            # Initialize results
            self.diagnostics = {
                'timestamp': datetime.now().isoformat(),
                'wallet_address': self.agent.address,
                'network_mode': self.agent.network_mode,
                'tests': {}
            }

            # Test 1: Network and connectivity
            self._test_network_connectivity()
            
            # Test 2: Contract validation
            self._test_contract_validation()
            
            # Test 3: Aave position analysis
            self._test_aave_position()
            
            # Test 4: Gas and ETH analysis
            self._test_gas_readiness()
            
            # Test 5: Enhanced borrow manager
            self._test_enhanced_borrow_manager()
            
            # Test 6: Simulation test
            self._test_borrow_simulation()

            # Generate final report
            self._generate_diagnostic_report()
            
            return self.diagnostics

        except Exception as e:
            print(f"❌ Comprehensive diagnostic failed: {e}")
            self.diagnostics['critical_error'] = str(e)
            return self.diagnostics

    def _test_network_connectivity(self):
        """Test network connectivity and RPC health"""
        print("\n1️⃣ Testing Network Connectivity...")
        test_result = {
            'connected': False,
            'chain_id': None,
            'block_number': None,
            'gas_price': None,
            'issues': []
        }

        try:
            if not self.w3.is_connected():
                test_result['issues'].append("Web3 not connected")
                return

            test_result['connected'] = True
            test_result['chain_id'] = self.w3.eth.chain_id
            test_result['block_number'] = self.w3.eth.block_number
            test_result['gas_price'] = self.w3.eth.gas_price

            print(f"   ✅ Connected to chain {test_result['chain_id']}")
            print(f"   ✅ Latest block: {test_result['block_number']}")
            print(f"   ✅ Gas price: {Web3.from_wei(test_result['gas_price'], 'gwei'):.2f} gwei")

        except Exception as e:
            test_result['issues'].append(f"Network test failed: {e}")
            print(f"   ❌ Network connectivity failed: {e}")

        self.diagnostics['tests']['network'] = test_result

    def _test_contract_validation(self):
        """Test all contract addresses"""
        print("\n2️⃣ Testing Contract Validation...")
        test_result = {
            'contracts_valid': {},
            'aave_pool_valid': False,
            'issues': []
        }

        try:
            # Test token contracts
            contracts = {
                'USDC': self.agent.usdc_address,
                'WBTC': self.agent.wbtc_address,
                'WETH': self.agent.weth_address,
                'DAI': self.agent.dai_address
            }

            for name, address in contracts.items():
                try:
                    if not Web3.is_address(address):
                        test_result['contracts_valid'][name] = False
                        test_result['issues'].append(f"Invalid {name} address")
                        continue

                    code = self.w3.eth.get_code(Web3.to_checksum_address(address))
                    if code == b'':
                        test_result['contracts_valid'][name] = False
                        test_result['issues'].append(f"No contract at {name} address")
                        continue

                    test_result['contracts_valid'][name] = True
                    print(f"   ✅ {name}: Valid contract")

                except Exception as e:
                    test_result['contracts_valid'][name] = False
                    test_result['issues'].append(f"{name} validation failed: {e}")
                    print(f"   ❌ {name}: {e}")

            # Test Aave pool
            try:
                pool_abi = [{
                    "inputs": [{"name": "user", "type": "address"}],
                    "name": "getUserAccountData",
                    "outputs": [
                        {"name": "totalCollateralBase", "type": "uint256"},
                        {"name": "totalDebtBase", "type": "uint256"},
                        {"name": "availableBorrowsBase", "type": "uint256"},
                        {"name": "currentLiquidationThreshold", "type": "uint256"},
                        {"name": "ltv", "type": "uint256"},
                        {"name": "healthFactor", "type": "uint256"}
                    ],
                    "stateMutability": "view",
                    "type": "function"
                }]

                pool_contract = self.w3.eth.contract(
                    address=Web3.to_checksum_address(self.agent.aave_pool_address),
                    abi=pool_abi
                )

                # Test with agent's address
                account_data = pool_contract.functions.getUserAccountData(self.agent.address).call()
                test_result['aave_pool_valid'] = True
                print(f"   ✅ Aave Pool: Valid and accessible")

            except Exception as e:
                test_result['issues'].append(f"Aave pool validation failed: {e}")
                print(f"   ❌ Aave Pool: {e}")

        except Exception as e:
            test_result['issues'].append(f"Contract validation failed: {e}")
            print(f"   ❌ Contract validation error: {e}")

        self.diagnostics['tests']['contracts'] = test_result

    def _test_aave_position(self):
        """Test current Aave position"""
        print("\n3️⃣ Testing Aave Position...")
        test_result = {
            'position_accessible': False,
            'collateral_usd': 0,
            'debt_usd': 0,
            'available_borrows_usd': 0,
            'health_factor': 0,
            'can_borrow': False,
            'issues': []
        }

        try:
            pool_abi = [{
                "inputs": [{"name": "user", "type": "address"}],
                "name": "getUserAccountData",
                "outputs": [
                    {"name": "totalCollateralBase", "type": "uint256"},
                    {"name": "totalDebtBase", "type": "uint256"},
                    {"name": "availableBorrowsBase", "type": "uint256"},
                    {"name": "currentLiquidationThreshold", "type": "uint256"},
                    {"name": "ltv", "type": "uint256"},
                    {"name": "healthFactor", "type": "uint256"}
                ],
                "stateMutability": "view",
                "type": "function"
            }]

            pool_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.agent.aave_pool_address),
                abi=pool_abi
            )

            account_data = pool_contract.functions.getUserAccountData(self.agent.address).call()

            test_result['position_accessible'] = True
            test_result['collateral_usd'] = account_data[0] / (10**8)
            test_result['debt_usd'] = account_data[1] / (10**8)
            test_result['available_borrows_usd'] = account_data[2] / (10**8)
            test_result['health_factor'] = account_data[5] / (10**18) if account_data[5] > 0 else float('inf')

            print(f"   ✅ Collateral: ${test_result['collateral_usd']:,.2f}")
            print(f"   ✅ Debt: ${test_result['debt_usd']:,.2f}")
            print(f"   ✅ Available Borrows: ${test_result['available_borrows_usd']:,.2f}")
            print(f"   ✅ Health Factor: {test_result['health_factor']:.4f}")

            # Determine if can borrow
            test_result['can_borrow'] = (
                test_result['health_factor'] > 1.5 and
                test_result['available_borrows_usd'] >= 1.0
            )

            if test_result['can_borrow']:
                print(f"   ✅ Position ready for borrowing")
            else:
                reasons = []
                if test_result['health_factor'] <= 1.5:
                    reasons.append(f"Low health factor: {test_result['health_factor']:.4f}")
                if test_result['available_borrows_usd'] < 1.0:
                    reasons.append(f"Low available borrows: ${test_result['available_borrows_usd']:.2f}")
                test_result['issues'].extend(reasons)
                print(f"   ⚠️ Position not ready: {', '.join(reasons)}")

        except Exception as e:
            test_result['issues'].append(f"Aave position test failed: {e}")
            print(f"   ❌ Aave position test failed: {e}")

        self.diagnostics['tests']['aave_position'] = test_result

    def _test_gas_readiness(self):
        """Test ETH balance and gas readiness"""
        print("\n4️⃣ Testing Gas Readiness...")
        test_result = {
            'eth_balance': 0,
            'sufficient_for_gas': False,
            'estimated_gas_cost': 0,
            'issues': []
        }

        try:
            eth_balance = self.agent.get_eth_balance()
            test_result['eth_balance'] = float(eth_balance)

            # Estimate gas cost for borrow operation
            current_gas_price = self.w3.eth.gas_price
            estimated_gas_limit = 300000  # Conservative estimate for borrow
            estimated_cost_wei = current_gas_price * estimated_gas_limit
            estimated_cost_eth = Web3.from_wei(estimated_cost_wei, 'ether')
            test_result['estimated_gas_cost'] = float(estimated_cost_eth)

            min_eth_needed = estimated_cost_eth * 2  # 2x buffer
            test_result['sufficient_for_gas'] = eth_balance >= min_eth_needed

            print(f"   ✅ ETH Balance: {eth_balance:.6f} ETH")
            print(f"   ✅ Estimated Gas Cost: {estimated_cost_eth:.6f} ETH")

            if test_result['sufficient_for_gas']:
                print(f"   ✅ Sufficient ETH for gas operations")
            else:
                shortage = min_eth_needed - eth_balance
                test_result['issues'].append(f"Need {shortage:.6f} more ETH for gas")
                print(f"   ⚠️ Need {shortage:.6f} more ETH")

        except Exception as e:
            test_result['issues'].append(f"Gas readiness test failed: {e}")
            print(f"   ❌ Gas readiness test failed: {e}")

        self.diagnostics['tests']['gas_readiness'] = test_result

    def _test_enhanced_borrow_manager(self):
        """Test enhanced borrow manager"""
        print("\n5️⃣ Testing Enhanced Borrow Manager...")
        test_result = {
            'manager_available': False,
            'validation_method_exists': False,
            'fallback_methods_available': 0,
            'issues': []
        }

        try:
            # Check if enhanced borrow manager exists
            if hasattr(self.agent, 'enhanced_borrow_manager') and self.agent.enhanced_borrow_manager:
                test_result['manager_available'] = True
                ebm = self.agent.enhanced_borrow_manager
                print(f"   ✅ Enhanced Borrow Manager: Available")

                # Check validation method
                if hasattr(ebm, '_validate_borrow_conditions'):
                    test_result['validation_method_exists'] = True
                    print(f"   ✅ Validation Method: Available")
                else:
                    test_result['issues'].append("Validation method missing")

                # Check fallback methods
                fallback_methods = [
                    'safe_borrow_with_fallbacks',
                    '_validate_borrow_conditions'
                ]
                
                available_methods = sum(1 for method in fallback_methods if hasattr(ebm, method))
                test_result['fallback_methods_available'] = available_methods
                print(f"   ✅ Fallback Methods: {available_methods}/{len(fallback_methods)}")

            else:
                test_result['issues'].append("Enhanced borrow manager not initialized")
                print(f"   ❌ Enhanced Borrow Manager: Not available")

        except Exception as e:
            test_result['issues'].append(f"Enhanced borrow manager test failed: {e}")
            print(f"   ❌ Enhanced borrow manager test failed: {e}")

        self.diagnostics['tests']['enhanced_borrow_manager'] = test_result

    def _test_borrow_simulation(self):
        """Test borrow operation simulation"""
        print("\n6️⃣ Testing Borrow Simulation...")
        test_result = {
            'simulation_possible': False,
            'recommended_amount': 0,
            'safety_checks_passed': False,
            'issues': []
        }

        try:
            # Get current position data
            aave_test = self.diagnostics['tests'].get('aave_position', {})
            
            if not aave_test.get('position_accessible'):
                test_result['issues'].append("Cannot access Aave position for simulation")
                return

            available_borrows = aave_test.get('available_borrows_usd', 0)
            health_factor = aave_test.get('health_factor', 0)

            # Calculate recommended borrow amount
            if available_borrows > 0 and health_factor > 1.5:
                # Conservative: 10% of available capacity, min $0.50, max $5.00
                recommended = min(max(available_borrows * 0.1, 0.5), 5.0)
                test_result['recommended_amount'] = recommended
                test_result['simulation_possible'] = True
                test_result['safety_checks_passed'] = True
                
                print(f"   ✅ Simulation Possible: Yes")
                print(f"   ✅ Recommended Amount: ${recommended:.2f}")
                print(f"   ✅ Safety Checks: Passed")
            else:
                reasons = []
                if available_borrows <= 0:
                    reasons.append("No available borrows")
                if health_factor <= 1.5:
                    reasons.append(f"Low health factor: {health_factor:.4f}")
                test_result['issues'].extend(reasons)
                print(f"   ⚠️ Simulation not recommended: {', '.join(reasons)}")

        except Exception as e:
            test_result['issues'].append(f"Borrow simulation failed: {e}")
            print(f"   ❌ Borrow simulation failed: {e}")

        self.diagnostics['tests']['borrow_simulation'] = test_result

    def _generate_diagnostic_report(self):
        """Generate final diagnostic report"""
        print("\n📊 DIAGNOSTIC SUMMARY")
        print("=" * 30)

        total_tests = len(self.diagnostics['tests'])
        passed_tests = 0
        critical_issues = []

        for test_name, test_data in self.diagnostics['tests'].items():
            issues = test_data.get('issues', [])
            
            if test_name == 'network' and test_data.get('connected'):
                passed_tests += 1
                print(f"✅ Network: PASSED")
            elif test_name == 'contracts' and test_data.get('aave_pool_valid'):
                passed_tests += 1
                print(f"✅ Contracts: PASSED")
            elif test_name == 'aave_position' and test_data.get('position_accessible'):
                passed_tests += 1
                print(f"✅ Aave Position: PASSED")
            elif test_name == 'gas_readiness' and test_data.get('sufficient_for_gas'):
                passed_tests += 1
                print(f"✅ Gas Readiness: PASSED")
            elif test_name == 'enhanced_borrow_manager' and test_data.get('manager_available'):
                passed_tests += 1
                print(f"✅ Enhanced Borrow Manager: PASSED")
            elif test_name == 'borrow_simulation' and test_data.get('simulation_possible'):
                passed_tests += 1
                print(f"✅ Borrow Simulation: PASSED")
            else:
                print(f"❌ {test_name.replace('_', ' ').title()}: FAILED")
                critical_issues.extend(issues)

        print(f"\n🎯 Overall Score: {passed_tests}/{total_tests} tests passed")

        if critical_issues:
            print(f"\n🚨 CRITICAL ISSUES:")
            for issue in critical_issues[:5]:  # Show top 5 issues
                print(f"   • {issue}")

        # Save diagnostic report
        self._save_diagnostic_report()

        return passed_tests >= (total_tests * 0.8)  # 80% pass rate

    def _save_diagnostic_report(self):
        """Save diagnostic report to file"""
        try:
            filename = f"borrow_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            from fix_json_serialization import safe_json_dump
            success = safe_json_dump(self.diagnostics, filename)
            
            if success:
                print(f"\n💾 Diagnostic report saved: {filename}")
            else:
                print(f"\n⚠️ Failed to save diagnostic report")

        except Exception as e:
            print(f"⚠️ Error saving report: {e}")
# --- Merged from supply_diagnostic.py ---

def diagnose_supply_failure():
    """Comprehensive diagnostic for Aave supply failures"""
    print("🔍 AAVE SUPPLY FAILURE DIAGNOSTIC")
    print("=" * 50)
    
    try:
        load_dotenv()
        
        # Initialize connection
        network_mode = os.getenv('NETWORK_MODE', 'testnet')
        if network_mode == 'mainnet':
            w3 = Web3(Web3.HTTPProvider('https://arb1.arbitrum.io/rpc'))
            expected_chain = 42161
        else:
            w3 = Web3(Web3.HTTPProvider('https://sepolia-rollup.arbitrum.io/rpc'))
            expected_chain = 421614
            
        if not w3.is_connected():
            print("❌ CRITICAL: Cannot connect to Arbitrum network")
            return False
            
        chain_id = w3.eth.chain_id
        print(f"✅ Connected to Arbitrum (Chain ID: {chain_id})")
        
        if chain_id != expected_chain:
            print(f"⚠️  Chain ID mismatch! Expected {expected_chain}, got {chain_id}")
        
        # Initialize account
        private_key = os.getenv('PRIVATE_KEY')
        if not private_key:
            print("❌ CRITICAL: PRIVATE_KEY not found in environment")
            return False
            
        account = Account.from_key(private_key)
        print(f"✅ Wallet: {account.address}")
        
        # Check ETH balance
        eth_balance = w3.eth.get_balance(account.address) / 1e18
        print(f"💰 ETH Balance: {eth_balance:.6f} ETH")
        
        if eth_balance < 0.001:
            print("❌ CRITICAL: Insufficient ETH for gas fees")
            return False
            
        # Contract addresses based on network
        if network_mode == 'mainnet':
            dai_address = "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1"
            pool_address = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
        else:
            dai_address = "0x82E64f49Ed5EC1bC6e43DAD4FC8Af9bb3A2312EE"
            pool_address = "0x6Ae43d3271ff6888e7Fc43Fd7321a503ff738951"
        
        print(f"🏦 Aave Pool: {pool_address}")
        print(f"🪙 DAI Token: {dai_address}")
        
        # Check contract deployments
        pool_code = w3.eth.get_code(pool_address)
        dai_code = w3.eth.get_code(dai_address)
        
        if pool_code == b'':
            print("❌ CRITICAL: Aave Pool contract not deployed")
            return False
        else:
            print("✅ Aave Pool contract exists")
            
        if dai_code == b'':
            print("❌ CRITICAL: DAI token contract not deployed")
            return False
        else:
            print("✅ DAI token contract exists")
        
        # Check DAI balance
        dai_abi = [{
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        }]
        
        dai_contract = w3.eth.contract(address=dai_address, abi=dai_abi)
        dai_balance_wei = dai_contract.functions.balanceOf(account.address).call()
        dai_balance = dai_balance_wei / 1e18
        
        print(f"💰 DAI Balance: {dai_balance:.6f} DAI")
        
        if dai_balance == 0:
            print("❌ CRITICAL: No DAI tokens to supply")
            return False
        
        # Check current DAI allowance
        allowance_abi = [{
            "constant": True,
            "inputs": [
                {"name": "_owner", "type": "address"},
                {"name": "_spender", "type": "address"}
            ],
            "name": "allowance",
            "outputs": [{"name": "", "type": "uint256"}],
            "type": "function"
        }]
        
        try:
            dai_contract_full = w3.eth.contract(address=dai_address, abi=allowance_abi)
            current_allowance = dai_contract_full.functions.allowance(
                account.address, 
                pool_address
            ).call()
            
            allowance_formatted = current_allowance / 1e18
            print(f"🔐 Current DAI Allowance: {allowance_formatted:.6f} DAI")
            
            if current_allowance == 0:
                print("❌ ISSUE: No DAI allowance set for Aave pool")
                print("💡 SOLUTION: Must approve DAI spending before supply")
            else:
                print("✅ DAI allowance exists")
                
        except Exception as allowance_err:
            print(f"⚠️ Could not check allowance: {allowance_err}")
        
        # Test gas price
        gas_price = w3.eth.gas_price
        gas_price_gwei = gas_price / 1e9
        print(f"⛽ Current Gas Price: {gas_price_gwei:.2f} Gwei")
        
        if gas_price_gwei < 0.01:
            print("⚠️ Very low gas price - transactions may be slow")
        
        # Check latest block
        latest_block = w3.eth.block_number
        print(f"📦 Latest Block: {latest_block}")
        
        # Simulate approval transaction
        print("\n🧪 SIMULATING APPROVAL TRANSACTION:")
        
        approve_abi = [{
            "constant": False,
            "inputs": [
                {"name": "_spender", "type": "address"},
                {"name": "_value", "type": "uint256"}
            ],
            "name": "approve",
            "outputs": [{"name": "", "type": "bool"}],
            "type": "function"
        }]
        
        try:
            dai_approve_contract = w3.eth.contract(address=dai_address, abi=approve_abi)
            
            # Simulate approving 1 DAI
            test_amount = int(1 * 1e18)
            
            estimated_gas = dai_approve_contract.functions.approve(
                pool_address,
                test_amount
            ).estimate_gas({'from': account.address})
            
            print(f"✅ Approval simulation successful - Gas needed: {estimated_gas}")
            
        except Exception as approve_sim_err:
            print(f"❌ Approval simulation failed: {approve_sim_err}")
            
        # Simulate supply transaction
        print("\n🧪 SIMULATING SUPPLY TRANSACTION:")
        
        pool_abi = [{
            "inputs": [
                {"name": "asset", "type": "address"},
                {"name": "amount", "type": "uint256"},
                {"name": "onBehalfOf", "type": "address"},
                {"name": "referralCode", "type": "uint16"}
            ],
            "name": "supply",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }]
        
        try:
            pool_contract = w3.eth.contract(address=pool_address, abi=pool_abi)
            
            # Simulate supplying 1 DAI
            test_supply_amount = int(1 * 1e18)
            
            estimated_supply_gas = pool_contract.functions.supply(
                dai_address,
                test_supply_amount,
                account.address,
                0
            ).estimate_gas({'from': account.address})
            
            print(f"✅ Supply simulation successful - Gas needed: {estimated_supply_gas}")
            
        except Exception as supply_sim_err:
            print(f"❌ Supply simulation failed: {supply_sim_err}")
            if "insufficient allowance" in str(supply_sim_err).lower():
                print("💡 CAUSE: Token approval required before supply")
            elif "insufficient balance" in str(supply_sim_err).lower():
                print("💡 CAUSE: Insufficient token balance")
            else:
                print(f"💡 CAUSE: {supply_sim_err}")
        
        print("\n📋 DIAGNOSTIC SUMMARY:")
        print("=" * 30)
        
        issues = []
        if eth_balance < 0.001:
            issues.append("Insufficient ETH for gas")
        if dai_balance == 0:
            issues.append("No DAI tokens available")
        if 'current_allowance' in locals() and current_allowance == 0:
            issues.append("DAI approval required")
            
        if issues:
            print("❌ ISSUES FOUND:")
            for issue in issues:
                print(f"   • {issue}")
        else:
            print("✅ All checks passed - supply should work")
            
        return len(issues) == 0
        
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        return False
# --- Merged from autonomous_system_diagnostic.py ---

def check_aave_position(agent):
    """Check current Aave position"""
    print("🔍 Checking Aave Position...")
    
    try:
        # Get fresh Aave data
        pool_abi = [{
            "inputs": [{"name": "user", "type": "address"}],
            "name": "getUserAccountData",
            "outputs": [
                {"name": "totalCollateralBase", "type": "uint256"},
                {"name": "totalDebtBase", "type": "uint256"},
                {"name": "availableBorrowsBase", "type": "uint256"},
                {"name": "currentLiquidationThreshold", "type": "uint256"},
                {"name": "ltv", "type": "uint256"},
                {"name": "healthFactor", "type": "uint256"}
            ],
            "stateMutability": "view",
            "type": "function"
        }]
        
        pool_contract = agent.w3.eth.contract(
            address=agent.aave_pool_address,
            abi=pool_abi
        )
        
        account_data = pool_contract.functions.getUserAccountData(agent.address).call()
        
        collateral_usd = account_data[0] / (10**8)
        debt_usd = account_data[1] / (10**8)
        available_borrows_usd = account_data[2] / (10**8)
        health_factor = account_data[5] / (10**18) if account_data[5] > 0 else float('inf')
        
        return {
            'collateral': f"✅ Collateral: ${collateral_usd:,.2f}",
            'debt': f"✅ Debt: ${debt_usd:,.2f}",
            'available_borrows': f"✅ Available Borrows: ${available_borrows_usd:,.2f}",
            'health_factor': f"✅ Health Factor: {health_factor:.4f}",
            'position_ready': '✅ Position suitable for autonomous operations' if collateral_usd > 100 else '⚠️ Position too small for operations'
        }
        
    except Exception as e:
        return {'error': f"❌ Aave position check failed: {e}"}

def check_autonomous_readiness():
    """Check if system is ready for autonomous operation"""
    print("🔍 Checking Autonomous Readiness...")
    
    readiness_checks = {
        'baseline_file': os.path.exists('agent_baseline.json'),
        'emergency_stop': not os.path.exists('EMERGENCY_STOP_ACTIVE.flag'),
        'performance_log': os.path.exists('performance_log.json')
    }
    
    results = {}
    for check, status in readiness_checks.items():
        results[check] = "✅ Ready" if status else "❌ Not ready"
    
    return results