import json

import pytest

from src import providers
from src.providers import (
    ProviderError,
    classify,
    find_amount,
    find_date,
    provider_status,
    resolve_chain,
)
from src.schema import JobOrganizationResult

SAMPLE = """Project: Alvarez kitchen renovation
Client: Sofia Alvarez

2026-07-21 - Crew completed cabinet removal.
Receipt: BuildRight, drywall and screws, $142.75.
"""


@pytest.fixture(autouse=True)
def clear_provider_env(monkeypatch):
    for name in ["AI_PROVIDER", "ANTHROPIC_API_KEY", "GROQ_API_KEY"]:
        monkeypatch.delenv(name, raising=False)


def test_anthropic_leads_when_both_keys_are_set(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    monkeypatch.setenv("GROQ_API_KEY", "g")

    assert resolve_chain() == ["anthropic", "groq", "local"]


def test_groq_leads_when_anthropic_has_no_key(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "g")

    assert resolve_chain() == ["groq", "local"]


def test_local_is_all_that_is_left_without_keys():
    assert resolve_chain() == ["local"]


def test_a_pinned_provider_skips_the_chain(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    monkeypatch.setenv("AI_PROVIDER", "local")

    assert resolve_chain() == ["local"]


def test_status_lists_anthropic_even_with_no_key(monkeypatch):
    # The whole point: a missing row would make "leads but unconfigured" look
    # the same as "not part of this app".
    monkeypatch.setenv("GROQ_API_KEY", "g")

    assert provider_status() == [
        ("anthropic", "no key"),
        ("groq", "active"),
        ("local", "standby"),
    ]


def test_status_marks_anthropic_active_when_it_has_a_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    monkeypatch.setenv("GROQ_API_KEY", "g")

    assert provider_status() == [
        ("anthropic", "active"),
        ("groq", "standby"),
        ("local", "standby"),
    ]


def test_status_says_off_rather_than_no_key_when_a_provider_is_pinned(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    monkeypatch.setenv("GROQ_API_KEY", "g")
    monkeypatch.setenv("AI_PROVIDER", "groq")

    assert provider_status() == [
        ("anthropic", "off"),
        ("groq", "active"),
        ("local", "off"),
    ]


def test_status_with_no_keys_at_all():
    assert provider_status() == [
        ("anthropic", "no key"),
        ("groq", "no key"),
        ("local", "active"),
    ]


def test_groq_takes_over_when_anthropic_raises(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    monkeypatch.setenv("GROQ_API_KEY", "g")

    def boom(system_prompt, user_prompt, model=None):
        raise RuntimeError("anthropic is down")

    monkeypatch.setattr(providers, "call_anthropic", boom)
    monkeypatch.setattr(providers, "call_groq", lambda s, u, model=None: '{"ok": true}')

    text, used, failures = providers.complete("sys", "user", SAMPLE)

    assert used == "groq"
    assert text == '{"ok": true}'
    # The reason has to survive the fallback. Groq answering is not by itself a
    # sign that anything went wrong, so the result cannot be the only record.
    assert failures == ["anthropic: RuntimeError: anthropic is down"]


def test_nothing_is_reported_when_the_first_provider_answers(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    monkeypatch.setattr(providers, "call_anthropic", lambda s, u, model=None: '{"ok": true}')

    _, used, failures = providers.complete("sys", "user", SAMPLE)

    assert used == "anthropic"
    assert failures == []


def test_a_missing_sdk_is_named_as_a_setup_problem(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    monkeypatch.setenv("GROQ_API_KEY", "g")

    def not_installed(*args, **kwargs):
        raise ImportError("No module named 'anthropic'")

    monkeypatch.setattr(providers, "call_anthropic", not_installed)
    monkeypatch.setattr(providers, "call_groq", lambda s, u, model=None: "{}")

    _, _, failures = providers.complete("sys", "user", SAMPLE)

    assert failures == ["anthropic: the SDK is not installed (No module named 'anthropic')"]


def test_a_missing_key_says_which_key(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "anthropic")

    # No key, so the real call_anthropic raises KeyError on os.environ.
    with pytest.raises(ProviderError) as caught:
        providers.complete("sys", "user", SAMPLE)

    assert "ANTHROPIC_API_KEY is not set" in str(caught.value)


def test_the_local_engine_catches_a_total_outage(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    monkeypatch.setenv("GROQ_API_KEY", "g")

    def boom(*args, **kwargs):
        raise RuntimeError("no network")

    monkeypatch.setattr(providers, "call_anthropic", boom)
    monkeypatch.setattr(providers, "call_groq", boom)

    text, used, failures = providers.complete("sys", "user", SAMPLE)

    assert used == "local"
    assert json.loads(text)["items"]
    assert len(failures) == 2


def test_every_provider_failing_is_an_error(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "groq")
    monkeypatch.setattr(providers, "call_groq", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x")))

    with pytest.raises(ProviderError):
        providers.complete("sys", "user", SAMPLE)


def test_the_local_engine_output_passes_the_real_schema():
    # The whole point of the fallback is that nothing downstream has to know.
    result = JobOrganizationResult.model_validate(json.loads(providers.local_result(SAMPLE)))

    assert result.project_name == "Alvarez kitchen renovation"
    assert result.client_name == "Sofia Alvarez"
    assert [item.category for item in result.items] == ["contractor_update", "receipt"]


def test_the_local_engine_will_not_invent_a_year():
    result = json.loads(providers.local_result("7/27 demo done, moisture behind the wall"))

    assert result["items"][0]["date"] is None


def test_classify_picks_the_specific_rule_over_the_broad_one():
    assert classify("Receipt: BuildRight, screws, $142.75") == "receipt"
    assert classify("photo_0431.jpg - dark staining on the framing") == "photo"
    assert classify("something entirely unremarkable") == "other"


def test_find_amount_reads_the_currency_with_the_number():
    assert find_amount("Receipt: screws, $142.75") == (142.75, "USD")
    assert find_amount("paid 118.90 TND for the primer") == (118.90, "TND")


def test_find_amount_ignores_a_date():
    assert find_amount("7/27 demo done") == (None, None)


def test_find_date_needs_a_year():
    assert find_date("2026-07-21 - crew on site") == "2026-07-21"
    assert find_date("7/27 demo done") is None
