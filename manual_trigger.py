
#!/usr/bin/env python3
"""
Manual Trigger Activation - Force autonomous sequence for testing
"""

import os

def activate_manual_trigger():
    """Create manual override flag to force trigger activation"""
    with open('manual_override.flag', 'w') as f:
        f.write('MANUAL_TRIGGER_ACTIVATED\n')
        f.write(f'Timestamp: {time.time()}\n')
    
    print("✅ Manual trigger activated!")
    print("🚀 Next monitoring cycle will execute autonomous sequence")
    print("💡 Remove with: rm manual_override.flag")

if __name__ == "__main__":
    import time
    activate_manual_trigger()
