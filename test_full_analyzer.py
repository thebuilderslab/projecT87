#!/usr/bin/env python3
"""
Test the full Enhanced Forensic Analyzer
"""

import os
import sys
import traceback
from datetime import datetime

def test_full_analyzer():
    """Test the comprehensive analyzer"""
    print(f"🔍 TESTING FULL ENHANCED FORENSIC ANALYZER")
    print(f"⏰ {datetime.now().isoformat()}")
    print("=" * 70)
    
    try:
        # Import the enhanced analyzer
        print("📦 Importing EnhancedForensicAnalyzer...")
        
        # Import components individually for testing
        sys.path.append('.')
        from enhanced_forensic_analyzer import (
            EnhancedRPCManager, 
            ABIRegistry, 
            TraceAndLogFetcher,
            EventDecoder,
            TokenMetadataCache
        )
        
        print("✅ Component imports successful")
        
        # Test 1: RPC Manager
        print("\n🔗 Testing Enhanced RPC Manager...")
        rpc_manager = EnhancedRPCManager()
        block_number = rpc_manager.w3.eth.block_number
        print(f"✅ RPC Manager initialized - Block: {block_number}")
        
        # Test 2: ABI Registry
        print("\n📚 Testing ABI Registry...")
        abi_registry = ABIRegistry()
        # Test with a known token
        dai_abi = abi_registry.get_abi("0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1")
        print(f"✅ ABI Registry working - DAI ABI: {len(dai_abi) if dai_abi else 0} functions")
        
        # Test 3: Token Cache
        print("\n🪙 Testing Token Metadata Cache...")
        token_cache = TokenMetadataCache(rpc_manager)
        dai_info = token_cache.get_token_info("0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1")
        print(f"✅ Token Cache working - DAI: {dai_info}")
        
        # Test 4: Event Decoder
        print("\n🔧 Testing Event Decoder...")
        event_decoder = EventDecoder(abi_registry, rpc_manager)
        print("✅ Event Decoder initialized")
        
        # Test 5: Trace Fetcher
        print("\n📋 Testing Trace and Log Fetcher...")
        trace_fetcher = TraceAndLogFetcher(rpc_manager)
        print("✅ Trace Fetcher initialized")
        
        print(f"\n✅ ALL COMPONENTS WORKING!")
        return True
        
    except Exception as e:
        print(f"❌ Full analyzer test failed: {e}")
        traceback.print_exc()
        return False

def test_transaction_analysis():
    """Test actual transaction analysis"""
    print(f"\n🎯 TESTING TRANSACTION ANALYSIS")
    print("=" * 50)
    
    try:
        from enhanced_forensic_analyzer import EnhancedForensicAnalyzer
        
        analyzer = EnhancedForensicAnalyzer()
        print("✅ Full analyzer initialized")
        
        # Test with first transaction hash
        tx_hash = '0x5f5d8e9b2ddd18cb3ee46a1e1f27d84d10725d61fa965ab272786ceac47f8996'
        print(f"\n📊 Analyzing: {tx_hash[:30]}...")
        
        result = analyzer.analyze_transaction_comprehensive(tx_hash)
        
        if 'error' in result:
            print(f"⚠️ Analysis had error: {result['error']}")
            return False
        else:
            print(f"✅ Analysis successful!")
            print(f"   Block: {result['block_number']}")
            print(f"   Status: {result['status']}")
            print(f"   Total logs: {result['logs_analysis']['total_logs']}")
            print(f"   Events: {list(result['logs_analysis']['event_summary'].keys())}")
            return True
            
    except Exception as e:
        print(f"❌ Transaction analysis failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    success1 = test_full_analyzer()
    success2 = test_transaction_analysis() if success1 else False
    
    print(f"\n📊 FINAL TEST RESULTS")
    print("=" * 50)
    print(f"Component Tests: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"Transaction Analysis: {'✅ PASS' if success2 else '❌ FAIL'}")
    print(f"Overall: {'✅ COMPLETE SUCCESS' if success1 and success2 else '⚠️ PARTIAL SUCCESS' if success1 else '❌ FAILED'}")
    
    return success1 and success2

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)