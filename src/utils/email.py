import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class Emailer:

    def __init__(self, smtp_host, smtp_port):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port

    def send(self, from_email, to_emails, subject_template,
             content_template_name, template_values):
        #text_message = """This is a test e-mail message."""
        #html_message = """This is a <strong>test</strong> e-mail message."""

        text_template = self.read_file(content_template_name + ".txt")
        html_template = self.read_file(content_template_name + ".html")

        text_msg = self.apply_template_values(text_template, template_values)
        html_msg = self.apply_template_values(html_template, template_values)
        subject = self.apply_template_values(subject_template, template_values)

        #from_email = "from@example.com"
        #to_emails = ["to1@example.com", "to2@example.com"]

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_email
            msg['To'] = ", ".join(to_emails)

            part1 = MIMEText(text_msg, 'plain')
            part2 = MIMEText(html_msg, 'html')

            msg.attach(part1)
            msg.attach(part2)

            #smtp = smtplib.SMTP('localhost', 1025)
            smtp = smtplib.SMTP(self.smtp_host, self.smtp_port)
            smtp.sendmail(from_email, to_emails, msg.as_string())
            smtp.quit()
            logging.info("Successfully sent email")
        except smtplib.SMTPException as ex:
            #TODO something better
            logging.error("Error: unable to send email")
            return "fail: " + str(ex)

    @staticmethod
    def read_file(filename):
        with open("config/email_templates/" + filename, "r") as file:
            return file.read()

    @staticmethod
    def apply_template_values(template, values):
        #TODO: be more defensive, this can blow up if template key not found
        return template.format(**values)
