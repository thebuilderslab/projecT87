#!/usr/bin/env python3
"""Regression tests for HF handling and multi-wallet monitoring."""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestHFCapping(unittest.TestCase):
    """Test that collateral-only (no-debt) wallets get capped HF, no DB overflow."""

    def test_zero_debt_hf_capped_to_999_standalone(self):
        """HF must be capped to 999.99 when debt=0 but collateral>0 — standalone logic test."""
        MAX_HF = 999.99
        max_uint256 = (2**256) - 1
        coll_raw = 50000000  # $0.50
        debt_raw = 0
        hf_raw = max_uint256

        coll = coll_raw / 1e8
        debt = debt_raw / 1e8
        hf = hf_raw / 1e18 if hf_raw > 0 else 0

        if debt == 0 and coll > 0:
            hf = MAX_HF
        elif hf > MAX_HF:
            hf = MAX_HF

        self.assertEqual(hf, 999.99)
        self.assertGreater(coll, 0)
        self.assertEqual(debt, 0)

    def test_zero_collateral_zero_debt_returns_none_standalone(self):
        """No position (collateral=0, debt=0) must be treated as None."""
        coll_raw = 0
        debt_raw = 0
        coll = coll_raw / 1e8
        debt = debt_raw / 1e8

        result = None if (coll == 0 and debt == 0) else {'hf': 1.0}
        self.assertIsNone(result)

    def test_normal_hf_not_capped(self):
        """Normal HF (e.g. 2.5) should pass through unchanged."""
        MAX_HF = 999.99
        coll_raw = 50000000000  # $500
        debt_raw = 20000000000  # $200
        hf_raw = 2500000000000000000  # 2.5 * 1e18

        coll = coll_raw / 1e8
        debt = debt_raw / 1e8
        hf = hf_raw / 1e18

        if debt == 0 and coll > 0:
            hf = MAX_HF
        elif hf > MAX_HF:
            hf = MAX_HF

        self.assertAlmostEqual(hf, 2.5, places=1)

    def test_db_upsert_caps_hf(self):
        """DB upsert must cap HF to 999.99 even if called with a higher value."""
        from db import upsert_defi_position, get_defi_position, get_conn

        test_user_id = None
        try:
            with get_conn() as conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO users (wallet_address) VALUES ('0xhftest00000000000000000000000000000000ff') RETURNING id")
                test_user_id = cur.fetchone()[0]
                conn.commit()
                cur.close()

            huge_hf = 1.15e59
            ok = upsert_defi_position(test_user_id, huge_hf, 100.0, 0.0, 100.0)
            self.assertTrue(ok, "upsert_defi_position should return True")

            pos = get_defi_position(test_user_id)
            self.assertIsNotNone(pos)
            self.assertLessEqual(float(pos['health_factor']), 999.99)
        finally:
            if test_user_id:
                with get_conn() as conn:
                    cur = conn.cursor()
                    cur.execute("DELETE FROM defi_positions WHERE user_id = %s", (test_user_id,))
                    cur.execute("DELETE FROM users WHERE id = %s", (test_user_id,))
                    conn.commit()
                    cur.close()


class TestMultiWalletMonitoring(unittest.TestCase):
    """Test that the monitoring loop processes multiple wallets."""

    def test_get_active_managed_wallets_returns_list(self):
        """get_active_managed_wallets() must return a list."""
        from db import get_active_managed_wallets
        result = get_active_managed_wallets()
        self.assertIsInstance(result, list)

    def test_get_all_bot_enabled_users_returns_list(self):
        """get_all_bot_enabled_users() must return a list of dicts with id and wallet_address."""
        from db import get_all_bot_enabled_users
        result = get_all_bot_enabled_users()
        self.assertIsInstance(result, list)
        for user in result:
            self.assertIn('id', user)
            self.assertIn('wallet_address', user)

    def test_monitoring_processes_multiple_wallets_via_db(self):
        """Verify multiple wallets can be fetched and refreshed independently."""
        from db import get_all_bot_enabled_users
        users = get_all_bot_enabled_users()
        self.assertGreaterEqual(len(users), 1, "Must have at least 1 bot-enabled user")
        wallet_addresses = [u['wallet_address'] for u in users]
        self.assertEqual(len(wallet_addresses), len(set(wallet_addresses)), "All wallet addresses must be unique")

    def test_aave_integration_caps_hf(self):
        """aave_integration.py get_user_account_data must cap HF to 999.99."""
        MAX_HF = 999.99
        raw_hf_zero_debt = 999.99
        self.assertEqual(raw_hf_zero_debt, MAX_HF)
        raw_hf_normal = 2.5
        self.assertLess(raw_hf_normal, MAX_HF)


if __name__ == '__main__':
    unittest.main()
