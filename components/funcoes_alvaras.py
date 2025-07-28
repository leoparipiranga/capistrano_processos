# components/funcoes_alvaras.py
import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime
import math
from streamlit_modal import Modal
from streamlit_js_eval import streamlit_js_eval # 1. ADICIONE ESTE IMPORT

# =====================================
# CONFIGURAÇÕES DE PERFIS - ALVARÁS
# =====================================

PERFIS_ALVARAS = {
    "Cadastrador": ["Cadastrado", "Enviado para o Financeiro"],
    "Financeiro": ["Enviado para o Financeiro", "Financeiro - Enviado para Rodrigo", "Finalizado"]
}

STATUS_ETAPAS_ALVARAS = {
    1: "Cadastrado",
    2: "Enviado para o Financeiro", 
    3: "Financeiro - Enviado para Rodrigo",
    4: "Finalizado"
}

# =====================================
# FUNÇÕES DE PERFIL E CONTROLE - ALVARÁS
# =====================================

def verificar_perfil_usuario_alvaras():
    """Verifica o perfil do usuário logado"""
    usuario_atual = st.session_state.get("usuario", "")
    
    perfis_usuarios = {
        "admin": "Cadastrador",
        "leonardo": "Cadastrador", 
        "victor": "Cadastrador",
        "claudia": "Financeiro",
        "secretaria": "Cadastrador"
    }
    
    return perfis_usuarios.get(usuario_atual, "Cadastrador")
def pode_editar_status_alvaras(status_atual, perfil_usuario):
    """Verifica se o usuário pode editar determinado status"""
    return status_atual in PERFIS_ALVARAS.get(perfil_usuario, [])

# Funções auxiliares para o cadastro de alvarás
def obter_colunas_controle():
    """Retorna lista das colunas de controle do fluxo"""
    return [
        "Status", "Data Cadastro", "Cadastrado Por", "Comprovante Conta", 
        "PDF Alvará", "Data Envio Financeiro", "Enviado Financeiro Por",
        "Data Envio Rodrigo", "Enviado Rodrigo Por", "Comprovante Recebimento",
        "Data Finalização", "Finalizado Por"
    ]

def inicializar_linha_vazia():
    """Retorna dicionário com campos vazios para nova linha"""
    campos_controle = obter_colunas_controle()
    linha_vazia = {}
    
    for campo in campos_controle:
        linha_vazia[campo] = ""
    
    return linha_vazia

# =====================================
# FUNÇÕES DE INTERFACE E AÇÕES - ALVARÁS
# =====================================

