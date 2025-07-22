# components/funcoes_alvaras.py
import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime

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
    """Lista de alvarás com botão Abrir para ações"""
    st.subheader("📊 Lista de Alvarás")
    
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
        # Filtro por Processo
        processo_filtro = st.text_input(
            "🔍 Filtrar por Processo:",
            placeholder="Digite o número do processo..."
        )
    
    with col_filtro3:
        # Filtro por Nome (Parte)
        nome_filtro = st.text_input(
            "🔍 Filtrar por Nome:",
            placeholder="Digite o nome da parte..."
        )
    
    with col_filtro4:
        mostrar_apenas_meus = False
        if perfil_usuario == "Financeiro":
            mostrar_apenas_meus = st.checkbox("Mostrar apenas processos que posso editar")
    
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
    
    # Filtro por processo
    if processo_filtro:
        df_filtrado = df_filtrado[df_filtrado["Processo"].astype(str).str.contains(processo_filtro, case=False, na=False)]
    
    # Filtro por nome (parte)
    if nome_filtro:
        df_filtrado = df_filtrado[df_filtrado["Parte"].astype(str).str.contains(nome_filtro, case=False, na=False)]
    
    if mostrar_apenas_meus and perfil_usuario == "Financeiro":
        df_filtrado = df_filtrado[df_filtrado["Status"].isin([
            "Enviado para o Financeiro", 
            "Financeiro - Enviado para Chefe"
        ])]
    
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
            st.session_state.df_editado_alvaras.loc[idx, "ID"] = novo_id
    
    # Aplicar limite de quantidade
    total_registros = len(df_trabalho)
    if qtd_mostrar != "Todos":
        df_trabalho = df_trabalho.head(qtd_mostrar)
    
    # Botão para salvar alterações (se houver linhas pendentes)
    if "preview_novas_linhas" in st.session_state and len(st.session_state["preview_novas_linhas"]) > 0:
        st.warning(f"⚠️ Você tem {len(st.session_state['preview_novas_linhas'])} linha(s) não salva(s)")
        if st.button("💾 Salvar Alterações", type="primary"):
            from components.functions_controle import save_data_to_github_seguro
            novo_sha = save_data_to_github_seguro(
                st.session_state.df_editado_alvaras,
                "lista_alvaras.csv",
                "file_sha_alvaras"
            )
            if novo_sha:
                st.session_state.file_sha_alvaras = novo_sha
            del st.session_state["preview_novas_linhas"]
            st.rerun()
    
    # Exibir lista com botão Abrir
    if len(df_trabalho) > 0:
        # Mostrar informações de quantidade
        if qtd_mostrar != "Todos":
            st.markdown(f"### 📋 Lista (mostrando {len(df_trabalho)} de {total_registros} alvarás)")
        else:
            st.markdown(f"### 📋 Lista ({len(df_trabalho)} alvarás)")
        
        # Cabeçalhos das colunas
        col_abrir, col_processo, col_parte, col_valor, col_status = st.columns([1, 2, 2, 1.5, 2])
        
        with col_abrir:
            st.markdown("**Ação**")
        with col_processo:
            st.markdown("**Processo**")
        with col_parte:
            st.markdown("**Parte**")
        with col_valor:
            st.markdown("**Valor**")
        with col_status:
            st.markdown("**Status**")
        
        st.markdown("---")  # Linha separadora
        
        for idx, processo in df_trabalho.iterrows():
            col_abrir, col_processo, col_parte, col_valor, col_status = st.columns([1, 2, 2, 1.5, 2])
            
            # USAR ID SEGURO E ÚNICO
            alvara_id = processo.get("ID", f"temp_{idx}")
            
            # Garantir que ID seja string limpa (sem caracteres especiais)
            alvara_id_clean = str(alvara_id).replace(".", "_").replace(",", "_").replace(" ", "_").replace("+", "plus").replace("-", "_")
            
            with col_abrir:
                if st.button(f"🔓 Abrir", key=f"abrir_alvara_id_{alvara_id_clean}"):
                    st.session_state['processo_aberto'] = alvara_id  # Salvar ID original
                    st.rerun()
            
            with col_processo:
                st.write(f"**{processo.get('Processo', 'N/A')}**")
            
            with col_parte:
                st.write(processo.get('Parte', 'N/A'))
            
            with col_valor:
                # Exibir valor do pagamento
                valor = processo.get('Pagamento', 'N/A')
                if valor and valor != 'N/A':
                    st.write(valor)
                else:
                    st.write('-')
            
            with col_status:
                # Colorir status
                status_atual = processo.get('Status', 'N/A')
                if status_atual == 'Cadastrado':
                    st.write(f"🟡 {status_atual}")
                elif status_atual == 'Enviado para o Financeiro':
                    st.write(f"🟠 {status_atual}")
                elif status_atual == 'Financeiro - Enviado para Rodrigo':
                    st.write(f"🔵 {status_atual}")
                elif status_atual == 'Finalizado':
                    st.write(f"🟢 {status_atual}")
                else:
                    st.write(status_atual)
        
        # Interface de edição se processo foi aberto
        if 'processo_aberto' in st.session_state:
            st.markdown("---")
            alvara_id = st.session_state['processo_aberto']
            
            # Botão para fechar
            if st.button("❌ Fechar", key="fechar_processo"):
                del st.session_state['processo_aberto']
                st.rerun()
            
            # Buscar dados do alvará POR ID (convertendo para string)
            linha_processo = df[df["ID"].astype(str) == str(alvara_id)]
            if len(linha_processo) > 0:
                linha_processo = linha_processo.iloc[0]
                numero_processo = linha_processo.get("Processo", "N/A")
                status_atual = linha_processo.get("Status", "")
                
                # Interface baseada no status e perfil
                interface_edicao_processo(df, alvara_id, status_atual, perfil_usuario)
            else:
                st.error("❌ Alvará não encontrado")
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

