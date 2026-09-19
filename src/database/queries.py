import pandas as pd

def get_kpi_metrics(engine):
    q = """
    SELECT 
        SUM(total_amount) as total_revenue,
        COUNT(id) as total_orders,
        COUNT(DISTINCT customer_id) as total_customers
    FROM orders 
    WHERE status = 'Completed'
    """
    df = pd.read_sql(q, engine)
    total_rev = df['total_revenue'].iloc[0] or 0
    total_orders = df['total_orders'].iloc[0] or 0
    total_cust = df['total_customers'].iloc[0] or 0
    aov = total_rev / total_orders if total_orders > 0 else 0
    
    return {
        "total_revenue": total_rev,
        "total_orders": total_orders,
        "avg_order_value": aov,
        "total_customers": total_cust
    }

def get_monthly_revenue(engine):
    # Cross-platform way (SQLite vs Postgres)
    if engine.name == "sqlite":
        q = "SELECT strftime('%Y-%m', order_date) as month, SUM(total_amount) as revenue FROM orders WHERE status = 'Completed' GROUP BY month ORDER BY month"
    else:
        q = "SELECT to_char(order_date, 'YYYY-MM') as month, SUM(total_amount) as revenue FROM orders WHERE status = 'Completed' GROUP BY month ORDER BY month"
    return pd.read_sql(q, engine)

def get_top_products(engine, n=10):
    q = f"""
    SELECT p.name as product, SUM(o.total_amount) as revenue, COUNT(o.id) as orders
    FROM orders o
    JOIN products p ON o.product_id = p.id
    WHERE o.status = 'Completed'
    GROUP BY p.name
    ORDER BY revenue DESC
    LIMIT {n}
    """
    return pd.read_sql(q, engine)

def get_customer_segments(engine):
    q = """
    SELECT c.segment, COUNT(DISTINCT c.id) as count, SUM(o.total_amount) as revenue
    FROM customers c
    LEFT JOIN orders o ON c.id = o.customer_id AND o.status = 'Completed'
    GROUP BY c.segment
    """
    return pd.read_sql(q, engine)

def get_category_breakdown(engine):
    q = """
    SELECT p.category, SUM(o.total_amount) as revenue
    FROM orders o
    JOIN products p ON o.product_id = p.id
    WHERE o.status = 'Completed'
    GROUP BY p.category
    """
    return pd.read_sql(q, engine)

def get_daily_orders_trend(engine, days=30):
    if engine.name == "sqlite":
        q = f"SELECT order_date as date, COUNT(id) as orders FROM orders WHERE order_date >= date('now', '-{days} days') GROUP BY date ORDER BY date"
    else:
        q = f"SELECT order_date as date, COUNT(id) as orders FROM orders WHERE order_date >= CURRENT_DATE - INTERVAL '{days} days' GROUP BY date ORDER BY date"
    return pd.read_sql(q, engine)
