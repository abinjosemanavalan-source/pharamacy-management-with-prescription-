import mysql.connector
from config import MYSQL_CONFIG

def check_db():
    try:
        print("Connecting to DB...")
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        print("Executing DESCRIBE users...")
        cursor.execute("DESCRIBE users")
        columns = cursor.fetchall()
        
        print("Executing DESCRIBE medicines...")
        cursor.execute("DESCRIBE medicines")
        med_columns = cursor.fetchall()
        
        with open("results.txt", "a", encoding="utf-8") as f:
            f.write("\nMedicines Columns:\n")
            for col in med_columns:
                f.write(str(col) + "\n")
            
            f.write("\nMedicines Data:\n")
            cursor.execute("SELECT * FROM medicines")
            medicines = cursor.fetchall()
            for med in medicines:
                f.write(str(med) + "\n")

        print("Executing DESCRIBE orders...")
        try:
            cursor.execute("DESCRIBE orders")
            order_columns = cursor.fetchall()
            with open("results.txt", "a", encoding="utf-8") as f:
                f.write("\nOrders Columns:\n")
                for col in order_columns:
                    f.write(str(col) + "\n")
                
                f.write("\nOrders Data:\n")
                cursor.execute("SELECT * FROM orders")
                orders = cursor.fetchall()
                for order in orders:
                    f.write(str(order) + "\n")
            print("Done. Appended orders info to results.txt")
        except mysql.connector.Error as err:
            print(f"Error checking orders: {err}")
            with open("results.txt", "a", encoding="utf-8") as f:
                f.write(f"\nError checking orders: {err}\n")

        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        with open("results.txt", "a", encoding="utf-8") as f:
             f.write(f"\nError: {err}")

if __name__ == "__main__":
    check_db()


