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

page_header("Delivery & Logistics", "Analyze delivery performance, SLA adherence, and logistics bottlenecks.")

# --- KPIs ---
kpi_query = """
SELECT 
    (SUM(CASE WHEN IS_LATE = false THEN 1 ELSE 0 END) / COUNT(*)) * 100 as ON_TIME_RATE,
    AVG(DATEDIFF('day', ORDER_PURCHASE_DATE, ORDER_DELIVERED_DATE)) as AVG_DELIVERY_DAYS,
    SUM(CASE WHEN IS_LATE = true THEN 1 ELSE 0 END) as LATE_DELIVERIES,
    MAX(DELIVERY_DELAY_DAYS) as WORST_DELAY
FROM fct_delivery_performance 
WHERE ORDER_DELIVERED_DATE IS NOT NULL
"""
kpi_df = run_query(kpi_query)

if not kpi_df.empty:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("On-Time Rate", format_pct(kpi_df['ON_TIME_RATE'].iloc[0]), icon="⏱️")
    with col2:
        kpi_card("Avg Delivery Days", f"{kpi_df['AVG_DELIVERY_DAYS'].iloc[0]:.1f}", icon="📦")
    with col3:
        kpi_card("Late Deliveries", format_number(kpi_df['LATE_DELIVERIES'].iloc[0]), icon="⚠️")
    with col4:
        kpi_card("Worst Delay", f"{kpi_df['WORST_DELAY'].iloc[0]:.0f} days", icon="🔴")

st.markdown("<br>", unsafe_allow_html=True)

