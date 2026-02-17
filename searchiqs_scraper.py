import os
import re
import json
import logging
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

SEARCHIQS_BASE_URL = "https://www.searchiqs.com/CTHAR"
SEARCHIQS_SEARCH_URL = f"{SEARCHIQS_BASE_URL}/SearchAdvancedMP.aspx"
SEARCHIQS_GUEST_URL = f"{SEARCHIQS_BASE_URL}/Default.aspx"
CT_COURT_URL = "https://civilinquiry.jud.ct.gov"


class SearchIQSScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        self.logged_in = False

    def login_as_guest(self) -> bool:
        try:
            logger.info("Logging into SearchIQS as guest (Hartford)...")
            resp = self.session.get(SEARCHIQS_GUEST_URL, timeout=30)
            resp.raise_for_status()

            viewstate = self._extract_field(resp.text, "__VIEWSTATE")
            viewstategenerator = self._extract_field(resp.text, "__VIEWSTATEGENERATOR")
            eventvalidation = self._extract_field(resp.text, "__EVENTVALIDATION")

            login_data = {
                "__VIEWSTATE": viewstate,
                "__VIEWSTATEGENERATOR": viewstategenerator,
                "__EVENTVALIDATION": eventvalidation,
                "ctl00$ContentPlaceHolder1$btnGuest": "Guest",
            }

            resp2 = self.session.post(SEARCHIQS_GUEST_URL, data=login_data, timeout=30, allow_redirects=True)
            if resp2.status_code == 200 and ("Search" in resp2.text or "Advanced" in resp2.text):
                self.logged_in = True
                logger.info("SearchIQS guest login successful")
                return True
            else:
                logger.warning(f"SearchIQS login may have failed (status: {resp2.status_code})")
                self.logged_in = True
                return True
        except Exception as e:
            logger.error(f"SearchIQS login failed: {e}")
            return False

    def search_lis_pendens(self, days_back: int = 3) -> List[Dict]:
        if not self.logged_in:
            if not self.login_as_guest():
                return []

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        date_from = start_date.strftime("%m/%d/%Y")
        date_to = end_date.strftime("%m/%d/%Y")

        logger.info(f"Searching Lis Pendens from {date_from} to {date_to}")

        try:
            resp = self.session.get(SEARCHIQS_SEARCH_URL, timeout=30)
            resp.raise_for_status()

            viewstate = self._extract_field(resp.text, "__VIEWSTATE")
            viewstategenerator = self._extract_field(resp.text, "__VIEWSTATEGENERATOR")
            eventvalidation = self._extract_field(resp.text, "__EVENTVALIDATION")

            search_data = {
                "__VIEWSTATE": viewstate,
                "__VIEWSTATEGENERATOR": viewstategenerator,
                "__EVENTVALIDATION": eventvalidation,
                "ctl00$ContentPlaceHolder1$ddlDocType": "LIS PENDENS",
                "ctl00$ContentPlaceHolder1$txtFromDate": date_from,
                "ctl00$ContentPlaceHolder1$txtToDate": date_to,
                "ctl00$ContentPlaceHolder1$btnSearch": "Search",
            }

            resp2 = self.session.post(SEARCHIQS_SEARCH_URL, data=search_data, timeout=60, allow_redirects=True)
            resp2.raise_for_status()

            results = self._parse_search_results(resp2.text)
            logger.info(f"Found {len(results)} Lis Pendens filings")
            return results

        except Exception as e:
            logger.error(f"SearchIQS search failed: {e}")
            return []

    def _parse_search_results(self, html: str) -> List[Dict]:
        results = []

        row_pattern = re.compile(
            r'<tr[^>]*class="(?:GridRow|GridAltRow)"[^>]*>(.*?)</tr>',
            re.DOTALL | re.IGNORECASE
        )
        cell_pattern = re.compile(r'<td[^>]*>(.*?)</td>', re.DOTALL | re.IGNORECASE)
        tag_cleaner = re.compile(r'<[^>]+>')

        rows = row_pattern.findall(html)

        for row in rows:
            cells = cell_pattern.findall(row)
            cleaned = [tag_cleaner.sub('', c).strip() for c in cells]

            if len(cleaned) >= 4:
                result = {
                    "recording_date": cleaned[0] if len(cleaned) > 0 else "",
                    "doc_type": cleaned[1] if len(cleaned) > 1 else "LIS PENDENS",
                    "book_page": cleaned[2] if len(cleaned) > 2 else "",
                    "parties": cleaned[3] if len(cleaned) > 3 else "",
                    "plaintiff": "",
                    "defendant": "",
                    "property_address": "",
                }

                parties = result["parties"]
                if " VS " in parties.upper():
                    parts = re.split(r'\s+VS?\s+', parties, flags=re.IGNORECASE)
                    result["plaintiff"] = parts[0].strip()
                    result["defendant"] = parts[1].strip() if len(parts) > 1 else ""
                elif " V " in parties.upper():
                    parts = re.split(r'\s+V\s+', parties, flags=re.IGNORECASE)
                    result["plaintiff"] = parts[0].strip()
                    result["defendant"] = parts[1].strip() if len(parts) > 1 else ""

                if len(cleaned) > 4:
                    result["property_address"] = cleaned[4]

                results.append(result)

        if not results and "No records found" not in html:
            logger.info("No table rows matched, attempting alternate parse...")
            text_blocks = re.findall(r'LIS\s+PENDENS.*?(?=LIS\s+PENDENS|$)', html, re.DOTALL | re.IGNORECASE)
            for block in text_blocks[:20]:
                date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', block)
                result = {
                    "recording_date": date_match.group(1) if date_match else "",
                    "doc_type": "LIS PENDENS",
                    "book_page": "",
                    "parties": tag_cleaner.sub('', block[:200]).strip(),
                    "plaintiff": "",
                    "defendant": "",
                    "property_address": "",
                }
                results.append(result)

        return results

    def search_court_case(self, party_name: str) -> Optional[Dict]:
        try:
            search_url = f"{CT_COURT_URL}/CaseSearch"
            resp = self.session.get(search_url, params={
                "partyName": party_name,
                "caseType": "FC",
            }, timeout=30)

            if resp.status_code == 200:
                case_match = re.search(r'(HHD-CV\d{2}-\d+)', resp.text)
                debt_match = re.search(r'\$[\d,]+\.?\d*', resp.text)
                date_match = re.search(r'Return Date:?\s*(\d{1,2}/\d{1,2}/\d{4})', resp.text)
                status_match = re.search(r'Status:?\s*([A-Za-z\s]+)', resp.text)

                return {
                    "case_number": case_match.group(1) if case_match else "Not found",
                    "debt_amount": debt_match.group(0) if debt_match else "Unknown",
                    "return_date": date_match.group(1) if date_match else "TBD",
                    "status": status_match.group(1).strip() if status_match else "Pending",
                }

            return None
        except Exception as e:
            logger.warning(f"Court case search failed for {party_name}: {e}")
            return None

    def _extract_field(self, html: str, field_name: str) -> str:
        pattern = rf'id="{field_name}"[^>]*value="([^"]*)"'
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            return match.group(1)
        pattern2 = rf'name="{field_name}"[^>]*value="([^"]*)"'
        match2 = re.search(pattern2, html, re.IGNORECASE)
        return match2.group(1) if match2 else ""


_scraper = None

def get_scraper() -> SearchIQSScraper:
    global _scraper
    if _scraper is None:
        _scraper = SearchIQSScraper()
    return _scraper


logger.info("SearchIQS scraper module loaded")
