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
    interface_lista_alvaras, interface_cadastro_alvara,
    interface_visualizar_dados, interface_visualizar_dados_alvara,
    
    # Funções de renderização de abas
    render_tab_info_alvara, render_tab_acoes_alvara, render_tab_historico_alvara
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
    # ADICIONAR verificação de perfil
    perfil_usuario = verificar_perfil_usuario_alvaras()
    
    # MODIFICAR o título
    st.title(f"📋 Gestão de Alvarás")

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

    # Abas - adicionando aba Visualizar Dados
    aba = st.tabs(["📝 Cadastrar Alvará", "📊 Gerenciar Alvarás", "📈 Visualizar Dados"])

    with aba[0]:
        interface_cadastro_alvara(df, perfil_usuario)
    
    with aba[1]:
        interface_lista_alvaras(df, perfil_usuario)
    
    with aba[2]:
        interface_visualizar_dados_alvara(df)

    # ====== DIÁLOGO DE ALVARÁS (RENDERIZADO APÓS TODA A INTERFACE) ======
    
    # Verificar requests de diálogo pendentes
    dialog_requests = [key for key in st.session_state.keys() if key.startswith("dialogo_request_")]
    
    if dialog_requests:
        # Pegar o request mais recente
        latest_request = max(dialog_requests)
        request_data = st.session_state[latest_request]
        
        # Usar dados do request
        show_dialog = request_data["show_alvara_dialog"]
        processo_id = request_data["processo_aberto_id"]
        
        if show_dialog and processo_id:
            # Limpar o request usado
            del st.session_state[latest_request]
            
            # Buscar dados do processo
            alvara_id_aberto = processo_id
            linha_processo = df[df["ID"].astype(str) == str(alvara_id_aberto)]
            titulo_dialog = f"Detalhes do Alvará: {linha_processo.iloc[0].get('Processo', 'Não informado')}" if not linha_processo.empty else "Detalhes do Alvará"

            @st.dialog(titulo_dialog, width="large")
            def alvara_dialog():
                if not linha_processo.empty:
                    processo = linha_processo.iloc[0]
                    status_atual = processo.get("Status", "")
                    
                    # Criar abas no diálogo
                    tab_info, tab_acoes, tab_historico = st.tabs(["📋 Info", "⚙️ Ações", "📜 Histórico"])
                    
                    with tab_info:
                        render_tab_info_alvara(processo, alvara_id_aberto)
                    
                    with tab_acoes:
                        render_tab_acoes_alvara(df, processo, alvara_id_aberto, status_atual, perfil_usuario)
                    
                    with tab_historico:
                        render_tab_historico_alvara(processo, alvara_id_aberto)
                else:
                    st.error("❌ Alvará não encontrado.")
                
                if st.button("Fechar", key="fechar_dialog_alvaras"):
                    st.rerun()

            # Renderizar o diálogo
            alvara_dialog()
