# comment added here - Date: 2024-10-11 16:10:19

from pymongo import MongoClient

# Connect to the MongoDB server (default URI)
client = MongoClient('mongodb://localhost:27017/')

# Create a new database named 'commerce'
db = client['commerce']

# Create sample collections with documents

# Customers collection
customers = db['customers']
customers.insert_many([
    {
        "customer_id": "C001",
        "name": "John Doe",
        "e-mail": "johndoe@example.com",
        "address": "123 Elm Street",
        "phone": "123-456-7890",
        "mobile_no": "555-0123",
        "join_date": "2022-01-15",
        "leave_date": None,  # New leave date field
        "favorite_city": "Los Angeles",
        "favorite_country": "USA",
        "favorite_game": "Chess",
    },
    {
        "customer_id": "C002",
        "name": "Jane Smith",
        "e-mail": "janesmith@example.com",
        "address": "456 Oak Avenue",
        "phone": "098-765-4321",
        "mobile_no": "555-0456",
        "join_date": "2022-03-22",
        "leave_date": None,  # New leave date field
        "favorite_city": "Houston", 
        "favorite_country": "UK", 
        "favorite_game": "Golf", 
    }
])


# Products collection
products = db['products']
products.insert_many([
    {
        "product_id": "P001",
        "name": "Wireless Mouse",
        "description": "Ergonomic wireless mouse with USB receiver",
        "price": 25.99,
        "category": "Electronics",
        "quantity_in_stock": 150,
        "supplier": "Supplier A"
    },
    {
        "product_id": "P002",
        "name": "Bluetooth Speaker",
        "description": "Portable Bluetooth speaker with high-quality sound",
        "price": 45.50,
        "category": "Electronics",
        "quantity_in_stock": 75,
        "supplier": "Supplier B"
    }
])

# Orders collection
orders = db['orders']
orders.insert_many([
    {
        "order_id": "O001",
        "customer_id": "C001",
        "order_date": "2023-10-05",
        "status": "Shipped",
        "total_amount": 71.49,
        "products": ["P001", "P002"]
    },
    {
        "order_id": "O002",
        "customer_id": "C002",
        "order_date": "2023-11-01",
        "status": "Pending",
        "total_amount": 25.99,
        "products": ["P001"]
    }
])

# Inventory collection
inventory = db['inventory']
inventory.insert_many([
    {
        "product_id": "P001",
        "last_updated": "2023-11-10",
        "quantity": 145
    },
    {
        "product_id": "P002",
        "last_updated": "2023-11-15",
        "quantity": 70
    }
])

# Categories collection
categories = db['categories']
categories.insert_many([
    {
        "category_id": "C001",
        "name": "Electronics",
        "description": "Electronic devices and accessories"
    },
    {
        "category_id": "C002",
        "name": "Home Appliances",
        "description": "Appliances for home use"
    }
])

# Reviews collection
reviews = db['reviews']
reviews.insert_many([
    {
        "review_id": "R001",
        "product_id": "P001",
        "customer_id": "C002",
        "rating": 4.5,
        "comment": "Great mouse, very comfortable to use."
    },
    {
        "review_id": "R002",
        "product_id": "P002",
        "customer_id": "C001",
        "rating": 4.0,
        "comment": "Good sound quality, but a bit bulky."
    }
])
