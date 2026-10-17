import json
from contextlib import contextmanager
from datetime import date
from types import SimpleNamespace as NS

import pytest

from med_sync import __main__ as cli
from med_sync import ga4


class FakeClient:
    def run_report(self, request):
        return NS(rows=[
            NS(dimension_values=[NS(value="20261016")],
               metric_values=[NS(value="10"), NS(value="5"), NS(value="4")])
        ])


@pytest.fixture(autouse=True)
def stub_request(monkeypatch):
    # google-analytics-data が無くてもテストできるようにする
    monkeypatch.setattr(ga4, "build_request", lambda *args: args)
    monkeypatch.setenv("MED_GA4_PROPERTY_ID", "123456789")


def test_dry_run_prints_without_posting(capsys):
    cli.main(["--dry-run"], today=date(2026, 10, 17), client=FakeClient())
    rows = json.loads(capsys.readouterr().out)
    assert len(rows) == 3 and rows[0]["date"] == "2026-10-16"


def test_posts_each_snapshot_with_basic_auth(monkeypatch):
    monkeypatch.setenv("MED_WP_BASE_URL", "https://example.com/")
    monkeypatch.setenv("MED_WP_USER", "admin")
    monkeypatch.setenv("MED_WP_APP_PASSWORD", "xxxx xxxx")
    sent = []

    @contextmanager
    def opener(request, timeout):
        sent.append(request)
        yield NS(status=200)

    cli.main([], today=date(2026, 10, 17), client=FakeClient(), opener=opener)
    assert len(sent) == 3
    assert sent[0].full_url == "https://example.com/wp-json/med/v1/snapshot"
    assert sent[0].get_header("Authorization").startswith("Basic ")


def test_rejects_plain_http(monkeypatch):
    monkeypatch.setenv("MED_WP_BASE_URL", "http://example.com")
    monkeypatch.setenv("MED_WP_USER", "admin")
    monkeypatch.setenv("MED_WP_APP_PASSWORD", "x")
    with pytest.raises(ValueError):
        cli.main([], today=date(2026, 10, 17), client=FakeClient())
