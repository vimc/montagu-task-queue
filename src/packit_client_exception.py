class PackitClientException(Exception):
    def __init__(self, response):
        self.response = response
        json = response.json()
        msg = "Unexpected response status from Packit API: " + \
            f"{response.status_code}."
        if "error" in json and "detail" in json["error"]:
            msg = f"{msg} Detail: {json["error"]["detail"]}"
        super().__init__(msg)
