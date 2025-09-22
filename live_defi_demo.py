#!/usr/bin/env python3
"""
Live DeFi Monitoring Demonstration
Demonstrates the Sequential File Selection and Error Handling system with real operations.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import our systems
from defi_automation_executor import DeFiAutomationExecutor

def main():
    """
    Execute live DeFi monitoring demonstration using the file selection system
    """
    print("🚀 LIVE DEFI MONITORING DEMONSTRATION")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Purpose: Demonstrate Sequential File Selection and Error Handling")
    print()
    
    try:
        # Initialize the DeFi automation executor
        print("📊 Initializing DeFi Automation Executor...")
        executor = DeFiAutomationExecutor()
        print("✅ Executor initialized successfully")
        print()
        
        # Execute the comprehensive DeFi sequence
        print("🎯 Executing Comprehensive DeFi Monitoring Sequence...")
        print("   This will demonstrate:")
        print("   1. Sequential file selection using 5-approach framework")
        print("   2. Systematic execution (balance → gas → health factor → validation)")
        print("   3. Comprehensive error detection and handling")
        print("   4. Structured audit trail generation")
        print()
        
        # Optional manual overrides for demonstration
        manual_overrides = {
            'monitoring': 'aave_health_monitor.py',  # Force specific monitoring file
            # Let other categories use automatic selection
        }
        
        print("🔧 Manual overrides for demonstration:")
        print(f"   Monitoring file: {manual_overrides.get('monitoring', 'Auto-select')}")
        print("   Other categories: Auto-select using 5-approach framework")
        print()
        
        # Execute the complete sequence
        result = executor.execute_comprehensive_defi_sequence(manual_overrides)
        
        print("✅ Comprehensive sequence completed!")
        print()
        
        # Display summary results
        print("📊 EXECUTION SUMMARY")
        print("-" * 40)
        
        metadata = result.get('execution_metadata', {})
        print(f"Execution ID: {metadata.get('execution_id', 'Unknown')}")
        print(f"Total Time: {metadata.get('total_execution_time_seconds', 0):.2f} seconds")
        print(f"Completed Steps: {len(metadata.get('completed_steps', []))}")
        print(f"Failed Steps: {len(metadata.get('failed_steps', []))}")
        print()
        
        # Generate and display audit reports
        print("📄 GENERATING AUDIT REPORTS")
        print("-" * 40)
        
        # Generate Markdown report
        markdown_report = executor.generate_markdown_audit_report(result)
        print("✅ Markdown audit report generated")
        
        # Generate JSON report  
        json_report = executor.generate_json_audit_report(result)
        print("✅ JSON audit report generated")
        
        # Save reports to files
        saved_files = executor.save_audit_reports(result)
        if saved_files:
            print("💾 Audit reports saved:")
            for report_type, file_path in saved_files.items():
                print(f"   {report_type.upper()}: {file_path}")
        print()
        
        # Display the structured audit table (exact format requested)
        print("📋 STRUCTURED AUDIT TABLE (REQUESTED FORMAT)")
        print("=" * 80)
        
        # Extract the main audit table from markdown report
        lines = markdown_report.split('\n')
        in_table = False
        for line in lines:
            if '| Step        | File Name           | Action      |' in line:
                in_table = True
            if in_table:
                if line.startswith('|') or line.startswith('-'):
                    print(line)
                elif line.strip() == '' and in_table:
                    break
        print()
        
        # Display key insights
        print("🔍 KEY INSIGHTS FROM DEMONSTRATION")
        print("-" * 50)
        
        file_selection_result = result.get('file_selection_result', {})
        if file_selection_result:
            final_selections = file_selection_result.get('final_selections', {})
            print("Selected Files by Category:")
            for category, filename in final_selections.items():
                if filename:
                    print(f"   {category}: {filename}")
                else:
                    print(f"   {category}: No suitable file found")
            print()
        
        execution_results = result.get('execution_results', [])
        if execution_results:
            successful_steps = [r for r in execution_results if '✅' in r.get('used_skipped', '')]
            failed_steps = [r for r in execution_results if '❌' in r.get('used_skipped', '')]
            
            print(f"Execution Success Rate: {len(successful_steps)}/{len(execution_results)} ({len(successful_steps)/len(execution_results)*100:.1f}%)")
            
            if failed_steps:
                print("\nFailed Steps:")
                for step in failed_steps:
                    print(f"   {step.get('step', 'Unknown')}: {step.get('result_issue', 'Unknown error')}")
            else:
                print("✅ All steps completed successfully!")
        print()
        
        print("🎉 DEMONSTRATION COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("The Sequential File Selection and Error Handling system has been")
        print("successfully demonstrated with live DeFi operations, showing:")
        print("✅ Intelligent file selection using 5-approach framework")
        print("✅ Systematic execution with proper error handling")  
        print("✅ Comprehensive audit trail generation")
        print("✅ Structured reporting in both Markdown and JSON formats")
        
        return result
        
    except Exception as e:
        print(f"❌ Demonstration failed: {str(e)}")
        import traceback
        print(f"Stack trace: {traceback.format_exc()}")
        return None

if __name__ == "__main__":
    main()