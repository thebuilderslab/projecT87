
#!/usr/bin/env python3
"""
COMPREHENSIVE DIAGNOSTIC SCRIPT
Provides detailed system analysis for debugging and troubleshooting
"""

import os
import sys
import json
import time
import traceback
import subprocess
from datetime import datetime

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

if __name__ == "__main__":
    main()
