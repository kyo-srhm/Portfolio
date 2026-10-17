"""取得した実績を WordPress プラグインの REST API に登録する。"""
from __future__ import annotations

import base64
import json
import urllib.request
from typing import Callable, Iterable

from .ga4 import Snapshot

ENDPOINT = "/wp-json/med/v1/snapshot"


def auth_header(user: str, app_password: str) -> str:
    """WordPress アプリケーションパスワードの Basic 認証ヘッダー。"""
    token = base64.b64encode(f"{user}:{app_password}".encode()).decode()
    return f"Basic {token}"


def post_snapshots(
    snapshots: Iterable[Snapshot],
    base_url: str,
    user: str,
    app_password: str,
    opener: Callable = urllib.request.urlopen,
) -> int:
    if not base_url.startswith("https://"):
        raise ValueError("WordPress の URL は https:// で指定してください")
    url = base_url.rstrip("/") + ENDPOINT
    headers = {
        "Authorization": auth_header(user, app_password),
        "Content-Type": "application/json",
    }
    count = 0
    for snapshot in snapshots:
        body = json.dumps(snapshot.to_payload()).encode()
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with opener(request, timeout=30) as response:
            if response.status >= 300:
                raise RuntimeError(f"登録に失敗しました: HTTP {response.status}")
        count += 1
    return count
