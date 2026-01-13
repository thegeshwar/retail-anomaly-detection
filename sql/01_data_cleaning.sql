-- =============================================================================
-- Data Cleaning and Preparation
-- Load and clean Olist e-commerce data using DuckDB
-- =============================================================================

-- Create consolidated orders view with all relevant dimensions
CREATE OR REPLACE VIEW v_orders_enriched AS
SELECT
    o.order_id,
    o.customer_id,
    o.order_status,
    o.order_purchase_timestamp,
    o.order_approved_at,
    o.order_delivered_carrier_date,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,

    -- Time dimensions
    DATE_PART('year', o.order_purchase_timestamp) AS order_year,
    DATE_PART('month', o.order_purchase_timestamp) AS order_month,
    DATE_PART('day', o.order_purchase_timestamp) AS order_day,
    DATE_PART('dow', o.order_purchase_timestamp) AS day_of_week,
    DATE_PART('hour', o.order_purchase_timestamp) AS hour_of_day,
    DATE_PART('week', o.order_purchase_timestamp) AS week_of_year,

    -- Order metrics from order_items
    oi.total_items,
    oi.total_amount,
    oi.total_freight,
    oi.avg_item_price,
    oi.min_item_price,
    oi.max_item_price,

    -- Customer location
    c.customer_city,
    c.customer_state,
    c.customer_zip_code_prefix,

    -- Payment info
    p.payment_type,
    p.payment_installments,
    p.payment_value,
    p.payment_count

FROM read_csv_auto('data/raw/olist_orders_dataset.csv') o

-- Join order items aggregated by order
LEFT JOIN (
    SELECT
        order_id,
        COUNT(*) AS total_items,
        SUM(price + freight_value) AS total_amount,
        SUM(freight_value) AS total_freight,
        AVG(price) AS avg_item_price,
        MIN(price) AS min_item_price,
        MAX(price) AS max_item_price
    FROM read_csv_auto('data/raw/olist_order_items_dataset.csv')
    GROUP BY order_id
) oi ON o.order_id = oi.order_id

-- Join customer data
LEFT JOIN read_csv_auto('data/raw/olist_customers_dataset.csv') c
    ON o.customer_id = c.customer_id

-- Join payment data aggregated by order
LEFT JOIN (
    SELECT
        order_id,
        STRING_AGG(DISTINCT payment_type, ', ') AS payment_type,
        MAX(payment_installments) AS payment_installments,
        SUM(payment_value) AS payment_value,
        COUNT(*) AS payment_count
    FROM read_csv_auto('data/raw/olist_order_payments_dataset.csv')
    GROUP BY order_id
) p ON o.order_id = p.order_id

WHERE o.order_status = 'delivered';


-- =============================================================================
-- Data Quality Checks
-- =============================================================================

-- Check for NULL values in key fields
SELECT
    'order_id' AS field,
    COUNT(*) FILTER (WHERE order_id IS NULL) AS null_count,
    COUNT(*) AS total_count
FROM v_orders_enriched
UNION ALL
SELECT 'total_amount', COUNT(*) FILTER (WHERE total_amount IS NULL), COUNT(*) FROM v_orders_enriched
UNION ALL
SELECT 'customer_state', COUNT(*) FILTER (WHERE customer_state IS NULL), COUNT(*) FROM v_orders_enriched
UNION ALL
SELECT 'payment_value', COUNT(*) FILTER (WHERE payment_value IS NULL), COUNT(*) FROM v_orders_enriched;


-- Check for duplicate order_ids
SELECT
    order_id,
    COUNT(*) AS cnt
FROM v_orders_enriched
GROUP BY order_id
HAVING COUNT(*) > 1;


-- Summary statistics for key numeric fields
SELECT
    COUNT(*) AS total_orders,
    AVG(total_amount) AS avg_order_amount,
    STDDEV(total_amount) AS std_order_amount,
    MIN(total_amount) AS min_order_amount,
    MAX(total_amount) AS max_order_amount,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY total_amount) AS q1_amount,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY total_amount) AS median_amount,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total_amount) AS q3_amount,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY total_amount) AS p99_amount
FROM v_orders_enriched
WHERE total_amount IS NOT NULL;
