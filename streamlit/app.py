import streamlit as st
import os

st.set_page_config(
    page_title='RetailScale Analytics', 
    page_icon='📊', 
    layout='wide'
)

# Load CSS
css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Main Landing Page Content
st.markdown("""
<div style="text-align: center; margin-top: 40px; margin-bottom: 60px; font-family: 'Inter', sans-serif;">
    <h1 style="color: #FAFAFA; font-size: 3.5em; font-weight: 800; margin-bottom: 8px;">RetailScale Analytics</h1>
    <h3 style="color: #58A6FF; font-weight: 500; margin-top: 0; margin-bottom: 24px;">Enterprise Sales & Operations Intelligence</h3>
    <p style="color: #8B949E; font-size: 1.2em; max-width: 800px; margin: 0 auto;">
        Welcome to the RetailScale command center. Monitor core business metrics, dive into product and customer analytics, 
        and optimize delivery performance across the Olist e-commerce ecosystem.
    </p>
</div>
""", unsafe_allow_html=True)

# Grid of Navigation Cards
cols1 = st.columns(3)
cols2 = st.columns(3)

cards = [
    {"col": cols1[0], "icon": "📈", "title": "Executive Overview", "desc": "High-level metrics and C-suite KPI dashboard."},
    {"col": cols1[1], "icon": "💰", "title": "Revenue Analytics", "desc": "Sales performance, revenue trends, and payment analysis."},
    {"col": cols1[2], "icon": "📦", "title": "Product Analytics", "desc": "Category performance, product volume, and catalogue insights."},
    {"col": cols2[0], "icon": "👥", "title": "Customer Analytics", "desc": "Geographic distribution, retention, and customer lifetime value."},
    {"col": cols2[1], "icon": "🚚", "title": "Delivery & Logistics", "desc": "Shipping times, freight costs, and late delivery tracking."},
    {"col": cols2[2], "icon": "🏪", "title": "Seller Performance", "desc": "Seller distribution, revenue by seller, and fulfillment metrics."}
]

for card in cards:
    with card["col"]:
        st.markdown(f"""
        <div class="kpi-card" style="margin-bottom: 24px; cursor: pointer;">
            <div style="position: absolute; top: 0; left: 0; right: 0; height: 4px; background: linear-gradient(90deg, #58A6FF, #BC8CFF);"></div>
            <div style="font-size: 2.5em; margin-bottom: 12px;">{card["icon"]}</div>
            <h3 style="color: #FAFAFA; margin: 0 0 8px 0; font-size: 1.3em;">{card["title"]}</h3>
            <p style="color: #8B949E; margin: 0; font-size: 0.9em; line-height: 1.4;">{card["desc"]}</p>
        </div>
        """, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("""
    <div style="padding: 16px 0;">
        <h2 style="color: #FAFAFA; font-weight: 700; margin: 0;">RetailScale</h2>
        <div style="color: #58A6FF; font-size: 0.9em; font-weight: 500;">ANALYTICS PLATFORM</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()
    st.info("👆 Navigate using the sidebar pages above")
    
    st.markdown("<div style='margin-top: 100px;'></div>", unsafe_allow_html=True)
    st.divider()
    st.markdown("""
    <div style="color: #8B949E; font-size: 0.8em; text-align: center;">
        Powered by Snowflake · dbt · Airflow · Streamlit
    </div>
    """, unsafe_allow_html=True)