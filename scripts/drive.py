"""Minimal Google Drive API v3 client for reading a public folder with an API key."""
import re

import requests

API = "https://www.googleapis.com/drive/v3/files"
FOLDER_MIME = "application/vnd.google-apps.folder"
SHEET_MIME = "application/vnd.google-apps.spreadsheet"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
SEMESTER_RE = re.compile(r"^(\d{3})-([12])$")


class DriveClient:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("GOOGLE_DRIVE_API_KEY is not set")
        self.api_key = api_key
        self.session = requests.Session()

    def _get(self, url: str, **params) -> requests.Response:
        params["key"] = self.api_key
        resp = self.session.get(url, params=params, timeout=60)
        resp.raise_for_status()
        return resp

    def list_children(self, folder_id: str) -> list[dict]:
        files, token = [], None
        while True:
            params = {
                "q": f"'{folder_id}' in parents and trashed = false",
                "fields": "nextPageToken, files(id, name, mimeType, modifiedTime)",
                "pageSize": 1000,
            }
            if token:
                params["pageToken"] = token
            data = self._get(API, **params).json()
            files.extend(data.get("files", []))
            token = data.get("nextPageToken")
            if not token:
                return files

    def semester_folders(self, root_id: str, count: int = 2) -> list[dict]:
        """Return the newest `count` semester folders (named like `115-1`), newest first."""
        folders = []
        for f in self.list_children(root_id):
            m = SEMESTER_RE.match(f["name"].strip())
            if f["mimeType"] == FOLDER_MIME and m:
                folders.append(((int(m.group(1)), int(m.group(2))), f))
        folders.sort(key=lambda x: x[0], reverse=True)
        return [f for _, f in folders[:count]]

    def list_spreadsheets(self, folder_id: str) -> list[dict]:
        return [
            f for f in self.list_children(folder_id)
            if f["mimeType"] in (XLSX_MIME, SHEET_MIME) or f["name"].lower().endswith(".xlsx")
        ]

    def download_xlsx(self, file: dict) -> bytes:
        if file["mimeType"] == SHEET_MIME:
            return self._get(f"{API}/{file['id']}/export", mimeType=XLSX_MIME).content
        return self._get(f"{API}/{file['id']}", alt="media").content
