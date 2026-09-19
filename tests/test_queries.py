import pytest
from sqlalchemy import create_engine
import pandas as pd
from src.database.queries import get_kpi_metrics, get_monthly_revenue

@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:")
    # Create simple tables
    eng.execute("CREATE TABLE orders (id INTEGER, total_amount REAL, customer_id INTEGER, status TEXT, order_date DATE)")
    eng.execute("INSERT INTO orders VALUES (1, 100.0, 1, 'Completed', '2023-01-01')")
    eng.execute("INSERT INTO orders VALUES (2, 200.0, 2, 'Completed', '2023-01-15')")
    eng.execute("INSERT INTO orders VALUES (3, 50.0, 1, 'Pending', '2023-01-20')")
    return eng

def test_kpi_metrics(engine):
    kpis = get_kpi_metrics(engine)
    assert kpis["total_revenue"] == 300.0
    assert kpis["total_orders"] == 2
    assert kpis["total_customers"] == 2
    assert kpis["avg_order_value"] == 150.0

def test_monthly_revenue(engine):
    df = get_monthly_revenue(engine)
    assert len(df) == 1
    assert df["month"].iloc[0] == "2023-01"
    assert df["revenue"].iloc[0] == 300.0
