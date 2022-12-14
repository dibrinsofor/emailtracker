import email, email.parser, email.policy
from os.path import join, dirname, exists
import re
import sqlite3
from dotenv import load_dotenv
from imaplib import IMAP4_SSL, IMAP4
import html2text
from datetime import datetime
from csv import writer


dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

h = html2text.HTML2Text()
h.ignore_links = False

class Email():
    emails_scanned = 0

    def __init__(self, mail_id, subject, sender, sender_mail_server, links, images, tracking_squares):
        self.mail_id = mail_id
        self.subject = subject
        self.sender = sender
        self.sender_mail_server = sender_mail_server
        self.links = links
        self.images = images
        self.tracking_squares = tracking_squares
        Email.emails_scanned += 1

    def append_file(self):
        with open("email_dump.txt", "a", encoding="utf-8") as g:
            g.write("\n\n===========Mail[{}]===========\n".format(self.mail_id)) #id looks like this b'7'
            g.write("Subject:     {}\n".format(self.subject))
            g.write("Sender's Email Address: {}\n".format(self.sender))
            g.write("Sender's Mail Server: {}\n".format(self.sender_mail_server))
            g.write("Links Found:\n{}".format(self.links))
            g.write("Images Found:\n{}".format(self.images))
            if self.tracking_squares != "":
                g.write("Tracking Squares Found: \n{}".format(self.tracking_squares))
            else:
                g.write("NO TRACKING SQUARES FOUND")
        pass

class EmailAdd():
    def __init__(self, month, year, domain_name, secure_links, unsecure_links, tracking_service):
        # we want to know the year of mail, number of secure links, number of unsecure links, company name or 
        self.month = month
        self.year = year
        self.domain_name = domain_name
        self.secure_links = secure_links
        self.unsecure_links = unsecure_links
        self.tracking_service = tracking_service

    def append_file(self):
        with open("results_data.csv", "a", encoding="utf-8") as f:
            row = [self.month, self.year, self.domain_name, self.secure_links, self.unsecure_links, self.tracking_service]
            writer(f).writerow(row)

def login_mail_client(email_address, password):
    SMTP_SERVER = 'imap.gmail.com'
    SMTP_PORT = 993

    mail = None

    try:
        mail = IMAP4_SSL(SMTP_SERVER, SMTP_PORT)
        mail.noop()
    except Exception as e:
        print("ErrorType : {}, Error : {}".format(type(e).__name__, e))

    try:
        mail.login(email_address, password)
    except Exception as e:
        print("ErrorType : {}, Error : {}".format(type(e).__name__, e))
    return mail

# TODO: move to own file, init_db.py
def create_sqlite_connection():

    conn = None
    try:
        conn = sqlite3.connect("instance/emailtracker.db")
    except sqlite3.Error as e:
        print('Error occured - ', e)

    # how do we close db connection

    cursor = conn.cursor()

    init_table = '''CREATE TABLE IF NOT EXISTS EMAIL_DUMP (
    email_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    domain VARCHAR(50),
    secure_links INTEGER,
    unsecure_links INTEGER,
    email_date TIMESTAMP,
    tracking_service VARCHAR(100));'''

    cursor.execute(init_table)

    return conn

def persist_email(conn, email_data):
    insert_sql = '''INSERT INTO EMAIL_DUMP VALUES (?,?,?,?,?,?)'''

    # c.execute("INSERT INTO SurfDate (Day) VALUES (?)", (e,))

    cursor = conn.cursor()
    cursor.execute(insert_sql, email_data)

    conn.commit()

def get_mail(mail):
    if exists("email_dump.txt"):
        pass
    else:
        open("email_dump.txt", "w", encoding='utf-8')

    if exists("results_data.csv"):
        pass
    else:
        with open("results_data.csv", "w", encoding='utf-8') as f:
            header = ['Month', 'Year', 'Domain', 'Secure', 'Unsecure', 'Tracking Service']
            cursor = writer(f)
            cursor.writerow(header)
    
    count_table = "SELECT Count(email_id) from EMAIL_DUMP;"
    conn = create_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute(count_table)
    last_email_checked = cursor.fetchone()[0]

    try:
        status, response = mail.select("INBOX", False)
        if status == 'OK':
            print("SUCCESS\n")
            total = process_mail(mail, last_email_checked)
            mail.close()
            return total
        else:
            print("ERROR: Unable to open mailbox ", status)
    except IMAP4.error:
        print ("LOGIN FAILED")

    mail.logout()

def header_decode(header):
    hdr = ""
    for text, encoding in email.header.decode_header(header):
        if isinstance(text, bytes):
            text = text.decode(encoding or "us-ascii")
        hdr += text
    return hdr

