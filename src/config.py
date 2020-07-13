import yaml


class ReportConfig:
    def __init__(self, name, parameters):
        self.name = name
        self.parameters = parameters


class Config:
    def __init__(self):
        with open("config/config.yml", "r") as ymlfile:
            self.cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)

    @property
    def broker(self):
        return self.cfg["broker"]

    @property
    def backend(self):
        return self.cfg["backend"]

    @property
    def montagu_url(self):
        return self.cfg["montagu_url"]

    @property
    def montagu_user(self):
        return self.cfg["montagu_user"]

    @property
    def montagu_password(self):
        return self.cfg["montagu_password"]

    @property
    def orderlyweb_url(self):
        return self.cfg["orderlyweb_url"]

    @property
    def report_poll_seconds(self):
        return self.cfg["report_poll_seconds"]

    def diagnostic_reports(self, group, disease):
        result = []
        reports_config = self.cfg["diagnostic_reports"]
        if group in reports_config and disease in reports_config[group]:
            for r in reports_config[group][disease]:
                params = r["parameters"] if "parameters" in r else {}
                result.append(ReportConfig(r["report_name"], params))
        return result
