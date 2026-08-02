from src.dates import date_is_grounded


def test_keeps_slash_date():
    assert date_is_grounded("2024-06-14", "inspection passed 6/14, signed card")


def test_keeps_month_name():
    assert date_is_grounded("2024-06-14", "passed on June 14 by the inspector")


def test_keeps_iso():
    assert date_is_grounded("2026-03-04", "2026-03-04 - tear-off started")


def test_rejects_absent_date():
    assert not date_is_grounded("2024-06-14", "poured the footings today")


def test_rejects_non_iso_input():
    assert not date_is_grounded("June 14", "June 14 on site")
