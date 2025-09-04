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
    # Funções GitHub
    get_github_api_info, load_data_from_github,
    save_data_local, save_data_to_github_seguro,
    
    # Funções de arquivo
    salvar_arquivo, baixar_arquivo_drive,
    gerar_id_unico, garantir_coluna_id,
    
    # Funções de análise
    mostrar_diferencas, validar_cpf, formatar_processo
)

from components.funcoes_beneficios import (
    interface_cadastro_beneficio,
    interface_lista_beneficios,
    interface_visualizar_dados_beneficio,
    limpar_estados_dialogo_beneficio
)

def show():
    """Função principal do módulo Benefícios"""
    
    # CSS para estilização (removido CSS que sobrescreve cores dos inputs)
    st.markdown("""
    <style>
        .metric-container {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #28a745;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Verificação de perfil simples
    perfil_usuario = st.session_state.get("perfil_usuario", "N/A")
    
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
    
    # Abas - adicionando aba Visualizar Dados
    aba_selecionada = st.tabs(["📝 Cadastrar Benefício", "📊 Gerenciar Benefícios", "📈 Visualizar Dados"])
    
    with aba_selecionada[0]:
        # LIMPAR diálogos apenas quando mudando para aba de cadastro E não há diálogo ativo
        if (st.session_state.get("aba_atual_beneficios") != "cadastrar" and
            not st.session_state.get("show_beneficio_dialog", False)):
            st.session_state.show_beneficio_dialog = False
            st.session_state.beneficio_aberto_id = None
            st.session_state.aba_atual_beneficios = "cadastrar"
        interface_cadastro_beneficio(df, perfil_usuario)
    
    with aba_selecionada[1]:
        # Marcar que estamos na aba gerenciar
        if st.session_state.get("aba_atual_beneficios") != "gerenciar":
            st.session_state.aba_atual_beneficios = "gerenciar"
        interface_lista_beneficios(df, perfil_usuario)
    
    with aba_selecionada[2]:
        # LIMPAR diálogos apenas quando mudando para aba de visualização E não há diálogo ativo
        if (st.session_state.get("aba_atual_beneficios") != "visualizar" and
            not st.session_state.get("show_beneficio_dialog", False)):
            st.session_state.show_beneficio_dialog = False
            st.session_state.beneficio_aberto_id = None
            st.session_state.aba_atual_beneficios = "visualizar"
        interface_visualizar_dados_beneficio(df)

    # ====== DIÁLOGO DE BENEFÍCIOS (RENDERIZADO APÓS TODA A INTERFACE) ======
    
    # Verificar requests de diálogo pendentes
    dialog_requests = [key for key in st.session_state.keys() if key.startswith("dialogo_beneficio_request_")]
    
    if dialog_requests:
        # Pegar o request mais recente
        latest_request = max(dialog_requests)
        request_data = st.session_state[latest_request]
        
        # Usar dados do request
        show_dialog = request_data["show_beneficio_dialog"]
        beneficio_id = request_data["beneficio_aberto_id"]
        
        if show_dialog and beneficio_id:
            # Limpar o request usado
            del st.session_state[latest_request]
            
            # Buscar dados do processo
            linha_processo = df[df["ID"].astype(str) == str(beneficio_id)]
            titulo_dialog = f"Detalhes do Benefício: {linha_processo.iloc[0].get('PARTE', 'Não informado')}" if not linha_processo.empty else "Detalhes do Benefício"

            @st.dialog(titulo_dialog, width="large")
            def beneficio_dialog():
                if not linha_processo.empty:
                    # Importar e chamar a função de edição (só 3 parâmetros)
                    from components.funcoes_beneficios import interface_edicao_beneficio
                    interface_edicao_beneficio(df, beneficio_id, perfil_usuario)
                else:
                    st.error("❌ Benefício não encontrado.")
                
                if st.button("Fechar", key="fechar_dialog_beneficio"):
                    st.rerun()

            # Renderizar o diálogo
            beneficio_dialog()
