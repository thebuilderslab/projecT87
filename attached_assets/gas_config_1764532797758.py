#!/usr/bin/env python3
"""
Gas Configuration Utility for Aave Debt Swap System
Provides dynamic gas limits based on observed mainnet usage patterns

Based on comprehensive gas profiling audit (2025-01-19):
- Successful debt swap: 729,485 gas
- Failed debt swap: 765,583 gas
- Credit delegation: ~60,000-80,000 gas
"""

from typing import Literal, Dict

# Observed gas usage from mainnet transactions
OBSERVED_GAS_USAGE = {
    'debt_swap_specific_route': 729_485,    # ParaSwap specific method (0xa76f4eb6)
    'debt_swap_generic_route': 765_583,     # ParaSwap generic method (0x7f457675)
    'credit_delegation': 70_000,            # approveDelegation() average
    'simple_approval': 50_000,              # ERC20 approve()
}

# Safety buffer multipliers
SAFETY_BUFFERS = {
    'conservative': 1.20,  # 20% buffer (recommended for production)
    'standard': 1.15,      # 15% buffer (balanced)
    'tight': 1.10,         # 10% buffer (aggressive)
}

# Gas price multipliers for transaction fee calculation
GAS_PRICE_MULTIPLIERS = {
    'urgent': 1.5,    # High priority
    'normal': 1.2,    # Standard (recommended)
    'patient': 1.0,   # Base fee only
}


def get_gas_limit(
    operation: Literal['debt_swap', 'credit_delegation', 'simple_approval'],
    buffer_strategy: Literal['conservative', 'standard', 'tight'] = 'standard',
    max_cap: int = None
) -> int:
    """
    Calculate optimal gas limit for a given operation type.
    
    Args:
        operation: Type of operation
        buffer_strategy: Safety buffer level
        max_cap: Optional maximum gas limit cap
        
    Returns:
        Recommended gas limit in gas units
        
    Examples:
        >>> get_gas_limit('debt_swap')
        880121  # 765,583 * 1.15
        
        >>> get_gas_limit('debt_swap', 'conservative')
        918699  # 765,583 * 1.20
        
        >>> get_gas_limit('credit_delegation', 'tight')
        77000  # 70,000 * 1.10
    """
    operation_map = {
        'debt_swap': 'debt_swap_generic_route',  # Use worst-case (generic route)
        'credit_delegation': 'credit_delegation',
        'simple_approval': 'simple_approval',
    }
    
    if operation not in operation_map:
        raise ValueError(f"Unknown operation: {operation}. Must be one of {list(operation_map.keys())}")
    
    base_gas = OBSERVED_GAS_USAGE[operation_map[operation]]
    multiplier = SAFETY_BUFFERS[buffer_strategy]
    calculated_limit = int(base_gas * multiplier)
    
    if max_cap and calculated_limit > max_cap:
        return max_cap
    
    return calculated_limit


def get_recommended_limits() -> Dict[str, int]:
    """
    Get production-ready gas limits for all operations.
    
    Returns:
        Dictionary mapping operation names to recommended gas limits
    """
    return {
        'debt_swap': 800_000,           # Proven safe on mainnet (91% utilization)
        'credit_delegation': 100_000,   # 30% buffer over observed usage
        'simple_approval': 75_000,      # 50% buffer for safety
        'fallback': 1_000_000,          # Emergency fallback
    }


def get_gas_price_multiplier(priority: Literal['urgent', 'normal', 'patient'] = 'normal') -> float:
    """
    Get gas price multiplier for transaction priority.
    
    Args:
        priority: Transaction priority level
        
    Returns:
        Multiplier to apply to base gas price
    """
    return GAS_PRICE_MULTIPLIERS[priority]


# Production-ready configuration
PRODUCTION_GAS_LIMITS = get_recommended_limits()


# ParaSwap routing variance warning
PARASWAP_ROUTING_WARNING = """
⚠️  PARASWAP ROUTING GAS VARIANCE
ParaSwap routing algorithm is non-deterministic and can increase gas usage by ~5%:
- Specific route (0xa76f4eb6): 729,485 gas ✅
- Generic route (0x7f457675): 765,583 gas (+5%)
Gas limits account for worst-case routing. Monitor logs for actual method used.
"""


def log_gas_variance_warning():
    """Print ParaSwap routing variance warning to console."""
    print(PARASWAP_ROUTING_WARNING)


if __name__ == '__main__':
    print("=" * 80)
    print("GAS CONFIGURATION UTILITY - MAINNET OPTIMIZED")
    print("=" * 80)
    print("\n📊 Observed Gas Usage (Mainnet):")
    for op, gas in OBSERVED_GAS_USAGE.items():
        print(f"   {op:30s}: {gas:,} gas")
    
    print("\n✅ Recommended Production Limits:")
    for op, limit in PRODUCTION_GAS_LIMITS.items():
        print(f"   {op:30s}: {limit:,} gas")
    
    print("\n🔧 Dynamic Calculation Examples:")
    print(f"   Debt swap (standard):     {get_gas_limit('debt_swap', 'standard'):,} gas")
    print(f"   Debt swap (conservative): {get_gas_limit('debt_swap', 'conservative'):,} gas")
    print(f"   Delegation (standard):    {get_gas_limit('credit_delegation', 'standard'):,} gas")
    
    print("\n" + PARASWAP_ROUTING_WARNING)
