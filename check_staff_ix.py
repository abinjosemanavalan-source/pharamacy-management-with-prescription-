import mysql.connector
from config import MYSQL_CONFIG

db = mysql.connector.connect(**MYSQL_CONFIG)
cursor = db.cursor()

def fetch_table(table):
    try:
        cursor.execute(f"DESCRIBE {table}")
        res = cursor.fetchall()
        print(f"--- {table} ---")
        for i, row in enumerate(res):
            print(i, row[0], row[1])
    except Exception as e:
        pass

fetch_table("staff")

cursor.close()
db.close()
