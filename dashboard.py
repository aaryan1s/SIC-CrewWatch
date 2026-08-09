import plotly.express as px
import plotly.graph_objects as go
import json

def get_compliance_breakdown_chart_json(compliance_data):
    """
    Returns Plotly JSON representation for the equipment compliance breakdown bar chart.
    """
    categories = ['Helmet', 'Vest', 'Glove', 'Boots']
    percentages = [
        compliance_data.get('helmet_compliance_pct', 0),
        compliance_data.get('vest_compliance_pct', 0),
        compliance_data.get('glove_compliance_pct', 0),
        compliance_data.get('boot_compliance_pct', 0)
    ]
    
    # High-impact corporate palette: Green >= 85%, Amber >= 60%, Red < 60%
    colors = ['#10B981' if p >= 85 else ('#F59E0B' if p >= 60 else '#EF4444') for p in percentages]

    fig_bar = go.Figure(data=[
        go.Bar(
            x=categories,
            y=percentages,
            text=[f"<b>{p:.1f}%</b>" for p in percentages],
            textposition='auto',
            marker=dict(color=colors, cornerradius=6),
            width=0.42,
            hovertemplate="<b>%{x}</b><br>Compliance: %{y:.1f}%<extra></extra>"
        )
    ])
    
    fig_bar.add_shape(
        type="line", x0=-0.5, x1=3.5, y0=90, y1=90,
        line=dict(color="#FBBF24", width=2, dash="dash"),
        name="OSHA Target (90%)"
    )
    
    fig_bar.update_layout(
        title=dict(text="Equipment Compliance Breakdown", font=dict(color="#F8FAFC", size=15, weight="bold")),
        yaxis=dict(
            range=[0, 105],
            title=dict(text="Compliance Percentage (%)", font=dict(color="#94A3B8", size=12)),
            tickfont=dict(color="#94A3B8"),
            gridcolor="rgba(255, 255, 255, 0.07)",
            zerolinecolor="rgba(255, 255, 255, 0.1)"
        ),
        xaxis=dict(
            title=dict(text="PPE Category", font=dict(color="#94A3B8", size=12)),
            tickfont=dict(color="#F8FAFC", size=13, weight="bold"),
            gridcolor="rgba(255, 255, 255, 0.07)"
        ),
        height=320,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", color="#F8FAFC")
    )
    return fig_bar.to_json()

def get_worker_ratio_chart_json(compliance_data):
    """
    Returns Plotly JSON representation for worker compliance distribution donut chart.
    """
    compliant = compliance_data.get('compliant_workers', 0)
    non_compliant = compliance_data.get('non_compliant_workers', 0)
    total = compliant + non_compliant

    fig_pie = go.Figure(data=[
        go.Pie(
            labels=['Fully Compliant', 'Non-Compliant'],
            values=[compliant, non_compliant] if total > 0 else [1, 0],
            hole=0.62,
            marker=dict(colors=['#10B981', '#EF4444'], line=dict(color='#0F172A', width=3)),
            textinfo='percent+value' if total > 0 else 'none',
            textfont=dict(color='#FFFFFF', size=13, weight='bold'),
            hovertemplate="<b>%{label}</b><br>Count: %{value}<extra></extra>"
        )
    ])
    
    fig_pie.update_layout(
        title=dict(text="Worker Status Ratio", font=dict(color="#F8FAFC", size=15, weight="bold")),
        height=320,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(color="#94A3B8")
        ),
        font=dict(family="Inter, sans-serif", color="#F8FAFC"),
        annotations=[dict(text=f"<b>{total}</b><br>Workers", x=0.5, y=0.5, font_size=16, font_color="#F8FAFC", showarrow=False)]
    )
    return fig_pie.to_json()
