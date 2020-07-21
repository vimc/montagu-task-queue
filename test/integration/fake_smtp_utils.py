import requests


class FakeEmailProperties:
    def __init__(self, subject, to_emails, from_email, text, html):
        self.subject = subject
        self.to_emails = to_emails
        self.from_email = from_email
        self.text = text
        self.html = html


class FakeSmtpUtils:
    def __init__(self, host="localhost", port=1080):
        self.url = "http://{}:{}/api/emails".format(host, port)

    # Test that the emails send to the fake smtp server match the given
    # array of email properties, where first item in the array = most recent
    def assert_emails_match(self, email_props_list):
        emails = requests.get(self.url).json()
        assert len(emails) == len(email_props_list)
        for email_props in email_props_list:
            email = emails.pop()
            assert email["subject"] == email_props.subject
            to = email["to"]["value"]
            assert len(to) == len(email_props.to_emails)
            for to_addr in email_props.to_emails:
                assert to.pop(0)["address"] == to_addr
            assert email["from"]["value"][0]["address"] == \
                email_props.from_email
            assert email["text"] == email_props.text
            assert email["html"] == email_props.html

    def delete_all(self):
        requests.delete(self.url)
