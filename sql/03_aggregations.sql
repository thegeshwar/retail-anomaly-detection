-- =============================================================================
-- Aggregation Queries for Dashboard
-- Summary metrics and trends for visualization
-- =============================================================================

-- =============================================================================
-- 1. Overall Anomaly Summary
-- =============================================================================
SELECT
    amount_flag,
    COUNT(*) AS order_count,
    SUM(total_amount) AS total_revenue,
    AVG(total_amount) AS avg_order_value,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() AS pct_of_orders,
    SUM(total_amount) * 100.0 / SUM(SUM(total_amount)) OVER() AS pct_of_revenue
FROM v_anomaly_stats
GROUP BY amount_flag
ORDER BY order_count DESC;


-- =============================================================================
-- 2. Monthly Anomaly Trends
-- =============================================================================
SELECT
    order_year,
    order_month,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN amount_flag != 'NORMAL' THEN 1 ELSE 0 END) AS anomaly_count,
    SUM(CASE WHEN amount_flag != 'NORMAL' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS anomaly_rate,
    SUM(total_amount) AS total_revenue,
    SUM(CASE WHEN amount_flag != 'NORMAL' THEN total_amount ELSE 0 END) AS anomaly_revenue,
    AVG(total_amount) AS avg_order_value
FROM v_anomaly_stats
GROUP BY order_year, order_month
ORDER BY order_year, order_month;


-- =============================================================================
-- 3. Regional Anomaly Distribution
-- =============================================================================
SELECT
    customer_state,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN amount_flag != 'NORMAL' THEN 1 ELSE 0 END) AS anomaly_count,
    SUM(CASE WHEN amount_flag != 'NORMAL' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS anomaly_rate,
    SUM(total_amount) AS total_revenue,
    SUM(CASE WHEN amount_flag = 'HIGH_AMOUNT' THEN total_amount ELSE 0 END) AS high_amount_revenue,
    AVG(total_amount) AS avg_order_value
FROM v_anomaly_stats
GROUP BY customer_state
ORDER BY anomaly_count DESC;


-- =============================================================================
-- 4. Hourly Distribution of Anomalies
-- =============================================================================
SELECT
    hour_of_day,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN amount_flag != 'NORMAL' THEN 1 ELSE 0 END) AS anomaly_count,
    SUM(CASE WHEN amount_flag != 'NORMAL' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS anomaly_rate,
    AVG(total_amount) AS avg_order_value
FROM v_anomaly_stats
GROUP BY hour_of_day
ORDER BY hour_of_day;


-- =============================================================================
-- 5. Day of Week Analysis
-- =============================================================================
SELECT
    day_of_week,
    CASE day_of_week
        WHEN 0 THEN 'Sunday'
        WHEN 1 THEN 'Monday'
        WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday'
        WHEN 4 THEN 'Thursday'
        WHEN 5 THEN 'Friday'
        WHEN 6 THEN 'Saturday'
    END AS day_name,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN amount_flag != 'NORMAL' THEN 1 ELSE 0 END) AS anomaly_count,
    SUM(CASE WHEN amount_flag != 'NORMAL' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS anomaly_rate,
    SUM(total_amount) AS total_revenue
FROM v_anomaly_stats
GROUP BY day_of_week
ORDER BY day_of_week;


-- =============================================================================
-- 6. Payment Method Analysis
-- =============================================================================
SELECT
    payment_type,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN amount_flag != 'NORMAL' THEN 1 ELSE 0 END) AS anomaly_count,
    SUM(CASE WHEN amount_flag != 'NORMAL' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS anomaly_rate,
    AVG(payment_installments) AS avg_installments,
    SUM(total_amount) AS total_revenue
FROM v_anomaly_stats
GROUP BY payment_type
ORDER BY total_orders DESC;


-- =============================================================================
-- 7. Z-Score Distribution Buckets
-- =============================================================================
SELECT
    CASE
        WHEN amount_zscore < -3 THEN '< -3 (Extreme Low)'
        WHEN amount_zscore < -2 THEN '-3 to -2 (Very Low)'
        WHEN amount_zscore < -1 THEN '-2 to -1 (Low)'
        WHEN amount_zscore < 1 THEN '-1 to 1 (Normal)'
        WHEN amount_zscore < 2 THEN '1 to 2 (High)'
        WHEN amount_zscore < 3 THEN '2 to 3 (Very High)'
        ELSE '>= 3 (Extreme High)'
    END AS zscore_bucket,
    COUNT(*) AS order_count,
    SUM(total_amount) AS total_revenue,
    AVG(total_amount) AS avg_order_value
FROM v_anomaly_stats
GROUP BY
    CASE
        WHEN amount_zscore < -3 THEN '< -3 (Extreme Low)'
        WHEN amount_zscore < -2 THEN '-3 to -2 (Very Low)'
        WHEN amount_zscore < -1 THEN '-2 to -1 (Low)'
        WHEN amount_zscore < 1 THEN '-1 to 1 (Normal)'
        WHEN amount_zscore < 2 THEN '1 to 2 (High)'
        WHEN amount_zscore < 3 THEN '2 to 3 (Very High)'
        ELSE '>= 3 (Extreme High)'
    END
ORDER BY MIN(amount_zscore);


-- =============================================================================
-- 8. Top Anomalous Transactions
-- =============================================================================
SELECT
    order_id,
    customer_state,
    order_purchase_timestamp,
    total_amount,
    total_items,
    payment_installments,
    payment_type,
    amount_zscore,
    amount_flag,
    time_flag,
    installment_flag,
    anomaly_flag_count
FROM v_anomaly_stats
WHERE amount_flag != 'NORMAL'
   OR time_flag != 'NORMAL'
   OR installment_flag != 'NORMAL'
ORDER BY amount_zscore DESC
LIMIT 100;
