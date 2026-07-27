from __future__ import annotations

import re
from io import BytesIO
from urllib.parse import parse_qs, urlparse

import requests

SHEET_ID_RE = re.compile(r"/spreadsheets/d/([a-zA-Z0-9-_]+)")


def google_sheet_export_url(url: str) -> str:
    match = SHEET_ID_RE.search(url)
    if not match:
        raise ValueError("Не удалось извлечь ID Google Sheets из URL.")
    sheet_id = match.group(1)
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    gid = query.get("gid", [None])[0]
    if gid is None and parsed.fragment.startswith("gid="):
        gid = parsed.fragment.split("=", 1)[1].split("&", 1)[0]
    export = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    if gid and gid.isdigit():
        export += f"&gid={gid}"
    return export


def download_google_sheet(url: str, timeout: int = 30) -> BytesIO:
    response = requests.get(google_sheet_export_url(url), timeout=timeout)
    if not response.ok:
        raise RuntimeError(
            "Google Sheets не отдал XLSX. Проверьте доступ по ссылке; "
            "для закрытой таблицы нужен service account."
        )
    content_type = response.headers.get("Content-Type", "")
    if "spreadsheet" not in content_type and not response.content.startswith(b"PK"):
        raise RuntimeError(
            "Вместо XLSX получена HTML-страница авторизации. "
            "Откройте доступ или используйте service account."
        )
    return BytesIO(response.content)
