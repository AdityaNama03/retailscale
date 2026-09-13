import sys, os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from connection import run_query
from components.kpi_card import kpi_card
from components.header import page_header
from config import *

# Load CSS
css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'style.css')
with open(css_path) as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

page_header("Data Quality Monitor", "Ensure pipeline integrity, review table statistics, and monitor dbt test results.")

# --- Row Counts Query ---
row_count_query = """
SELECT 'fct_orders' as TABLE_NAME, COUNT(*) as ROW_COUNT FROM fct_orders
UNION ALL SELECT 'fct_order_items', COUNT(*) FROM fct_order_items
UNION ALL SELECT 'fct_payments', COUNT(*) FROM fct_payments
UNION ALL SELECT 'fct_delivery_performance', COUNT(*) FROM fct_delivery_performance
UNION ALL SELECT 'dim_customers', COUNT(*) FROM dim_customers
UNION ALL SELECT 'dim_products', COUNT(*) FROM dim_products
UNION ALL SELECT 'dim_sellers', COUNT(*) FROM dim_sellers
UNION ALL SELECT 'dim_dates', COUNT(*) FROM dim_dates
"""
row_counts_df = run_query(row_count_query)
total_rows = row_counts_df['ROW_COUNT'].sum() if not row_counts_df.empty else 0

# --- KPIs ---
null_rate_query = "SELECT (SUM(CASE WHEN TOTAL_PAYMENT_VALUE IS NULL THEN 1 ELSE 0 END) / COUNT(*)) * 100 as NULL_RATE FROM fct_orders"
null_rate_df = run_query(null_rate_query)
null_rate = null_rate_df['NULL_RATE'].iloc[0] if not null_rate_df.empty else 0

orphan_query = """
SELECT COUNT(*) as ORPHAN_COUNT 
FROM fct_order_items oi 
LEFT JOIN fct_orders o ON oi.ORDER_ID = o.ORDER_ID 
WHERE o.ORDER_ID IS NULL
"""
orphan_df = run_query(orphan_query)
orphan_count = orphan_df['ORPHAN_COUNT'].iloc[0] if not orphan_df.empty else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi_card("Tables Monitored", "8", icon="🗄️")
with col2:
    kpi_card("Total Gold Rows", format_number(total_rows), icon="📊")
with col3:
    kpi_card("Null Rate (Orders)", format_pct(null_rate), icon="⚠️")
with col4:
    kpi_card("Orphan Items", format_number(orphan_count), icon="🔗")

st.markdown("<br>", unsafe_allow_html=True)

