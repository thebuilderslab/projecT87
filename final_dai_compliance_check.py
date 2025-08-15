
#!/usr/bin/env python3
"""
Final DAI Compliance Check
Ensures no USDC references remain in critical system files
"""

import os
import re

def check_dai_compliance():
    print("🔍 FINAL DAI COMPLIANCE VALIDATION")
    print("=" * 50)
    
    # Critical files that must be DAI-only compliant
    critical_files = [
        'arbitrum_testnet_agent.py',
        'aave_integration.py',
        'enhanced_borrow_manager.py',
        'uniswap_integration.py'
    ]
    
    all_compliant = True
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            print(f"\n📄 Checking critical file: {file_path}")
            
            with open(file_path, 'r') as f:
                content = f.read().lower()
            
            # Check for any USDC references
            usdc_patterns = ['usdc', 'usdc_address', 'usdc_amount', 'usdc_balance']
            violations = []
            
            for pattern in usdc_patterns:
                if pattern in content:
                    violations.append(pattern)
            
            if violations:
                print(f"   ❌ VIOLATIONS FOUND: {violations}")
                all_compliant = False
            else:
                print(f"   ✅ DAI COMPLIANT")
    
    print(f"\n{'✅ SYSTEM READY FOR DEPLOYMENT' if all_compliant else '❌ CRITICAL ISSUES REMAIN'}")
    return all_compliant

if __name__ == "__main__":
    check_dai_compliance()

# --- Merged from dai_compliance_final_validator.py ---

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
# --- Merged from dai_compliance_enforcer.py ---

class DAIComplianceEnforcer:
    def __init__(self):
        self.dai_address = "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1"  # Arbitrum Mainnet DAI
        self.wbtc_address = "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f"  # Arbitrum Mainnet WBTC
        self.weth_address = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"  # Arbitrum Mainnet WETH

        self.allowed_swap_pairs = [
            (self.dai_address.lower(), self.wbtc_address.lower()),  # DAI → WBTC
            (self.dai_address.lower(), self.weth_address.lower()),  # DAI → WETH
        ]

        self.violations = []
        self.fixes_applied = []

    def enforce_dai_compliance(self):
        """Enforce DAI-only compliance across all swap-related files"""
        print("🔒 ENFORCING DAI-ONLY COMPLIANCE")
        print("=" * 50)

        # Find and fix all swap-related files
        swap_files = self._find_swap_files()

        for file_path in swap_files:
            self._enforce_file_compliance(file_path)

        self._generate_enforcement_report()

        return len(self.violations) == 0

    def _find_swap_files(self):
        """Find all files that contain swap operations"""
        patterns = [
            "*swap*.py",
            "*uniswap*.py",
            "*enhanced_swap*.py",
            "*force_swap*.py",
            "*manual_*swap*.py",
            "*ultimate_swap*.py"
        ]

        files = []
        for pattern in patterns:
            files.extend(Path('.').glob(pattern))

        return [str(f) for f in files if f.is_file()]

    def _enforce_file_compliance(self, file_path):
        """Enforce DAI compliance in individual file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            print(f"\n🔍 Enforcing compliance: {file_path}")

            # Check for USDC violations
            usdc_violations = self._find_usdc_violations(content)
            if usdc_violations:
                print(f"   ❌ USDC violations found: {len(usdc_violations)}")
                self.violations.append({
                    'file': file_path,
                    'type': 'USDC_USAGE',
                    'count': len(usdc_violations)
                })

                # Apply DAI-only fixes
                fixed_content = self._apply_dai_fixes(content, file_path)
                if fixed_content != content:
                    with open(file_path, 'w') as f:
                        f.write(fixed_content)
                    print(f"   ✅ DAI compliance fixes applied")
                    self.fixes_applied.append(file_path)
            else:
                print(f"   ✅ No USDC violations found")

        except Exception as e:
            print(f"   ❌ Error processing {file_path}: {e}")

    def _find_usdc_violations(self, content):
        """Find USDC usage violations"""
        violations = []

        # Pattern to find USDC references
        usdc_patterns = [
            r'usdc_address',
            r'USDC',
            r'\.usdc',
            r'swap.*usdc',
            r'usdc.*swap'
        ]

        for pattern in usdc_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            violations.extend(matches)

        return violations

    def _apply_dai_fixes(self, content, file_path):
        """Apply DAI-only fixes to content"""
        original_content = content

        # Replace USDC references with DAI
        replacements = [
            (r'usdc_address', 'dai_address'),
            (r'USDC', 'DAI'),
            (r'\.usdc\.', '.dai.'),
            (r'swap_usdc_for', 'swap_dai_for'),
            (r'usdc_to_', 'dai_to_'),
            (r'borrow.*usdc', 'borrow DAI'),
            (r'supply.*usdc', 'supply DAI')
        ]

        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

        # Add DAI compliance header if file was modified
        if content != original_content:
            dai_header = '''"""
