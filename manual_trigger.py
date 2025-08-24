
#!/usr/bin/env python3
"""
Manual Trigger Activation - Force autonomous sequence for testing
"""

import os

def activate_manual_trigger():
    """Create manual override flag to force trigger activation"""
    import time
    
    # Create multiple flag files for better detection
    flag_files = ['manual_override.flag', 'trigger_test.flag', 'force_trigger.flag']
    
    for flag_file in flag_files:
        with open(flag_file, 'w') as f:
            f.write('MANUAL_TRIGGER_ACTIVATED\n')
            f.write(f'Timestamp: {time.time()}\n')
            f.write(f'Flag file: {flag_file}\n')
    
    print("✅ Manual trigger activated!")
    print("🚀 Next monitoring cycle will execute autonomous sequence")
    print("💡 Remove with: rm manual_override.flag trigger_test.flag force_trigger.flag")

if __name__ == "__main__":
    import time
    activate_manual_trigger()
