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
SEARCHIQS_VIEW_URL = f"{SEARCHIQS_BASE_URL}/ViewDocument.aspx"
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

    def search_lis_pendens(self, days_back: int = 3, fetch_details: bool = True) -> List[Dict]:
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
            logger.info(f"Found {len(results)} Lis Pendens filings from search results")

            if fetch_details and results:
                for i, result in enumerate(results):
                    view_url = result.get("view_url", "")
                    if view_url:
                        try:
                            details = self._fetch_document_details(view_url)
                            if details:
                                result.update(details)
                                logger.info(f"Fetched details for filing {i+1}/{len(results)}: {result.get('property_address', 'N/A')}")
                        except Exception as e:
                            logger.warning(f"Failed to fetch details for filing {i+1}: {e}")
                        time.sleep(1.5)

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
        link_pattern = re.compile(r'href=["\']([^"\']*ViewDocument[^"\']*)["\']', re.IGNORECASE)

        rows = row_pattern.findall(html)

        for row in rows:
            cells = cell_pattern.findall(row)
            cleaned = [tag_cleaner.sub('', c).strip() for c in cells]

            view_match = link_pattern.search(row)
            view_url = ""
            if view_match:
                url_path = view_match.group(1)
                if url_path.startswith("http"):
                    view_url = url_path
                elif url_path.startswith("/"):
                    view_url = f"https://www.searchiqs.com{url_path}"
                else:
                    view_url = f"{SEARCHIQS_BASE_URL}/{url_path}"

            if len(cleaned) >= 8:
                party1 = ""
                party2 = ""
                doc_type = ""
                book_page = ""
                rec_date = ""
                status = ""
                prop_desc = ""
                addl_desc = ""

                for idx, val in enumerate(cleaned):
                    if val in ("View", "My Doc", ""):
                        continue
                    val_upper = val.upper()
                    if "LIS PENDENS" in val_upper or val_upper in ("LP", "LR / LIS PENDENS"):
                        doc_type = val
                    elif re.match(r'^\d{4,5}[\s/-]\d+', val):
                        book_page = val
                    elif re.match(r'^\d{1,2}/\d{1,2}/\d{4}', val):
                        rec_date = val
                    elif val_upper in ("PENDING", "RELEASED", "ACTIVE"):
                        status = val
                    elif "VOL" in val_upper and "PAGE" in val_upper:
                        addl_desc = val
                    elif "SEE DEED" in val_upper:
                        prop_desc = val
                    elif re.match(r'^\d+\s', val) and ("STREET" in val_upper or "AVENUE" in val_upper or "ROAD" in val_upper or "DRIVE" in val_upper or "LANE" in val_upper or "COURT" in val_upper or "PLACE" in val_upper or "TERRACE" in val_upper or "BLVD" in val_upper or "WAY" in val_upper or "CIRCLE" in val_upper):
                        prop_desc = val
                    elif not party1 and len(val) > 2 and not val.isdigit():
                        party1 = val
                    elif party1 and not party2 and len(val) > 2 and not val.isdigit() and val != party1:
                        party2 = val

                if not status:
                    status = "PENDING"

                result = {
                    "party1_seller": party1,
                    "party2_lender": party2,
                    "doc_type": doc_type or "LIS PENDENS",
                    "book_page": book_page,
                    "recording_date": rec_date,
                    "status": status,
                    "property_description": prop_desc,
                    "additional_description": addl_desc,
                    "view_url": view_url,
                    "searchiqs_url": view_url,
                    "property_address": prop_desc if prop_desc and prop_desc.upper() != "SEE DEED" else "",
                    "seller": party1,
                    "lender": party2,
                    "original_mortgage": addl_desc,
                    "court_case_number": "",
                    "debt_amount": "",
                    "return_date": "",
                    "plaintiff": party2,
                    "defendant": party1,
                    "parties": f"{party1} vs {party2}" if party1 and party2 else party1 or party2,
                }

                results.append(result)

        if not results and "No records found" not in html:
            logger.info("No table rows matched GridRow/GridAltRow, attempting alternate parse...")
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
                    "seller": "",
                    "lender": "",
                    "property_address": "",
                    "view_url": "",
                    "searchiqs_url": "",
                    "court_case_number": "",
                    "debt_amount": "",
                    "return_date": "",
                    "status": "PENDING",
                    "original_mortgage": "",
                    "property_description": "",
                    "additional_description": "",
                    "party1_seller": "",
                    "party2_lender": "",
                }
                results.append(result)

        return results

    def _fetch_document_details(self, view_url: str) -> Optional[Dict]:
        try:
            resp = self.session.get(view_url, timeout=30)
            if resp.status_code != 200:
                return None

            html = resp.text
            details = {}

            instr_match = re.search(r'Instr\s*#?:?\s*(\d{4}-\d+)', html)
            if instr_match:
                details["instrument_number"] = instr_match.group(1)

            bp_match = re.search(r'Book/Page:?\s*(\d+\s*/?\s*\d+)', html)
            if bp_match:
                details["book_page_detail"] = bp_match.group(1).strip()

            rec_match = re.search(r'Rec\s*Date:?\s*(\d{1,2}/\d{1,2}/\d{4})', html)
            if rec_match:
                details["recording_date_detail"] = rec_match.group(1)

            or_party_match = re.search(r'OR\s*Party:?\s*(.*?)(?=EE\s*Party|Description|$)', html, re.DOTALL | re.IGNORECASE)
            if or_party_match:
                or_text = re.sub(r'<[^>]+>', '\n', or_party_match.group(1))
                or_names = [n.strip() for n in or_text.strip().split('\n') if n.strip() and len(n.strip()) > 2]
                details["or_parties"] = or_names
                if or_names:
                    details["seller"] = or_names[0]

            ee_party_match = re.search(r'EE\s*Party:?\s*(.*?)(?=Description|Property|$)', html, re.DOTALL | re.IGNORECASE)
            if ee_party_match:
                ee_text = re.sub(r'<[^>]+>', '\n', ee_party_match.group(1))
                ee_names = [n.strip() for n in ee_text.strip().split('\n') if n.strip() and len(n.strip()) > 2]
                details["ee_parties"] = ee_names
                if ee_names:
                    details["lender"] = ee_names[0]

            desc_match = re.search(r'Description:?\s*([^\n<]+)', html)
            if desc_match:
                details["description"] = desc_match.group(1).strip()

            prop_match = re.search(r'Property\s*Description:?\s*([^\n<]+)', html)
            if prop_match:
                details["property_description_detail"] = prop_match.group(1).strip()

            return_match = re.search(r'Return\s*Name/Address:?\s*([^\n<]+)', html)
            if return_match:
                details["return_name_address"] = return_match.group(1).strip()

            clean_text = re.sub(r'<[^>]+>', ' ', html)
            clean_text = re.sub(r'\s+', ' ', clean_text)

            return_date_match = re.search(
                r'(?:RETURN\s*DATE|returnable|made\s+returnable)\s*:?\s*(\w+\s+\d{1,2},?\s+\d{4})',
                clean_text, re.IGNORECASE
            )
            if return_date_match:
                details["return_date"] = return_date_match.group(1).strip()

            file_match = re.search(r'File:?\s*([\d-]+\w*CT)', clean_text, re.IGNORECASE)
            if not file_match:
                file_match = re.search(r'(HHD-CV[\d-]+\w*)', clean_text, re.IGNORECASE)
            if not file_match:
                file_match = re.search(r'(\d{2,4}-\d{4,6}\s*CT)', clean_text, re.IGNORECASE)
            if file_match:
                details["court_case_number"] = file_match.group(1).strip()

            addr_match = re.search(
                r'(?:known\s+as|located\s+at|property\s+address[:\s]+)\s*(\d+[\w\s\-,]+(?:Street|Avenue|Road|Drive|Lane|Court|Place|Terrace|Boulevard|Way|Circle|Blvd|Ave|Rd|Dr|Ln|Ct|Pl|Pkwy)(?:\s*,?\s*(?:aka|also\s+known)\s+[\w\s\-,]+)?)',
                clean_text, re.IGNORECASE
            )
            if addr_match:
                address = addr_match.group(1).strip()
                address = re.sub(r'\s*,?\s*(?:in\s+the|City|County|Hartford|Connecticut|Town).*$', '', address, flags=re.IGNORECASE)
                details["property_address"] = address.strip().rstrip(',')

            mortgage_match = re.search(
                r'(?:mortgage\s+was\s+dated|recorded)\s+.*?(?:in\s+)?Volume\s+(\d+)\s+(?:at\s+)?Page\s+(\d+)',
                clean_text, re.IGNORECASE
            )
            if mortgage_match:
                details["original_mortgage"] = f"VOL {mortgage_match.group(1)} PAGE {mortgage_match.group(2)}"

            vol_match = re.search(r'(VOL\.?\s*\d+\s*(?:PAGE|PG)\.?\s*\d+)', clean_text, re.IGNORECASE)
            if vol_match and "original_mortgage" not in details:
                details["original_mortgage"] = vol_match.group(1).strip()

            v_match = re.search(
                r'([\w\s,\.]+(?:TRUST|LLC|ASSOCIATION|BANK|CORP|INC|COMPANY)[\w\s,\.]*)\s*V\.?\s+([\w\s,\.]+?)(?:\s*[:,]|\s+DECEMBER|\s+JANUARY|\s+FEBRUARY|\s+MARCH|\s+APRIL|\s+MAY|\s+JUNE|\s+JULY|\s+AUGUST|\s+SEPTEMBER|\s+OCTOBER|\s+NOVEMBER)',
                clean_text, re.IGNORECASE
            )
            if v_match:
                if "plaintiff_full" not in details:
                    details["plaintiff_full"] = v_match.group(1).strip()
                if "defendant_full" not in details:
                    defendant_text = v_match.group(2).strip()
                    defendant_text = re.sub(r',?\s*ET\s*AL\.?', '', defendant_text, flags=re.IGNORECASE).strip()
                    details["defendant_full"] = defendant_text

            attorney_match = re.search(
                r'(?:By|Plaintiff):\s*\n?\s*([\w\s\.]+,?\s*Esq\.?)\s*\n?\s*([\w\s,\.]+(?:LLP|LLC|P\.?C\.?|PA|PLLC))',
                clean_text, re.IGNORECASE
            )
            if attorney_match:
                details["attorney"] = attorney_match.group(1).strip()
                details["attorney_firm"] = attorney_match.group(2).strip()

            related_links = re.findall(r'href=["\']([^"\']*)["\'][^>]*>\s*(\d{1,2}/\d{1,2}/\d{4}\s+MORTGAGE[^<]*)', html, re.IGNORECASE)
            if related_links:
                details["related_documents"] = [{"url": l[0], "description": l[1].strip()} for l in related_links]

            return details if details else None

        except Exception as e:
            logger.warning(f"Document detail fetch failed for {view_url}: {e}")
            return None

    def search_court_case(self, party_name: str) -> Optional[Dict]:
        try:
            search_url = f"{CT_COURT_URL}/CaseSearch"
            resp = self.session.get(search_url, params={
                "partyName": party_name,
                "caseType": "FC",
            }, timeout=30)

            if resp.status_code == 200:
                case_match = re.search(r'(HHD-CV\d{2}-\d+)', resp.text)
                if not case_match:
                    case_match = re.search(r'(\d{2,4}-\d{4,6}\s*CT)', resp.text, re.IGNORECASE)
                debt_match = re.search(r'\$[\d,]+\.?\d*', resp.text)
                date_match = re.search(r'Return Date:?\s*(\d{1,2}/\d{1,2}/\d{4})', resp.text)
                status_match = re.search(r'Status:?\s*([A-Za-z\s]+)', resp.text)

                return {
                    "case_number": case_match.group(1) if case_match else "Not found",
                    "debt_amount": debt_match.group(0) if debt_match else "Unknown",
                    "return_date": date_match.group(1) if date_match else "TBD",
                    "status": status_match.group(1).strip() if status_match else "Pending",
                    "court_url": f"{CT_COURT_URL}/CaseDetail.aspx?DocketNo={case_match.group(1)}" if case_match else "",
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

    def get_filing_as_row(self, filing: Dict) -> List[str]:
        return [
            filing.get("property_address", "") or filing.get("property_description", "SEE DEED"),
            filing.get("seller", "") or filing.get("party1_seller", ""),
            filing.get("lender", "") or filing.get("party2_lender", ""),
            filing.get("recording_date", "") or filing.get("recording_date_detail", ""),
            filing.get("original_mortgage", "") or filing.get("additional_description", ""),
            filing.get("court_case_number", ""),
            filing.get("debt_amount", ""),
            filing.get("return_date", ""),
            filing.get("status", "PENDING"),
        ]


_scraper = None

def get_scraper() -> SearchIQSScraper:
    global _scraper
    if _scraper is None:
        _scraper = SearchIQSScraper()
    return _scraper


logger.info("SearchIQS scraper module loaded (v2 - full document extraction)")
