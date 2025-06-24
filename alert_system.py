
import requests
import json
import time
from datetime import datetime

class AlertManager:
    def __init__(self):
        self.telegram_bot_token = None  # Set in secrets
        self.telegram_chat_id = None    # Set in secrets
        self.discord_webhook = None     # Set in secrets
        
    def send_critical_alert(self, message, alert_type="CRITICAL"):
        """Send critical alerts through multiple channels"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        formatted_message = f"🚨 {alert_type}: {message}\nTime: {timestamp}"
        
        # Log to emergency file
        with open('critical_alerts.log', 'a') as f:
            f.write(f"{timestamp} - {alert_type}: {message}\n")
        
        # Send notifications (implement based on available services)
        print(f"ALERT: {formatted_message}")
    
    def health_factor_alert(self, current_hf, threshold=1.1):
        """Alert when health factor drops below threshold"""
        if current_hf < threshold:
            self.send_critical_alert(
                f"Health Factor Critical: {current_hf:.4f} < {threshold}",
                "LIQUIDATION_RISK"
            )
    
    def rpc_failure_alert(self, rpc_url, error_count):
        """Alert on RPC connectivity issues"""
        if error_count >= 3:
            self.send_critical_alert(
                f"RPC Failure: {rpc_url} failed {error_count} times",
                "RPC_OUTAGE"
            )
