# components/funcoes_rpv.py
import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime

# =====================================
# CONFIGURAÇÕES DE PERFIS - RPV
# =====================================

PERFIS_RPV = {
    "Cadastrador": ["Enviado"],  
    "Jurídico": ["Enviado", "Certidão anexa"],
    "Financeiro": ["Enviado", "Certidão anexa", "Enviado para Rodrigo", "Finalizado"]
}

STATUS_ETAPAS_RPV = {
    1: "Enviado",              # ← Era "Cadastrado", agora começa em "Enviado"
    2: "Certidão anexa", 
    3: "Enviado para Rodrigo",
    4: "Finalizado"
}

# =====================================
# FUNÇÕES DE PERFIL E CONTROLE - RPV
# =====================================

def verificar_perfil_usuario_rpv():
    """Verifica o perfil do usuário logado para RPV"""
    usuario_atual = st.session_state.get("usuario", "")
    
    # USUÁRIOS LOCAIS TEMPORÁRIOS PARA TESTE RPV
    perfis_usuarios_rpv = {
        "cadastrador": "Cadastrador",
        "juridico": "Jurídico",
        "financeiro": "Financeiro", 
        "admin": "Cadastrador"
    }
    
    return perfis_usuarios_rpv.get(usuario_atual, "Cadastrador")

def pode_editar_status_rpv(status_atual, perfil_usuario):
    """Verifica se o usuário pode editar determinado status RPV"""
    return status_atual in PERFIS_RPV.get(perfil_usuario, [])

def obter_colunas_controle_rpv():
    """Retorna lista das colunas de controle do fluxo RPV"""
    return [
        "Solicitar Certidão", "Status", "Data Cadastro", "Cadastrado Por", 
        "PDF RPV", "Data Envio", "Enviado Por",
        "Certidão Anexada", "Data Certidão", "Anexado Certidão Por",
        "Data Envio Rodrigo", "Enviado Rodrigo Por", 
        "Comprovante Saque", "Comprovante Pagamento", "Valor Final Escritório",
        "Data Finalização", "Finalizado Por"
    ]

def inicializar_linha_vazia_rpv():
    """Retorna dicionário com campos vazios para nova linha RPV"""
    campos_controle = obter_colunas_controle_rpv()
    linha_vazia = {}
    
    for campo in campos_controle:
        linha_vazia[campo] = ""
    
    return linha_vazia

# =====================================
# FUNÇÕES DE INTERFACE E AÇÕES - RPV
# =====================================