def interface_fluxo_trabalho(df, perfil_usuario):
    """Interface do fluxo de trabalho com dashboards por perfil"""
    st.subheader("🔄 Fluxo de Trabalho - Alvarás")
    
    # Dashboard geral
    col_dash1, col_dash2, col_dash3, col_dash4 = st.columns(4)
    
    # Contadores por status
    total_cadastrados = len(df[df["Status"] == "Cadastrado"]) if "Status" in df.columns else 0
    total_financeiro = len(df[df["Status"] == "Enviado para o Financeiro"]) if "Status" in df.columns else 0
    total_Rodrigo = len(df[df["Status"] == "Financeiro - Enviado para Rodrigo"]) if "Status" in df.columns else 0
    total_finalizados = len(df[df["Status"] == "Finalizado"]) if "Status" in df.columns else 0
    
    with col_dash1:
        st.metric("📝 Cadastrados", total_cadastrados)
    
    with col_dash2:
        st.metric("📤 No Financeiro", total_financeiro)
    
    with col_dash3:
        st.metric("👨‍💼 Com Rodrigo", total_Rodrigo)
    
    with col_dash4:
        st.metric("✅ Finalizados", total_finalizados)
    
    st.markdown("---")
    
    # Interface específica por perfil
    if perfil_usuario == "Cadastrador":
        interface_cadastrador_fluxo(df)
    elif perfil_usuario == "Financeiro":
        interface_financeiro_fluxo(df)
    else:
        st.info("👤 Perfil não reconhecido para este fluxo")

