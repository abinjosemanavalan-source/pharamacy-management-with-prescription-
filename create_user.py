import mysql.connector
from werkzeug.security import generate_password_hash

# Connect without specifying database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password=""
)
cursor = db.cursor()

# Drop and recreate the database cleanly
print("Dropping and recreating pharmacy_db...")
cursor.execute("DROP DATABASE IF EXISTS pharmacy_db")
cursor.execute("CREATE DATABASE pharmacy_db")
cursor.execute("USE pharmacy_db")
print("  Database ready!")

# Create users table (NO unique on role!)
print("Creating users table...")
cursor.execute("""
    CREATE TABLE users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100),
        email VARCHAR(100) NOT NULL,
        password VARCHAR(255) NOT NULL,
        role ENUM('admin','user') DEFAULT 'user',
        phone VARCHAR(20)
    )
""")
print("  Users table created!")

# Create medicines table
print("Creating medicines table...")
cursor.execute("""
    CREATE TABLE medicines (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        price DECIMAL(10,2) NOT NULL,
        stock INT NOT NULL,
        requires_prescription TINYINT(1) DEFAULT 0
    )
""")
print("  Medicines table created!")

# Create orders table
print("Creating orders table...")
cursor.execute("""
    CREATE TABLE orders (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        medicine_name VARCHAR(100),
        quantity INT,
        price DECIMAL(10,2),
        total DECIMAL(10,2),
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        payment_method VARCHAR(50),
        status ENUM('pending','completed','cancelled') DEFAULT 'pending',
        total_amount DECIMAL(10,2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
""")
print("  Orders table created!")

# Insert sample medicines
print("Adding sample medicines...")
cursor.execute("INSERT INTO medicines (name, price, stock, requires_prescription) VALUES ('Paracetamol 500mg', 25.00, 100, 0)")
cursor.execute("INSERT INTO medicines (name, price, stock, requires_prescription) VALUES ('Amoxicillin 250mg', 120.00, 50, 1)")
cursor.execute("INSERT INTO medicines (name, price, stock, requires_prescription) VALUES ('Cetirizine', 30.00, 80, 0)")
print("  Medicines added!")

# Create users
print("Creating users...")
admin_pw = generate_password_hash("admin123")
cursor.execute(
    "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
    ("Admin", "admin@pharmacy.com", admin_pw, "admin")
)

user_pw = generate_password_hash("user123")
cursor.execute(
    "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
    ("User", "user@pharmacy.com", user_pw, "user")
)

db.commit()

# Verify
print("\nVerifying users...")
cursor.execute("SELECT id, name, email, role FROM users")
for row in cursor.fetchall():
    print(f"  ID: {row[0]}, Name: {row[1]}, Email: {row[2]}, Role: {row[3]}")

print("\n" + "="*50)
print("  ALL DONE! Login with:")
print("  Admin -> email: admin@pharmacy.com  password: admin123")
print("  User  -> email: user@pharmacy.com   password: user123")
print("="*50)

cursor.close()
db.close()
