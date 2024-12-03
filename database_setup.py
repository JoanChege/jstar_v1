from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['jstar_designer']

# Insert categories
categories = [
    {"name": "Dresses", "image": "dresses.jpg"},
    {"name": "Suits", "image": "suits.jpg"},
    {"name": "Shirt Dress", "image": "shirtdress.jpg"},
    {"name": "Coats", "image": "coats.jpg"},
    {"name": "Shoes", "image": "shoes.jpg"},
    {"name": "Panties", "image": "panties.jpg"}
]

db.categories.drop()  # Clear existing data
db.categories.insert_many(categories)

# Insert sample products with sizes and types
products = [
    {
        "name": "Red Evening Dress",
        "category": "Dresses",
        "price": 4500,
        "image": "reddress.jpg",
        "sizes": ["XS","S", "M", "L", "X", "XXL"],
        "types": ["Long Sleeve", "Short Sleeve"],
        "types_length": ["Long", "Short"]
    },
    {
        "name": "Blue Office Suit",
        "category": "Suits",
        "price": 5000,
        "image": "blacksuit.jpg",
        "sizes": ["XS","S", "M", "L", "X", "XXL"],
        "types": []
    },
    {
        "name": "Casual Shirt Dress",
        "category": "Shirt Dress",
        "price": 3000,
        "image": "blueshirtdress.jpg",
        "sizes": ["XS","S", "M", "L", "X", "XXL"],
        "types": ["Short Sleeve"]
    },
    {
        "name": "Winter Long Coat",
        "category": "Coats",
        "price": 8000,
        "image": "coats.jpg",
        "sizes": ["XS","S", "M", "L", "X", "XXL"],
    },
    {
        "name": "Stylish Heels",
        "category": "Shoes",
        "price": 3500,
        "image": "heels.jpg",
        "sizes": ["37", "38", "39", "40"],
        "types": ["Pointy Heel", "Blocked Heel"],
        "types_length": ["Long Heel", "Short Heel"]
    },
    {
        "name": "Brazilian Panties",
        "category": "Panties",
        "price": 1000,
        "image": "panties.jpg",
        "types": ["Brazilian", "Cotton", "Laced"]
    }
]

db.products.drop()  # Clear existing data
db.products.insert_many(products)

# Insert a sample user (hashed password for security)
from werkzeug.security import generate_password_hash, check_password_hash


users = [
    {"email": "testuser@example.com", "password": generate_password_hash("password123", method='pbkdf2:sha256')
}
]

db.users.drop()  # Clear existing data
db.users.insert_many(users)

print("Database setup completed!")
