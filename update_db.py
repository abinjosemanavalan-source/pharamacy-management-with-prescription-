import mysql.connector
from config import MYSQL_CONFIG

def update_db():
    print("Connecting to database...")
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        print("Checking 'users' table schema...")
        cursor.execute("DESCRIBE users")
        columns = [column[0] for column in cursor.fetchall()]
        print(f"Current columns: {columns}")

        # 0. Add Name if missing
        if 'name' not in columns:
            print("Adding 'name' column...")
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN name VARCHAR(100) AFTER id")
                print("Column 'name' added successfully.")
            except mysql.connector.Error as e:
                print(f"Error adding name column: {e}")
        
        # 1. Handle Email/Username migration
        if 'email' not in columns:
            if 'username' in columns:
                print("Migrating 'username' column to 'email'...")
                try:
                    # Rename username to email. Preserving NOT NULL.
                    # Note: We aren't forcing UNIQUE here to avoid errors if duplicates exist, 
                    # but typically it should be unique.
                    cursor.execute("ALTER TABLE users CHANGE username email VARCHAR(100) NOT NULL")
                    print("Column renamed successfully.")
                except mysql.connector.Error as e:
                     print(f"Error renaming column: {e}")
            else:
                print("Adding 'email' column...")
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR(100) UNIQUE NOT NULL")
                except mysql.connector.Error as e:
                    print(f"Error adding email column: {e}")
        
        # 2. Add Role if missing
        if 'role' not in columns:
            print("Adding 'role' column...")
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN role ENUM('admin', 'pharmacist', 'user') DEFAULT 'user'")
            except mysql.connector.Error as e:
                print(f"Error adding role column: {e}")
        
        # 3. Add Phone if missing
        if 'phone' not in columns:
             print("Adding 'phone' column...")
             try:
                cursor.execute("ALTER TABLE users ADD COLUMN phone VARCHAR(20)")
             except mysql.connector.Error as e:
                print(f"Error adding phone column: {e}")

        # 4. Check 'medicines' table schema
        print("Checking 'medicines' table schema...")
        cursor.execute("DESCRIBE medicines")
        med_columns = [column[0] for column in cursor.fetchall()]
        if 'requires_prescription' not in med_columns:
            print("Adding 'requires_prescription' column to medicines...")
            try:
                cursor.execute("ALTER TABLE medicines ADD COLUMN requires_prescription BOOLEAN DEFAULT FALSE")
            except mysql.connector.Error as e:
                print(f"Error adding requires_prescription column: {e}")

        # 5. Create other tables
        print("Creating table: medicines...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicines (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            price DECIMAL(10, 2) NOT NULL,
            stock INT DEFAULT 0,
            expiry_date DATE,
            manufacturer VARCHAR(100),
            requires_prescription BOOLEAN DEFAULT FALSE
        )
        """)
        
        print("Creating table: prescriptions...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS prescriptions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            image_path VARCHAR(255) NOT NULL,
            status ENUM('pending', 'verified', 'rejected', 'approved') DEFAULT 'pending',
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)

        print("Creating table: orders...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            total_amount DECIMAL(10, 2),
            status ENUM('pending', 'completed', 'cancelled') DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)

        print("Creating table: feedback...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            type ENUM('rating', 'complaint', 'review') NOT NULL,
            message TEXT,
            rating INT CHECK (rating BETWEEN 1 AND 5),
            reply TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)
        
        print("Creating table: attendance...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INT AUTO_INCREMENT PRIMARY KEY,
            staff_id INT,
            date DATE,
            status ENUM('present', 'absent', 'leave'),
            work_assigned TEXT,
            FOREIGN KEY (staff_id) REFERENCES users(id)
        )
        """)

        print("Creating table: cart...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            medicine_id INT NOT NULL,
            quantity INT DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (medicine_id) REFERENCES medicines(id)
        )
        """)

        conn.commit()
        print("Database updated successfully!")

    except mysql.connector.Error as err:
        print(f"Critical Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    update_db()
