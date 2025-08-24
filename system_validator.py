#!/usr/bin/env python3
"""
System Validator - Runs for 4 minutes to validate system stability
Tests all endpoints and monitors for errors
"""

import time
import requests
import threading
import json
from datetime import datetime

class SystemValidator:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.start_time = time.time()
        self.test_duration = 240  # 4 minutes
        self.results = {
            'total_tests': 0,
            'successful_tests': 0,
            'failed_tests': 0,
            'api_responses': [],
            'errors': [],
            'status': 'running'
        }

    def test_api_endpoint(self, endpoint: str) -> bool:
        """Test a single API endpoint"""
        try:
            response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
            self.results['total_tests'] += 1

            if response.status_code == 200:
                data = response.json()
                self.results['successful_tests'] += 1
                self.results['api_responses'].append({
                    'endpoint': endpoint,
                    'status': 'success',
                    'timestamp': time.time(),
                    'data_keys': list(data.keys()) if isinstance(data, dict) else []
                })
                return True
            else:
                self.results['failed_tests'] += 1
                self.results['errors'].append({
                    'endpoint': endpoint,
                    'error': f"HTTP {response.status_code}",
                    'timestamp': time.time()
                })
                return False

        except Exception as e:
            self.results['failed_tests'] += 1
            self.results['errors'].append({
                'endpoint': endpoint,
                'error': str(e),
                'timestamp': time.time()
            })
            return False

    def continuous_testing(self):
        """Run continuous tests for 4 minutes"""
        print("🧪 STARTING 4-MINUTE SYSTEM VALIDATION")
        print("=" * 50)

        endpoints_to_test = [
            "/api/wallet-status",
            "/api/system-status",
            "/"
        ]

        test_count = 0
        while time.time() - self.start_time < self.test_duration:
            current_time = time.time() - self.start_time

            # Test each endpoint
            for endpoint in endpoints_to_test:
                success = self.test_api_endpoint(endpoint)
                test_count += 1

                if test_count % 10 == 0:  # Print status every 10 tests
                    print(f"⏱️ {current_time:.1f}s - Tests: {self.results['total_tests']}, "
                          f"Success: {self.results['successful_tests']}, "
                          f"Failed: {self.results['failed_tests']}")

            # Wait 10 seconds between test cycles
            time.sleep(10)

        self.results['status'] = 'completed'
        self.results['duration'] = time.time() - self.start_time

    def generate_report(self):
        """Generate final validation report"""
        print("\n🎯 4-MINUTE VALIDATION COMPLETE")
        print("=" * 50)
        print(f"Duration: {self.results['duration']:.1f} seconds")
        print(f"Total Tests: {self.results['total_tests']}")
        print(f"Successful: {self.results['successful_tests']}")
        print(f"Failed: {self.results['failed_tests']}")

        success_rate = (self.results['successful_tests'] / self.results['total_tests'] * 100) if self.results['total_tests'] > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")

        if self.results['errors']:
            print(f"\n❌ ERRORS DETECTED ({len(self.results['errors'])}):")
            for error in self.results['errors'][-5:]:  # Show last 5 errors
                print(f"   {error['endpoint']}: {error['error']}")

        # System health assessment
        if success_rate >= 90 and len(self.results['errors']) < 5:
            print(f"\n✅ SYSTEM STATUS: HEALTHY")
            print(f"✅ Dashboard is running stably")
            print(f"✅ Ready for continuous operation")
        elif success_rate >= 70:
            print(f"\n⚠️ SYSTEM STATUS: MODERATE")
            print(f"⚠️ Some issues detected but functional")
        else:
            print(f"\n❌ SYSTEM STATUS: UNSTABLE")
            print(f"❌ Significant issues detected")

        return success_rate >= 90

def run_validation():
    """Run the 4-minute system validation"""
    validator = SystemValidator()

    # Start validation in background
    validation_thread = threading.Thread(target=validator.continuous_testing)
    validation_thread.daemon = True
    validation_thread.start()

    # Wait for completion
    validation_thread.join()

    # Generate report
    return validator.generate_report()

if __name__ == "__main__":
    print("🚀 System Validator Starting...")
    print("⏱️ Will run for 4 minutes to validate system stability")

    # Give dashboard time to start
    print("⏳ Waiting 30 seconds for dashboard to initialize...")
    time.sleep(30)

    # Run validation
    success = run_validation()

    if success:
        print("\n🎉 SYSTEM VALIDATION PASSED!")
        print("🎪 Ready to tell knock-knock joke!")
    else:
        print("\n❌ SYSTEM VALIDATION FAILED!")
        print("🔧 Additional fixes needed")