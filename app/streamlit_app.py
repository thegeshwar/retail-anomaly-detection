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

# Color palette - professional, works with dark/light mode
COLORS = {
    'primary': '#4A90D9',
    'secondary': '#6C757D',
    'success': '#28A745',
    'danger': '#DC3545',
    'warning': '#FFC107',
    'info': '#17A2B8',
    'light': '#F8F9FA',
    'dark': '#343A40',
    'anomaly': '#E63946',
    'normal': '#457B9D',
    'highlight': '#F4A261'
}

# Page configuration
st.set_page_config(
    page_title="Retail Anomaly Detection",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Header styling */
    h1 {
        font-weight: 600;
        letter-spacing: -0.5px;
        margin-bottom: 0.5rem;
    }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, rgba(74, 144, 217, 0.1) 0%, rgba(74, 144, 217, 0.05) 100%);
        border: 1px solid rgba(74, 144, 217, 0.2);
        border-radius: 8px;
        padding: 1rem;
    }

    [data-testid="metric-container"] label {
        font-size: 0.85rem;
        font-weight: 500;
        color: #8B949E;
    }

    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 600;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: rgba(0, 0, 0, 0.02);
    }

    [data-testid="stSidebar"] h2 {
        font-size: 1rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #8B949E;
        margin-bottom: 1rem;
    }

    /* Divider */
    hr {
        margin: 1.5rem 0;
        border: none;
        border-top: 1px solid rgba(128, 128, 128, 0.2);
    }

    /* Data table */
    [data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
    }

    /* Section headers */
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid rgba(74, 144, 217, 0.3);
    }

    /* Button styling */
    .stDownloadButton button {
        background-color: #4A90D9;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }

    .stDownloadButton button:hover {
        background-color: #3A7BC8;
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


def create_kpi_metrics(stats, filtered_stats=None):
    """Display KPI metrics in columns"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Orders",
            value=f"{stats['total_orders']:,}"
        )

    with col2:
        st.metric(
            label="Anomalies Detected",
            value=f"{stats['anomaly_count_ml']:,}",
            delta=f"{stats['anomaly_rate_ml']:.1f}%"
        )

    with col3:
        anomaly_pct = stats['anomaly_revenue'] / stats['total_revenue'] * 100
        st.metric(
            label="Revenue at Risk",
            value=f"R$ {stats['anomaly_revenue']:,.0f}",
            delta=f"{anomaly_pct:.1f}%"
        )

    with col4:
        change_pct = (stats['avg_anomaly_order'] / stats['avg_normal_order'] - 1) * 100
        st.metric(
            label="Avg Anomaly Value",
            value=f"R$ {stats['avg_anomaly_order']:,.0f}",
            delta=f"+{change_pct:.0f}% vs normal"
        )


def create_distribution_chart(df):
    """Create order amount distribution histogram"""
    fig = px.histogram(
        df,
        x='total_amount',
        color='is_anomaly_ml',
        nbins=50,
        color_discrete_map={True: COLORS['anomaly'], False: COLORS['normal']},
        labels={'is_anomaly_ml': 'Anomaly', 'total_amount': 'Order Amount (R$)'}
    )
    fig.update_layout(
        title=dict(text='Order Amount Distribution', font=dict(size=16)),
        bargap=0.05,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(t=60, b=40, l=40, r=40),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    fig.update_xaxes(gridcolor='rgba(128,128,128,0.1)', title_font=dict(size=12))
    fig.update_yaxes(gridcolor='rgba(128,128,128,0.1)', title_font=dict(size=12))
    return fig


def create_anomaly_score_chart(df):
    """Create anomaly score distribution"""
    color_map = {
        'Normal': COLORS['normal'],
        'ML Detected': COLORS['info'],
        'Statistical Outlier': COLORS['warning'],
        'High Confidence Anomaly': COLORS['anomaly']
    }

    fig = px.histogram(
        df,
        x='anomaly_probability',
        color='anomaly_type',
        nbins=50,
        color_discrete_map=color_map,
        labels={'anomaly_probability': 'Anomaly Score'}
    )
    fig.update_layout(
        title=dict(text='Anomaly Score Distribution', font=dict(size=16)),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10)
        ),
        margin=dict(t=60, b=40, l=40, r=40),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    fig.update_xaxes(gridcolor='rgba(128,128,128,0.1)', title_font=dict(size=12))
    fig.update_yaxes(gridcolor='rgba(128,128,128,0.1)', title_font=dict(size=12))
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
            marker_color=COLORS['normal'],
            opacity=0.7
        ),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(
            x=monthly['order_purchase_timestamp'],
            y=monthly['anomaly_rate'],
            name='Anomaly Rate %',
            line=dict(color=COLORS['anomaly'], width=3),
            mode='lines+markers',
            marker=dict(size=6)
        ),
        secondary_y=True
    )

    fig.update_layout(
        title=dict(text='Monthly Trend Analysis', font=dict(size=16)),
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(t=60, b=40, l=40, r=40),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    fig.update_xaxes(gridcolor='rgba(128,128,128,0.1)', title_text='Month')
    fig.update_yaxes(title_text="Order Count", secondary_y=False, gridcolor='rgba(128,128,128,0.1)')
    fig.update_yaxes(title_text="Anomaly Rate %", secondary_y=True, gridcolor='rgba(128,128,128,0.1)')

    return fig


def create_state_chart(state_summary):
    """Create bar chart of anomalies by state"""
    data = state_summary.head(12).reset_index()

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=data['customer_state'],
        y=data['anomaly_count'],
        marker=dict(
            color=data['anomaly_rate'],
            colorscale=[[0, COLORS['normal']], [1, COLORS['anomaly']]],
            colorbar=dict(title='Rate %', thickness=15)
        ),
        text=data['anomaly_count'],
        textposition='outside',
        textfont=dict(size=10)
    ))

    fig.update_layout(
        title=dict(text='Anomalies by State (Top 12)', font=dict(size=16)),
        xaxis_title='State',
        yaxis_title='Anomaly Count',
        margin=dict(t=60, b=40, l=40, r=40),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    fig.update_xaxes(gridcolor='rgba(128,128,128,0.1)')
    fig.update_yaxes(gridcolor='rgba(128,128,128,0.1)')
    return fig


def create_hourly_chart(df):
    """Create hourly distribution of anomalies"""
    hourly = df.groupby('hour_of_day').agg({
        'order_id': 'count',
        'is_anomaly_ml': 'sum'
    }).reset_index()
    hourly['anomaly_rate'] = hourly['is_anomaly_ml'] / hourly['order_id'] * 100

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=hourly['hour_of_day'],
        y=hourly['anomaly_rate'],
        marker=dict(
            color=hourly['anomaly_rate'],
            colorscale=[[0, COLORS['normal']], [0.5, COLORS['warning']], [1, COLORS['anomaly']]]
        )
    ))

    fig.update_layout(
        title=dict(text='Anomaly Rate by Hour', font=dict(size=16)),
        xaxis_title='Hour of Day',
        yaxis_title='Anomaly Rate %',
        margin=dict(t=60, b=40, l=40, r=40),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    fig.update_xaxes(gridcolor='rgba(128,128,128,0.1)', dtick=2)
    fig.update_yaxes(gridcolor='rgba(128,128,128,0.1)')
    return fig


def create_type_breakdown_chart(df):
    """Create anomaly type breakdown"""
    type_counts = df['anomaly_type'].value_counts().reset_index()
    type_counts.columns = ['type', 'count']

    color_map = {
        'Normal': COLORS['normal'],
        'ML Detected': COLORS['info'],
        'Statistical Outlier': COLORS['warning'],
        'High Confidence Anomaly': COLORS['anomaly']
    }
    colors = [color_map.get(t, COLORS['secondary']) for t in type_counts['type']]

    fig = go.Figure(data=[go.Pie(
        labels=type_counts['type'],
        values=type_counts['count'],
        hole=0.4,
        marker=dict(colors=colors),
        textinfo='percent+label',
        textposition='outside',
        textfont=dict(size=11)
    )])

    fig.update_layout(
        title=dict(text='Detection Method Breakdown', font=dict(size=16)),
        showlegend=False,
        margin=dict(t=60, b=40, l=40, r=40),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    return fig


def main():
    # Header
    st.title("Retail Transaction Anomaly Detection")
    st.markdown(
        "Identifying unusual transaction patterns in Brazilian e-commerce data using "
        "**Isolation Forest** and **Statistical Methods** (IQR, Z-Score)."
    )

    # Load data
    try:
        with st.spinner('Loading and processing data...'):
            detector = load_and_process_data()
            df = detector.df
            stats = detector.get_summary_stats()
    except FileNotFoundError:
        st.error("""
        **Data Files Not Found**

        Please download the Olist dataset from Kaggle and place the CSV files in the `data/raw/` directory.

        Required files:
        - olist_orders_dataset.csv
        - olist_order_items_dataset.csv
        - olist_customers_dataset.csv
        - olist_order_payments_dataset.csv

        Download: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
        """)
        return

    # Sidebar filters
    st.sidebar.markdown("## FILTERS")

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
        value=(min_amt, max_amt),
        format="R$ %.0f"
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

    # Filter summary
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Showing:** {len(filtered_df):,} orders")
    st.sidebar.markdown(f"**Total:** {len(df):,} orders")

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
        fig = create_type_breakdown_chart(filtered_df)
        st.plotly_chart(fig, use_container_width=True)

    # Data Table Section
    st.markdown("---")
    st.subheader("Anomalous Transactions")

    # Show only anomalies
    anomaly_df = filtered_df[filtered_df['is_anomaly_ml']].sort_values(
        'anomaly_probability', ascending=False
    )

    if len(anomaly_df) > 0:
        # Select columns to display
        display_cols = [
            'order_id', 'customer_state', 'total_amount', 'total_items',
            'payment_installments', 'hour_of_day', 'anomaly_probability', 'anomaly_type'
        ]
        display_df = anomaly_df[display_cols].head(100).copy()

        # Format columns
        display_df['total_amount'] = display_df['total_amount'].apply(lambda x: f"R$ {x:,.2f}")
        display_df['anomaly_probability'] = display_df['anomaly_probability'].apply(lambda x: f"{x:.4f}")

        # Rename columns for display
        display_df.columns = [
            'Order ID', 'State', 'Amount', 'Items',
            'Installments', 'Hour', 'Anomaly Score', 'Type'
        ]

        st.dataframe(display_df, use_container_width=True, height=400)

        # Download button
        csv = anomaly_df.to_csv(index=False)
        st.download_button(
            label="Download Anomaly Data (CSV)",
            data=csv,
            file_name="anomalous_transactions.csv",
            mime="text/csv"
        )
    else:
        st.info("No anomalies found with current filter criteria.")

    # Methodology Section
    st.markdown("---")
    with st.expander("Methodology"):
        st.markdown("""
        **Machine Learning Approach**

        *Isolation Forest* is an unsupervised algorithm that isolates anomalies by randomly
        selecting features and split values. Anomalies require fewer splits to isolate,
        making them easier to detect.

        **Statistical Methods**

        - *IQR Method*: Flags values outside the range [Q1 - 1.5 x IQR, Q3 + 1.5 x IQR]
        - *Z-Score*: Identifies values more than 3 standard deviations from the mean

        **Features Used**

        Order amount, item count, payment installments, hour of day, day of week

        **Data Source**

        Brazilian E-Commerce Public Dataset by Olist (Kaggle)
        """)


if __name__ == "__main__":
    main()
