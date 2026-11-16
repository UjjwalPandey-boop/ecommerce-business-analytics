-- Active: 1793742355777@@127.0.0.1@3306@ecommerce_analytics

USE ecommerce_analytics;

-- =====================================================
-- 1. TOTAL ORDERS
-- =====================================================

SELECT
    COUNT(DISTINCT order_id) AS total_orders
FROM orders;


-- =====================================================
-- 2. TOTAL CUSTOMERS
-- =====================================================

SELECT
    COUNT(DISTINCT customer_unique_id) AS total_customers
FROM customers;


-- =====================================================
-- 3. ORDER STATUS ANALYSIS
-- =====================================================

SELECT
    order_status,
    COUNT(*) AS total_orders
FROM orders
GROUP BY order_status
ORDER BY total_orders DESC;


-- =====================================================
-- 4. TOTAL REVENUE IN INDIAN RUPEES
-- =====================================================

SELECT
    ROUND(SUM(payment_value) * 17.25, 2)
        AS total_revenue_inr
FROM payments;


-- =====================================================
-- 5. REVENUE FROM DELIVERED ORDERS IN INR
-- =====================================================

SELECT
    ROUND(SUM(p.payment_value) * 17.25, 2)
        AS delivered_revenue_inr
FROM orders o
JOIN payments p
    ON o.order_id = p.order_id
WHERE o.order_status = 'delivered';


-- =====================================================
-- 6. AVERAGE ORDER VALUE (AVERAGE BILL AMOUNT)
-- =====================================================

SELECT
    ROUND(
        SUM(p.payment_value) * 17.25
        / COUNT(DISTINCT p.order_id),
        2
    ) AS average_order_value_inr
FROM orders o
JOIN payments p
    ON o.order_id = p.order_id
WHERE o.order_status = 'delivered';


-- =====================================================
-- 7. MONTHLY SALES IN INR
-- =====================================================

SELECT
    DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m')
        AS sales_month,

    ROUND(SUM(p.payment_value) * 17.25, 2)
        AS monthly_sales_inr

FROM orders o
JOIN payments p
    ON o.order_id = p.order_id

WHERE o.order_status = 'delivered'

GROUP BY sales_month
ORDER BY sales_month;


-- =====================================================
-- 8. MONTHLY ORDER COUNT
-- =====================================================

SELECT
    DATE_FORMAT(order_purchase_timestamp, '%Y-%m')
        AS sales_month,

    COUNT(*) AS total_orders

FROM orders

WHERE order_status = 'delivered'

GROUP BY sales_month
ORDER BY sales_month;


-- =====================================================
-- 9. TOP 10 BEST-SELLING PRODUCTS
-- =====================================================

SELECT
    product_id,
    COUNT(*) AS units_sold,
    ROUND(SUM(price) * 17.25, 2)
        AS product_sales_inr

FROM order_items

GROUP BY product_id
ORDER BY units_sold DESC
LIMIT 10;


-- =====================================================
-- 10. TOP 10 PRODUCT CATEGORIES BY SALES
-- =====================================================

SELECT
    p.product_category_name AS product_category,

    COUNT(oi.order_item_id) AS units_sold,

    ROUND(SUM(oi.price) * 17.25, 2)
        AS category_sales_inr

FROM order_items oi

JOIN products p
    ON oi.product_id = p.product_id

GROUP BY p.product_category_name

ORDER BY category_sales_inr DESC
LIMIT 10;


-- =====================================================
-- 11. CUSTOMER DISTRIBUTION BY STATE
-- =====================================================

SELECT
    customer_state AS state,

    COUNT(DISTINCT customer_unique_id)
        AS total_customers

FROM customers

GROUP BY customer_state
ORDER BY total_customers DESC;


-- =====================================================
-- 12. PAYMENT METHOD ANALYSIS
-- =====================================================

SELECT
    payment_type,

    COUNT(*) AS payment_transactions,

    ROUND(SUM(payment_value) * 17.25, 2)
        AS total_payment_inr,

    ROUND(
        SUM(payment_value) * 100
        / (SELECT SUM(payment_value) FROM payments),
        2
    ) AS payment_share_percentage

FROM payments

GROUP BY payment_type
ORDER BY total_payment_inr DESC;


-- =====================================================
-- 13. DELIVERY PERFORMANCE
-- =====================================================

SELECT
    COUNT(*) AS delivered_orders,

    SUM(
        CASE
            WHEN order_delivered_customer_date
                 > order_estimated_delivery_date
            THEN 1
            ELSE 0
        END
    ) AS late_deliveries,

    ROUND(
        SUM(
            CASE
                WHEN order_delivered_customer_date
                     > order_estimated_delivery_date
                THEN 1
                ELSE 0
            END
        ) * 100.0 / COUNT(*),
        2
    ) AS late_delivery_percentage

