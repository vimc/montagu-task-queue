import yaml


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
