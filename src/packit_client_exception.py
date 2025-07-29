class PackitClientException(Exception):
    def __init__(self, response):
        self.response = response
        json = response.json()
        msg = "Unexpected response status from Packit API: " + \
            f"{response.status_code}."
        if "error" in json and "detail" in json["error"]:
            detail = json["error"]["detail"]
            msg = f"{msg} Detail: {detail}"
        super().__init__(msg)
