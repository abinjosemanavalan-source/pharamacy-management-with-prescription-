import mysql.connector
from config import MYSQL_CONFIG

db = mysql.connector.connect(**MYSQL_CONFIG)
cursor = db.cursor()

# ALTER staff table
try:
    cursor.execute("ALTER TABLE staff ADD COLUMN address VARCHAR(255)")
except Exception as e: print(e)

try:
    cursor.execute("ALTER TABLE staff ADD COLUMN photo VARCHAR(200)")
except Exception as e: print(e)

# CREATE tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ratings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    value INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS complaints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

db.commit()
cursor.close()
db.close()
print("DB Updates applied.")
