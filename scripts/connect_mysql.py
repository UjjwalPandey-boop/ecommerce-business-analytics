
import pandas as pd
from sqlalchemy import create_engine, text

# Connect Python to MySQL

engine = create_engine(
    "mysql+pymysql://root:root%40123@127.0.0.1:3306/ecommerce_analytics"
)


# Test connection
with engine.connect() as connection:
    total_orders = connection.execute(
        text("SELECT COUNT(*) FROM orders")
    ).scalar()

print("Total Orders:", total_orders)

# Extract monthly revenue
query = """
SELECT
    
    DATE_FORMAT(o.order_purchase_timestamp, '%%Y-%%m') AS sales_month,
    ROUND(SUM(p.payment_value) * 17.25, 2) AS revenue_inr
FROM orders o
JOIN payments p
    ON o.order_id = p.order_id
WHERE o.order_status = 'delivered'
GROUP BY sales_month
ORDER BY sales_month;
"""

df = pd.read_sql(query, engine)

print("\nMonthly Revenue:")
print(df)

df.to_csv("reports/monthly_revenue.csv", index=False)

print("\nCSV file created successfully!")
