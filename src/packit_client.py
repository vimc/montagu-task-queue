import montagu

# TODO: How will we be able to recognise expired token?
# TODO: How to authenticate? user and pw from vault or something smarter?

class PackitClient:
    def __init__(self, config):
        self.config = config

    #def __get()
    #def __post()
    #def run_packet()
    #def poll_running_packet()
    #def kill_running_packet()