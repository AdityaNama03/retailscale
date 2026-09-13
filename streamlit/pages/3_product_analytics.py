import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.express as px
import pandas as pd

from connection import run_query
from components.kpi_card import kpi_card
from components.header import page_header
from config import *

# Load CSS
css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'style.css')
with open(css_path) as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

page_header("Product Analytics", "Detailed insights into product performance, pricing, and freight")

# --- DATA FETCHING ---
@st.cache_data(ttl=3600)
def get_kpi_data():
    q_cat = "SELECT COUNT(DISTINCT PRODUCT_CATEGORY_NAME) as CAT_COUNT FROM dim_products"
    q_prod = "SELECT COUNT(DISTINCT PRODUCT_ID) as PROD_COUNT FROM fct_order_items"
    q_top_cat = """
        SELECT p.PRODUCT_CATEGORY_NAME, SUM(i.PRICE) as REVENUE
        FROM fct_order_items i
        JOIN dim_products p ON i.PRODUCT_ID = p.PRODUCT_ID
        WHERE p.PRODUCT_CATEGORY_NAME IS NOT NULL
        GROUP BY p.PRODUCT_CATEGORY_NAME
        ORDER BY REVENUE DESC
        LIMIT 1
    """
    q_avg_price = "SELECT AVG(PRICE) as AVG_P FROM fct_order_items"
    
    cats = run_query(q_cat).iloc[0]['CAT_COUNT']
    prods = run_query(q_prod).iloc[0]['PROD_COUNT']
    top_c = run_query(q_top_cat)
    top_cat_name = top_c.iloc[0]['PRODUCT_CATEGORY_NAME'] if not top_c.empty else "N/A"
    top_cat_rev = top_c.iloc[0]['REVENUE'] if not top_c.empty else 0
    avg_p = run_query(q_avg_price).iloc[0]['AVG_P']
    
    return cats, prods, top_cat_name, top_cat_rev, avg_p

@st.cache_data(ttl=3600)
def get_category_data():
    query = """
        SELECT 
            p.PRODUCT_CATEGORY_NAME as CATEGORY,
            SUM(i.PRICE) as REVENUE,
            COUNT(i.ORDER_ITEM_ID) as UNITS,
            AVG(i.PRICE) as AVG_PRICE,
            AVG(i.FREIGHT_VALUE) as AVG_FREIGHT,
            AVG(p.PRODUCT_WEIGHT_G) as AVG_WEIGHT
        FROM fct_order_items i
        JOIN dim_products p ON i.PRODUCT_ID = p.PRODUCT_ID
        WHERE p.PRODUCT_CATEGORY_NAME IS NOT NULL
        GROUP BY p.PRODUCT_CATEGORY_NAME
        ORDER BY REVENUE DESC
    """
    return run_query(query)

@st.cache_data(ttl=3600)
def get_box_data(top_categories):
    cats_str = "', '".join(top_categories)
    query = f"""
        SELECT 
            p.PRODUCT_CATEGORY_NAME as CATEGORY,
            i.PRICE
        FROM fct_order_items i
        JOIN dim_products p ON i.PRODUCT_ID = p.PRODUCT_ID
        WHERE p.PRODUCT_CATEGORY_NAME IN ('{cats_str}')
    """
    return run_query(query)

# --- LOAD DATA ---
cat_count, prod_count, top_category, top_cat_revenue, avg_price = get_kpi_data()
df_cats = get_category_data()
# Top 20 categories by revenue
df_top20_rev = df_cats.head(20).copy()
# Top 15 categories by units
df_top15_units = df_cats.sort_values('UNITS', ascending=False).head(15).copy()
# Top 15 categories by avg price
df_top15_price = df_cats.sort_values('AVG_PRICE', ascending=False).head(15).copy()

# Box plot data (top 10 by volume)
top10_vol = df_cats.sort_values('UNITS', ascending=False).head(10)['CATEGORY'].tolist()
df_box = get_box_data(top10_vol) if top10_vol else pd.DataFrame()

# --- KPI ROW ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi_card("Active Categories", format_number(cat_count))
with col2:
    kpi_card("Products Sold", format_number(prod_count))
with col3:
    kpi_card("Top Category", top_category, format_currency(top_cat_revenue))
with col4:
    kpi_card("Avg Item Price", format_currency(avg_price))

st.markdown("<br>", unsafe_allow_html=True)

# --- TREEMAP ---
st.markdown("### Category Revenue Treemap")
fig_tree = px.treemap(
    df_top20_rev,
    path=[px.Constant("All Categories"), 'CATEGORY'],
    values='REVENUE',
    color='UNITS',
    color_continuous_scale='Blues'
)
apply_chart_style(fig_tree)
fig_tree.update_layout(height=550)
st.plotly_chart(fig_tree, use_container_width=True)

# --- 2 CHARTS ROW ---
c1, c2 = st.columns(2)

with c1:
    st.markdown("### Top 15 Categories by Units Sold")
    fig_units = px.bar(
        df_top15_units.sort_values('UNITS', ascending=True), 
        x='UNITS', 
        y='CATEGORY', 
        orientation='h'
    )
    fig_units.update_traces(marker_color=ACCENT_PRIMARY)
    apply_chart_style(fig_units)
    st.plotly_chart(fig_units, use_container_width=True)

with c2:
    st.markdown("### Top 15 Categories by Avg Price")
    fig_price = px.bar(
        df_top15_price.sort_values('AVG_PRICE', ascending=True), 
        x='AVG_PRICE', 
        y='CATEGORY', 
        orientation='h'
    )
    fig_price.update_traces(marker_color=ACCENT_SECONDARY)
    apply_chart_style(fig_price)
    st.plotly_chart(fig_price, use_container_width=True)

# --- 2 CHARTS ROW ---
c3, c4 = st.columns(2)

with c3:
    st.markdown("### Price vs Freight Scatter")
    fig_scatter = px.scatter(
        df_cats,
        x='AVG_PRICE',
        y='AVG_FREIGHT',
        size='UNITS',
        hover_name='CATEGORY',
        color_discrete_sequence=[ACCENT_PRIMARY]
    )
    apply_chart_style(fig_scatter)
    st.plotly_chart(fig_scatter, use_container_width=True)

with c4:
    st.markdown("### Price Distribution (Top 10 Categories)")
    if not df_box.empty:
        fig_box = px.box(
            df_box,
            x='PRICE',
            y='CATEGORY',
            color_discrete_sequence=[ACCENT_SECONDARY],
            orientation='h'
        )
        apply_chart_style(fig_box)
        st.plotly_chart(fig_box, use_container_width=True)
    else:
        st.info("No data available for price distribution.")

# --- TABLE ---
st.markdown("### Full Category Breakdown")
st.dataframe(
    df_cats,
    column_config={
        "CATEGORY": "Category",
        "REVENUE": st.column_config.NumberColumn("Revenue", format="R$ %.2f"),
        "UNITS": st.column_config.NumberColumn("Units", format="%d"),
        "AVG_PRICE": st.column_config.NumberColumn("Avg Price", format="R$ %.2f"),
        "AVG_FREIGHT": st.column_config.NumberColumn("Avg Freight", format="R$ %.2f"),
        "AVG_WEIGHT": st.column_config.NumberColumn("Avg Weight (g)", format="%.0f")
    },
    use_container_width=True,
    hide_index=True
)