def interface_cadastrador_fluxo(df):
    """Interface específica para Cadastradores no fluxo"""
    st.markdown("### 👨‍💻 Ações do Cadastrador")
    
    # Processos que precisam de documentos
    if "Status" in df.columns:
        processos_pendentes = df[df["Status"] == "Cadastrado"]
    else:
        processos_pendentes = pd.DataFrame()
    
    if len(processos_pendentes) > 0:
        st.markdown("#### 📎 Processos aguardando documentos:")
        
        for _, processo in processos_pendentes.iterrows():
            with st.expander(f"📋 {processo['Processo']} - {processo['Parte']}"):
                col_info, col_acao = st.columns([2, 1])
                
                with col_info:
                    st.write(f"**Parte:** {processo['Parte']}")
                    st.write(f"**Pagamento:** {processo.get('Pagamento', 'N/A')}")
                    st.write(f"**Banco:** {processo.get('Banco', 'N/A')}")
                    st.write(f"**Cadastrado em:** {processo.get('Data Cadastro', 'N/A')}")
                
                with col_acao:
                    if st.button(f"📎 Anexar Documentos", key=f"anexar_{processo['Processo']}"):
                        st.session_state['processo_anexar'] = processo['Processo']
                        st.rerun()
        
        # Interface de anexação se processo foi selecionado
        if 'processo_anexar' in st.session_state:
            st.markdown("---")
            interface_anexar_documentos(df, st.session_state['processo_anexar'])
    else:
        st.success("✅ Todos os processos cadastrados já têm documentos anexados!")
    
    # Histórico de processos enviados
    if "Status" in df.columns:
        enviados = df[df["Status"] == "Enviado para o Financeiro"]
        if len(enviados) > 0:
            st.markdown("#### 📤 Processos enviados para o Financeiro:")
            st.dataframe(
                enviados[["Processo", "Parte", "Data Envio Financeiro", "Enviado Financeiro Por"]],
                use_container_width=True
            )

