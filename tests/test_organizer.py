from src.organizer import organize_job_stream


def test_demo_mode_organizes_sample():
    text = """
    Project: Test roof repair
    2026-07-29 - Crew found a damaged flashing.
    Receipt: Roof Supply, $90.00.
    """
    result = organize_job_stream(text, demo_mode=True)
    assert result.project_name == "Test roof repair"
    assert len(result.items) == 2
    assert any(item.action_required for item in result.items)
    assert any(item.amount == 90.0 for item in result.items)
