import streamlit as st
import pandas as pd
from datetime import datetime
import base64
import requests
import sys
from pathlib import Path

# Adicionar path do projeto
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Importar funções do módulo de controle
from components.functions_controle import (
    # Configurações Benefícios
    PERFIS_BENEFICIOS, STATUS_ETAPAS_BENEFICIOS,
    
    # Funções de perfil Benefícios
    verificar_perfil_usuario_beneficios, pode_editar_status_beneficios,
    
    # Funções GitHub
    get_github_api_info, load_data_from_github, 
    save_data_local, save_data_to_github_seguro,
    
    # Funções de arquivo
    salvar_arquivo, baixar_arquivo_drive,
    gerar_id_unico, garantir_coluna_id,
    
    # Funções de análise
    mostrar_diferencas, validar_cpf, formatar_processo,
    
    # Funções de limpeza Benefícios
    limpar_campos_formulario, obter_colunas_controle_beneficios, inicializar_linha_vazia_beneficios
)

from components.funcoes_beneficios import *

def show():
    """Função principal do módulo Benefícios"""
    
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
            border-left: 4px solid #28a745;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Verificação de perfil
    perfil_usuario = verificar_perfil_usuario_beneficios()
    
    # Título
    st.title("🏥 Gestão de Benefícios")
    
    # Carregar dados
    selected_file_name = "lista_beneficios.csv"
    
    if "df_editado_beneficios" not in st.session_state or st.session_state.get("last_file_path_beneficios") != selected_file_name:
        df, file_sha = load_data_from_github(selected_file_name)
        
        # GARANTIR QUE VALOR PAGO SEJA NUMÉRICO
        if "Valor Pago" in df.columns:
            df["Valor Pago"] = pd.to_numeric(df["Valor Pago"], errors='coerce')
        
        st.session_state.df_editado_beneficios = df.copy()
        st.session_state.last_file_path_beneficios = selected_file_name
        st.session_state.file_sha_beneficios = file_sha
   
    
    df = st.session_state.df_editado_beneficios
    
    # Limpar colunas sem nome
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # Abas
    aba = st.tabs(["📝 Cadastrar Benefício", "📊 Gerenciar Benefícios", "📁 Visualizar Dados"])
    
    with aba[0]:
        interface_cadastro_beneficio(df, perfil_usuario)
    
    with aba[1]:
        interface_lista_beneficios(df, perfil_usuario)
    
    with aba[2]:
        interface_visualizar_dados_beneficios(df)

