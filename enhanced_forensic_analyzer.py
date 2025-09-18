#!/usr/bin/env python3
"""
ENHANCED FORENSIC ANALYZER - Detailed Calldata and Approval Pattern Extraction
Comprehensive analysis with proper hex decoding and approval pattern identification
"""

import os
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from web3 import Web3
from web3.types import TxReceipt, TxData
from eth_utils import to_hex, decode_hex, keccak, function_signature_to_4byte_selector
from datetime import datetime
import struct

class EnhancedForensicAnalyzer:
    """Enhanced forensic analyzer with detailed calldata decoding"""
    
    def __init__(self):
        """Initialize with enhanced Web3 connection and ABI definitions"""
        # Use Alchemy RPC for reliability
        alchemy_key = os.getenv('ALCHEMY_RPC_URL', 'https://arb1.arbitrum.io/rpc')
        self.w3 = Web3(Web3.HTTPProvider(alchemy_key))
        
        if not self.w3.is_connected():
            raise Exception(f"Failed to connect to Arbitrum RPC: {alchemy_key}")
        
        print(f"🔗 Enhanced Forensic Analyzer connected to Arbitrum")
        print(f"   Latest block: {self.w3.eth.block_number}")
        
        # Contract addresses
        self.contracts = {
            'aave_debt_switch_v3': '0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4',
            'paraswap_augustus': '0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57',
            'aave_pool': '0x794a61358D6845594F94dc1DB02A252b5b4814aD',
            'dai_token': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1',
            'arb_token': '0x912CE59144191C1204E64559FE8253a0e49E6548'
        }
        
        # Event signatures
        self.event_signatures = {
            'Transfer': '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef',
            'Approval': '0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925',
            'SwapDebt': '0xbf77fd13a39d14dc0da779342c14105c38d9a5d0c60f2caa22f5fd1d5525416d'
        }

    def analyze_transaction_enhanced(self, tx_hash: str) -> Dict:
        """Enhanced transaction analysis with proper calldata decoding"""
        print(f"\n🔍 ENHANCED ANALYSIS: {tx_hash}")
        print("=" * 80)
        
        try:
            # Get transaction data and receipt
            tx_data = self.w3.eth.get_transaction(tx_hash)
            tx_receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            
            analysis = {
                'transaction_hash': tx_hash,
                'block_number': tx_data['blockNumber'],
                'timestamp': self.get_block_timestamp(tx_data['blockNumber']),
                'from_address': tx_data['from'],
                'to_address': tx_data['to'],
                'value': int(tx_data['value']),
                'gas_used': int(tx_receipt['gasUsed']),
                'gas_price': int(tx_data['gasPrice']),
                'status': int(tx_receipt['status']),
                'raw_input': tx_data['input'].hex(),
                'logs': tx_receipt['logs'],
                'calldata_analysis': {},
                'approval_patterns': {},
                'transfer_analysis': {},
                'paraswap_routing': {},
                'permit_signatures': {},
                'critical_patterns': []
            }
            
            print(f"✅ Transaction retrieved:")
            print(f"   Block: {analysis['block_number']}")
            print(f"   From: {analysis['from_address']}")
            print(f"   To: {analysis['to_address']}")
            print(f"   Status: {'SUCCESS' if analysis['status'] == 1 else 'FAILED'}")
            print(f"   Gas Used: {analysis['gas_used']:,}")
            print(f"   Input Size: {len(analysis['raw_input'])} chars")
            
            # Enhanced calldata analysis
            if analysis['to_address'].lower() == self.contracts['aave_debt_switch_v3'].lower():
                analysis['calldata_analysis'] = self.decode_swapdebt_calldata(analysis['raw_input'])
                print(f"🎯 CONFIRMED: Aave Debt Switch V3 interaction")
            else:
                print(f"⚠️ Unexpected contract: {analysis['to_address']}")
            
            # Enhanced log analysis
            analysis['approval_patterns'] = self.analyze_approvals_enhanced(analysis['logs'])
            analysis['transfer_analysis'] = self.analyze_transfers_enhanced(analysis['logs'])
            
            # Extract ParaSwap routing from swapData
            if 'swapData' in analysis['calldata_analysis']:
                analysis['paraswap_routing'] = self.decode_paraswap_routing(
                    analysis['calldata_analysis']['swapData']
                )
            
            # Analyze permit signatures
            analysis['permit_signatures'] = self.analyze_permit_signatures(analysis['calldata_analysis'])
            
            # Identify critical automation patterns
            analysis['critical_patterns'] = self.extract_critical_patterns(analysis)
            
            return analysis
            
        except Exception as e:
            print(f"❌ Error in enhanced analysis: {e}")
            return {
                'transaction_hash': tx_hash,
                'error': str(e),
                'error_details': [f"Enhanced analysis failed: {e}"]
            }

    def get_block_timestamp(self, block_number: int) -> str:
        """Get block timestamp"""
        try:
            block = self.w3.eth.get_block(block_number)
            return datetime.fromtimestamp(block['timestamp']).isoformat()
        except:
            return "unknown"

    def decode_swapdebt_calldata(self, raw_input: str) -> Dict:
        """Enhanced swapDebt calldata decoding with proper parameter extraction"""
        try:
            print(f"🔧 Enhanced calldata decoding...")
            
            # Remove 0x prefix if present
            if raw_input.startswith('0x'):
                raw_input = raw_input[2:]
            
            # Verify function selector
            function_selector = '0x' + raw_input[:8]
            if function_selector != '0xb8bd1c6b':
                return {'error': f'Wrong function selector: {function_selector}, expected 0xb8bd1c6b'}
            
            print(f"✅ Function selector verified: {function_selector}")
            
            # Parse parameters manually (more reliable than ABI decoding)
            calldata_params = self.parse_swapdebt_parameters(raw_input[8:])
            
            if 'error' in calldata_params:
                return calldata_params
            
            print(f"✅ Successfully decoded swapDebt parameters")
            print(f"   Debt Asset: {calldata_params['debtSwapParams']['debtAsset']}")
            print(f"   Repay Amount: {calldata_params['debtSwapParams']['debtRepayAmount'] / 1e18:.6f}")
            print(f"   New Debt Asset: {calldata_params['debtSwapParams']['newDebtAsset']}")
            print(f"   Max New Debt: {calldata_params['debtSwapParams']['maxNewDebtAmount'] / 1e18:.6f}")
            print(f"   Offset: {calldata_params['debtSwapParams']['offset']}")
            print(f"   SwapData Length: {len(calldata_params['debtSwapParams']['swapData'])} bytes")
            
            return {
                'function_selector': function_selector,
                'function_name': 'swapDebt',
                'debtSwapParams': calldata_params['debtSwapParams'],
                'creditDelegationPermit': calldata_params['creditDelegationPermit'],
                'collateralATokenPermit': calldata_params['collateralATokenPermit'],
                'raw_calldata': raw_input,
                'calldata_length': len(raw_input) // 2
            }
            
        except Exception as e:
            print(f"❌ Error decoding calldata: {e}")
            return {'error': f'Calldata decoding failed: {e}'}

    def parse_swapdebt_parameters(self, calldata_hex: str) -> Dict:
        """Manual parameter parsing for swapDebt function"""
        try:
            # Convert hex to bytes
            calldata_bytes = bytes.fromhex(calldata_hex)
            
            # Parse the three main parameter offsets (each 32 bytes)
            debt_swap_params_offset = int.from_bytes(calldata_bytes[0:32], 'big')
            credit_delegation_permit_offset = int.from_bytes(calldata_bytes[32:64], 'big')
            collateral_atoken_permit_offset = int.from_bytes(calldata_bytes[64:96], 'big')
            
            print(f"   Parameter offsets: {debt_swap_params_offset}, {credit_delegation_permit_offset}, {collateral_atoken_permit_offset}")
            
            # Parse debtSwapParams struct
            debt_swap_params = self.parse_debt_swap_params(calldata_bytes, debt_swap_params_offset)
            
            # Parse creditDelegationPermit struct
            credit_delegation_permit = self.parse_permit_struct(calldata_bytes, credit_delegation_permit_offset)
            
            # Parse collateralATokenPermit struct  
            collateral_atoken_permit = self.parse_permit_struct(calldata_bytes, collateral_atoken_permit_offset)
            
            return {
                'debtSwapParams': debt_swap_params,
                'creditDelegationPermit': credit_delegation_permit,
                'collateralATokenPermit': collateral_atoken_permit
            }
            
        except Exception as e:
            return {'error': f'Parameter parsing failed: {e}'}

    def parse_debt_swap_params(self, calldata_bytes: bytes, offset: int) -> Dict:
        """Parse debtSwapParams struct"""
        try:
            start = offset
            
            # Each field is 32 bytes (256 bits)
            debt_asset = '0x' + calldata_bytes[start+12:start+32].hex()  # address (last 20 bytes)
            debt_repay_amount = int.from_bytes(calldata_bytes[start+32:start+64], 'big')
            debt_rate_mode = int.from_bytes(calldata_bytes[start+64:start+96], 'big')
            new_debt_asset = '0x' + calldata_bytes[start+96+12:start+128].hex()  # address (last 20 bytes)
            max_new_debt_amount = int.from_bytes(calldata_bytes[start+128:start+160], 'big')
            extra_collateral_asset = '0x' + calldata_bytes[start+160+12:start+192].hex()  # address
            extra_collateral_amount = int.from_bytes(calldata_bytes[start+192:start+224], 'big')
            swap_data_offset = int.from_bytes(calldata_bytes[start+224:start+256], 'big')
            actual_offset = int.from_bytes(calldata_bytes[start+256:start+288], 'big')
            
            # Parse swapData
            swap_data_length = int.from_bytes(calldata_bytes[start+swap_data_offset:start+swap_data_offset+32], 'big')
            swap_data_start = start + swap_data_offset + 32
            swap_data = calldata_bytes[swap_data_start:swap_data_start+swap_data_length].hex()
            
            return {
                'debtAsset': debt_asset,
                'debtRepayAmount': debt_repay_amount,
                'debtRateMode': debt_rate_mode,
                'newDebtAsset': new_debt_asset,
                'maxNewDebtAmount': max_new_debt_amount,
                'extraCollateralAsset': extra_collateral_asset,
                'extraCollateralAmount': extra_collateral_amount,
                'offset': actual_offset,
                'swapData': swap_data,
                'swapDataLength': swap_data_length
            }
            
        except Exception as e:
            return {'error': f'DebtSwapParams parsing failed: {e}'}

    def parse_permit_struct(self, calldata_bytes: bytes, offset: int) -> Dict:
        """Parse permit struct (creditDelegationPermit or collateralATokenPermit)"""
        try:
            start = offset
            
            token_address = '0x' + calldata_bytes[start+12:start+32].hex()  # address (last 20 bytes)
            value = int.from_bytes(calldata_bytes[start+32:start+64], 'big')
            deadline = int.from_bytes(calldata_bytes[start+64:start+96], 'big')
            v = int.from_bytes(calldata_bytes[start+96:start+128], 'big')
            r = '0x' + calldata_bytes[start+128:start+160].hex()
            s = '0x' + calldata_bytes[start+160:start+192].hex()
            
            return {
                'token': token_address,
                'value': value,
                'deadline': deadline,
                'v': v,
                'r': r,
                's': s,
                'is_permit': value > 0 and deadline > 0
            }
            
        except Exception as e:
            return {'error': f'Permit parsing failed: {e}'}

    def analyze_approvals_enhanced(self, logs: List) -> Dict:
        """Enhanced approval analysis with proper event decoding"""
        approvals = {
            'erc20_approvals': [],
            'token_approvals': [],
            'approval_events': [],
            'total_approvals': 0,
            'approval_summary': {}
        }
        
        print(f"🔍 Enhanced approval analysis...")
        
        for log in logs:
            if len(log['topics']) > 0 and log['topics'][0].hex() == self.event_signatures['Approval']:
                try:
                    # Decode approval event
                    owner = '0x' + log['topics'][1].hex()[26:]  # Remove padding
                    spender = '0x' + log['topics'][2].hex()[26:]  # Remove padding
                    amount = int(log['data'], 16)
                    
                    approval_event = {
                        'contract': log['address'],
                        'owner': owner,
                        'spender': spender,
                        'amount': amount,
                        'amount_formatted': self.format_amount(amount),
                        'token_symbol': self.identify_token_symbol(log['address'])
                    }
                    
                    approvals['approval_events'].append(approval_event)
                    approvals['total_approvals'] += 1
                    
                    print(f"   📝 Approval: {approval_event['token_symbol']} {approval_event['amount_formatted']} to {spender[-6:]}")
                    
                except Exception as e:
                    print(f"⚠️ Error decoding approval: {e}")
        
        # Create approval summary
        for approval in approvals['approval_events']:
            token = approval['token_symbol']
            if token not in approvals['approval_summary']:
                approvals['approval_summary'][token] = []
            approvals['approval_summary'][token].append({
                'spender': approval['spender'],
                'amount': approval['amount_formatted']
            })
        
        print(f"✅ Found {approvals['total_approvals']} approval events")
        return approvals

    def analyze_transfers_enhanced(self, logs: List) -> Dict:
        """Enhanced transfer analysis to track token flow"""
        transfers = {
            'transfer_events': [],
            'token_flows': {},
            'swap_route': [],
            'total_transfers': 0
        }
        
        print(f"🔍 Enhanced transfer analysis...")
        
        for log in logs:
            if len(log['topics']) > 0 and log['topics'][0].hex() == self.event_signatures['Transfer']:
                try:
                    from_addr = '0x' + log['topics'][1].hex()[26:]  # Remove padding
                    to_addr = '0x' + log['topics'][2].hex()[26:]  # Remove padding
                    amount = int(log['data'], 16)
                    
                    transfer_event = {
                        'contract': log['address'],
                        'from': from_addr,
                        'to': to_addr,
                        'amount': amount,
                        'amount_formatted': self.format_amount(amount),
                        'token_symbol': self.identify_token_symbol(log['address'])
                    }
                    
                    transfers['transfer_events'].append(transfer_event)
                    transfers['total_transfers'] += 1
                    
                    # Track token flows
                    token = transfer_event['token_symbol']
                    if token not in transfers['token_flows']:
                        transfers['token_flows'][token] = []
                    transfers['token_flows'][token].append(f"{from_addr[-6:]} → {to_addr[-6:]} ({transfer_event['amount_formatted']})")
                    
                    print(f"   💸 Transfer: {token} {transfer_event['amount_formatted']} {from_addr[-6:]} → {to_addr[-6:]}")
                    
                except Exception as e:
                    print(f"⚠️ Error decoding transfer: {e}")
        
        # Determine swap route
        transfers['swap_route'] = self.determine_swap_route(transfers['transfer_events'])
        
        print(f"✅ Found {transfers['total_transfers']} transfer events")
        return transfers

    def decode_paraswap_routing(self, swap_data_hex: str) -> Dict:
        """Enhanced ParaSwap routing data analysis"""
        try:
            print(f"🔧 Enhanced ParaSwap routing analysis...")
            
            if not swap_data_hex or len(swap_data_hex) < 8:
                return {'error': 'Empty or invalid swap data'}
            
            # Parse function selector
            function_selector = '0x' + swap_data_hex[:8]
            
            routing = {
                'function_selector': function_selector,
                'data_length': len(swap_data_hex) // 2,
                'raw_data': '0x' + swap_data_hex,
                'function_name': self.identify_paraswap_function(function_selector),
                'token_addresses': [],
                'routing_analysis': {}
            }
            
            # Extract token addresses
            dai_addr = self.contracts['dai_token'].lower()[2:]  # Remove 0x
            arb_addr = self.contracts['arb_token'].lower()[2:]  # Remove 0x
            
            routing['contains_dai'] = dai_addr in swap_data_hex.lower()
            routing['contains_arb'] = arb_addr in swap_data_hex.lower()
            
            # Find positions of token addresses
            if routing['contains_dai']:
                dai_pos = swap_data_hex.lower().find(dai_addr)
                routing['dai_position'] = dai_pos
            
            if routing['contains_arb']:
                arb_pos = swap_data_hex.lower().find(arb_addr)
                routing['arb_position'] = arb_pos
            
            print(f"   Function: {routing['function_name']}")
            print(f"   Contains DAI: {routing['contains_dai']}")
            print(f"   Contains ARB: {routing['contains_arb']}")
            print(f"   Data length: {routing['data_length']} bytes")
            
            return routing
            
        except Exception as e:
            print(f"❌ Error decoding ParaSwap routing: {e}")
            return {'error': f'ParaSwap routing analysis failed: {e}'}

    def analyze_permit_signatures(self, calldata_analysis: Dict) -> Dict:
        """Analyze permit signature usage"""
        permits = {
            'credit_delegation_used': False,
            'collateral_atoken_used': False,
            'permit_vs_approval': 'approval',
            'permit_details': {}
        }
        
        print(f"🔍 Permit signature analysis...")
        
        if 'creditDelegationPermit' in calldata_analysis:
            credit_permit = calldata_analysis['creditDelegationPermit']
            if credit_permit.get('is_permit', False):
                permits['credit_delegation_used'] = True
                permits['permit_vs_approval'] = 'permit'
                permits['permit_details']['credit_delegation'] = credit_permit
                print(f"   ✅ Credit delegation permit used: {credit_permit['value'] / 1e18:.6f}")
        
        if 'collateralATokenPermit' in calldata_analysis:
            atoken_permit = calldata_analysis['collateralATokenPermit']
            if atoken_permit.get('is_permit', False):
                permits['collateral_atoken_used'] = True
                permits['permit_vs_approval'] = 'permit'
                permits['permit_details']['collateral_atoken'] = atoken_permit
                print(f"   ✅ Collateral aToken permit used: {atoken_permit['value'] / 1e18:.6f}")
        
        if not permits['credit_delegation_used'] and not permits['collateral_atoken_used']:
            print(f"   📝 Using standard approvals (no permits)")
        
        return permits

    def extract_critical_patterns(self, analysis: Dict) -> List[str]:
        """Extract critical patterns for automation replication"""
        patterns = []
        
        # Contract address pattern
        if analysis['to_address'].lower() == self.contracts['aave_debt_switch_v3'].lower():
            patterns.append(f"CRITICAL: Uses Aave Debt Switch V3: {self.contracts['aave_debt_switch_v3']}")
        
        # Function selector pattern
        if 'function_selector' in analysis.get('calldata_analysis', {}):
            patterns.append(f"CRITICAL: Function selector: {analysis['calldata_analysis']['function_selector']}")
        
        # Approval pattern
        approvals = analysis.get('approval_patterns', {})
        if approvals.get('total_approvals', 0) > 0:
            patterns.append(f"CRITICAL: {approvals['total_approvals']} approval events required")
            for token, approval_list in approvals.get('approval_summary', {}).items():
                patterns.append(f"PATTERN: {token} approvals to {len(approval_list)} spenders")
        
        # Permit pattern
        permits = analysis.get('permit_signatures', {})
        if permits.get('permit_vs_approval') == 'permit':
            patterns.append(f"CRITICAL: Uses permit signatures instead of approvals")
        else:
            patterns.append(f"CRITICAL: Uses standard approvals (no permits)")
        
        # ParaSwap routing pattern
        paraswap = analysis.get('paraswap_routing', {})
        if paraswap.get('function_name'):
            patterns.append(f"CRITICAL: ParaSwap function: {paraswap['function_name']}")
        
        # Offset pattern
        calldata = analysis.get('calldata_analysis', {})
        if 'debtSwapParams' in calldata and 'offset' in calldata['debtSwapParams']:
            offset = calldata['debtSwapParams']['offset']
            patterns.append(f"CRITICAL: Offset calculation: {offset}")
        
        return patterns

    def identify_token_symbol(self, address: str) -> str:
        """Identify token symbol from address"""
        address_lower = address.lower()
        if address_lower == self.contracts['dai_token'].lower():
            return 'DAI'
        elif address_lower == self.contracts['arb_token'].lower():
            return 'ARB'
        else:
            return f"Token({address[-6:]})"

    def identify_paraswap_function(self, selector: str) -> str:
        """Identify ParaSwap function from selector"""
        known_selectors = {
            '0x935fb84b': 'multiSwap',
            '0xb22f4db8': 'megaSwap',
            '0x64466805': 'directSwap',
            '0x54e3f31b': 'simpleSwap',
            '0xa94e78ef': 'directUniV3Swap'
        }
        return known_selectors.get(selector, f'Unknown({selector})')

    def format_amount(self, amount: int) -> str:
        """Format amount with appropriate decimals"""
        if amount == 0:
            return "0"
        elif amount >= 10**30:  # Likely max uint256
            return "MAX_UINT256"
        else:
            return f"{amount / 1e18:.6f}"

    def determine_swap_route(self, transfers: List[Dict]) -> List[str]:
        """Determine the swap route from transfer events"""
        route = []
        dai_transfers = [t for t in transfers if t['token_symbol'] == 'DAI']
        arb_transfers = [t for t in transfers if t['token_symbol'] == 'ARB']
        
        if dai_transfers and arb_transfers:
            route.append("DAI → ARB debt swap detected")
            route.append(f"DAI transfers: {len(dai_transfers)}")
            route.append(f"ARB transfers: {len(arb_transfers)}")
        
        return route

