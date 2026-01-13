# Retail Transaction Anomaly Detection

> Identifying unusual transaction patterns in e-commerce data using Machine Learning and Statistical Methods

## Key Results

| Metric | Value | Impact |
|--------|-------|--------|
| Anomaly Detection Rate | ~5% | Identified high-value outlier transactions |
| Revenue at Risk | Varies | Quantified potential fraud/error exposure |
| Model Precision | High | Isolation Forest + IQR cross-validation |

## Business Problem

E-commerce platforms process thousands of transactions daily. Identifying anomalous transactions - whether from fraud, data entry errors, or unusual customer behavior - is critical for:
- **Fraud Prevention**: Early detection of suspicious activity
- **Data Quality**: Identifying data entry or system errors
- **Business Intelligence**: Understanding unusual purchasing patterns

This project implements a multi-method anomaly detection system that combines machine learning (Isolation Forest) with statistical approaches (IQR, Z-Score) to flag transactions that warrant further investigation.

## Tech Stack

`Python` `SQL` `Streamlit` `scikit-learn` `DuckDB` `Plotly`

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/retail-anomaly-detection.git
cd retail-anomaly-detection

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download dataset (see Data Setup section)

# Run the dashboard
streamlit run app/streamlit_app.py
```

## Data Setup

1. Download the **Brazilian E-Commerce Public Dataset by Olist** from Kaggle:
   - Link: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

2. Extract the following CSV files to `data/raw/`:
   - `olist_orders_dataset.csv`
   - `olist_order_items_dataset.csv`
   - `olist_customers_dataset.csv`
   - `olist_order_payments_dataset.csv`
   - `olist_products_dataset.csv` (optional)
   - `olist_sellers_dataset.csv` (optional)

## Project Structure

```
retail-anomaly-detection/
├── data/
│   └── raw/                    # Place Olist CSV files here
├── notebooks/
│   ├── 01_eda.ipynb           # Exploratory Data Analysis
│   └── 02_anomaly_detection.ipynb
├── sql/
│   ├── 01_data_cleaning.sql   # Data preparation queries
│   ├── 02_anomaly_flags.sql   # Statistical anomaly detection
│   └── 03_aggregations.sql    # Dashboard aggregation queries
├── src/
│   ├── __init__.py
│   ├── anomaly_detector.py    # Core ML anomaly detection
│   └── data_loader.py         # Data loading utilities
├── app/
│   └── streamlit_app.py       # Interactive dashboard
├── assets/                     # Images and screenshots
├── requirements.txt
└── README.md
```

## Methodology

### 1. Data Preparation (SQL)
- Load and join multiple Olist tables using DuckDB
- Clean and enrich order data with customer/payment info
- Create time-based features (hour, day of week)

### 2. Anomaly Detection (Python)

**Machine Learning - Isolation Forest:**
- Unsupervised algorithm that isolates outliers
- Features: order amount, item count, installments, time of day
- Contamination parameter set to 5%

**Statistical Methods:**
- **IQR Method**: Flag values outside [Q1 - 1.5×IQR, Q3 + 1.5×IQR]
- **Z-Score**: Flag values > 3 standard deviations from mean

### 3. Visualization (Streamlit)
- Interactive filters by state, anomaly type, amount range
- Distribution charts, time series, geographic analysis
- Exportable anomaly transaction list

## Key Findings

1. **High-Value Outliers**: ~5% of transactions flagged as anomalous, with average anomaly order value significantly higher than normal orders

2. **Regional Patterns**: Certain states show higher anomaly rates, warranting geographic-specific investigation

3. **Time-Based Anomalies**: Orders placed during unusual hours (2-5 AM) show different characteristics

4. **Payment Patterns**: High installment counts (>10) correlate with higher anomaly flags

## Dashboard Features

- **KPI Cards**: Total orders, anomaly count, revenue at risk
- **Distribution Analysis**: Order amount histogram with anomaly overlay
- **Time Series**: Monthly trends with dual-axis (volume + anomaly rate)
- **Geographic View**: State-level anomaly breakdown
- **Drill-Down Table**: Detailed view of flagged transactions
- **Export**: Download anomaly data as CSV

## Usage Examples

```python
from src.anomaly_detector import RetailAnomalyDetector

# Initialize detector
detector = RetailAnomalyDetector(contamination=0.05)

# Load and process data
detector.load_data('data/raw/')
detector.fit_isolation_forest()
detector.add_statistical_flags()

# Get summary statistics
stats = detector.get_summary_stats()
print(f"Anomaly Rate: {stats['anomaly_rate_ml']:.1f}%")

# Get anomalies by state
state_anomalies = detector.get_anomalies_by_state()
```

## SQL Analysis

Run SQL scripts directly with DuckDB:

```bash
duckdb < sql/01_data_cleaning.sql
duckdb < sql/02_anomaly_flags.sql
duckdb < sql/03_aggregations.sql
```

## Future Enhancements

- [ ] Add product category analysis
- [ ] Implement real-time streaming detection
- [ ] Add seller-level anomaly detection
- [ ] Integration with alerting systems

## Author

**Thegeshwar**

---

*Built as a portfolio project demonstrating retail analytics, anomaly detection, and dashboard development skills.*
