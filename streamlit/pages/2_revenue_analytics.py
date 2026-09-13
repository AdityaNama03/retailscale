import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from connection import run_query
from components.kpi_card import kpi_card
from components.header import page_header
from config import *

css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'style.css')
with open(css_path) as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

page_header("Revenue Analytics", "Deep-dive into revenue and payment metrics")

query_kpi = """
WITH items AS (
    SELECT SUM(PRICE) AS GMV, SUM(FREIGHT_VALUE) AS FREIGHT
    FROM fct_order_items
),
payments AS (
    SELECT AVG(PAYMENT_INSTALLMENTS) AS AVG_INSTALLMENTS
    FROM fct_payments
),
orders AS (
    SELECT SUM(TOTAL_PAYMENT_VALUE) AS REVENUE, COUNT(DISTINCT CUSTOMER_ID) AS CUSTOMERS
    FROM fct_orders
    WHERE ORDER_STATUS != 'canceled'
)
SELECT i.GMV, i.FREIGHT, p.AVG_INSTALLMENTS,
       o.REVENUE / NULLIF(o.CUSTOMERS, 0) AS REV_PER_CUST
FROM items i, payments p, orders o
"""
df_kpi = run_query(query_kpi)

cols = st.columns(4)
with cols[0]:
    val = df_kpi['GMV'].iloc[0] if not df_kpi.empty else None
    kpi_card("GMV", format_currency(val) if pd.notnull(val) else "R$ 0")
with cols[1]:
    val = df_kpi['FREIGHT'].iloc[0] if not df_kpi.empty else None
    kpi_card("Total Freight Revenue", format_currency(val) if pd.notnull(val) else "R$ 0")
with cols[2]:
    val = df_kpi['AVG_INSTALLMENTS'].iloc[0] if not df_kpi.empty else None
    kpi_card("Avg Installments", f"{val:.1f}" if pd.notnull(val) else "0")
with cols[3]:
    val = df_kpi['REV_PER_CUST'].iloc[0] if not df_kpi.empty else None
    kpi_card("Revenue per Customer", format_currency(val) if pd.notnull(val) else "R$ 0")

st.markdown('---')

st.subheader("GMV vs AOV Trend")
query_gmv_aov = """
WITH monthly_gmv AS (
    SELECT DATE_TRUNC('month', ORDER_PURCHASE_DATE) AS MONTH, SUM(PRICE) AS GMV
    FROM fct_order_items
    GROUP BY MONTH
),
monthly_aov AS (
    SELECT DATE_TRUNC('month', PURCHASE_DATE) AS MONTH, 
           AVG(TOTAL_PAYMENT_VALUE) AS AOV,
           COUNT(ORDER_ID) as ORDERS
    FROM fct_orders
    WHERE ORDER_STATUS != 'canceled'
    GROUP BY MONTH
)
SELECT g.MONTH, g.GMV, a.AOV, a.ORDERS,
       LAG(g.GMV) OVER (ORDER BY g.MONTH) AS PREV_GMV
FROM monthly_gmv g
JOIN monthly_aov a ON g.MONTH = a.MONTH
ORDER BY g.MONTH
"""
df_gmv_aov = run_query(query_gmv_aov)

if not df_gmv_aov.empty:
    df_gmv_aov['MONTH'] = pd.to_datetime(df_gmv_aov['MONTH'])

    fig1 = make_subplots(specs=[[{"secondary_y": True}]])
    fig1.add_trace(go.Bar(x=df_gmv_aov['MONTH'], y=df_gmv_aov['GMV'], name="GMV", marker_color=ACCENT_PRIMARY), secondary_y=False)
    fig1.add_trace(go.Scatter(x=df_gmv_aov['MONTH'], y=df_gmv_aov['AOV'], name="AOV", line=dict(color=ACCENT_REVENUE, width=3)), secondary_y=True)
    apply_chart_style(fig1)
    fig1.update_layout(height=500)
    fig1.update_yaxes(title_text="GMV", secondary_y=False)
    fig1.update_yaxes(title_text="AOV", secondary_y=True)
    st.plotly_chart(fig1, use_container_width=True)

