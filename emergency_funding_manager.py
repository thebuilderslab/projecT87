#!/usr/bin/env python3
"""
Emergency Funding Manager
Handles emergency stop functionality and system safety
"""

import os
import time
import json
from datetime import datetime

class EmergencyFundingManager:
    """Manages emergency stop and safety features"""

    def __init__(self):
        self.emergency_stop_file = 'EMERGENCY_STOP_ACTIVE.flag'
        self.emergency_active = False

    def activate_emergency_stop(self, reason="Manual activation"):
        """Activate emergency stop"""
        self.emergency_active = True

        emergency_data = {
            'timestamp': time.time(),
            'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
            'reason': reason,
            'activated_by': 'EmergencyFundingManager'
        }

        with open(self.emergency_stop_file, 'w') as f:
            f.write(f"EMERGENCY STOP ACTIVATED\n")
            f.write(f"Reason: {reason}\n")
            f.write(f"Time: {emergency_data['datetime']}\n")
            f.write(f"Timestamp: {emergency_data['timestamp']}\n")

        print(f"🚨 EMERGENCY STOP ACTIVATED: {reason}")
        return True

    def clear_emergency_stop(self):
        """Clear emergency stop"""
        if os.path.exists(self.emergency_stop_file):
            os.remove(self.emergency_stop_file)

        self.emergency_active = False
        print("✅ Emergency stop cleared")
        return True

    def is_emergency_active(self):
        """Check if emergency stop is active"""
        return os.path.exists(self.emergency_stop_file) or self.emergency_active

    def get_emergency_status(self):
        """Get emergency status details"""
        if not self.is_emergency_active():
            return {
                'active': False,
                'status': 'Normal operation'
            }

        try:
            with open(self.emergency_stop_file, 'r') as f:
                content = f.read()

            return {
                'active': True,
                'status': 'Emergency stop active',
                'details': content
            }
        except:
            return {
                'active': True,
                'status': 'Emergency stop active',
                'details': 'Details unavailable'
            }

def activate_emergency_stop(reason="Manual activation"):
    """Global function to activate emergency stop"""
    manager = EmergencyFundingManager()
    return manager.activate_emergency_stop(reason)

def clear_emergency_stop():
    """Global function to clear emergency stop"""
    manager = EmergencyFundingManager()
    return manager.clear_emergency_stop()

def check_emergency_status():
    """Global function to check emergency status"""
    manager = EmergencyFundingManager()
    return manager.get_emergency_status()

if __name__ == "__main__":
    print("🚨 Emergency Funding Manager")
    print("=" * 40)

    manager = EmergencyFundingManager()
    status = manager.get_emergency_status()

    print(f"Emergency Status: {'ACTIVE' if status['active'] else 'CLEAR'}")
    print(f"Details: {status['status']}")

    if status['active']:
        print("\n💡 To clear emergency stop:")
        print("1. Run: python emergency_funding_manager.py clear")
        print("2. Or use the web dashboard")
        print("3. Or call clear_emergency_stop() function")

    # Handle command line arguments
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == 'clear':
            manager.clear_emergency_stop()
        elif sys.argv[1] == 'activate':
            reason = sys.argv[2] if len(sys.argv) > 2 else "Command line activation"
            manager.activate_emergency_stop(reason)