# --- Panel 1: Gold Table Row Counts ---
st.subheader("Gold Table Row Counts")
if not row_counts_df.empty:
    tables = row_counts_df.to_dict('records')
    # 4x2 Grid
    c1, c2, c3, c4 = st.columns(4)
    cols = [c1, c2, c3, c4]
    
    for i, row in enumerate(tables):
        with cols[i % 4]:
            kpi_card(row['TABLE_NAME'], format_number(row['ROW_COUNT']), "")
            if i == 3:  # End of first row, add space
                st.markdown("<br>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- Panel 2: Column Null Analysis ---
st.subheader("Column Null Analysis (fct_orders)")
null_analysis_query = """
SELECT
  COUNT(*) as TOTAL,
  SUM(CASE WHEN PURCHASE_DATE IS NULL THEN 1 ELSE 0 END) as NULL_PURCHASE_DATE,
  SUM(CASE WHEN APPROVED_DATE IS NULL THEN 1 ELSE 0 END) as NULL_APPROVED_DATE,
  SUM(CASE WHEN DELIVERY_DATE IS NULL THEN 1 ELSE 0 END) as NULL_DELIVERY_DATE,
  SUM(CASE WHEN TOTAL_PAYMENT_VALUE IS NULL THEN 1 ELSE 0 END) as NULL_PAYMENT,
  SUM(CASE WHEN IS_LATE_DELIVERY IS NULL THEN 1 ELSE 0 END) as NULL_IS_LATE
FROM fct_orders
"""
null_analysis_df = run_query(null_analysis_query)
if not null_analysis_df.empty:
    total = null_analysis_df['TOTAL'].iloc[0]
    null_data = {
        'Column': ['PURCHASE_DATE', 'APPROVED_DATE', 'DELIVERY_DATE', 'TOTAL_PAYMENT_VALUE', 'IS_LATE_DELIVERY'],
        'Null Percentage': [
            (null_analysis_df['NULL_PURCHASE_DATE'].iloc[0] / total) * 100,
            (null_analysis_df['NULL_APPROVED_DATE'].iloc[0] / total) * 100,
            (null_analysis_df['NULL_DELIVERY_DATE'].iloc[0] / total) * 100,
            (null_analysis_df['NULL_PAYMENT'].iloc[0] / total) * 100,
            (null_analysis_df['NULL_IS_LATE'].iloc[0] / total) * 100
        ]
    }
    null_df = pd.DataFrame(null_data)
    
    fig1 = px.bar(
        null_df, 
        x='Null Percentage', 
        y='Column', 
        orientation='h',
        color='Null Percentage',
        color_continuous_scale=[ACCENT_REVENUE, ACCENT_WARNING, ACCENT_DANGER],
        labels={'Null Percentage': 'Null Rate (%)', 'Column': 'Column Name'}
    )
    apply_chart_style(fig1)
    st.plotly_chart(fig1, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- Panel 3: Order Status Distribution ---
st.subheader("Order Status Distribution")
status_query = "SELECT ORDER_STATUS, COUNT(*) as COUNT FROM fct_orders GROUP BY 1 ORDER BY 2 DESC"
status_df = run_query(status_query)
if not status_df.empty:
    fig2 = px.bar(
        status_df, 
        x='ORDER_STATUS', 
        y='COUNT',
        color_discrete_sequence=[ACCENT_PRIMARY],
        labels={'ORDER_STATUS': 'Order Status', 'COUNT': 'Number of Orders'}
    )
    apply_chart_style(fig2)
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- Panel 4: Data Quality Checks Summary ---
st.subheader("Data Quality Checks Summary")
dq_html = f"""
<div style="background-color: {SURFACE}; padding: 20px; border-radius: 8px; border: 1px solid {BORDER};">
    <table style="width: 100%; text-align: left; border-collapse: collapse;">
        <tr style="border-bottom: 1px solid {BORDER}; color: {TEXT_SECONDARY};">
            <th style="padding: 10px;">dbt Test Name</th>
            <th style="padding: 10px;">Description</th>
            <th style="padding: 10px;">Status</th>
        </tr>
        <tr style="border-bottom: 1px solid {BORDER};">
            <td style="padding: 10px; color: {TEXT_PRIMARY};">assert_delivery_date_after_purchase</td>
            <td style="padding: 10px; color: {TEXT_SECONDARY};">Ensures delivery is never before purchase</td>
            <td style="padding: 10px;"><span style="background-color: {ACCENT_REVENUE}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">CONFIGURED</span></td>
        </tr>
        <tr style="border-bottom: 1px solid {BORDER};">
            <td style="padding: 10px; color: {TEXT_PRIMARY};">assert_no_orphan_order_items</td>
            <td style="padding: 10px; color: {TEXT_SECONDARY};">All items have a valid parent order</td>
            <td style="padding: 10px;"><span style="background-color: {ACCENT_REVENUE}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">CONFIGURED</span></td>
        </tr>
        <tr style="border-bottom: 1px solid {BORDER};">
            <td style="padding: 10px; color: {TEXT_PRIMARY};">assert_payment_totals_match_order_totals</td>
            <td style="padding: 10px; color: {TEXT_SECONDARY};">Payment sums match order totals</td>
            <td style="padding: 10px;"><span style="background-color: {ACCENT_REVENUE}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">CONFIGURED</span></td>
        </tr>
        <tr>
            <td style="padding: 10px; color: {TEXT_PRIMARY};">assert_positive_order_values</td>
            <td style="padding: 10px; color: {TEXT_SECONDARY};">Non-canceled orders have positive value</td>
            <td style="padding: 10px;"><span style="background-color: {ACCENT_REVENUE}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">CONFIGURED</span></td>
        </tr>
    </table>
</div>
"""
st.markdown(dq_html, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# --- Panel 5: Pipeline Architecture ---
st.subheader("Pipeline Architecture")
pipeline_html = f"""
<div style="display: flex; justify-content: space-between; align-items: center; background-color: {SURFACE}; padding: 20px; border-radius: 8px; border: 1px solid {BORDER}; overflow-x: auto;">
    <div style="text-align: center; padding: 15px; min-width: 120px; border: 1px solid {BORDER}; border-radius: 6px; background-color: {BACKGROUND};">
        <h4 style="color: {ACCENT_PRIMARY}; margin-bottom: 5px; margin-top: 0;">Amazon S3</h4>
        <span style="color: {TEXT_SECONDARY}; font-size: 12px;">Raw Data Lake</span>
    </div>
    <div style="color: {TEXT_SECONDARY}; font-size: 24px;">➔</div>
    <div style="text-align: center; padding: 15px; min-width: 120px; border: 1px solid {BORDER}; border-radius: 6px; background-color: {BACKGROUND};">
        <h4 style="color: {ACCENT_SECONDARY}; margin-bottom: 5px; margin-top: 0;">Snowflake</h4>
        <span style="color: {TEXT_SECONDARY}; font-size: 12px;">Bronze Layer</span>
    </div>
    <div style="color: {TEXT_SECONDARY}; font-size: 24px;">➔</div>
    <div style="text-align: center; padding: 15px; min-width: 120px; border: 1px solid {BORDER}; border-radius: 6px; background-color: {BACKGROUND};">
        <h4 style="color: {ACCENT_WARNING}; margin-bottom: 5px; margin-top: 0;">dbt</h4>
        <span style="color: {TEXT_SECONDARY}; font-size: 12px;">Silver Models</span>
    </div>
    <div style="color: {TEXT_SECONDARY}; font-size: 24px;">➔</div>
    <div style="text-align: center; padding: 15px; min-width: 120px; border: 1px solid {BORDER}; border-radius: 6px; background-color: {BACKGROUND};">
        <h4 style="color: {ACCENT_REVENUE}; margin-bottom: 5px; margin-top: 0;">dbt</h4>
        <span style="color: {TEXT_SECONDARY}; font-size: 12px;">Gold Marts</span>
    </div>
    <div style="color: {TEXT_SECONDARY}; font-size: 24px;">➔</div>
    <div style="text-align: center; padding: 15px; min-width: 120px; border: 1px solid {BORDER}; border-radius: 6px; background-color: {BACKGROUND};">
        <h4 style="color: {ACCENT_DANGER}; margin-bottom: 5px; margin-top: 0;">Streamlit</h4>
        <span style="color: {TEXT_SECONDARY}; font-size: 12px;">Dashboard UI</span>
    </div>
</div>
"""
st.markdown(pipeline_html, unsafe_allow_html=True)
