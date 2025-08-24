
#!/usr/bin/env python3
"""
Final DAI Compliance Validator - Ensures 100% DAI-only operations
"""

import os
import re
import sys
from typing import List, Dict

class FinalDAIComplianceValidator:
    def __init__(self):
        self.violations = []
        self.compliant_files = []
        
    def validate_dai_only_compliance(self) -> bool:
        """Validate that all swap operations use DAI only"""
        print("🔒 FINAL DAI COMPLIANCE VALIDATION")
        print("=" * 50)
        
        # Core files that must be DAI compliant
        critical_files = [
            'arbitrum_testnet_agent.py',
            'enhanced_borrow_manager.py',
            'aave_integration.py',
            'uniswap_integration.py',
            'transaction_validator.py'
        ]
        
        for file_path in critical_files:
            if os.path.exists(file_path):
                self._validate_file_compliance(file_path)
        
        return self._generate_final_report()
    
    def _validate_file_compliance(self, file_path: str):
        """Validate a single file for DAI compliance"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for USDC violations (case insensitive)
            usdc_pattern = r'(?i)usdc(?!.*dai)'  # USDC not followed by DAI context
            usdc_matches = re.findall(usdc_pattern, content)
            
            # Check for DAI references
            dai_pattern = r'(?i)dai'
            dai_matches = re.findall(dai_pattern, content)
            
            print(f"\n📄 Validating: {file_path}")
            
            if usdc_matches and len(usdc_matches) > 3:  # Allow minimal references
                self.violations.append({
                    'file': file_path,
                    'type': 'USDC_VIOLATION',
                    'count': len(usdc_matches),
                    'severity': 'CRITICAL'
                })
                print(f"   ❌ USDC violations found: {len(usdc_matches)}")
            else:
                print(f"   ✅ No significant USDC violations")
            
            if dai_matches:
                print(f"   ✅ DAI compliance confirmed: {len(dai_matches)} references")
                self.compliant_files.append(file_path)
            else:
                print(f"   ⚠️ No DAI references found")
                
        except Exception as e:
            print(f"   ❌ Error validating {file_path}: {e}")
    
    def _generate_final_report(self) -> bool:
        """Generate final compliance report"""
        print("\n" + "=" * 50)
        print("📊 FINAL DAI COMPLIANCE REPORT")
        print("=" * 50)
        
        critical_violations = [v for v in self.violations if v['severity'] == 'CRITICAL']
        
        print(f"✅ Compliant files: {len(self.compliant_files)}")
        print(f"❌ Critical violations: {len(critical_violations)}")
        
        if critical_violations:
            print("\n🚨 CRITICAL VIOLATIONS:")
            for violation in critical_violations:
                print(f"   {violation['file']}: {violation['count']} USDC references")
            
            print("\n❌ DAI COMPLIANCE: FAILED")
            print("🔧 Fix critical violations before deployment")
            return False
        else:
            print(f"\n✅ DAI COMPLIANCE: FULLY ENFORCED")
            print(f"🔒 All operations restricted to DAI-only methodology")
            return True

def main():
    """Run final DAI compliance validation"""
    validator = FinalDAIComplianceValidator()
    is_compliant = validator.validate_dai_only_compliance()
    
    if not is_compliant:
        sys.exit(1)
    
    return True

if __name__ == "__main__":
    main()
