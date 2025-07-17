
<file_content>
import time
import random
from web3 import Web3
from web3.providers import HTTPProvider
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests

class FallbackHTTPProvider:
    """Enhanced Web3 provider with automatic RPC failover and circuit breaker logic"""
    
    def __init__(self, rpc_urls, request_timeout=30):
        self.rpc_urls = rpc_urls
        self.request_timeout = request_timeout
        self.current_provider_index = 0
        self.failed_providers = {}  # Track failed providers with timestamps
        self.circuit_breaker_duration = 300  # 5 minutes
        
        # Initialize session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=2,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def get_active_provider(self):
        """Get the current active Web3 provider, switching if necessary"""
        current_time = time.time()
        
        # Clean up expired circuit breaker entries
        self.failed_providers = {
            url: timestamp for url, timestamp in self.failed_providers.items()
            if current_time - timestamp < self.circuit_breaker_duration
        }
        
        # Try to find a working provider
        attempts = 0
        while attempts < len(self.rpc_urls):
            current_url = self.rpc_urls[self.current_provider_index]
            
            # Skip if in circuit breaker
            if current_url in self.failed_providers:
                print(f"⚠️ Skipping {current_url} (circuit breaker active)")
                self.current_provider_index = (self.current_provider_index + 1) % len(self.rpc_urls)
                attempts += 1
                continue
            
            # Test the provider
            if self._test_provider(current_url):
                print(f"✅ Using RPC: {current_url}")
                return HTTPProvider(
                    current_url,
                    request_kwargs={
                        'timeout': self.request_timeout,
                        'headers': {
                            'User-Agent': 'ArbitrumAgent/1.0',
                            'Accept': 'application/json',
                            'Content-Type': 'application/json'
                        }
                    },
                    session=self.session
                )
            else:
                # Mark as failed and try next
                self.failed_providers[current_url] = current_time
                print(f"❌ RPC failed, marking for circuit breaker: {current_url}")
                self.current_provider_index = (self.current_provider_index + 1) % len(self.rpc_urls)
                attempts += 1
        
        # If all providers failed, reset circuit breaker and try again
        print("🔄 All providers failed, resetting circuit breaker...")
        self.failed_providers.clear()
        return self.get_active_provider()
    
    def _test_provider(self, rpc_url):
        """Test if a provider is working"""
        try:
            test_w3 = Web3(HTTPProvider(rpc_url, request_kwargs={'timeout': 5}))
            if not test_w3.is_connected():
                return False
            
            # Quick chain ID check
            chain_id = test_w3.eth.chain_id
            return chain_id == 42161  # Arbitrum Mainnet
            
        except Exception as e:
            print(f"🔍 Provider test failed for {rpc_url}: {e}")
            return False
    
    def switch_provider(self):
        """Manually switch to next provider"""
        self.current_provider_index = (self.current_provider_index + 1) % len(self.rpc_urls)
        return self.get_active_provider()

def create_robust_web3_connection(rpc_urls):
    """Create a Web3 instance with robust failover capability"""
    fallback_provider = FallbackHTTPProvider(rpc_urls)
    active_provider = fallback_provider.get_active_provider()
    
    w3 = Web3(active_provider)
    
    # Add PoA middleware if needed
    try:
        from web3.middleware import geth_poa_middleware
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    except:
        pass
    
    # Attach fallback provider for manual switching
    w3.fallback_provider = fallback_provider
    
    return w3
</file_content>