def main():
    """Enhanced forensic analysis execution"""
    print(f"🔍 ENHANCED FORENSIC ANALYZER - Detailed Pattern Extraction")
    print(f"⏰ {datetime.now().isoformat()}")
    print("=" * 80)
    
    transactions = [
        '0x988cd8ad6df4f4557ddef352f42fe7e9ca9909553efe0abe2b4f36d6fad3e663',
        '0xdb1da3add62b0736c862ca7bc63e22afa9e1b85e0d06750b35dbe514b00deb2f'
    ]
    
    try:
        analyzer = EnhancedForensicAnalyzer()
        
        enhanced_analyses = []
        for i, tx_hash in enumerate(transactions, 1):
            print(f"\n🎯 ENHANCED ANALYSIS {i}/{len(transactions)}")
            analysis = analyzer.analyze_transaction_enhanced(tx_hash)
            enhanced_analyses.append(analysis)
            time.sleep(1)
        
        # Create comprehensive forensic report
        enhanced_report = {
            'enhanced_forensic_metadata': {
                'analysis_timestamp': datetime.now().isoformat(),
                'analyzer_version': '2.0.0_enhanced',
                'target_transactions': transactions,
                'network': 'arbitrum_mainnet',
                'purpose': 'detailed_automation_pattern_extraction',
                'enhancements': [
                    'proper_calldata_decoding',
                    'enhanced_approval_analysis', 
                    'detailed_transfer_tracking',
                    'paraswap_routing_analysis',
                    'permit_signature_detection',
                    'critical_pattern_extraction'
                ]
            },
            'enhanced_analyses': enhanced_analyses,
            'automation_blueprint': {
                'critical_requirements': [],
                'exact_parameters': {},
                'approval_patterns': {},
                'routing_requirements': {},
                'implementation_checklist': []
            }
        }
        
        # Extract automation blueprint
        if len(enhanced_analyses) >= 2:
            blueprint = enhanced_report['automation_blueprint']
            
            # Collect critical patterns from both transactions
            all_patterns = []
            for analysis in enhanced_analyses:
                all_patterns.extend(analysis.get('critical_patterns', []))
            
            blueprint['critical_requirements'] = list(set(all_patterns))
            
            # Extract exact parameters
            for i, analysis in enumerate(enhanced_analyses):
                calldata = analysis.get('calldata_analysis', {})
                if 'debtSwapParams' in calldata:
                    blueprint['exact_parameters'][f'transaction_{i+1}'] = {
                        'debtAsset': calldata['debtSwapParams'].get('debtAsset'),
                        'newDebtAsset': calldata['debtSwapParams'].get('newDebtAsset'),
                        'offset': calldata['debtSwapParams'].get('offset'),
                        'swapDataLength': calldata['debtSwapParams'].get('swapDataLength')
                    }
                
                # Extract approval patterns
                approvals = analysis.get('approval_patterns', {})
                blueprint['approval_patterns'][f'transaction_{i+1}'] = approvals.get('approval_summary', {})
                
                # Extract routing requirements
                paraswap = analysis.get('paraswap_routing', {})
                blueprint['routing_requirements'][f'transaction_{i+1}'] = {
                    'function': paraswap.get('function_name'),
                    'data_length': paraswap.get('data_length'),
                    'contains_dai': paraswap.get('contains_dai'),
                    'contains_arb': paraswap.get('contains_arb')
                }
            
            # Implementation checklist
            blueprint['implementation_checklist'] = [
                '1. Use Aave Debt Switch V3 contract: 0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4',
                '2. Ensure swapDebt function selector: 0xb8bd1c6b',
                '3. Calculate correct offset matching ParaSwap data length',
                '4. Handle standard approvals (no permits detected)',
                '5. Encode ParaSwap routing data correctly',
                '6. Verify token addresses in swap route',
                '7. Test gas estimation with exact parameters'
            ]
        
        # Export enhanced report
        filename = f'enhanced_forensic_analysis_{int(time.time())}.json'
        with open(filename, 'w') as f:
            json.dump(enhanced_report, f, indent=2, default=str)
        
        print(f"\n🎉 ENHANCED FORENSIC ANALYSIS COMPLETE")
        print("=" * 80)
        print(f"📊 Enhanced analyses completed: {len(enhanced_analyses)}")
        print(f"📄 Enhanced report: {filename}")
        print(f"🎯 Critical patterns identified: {len(enhanced_report['automation_blueprint']['critical_requirements'])}")
        print(f"🔧 Ready for automation implementation")
        
        return enhanced_report
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR in enhanced analysis: {e}")
        return {'error': str(e)}

if __name__ == "__main__":
    main()