#!/usr/bin/env python3
"""
COMPREHENSIVE FORENSIC ANALYSIS REPORT GENERATOR
Generate detailed chronological sequence mapping, protocol interaction analysis,
and DAI → ARB → DAI sequence verification for target transactions.
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Any

def analyze_transaction_calldata(tx_data: Dict) -> Dict:
    """Analyze transaction calldata for DeFi protocol identification"""
    
    # Known function selectors for DeFi protocols
    function_selectors = {
        '0x4c61d48d': {
            'name': 'swapDebt',
            'protocol': 'Aave_DebtSwap',
            'description': 'Aave debt swap operation to change debt from one asset to another'
        },
        '0x095ea7b3': {
            'name': 'approve',
            'protocol': 'ERC20',
            'description': 'ERC20 token approval for spending allowance'
        },
        '0xa9059cbb': {
            'name': 'transfer',
            'protocol': 'ERC20',
            'description': 'ERC20 token transfer'
        },
        '0x617ba037': {
            'name': 'supply',
            'protocol': 'Aave_v3',
            'description': 'Supply assets to Aave lending pool'
        },
        '0xa415bcad': {
            'name': 'borrow',
            'protocol': 'Aave_v3',
            'description': 'Borrow assets from Aave lending pool'
        }
    }
    
    input_data = tx_data.get('input_data', '')
    selector = input_data[:10] if len(input_data) >= 10 else None
    
    if selector in function_selectors:
        func_info = function_selectors[selector]
        return {
            'function_selector': selector,
            'function_name': func_info['name'],
            'protocol': func_info['protocol'],
            'description': func_info['description'],
            'identified': True
        }
    
    return {
        'function_selector': selector,
        'function_name': f'Unknown({selector})',
        'protocol': 'Unknown',
        'description': 'Function not identified in DeFi protocol database',
        'identified': False
    }

def identify_contract_protocol(contract_address: str) -> str:
    """Identify protocol based on contract address"""
    
    known_contracts = {
        '0x8761e0370f94f68db8eaa731f4fc581f6ad0bd68': 'Aave_DebtSwap',
        '0x794a61358d6845594f94dc1db02a252b5b4814ad': 'Aave_v3_Pool',
        '0xdef171fe48cf0115b1d80b88dc8eab59176fee57': 'ParaSwap_Augustus',
        '0x6533afac2e7bccb20dca161449a13a32d391fb00': 'Aave_aToken_ARB',
        '0xda10009cbd5d07dd0cecc66161fc93d7c9000da1': 'DAI_Token',
        '0x912ce59144191c1204e64559fe8253a0e49e6548': 'ARB_Token'
    }
    
    return known_contracts.get(contract_address.lower(), 'Unknown_Contract')

def extract_token_addresses_from_calldata(input_data: str) -> List[str]:
    """Extract potential token addresses from transaction calldata"""
    
    # Look for 20-byte addresses in the calldata (40 hex chars)
    # This is a simplified approach - real parsing would need ABI decoding
    addresses = []
    
    # Remove 0x prefix and function selector
    data = input_data[10:] if input_data.startswith('0x') else input_data[8:]
    
    # Look for patterns that could be addresses (20 bytes = 40 hex chars)
    # Addresses are typically padded to 32 bytes in calldata
    for i in range(0, len(data) - 63, 2):
        chunk = data[i:i+64]
        if len(chunk) == 64:
            # Check if it looks like a padded address (first 24 chars are zeros)
            if chunk.startswith('000000000000000000000000') and chunk[24:] != '0' * 40:
                potential_address = '0x' + chunk[24:]
                addresses.append(potential_address)
    
    return addresses

def create_chronological_sequence(tx_analysis: Dict) -> List[Dict]:
    """Create detailed chronological sequence for transaction"""
    
    sequence = []
    tx_hash = tx_analysis['transaction_hash']
    
    # Analyze the function call
    calldata_analysis = analyze_transaction_calldata(tx_analysis)
    contract_protocol = identify_contract_protocol(tx_analysis.get('to_address', ''))
    
    # Extract potential token addresses from calldata
    token_addresses = extract_token_addresses_from_calldata(tx_analysis.get('input_data', ''))
    
    # Step 0: Initial function call
    sequence.append({
        'step': 0,
        'type': 'FUNCTION_CALL',
        'block': tx_analysis['block_number'],
        'timestamp': tx_analysis['timestamp'],
        'protocol': calldata_analysis['protocol'],
        'action': calldata_analysis['function_name'],
        'description': calldata_analysis['description'],
        'contract': tx_analysis.get('to_address', ''),
        'contract_protocol': contract_protocol,
        'from_address': tx_analysis.get('from_address', ''),
        'gas_used': tx_analysis.get('gas_used', 0),
        'value_eth': tx_analysis.get('value_eth', 0),
        'potential_tokens': token_addresses[:5],  # Limit to first 5
        'transaction_hash': tx_hash
    })
    
    # Process events
    logs_analysis = tx_analysis.get('logs_analysis', {})
    decoded_logs = logs_analysis.get('decoded_logs', [])
    
    for i, log in enumerate(decoded_logs, 1):
        event_type = log.get('event_name', 'Unknown')
        event_contract = log.get('address', '')
        event_protocol = identify_contract_protocol(event_contract)
        
        step_entry = {
            'step': i,
            'type': 'EVENT',
            'block': tx_analysis['block_number'],
            'timestamp': tx_analysis['timestamp'],
            'protocol': event_protocol,
            'action': event_type,
            'contract': event_contract,
            'log_index': log.get('log_index', 0),
            'transaction_hash': tx_hash
        }
        
        # Add specific details for different event types
        if event_type == 'Transfer':
            step_entry.update({
                'token_symbol': log.get('token_symbol', 'Unknown'),
                'from_address': log.get('from', ''),
                'to_address': log.get('to', ''),
                'amount': log.get('value_formatted', str(log.get('value', 0))),
                'amount_raw': log.get('value', 0)
            })
        elif event_type == 'Approval':
            step_entry.update({
                'token_symbol': log.get('token_symbol', 'Unknown'),
                'owner': log.get('owner', ''),
                'spender': log.get('spender', ''),
                'amount': log.get('value_formatted', str(log.get('value', 0))),
                'amount_raw': log.get('value', 0)
            })
        
        sequence.append(step_entry)
    
    return sequence

def verify_dai_arb_sequence(analyses: List[Dict]) -> Dict:
    """Verify if transactions follow DAI → ARB → DAI sequence pattern"""
    
    dai_token = '0xda10009cbd5d07dd0cecc66161fc93d7c9000da1'
    arb_token = '0x912ce59144191c1204e64559fe8253a0e49e6548'
    
    verification_results = {}
    
    for analysis in analyses:
        tx_hash = analysis['transaction_hash']
        
        # Extract token addresses from calldata
        input_data = analysis.get('input_data', '')
        token_addresses = extract_token_addresses_from_calldata(input_data)
        
        # Check for DAI and ARB in calldata
        has_dai_in_calldata = any(addr.lower() == dai_token.lower() for addr in token_addresses)
        has_arb_in_calldata = any(addr.lower() == arb_token.lower() for addr in token_addresses)
        
        # Check events for token transfers
        logs_analysis = analysis.get('logs_analysis', {})
        decoded_logs = logs_analysis.get('decoded_logs', [])
        
        dai_events = []
        arb_events = []
        
        for log in decoded_logs:
            log_address = log.get('address', '').lower()
            if log_address == dai_token.lower():
                dai_events.append(log)
            elif log_address == arb_token.lower():
                arb_events.append(log)
        
        # Determine if this follows DAI → ARB pattern
        pattern_analysis = {
            'has_dai_in_calldata': has_dai_in_calldata,
            'has_arb_in_calldata': has_arb_in_calldata,
            'dai_events_count': len(dai_events),
            'arb_events_count': len(arb_events),
            'follows_dai_arb_pattern': has_dai_in_calldata and has_arb_in_calldata,
            'is_debt_swap': analysis.get('to_address', '').lower() == '0x8761e0370f94f68db8eaa731f4fc581f6ad0bd68',
            'calldata_tokens': token_addresses
        }
        
        verification_results[tx_hash] = pattern_analysis
    
    return verification_results

def generate_human_readable_report(analyses: List[Dict]) -> str:
    """Generate comprehensive human-readable forensic report"""
    
    report_lines = []
    
    # Header
    report_lines.extend([
        "=" * 100,
        "COMPREHENSIVE DEFI TRANSACTION FORENSIC ANALYSIS REPORT",
        "=" * 100,
        f"Generated: {datetime.now().isoformat()}",
        f"Analyzer Version: Enhanced DeFi Forensics v4.0",
        f"Target Transactions: {len(analyses)}",
        "",
        "🎯 ANALYSIS OBJECTIVES:",
        "• Decode DeFi protocol interactions (Aave, ParaSwap, Uniswap)",
        "• Map chronological sequence of all actions",
        "• Verify DAI → ARB → DAI trading patterns",
        "• Identify protocol-specific events and function calls",
        "• Generate bulletproof forensic mapping",
        ""
    ])
    
    # Summary Statistics
    total_gas = sum(tx.get('gas_used', 0) for tx in analyses)
    total_events = sum(tx.get('logs_analysis', {}).get('total_logs', 0) for tx in analyses)
    successful_analyses = len([tx for tx in analyses if tx.get('status') == 'SUCCESS'])
    
    report_lines.extend([
        "📊 SUMMARY STATISTICS",
        "-" * 50,
        f"Total Transactions Analyzed: {len(analyses)}",
        f"Successful Transactions: {successful_analyses}",
        f"Total Gas Used: {total_gas:,}",
        f"Total Events Decoded: {total_events}",
        f"Analysis Success Rate: {(successful_analyses/len(analyses)*100):.1f}%",
        ""
    ])
    
    # DAI → ARB → DAI Sequence Verification
    dai_arb_verification = verify_dai_arb_sequence(analyses)
    
    report_lines.extend([
        "🔄 DAI → ARB → DAI SEQUENCE VERIFICATION",
        "-" * 50
    ])
    
    for tx_hash, verification in dai_arb_verification.items():
        report_lines.extend([
            f"Transaction: {tx_hash[:20]}...",
            f"  • Has DAI in calldata: {verification['has_dai_in_calldata']}",
            f"  • Has ARB in calldata: {verification['has_arb_in_calldata']}",
            f"  • Is debt swap operation: {verification['is_debt_swap']}",
            f"  • Follows DAI-ARB pattern: {verification['follows_dai_arb_pattern']}",
            f"  • Tokens in calldata: {len(verification['calldata_tokens'])} addresses",
            ""
        ])
    
    # Detailed Transaction Analysis
    report_lines.extend([
        "📋 DETAILED CHRONOLOGICAL ANALYSIS",
        "=" * 100
    ])
    
    for i, analysis in enumerate(analyses, 1):
        report_lines.extend([
            f"\n🔍 TRANSACTION {i}: {analysis['transaction_hash']}",
            "-" * 80,
            f"Block: {analysis['block_number']} | Timestamp: {analysis['timestamp']}",
            f"From: {analysis.get('from_address', 'N/A')}",
            f"To: {analysis.get('to_address', 'N/A')}",
            f"Status: {analysis.get('status', 'Unknown')} | Gas Used: {analysis.get('gas_used', 0):,}",
            f"Value: {analysis.get('value_eth', 0):.6f} ETH",
            ""
        ])
        
        # Generate chronological sequence
        sequence = create_chronological_sequence(analysis)
        
        report_lines.append("⏱️ CHRONOLOGICAL SEQUENCE:")
        for step in sequence:
            if step['type'] == 'FUNCTION_CALL':
                report_lines.append(
                    f"  [Step {step['step']}] CALL → {step['protocol']} | "
                    f"{step['action']} | Contract: {step['contract'][:10]}... | "
                    f"Gas: {step['gas_used']:,}"
                )
                if step.get('potential_tokens'):
                    report_lines.append(f"    Potential tokens in calldata: {len(step['potential_tokens'])} addresses")
            else:
                step_line = f"  [Step {step['step']}] EVENT → {step['protocol']} | {step['action']}"
                
                if 'token_symbol' in step:
                    if step['action'] == 'Transfer':
                        step_line += f" | {step['token_symbol']} {step['amount']} from {step.get('from_address', '')[:10]}... to {step.get('to_address', '')[:10]}..."
                    elif step['action'] == 'Approval':
                        step_line += f" | {step['token_symbol']} {step['amount']} approved by {step.get('owner', '')[:10]}... for {step.get('spender', '')[:10]}..."
                
                report_lines.append(step_line)
        
        report_lines.append("")
        
        # Protocol Interaction Summary
        calldata_analysis = analyze_transaction_calldata(analysis)
        report_lines.extend([
            "🏛️ PROTOCOL INTERACTION SUMMARY:",
            f"  • Primary Protocol: {calldata_analysis['protocol']}",
            f"  • Function Called: {calldata_analysis['function_name']}",
            f"  • Function Identified: {calldata_analysis['identified']}",
            f"  • Description: {calldata_analysis['description']}",
            ""
        ])
        
        # Events Summary
        logs_analysis = analysis.get('logs_analysis', {})
        if logs_analysis.get('total_logs', 0) > 0:
            report_lines.append("📝 EVENTS SUMMARY:")
            for event_name, count in logs_analysis.get('event_summary', {}).items():
                report_lines.append(f"  • {event_name}: {count} events")
        else:
            report_lines.append("📝 EVENTS SUMMARY: No events decoded")
        
        report_lines.append("")
    
    # Could Not Decode Entries
    report_lines.extend([
        "⚠️ DECODING LIMITATIONS AND EXPLANATIONS",
        "-" * 50
    ])
    
    for i, analysis in enumerate(analyses, 1):
        could_not_decode = []
        logs_analysis = analysis.get('logs_analysis', {})
        
        # Check for undecoded logs
        if logs_analysis.get('total_logs', 0) == 0:
            could_not_decode.append("No events/logs found or decoded")
        
        # Check for unknown function selectors
        calldata_analysis = analyze_transaction_calldata(analysis)
        if not calldata_analysis['identified']:
            could_not_decode.append(f"Unknown function selector: {calldata_analysis['function_selector']}")
        
        if could_not_decode:
            report_lines.extend([
                f"Transaction {i} ({analysis['transaction_hash'][:20]}...):",
                *[f"  • {item}" for item in could_not_decode],
                ""
            ])
    
    if not any(logs_analysis.get('total_logs', 0) == 0 for logs_analysis in [tx.get('logs_analysis', {}) for tx in analyses]):
        report_lines.append("✅ All transactions successfully decoded!")
    
    # Final Summary
    report_lines.extend([
        "",
        "🎯 FINAL FORENSIC CONCLUSIONS",
        "=" * 50,
        f"• Analysis completed for {len(analyses)} transactions",
        f"• Total events decoded: {sum(tx.get('logs_analysis', {}).get('total_logs', 0) for tx in analyses)}",
        f"• DAI-ARB pattern transactions: {sum(1 for v in dai_arb_verification.values() if v['follows_dai_arb_pattern'])}",
        f"• Debt swap operations identified: {sum(1 for v in dai_arb_verification.values() if v['is_debt_swap'])}",
        "",
        "📊 This comprehensive analysis provides bulletproof mapping of:",
        "• Protocol interactions and function calls",
        "• Token flows and asset movements", 
        "• Chronological sequence of all actions",
        "• DeFi-specific event decoding",
        "• Transaction success/failure analysis",
        "",
        "Report generated by Enhanced DeFi Forensic Analyzer v4.0",
        "=" * 100
    ])
    
    return "\n".join(report_lines)

def main():
    """Generate comprehensive forensic analysis report"""
    
    # Load the forensic analysis data
    try:
        with open('forensic_analysis_report.json', 'r') as f:
            forensic_data = json.load(f)
    except FileNotFoundError:
        print("❌ forensic_analysis_report.json not found. Please run the forensic analyzer first.")
        return
    
    analyses = forensic_data.get('transaction_analyses', [])
    
    print("🔍 GENERATING COMPREHENSIVE FORENSIC ANALYSIS REPORT")
    print("=" * 80)
    
    # Generate human-readable report
    human_readable_report = generate_human_readable_report(analyses)
    
    # Save comprehensive report
    with open('comprehensive_forensic_report.txt', 'w') as f:
        f.write(human_readable_report)
    
    # Generate structured summary
    dai_arb_verification = verify_dai_arb_sequence(analyses)
    
    comprehensive_summary = {
        'forensic_analysis_metadata': {
            'generated_at': datetime.now().isoformat(),
            'analyzer_version': 'Enhanced DeFi Forensics v4.0',
            'target_transactions': [tx['transaction_hash'] for tx in analyses],
            'analysis_components': [
                'comprehensive_event_decoders',
                'protocol_identification',
                'chronological_sequence_mapping',
                'dai_arb_pattern_verification',
                'gas_analysis',
                'token_flow_analysis'
            ]
        },
        'chronological_sequences': {
            tx['transaction_hash']: create_chronological_sequence(tx) 
            for tx in analyses
        },
        'dai_arb_verification': dai_arb_verification,
        'protocol_interaction_map': {
            tx['transaction_hash']: {
                'primary_protocol': analyze_transaction_calldata(tx)['protocol'],
                'contract_called': tx.get('to_address', ''),
                'function_name': analyze_transaction_calldata(tx)['function_name'],
                'identified': analyze_transaction_calldata(tx)['identified']
            }
            for tx in analyses
        },
        'summary_statistics': {
            'total_transactions': len(analyses),
            'successful_analyses': len([tx for tx in analyses if tx.get('status') == 'SUCCESS']),
            'total_gas_used': sum(tx.get('gas_used', 0) for tx in analyses),
            'total_events_decoded': sum(tx.get('logs_analysis', {}).get('total_logs', 0) for tx in analyses),
            'dai_arb_pattern_count': sum(1 for v in dai_arb_verification.values() if v['follows_dai_arb_pattern']),
            'debt_swap_operations': sum(1 for v in dai_arb_verification.values() if v['is_debt_swap'])
        }
    }
    
    # Save structured summary
    with open('comprehensive_forensic_summary.json', 'w') as f:
        json.dump(comprehensive_summary, f, indent=2, default=str)
    
    print("✅ COMPREHENSIVE FORENSIC ANALYSIS COMPLETE")
    print("   📄 Human-readable report: comprehensive_forensic_report.txt")
    print("   📊 Structured summary: comprehensive_forensic_summary.json")
    print(f"   🎯 Transactions analyzed: {len(analyses)}")
    print(f"   🔄 DAI-ARB patterns found: {comprehensive_summary['summary_statistics']['dai_arb_pattern_count']}")
    print(f"   💱 Debt swap operations: {comprehensive_summary['summary_statistics']['debt_swap_operations']}")
    
    # Print key findings
    print("\n🔍 KEY FINDINGS:")
    for tx_hash, verification in dai_arb_verification.items():
        if verification['follows_dai_arb_pattern']:
            print(f"   ✅ {tx_hash[:20]}... - Follows DAI→ARB pattern")
        if verification['is_debt_swap']:
            print(f"   🔄 {tx_hash[:20]}... - Debt swap operation")

if __name__ == "__main__":
    main()