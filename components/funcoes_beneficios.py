# components/funcoes_beneficios.py
import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime
from components.functions_controle import (
    gerar_id_unico, garantir_coluna_id,
    get_github_api_info, save_data_to_github_seguro, load_data_from_github
)

# =====================================
# CONFIGURAÇÕES DE PERFIS - BENEFÍCIOS
# =====================================

PERFIS_BENEFICIOS = {
    "Cadastrador": ["Cadastrado", "Enviado para administrativo", "Implantado", "Enviado para o financeiro"],
    "Administrativo": ["Enviado para administrativo", "Implantado"],
    "Financeiro": ["Enviado para o financeiro", "Finalizado"],
    "SAC": ["Enviado para administrativo", "Implantado", "Enviado para o financeiro", "Finalizado"]  # SAC vê tudo
}

STATUS_ETAPAS_BENEFICIOS = {
    1: "Enviado para administrativo",  # Começa aqui automaticamente
    2: "Implantado",
    3: "Enviado para o financeiro",
    4: "Finalizado"
}

# =====================================
# FUNÇÕES DE PERFIL E CONTROLE - BENEFÍCIOS
# =====================================

def verificar_perfil_usuario_beneficios():
    """Verifica o perfil do usuário logado para Benefícios"""
    usuario_atual = st.session_state.get("usuario", "")
    
    # USUÁRIOS LOCAIS TEMPORÁRIOS PARA TESTE BENEFÍCIOS
    perfis_usuarios_beneficios = {
        "cadastrador": "Cadastrador",
        "administrativo": "Administrativo",
        "financeiro": "Financeiro",
        "sac": "SAC",
        "admin": "Cadastrador"
    }
    
    return perfis_usuarios_beneficios.get(usuario_atual, "Cadastrador")

def pode_editar_status_beneficios(status_atual, perfil_usuario):
    """Verifica se o usuário pode editar determinado status Benefícios"""
    return status_atual in PERFIS_BENEFICIOS.get(perfil_usuario, [])

def obter_colunas_controle_beneficios():
    """Retorna lista das colunas de controle do fluxo Benefícios"""
    return [
        "Status", "Data Cadastro", "Cadastrado Por",
        "Data Envio Administrativo", "Enviado Administrativo Por",
        "Implantado", "Data Implantação", "Implantado Por",
        "Benefício Verificado", "Percentual Cobrança", "Data Envio Financeiro", "Enviado Financeiro Por",
        "Tipo Pagamento", "Comprovante Pagamento", "Valor Pago", "Data Finalização", "Finalizado Por"
    ]

def inicializar_linha_vazia_beneficios():
    """Retorna dicionário com campos vazios para nova linha Benefícios"""
    campos_controle = obter_colunas_controle_beneficios()
    linha_vazia = {}
    
    for campo in campos_controle:
        linha_vazia[campo] = ""
    
    return linha_vazia

# =====================================
# FUNÇÕES DE INTERFACE E INTERAÇÃO - BENEFÍCIOS
# =====================================

