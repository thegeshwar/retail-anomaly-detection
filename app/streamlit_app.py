"""
Retail Anomaly Detection Dashboard
Interactive visualization of transaction anomalies in Brazilian e-commerce data
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.anomaly_detector import RetailAnomalyDetector

# Page configuration
st.set_page_config(
    page_title="Retail Anomaly Detection",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def load_and_process_data():
    """Load data and run anomaly detection (cached for performance)"""
    detector = RetailAnomalyDetector(contamination=0.05)
    detector.load_data()
    detector.fit_isolation_forest()
    detector.add_statistical_flags()
    return detector


def create_kpi_metrics(stats):
    """Display KPI metrics in columns"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Orders Analyzed",
            value=f"{stats['total_orders']:,}"
        )

    with col2:
        st.metric(
            label="Anomalies Detected",
            value=f"{stats['anomaly_count_ml']:,}",
            delta=f"{stats['anomaly_rate_ml']:.1f}% of total"
        )

    with col3:
        anomaly_pct = stats['anomaly_revenue'] / stats['total_revenue'] * 100
        st.metric(
            label="Revenue at Risk",
            value=f"R${stats['anomaly_revenue']:,.0f}",
            delta=f"{anomaly_pct:.1f}% of total"
        )

    with col4:
        change_pct = (stats['avg_anomaly_order'] / stats['avg_normal_order'] - 1) * 100
        st.metric(
            label="Avg Anomaly Value",
            value=f"R${stats['avg_anomaly_order']:,.0f}",
            delta=f"{change_pct:+.0f}% vs normal"
        )


def create_distribution_chart(df):
    """Create order amount distribution histogram"""
    fig = px.histogram(
        df,
        x='total_amount',
        color='is_anomaly_ml',
        nbins=50,
        color_discrete_map={True: '#e74c3c', False: '#3498db'},
        labels={'is_anomaly_ml': 'Anomaly', 'total_amount': 'Order Amount (R$)'},
        title='Order Amount Distribution'
    )
    fig.update_layout(
        bargap=0.1,
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99)
    )
    return fig


def create_anomaly_score_chart(df):
    """Create anomaly score distribution"""
    fig = px.histogram(
        df,
        x='anomaly_probability',
        color='anomaly_type',
        nbins=50,
        labels={'anomaly_probability': 'Anomaly Score (higher = more anomalous)'},
        title='Anomaly Score Distribution'
    )
    fig.update_layout(
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99)
    )
    return fig


def create_time_series_chart(df):
    """Create time series with dual axis for orders and anomaly rate"""
    monthly = df.groupby(
        df['order_purchase_timestamp'].dt.to_period('M')
    ).agg({
        'order_id': 'count',
        'is_anomaly_ml': 'sum'
    }).reset_index()
    monthly['order_purchase_timestamp'] = monthly['order_purchase_timestamp'].astype(str)
    monthly['anomaly_rate'] = monthly['is_anomaly_ml'] / monthly['order_id'] * 100

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=monthly['order_purchase_timestamp'],
            y=monthly['order_id'],
            name='Total Orders',
            marker_color='#3498db'
        ),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(
            x=monthly['order_purchase_timestamp'],
            y=monthly['anomaly_rate'],
            name='Anomaly Rate %',
            line=dict(color='#e74c3c', width=3),
            mode='lines+markers'
        ),
        secondary_y=True
    )

    fig.update_layout(
        title='Anomalies Over Time',
        hovermode='x unified'
    )
    fig.update_yaxes(title_text="Order Count", secondary_y=False)
    fig.update_yaxes(title_text="Anomaly Rate %", secondary_y=True)

    return fig


def create_state_chart(state_summary):
    """Create bar chart of anomalies by state"""
    fig = px.bar(
        state_summary.head(15).reset_index(),
        x='customer_state',
        y='anomaly_count',
        color='anomaly_rate',
        color_continuous_scale='Reds',
        labels={
            'customer_state': 'State',
            'anomaly_count': 'Anomaly Count',
            'anomaly_rate': 'Anomaly Rate %'
        },
        title='Anomalies by State (Top 15)'
    )
    return fig


def create_hourly_chart(df):
    """Create hourly distribution of anomalies"""
    hourly = df.groupby('hour_of_day').agg({
        'order_id': 'count',
        'is_anomaly_ml': 'sum'
    }).reset_index()
    hourly['anomaly_rate'] = hourly['is_anomaly_ml'] / hourly['order_id'] * 100

    fig = px.bar(
        hourly,
        x='hour_of_day',
        y='anomaly_rate',
        labels={'hour_of_day': 'Hour of Day', 'anomaly_rate': 'Anomaly Rate %'},
        title='Anomaly Rate by Hour of Day',
        color='anomaly_rate',
        color_continuous_scale='Reds'
    )
    return fig


