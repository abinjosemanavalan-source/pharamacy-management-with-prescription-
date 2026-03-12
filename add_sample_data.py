import mysql.connector
from config import MYSQL_CONFIG
from datetime import datetime

def add_sample_orders():
    print("Connecting to database...")
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        # Get Admin user id
        cursor.execute("SELECT id FROM users WHERE email='abinjosemanavalan@gmail.com'")
        user = cursor.fetchone()
        if not user:
            print("Admin user not found.")
            return
        
        user_id = user[0]

        print(f"Adding sample orders for user_id {user_id}...")
        sample_orders = [
            (user_id, 'Paracetamol 500mg', 2, 25.00, 50.00, 'Cash on Delivery', 'Completed'),
            (user_id, 'Amoxicillin 250mg', 1, 120.00, 120.00, 'Online Payment', 'Pending'),
            (user_id, 'Cetirizine', 3, 30.00, 90.00, 'Online Payment', 'Cancelled')
        ]

        query = """
            INSERT INTO orders (user_id, medicine_name, quantity, price, total, payment_method, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.executemany(query, sample_orders)
        conn.commit()
        print("Sample orders added successfully!")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    add_sample_orders()