st.markdown('---')
col1, col2 = st.columns(2)

with col1:
    st.subheader("Revenue by Payment Type Over Time")
    query_pay_time = """
    SELECT DATE_TRUNC('month', ORDER_PURCHASE_DATE) AS MONTH,
           PAYMENT_TYPE, SUM(PAYMENT_VALUE) AS REV
    FROM fct_payments
    GROUP BY MONTH, PAYMENT_TYPE
    ORDER BY MONTH
    """
    df_pay_time = run_query(query_pay_time)
    if not df_pay_time.empty:
        df_pay_time['MONTH'] = pd.to_datetime(df_pay_time['MONTH'])
        fig2 = px.area(df_pay_time, x='MONTH', y='REV', color='PAYMENT_TYPE')
        apply_chart_style(fig2)
        st.plotly_chart(fig2, use_container_width=True)

with col2:
    st.subheader("Installment Distribution")
    query_inst = """
    SELECT PAYMENT_INSTALLMENTS, COUNT(*) AS INSTALLMENT_COUNT
    FROM fct_payments
    GROUP BY PAYMENT_INSTALLMENTS
    ORDER BY PAYMENT_INSTALLMENTS
    """
    df_inst = run_query(query_inst)
    if not df_inst.empty:
        df_inst['PAYMENT_INSTALLMENTS'] = df_inst['PAYMENT_INSTALLMENTS'].astype(str)
        fig3 = px.bar(df_inst, x='PAYMENT_INSTALLMENTS', y='INSTALLMENT_COUNT', color_discrete_sequence=[ACCENT_SECONDARY])
        apply_chart_style(fig3)
        st.plotly_chart(fig3, use_container_width=True)

st.markdown('---')

st.subheader("Revenue Heatmap")
query_heat = """
SELECT d.DAY_OF_WEEK, d.MONTH, SUM(o.TOTAL_PAYMENT_VALUE) AS REVENUE
FROM fct_orders o
JOIN dim_dates d ON DATE_TRUNC('day', o.PURCHASE_DATE) = d.DATE_DAY
WHERE o.ORDER_STATUS != 'canceled'
GROUP BY d.DAY_OF_WEEK, d.MONTH
ORDER BY d.DAY_OF_WEEK, d.MONTH
"""
df_heat = run_query(query_heat)
if not df_heat.empty:
    pivot_heat = df_heat.pivot(index='DAY_OF_WEEK', columns='MONTH', values='REVENUE')
    fig4 = px.imshow(pivot_heat, labels=dict(x="Month", y="Day of Week", color="Revenue"), color_continuous_scale="Blues")
    apply_chart_style(fig4)
    st.plotly_chart(fig4, use_container_width=True)

st.markdown('---')

st.subheader("Monthly Revenue Table")
if not df_gmv_aov.empty:
    df_gmv_aov['MoM Growth %'] = ((df_gmv_aov['GMV'] - df_gmv_aov['PREV_GMV']) / df_gmv_aov['PREV_GMV'] * 100).round(1)
    df_table = df_gmv_aov[['MONTH', 'GMV', 'ORDERS', 'AOV', 'MoM Growth %']].copy()
    df_table.columns = ['Month', 'Revenue', 'Orders', 'AOV', 'MoM Growth %']
    df_table['Month'] = df_table['Month'].dt.strftime('%Y-%m')

    st.dataframe(
        df_table,
        column_config={
            "Month": st.column_config.TextColumn("Month"),
            "Revenue": st.column_config.NumberColumn("Revenue", format="R$ %.2f"),
            "Orders": st.column_config.NumberColumn("Orders", format="%d"),
            "AOV": st.column_config.NumberColumn("AOV", format="R$ %.2f"),
            "MoM Growth %": st.column_config.NumberColumn("MoM Growth %", format="%.1f%%")
        },
        use_container_width=True,
        hide_index=True
    )
