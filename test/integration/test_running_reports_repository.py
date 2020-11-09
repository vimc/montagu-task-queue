from src.utils.running_reports_repository import RunningReportsRepository

repo = RunningReportsRepository()
group = "test_group"
disease = "test_disease"
report = "test_report"
report_key = "test_report_key"


class TestRunningReportsRepository:

    def setup_method(self):
        repo.delete_if_matches(group, disease, report, report_key)

    def test_get_nonexistent_running_report(self):
        value = repo.get(group, disease, report)
        assert value is None

    def test_can_set_and_get_running_report(self):
        repo.set(group, disease, report, report_key)
        value = repo.get(group, disease, report)
        assert value == report_key

    def test_can_delete_running_report_if_matches(self):
        repo.set(group, disease, report, report_key)
        repo.delete_if_matches(group, disease, report, report_key)
        value = repo.get(group, disease, report)
        assert value is None

    def test_value_not_deleted_if_expected_values_does_not_match(self):
        repo.set(group, disease, report, report_key)
        repo.delete_if_matches(group, disease, report, "wrong_key")
        value = repo.get(group, disease, report)
        assert value == report_key

    def test_can_create_expected_db_key(self):
        value = repo.db_key(group, disease, report)
        assert value == "running_report_test_group_test_disease_test_report"