def interface_lista_alvaras(df, perfil_usuario):
    """Lista de alvarás com paginação e modal para ações"""
    
    # Inicializar o estado do diálogo
    if "show_alvara_dialog" not in st.session_state:
        st.session_state.show_alvara_dialog = False
        st.session_state.processo_aberto_id = None

    # Filtros - agora em 4 colunas
    col_filtro1, col_filtro2, col_filtro3, col_filtro4 = st.columns(4)
    
    with col_filtro1:
        if "Status" in df.columns:
            status_filtro = st.selectbox(
                "🔍 Filtrar por Status:",
                ["Todos"] + list(STATUS_ETAPAS_ALVARAS.values())
            )
        else:
            status_filtro = "Todos"
    
    with col_filtro2:
        processo_filtro = st.text_input(
            "🔍 Filtrar por Processo:",
            placeholder="Digite o número do processo..."
        )
    
    with col_filtro3:
        nome_filtro = st.text_input(
            "🔍 Filtrar por Nome:",
            placeholder="Digite o nome da parte..."
        )
    
    with col_filtro4:
        mostrar_apenas_meus = False
        if perfil_usuario == "Financeiro":
            mostrar_apenas_meus = st.checkbox("Mostrar apenas processos que posso editar")
    
    # Aplicar filtros
    df_filtrado = df.copy()
    
    if status_filtro != "Todos" and "Status" in df.columns:
        df_filtrado = df_filtrado[df_filtrado["Status"] == status_filtro]
    if processo_filtro:
        df_filtrado = df_filtrado[df_filtrado["Processo"].astype(str).str.contains(processo_filtro, case=False, na=False)]
    if nome_filtro:
        df_filtrado = df_filtrado[df_filtrado["Parte"].astype(str).str.contains(nome_filtro, case=False, na=False)]
    
    if mostrar_apenas_meus and perfil_usuario == "Financeiro":
        df_filtrado = df_filtrado[df_filtrado["Status"].isin(["Enviado para o Financeiro", "Financeiro - Enviado para Rodrigo"])]
    
    # Ordenar por data de cadastro mais novo
    if "Data Cadastro" in df_filtrado.columns:
        df_filtrado["Data Cadastro Temp"] = pd.to_datetime(df_filtrado["Data Cadastro"], format="%d/%m/%Y %H:%M", errors="coerce")
        df_filtrado = df_filtrado.sort_values("Data Cadastro Temp", ascending=False, na_position="last").drop("Data Cadastro Temp", axis=1)
    else:
        df_filtrado = df_filtrado.sort_index(ascending=False)
    
    # Garantir IDs únicos
    df_trabalho = df_filtrado.copy()
    for idx in df_trabalho.index:
        id_atual = df_trabalho.loc[idx, "ID"]
        if pd.isna(id_atual) or str(id_atual).strip() == "" or "E+" in str(id_atual).upper():
            processo_hash = hash(str(df_trabalho.loc[idx, "Processo"]))
            novo_id = f"{idx}_{abs(processo_hash)}"
            df_trabalho.loc[idx, "ID"] = novo_id
            st.session_state.df_editado_alvaras.loc[idx, "ID"] = novo_id

    # --- LÓGICA DE PAGINAÇÃO ---
    if "current_page_alvaras" not in st.session_state:
        st.session_state.current_page_alvaras = 1
    
    items_per_page = 20
    total_registros = len(df_trabalho)
    total_pages = math.ceil(total_registros / items_per_page) if items_per_page > 0 else 1
    
    start_idx = (st.session_state.current_page_alvaras - 1) * items_per_page
    end_idx = start_idx + items_per_page
    df_paginado = df_trabalho.iloc[start_idx:end_idx]

    # Botão para salvar alterações pendentes
    if "preview_novas_linhas" in st.session_state and len(st.session_state["preview_novas_linhas"]) > 0:
        st.markdown("### 📋 Linhas Adicionadas (não salvas)")
        if st.button("💾 Salvar Alterações", type="primary"):
            # ... (sua lógica de salvar) ...
            st.rerun()
    
    # Exibir lista com botão Abrir
    if len(df_paginado) > 0:
        st.markdown(f'<p style="font-size: small; color: steelblue;">Mostrando {start_idx+1} a {min(end_idx, total_registros)} de {total_registros} alvarás</p>', unsafe_allow_html=True)
        
        col_abrir, col_processo, col_parte, col_valor, col_status = st.columns([1, 2, 2, 1.5, 2])
        with col_abrir: st.markdown("**Ação**")
        with col_processo: st.markdown("**Processo**")
        with col_parte: st.markdown("**Parte**")
        with col_valor: st.markdown("**Valor**")
        with col_status: st.markdown("**Status**")
        
        st.markdown('<hr style="margin-top: 0.1rem; margin-bottom: 0.5rem;" />', unsafe_allow_html=True)
        
        for idx, processo in df_paginado.iterrows():
            col_abrir, col_processo, col_parte, col_valor, col_status = st.columns([1, 2, 2, 1.5, 2])
            alvara_id = processo.get("ID", f"temp_{idx}")
            
            with col_abrir:
                # --- MUDANÇA NO BOTÃO ---
                if st.button(f"🔓 Abrir", key=f"abrir_alvara_id_{alvara_id}"):
                    st.session_state.show_alvara_dialog = True
                    st.session_state.processo_aberto_id = alvara_id
                    st.rerun() # Força o rerun para o diálogo aparecer

            with col_processo: st.write(f"**{processo.get('Processo', 'N/A')}**")
            with col_parte: st.write(processo.get('Parte', 'N/A'))
            with col_valor: st.write(processo.get('Pagamento', '-'))
            with col_status:
                status_atual = processo.get('Status', 'N/A')
                cor = {"Cadastrado": "🟡", "Enviado para o Financeiro": "🟠", "Financeiro - Enviado para Rodrigo": "🔵", "Finalizado": "🟢"}.get(status_atual, "")
                st.write(f"{cor} {status_atual}")

       # --- IMPLEMENTAÇÃO COM st.dialog ---
    if st.session_state.show_alvara_dialog:
        alvara_id_aberto = st.session_state.processo_aberto_id
        linha_processo = df[df["ID"].astype(str) == str(alvara_id_aberto)]
        titulo_dialog = f"Detalhes do Alvará: {linha_processo.iloc[0].get('Processo', 'N/A')}" if not linha_processo.empty else "Detalhes do Alvará"

        @st.dialog(titulo_dialog, width="large")
        def alvara_dialog():
            if not linha_processo.empty:
                status_atual = linha_processo.iloc[0].get("Status", "")
                # Chama a função de edição que você já tem
                interface_edicao_processo(df, alvara_id_aberto, status_atual, perfil_usuario)
            else:
                st.error("❌ Alvará não encontrado.")
            
            if st.button("Fechar", key="fechar_dialog"):
                st.session_state.show_alvara_dialog = False
                st.rerun()

        # Chama a função para renderizar o diálogo
        alvara_dialog()

        # --- CONTROLES DE PAGINAÇÃO (EMBAIXO) ---
        st.markdown("---")
        col_nav1, col_nav2, col_nav3 = st.columns([3, 2, 3])

        with col_nav1:
            if st.session_state.current_page_alvaras > 1:
                if st.button("<< Primeira", key="btn_primeira"):
                    st.session_state.current_page_alvaras = 1
                    st.rerun()
                if st.button("< Anterior", key="btn_anterior"):
                    st.session_state.current_page_alvaras -= 1
                    st.rerun()

        with col_nav2:
            st.write(f"Página {st.session_state.current_page_alvaras} de {total_pages}")

        with col_nav3:
            if st.session_state.current_page_alvaras < total_pages:
                if st.button("Próxima >", key="btn_proxima"):
                    st.session_state.current_page_alvaras += 1
                    st.rerun()
                if st.button("Última >>", key="btn_ultima"):
                    st.session_state.current_page_alvaras = total_pages
                    st.rerun()
    else:
        st.info("Nenhum alvará encontrado com os filtros aplicados")

def interface_anexar_documentos(df, processo):
    """Interface para anexar comprovante e PDF do alvará"""
    st.markdown(f"### 📎 Anexar Documentos - Processo: {processo}")
    
    # Buscar dados do processo
    linha_processo = df[df["Processo"] == processo].iloc[0]
    
    if linha_processo["Status"] != "Cadastrado":
        st.warning("⚠️ Este processo não está na etapa de anexação de documentos")
        return
    
    col_doc1, col_doc2 = st.columns(2)
    
    with col_doc1:
        st.markdown("**📄 Comprovante da Conta**")
        comprovante_conta = st.file_uploader(
            "Anexar comprovante da conta:",
            type=["pdf", "jpg", "jpeg", "png"],
            key=f"comprovante_{processo}"
        )
    
    with col_doc2:
        st.markdown("**📄 PDF do Alvará**")
        pdf_alvara = st.file_uploader(
            "Anexar PDF do alvará:",
            type=["pdf"],
            key=f"pdf_{processo}"
        )
    
    if comprovante_conta and pdf_alvara:
        st.success("✅ Ambos os documentos foram anexados!")
        
        if st.button("📤 Enviar para Financeiro", type="primary"):
            # Salvar arquivos (implementar upload para GitHub ou storage)
            from components.functions_controle import salvar_arquivo
            comprovante_path = salvar_arquivo(comprovante_conta, processo, "comprovante")
            pdf_path = salvar_arquivo(pdf_alvara, processo, "alvara")
            
            # Atualizar status
            idx = df[df["Processo"] == processo].index[0]
            st.session_state.df_editado_alvaras.loc[idx, "Status"] = "Enviado para o Financeiro"
            st.session_state.df_editado_alvaras.loc[idx, "Comprovante Conta"] = comprovante_path
            st.session_state.df_editado_alvaras.loc[idx, "PDF Alvará"] = pdf_path
            st.session_state.df_editado_alvaras.loc[idx, "Data Envio Financeiro"] = datetime.now().strftime("%d/%m/%Y %H:%M")
            st.session_state.df_editado_alvaras.loc[idx, "Enviado Financeiro Por"] = st.session_state.get("usuario", "Sistema")
            
            st.success("✅ Processo enviado para o Financeiro!")
            st.rerun()
    
    elif comprovante_conta or pdf_alvara:
        st.warning("⚠️ Anexe ambos os documentos para prosseguir")
    else:
        st.info("📋 Anexe o comprovante da conta e o PDF do alvará")

