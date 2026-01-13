-- =============================================================================
-- Statistical Anomaly Detection using SQL
-- Implements Z-Score and IQR methods for outlier detection
-- =============================================================================

-- Calculate global statistics for anomaly detection
CREATE OR REPLACE VIEW v_global_stats AS
SELECT
    AVG(total_amount) AS mean_amount,
    STDDEV(total_amount) AS std_amount,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY total_amount) AS q1,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total_amount) AS q3,
    AVG(total_items) AS mean_items,
    STDDEV(total_items) AS std_items,
    AVG(payment_installments) AS mean_installments,
    STDDEV(payment_installments) AS std_installments
FROM v_orders_enriched
WHERE total_amount IS NOT NULL;


-- Main anomaly detection view with multiple flags
CREATE OR REPLACE VIEW v_anomaly_stats AS
WITH stats AS (SELECT * FROM v_global_stats)

SELECT
    o.*,
    s.mean_amount,
    s.std_amount,
    s.q1,
    s.q3,

    -- Z-score calculations
    CASE
        WHEN s.std_amount > 0 THEN (o.total_amount - s.mean_amount) / s.std_amount
        ELSE 0
    END AS amount_zscore,

    CASE
        WHEN s.std_items > 0 THEN (o.total_items - s.mean_items) / s.std_items
        ELSE 0
    END AS items_zscore,

    -- IQR-based amount flags
    CASE
        WHEN o.total_amount > s.q3 + 1.5 * (s.q3 - s.q1) THEN 'HIGH_AMOUNT'
        WHEN o.total_amount < s.q1 - 1.5 * (s.q3 - s.q1) THEN 'LOW_AMOUNT'
        ELSE 'NORMAL'
    END AS amount_flag,

    -- Extreme outlier flag (3x IQR)
    CASE
        WHEN o.total_amount > s.q3 + 3 * (s.q3 - s.q1) THEN 'EXTREME_HIGH'
        WHEN o.total_amount < s.q1 - 3 * (s.q3 - s.q1) THEN 'EXTREME_LOW'
        ELSE 'NORMAL'
    END AS extreme_flag,

    -- Time-based anomaly (orders at unusual hours: 2 AM - 5 AM)
    CASE
        WHEN o.hour_of_day BETWEEN 2 AND 5 THEN 'UNUSUAL_HOUR'
        ELSE 'NORMAL'
    END AS time_flag,

    -- High installment flag (more than 10 installments is unusual)
    CASE
        WHEN o.payment_installments > 10 THEN 'HIGH_INSTALLMENTS'
        ELSE 'NORMAL'
    END AS installment_flag,

    -- Large order flag (many items)
    CASE
        WHEN o.total_items > 5 THEN 'LARGE_ORDER'
        ELSE 'NORMAL'
    END AS size_flag,

    -- Combined anomaly score (count of anomaly flags)
    (CASE WHEN o.total_amount > s.q3 + 1.5 * (s.q3 - s.q1) THEN 1 ELSE 0 END +
     CASE WHEN o.total_amount < s.q1 - 1.5 * (s.q3 - s.q1) THEN 1 ELSE 0 END +
     CASE WHEN o.hour_of_day BETWEEN 2 AND 5 THEN 1 ELSE 0 END +
     CASE WHEN o.payment_installments > 10 THEN 1 ELSE 0 END +
     CASE WHEN o.total_items > 5 THEN 1 ELSE 0 END) AS anomaly_flag_count

FROM v_orders_enriched o
CROSS JOIN stats s;


-- =============================================================================
-- Anomaly Summary Views
-- =============================================================================

-- Count of orders by anomaly type
CREATE OR REPLACE VIEW v_anomaly_summary AS
SELECT
    amount_flag,
    time_flag,
    installment_flag,
    COUNT(*) AS order_count,
    SUM(total_amount) AS total_revenue,
    AVG(total_amount) AS avg_order_value,
    MIN(total_amount) AS min_order_value,
    MAX(total_amount) AS max_order_value
FROM v_anomaly_stats
GROUP BY amount_flag, time_flag, installment_flag
ORDER BY order_count DESC;


-- High-risk transactions (multiple anomaly flags)
CREATE OR REPLACE VIEW v_high_risk_transactions AS
SELECT
    order_id,
    customer_id,
    customer_state,
    order_purchase_timestamp,
    total_amount,
    total_items,
    payment_installments,
    amount_flag,
    time_flag,
    installment_flag,
    anomaly_flag_count,
    amount_zscore
FROM v_anomaly_stats
WHERE anomaly_flag_count >= 2
ORDER BY anomaly_flag_count DESC, total_amount DESC;
