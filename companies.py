from imapencoding import create_sqlite_connection

# def create_sqlite_connection():
    
#     conn = None
#     try:
#         conn = sqlite3.connect("instance/emailtracker.db")
#     except sqlite3.Error as e:
#         print('Error occured - ', e)

#     # how do we close db connection

#     cursor = conn.cursor()

#     init_table = '''CREATE TABLE IF NOT EXISTS COMPANIES (
#     id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
#     domain VARCHAR(50),
#     company VARCHAR(50));'''

#     # consider indexing domain

#     cursor.execute(init_table)

#     return conn

def persist_email(conn, company_data):
    insert_sql = '''INSERT INTO COMPANIES VALUES (?,?,?)'''

    cursor = conn.cursor()
    cursor.execute(insert_sql, company_data)

    conn.commit()

def get_company_data(conn):
    with open('entities.txt') as f:
        for line in f:
            line = line.strip()
            column = line.split(":")

            data = (None, column[0], column[1])
            persist_email(conn, data)

    return

if __name__ == "__main__":
    conn = create_sqlite_connection("COMPANIES")
    get_company_data(conn)