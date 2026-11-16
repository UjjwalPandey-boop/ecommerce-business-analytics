
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine
from urllib.parse import quote_plus

# -----------------------------
# Configuration
# -----------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "raw"

DB_USER = "root"
DB_PASSWORD = "root@123"
DB_HOST = "localhost"
DB_PORT = 3306
DB_NAME = "ecommerce_analytics"

# -----------------------------
# MySQL Connection
# -----------------------------

password = quote_plus(DB_PASSWORD)

engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{password}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# -----------------------------
# CSV to MySQL Table Mapping
# -----------------------------

files = {
    "olist_orders_dataset.csv": "orders",
    "olist_order_items_dataset.csv": "order_items",
    "olist_customers_dataset.csv": "customers",
    "olist_products_dataset.csv": "products",
    "olist_order_payments_dataset.csv": "payments",
    "olist_order_reviews_dataset.csv": "reviews",
    "olist_sellers_dataset.csv": "sellers",
    "product_category_name_translation.csv": "category_translation",
}

# -----------------------------
# Import Data
# -----------------------------

for filename, table_name in files.items():

    file_path = DATA_DIR / filename

    print(f"\nLoading {filename}...")

    df = pd.read_csv(file_path)

    df.to_sql(
        table_name,
        con=engine,
        if_exists="replace",
        index=False,
        chunksize=1000
    )

    print(f"Imported {len(df)} rows into {table_name}")

print("\nAll datasets imported successfully!")
