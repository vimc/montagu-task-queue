from src.utils.running_reports_repository import RunningReportsRepository


def test_get_nonexistent_running_report():
    repo = RunningReportsRepository()
    value = repo.get("test_group", "test_disease")
    assert value is None


def test_can_set_and_delete_running_report():
    repo = RunningReportsRepository()
    repo.set("test_group", "test_disease", "test_report_key")
    value = repo.get("test_group", "test_disease")
    assert value == "test_report_key"
    repo.delete("test_group", "test_disease")
    value = repo.get("test_group", "test_disease")
    assert value is None


def test_can_create_expected_db_key():
    repo = RunningReportsRepository()
    value = repo.db_key("test_group", "test_disease")
    assert value == "running_report_test_group_test_disease"
