import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from datetime import datetime, timezone

DATABASE_URL = os.environ.get("DATABASE_URL")

@contextmanager
def get_conn():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

@contextmanager
def get_cursor(commit=True):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cur
        finally:
            cur.close()

def init_db():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            wallet_address VARCHAR(42) UNIQUE NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            last_seen TIMESTAMPTZ DEFAULT NOW(),
            bot_enabled BOOLEAN NOT NULL DEFAULT true
        );
        ALTER TABLE users ADD COLUMN IF NOT EXISTS bot_enabled BOOLEAN NOT NULL DEFAULT true;

        CREATE TABLE IF NOT EXISTS towns (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            code VARCHAR(20) NOT NULL,
            base_url TEXT NOT NULL,
            state VARCHAR(2) DEFAULT 'CT',
            county VARCHAR(50) DEFAULT 'Hartford'
        );

        CREATE TABLE IF NOT EXISTS user_towns (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            town_id INTEGER REFERENCES towns(id) ON DELETE CASCADE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(user_id, town_id)
        );

        CREATE TABLE IF NOT EXISTS filings (
            id SERIAL PRIMARY KEY,
            town_id INTEGER REFERENCES towns(id) ON DELETE CASCADE,
            property_address TEXT,
            seller TEXT,
            lender TEXT,
            recording_date DATE,
            book_page VARCHAR(100),
            original_mortgage TEXT,
            court_case_number VARCHAR(100),
            debt_amount VARCHAR(100),
            return_date VARCHAR(100),
            status VARCHAR(50) DEFAULT 'PENDING',
            raw_data JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS defi_positions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            health_factor NUMERIC(12,4),
            total_collateral_usd NUMERIC(14,2),
            total_debt_usd NUMERIC(14,2),
            net_worth_usd NUMERIC(14,2),
            positions JSONB DEFAULT '{}',
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS income_events (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            event_type VARCHAR(50) NOT NULL,
            amount_usd NUMERIC(14,4),
            token VARCHAR(20),
            tx_hash VARCHAR(66),
            description TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS lead_notes (
            id SERIAL PRIMARY KEY,
            filing_id INTEGER REFERENCES filings(id) ON DELETE CASCADE,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            note_type VARCHAR(50) DEFAULT 'analysis',
            content TEXT NOT NULL,
            priority VARCHAR(20) DEFAULT 'medium',
            created_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS pipeline_runs (
            id SERIAL PRIMARY KEY,
            run_type VARCHAR(50) NOT NULL,
            started_at TIMESTAMPTZ DEFAULT NOW(),
            completed_at TIMESTAMPTZ,
            towns_scraped INTEGER DEFAULT 0,
            filings_found INTEGER DEFAULT 0,
            status VARCHAR(20) DEFAULT 'running',
            details JSONB DEFAULT '{}',
            error_message TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_filings_town ON filings(town_id);
        CREATE INDEX IF NOT EXISTS idx_filings_date ON filings(recording_date);
        CREATE INDEX IF NOT EXISTS idx_filings_status ON filings(status);
        CREATE INDEX IF NOT EXISTS idx_user_towns_user ON user_towns(user_id);
        CREATE INDEX IF NOT EXISTS idx_lead_notes_filing ON lead_notes(filing_id);
        CREATE INDEX IF NOT EXISTS idx_income_events_user ON income_events(user_id);
        CREATE INDEX IF NOT EXISTS idx_defi_positions_user ON defi_positions(user_id);

        CREATE TABLE IF NOT EXISTS managed_wallets (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            wallet_address TEXT NOT NULL,
            delegation_status TEXT NOT NULL DEFAULT 'none',
            auto_supply_wbtc BOOLEAN NOT NULL DEFAULT false,
            supplied_wbtc_amount NUMERIC DEFAULT 0,
            last_auto_supply_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(user_id, wallet_address)
        );

        CREATE TABLE IF NOT EXISTS wallet_actions (
            id BIGSERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            wallet_address TEXT NOT NULL,
            action_type TEXT NOT NULL,
            details JSONB NOT NULL DEFAULT '{}',
            tx_hash TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_managed_wallets_active
            ON managed_wallets(delegation_status) WHERE delegation_status = 'active';
        CREATE INDEX IF NOT EXISTS idx_wallet_actions_user
            ON wallet_actions(user_id, created_at DESC);
        """)
        cur.close()

def seed_towns():
    towns = [
        ("Hartford", "CTHAR", "https://www.searchiqs.com/CTHAR"),
        ("East Hartford", "CTEHA", "https://www.searchiqs.com/CTEHA"),
        ("Windsor", "CTWIN", "https://www.searchiqs.com/CTWIN"),
        ("Berlin", "CTBER", "https://www.searchiqs.com/CTBER"),
        ("Rocky Hill", "CTROC", "https://www.searchiqs.com/CTROC"),
    ]
    with get_conn() as conn:
        cur = conn.cursor()
        for name, code, base_url in towns:
            cur.execute("""
                INSERT INTO towns (name, code, base_url)
                VALUES (%s, %s, %s)
                ON CONFLICT (name) DO UPDATE SET code=EXCLUDED.code, base_url=EXCLUDED.base_url
            """, (name, code, base_url))
        cur.close()


def upsert_user(wallet_address):
    wallet_address = wallet_address.lower().strip()
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            INSERT INTO users (wallet_address, last_seen)
            VALUES (%s, NOW())
            ON CONFLICT (wallet_address) DO UPDATE SET last_seen = NOW()
            RETURNING id, wallet_address, created_at, last_seen
        """, (wallet_address,))
        user = cur.fetchone()
        cur.close()
        return dict(user)


def get_user_by_wallet(wallet_address):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users WHERE wallet_address = %s", (wallet_address.lower().strip(),))
        row = cur.fetchone()
        cur.close()
        return dict(row) if row else None


def get_user_by_id(user_id):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
        return dict(row) if row else None


def set_bot_enabled(user_id, enabled: bool):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET bot_enabled = %s WHERE id = %s",
                (enabled, user_id),
            )


def is_bot_enabled(user_id) -> bool:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT bot_enabled FROM users WHERE id = %s",
                (user_id,)
            )
            row = cur.fetchone()
            return bool(row[0]) if row else False


def get_towns():
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT t.*, COALESCE(fc.cnt, 0) AS filing_count
            FROM towns t
            LEFT JOIN (SELECT town_id, COUNT(*) AS cnt FROM filings GROUP BY town_id) fc
            ON t.id = fc.town_id
            ORDER BY t.name
        """)
        rows = cur.fetchall()
        cur.close()
        return [dict(r) for r in rows]


def get_user_towns(user_id):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT t.* FROM towns t
            JOIN user_towns ut ON ut.town_id = t.id
            WHERE ut.user_id = %s ORDER BY t.name
        """, (user_id,))
        rows = cur.fetchall()
        cur.close()
        return [dict(r) for r in rows]


def set_user_towns(user_id, town_ids):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM user_towns WHERE user_id = %s", (user_id,))
        for tid in town_ids:
            cur.execute("INSERT INTO user_towns (user_id, town_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (user_id, tid))
        cur.close()


def insert_filing(town_id, data):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        rec_date = data.get("recording_date") or data.get("recording_date_detail")
        parsed_date = None
        if rec_date:
            for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y"):
                try:
                    parsed_date = datetime.strptime(rec_date.strip(), fmt).date()
                    break
                except (ValueError, AttributeError):
                    continue
        cur.execute("""
            INSERT INTO filings (town_id, property_address, seller, lender, recording_date,
                book_page, original_mortgage, court_case_number, debt_amount, return_date, status, raw_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            town_id,
            data.get("property_address") or data.get("property_description", "SEE DEED"),
            data.get("seller") or data.get("party1_seller", ""),
            data.get("lender") or data.get("party2_lender", ""),
            parsed_date,
            data.get("book_page", ""),
            data.get("original_mortgage") or data.get("additional_description", ""),
            data.get("court_case_number", ""),
            data.get("debt_amount", ""),
            data.get("return_date", ""),
            data.get("status", "PENDING"),
            psycopg2.extras.Json(data),
        ))
        row = cur.fetchone()
        cur.close()
        return row["id"]


def get_filings(town_id=None, date_from=None, date_to=None, status=None, page=1, per_page=50):
    conditions = []
    params = []
    if town_id:
        conditions.append("f.town_id = %s")
        params.append(town_id)
    if date_from:
        conditions.append("f.recording_date >= %s")
        params.append(date_from)
    if date_to:
        conditions.append("f.recording_date <= %s")
        params.append(date_to)
    if status:
        conditions.append("f.status = %s")
        params.append(status)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    offset = (page - 1) * per_page

    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(f"SELECT COUNT(*) as total FROM filings f {where}", params)
        total = cur.fetchone()["total"]

        cur.execute(f"""
            SELECT f.*, t.name as town_name
            FROM filings f
            JOIN towns t ON t.id = f.town_id
            {where}
            ORDER BY f.recording_date DESC NULLS LAST, f.id DESC
            LIMIT %s OFFSET %s
        """, params + [per_page, offset])
        rows = cur.fetchall()
        cur.close()

        result = []
        for r in rows:
            d = dict(r)
            if d.get("recording_date"):
                d["recording_date"] = d["recording_date"].isoformat()
            if d.get("created_at"):
                d["created_at"] = d["created_at"].isoformat()
            if d.get("updated_at"):
                d["updated_at"] = d["updated_at"].isoformat()
            result.append(d)

        return {"filings": result, "total": total, "page": page, "per_page": per_page, "pages": (total + per_page - 1) // per_page}


def get_filing_stats():
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT t.id as town_id, t.name as town_name, COUNT(f.id) as filing_count,
                MAX(f.recording_date) as latest_filing
            FROM towns t
            LEFT JOIN filings f ON f.town_id = t.id
            GROUP BY t.id, t.name
            ORDER BY t.name
        """)
        rows = cur.fetchall()
        cur.close()
        result = []
        for r in rows:
            d = dict(r)
            if d.get("latest_filing"):
                d["latest_filing"] = d["latest_filing"].isoformat()
            result.append(d)
        return result


def upsert_defi_position(user_id, health_factor, collateral, debt, net_worth, positions=None):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO defi_positions (user_id, health_factor, total_collateral_usd, total_debt_usd, net_worth_usd, positions, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (user_id) DO UPDATE SET
                health_factor = EXCLUDED.health_factor,
                total_collateral_usd = EXCLUDED.total_collateral_usd,
                total_debt_usd = EXCLUDED.total_debt_usd,
                net_worth_usd = EXCLUDED.net_worth_usd,
                positions = EXCLUDED.positions,
                updated_at = NOW()
        """, (user_id, health_factor, collateral, debt, net_worth, psycopg2.extras.Json(positions or {})))
        cur.close()


def get_defi_position(user_id):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM defi_positions WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
        if row:
            d = dict(row)
            if d.get("updated_at"):
                d["updated_at"] = d["updated_at"].isoformat()
            return d
        return None


def add_income_event(user_id, event_type, amount_usd, token=None, tx_hash=None, description=None):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            INSERT INTO income_events (user_id, event_type, amount_usd, token, tx_hash, description)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (user_id, event_type, amount_usd, token, tx_hash, description))
        row = cur.fetchone()
        cur.close()
        return row["id"]


def get_income_events(user_id, limit=50):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT * FROM income_events WHERE user_id = %s
            ORDER BY created_at DESC LIMIT %s
        """, (user_id, limit))
        rows = cur.fetchall()
        cur.close()
        result = []
        for r in rows:
            d = dict(r)
            if d.get("created_at"):
                d["created_at"] = d["created_at"].isoformat()
            result.append(d)
        return result


def add_lead_note(filing_id, content, note_type="analysis", priority="medium", user_id=None):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            INSERT INTO lead_notes (filing_id, user_id, note_type, content, priority)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (filing_id, user_id, note_type, content, priority))
        row = cur.fetchone()
        cur.close()
        return row["id"]


def get_lead_notes(filing_id):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM lead_notes WHERE filing_id = %s ORDER BY created_at DESC", (filing_id,))
        rows = cur.fetchall()
        cur.close()
        result = []
        for r in rows:
            d = dict(r)
            if d.get("created_at"):
                d["created_at"] = d["created_at"].isoformat()
            result.append(d)
        return result


def create_pipeline_run(run_type):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            INSERT INTO pipeline_runs (run_type) VALUES (%s) RETURNING id
        """, (run_type,))
        row = cur.fetchone()
        cur.close()
        return row["id"]


def complete_pipeline_run(run_id, towns_scraped, filings_found, status="completed", details=None, error=None):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE pipeline_runs SET completed_at = NOW(), towns_scraped = %s, filings_found = %s,
                status = %s, details = %s, error_message = %s
            WHERE id = %s
        """, (towns_scraped, filings_found, status, psycopg2.extras.Json(details or {}), error, run_id))
        cur.close()


