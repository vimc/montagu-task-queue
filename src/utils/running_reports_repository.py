import redis


class RunningReportsRepository:
    def __init__(self):
        self.redis = redis.Redis()  # default localhost, port 6379
        self.prefix = "running_report"

    def set(self, group, disease, report_key):
        self.redis.set(self.db_key(group, disease), report_key)

    def get(self, group, disease):
        result = self.redis.get(self.db_key(group, disease))
        if result is not None:
            result = result.decode("utf-8")
        return result

    def delete(self, group, disease):
        self.redis.delete(self.db_key(group, disease))

    def db_key(self, group, disease):
        return "{}_{}_{}".format(self.prefix, group, disease)
