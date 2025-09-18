#!/usr/bin/env python3
"""
FORENSIC TRANSACTION ANALYZER - Step 1: Aave Debt Swap Replay
Comprehensive analysis of successful manual transactions to extract automation patterns
"""

import os
import json
import time
from typing import Dict, List, Optional, Any
from web3 import Web3
from web3.types import TxReceipt, TxData
from eth_utils import to_hex, decode_hex
from datetime import datetime

class ForensicTransactionAnalyzer:
    """Forensic analyzer for successful Aave debt swap transactions"""
    
    def __init__(self):
        """Initialize with Web3 connection to Arbitrum mainnet"""
        # Use Alchemy RPC for reliability
        alchemy_key = os.getenv('ALCHEMY_RPC_URL', 'https://arb1.arbitrum.io/rpc')
        self.w3 = Web3(Web3.HTTPProvider(alchemy_key))
        
        if not self.w3.is_connected():
            raise Exception(f"Failed to connect to Arbitrum RPC: {alchemy_key}")
        
        print(f"🔗 Connected to Arbitrum mainnet")
        print(f"   Latest block: {self.w3.eth.block_number}")
        
        # Contract addresses for analysis
        self.contracts = {
            'aave_debt_switch_v3': '0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4',
            'paraswap_augustus': '0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57',
            'aave_pool': '0x794a61358D6845594F94dc1DB02A252b5b4814aD',
            'dai_token': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1',
            'arb_token': '0x912CE59144191C1204E64559FE8253a0e49E6548'
        }
        
        # Known function signatures
        self.function_signatures = {
            '0xb8bd1c6b': 'swapDebt(tuple,tuple,tuple)',
            '0xa9059cbb': 'transfer(address,uint256)',
            '0x095ea7b3': 'approve(address,uint256)',
            '0xd505accf': 'permit(address,address,uint256,uint256,uint8,bytes32,bytes32)',
            '0x6e553f65': 'creditDelegationApproval(address,uint256,uint256,uint8,bytes32,bytes32)'
        }
        
        # ERC20 ABI for decoding
        self.erc20_abi = [
            {
                "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "owner", "type": "address"},
                    {"name": "spender", "type": "address"},
                    {"name": "value", "type": "uint256"},
                    {"name": "deadline", "type": "uint256"},
                    {"name": "v", "type": "uint8"},
                    {"name": "r", "type": "bytes32"},
                    {"name": "s", "type": "bytes32"}
                ],
                "name": "permit",
                "outputs": [],
                "type": "function"
            }
        ]
        
        # Debt swap ABI for decoding calldata
        self.debt_swap_abi = [{
            "inputs": [
                {
                    "components": [
                        {"name": "debtAsset", "type": "address"},
                        {"name": "debtRepayAmount", "type": "uint256"},
                        {"name": "debtRateMode", "type": "uint256"},
                        {"name": "newDebtAsset", "type": "address"},
                        {"name": "maxNewDebtAmount", "type": "uint256"},
                        {"name": "extraCollateralAsset", "type": "address"},
                        {"name": "extraCollateralAmount", "type": "uint256"},
                        {"name": "offset", "type": "uint256"},
                        {"name": "swapData", "type": "bytes"}
                    ],
                    "name": "debtSwapParams",
                    "type": "tuple"
                },
                {
                    "components": [
                        {"name": "debtToken", "type": "address"},
                        {"name": "value", "type": "uint256"},
                        {"name": "deadline", "type": "uint256"},
                        {"name": "v", "type": "uint8"},
                        {"name": "r", "type": "bytes32"},
                        {"name": "s", "type": "bytes32"}
                    ],
                    "name": "creditDelegationPermit",
                    "type": "tuple"
                },
                {
                    "components": [
                        {"name": "aToken", "type": "address"},
                        {"name": "value", "type": "uint256"},
                        {"name": "deadline", "type": "uint256"},
                        {"name": "v", "type": "uint8"},
                        {"name": "r", "type": "bytes32"},
                        {"name": "s", "type": "bytes32"}
                    ],
                    "name": "collateralATokenPermit",
                    "type": "tuple"
                }
            ],
            "name": "swapDebt",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }]

    def analyze_transaction(self, tx_hash: str) -> Dict:
        """Comprehensive forensic analysis of a single transaction"""
        print(f"\n🔍 FORENSIC ANALYSIS: {tx_hash}")
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
                'value': tx_data['value'],
                'gas_used': tx_receipt['gasUsed'],
                'gas_price': tx_data['gasPrice'],
                'status': tx_receipt['status'],
                'input_data': tx_data['input'],
                'logs': tx_receipt['logs'],
                'decoded_data': {},
                'approval_analysis': {},
                'permit_analysis': {},
                'paraswap_analysis': {},
                'contract_interactions': {},
                'error_details': []
            }
            
            print(f"✅ Transaction data retrieved:")
            print(f"   Block: {analysis['block_number']}")
            print(f"   From: {analysis['from_address']}")
            print(f"   To: {analysis['to_address']}")
            print(f"   Status: {'SUCCESS' if analysis['status'] == 1 else 'FAILED'}")
            print(f"   Gas Used: {analysis['gas_used']:,}")
            
            # Identify contract interaction
            analysis['contract_interactions'] = self.identify_contract_interactions(analysis)
            
            # Decode main transaction calldata
            if analysis['to_address'].lower() == self.contracts['aave_debt_switch_v3'].lower():
                analysis['decoded_data'] = self.decode_debt_swap_calldata(analysis['input_data'])
                print(f"🎯 CONFIRMED: Aave Debt Switch V3 interaction")
            else:
                print(f"⚠️ Unexpected contract: {analysis['to_address']}")
                analysis['error_details'].append(f"Not Aave Debt Switch V3: {analysis['to_address']}")
            
            # Analyze transaction logs for approvals and permits
            analysis['approval_analysis'] = self.analyze_approvals_from_logs(analysis['logs'])
            analysis['permit_analysis'] = self.analyze_permits_from_logs(analysis['logs'])
            
            # Extract ParaSwap routing data
            if 'swapData' in analysis['decoded_data']:
                analysis['paraswap_analysis'] = self.decode_paraswap_data(analysis['decoded_data']['swapData'])
            
            return analysis
            
        except Exception as e:
            print(f"❌ Error analyzing transaction {tx_hash}: {e}")
            return {
                'transaction_hash': tx_hash,
                'error': str(e),
                'error_details': [f"Failed to retrieve transaction: {e}"]
            }

    def get_block_timestamp(self, block_number: int) -> str:
        """Get block timestamp"""
        try:
            block = self.w3.eth.get_block(block_number)
            return datetime.fromtimestamp(block['timestamp']).isoformat()
        except:
            return "unknown"

    def identify_contract_interactions(self, analysis: Dict) -> Dict:
        """Identify which contracts were interacted with"""
        interactions = {
            'main_contract': analysis['to_address'],
            'is_aave_debt_switch_v3': analysis['to_address'].lower() == self.contracts['aave_debt_switch_v3'].lower(),
            'paraswap_interactions': [],
            'token_interactions': []
        }
        
        # Check logs for contract interactions
        for log in analysis['logs']:
            contract_addr = log['address'].lower()
            
            if contract_addr == self.contracts['paraswap_augustus'].lower():
                interactions['paraswap_interactions'].append(log)
            elif contract_addr in [self.contracts['dai_token'].lower(), self.contracts['arb_token'].lower()]:
                interactions['token_interactions'].append({
                    'contract': log['address'],
                    'topics': [t.hex() for t in log['topics']],
                    'data': log['data']
                })
        
        return interactions

    def decode_debt_swap_calldata(self, input_data: str) -> Dict:
        """Decode swapDebt function calldata"""
        try:
            print(f"🔧 Decoding swapDebt calldata...")
            
            # Check function selector
            function_selector = input_data[:10]
            if function_selector != '0xb8bd1c6b':
                return {'error': f'Wrong function selector: {function_selector}, expected 0xb8bd1c6b'}
            
            # Create contract instance for decoding
            contract = self.w3.eth.contract(abi=self.debt_swap_abi)
            
            # Decode the input data
            decoded = contract.decode_function_input(input_data)
            function_obj, inputs = decoded
            
            decoded_data = {
                'function_name': function_obj.function_identifier,
                'function_selector': function_selector,
                'debtSwapParams': {
                    'debtAsset': inputs['debtSwapParams'][0],
                    'debtRepayAmount': inputs['debtSwapParams'][1],
                    'debtRateMode': inputs['debtSwapParams'][2],
                    'newDebtAsset': inputs['debtSwapParams'][3],
                    'maxNewDebtAmount': inputs['debtSwapParams'][4],
                    'extraCollateralAsset': inputs['debtSwapParams'][5],
                    'extraCollateralAmount': inputs['debtSwapParams'][6],
                    'offset': inputs['debtSwapParams'][7],
                    'swapData': inputs['debtSwapParams'][8].hex()
                },
                'creditDelegationPermit': {
                    'debtToken': inputs['creditDelegationPermit'][0],
                    'value': inputs['creditDelegationPermit'][1],
                    'deadline': inputs['creditDelegationPermit'][2],
                    'v': inputs['creditDelegationPermit'][3],
                    'r': inputs['creditDelegationPermit'][4].hex(),
                    's': inputs['creditDelegationPermit'][5].hex()
                },
                'collateralATokenPermit': {
                    'aToken': inputs['collateralATokenPermit'][0],
                    'value': inputs['collateralATokenPermit'][1],
                    'deadline': inputs['collateralATokenPermit'][2],
                    'v': inputs['collateralATokenPermit'][3],
                    'r': inputs['collateralATokenPermit'][4].hex(),
                    's': inputs['collateralATokenPermit'][5].hex()
                }
            }
            
            print(f"✅ Successfully decoded calldata")
            print(f"   Debt Asset: {decoded_data['debtSwapParams']['debtAsset']}")
            print(f"   Repay Amount: {decoded_data['debtSwapParams']['debtRepayAmount'] / 1e18:.6f}")
            print(f"   New Debt Asset: {decoded_data['debtSwapParams']['newDebtAsset']}")
            print(f"   Max New Debt: {decoded_data['debtSwapParams']['maxNewDebtAmount'] / 1e18:.6f}")
            print(f"   Offset: {decoded_data['debtSwapParams']['offset']}")
            
            return decoded_data
            
        except Exception as e:
            print(f"❌ Error decoding calldata: {e}")
            return {'error': f'Decoding failed: {e}'}

    def analyze_approvals_from_logs(self, logs: List) -> Dict:
        """Analyze approval events from transaction logs"""
        approvals = {
            'erc20_approvals': [],
            'atoken_approvals': [],
            'debt_token_approvals': [],
            'total_approvals': 0
        }
        
        # ERC20 Approval event signature: keccak256("Approval(address,address,uint256)")
        approval_signature = '0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925'
        
        print(f"🔍 Analyzing approval events from logs...")
        
        for log in logs:
            if len(log['topics']) > 0 and log['topics'][0].hex() == approval_signature:
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
                        'amount_formatted': amount / 1e18 if amount < 10**30 else 'MAX_UINT256'
                    }
                    
                    # Categorize approval
                    contract_lower = log['address'].lower()
                    if contract_lower in [self.contracts['dai_token'].lower(), self.contracts['arb_token'].lower()]:
                        approvals['erc20_approvals'].append(approval_event)
                        print(f"   📝 ERC20 Approval: {approval_event['contract'][-6:]} → {approval_event['spender'][-6:]} amount: {approval_event['amount_formatted']}")
                    else:
                        # Could be aToken or debt token
                        approvals['atoken_approvals'].append(approval_event)
                        print(f"   📝 aToken/Debt Approval: {approval_event['contract'][-6:]} → {approval_event['spender'][-6:]} amount: {approval_event['amount_formatted']}")
                    
                    approvals['total_approvals'] += 1
                    
                except Exception as e:
                    print(f"⚠️ Error decoding approval log: {e}")
        
        print(f"✅ Found {approvals['total_approvals']} approval events")
        return approvals

    def analyze_permits_from_logs(self, logs: List) -> Dict:
        """Analyze permit signatures from transaction logs and calldata"""
        permits = {
            'credit_delegation_permits': [],
            'atoken_permits': [],
            'erc20_permits': [],
            'permit_usage': 'none'
        }
        
        print(f"🔍 Analyzing permit signatures...")
        
        # Since permits are typically in calldata rather than events,
        # we need to check the decoded calldata for permit parameters
        # This will be filled in by the main analysis when calldata is decoded
        
        return permits

    def decode_paraswap_data(self, swap_data_hex: str) -> Dict:
        """Decode ParaSwap routing data from swapData bytes"""
        try:
            print(f"🔧 Decoding ParaSwap routing data...")
            print(f"   SwapData length: {len(swap_data_hex)} characters")
            
            if not swap_data_hex or swap_data_hex == '0x':
                return {'error': 'Empty swap data'}
            
            # Remove 0x prefix if present
            if swap_data_hex.startswith('0x'):
                swap_data_hex = swap_data_hex[2:]
            
            # Parse ParaSwap data structure
            # First 4 bytes are usually the function selector for ParaSwap
            function_selector = '0x' + swap_data_hex[:8]
            
            paraswap_analysis = {
                'function_selector': function_selector,
                'data_length': len(swap_data_hex) // 2,
                'raw_data': '0x' + swap_data_hex,
                'routing_info': {},
                'slippage_info': {},
                'token_path': []
            }
            
            print(f"   Function selector: {function_selector}")
            
            # Try to identify known ParaSwap functions
            known_paraswap_selectors = {
                '0x935fb84b': 'multiSwap',
                '0xb22f4db8': 'megaSwap', 
                '0x64466805': 'directSwap',
                '0x54e3f31b': 'simpleSwap'
            }
            
            if function_selector in known_paraswap_selectors:
                paraswap_analysis['function_name'] = known_paraswap_selectors[function_selector]
                print(f"   Identified function: {paraswap_analysis['function_name']}")
            else:
                paraswap_analysis['function_name'] = 'unknown'
                print(f"   Unknown ParaSwap function: {function_selector}")
            
            # For detailed parsing, we'd need ParaSwap's ABI
            # For now, extract basic structure
            if len(swap_data_hex) > 8:
                # Extract token addresses that commonly appear in swap data
                paraswap_analysis['contains_dai'] = self.contracts['dai_token'].lower()[2:] in swap_data_hex.lower()
                paraswap_analysis['contains_arb'] = self.contracts['arb_token'].lower()[2:] in swap_data_hex.lower()
                
                print(f"   Contains DAI address: {paraswap_analysis['contains_dai']}")
                print(f"   Contains ARB address: {paraswap_analysis['contains_arb']}")
            
            return paraswap_analysis
            
        except Exception as e:
            print(f"❌ Error decoding ParaSwap data: {e}")
            return {'error': f'ParaSwap decoding failed: {e}'}

    def compare_transactions(self, analysis1: Dict, analysis2: Dict) -> Dict:
        """Compare two transaction analyses to identify patterns"""
        print(f"\n🔬 COMPARATIVE ANALYSIS")
        print("=" * 80)
        
        comparison = {
            'timestamp': datetime.now().isoformat(),
            'transaction_1': analysis1['transaction_hash'],
            'transaction_2': analysis2['transaction_hash'],
            'common_patterns': {},
            'differences': {},
            'automation_requirements': {},
            'critical_findings': []
        }
        
        try:
            # Compare contract interactions
            if analysis1.get('contract_interactions', {}).get('is_aave_debt_switch_v3') and \
               analysis2.get('contract_interactions', {}).get('is_aave_debt_switch_v3'):
                comparison['common_patterns']['uses_aave_debt_switch_v3'] = True
                print(f"✅ PATTERN: Both use Aave Debt Switch V3")
            
            # Compare function selectors
            if analysis1.get('decoded_data', {}).get('function_selector') == \
               analysis2.get('decoded_data', {}).get('function_selector'):
                comparison['common_patterns']['same_function'] = analysis1.get('decoded_data', {}).get('function_selector')
                print(f"✅ PATTERN: Same function selector: {comparison['common_patterns']['same_function']}")
            
            # Compare approval patterns
            approvals1 = analysis1.get('approval_analysis', {})
            approvals2 = analysis2.get('approval_analysis', {})
            
            if approvals1.get('total_approvals') and approvals2.get('total_approvals'):
                comparison['common_patterns']['approval_count_range'] = [
                    min(approvals1['total_approvals'], approvals2['total_approvals']),
                    max(approvals1['total_approvals'], approvals2['total_approvals'])
                ]
                print(f"✅ PATTERN: Approval count range: {comparison['common_patterns']['approval_count_range']}")
            
            # Compare ParaSwap usage
            para1 = analysis1.get('paraswap_analysis', {})
            para2 = analysis2.get('paraswap_analysis', {})
            
            if para1.get('function_name') == para2.get('function_name'):
                comparison['common_patterns']['paraswap_function'] = para1.get('function_name')
                print(f"✅ PATTERN: Same ParaSwap function: {comparison['common_patterns']['paraswap_function']}")
            
            # Extract automation requirements
            comparison['automation_requirements'] = {
                'required_contract': self.contracts['aave_debt_switch_v3'],
                'required_function': '0xb8bd1c6b',
                'min_approvals_needed': min(
                    approvals1.get('total_approvals', 0),
                    approvals2.get('total_approvals', 0)
                ),
                'paraswap_integration': True,
                'permit_signatures': self.analyze_permit_requirements(analysis1, analysis2)
            }
            
            print(f"\n🎯 AUTOMATION REQUIREMENTS IDENTIFIED:")
            for key, value in comparison['automation_requirements'].items():
                print(f"   {key}: {value}")
            
            return comparison
            
        except Exception as e:
            print(f"❌ Error in comparative analysis: {e}")
            comparison['error'] = str(e)
            return comparison

    def analyze_permit_requirements(self, analysis1: Dict, analysis2: Dict) -> Dict:
        """Analyze permit signature requirements from both transactions"""
        permit_reqs = {
            'credit_delegation_required': False,
            'atoken_permit_required': False,
            'permit_vs_approval': 'approval'  # Default assumption
        }
        
        # Check if credit delegation permits have non-zero values
        for analysis in [analysis1, analysis2]:
            credit_permit = analysis.get('decoded_data', {}).get('creditDelegationPermit', {})
            atoken_permit = analysis.get('decoded_data', {}).get('collateralATokenPermit', {})
            
            if credit_permit.get('value', 0) > 0:
                permit_reqs['credit_delegation_required'] = True
                permit_reqs['permit_vs_approval'] = 'permit'
            
            if atoken_permit.get('value', 0) > 0:
                permit_reqs['atoken_permit_required'] = True
                permit_reqs['permit_vs_approval'] = 'permit'
        
        return permit_reqs

    def export_analysis(self, analysis_data: Dict, filename: str = None) -> str:
        """Export analysis data to JSON file"""
        if not filename:
            filename = f"forensic_analysis_{int(time.time())}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(analysis_data, f, indent=2, default=str)
            
            print(f"📄 Analysis exported to: {filename}")
            return filename
        except Exception as e:
            print(f"❌ Error exporting analysis: {e}")
            return ""