def get_latest_pipeline_run():
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM pipeline_runs ORDER BY started_at DESC LIMIT 1")
        row = cur.fetchone()
        cur.close()
        if row:
            d = dict(row)
            for k in ("started_at", "completed_at"):
                if d.get(k):
                    d[k] = d[k].isoformat()
            return d
        return None


def clear_filings_for_town(town_id):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM filings WHERE town_id = %s", (town_id,))
        cur.close()


def get_leads_summary():
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT
                COUNT(*) as total_filings,
                COUNT(CASE WHEN ln.priority = 'high' THEN 1 END) as high_priority,
                COUNT(CASE WHEN ln.priority = 'medium' THEN 1 END) as medium_priority,
                COUNT(CASE WHEN ln.priority = 'low' THEN 1 END) as low_priority,
                COUNT(DISTINCT ln.filing_id) as filings_with_notes
            FROM filings f
            LEFT JOIN lead_notes ln ON ln.filing_id = f.id
        """)
        row = cur.fetchone()
        cur.close()
        return dict(row) if row else {}


def get_income_summary(user_id):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN created_at >= NOW() - INTERVAL '30 days' THEN amount_usd ELSE 0 END), 0) AS total_30d,
                COUNT(CASE WHEN created_at >= NOW() - INTERVAL '30 days' THEN 1 END) AS count_30d,
                COALESCE(SUM(CASE WHEN created_at >= NOW() - INTERVAL '60 days' AND created_at < NOW() - INTERVAL '30 days' THEN amount_usd ELSE 0 END), 0) AS total_prev_30d
            FROM income_events WHERE user_id = %s
        """, (user_id,))
        row = cur.fetchone()
        cur.close()
        return dict(row) if row else {"total_30d": 0, "count_30d": 0, "total_prev_30d": 0}


