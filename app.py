from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_mail import Mail, Message
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import requests
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import json


# Custom JSON encoder for handling ObjectId serialization
class CustomJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)  # Convert ObjectId to string
        return super().default(obj)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_paco_key_is_here'  # Set a secure key for session handling
app.json_encoder = CustomJsonEncoder  # Use custom JSON encoder
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Redirects unauthorized users to login page
login_manager.login_message = "Please log in to access this page."

# Example User class
class User(UserMixin):
    def __init__(self, id, email):
        self.id = id  # MongoDB `_id` (converted to string)
        self.email = email

    def get_id(self):
        return self.id  # Must return the unique identifier for the user

users = {
    '1': User(id='1', email='user@example.com'),
}  # Replace with database logic



# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_email_password'
mail = Mail(app)


# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")  # Connect to MongoDB
db = client.jstar_designer  # Access the 'jstar_designer' database

# Home Page Route
@app.route('/')
def index():
    categories = list(db.categories.find())  # Fetch all categories from MongoDB
    return render_template('index.html', categories=categories)  # Render home page with categories

# Product Listings Route
@app.route('/product/<category>')
def product(category):
    products = list(db.products.find({"category": category}))  # Fetch products based on category
    return render_template('product.html', products=products, category=category)  # Render the products page

# Cart Route
@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])  # Retrieve cart items from session
    return render_template('cart.html', cart_items=cart_items)  # Render cart page

# Add to Cart Route
@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    product_id = request.form.get('product_id')  # Get product ID from form
    size = request.form.get('size')  # Get size from form
    type_ = request.form.get('type')  # Get type from form

    try:
        # Find product by ObjectId
        product = db.products.find_one({"_id": ObjectId(product_id)})
        if not product:
            return "Product not found", 404  # Handle case if product is not found

        # Convert ObjectId to string before storing it in the session
        product['_id'] = str(product['_id'])  # Convert ObjectId to string

        # Initialize the cart if it doesn't exist in the session
        if 'cart' not in session:
            session['cart'] = []

        # Check if the product with the same size and type is already in the cart
        for item in session['cart']:
            if item['_id'] == product['_id'] and item.get('size') == size and item.get('type') == type_:
                item['quantity'] += 1  # If product exists with same size/type, increase the quantity
                session.modified = True
                return redirect(url_for('cart'))

        # Add size, type, and quantity to the product data
        product['size'] = size
        product['type'] = type_
        product['quantity'] = 1

        # Add the product to the cart
        session['cart'].append(product)
        session.modified = True  # Mark the session as modified

        return redirect(url_for('cart'))  # Redirect to the cart page

    except Exception as e:
        return f"Error: {str(e)}", 500  # Error handling for invalid ObjectId or database errors

# Remove from Cart Route
@app.route('/remove_from_cart/<product_id>')
def remove_from_cart(product_id):
    try:
        # Remove product by matching the ObjectId in the cart
        session['cart'] = [item for item in session['cart'] if item['_id'] != product_id]
        session.modified = True  # Mark the session as modified
        return redirect(url_for('cart'))  # Redirect to the cart page
    except Exception as e:
        return f"Error: {str(e)}", 500  # Handle any potential errors

# Decrease Quantity Route
@app.route('/decrease_quantity/<product_id>')
def decrease_quantity(product_id):
    try:
        # Find product in the cart
        for item in session['cart']:
            if item['_id'] == product_id:
                if item['quantity'] > 1:
                    item['quantity'] -= 1  # Decrease the quantity
                else:
                    session['cart'] = [cart_item for cart_item in session['cart'] if cart_item['_id'] != product_id]  # Remove item if quantity is 1
                session.modified = True  # Mark the session as modified
                break
        return redirect(url_for('cart'))  # Redirect to the cart page
    except Exception as e:
        return f"Error: {str(e)}", 500  # Handle any potential errors
    
# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Retrieve user by email
        user_data = db.users.find_one({"email": email})
        
        #Check if user exists and password matches
        if user_data:
            if check_password_hash(user_data['password'], password):
                user = User(id=str(user_data['_id']), email=user_data['email'])
                login_user(user)  # Store user in session
                flash('Login successful!', 'success')
                return redirect(url_for('index'))  # Redirect to homepage after login
            else:
                flash('Invalid password.', 'danger')  # Password mismatch
        else:
            flash('User not found.', 'danger')  # Email not found


    return render_template('login.html')



@login_manager.user_loader
def load_user(user_id):
    # Retrieve the user from MongoDB based on user_id
    user_data = db.users.find_one({"_id": ObjectId(user_id)})
    if user_data:
        return User(id=str(user_data['_id']), email=user_data['email'])
    return None  # Return None if user not found


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if user already exists
        if db.users.find_one({"email": email}):
            flash('User already exists. Please log in.', 'warning')
            return redirect(url_for('login'))

        # Hash the password before saving
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        db.users.insert_one({"email": email, "password": hashed_password})
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))  # Redirect to login page after registration

    return render_template('register.html')



@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    return render_template('checkout.html')

@app.route('/process_checkout', methods=['POST'])
def process_checkout():
    payment_method = request.form.get('payment_method')
    user_email = 'user_email@example.com'  # Replace with the logged-in user's email

    if payment_method == 'visa':
        card_number = request.form.get('card_number')
        expiry_date = request.form.get('expiry_date')
        cvv = request.form.get('cvv')
        # Mock Visa payment processing (use an actual payment gateway in production)
        if card_number and expiry_date and cvv:
            flash('Payment successful via Visa!', 'success')
            send_receipt(user_email)
        else:
            flash('Payment failed. Please check your Visa details.', 'danger')

    elif payment_method == 'mpesa':
        phone = request.form.get('phone')
        # Mock M-Pesa payment processing
        if phone:
            # Simulate sending payment prompt (API call to Safaricom)
            response = requests.post('https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest', json={
                'BusinessShortCode': '174379',
                'Password': 'your_encoded_password',
                'Timestamp': '20240101120000',
                'TransactionType': 'CustomerPayBillOnline',
                'Amount': '1',  # Mock amount
                'PartyA': phone,
                'PartyB': '174379',
                'PhoneNumber': phone,
                'CallBackURL': 'https://yourdomain.com/callback',
                'AccountReference': 'JSTAR Designers',
                'TransactionDesc': 'Payment'
            }, headers={'Authorization': 'Bearer your_access_token'})
            if response.status_code == 200:
                flash('Payment prompt sent via M-Pesa!', 'success')
                send_receipt(user_email)
            else:
                flash('Payment failed. Please check your phone number.', 'danger')
        else:
            flash('Phone number is required for M-Pesa payment.', 'danger')

    return redirect(url_for('checkout'))

def send_receipt(email):
    msg = Message('Payment Receipt', sender='your_email@gmail.com', recipients=[email])
    msg.body = 'Thank you for your payment! Your order is confirmed.'
    mail.send(msg)

# Run the application
if __name__ == '__main__':
    app.run(debug=True)