# TODO: we are not curently scanning the first email. fix that 
def process_mail(mail, start):
    no_links_found = 0
    emails_scanned = 0

    conn = create_sqlite_connection()
    #learn how cursors work does it matter when they get invoked is it memory intensive

    status, response = mail.search(None, "(ALL)")
    if status == "OK" and response != "":
        for mail_id in response[0].split()[start:]:
            entire_body = ""
            images_found = ""
            tracking_squares = ""
            links_found = ""
            secure_links = 0
            unsecure_links = 0

            emails_scanned += 1

            tracking_service = "nil"

            status, response = mail.fetch(mail_id, '(RFC822)')
            message = email.message_from_bytes(response[0][1], policy=email.policy.default)   

            subject = header_decode(message.get('Subject'))
            
            date = datetime.strptime(message['Date'], "%a, %d %b %Y %H:%M:%S %z")
            month = date.strftime("%B")

            sender = header_decode(message.get('From'))
            if sender:
                pattern = re.compile(r"\<.*?\>")
                address = re.search(pattern, sender)
                if address:
                    sender = address.group() 
                    #TODO: write func to sanitize strings. remove unnecessary chars and spaces


            received_spf = message['Received-SPF']
            if received_spf:
                tracking_pattern = re.compile(r"@(.*?) ")
                server_pattern = re.compile(r"client-ip=(.*?);")

                tracking_service = re.search(tracking_pattern, str(received_spf))
                tracking_service = tracking_service.group(1)
            
                mail_server = re.search(server_pattern, str(received_spf))
                mail_server = mail_server.group(1)

            domain_name = message['DKIM-Signature']
            if domain_name:
                pattern = re.compile(r"d=(.*?);")
                domain_name = re.search(pattern, str(domain_name))
                domain_name = domain_name.group(1)

            if domain_name is None:
                domain_name = mail_server

            sender_mail_server = "{}".format(domain_name) + " " + "{}".format(mail_server)

            # print(message.keys())
            # keys => ['Delivered-To', 'Received', 'X-Received', 'ARC-Seal', 'ARC-Message-Signature', 'ARC-Authentication-Results', 'Return-Path', 'Received', 'Received-SPF', 'Authentication-Results', 'DKIM-Signature', 'X-Google-DKIM-Signature', 'X-Gm-Message-State', 'X-Google-Smtp-Source', 'MIME-Version', 'X-Received', 'Date', 'Reply-To', 'Precedence', 'List-Unsubscribe', 'Feedback-ID', 'List-Id', 'X-Notifications', 'X-Notifications-Bounce-Info', 'Message-ID', 'Subject', 'From', 'To', 'Content-Type']


            if message.is_multipart():
                for part in message.walk():
                    # content_type = part.get_content_type()
                    # content_charset = part.get_content_charset()
                    # content_transfer_encoding = part.get("Content-Transfer-Encoding")
                    body_lines = part.as_string().split("\n")
                    
                    tracking_links = Find_tracking_pixels(body_lines)
                    if tracking_links:
                        tracking_squares += tracking_links

                    # sender_mail_server = domain_name[12:] + " " + mail_server[14:]

                    # for line in body_lines:
                    #     sender_mailserver = re.search("(Received: from)", line)
                    #     if sender_mailserver:
                    #         pattern = re.compile(r"\((.*?)\)")
                    #         mailserver = re.search(pattern, sender_mailserver.string)
                    #         if mailserver:
                    #             sender_mail_server = mailserver.group(1)
                    #             server_details = sender_mail_server.split(". ")
                    #             domain_name = server_details[0]
                    #             mail_server = server_details[1]
                    #         else:
                    #             sender_mail_server = "None"
                    #             domain_name = "None"
                    #             mail_server = "None"

                    if part.get_content_maintype() == "text":
                        body = part.get_content()

                    if part.get_content_subtype() == "html":
                        try: 
                            ed_body = h.handle(body)
                            if ed_body is not None:
                                entire_body += ed_body
                        except:
                            print("html2text failed to work")

            else:
                # content_type = message.get_content_type()
                # content_charset = message.get_content_charset()
                # content_transfer_encoding = message.get("Content-Transfer-Encoding")
                body_lines = message.as_string().split("\n")
                tracking_links = Find_tracking_pixels(body_lines)
                if tracking_links:
                    tracking_squares += tracking_links

                if message.get_content_maintype() == "text":
                    body = message.get_content()

                if message.get_content_subtype() == "html":
                    try: 
                        ed_body = h.handle(body)
                        if ed_body is not None:
                            entire_body += ed_body
                    except:
                        print("html2text failed to work")

            new_lines = entire_body.split("\n")
            for line in new_lines:
                pattern = re.compile(r"\(([^)]+)\)")
                matchResult = pattern.search(line)
                if matchResult:
                    potential_ext = (".png", ".jpeg", ".jpg", ".gif")
                    secure = ("https://")
                    if matchResult.group(1).endswith(potential_ext):
                        images_found += str(matchResult.group(1)) + "\n"
                        if matchResult.group(1).startswith(secure):
                            no_links_found += 1
                            secure_links += 1
                        else:
                            no_links_found += 1
                            unsecure_links += 1

                    elif "tel:" in matchResult.group(1) or "mailto:" in matchResult.group(1):
                        pass
                    else:
                        link = matchResult.group(1)
                        links_found += link + "\n"
                        if matchResult.group(1).startswith(secure):
                            secure_links += 1
                            no_links_found += 1
                        else:
                            no_links_found += 1
                            unsecure_links += 1

            email_data = Email(mail_id, subject, sender, sender_mail_server, links_found, images_found, tracking_squares)
            email_data.append_file()

            # if mail_server[0] == "[":
            #     mail_server = mail_server[1:-1]

            table_data = EmailAdd(month, date.year, domain_name, secure_links, unsecure_links, tracking_service)
            table_data.append_file()
            
            data = (None, domain_name, secure_links, unsecure_links, date, tracking_service)
            persist_email(conn, data)

    return no_links_found, emails_scanned

def Find_tracking_pixels(html: str) -> str:
    tracking_links = ""
    cases = ['width="1" height="1"', 'width="0" height="0"', 'width: 1px;height: 1px']

    for line in html:
        pattern = re.compile(r"\<img (.*?)\>")
        found_tags = pattern.search(line)
        if found_tags:
            for case in cases:
                if case in str(found_tags.group(0)):
                    tracking_links += str(found_tags.group(0)) + "\n"
                else:
                    pass
    return tracking_links
