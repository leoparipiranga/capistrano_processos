import streamlit as st
import pandas as pd

def aplicar_filtros_temporais(df_analise):
    """Aplica filtros de ano e tipo principal"""
    
    st.subheader("🔍 Filtros")
    col_filtro1, col_filtro2 = st.columns(2)
    
    df_filtrado = df_analise.copy()
    
    with col_filtro1:
        # Filtro de data
        if 'data_convertida' in df_analise.columns:
            anos_disponiveis = sorted(df_analise['data_convertida'].dt.year.dropna().unique())
            if len(anos_disponiveis) > 0:
                anos_selecionados = st.slider(
                    "📅 Período:",
                    min_value=int(min(anos_disponiveis)),
                    max_value=int(max(anos_disponiveis)),
                    value=(int(min(anos_disponiveis)), int(max(anos_disponiveis))),
                    step=1
                )
                
                # Aplicar filtro de data
                df_filtrado = df_filtrado[
                    (df_filtrado['data_convertida'].dt.year >= anos_selecionados[0]) &
                    (df_filtrado['data_convertida'].dt.year <= anos_selecionados[1])
                ]
    
    with col_filtro2:
        # Filtro de tipo
        if 'tipoPrincipal' in df_analise.columns:
            tipos_disponiveis = ['Todos'] + sorted(df_analise['tipoPrincipal'].unique())
            tipo_selecionado = st.selectbox(
                "⚖️ Tipo de Processo:",
                tipos_disponiveis
            )
            
            if tipo_selecionado != 'Todos':
                df_filtrado = df_filtrado[df_filtrado['tipoPrincipal'] == tipo_selecionado]
    
    return df_filtrado