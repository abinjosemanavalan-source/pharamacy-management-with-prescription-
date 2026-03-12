import mysql.connector
from config import MYSQL_CONFIG

def fix_orders():
    print("Connecting to database...")
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        print("Dropping existing 'orders' table...")
        cursor.execute("DROP TABLE IF EXISTS orders")

        print("Creating 'orders' table with correct columns...")
        cursor.execute("""
            CREATE TABLE orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                medicine_name VARCHAR(100),
                quantity INT,
                price DECIMAL(10,2),
                total DECIMAL(10,2),
                order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                payment_method VARCHAR(50),
                status VARCHAR(30) DEFAULT 'Pending',
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        conn.commit()
        print("Table 'orders' recreated successfully!")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    fix_orders()