def interface_lista_rpv(df, perfil_usuario):
    """Lista de RPVs com botão Abrir para ações"""
    st.subheader("📊 Lista de RPVs")
    
    # Filtros - agora em 4 colunas
    col_filtro1, col_filtro2, col_filtro3, col_filtro4 = st.columns(4)
    
    with col_filtro1:
        if "Status" in df.columns:
            status_filtro = st.selectbox(
                "🔍 Filtrar por Status:",
                ["Todos"] + list(STATUS_ETAPAS_RPV.values())
            )
        else:
            status_filtro = "Todos"
    
    with col_filtro2:
        # Filtro por Nome (Beneficiário)
        nome_filtro = st.text_input(
            "🔍 Filtrar por Nome:",
            placeholder="Digite o nome do beneficiário..."
        )
    
    with col_filtro3:
        # Filtro por CPF
        cpf_filtro = st.text_input(
            "🔍 Filtrar por CPF:",
            placeholder="Digite o CPF..."
        )
    
    with col_filtro4:
        mostrar_solicitar = st.checkbox("Mostrar apenas com solicitação de certidão", value=False)
    
    # Seletor de quantidade de registros
    col_qtd1, col_qtd2 = st.columns([1, 3])
    with col_qtd1:
        qtd_mostrar = st.selectbox(
            "📊 Mostrar:",
            options=[20, 50, "Todos"],
            index=0
        )
    
    # Aplicar filtros
    df_filtrado = df.copy()
    
    if status_filtro != "Todos" and "Status" in df.columns:
        df_filtrado = df_filtrado[df_filtrado["Status"] == status_filtro]
    
    # Filtro por nome (beneficiário)
    if nome_filtro:
        df_filtrado = df_filtrado[df_filtrado["Beneficiário"].astype(str).str.contains(nome_filtro, case=False, na=False)]
    
    # Filtro por CPF
    if cpf_filtro:
        df_filtrado = df_filtrado[df_filtrado["CPF"].astype(str).str.contains(cpf_filtro, case=False, na=False)]
    
    if mostrar_solicitar:
        df_filtrado = df_filtrado[df_filtrado["Solicitar Certidão"] == "Sim"]
    
    # Ordenar por data de cadastro mais novo (se a coluna existir)
    if "Data Cadastro" in df_filtrado.columns:
        # Converter para datetime para ordenação correta
        df_filtrado = df_filtrado.copy()
        df_filtrado["Data Cadastro Temp"] = pd.to_datetime(df_filtrado["Data Cadastro"], format="%d/%m/%Y %H:%M", errors="coerce")
        df_filtrado = df_filtrado.sort_values("Data Cadastro Temp", ascending=False, na_position="last")
        df_filtrado = df_filtrado.drop("Data Cadastro Temp", axis=1)
    else:
        # Se não houver data de cadastro, ordenar pelo índice inverso (mais recentes primeiro)
        df_filtrado = df_filtrado.sort_index(ascending=False)
    
    # FORÇAR REGENERAÇÃO DE IDs VÁLIDOS E ÚNICOS
    df_trabalho = df_filtrado.copy()
    
    for idx in df_trabalho.index:
        id_atual = df_trabalho.loc[idx, "ID"]
        
        # Se ID é inválido, gerar novo baseado no índice
        if (pd.isna(id_atual) or 
            str(id_atual).strip() == "" or 
            str(id_atual) == "nan" or
            "E+" in str(id_atual) or  # Notação científica
            "e+" in str(id_atual).lower()):
            
            # Gerar ID único baseado no índice + hash do processo
            processo_hash = hash(str(df_trabalho.loc[idx, "Processo"]))
            novo_id = f"{idx}_{abs(processo_hash)}"
            df_trabalho.loc[idx, "ID"] = novo_id
            # Atualizar também no DataFrame principal
            st.session_state.df_editado_rpv.loc[idx, "ID"] = novo_id
    
    # Aplicar limite de quantidade
    total_registros = len(df_trabalho)
    if qtd_mostrar != "Todos":
        df_trabalho = df_trabalho.head(qtd_mostrar)
    
    # Botão para salvar alterações (se houver linhas pendentes)
    if "preview_novas_linhas_rpv" in st.session_state and len(st.session_state["preview_novas_linhas_rpv"]) > 0:
        st.warning(f"⚠️ Você tem {len(st.session_state['preview_novas_linhas_rpv'])} linha(s) não salva(s)")
        if st.button("💾 Salvar Alterações", type="primary"):
            from components.functions_controle import save_data_to_github_seguro
            novo_sha = save_data_to_github_seguro(
                st.session_state.df_editado_rpv,
                "lista_rpv.csv",
                "file_sha_rpv"
            )
            if novo_sha:
                st.session_state.file_sha_rpv = novo_sha
            del st.session_state["preview_novas_linhas_rpv"]
            st.rerun()
    
    # Exibir lista com botão Abrir
    if len(df_trabalho) > 0:
        # Mostrar informações de quantidade
        if qtd_mostrar != "Todos":
            st.markdown(f"### 📋 Lista (mostrando {len(df_trabalho)} de {total_registros} RPVs)")
        else:
            st.markdown(f"### 📋 Lista ({len(df_trabalho)} RPVs)")
        
        # Cabeçalhos das colunas
        col_abrir, col_parte, col_cpf, col_status, col_data = st.columns([1, 2.5, 1.5, 2, 2])
        
        with col_abrir:
            st.markdown("**Ação**")
        with col_parte:
            st.markdown("**Parte**")
        with col_cpf:
            st.markdown("**CPF**")
        with col_status:
            st.markdown("**Status**")
        with col_data:
            st.markdown("**Data Cadastro**")
        
        st.markdown("---")  # Linha separadora
        
        for idx, processo in df_trabalho.iterrows():
            col_abrir, col_parte, col_cpf, col_status, col_data = st.columns([1, 2.5, 1.5, 2, 2])
            
            # USAR ID SEGURO E ÚNICO
            rpv_id = processo.get("ID", f"temp_{idx}")
            
            # Garantir que ID seja string limpa (sem caracteres especiais)
            rpv_id_clean = str(rpv_id).replace(".", "_").replace(",", "_").replace(" ", "_").replace("+", "plus").replace("-", "_")
            
            with col_abrir:
                if st.button(f"🔓 Abrir", key=f"abrir_rpv_id_{rpv_id_clean}"):
                    st.session_state['rpv_aberto'] = rpv_id  # Salvar ID original
                    st.rerun()
            
            with col_parte:
                st.write(f"**{processo.get('Beneficiário', 'N/A')}**")
            
            with col_cpf:
                cpf = processo.get('CPF', 'N/A')
                if cpf and cpf != 'N/A' and str(cpf).strip():
                    st.write(cpf)
                else:
                    st.write('-')
            
            with col_status:
                # Colorir status
                status_atual = processo.get('Status', 'N/A')
                if status_atual == 'Enviado':
                    st.write(f"🟡 {status_atual}")
                elif status_atual == 'Certidão anexa':
                    st.write(f"🟠 {status_atual}")
                elif status_atual == 'Enviado para Rodrigo':
                    st.write(f"🔵 {status_atual}")
                elif status_atual == 'Finalizado':
                    st.write(f"🟢 {status_atual}")
                else:
                    st.write(status_atual)
            
            with col_data:
                data_cadastro = processo.get('Data Cadastro', 'N/A')
                if data_cadastro and data_cadastro != 'N/A':
                    st.write(data_cadastro)
                else:
                    st.write('-')
        
        # Interface de edição se processo foi aberto
        if 'rpv_aberto' in st.session_state:
            st.markdown("---")
            rpv_id = st.session_state['rpv_aberto']
            
            # Botão para fechar
            if st.button("❌ Fechar", key="fechar_rpv"):
                del st.session_state['rpv_aberto']
                st.rerun()
            
            # Buscar dados da RPV POR ID (convertendo para string)
            linha_processo = df[df["ID"].astype(str) == str(rpv_id)]
            if len(linha_processo) > 0:
                linha_processo = linha_processo.iloc[0]
                numero_processo = linha_processo.get("Processo", "N/A")
                status_atual = linha_processo.get("Status", "")
                
                # Interface baseada no status e perfil
                interface_edicao_rpv(df, rpv_id, status_atual, perfil_usuario)
            else:
                st.error("❌ RPV não encontrada")
    else:
        st.info("Nenhuma RPV encontrada com os filtros aplicados")

