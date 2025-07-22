import plotly.express as px

def criar_grafico_barras_horizontal(dados, x_col, y_col, cor='steelblue', altura=500):
    """Cria gráfico de barras horizontal padronizado"""
    fig = px.bar(
        dados,
        x=x_col,
        y=y_col,
        orientation='h',
        color_discrete_sequence=[cor]
    )
    
    # Configurações padrão
    valor_max = dados[x_col].max()
    padding = valor_max * 0.2
    
    fig.update_layout(
        yaxis={'categoryorder':'total ascending'},
        height=altura,
        margin=dict(l=100, r=50, t=20, b=20),
        xaxis_title="",
        yaxis_title="",
        xaxis=dict(
            range=[0, valor_max + padding],
            automargin=True
        )
    )
    
    fig.update_traces(
        texttemplate='%{x}',
        textposition='outside'
    )
    
    return fig