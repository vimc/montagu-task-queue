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
        return self.__montagu()["url"]

    @property
    def montagu_user(self):
        return self.__montagu()["user"]

    @property
    def montagu_password(self):
        return self.__montagu()["password"]

    @property
    def orderlyweb_url(self):
        return self.__server("orderlyweb")["url"]

    @property
    def report_poll_seconds(self):
        return self.__task("diagnostic_reports")["poll_seconds"]

    def diagnostic_reports(self, group, disease):
        result = []
        reports_config = self.__task("diagnostic_reports")["reports"]
        if group in reports_config and disease in reports_config[group]:
            for r in reports_config[group][disease]:
                params = r["parameters"] if "parameters" in r else {}
                result.append(ReportConfig(r["report_name"], params))
        return result

    def __server(self, name):
        return self.cfg["servers"][name]

    def __task(self, name):
        return self.cfg["tasks"][name]

    def __montagu(self):
        return self.__server("montagu")
