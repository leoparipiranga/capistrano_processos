# No início do arquivo lista_alvaras.py
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

# Importar funções do módulo específico de alvarás
from components.funcoes_alvaras import (
    # Configurações
    PERFIS_ALVARAS, STATUS_ETAPAS_ALVARAS,
    
    # Funções de perfil
    verificar_perfil_usuario_alvaras, pode_editar_status_alvaras,
    
    # Funções de interface
    interface_lista_alvaras, interface_anexar_documentos, 
    interface_acoes_financeiro, interface_edicao_processo, 
    interface_cadastro_alvara,
    interface_visualizar_dados, interface_visualizar_alvara
)

# Importar funções comuns que ainda estão no módulo de controle
from components.functions_controle import (
    # Funções GitHub
    get_github_api_info, load_data_from_github, 
    save_data_local, save_data_to_github_seguro,
    
    # Funções de arquivo
    salvar_arquivo, baixar_arquivo_drive,
    gerar_id_unico, garantir_coluna_id,
    
    # Funções de análise
    mostrar_diferencas, validar_cpf, formatar_processo,
    
    # Funções de limpeza
    limpar_campos_formulario, resetar_estado_processo, 
    obter_colunas_controle, inicializar_linha_vazia
)

def show():
    # CSS para ocultar a navegação padrão do Streamlit
    st.markdown("""
    <style>
        /* Oculta a navegação padrão do Streamlit */
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
        
        /* Oculta qualquer elemento de navegação no sidebar */
        .stSidebar nav {
            display: none !important;
        }
        
        /* Oculta elementos de navegação por classe */
        .css-1d391kg, .css-1v0mbdj {
            display: none !important;
        }
        
        /* Remove padding superior do primeiro elemento do sidebar */
        .stSidebar > div:first-child {
            padding-top: 0rem;
        }
    </style>
    """, unsafe_allow_html=True)

    # ADICIONAR verificação de perfil
    perfil_usuario = verificar_perfil_usuario_alvaras()
    
    # MODIFICAR o título
    st.title("📋 Gestão de Alvarás")

    # Apenas o arquivo de alvarás
    selected_file_name = "lista_alvaras.csv"

    if "df_editado_alvaras" not in st.session_state or st.session_state.get("last_file_path_alvaras") != selected_file_name:
        df, file_sha = load_data_from_github(selected_file_name)
        st.session_state.df_editado_alvaras = df.copy()
        st.session_state.last_file_path_alvaras = selected_file_name
        st.session_state.file_sha_alvaras = file_sha
    
    df = st.session_state.df_editado_alvaras
    
    # Limpar colunas sem nome
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    aba = st.tabs(["📝 Cadastrar Alvará", "📊 Gerenciar Alvarás", "📁 Visualizar Dados"])

    with aba[0]:
        interface_cadastro_alvara(df, perfil_usuario)
    
    with aba[1]:
        interface_lista_alvaras(df, perfil_usuario)
    
    with aba[2]:
        interface_visualizar_dados(df)