def interface_financeiro_fluxo(df):
    """Interface específica para o Financeiro no fluxo"""
    st.markdown("### 💰 Ações do Financeiro")
    
    # Separar processos por etapa
    if "Status" in df.columns:
        aguardando_financeiro = df[df["Status"] == "Enviado para o Financeiro"]
        aguardando_finalizacao = df[df["Status"] == "Financeiro - Enviado para Rodrigo"]
    else:
        aguardando_financeiro = pd.DataFrame()
        aguardando_finalizacao = pd.DataFrame()
    
    # ETAPA 3: Processos para enviar ao Rodrigo
    if len(aguardando_financeiro) > 0:
        st.markdown("#### 📤 Enviar para o Rodrigo:")
        
        for _, processo in aguardando_financeiro.iterrows():
            with st.expander(f"📋 {processo['Processo']} - {processo['Parte']}"):
                col_info, col_docs, col_acao = st.columns([2, 1, 1])
                
                with col_info:
                    st.write(f"**Parte:** {processo['Parte']}")
                    st.write(f"**Pagamento:** {processo.get('Pagamento', 'N/A')}")
                    st.write(f"**Banco:** {processo.get('Banco', 'N/A')}")
                    st.write(f"**Enviado em:** {processo.get('Data Envio Financeiro', 'N/A')}")
                
                with col_docs:
                    st.markdown("**📎 Documentos:**")
                    if processo.get("Comprovante Conta"):
                        from components.functions_controle import baixar_arquivo_github
                        baixar_arquivo_github(processo["Comprovante Conta"], "Comprovante")
                    if processo.get("PDF Alvará"):
                        from components.functions_controle import baixar_arquivo_github
                        baixar_arquivo_github(processo["PDF Alvará"], "PDF Alvará")
                
                with col_acao:
                    if st.button(f"📤 Enviar para Rodrigo", key=f"enviar_Rodrigo_{processo['Processo']}"):
                        # Atualizar status
                        idx = df[df["Processo"] == processo["Processo"]].index[0]
                        st.session_state.df_editado_alvaras.loc[idx, "Status"] = "Financeiro - Enviado para Rodrigo"
                        st.session_state.df_editado_alvaras.loc[idx, "Data Envio Rodrigo"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                        st.session_state.df_editado_alvaras.loc[idx, "Enviado Rodrigo Por"] = st.session_state.get("usuario", "Sistema")
                        
                        # Salvar no GitHub
                        from components.functions_controle import save_data_to_github
                        novo_sha = save_data_to_github(
                            st.session_state.df_editado_alvaras,
                            "lista_alvaras.csv",
                            st.session_state.file_sha_alvaras
                        )
                        st.session_state.file_sha_alvaras = novo_sha
                        
                        st.success("✅ Processo enviado para o Rodrigo!")
                        st.rerun()
    
    # ETAPA 4: Processos para finalizar
    if len(aguardando_finalizacao) > 0:
        st.markdown("#### ✅ Finalizar Processos")
        
        for _, processo in aguardando_finalizacao.iterrows():
            with st.expander(f"📋 {processo['Processo']} - {processo['Parte']} - FINALIZAR"):
                col_info, col_anexo = st.columns([2, 1])
                
                with col_info:
                    st.write(f"**Parte:** {processo['Parte']}")
                    st.write(f"**Pagamento:** {processo.get('Pagamento', 'N/A')}")
                    st.write(f"**Enviado para Rodrigo em:** {processo.get('Data Envio Rodrigo', 'N/A')}")
                    
                    # Mostrar comprovante de recebimento se já existe
                    if processo.get("Comprovante Recebimento"):
                        st.success("✅ Comprovante de recebimento já anexado")
                        from components.functions_controle import baixar_arquivo_github
                        baixar_arquivo_github(processo["Comprovante Recebimento"], "Comprovante Recebimento")
                
                with col_anexo:
                    st.markdown("**📎 Anexar Comprovante de Recebimento:**")
                    comprovante_recebimento = st.file_uploader(
                        "Comprovante do Rodrigo:",
                        type=["pdf", "jpg", "jpeg", "png"],
                        key=f"recebimento_{processo['Processo']}"
                    )
                    
                    if comprovante_recebimento:
                        if st.button(f"✅ Finalizar", key=f"finalizar_{processo['Processo']}", type="primary"):
                            # Salvar comprovante de recebimento
                            from components.functions_controle import salvar_arquivo
                            recebimento_url = salvar_arquivo(comprovante_recebimento, processo['Processo'], "recebimento")
                            
                            if recebimento_url:
                                # Atualizar status
                                idx = df[df["Processo"] == processo["Processo"]].index[0]
                                st.session_state.df_editado_alvaras.loc[idx, "Status"] = "Finalizado"
                                st.session_state.df_editado_alvaras.loc[idx, "Comprovante Recebimento"] = recebimento_url
                                st.session_state.df_editado_alvaras.loc[idx, "Data Finalização"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                                st.session_state.df_editado_alvaras.loc[idx, "Finalizado Por"] = st.session_state.get("usuario", "Sistema")
                                
                                # Salvar no GitHub
                                from components.functions_controle import save_data_to_github
                                novo_sha = save_data_to_github(
                                    st.session_state.df_editado_alvaras,
                                    "lista_alvaras.csv",
                                    st.session_state.file_sha_alvaras
                                )
                                st.session_state.file_sha_alvaras = novo_sha
                                
                                st.success("🎉 Processo finalizado com sucesso!")
                                st.balloons()
                                st.rerun()
    
    # Mostrar processos finalizados recentemente
    if "Status" in df.columns:
        finalizados_recentes = df[df["Status"] == "Finalizado"].tail(5)
        if len(finalizados_recentes) > 0:
            st.markdown("#### 🎉 Últimos processos finalizados:")
            st.dataframe(
                finalizados_recentes[["Processo", "Parte", "Data Finalização", "Finalizado Por"]],
                use_container_width=True
            )

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
    st.markdown(f"**Status atual:** {status_atual}")
    
    # Mostrar informações básicas do processo
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.write(f"**Pagamento:** {linha_processo.get('Pagamento', 'N/A')}")
    with col_info2:
        st.write(f"**Banco:** {linha_processo.get('Banco', 'N/A')}")
    with col_info3:
        st.write(f"**Cadastrado em:** {linha_processo.get('Data Cadastro', 'N/A')}")
    
    st.markdown("---")
    
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
            
            # Mostrar se já existe
            if linha_processo.get("Comprovante Conta"):
                st.info("✅ Comprovante já anexado anteriormente")
        
        with col_doc2:
            st.markdown("**📄 PDF do Alvará**")
            pdf_alvara = st.file_uploader(
                "Anexar PDF do alvará:",
                type=["pdf"],
                key=f"pdf_{numero_processo}"
            )
            
            # Mostrar se já existe
            if linha_processo.get("PDF Alvará"):
                st.info("✅ PDF já anexado anteriormente")
        
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
                    st.balloons()
                    del st.session_state['processo_aberto']
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
            del st.session_state['processo_aberto']
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
                    del st.session_state['processo_aberto']
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
    
    st.subheader("📝 Cadastrar Novo Alvará")

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
                novo_sha = save_data_to_github_seguro(
                    st.session_state.df_editado_alvaras,
                    "lista_alvaras.csv",
                    st.session_state.file_sha_alvaras
                )
                if novo_sha != st.session_state.file_sha_alvaras:  # Se salvou com sucesso
                    st.session_state.file_sha_alvaras = novo_sha
                    del st.session_state["preview_novas_linhas"]
                    st.success("✅ Todas as linhas foram salvas!")
                    st.rerun()
        
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
        
        # DEFINIR COLUNAS ESPECÍFICAS DO FORMULÁRIO
        colunas_form = [
            "Processo", "Parte", "CPF", "Pagamento", "Observação pagamento", 
            "Órgão Judicial", "Banco", "Honorários Sucumbenciais", "Observação Honorários"
        ]
        
        # Processar campos principais em colunas
        cols = st.columns(2)
        
        for idx, col in enumerate(colunas_form):
            with cols[idx % 2]:
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
                
                elif col == "Pagamento":
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
                
                elif col == "Parte":
                    valor = st.text_input(
                        f"{col}",
                        key=f"input_alvaras_{col}_{st.session_state.form_reset_counter_alvaras}",
                        max_chars=100,
                        help=hints.get(col, ""),
                        placeholder="NOME COMPLETO DA PARTE"
                    ).upper()
                
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

        # Validação antes de submeter
        col_submit, col_validacao = st.columns([1, 2])

        with col_submit:
            submitted = st.form_submit_button("📝 Adicionar Linha", type="primary")

        with col_validacao:
            # Mostrar validação em tempo real
            campos_obrigatorios = ["Processo", "Parte", "CPF"]
            campos_preenchidos = [col for col in campos_obrigatorios if nova_linha.get(col, "").strip()]
            
            if len(campos_preenchidos) == len(campos_obrigatorios):
                st.success(f"✅ {len(campos_preenchidos)}/{len(campos_obrigatorios)} campos obrigatórios preenchidos")
            else:
                faltando = [col for col in campos_obrigatorios if not nova_linha.get(col, "").strip()]
                st.warning(f"⚠️ Campos obrigatórios faltando: {', '.join(faltando)}")


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
            
            st.success("✅ Linha adicionada!")
            st.rerun()

def interface_visualizar_dados(df):
    """Interface para visualizar e gerenciar dados"""
    st.subheader("📁 Visualizar Dados")
    
    if len(df) > 0:
        # Estatísticas gerais
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            st.metric("Total de Processos", len(df))
        
        with col_stat2:
            if "Status" in df.columns:
                finalizados = len(df[df["Status"] == "Finalizado"])
                st.metric("Finalizados", finalizados)
            else:
                st.metric("Finalizados", "N/A")
        
        with col_stat3:
            if "Status" in df.columns:
                pendentes = len(df[df["Status"] != "Finalizado"])
                st.metric("Pendentes", pendentes)
            else:
                st.metric("Pendentes", "N/A")
        
        with col_stat4:
            if "Data Cadastro" in df.columns:
                hoje = datetime.now().strftime("%d/%m/%Y")
                
                # CONVERTER PARA STRING E FILTRAR VALORES VÁLIDOS
                df_temp = df.copy()
                df_temp["Data Cadastro"] = df_temp["Data Cadastro"].astype(str)
                
                # Filtrar apenas registros com data válida e que contém a data de hoje
                hoje_count = len(df_temp[
                    (df_temp["Data Cadastro"] != "nan") & 
                    (df_temp["Data Cadastro"] != "") & 
                    (df_temp["Data Cadastro"].str.contains(hoje, na=False))
                ])
                st.metric("Cadastrados Hoje", hoje_count)
            else:
                st.metric("Cadastrados Hoje", "N/A")
        
        # Filtros para visualização
        st.markdown("### 🔍 Filtros")
        col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
        
        with col_filtro1:
            if "Status" in df.columns:
                # FILTRAR VALORES VÁLIDOS PARA O SELECTBOX
                status_unicos = df["Status"].dropna().unique()
                status_filtro = st.multiselect(
                    "Status:",
                    options=status_unicos,
                    default=status_unicos
                )
            else:
                status_filtro = []
        
        with col_filtro2:
            if "Cadastrado Por" in df.columns:
                # FILTRAR VALORES VÁLIDOS
                usuarios_unicos = df["Cadastrado Por"].dropna().unique()
                usuario_filtro = st.multiselect(
                    "Cadastrado Por:",
                    options=usuarios_unicos,
                    default=usuarios_unicos
                )
            else:
                usuario_filtro = []
        
        with col_filtro3:
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
            colunas_principais = [
                "Processo", "Parte", "Pagamento", "Status", 
                "Data Cadastro", "Cadastrado Por"
            ]
            colunas_exibir = [col for col in colunas_principais if col in df_visualizado.columns]
        
        # Exibir dados
        st.markdown(f"### 📊 Dados ({len(df_visualizado)} registros)")
        
        if len(df_visualizado) > 0:
            # Opções de visualização
            col_view1, col_view2 = st.columns(2)
            
            with col_view1:
                max_rows = st.slider("Máximo de linhas:", 10, 100, 50)
            
            with col_view2:
                if colunas_exibir:
                    ordenar_por = st.selectbox(
                        "Ordenar por:",
                        options=colunas_exibir,
                        index=0
                    )
                else:
                    ordenar_por = None
            
            # Aplicar ordenação
            if ordenar_por and ordenar_por in df_visualizado.columns:
                # ORDENAR APENAS SE A COLUNA CONTÉM DADOS VÁLIDOS
                df_temp = df_visualizado.copy()
                df_temp[ordenar_por] = df_temp[ordenar_por].astype(str)
                df_visualizado = df_temp.sort_values(ordenar_por, ascending=False)
            
            # Exibir tabela
            st.dataframe(
                df_visualizado[colunas_exibir].head(max_rows),
                use_container_width=True,
                height=400
            )
            
            # Opções de download
            st.markdown("### 💾 Download")
            col_down1, col_down2 = st.columns(2)
            
            with col_down1:
                if st.button("📥 Download CSV"):
                    csv = df_visualizado.to_csv(index=False, sep=';')
                    st.download_button(
                        label="Baixar arquivo CSV",
                        data=csv,
                        file_name=f"dados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            
            with col_down2:
                if st.button("📊 Download Excel"):
                    try:
                        from io import BytesIO
                        buffer = BytesIO()
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            df_visualizado.to_excel(writer, index=False, sheet_name='Dados')
                        
                        st.download_button(
                            label="Baixar arquivo Excel",
                            data=buffer.getvalue(),
                            file_name=f"dados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    except ImportError:
                        st.error("📊 openpyxl não instalado. Instale com: pip install openpyxl")
        
        else:
            st.info("Nenhum registro encontrado com os filtros aplicados")
        
        # Análise por status
        if "Status" in df.columns and len(df) > 0:
            st.markdown("### 📈 Análise por Status")
            
            # FILTRAR VALORES VÁLIDOS PARA O GRÁFICO
            status_validos = df["Status"].dropna()
            if len(status_validos) > 0:
                status_counts = status_validos.value_counts()
                
                col_chart1, col_chart2 = st.columns(2)
                
                with col_chart1:
                    st.markdown("**Distribuição por Status:**")
                    st.bar_chart(status_counts)
                
                with col_chart2:
                    st.markdown("**Resumo Quantitativo:**")
                    for status, count in status_counts.items():
                        porcentagem = (count / len(status_validos)) * 100
                        st.write(f"• **{status}:** {count} ({porcentagem:.1f}%)")
