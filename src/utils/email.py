import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class Emailer:

    def __init__(self, smtp_host, smtp_port, smtp_user, smtp_password):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password

    def send(self, from_email, to_emails, subject_template,
             content_template_name, template_values):
        text_template = self.read_file(content_template_name + ".txt")
        html_template = self.read_file(content_template_name + ".html")

        text_msg = self.apply_template_values(text_template, template_values)
        html_msg = self.apply_template_values(html_template, template_values)
        subject = self.apply_template_values(subject_template, template_values)

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = ", ".join(to_emails)

        part1 = MIMEText(text_msg, 'plain')
        part2 = MIMEText(html_msg, 'html')

        msg.attach(part1)
        msg.attach(part2)

        smtp = smtplib.SMTP(self.smtp_host, self.smtp_port)
        smtp.starttls()
        if self.smtp_user is not None and self.smtp_password is not None:
            smtp.login(self.smtp_user, self.smtp_password)
        smtp.sendmail(from_email, to_emails, msg.as_string())
        smtp.quit()
        logging.info("Successfully sent email")

    @staticmethod
    def read_file(filename):
        with open("config/email_templates/" + filename, "r") as file:
            return file.read()

    @staticmethod
    def apply_template_values(template, values):
        return template.format(**values)