def interface_lista_beneficios(df, perfil_usuario):
    """Lista de benefícios com botão Abrir para ações"""
    st.subheader("📊 Lista de Benefícios")
    
    # FILTROS
    with st.expander("🔍 Filtros", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # Filtro por status
            filtro_status = st.selectbox(
                "Status",
                ["Todos"] + list(STATUS_ETAPAS_BENEFICIOS.values())
            )
        
        with col2:
            # Filtro por termo de busca
            filtro_busca = st.text_input("Buscar por nome ou processo")
    
    # Aplicar filtros
    df_trabalho = df.copy()
    
    # Filtro por status
    if filtro_status != "Todos":
        df_trabalho = df_trabalho[df_trabalho["Status"] == filtro_status]
    
    # Filtro por termo de busca
    if filtro_busca:
        df_trabalho = df_trabalho[
            df_trabalho.apply(
                lambda row: any(
                    filtro_busca.lower() in str(value).lower()
                    for value in row.values
                ),
                axis=1
            )
        ]
    
    # Verificar se há dados
    if len(df_trabalho) == 0:
        st.info("Nenhum benefício encontrado com os filtros selecionados.")
        return
    
    # Botão para adicionar novo benefício
    st.button("➕ Adicionar Novo Benefício", key="add_beneficio", 
              on_click=lambda: adicionar_novo_beneficio(df))
    
    # Exibir tabela com botão para abrir cada item
    st.markdown(f"### 📋 Lista ({len(df_trabalho)} benefícios)")
    
    # Mostrar registros em tabela com botão para abrir
    for _, row in df_trabalho.iterrows():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        
        with col1:
            st.write(f"**{row.get('Beneficiário', 'N/A')}**")
            st.caption(f"Processo: {row.get('Processo', 'N/A')}")
        
        with col2:
            st.write(f"**Espécie:** {row.get('Espécie', 'N/A')}")
            st.caption(f"DIB: {row.get('DIB', 'N/A')}")
        
        with col3:
            st.write(f"**Status:** {row.get('Status', 'N/A')}")
            
        with col4:
            # Botão para abrir detalhes do benefício
            st.button("Abrir", key=f"open_{row.get('ID')}", 
                      on_click=lambda id=row.get('ID'): abrir_beneficio(id, df))
        
        st.divider()

def abrir_beneficio(beneficio_id, df):
    """Abre um benefício para visualização/edição"""
    # Armazenar ID do benefício selecionado na sessão
    st.session_state.beneficio_selecionado = beneficio_id
    st.session_state.view = "editar_beneficio"

def adicionar_novo_beneficio(df):
    """Prepara para adicionar um novo benefício"""
    # Atualizar visualização para formulário de cadastro
    st.session_state.view = "cadastrar_beneficio"
    st.session_state.beneficio_selecionado = None

def interface_cadastro_beneficio(df, perfil_usuario):
    """Interface para cadastro de novo benefício"""
    st.header("📝 Cadastrar Novo Benefício")
    
    # Colunas para os campos do formulário
    col1, col2 = st.columns(2)
    
    with col1:
        processo = st.text_input("Processo", key="input_beneficio_Processo")
        beneficiario = st.text_input("Beneficiário", key="input_beneficio_Beneficiario")
        cpf = st.text_input("CPF", key="input_beneficio_CPF")
        nb = st.text_input("NB", key="input_beneficio_NB")
    
    with col2:
        especie = st.text_input("Espécie", key="input_beneficio_Especie")
        dib = st.date_input("DIB", key="input_beneficio_DIB")
        dcb = st.date_input("DCB", key="input_beneficio_DCB")
        valor = st.text_input("Valor", key="input_beneficio_Valor")
    
    observacoes = st.text_area("Observações", key="input_beneficio_Observacoes")
    
    # Botões de ação
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Salvar", use_container_width=True):
            # Verificar se campos obrigatórios foram preenchidos
            if not processo or not beneficiario:
                st.error("Preencha os campos obrigatórios: Processo e Beneficiário")
                return
            
            # Gerar novo ID
            novo_id = gerar_id_unico(df, "ID")
            
            # Preparar nova linha com dados
            nova_linha = {
                "ID": novo_id,
                "Processo": processo,
                "Beneficiário": beneficiario,
                "CPF": cpf,
                "NB": nb,
                "Espécie": especie,
                "DIB": dib.strftime("%d/%m/%Y") if hasattr(dib, "strftime") else dib,
                "DCB": dcb.strftime("%d/%m/%Y") if hasattr(dcb, "strftime") else dcb,
                "Valor": valor,
                "Observações": observacoes,
                "Status": "Cadastrado",
                "Data Cadastro": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Cadastrado Por": st.session_state.get("usuario", "")
            }
            
            # Adicionar informações de controle
            campos_controle = inicializar_linha_vazia_beneficios()
            nova_linha.update(campos_controle)
            
            # Adicionar nova linha ao DataFrame
            if "df_editado_beneficios" not in st.session_state:
                st.session_state.df_editado_beneficios = df.copy()
            
            st.session_state.df_editado_beneficios = pd.concat(
                [st.session_state.df_editado_beneficios, pd.DataFrame([nova_linha])], 
                ignore_index=True
            )
            
            # Salvar no GitHub
            novo_sha = save_data_to_github_seguro(
                st.session_state.df_editado_beneficios,
                "lista_beneficios.csv",
                "file_sha_beneficios"
            )
            
            if novo_sha:
                st.session_state.file_sha_beneficios = novo_sha
                st.success(f"Benefício cadastrado com sucesso! ID: {novo_id}")
                st.session_state.view = "lista_beneficios"  # Voltar para lista
    
    with col2:
        if st.button("❌ Cancelar", use_container_width=True):
            st.session_state.view = "lista_beneficios"  # Voltar para lista

def interface_edicao_beneficio(df, beneficio_id, perfil_usuario):
    """Interface para edição de um benefício existente"""
    # Verificar se o ID existe no DataFrame
    if "ID" not in df.columns or beneficio_id not in df["ID"].values:
        st.error(f"Benefício ID {beneficio_id} não encontrado.")
        st.session_state.view = "lista_beneficios"
        return
    
    # Obter os dados do benefício
    beneficio = df[df["ID"] == beneficio_id].iloc[0]
    processo = beneficio.get("Processo", "")
    status_atual = beneficio.get("Status", "")
    
    st.header(f"Benefício: {processo}")
    st.subheader(f"Beneficiário: {beneficio.get('Beneficiário', '')}")
    
    # Exibir informações gerais
    with st.expander("📄 Informações Gerais", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**ID:** {beneficio_id}")
            st.write(f"**Processo:** {processo}")
            st.write(f"**Beneficiário:** {beneficio.get('Beneficiário', '')}")
            st.write(f"**CPF:** {beneficio.get('CPF', '')}")
            st.write(f"**NB:** {beneficio.get('NB', '')}")
        
        with col2:
            st.write(f"**Espécie:** {beneficio.get('Espécie', '')}")
            st.write(f"**DIB:** {beneficio.get('DIB', '')}")
            st.write(f"**DCB:** {beneficio.get('DCB', '')}")
            st.write(f"**Valor:** {beneficio.get('Valor', '')}")
    
    st.write(f"**Observações:** {beneficio.get('Observações', '')}")
    
    # Verificar se o usuário pode editar o status atual
    pode_editar = pode_editar_status_beneficios(status_atual, perfil_usuario)
    
    # Exibir status atual e opções de fluxo
    st.write(f"**Status Atual:** {status_atual}")
    
    if pode_editar:
        # Exibir opções de próximos passos baseado no status atual
        if status_atual == "Cadastrado":
            if st.button("📤 Enviar para Administrativo"):
                atualizar_status_beneficio(beneficio_id, "Enviado para administrativo", df)
        
        elif status_atual == "Enviado para administrativo":
            if perfil_usuario in ["Administrativo", "SAC"]:
                if st.button("✅ Marcar como Implantado"):
                    atualizar_status_beneficio(beneficio_id, "Implantado", df)
        
        elif status_atual == "Implantado":
            if st.button("📤 Enviar para Financeiro"):
                atualizar_status_beneficio(beneficio_id, "Enviado para o financeiro", df)
        
        elif status_atual == "Enviado para o financeiro":
            if perfil_usuario == "Financeiro":
                # Upload de comprovante de pagamento
                comprovante = st.file_uploader("Comprovante de Pagamento", type=["pdf"])
                valor_pago = st.text_input("Valor Pago")
                tipo_pagamento = st.selectbox("Tipo de Pagamento", ["Transferência", "PIX", "Cheque", "Dinheiro"])
                
                if st.button("✅ Finalizar"):
                    # Salvar comprovante se foi enviado
                    comprovante_base64 = ""
                    if comprovante:
                        comprovante_bytes = comprovante.read()
                        comprovante_base64 = base64.b64encode(comprovante_bytes).decode()
                    
                    # Atualizar dados do benefício
                    atualizar_dados_finalizacao(
                        beneficio_id, "Finalizado", df, 
                        comprovante_base64, valor_pago, tipo_pagamento
                    )
    
    # Botão para voltar à lista
    if st.button("↩️ Voltar para Lista"):
        st.session_state.view = "lista_beneficios"

def atualizar_status_beneficio(beneficio_id, novo_status, df):
    """Atualiza o status de um benefício"""
    # Verificar se dataframe editado existe na sessão
    if "df_editado_beneficios" not in st.session_state:
        st.session_state.df_editado_beneficios = df.copy()
    
    # Atualizar status
    idx = st.session_state.df_editado_beneficios["ID"] == beneficio_id
    
    # Obter usuário atual
    usuario_atual = st.session_state.get("usuario", "")
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    # Atualizar campos com base no novo status
    if novo_status == "Enviado para administrativo":
        st.session_state.df_editado_beneficios.loc[idx, "Data Envio Administrativo"] = data_atual
        st.session_state.df_editado_beneficios.loc[idx, "Enviado Administrativo Por"] = usuario_atual
    
    elif novo_status == "Implantado":
        st.session_state.df_editado_beneficios.loc[idx, "Implantado"] = "Sim"
        st.session_state.df_editado_beneficios.loc[idx, "Data Implantação"] = data_atual
        st.session_state.df_editado_beneficios.loc[idx, "Implantado Por"] = usuario_atual
    
    elif novo_status == "Enviado para o financeiro":
        st.session_state.df_editado_beneficios.loc[idx, "Data Envio Financeiro"] = data_atual
        st.session_state.df_editado_beneficios.loc[idx, "Enviado Financeiro Por"] = usuario_atual
    
    # Atualizar status
    st.session_state.df_editado_beneficios.loc[idx, "Status"] = novo_status
    
    # Salvar no GitHub
    novo_sha = save_data_to_github_seguro(
        st.session_state.df_editado_beneficios,
        "lista_beneficios.csv",
        "file_sha_beneficios"
    )
    
    if novo_sha:
        st.session_state.file_sha_beneficios = novo_sha
        st.success(f"Status atualizado para: {novo_status}")
        # Recarregar a página para mostrar as mudanças
        st.experimental_rerun()

def atualizar_dados_finalizacao(beneficio_id, novo_status, df, comprovante, valor_pago, tipo_pagamento):
    """Atualiza os dados de finalização de um benefício"""
    # Verificar se dataframe editado existe na sessão
    if "df_editado_beneficios" not in st.session_state:
        st.session_state.df_editado_beneficios = df.copy()
    
    # Atualizar dados
    idx = st.session_state.df_editado_beneficios["ID"] == beneficio_id
    
    # Obter usuário atual
    usuario_atual = st.session_state.get("usuario", "")
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    # Atualizar campos
    st.session_state.df_editado_beneficios.loc[idx, "Status"] = novo_status
    st.session_state.df_editado_beneficios.loc[idx, "Data Finalização"] = data_atual
    st.session_state.df_editado_beneficios.loc[idx, "Finalizado Por"] = usuario_atual
    st.session_state.df_editado_beneficios.loc[idx, "Comprovante Pagamento"] = comprovante
    st.session_state.df_editado_beneficios.loc[idx, "Valor Pago"] = valor_pago
    st.session_state.df_editado_beneficios.loc[idx, "Tipo Pagamento"] = tipo_pagamento
    
    # Salvar no GitHub
    novo_sha = save_data_to_github_seguro(
        st.session_state.df_editado_beneficios,
        "lista_beneficios.csv",
        "file_sha_beneficios"
    )
    
    if novo_sha:
        st.session_state.file_sha_beneficios = novo_sha
        st.success("Benefício finalizado com sucesso!")
        # Recarregar a página para mostrar as mudanças
        st.experimental_rerun()

# =====================================
# FUNÇÕES DE EXPORTAÇÃO E IMPORTAÇÃO - BENEFÍCIOS
# =====================================

def carregar_beneficios():
    """Carrega os dados de benefícios do GitHub"""
    df, file_sha = load_data_from_github("lista_beneficios.csv")
    
    # Garantir que o DataFrame tenha a coluna ID
    df = garantir_coluna_id(df)
    
    return df
