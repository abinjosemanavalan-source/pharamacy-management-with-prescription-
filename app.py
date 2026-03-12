from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from config import MYSQL_CONFIG

app = Flask(__name__)
app.secret_key = "supersecretkey"


def get_db():
    return mysql.connector.connect(**MYSQL_CONFIG)

@app.context_processor
def inject_cart_count():
    cart_count = 0
    if 'user_id' in session:
        try:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT SUM(quantity) as total_qty FROM cart WHERE user_id=%s", (session['user_id'],))
            result = cursor.fetchone()
            if result and result['total_qty']:
                cart_count = result['total_qty']
            cursor.close()
            db.close()
        except:
            pass
    return dict(cart_count=cart_count)

# ---------- WELCOME ----------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/welcome')
def welcome():
    return render_template('welcome.html')

# ---------- REGISTER ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, 'user')",
                (name, email, password)
            )
            db.commit()

            # Automatically log the user in after registration
            cursor.execute("SELECT id, name, role FROM users WHERE email=%s", (email,))
            # We need to fetch the user we just inserted. 
            # Since the cursor was set to dictionary=True in login but not here, we check.
            # get_db().cursor is default (tuple) here.
            new_user = cursor.fetchone()
            if new_user:
                session['user_id'] = new_user[0]
                session['user'] = new_user[1]
                session['role'] = new_user[2]

            flash("Registration successful!", "success")
            return redirect(url_for('home'))
        except Exception as e:
            print(f"Registration error: {e}")
            flash("Email already exists!", "danger")
        finally:
            cursor.close()
            db.close()

    if request.method == 'GET':
        return redirect(url_for('login'))
    return redirect(url_for('login'))

# ---------- LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['user'] = user['name'] # Ensure user name is in session for base.html
            return redirect(url_for('home'))
        else:
            flash("Invalid username or password", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')


# ---------- HOME ----------
@app.route('/home')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('home.html')

# ---------- MEDICINES ----------

@app.route('/medicines')
def medicines():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    search_query = request.args.get('q', '')
    if search_query:
        cursor.execute("SELECT * FROM medicines WHERE name LIKE %s", ("%" + search_query + "%",))
    else:
        cursor.execute("SELECT * FROM medicines")
        
    medicines = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('medicines.html', medicines=medicines, search_query=search_query)


@app.route('/medicine/<int:id>')
def medicine_details(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM medicines WHERE id=%s", (id,))
    medicine = cursor.fetchone()
    cursor.close()
    db.close()
    
    if not medicine:
        flash("Medicine not found.", "danger")
        return redirect(url_for('medicines'))
        
    return render_template('medicine_details.html', medicine=medicine)

# ---------- PRESCRIPTION ----------

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == "POST":
        file = request.files.get("prescription")
        if file and file.filename:
            filename = secure_filename(file.filename)
            os.makedirs("static/uploads", exist_ok=True)
            file.save(os.path.join("static/uploads", filename))
            
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO prescriptions (user_id, image_path, status) VALUES (%s, %s, 'pending')",
                (session['user_id'], filename)
            )
            db.commit()
            cursor.close()
            db.close()
            
            flash("Prescription uploaded successfully!", "success")
            return redirect(url_for('history'))
        else:
            flash("Please attach a file.", "danger")
            
    return render_template("upload.html")

# ---------- HISTORY ----------
@app.route("/history")
def history():
    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    query = """
        SELECT medicine_name, quantity, price, total, order_date, payment_method, status
        FROM orders
        WHERE user_id = %s
        ORDER BY order_date DESC
    """
    cursor.execute(query, (session["user_id"],))
    orders = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("history.html", orders=orders)

# ---------- TRACK ORDER ----------
@app.route('/track-order')
def track_order():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    order = None
    order_id = request.args.get('order_id')

    if order_id:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            """SELECT * FROM orders WHERE id=%s AND user_id=%s""",
            (order_id, session['user_id'])
        )
        order = cursor.fetchone()
        cursor.close()
        db.close()

        if not order:
            flash("Order not found. Please check your Order ID.", "danger")

    return render_template("tracking_order.html", order=order, order_id=order_id)

