import streamlit as st

def page_header(title, subtitle=None, icon=None):
    icon_html = f"<span style='margin-right: 12px; font-size: 1.2em;'>{icon}</span>" if icon else ""
    subtitle_html = f"<div style='color: #8B949E; font-size: 1.1em; margin-top: 4px;'>{subtitle}</div>" if subtitle else ""
    
    html = f"""
    <div class="page-header" style="
        margin-bottom: 24px; 
        padding-bottom: 16px; 
        border-bottom: 1px solid #2D3340;
        font-family: 'Inter', sans-serif;
    ">
        <h1 style="color: #FAFAFA; margin: 0; display: flex; align-items: center; font-size: 2.2em; font-weight: 700;">
            {icon_html}{title}
        </h1>
        {subtitle_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
