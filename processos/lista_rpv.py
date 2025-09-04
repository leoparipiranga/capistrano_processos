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
    salvar_arquivo, baixar_arquivo_drive,
    gerar_id_unico, garantir_coluna_id,
    
    # Funções de análise
    mostrar_diferencas, validar_cpf, formatar_processo,
    
    # Funções de limpeza comuns
    limpar_campos_formulario
)

def show():
    """Função principal do módulo RPV"""
    
    # CSS para estilização (removido CSS que sobrescreve cores dos inputs)
    st.markdown("""
    <style>
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
    
    # Título
    st.title("📄 Gestão de RPV")
    
    # Carregar dados
    selected_file_name = "lista_rpv.csv"
    
    if "df_editado_rpv" not in st.session_state or st.session_state.get("last_file_path_rpv") != selected_file_name:
        df, file_sha = load_data_from_github(selected_file_name)
        st.session_state.df_editado_rpv = df.copy()
        st.session_state.last_file_path_rpv = selected_file_name
        st.session_state.file_sha_rpv = file_sha
    
    df = st.session_state.df_editado_rpv
    
    # Garantir colunas do novo fluxo
    from components.funcoes_rpv import garantir_colunas_novo_fluxo
    df = garantir_colunas_novo_fluxo(df)
    st.session_state.df_editado_rpv = df
    
    # Limpar colunas sem nome
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # Abas (adicionada terceira aba Visualizar Dados)
    aba_selecionada = st.tabs(["📝 Cadastrar RPVs", "📊 Gerenciar RPVs", "📈 Visualizar Dados"])
    
    with aba_selecionada[0]:
        # LIMPAR diálogos apenas quando mudando para aba de cadastro E não há diálogo ativo
        if (st.session_state.get("aba_atual_rpv") != "cadastrar" and
            not st.session_state.get("show_rpv_dialog", False)):
            st.session_state.show_rpv_dialog = False
            st.session_state.rpv_aberto_id = None
            st.session_state.aba_atual_rpv = "cadastrar"
        interface_cadastro_rpv(df, perfil_usuario)
    
    with aba_selecionada[1]:
        # Marcar que estamos na aba gerenciar
        if st.session_state.get("aba_atual_rpv") != "gerenciar":
            st.session_state.aba_atual_rpv = "gerenciar"
        interface_lista_rpv(df, perfil_usuario)
    
    with aba_selecionada[2]:
        # LIMPAR diálogos apenas quando mudando para aba de visualização E não há diálogo ativo
        if (st.session_state.get("aba_atual_rpv") != "visualizar" and
            not st.session_state.get("show_rpv_dialog", False)):
            st.session_state.show_rpv_dialog = False
            st.session_state.rpv_aberto_id = None
            st.session_state.aba_atual_rpv = "visualizar"
        interface_visualizar_dados_rpv(df)

    # ====== DIÁLOGO DE RPV (RENDERIZADO APÓS TODA A INTERFACE) ======
    
    # Verificar requests de diálogo pendentes
    dialog_requests = [key for key in st.session_state.keys() if key.startswith("dialogo_rpv_request_")]
    
    if dialog_requests:
        # Pegar o request mais recente
        latest_request = max(dialog_requests)
        request_data = st.session_state[latest_request]
        
        # Usar dados do request
        show_dialog = request_data["show_rpv_dialog"]
        rpv_id = request_data["rpv_aberto_id"]
        
        if show_dialog and rpv_id:
            # Limpar o request usado
            del st.session_state[latest_request]
            
            # Buscar dados do processo
            linha_processo = df[df["ID"].astype(str) == str(rpv_id)]
            titulo_dialog = f"Detalhes do RPV: {linha_processo.iloc[0].get('Processo', 'Não informado')}" if not linha_processo.empty else "Detalhes do RPV"

            @st.dialog(titulo_dialog, width="large")
            def rpv_dialog():
                if not linha_processo.empty:
                    status_atual = linha_processo.iloc[0].get("Status", "")
                    # Chama a função de edição
                    interface_edicao_rpv(df, rpv_id, status_atual, perfil_usuario)
                else:
                    st.error("❌ RPV não encontrado.")
                
                if st.button("Fechar", key="fechar_dialog_rpv"):
                    st.rerun()

            # Renderizar o diálogo
            rpv_dialog()
