import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.express as px
from datetime import datetime
import os

from src.database.connection import get_engine
from src.database.queries import (
    get_kpi_metrics, get_monthly_revenue, get_top_products, 
    get_customer_segments, get_category_breakdown, get_daily_orders_trend
)

# Seed DB if using SQLite and it doesn't exist
db_host = os.getenv("POSTGRES_HOST")
if not db_host and not os.path.exists("data/ecommerce.db"):
    from src.data.seed_database import seed
    seed()

engine = get_engine()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server

app.layout = dbc.Container([
    dcc.Interval(id='interval-update', interval=60000, n_intervals=0),
    
    dbc.Row([
        dbc.Col(html.H2("CODELENS | E-commerce BI Dashboard", className="text-light"), width=9),
        dbc.Col(html.Div(id='last-updated', className="text-end text-muted mt-2"), width=3)
    ], className="mb-4 mt-4"),

    dbc.Row(id='kpi-row', className="mb-4"),
    
    dbc.Row([
        dbc.Col(dcc.Graph(id='monthly-revenue-chart'), width=8),
        dbc.Col(dcc.Graph(id='customer-segments-chart'), width=4)
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(dcc.Graph(id='top-products-chart'), width=6),
        dbc.Col(dcc.Graph(id='category-breakdown-chart'), width=6)
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col(dcc.Graph(id='daily-orders-chart'), width=12)
    ], className="mb-4")

], fluid=True, style={"backgroundColor": "#111111", "minHeight": "100vh"})

@app.callback(
    [Output('kpi-row', 'children'),
     Output('monthly-revenue-chart', 'figure'),
     Output('customer-segments-chart', 'figure'),
     Output('top-products-chart', 'figure'),
     Output('category-breakdown-chart', 'figure'),
     Output('daily-orders-chart', 'figure'),
     Output('last-updated', 'children')],
    [Input('interval-update', 'n_intervals')]
)
def update_dashboard(n):
    # Fetch Data
    kpis = get_kpi_metrics(engine)
    df_monthly = get_monthly_revenue(engine)
    df_segments = get_customer_segments(engine)
    df_top = get_top_products(engine)
    df_cat = get_category_breakdown(engine)
    df_daily = get_daily_orders_trend(engine)
    
    # KPIs
    kpi_cards = [
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("💰 Total Revenue", className="card-title"),
            html.H3(f"${kpis['total_revenue']:,.2f}")
        ]), color="dark", inverse=True), width=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("🛒 Orders", className="card-title"),
            html.H3(f"{kpis['total_orders']:,}")
        ]), color="dark", inverse=True), width=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("💵 Avg Order Value", className="card-title"),
            html.H3(f"${kpis['avg_order_value']:,.2f}")
        ]), color="dark", inverse=True), width=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("👥 Customers", className="card-title"),
            html.H3(f"{kpis['total_customers']:,}")
        ]), color="dark", inverse=True), width=3),
    ]

    # Charts
    template = "plotly_dark"
    
    fig_monthly = px.line(df_monthly, x='month', y='revenue', title='Monthly Revenue Trend', template=template, markers=True)
    fig_monthly.update_traces(line_color='#00ff99')

    fig_segments = px.pie(df_segments, values='count', names='segment', title='Customer Segments', template=template, hole=0.4)
    
    fig_top = px.bar(df_top, x='revenue', y='product', orientation='h', title='Top 10 Products by Revenue', template=template)
    fig_top.update_layout(yaxis={'categoryorder':'total ascending'})
    
    fig_cat = px.bar(df_cat, x='category', y='revenue', title='Category Breakdown', template=template, color='category')
    
    fig_daily = px.area(df_daily, x='date', y='orders', title='Daily Orders (Last 30 Days)', template=template)
    fig_daily.update_traces(line_color='#ff00ff', fillcolor='rgba(255,0,255,0.2)')

    now = f"Last updated: {datetime.now().strftime('%H:%M:%S')}"

    return kpi_cards, fig_monthly, fig_segments, fig_top, fig_cat, fig_daily, now

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