def main():
    """Main forensic analysis execution"""
    print(f"🔍 FORENSIC TRANSACTION ANALYZER - Step 1")
    print(f"⏰ {datetime.now().isoformat()}")
    print("=" * 80)
    
    # Target transactions for analysis
    transactions = [
        '0x988cd8ad6df4f4557ddef352f42fe7e9ca9909553efe0abe2b4f36d6fad3e663',
        '0xdb1da3add62b0736c862ca7bc63e22afa9e1b85e0d06750b35dbe514b00deb2f'
    ]
    
    try:
        analyzer = ForensicTransactionAnalyzer()
        
        # Analyze both transactions
        analyses = []
        for i, tx_hash in enumerate(transactions, 1):
            print(f"\n🎯 ANALYZING TRANSACTION {i}/{len(transactions)}")
            analysis = analyzer.analyze_transaction(tx_hash)
            analyses.append(analysis)
            
            # Brief pause between analyses
            time.sleep(1)
        
        # Compare transactions for patterns
        if len(analyses) >= 2:
            comparison = analyzer.compare_transactions(analyses[0], analyses[1])
        else:
            comparison = {'error': 'Insufficient transaction analyses for comparison'}
        
        # Compile final forensic report
        forensic_report = {
            'forensic_analysis_metadata': {
                'analysis_timestamp': datetime.now().isoformat(),
                'analyzer_version': '1.0.0',
                'target_transactions': transactions,
                'network': 'arbitrum_mainnet',
                'purpose': 'debt_swap_automation_pattern_extraction'
            },
            'individual_analyses': analyses,
            'comparative_analysis': comparison,
            'automation_blueprint': {
                'required_steps': [
                    '1. Connect to Aave Debt Switch V3: 0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4',
                    '2. Ensure proper ERC20/aToken approvals are in place',
                    '3. Construct swapDebt calldata with correct offset calculation',
                    '4. Handle permit signatures if required (EIP-2612)',
                    '5. Encode ParaSwap routing data correctly',
                    '6. Execute with appropriate gas estimation'
                ],
                'critical_parameters': comparison.get('automation_requirements', {}),
                'verification_checklist': [
                    'Function selector == 0xb8bd1c6b',
                    'Contract address == Aave Debt Switch V3',
                    'Offset calculation matches ParaSwap data length',
                    'Approval events present in transaction logs',
                    'ParaSwap routing data properly encoded'
                ]
            }
        }
        
        # Export comprehensive report
        report_filename = analyzer.export_analysis(forensic_report, 'forensic_debt_swap_analysis.json')
        
        print(f"\n🎉 FORENSIC ANALYSIS COMPLETE")
        print("=" * 80)
        print(f"📊 Transactions analyzed: {len(analyses)}")
        print(f"📄 Report exported: {report_filename}")
        print(f"🔧 Ready for Step 2: Automation comparison and fixes")
        
        return forensic_report
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR in forensic analysis: {e}")
        return {'error': str(e)}

if __name__ == "__main__":
    main()