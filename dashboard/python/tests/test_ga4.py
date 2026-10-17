from datetime import date
from types import SimpleNamespace as NS

import pytest

from med_sync import ga4


def fake_response(rows):
    return NS(rows=[
        NS(dimension_values=[NS(value=day)], metric_values=[NS(value=v) for v in values])
        for day, values in rows
    ])


def test_date_range_excludes_today():
    assert ga4.date_range(date(2026, 10, 17)) == (date(2026, 9, 17), date(2026, 10, 16))


@pytest.mark.parametrize("days", [0, 366])
def test_date_range_rejects_out_of_range(days):
    with pytest.raises(ValueError):
        ga4.date_range(date(2026, 10, 17), days)


def test_parse_response_maps_metrics_in_order():
    snapshots = ga4.parse_response(fake_response([("20261016", ["120", "80", "60"])]))
    assert {s.metric: s.value for s in snapshots} == {
        "page_views": 120.0,
        "sessions": 80.0,
        "users": 60.0,
    }
    assert all(s.service == "wordpress" and s.source == "ga4" for s in snapshots)


def test_parse_response_does_not_fill_missing_days():
    snapshots = ga4.parse_response(fake_response([("20261014", ["1", "1", "1"])]))
    assert {s.date for s in snapshots} == {date(2026, 10, 14)}


def test_payload_matches_rest_api():
    snapshot = ga4.Snapshot("wordpress", "sessions", date(2026, 10, 16), 80.0, "ga4")
    assert snapshot.to_payload() == {
        "service": "wordpress",
        "metric": "sessions",
        "date": "2026-10-16",
        "value": 80.0,
        "source": "ga4",
    }
