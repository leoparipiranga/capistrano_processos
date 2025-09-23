import streamlit as st
import pandas as pd
from datetime import datetime
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

from components.funcoes_acordos import (
    interface_cadastro_acordo,
    interface_lista_acordos,
    interface_visualizar_dados_acordo,
    limpar_estados_dialogo_acordo
)

def show():
    """Função principal do módulo Acordos"""
    
    # CSS para estilização
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
    
    # Verificação de perfil simples
    perfil_usuario = st.session_state.get("perfil_usuario", "N/A")
    
    # Título
    st.title("🤝 Gestão de Acordos")
    
    # Carregar dados
    selected_file_name = "lista_acordos.csv"
    
    if "df_editado_acordos" not in st.session_state or st.session_state.get("last_file_path_acordos") != selected_file_name:
        df, file_sha = load_data_from_github(selected_file_name)
        
        # GARANTIR QUE AS COLUNAS ESSENCIAIS EXISTAM
        colunas_essenciais = [
            "ID", "Processo", "Nome_Reu", "CPF_Reu", "Nome_Cliente", "CPF_Cliente", 
            "Banco", "Valor_Total", "Forma_Acordo", "A_Vista", "Num_Parcelas", 
            "Data_Primeiro_Pagamento", "Status", "Cadastrado_Por", "Data_Cadastro",
            "Comprovante_Pago", "Honorarios_Contratuais", "Valor_Cliente", 
            "H_Sucumbenciais", "Valor_Parceiro", "Outros_Valores", "Observacoes",
            "Valor_Atualizado", "Houve_Renegociacao", "Nova_Num_Parcelas", 
            "Novo_Valor_Parcela", "Acordo_Nao_Cumprido", "Data_Ultimo_Update", 
            "Usuario_Ultimo_Update"
        ]
        
        for coluna in colunas_essenciais:
            if coluna not in df.columns:
                if coluna == "Status":
                    df[coluna] = "Aguardando Pagamento"
                elif coluna == "A_Vista":
                    df[coluna] = False
                elif coluna == "Houve_Renegociacao":
                    df[coluna] = False
                elif coluna == "Acordo_Nao_Cumprido":
                    df[coluna] = False
                else:
                    df[coluna] = ""
        
        st.session_state.df_editado_acordos = df.copy()
        st.session_state.last_file_path_acordos = selected_file_name
        st.session_state.file_sha_acordos = file_sha
    
    df = st.session_state.df_editado_acordos
    
    # Limpar colunas sem nome
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # Abas - seguindo o padrão dos outros módulos
    aba_selecionada = st.tabs(["📝 Cadastrar Acordo", "📊 Gerenciar Acordos", "📈 Visualizar Dados"])
    
    with aba_selecionada[0]:
        # LIMPAR diálogos apenas quando mudando para aba de cadastro E não há diálogo ativo
        if (st.session_state.get("aba_atual_acordos") != "cadastrar" and
            not st.session_state.get("show_acordo_dialog", False)):
            st.session_state.show_acordo_dialog = False
            st.session_state.acordo_aberto_id = None
            st.session_state.aba_atual_acordos = "cadastrar"
        interface_cadastro_acordo(df, perfil_usuario)
    
    with aba_selecionada[1]:
        # Marcar que estamos na aba gerenciar
        if st.session_state.get("aba_atual_acordos") != "gerenciar":
            st.session_state.aba_atual_acordos = "gerenciar"
        interface_lista_acordos(df, perfil_usuario)
    
    with aba_selecionada[2]:
        # LIMPAR diálogos apenas quando mudando para aba de visualização E não há diálogo ativo
        if (st.session_state.get("aba_atual_acordos") != "visualizar" and
            not st.session_state.get("show_acordo_dialog", False)):
            st.session_state.show_acordo_dialog = False
            st.session_state.acordo_aberto_id = None
            st.session_state.aba_atual_acordos = "visualizar"
        interface_visualizar_dados_acordo(df)

    # ====== DIÁLOGO DE ACORDOS (RENDERIZADO APÓS TODA A INTERFACE) ======
    
    # Verificar requests de diálogo pendentes
    dialog_requests = [key for key in st.session_state.keys() if key.startswith("dialogo_acordo_request_")]
    
    if dialog_requests:
        # Pegar o request mais recente
        latest_request = max(dialog_requests)
        request_data = st.session_state[latest_request]
        
        # Usar dados do request
        show_dialog = request_data["show_acordo_dialog"]
        acordo_id = request_data["acordo_aberto_id"]
        
        if show_dialog and acordo_id:
            # Limpar o request usado
            del st.session_state[latest_request]
            
            # Buscar dados do processo
            linha_processo = df[df["ID"].astype(str) == str(acordo_id)]
            titulo_dialog = f"Detalhes do Acordo: {linha_processo.iloc[0].get('Nome_Cliente', 'Não informado')}" if not linha_processo.empty else "Detalhes do Acordo"

            @st.dialog(titulo_dialog, width="large")
            def acordo_dialog():
                if not linha_processo.empty:
                    # Importar e chamar a função de edição
                    from components.funcoes_acordos import interface_edicao_acordo
                    interface_edicao_acordo(df, acordo_id, perfil_usuario)
                else:
                    st.error("❌ Acordo não encontrado.")
                
                if st.button("Fechar", key="fechar_dialog_acordo"):
                    st.rerun()

            # Renderizar o diálogo
            acordo_dialog()

if __name__ == "__main__":
    show()