def get_recent_filings_for_towns(town_ids, limit=5):
    if not town_ids:
        return []
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        placeholders = ','.join(['%s'] * len(town_ids))
        cur.execute(f"""
            SELECT f.property_address, f.seller, f.recording_date, t.name as town_name
            FROM filings f JOIN towns t ON t.id = f.town_id
            WHERE f.town_id IN ({placeholders})
            ORDER BY f.recording_date DESC NULLS LAST, f.id DESC
            LIMIT %s
        """, town_ids + [limit])
        rows = cur.fetchall()
        cur.close()
        result = []
        for r in rows:
            d = dict(r)
            if d.get("recording_date"):
                d["recording_date"] = d["recording_date"].isoformat()
            result.append(d)
        return result


def upsert_managed_wallet(user_id, wallet_address, auto_supply_wbtc=False):
    wallet_address = wallet_address.lower().strip()
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            INSERT INTO managed_wallets (user_id, wallet_address, delegation_status, auto_supply_wbtc)
            VALUES (%s, %s, 'none', %s)
            ON CONFLICT (user_id, wallet_address) DO UPDATE SET
                auto_supply_wbtc = EXCLUDED.auto_supply_wbtc,
                updated_at = NOW()
            RETURNING *
        """, (user_id, wallet_address, auto_supply_wbtc))
        row = cur.fetchone()
        cur.close()
        return dict(row) if row else None


def update_delegation_status(user_id, wallet_address, status):
    wallet_address = wallet_address.lower().strip()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE managed_wallets
            SET delegation_status = %s, updated_at = NOW()
            WHERE user_id = %s AND wallet_address = %s
        """, (status, user_id, wallet_address))
        cur.close()


