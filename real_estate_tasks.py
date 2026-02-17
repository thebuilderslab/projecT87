import os
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from zoneinfo import ZoneInfo
    EASTERN = ZoneInfo('America/New_York')
except ImportError:
    from datetime import timezone
    EASTERN = timezone(timedelta(hours=-5))

from config import REAL_ESTATE_CONFIG, PERPLEXITY_CONFIG
from perplexity_client import (
    perplexity_chat,
    generate_case_law_summary,
    generate_property_analysis,
    generate_outreach_letters,
)
from searchiqs_scraper import get_scraper
from google_client import get_google_client

RE_STATE_FILE = "real_estate_state.json"


def _load_state() -> Dict:
    try:
        if os.path.exists(RE_STATE_FILE):
            with open(RE_STATE_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load RE state: {e}")
    return {
        "last_ingest": None,
        "last_analysis": None,
        "last_reviews": None,
        "last_outreach": None,
        "filings_today": 0,
        "leads_high": 0,
        "leads_med": 0,
        "leads_low": 0,
        "reviews_generated": 0,
        "letters_queued": 0,
        "raw_filings": [],
        "analyzed_leads": [],
        "errors": [],
    }


def _save_state(state: Dict):
    try:
        with open(RE_STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Failed to save RE state: {e}")


def run_0700_searchiqs_ingest() -> Dict:
    logger.info("=== PHASE 1: Data Collection (7:00 AM) ===")
    state = _load_state()
    result = {"task": "searchiqs_ingest", "status": "started", "timestamp": datetime.now(EASTERN).isoformat()}

    try:
        scraper = get_scraper()
        lookback = REAL_ESTATE_CONFIG.get("lookback_days", 3)
        filings = scraper.search_lis_pendens(days_back=lookback)

        state["raw_filings"] = filings
        state["filings_today"] = len(filings)
        state["last_ingest"] = datetime.now(EASTERN).isoformat()

        google = get_google_client()
        spreadsheet_id = os.getenv("RE_RAW_DATA_SHEET_ID")
        if spreadsheet_id and google.credentials:
            rows = []
            for f in filings:
                rows.append([
                    f.get("recording_date", ""),
                    f.get("doc_type", "LIS PENDENS"),
                    f.get("book_page", ""),
                    f.get("plaintiff", ""),
                    f.get("defendant", ""),
                    f.get("property_address", ""),
                    f.get("parties", ""),
                    datetime.now(EASTERN).strftime("%Y-%m-%d %H:%M"),
                ])
            if rows:
                google.append_rows(spreadsheet_id, "RawData", rows)
                logger.info(f"Wrote {len(rows)} rows to Raw Data sheet")

        for filing in filings:
            defendant = filing.get("defendant", "")
            if defendant:
                court_info = scraper.search_court_case(defendant)
                if court_info:
                    filing["court_case"] = court_info
                    logger.info(f"Found court case for {defendant}: {court_info.get('case_number', 'N/A')}")
                time.sleep(1)

        state["raw_filings"] = filings
        _save_state(state)

        result["status"] = "success"
        result["filings_found"] = len(filings)
        result["message"] = f"Scraped {len(filings)} Lis Pendens filings from Hartford"
        logger.info(f"Phase 1 complete: {len(filings)} filings found")

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        state["errors"].append({"task": "ingest", "error": str(e), "time": datetime.now(EASTERN).isoformat()})
        _save_state(state)
        logger.error(f"Phase 1 error: {e}")

    return result


def run_0730_analysis() -> Dict:
    logger.info("=== PHASE 2: Analysis (7:30 AM) ===")
    state = _load_state()
    result = {"task": "analysis", "status": "started", "timestamp": datetime.now(EASTERN).isoformat()}

    try:
        filings = state.get("raw_filings", [])
        if not filings:
            result["status"] = "skipped"
            result["message"] = "No filings to analyze"
            return result

        equity_high = REAL_ESTATE_CONFIG["equity_thresholds"]["high"]
        equity_med = REAL_ESTATE_CONFIG["equity_thresholds"]["medium"]
        rehab_pct = REAL_ESTATE_CONFIG["rehab_cost_pct"]
        closing = REAL_ESTATE_CONFIG["closing_costs"]

        analyzed = []
        for filing in filings:
            address = filing.get("property_address", "")
            defendant = filing.get("defendant", "")
            court = filing.get("court_case", {})
            debt_str = court.get("debt_amount", "0")
            debt_amount = float(debt_str.replace("$", "").replace(",", "")) if debt_str and debt_str != "Unknown" else 0

            system_prompt = (
                "You are a CT real estate data analyst. Given a property address, "
                "estimate the current market value based on recent comparable sales. "
                "Return ONLY a JSON object: {\"estimated_value\": NUMBER, \"confidence\": \"high\"|\"medium\"|\"low\", \"comps_summary\": \"brief text\"}"
            )
            user_prompt = f"Property address: {address or defendant}, Hartford CT. Estimate current market value."

            try:
                value_response = perplexity_chat(system_prompt, user_prompt, max_tokens=500)
                try:
                    value_data = json.loads(value_response.strip().strip('`').strip())
                    market_value = value_data.get("estimated_value", 0)
                except (json.JSONDecodeError, ValueError):
                    import re
                    val_match = re.search(r'\$?([\d,]+)', value_response)
                    market_value = float(val_match.group(1).replace(",", "")) if val_match else 0
            except Exception as e:
                logger.warning(f"Value estimate failed for {address}: {e}")
                market_value = 0

            rehab_cost = market_value * rehab_pct
            equity = market_value - debt_amount - rehab_cost - closing

            if equity >= equity_high:
                priority = "HIGH"
            elif equity >= equity_med:
                priority = "MED"
            else:
                priority = "LOW"

            lead = {
                "address": address,
                "defendant": defendant,
                "plaintiff": filing.get("plaintiff", ""),
                "recording_date": filing.get("recording_date", ""),
                "market_value": round(market_value, 2),
                "debt_amount": round(debt_amount, 2),
                "rehab_cost": round(rehab_cost, 2),
                "closing_costs": closing,
                "estimated_equity": round(equity, 2),
                "priority": priority,
                "court_case": court.get("case_number", "N/A"),
                "return_date": court.get("return_date", "TBD"),
                "status": court.get("status", "Pending"),
            }

            if address and priority in ("HIGH", "MED"):
                try:
                    analysis = generate_property_analysis(address, market_value, debt_amount, equity)
                    lead["perplexity_analysis"] = analysis
                except Exception as e:
                    logger.warning(f"Property analysis failed for {address}: {e}")
                    lead["perplexity_analysis"] = f"[ERROR] {e}"

            analyzed.append(lead)
            time.sleep(2)

        state["analyzed_leads"] = analyzed
        state["leads_high"] = sum(1 for l in analyzed if l["priority"] == "HIGH")
        state["leads_med"] = sum(1 for l in analyzed if l["priority"] == "MED")
        state["leads_low"] = sum(1 for l in analyzed if l["priority"] == "LOW")
        state["last_analysis"] = datetime.now(EASTERN).isoformat()
        _save_state(state)

        google = get_google_client()
        spreadsheet_id = os.getenv("RE_MASTER_ANALYSIS_SHEET_ID")
        if spreadsheet_id and google.credentials:
            rows = []
            for lead in analyzed:
                rows.append([
                    lead["address"],
                    lead["defendant"],
                    lead["plaintiff"],
                    lead["recording_date"],
                    f"${lead['market_value']:,.0f}",
                    f"${lead['debt_amount']:,.0f}",
                    f"${lead['estimated_equity']:,.0f}",
                    lead["priority"],
                    lead["court_case"],
                    lead["return_date"],
                    lead.get("perplexity_analysis", "")[:500],
                ])
            if rows:
                google.append_rows(spreadsheet_id, "MasterAnalysis", rows)

        result["status"] = "success"
        result["analyzed"] = len(analyzed)
        result["high"] = state["leads_high"]
        result["med"] = state["leads_med"]
        result["low"] = state["leads_low"]
        result["message"] = f"Analyzed {len(analyzed)} leads: {state['leads_high']} HIGH, {state['leads_med']} MED, {state['leads_low']} LOW"
        logger.info(result["message"])

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        state["errors"].append({"task": "analysis", "error": str(e), "time": datetime.now(EASTERN).isoformat()})
        _save_state(state)
        logger.error(f"Phase 2 error: {e}")

    return result


def run_0800_reviews() -> Dict:
    logger.info("=== PHASE 3: Reviews (8:00 AM) ===")
    state = _load_state()
    result = {"task": "reviews", "status": "started", "timestamp": datetime.now(EASTERN).isoformat()}

    try:
        analyzed = state.get("analyzed_leads", [])
        high_leads = [l for l in analyzed if l.get("priority") == "HIGH"]

        if not high_leads:
            result["status"] = "skipped"
            result["message"] = "No HIGH priority leads for review docs"
            state["last_reviews"] = datetime.now(EASTERN).isoformat()
            _save_state(state)
            return result

        google = get_google_client()
        template_id = REAL_ESTATE_CONFIG.get("review_template_doc_id")
        folder_id = REAL_ESTATE_CONFIG.get("google_drive_folder_id")
        reviews_created = 0

        for lead in high_leads:
            address = lead.get("address", "Unknown")
            defendant = lead.get("defendant", "Unknown")

            case_summary = ""
            if lead.get("court_case") and lead["court_case"] != "N/A":
                try:
                    case_summary = generate_case_law_summary(address, lead["court_case"])
                except Exception as e:
                    case_summary = f"[Case law lookup failed: {e}]"

            doc_title = f"REVIEW - {address or defendant} - {datetime.now(EASTERN).strftime('%Y-%m-%d')}"

            if template_id and google.credentials:
                try:
                    doc_id = google.copy_document(template_id, doc_title, folder_id)
                    if doc_id:
                        replacements = {
                            "{{PROPERTY_ADDRESS}}": address or "N/A",
                            "{{OWNER_NAME}}": defendant or "N/A",
                            "{{PLAINTIFF}}": lead.get("plaintiff", "N/A"),
                            "{{MARKET_VALUE}}": f"${lead.get('market_value', 0):,.0f}",
                            "{{DEBT_AMOUNT}}": f"${lead.get('debt_amount', 0):,.0f}",
                            "{{ESTIMATED_EQUITY}}": f"${lead.get('estimated_equity', 0):,.0f}",
                            "{{PRIORITY}}": lead.get("priority", "N/A"),
                            "{{CASE_NUMBER}}": lead.get("court_case", "N/A"),
                            "{{RETURN_DATE}}": lead.get("return_date", "TBD"),
                            "{{CASE_SUMMARY}}": case_summary[:2000],
                            "{{ANALYSIS}}": lead.get("perplexity_analysis", "")[:2000],
                            "{{DATE}}": datetime.now(EASTERN).strftime("%B %d, %Y"),
                        }
                        google.replace_text_in_doc(doc_id, replacements)
                        reviews_created += 1
                        lead["review_doc_id"] = doc_id
                        logger.info(f"Created review doc for {address}: {doc_id}")
                except Exception as e:
                    logger.error(f"Failed to create review for {address}: {e}")
            else:
                doc_id = None
                if google.credentials:
                    try:
                        doc_id = google.create_document(doc_title, folder_id)
                        if doc_id:
                            content = (
                                f"PROPERTY REVIEW\n{'='*50}\n\n"
                                f"Property: {address}\nOwner: {defendant}\n"
                                f"Plaintiff: {lead.get('plaintiff', 'N/A')}\n"
                                f"Market Value: ${lead.get('market_value', 0):,.0f}\n"
                                f"Debt: ${lead.get('debt_amount', 0):,.0f}\n"
                                f"Equity: ${lead.get('estimated_equity', 0):,.0f}\n"
                                f"Priority: {lead.get('priority', 'N/A')}\n"
                                f"Case: {lead.get('court_case', 'N/A')}\n"
                                f"Return Date: {lead.get('return_date', 'TBD')}\n\n"
                                f"CASE SUMMARY\n{'-'*30}\n{case_summary}\n\n"
                                f"ANALYSIS\n{'-'*30}\n{lead.get('perplexity_analysis', 'N/A')}\n"
                            )
                            google.write_document_content(doc_id, content)
                            reviews_created += 1
                            lead["review_doc_id"] = doc_id
                    except Exception as e:
                        logger.error(f"Failed to create plain review: {e}")

            time.sleep(2)

        state["reviews_generated"] = reviews_created
        state["analyzed_leads"] = analyzed
        state["last_reviews"] = datetime.now(EASTERN).isoformat()
        _save_state(state)

        result["status"] = "success"
        result["reviews_created"] = reviews_created
        result["message"] = f"Generated {reviews_created} review documents for {len(high_leads)} HIGH leads"
        logger.info(result["message"])

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        state["errors"].append({"task": "reviews", "error": str(e), "time": datetime.now(EASTERN).isoformat()})
        _save_state(state)
        logger.error(f"Phase 3 error: {e}")

    return result


def run_0830_outreach() -> Dict:
    logger.info("=== PHASE 4: Outreach (8:30 AM) ===")
    state = _load_state()
    result = {"task": "outreach", "status": "started", "timestamp": datetime.now(EASTERN).isoformat()}

    try:
        analyzed = state.get("analyzed_leads", [])
        high_leads = [l for l in analyzed if l.get("priority") == "HIGH"]

        if not high_leads:
            result["status"] = "skipped"
            result["message"] = "No HIGH priority leads for outreach"
            state["last_outreach"] = datetime.now(EASTERN).isoformat()
            _save_state(state)
            return result

        google = get_google_client()
        folder_id = REAL_ESTATE_CONFIG.get("google_drive_folder_id")
        letters_created = 0

        for lead in high_leads:
            address = lead.get("address", "Unknown")
            owner = lead.get("defendant", "Property Owner")
            plaintiff = lead.get("plaintiff", "")
            analysis = lead.get("perplexity_analysis", "")

            try:
                letters = generate_outreach_letters(
                    owner_name=owner,
                    property_address=address,
                    summary=analysis[:500],
                    lender=plaintiff,
                    court_date=lead.get("return_date", "TBD"),
                    years_at_property=0,
                    equity_estimate=max(0, lead.get("estimated_equity", 0)),
                )

                if google.credentials:
                    doc_title = f"LETTERS - {address or owner} - {datetime.now(EASTERN).strftime('%Y-%m-%d')}"
                    doc_id = google.create_document(doc_title, folder_id)
                    if doc_id:
                        google.write_document_content(doc_id, letters)
                        lead["letters_doc_id"] = doc_id
                        letters_created += 1
                        logger.info(f"Created letters doc for {address}: {doc_id}")
                else:
                    letters_created += 1

            except Exception as e:
                logger.error(f"Failed to generate letters for {address}: {e}")

            time.sleep(3)

        state["letters_queued"] = letters_created
        state["last_outreach"] = datetime.now(EASTERN).isoformat()
        _save_state(state)

        result["status"] = "success"
        result["letters_created"] = letters_created
        result["message"] = f"Generated {letters_created} letter sets for {len(high_leads)} HIGH leads"
        logger.info(result["message"])

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        state["errors"].append({"task": "outreach", "error": str(e), "time": datetime.now(EASTERN).isoformat()})
        _save_state(state)
        logger.error(f"Phase 4 error: {e}")

    return result


def get_real_estate_status() -> Dict:
    state = _load_state()
    return {
        "filings_today": state.get("filings_today", 0),
        "leads_high": state.get("leads_high", 0),
        "leads_med": state.get("leads_med", 0),
        "leads_low": state.get("leads_low", 0),
        "reviews_generated": state.get("reviews_generated", 0),
        "letters_queued": state.get("letters_queued", 0),
        "last_ingest": state.get("last_ingest"),
        "last_analysis": state.get("last_analysis"),
        "last_reviews": state.get("last_reviews"),
        "last_outreach": state.get("last_outreach"),
        "errors": state.get("errors", [])[-5:],
        "pipeline_active": True,
    }


def check_and_run_scheduled_tasks() -> Optional[Dict]:
    now = datetime.now(EASTERN)
    current_hour = now.hour
    current_minute = now.minute

    tasks = REAL_ESTATE_CONFIG.get("tasks", {})
    state = _load_state()

    today_str = now.strftime("%Y-%m-%d")

    def already_ran(task_key):
        last_run = state.get(f"last_{task_key.replace('searchiqs_', '')}")
        if not last_run:
            return False
        try:
            last_dt = datetime.fromisoformat(last_run)
            return last_dt.strftime("%Y-%m-%d") == today_str
        except Exception:
            return False

    for task_name, schedule in tasks.items():
        target_hour = schedule["hour"]
        target_minute = schedule["minute"]

        if current_hour == target_hour and abs(current_minute - target_minute) <= 2:
            task_key = task_name
            if task_name == "searchiqs_ingest":
                task_key = "searchiqs_ingest"
                state_key = "ingest"
            elif task_name == "analysis":
                state_key = "analysis"
            elif task_name == "reviews":
                state_key = "reviews"
            elif task_name == "outreach":
                state_key = "outreach"
            else:
                continue

            if already_ran(state_key):
                continue

            logger.info(f"Scheduled task triggered: {task_name} at {current_hour}:{current_minute:02d}")

            if task_name == "searchiqs_ingest":
                return run_0700_searchiqs_ingest()
            elif task_name == "analysis":
                return run_0730_analysis()
            elif task_name == "reviews":
                return run_0800_reviews()
            elif task_name == "outreach":
                return run_0830_outreach()

    return None


logger.info("Real estate tasks module loaded")
