import yaml


class ReportConfig:

    def __init__(self,
                 name,
                 parameters,
                 success_email_recipients,
                 success_email_subject,
                 assignee,
                 publish_roles):
        self.name = name
        self.parameters = parameters
        self.success_email_recipients = success_email_recipients
        self.success_email_subject = success_email_subject
        self.assignee = assignee
        self.publish_roles = publish_roles


class ArchiveFolderContentsConfig:

    def __init__(self, min_file_age_seconds):
        self.min_file_age_seconds = min_file_age_seconds


class Config:
    def __init__(self):
        with open("config/config.yml", "r") as ymlfile:
            self.cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)

    @property
    def host(self):
        return self.cfg["host"]

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
    def packit_url(self):
        return self.__server("packit")["url"]

    @property
    def disable_certificate_verify(self):
        return self.__server("packit")["disable_certificate_verify"]

    @property
    def youtrack_token(self):
        return self.__server("youtrack")["token"]

    @property
    def report_poll_seconds(self):
        return self.__task("diagnostic_reports")["poll_seconds"]

    @property
    def use_additional_recipients(self):
        return self.__task("diagnostic_reports")["use_additional_recipients"]

    @property
    def smtp_host(self):
        return self.__smtp()["host"]

    @property
    def smtp_port(self):
        return self.__smtp()["port"]

    @property
    def smtp_from(self):
        return self.__smtp()["from"]

    @property
    def smtp_user(self):
        return self.__value_or_default(self.__smtp(), "user", None)

    @property
    def smtp_password(self):
        return self.__value_or_default(self.__smtp(), "password", None)

    @property
    def archive_folder_contents(self):
        return ArchiveFolderContentsConfig(
            self.__task("archive_folder_contents")["min_file_age_seconds"])

    def diagnostic_reports(self, group, disease):
        result = []
        reports_config = self.__task("diagnostic_reports")["reports"]
        if group in reports_config and disease in reports_config[group]:
            for r in reports_config[group][disease]:
                params = self.__value_or_default(r, "parameters", {})

                email = self.__value_or_default(r, "success_email", {})
                recipients = self.__value_or_default(email, "recipients", [])
                subject = self.__value_or_default(email, "subject", "")
                assignee = r["assignee"]
                publish_roles = self.__value_or_default(r, "publish_roles", [])

                result.append(ReportConfig(r["report_name"],
                                           params,
                                           recipients,
                                           subject,
                                           assignee,
                                           publish_roles))
        return result

    def __server(self, name):
        return self.cfg["servers"][name]

    def __task(self, name):
        return self.cfg["tasks"][name]

    def __montagu(self):
        return self.__server("montagu")

    def __smtp(self):
        return self.__server("smtp")

    @staticmethod
    def __value_or_default(obj, key, default):
        return obj[key] if key in obj else default
