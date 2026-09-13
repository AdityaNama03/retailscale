import streamlit as st
import datetime

def render_sidebar_filters(run_query_fn):
    st.sidebar.header("Global Filters")
    
    # Date Range
    today = datetime.date.today()
    default_start = today - datetime.timedelta(days=2*365)
    date_range = st.sidebar.date_input("Date Range", [default_start, today])
    
    # States
    states_df = run_query_fn("SELECT DISTINCT CUSTOMER_STATE FROM RETAILSCALE_DEV.GOLD.dim_customers ORDER BY CUSTOMER_STATE")
    states_list = ['All'] + states_df['CUSTOMER_STATE'].tolist() if not states_df.empty else ['All']
    states = st.sidebar.multiselect("State", states_list, default=['All'])
    
    # Statuses
    statuses_df = run_query_fn("SELECT DISTINCT ORDER_STATUS FROM RETAILSCALE_DEV.GOLD.fct_orders ORDER BY ORDER_STATUS")
    statuses_list = ['All'] + statuses_df['ORDER_STATUS'].tolist() if not statuses_df.empty else ['All']
    statuses = st.sidebar.multiselect("Order Status", statuses_list, default=['All'])
    
    # Categories
    categories_df = run_query_fn(\"\"\"
        SELECT PRODUCT_CATEGORY_NAME, COUNT(*) as cnt 
        FROM RETAILSCALE_DEV.GOLD.dim_products 
        WHERE PRODUCT_CATEGORY_NAME IS NOT NULL
        GROUP BY PRODUCT_CATEGORY_NAME 
        ORDER BY cnt DESC 
        LIMIT 20
    \"\"\")
    categories_list = ['All'] + categories_df['PRODUCT_CATEGORY_NAME'].tolist() if not categories_df.empty else ['All']
    categories = st.sidebar.multiselect("Top Categories", categories_list, default=['All'])
    
    return {
        'date_range': date_range,
        'states': states,
        'statuses': statuses,
        'categories': categories
    }

def build_where_clause(filters, date_col='PURCHASE_DATE', state_col=None, status_col=None, category_col=None):
    conditions = []
    
    if filters.get('date_range') and len(filters['date_range']) == 2:
        start_date, end_date = filters['date_range']
        if date_col:
            conditions.append(f"{date_col} >= '{start_date}' AND {date_col} <= '{end_date}'")
            
    if filters.get('states') and 'All' not in filters['states'] and state_col:
        states_str = "', '".join(filters['states'])
        conditions.append(f"{state_col} IN ('{states_str}')")
        
    if filters.get('statuses') and 'All' not in filters['statuses'] and status_col:
        statuses_str = "', '".join(filters['statuses'])
        conditions.append(f"{status_col} IN ('{statuses_str}')")
        
    if filters.get('categories') and 'All' not in filters['categories'] and category_col:
        cats_str = "', '".join(filters['categories'])
        conditions.append(f"{category_col} IN ('{cats_str}')")
        
    return " AND ".join(conditions) if conditions else "1=1"
