import os
import json
import logging
import requests
import time
from datetime import datetime
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)


class GoogleClient:
    def __init__(self):
        self.credentials = None
        self.access_token = None
        self.token_expiry = 0
        self._load_credentials()

    def _load_credentials(self):
        creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        if creds_json:
            try:
                self.credentials = json.loads(creds_json)
                logger.info("Google service account credentials loaded")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse GOOGLE_SERVICE_ACCOUNT_JSON: {e}")
                self.credentials = None
        else:
            creds_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if creds_file and os.path.exists(creds_file):
                try:
                    with open(creds_file) as f:
                        self.credentials = json.load(f)
                    logger.info(f"Google credentials loaded from file: {creds_file}")
                except Exception as e:
                    logger.error(f"Failed to load credentials file: {e}")
            else:
                logger.warning("No Google credentials configured. Set GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_APPLICATION_CREDENTIALS")

    def _get_access_token(self) -> Optional[str]:
        if not self.credentials:
            logger.error("No Google credentials available")
            return None

        if self.access_token and time.time() < self.token_expiry - 60:
            return self.access_token

        try:
            jwt_token = self._create_signed_jwt()
            if not jwt_token:
                return None

            resp = requests.post("https://oauth2.googleapis.com/token", data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": jwt_token,
            }, timeout=30)
            resp.raise_for_status()
            token_data = resp.json()
            self.access_token = token_data["access_token"]
            self.token_expiry = int(time.time()) + token_data.get("expires_in", 3600)
            logger.info("Google access token refreshed")
            return self.access_token
        except Exception as e:
            logger.error(f"Failed to get Google access token: {e}")
            return None

    def _create_signed_jwt(self) -> Optional[str]:
        import base64
        import subprocess
        import tempfile

        try:
            now = int(time.time())
            header = base64.urlsafe_b64encode(
                json.dumps({"alg": "RS256", "typ": "JWT"}).encode()
            ).rstrip(b"=")
            payload_data = {
                "iss": self.credentials["client_email"],
                "scope": "https://www.googleapis.com/auth/spreadsheets https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/documents",
                "aud": "https://oauth2.googleapis.com/token",
                "iat": now,
                "exp": now + 3600,
            }
            payload = base64.urlsafe_b64encode(
                json.dumps(payload_data).encode()
            ).rstrip(b"=")
            signing_input = header + b"." + payload

            with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as kf:
                kf.write(self.credentials["private_key"])
                key_path = kf.name

            try:
                result = subprocess.run(
                    ["openssl", "dgst", "-sha256", "-sign", key_path],
                    input=signing_input,
                    capture_output=True,
                    timeout=10
                )
                if result.returncode != 0:
                    logger.error(f"OpenSSL signing failed: {result.stderr.decode()}")
                    return None
                signature = result.stdout
            finally:
                os.unlink(key_path)

            sig_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=")
            jwt_token = (signing_input + b"." + sig_b64).decode()
            return jwt_token
        except Exception as e:
            logger.error(f"JWT creation failed: {e}")
            return None

    def _headers(self) -> Dict:
        token = self._get_access_token()
        if not token:
            return {}
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def create_spreadsheet(self, title: str, folder_id: str = None) -> Optional[str]:
        headers = self._headers()
        if not headers:
            return None

        try:
            body = {"properties": {"title": title}}
            resp = requests.post(
                "https://sheets.googleapis.com/v4/spreadsheets",
                headers=headers, json=body, timeout=30
            )
            resp.raise_for_status()
            spreadsheet_id = resp.json()["spreadsheetId"]
            logger.info(f"Created spreadsheet: {title} ({spreadsheet_id})")

            if folder_id:
                self._move_to_folder(spreadsheet_id, folder_id)

            return spreadsheet_id
        except Exception as e:
            logger.error(f"Failed to create spreadsheet: {e}")
            return None

    def append_rows(self, spreadsheet_id: str, sheet_name: str, rows: List[List]) -> bool:
        headers = self._headers()
        if not headers:
            return False

        try:
            url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{sheet_name}:append"
            body = {"values": rows}
            resp = requests.post(
                url, headers=headers, json=body,
                params={"valueInputOption": "USER_ENTERED", "insertDataOption": "INSERT_ROWS"},
                timeout=30
            )
            resp.raise_for_status()
            logger.info(f"Appended {len(rows)} rows to {sheet_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to append rows: {e}")
            return False

    def read_sheet(self, spreadsheet_id: str, range_name: str) -> List[List]:
        headers = self._headers()
        if not headers:
            return []

        try:
            url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_name}"
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp.json().get("values", [])
        except Exception as e:
            logger.error(f"Failed to read sheet: {e}")
            return []

    def create_document(self, title: str, folder_id: str = None) -> Optional[str]:
        headers = self._headers()
        if not headers:
            return None

        try:
            body = {"title": title}
            resp = requests.post(
                "https://docs.googleapis.com/v1/documents",
                headers=headers, json=body, timeout=30
            )
            resp.raise_for_status()
            doc_id = resp.json()["documentId"]
            logger.info(f"Created document: {title} ({doc_id})")

            if folder_id:
                self._move_to_folder(doc_id, folder_id)

            return doc_id
        except Exception as e:
            logger.error(f"Failed to create document: {e}")
            return None

    def write_document_content(self, doc_id: str, content: str) -> bool:
        headers = self._headers()
        if not headers:
            return False

        try:
            requests_body = [
                {
                    "insertText": {
                        "location": {"index": 1},
                        "text": content
                    }
                }
            ]
            resp = requests.post(
                f"https://docs.googleapis.com/v1/documents/{doc_id}:batchUpdate",
                headers=headers,
                json={"requests": requests_body},
                timeout=30
            )
            resp.raise_for_status()
            logger.info(f"Wrote content to document {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to write document: {e}")
            return False

    def append_document_content(self, doc_id: str, content: str) -> bool:
        headers = self._headers()
        if not headers:
            return False

        try:
            get_resp = requests.get(
                f"https://docs.googleapis.com/v1/documents/{doc_id}",
                headers=headers, timeout=30
            )
            get_resp.raise_for_status()
            doc_data = get_resp.json()
            body_content = doc_data.get("body", {}).get("content", [])
            end_index = 1
            if body_content:
                last_element = body_content[-1]
                end_index = last_element.get("endIndex", 1) - 1
            if end_index < 1:
                end_index = 1

            requests_body = [
                {
                    "insertText": {
                        "location": {"index": end_index},
                        "text": content
                    }
                }
            ]
            resp = requests.post(
                f"https://docs.googleapis.com/v1/documents/{doc_id}:batchUpdate",
                headers=headers,
                json={"requests": requests_body},
                timeout=30
            )
            resp.raise_for_status()
            logger.info(f"Appended content to document {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to append to document: {e}")
            return False

    def copy_document(self, template_doc_id: str, new_title: str, folder_id: str = None) -> Optional[str]:
        headers = self._headers()
        if not headers:
            return None

        try:
            body = {"name": new_title}
            if folder_id:
                body["parents"] = [folder_id]

            resp = requests.post(
                f"https://www.googleapis.com/drive/v3/files/{template_doc_id}/copy",
                headers=headers, json=body, timeout=30
            )
            resp.raise_for_status()
            new_id = resp.json()["id"]
            logger.info(f"Copied template to: {new_title} ({new_id})")
            return new_id
        except Exception as e:
            logger.error(f"Failed to copy document: {e}")
            return None

    def replace_text_in_doc(self, doc_id: str, replacements: Dict[str, str]) -> bool:
        headers = self._headers()
        if not headers:
            return False

        try:
            reqs = []
            for placeholder, value in replacements.items():
                reqs.append({
                    "replaceAllText": {
                        "containsText": {"text": placeholder, "matchCase": True},
                        "replaceText": str(value)
                    }
                })

            resp = requests.post(
                f"https://docs.googleapis.com/v1/documents/{doc_id}:batchUpdate",
                headers=headers,
                json={"requests": reqs},
                timeout=30
            )
            resp.raise_for_status()
            logger.info(f"Replaced {len(replacements)} fields in doc {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to replace text: {e}")
            return False

    def _move_to_folder(self, file_id: str, folder_id: str) -> bool:
        headers = self._headers()
        if not headers:
            return False

        try:
            get_resp = requests.get(
                f"https://www.googleapis.com/drive/v3/files/{file_id}",
                headers=headers, params={"fields": "parents"}, timeout=30
            )
            get_resp.raise_for_status()
            current_parents = ",".join(get_resp.json().get("parents", []))

            resp = requests.patch(
                f"https://www.googleapis.com/drive/v3/files/{file_id}",
                headers=headers,
                params={"addParents": folder_id, "removeParents": current_parents},
                timeout=30
            )
            resp.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to move file to folder: {e}")
            return False


_client = None

def get_google_client() -> GoogleClient:
    global _client
    if _client is None:
        _client = GoogleClient()
    return _client


logger.info("Google client module loaded")