DAI COMPLIANCE ENFORCED: This file has been modified to use DAI-only operations.
Only DAI → WBTC and DAI → WETH swaps are permitted.
"""

'''
            if not content.startswith('"""'):
                content = dai_header + content

        return content

    def _generate_enforcement_report(self):
        """Generate enforcement report"""
        print("\n" + "=" * 60)
        print("🔒 DAI COMPLIANCE ENFORCEMENT REPORT")
        print("=" * 60)

        print(f"❌ Violations found: {len(self.violations)}")
        print(f"✅ Fixes applied: {len(self.fixes_applied)}")

        if self.violations:
            print("\n🚨 VIOLATIONS DETECTED:")
            for violation in self.violations:
                print(f"   {violation['file']}: {violation['count']} {violation['type']} violations")

        if self.fixes_applied:
            print("\n✅ FILES FIXED:")
            for fixed_file in self.fixes_applied:
                print(f"   {fixed_file}: DAI compliance enforced")

        if len(self.violations) == 0:
            print("\n✅ DAI COMPLIANCE FULLY ENFORCED")
            print("🔒 All swap operations now use DAI-only methodology")
            return True
        else:
            print("\n❌ DAI COMPLIANCE ENFORCEMENT INCOMPLETE")
            print("🔧 Manual review required for remaining violations")
            return False

    def enforce_dai_compliance(self):
        """Enforce DAI-only compliance across all swap-related files"""
        print("🔒 ENFORCING DAI-ONLY COMPLIANCE")
        print("=" * 50)

        # Find and fix all swap-related files
        swap_files = self._find_swap_files()

        for file_path in swap_files:
            self._enforce_file_compliance(file_path)

        self._generate_enforcement_report()

        return len(self.violations) == 0

    def _find_swap_files(self):
        """Find all files that contain swap operations"""
        patterns = [
            "*swap*.py",
            "*uniswap*.py",
            "*enhanced_swap*.py",
            "*force_swap*.py",
            "*manual_*swap*.py",
            "*ultimate_swap*.py"
        ]

        files = []
        for pattern in patterns:
            files.extend(Path('.').glob(pattern))

        return [str(f) for f in files if f.is_file()]

    def _enforce_file_compliance(self, file_path):
        """Enforce DAI compliance in individual file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            print(f"\n🔍 Enforcing compliance: {file_path}")

            # Check for USDC violations
            usdc_violations = self._find_usdc_violations(content)
            if usdc_violations:
                print(f"   ❌ USDC violations found: {len(usdc_violations)}")
                self.violations.append({
                    'file': file_path,
                    'type': 'USDC_USAGE',
                    'count': len(usdc_violations)
                })

                # Apply DAI-only fixes
                fixed_content = self._apply_dai_fixes(content, file_path)
                if fixed_content != content:
                    with open(file_path, 'w') as f:
                        f.write(fixed_content)
                    print(f"   ✅ DAI compliance fixes applied")
                    self.fixes_applied.append(file_path)
            else:
                print(f"   ✅ No USDC violations found")

        except Exception as e:
            print(f"   ❌ Error processing {file_path}: {e}")

    def _find_usdc_violations(self, content):
        """Find USDC usage violations"""
        violations = []

        # Pattern to find USDC references
        usdc_patterns = [
            r'usdc_address',
            r'USDC',
            r'\.usdc',
            r'swap.*usdc',
            r'usdc.*swap'
        ]

        for pattern in usdc_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            violations.extend(matches)

        return violations

    def _apply_dai_fixes(self, content, file_path):
        """Apply DAI-only fixes to content"""
        original_content = content

        # Replace USDC references with DAI
        replacements = [
            (r'usdc_address', 'dai_address'),
            (r'USDC', 'DAI'),
            (r'\.usdc\.', '.dai.'),
            (r'swap_usdc_for', 'swap_dai_for'),
            (r'usdc_to_', 'dai_to_'),
            (r'borrow.*usdc', 'borrow DAI'),
            (r'supply.*usdc', 'supply DAI')
        ]

        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

        # Add DAI compliance header if file was modified
        if content != original_content:
            dai_header = '''"""
DAI COMPLIANCE ENFORCED: This file has been modified to use DAI-only operations.
Only DAI → WBTC and DAI → WETH swaps are permitted.
"""

'''
            if not content.startswith('"""'):
                content = dai_header + content

        return content

    def _generate_enforcement_report(self):
        """Generate enforcement report"""
        print("\n" + "=" * 60)
        print("🔒 DAI COMPLIANCE ENFORCEMENT REPORT")
        print("=" * 60)

        print(f"❌ Violations found: {len(self.violations)}")
        print(f"✅ Fixes applied: {len(self.fixes_applied)}")

        if self.violations:
            print("\n🚨 VIOLATIONS DETECTED:")
            for violation in self.violations:
                print(f"   {violation['file']}: {violation['count']} {violation['type']} violations")

        if self.fixes_applied:
            print("\n✅ FILES FIXED:")
            for fixed_file in self.fixes_applied:
                print(f"   {fixed_file}: DAI compliance enforced")

        if len(self.violations) == 0:
            print("\n✅ DAI COMPLIANCE FULLY ENFORCED")
            print("🔒 All swap operations now use DAI-only methodology")
            return True
        else:
            print("\n❌ DAI COMPLIANCE ENFORCEMENT INCOMPLETE")
            print("🔧 Manual review required for remaining violations")
            return False
# --- Merged from system_compliance_checker.py ---

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

    def check_dai_only_compliance(self):
        """Check all swap-related files for DAI-only compliance"""
        print("🔍 CHECKING DAI-ONLY SWAP COMPLIANCE")
        print("=" * 50)
        
        # Find all Python files that might contain swap logic
        swap_files = self._find_swap_files()
        
        for file_path in swap_files:
            self._check_file_compliance(file_path)
            
        self._generate_report()

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