def record_wallet_action(user_id, wallet_address, action_type, details, tx_hash=None):
    wallet_address = wallet_address.lower().strip()
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            INSERT INTO wallet_actions (user_id, wallet_address, action_type, details, tx_hash)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
        """, (user_id, wallet_address, action_type, json.dumps(details), tx_hash))
        row = cur.fetchone()
        cur.close()
        return dict(row) if row else None


def get_managed_wallet(user_id, wallet_address):
    wallet_address = wallet_address.lower().strip()
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT * FROM managed_wallets
            WHERE user_id = %s AND wallet_address = %s
        """, (user_id, wallet_address))
        row = cur.fetchone()
        cur.close()
        return dict(row) if row else None


def get_active_managed_wallets():
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT mw.*, u.bot_enabled
            FROM managed_wallets mw
            JOIN users u ON u.id = mw.user_id
            WHERE mw.delegation_status = 'active'
              AND mw.auto_supply_wbtc = true
              AND u.bot_enabled = true
        """)
        rows = cur.fetchall()
        cur.close()
        return [dict(r) for r in rows]


def update_managed_wallet_supplied(user_id, wallet_address, amount_wbtc):
    wallet_address = wallet_address.lower().strip()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE managed_wallets
            SET supplied_wbtc_amount = supplied_wbtc_amount + %s,
                last_auto_supply_at = NOW(),
                updated_at = NOW()
            WHERE user_id = %s AND wallet_address = %s
        """, (amount_wbtc, user_id, wallet_address))
        cur.close()


def get_last_wallet_action(user_id, wallet_address, action_type=None):
    wallet_address = wallet_address.lower().strip()
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        if action_type:
            cur.execute("""
                SELECT * FROM wallet_actions
                WHERE user_id = %s AND wallet_address = %s AND action_type = %s
                ORDER BY created_at DESC LIMIT 1
            """, (user_id, wallet_address, action_type))
        else:
            cur.execute("""
                SELECT * FROM wallet_actions
                WHERE user_id = %s AND wallet_address = %s
                ORDER BY created_at DESC LIMIT 1
            """, (user_id, wallet_address))
        row = cur.fetchone()
        cur.close()
        if row:
            d = dict(row)
            if d.get('created_at'):
                d['created_at'] = d['created_at'].isoformat()
            return d
        return None


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Seeding towns...")
    seed_towns()
    print("Database ready.")