# --- Full-Width Chart: Monthly On-Time Delivery Rate ---
st.subheader("Monthly On-Time Delivery Rate")
monthly_rate_query = """
SELECT 
    DATE_TRUNC('month', ORDER_PURCHASE_DATE) as MONTH,
    (SUM(CASE WHEN IS_LATE = false THEN 1 ELSE 0 END) / COUNT(*)) * 100 as ON_TIME_PCT
FROM fct_delivery_performance
WHERE ORDER_PURCHASE_DATE IS NOT NULL
GROUP BY 1
ORDER BY 1
"""
monthly_rate_df = run_query(monthly_rate_query)
if not monthly_rate_df.empty:
    fig1 = px.line(
        monthly_rate_df, 
        x='MONTH', 
        y='ON_TIME_PCT', 
        labels={'MONTH': 'Month', 'ON_TIME_PCT': 'On-Time %'},
        color_discrete_sequence=[ACCENT_REVENUE]
    )
    fig1.add_hline(y=95, line_dash="dash", line_color=ACCENT_DANGER, annotation_text="95% Target")
    apply_chart_style(fig1)
    st.plotly_chart(fig1, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- 2-Column Charts ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Delivery Delay Distribution")
    delay_query = """
    SELECT DELIVERY_DELAY_DAYS 
    FROM fct_delivery_performance 
    WHERE ORDER_DELIVERED_DATE IS NOT NULL
    """
    delay_df = run_query(delay_query)
    if not delay_df.empty:
        # Custom color map for delays
        delay_df['COLOR'] = delay_df['DELIVERY_DELAY_DAYS'].apply(lambda x: ACCENT_DANGER if x > 0 else ACCENT_REVENUE)
        
        fig2 = px.histogram(
            delay_df, 
            x='DELIVERY_DELAY_DAYS', 
            nbins=40, 
            range_x=[-15, 50],
            color='COLOR',
            color_discrete_map={ACCENT_DANGER: ACCENT_DANGER, ACCENT_REVENUE: ACCENT_REVENUE}
        )
        fig2.update_layout(showlegend=False, xaxis_title="Days (Negative = Early, Positive = Late)", yaxis_title="Count")
        apply_chart_style(fig2)
        st.plotly_chart(fig2, use_container_width=True)

with col_right:
    st.subheader("Late Delivery % by State")
    state_late_query = """
    SELECT 
        c.CUSTOMER_STATE,
        (SUM(CASE WHEN p.IS_LATE = true THEN 1 ELSE 0 END) / COUNT(*)) * 100 as LATE_PCT
    FROM fct_delivery_performance p
    JOIN fct_orders o ON p.ORDER_ID = o.ORDER_ID
    JOIN dim_customers c ON o.CUSTOMER_ID = c.CUSTOMER_ID
    GROUP BY 1
    ORDER BY LATE_PCT DESC
    LIMIT 15
    """
    state_late_df = run_query(state_late_query)
    if not state_late_df.empty:
        fig3 = px.bar(
            state_late_df, 
            x='LATE_PCT', 
            y='CUSTOMER_STATE', 
            orientation='h',
            labels={'LATE_PCT': 'Late Delivery %', 'CUSTOMER_STATE': 'State'},
            color_discrete_sequence=[ACCENT_WARNING]
        )
        fig3.update_layout(yaxis={'categoryorder': 'total ascending'})
        apply_chart_style(fig3)
        st.plotly_chart(fig3, use_container_width=True)

# --- Another 2-Column Row ---
col_left2, col_right2 = st.columns(2)

with col_left2:
    st.subheader("Delivery Breakdown")
    breakdown_query = """
    SELECT 
        CASE 
            WHEN ORDER_DELIVERED_DATE IS NULL THEN 'Undelivered'
            WHEN IS_LATE = true THEN 'Late'
            ELSE 'On-Time'
        END as DELIVERY_STATUS,
        COUNT(*) as CNT
    FROM fct_delivery_performance
    GROUP BY 1
    """
    breakdown_df = run_query(breakdown_query)
    if not breakdown_df.empty:
        color_map = {'On-Time': ACCENT_REVENUE, 'Late': ACCENT_DANGER, 'Undelivered': TEXT_SECONDARY}
        fig4 = px.pie(
            breakdown_df, 
            names='DELIVERY_STATUS', 
            values='CNT',
            hole=0.5,
            color='DELIVERY_STATUS',
            color_discrete_map=color_map
        )
        apply_chart_style(fig4)
        st.plotly_chart(fig4, use_container_width=True)

with col_right2:
    st.subheader("Delivery Time by Month")
    box_query = """
    SELECT 
        DATE_TRUNC('month', ORDER_PURCHASE_DATE) as MONTH,
        DATEDIFF('day', ORDER_PURCHASE_DATE, ORDER_DELIVERED_DATE) as DAYS_TO_DELIVER
    FROM fct_delivery_performance
    WHERE ORDER_DELIVERED_DATE IS NOT NULL
    """
    box_df = run_query(box_query)
    if not box_df.empty:
        # Convert month to string for proper categorical axis
        box_df['MONTH'] = pd.to_datetime(box_df['MONTH']).dt.strftime('%Y-%m')
        fig5 = px.box(
            box_df, 
            x='MONTH', 
            y='DAYS_TO_DELIVER',
            color_discrete_sequence=[ACCENT_PRIMARY]
        )
        fig5.update_layout(xaxis_title="Month", yaxis_title="Days to Deliver")
        apply_chart_style(fig5)
        st.plotly_chart(fig5, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- State SLA Table ---
st.subheader("State SLA Table")
sla_query = """
SELECT 
    c.CUSTOMER_STATE as "State",
    COUNT(*) as "Total Deliveries",
    (SUM(CASE WHEN p.IS_LATE = false THEN 1 ELSE 0 END) / COUNT(*)) * 100 as "On-Time %",
    AVG(p.DELIVERY_DELAY_DAYS) as "Avg Delay Days",
    MAX(p.DELIVERY_DELAY_DAYS) as "Worst Delay"
FROM fct_delivery_performance p
JOIN fct_orders o ON p.ORDER_ID = o.ORDER_ID
JOIN dim_customers c ON o.CUSTOMER_ID = c.CUSTOMER_ID
GROUP BY 1
ORDER BY "On-Time %" ASC
"""
sla_df = run_query(sla_query)
if not sla_df.empty:
    st.dataframe(sla_df, use_container_width=True)
