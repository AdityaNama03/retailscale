import streamlit as st

def kpi_card(label, value, delta=None, delta_color='#3FB950', icon=None):
    icon_html = f"<span style='font-size: 1.5em; margin-right: 8px;'>{icon}</span>" if icon else ""
    
    delta_html = ""
    if delta:
        indicator = "▲" if str(delta).startswith('+') else "▼" if str(delta).startswith('-') else ""
        delta_html = f"""
        <div style="color: {delta_color}; font-size: 0.85em; margin-top: 4px; display: flex; align-items: center;">
            <span style="margin-right: 4px;">{indicator}</span> {delta}
        </div>
        """
        
    html = f"""
    <div class="kpi-card" style="
        background-color: #1B1F2A;
        border: 1px solid #2D3340;
        border-radius: 8px;
        padding: 20px;
        position: relative;
        overflow: hidden;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    ">
        <div style="
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #58A6FF, #BC8CFF);
        "></div>
        <div style="color: #8B949E; font-size: 0.9em; font-weight: 500; margin-bottom: 8px; display: flex; align-items: center;">
            {icon_html}{label}
        </div>
        <div style="color: #FAFAFA; font-size: 1.8em; font-weight: 700;">
            {value}
        </div>
        {delta_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)