import os
from YTClient.YTClient import YTClient
from YTClient.YTDataClasses import Command


class YouTrackUtils:
    def __init__(self):
        self.test_touchstone = "touchstone-task-runner-test"
        yt_token = os.environ["YOUTRACK_TOKEN"]
        self.yt = YTClient('https://mrc-ide.myjetbrains.com/youtrack/',
                           token=yt_token)

    def cleanup(self):
        issues = self.yt.get_issues("tag: {}".format(self.test_touchstone))
        if len(issues) > 0:
            self.yt.run_command(Command(issues, "delete"))

    def get_issues(self, query=None, fields=None):
        if query is None:
            query = "summary: {}".format(self.test_touchstone)
        if fields is None:
            fields = ["id"]
        return self.yt.get_issues(query, fields)
