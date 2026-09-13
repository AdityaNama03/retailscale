import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

from connection import run_query
from components.kpi_card import kpi_card
from components.header import page_header
from config import *

# Load CSS
css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'style.css')
with open(css_path) as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

page_header("Customer Analytics", "Insights into customer behavior, geography, and value")

# --- DATA FETCHING ---
@st.cache_data(ttl=3600)
def get_kpi_data():
    q_unique = "SELECT COUNT(DISTINCT CUSTOMER_UNIQUE_ID) as C_COUNT FROM dim_customers WHERE IS_CURRENT = true"
    q_orders = "SELECT COUNT(ORDER_ID) as O_COUNT FROM fct_orders"
    q_top_state = """
        SELECT c.CUSTOMER_STATE, COUNT(o.ORDER_ID) as O_COUNT
        FROM fct_orders o
        JOIN dim_customers c ON o.CUSTOMER_ID = c.CUSTOMER_ID
        WHERE c.IS_CURRENT = true
        GROUP BY c.CUSTOMER_STATE
        ORDER BY O_COUNT DESC
        LIMIT 1
    """
    q_avg_val = """
        SELECT AVG(CUSTOMER_SPEND) as AVG_CUST_VAL
        FROM (
            SELECT c.CUSTOMER_UNIQUE_ID, SUM(o.TOTAL_PAYMENT_VALUE) as CUSTOMER_SPEND
            FROM fct_orders o
            JOIN dim_customers c ON o.CUSTOMER_ID = c.CUSTOMER_ID
            WHERE c.IS_CURRENT = true
            GROUP BY c.CUSTOMER_UNIQUE_ID
        )
    """
    
    c_count = run_query(q_unique).iloc[0]['C_COUNT']
    o_count = run_query(q_orders).iloc[0]['O_COUNT']
    avg_orders = o_count / c_count if c_count > 0 else 0
    
    top_st_df = run_query(q_top_state)
    top_state = top_st_df.iloc[0]['CUSTOMER_STATE'] if not top_st_df.empty else "N/A"
    
    avg_val = run_query(q_avg_val).iloc[0]['AVG_CUST_VAL']
    
    return c_count, avg_orders, top_state, avg_val

@st.cache_data(ttl=3600)
def get_state_data():
    query = """
        SELECT 
            c.CUSTOMER_STATE as STATE,
            COUNT(DISTINCT c.CUSTOMER_UNIQUE_ID) as CUSTOMERS,
            COUNT(o.ORDER_ID) as ORDERS,
            SUM(o.TOTAL_PAYMENT_VALUE) as REVENUE
        FROM fct_orders o
        JOIN dim_customers c ON o.CUSTOMER_ID = c.CUSTOMER_ID
        WHERE c.IS_CURRENT = true
        GROUP BY c.CUSTOMER_STATE
        ORDER BY REVENUE DESC
    """
    df = run_query(query)
    df['AOV'] = np.where(df['ORDERS'] > 0, df['REVENUE'] / df['ORDERS'], 0)
    return df

@st.cache_data(ttl=3600)
def get_city_data():
    query = """
        SELECT 
            c.CUSTOMER_CITY as CITY,
            SUM(o.TOTAL_PAYMENT_VALUE) as REVENUE
        FROM fct_orders o
        JOIN dim_customers c ON o.CUSTOMER_ID = c.CUSTOMER_ID
        WHERE c.IS_CURRENT = true
        GROUP BY c.CUSTOMER_CITY
        ORDER BY REVENUE DESC
        LIMIT 10
    """
    return run_query(query)

@st.cache_data(ttl=3600)
def get_freq_data():
    query = """
        WITH customer_orders AS (
            SELECT c.CUSTOMER_UNIQUE_ID, COUNT(o.ORDER_ID) as ORDER_COUNT
            FROM fct_orders o
            JOIN dim_customers c ON o.CUSTOMER_ID = c.CUSTOMER_ID
            WHERE c.IS_CURRENT = true
            GROUP BY c.CUSTOMER_UNIQUE_ID
        )
        SELECT 
            CASE 
                WHEN ORDER_COUNT = 1 THEN 'Single Order'
                WHEN ORDER_COUNT = 2 THEN '2 Orders'
                ELSE '3+ Orders'
            END AS ORDER_FREQUENCY,
            COUNT(CUSTOMER_UNIQUE_ID) as CUSTOMER_COUNT
        FROM customer_orders
        GROUP BY ORDER_FREQUENCY
    """
    return run_query(query)

