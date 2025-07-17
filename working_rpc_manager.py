
class WorkingRPCManager:
    """Manages only the working RPC endpoints for reliability"""
    
    def __init__(self, network_mode='mainnet'):
        self.network_mode = network_mode
        self.working_rpcs = self._get_working_rpcs()
        self.current_rpc_index = 0
        
    def _get_working_rpcs(self):
        """Get list of working RPC endpoints"""
        if self.network_mode == 'mainnet':
            return [
                "https://arbitrum-mainnet.infura.io/v3/5d36f0061cbc4dda980f938ff891c141",
                "https://arb1.arbitrum.io/rpc",
                "https://arbitrum-one.publicnode.com", 
                "https://arbitrum-one.public.blastapi.io",
                "https://1rpc.io/arb"
            ]
        else:
            return [
                "https://sepolia-rollup.arbitrum.io/rpc",
                "https://arbitrum-sepolia.blockpi.network/v1/rpc/public"
            ]
    
    def get_primary_rpc(self):
        """Get the primary RPC endpoint"""
        return self.working_rpcs[0] if self.working_rpcs else None
    
    def get_next_rpc(self):
        """Get next working RPC in rotation"""
        if not self.working_rpcs:
            return None
            
        self.current_rpc_index = (self.current_rpc_index + 1) % len(self.working_rpcs)
        return self.working_rpcs[self.current_rpc_index]
    
    def get_all_working_rpcs(self):
        """Get all working RPC endpoints"""
        return self.working_rpcs.copy()
    
    def test_rpc_health(self, rpc_url):
        """Test if an RPC endpoint is healthy"""
        try:
            from web3 import Web3
            import time
            
            start_time = time.time()
            w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 10}))
            
            if not w3.is_connected():
                return False, "Not connected"
                
            # Test chain ID
            expected_chain_id = 42161 if self.network_mode == 'mainnet' else 421614
            chain_id = w3.eth.chain_id
            if chain_id != expected_chain_id:
                return False, f"Wrong chain ID: {chain_id}"
                
            # Test block number
            block_number = w3.eth.block_number
            if block_number < 1000000:
                return False, "Invalid block number"
                
            response_time = time.time() - start_time
            return True, f"Healthy (response: {response_time:.2f}s)"
            
        except Exception as e:
            return False, str(e)
