"""GA4 Data API から日別の指標を取得する。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

# 保存指標キー -> GA4 指標名（設計書 4.2）
METRICS: dict[str, str] = {
    "page_views": "screenPageViews",
    "sessions": "sessions",
    "users": "totalUsers",
}


@dataclass(frozen=True)
class Snapshot:
    service: str
    metric: str
    date: date
    value: float
    source: str

    def to_payload(self) -> dict:
        """WordPress の POST /med/v1/snapshot に送る JSON。"""
        return {
            "service": self.service,
            "metric": self.metric,
            "date": self.date.isoformat(),
            "value": self.value,
            "source": self.source,
        }


def date_range(today: date, days: int = 30) -> tuple[date, date]:
    """前日までの直近 days 日間を返す（当日は集計途中なので含めない）。"""
    if not 1 <= days <= 365:
        raise ValueError("days は 1〜365 で指定してください")
    end = today - timedelta(days=1)
    return end - timedelta(days=days - 1), end


def build_request(property_id: str, start: date, end: date):
    from google.analytics.data_v1beta.types import (
        DateRange,
        Dimension,
        Metric,
        RunReportRequest,
    )

    return RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="date")],
        metrics=[Metric(name=name) for name in METRICS.values()],
        date_ranges=[DateRange(start_date=start.isoformat(), end_date=end.isoformat())],
    )


def parse_response(response) -> list[Snapshot]:
    """RunReport の応答を Snapshot の一覧に変換する。

    GA4 は値が 0 の日も行を返すが、行が無い日は「未取得」として扱うため補完しない。
    """
    keys = list(METRICS.keys())
    snapshots = []
    for row in response.rows:
        day = datetime.strptime(row.dimension_values[0].value, "%Y%m%d").date()
        for key, metric_value in zip(keys, row.metric_values):
            snapshots.append(
                Snapshot("wordpress", key, day, float(metric_value.value), "ga4")
            )
    return sorted(snapshots, key=lambda s: (s.date, s.metric))


def fetch_daily(property_id: str, start: date, end: date, client=None) -> list[Snapshot]:
    if client is None:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient

        # 認証は環境変数 GOOGLE_APPLICATION_CREDENTIALS の JSON 鍵を使う
        client = BetaAnalyticsDataClient()
    response = client.run_report(build_request(property_id, start, end))
    return parse_response(response)
