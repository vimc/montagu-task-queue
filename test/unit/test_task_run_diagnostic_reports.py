from src.task_run_diagnostic_reports import run_diagnostic_reports


def test_run_diagnostic_reports():
    keys = run_diagnostic_reports("testGroup", "testDisease")
    assert len(keys) == 2
