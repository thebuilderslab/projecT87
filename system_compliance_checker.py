
#!/usr/bin/env python3
"""
System Compliance Checker - Verify all swap.py files use DAI-only operations
"""

import os
import re
import sys
from pathlib import Path

class SystemComplianceChecker:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.compliant_files = []
        
    def check_dai_only_compliance(self):
        """Check all swap-related files for DAI-only compliance"""
        print("🔍 CHECKING DAI-ONLY SWAP COMPLIANCE")
        print("=" * 50)
        
        # Find all Python files that might contain swap logic
        swap_files = self._find_swap_files()
        
        for file_path in swap_files:
            self._check_file_compliance(file_path)
            
        self._generate_report()
        
    def _find_swap_files(self):
        """Find all files that might contain swap operations"""
        patterns = [
            "*swap*.py",
            "*uniswap*.py", 
            "*arbitrum*.py",
            "*borrow*.py",
            "*integration*.py"
        ]
        
        files = []
        for pattern in patterns:
            files.extend(Path('.').glob(pattern))
            files.extend(Path('.').glob(f"**/{pattern}"))
            
        return [str(f) for f in files if f.is_file()]
    
    def _check_file_compliance(self, file_path):
        """Check individual file for compliance"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            print(f"\n📄 Checking: {file_path}")
            
            # Check for USDC references (forbidden)
            usdc_patterns = [
                r'usdc_address',
                r'USDC',
                r'\.usdc\.',
                r'swap.*usdc',
                r'usdc.*swap'
            ]
            
            usdc_violations = []
            for pattern in usdc_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    usdc_violations.extend(matches)
            
            # Check for DAI references (required)
            dai_patterns = [
                r'dai_address',
                r'DAI',
                r'dai_to_wbtc',
                r'dai_to_weth'
            ]
            
            dai_compliance = []
            for pattern in dai_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    dai_compliance.extend(matches)
            
            # Evaluate compliance
            if usdc_violations:
                self.issues.append({
                    'file': file_path,
                    'type': 'USDC_VIOLATION',
                    'details': f"Found USDC references: {usdc_violations[:3]}"
                })
                print(f"   ❌ USDC violations found: {len(usdc_violations)}")
            
            if dai_compliance:
                self.compliant_files.append({
                    'file': file_path,
                    'dai_references': len(dai_compliance)
                })
                print(f"   ✅ DAI compliance confirmed: {len(dai_compliance)} references")
            else:
                self.warnings.append({
                    'file': file_path,
                    'type': 'NO_DAI_REFERENCES',
                    'details': 'No DAI references found - may not be swap-related'
                })
                print(f"   ⚠️ No DAI references found")
                
        except Exception as e:
            self.issues.append({
                'file': file_path,
                'type': 'FILE_ERROR',
                'details': f"Could not read file: {e}"
            })
            print(f"   ❌ Error reading file: {e}")
    
    def _generate_report(self):
        """Generate final compliance report"""
        print("\n" + "=" * 60)
        print("📊 SYSTEM COMPLIANCE REPORT")
        print("=" * 60)
        
        print(f"✅ Compliant files: {len(self.compliant_files)}")
        print(f"⚠️ Warnings: {len(self.warnings)}")
        print(f"❌ Critical issues: {len(self.issues)}")
        
        if self.issues:
            print("\n🚨 CRITICAL ISSUES:")
            for issue in self.issues:
                print(f"   {issue['file']}: {issue['details']}")
        
        if self.warnings:
            print("\n⚠️ WARNINGS:")
            for warning in self.warnings:
                print(f"   {warning['file']}: {warning['details']}")
        
        if self.compliant_files:
            print("\n✅ COMPLIANT FILES:")
            for compliant in self.compliant_files:
                print(f"   {compliant['file']}: {compliant['dai_references']} DAI references")
        
        # Overall assessment
        if self.issues:
            print("\n❌ SYSTEM NOT COMPLIANT - Fix critical issues before deployment")
            return False
        else:
            print("\n✅ SYSTEM COMPLIANT - All swap files follow DAI-only policy")
            return True

def main():
    """Run compliance check"""
    checker = SystemComplianceChecker()
    is_compliant = checker.check_dai_only_compliance()
    
    if not is_compliant:
        sys.exit(1)
    
    return True

if __name__ == "__main__":
    main()
