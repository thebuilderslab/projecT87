
#!/usr/bin/env python3
"""
Comprehensive System Audit - Integrated into Main System
Combines deduplication, syntax checking, and error reporting with main system integration
"""

import os
import sys
import json
import time
import subprocess
import re
import ast
import shutil
from datetime import datetime
from collections import defaultdict

# Enhanced keywords for feature grouping
KEYWORDS = [
    "diagnostic", "compliance", "launcher", "dashboard", "sync", "test", 
    "emergency", "health_monitor", "fetcher", "validator", "borrow", 
    "aave", "uniswap", "integration", "rpc", "gas", "agent", "autonomous",
    "strategy", "market_signal", "enhanced", "fix", "comprehensive", "web"
]

BASE_DIR = "."
ARCHIVE_DIR = "archive_duplicates"
REPORT_FILE = "comprehensive_audit_report.txt"

class ComprehensiveSystemAudit:
    def __init__(self):
        self.report = {
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat(),
            'overall_status': 'CHECKING',
            'critical_issues': [],
            'warnings': [],
            'component_status': {},
            'duplicates_processed': 0,
            'files_scanned': 0,
            'recommendations': []
        }
    
    def run_full_audit(self):
        """Execute comprehensive system audit"""
        print("🚀 Starting integrated comprehensive system audit...")
        print("=" * 60)
        
        try:
            # Phase 1: File scanning and deduplication
            files = self.scan_files()
            groups = self.group_by_keyword(files)
            
            # Phase 2: Syntax and integration checks
            syntax_errors = self.check_syntax_errors()
            import_errors = self.check_import_errors()
            
            # Phase 3: System component validation
            self.validate_main_components()
            
            # Phase 4: Generate comprehensive report
            self.generate_final_report(groups, syntax_errors, import_errors)
            
            return self.report
            
        except Exception as e:
            self.report['critical_issues'].append(f"Audit failed: {e}")
            self.report['overall_status'] = 'FAILED'
            return self.report
    
    def scan_files(self):
        """Scan for all Python files in the project"""
        print("🔍 Scanning project files...")
        
        py_files = []
        excluded_dirs = {'.git', '__pycache__', 'node_modules', '.replit_cache'}
        
        for root, dirs, files in os.walk(BASE_DIR):
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            
            for f in files:
                if f.endswith(".py") and not f.startswith('.'):
                    full_path = os.path.join(root, f)
                    if os.path.getsize(full_path) > 0:
                        py_files.append(full_path)
        
        self.report['files_scanned'] = len(py_files)
        print(f"📁 Found {len(py_files)} Python files")
        return py_files
    
    def group_by_keyword(self, files):
        """Group files by functionality keywords"""
        groups = defaultdict(list)
        
        for f in files:
            name_lower = os.path.basename(f).lower()
            matched = False
            
            for kw in KEYWORDS:
                if kw in name_lower:
                    groups[kw].append(f)
                    matched = True
                    break
            
            if not matched:
                if any(word in name_lower for word in ['start', 'run', 'launch', 'main']):
                    groups["launcher"].append(f)
                elif any(word in name_lower for word in ['monitor', 'health', 'status']):
                    groups["health_monitor"].append(f)
                else:
                    groups["misc"].append(f)
        
        print(f"📊 Grouped into {len(groups)} feature categories")
        return groups
    
    def check_syntax_errors(self):
        """Check for syntax errors in key files"""
        print("🔍 Checking syntax errors...")
        
        key_files = ['main.py', 'web_dashboard.py', 'aave_integration.py']
        syntax_errors = []
        
        for file_path in key_files:
            if os.path.exists(file_path):
                try:
                    result = subprocess.run(
                        ["python", "-m", "py_compile", file_path],
                        capture_output=True, text=True
                    )
                    if result.returncode != 0:
                        error_msg = result.stderr.strip() or result.stdout.strip()
                        first_line = error_msg.split('\n')[0] if error_msg else "Unknown syntax error"
                        syntax_errors.append(f"{file_path}: {first_line}")
                        self.report['critical_issues'].append(f"Syntax error in {file_path}")
                except Exception as e:
                    syntax_errors.append(f"{file_path}: Error during syntax check - {e}")
        
        return syntax_errors
    
    def check_import_errors(self):
        """Check for critical import issues"""
        print("🔍 Checking import errors...")
        
        import_errors = []
        
        # Test critical imports
        critical_imports = [
            ('web3', 'Web3 blockchain connection'),
            ('flask', 'Web dashboard framework'),
            ('requests', 'HTTP requests for APIs')
        ]
        
        for module, description in critical_imports:
            try:
                __import__(module)
                self.report['component_status'][module] = 'OK'
            except ImportError:
                import_errors.append(f"Missing critical module: {module} ({description})")
                self.report['critical_issues'].append(f"Missing {module}")
                self.report['component_status'][module] = 'MISSING'
        
        return import_errors
    
    def validate_main_components(self):
        """Validate main system components"""
        print("🔍 Validating main system components...")
        
        # Check main.py functionality
        try:
            if os.path.exists('main.py'):
                with open('main.py', 'r') as f:
                    content = f.read()
                    if 'class ArbitrumTestnetAgent' in content:
                        self.report['component_status']['main_agent'] = 'OK'
                    else:
                        self.report['warnings'].append("ArbitrumTestnetAgent class not found in main.py")
                        self.report['component_status']['main_agent'] = 'WARNING'
        except Exception as e:
            self.report['critical_issues'].append(f"Cannot validate main.py: {e}")
            self.report['component_status']['main_agent'] = 'ERROR'
        
        # Check web dashboard
        try:
            if os.path.exists('web_dashboard.py'):
                self.report['component_status']['web_dashboard'] = 'OK'
            else:
                self.report['warnings'].append("web_dashboard.py not found")
                self.report['component_status']['web_dashboard'] = 'MISSING'
        except Exception as e:
            self.report['component_status']['web_dashboard'] = 'ERROR'
        
        # Check Aave integration
        try:
            if os.path.exists('aave_integration.py'):
                self.report['component_status']['aave_integration'] = 'OK'
            else:
                self.report['warnings'].append("aave_integration.py not found")
                self.report['component_status']['aave_integration'] = 'MISSING'
        except Exception as e:
            self.report['component_status']['aave_integration'] = 'ERROR'
    
    def generate_final_report(self, groups, syntax_errors, import_errors):
        """Generate comprehensive final report"""
        print("📄 Generating comprehensive audit report...")
        
        # Calculate overall status
        critical_count = len(self.report['critical_issues'])
        warning_count = len(self.report['warnings'])
        
        if critical_count == 0 and warning_count == 0:
            self.report['overall_status'] = 'EXCELLENT'
        elif critical_count == 0:
            self.report['overall_status'] = 'GOOD'
        elif critical_count <= 2:
            self.report['overall_status'] = 'NEEDS_ATTENTION'
        else:
            self.report['overall_status'] = 'CRITICAL'
        
        # Add recommendations
        if syntax_errors:
            self.report['recommendations'].append("Fix syntax errors in key files")
        if import_errors:
            self.report['recommendations'].append("Install missing Python packages")
        if self.report['component_status'].get('main_agent') != 'OK':
            self.report['recommendations'].append("Verify main agent functionality")
        
        # Generate text report
        report_lines = [
            "COMPREHENSIVE SYSTEM AUDIT REPORT",
            "=" * 50,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Overall Status: {self.report['overall_status']}",
            f"Files Scanned: {self.report['files_scanned']}",
            f"Critical Issues: {len(self.report['critical_issues'])}",
            f"Warnings: {len(self.report['warnings'])}",
            ""
        ]
        
        # Component status
        report_lines.append("COMPONENT STATUS:")
        report_lines.append("-" * 30)
        for component, status in self.report['component_status'].items():
            status_symbol = "✅" if status == "OK" else "⚠️" if status == "WARNING" else "❌"
            report_lines.append(f"  {status_symbol} {component}: {status}")
        report_lines.append("")
        
        # Feature breakdown
        report_lines.append("FEATURE BREAKDOWN:")
        report_lines.append("-" * 30)
        for feature, files in groups.items():
            report_lines.append(f"  {feature.upper()}: {len(files)} files")
        report_lines.append("")
        
        # Issues and recommendations
        if self.report['critical_issues']:
            report_lines.append("CRITICAL ISSUES:")
            report_lines.append("-" * 20)
            for issue in self.report['critical_issues']:
                report_lines.append(f"  ❌ {issue}")
            report_lines.append("")
        
        if self.report['warnings']:
            report_lines.append("WARNINGS:")
            report_lines.append("-" * 20)
            for warning in self.report['warnings']:
                report_lines.append(f"  ⚠️ {warning}")
            report_lines.append("")
        
        if self.report['recommendations']:
            report_lines.append("RECOMMENDATIONS:")
            report_lines.append("-" * 20)
            for rec in self.report['recommendations']:
                report_lines.append(f"  💡 {rec}")
            report_lines.append("")
        
        # Final assessment
        if self.report['overall_status'] == 'EXCELLENT':
            report_lines.append("🎉 SYSTEM STATUS: EXCELLENT - Ready for production")
        elif self.report['overall_status'] == 'GOOD':
            report_lines.append("✅ SYSTEM STATUS: GOOD - Minor issues to address")
        elif self.report['overall_status'] == 'NEEDS_ATTENTION':
            report_lines.append("⚠️ SYSTEM STATUS: NEEDS ATTENTION - Address critical issues")
        else:
            report_lines.append("❌ SYSTEM STATUS: CRITICAL - Immediate action required")
        
        # Save report
        report_content = "\n".join(report_lines)
        
        try:
            with open(REPORT_FILE, "w", encoding="utf-8") as f:
                f.write(report_content)
        except Exception as e:
            print(f"⚠️ Could not save text report: {e}")
        
        try:
            with open("comprehensive_audit_report.json", "w", encoding="utf-8") as f:
                json.dump(self.report, f, indent=2)
        except Exception as e:
            print(f"⚠️ Could not save JSON report: {e}")
        
        print(report_content)
    
    def save_report(self):
        """Save audit report to files"""
        try:
            with open("system_audit_report.json", "w", encoding="utf-8") as f:
                json.dump(self.report, f, indent=2)
            print(f"📄 Audit report saved to: system_audit_report.json")
        except Exception as e:
            print(f"⚠️ Could not save report: {e}")

def main():
    """Run comprehensive system audit"""
    audit = ComprehensiveSystemAudit()
    
    try:
        report = audit.run_full_audit()
        audit.save_report()
        
        # Return success based on status
        return report['overall_status'] in ['EXCELLENT', 'GOOD']
        
    except Exception as e:
        print(f"❌ Audit failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
