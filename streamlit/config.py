try:
    import millify as _millify
    def _mill(val, precision=1):
        return _millify.millify(val, precision=precision)
except ImportError:
    def _mill(val, precision=1):
        if abs(val) >= 1_000_000:
            return f"{val / 1_000_000:.{precision}f}M"
        elif abs(val) >= 1_000:
            return f"{val / 1_000:.{precision}f}K"
        return f"{val:,.{precision}f}"

# Colors
BACKGROUND = "#0E1117"
SURFACE = "#1B1F2A"
BORDER = "#2D3340"
TEXT_PRIMARY = "#FAFAFA"
TEXT_SECONDARY = "#8B949E"
ACCENT_PRIMARY = "#58A6FF"   # Primary blue
ACCENT_REVENUE = "#3FB950"   # Green for positive
ACCENT_WARNING = "#D29922"   # Amber for warnings
ACCENT_DANGER = "#F85149"    # Red for negative
ACCENT_SECONDARY = "#BC8CFF" # Violet for secondary
PLOTLY_TEMPLATE = "plotly_dark"

CHART_COLORS = [
    ACCENT_PRIMARY, ACCENT_REVENUE, ACCENT_WARNING, ACCENT_DANGER, 
    ACCENT_SECONDARY, '#79C0FF', '#7EE787', '#FFA657'
]

CHART_LAYOUT = dict(
    template="plotly_dark",
    plot_bgcolor="#1B1F2A",
    paper_bgcolor="#1B1F2A",
    font=dict(color="#8B949E", family="Inter"),
    height=450,
    margin=dict(l=20, r=20, t=40, b=30),
    xaxis=dict(gridcolor="#2D3340", title_font_color="#8B949E", tickfont_color="#8B949E"),
    yaxis=dict(gridcolor="#2D3340", title_font_color="#8B949E", tickfont_color="#8B949E"),
    legend=dict(font_color="#8B949E"),
    hoverlabel=dict(bgcolor="#1B1F2A", font_color="#FAFAFA"),
)

def apply_chart_style(fig):
    fig.update_layout(**CHART_LAYOUT)
    return fig

def format_currency(value):
    if value is None:
        return "R$ 0"
    return f"R$ {_mill(float(value), precision=1)}"

def format_number(value):
    if value is None:
        return "0"
    return _mill(float(value), precision=1)

def format_pct(value):
    if value is None:
        return "0.0%"
    return f"{value:.1f}%"

STATE_NAMES = {
    'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas',
    'BA': 'Bahia', 'CE': 'Ceará', 'DF': 'Distrito Federal', 'ES': 'Espírito Santo',
    'GO': 'Goiás', 'MA': 'Maranhão', 'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul',
    'MG': 'Minas Gerais', 'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná',
    'PE': 'Pernambuco', 'PI': 'Piauí', 'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte',
    'RS': 'Rio Grande do Sul', 'RO': 'Rondônia', 'RR': 'Roraima', 'SC': 'Santa Catarina',
    'SP': 'São Paulo', 'SE': 'Sergipe', 'TO': 'Tocantins'
}