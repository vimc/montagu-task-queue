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
