"""
Anomaly Detection Module
Uses Isolation Forest and statistical methods to identify outliers
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import duckdb


class RetailAnomalyDetector:
    def __init__(self, contamination=0.05):
        self.contamination = contamination
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = [
            'total_amount',
            'total_items',
            'payment_installments',
            'hour_of_day',
            'day_of_week'
        ]
        self.df = None

    def load_data(self, data_path='data/raw/'):
        """Load and merge all Olist datasets using DuckDB"""
        conn = duckdb.connect()

        query = f"""
        SELECT
            o.order_id,
            o.customer_id,
            o.order_purchase_timestamp,
            DATE_PART('hour', o.order_purchase_timestamp) AS hour_of_day,
            DATE_PART('dow', o.order_purchase_timestamp) AS day_of_week,
            oi.total_items,
            oi.total_amount,
            COALESCE(p.payment_installments, 1) AS payment_installments,
            c.customer_state
        FROM read_csv_auto('{data_path}olist_orders_dataset.csv') o
        LEFT JOIN (
            SELECT order_id, COUNT(*) AS total_items,
                   SUM(price + freight_value) AS total_amount
            FROM read_csv_auto('{data_path}olist_order_items_dataset.csv')
            GROUP BY order_id
        ) oi ON o.order_id = oi.order_id
        LEFT JOIN (
            SELECT order_id, MAX(payment_installments) AS payment_installments
            FROM read_csv_auto('{data_path}olist_order_payments_dataset.csv')
            GROUP BY order_id
        ) p ON o.order_id = p.order_id
        LEFT JOIN read_csv_auto('{data_path}olist_customers_dataset.csv') c
            ON o.customer_id = c.customer_id
        WHERE o.order_status = 'delivered'
          AND oi.total_amount IS NOT NULL
        """

        self.df = conn.execute(query).fetchdf()
        self.df['order_purchase_timestamp'] = pd.to_datetime(
            self.df['order_purchase_timestamp']
        )
        conn.close()
        return self.df

    def fit_isolation_forest(self):
        """Train Isolation Forest model"""
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")

        X = self.df[self.feature_columns].fillna(0)
        X_scaled = self.scaler.fit_transform(X)

        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_estimators=100
        )

        self.df['anomaly_score'] = self.model.fit_predict(X_scaled)
        self.df['anomaly_probability'] = -self.model.score_samples(X_scaled)

        # -1 = anomaly, 1 = normal
        self.df['is_anomaly_ml'] = self.df['anomaly_score'] == -1

        return self

    def add_statistical_flags(self):
        """Add Z-score and IQR based anomaly flags"""
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")

        # Z-score for amount
        mean_amt = self.df['total_amount'].mean()
        std_amt = self.df['total_amount'].std()
        self.df['amount_zscore'] = (self.df['total_amount'] - mean_amt) / std_amt

        # IQR method
        q1 = self.df['total_amount'].quantile(0.25)
        q3 = self.df['total_amount'].quantile(0.75)
        iqr = q3 - q1

        self.df['is_anomaly_iqr'] = (
            (self.df['total_amount'] < q1 - 1.5 * iqr) |
            (self.df['total_amount'] > q3 + 1.5 * iqr)
        )

        # Combined flag
        self.df['anomaly_type'] = 'Normal'
        self.df.loc[self.df['is_anomaly_ml'], 'anomaly_type'] = 'ML Detected'
        self.df.loc[self.df['is_anomaly_iqr'], 'anomaly_type'] = 'Statistical Outlier'
        self.df.loc[
            self.df['is_anomaly_ml'] & self.df['is_anomaly_iqr'],
            'anomaly_type'
        ] = 'High Confidence Anomaly'

        return self

    def get_summary_stats(self):
        """Generate summary statistics"""
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")

        summary = {
            'total_orders': len(self.df),
            'total_revenue': self.df['total_amount'].sum(),
            'anomaly_count_ml': self.df['is_anomaly_ml'].sum(),
            'anomaly_count_iqr': self.df['is_anomaly_iqr'].sum(),
            'anomaly_rate_ml': self.df['is_anomaly_ml'].mean() * 100,
            'anomaly_revenue': self.df.loc[
                self.df['is_anomaly_ml'], 'total_amount'
            ].sum(),
            'avg_normal_order': self.df.loc[
                ~self.df['is_anomaly_ml'], 'total_amount'
            ].mean(),
            'avg_anomaly_order': self.df.loc[
                self.df['is_anomaly_ml'], 'total_amount'
            ].mean(),
        }
        return summary

    def get_anomalies_by_state(self):
        """Aggregate anomalies by state"""
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")

        return self.df.groupby('customer_state').agg({
            'order_id': 'count',
            'is_anomaly_ml': 'sum',
            'total_amount': 'sum'
        }).rename(columns={
            'order_id': 'total_orders',
            'is_anomaly_ml': 'anomaly_count'
        }).assign(
            anomaly_rate=lambda x: x['anomaly_count'] / x['total_orders'] * 100
        ).sort_values('anomaly_count', ascending=False)

    def get_monthly_trends(self):
        """Get monthly anomaly trends"""
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")

        monthly = self.df.groupby(
            self.df['order_purchase_timestamp'].dt.to_period('M')
        ).agg({
            'order_id': 'count',
            'is_anomaly_ml': 'sum',
            'total_amount': 'sum'
        }).reset_index()
        monthly['order_purchase_timestamp'] = monthly['order_purchase_timestamp'].astype(str)
        monthly['anomaly_rate'] = monthly['is_anomaly_ml'] / monthly['order_id'] * 100
        monthly.columns = ['month', 'total_orders', 'anomaly_count', 'total_revenue', 'anomaly_rate']
        return monthly


if __name__ == "__main__":
    detector = RetailAnomalyDetector(contamination=0.05)
    detector.load_data()
    detector.fit_isolation_forest()
    detector.add_statistical_flags()

    print("\n=== ANOMALY DETECTION RESULTS ===")
    stats = detector.get_summary_stats()
    for k, v in stats.items():
        print(f"{k}: {v:,.2f}" if isinstance(v, float) else f"{k}: {v:,}")