# ---------- CART ----------
@app.route('/add_to_cart/<int:medicine_id>')
def add_to_cart(medicine_id):
    if 'user_id' not in session:
        flash("Please login to add items to cart.", "warning")
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Check if item already exists in cart
    cursor.execute("SELECT * FROM cart WHERE user_id=%s AND medicine_id=%s", (user_id, medicine_id))
    item = cursor.fetchone()
    
    if item:
        cursor.execute("UPDATE cart SET quantity = quantity + 1 WHERE id=%s", (item['id'],))
    else:
        cursor.execute("INSERT INTO cart (user_id, medicine_id, quantity) VALUES (%s, %s, 1)", (user_id, medicine_id))
    
    db.commit()
    cursor.close()
    db.close()
    flash("Item added to cart!", "success")
    return redirect(url_for('medicines'))

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT c.id, m.name, m.price, c.quantity, (m.price * c.quantity) as total 
        FROM cart c 
        JOIN medicines m ON c.medicine_id = m.id 
        WHERE c.user_id = %s
    """, (user_id,))
    items = cursor.fetchall()
    
    grand_total = sum(item['total'] for item in items)
    
    cursor.close()
    db.close()

    return render_template('cart.html', items=items, grand_total=grand_total)

# ---------- PAY AND CHECKOUT ----------

@app.route('/checkout', methods=['GET'])
def checkout():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('payment.html')

@app.route('/process_payment', methods=['POST'])
def process_payment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT c.id, m.name as medicine_name, m.price, c.quantity, (m.price * c.quantity) as total 
        FROM cart c 
        JOIN medicines m ON c.medicine_id = m.id 
        WHERE c.user_id = %s
    """, (user_id,))
    items = cursor.fetchall()
    
    for item in items:
        cursor.execute(
            "INSERT INTO orders (user_id, medicine_name, quantity, price, total, payment_method, status) VALUES (%s, %s, %s, %s, %s, 'Card', 'completed')",
            (user_id, item['medicine_name'], item['quantity'], item['price'], item['total'])
        )
        cursor.execute(
            "INSERT INTO payments (user_id, amount, status) VALUES (%s, %s, 'completed')",
            (user_id, item['total'])
        )
        
    cursor.execute("DELETE FROM cart WHERE user_id=%s", (user_id,))
    db.commit()
    cursor.close()
    db.close()
    
    return render_template('loading.html')

# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))



@app.route('/add_medicine', methods=['GET','POST'])
def add_medicine():

    if request.method == 'POST':

        name = request.form['name']
        company = request.form['company']
        price = request.form['price']
        stock = request.form['stock']
        
        photo = request.files.get('image')
        filename = secure_filename(photo.filename) if photo and photo.filename else None
        
        if filename:
            os.makedirs('static/uploads', exist_ok=True)
            photo.save(os.path.join('static/uploads', filename))

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "INSERT INTO medicines(name, company, price, stock, image_path) VALUES(%s,%s,%s,%s,%s)",
            (name, company, price, stock, filename)
        )

        db.commit()

        cursor.close()
        db.close()

        return redirect('/medicines')

    return render_template('add_medicine.html')

@app.route('/view_medicines')
def view_medicines():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM medicines")
    data = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('view_medicines.html', medicines=data)


@app.route('/update_medicine/<int:id>', methods=['GET', 'POST'])
def update_medicine(id):
    db = get_db()
    cursor = db.cursor()

    if request.method == 'POST':
        name = request.form['name']
        company = request.form['company']
        price = request.form['price']
        stock = request.form['stock']
        
        photo = request.files.get('image')
        filename = secure_filename(photo.filename) if photo and photo.filename else None

        if filename:
            os.makedirs('static/uploads', exist_ok=True)
            photo.save(os.path.join('static/uploads', filename))
            cursor.execute(
                "UPDATE medicines SET name=%s, company=%s, price=%s, stock=%s, image_path=%s WHERE id=%s",
                (name, company, price, stock, filename, id)
            )
        else:
            cursor.execute(
                "UPDATE medicines SET name=%s, company=%s, price=%s, stock=%s WHERE id=%s",
                (name, company, price, stock, id)
            )
        db.commit()
        cursor.close()
        db.close()
        return redirect('/view_medicines')

    cursor.execute("SELECT * FROM medicines WHERE id=%s", (id,))
    data = cursor.fetchone()
    cursor.close()
    db.close()

    return render_template('update_medicine.html', medicine=data)


