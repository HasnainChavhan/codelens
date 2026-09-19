# codelens

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Plotly Dash](https://img.shields.io/badge/Plotly_Dash-2.14-008080)
![SQLite](https://img.shields.io/badge/SQLite-Database-lightblue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Ready-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## Problem Statement
Business teams need real-time, interactive insights into their e-commerce data without relying on static reports or slow SQL query times. `codelens` is an interactive Business Intelligence dashboard built with Plotly Dash and SQL Analytics to provide real-time KPI tracking, customer segmentation, and product performance analysis.

## Architecture
```
+---------------+      +----------------+      +-------------------+
|               |      |                |      |                   |
|  Web Browser  +----->+  Plotly Dash   +----->+ SQLite / Postgres |
|  (UI Client)  |      |  (App Server)  |      | (Data Storage)    |
|               |      |                |      |                   |
+---------------+      +----------------+      +-------------------+
```

## Features
- Real-time KPI Tracking (Revenue, Orders, AOV, Customers)
- Interactive Charts (Time series, categorical breakdowns)
- Dark mode optimized UI
- Seed script to generate realistic test data using Faker
- Docker and Docker Compose ready

## Tech Stack
| Component | Technology |
|---|---|
| Language | Python 3.10 |
| Dashboard | Plotly Dash |
| Database | SQLite (Default), PostgreSQL |
| ORM / Driver | SQLAlchemy, Psycopg2 |
| Data Manipulation | Pandas, Numpy |
| Testing | Pytest |

## Quick Start
```bash
git clone https://github.com/HasnainChavhan/codelens.git
cd codelens
# To run locally:
pip install -r requirements.txt
python -m src.data.seed_database
python -m src.dashboard.app

# To run with Docker (PostgreSQL):
docker-compose up -d --build
```

## Dashboard Screenshots (ASCII)
```text
========================================================================
| CODELENS | E-commerce BI Dashboard                   Last updated: Now|
========================================================================
| [ $ Total Revenue ]  [ # Orders ]  [ $ Avg Order Val ] [ # Customers ]|
| [    $1,200,500   ]  [   5,000  ]  [       $240      ] [    1,000    ]|
| [      ^ 5.2%     ]  [   ^ 2.1% ]  [      ^ 3.0%     ] [    ^ 1.5%   ]|
========================================================================
|     Monthly Revenue Trend           |        Customer Segments       |
|      /\                             |             ____               |
|     /  \/\      /                   |          .-'    '-.            |
|    /      \____/                    |         /  PREM    \           |
|   /                                 |         \   STD    /           |
|                                     |          '-.____.-'            |
========================================================================
```

## KPI Descriptions
- **Total Revenue**: Sum of all completed orders.
- **Orders**: Total number of transactions.
- **Avg Order Value**: Total Revenue divided by Total Orders.
- **Customers**: Unique active users.

## SQL Queries
Analytics queries are located in `src/database/queries.py` and use pandas `read_sql` for optimized extraction and transformation.

## Project Structure
```
.
├── src/
│   ├── dashboard/
│   ├── data/
│   └── database/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── requirements.txt
```