FROM orders

WHERE order_status = 'delivered';


-- =====================================================
-- 14. CUSTOMER REVIEW ANALYSIS
-- =====================================================

SELECT
    review_score,

    COUNT(*) AS total_reviews,

    ROUND(
        COUNT(*) * 100.0
        / (SELECT COUNT(*) FROM reviews),
        2
    ) AS review_percentage

FROM reviews

GROUP BY review_score
ORDER BY review_score DESC;


-- =====================================================
-- 15. TOP 10 SELLERS BY SALES IN INR
-- =====================================================

SELECT
    seller_id,

    COUNT(*) AS products_sold,

    ROUND(SUM(price) * 17.25, 2)
        AS seller_sales_inr

FROM order_items

GROUP BY seller_id

ORDER BY seller_sales_inr DESC
LIMIT 10;



-- 16. MONTHLY REVENUE GROWTH

SELECT
    current_month.sales_month,

    ROUND(current_month.revenue_inr, 2)
        AS revenue_inr,

    ROUND(
        (
            current_month.revenue_inr
            - previous_month.revenue_inr
        ) * 100
        / NULLIF(previous_month.revenue_inr, 0),
        2
    ) AS monthly_growth_percentage

FROM
(
    SELECT
        DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m')
            AS sales_month,

        SUM(p.payment_value) * 17.25
            AS revenue_inr

    FROM orders o

    JOIN payments p
        ON o.order_id = p.order_id

    WHERE o.order_status = 'delivered'

    GROUP BY sales_month
) AS current_month

LEFT JOIN
(
    SELECT
        DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m')
            AS sales_month,

        SUM(p.payment_value) * 17.25
            AS revenue_inr

    FROM orders o

    JOIN payments p
        ON o.order_id = p.order_id

    WHERE o.order_status = 'delivered'

    GROUP BY sales_month
) AS previous_month

ON previous_month.sales_month =
    DATE_FORMAT(
        DATE_SUB(
            STR_TO_DATE(
                CONCAT(current_month.sales_month, '-01'),
                '%Y-%m-%d'
            ),
            INTERVAL 1 MONTH
        ),
        '%Y-%m'
    )

ORDER BY current_month.sales_month;



-- =====================================================
-- 17. AVERAGE DELIVERY TIME IN DAYS
-- =====================================================

SELECT
    ROUND(
        AVG(
            DATEDIFF(
                order_delivered_customer_date,
                order_purchase_timestamp
            )
        ),
        2
    ) AS average_delivery_days

FROM orders

WHERE order_status = 'delivered';


-- =====================================================
-- 18. REVENUE BY CUSTOMER STATE IN INR
-- =====================================================

SELECT
    c.customer_state AS state,

    COUNT(DISTINCT o.order_id) AS total_orders,

    ROUND(SUM(p.payment_value) * 17.25, 2)
        AS revenue_inr

FROM customers c

JOIN orders o
    ON c.customer_id = o.customer_id

JOIN payments p
    ON o.order_id = p.order_id

WHERE o.order_status = 'delivered'

GROUP BY c.customer_state

ORDER BY revenue_inr DESC;


-- =====================================================
-- 19. REPEAT CUSTOMER ANALYSIS
-- =====================================================

SELECT
    customer_unique_id,

    COUNT(DISTINCT o.order_id) AS total_orders

FROM customers c

JOIN orders o
    ON c.customer_id = o.customer_id

WHERE o.order_status = 'delivered'

GROUP BY customer_unique_id

HAVING COUNT(DISTINCT o.order_id) > 1

ORDER BY total_orders DESC;


-- =====================================================
-- 20. REVENUE CONTRIBUTION BY PAYMENT METHOD
-- =====================================================

SELECT
    payment_type,

    ROUND(SUM(payment_value) * 17.25, 2)
        AS revenue_inr,

    ROUND(
        SUM(payment_value) * 100
        / (SELECT SUM(payment_value) FROM payments),
        2
    ) AS revenue_contribution_percentage

FROM payments

GROUP BY payment_type

ORDER BY revenue_inr DESC;

SELECT COUNT(DISTINCT order_id) AS delivered_orders
FROM orders
WHERE order_status = 'delivered';

SELECT COUNT(DISTINCT customer_unique_id) AS unique_customers
FROM customers;

SHOW TABLES;
DESCRIBE category_translation;