@app.route('/delete_medicine/<int:id>')
def delete_medicine(id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("DELETE FROM medicines WHERE id=%s", (id,))
    db.commit()

    cursor.close()
    db.close()

    return redirect('/view_medicines')



@app.route('/view_staff')
def view_staff():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM staff")
    data = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('view_staff.html', staff=data)

@app.route('/update_staff/<int:id>', methods=['GET','POST'])
def update_staff(id):
    db = get_db()
    cursor = db.cursor()

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        role = request.form['role']
        address = request.form['address']
        
        photo = request.files.get('photo')
        filename = secure_filename(photo.filename) if photo and photo.filename else None
        
        if filename:
            os.makedirs('static/staff_photos', exist_ok=True)
            photo.save(os.path.join('static/staff_photos', filename))
            cursor.execute(
                "UPDATE staff SET name=%s,email=%s,phone=%s,role=%s,address=%s,photo=%s WHERE id=%s",
                (name,email,phone,role,address,filename,id)
            )
        else:
            cursor.execute(
                "UPDATE staff SET name=%s,email=%s,phone=%s,role=%s,address=%s WHERE id=%s",
                (name,email,phone,role,address,id)
            )
        db.commit()
        cursor.close()
        db.close()
        return redirect('/view_staff')

    cursor.execute("SELECT * FROM staff WHERE id=%s",(id,))
    data = cursor.fetchone()
    
    cursor.close()
    db.close()

    return render_template('update_staff.html', staff=data)

@app.route('/delete_staff/<int:id>')
def delete_staff(id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("DELETE FROM staff WHERE id=%s",(id,))
    db.commit()

    cursor.close()
    db.close()

    return redirect('/view_staff')


@app.route('/view_prescriptions')
def view_prescriptions():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT p.id, u.name, p.image_path, p.status 
        FROM prescriptions p 
        JOIN users u ON p.user_id = u.id
        ORDER BY p.id DESC
    """)
    data = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('view_prescriptions.html', prescriptions=data)

@app.route('/view_orders')
def view_orders():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT o.id, u.name, o.medicine_name, o.quantity, o.status 
        FROM orders o 
        JOIN users u ON o.user_id = u.id
    """)
    data = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('view_orders.html', orders=data)

@app.route('/verify_script', methods=['GET','POST'])
def verify_script():
    db = get_db()
    cursor = db.cursor()

    if request.method == 'POST':
        pid = request.form['prescription_id']
        status = request.form['status']

        cursor.execute(
            "UPDATE prescriptions SET status=%s WHERE id=%s",
            (status,pid)
        )
        db.commit()
        flash("Prescription status updated successfully!", "success")

    cursor.close()
    db.close()
    return redirect(url_for('view_prescriptions'))

@app.route('/view_payments')
def view_payments():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT p.id, u.name, p.amount, p.status 
        FROM payments p 
        JOIN users u ON p.user_id = u.id
    """)
    data = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('view_payments.html', payments=data)

@app.route('/low_stock')
def low_stock():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT name, stock FROM medicines WHERE stock < 10")
    data = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('low_stock.html', medicines=data)

@app.route('/expiry_alert')
def expiry_alert():
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT name, expiry_date FROM medicines WHERE expiry_date <= CURDATE() + INTERVAL 30 DAY"
    )
    data = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('expiry_alert.html', medicines=data)
@app.route('/reorder_medicine', methods=['GET','POST'])
def reorder_medicine():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        medicine_name = request.form['medicine']
        quantity = int(request.form['quantity'])

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM medicines WHERE name LIKE %s", ("%" + medicine_name + "%",))
        med = cursor.fetchone()
        
        if med:
            medicine_id = med['id']
            # Check if item already exists in cart
            cursor.execute("SELECT * FROM cart WHERE user_id=%s AND medicine_id=%s", (session['user_id'], medicine_id))
            item = cursor.fetchone()
            
            if item:
                cursor.execute("UPDATE cart SET quantity = quantity + %s WHERE id=%s", (quantity, item['id']))
            else:
                cursor.execute("INSERT INTO cart (user_id, medicine_id, quantity) VALUES (%s, %s, %s)", (session['user_id'], medicine_id, quantity))
            
            db.commit()
            flash(f"Added {quantity} x {med['name']} to cart!", "success")
            cursor.close()
            db.close()
            return redirect(url_for('cart'))
        else:
            flash("Medicine not found in inventory. Please check the name.", "danger")

        cursor.close()
        db.close()

    return render_template('reorder_medicine.html')


@app.route('/download_pdf')
def download_pdf():
    return render_template('download_pdf.html')


@app.route('/feedback', methods=['GET','POST'])
def feedback():
    if request.method == 'POST':
        message = request.form['message']

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "INSERT INTO feedback(message) VALUES(%s)", (message,)
        )

        db.commit()
        cursor.close()
        db.close()
        flash("Feedback sent to admin!", "success")
        return redirect(url_for('home'))

    return render_template('feedback.html')


@app.route('/rate_us', methods=['GET','POST'])
def rate_us():
    if request.method == 'POST':
        rating = request.form['rating']

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "INSERT INTO ratings(value) VALUES(%s)", (rating,)
        )

        db.commit()
        cursor.close()
        db.close()
        flash("Rating sent to admin!", "success")
        return redirect(url_for('home'))

    return render_template('rate_us.html')


@app.route('/file_complaint', methods=['GET','POST'])
def file_complaint():
    if request.method == 'POST':
        complaint = request.form['complaint']

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "INSERT INTO complaints(message) VALUES(%s)", (complaint,)
        )

        db.commit()
        cursor.close()
        db.close()
        flash("Complaint submitted to admin!", "success")
        return redirect(url_for('home'))

    return render_template('file_complaint.html')

@app.route('/view_reviews')
def view_reviews():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
        
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM feedback")
    feedbacks = cursor.fetchall()
    
    cursor.execute("SELECT * FROM complaints")
    complaints = cursor.fetchall()
    
    cursor.execute("SELECT * FROM ratings")
    ratings = cursor.fetchall()
    
    cursor.close()
    db.close()
    return render_template('view_reviews.html', feedbacks=feedbacks, complaints=complaints, ratings=ratings)


@app.route('/account')
def account():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id=%s", (session['user_id'],))
    user = cursor.fetchone()
    cursor.close()
    db.close()
    
    return render_template('account.html', user=user)


@app.route('/change_password', methods=['GET','POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            flash("New passwords do not match!", "danger")
            return redirect(url_for('change_password'))
            
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT password FROM users WHERE id=%s", (session['user_id'],))
        user = cursor.fetchone()
        
        if user and check_password_hash(user['password'], current_password):
            hashed_pw = generate_password_hash(new_password)
            cursor.execute("UPDATE users SET password=%s WHERE id=%s", (hashed_pw, session['user_id']))
            db.commit()
            flash("Password changed successfully!", "success")
            cursor.close()
            db.close()
            return redirect(url_for('account'))
        else:
            flash("Incorrect current password", "danger")
            cursor.close()
            db.close()
            return redirect(url_for('change_password'))

    return render_template('change_password.html')




@app.route('/add_staff', methods=['GET','POST'])
def add_staff():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        role = request.form['role']
        address = request.form['address']

        photo = request.files['photo']
        filename = secure_filename(photo.filename) if photo else ''
        
        if filename:
            os.makedirs('static/staff_photos', exist_ok=True)
            photo.save(os.path.join('static/staff_photos', filename))

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "INSERT INTO staff(name,email,phone,role,address,photo) VALUES(%s,%s,%s,%s,%s,%s)",
            (name,email,phone,role,address,filename)
        )

        db.commit()
        cursor.close()
        db.close()

        return redirect('/view_staff')

    return render_template('add_staff.html')


# ---------- LAB TESTS MODULE ----------
@app.route('/lab_tests')
def lab_tests():
    return render_template('lab_tests.html')

@app.route('/book_lab_test', methods=['GET', 'POST'])
def book_lab_test():
    if request.method == 'POST':
        flash('Test booked successfully! We will contact you soon.', 'success')
        return redirect(url_for('test_status'))
    return render_template('book_lab_test.html')

@app.route('/test_status')
def test_status():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('test_status.html')

@app.route('/download_test_report')
def download_test_report():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('download_test_report.html')

@app.route('/test_report')
def test_report():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('test_report.html')

# ⚠️ THIS MUST BE LAST
if __name__ == '__main__':
    app.run(debug=True)
