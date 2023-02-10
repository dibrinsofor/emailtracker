import email, email.parser, email.policy
from os.path import join, dirname, exists
import re
import sqlite3
from dotenv import load_dotenv
from imaplib import IMAP4_SSL
import html2text
from datetime import datetime
from csv import writer
from tld import get_fld


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

    def append_file(self, email_md5):
        with open("{}_email_dump.txt".format(email_md5), "a", encoding="utf-8") as g:
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
    def __init__(self, month, year, domain_name, tracking_service, secure_links, unsecure_links):
        # we want to know the year of mail, number of secure links, number of unsecure links, company name or 
        self.month = month
        self.year = year
        self.domain_name = domain_name
        self.secure_links = secure_links
        self.unsecure_links = unsecure_links
        self.tracking_service = tracking_service

    def append_file(self, email_md5):
        with open("{}_results_data.csv".format(email_md5), "a", encoding="utf-8") as f:
            row = [self.month, self.year, self.domain_name, self.tracking_service, self.secure_links, self.unsecure_links]
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
def create_sqlite_connection(table_name, email_md5):

    conn = None
    try:
        conn = sqlite3.connect("instance/emailtracker.db")
    except sqlite3.Error as e:
        print('Error occured - ', e)
    
    cursor = conn.cursor()

    if table_name == "[{}_EMAIL_DUMP]".format(email_md5): 
        init_table = '''CREATE TABLE IF NOT EXISTS {table} (
        email_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        domain VARCHAR(50),
        secure_links INTEGER,
        unsecure_links INTEGER,
        email_date TIMESTAMP,
        tracking_service VARCHAR(100)
        )'''.format(table=str(table_name))

        cursor.execute(init_table)
        # cursor.execute('''CREATE TABLE IF NOT EXISTS {table} (
        # email_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        # domain VARCHAR(50),
        # secure_links INTEGER,
        # unsecure_links INTEGER,
        # email_date TIMESTAMP,
        # tracking_service VARCHAR(100)
        # )'''.format(table=table_name))

    elif table_name == "COMPANIES":
        init_table = '''CREATE TABLE IF NOT EXISTS COMPANIES (
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        domain VARCHAR(50),
        company VARCHAR(50)
        );'''

        # consider indexing domain

        cursor.execute(init_table)

    # consider storing the number of emails scanned and maybe some of the other data we'd need for results.html upfront
    # consider this too. [domain = db.Column(db.String(40))] maybe some domains recieve more unecrypted mails
    elif table_name == "USERS":
        init_table = '''CREATE TABLE IF NOT EXISTS USERS (
        id VARCHAR(50) PRIMARY KEY NOT NULL,
        emails_scanned INTEGER,
        links_found INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );'''


        cursor.execute(init_table)
        cursor.execute('INSERT INTO "USERS"(id, emails_scanned, links_found) SELECT (?), 0, 0 WHERE NOT EXISTS (SELECT * FROM "USERS" WHERE id=(?))', (email_md5, email_md5))
        cursor.execute("commit")


    return conn

def persist_email(email_data, email_md5):
    # table_name = email_md5 + "_EMAIL_DUMP"
    table_name = "[{}_EMAIL_DUMP]".format(email_md5)
    conn = create_sqlite_connection(table_name, email_md5)
    # insert_sql = '''INSERT INTO EMAIL_DUMP VALUES (?,?,?,?,?,?)'''
    insert_sql = "INSERT INTO " + str(table_name) + " VALUES (?,?,?,?,?,?)"
    cursor = conn.cursor()
    cursor.execute(insert_sql, email_data)

    conn.commit()
    # conn.close()

def get_company(domain):
    conn = create_sqlite_connection("COMPANIES", None)
    cursor = conn.cursor()
    data = cursor.execute("SELECT company FROM COMPANIES WHERE domain=?", (domain,))
    company = data.fetchone()
    conn.close()
    if company is None:
        return domain
        # TODO: let's collect domains that aren't found.

    return company[0]

def get_user(email_md5):
    conn = create_sqlite_connection("USERS", email_md5)
    cursor = conn.cursor()

    data = cursor.execute("SELECT * FROM USERS WHERE id=?", (email_md5,))
    user =  data.fetchone()
    print(user)
    conn.close()

    if user is None:
        return ""

    return user[0] 

