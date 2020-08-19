import montagu
import orderlyweb_api


def get_authorised_client(config):
    monty = montagu.MontaguAPI(config.montagu_url, config.montagu_user,
                               config.montagu_password)
    ow = orderlyweb_api.OrderlyWebAPI(config.orderlyweb_url,
                                      monty.token)
    return ow


class OrderlyWebClientWrapper:
    def __init__(self, config, auth=get_authorised_client):
        self.config = config
        self.auth = auth
        self.ow = auth(config)

    def execute(self, func, *args):
        try:
            return func(*args)
        except Exception as ex:
            if "expired" in str(ex):
                self.ow = self.auth(self.config)
                func = getattr(self.ow, func.__name__)
                return func(*args)
            else:
                raise ex
