"""End-to-end tests on the local rule-based provider (no API key needed)."""
import os

from src import aggregate
from src.organizer import organize_item, organize_stream, split_items

os.environ.pop("ANTHROPIC_API_KEY", None)  # force the local provider


def test_split_items_on_blank_lines():
    assert len(split_items("one thing\n\nsecond thing\n\nthird")) == 3


def test_local_extracts_amount_and_vendor():
    item = organize_item("Home Depot 6/11 receipt $1,284.50 - 18 base cabinets.")
    assert item.category == "material_purchase"
    assert abs((item.amount or 0) - 1284.50) < 0.01
    assert item.vendor and "home depot" in item.vendor.lower()


def test_local_never_invents_money():
    item = organize_item("Client wants to add under-cabinet LED lighting, need to price it.")
    assert item.amount is None
    assert "missing_amount" in item.flags


def test_stream_and_summary():
    items = organize_stream(
        "6/14 - inspection PASSED, signed card.\n\n"
        "Home Depot receipt $200.00 for screws."
    )
    assert len(items) == 2
    summary = aggregate.summarize(items)
    assert summary["item_count"] == 2
    assert summary["total_spend"] == 200.0
    assert len(summary["timeline"]) == 2
