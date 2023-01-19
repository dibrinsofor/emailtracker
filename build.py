import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
import sys

load_dotenv()
if len(sys.argv) > 3:
    print("too many arguments passed")
    sys.exit()
if len(sys.argv) < 1:
    print("no arguments passed")

def setup_environment():
    # install proj dependencies
    print("Installing project dependencies...")
    os.system("pip install -r requirements.txt")
    # check if companies.py exists and is up to date
    print("Checking if company registry is up to date...")
    try:
        try:
            conn = sqlite3.connect("instance/emailtracker.db")
        except sqlite3.Error as e:
                print('Error occured - ', e)

        cursor = conn.cursor()
        cursor.execute('''SELECT Count(id) FROM COMPANIES''')
        row_count = cursor.fetchone()[0]

        lines_companies = sum(1 for _ in open('entities.txt'))

        if row_count == (lines_companies - 1):
            print("Company registry is up to date")
    except sqlite3.OperationalError:
        # create and fill table
        os.system("python3 companies.py")
        print("Company registry is up to date")

    if os.path.exists("./instance/emailtracker.db"):
        # connect to db and drop table
        conn = sqlite3.connect('./instance/emailtracker.db')
        cursor = conn.cursor()
        cursor.execute('''DROP TABLE IF EXISTS EMAIL_DUMP''')
        print("Dropping stale tables")
        conn.commit()
        conn.close()
        pass
    else:
        pass
    # move old files around if exist
    if os.path.exists("email_dump.txt") or os.path.exists("results_data.csv"):
        path = "old_scans"

        last_modified_dump = os.path.getmtime("email_dump.txt")
        last_modified_csv = os.path.getmtime("results_data.csv")

        last_modified_dump = datetime.fromtimestamp(last_modified_dump)
        last_modified_csv = datetime.fromtimestamp(last_modified_csv)

        last_modified_dump = last_modified_dump.strftime("%Y%m%d-%H%M%S")
        last_modified_csv = last_modified_csv.strftime("%Y%m%d-%H%M%S")

        if not os.path.exists(path):
            os.makedirs(path)
        
        os.rename("email_dump.txt", f"old_scans/email_dump_{last_modified_dump}.txt")
        os.rename("results_data.csv", f"old_scans/results_data_{last_modified_csv}.csv")

def run_build(flag, name=None):
    if flag == "-f":
        # run flask app
        if name == "debug":
            os.system("flask --debug run")
        else:
            os.system("flask run")

    elif flag == "-s":
        # setup environment
        # install proj dependencies
        # check if companies.py exists and is up to date
        # move old files around if exist
        setup_environment()
        print("All set! You can now run `python build.py -f` or `flask run` to run your developent server.")
    else:
        # run full build: setup environment and spin up a development server
        setup_environment()
        print("All set! Let's get the server up and running...")
        # run flask app 
        os.system("flask run")

if __name__ == "__main__":
    run_build(*sys.argv[1:])
