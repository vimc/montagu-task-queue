import redis


class RunningReportsRepository:
    def __init__(self, host="localhost"):
        self.redis = redis.Redis(host=host)  # default port 6379
        self.prefix = "running_report"

    def set(self, group, disease, report_name, report_key):
        self.redis.set(self.db_key(group, disease, report_name), report_key)

    def get(self, group, disease, report_name):
        result = self.redis.get(self.db_key(group, disease, report_name))
        if result is not None:
            result = result.decode("utf-8")
        return result

    def delete_if_matches(self, group, disease, report_name,
                          expected_report_key):
        # Delete a running report value, but only if it matches an expected
        # value - i.e. has not been overwritten by a subsequent task
        db_key = self.db_key(group, disease, report_name)

        def transaction_method(pipe: redis.client.Pipeline) -> None:
            value = pipe.get(db_key)
            if value is not None and \
                    value.decode("utf-8") == expected_report_key:
                pipe.delete(db_key)
        self.redis.transaction(transaction_method, *[db_key])

    def db_key(self, group, disease, report_name):
        return "{}_{}_{}_{}".format(self.prefix, group, disease, report_name)
