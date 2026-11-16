
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

# ==========================================
# CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="E-Commerce Business Analytics",
    page_icon="📊",
    layout="wide"
)

INR_RATE = 17.25  # Approximate INR per BRL

# ==========================================
# MYSQL CONNECTION
# ==========================================

DB_USER = "root"
DB_PASSWORD = "root@123"
DB_HOST = "127.0.0.1"
DB_PORT = "3306"
DB_NAME = "ecommerce_analytics"

engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# ==========================================
# LOAD DATA
# ==========================================

@st.cache_data(ttl=300)
def load_data():

    orders = pd.read_sql(
        """
        SELECT order_id, customer_id, order_status,
               order_purchase_timestamp,
               order_delivered_customer_date,
               order_estimated_delivery_date
        FROM orders
        """,
        engine
    )

    payments = pd.read_sql(
        "SELECT order_id, payment_type, payment_value FROM payments",
        engine
    )

    items = pd.read_sql(
        """
        SELECT order_id, product_id, seller_id,
               price, freight_value
        FROM order_items
        """,
        engine
    )

    customers = pd.read_sql(
        """
        SELECT customer_id, customer_unique_id,
               customer_city, customer_state
        FROM customers
        """,
        engine
    )

    products = pd.read_sql(
        """
        SELECT product_id, product_category_name
        FROM products
        """,
        engine
    )

    reviews = pd.read_sql(
        "SELECT order_id, review_score FROM reviews",
        engine
    )

    return orders, payments, items, customers, products, reviews


try:
    orders, payments, items, customers, products, reviews = load_data()
except Exception as e:
    st.error(f"MySQL connection or data loading failed: {e}")
    st.stop()

# ==========================================
# HEADER
# ==========================================

st.title("📊 E-Commerce Business Analytics")
st.caption("Brazilian E-Commerce | Revenue displayed in Indian Rupees")

# ==========================================
# DATE FILTER
# ==========================================

orders["order_purchase_timestamp"] = pd.to_datetime(
    orders["order_purchase_timestamp"]
)

min_date = orders["order_purchase_timestamp"].min().date()
max_date = orders["order_purchase_timestamp"].max().date()

st.sidebar.header("Dashboard Filters")

