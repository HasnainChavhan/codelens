import random
import datetime
from faker import Faker
import pandas as pd
from sqlalchemy import text
from src.database.connection import get_engine

fake = Faker()

def seed():
    engine = get_engine()
    
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS orders;"))
        conn.execute(text("DROP TABLE IF EXISTS products;"))
        conn.execute(text("DROP TABLE IF EXISTS customers;"))
        
        conn.execute(text("""
            CREATE TABLE customers (
                id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT,
                city TEXT,
                country TEXT,
                segment TEXT,
                signup_date DATE
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE products (
                id INTEGER PRIMARY KEY,
                name TEXT,
                category TEXT,
                price REAL,
                cost REAL
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                product_id INTEGER,
                quantity INTEGER,
                total_amount REAL,
                order_date DATE,
                status TEXT
            )
        """))

    print("Tables created.")
    
    # 1. Customers
    customers = []
    segments = ["Premium", "Standard", "Basic"]
    for i in range(1, 1001):
        customers.append({
            "id": i,
            "name": fake.name(),
            "email": fake.email(),
            "city": fake.city(),
            "country": fake.country(),
            "segment": random.choices(segments, weights=[0.2, 0.5, 0.3])[0],
            "signup_date": fake.date_between(start_date='-2y', end_date='today')
        })
    pd.DataFrame(customers).to_sql("customers", engine, if_exists="append", index=False)
    
    # 2. Products
    products = []
    categories = ["Electronics", "Clothing", "Books", "Home", "Sports"]
    for i in range(1, 51):
        price = round(random.uniform(10.0, 500.0), 2)
        cost = round(price * random.uniform(0.3, 0.7), 2)
        products.append({
            "id": i,
            "name": fake.word().capitalize() + " " + fake.word().capitalize(),
            "category": random.choice(categories),
            "price": price,
            "cost": cost
        })
    pd.DataFrame(products).to_sql("products", engine, if_exists="append", index=False)
    
    # 3. Orders
    orders = []
    statuses = ["Completed", "Completed", "Completed", "Pending", "Cancelled"]
    for i in range(1, 5001):
        prod = random.choice(products)
        qty = random.randint(1, 5)
        orders.append({
            "id": i,
            "customer_id": random.randint(1, 1000),
            "product_id": prod["id"],
            "quantity": qty,
            "total_amount": round(prod["price"] * qty, 2),
            "order_date": fake.date_between(start_date='-2y', end_date='today'),
            "status": random.choice(statuses)
        })
    pd.DataFrame(orders).to_sql("orders", engine, if_exists="append", index=False)
    
    print("Database seeded with 1000 customers, 50 products, 5000 orders.")

if __name__ == "__main__":
    seed()