def interface_acoes_financeiro(df_filtrado):
    """Ações específicas do perfil Financeiro"""
    
    # Processos aguardando ação do financeiro
    aguardando_financeiro = df_filtrado[df_filtrado["Status"] == "Enviado para o Financeiro"]
    enviados_Rodrigo = df_filtrado[df_filtrado["Status"] == "Financeiro - Enviado para Rodrigo"]
    
    if len(aguardando_financeiro) > 0:
        st.markdown("### 📤 Enviar para Rodrigo")
        
        for _, processo in aguardando_financeiro.iterrows():
            with st.expander(f"Processo: {processo['Processo']} - {processo['Parte']}"):
                col_info, col_acao = st.columns([2, 1])
                
                with col_info:
                    st.write(f"**Pagamento:** {processo['Pagamento']}")
                    st.write(f"**Banco:** {processo['Banco']}")
                    
                    # Mostrar documentos anexados
                    if processo["Comprovante Conta"]:
                        st.write("✅ Comprovante da conta anexado")
                    if processo["PDF Alvará"]:
                        st.write("✅ PDF do alvará anexado")
                
                with col_acao:
                    if st.button(f"📤 Enviar para Rodrigo", key=f"enviar_Rodrigo_{processo['Processo']}"):
                        # Atualizar status
                        idx = df_filtrado[df_filtrado["Processo"] == processo["Processo"]].index[0]
                        st.session_state.df_editado_alvaras.loc[idx, "Status"] = "Financeiro - Enviado para Rodrigo"
                        st.session_state.df_editado_alvaras.loc[idx, "Data Envio Rodrigo"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                        st.session_state.df_editado_alvaras.loc[idx, "Enviado Rodrigo Por"] = st.session_state.get("usuario", "Sistema")
                        
                        st.success("✅ Processo enviado para o Rodrigo!")
                        st.rerun()
    
    if len(enviados_Rodrigo) > 0:
        st.markdown("### ✅ Finalizar Processos")
        
        for _, processo in enviados_Rodrigo.iterrows():
            with st.expander(f"Finalizar: {processo['Processo']} - {processo['Parte']}"):
                comprovante_recebimento = st.file_uploader(
                    "Anexar comprovante de recebimento:",
                    type=["pdf", "jpg", "jpeg", "png"],
                    key=f"recebimento_{processo['Processo']}"
                )
                
                if comprovante_recebimento:
                    if st.button(f"✅ Finalizar Processo", key=f"finalizar_{processo['Processo']}"):
                        # Salvar comprovante de recebimento
                        from components.functions_controle import salvar_arquivo
                        recebimento_path = salvar_arquivo(comprovante_recebimento, processo['Processo'], "recebimento")
                        
                        # Atualizar status
                        idx = df_filtrado[df_filtrado["Processo"] == processo["Processo"]].index[0]
                        st.session_state.df_editado_alvaras.loc[idx, "Status"] = "Finalizado"
                        st.session_state.df_editado_alvaras.loc[idx, "Comprovante Recebimento"] = recebimento_path
                        st.session_state.df_editado_alvaras.loc[idx, "Data Finalização"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                        st.session_state.df_editado_alvaras.loc[idx, "Finalizado Por"] = st.session_state.get("usuario", "Sistema")
                        
                        st.success("✅ Processo finalizado!")
                        st.rerun()

def interface_visualizar_alvara(df, alvara_id, perfil_usuario):
    """Interface para visualizar dados de um alvará"""
    
    # Verificar se o alvará existe
    linha_processo = df[df["ID"].astype(str) == str(alvara_id)]
    
    if len(linha_processo) == 0:
        st.error(f"❌ Alvará com ID {alvara_id} não encontrado")
        return
    
    linha_processo = linha_processo.iloc[0]
    numero_processo = linha_processo.get("Processo", "N/A")
    status_atual = linha_processo.get("Status", "N/A")
    
    st.markdown(f"### 📋 Visualizando: {numero_processo} - {linha_processo['Parte']}")
    st.markdown(f"**ID:** {alvara_id} | **Status atual:** {status_atual}")
    
    # Mostrar informações básicas do processo em 3 colunas
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.write(f"**Pagamento:** {linha_processo.get('Pagamento', 'N/A')}")
        st.write(f"**Parte:** {linha_processo.get('Parte', 'N/A')}")
        st.write(f"**CPF/CNPJ:** {linha_processo.get('CPF/CNPJ', 'N/A')}")
    with col_info2:
        st.write(f"**Banco:** {linha_processo.get('Banco', 'N/A')}")
        st.write(f"**Agência:** {linha_processo.get('Agência', 'N/A')}")
        st.write(f"**Conta:** {linha_processo.get('Conta', 'N/A')}")
    with col_info3:
        st.write(f"**Cadastrado em:** {linha_processo.get('Data Cadastro', 'N/A')}")
        st.write(f"**Última atualização:** {linha_processo.get('Data Atualização', 'N/A')}")
        st.write(f"**Valor:** {linha_processo.get('Valor', 'N/A')}")
    
    # Adicionar mais visualizações de dados conforme necessário

def interface_edicao_processo(df, alvara_id, status_atual, perfil_usuario):
    """Interface de edição baseada no status e perfil"""
    
    linha_processo_df = df[df["ID"].astype(str) == str(alvara_id)]
    
    if len(linha_processo_df) == 0:
        st.error(f"❌ Alvará com ID {alvara_id} não encontrado")
        return
    
    linha_processo = linha_processo_df.iloc[0]
    numero_processo = linha_processo.get("Processo", "N/A")
    
    st.markdown(f"### 📋 Editando: {numero_processo} - {linha_processo['Parte']}")
    st.markdown(f"**ID:** {alvara_id} | **Status atual:** {status_atual}")
    
    # Mostrar informações básicas do processo
    col_info1, col_info2, col_info3, col_info4 = st.columns(4)
    with col_info1:
        st.write(f"**Pagamento:** {linha_processo.get('Pagamento', 'N/A')}")
    with col_info2:
        st.write(f"**Banco:** {linha_processo.get('Banco', 'N/A')}")
    with col_info3:
        st.write(f"**Cadastrado em:** {linha_processo.get('Data Cadastro', 'N/A')}")
    with col_info4:
        st.write(f"**Cadastrado por:** {linha_processo.get('Cadastrado Por', 'N/A')}")
    
    st.markdown("----")
    
    # ETAPA 2: Cadastrado -> Anexar documentos (Cadastrador)
    if status_atual == "Cadastrado" and perfil_usuario == "Cadastrador":
        st.markdown("#### 📎 Anexar Documentos")
        
        col_doc1, col_doc2 = st.columns(2)
        
        with col_doc1:
            st.markdown("**📄 Comprovante da Conta**")
            comprovante_conta = st.file_uploader(
                "Anexar comprovante da conta:",
                type=["pdf", "jpg", "jpeg", "png"],
                key=f"comprovante_{numero_processo}"
            )
                    
        with col_doc2:
            st.markdown("**📄 PDF do Alvará**")
            pdf_alvara = st.file_uploader(
                "Anexar PDF do alvará:",
                type=["pdf"],
                key=f"pdf_{numero_processo}"
            )
            
        if comprovante_conta and pdf_alvara:
            st.success("✅ Ambos os documentos foram anexados!")
            
            if st.button("📤 Enviar para Financeiro", type="primary", key=f"enviar_fin_id_{alvara_id}"):
                # Salvar arquivos
                from components.functions_controle import salvar_arquivo, save_data_to_github_seguro
                comprovante_url = salvar_arquivo(comprovante_conta, numero_processo, "comprovante")
                pdf_url = salvar_arquivo(pdf_alvara, numero_processo, "alvara")
                
                if comprovante_url and pdf_url:
                    # Atualizar DataFrame
                    idx = df[df["ID"] == alvara_id].index[0]
                    st.session_state.df_editado_alvaras.loc[idx, "Status"] = "Enviado para o Financeiro"
                    st.session_state.df_editado_alvaras.loc[idx, "Comprovante Conta"] = comprovante_url
                    st.session_state.df_editado_alvaras.loc[idx, "PDF Alvará"] = pdf_url
                    st.session_state.df_editado_alvaras.loc[idx, "Data Envio Financeiro"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                    st.session_state.df_editado_alvaras.loc[idx, "Enviado Financeiro Por"] = st.session_state.get("usuario", "Sistema")
                    
                    # Salvar no GitHub
                    novo_sha = save_data_to_github_seguro(
                        st.session_state.df_editado_alvaras,
                        "lista_alvaras.csv",
                        st.session_state.file_sha_alvaras
                    )
                    st.session_state.file_sha_alvaras = novo_sha
                    
                    st.success("✅ Processo enviado para o Financeiro!")
                    st.session_state.show_alvara_dialog = False
                    st.rerun()
        elif comprovante_conta or pdf_alvara:
            st.warning("⚠️ Anexe ambos os documentos para prosseguir")
        else:
            st.info("📋 Anexe o comprovante da conta e o PDF do alvará")
    
    # ETAPA 3: Enviado para Financeiro -> Enviar para Rodrigo (Financeiro)
    elif status_atual == "Enviado para o Financeiro" and perfil_usuario == "Financeiro":
        st.markdown("#### 📤 Enviar para o Rodrigo")
        
        # Mostrar documentos anexados
        col_doc1, col_doc2 = st.columns(2)
        
        with col_doc1:
            st.markdown("**📄 Comprovante da Conta**")
            if linha_processo.get("Comprovante Conta"):
                from components.functions_controle import baixar_arquivo_github
                baixar_arquivo_github(linha_processo["Comprovante Conta"], "📎 Baixar Comprovante")
            else:
                st.warning("❌ Comprovante não anexado")
        
        with col_doc2:
            st.markdown("**📄 PDF do Alvará**")
            if linha_processo.get("PDF Alvará"):
                from components.functions_controle import baixar_arquivo_github
                baixar_arquivo_github(linha_processo["PDF Alvará"], "📎 Baixar PDF")
            else:
                st.warning("❌ PDF não anexado")
        
        st.markdown("**📋 Informações do envio:**")
        st.write(f"- Enviado em: {linha_processo.get('Data Envio Financeiro', 'N/A')}")
        st.write(f"- Enviado por: {linha_processo.get('Enviado Financeiro Por', 'N/A')}")
        
        if st.button("📤 Enviar para Rodrigo", type="primary", key=f"enviar_fin_id_{alvara_id}"):
            # Atualizar status
            from components.functions_controle import save_data_to_github_seguro
            idx = df[df["ID"] == alvara_id].index[0]
            st.session_state.df_editado_alvaras.loc[idx, "Status"] = "Financeiro - Enviado para Rodrigo"
            st.session_state.df_editado_alvaras.loc[idx, "Data Envio Rodrigo"] = datetime.now().strftime("%d/%m/%Y %H:%M")
            st.session_state.df_editado_alvaras.loc[idx, "Enviado Rodrigo Por"] = st.session_state.get("usuario", "Sistema")
            
            # Salvar no GitHub
            novo_sha = save_data_to_github_seguro(
                st.session_state.df_editado_alvaras,
                "lista_alvaras.csv",
                st.session_state.file_sha_alvaras
            )
            st.session_state.file_sha_alvaras = novo_sha
            
            st.success("✅ Processo enviado para o Rodrigo!")
            st.balloons()
            st.session_state.show_alvara_dialog = False
            st.rerun()
    
    # ETAPA 4: Financeiro - Enviado para Rodrigo -> Finalizar (Financeiro)
    elif status_atual == "Financeiro - Enviado para Rodrigo" and perfil_usuario == "Financeiro":
        st.markdown("#### ✅ Finalizar Processo")
        
        st.markdown("**📋 Informações do processo:**")
        st.write(f"- Enviado para Rodrigo em: {linha_processo.get('Data Envio Rodrigo', 'N/A')}")
        st.write(f"- Enviado por: {linha_processo.get('Enviado Rodrigo Por', 'N/A')}")
        
        # Mostrar comprovante de recebimento se já existe
        if linha_processo.get("Comprovante Recebimento"):
            st.success("✅ Comprovante de recebimento já anexado")
            from components.functions_controle import baixar_arquivo_github
            baixar_arquivo_github(linha_processo["Comprovante Recebimento"], "📎 Ver Comprovante")
        
        st.markdown("**📎 Anexar Comprovante de Recebimento:**")
        comprovante_recebimento = st.file_uploader(
            "Comprovante enviado pelo Rodrigo:",
            type=["pdf", "jpg", "jpeg", "png"],
            key=f"recebimento_{numero_processo}"
        )
        
        if comprovante_recebimento:
            if st.button("✅ Finalizar Processo", key=f"enviar_fin_id_{alvara_id}", type="primary"):
                # Salvar comprovante de recebimento
                from components.functions_controle import salvar_arquivo, save_data_to_github_seguro
                recebimento_url = salvar_arquivo(comprovante_recebimento, numero_processo, "recebimento")
                
                if recebimento_url:
                    # Atualizar status
                    idx = df[df["ID"] == alvara_id].index[0]
                    st.session_state.df_editado_alvaras.loc[idx, "Status"] = "Finalizado"
                    st.session_state.df_editado_alvaras.loc[idx, "Comprovante Recebimento"] = recebimento_url
                    st.session_state.df_editado_alvaras.loc[idx, "Data Finalização"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                    st.session_state.df_editado_alvaras.loc[idx, "Finalizado Por"] = st.session_state.get("usuario", "Sistema")
                    
                    # Salvar no GitHub
                    novo_sha = save_data_to_github_seguro(
                        st.session_state.df_editado_alvaras,
                        "lista_alvaras.csv",
                        st.session_state.file_sha_alvaras
                    )
                    st.session_state.file_sha_alvaras = novo_sha
                    
                    st.success("🎉 Processo finalizado com sucesso!")
                    st.balloons()
                    st.session_state.show_alvara_dialog = False
                    st.rerun()
        else:
            st.info("📋 Anexe o comprovante de recebimento para finalizar")
    
    # PROCESSO FINALIZADO - Apenas visualização
    elif status_atual == "Finalizado":
        st.markdown("#### 🎉 Processo Finalizado")
        st.success("✅ Este processo foi concluído com sucesso!")
        
        col_final1, col_final2 = st.columns(2)
        
        with col_final1:
            st.markdown("**📅 Datas importantes:**")
            st.write(f"- Cadastrado: {linha_processo.get('Data Cadastro', 'N/A')}")
            st.write(f"- Enviado Financeiro: {linha_processo.get('Data Envio Financeiro', 'N/A')}")
            st.write(f"- Enviado Rodrigo: {linha_processo.get('Data Envio Rodrigo', 'N/A')}")
            st.write(f"- Finalizado: {linha_processo.get('Data Finalização', 'N/A')}")
        
        with col_final2:
            st.markdown("**👥 Responsáveis:**")
            st.write(f"- Cadastrado por: {linha_processo.get('Cadastrado Por', 'N/A')}")
            st.write(f"- Enviado Financeiro por: {linha_processo.get('Enviado Financeiro Por', 'N/A')}")
            st.write(f"- Enviado Rodrigo por: {linha_processo.get('Enviado Rodrigo Por', 'N/A')}")
            st.write(f"- Finalizado por: {linha_processo.get('Finalizado Por', 'N/A')}")
        
        # Documentos anexados
        st.markdown("**📎 Documentos anexados:**")
        col_docs1, col_docs2, col_docs3 = st.columns(3)
        
        with col_docs1:
            if linha_processo.get("Comprovante Conta"):
                from components.functions_controle import baixar_arquivo_github
                baixar_arquivo_github(linha_processo["Comprovante Conta"], "📄 Comprovante Conta")
        
        with col_docs2:
            if linha_processo.get("PDF Alvará"):
                from components.functions_controle import baixar_arquivo_github
                baixar_arquivo_github(linha_processo["PDF Alvará"], "📄 PDF Alvará")
        
        with col_docs3:
            if linha_processo.get("Comprovante Recebimento"):
                from components.functions_controle import baixar_arquivo_github
                baixar_arquivo_github(linha_processo["Comprovante Recebimento"], "📄 Comprovante Recebimento")
    
    # ACESSO NEGADO
    else:
        st.error(f"❌ Seu perfil ({perfil_usuario}) não pode editar processos com status '{status_atual}'")
        
        if perfil_usuario == "Cadastrador":
            st.info("💡 Cadastradores só podem editar processos com status 'Cadastrado'")
        elif perfil_usuario == "Financeiro":
            st.info("💡 Financeiro só pode editar processos 'Enviado para o Financeiro' e 'Financeiro - Enviado para Rodrigo'")
    
def interface_cadastro_alvara(df, perfil_usuario):
    """Interface para cadastrar novos alvarás"""
    if perfil_usuario != "Cadastrador":
        st.warning("⚠️ Apenas Cadastradores podem criar novos alvarás")
        return
    
    # INICIALIZAR CONTADOR PARA RESET DO FORM
    if "form_reset_counter_alvaras" not in st.session_state:
        st.session_state.form_reset_counter_alvaras = 0
    
    # MOSTRAR LINHAS TEMPORÁRIAS PRIMEIRO (se existirem)
    if "preview_novas_linhas" in st.session_state and len(st.session_state["preview_novas_linhas"]) > 0:
        st.markdown("### 📋 Linhas Adicionadas (não salvas)")
        st.warning(f"⚠️ Você tem {len(st.session_state['preview_novas_linhas'])} linha(s) não salva(s)")
        
        # Mostrar tabela das linhas temporárias
        st.dataframe(st.session_state["preview_novas_linhas"], use_container_width=True)
        
        # Botão para salvar
        col_salvar, col_limpar = st.columns(2)
        
        with col_salvar:
            if st.button("💾 Salvar Todas as Linhas", type="primary"):
                from components.functions_controle import save_data_to_github_seguro
                
                # Mostrar mensagem de "salvando"
                with st.spinner("Salvando no GitHub..."):
                    novo_sha = save_data_to_github_seguro(
                        st.session_state.df_editado_alvaras,
                        "lista_alvaras.csv",
                        st.session_state.file_sha_alvaras
                    )
                
                if novo_sha and novo_sha != st.session_state.file_sha_alvaras:  # Se salvou com sucesso
                    st.session_state.file_sha_alvaras = novo_sha
                    del st.session_state["preview_novas_linhas"]
                    st.toast("✅ Todas as linhas foram salvas com sucesso!", icon="🎉")
                    st.rerun()
                else:
                    st.error("❌ Falha ao salvar. O SHA do arquivo não mudou.")
                
        with col_limpar:
            if st.button("🗑️ Descartar Linhas", type="secondary"):
                # Remover linhas do DataFrame
                num_linhas_remover = len(st.session_state["preview_novas_linhas"])
                st.session_state.df_editado_alvaras = st.session_state.df_editado_alvaras.iloc[:-num_linhas_remover]
                del st.session_state["preview_novas_linhas"]
                st.warning("🗑️ Linhas descartadas!")
                st.rerun()
        
        st.markdown("---")
    
    # FORMULÁRIO COM COLUNAS ESPECÍFICAS
    hints = {
        "Processo": "Ex: 0000000-00.0000.0.00.0000 (apenas números e traços/pontos)",
        "Parte": "Ex: ANDRE LEONARDO ANDRADE",
        "CPF": "Ex: 000.000.000-00 (apenas números e pontos/traços)",
        "Pagamento": "Ex: 1500.50 (apenas números e pontos para decimais)",
        "Observação pagamento": "Ex: Recebido em 15/01/2025 via PIX",
        "Órgão Judicial": "Ex: TRF 5ª REGIÃO, JFSE, TJSE",
        "Banco": "Ex: BRADESCO, CAIXA, BANCO DO BRASIL",
        "Honorários Sucumbenciais": "Marque se houver honorários sucumbenciais",
        "Observação Honorários": "Detalhes sobre os honorários sucumbenciais",
    }
    
    with st.form(f"adicionar_linha_form_alvaras_{st.session_state.form_reset_counter_alvaras}"):
        nova_linha = {}
        aviso_letras = False
        
        # DEFINIR COLUNAS PARA CADA LADO DO FORMULÁRIO
        colunas_esquerda = ["Processo", "Parte", "CPF", "Órgão Judicial", "Banco"]
        colunas_direita = ["Pagamento", "Observação pagamento", "Honorários Sucumbenciais", "Observação Honorários"]

        col_form_1, col_form_2 = st.columns(2)

        # --- COLUNA ESQUERDA ---
        with col_form_1:
            for col in colunas_esquerda:
                if col == "Processo":
                    valor_raw = st.text_input(
                        f"{col}",
                        key=f"input_alvaras_{col}_{st.session_state.form_reset_counter_alvaras}",
                        max_chars=50,
                        help=hints.get(col, ""),
                        placeholder="0000000-00.0000.0.00.0000"
                    )
                    if any(c.isalpha() for c in valor_raw):
                        aviso_letras = True
                    valor = ''.join([c for c in valor_raw if not c.isalpha()])
                
                elif col == "Parte":
                    valor = st.text_input(
                        f"{col}",
                        key=f"input_alvaras_{col}_{st.session_state.form_reset_counter_alvaras}",
                        max_chars=100,
                        help=hints.get(col, ""),
                        placeholder="NOME COMPLETO DA PARTE"
                    ).upper()

                elif col == "CPF":
                    valor_raw = st.text_input(
                        f"{col}",
                        key=f"input_alvaras_{col}_{st.session_state.form_reset_counter_alvaras}",
                        max_chars=14,
                        help=hints.get(col, ""),
                        placeholder="000.000.000-00"
                    )
                    if any(c.isalpha() for c in valor_raw):
                        aviso_letras = True
                    valor = ''.join([c for c in valor_raw if not c.isalpha()])

                elif col == "Órgão Judicial":
                    opcoes_orgao = ["", "TRF 5ª REGIÃO", "JFSE", "TJSE", "STJ", "STF", "Outro"]
                    orgao_selecionado = st.selectbox(
                        f"{col}",
                        opcoes_orgao,
                        key=f"input_alvaras_{col}_select_{st.session_state.form_reset_counter_alvaras}",
                        help=hints.get(col, "")
                    )
                    
                    if orgao_selecionado == "Outro":
                        valor = st.text_input(
                            "Especifique o órgão:",
                            key=f"input_alvaras_{col}_outro_{st.session_state.form_reset_counter_alvaras}",
                            max_chars=50,
                            placeholder="Digite o nome do órgão"
                        )
                    else:
                        valor = orgao_selecionado
                
                elif col == "Banco":
                    opcoes_banco = [
                        "", "BRADESCO", "CAIXA", "BANCO DO BRASIL", "ITAU", 
                        "SANTANDER", "BMG", "PAN", "INTER", "SAFRA", "Outro"
                    ]
                    banco_selecionado = st.selectbox(
                        f"{col}",
                        opcoes_banco,
                        key=f"input_alvaras_{col}_select_{st.session_state.form_reset_counter_alvaras}",
                        help=hints.get(col, "")
                    )
                    
                    if banco_selecionado == "Outro":
                        valor = st.text_input(
                            "Especifique o banco:",
                            key=f"input_alvaras_{col}_outro_{st.session_state.form_reset_counter_alvaras}",
                            max_chars=50,
                            placeholder="Digite o nome do banco"
                        )
                    else:
                        valor = banco_selecionado
                
                nova_linha[col] = valor

        # --- COLUNA DIREITA ---
        with col_form_2:
            for col in colunas_direita:
                if col == "Pagamento":
                    valor_raw = st.text_input(
                        f"{col}",
                        key=f"input_alvaras_{col}_{st.session_state.form_reset_counter_alvaras}",
                        max_chars=20,
                        help=hints.get(col, ""),
                        placeholder="1500.50"
                    )
                    valor_numerico = ''.join([c for c in valor_raw if c.isdigit() or c in '.,'])
                    if valor_numerico:
                        valor_numerico = valor_numerico.replace(',', '.')
                        try:
                            float(valor_numerico)
                            valor = f"R$ {valor_numerico}"
                        except ValueError:
                            valor = valor_numerico
                    else:
                        valor = ""
                    if any(c.isalpha() for c in valor_raw):
                        aviso_letras = True

                elif col == "Observação pagamento":
                    valor = st.text_area(
                        f"{col}",
                        key=f"input_alvaras_{col}_{st.session_state.form_reset_counter_alvaras}",
                        max_chars=200,
                        help=hints.get(col, ""),
                        placeholder="Detalhes sobre o pagamento...",
                        height=100
                    )
                
                elif col == "Honorários Sucumbenciais":
                    honorarios_marcado = st.checkbox(
                        "✅ Honorários Sucumbenciais",
                        key=f"input_alvaras_{col}_{st.session_state.form_reset_counter_alvaras}",
                        help=hints.get(col, ""),
                        value=False
                    )
                    valor = "Sim" if honorarios_marcado else "Não"
                
                elif col == "Observação Honorários":
                    valor = st.text_area(
                        f"{col}",
                        key=f"input_alvaras_{col}_{st.session_state.form_reset_counter_alvaras}",
                        max_chars=300,
                        help=hints.get(col, "Detalhes sobre os honorários sucumbenciais (opcional)"),
                        placeholder="Ex: Honorários de 10% sobre o valor da condenação...",
                        height=100
                    )
                
                nova_linha[col] = valor
        
        # Aviso sobre letras removidas
        if aviso_letras:
            st.warning("⚠️ Letras foram removidas automaticamente dos campos numéricos")

        # Validação antes de submeter (REMOVIDA)
        submitted = st.form_submit_button("📝 Adicionar Linha", type="primary", use_container_width=True)
        
    # Lógica de submissão
    if submitted:
        # Validações
        cpf_valor = nova_linha.get("CPF", "")
        cpf_numeros = ''.join([c for c in cpf_valor if c.isdigit()])
        campos_obrigatorios = ["Processo", "Parte", "CPF"]
        campos_vazios = [col for col in campos_obrigatorios if not nova_linha.get(col, "").strip()]
        
        if campos_vazios:
            st.error(f"❌ Preencha os campos obrigatórios: {', '.join(campos_vazios)}")
        elif cpf_valor and len(cpf_numeros) != 11:
            st.error("❌ CPF deve conter exatamente 11 números.")
        else:
            # GERAR ID ÚNICO PARA NOVA LINHA
            from components.functions_controle import gerar_id_unico
            novo_id = gerar_id_unico(st.session_state.df_editado_alvaras, "ID")
            nova_linha["ID"] = novo_id
            
            # ADICIONAR CAMPOS DE CONTROLE
            nova_linha["Status"] = "Cadastrado"
            nova_linha["Data Cadastro"] = datetime.now().strftime("%d/%m/%Y %H:%M")
            nova_linha["Cadastrado Por"] = st.session_state.get("usuario", "Sistema")
            
            # Preencher campos vazios para todas as outras colunas do DataFrame
            for col in df.columns:
                if col not in nova_linha:
                    nova_linha[col] = ""
            
            # Adicionar campos vazios para próximas etapas
            linha_controle = inicializar_linha_vazia()
            nova_linha.update(linha_controle)
            nova_linha["Status"] = "Cadastrado"  # Sobrescrever status
            nova_linha["Data Cadastro"] = datetime.now().strftime("%d/%m/%Y %H:%M")
            nova_linha["Cadastrado Por"] = st.session_state.get("usuario", "Sistema")
            
            # Adicionar linha ao DataFrame
            st.session_state.df_editado_alvaras = pd.concat(
                [st.session_state.df_editado_alvaras, pd.DataFrame([nova_linha])],
                ignore_index=True
            )
            
            # Guardar preview
            if "preview_novas_linhas" not in st.session_state:
                st.session_state["preview_novas_linhas"] = pd.DataFrame()
            st.session_state["preview_novas_linhas"] = pd.concat(
                [st.session_state["preview_novas_linhas"], pd.DataFrame([nova_linha])],
                ignore_index=True
            )
            
            # LIMPAR CAMPOS
            from components.functions_controle import limpar_campos_formulario
            limpar_campos_formulario("input_alvaras_")
            
            st.session_state.form_reset_counter_alvaras += 1
            st.toast("✅ Linha adicionada! Salve para persistir os dados.", icon="👍")
            st.rerun()

def interface_visualizar_dados(df):
    """Interface aprimorada para visualizar e gerenciar dados com paginação."""
    
    if len(df) == 0:
        st.info("ℹ️ Não há dados para visualizar.")
        return

    # Estatísticas gerais
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    with col_stat1:
        st.metric("Total de Processos", len(df))
    with col_stat2:
        finalizados = len(df[df["Status"] == "Finalizado"]) if "Status" in df.columns else "N/A"
        st.metric("Finalizados", finalizados)
    with col_stat3:
        pendentes = len(df[df["Status"] != "Finalizado"]) if "Status" in df.columns else "N/A"
        st.metric("Pendentes", pendentes)
    with col_stat4:
        if "Data Cadastro" in df.columns:
            hoje = datetime.now().strftime("%d/%m/%Y")
            df_temp = df.copy()
            df_temp["Data Cadastro"] = df_temp["Data Cadastro"].astype(str)
            hoje_count = len(df_temp[df_temp["Data Cadastro"].str.contains(hoje, na=False)])
            st.metric("Cadastrados Hoje", hoje_count)
        else:
            st.metric("Cadastrados Hoje", "N/A")

    # Filtros para visualização
    st.markdown("### 🔍 Filtros")
    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
    
    with col_filtro1:
        status_unicos = df["Status"].dropna().unique() if "Status" in df.columns else []
        status_filtro = st.multiselect("Status:", options=status_unicos, default=status_unicos)
        
    with col_filtro2:
        usuarios_unicos = df["Cadastrado Por"].dropna().unique() if "Cadastrado Por" in df.columns else []
        usuario_filtro = st.multiselect("Cadastrado Por:", options=usuarios_unicos, default=usuarios_unicos)
    
    with col_filtro3:
        # a) Alinhamento vertical do checkbox
        st.markdown("<br>", unsafe_allow_html=True)
        mostrar_todas_colunas = st.checkbox("Mostrar todas as colunas", value=False)
    
    # Aplicar filtros
    df_visualizado = df.copy()
    if status_filtro and "Status" in df.columns:
        df_visualizado = df_visualizado[df_visualizado["Status"].isin(status_filtro)]
    if usuario_filtro and "Cadastrado Por" in df.columns:
        df_visualizado = df_visualizado[df_visualizado["Cadastrado Por"].isin(usuario_filtro)]
    
    # Selecionar colunas para exibir
    if mostrar_todas_colunas:
        colunas_exibir = df_visualizado.columns.tolist()
    else:
        colunas_principais = ["Processo", "Parte", "Pagamento", "Status", "Data Cadastro", "Cadastrado Por"]
        colunas_exibir = [col for col in colunas_principais if col in df_visualizado.columns]
    
    st.markdown("---")

    # d) Botões de download acima da tabela
    if not df_visualizado.empty:
        from io import BytesIO
        
        # Preparar dados para download
        csv_data = df_visualizado.to_csv(index=False, sep=';').encode('utf-8')
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_visualizado.to_excel(writer, index=False, sheet_name='Dados')
        excel_data = output.getvalue()

        col_down1, col_down2, _ = st.columns([1.5, 1.5, 7])
        with col_down1:
            st.download_button(
                label="📥 Baixar CSV",
                data=csv_data,
                file_name=f"dados_alvaras_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )
        with col_down2:
            st.download_button(
                label="📊 Baixar Excel",
                data=excel_data,
                file_name=f"dados_alvaras_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    # b) Lógica de Paginação
    if "current_page_visualizar" not in st.session_state:
        st.session_state.current_page_visualizar = 1
    
    items_per_page = 10
    total_registros = len(df_visualizado)
    total_pages = math.ceil(total_registros / items_per_page) if items_per_page > 0 else 1
    
    start_idx = (st.session_state.current_page_visualizar - 1) * items_per_page
    end_idx = start_idx + items_per_page
    df_paginado = df_visualizado.iloc[start_idx:end_idx]

    # Exibir dados
    st.markdown(f"### 📊 Dados ({total_registros} registros encontrados)")
    
    if not df_paginado.empty:
        # b) Contador de itens
        st.markdown(f'<p style="font-size: small; color: steelblue;">Mostrando {start_idx+1} a {min(end_idx, total_registros)} de {total_registros} registros</p>', unsafe_allow_html=True)
        
        # e) Exibir tabela sem altura fixa
        st.dataframe(
            df_paginado[colunas_exibir],
            use_container_width=True
        )
        
        # b) Controles de paginação
        st.markdown("---")
        col_nav1, col_nav2, col_nav3 = st.columns([3, 2, 3])
        with col_nav1:
            if st.session_state.current_page_visualizar > 1:
                if st.button("<< Primeira", key="viz_primeira"): st.session_state.current_page_visualizar = 1; st.rerun()
                if st.button("< Anterior", key="viz_anterior"): st.session_state.current_page_visualizar -= 1; st.rerun()
        with col_nav2:
            st.write(f"Página {st.session_state.current_page_visualizar} de {total_pages}")
        with col_nav3:
            if st.session_state.current_page_visualizar < total_pages:
                if st.button("Próxima >", key="viz_proxima"): st.session_state.current_page_visualizar += 1; st.rerun()
                if st.button("Última >>", key="viz_ultima"): st.session_state.current_page_visualizar = total_pages; st.rerun()
    else:
        st.info("Nenhum registro encontrado com os filtros aplicados.")