date_range = st.sidebar.date_input(
    "Select Purchase Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

filtered_orders = orders[
    (orders["order_purchase_timestamp"].dt.date >= start_date)
    &
    (orders["order_purchase_timestamp"].dt.date <= end_date)
].copy()

# ==========================================
# DELIVERED ORDERS
# ==========================================

delivered = filtered_orders[
    filtered_orders["order_status"] == "delivered"
].copy()

delivered_ids = delivered["order_id"].unique()

filtered_payments = payments[
    payments["order_id"].isin(delivered_ids)
].copy()

filtered_items = items[
    items["order_id"].isin(delivered_ids)
].copy()

filtered_customers = customers[
    customers["customer_id"].isin(delivered["customer_id"])
].copy()

# ==========================================
# KPI CALCULATIONS
# ==========================================

total_orders = len(delivered)


customers_query = """
SELECT COUNT(DISTINCT c.customer_unique_id)
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_purchase_timestamp >= %(start_date)s
  AND o.order_purchase_timestamp < %(end_date)s
"""

total_customers = pd.read_sql(
    customers_query,
    engine,
    params={
        "start_date": start_date,
        "end_date": end_date
    }
).iloc[0, 0]


total_revenue = filtered_payments["payment_value"].sum() * INR_RATE

average_order_value = (
    total_revenue / total_orders if total_orders else 0
)

# ==========================================
# KPI DISPLAY
# ==========================================

c1, c2, c3, c4 = st.columns(4)

c1.metric("Delivered Orders", f"{total_orders:,}")
c2.metric("Customers", f"{total_customers:,}")
c3.metric("Revenue", f"₹{total_revenue:,.0f}")
c4.metric("Average Order Value", f"₹{average_order_value:,.0f}")

st.divider()

# ==========================================
# MONTHLY REVENUE
# ==========================================

st.header("📈 Monthly Revenue Performance")

monthly_revenue = (
    filtered_payments.merge(
        filtered_orders[["order_id", "order_purchase_timestamp"]],
        on="order_id"
    )
)

monthly_revenue["Month"] = (
    monthly_revenue["order_purchase_timestamp"]
    .dt.to_period("M")
    .astype(str)
)

monthly_revenue = (
    monthly_revenue.groupby("Month")["payment_value"]
    .sum()
    .reset_index()
)

monthly_revenue["Revenue (INR)"] = (
    monthly_revenue["payment_value"] * INR_RATE
)

if not monthly_revenue.empty:

    fig = px.line(
        monthly_revenue,
        x="Month",
        y="Revenue (INR)",
        markers=True,
        title="Monthly Revenue Trend"
    )

    fig.update_layout(
        yaxis_title="Revenue (₹)",
        xaxis_title="Month"
    )

    st.plotly_chart(fig, use_container_width=True)

    monthly_revenue["Growth (%)"] = (
        monthly_revenue["Revenue (INR)"].pct_change() * 100
    )

    

    
# ==========================================
# MONTH-OVER-MONTH REVENUE GROWTH
# ==========================================

st.subheader("Month-over-Month Revenue Growth")

monthly_revenue["Previous Revenue"] = (
    monthly_revenue["Revenue (INR)"].shift(1)
)

monthly_revenue["Growth (%)"] = (
    (
        monthly_revenue["Revenue (INR)"]
        - monthly_revenue["Previous Revenue"]
    )
    / monthly_revenue["Previous Revenue"]
) * 100

# Exclude first month and months with very small previous revenue
growth_data = monthly_revenue[
    monthly_revenue["Previous Revenue"] >= 100000
].copy()

if not growth_data.empty:

    fig_growth = px.bar(
        growth_data,
        x="Month",
        y="Growth (%)",
        color="Growth (%)",
        color_continuous_scale="RdYlGn",
        title="Monthly Revenue Growth (%)",
        hover_data={
            "Growth (%)": ":.2f",
            "Revenue (INR)": ":,.0f",
            "Previous Revenue": ":,.0f"
        }
    )

    fig_growth.add_hline(
        y=0,
        line_dash="dash",
        line_color="white"
    )

    fig_growth.update_layout(
        xaxis_title="Month",
        yaxis_title="Growth (%)",
        coloraxis_colorbar_title="Growth (%)"
    )

    
    st.plotly_chart(
        fig_growth,
        use_container_width=True,
        key="monthly_revenue_growth_chart"
    )


    st.caption(
        "Growth is calculated against the previous month. "
        "Months with previous revenue below ₹1 lakh are excluded "
        "to avoid misleading percentage spikes."
    )




# ==========================================
# PRODUCT CATEGORY ANALYSIS
# ==========================================

st.divider()
st.header("📦 Product Category Analysis")


category_sales_query = """
SELECT
    COALESCE(t.product_category_name_english,
             p.product_category_name,
             'Unknown') AS product_category,
    ROUND(SUM(oi.price) * 17.25, 0) AS category_sales_inr,
    COUNT(oi.order_item_id) AS products_sold
FROM order_items oi
JOIN products p
    ON oi.product_id = p.product_id
LEFT JOIN category_translation t
    ON p.product_category_name = t.product_category_name
JOIN orders o
    ON oi.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY product_category
ORDER BY category_sales_inr DESC
"""


category_sales = pd.read_sql(category_sales_query, engine)

if not category_sales.empty:

    top_categories = category_sales.head(10)

    fig_category = px.bar(
        top_categories,
        x="category_sales_inr",
        y="product_category",
        orientation="h",
        color="category_sales_inr",
        color_continuous_scale="Blues",
        title="Top 10 Product Categories by Sales (₹)"
    )

    fig_category.update_layout(
        yaxis=dict(autorange="reversed"),
        xaxis_title="Sales (₹)",
        yaxis_title="Product Category",
        coloraxis_showscale=False
    )

    st.plotly_chart(
        fig_category,
        use_container_width=True,
        key="category_sales_chart"
    )

    best_category = category_sales.iloc[0]

    st.success(
        f"🏆 Best Category: {best_category['product_category']} "
        f"with ₹{best_category['category_sales_inr']:,.0f} sales."
    )
else:
    st.warning("No product category data available.")


# ==========================================
# SELLER PERFORMANCE ANALYSIS
# ==========================================

st.divider()
st.header("🏪 Seller Performance Analysis")

seller_query = """
SELECT
    s.seller_id,
    s.seller_city,
    s.seller_state,
    ROUND(SUM(oi.price) * 17.25, 0) AS seller_sales_inr,
    COUNT(DISTINCT oi.order_id) AS orders_handled,
    COUNT(oi.order_item_id) AS items_sold
FROM order_items oi
JOIN sellers s
    ON oi.seller_id = s.seller_id
JOIN orders o
    ON oi.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY
    s.seller_id,
    s.seller_city,
    s.seller_state
ORDER BY seller_sales_inr DESC
LIMIT 10
"""

seller_data = pd.read_sql(seller_query, engine)

if not seller_data.empty:

    # Top 10 sellers by sales
    fig_seller = px.bar(
        seller_data,
        x="seller_sales_inr",
        y="seller_id",
        orientation="h",
        color="seller_sales_inr",
        color_continuous_scale="Blues",
        title="Top 10 Sellers by Sales (₹)"
    )

    fig_seller.update_layout(
        yaxis=dict(autorange="reversed"),
        xaxis_title="Sales (₹)",
        yaxis_title="Seller ID",
        coloraxis_showscale=False
    )

    st.plotly_chart(
        fig_seller,
        use_container_width=True,
        key="seller_sales_chart"
    )

    # Seller performance table
    st.subheader("Seller Performance Details")

    seller_display = seller_data.copy()
    seller_display["seller_sales_inr"] = seller_display[
        "seller_sales_inr"
    ].apply(lambda x: f"₹{x:,.0f}")

    st.dataframe(
        seller_display,
        use_container_width=True,
        hide_index=True
    )

    # Best performing seller
    best_seller = seller_data.iloc[0]

    st.success(
        f"🏆 Top Seller: {best_seller['seller_id']} "
        f"with ₹{best_seller['seller_sales_inr']:,.0f} sales."
    )





# ==========================================
# DELIVERY PERFORMANCE
# ==========================================

st.divider()
st.header("🚚 Delivery Performance")

delivery_data = delivered.dropna(
    subset=[
        "order_delivered_customer_date",
        "order_estimated_delivery_date"
    ]
).copy()

delivery_data["order_delivered_customer_date"] = pd.to_datetime(
    delivery_data["order_delivered_customer_date"]
)

delivery_data["order_estimated_delivery_date"] = pd.to_datetime(
    delivery_data["order_estimated_delivery_date"]
)

delivery_data["Late Delivery"] = (
    delivery_data["order_delivered_customer_date"]
    > delivery_data["order_estimated_delivery_date"]
)

late_orders = delivery_data["Late Delivery"].sum()

late_percentage = (
    late_orders / len(delivery_data) * 100
    if len(delivery_data) else 0
)

d1, d2 = st.columns(2)

d1.metric("Late Deliveries", f"{late_orders:,}")
d2.metric("Late Delivery Rate", f"{late_percentage:.2f}%")

# ==========================================
# CUSTOMER EXPERIENCE
# ==========================================

st.divider()
st.header("⭐ Customer Experience")

review_data = reviews[
    reviews["order_id"].isin(delivered_ids)
]

average_rating = (
    review_data["review_score"].mean()
    if not review_data.empty else 0
)

r1, r2 = st.columns(2)

r1.metric("Average Review Score", f"{average_rating:.2f}/5")

r2.metric(
    "Low Rated Orders",
    f"{(review_data['review_score'] <= 2).sum():,}"
)

review_distribution = (
    review_data["review_score"]
    .value_counts()
    .sort_index()
    .reset_index()
)

review_distribution.columns = ["Rating", "Count"]

fig = px.bar(
    review_distribution,
    x="Rating",
    y="Count",
    title="Customer Review Distribution"
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================
# BUSINESS INSIGHTS
# ==========================================

st.divider()
st.header("💡 Business Insights")

if not monthly_revenue.empty:

    best_month = monthly_revenue.loc[
        monthly_revenue["Revenue (INR)"].idxmax()
    ]

    st.success(
        f"🏆 Highest revenue month: {best_month['Month']} "
        f"with ₹{best_month['Revenue (INR)']:,.0f} revenue."
    )

    if len(monthly_revenue) >= 2:

        first_revenue = monthly_revenue.iloc[0]["Revenue (INR)"]
        last_revenue = monthly_revenue.iloc[-1]["Revenue (INR)"]

        if first_revenue != 0:

            growth = (
                (last_revenue - first_revenue)
                / first_revenue
            ) * 100

            st.info(
                f"📊 Revenue change between first and last "
                f"months: {growth:.2f}%."
            )

if not category_sales.empty:

    top_category = category_sales.loc[
        category_sales["category_sales_inr"].idxmax()
    ]

    st.success(
        f"📦 Best category: "
        f"{top_category['product_category']} "
        f"with ₹{top_category['category_sales_inr']:,.0f} sales."
    )

# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "E-Commerce Business Analytics | "
    "Built using Python, MySQL, Streamlit and Plotly"
)

st.caption(
    "Currency conversion uses an approximate fixed rate "
    "of ₹17.25 per Brazilian Real."
)
