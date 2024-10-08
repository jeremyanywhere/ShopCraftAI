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
        "email": "johndoe@example.com",
        "address": "123 Elm Street",
        "phone": "123-456-7890",
        "join_date": "2022-01-15",
        "favorite_game": "Chess"
    },
    {
        "customer_id": "C002",
        "name": "Jane Smith",
        "email": "janesmith@example.com",
        "address": "456 Oak Avenue",
        "phone": "098-765-4321",
        "join_date": "2022-02-20",
        "favorite_game": "Sudoku"
    }
])

# Products collection
products = db['products']
products.insert_many([
    {
        "product_id": "P001",
        "name": "Laptop",
        "category": "Electronics",
        "price": 1200.00,
        "stock": 50
    },
    {
        "product_id": "P002",
        "name": "Smartphone",
        "category": "Electronics",
        "price": 800.00,
        "stock": 100
    }
])

# Orders collection
orders = db['orders']
orders.insert_many([
    {
        "order_id": "O1001",
        "customer_id": "C001",
        "order_date": "2022-03-10",
        "status": "Shipped",
        "total_amount": 2000.00,
        "items": [
            {"product_id": "P001", "quantity": 1},
            {"product_id": "P002", "quantity": 1}
        ]
    },
    {
        "order_id": "O1002",
        "customer_id": "C002",
        "order_date": "2022-03-15",
        "status": "Pending",
        "total_amount": 1200.00,
        "items": [
            {"product_id": "P001", "quantity": 1}
        ]
    }
])

# Categories collection
categories = db['categories']
categories.insert_many([
    {"category_name": "Electronics", "description": "Electronic devices and gadgets"},
    {"category_name": "Home Appliances", "description": "Household appliances and equipment"}
])

# Reviews collection
reviews = db['reviews']
reviews.insert_many([
    {
        "review_id": "R001",
        "product_id": "P001",
        "customer_id": "C002",
        "rating": 5,
        "comment": "Great product, highly recommend!",
        "date": "2022-03-20"
    }
])

# Output message
print("Sample data inserted into the 'commerce' database.")