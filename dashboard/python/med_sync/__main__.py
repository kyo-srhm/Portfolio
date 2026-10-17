"""使い方: python -m med_sync [--days 30] [--dry-run]"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date

from . import ga4, wordpress


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        sys.exit(f"環境変数 {name} が設定されていません（.env.example を参照）")
    return value


def main(argv=None, today=None, client=None, opener=None) -> int:
    parser = argparse.ArgumentParser(description="GA4 の日別実績を WordPress に同期する")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--dry-run", action="store_true", help="登録せず取得結果を表示する")
    args = parser.parse_args(argv)

    start, end = ga4.date_range(today or date.today(), args.days)
    snapshots = ga4.fetch_daily(require_env("MED_GA4_PROPERTY_ID"), start, end, client)

    if args.dry_run:
        print(json.dumps([s.to_payload() for s in snapshots], ensure_ascii=False, indent=2))
        return 0

    kwargs = {"opener": opener} if opener else {}
    count = wordpress.post_snapshots(
        snapshots,
        require_env("MED_WP_BASE_URL"),
        require_env("MED_WP_USER"),
        require_env("MED_WP_APP_PASSWORD"),
        **kwargs,
    )
    print(f"{start}〜{end} の {count} 件を登録しました")
    return 0


if __name__ == "__main__":
    sys.exit(main())
