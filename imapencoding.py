import email, email.parser, email.policy
import os
from os.path import join, dirname
import re
from dotenv import load_dotenv
from imaplib import IMAP4_SSL
import html2text


dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

h = html2text.HTML2Text()
h.ignore_links = False


def login_mail_client(email_address):
    SMTP_SERVER = 'imap.gmail.com'
    SMTP_PORT = 993

    password = os.environ.get("PASSWORD")

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

def header_decode(header):
    hdr = ""
    for text, encoding in email.header.decode_header(header):
        if isinstance(text, bytes):
            text = text.decode(encoding or "us-ascii")
        hdr += text
    return hdr

def process_mail(mail):
    with open('email_dump4.txt', 'w') as f:
        status, response = mail.search(None, "(ALL)")
        if status == "OK" and response != "":
            for mail_id in response[0].split()[0:10]:
                f.write("\n\n===========Mail[{}]===========\n".format(mail_id))
                status, response = mail.fetch(mail_id, '(RFC822)')
                message = email.message_from_bytes(response[0][1], policy=email.policy.default)

                f.write("Subject:     {}\n".format(header_decode(message.get('Subject'))))

                sender_address = header_decode(message.get('From'))
                if sender_address:
                    pattern = re.compile(r"\<.*?\>")
                    address = re.search(pattern, sender_address)
                    if address:
                        newline = address.group() #todo write func to sanitize strings. remove unnecessary chars and spaces
                        f.write("Sender's Email Address: {}\n".format(newline))

                links = ""
                entire_body = ""
                image_url = ""

                if message.is_multipart():
                    for part in message.walk():
                        content_type = part.get_content_type()
                        content_charset = part.get_content_charset()
                        content_transfer_encoding = part.get("Content-Transfer-Encoding")
                        body_lines = part.as_string().split("\n")

                        for line in body_lines:
                            sender_mailserver = re.search("(Received: from)", line)
                            if sender_mailserver:
                                pattern = re.compile(r"\((.*?)\)")
                                mailserver = re.search(pattern, sender_mailserver.string)
                                if mailserver:
                                    newline_ms = mailserver.group(1)
                                    f.write("Sender's Mail Server: {}\n".format(newline_ms))

                        if part.get_content_maintype() == "text":
                            body = part.get_content()

                            if part.get_content_subtype() == "html":
                                try: 
                                    body = h.handle(body)
                                    if body is not None:
                                        entire_body += body
                                except:
                                    print("html2text failed to work")

                else:
                    content_type = message.get_content_type()
                    content_charset = message.get_content_charset()
                    content_transfer_encoding = message.get("Content-Transfer-Encoding")
                    body_lines = message.as_string().split("\n")

                    if message.get_content_maintype() == "text":
                        body = message.get_content()

                    if message.get_content_subtype() == "html":
                        try: 
                            body = h.handle(body)
                            if body is not None:
                                entire_body += body
                        except:
                            print("html2text failed to work")

                f.write("Links found:\n")
                new_lines = entire_body.split("\n")
                for line in new_lines:
                    pattern = re.compile(r"\(([^)]+)\)")
                    matchResult = pattern.search(line)
                    if matchResult:
                        potential_ext = (".png", ".jpeg", ".jpg", ".gif")
                        if matchResult.group(1).endswith(potential_ext):
                            image_url += str(matchResult.group(1)) + "\n"
                            # print("gatteeem")
                        elif "tel:" in matchResult.group(1) or "mailto:" in matchResult.group(1):
                            pass
                        else:
                            matchResult = matchResult.group(1)
                            f.write("{}\n".format(matchResult))
                #         print(f"2 {image_url}")
                #     print(f"1 {image_url}")
                # print(f"3 {image_url}")

                f.write("Images found:\n{}".format(image_url))
                    # if matchResult:
                    #     links += matchResult
                # print(links)


if __name__ == "__main__":
    mail = login_mail_client(os.environ.get("ADDRESS"))
    get_mail(mail)
    os._exit(1)

