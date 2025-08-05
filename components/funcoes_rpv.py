# components/funcoes_rpv.py
import streamlit as st
import pandas as pd
import requests
import base64
import math
from datetime import datetime
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

# =====================================
# CONFIGURAÇÕES DE PERFIS - RPV
# =====================================

# a) Novos Status
STATUS_ETAPAS_RPV = {
    1: "Enviado ao Jurídico",
    2: "Enviado ao Financeiro", 
    3: "Enviado para Rodrigo",
    4: "Finalizado"
}

# b) Novas Permissões de Edição por Perfil
PERFIS_RPV = {
    "Cadastrador": [], # Cadastrador apenas cria, não edita RPVs no fluxo.
    "Jurídico": ["Enviado ao Jurídico"],
    "Financeiro": ["Enviado ao Financeiro", "Enviado para Rodrigo"],
    "Admin": ["Enviado ao Jurídico", "Enviado ao Financeiro", "Enviado para Rodrigo", "Finalizado"]  # Admin tem acesso total
}

# =====================================
# FUNÇÕES DE PERFIL E CONTROLE - RPV
# =====================================

def validar_mes_competencia(mes_competencia):
    """Valida se o mês de competência está no formato mm/yyyy"""
    if not mes_competencia:
        return True  # Campo opcional
    
    import re
    # Padrão: mm/yyyy (01-12/ano de 4 dígitos)
    padrao = r'^(0[1-9]|1[0-2])\/\d{4}$'
    return bool(re.match(padrao, mes_competencia))

def verificar_perfil_usuario_rpv():
    """Verifica o perfil do usuário logado para RPV a partir do st.secrets."""
    usuario_atual = st.session_state.get("usuario", "")
    
    # Se não houver usuário logado, retorna um perfil sem permissões.
    if not usuario_atual:
        return "Visitante"

    # Acessa a seção [usuarios] do secrets.toml,
    # pega o dicionário do usuario_atual (ou um dict vazio se não encontrar),
    # e então pega o valor da chave "perfil" (ou "Visitante" se não encontrar).
    perfil = st.secrets.usuarios.get(usuario_atual, {}).get("perfil", "Visitante")
    
    return perfil

def pode_editar_status_rpv(status_atual, perfil_usuario):
    """Verifica se o usuário pode editar determinado status RPV"""
    return status_atual in PERFIS_RPV.get(perfil_usuario, [])

