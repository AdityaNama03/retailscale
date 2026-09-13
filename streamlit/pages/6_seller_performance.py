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

page_header("Seller Performance", "Evaluate top sellers, geographical distribution, and revenue generation.")

# --- KPIs ---
kpi1_query = "SELECT COUNT(DISTINCT SELLER_ID) as ACTIVE_SELLERS FROM fct_order_items"
kpi2_query = "SELECT SELLER_STATE, COUNT(DISTINCT SELLER_ID) FROM dim_sellers GROUP BY 1 ORDER BY 2 DESC LIMIT 1"
kpi3_query = "SELECT SUM(PRICE) / NULLIF(COUNT(DISTINCT SELLER_ID), 0) as AVG_REV FROM fct_order_items"
kpi4_query = "SELECT COUNT(*) / NULLIF(COUNT(DISTINCT SELLER_ID), 0) as AVG_ITEMS FROM fct_order_items"

kpi1_df = run_query(kpi1_query)
kpi2_df = run_query(kpi2_query)
kpi3_df = run_query(kpi3_query)
kpi4_df = run_query(kpi4_query)

col1, col2, col3, col4 = st.columns(4)
with col1:
    val = kpi1_df['ACTIVE_SELLERS'].iloc[0] if not kpi1_df.empty else 0
    kpi_card("Active Sellers", format_number(val), icon="👥")
with col2:
    val = kpi2_df['SELLER_STATE'].iloc[0] if not kpi2_df.empty else "N/A"
    kpi_card("Top Seller State", val, icon="📍")
with col3:
    val = kpi3_df['AVG_REV'].iloc[0] if not kpi3_df.empty else 0
    kpi_card("Avg Revenue / Seller", format_currency(val), icon="💰")
with col4:
    val = kpi4_df['AVG_ITEMS'].iloc[0] if not kpi4_df.empty else 0
    kpi_card("Avg Items / Seller", format_number(val), icon="📦")

st.markdown("<br>", unsafe_allow_html=True)

# --- Full-Width Chart: Seller Distribution by State ---
st.subheader("Seller Distribution by State")
state_dist_query = """
SELECT SELLER_STATE, COUNT(DISTINCT SELLER_ID) as SELLER_COUNT
FROM dim_sellers
GROUP BY 1
ORDER BY 2 DESC
LIMIT 15
"""
state_dist_df = run_query(state_dist_query)
if not state_dist_df.empty:
    fig1 = px.bar(
        state_dist_df, 
        x='SELLER_COUNT', 
        y='SELLER_STATE', 
        orientation='h',
        color_discrete_sequence=[ACCENT_PRIMARY],
        labels={'SELLER_COUNT': 'Number of Sellers', 'SELLER_STATE': 'State'}
    )
    fig1.update_layout(yaxis={'categoryorder': 'total ascending'})
    apply_chart_style(fig1)
    st.plotly_chart(fig1, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- 2-Column Charts (Top Sellers) ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Top 15 Sellers by Revenue")
    top_rev_query = """
    SELECT SELLER_ID, SUM(PRICE) as TOTAL_REVENUE
    FROM fct_order_items
    GROUP BY 1
    ORDER BY 2 DESC
    LIMIT 15
    """
    top_rev_df = run_query(top_rev_query)
    if not top_rev_df.empty:
        top_rev_df['SELLER_ID_SHORT'] = top_rev_df['SELLER_ID'].astype(str).str[:8]
        fig2 = px.bar(
            top_rev_df, 
            x='TOTAL_REVENUE', 
            y='SELLER_ID_SHORT', 
            orientation='h',
            color_discrete_sequence=[ACCENT_REVENUE],
            labels={'TOTAL_REVENUE': 'Revenue (R$)', 'SELLER_ID_SHORT': 'Seller ID'}
        )
        fig2.update_layout(yaxis={'categoryorder': 'total ascending'})
        apply_chart_style(fig2)
        st.plotly_chart(fig2, use_container_width=True)

with col_right:
    st.subheader("Top 15 Sellers by Order Count")
    top_orders_query = """
    SELECT SELLER_ID, COUNT(DISTINCT ORDER_ID) as ORDER_COUNT
    FROM fct_order_items
    GROUP BY 1
    ORDER BY 2 DESC
    LIMIT 15
    """
    top_orders_df = run_query(top_orders_query)
    if not top_orders_df.empty:
        top_orders_df['SELLER_ID_SHORT'] = top_orders_df['SELLER_ID'].astype(str).str[:8]
        fig3 = px.bar(
            top_orders_df, 
            x='ORDER_COUNT', 
            y='SELLER_ID_SHORT', 
            orientation='h',
            color_discrete_sequence=[ACCENT_PRIMARY],
            labels={'ORDER_COUNT': 'Orders', 'SELLER_ID_SHORT': 'Seller ID'}
        )
        fig3.update_layout(yaxis={'categoryorder': 'total ascending'})
        apply_chart_style(fig3)
        st.plotly_chart(fig3, use_container_width=True)

# --- 2-Column Charts (Distribution & Freight) ---
col_left2, col_right2 = st.columns(2)

with col_left2:
    st.subheader("Revenue Distribution per Seller")
    rev_dist_query = """
    SELECT SELLER_ID, SUM(PRICE) as TOTAL_REVENUE
    FROM fct_order_items
    GROUP BY 1
    """
    rev_dist_df = run_query(rev_dist_query)
    if not rev_dist_df.empty:
        fig4 = px.histogram(
            rev_dist_df, 
            x='TOTAL_REVENUE',
            nbins=30,
            color_discrete_sequence=[ACCENT_SECONDARY],
            labels={'TOTAL_REVENUE': 'Revenue (R$)'}
        )
        fig4.update_layout(yaxis_title="Count of Sellers")
        apply_chart_style(fig4)
        st.plotly_chart(fig4, use_container_width=True)

with col_right2:
    st.subheader("Avg Freight by Seller State")
    freight_query = """
    SELECT s.SELLER_STATE, AVG(oi.FREIGHT_VALUE) as AVG_FREIGHT
    FROM fct_order_items oi
    JOIN dim_sellers s ON oi.SELLER_ID = s.SELLER_ID
    GROUP BY 1
    ORDER BY 2 DESC
    LIMIT 15
    """
    freight_df = run_query(freight_query)
    if not freight_df.empty:
        fig5 = px.bar(
            freight_df,
            x='SELLER_STATE',
            y='AVG_FREIGHT',
            color_discrete_sequence=[ACCENT_WARNING],
            labels={'SELLER_STATE': 'State', 'AVG_FREIGHT': 'Avg Freight (R$)'}
        )
        fig5.update_layout(xaxis={'categoryorder': 'total descending'})
        apply_chart_style(fig5)
        st.plotly_chart(fig5, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- Seller Directory Table ---
st.subheader("Seller Directory Table")
dir_query = """
SELECT 
    LEFT(s.SELLER_ID, 12) as "Seller ID",
    s.SELLER_CITY as "City",
    s.SELLER_STATE as "State",
    SUM(oi.PRICE) as "Revenue",
    COUNT(DISTINCT oi.ORDER_ID) as "Orders",
    AVG(oi.PRICE) as "Avg Item Price"
FROM dim_sellers s
LEFT JOIN fct_order_items oi ON s.SELLER_ID = oi.SELLER_ID
GROUP BY 1, 2, 3
ORDER BY "Revenue" DESC NULLS LAST
LIMIT 100
"""
dir_df = run_query(dir_query)
if not dir_df.empty:
    st.dataframe(dir_df, use_container_width=True)