def main():
    # Header
    st.title("🔍 Retail Transaction Anomaly Detection")
    st.markdown("""
    Identifying unusual transaction patterns in Brazilian e-commerce data using
    **Isolation Forest** and **Statistical Methods** (IQR, Z-Score).
    """)

    # Load data
    try:
        with st.spinner('Loading and processing data...'):
            detector = load_and_process_data()
            df = detector.df
            stats = detector.get_summary_stats()
    except FileNotFoundError:
        st.error("""
        ### Data Files Not Found
        Please download the Olist dataset from Kaggle and place the CSV files in the `data/raw/` directory.

        **Required files:**
        - olist_orders_dataset.csv
        - olist_order_items_dataset.csv
        - olist_customers_dataset.csv
        - olist_order_payments_dataset.csv

        **Download link:** [Brazilian E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
        """)
        return

    # Sidebar filters
    st.sidebar.header("🎛️ Filters")

    # State filter
    states = ['All'] + sorted(df['customer_state'].dropna().unique().tolist())
    selected_state = st.sidebar.selectbox("State", states)

    # Anomaly type filter
    anomaly_types = ['All'] + df['anomaly_type'].unique().tolist()
    selected_anomaly = st.sidebar.selectbox("Anomaly Type", anomaly_types)

    # Amount range filter
    min_amt = float(df['total_amount'].min())
    max_amt = float(df['total_amount'].quantile(0.99))
    amount_range = st.sidebar.slider(
        "Order Amount Range (R$)",
        min_value=min_amt,
        max_value=float(df['total_amount'].max()),
        value=(min_amt, max_amt)
    )

    # Date range filter
    min_date = df['order_purchase_timestamp'].min().date()
    max_date = df['order_purchase_timestamp'].max().date()
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # Apply filters
    filtered_df = df.copy()
    if selected_state != 'All':
        filtered_df = filtered_df[filtered_df['customer_state'] == selected_state]
    if selected_anomaly != 'All':
        filtered_df = filtered_df[filtered_df['anomaly_type'] == selected_anomaly]
    filtered_df = filtered_df[
        (filtered_df['total_amount'] >= amount_range[0]) &
        (filtered_df['total_amount'] <= amount_range[1])
    ]
    if len(date_range) == 2:
        filtered_df = filtered_df[
            (filtered_df['order_purchase_timestamp'].dt.date >= date_range[0]) &
            (filtered_df['order_purchase_timestamp'].dt.date <= date_range[1])
        ]

    # Show filter summary
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Showing:** {len(filtered_df):,} orders")
    st.sidebar.markdown(f"**Filtered from:** {len(df):,} total")

    # KPI Section
    st.markdown("---")
    create_kpi_metrics(stats)

    st.markdown("---")

    # Row 1: Distribution Charts
    col1, col2 = st.columns(2)

    with col1:
        fig = create_distribution_chart(filtered_df)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = create_anomaly_score_chart(filtered_df)
        st.plotly_chart(fig, use_container_width=True)

    # Row 2: Time Series and Geographic
    col1, col2 = st.columns(2)

    with col1:
        fig = create_time_series_chart(filtered_df)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        state_summary = detector.get_anomalies_by_state()
        fig = create_state_chart(state_summary)
        st.plotly_chart(fig, use_container_width=True)

    # Row 3: Additional Analysis
    col1, col2 = st.columns(2)

    with col1:
        fig = create_hourly_chart(filtered_df)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Anomaly type breakdown
        type_counts = filtered_df['anomaly_type'].value_counts().reset_index()
        type_counts.columns = ['Anomaly Type', 'Count']
        fig = px.pie(
            type_counts,
            values='Count',
            names='Anomaly Type',
            title='Anomaly Type Distribution',
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        st.plotly_chart(fig, use_container_width=True)

    # Data Table Section
    st.markdown("---")
    st.subheader("📋 Anomalous Transactions Detail")

    # Show only anomalies
    anomaly_df = filtered_df[filtered_df['is_anomaly_ml']].sort_values(
        'anomaly_probability', ascending=False
    )

    # Select columns to display
    display_cols = [
        'order_id', 'customer_state', 'total_amount', 'total_items',
        'payment_installments', 'hour_of_day', 'anomaly_probability', 'anomaly_type'
    ]
    display_df = anomaly_df[display_cols].head(100)

    # Format columns
    display_df = display_df.copy()
    display_df['total_amount'] = display_df['total_amount'].apply(lambda x: f"R${x:,.2f}")
    display_df['anomaly_probability'] = display_df['anomaly_probability'].apply(lambda x: f"{x:.4f}")

    st.dataframe(display_df, use_container_width=True, height=400)

    # Download button
    csv = anomaly_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Anomaly Data (CSV)",
        data=csv,
        file_name="anomalous_transactions.csv",
        mime="text/csv"
    )

    # Footer
    st.markdown("---")
    st.markdown("""
    ### Methodology

    **Machine Learning Approach:**
    - **Isolation Forest**: Unsupervised algorithm that isolates anomalies by randomly selecting features
      and split values. Anomalies require fewer splits to isolate.

    **Statistical Methods:**
    - **IQR Method**: Flags values outside the range [Q1 - 1.5×IQR, Q3 + 1.5×IQR]
    - **Z-Score**: Identifies values more than 3 standard deviations from the mean

    **Features Used:**
    - Order amount, item count, payment installments, hour of day, day of week

    **Data Source:** [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
    """)


if __name__ == "__main__":
    main()