def obter_colunas_controle_rpv():
    """Retorna lista das colunas de controle do fluxo RPV"""
    return [
        "Solicitar Certidão", "Status", "Data Cadastro", "Cadastrado Por", 
        "PDF RPV", "Data Envio", "Enviado Por", "Mês Competência",
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

def toggle_rpv_selection(rpv_id):
    """Função callback para alternar seleção de RPV"""
    # Garantir que a lista existe
    if "processos_selecionados_rpv" not in st.session_state:
        st.session_state.processos_selecionados_rpv = []
    
    # Converter para string para consistência
    rpv_id_str = str(rpv_id)
    
    # Remover qualquer versão duplicada (int ou str)
    st.session_state.processos_selecionados_rpv = [
        pid for pid in st.session_state.processos_selecionados_rpv 
        if str(pid) != rpv_id_str
    ]
    
    # Se o checkbox está marcado, adicionar à lista
    checkbox_key = f"check_rpv_{rpv_id}"
    if st.session_state.get(checkbox_key, False):
        st.session_state.processos_selecionados_rpv.append(rpv_id_str)

def interface_lista_rpv(df, perfil_usuario):
    """Lista de RPVs com paginação e diálogo para ações"""
    st.subheader("📊 Gerenciar RPVs")

    # Inicializar o estado do diálogo
    if "show_rpv_dialog" not in st.session_state:
        st.session_state.show_rpv_dialog = False
        st.session_state.rpv_aberto_id = None
    
    # Inicializar estado de exclusão em massa
    if "modo_exclusao_rpv" not in st.session_state:
        st.session_state.modo_exclusao_rpv = False
    if "processos_selecionados_rpv" not in st.session_state:
        st.session_state.processos_selecionados_rpv = []
    
    # Validar consistência da lista de selecionados
    if st.session_state.processos_selecionados_rpv:
        ids_existentes = set(df["ID"].astype(str).tolist())
        st.session_state.processos_selecionados_rpv = [
            pid for pid in st.session_state.processos_selecionados_rpv 
            if str(pid) in ids_existentes
        ]

    # Botão para habilitar exclusão (apenas para Admin e Cadastrador)
    usuario_atual = st.session_state.get("usuario", "")
    perfil_atual = st.session_state.get("perfil_usuario", "")
    pode_excluir = (perfil_atual in ["Admin", "Cadastrador"] or usuario_atual == "admin")
    
    if pode_excluir:
        col_btn1, col_btn2, col_rest = st.columns([2, 2, 6])
        with col_btn1:
            if not st.session_state.modo_exclusao_rpv:
                if st.button("🗑️ Habilitar Exclusão", key="habilitar_exclusao_rpv"):
                    st.session_state.modo_exclusao_rpv = True
                    st.session_state.processos_selecionados_rpv = []
                    st.rerun()
            else:
                if st.button("❌ Cancelar Exclusão", key="cancelar_exclusao_rpv"):
                    st.session_state.modo_exclusao_rpv = False
                    st.session_state.processos_selecionados_rpv = []
                    st.rerun()
        
        with col_btn2:
            if st.session_state.modo_exclusao_rpv and st.session_state.processos_selecionados_rpv:
                if st.button(f"🗑️ Excluir ({len(st.session_state.processos_selecionados_rpv)})", 
                           key="confirmar_exclusao_rpv", type="primary"):
                    confirmar_exclusao_massa_rpv(df, st.session_state.processos_selecionados_rpv)

    # Filtros
    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
    with col_filtro1:
        status_filtro = st.selectbox(
            "🔍 Filtrar por Status:",
            ["Todos"] + list(STATUS_ETAPAS_RPV.values()),
            key="rpv_status_filter"
        )
    with col_filtro2:
        # Filtro por mês de competência
        meses_disponiveis = ["Todos"]
        if "Mês Competência" in df.columns:
            meses_unicos = df["Mês Competência"].dropna().unique()
            meses_unicos = [m for m in meses_unicos if m and str(m) != 'nan']
            meses_unicos = sorted(meses_unicos, reverse=True)  # Mais recentes primeiro
            meses_disponiveis.extend(meses_unicos)
        
        mes_filtro = st.selectbox(
            "📅 Filtrar por Mês:",
            meses_disponiveis,
            key="rpv_mes_filter"
        )
    with col_filtro3:
        mostrar_apenas_meus = False
        if perfil_usuario == "Jurídico":
            mostrar_apenas_meus = st.checkbox("Mostrar apenas RPVs que preciso de certidão")
        elif perfil_usuario == "Financeiro":
            mostrar_apenas_meus = st.checkbox("Mostrar apenas RPVs que posso editar")

    # Aplicar filtros
    df_filtrado = df.copy()
    if status_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Status"] == status_filtro]
    if mes_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Mês Competência"] == mes_filtro]
    if mostrar_apenas_meus:
        if perfil_usuario == "Jurídico":
            df_filtrado = df_filtrado[
                (df_filtrado["Solicitar Certidão"] == "Sim") &
                (df_filtrado["Status"].isin(["Enviado", "Certidão anexa"]))
            ]
        elif perfil_usuario == "Financeiro":
            df_filtrado = df_filtrado[df_filtrado["Status"].isin(["Enviado", "Certidão anexa", "Enviado para Rodrigo"])]

    # Lógica de Paginação
    if "current_page_rpv" not in st.session_state:
        st.session_state.current_page_rpv = 1
    
    items_per_page = 20
    total_registros = len(df_filtrado)
    total_pages = math.ceil(total_registros / items_per_page) if items_per_page > 0 else 1
    
    start_idx = (st.session_state.current_page_rpv - 1) * items_per_page
    end_idx = start_idx + items_per_page
    df_paginado = df_filtrado.iloc[start_idx:end_idx]

    # Exibir lista
    if not df_paginado.empty:
        st.markdown(f'<p style="font-size: small; color: steelblue;">Mostrando {start_idx+1} a {min(end_idx, total_registros)} de {total_registros} RPVs</p>', unsafe_allow_html=True)
        
        # Cabeçalhos dinâmicos baseados no modo de exclusão
        if st.session_state.modo_exclusao_rpv:
            col_h1, col_h2, col_h3, col_h4, col_h5, col_h6 = st.columns([0.5, 1, 2, 2, 1.5, 2])
            with col_h1: st.markdown("**☑️**")
            with col_h2: st.markdown("**Ação**")
            with col_h3: st.markdown("**Processo**")
            with col_h4: st.markdown("**Beneficiário**")
            with col_h5: st.markdown("**Valor**")
            with col_h6: st.markdown("**Status**")
        else:
            col_h1, col_h2, col_h3, col_h4, col_h5 = st.columns([1, 2, 2, 1.5, 2])
            with col_h1: st.markdown("**Ação**")
            with col_h2: st.markdown("**Processo**")
            with col_h3: st.markdown("**Beneficiário**")
            with col_h4: st.markdown("**Valor**")
            with col_h5: st.markdown("**Status**")
        
        st.markdown('<hr style="margin-top: 0.1rem; margin-bottom: 0.5rem;" />', unsafe_allow_html=True)

        for idx, rpv in df_paginado.iterrows():
            rpv_id = rpv.get("ID", idx)
            
            if st.session_state.modo_exclusao_rpv:
                col_b1, col_b2, col_b3, col_b4, col_b5, col_b6 = st.columns([0.5, 1, 2, 2, 1.5, 2])
                
                with col_b1:
                    # Usar callback para atualizar imediatamente
                    checkbox_key = f"checkbox_rpv_{rpv_id}"
                    current_value = rpv_id in st.session_state.processos_selecionados_rpv
                    
                    is_selected = st.checkbox(
                        "",
                        value=current_value,
                        key=checkbox_key,
                        on_change=lambda rid=rpv_id: toggle_rpv_selection(rid)
                    )
                
                with col_b2:
                    if st.button("🔓 Abrir", key=f"abrir_rpv_id_{rpv_id}"):
                        st.session_state.show_rpv_dialog = True
                        st.session_state.rpv_aberto_id = rpv_id
                        st.rerun()
                
                with col_b3: st.write(f"**{rpv.get('Processo', 'N/A')}**")
                with col_b4: st.write(rpv.get('Beneficiário', 'N/A'))
                with col_b5: st.write(rpv.get('Valor RPV', 'N/A'))
                with col_b6:
                    status_atual = rpv.get('Status', 'N/A')
                    cor = {"Enviado": "🟠", "Certidão anexa": "🔵", "Enviado para Rodrigo": "🟣", "Finalizado": "🟢"}.get(status_atual, "⚫")
                    st.write(f"{cor} {status_atual}")
            else:
                col_b1, col_b2, col_b3, col_b4, col_b5 = st.columns([1, 2, 2, 1.5, 2])
                
                with col_b1:
                    if st.button("🔓 Abrir", key=f"abrir_rpv_id_{rpv_id}"):
                        st.session_state.show_rpv_dialog = True
                        st.session_state.rpv_aberto_id = rpv_id
                        st.rerun()
                
                with col_b2: st.write(f"**{rpv.get('Processo', 'N/A')}**")
                with col_b3: st.write(rpv.get('Beneficiário', 'N/A'))
                with col_b4: st.write(rpv.get('Valor RPV', 'N/A'))
                with col_b5:
                    status_atual = rpv.get('Status', 'N/A')
                    cor = {"Enviado": "🟠", "Certidão anexa": "🔵", "Enviado para Rodrigo": "🟣", "Finalizado": "🟢"}.get(status_atual, "⚫")
                    st.write(f"{cor} {status_atual}")

    else:
        st.info("Nenhum RPV encontrado com os filtros aplicados.")

    # Implementação com st.dialog
    if st.session_state.show_rpv_dialog:
        rpv_id_aberto = st.session_state.rpv_aberto_id
        linha_rpv = df[df["ID"] == rpv_id_aberto]
        titulo = f"Detalhes do RPV: {linha_rpv.iloc[0].get('Processo', 'N/A')}" if not linha_rpv.empty else "Detalhes do RPV"

        @st.dialog(titulo, width="large")
        def rpv_dialog():
            if not linha_rpv.empty:
                status_atual = linha_rpv.iloc[0].get("Status", "")
                interface_edicao_rpv(df, rpv_id_aberto, status_atual, perfil_usuario)
            else:
                st.error("❌ RPV não encontrado.")
            
            if st.button("Fechar", key="fechar_rpv_dialog"):
                st.session_state.show_rpv_dialog = False
                st.rerun()
        
        rpv_dialog()

    # Controles de paginação
    if total_pages > 1:
        st.markdown("---")
        col_nav1, col_nav2, col_nav3 = st.columns([3, 2, 3])
        with col_nav1:
            if st.session_state.current_page_rpv > 1:
                if st.button("<< Primeira", key="rpv_primeira"): st.session_state.current_page_rpv = 1; st.rerun()
                if st.button("< Anterior", key="rpv_anterior"): st.session_state.current_page_rpv -= 1; st.rerun()
        with col_nav2:
            st.write(f"Página {st.session_state.current_page_rpv} de {total_pages}")
        with col_nav3:
            if st.session_state.current_page_rpv < total_pages:
                if st.button("Próxima >", key="rpv_proxima"): st.session_state.current_page_rpv += 1; st.rerun()
                if st.button("Última >>", key="rpv_ultima"): st.session_state.current_page_rpv = total_pages; st.rerun()

def interface_edicao_rpv(df, rpv_id, status_atual, perfil_usuario):
    """Interface de edição completamente redesenhada para o novo fluxo de RPV."""
    
    # Verificar permissão de edição ANTES de mostrar qualquer coisa
    if not pode_editar_status_rpv(status_atual, perfil_usuario):
        st.error(f"❌ Seu perfil ({perfil_usuario}) não pode editar RPVs com status '{status_atual}'.")
        # Mensagens de ajuda mais claras
        if perfil_usuario == "Jurídico":
            st.info("💡 O Jurídico só pode atuar em RPVs com status 'Enviado ao Jurídico'.")
        elif perfil_usuario == "Financeiro":
            st.info("💡 O Financeiro atua em RPVs com status 'Enviado ao Financeiro' e 'Enviado para Rodrigo'.")
        else:
            st.info("💡 Apenas Jurídico e Financeiro podem editar RPVs após o cadastro.")
        return

    linha_rpv = df[df["ID"] == rpv_id].iloc[0]
    numero_processo = linha_rpv.get("Processo", "N/A")
    
    # --- ETAPA 1: Ação do Jurídico ---
    if status_atual == "Enviado ao Jurídico" and perfil_usuario in ["Jurídico", "Admin"]:
        st.markdown("#### Ação do Jurídico")
        st.info("Verifique a necessidade da certidão e confirme a inserção no sistema Korbil.")
        
        certidao_korbil = st.checkbox("✅ Certidão inserida no Korbil", key=f"korbil_{rpv_id}")
        
        if certidao_korbil:
            if st.button("➡️ Enviar para o Financeiro", type="primary"):
                idx = df[df["ID"] == rpv_id].index[0]
                st.session_state.df_editado_rpv.loc[idx, "Status"] = "Enviado ao Financeiro"
                st.session_state.df_editado_rpv.loc[idx, "Certidão no Korbil"] = "Sim"
                # Salvar e fechar
                save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                st.session_state.show_rpv_dialog = False
                st.success("✅ RPV enviado ao Financeiro!")
                st.rerun()

    # --- ETAPA 2: Ação do Financeiro (Pré-Rodrigo) ---
    elif status_atual == "Enviado ao Financeiro" and perfil_usuario in ["Financeiro", "Admin"]:
        st.markdown("#### Ação do Financeiro")
        st.info("Analise a documentação do cliente e confirme que está organizada.")
        
        doc_ok = st.checkbox("✅ Documentação do cliente organizada", key=f"doc_ok_{rpv_id}")
        
        if doc_ok:
            if st.button("➡️ Enviar para Rodrigo", type="primary"):
                idx = df[df["ID"] == rpv_id].index[0]
                st.session_state.df_editado_rpv.loc[idx, "Status"] = "Enviado para Rodrigo"
                st.session_state.df_editado_rpv.loc[idx, "Documentação Cliente OK"] = "Sim"
                # Salvar e fechar
                save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                st.session_state.show_rpv_dialog = False
                st.success("✅ RPV enviado para Rodrigo!")
                st.rerun()

    # --- ETAPA 3: Ação do Financeiro (Pós-Rodrigo) ---
    elif status_atual == "Enviado para Rodrigo" and perfil_usuario in ["Financeiro", "Admin"]:
        st.markdown("#### Ação do Financeiro (Finalização)")
        st.info("Anexe os comprovantes e preencha os valores para finalizar o processo.")
        
        # Checkbox para anexar múltiplos documentos
        anexar_multiplos = st.checkbox("📎 Anexar múltiplos documentos", key=f"multiplos_rpv_{rpv_id}")
        
        col1, col2 = st.columns(2)
        with col1:
            if anexar_multiplos:
                comp_saque = st.file_uploader("Comprovantes de Saque (Rodrigo)", 
                                            type=["pdf", "png", "jpg", "jpeg"],
                                            accept_multiple_files=True,
                                            key=f"saque_multiplos_{rpv_id}")
            else:
                comp_saque = st.file_uploader("Comprovante de Saque (Rodrigo)", 
                                            type=["pdf", "png", "jpg", "jpeg"],
                                            key=f"saque_{rpv_id}")
        with col2:
            if anexar_multiplos:
                comp_pagamento = st.file_uploader("Comprovantes de Pagamento (Clientes)", 
                                                type=["pdf", "png", "jpg", "jpeg"],
                                                accept_multiple_files=True,
                                                key=f"pagamento_multiplos_{rpv_id}")
            else:
                comp_pagamento = st.file_uploader("Comprovante de Pagamento (Clientes)", 
                                                type=["pdf", "png", "jpg", "jpeg"],
                                                key=f"pagamento_{rpv_id}")
            
        valor_final = st.text_input("Valor Final para o Escritório (R$):")
        obs_valor = st.text_area("Observações sobre o Valor:")
        
        # Verificar se documentos foram anexados (considerando múltiplos ou únicos)
        docs_anexados = False
        if anexar_multiplos:
            docs_anexados = (comp_saque and len(comp_saque) > 0) and (comp_pagamento and len(comp_pagamento) > 0) and valor_final
        else:
            docs_anexados = comp_saque and comp_pagamento and valor_final
        
        if docs_anexados:
            if st.button("🏁 Finalizar RPV", type="primary"):
                processo_num = linha_rpv["Processo"]
                
                if anexar_multiplos:
                    # Salvar múltiplos arquivos
                    urls_saque = []
                    urls_pagamento = []
                    
                    for i, arquivo in enumerate(comp_saque):
                        url = salvar_arquivo(arquivo, processo_num, f"saque_rpv_{i+1}")
                        urls_saque.append(url)
                    
                    for i, arquivo in enumerate(comp_pagamento):
                        url = salvar_arquivo(arquivo, processo_num, f"pagamento_rpv_{i+1}")
                        urls_pagamento.append(url)
                    
                    url_saque = "; ".join(urls_saque)
                    url_pagamento = "; ".join(urls_pagamento)
                else:
                    # Salvar arquivo único
                    url_saque = salvar_arquivo(comp_saque, processo_num, "saque_rpv")
                    url_pagamento = salvar_arquivo(comp_pagamento, processo_num, "pagamento_rpv")
                
                if url_saque and url_pagamento:
                    idx = df[df["ID"] == rpv_id].index[0]
                    st.session_state.df_editado_rpv.loc[idx, "Status"] = "Finalizado"
                    st.session_state.df_editado_rpv.loc[idx, "Comprovante Saque"] = url_saque
                    st.session_state.df_editado_rpv.loc[idx, "Comprovante Pagamento"] = url_pagamento
                    st.session_state.df_editado_rpv.loc[idx, "Valor Final Escritório"] = valor_final
                    st.session_state.df_editado_rpv.loc[idx, "Observações Valor"] = obs_valor
                    # Salvar e fechar
                    save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                    st.session_state.show_rpv_dialog = False
                    st.success("🎉 RPV Finalizado com sucesso!")
                    st.balloons()
                    st.rerun()
        else:
            st.warning("⚠️ Anexe ambos os comprovantes e preencha o valor final para poder finalizar.")
            
    # --- Visualização de RPV Finalizado (para todos) ---
    elif status_atual == "Finalizado":
        st.markdown("#### 🎉 RPV Finalizado")
        st.success("Este processo foi concluído.")
        
        # Mostrar documentos finais
        col_final1, col_final2 = st.columns(2)
        
        with col_final1:
            if linha_rpv.get("Comprovante Saque"):
                st.markdown("**📄 Comprovante de Saque:**")
                baixar_arquivo_drive(linha_rpv["Comprovante Saque"], "📎 Baixar Comprovante")
        
        with col_final2:
            if linha_rpv.get("Comprovante Pagamento"):
                st.markdown("**📄 Comprovante de Pagamento:**")
                baixar_arquivo_drive(linha_rpv["Comprovante Pagamento"], "📎 Baixar Comprovante")
        
        # Valor final
        if linha_rpv.get("Valor Final Escritório"):
            st.markdown("**💰 Valor Final para o Escritório:**")
            st.text_area("", value=linha_rpv["Valor Final Escritório"], disabled=True, height=100)
        
        # Timeline
        st.markdown("**📅 Timeline do RPV:**")
        timeline_data = []
        if linha_rpv.get("Data Cadastro"):
            timeline_data.append(f"• **Cadastrado:** {linha_rpv['Data Cadastro']} por {linha_rpv.get('Cadastrado Por', 'N/A')}")
        if linha_rpv.get("Data Envio"):
            timeline_data.append(f"• **Enviado:** {linha_rpv['Data Envio']} por {linha_rpv.get('Enviado Por', 'N/A')}")
        if linha_rpv.get("Data Certidão"):
            timeline_data.append(f"• **Certidão anexada:** {linha_rpv['Data Certidão']} por {linha_rpv.get('Anexado Certidão Por', 'N/A')}")
        if linha_rpv.get("Data Envio Rodrigo"):
            timeline_data.append(f"• **Enviado para Rodrigo:** {linha_rpv['Data Envio Rodrigo']} por {linha_rpv.get('Enviado Rodrigo Por', 'N/A')}")
        if linha_rpv.get("Data Finalização"):
            timeline_data.append(f"• **Finalizado:** {linha_rpv['Data Finalização']} por {linha_rpv.get('Finalizado Por', 'N/A')}")
        
        for item in timeline_data:
            st.markdown(item)
    
    # ACESSO NEGADO
    else:
        st.error(f"❌ Seu perfil ({perfil_usuario}) não pode editar RPVs com status '{status_atual}'")
        
        if perfil_usuario == "Cadastrador":
            st.info("💡 Cadastradores só podem editar RPVs com status 'Cadastrado'")
        elif perfil_usuario == "Jurídico":
            st.info("💡 Jurídico só pode anexar certidões em RPVs com status 'Enviado'")
        elif perfil_usuario == "Financeiro":
            st.info("💡 Financeiro pode editar RPVs 'Enviado', 'Certidão anexa' e 'Enviado para Rodrigo'")

def interface_visualizar_dados_rpv(df):
    """Interface aprimorada para visualizar dados de RPVs com paginação."""
    if df.empty:
        st.info("ℹ️ Não há RPVs para visualizar.")
        return

    # Estatísticas gerais
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    with col_stat1:
        st.metric("Total de RPVs", len(df))
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
        status_filtro = st.multiselect("Status:", options=status_unicos, default=status_unicos, key="viz_rpv_status")
        
    with col_filtro2:
        usuarios_unicos = df["Cadastrado Por"].dropna().unique() if "Cadastrado Por" in df.columns else []
        usuario_filtro = st.multiselect("Cadastrado Por:", options=usuarios_unicos, default=usuarios_unicos, key="viz_rpv_user")
    
    with col_filtro3:
        pesquisa = st.text_input("Pesquisar por Beneficiário ou Processo:", key="viz_rpv_search")

    # Aplicar filtros
    df_visualizado = df.copy()
    if status_filtro and "Status" in df.columns:
        df_visualizado = df_visualizado[df_visualizado["Status"].isin(status_filtro)]
    if usuario_filtro and "Cadastrado Por" in df.columns:
        df_visualizado = df_visualizado[df_visualizado["Cadastrado Por"].isin(usuario_filtro)]
    if pesquisa:
        df_visualizado = df_visualizado[
            df_visualizado["Beneficiário"].astype(str).str.contains(pesquisa, case=False, na=False) |
            df_visualizado["Processo"].astype(str).str.contains(pesquisa, case=False, na=False)
        ]
    
    st.markdown("---")

    # Botões de download acima da tabela
    if not df_visualizado.empty:
        from io import BytesIO
        
        csv_data = df_visualizado.to_csv(index=False, sep=';').encode('utf-8')
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_visualizado.to_excel(writer, index=False, sheet_name='Dados RPV')
        excel_data = output.getvalue()

        col_down1, col_down2, _ = st.columns([1.5, 1.5, 7])
        with col_down1:
            st.download_button(
                label="📥 Baixar CSV",
                data=csv_data,
                file_name=f"dados_rpv_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )
        with col_down2:
            st.download_button(
                label="📊 Baixar Excel",
                data=excel_data,
                file_name=f"dados_rpv_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    # Lógica de Paginação
    if "current_page_visualizar_rpv" not in st.session_state:
        st.session_state.current_page_visualizar_rpv = 1
    
    items_per_page = 10
    total_registros = len(df_visualizado)
    total_pages = math.ceil(total_registros / items_per_page) if items_per_page > 0 else 1
    
    start_idx = (st.session_state.current_page_visualizar_rpv - 1) * items_per_page
    end_idx = start_idx + items_per_page
    df_paginado = df_visualizado.iloc[start_idx:end_idx]

    # Exibir dados
    st.markdown(f"### 📊 Dados ({total_registros} registros encontrados)")
    
    if not df_paginado.empty:
        st.markdown(f'<p style="font-size: small; color: steelblue;">Mostrando {start_idx+1} a {min(end_idx, total_registros)} de {total_registros} registros</p>', unsafe_allow_html=True)
        
        st.dataframe(df_paginado, use_container_width=True)
        
        # Controles de paginação
        st.markdown("---")
        col_nav1, col_nav2, col_nav3 = st.columns([3, 2, 3])
        with col_nav1:
            if st.session_state.current_page_visualizar_rpv > 1:
                if st.button("<< Primeira", key="viz_rpv_primeira"): st.session_state.current_page_visualizar_rpv = 1; st.rerun()
                if st.button("< Anterior", key="viz_rpv_anterior"): st.session_state.current_page_visualizar_rpv -= 1; st.rerun()
        with col_nav2:
            st.write(f"Página {st.session_state.current_page_visualizar_rpv} de {total_pages}")
        with col_nav3:
            if st.session_state.current_page_visualizar_rpv < total_pages:
                if st.button("Próxima >", key="viz_rpv_proxima"): st.session_state.current_page_visualizar_rpv += 1; st.rerun()
                if st.button("Última >>", key="viz_rpv_ultima"): st.session_state.current_page_visualizar_rpv = total_pages; st.rerun()
    else:
        st.info("Nenhum registro encontrado com os filtros aplicados.")

def interface_cadastro_rpv(df, perfil_usuario):
    """Interface para cadastrar novos RPVs"""
    if perfil_usuario not in ["Cadastrador", "Admin"]:
        st.warning("⚠️ Apenas Cadastradores e Administradores podem criar novos RPVs")
        return

    # Mostrar linhas temporárias primeiro (se existirem)
    if "preview_novas_linhas_rpv" in st.session_state and len(st.session_state["preview_novas_linhas_rpv"]) > 0:
        st.markdown("### 📋 Linhas Adicionadas (não salvas)")
        st.warning(f"⚠️ Você tem {len(st.session_state['preview_novas_linhas_rpv'])} linha(s) não salva(s)")
        
        st.dataframe(st.session_state["preview_novas_linhas_rpv"], use_container_width=True)
        
        col_salvar, col_limpar = st.columns(2)
        
        with col_salvar:
            if st.button("💾 Salvar Todas as Linhas", type="primary"):
                from components.functions_controle import save_data_to_github_seguro
                with st.spinner("Salvando no GitHub..."):
                    novo_sha = save_data_to_github_seguro(
                        st.session_state.df_editado_rpv,
                        "lista_rpv.csv",
                        "file_sha_rpv"
                    )
                
                if novo_sha:
                    st.session_state.file_sha_rpv = novo_sha
                    # c) CORREÇÃO: Deletar a chave do preview para a seção desaparecer
                    del st.session_state["preview_novas_linhas_rpv"]
                    st.toast("✅ Todas as linhas foram salvas com sucesso!", icon="🎉")
                    st.rerun()
                else:
                    st.error("❌ Falha ao salvar. Tente novamente.")

        with col_limpar:
            if st.button("🗑️ Descartar Linhas", type="secondary"):
                num_linhas_remover = len(st.session_state["preview_novas_linhas_rpv"])
                st.session_state.df_editado_rpv = st.session_state.df_editado_rpv.iloc[:-num_linhas_remover]
                del st.session_state["preview_novas_linhas_rpv"]
                st.warning("🗑️ Linhas descartadas!")
                st.rerun()
        
        st.markdown("---")

    st.subheader("📝 Cadastrar Novo RPV")

    # Remover formulário para permitir que file_uploader funcione corretamente
    # O problema é que st.form não funciona bem com accept_multiple_files=True
    
    col1, col2 = st.columns(2)
    
    # Usar chaves únicas para manter estado
    processo_key = "new_rpv_processo"
    beneficiario_key = "new_rpv_beneficiario"
    cpf_key = "new_rpv_cpf"
    certidao_key = "new_rpv_certidao"
    valor_key = "new_rpv_valor"
    obs_key = "new_rpv_observacoes"
    multiplos_key = "new_rpv_multiplos"
    competencia_key = "new_rpv_competencia"
    
    with col1:
        processo = st.text_input("Número do Processo:", key=processo_key)
        beneficiario = st.text_input("Beneficiário:", key=beneficiario_key)
        cpf = st.text_input("CPF:", key=cpf_key)
        solicitar_certidao = st.selectbox(
            "Solicitar Certidão?",
            options=["Sim", "Não"],
            key=certidao_key
        )
        # Novo campo: Mês de Competência
        mes_competencia = st.text_input(
            "Mês de Competência (mm/yyyy):",
            placeholder="Ex: 12/2024",
            help="Formato: mm/yyyy (mês/ano)",
            key=competencia_key
        )
    
    with col2:
        valor_rpv = st.text_input("Valor da RPV (R$):", key=valor_key)
        observacoes = st.text_area("Observações:", height=125, key=obs_key)
        
        # Checkbox para anexar múltiplos PDFs
        anexar_multiplos_pdf = st.checkbox("📎 Anexar múltiplos PDFs", key=multiplos_key)
        
        # Usar keys diferentes para múltiplos vs único para evitar conflitos
        if anexar_multiplos_pdf:
            pdf_rpv = st.file_uploader(
                "PDFs do RPV:", 
                type=["pdf"], 
                accept_multiple_files=True,
                key="pdf_rpv_multiplos"
            )
        else:
            pdf_rpv = st.file_uploader(
                "PDF do RPV:", 
                type=["pdf"],
                key="pdf_rpv_unico"
            )

    # Botão de submissão fora do formulário
    if st.button("📝 Adicionar Linha", type="primary", use_container_width=True):
        # Validação principal considerando múltiplos ou único arquivo
        pdf_valido = False
        if anexar_multiplos_pdf:
            pdf_valido = pdf_rpv and len(pdf_rpv) > 0
        else:
            pdf_valido = pdf_rpv is not None
        
        if not processo or not beneficiario or not pdf_valido:
            if anexar_multiplos_pdf:
                st.error("❌ Preencha os campos Processo, Beneficiário e anexe pelo menos um PDF do RPV.")
            else:
                st.error("❌ Preencha os campos Processo, Beneficiário e anexe o PDF do RPV.")
        elif mes_competencia and not validar_mes_competencia(mes_competencia):
            st.error("❌ Mês de competência deve estar no formato mm/yyyy (ex: 12/2024).")
        else:
            from components.functions_controle import formatar_processo, validar_cpf, gerar_id_unico
            
            processo_formatado = formatar_processo(processo)
            
            if cpf and not validar_cpf(cpf):
                st.error("❌ CPF inválido. Verifique e tente novamente.")
            elif "Processo" in df.columns and processo_formatado in df["Processo"].values:
                st.warning(f"⚠️ Processo {processo_formatado} já cadastrado.")
            else:
                # Definir o status inicial baseado na escolha da certidão
                if solicitar_certidao == "Sim":
                    status_inicial = "Enviado ao Jurídico"
                else:
                    status_inicial = "Enviado ao Financeiro"

                # Salvar PDF(s)
                if anexar_multiplos_pdf:
                    # Salvar múltiplos arquivos
                    pdf_urls = []
                    for i, arquivo in enumerate(pdf_rpv):
                        url = salvar_arquivo(arquivo, processo_formatado, f"rpv_{i+1}")
                        pdf_urls.append(url)
                    pdf_url = "; ".join(pdf_urls)
                else:
                    # Salvar arquivo único
                    pdf_url = salvar_arquivo(pdf_rpv, processo_formatado, "rpv")

                # Criar nova linha
                nova_linha = {
                    "ID": gerar_id_unico(st.session_state.df_editado_rpv, "ID"),
                    "Processo": processo_formatado,
                    "Beneficiário": beneficiario,
                    "CPF": cpf,
                    "Valor RPV": valor_rpv,
                    "Mês Competência": mes_competencia,
                    "Observações": observacoes,
                    "Solicitar Certidão": solicitar_certidao,
                    "Status": status_inicial, # <-- Status inicial dinâmico
                    "Data Cadastro": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Cadastrado Por": st.session_state.get("usuario", "Sistema"),
                    "PDF RPV": pdf_url,
                    # Adicionar os novos campos de controle
                    "Certidão no Korbil": "Não",
                    "Documentação Cliente OK": "Não",
                    "Valor Final Escritório": "",
                    "Observações Valor": ""
                }
                
                # Adicionar campos de controle vazios
                linha_controle = inicializar_linha_vazia_rpv()
                nova_linha.update({k: v for k, v in linha_controle.items() if k not in nova_linha})

                # Adicionar ao DataFrame em memória
                st.session_state.df_editado_rpv = pd.concat(
                    [st.session_state.df_editado_rpv, pd.DataFrame([nova_linha])],
                    ignore_index=True
                )
                
                # Adicionar ao preview
                if "preview_novas_linhas_rpv" not in st.session_state:
                    st.session_state["preview_novas_linhas_rpv"] = pd.DataFrame()
                st.session_state["preview_novas_linhas_rpv"] = pd.concat(
                    [st.session_state["preview_novas_linhas_rpv"], pd.DataFrame([nova_linha])],
                    ignore_index=True
                )

                # Limpar campos após submissão bem-sucedida
                for key in [processo_key, beneficiario_key, cpf_key, valor_key, obs_key, competencia_key]:
                    if key in st.session_state:
                        del st.session_state[key]
                
                st.success("✅ Linha adicionada! Salve para persistir os dados.")
                st.rerun()

def confirmar_exclusao_massa_rpv(df, processos_selecionados):
    """Função para confirmar exclusão em massa de RPVs"""
    
    @st.dialog("🗑️ Confirmar Exclusão em Massa", width="large")
    def dialog_confirmacao():
        st.error("⚠️ **ATENÇÃO:** Esta ação não pode ser desfeita!")
        
        # Mostrar processos que serão excluídos
        st.markdown(f"### Você está prestes a excluir **{len(processos_selecionados)}** processo(s):")
        
        processos_para_excluir = df[df["ID"].isin(processos_selecionados)]
        
        for _, processo in processos_para_excluir.iterrows():
            st.markdown(f"- **{processo.get('Processo', 'N/A')}** - {processo.get('Beneficiário', 'N/A')}")
        
        st.markdown("---")
        
        col_conf, col_canc = st.columns(2)
        
        with col_conf:
            if st.button("✅ Confirmar Exclusão", type="primary", use_container_width=True):
                # Importar sistema de log
                from components.log_exclusoes import registrar_exclusao
                
                usuario_atual = st.session_state.get("usuario", "Sistema")
                
                # Registrar cada exclusão no log
                for _, processo in processos_para_excluir.iterrows():
                    registrar_exclusao(
                        tipo_processo="RPV",
                        processo_numero=processo.get('Processo', 'N/A'),
                        dados_excluidos=processo,
                        usuario=usuario_atual
                    )
                
                # Remover processos do DataFrame
                st.session_state.df_editado_rpv = st.session_state.df_editado_rpv[
                    ~st.session_state.df_editado_rpv["ID"].isin(processos_selecionados)
                ].reset_index(drop=True)
                
                # Salvar no GitHub
                from components.functions_controle import save_data_to_github_seguro
                
                with st.spinner("Salvando alterações..."):
                    novo_sha = save_data_to_github_seguro(
                        st.session_state.df_editado_rpv,
                        "lista_rpv.csv",
                        "file_sha_rpv"
                    )
                
                if novo_sha:
                    st.session_state.file_sha_rpv = novo_sha
                    st.success(f"✅ {len(processos_selecionados)} processo(s) excluído(s) com sucesso!")
                    
                    # Resetar estado de exclusão
                    st.session_state.modo_exclusao_rpv = False
                    st.session_state.processos_selecionados_rpv = []
                    
                    st.rerun()
                else:
                    st.error("❌ Erro ao salvar. Exclusão cancelada.")
        
        with col_canc:
            if st.button("❌ Cancelar", use_container_width=True):
                st.rerun()
    
    dialog_confirmacao()