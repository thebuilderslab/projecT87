#!/usr/bin/env python3
"""
Comprehensive Transaction Verification Module
Post-execution verification system with Aave subgraph integration and Arbiscan event parsing
"""

import json
import os
import requests
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from web3 import Web3
from web3.types import TxReceipt

class TransactionVerifier:
    """Comprehensive transaction verification for debt swap operations"""
    
    def __init__(self, w3: Web3):
        self.w3 = w3
        self.chain_id = 42161  # Arbitrum
        
        # API endpoints
        self.arbiscan_api_base = "https://api.arbiscan.io/api"
        self.aave_subgraph_url = "https://api.thegraph.com/subgraphs/name/aave/protocol-v3-arbitrum"
        self.arbiscan_api_key = os.getenv('ARBISCAN_API_KEY', '')
        
        # Contract addresses for verification
        self.aave_debt_switch_v3 = "0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4"
        self.aave_pool = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
        self.aave_data_provider = "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654"
        
        # Token addresses
        self.tokens = {
            'DAI': "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
            'ARB': "0x912CE59144191C1204E64559FE8253a0e49E6548"
        }
        
        # Event signatures for parsing
        self.event_signatures = {
            'Borrow': "0x1e77446728e5558aa1b7e81e0cdab9cc1b075ba893b2c662fa5a24e2a61a6f5f",
            'Repay': "0x4cdde6e09bb755c9a5589ebaec640bbfedff1362d4b255ebf8339782b9942faa",
            'FlashLoan': "0x631042c832b07452973831137f2d73e395028b44b250dedc5abb0ee766e168ac",
            'Swap': "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67",
        }
        
        print("🔍 Transaction Verifier initialized")
        print(f"   Aave Debt Switch V3: {self.aave_debt_switch_v3}")
        print(f"   Arbiscan API: {'✅ Available' if self.arbiscan_api_key else '⚠️ No API key'}")

    def verify_debt_swap_transaction(self, tx_hash: str, expected_params: Dict) -> Dict[str, Any]:
        """
        Comprehensive verification of debt swap transaction
        Returns complete verification report including events, position changes, and debugging info
        """
        print(f"\n🔍 COMPREHENSIVE TRANSACTION VERIFICATION")
        print(f"Transaction: {tx_hash}")
        print("=" * 80)
        
        verification_result = {
            'transaction_hash': tx_hash,
            'verification_timestamp': datetime.now().isoformat(),
            'transaction_receipt': {},
            'decoded_events': [],
            'position_comparison': {},
            'arbiscan_analysis': {},
            'aave_subgraph_data': {},
            'verification_status': 'pending',
            'errors': [],
            'warnings': [],
            'debugging_info': {}
        }
        
        try:
            # Step 1: Get transaction receipt
            verification_result['transaction_receipt'] = self._get_transaction_receipt(tx_hash)
            if not verification_result['transaction_receipt']['success']:
                verification_result['errors'].append("Failed to get transaction receipt")
                return verification_result
            
            # Step 2: Parse and decode events
            verification_result['decoded_events'] = self._parse_transaction_events(
                verification_result['transaction_receipt']['receipt']
            )
            
            # Step 3: Get before/after position comparison
            verification_result['position_comparison'] = self._get_position_comparison(
                tx_hash, expected_params.get('user_address')
            )
            
            # Step 4: Arbiscan detailed analysis
            verification_result['arbiscan_analysis'] = self._analyze_with_arbiscan(tx_hash)
            
            # Step 5: Aave subgraph verification
            verification_result['aave_subgraph_data'] = self._verify_with_aave_subgraph(
                tx_hash, expected_params.get('user_address')
            )
            
            # Step 6: Generate debugging information
            verification_result['debugging_info'] = self._generate_debugging_info(
                verification_result, expected_params
            )
            
            # Step 7: Determine overall verification status
            verification_result['verification_status'] = self._determine_verification_status(
                verification_result
            )
            
            print(f"✅ Verification completed with status: {verification_result['verification_status']}")
            
        except Exception as e:
            verification_result['errors'].append(f"Verification failed: {str(e)}")
            verification_result['verification_status'] = 'failed'
            print(f"❌ Verification failed: {e}")
        
        return verification_result

    def _get_transaction_receipt(self, tx_hash: str) -> Dict[str, Any]:
        """Get transaction receipt with retry logic"""
        result = {'success': False, 'receipt': None, 'error': None}
        
        try:
            print("📋 Getting transaction receipt...")
            
            # Wait for transaction to be mined if necessary
            max_wait = 60  # seconds
            wait_time = 0
            
            while wait_time < max_wait:
                try:
                    receipt = self.w3.eth.get_transaction_receipt(tx_hash)
                    result['success'] = True
                    result['receipt'] = receipt
                    
                    print(f"✅ Transaction receipt obtained")
                    print(f"   Status: {'SUCCESS' if receipt.status == 1 else 'FAILED'}")
                    print(f"   Gas Used: {receipt.gasUsed:,}")
                    print(f"   Block Number: {receipt.blockNumber:,}")
                    
                    return result
                    
                except Exception as e:
                    if "not found" in str(e).lower():
                        print(f"⏳ Waiting for transaction to be mined... ({wait_time}s)")
                        time.sleep(5)
                        wait_time += 5
                    else:
                        raise e
            
            result['error'] = f"Transaction not found after {max_wait}s"
            
        except Exception as e:
            result['error'] = f"Failed to get receipt: {str(e)}"
        
        return result

    def _parse_transaction_events(self, receipt: TxReceipt) -> List[Dict[str, Any]]:
        """Parse and decode transaction events"""
        decoded_events = []
        
        try:
            print("🔍 Parsing transaction events...")
            
            for log in receipt.logs:
                try:
                    # Decode common Aave events
                    event_data = {
                        'address': log.address,
                        'topics': [topic.hex() for topic in log.topics],
                        'data': log.data.hex(),
                        'decoded': None
                    }
                    
                    # Check if this is a known event signature
                    if log.topics and log.topics[0].hex() in self.event_signatures.values():
                        event_name = next(
                            name for name, sig in self.event_signatures.items() 
                            if sig == log.topics[0].hex()
                        )
                        event_data['event_name'] = event_name
                        
                        # Attempt to decode based on event type
                        if event_name in ['Borrow', 'Repay']:
                            event_data['decoded'] = self._decode_borrow_repay_event(log)
                        elif event_name == 'FlashLoan':
                            event_data['decoded'] = self._decode_flashloan_event(log)
                        elif event_name == 'Swap':
                            event_data['decoded'] = self._decode_swap_event(log)
                    
                    decoded_events.append(event_data)
                    
                except Exception as e:
                    print(f"⚠️ Failed to decode event: {e}")
                    decoded_events.append({
                        'address': log.address,
                        'error': f"Decode failed: {str(e)}"
                    })
            
            print(f"✅ Parsed {len(decoded_events)} events")
            borrow_repay_events = [e for e in decoded_events if e.get('event_name') in ['Borrow', 'Repay']]
            if borrow_repay_events:
                print(f"📊 Found {len(borrow_repay_events)} Borrow/Repay events")
            else:
                print("⚠️ No Borrow/Repay events found - may not be visible on Aave UI")
            
        except Exception as e:
            print(f"❌ Event parsing failed: {e}")
        
        return decoded_events

    def _decode_borrow_repay_event(self, log) -> Dict[str, Any]:
        """Decode Borrow/Repay events"""
        try:
            # Basic decoding - this would need proper ABI for full decoding
            return {
                'type': 'borrow_repay',
                'reserve': log.topics[1].hex() if len(log.topics) > 1 else None,
                'user': log.topics[2].hex() if len(log.topics) > 2 else None,
                'amount': int(log.data[:64], 16) if log.data else 0,
                'raw_data': log.data.hex()
            }
        except Exception as e:
            return {'error': f"Decode failed: {str(e)}"}

    def _decode_flashloan_event(self, log) -> Dict[str, Any]:
        """Decode FlashLoan events"""
        try:
            return {
                'type': 'flashloan',
                'target': log.topics[1].hex() if len(log.topics) > 1 else None,
                'asset': log.topics[2].hex() if len(log.topics) > 2 else None,
                'amount': int(log.data[:64], 16) if log.data else 0,
                'raw_data': log.data.hex()
            }
        except Exception as e:
            return {'error': f"Decode failed: {str(e)}"}

    def _decode_swap_event(self, log) -> Dict[str, Any]:
        """Decode Swap events"""
        try:
            return {
                'type': 'swap',
                'token_in': log.topics[1].hex() if len(log.topics) > 1 else None,
                'token_out': log.topics[2].hex() if len(log.topics) > 2 else None,
                'amount_in': int(log.data[:64], 16) if log.data else 0,
                'raw_data': log.data.hex()
            }
        except Exception as e:
            return {'error': f"Decode failed: {str(e)}"}

    def _get_position_comparison(self, tx_hash: str, user_address: str) -> Dict[str, Any]:
        """Get before/after position comparison"""
        comparison = {
            'before': {},
            'after': {},
            'changes': {},
            'success': False
        }
        
        try:
            if not user_address:
                return comparison
            
            print("📊 Getting position comparison...")
            
            # Get transaction block number
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            block_number = receipt.blockNumber
            
            # Get position before (previous block) and after (current block)
            comparison['before'] = self._get_aave_position_at_block(user_address, block_number - 1)
            comparison['after'] = self._get_aave_position_at_block(user_address, block_number)
            
            # Calculate changes
            if comparison['before']['success'] and comparison['after']['success']:
                comparison['changes'] = self._calculate_position_changes(
                    comparison['before']['position'],
                    comparison['after']['position']
                )
                comparison['success'] = True
                
                print("✅ Position comparison completed")
                if comparison['changes']:
                    print("📈 Position changes detected:")
                    for change in comparison['changes']:
                        print(f"   • {change}")
            else:
                print("⚠️ Failed to get complete position data")
                
        except Exception as e:
            comparison['error'] = str(e)
            print(f"❌ Position comparison failed: {e}")
        
        return comparison

    def _get_aave_position_at_block(self, user_address: str, block_number: int) -> Dict[str, Any]:
        """Get Aave position at specific block"""
        result = {'success': False, 'position': {}, 'error': None}
        
        try:
            # Pool contract for getUserAccountData
            pool_abi = [{
                "inputs": [{"name": "user", "type": "address"}],
                "name": "getUserAccountData",
                "outputs": [
                    {"name": "totalCollateralBase", "type": "uint256"},
                    {"name": "totalDebtBase", "type": "uint256"},
                    {"name": "availableBorrowsBase", "type": "uint256"},
                    {"name": "currentLiquidationThreshold", "type": "uint256"},
                    {"name": "ltv", "type": "uint256"},
                    {"name": "healthFactor", "type": "uint256"}
                ],
                "stateMutability": "view",
                "type": "function"
            }]
            
            pool_contract = self.w3.eth.contract(address=self.aave_pool, abi=pool_abi)
            
            # Get account data at specific block
            account_data = pool_contract.functions.getUserAccountData(user_address).call(block_identifier=block_number)
            
            result['position'] = {
                'total_collateral_usd': float(account_data[0]) / (10**8),
                'total_debt_usd': float(account_data[1]) / (10**8),
                'available_borrows_usd': float(account_data[2]) / (10**8),
                'health_factor': float(account_data[5]) / (10**18) if account_data[5] != 2**256 - 1 else float('inf'),
                'block_number': block_number
            }
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
        
        return result

    def _calculate_position_changes(self, before: Dict, after: Dict) -> List[str]:
        """Calculate meaningful position changes"""
        changes = []
        
        try:
            # Health factor changes
            if abs(before['health_factor'] - after['health_factor']) > 0.01:
                changes.append(
                    f"Health Factor: {before['health_factor']:.3f} → {after['health_factor']:.3f}"
                )
            
            # Debt changes
            if abs(before['total_debt_usd'] - after['total_debt_usd']) > 0.01:
                changes.append(
                    f"Total Debt: ${before['total_debt_usd']:.2f} → ${after['total_debt_usd']:.2f}"
                )
            
            # Collateral changes
            if abs(before['total_collateral_usd'] - after['total_collateral_usd']) > 0.01:
                changes.append(
                    f"Total Collateral: ${before['total_collateral_usd']:.2f} → ${after['total_collateral_usd']:.2f}"
                )
            
        except Exception as e:
            changes.append(f"Error calculating changes: {str(e)}")
        
        return changes

    def _analyze_with_arbiscan(self, tx_hash: str) -> Dict[str, Any]:
        """Analyze transaction using Arbiscan API"""
        analysis = {
            'transaction_details': {},
            'internal_transactions': [],
            'token_transfers': [],
            'success': False
        }
        
        try:
            if not self.arbiscan_api_key:
                analysis['warning'] = "No Arbiscan API key - limited analysis"
                return analysis
            
            print("🔍 Analyzing with Arbiscan...")
            
            # Get transaction details
            tx_response = requests.get(f"{self.arbiscan_api_base}", params={
                'module': 'proxy',
                'action': 'eth_getTransactionByHash',
                'txhash': tx_hash,
                'apikey': self.arbiscan_api_key
            }, timeout=10)
            
            if tx_response.status_code == 200:
                analysis['transaction_details'] = tx_response.json().get('result', {})
            
            # Get internal transactions
            internal_response = requests.get(f"{self.arbiscan_api_base}", params={
                'module': 'account',
                'action': 'txlistinternal',
                'txhash': tx_hash,
                'apikey': self.arbiscan_api_key
            }, timeout=10)
            
            if internal_response.status_code == 200:
                analysis['internal_transactions'] = internal_response.json().get('result', [])
            
            # Get token transfers
            token_response = requests.get(f"{self.arbiscan_api_base}", params={
                'module': 'account',
                'action': 'tokentx',
                'txhash': tx_hash,
                'apikey': self.arbiscan_api_key
            }, timeout=10)
            
            if token_response.status_code == 200:
                analysis['token_transfers'] = token_response.json().get('result', [])
            
            analysis['success'] = True
            print(f"✅ Arbiscan analysis completed")
            print(f"   Internal transactions: {len(analysis['internal_transactions'])}")
            print(f"   Token transfers: {len(analysis['token_transfers'])}")
            
        except Exception as e:
            analysis['error'] = str(e)
            print(f"❌ Arbiscan analysis failed: {e}")
        
        return analysis

    def _verify_with_aave_subgraph(self, tx_hash: str, user_address: str) -> Dict[str, Any]:
        """Verify transaction with Aave subgraph"""
        subgraph_data = {
            'user_transactions': [],
            'borrow_events': [],
            'repay_events': [],
            'success': False
        }
        
        try:
            if not user_address:
                return subgraph_data
            
            print("🔍 Querying Aave subgraph...")
            
            # GraphQL query for user transactions around the time
            query = f'''
            {{
              userTransactions(
                where: {{user: "{user_address.lower()}"}}
                orderBy: timestamp
                orderDirection: desc
                first: 10
              ) {{
                id
                timestamp
                txHash
                action
                amount
                reserve {{
                  symbol
                  decimals
                }}
              }}
              
              borrows(
                where: {{user: "{user_address.lower()}"}}
                orderBy: timestamp
                orderDirection: desc
                first: 5
              ) {{
                id
                timestamp
                txHash
                amount
                reserve {{
                  symbol
                }}
              }}
              
              repays(
                where: {{user: "{user_address.lower()}"}}
                orderBy: timestamp
                orderDirection: desc
                first: 5
              ) {{
                id
                timestamp
                txHash
                amount
                reserve {{
                  symbol
                }}
              }}
            }}
            '''
            
            response = requests.post(
                self.aave_subgraph_url,
                json={'query': query},
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    subgraph_data.update(data['data'])
                    subgraph_data['success'] = True
                    
                    print("✅ Aave subgraph data retrieved")
                    print(f"   User transactions: {len(subgraph_data.get('userTransactions', []))}")
                    print(f"   Borrow events: {len(subgraph_data.get('borrows', []))}")
                    print(f"   Repay events: {len(subgraph_data.get('repays', []))}")
                else:
                    subgraph_data['error'] = "No data in response"
            else:
                subgraph_data['error'] = f"HTTP {response.status_code}"
                
        except Exception as e:
            subgraph_data['error'] = str(e)
            print(f"❌ Aave subgraph query failed: {e}")
        
        return subgraph_data

    def _generate_debugging_info(self, verification_result: Dict, expected_params: Dict) -> Dict[str, Any]:
        """Generate comprehensive debugging information"""
        debugging_info = {
            'manual_vs_automated_comparison': {},
            'event_sequence_analysis': {},
            'parameter_differences': {},
            'gas_analysis': {},
            'success_indicators': [],
            'failure_indicators': [],
            'recommendations': []
        }
        
        try:
            print("🔍 Generating debugging information...")
            
            # Analyze events sequence
            events = verification_result.get('decoded_events', [])
            debugging_info['event_sequence_analysis'] = {
                'total_events': len(events),
                'borrow_repay_events': len([e for e in events if e.get('event_name') in ['Borrow', 'Repay']]),
                'flashloan_events': len([e for e in events if e.get('event_name') == 'FlashLoan']),
                'swap_events': len([e for e in events if e.get('event_name') == 'Swap']),
                'event_addresses': list(set([e.get('address') for e in events if e.get('address')]))
            }
            
            # Gas analysis
            receipt = verification_result.get('transaction_receipt', {}).get('receipt')
            if receipt:
                debugging_info['gas_analysis'] = {
                    'gas_used': receipt.gasUsed,
                    'gas_limit': receipt.gas if hasattr(receipt, 'gas') else 'N/A',
                    'gas_efficiency': 'Normal' if receipt.gasUsed < 100000 else 'High'
                }
            
            # Success/failure indicators
            if verification_result['transaction_receipt'].get('success'):
                debugging_info['success_indicators'].append("Transaction mined successfully")
            
            if verification_result.get('decoded_events'):
                debugging_info['success_indicators'].append("Events decoded successfully")
            
            if verification_result.get('position_comparison', {}).get('success'):
                debugging_info['success_indicators'].append("Position changes detected")
            
            # Check for Aave UI visibility
            borrow_repay_events = debugging_info['event_sequence_analysis']['borrow_repay_events']
            if borrow_repay_events == 0:
                debugging_info['failure_indicators'].append("No Borrow/Repay events - may not appear in Aave UI")
                debugging_info['recommendations'].append("Check if transaction interacted with correct Aave contracts")
            
            print("✅ Debugging information generated")
            
        except Exception as e:
            debugging_info['error'] = str(e)
            print(f"❌ Debugging info generation failed: {e}")
        
        return debugging_info

    def _determine_verification_status(self, verification_result: Dict) -> str:
        """Determine overall verification status"""
        try:
            # Check critical success criteria
            has_receipt = verification_result['transaction_receipt'].get('success', False)
            has_events = len(verification_result.get('decoded_events', [])) > 0
            has_borrow_repay = any(
                e.get('event_name') in ['Borrow', 'Repay'] 
                for e in verification_result.get('decoded_events', [])
            )
            
            if has_receipt and has_events and has_borrow_repay:
                return 'success'
            elif has_receipt and has_events:
                return 'partial_success'
            elif has_receipt:
                return 'transaction_successful_but_incomplete_verification'
            else:
                return 'failed'
        except:
            return 'verification_error'

    def compare_manual_vs_automated_execution(self, manual_tx: str, automated_tx: str) -> Dict[str, Any]:
        """Compare manual transaction with automated execution"""
        comparison = {
            'manual_analysis': {},
            'automated_analysis': {},
            'differences': {},
            'recommendations': []
        }
        
        try:
            print(f"\n🔄 COMPARING MANUAL VS AUTOMATED EXECUTION")
            print("=" * 60)
            
            # Analyze both transactions
            comparison['manual_analysis'] = self.verify_debt_swap_transaction(manual_tx, {})
            comparison['automated_analysis'] = self.verify_debt_swap_transaction(automated_tx, {})
            
            # Compare key differences
            manual_events = len(comparison['manual_analysis'].get('decoded_events', []))
            automated_events = len(comparison['automated_analysis'].get('decoded_events', []))
            
            comparison['differences'] = {
                'event_count_difference': manual_events - automated_events,
                'gas_usage_difference': self._calculate_gas_difference(
                    comparison['manual_analysis'],
                    comparison['automated_analysis']
                ),
                'success_difference': (
                    comparison['manual_analysis']['verification_status'],
                    comparison['automated_analysis']['verification_status']
                )
            }
            
            # Generate recommendations
            if manual_events > automated_events:
                comparison['recommendations'].append("Automated execution missing some events - check contract interactions")
            
            print("✅ Manual vs Automated comparison completed")
            
        except Exception as e:
            comparison['error'] = str(e)
            print(f"❌ Comparison failed: {e}")
        
        return comparison

    def _calculate_gas_difference(self, manual_analysis: Dict, automated_analysis: Dict) -> int:
        """Calculate gas usage difference between executions"""
        try:
            manual_gas = manual_analysis['transaction_receipt']['receipt'].gasUsed
            automated_gas = automated_analysis['transaction_receipt']['receipt'].gasUsed
            return manual_gas - automated_gas
        except:
            return 0

    def generate_verification_report(self, verification_result: Dict) -> str:
        """Generate human-readable verification report"""
        report = []
        report.append("=" * 80)
        report.append("COMPREHENSIVE DEBT SWAP VERIFICATION REPORT")
        report.append("=" * 80)
        report.append(f"Transaction: {verification_result['transaction_hash']}")
        report.append(f"Verification Time: {verification_result['verification_timestamp']}")
        report.append(f"Status: {verification_result['verification_status'].upper()}")
        report.append("")
        
        # Transaction details
        if verification_result['transaction_receipt'].get('success'):
            receipt = verification_result['transaction_receipt']['receipt']
            report.append("TRANSACTION DETAILS:")
            report.append(f"  • Status: {'SUCCESS' if receipt.status == 1 else 'FAILED'}")
            report.append(f"  • Gas Used: {receipt.gasUsed:,}")
            report.append(f"  • Block: {receipt.blockNumber:,}")
        
        # Events analysis
        events = verification_result.get('decoded_events', [])
        report.append(f"\nEVENTS ANALYSIS:")
        report.append(f"  • Total Events: {len(events)}")
        borrow_repay = [e for e in events if e.get('event_name') in ['Borrow', 'Repay']]
        report.append(f"  • Borrow/Repay Events: {len(borrow_repay)}")
        if len(borrow_repay) == 0:
            report.append("  ⚠️  WARNING: No Borrow/Repay events - may not appear in Aave UI")
        
        # Position changes
        position_changes = verification_result.get('position_comparison', {}).get('changes', [])
        if position_changes:
            report.append(f"\nPOSITION CHANGES:")
            for change in position_changes:
                report.append(f"  • {change}")
        
        # Recommendations
        debugging = verification_result.get('debugging_info', {})
        recommendations = debugging.get('recommendations', [])
        if recommendations:
            report.append(f"\nRECOMMENDATIONS:")
            for rec in recommendations:
                report.append(f"  • {rec}")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)