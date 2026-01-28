"""
Data Loader Module
Utility functions for loading and preprocessing Olist e-commerce data
"""

import pandas as pd
import duckdb
from pathlib import Path


class OlistDataLoader:
    """Load and preprocess Olist Brazilian E-Commerce dataset"""

    DATASET_FILES = [
        'olist_orders_dataset.csv',
        'olist_order_items_dataset.csv',
        'olist_customers_dataset.csv',
        'olist_products_dataset.csv',
        'olist_sellers_dataset.csv',
        'olist_order_payments_dataset.csv',
        'olist_order_reviews_dataset.csv',
        'olist_geolocation_dataset.csv'
    ]

    def __init__(self, data_path: str = 'data/sample/'):
        self.data_path = Path(data_path)
        self.conn = duckdb.connect()
        self.tables = {}

    def check_data_exists(self) -> dict:
        """Check which dataset files exist"""
        status = {}
        for file in self.DATASET_FILES:
            file_path = self.data_path / file
            status[file] = file_path.exists()
        return status

    def load_all_tables(self) -> dict:
        """Load all CSV files into DuckDB tables"""
        for file in self.DATASET_FILES:
            file_path = self.data_path / file
            if file_path.exists():
                table_name = file.replace('olist_', '').replace('_dataset.csv', '')
                self.tables[table_name] = self.conn.execute(
                    f"SELECT * FROM read_csv_auto('{file_path}')"
                ).fetchdf()
                print(f"Loaded {table_name}: {len(self.tables[table_name]):,} rows")
        return self.tables

    def get_orders_enriched(self) -> pd.DataFrame:
        """Get enriched orders with items, payments, and customer info"""
        query = f"""
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
            DATE_PART('dow', o.order_purchase_timestamp) AS day_of_week,
            DATE_PART('hour', o.order_purchase_timestamp) AS hour_of_day,

            -- Order metrics
            oi.total_items,
            oi.total_amount,
            oi.total_freight,
            oi.avg_item_price,

            -- Customer info
            c.customer_city,
            c.customer_state,

            -- Payment info
            p.payment_type,
            p.payment_installments,
            p.payment_value

        FROM read_csv_auto('{self.data_path}/olist_orders_dataset.csv') o

        LEFT JOIN (
            SELECT
                order_id,
                COUNT(*) AS total_items,
                SUM(price) AS total_amount,
                SUM(freight_value) AS total_freight,
                AVG(price) AS avg_item_price
            FROM read_csv_auto('{self.data_path}/olist_order_items_dataset.csv')
            GROUP BY order_id
        ) oi ON o.order_id = oi.order_id

        LEFT JOIN read_csv_auto('{self.data_path}/olist_customers_dataset.csv') c
            ON o.customer_id = c.customer_id

        LEFT JOIN (
            SELECT
                order_id,
                STRING_AGG(DISTINCT payment_type, ', ') AS payment_type,
                MAX(payment_installments) AS payment_installments,
                SUM(payment_value) AS payment_value
            FROM read_csv_auto('{self.data_path}/olist_order_payments_dataset.csv')
            GROUP BY order_id
        ) p ON o.order_id = p.order_id

        WHERE o.order_status = 'delivered'
        """

        df = self.conn.execute(query).fetchdf()
        df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
        return df

    def get_product_categories(self) -> pd.DataFrame:
        """Get product category summary"""
        query = f"""
        SELECT
            p.product_category_name,
            COUNT(DISTINCT oi.product_id) AS product_count,
            COUNT(DISTINCT oi.order_id) AS order_count,
            SUM(oi.price) AS total_revenue,
            AVG(oi.price) AS avg_price
        FROM read_csv_auto('{self.data_path}/olist_order_items_dataset.csv') oi
        LEFT JOIN read_csv_auto('{self.data_path}/olist_products_dataset.csv') p
            ON oi.product_id = p.product_id
        GROUP BY p.product_category_name
        ORDER BY total_revenue DESC
        """
        return self.conn.execute(query).fetchdf()

    def get_seller_performance(self) -> pd.DataFrame:
        """Get seller performance metrics"""
        query = f"""
        SELECT
            s.seller_id,
            s.seller_city,
            s.seller_state,
            COUNT(DISTINCT oi.order_id) AS order_count,
            SUM(oi.price) AS total_revenue,
            AVG(oi.price) AS avg_order_value
        FROM read_csv_auto('{self.data_path}/olist_order_items_dataset.csv') oi
        LEFT JOIN read_csv_auto('{self.data_path}/olist_sellers_dataset.csv') s
            ON oi.seller_id = s.seller_id
        GROUP BY s.seller_id, s.seller_city, s.seller_state
        ORDER BY total_revenue DESC
        """
        return self.conn.execute(query).fetchdf()

    def close(self):
        """Close database connection"""
        self.conn.close()


if __name__ == "__main__":
    loader = OlistDataLoader()

    # Check data availability
    print("\n=== DATA FILE STATUS ===")
    status = loader.check_data_exists()
    for file, exists in status.items():
        status_str = "Found" if exists else "Missing"
        print(f"{file}: {status_str}")

    # If data exists, load and display sample
    if all(status.values()):
        print("\n=== LOADING DATA ===")
        loader.load_all_tables()

        print("\n=== ENRICHED ORDERS SAMPLE ===")
        orders = loader.get_orders_enriched()
        print(orders.head())
        print(f"\nTotal orders: {len(orders):,}")

    loader.close()
