from imaplib import IMAP4_SSL
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import email
import re

load_dotenv()
# make check to ignore mail without mulitpart/ content type
# instead of regex see email.message.EmailMessage.ismultipart() or do get_content_type() plus regex
# kaplan's emails are sent via bounce? can't accurately get sender's server. probably through salesforce or some alt
# https://www.rfc-editor.org/rfc/rfc3501#section-6.4.5

def login_mail_client(email_address):
    SMTP_SERVER = 'imap.gmail.com'
    SMTP_PORT = 993

    password = os.getenv("PASSWORD")

    try:
        mail = IMAP4_SSL(SMTP_SERVER, SMTP_PORT)
    except Exception as e:
        print("ErrorType : {}, Error : {}".format(type(e).__name__, e))

    try:
        mail.login(email_address, password)
    except Exception as e:
        print("ErrorType : {}, Error : {}".format(type(e).__name__, e))
    return mail

def get_mail(mail):
    status, response = mail.select("INBOX", False)
    if status == 'OK':
        print("Processing mailbox...\n")
        process_mail(mail)
        mail.close()
    else:
        print("ERROR: Unable to open mailbox ", status)

    mail.logout()


def process_mail(mail):
    with open('email_dump.txt', 'w') as f:
        status, response = mail.search(None, "ALL")
        for mail_id in response[0].split()[-10:]:
            f.write("===========Mail[{}]===========\n\n".format(mail_id))
            status, response = mail.fetch(mail_id, '(RFC822)')
            message = email.message_from_bytes(response[0][1])
            f.write("Subject:     {}\n".format(message.get("Subject")))
            # f.write("Body:\n")
            for part in message.walk():
            # if part.get_content_type() == "multipart/alternative":
                # tesst = part.get_content_subtype()
                tesst = part.get_payload()
                soup = BeautifulSoup(str(tesst), "html.parser")
                body_lines = part.as_string().split("\n")
                # text = "".join(body_lines)
                for line in body_lines:
                    sender_address = re.search("(From:)", line)
                    if sender_address:
                        pattern = re.compile(r"\<.*?\>")
                        address = re.search(pattern, sender_address.string)
                        if address:
                            newline = address.group()
                            f.write("Sender's Email Address: {}\n".format(newline))
                    sender_mailserver = re.search("(Received: from)", line)
                    if sender_mailserver:
                        pattern = re.compile(r"\((.*?)\)")
                        mailserver = re.search(pattern, sender_mailserver.string)
                        if mailserver:
                            newline_ms = mailserver.group()
                            f.write("Sender's Mail Server: {}\n".format(newline_ms))
            # TODO: fix email marketing search section
            # mail_marketing = re.search("(mailchimp|yesnow|Mailchimp|Yesnow|mailerlite|sendinblue|moosend|zoho|shopify|aweber|omnisend|pabbly|sendx|autopilot)", line)
            # if mail_marketing:
            #     print(mail_marketing)
            #     f.write("Email Marketing Providers Found:\n{}\n".format(mail_marketing))
            # avail_links = re.findall("(?:https?|ftp|file)", line)
            # avail_links = len(re.findall("(?:https?)", line))
            avail_links = [a.get('href') for a in soup.find_all('a', href=True)]
            avail_links.extend([img.get('src') for img in soup.find_all('img', src=True)]) 
            if avail_links:
                f.write("Links Found in Email:\n{}\n".format(avail_links))
                
            f.write("Email Marketing Providers Found: \n")
            f.write("\n=============END===========\n\n")
    f.close()


if __name__ == "__main__":
    mail = login_mail_client(os.getenv('ADDRESS'))
    get_mail(mail)
    os._exit(1)