def interface_edicao_rpv(df, rpv_id, status_atual, perfil_usuario):
    """Interface de edição de RPV baseada no status e perfil"""
    
    linha_processo_df = df[df["ID"].astype(str) == str(rpv_id)]
    
    if len(linha_processo_df) == 0:
        st.error(f"❌ RPV com ID {rpv_id} não encontrada")
        return
    
    linha_processo = linha_processo_df.iloc[0]
    numero_processo = linha_processo.get("Processo", "N/A")
    
    st.markdown(f"### 📋 Editando RPV: {numero_processo} - {linha_processo['Beneficiário']}")
    st.markdown(f"**ID:** {rpv_id} | **Status atual:** {status_atual}")
    
    # Mostrar informações básicas do processo
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.write(f"**Valor RPV:** {linha_processo.get('Valor RPV', 'N/A')}")
    with col_info2:
        st.write(f"**CPF:** {linha_processo.get('CPF', 'N/A')}")
    with col_info3:
        st.write(f"**Data Cadastro:** {linha_processo.get('Data Cadastro', 'N/A')}")
    
    st.markdown("---")
    
    # ETAPA 1: Enviado -> Anexar PDF da RPV (Cadastrador)
    if status_atual == "Enviado" and perfil_usuario in ["Cadastrador"]:
        st.markdown("#### 📎 Anexar PDF da RPV")
        
        pdf_rpv = st.file_uploader(
            "Anexar PDF da RPV:",
            type=["pdf"],
            key=f"pdf_rpv_{rpv_id}"
        )
        
        # Mostrar se já existe
        if linha_processo.get("PDF RPV"):
            from components.functions_controle import baixar_arquivo_github
            st.info("✅ PDF da RPV já anexado anteriormente")
            baixar_arquivo_github(linha_processo["PDF RPV"], "PDF da RPV")
        
        if pdf_rpv:
            st.success("✅ PDF da RPV anexado!")
            
            if st.button("📤 Enviar PDF da RPV", type="primary", key=f"enviar_pdf_rpv_{rpv_id}"):
                # Salvar arquivo
                from components.functions_controle import salvar_arquivo
                pdf_url = salvar_arquivo(pdf_rpv, numero_processo, "rpv")
                
                if pdf_url:
                    # Atualizar DataFrame
                    idx = df[df["ID"] == rpv_id].index[0]
                    st.session_state.df_editado_rpv.loc[idx, "PDF RPV"] = pdf_url
                    st.session_state.df_editado_rpv.loc[idx, "Data Envio"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                    st.session_state.df_editado_rpv.loc[idx, "Enviado Por"] = st.session_state.get("usuario", "Sistema")
                    
                    # Salvar no GitHub
                    from components.functions_controle import save_data_to_github_seguro
                    novo_sha = save_data_to_github_seguro(
                        st.session_state.df_editado_rpv,
                        "lista_rpv.csv",
                        "file_sha_rpv"
                    )
                    st.session_state.file_sha_rpv = novo_sha
                    
                    st.success("✅ PDF da RPV enviado com sucesso!")
                    st.rerun()
    
    # ETAPA 2: Anexar Certidão (Jurídico)
    if status_atual in ["Enviado", "Certidão anexa"] and perfil_usuario in ["Jurídico", "Financeiro"]:
        st.markdown("#### 📑 Anexar Certidão")
        
        certidao_arquivo = st.file_uploader(
            "Anexar Certidão:",
            type=["pdf", "jpg", "jpeg", "png"],
            key=f"certidao_{rpv_id}"
        )
        
        # Mostrar se já existe
        if linha_processo.get("Certidão Anexada"):
            from components.functions_controle import baixar_arquivo_github
            st.info("✅ Certidão já anexada anteriormente")
            baixar_arquivo_github(linha_processo["Certidão Anexada"], "Certidão")
        
        if certidao_arquivo:
            st.success("✅ Certidão anexada!")
            
            if st.button("📤 Salvar Certidão", type="primary", key=f"salvar_certidao_{rpv_id}"):
                # Salvar arquivo
                from components.functions_controle import salvar_arquivo
                certidao_url = salvar_arquivo(certidao_arquivo, numero_processo, "certidao")
                
                if certidao_url:
                    # Atualizar DataFrame
                    idx = df[df["ID"] == rpv_id].index[0]
                    st.session_state.df_editado_rpv.loc[idx, "Status"] = "Certidão anexa"
                    st.session_state.df_editado_rpv.loc[idx, "Certidão Anexada"] = certidao_url
                    st.session_state.df_editado_rpv.loc[idx, "Data Certidão"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                    st.session_state.df_editado_rpv.loc[idx, "Anexado Certidão Por"] = st.session_state.get("usuario", "Sistema")
                    
                    # Salvar no GitHub
                    from components.functions_controle import save_data_to_github_seguro
                    novo_sha = save_data_to_github_seguro(
                        st.session_state.df_editado_rpv,
                        "lista_rpv.csv",
                        "file_sha_rpv"
                    )
                    st.session_state.file_sha_rpv = novo_sha
                    
                    st.success("✅ Certidão salva com sucesso!")
                    st.rerun()
    
    # ETAPA 3: Enviar para Rodrigo (Financeiro)
    if status_atual == "Certidão anexa" and perfil_usuario == "Financeiro":
        st.markdown("#### 📤 Enviar para Rodrigo")
        
        if st.button("📤 Enviar para Rodrigo", type="primary", key=f"enviar_rodrigo_{rpv_id}"):
            # Atualizar DataFrame
            idx = df[df["ID"] == rpv_id].index[0]
            st.session_state.df_editado_rpv.loc[idx, "Status"] = "Enviado para Rodrigo"
            st.session_state.df_editado_rpv.loc[idx, "Data Envio Rodrigo"] = datetime.now().strftime("%d/%m/%Y %H:%M")
            st.session_state.df_editado_rpv.loc[idx, "Enviado Rodrigo Por"] = st.session_state.get("usuario", "Sistema")
            
            # Salvar no GitHub
            from components.functions_controle import save_data_to_github_seguro
            novo_sha = save_data_to_github_seguro(
                st.session_state.df_editado_rpv,
                "lista_rpv.csv",
                "file_sha_rpv"
            )
            st.session_state.file_sha_rpv = novo_sha
            
            st.success("✅ RPV enviada para Rodrigo com sucesso!")
            st.rerun()
    
    # ETAPA 4: Finalizar (Financeiro)
    if status_atual == "Enviado para Rodrigo" and perfil_usuario == "Financeiro":
        st.markdown("#### ✅ Finalizar RPV")
        
        col_anexo1, col_anexo2 = st.columns(2)
        
        with col_anexo1:
            st.markdown("**📄 Comprovante de Saque**")
            comprovante_saque = st.file_uploader(
                "Anexar comprovante de saque:",
                type=["pdf", "jpg", "jpeg", "png"],
                key=f"saque_{rpv_id}"
            )
            
            # Mostrar se já existe
            if linha_processo.get("Comprovante Saque"):
                from components.functions_controle import baixar_arquivo_github
                st.info("✅ Comprovante de saque já anexado")
                baixar_arquivo_github(linha_processo["Comprovante Saque"], "Comprovante de Saque")
        
        with col_anexo2:
            st.markdown("**📄 Comprovante de Pagamento**")
            comprovante_pagamento = st.file_uploader(
                "Anexar comprovante de pagamento:",
                type=["pdf", "jpg", "jpeg", "png"],
                key=f"pagamento_{rpv_id}"
            )
            
            # Mostrar se já existe
            if linha_processo.get("Comprovante Pagamento"):
                from components.functions_controle import baixar_arquivo_github
                st.info("✅ Comprovante de pagamento já anexado")
                baixar_arquivo_github(linha_processo["Comprovante Pagamento"], "Comprovante de Pagamento")
        
        # Valor final do escritório
        valor_escritorio = st.text_input(
            "Valor Final Escritório (R$):",
            value=linha_processo.get("Valor Final Escritório", ""),
            key=f"valor_escritorio_{rpv_id}"
        )
        
        if (comprovante_saque or linha_processo.get("Comprovante Saque")) and \
           (comprovante_pagamento or linha_processo.get("Comprovante Pagamento")) and \
           valor_escritorio:
            
            if st.button("✅ Finalizar RPV", type="primary", key=f"finalizar_rpv_{rpv_id}"):
                # Atualizar DataFrame
                idx = df[df["ID"] == rpv_id].index[0]
                
                # Salvar arquivos se foram anexados
                from components.functions_controle import salvar_arquivo
                
                if comprovante_saque:
                    saque_url = salvar_arquivo(comprovante_saque, numero_processo, "saque")
                    if saque_url:
                        st.session_state.df_editado_rpv.loc[idx, "Comprovante Saque"] = saque_url
                
                if comprovante_pagamento:
                    pagamento_url = salvar_arquivo(comprovante_pagamento, numero_processo, "pagamento")
                    if pagamento_url:
                        st.session_state.df_editado_rpv.loc[idx, "Comprovante Pagamento"] = pagamento_url
                
                # Atualizar status e valores
                st.session_state.df_editado_rpv.loc[idx, "Status"] = "Finalizado"
                st.session_state.df_editado_rpv.loc[idx, "Valor Final Escritório"] = valor_escritorio
                st.session_state.df_editado_rpv.loc[idx, "Data Finalização"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                st.session_state.df_editado_rpv.loc[idx, "Finalizado Por"] = st.session_state.get("usuario", "Sistema")
                
                # Salvar no GitHub
                from components.functions_controle import save_data_to_github_seguro
                novo_sha = save_data_to_github_seguro(
                    st.session_state.df_editado_rpv,
                    "lista_rpv.csv",
                    "file_sha_rpv"
                )
                st.session_state.file_sha_rpv = novo_sha
                
                st.success("🎉 RPV finalizada com sucesso!")
                st.balloons()
                st.rerun()
        else:
            st.warning("⚠️ Preencha todos os campos para finalizar a RPV")

def interface_fluxo_trabalho_rpv(df, perfil_usuario):
    """Interface do fluxo de trabalho RPV com dashboards por perfil"""
    st.subheader("🔄 Fluxo de Trabalho - RPVs")
    
    # Dashboard geral
    col_dash1, col_dash2, col_dash3, col_dash4 = st.columns(4)
    
    # Contadores por status
    total_enviados = len(df[df["Status"] == "Enviado"]) if "Status" in df.columns else 0
    total_certidao = len(df[df["Status"] == "Certidão anexa"]) if "Status" in df.columns else 0
    total_rodrigo = len(df[df["Status"] == "Enviado para Rodrigo"]) if "Status" in df.columns else 0
    total_finalizados = len(df[df["Status"] == "Finalizado"]) if "Status" in df.columns else 0
    
    with col_dash1:
        st.metric("📝 Enviados", total_enviados)
    
    with col_dash2:
        st.metric("📑 Com Certidão", total_certidao)
    
    with col_dash3:
        st.metric("👨‍💼 Com Rodrigo", total_rodrigo)
    
    with col_dash4:
        st.metric("✅ Finalizados", total_finalizados)
    
    st.markdown("---")
    
    # Interface específica por perfil
    if perfil_usuario == "Cadastrador":
        interface_cadastrador_fluxo_rpv(df)
    elif perfil_usuario == "Jurídico":
        interface_juridico_fluxo_rpv(df)
    elif perfil_usuario == "Financeiro":
        interface_financeiro_fluxo_rpv(df)
    else:
        st.info("👤 Perfil não reconhecido para este fluxo")

def interface_cadastrador_fluxo_rpv(df):
    """Interface específica para Cadastradores no fluxo RPV"""
    st.markdown("### 👨‍💻 Ações do Cadastrador")
    
    # Processos que precisam de PDF
    if "Status" in df.columns:
        processos_pendentes = df[df["Status"] == "Enviado"]
        processos_sem_pdf = processos_pendentes[processos_pendentes["PDF RPV"].isna() | (processos_pendentes["PDF RPV"] == "")]
    else:
        processos_sem_pdf = pd.DataFrame()
    
    if len(processos_sem_pdf) > 0:
        st.markdown("#### 📎 RPVs aguardando anexação de PDF:")
        
        for _, processo in processos_sem_pdf.iterrows():
            with st.expander(f"📋 {processo['Processo']} - {processo['Beneficiário']}"):
                col_info, col_acao = st.columns([2, 1])
                
                with col_info:
                    st.write(f"**Beneficiário:** {processo['Beneficiário']}")
                    st.write(f"**Valor RPV:** {processo.get('Valor RPV', 'N/A')}")
                    st.write(f"**CPF:** {processo.get('CPF', 'N/A')}")
                    st.write(f"**Cadastrado em:** {processo.get('Data Cadastro', 'N/A')}")
                
                with col_acao:
                    if st.button(f"📎 Anexar PDF", key=f"anexar_pdf_{processo['ID']}"):
                        st.session_state['rpv_aberto'] = processo['ID']
                        st.rerun()
    else:
        st.success("✅ Todos os PDFs das RPVs foram anexados!")
    
    # Histórico de processos enviados
    if "Status" in df.columns:
        enviados = df[(df["Status"] != "Enviado") | (~df["PDF RPV"].isna() & (df["PDF RPV"] != ""))]
        if len(enviados) > 0:
            st.markdown("#### 📤 RPVs com PDF anexado:")
            st.dataframe(
                enviados[["Processo", "Beneficiário", "Data Envio", "Enviado Por"]],
                use_container_width=True
            )

def interface_juridico_fluxo_rpv(df):
    """Interface específica para o Jurídico no fluxo RPV"""
    st.markdown("### ⚖️ Ações do Jurídico")
    
    # Processos que solicitam certidão
    if "Solicitar Certidão" in df.columns and "Status" in df.columns:
        solicitados = df[(df["Solicitar Certidão"] == "Sim") & 
                         (df["Status"] == "Enviado") & 
                         (~df["PDF RPV"].isna() & df["PDF RPV"] != "")]
    else:
        solicitados = pd.DataFrame()
    
    if len(solicitados) > 0:
        st.markdown("#### 📑 RPVs com solicitação de certidão:")
        
        for _, processo in solicitados.iterrows():
            with st.expander(f"📋 {processo['Processo']} - {processo['Beneficiário']}"):
                col_info, col_docs, col_acao = st.columns([2, 1, 1])
                
                with col_info:
                    st.write(f"**Beneficiário:** {processo['Beneficiário']}")
                    st.write(f"**Valor RPV:** {processo.get('Valor RPV', 'N/A')}")
                    st.write(f"**CPF:** {processo.get('CPF', 'N/A')}")
                
                with col_docs:
                    st.markdown("**📎 PDF da RPV:**")
                    if processo.get("PDF RPV"):
                        from components.functions_controle import baixar_arquivo_github
                        baixar_arquivo_github(processo["PDF RPV"], "PDF da RPV")
                
                with col_acao:
                    if st.button(f"📑 Anexar Certidão", key=f"anexar_certidao_{processo['ID']}"):
                        st.session_state['rpv_aberto'] = processo['ID']
                        st.rerun()
    else:
        st.success("✅ Não há RPVs com solicitação de certidão pendente")
    
    # Histórico de certidões anexadas
    if "Status" in df.columns:
        certidoes_anexadas = df[df["Status"] == "Certidão anexa"]
        if len(certidoes_anexadas) > 0:
            st.markdown("#### 📤 Certidões anexadas recentemente:")
            st.dataframe(
                certidoes_anexadas[["Processo", "Beneficiário", "Data Certidão", "Anexado Certidão Por"]],
                use_container_width=True
            )

def interface_financeiro_fluxo_rpv(df):
    """Interface específica para o Financeiro no fluxo RPV"""
    st.markdown("### 💰 Ações do Financeiro")
    
    # Separar processos por etapa
    if "Status" in df.columns:
        com_certidao = df[df["Status"] == "Certidão anexa"]
        com_rodrigo = df[df["Status"] == "Enviado para Rodrigo"]
    else:
        com_certidao = pd.DataFrame()
        com_rodrigo = pd.DataFrame()
    
    # ETAPA 3: RPVs para enviar ao Rodrigo
    if len(com_certidao) > 0:
        st.markdown("#### 📤 Enviar para o Rodrigo:")
        
        for _, processo in com_certidao.iterrows():
            with st.expander(f"📋 {processo['Processo']} - {processo['Beneficiário']}"):
                col_info, col_docs, col_acao = st.columns([2, 1, 1])
                
                with col_info:
                    st.write(f"**Beneficiário:** {processo['Beneficiário']}")
                    st.write(f"**Valor RPV:** {processo.get('Valor RPV', 'N/A')}")
                    st.write(f"**CPF:** {processo.get('CPF', 'N/A')}")
                
                with col_docs:
                    st.markdown("**📎 Documentos:**")
                    if processo.get("PDF RPV"):
                        from components.functions_controle import baixar_arquivo_github
                        baixar_arquivo_github(processo["PDF RPV"], "PDF da RPV")
                    if processo.get("Certidão Anexada"):
                        from components.functions_controle import baixar_arquivo_github
                        baixar_arquivo_github(processo["Certidão Anexada"], "Certidão")
                
                with col_acao:
                    if st.button(f"📤 Enviar para Rodrigo", key=f"enviar_rodrigo_fluxo_{processo['ID']}"):
                        idx = df[df["ID"] == processo["ID"]].index[0]
                        st.session_state.df_editado_rpv.loc[idx, "Status"] = "Enviado para Rodrigo"
                        st.session_state.df_editado_rpv.loc[idx, "Data Envio Rodrigo"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                        st.session_state.df_editado_rpv.loc[idx, "Enviado Rodrigo Por"] = st.session_state.get("usuario", "Sistema")
                        
                        # Salvar no GitHub
                        from components.functions_controle import save_data_to_github_seguro
                        novo_sha = save_data_to_github_seguro(
                            st.session_state.df_editado_rpv,
                            "lista_rpv.csv",
                            "file_sha_rpv"
                        )
                        st.session_state.file_sha_rpv = novo_sha
                        
                        st.success("✅ RPV enviada para o Rodrigo!")
                        st.rerun()
    
    # ETAPA 4: RPVs para finalizar
    if len(com_rodrigo) > 0:
        st.markdown("#### ✅ Finalizar RPVs:")
        
        for _, processo in com_rodrigo.iterrows():
            with st.expander(f"📋 {processo['Processo']} - {processo['Beneficiário']} - FINALIZAR"):
                if st.button(f"✅ Finalizar RPV", key=f"ir_finalizar_{processo['ID']}"):
                    st.session_state['rpv_aberto'] = processo['ID']
                    st.rerun()
    
    # Mostrar processos finalizados recentemente
    if "Status" in df.columns:
        finalizados_recentes = df[df["Status"] == "Finalizado"].tail(5)
        if len(finalizados_recentes) > 0:
            st.markdown("#### 🎉 Últimos processos finalizados:")
            st.dataframe(
                finalizados_recentes[["Processo", "Beneficiário", "Valor Final Escritório", "Data Finalização"]],
                use_container_width=True
            )

def interface_visualizar_dados_rpv(df):
    """Interface para visualizar dados de RPVs com filtros e exportação"""
    st.subheader("📊 Visualização de Dados - RPVs")
    
    # Filtros
    with st.expander("🔍 Filtros", expanded=True):
        col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
        
        with col_filtro1:
            if "Status" in df.columns:
                status_filtro = st.multiselect(
                    "Status:",
                    ["Todos"] + list(STATUS_ETAPAS_RPV.values()),
                    default=["Todos"]
                )
            else:
                status_filtro = ["Todos"]
        
        with col_filtro2:
            if "Solicitar Certidão" in df.columns:
                certidao_filtro = st.radio(
                    "Solicitar Certidão:",
                    ["Todos", "Sim", "Não"],
                    horizontal=True
                )
            else:
                certidao_filtro = "Todos"
        
        with col_filtro3:
            pesquisa = st.text_input("Pesquisar por nome ou processo:")
    
    # Aplicar filtros
    df_filtrado = df.copy()
    
    # Filtro por status
    if "Todos" not in status_filtro and "Status" in df.columns:
        df_filtrado = df_filtrado[df_filtrado["Status"].isin(status_filtro)]
    
    # Filtro por solicitação de certidão
    if certidao_filtro != "Todos" and "Solicitar Certidão" in df.columns:
        df_filtrado = df_filtrado[df_filtrado["Solicitar Certidão"] == certidao_filtro]
    
    # Filtro por pesquisa
    if pesquisa:
        mask = df_filtrado.apply(lambda row: any(
            pesquisa.lower() in str(value).lower() for value in row.values
        ), axis=1)
        df_filtrado = df_filtrado[mask]
    
    # Exibir dados
    if len(df_filtrado) > 0:
        st.markdown(f"### 📋 Resultados ({len(df_filtrado)} RPVs)")
        st.dataframe(df_filtrado, use_container_width=True)
        
        # Exportar para CSV
        if st.button("📥 Exportar para CSV"):
            csv = df_filtrado.to_csv(index=False).encode('utf-8')
            b64 = base64.b64encode(csv).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="rpvs_exportadas.csv">Download CSV</a>'
            st.markdown(href, unsafe_allow_html=True)
    else:
        st.info("Nenhuma RPV encontrada com os filtros aplicados")

def interface_cadastro_rpv(df, perfil_usuario):
    """Interface para cadastrar novos RPVs"""
    if perfil_usuario != "Cadastrador":
        st.warning("⚠️ Apenas Cadastradores podem criar novos RPVs")
        return
    
    st.subheader("📝 Cadastrar Novo RPV")
    
    # Formulário de cadastro
    col1, col2 = st.columns(2)
    
    with col1:
        processo = st.text_input("Número do Processo:", key="input_rpv_Processo")
        beneficiario = st.text_input("Beneficiário:", key="input_rpv_Beneficiario")
        cpf = st.text_input("CPF:", key="input_rpv_CPF")
    
    with col2:
        valor_rpv = st.text_input("Valor da RPV (R$):", key="input_rpv_Valor_RPV")
        solicitar_certidao = st.selectbox(
            "Solicitar Certidão?",
            options=["Sim", "Não"],
            key="input_rpv_Solicitar_Certidao"
        )
    
    # Campo de observações
    observacoes = st.text_area("Observações:", key="input_rpv_Observacoes")
    
    # Botão para salvar
    if st.button("💾 Cadastrar RPV", type="primary"):
        if not processo or not beneficiario:
            st.error("❌ Preencha pelo menos o Processo e o Beneficiário")
            return
        
        # Formatar processo
        from components.functions_controle import formatar_processo
        processo_formatado = formatar_processo(processo)
        
        # Validar CPF
        from components.functions_controle import validar_cpf
        if cpf and not validar_cpf(cpf):
            st.warning("⚠️ CPF inválido. Verifique e tente novamente.")
            return
        
        # Verificar se processo já existe
        if "Processo" in df.columns and processo_formatado in df["Processo"].values:
            st.warning(f"⚠️ Processo {processo_formatado} já cadastrado")
            # Mostrar detalhes do processo existente
            proc_existente = df[df["Processo"] == processo_formatado].iloc[0]
            st.info(f"**Beneficiário:** {proc_existente.get('Beneficiário', 'N/A')}\n"
                    f"**Status:** {proc_existente.get('Status', 'N/A')}")
            return
        
        # Gerar ID único
        from components.functions_controle import gerar_id_unico
        novo_id = gerar_id_unico(df, "ID")
        
        # Criar nova linha
        nova_linha = {
            "ID": novo_id,
            "Processo": processo_formatado,
            "Beneficiário": beneficiario,
            "CPF": cpf,
            "Valor RPV": valor_rpv,
            "Observações": observacoes,
            "Solicitar Certidão": solicitar_certidao,
            "Status": "Enviado",  # Status inicial
            "Data Cadastro": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Cadastrado Por": st.session_state.get("usuario", "Sistema"),
        }
        
        # Inicializar campos de controle
        campos_controle = inicializar_linha_vazia_rpv()
        nova_linha.update(campos_controle)
        
        # Adicionar ao DataFrame
        if "df_editado_rpv" not in st.session_state:
            st.session_state.df_editado_rpv = df.copy()
        
        # Inicializar lista de novas linhas se não existir
        if "preview_novas_linhas_rpv" not in st.session_state:
            st.session_state["preview_novas_linhas_rpv"] = []
        
        # Adicionar à lista de linhas pendentes
        st.session_state["preview_novas_linhas_rpv"].append(nova_linha)
        
        # Adicionar ao DataFrame em memória
        nova_linha_df = pd.DataFrame([nova_linha])
        st.session_state.df_editado_rpv = pd.concat([st.session_state.df_editado_rpv, nova_linha_df], ignore_index=True)
        
        # Salvar no GitHub
        from components.functions_controle import save_data_to_github_seguro
        novo_sha = save_data_to_github_seguro(
            st.session_state.df_editado_rpv,
            "lista_rpv.csv",
            "file_sha_rpv"
        )
        
        if novo_sha:
            st.session_state.file_sha_rpv = novo_sha
            # Limpar lista de linhas pendentes
            st.session_state["preview_novas_linhas_rpv"] = []
            st.success(f"✅ RPV cadastrada com sucesso! ID: {novo_id}")
            # Limpar campos
            for key in st.session_state:
                if key.startswith("input_rpv_"):
                    st.session_state[key] = ""
            st.rerun()
        else:
            st.error("❌ Erro ao salvar RPV. Tente novamente.")
    
    # Mostrar RPVs pendentes de salvar
    if "preview_novas_linhas_rpv" in st.session_state and len(st.session_state["preview_novas_linhas_rpv"]) > 0:
        st.markdown("---")
        st.subheader(f"📋 RPVs Pendentes ({len(st.session_state['preview_novas_linhas_rpv'])})")
        
        for i, linha in enumerate(st.session_state["preview_novas_linhas_rpv"]):
            st.markdown(f"**RPV {i+1}:** {linha['Processo']} - {linha['Beneficiário']}")
        
        if st.button("💾 Salvar Todas Pendentes", type="primary"):
            from components.functions_controle import save_data_to_github_seguro
            novo_sha = save_data_to_github_seguro(
                st.session_state.df_editado_rpv,
                "lista_rpv.csv",
                "file_sha_rpv"
            )
            
            if novo_sha:
                st.session_state.file_sha_rpv = novo_sha
                st.session_state["preview_novas_linhas_rpv"] = []
                st.success("✅ Todas as RPVs pendentes foram salvas!")
                st.rerun()
            else:
                st.error("❌ Erro ao salvar RPVs pendentes. Tente novamente.")
