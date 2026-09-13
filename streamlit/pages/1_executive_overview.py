import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from connection import run_query
from components.kpi_card import kpi_card
from components.header import page_header
from config import *

# Load CSS
css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'style.css')
with open(css_path) as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

page_header("Executive Overview", "High-level summary of business performance")

# KPIs
query_kpi = """
WITH rev_orders AS (
    SELECT SUM(TOTAL_PAYMENT_VALUE) AS TOTAL_REVENUE, 
           COUNT(ORDER_ID) AS TOTAL_ORDERS
    FROM fct_orders 
    WHERE ORDER_STATUS != 'canceled'
),
delivery AS (
    SELECT SUM(CASE WHEN IS_LATE = false THEN 1 ELSE 0 END) AS ON_TIME,
           COUNT(*) AS TOTAL_DELIVERIES
    FROM fct_delivery_performance 
    WHERE ORDER_DELIVERED_DATE IS NOT NULL
)
SELECT r.TOTAL_REVENUE, r.TOTAL_ORDERS, 
       r.TOTAL_REVENUE / r.TOTAL_ORDERS AS AOV,
       (d.ON_TIME * 100.0) / NULLIF(d.TOTAL_DELIVERIES, 0) AS ON_TIME_PCT
FROM rev_orders r, delivery d
"""
df_kpi = run_query(query_kpi)

cols = st.columns(4)
with cols[0]:
    val = df_kpi['TOTAL_REVENUE'].iloc[0] if not df_kpi.empty else None
    kpi_card("Total Revenue", format_currency(val) if pd.notnull(val) else "R$ 0")
with cols[1]:
    val = df_kpi['TOTAL_ORDERS'].iloc[0] if not df_kpi.empty else None
    kpi_card("Total Orders", format_number(val) if pd.notnull(val) else "0")
with cols[2]:
    val = df_kpi['AOV'].iloc[0] if not df_kpi.empty else None
    kpi_card("Avg Order Value", format_currency(val) if pd.notnull(val) else "R$ 0")
with cols[3]:
    val = df_kpi['ON_TIME_PCT'].iloc[0] if not df_kpi.empty else None
    kpi_card("On-Time Delivery %", f"{val:.1f}%" if pd.notnull(val) else "0%")

st.markdown('---')

col1, col2 = st.columns(2)

with col1:
    st.subheader("Monthly Revenue Trend")
    query_rev = """
    SELECT DATE_TRUNC('month', PURCHASE_DATE) AS MONTH, 
           SUM(TOTAL_PAYMENT_VALUE) AS TOTAL_REVENUE
    FROM fct_orders
    WHERE ORDER_STATUS != 'canceled'
    GROUP BY MONTH
    ORDER BY MONTH
    """
    df_rev = run_query(query_rev)
    if not df_rev.empty:
        df_rev['MONTH'] = pd.to_datetime(df_rev['MONTH'])
        df_rev['MA_3'] = df_rev['TOTAL_REVENUE'].rolling(window=3).mean()
        
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=df_rev['MONTH'], y=df_rev['TOTAL_REVENUE'], fill='tozeroy', 
                                  name='Revenue', line=dict(color=ACCENT_PRIMARY)))
        fig1.add_trace(go.Scatter(x=df_rev['MONTH'], y=df_rev['MA_3'], 
                                  name='3M Rolling Avg', line=dict(color=ACCENT_WARNING, dash='dash')))
        apply_chart_style(fig1)
        fig1.update_layout(height=420)
        st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Order Status Distribution")
    query_status = """
    SELECT DATE_TRUNC('month', PURCHASE_DATE) AS MONTH,
           ORDER_STATUS,
           COUNT(ORDER_ID) AS ORDER_COUNT
    FROM fct_orders
    GROUP BY MONTH, ORDER_STATUS
    ORDER BY MONTH
    """
    df_status = run_query(query_status)
    if not df_status.empty:
        df_status['MONTH'] = pd.to_datetime(df_status['MONTH'])
        fig2 = px.bar(df_status, x='MONTH', y='ORDER_COUNT', color='ORDER_STATUS', 
                      title='', barmode='stack')
        apply_chart_style(fig2)
        st.plotly_chart(fig2, use_container_width=True)

st.markdown('---')

col3, col4 = st.columns(2)

with col3:
    st.subheader("Payment Method Breakdown")
    query_pay = """
    SELECT PAYMENT_TYPE, SUM(PAYMENT_VALUE) AS TOTAL_VALUE
    FROM fct_payments
    GROUP BY PAYMENT_TYPE
    """
    df_pay = run_query(query_pay)
    if not df_pay.empty:
        color_map = {'credit_card': ACCENT_PRIMARY, 'boleto': ACCENT_REVENUE, 
                     'voucher': ACCENT_WARNING, 'debit_card': ACCENT_SECONDARY}
        fig3 = px.pie(df_pay, values='TOTAL_VALUE', names='PAYMENT_TYPE', hole=0.5,
                      color='PAYMENT_TYPE', color_discrete_map=color_map)
        apply_chart_style(fig3)
        st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("Top 10 Categories by Revenue")
    query_cat = """
    SELECT p.PRODUCT_CATEGORY_NAME, SUM(i.PRICE) AS CATEGORY_REVENUE
    FROM fct_order_items i
    JOIN dim_products p ON i.PRODUCT_ID = p.PRODUCT_ID
    WHERE p.PRODUCT_CATEGORY_NAME IS NOT NULL
    GROUP BY p.PRODUCT_CATEGORY_NAME
    ORDER BY CATEGORY_REVENUE DESC
    LIMIT 10
    """
    df_cat = run_query(query_cat)
    if not df_cat.empty:
        fig4 = px.bar(df_cat, x='CATEGORY_REVENUE', y='PRODUCT_CATEGORY_NAME', orientation='h',
                      color_discrete_sequence=[ACCENT_REVENUE])
        fig4.update_layout(yaxis={'categoryorder':'total ascending'})
        apply_chart_style(fig4)
        st.plotly_chart(fig4, use_container_width=True)