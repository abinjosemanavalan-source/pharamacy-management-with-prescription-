from update_db import update_db
import mysql.connector
from werkzeug.security import generate_password_hash
from config import MYSQL_CONFIG

def fix_user():
    # first run standard updates
    update_db()

    print("\nFixing user data...")
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        email = "abinjosemanavalan@gmail.com"
        # Check if user exists
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone() # returns tuple or None

        if user:
            print(f"User {email} found.")
            hashed_pw = generate_password_hash("123456")
            
            # Update password and name
            # Assuming 'name' column was just added by update_db() so it will be NULL
            print(f"Updating password to hashed '123456' and name to 'Admin'...")
            cursor.execute(
                "UPDATE users SET password=%s, name='Admin' WHERE email=%s",
                (hashed_pw, email)
            )
            conn.commit()
            print("User updated successfully.")
        else:
            print(f"User {email} not found. Creating it...")
            hashed_pw = generate_password_hash("123456")
            cursor.execute(
                "INSERT INTO users (name, email, password, role) VALUES ('Admin', %s, %s, 'admin')",
                (email, hashed_pw)
            )
            conn.commit()
            print("User created successfully.")

        cursor.close()
        conn.close()

    except mysql.connector.Error as err:
        print(f"Error: {err}")

if __name__ == "__main__":
    fix_user()
