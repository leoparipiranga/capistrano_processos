import streamlit as st
import pandas as pd
from datetime import datetime
import base64
import requests
import sys
from pathlib import Path
import math

# Adicionar path do projeto
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Importar funções do módulo específico de RPV
from components.funcoes_rpv import (
    # Configurações RPV
    PERFIS_RPV, STATUS_ETAPAS_RPV,
    
    # Funções de perfil RPV
    verificar_perfil_usuario_rpv, pode_editar_status_rpv,
    
    # Funções de limpeza RPV
    obter_colunas_controle_rpv, inicializar_linha_vazia_rpv,
    
    # Funções de interface
    interface_lista_rpv, interface_cadastro_rpv, interface_edicao_rpv,
    interface_visualizar_dados_rpv
)

# Importar funções comuns que ainda estão no módulo de controle
from components.functions_controle import (
    # Funções GitHub
    get_github_api_info, load_data_from_github, 
    save_data_local, save_data_to_github_seguro,
    
    # Funções de arquivo
    salvar_arquivo, baixar_arquivo_github,
    gerar_id_unico, garantir_coluna_id,
    
    # Funções de análise
    mostrar_diferencas, validar_cpf, formatar_processo,
    
    # Funções de limpeza comuns
    limpar_campos_formulario
)

def show():
    """Função principal do módulo RPV"""
    
    # CSS para estilização
    st.markdown("""
    <style>
        .stSelectbox > div > div > select {
            background-color: #f0f2f6;
        }
        .stTextInput > div > div > input {
            background-color: #f0f2f6;
        }
        .metric-container {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #007bff;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Verificação de perfil
    perfil_usuario = verificar_perfil_usuario_rpv()
    st.sidebar.info(f"👤 **Perfil RPV:** {perfil_usuario}")
    
    # Título
    st.title("📄 Gestão de RPV")
    st.markdown(f"**Perfil ativo:** {perfil_usuario}")
    
    # Carregar dados
    selected_file_name = "lista_rpv.csv"
    
    if "df_editado_rpv" not in st.session_state or st.session_state.get("last_file_path_rpv") != selected_file_name:
        df, file_sha = load_data_from_github(selected_file_name)
        st.session_state.df_editado_rpv = df.copy()
        st.session_state.last_file_path_rpv = selected_file_name
        st.session_state.file_sha_rpv = file_sha
    
    df = st.session_state.df_editado_rpv
    
    # Limpar colunas sem nome
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # Abas
    aba = st.tabs(["📝 Cadastrar RPVs", "📊 Gerenciar RPVs", "📁 Visualizar Dados"])
    
    with aba[0]:
        interface_cadastro_rpv(df, perfil_usuario)
    
    with aba[1]:
        interface_lista_rpv(df, perfil_usuario)
    
    with aba[2]:
        interface_visualizar_dados_rpv(df)

