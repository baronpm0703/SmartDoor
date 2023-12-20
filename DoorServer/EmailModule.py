import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class EmailModule():
    def __init__(self, gmail_username, gmail_password):
        self.gmail_username = gmail_username
        self.gmail_password = gmail_password

        # Gmail SMTP server configuration
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587  # Gmail SMTP port

        # Create a secure SSL context
        self.context = smtplib.SMTP(self.smtp_server, self.smtp_port)
        self.context.starttls()

        # Login to Gmail
        self.context.login(self.gmail_username, self.gmail_password)

    def sendMail(self, receiver_email, subject, body):
        # Setup the MIME
        message = MIMEMultipart()
        message['From'] = self.gmail_username
        message['To'] = receiver_email
        message['Subject'] = subject

        # Attach the body to the MIME message
        message.attach(MIMEText(body, 'plain'))

        # Send Email
        self.context.sendmail(self.gmail_username, receiver_email, message.as_string())
    
    def closeConnection(self):
        # Close the SMTP connection
        self.context.quit()