def add_user(user_data, email_md5):
    insert_sql = '''INSERT INTO USERS VALUES (?,?,?,?)'''

    conn = create_sqlite_connection("USERS", email_md5)
    cursor = conn.cursor()
    cursor.execute(insert_sql, user_data)

    conn.commit()
    return 


def get_mail(mail, email_md5):
    if exists("{}_email_dump.txt".format(email_md5)):
        pass
    else:
        open("{}_email_dump.txt".format(email_md5), "w", encoding='utf-8')

    if exists("{}_results_data.csv".format(email_md5)):
        pass
    else:
        with open("{}_results_data.csv".format(email_md5), "w", encoding='utf-8') as f:
            header = ['Month', 'Year', 'Domain', 'Tracking Service', 'Secure', 'Unsecure']
            cursor = writer(f)
            cursor.writerow(header)
    
    # table_name = email_md5 + "_EMAIL_DUMP"
    table_name = "[{}_EMAIL_DUMP]".format(email_md5)
    # count_table = "SELECT Count(email_id) FROM ?;"
    count_table = "SELECT Count(email_id) FROM {}".format(table_name)
    conn = create_sqlite_connection(table_name, email_md5)
    cursor = conn.cursor()
    cursor.execute(count_table)
    last_email_checked = cursor.fetchone()[0]

    status, response = mail.select("INBOX", False)
    if status == 'OK':
        print("SUCCESS\n")
        process_mail(mail, last_email_checked, email_md5)
        mail.close()
    else:
        print("ERROR: Unable to open mailbox ", status)

    mail.logout()

    # pass email hash and get stored count of emails_scanned and links_found
    emails_scanned, links_found = get_count(email_md5)

    return emails_scanned, links_found

def header_decode(header):
    hdr = ""
    for text, encoding in email.header.decode_header(header):
        if isinstance(text, bytes):
            text = text.decode(encoding or "us-ascii")
        hdr += text
    return hdr

def get_count(email_md5):
    # conn = create_sqlite_connection("SCAN_DATA")
    conn = create_sqlite_connection("USERS", email_md5)
    cursor = conn.cursor()
    # data = cursor.execute("SELECT * FROM SCAN_DATA")
    data = cursor.execute("SELECT * FROM USERS WHERE id=?", (email_md5,))
    row = data.fetchone()
    print(cursor.fetchone())
    conn.close()

    if row is not None:
        emails_scanned = row[1]
        links_found = row[2]
    else:
        emails_scanned = 0
        links_found = 0

    # print("emails_scanned: {}".format(emails_scanned))
    # print("links_found: {}".format(links_found))
    # print(row)

    return emails_scanned, links_found

def update_count(emails_scanned, links_found, email_md5):
    # conn = create_sqlite_connection("SCAN_DATA")
    conn = create_sqlite_connection("USERS", email_md5)
    conn.isolation_level = None
    cursor = conn.cursor()
    
    data = cursor.execute("select emails_scanned, links_found from USERS where id=?", (email_md5,))
    rows = data.fetchone()
    # print(rows)
    if rows is not None:      
        cur_emails_scanned = int(rows[0])
        cur_links_found = int(rows[1])
    else:
        cur_emails_scanned = 0
        cur_links_found = 0

    cursor.execute("begin")
    try:
        cursor.execute("update USERS set emails_scanned=? where id=?", ((cur_emails_scanned + emails_scanned), email_md5))
        cursor.execute("update USERS set links_found=? where id=?", ((cur_links_found + links_found), email_md5))
        cursor.execute("commit")
        # print(cursor.fetchone())
    except conn.Error:
        cursor.execute("rollback")

def process_mail(mail, start, email_md5):
    no_links_found = 0
    emails_scanned = 0

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
                fld = get_fld(tracking_service, fix_protocol=True)
                tracking_service = get_company("{}".format(fld))
            
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
            email_data.append_file(email_md5)

            # if mail_server[0] == "[":
            #     mail_server = mail_server[1:-1]

            table_data = EmailAdd(month, date.year, domain_name, tracking_service, secure_links, unsecure_links)
            table_data.append_file(email_md5)
            
            data = (None, domain_name, secure_links, unsecure_links, date, tracking_service)
            persist_email(data, email_md5)

            # is table empty? if no get val and add to no_links_found and emails_scanned
            # what happens if something fails

    update_count(emails_scanned, no_links_found, email_md5)

    # return no_links_found, emails_scanned

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