@st.cache_data(ttl=3600)
def get_hist_data():
    query = "SELECT TOTAL_PAYMENT_VALUE FROM fct_orders WHERE TOTAL_PAYMENT_VALUE < 2000"
    return run_query(query)

# --- LOAD DATA ---
cust_count, avg_orders, top_state, avg_cust_val = get_kpi_data()
df_states = get_state_data()
df_cities = get_city_data()
df_freq = get_freq_data()
df_hist = get_hist_data()

# --- KPI ROW ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi_card("Unique Customers", format_number(cust_count))
with col2:
    kpi_card("Avg Orders per Customer", format_number(avg_orders))
with col3:
    kpi_card("Top State", top_state)
with col4:
    kpi_card("Avg Customer Value", format_currency(avg_cust_val))

st.markdown("<br>", unsafe_allow_html=True)

# --- MAP / TOP STATES ---
st.markdown("### Top 15 States by Customers")
df_states_top = df_states.sort_values('CUSTOMERS', ascending=False).head(15)
fig_map = px.bar(
    df_states_top.sort_values('CUSTOMERS', ascending=True),
    x='CUSTOMERS',
    y='STATE',
    orientation='h'
)
fig_map.update_traces(marker_color=ACCENT_PRIMARY)
apply_chart_style(fig_map)
st.plotly_chart(fig_map, use_container_width=True)

# --- 2 CHARTS ROW ---
c1, c2 = st.columns(2)

with c1:
    st.markdown("### Top 10 States by Customers")
    fig_st = px.bar(
        df_states.sort_values('CUSTOMERS', ascending=False).head(10).sort_values('CUSTOMERS', ascending=True), 
        x='CUSTOMERS', 
        y='STATE', 
        orientation='h'
    )
    fig_st.update_traces(marker_color=ACCENT_PRIMARY)
    apply_chart_style(fig_st)
    st.plotly_chart(fig_st, use_container_width=True)

with c2:
    st.markdown("### Top 10 Cities by Revenue")
    fig_city = px.bar(
        df_cities.sort_values('REVENUE', ascending=True), 
        x='REVENUE', 
        y='CITY', 
        orientation='h'
    )
    fig_city.update_traces(marker_color=ACCENT_REVENUE)
    apply_chart_style(fig_city)
    st.plotly_chart(fig_city, use_container_width=True)

# --- 2 CHARTS ROW ---
c3, c4 = st.columns(2)

with c3:
    st.markdown("### Customer Order Frequency")
    fig_freq = px.pie(
        df_freq, 
        values='CUSTOMER_COUNT', 
        names='ORDER_FREQUENCY', 
        hole=0.4,
        color_discrete_sequence=[ACCENT_PRIMARY, ACCENT_SECONDARY, ACCENT_REVENUE]
    )
    apply_chart_style(fig_freq)
    st.plotly_chart(fig_freq, use_container_width=True)

with c4:
    st.markdown("### Order Value Distribution")
    if not df_hist.empty:
        fig_hist = px.histogram(
            df_hist, 
            x='TOTAL_PAYMENT_VALUE', 
            nbins=30,
            color_discrete_sequence=[ACCENT_PRIMARY]
        )
        apply_chart_style(fig_hist)
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.info("No data available for distribution.")

# --- TABLE ---
st.markdown("### State Performance Table")
st.dataframe(
    df_states,
    column_config={
        "STATE": "State",
        "CUSTOMERS": st.column_config.NumberColumn("Customers", format="%d"),
        "ORDERS": st.column_config.NumberColumn("Orders", format="%d"),
        "REVENUE": st.column_config.NumberColumn("Revenue", format="R$ %.2f"),
        "AOV": st.column_config.NumberColumn("Avg Order Value", format="R$ %.2f")
    },
    use_container_width=True,
    hide_index=True
)
