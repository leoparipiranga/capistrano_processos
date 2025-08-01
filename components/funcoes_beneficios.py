# components/funcoes_beneficios.py
import streamlit as st
import pandas as pd
import requests
import io
import base64
from datetime import datetime
import math
from components.functions_controle import (
    gerar_id_unico, garantir_coluna_id,
    get_github_api_info, save_data_to_github_seguro, 
    load_data_from_github, baixar_arquivo_drive
)

# =====================================
# CONFIGURAÇÕES DE PERFIS - BENEFÍCIOS
# =====================================

PERFIS_BENEFICIOS = {
    "Cadastrador": ["Implantado"],
    "Administrativo": ["Enviado para administrativo"],
    "Financeiro": ["Enviado para o financeiro"],
    "SAC": ["Enviado para administrativo", "Implantado", "Enviado para o financeiro"]  # SAC pode intervir em qualquer etapa
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
    """Lista de benefícios com paginação, filtros aprimorados e diálogo para ações."""
    
    # ORDENAR por data de cadastro mais recente, com NAs no final
    df_ordenado = df.copy()
    if "Data Cadastro" in df_ordenado.columns:
        # Converte para datetime para ordenar corretamente, tratando erros
        df_ordenado["_data_cadastro_dt"] = pd.to_datetime(
            df_ordenado["Data Cadastro"], format='%d/%m/%Y %H:%M', errors='coerce'
        )
        # Ordena por data (decrescente) e coloca os valores nulos (NaT) no final
        df_ordenado = df_ordenado.sort_values(
            by="_data_cadastro_dt", ascending=False, na_position='last'
        ).drop(columns=["_data_cadastro_dt"])

    # Inicializar estado do diálogo e paginação
    if "show_beneficio_dialog" not in st.session_state:
        st.session_state.show_beneficio_dialog = False
        st.session_state.beneficio_aberto_id = None
    if "current_page_beneficios" not in st.session_state:
        st.session_state.current_page_beneficios = 1

    # FILTROS
    st.markdown("### 🔍 Filtros")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_unicos = ["Todos"] + list(df["Status"].dropna().unique())
        filtro_status = st.selectbox(
            "Status:",
            options=status_unicos,
            key="beneficio_status_filter"
        )
    
    with col2:
        # Filtro por tipo de processo
        tipos_unicos = ["Todos"] + list(df["TIPO DE PROCESSO"].dropna().unique())
        filtro_tipo = st.selectbox(
            "Tipo de Processo:",
            options=tipos_unicos,
            key="beneficio_tipo_filter"
        )

    with col3:
        filtro_busca = st.text_input("Buscar por Parte, CPF ou Nº Processo:", key="beneficio_search")

    # Aplicar filtros
    df_filtrado = df_ordenado.copy()
    if filtro_status != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Status"] == filtro_status]
    if filtro_tipo != "Todos":
        df_filtrado = df_filtrado[df_filtrado["TIPO DE PROCESSO"] == filtro_tipo]
    if filtro_busca:
        df_filtrado = df_filtrado[
            df_filtrado["PARTE"].str.contains(filtro_busca, case=False, na=False) |
            df_filtrado["CPF"].str.contains(filtro_busca, case=False, na=False) |
            df_filtrado["Nº DO PROCESSO"].str.contains(filtro_busca, case=False, na=False)
        ]

    # Lógica de Paginação
    items_per_page = 20
    total_registros = len(df_filtrado)
    total_pages = math.ceil(total_registros / items_per_page) if items_per_page > 0 else 1
    
    if st.session_state.current_page_beneficios > total_pages:
        st.session_state.current_page_beneficios = 1

    start_idx = (st.session_state.current_page_beneficios - 1) * items_per_page
    end_idx = start_idx + items_per_page
    df_paginado = df_filtrado.iloc[start_idx:end_idx]

    # Exibir lista
    if not df_paginado.empty:
        st.markdown(f'<p style="font-size: small; color: steelblue;">Mostrando {start_idx+1} a {min(end_idx, total_registros)} de {total_registros} benefícios</p>', unsafe_allow_html=True)
        
        col_h1, col_h2, col_h3, col_h4, col_h5, col_h6 = st.columns([1, 3, 2, 2, 2, 2])
        with col_h1: st.markdown("**Ação**")
        with col_h2: st.markdown("**Parte**")
        with col_h3: st.markdown("**Processo**")
        with col_h4: st.markdown("**Tipo**")
        with col_h5: st.markdown("**Status**")
        with col_h6: st.markdown("**Data Cadastro**")
        st.markdown('<hr style="margin-top: 0.1rem; margin-bottom: 0.5rem;" />', unsafe_allow_html=True)

        for _, row in df_paginado.iterrows():
            col_b1, col_b2, col_b3, col_b4, col_b5, col_b6 = st.columns([1, 3, 2, 2, 2, 2])
            beneficio_id = row.get("ID")
            
            with col_b1:
                if st.button("🔓 Abrir", key=f"abrir_beneficio_id_{beneficio_id}"):
                    st.session_state.show_beneficio_dialog = True
                    st.session_state.beneficio_aberto_id = beneficio_id
                    st.rerun()
            
            with col_b2: st.write(f"**{row.get('PARTE', 'N/A')}**")
            with col_b3: st.write(row.get('Nº DO PROCESSO', 'N/A'))
            with col_b4: st.write(row.get('TIPO DE PROCESSO', 'N/A'))
            with col_b5: st.write(row.get('Status', 'N/A'))
            with col_b6:
                data_cadastro = row.get('Data Cadastro')
                # Verifica se o valor é NaN (float) ou None antes de tentar o split
                if pd.isna(data_cadastro):
                    st.write("N/A")
                else:
                    # Converte para string para garantir que o split funcione
                    st.write(str(data_cadastro).split(' ')[0])
    else:
        st.info("Nenhum benefício encontrado com os filtros aplicados.")


    # Implementação com st.dialog
    if st.session_state.get("show_beneficio_dialog"):
        beneficio_id_aberto = st.session_state.beneficio_aberto_id
        linha_beneficio = df[df["ID"] == beneficio_id_aberto]
        titulo = f"Detalhes do Benefício: {linha_beneficio.iloc[0].get('PARTE', 'N/A')}" if not linha_beneficio.empty else "Detalhes do Benefício"

        @st.dialog(titulo, width="large")
        def beneficio_dialog():
            if not linha_beneficio.empty:
                interface_edicao_beneficio(df, beneficio_id_aberto, perfil_usuario)
            else:
                st.error("❌ Benefício não encontrado.")
            
            if st.button("Fechar", key="fechar_beneficio_dialog"):
                st.session_state.show_beneficio_dialog = False
                st.rerun()
        
        beneficio_dialog()

    # Controles de paginação
    if total_pages > 1:
        st.markdown("---")
        col_nav1, col_nav2, col_nav3 = st.columns([3, 2, 3])
        with col_nav1:
            if st.session_state.current_page_beneficios > 1:
                if st.button("<< Primeira", key="ben_primeira"): st.session_state.current_page_beneficios = 1; st.rerun()
                if st.button("< Anterior", key="ben_anterior"): st.session_state.current_page_beneficios -= 1; st.rerun()
        with col_nav2:
            st.write(f"Página {st.session_state.current_page_beneficios} de {total_pages}")
        with col_nav3:
            if st.session_state.current_page_beneficios < total_pages:
                if st.button("Próxima >", key="ben_proxima"): st.session_state.current_page_beneficios += 1; st.rerun()
                if st.button("Última >>", key="ben_ultima"): st.session_state.current_page_beneficios = total_pages; st.rerun()

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
    """Interface para cadastrar novos benefícios, com validações e dicas."""

    # Inicializar contador para reset do formulário
    if "form_reset_counter_beneficios" not in st.session_state:
        st.session_state.form_reset_counter_beneficios = 0

    # Mostrar linhas temporárias (se existirem)
    if "preview_novas_linhas_beneficios" in st.session_state and len(st.session_state["preview_novas_linhas_beneficios"]) > 0:
        st.markdown("### 📋 Linhas Adicionadas (não salvas)")
        st.warning(f"⚠️ Você tem {len(st.session_state['preview_novas_linhas_beneficios'])} linha(s) não salva(s)")
        
        st.dataframe(st.session_state["preview_novas_linhas_beneficios"], use_container_width=True)
        
        col_salvar, col_limpar = st.columns(2)
        
        with col_salvar:
            if st.button("💾 Salvar Todas as Linhas", type="primary", key="salvar_beneficios"):
                from components.functions_controle import save_data_to_github_seguro
                with st.spinner("Salvando no GitHub..."):
                    novo_sha = save_data_to_github_seguro(
                        st.session_state.df_editado_beneficios,
                        "lista_beneficios.csv",
                        "file_sha_beneficios"
                    )
                
                if novo_sha:
                    st.session_state.file_sha_beneficios = novo_sha
                    del st.session_state["preview_novas_linhas_beneficios"]
                    st.toast("✅ Todas as linhas foram salvas com sucesso!", icon="🎉")
                    st.rerun()
                else:
                    st.error("❌ Falha ao salvar. Tente novamente.")

        with col_limpar:
            if st.button("🗑️ Descartar Linhas", type="secondary", key="descartar_beneficios"):
                num_linhas_remover = len(st.session_state["preview_novas_linhas_beneficios"])
                st.session_state.df_editado_beneficios = st.session_state.df_editado_beneficios.iloc[:-num_linhas_remover]
                del st.session_state["preview_novas_linhas_beneficios"]
                st.warning("🗑️ Linhas descartadas!")
                st.rerun()
        
        st.markdown("---")

    with st.form(f"adicionar_linha_form_beneficios_{st.session_state.form_reset_counter_beneficios}"):
        col1, col2 = st.columns(2)
        
        with col1:
            processo = st.text_input(
                "Nº DO PROCESSO *",
                placeholder="0000000-00.0000.0.00.0000",
                help="Ex: 0000000-00.0000.0.00.0000"
            )
            parte = st.text_input(
                "PARTE *",
                placeholder="Nome completo do beneficiário",
                help="O nome será convertido para maiúsculas automaticamente."
            ).upper()
            cpf = st.text_input(
                "CPF *",
                placeholder="000.000.000-00",
                help="Digite apenas os números.",
                max_chars=14
            )
            tipo_processo = st.selectbox(
                "TIPO DE PROCESSO *",
                ["", "LOAS", "LOAS DEFICIENTE", "LOAS IDOSO", "Aposentadoria por Invalidez", 
                 "Aposentadoria por Idade", "Auxílio Doença", "Auxílio Acidente", 
                 "Pensão por Morte", "Salário Maternidade", "Outros"],
                help="Selecione o tipo de benefício ou processo."
            )
        
        with col2:
            data_liminar = st.date_input(
                "DATA DA CONCESSÃO DA LIMINAR",
                value=None,
                help="Opcional: Data em que a liminar foi concedida."
            )
            prazo_fatal = st.date_input(
                "PROVÁVEL PRAZO FATAL PARA CUMPRIMENTO",
                value=None,
                help="Opcional: Prazo final para o cumprimento da obrigação."
            )
            observacoes = st.text_area(
                "OBSERVAÇÕES",
                placeholder="Detalhes importantes sobre o caso...",
                height=125
            )

        submitted = st.form_submit_button("📝 Adicionar Linha", type="primary", use_container_width=True)

    # Lógica de submissão
    if submitted:
        # Validações
        campos_obrigatorios = {"Nº DO PROCESSO": processo, "PARTE": parte, "CPF": cpf, "TIPO DE PROCESSO": tipo_processo}
        campos_vazios = [nome for nome, valor in campos_obrigatorios.items() if not valor or not valor.strip()]
        
        cpf_numeros = ''.join(filter(str.isdigit, cpf))
        
        if campos_vazios:
            st.error(f"❌ Preencha os campos obrigatórios: {', '.join(campos_vazios)}")
        elif cpf and len(cpf_numeros) != 11:
            st.error(f"❌ O CPF '{cpf}' é inválido. Deve conter 11 números.")
        else:
            from components.functions_controle import gerar_id_unico
            
            nova_linha = {
                "ID": gerar_id_unico(st.session_state.df_editado_beneficios, "ID"),
                "Nº DO PROCESSO": processo,
                "PARTE": parte,
                "CPF": cpf_numeros, # Salva apenas os números
                "TIPO DE PROCESSO": tipo_processo,
                "DATA DA CONCESSÃO DA LIMINAR": data_liminar.strftime("%d/%m/%Y") if data_liminar else "",
                "PROVÁVEL PRAZO FATAL PARA CUMPRIMENTO": prazo_fatal.strftime("%d/%m/%Y") if prazo_fatal else "",
                "OBSERVAÇÕES": observacoes,
                "Status": "Enviado para administrativo",
                "Data Cadastro": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Cadastrado Por": st.session_state.get("usuario", "Sistema")
            }
            
            # Adicionar ao DataFrame em memória
            df_nova_linha = pd.DataFrame([nova_linha])
            st.session_state.df_editado_beneficios = pd.concat(
                [st.session_state.df_editado_beneficios, df_nova_linha],
                ignore_index=True
            )
            
            # Adicionar ao preview
            if "preview_novas_linhas_beneficios" not in st.session_state:
                st.session_state["preview_novas_linhas_beneficios"] = pd.DataFrame()
            st.session_state["preview_novas_linhas_beneficios"] = pd.concat(
                [st.session_state["preview_novas_linhas_beneficios"], df_nova_linha],
                ignore_index=True
            )

            st.session_state.form_reset_counter_beneficios += 1
            st.toast("✅ Linha adicionada! Salve para persistir os dados.", icon="👍")
            st.rerun()

def interface_edicao_beneficio(df, beneficio_id, perfil_usuario):
    """
    Interface de edição com o fluxo de trabalho corrigido e adaptada para st.dialog.
    """
    from components.functions_controle import salvar_arquivo, baixar_arquivo_drive

    linha_beneficio = df[df["ID"] == beneficio_id].iloc[0]
    status_atual = linha_beneficio.get("Status", "N/A")
    processo = linha_beneficio.get("Nº DO PROCESSO", "N/A")

    st.markdown(f"**ID:** `{beneficio_id}` | **Beneficiário:** {linha_beneficio.get('PARTE', 'N/A')}")
    st.markdown(f"**Status atual:** {status_atual}")
    st.markdown("---")

    # ETAPA 1: Cadastrador cria -> Status 'Enviado para administrativo' (Tratado no cadastro)

    # ETAPA 2: Administrativo recebe, analisa e marca como implantado.
    if status_atual == "Enviado para administrativo" and perfil_usuario == "Administrativo":
        st.markdown("#### 🔧 Análise Administrativa")
        st.info("Após inserir os documentos no Korbil, marque a caixa abaixo e salve.")
        
        korbil_ok = st.checkbox("Carta de Concessão e Histórico de Crédito inseridos no Korbil")
        
        if st.button("💾 Salvar e Devolver para Cadastrador", type="primary", disabled=not korbil_ok):
            atualizar_status_beneficio(beneficio_id, "Implantado", df)

    # ETAPA 3: Cadastrador recebe, verifica e envia para o financeiro.
    elif status_atual == "Implantado" and perfil_usuario == "Cadastrador":
        st.markdown("#### 🔍 Verificação e Definição de Valores")
        st.info("Confira os dados, informe os valores e confirme a verificação para prosseguir.")

        col1, col2 = st.columns(2)
        with col1:
            valor_beneficio = st.text_input("Valor do Benefício *", placeholder="Ex: 1850.75")
        with col2:
            percentual_cobranca = st.text_input("Percentual a ser Cobrado *", placeholder="Ex: 30%")
        
        processo_verificado = st.checkbox("Processo verificado")

        if st.button("📤 Enviar para Financeiro", type="primary", disabled=not processo_verificado):
            if valor_beneficio and percentual_cobranca:
                atualizar_status_beneficio(
                    beneficio_id, "Enviado para o financeiro", df,
                    valor_beneficio=valor_beneficio,
                    percentual_cobranca=percentual_cobranca
                )
            else:
                st.error("❌ Preencha o Valor do Benefício e o Percentual a ser Cobrado.")

    # ETAPA 4: Financeiro recebe e finaliza o pagamento.
    elif status_atual == "Enviado para o financeiro" and perfil_usuario == "Financeiro":
        st.markdown("#### 💰 Finalização Financeira")
        st.info("Anexe o comprovante de pagamento ou marque como pago em dinheiro para finalizar.")

        pago_em_dinheiro = st.checkbox("Pago em dinheiro")
        
        comprovante = None
        if not pago_em_dinheiro:
            comprovante = st.file_uploader("Comprovante de Pagamento ou Boleto *", type=["pdf", "jpg", "png"])

        # Lógica de habilitação do botão
        pode_finalizar = (pago_em_dinheiro) or (not pago_em_dinheiro and comprovante is not None)

        if st.button("✅ Finalizar Benefício", type="primary", disabled=not pode_finalizar):
            comprovante_url = ""
            tipo_pagamento = "Dinheiro" if pago_em_dinheiro else "Anexo"
            
            if comprovante:
                with st.spinner("Enviando anexo..."):
                    comprovante_url = salvar_arquivo(comprovante, processo, "pagamento_beneficio")
            
            atualizar_dados_finalizacao(
                beneficio_id, "Finalizado", df,
                comprovante_url=comprovante_url,
                tipo_pagamento=tipo_pagamento
            )

    # BENEFÍCIO FINALIZADO - Apenas visualização
    elif status_atual == "Finalizado":
        st.markdown("#### 🎉 Benefício Finalizado")
        st.success("✅ Este benefício foi concluído com sucesso!")
        
        # Mostrar informações finais
        col_final1, col_final2 = st.columns(2)
        
        with col_final1:
            st.markdown("**💰 Informações do Pagamento:**")
            st.write(f"- Tipo: {linha_beneficio.get('Tipo Pagamento', 'N/A')}")
            
            # FORMATAR VALOR CORRETAMENTE
            valor_pago = linha_beneficio.get('Valor Pago', 0)
            if valor_pago and str(valor_pago).replace('.', '').isdigit():
                valor_formatado = f"R$ {float(valor_pago):,.2f}"
            else:
                valor_formatado = "N/A"
            
            st.write(f"- Valor: {valor_formatado}")
            st.write(f"- Data: {linha_beneficio.get('Data Finalização', 'N/A')}")
            
            if linha_beneficio.get("Comprovante Pagamento"):
                st.markdown("**📎 Comprovante:**")
                baixar_arquivo_drive(linha_beneficio["Comprovante Pagamento"], "📎 Baixar Comprovante")
        
            
            with col_final2:
                st.markdown("**📋 Informações do Benefício:**")
                st.write(f"- Benefício: {linha_beneficio.get('Benefício Verificado', 'N/A')}")
                st.write(f"- Percentual: {linha_beneficio.get('Percentual Cobrança', 'N/A')}")
                st.write(f"- Finalizado por: {linha_beneficio.get('Finalizado Por', 'N/A')}")
            
            # Timeline
            st.markdown("**📅 Timeline do Benefício:**")
            timeline_data = []
            if linha_beneficio.get("Data Cadastro"):
                timeline_data.append(f"• **Cadastrado:** {linha_beneficio['Data Cadastro']} por {linha_beneficio.get('Cadastrado Por', 'N/A')}")
            if linha_beneficio.get("Data Envio Administrativo"):
                timeline_data.append(f"• **Enviado para Administrativo:** {linha_beneficio['Data Envio Administrativo']} por {linha_beneficio.get('Enviado Administrativo Por', 'N/A')}")
            if linha_beneficio.get("Data Implantação"):
                timeline_data.append(f"• **Implantado:** {linha_beneficio['Data Implantação']} por {linha_beneficio.get('Implantado Por', 'N/A')}")
            if linha_beneficio.get("Data Envio Financeiro"):
                timeline_data.append(f"• **Enviado para Financeiro:** {linha_beneficio['Data Envio Financeiro']} por {linha_beneficio.get('Enviado Financeiro Por', 'N/A')}")
            if linha_beneficio.get("Data Finalização"):
                timeline_data.append(f"• **Finalizado:** {linha_beneficio['Data Finalização']} por {linha_beneficio.get('Finalizado Por', 'N/A')}")
            
            for item in timeline_data:
                st.markdown(item)
    
    # ACESSO NEGADO
    else:
        if not pode_editar_status_beneficios(status_atual, perfil_usuario):
            st.error(f"❌ Seu perfil ({perfil_usuario}) não pode editar benefícios com status '{status_atual}'")

def atualizar_status_beneficio(beneficio_id, novo_status, df, **kwargs):
    """
    Atualiza o status e outros campos de um benefício, salva e fecha o diálogo.
    """
    from components.functions_controle import save_data_to_github_seguro
    
    if "df_editado_beneficios" not in st.session_state:
        st.session_state.df_editado_beneficios = df.copy()

    idx = st.session_state.df_editado_beneficios[st.session_state.df_editado_beneficios["ID"] == beneficio_id].index
    if idx.empty:
        st.error("Erro: ID do benefício não encontrado para atualização."); return

    usuario_atual = st.session_state.get("usuario", "Sistema")
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")

    st.session_state.df_editado_beneficios.loc[idx, "Status"] = novo_status

    if novo_status == "Implantado":
        st.session_state.df_editado_beneficios.loc[idx, "Data Implantação"] = data_atual
        st.session_state.df_editado_beneficios.loc[idx, "Implantado Por"] = usuario_atual
    
    elif novo_status == "Enviado para o financeiro":
        st.session_state.df_editado_beneficios.loc[idx, "Data Envio Financeiro"] = data_atual
        st.session_state.df_editado_beneficios.loc[idx, "Enviado Financeiro Por"] = usuario_atual
        # Salva os novos campos de valor e percentual
        if 'valor_beneficio' in kwargs:
            st.session_state.df_editado_beneficios.loc[idx, "Valor do Benefício"] = kwargs['valor_beneficio']
        if 'percentual_cobranca' in kwargs:
            st.session_state.df_editado_beneficios.loc[idx, "Percentual Cobrança"] = kwargs['percentual_cobranca']

    # Salvar e fechar
    novo_sha = save_data_to_github_seguro(st.session_state.df_editado_beneficios, "lista_beneficios.csv", "file_sha_beneficios")
    if novo_sha:
        st.session_state.file_sha_beneficios = novo_sha
        st.toast(f"Status atualizado para: {novo_status}", icon="✅")
        st.session_state.show_beneficio_dialog = False
        st.rerun()
    else:
        st.error("Falha ao salvar a atualização.")

def atualizar_dados_finalizacao(beneficio_id, novo_status, df, comprovante_url, tipo_pagamento):
    """Atualiza os dados de finalização de um benefício, salva e fecha o diálogo."""
    from components.functions_controle import save_data_to_github_seguro

    if "df_editado_beneficios" not in st.session_state:
        st.session_state.df_editado_beneficios = df.copy()

    idx = st.session_state.df_editado_beneficios[st.session_state.df_editado_beneficios["ID"] == beneficio_id].index
    if idx.empty:
        st.error("Erro: ID do benefício não encontrado para finalização."); return

    usuario_atual = st.session_state.get("usuario", "Sistema")
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")

    st.session_state.df_editado_beneficios.loc[idx, "Status"] = novo_status
    st.session_state.df_editado_beneficios.loc[idx, "Data Finalização"] = data_atual
    st.session_state.df_editado_beneficios.loc[idx, "Finalizado Por"] = usuario_atual
    st.session_state.df_editado_beneficios.loc[idx, "Comprovante Pagamento"] = comprovante_url
    st.session_state.df_editado_beneficios.loc[idx, "Tipo Pagamento"] = tipo_pagamento

    # Salvar e fechar
    novo_sha = save_data_to_github_seguro(st.session_state.df_editado_beneficios, "lista_beneficios.csv", "file_sha_beneficios")
    if novo_sha:
        st.session_state.file_sha_beneficios = novo_sha
        st.toast("Benefício finalizado com sucesso!", icon="🎉")
        st.balloons()
        st.session_state.show_beneficio_dialog = False
        st.rerun()
    else:
        st.error("Falha ao salvar a finalização.")

def interface_visualizar_dados_beneficios(df):
    """Interface aprimorada para visualizar dados e métricas dos Benefícios com paginação."""
    st.subheader("📁 Visualizar Dados - Benefícios")
    
    if df.empty:
        st.info("📋 Nenhum benefício cadastrado para visualizar.")
        return

    # Inicializar estado da paginação para esta aba
    if "current_page_vis_beneficios" not in st.session_state:
        st.session_state.current_page_vis_beneficios = 1
    
    # --- Métricas Resumo ---
    st.markdown("#### 📊 Resumo Geral")
    col_resumo1, col_resumo2, col_resumo3, col_resumo4 = st.columns(4)
    
    with col_resumo1:
        st.metric("Total de Benefícios", len(df))
    with col_resumo2:
        finalizados = len(df[df["Status"] == "Finalizado"]) if "Status" in df.columns else 0
        st.metric("Benefícios Finalizados", finalizados)
    with col_resumo3:
        tipos_unicos = df["TIPO DE PROCESSO"].nunique() if "TIPO DE PROCESSO" in df.columns else 0
        st.metric("Tipos de Processo", tipos_unicos)
    with col_resumo4:
        if "Valor do Benefício" in df.columns:
            valores_numericos = pd.to_numeric(df["Valor do Benefício"], errors='coerce').dropna()
            total_valor = valores_numericos.sum()
            st.metric("Valor Total (Benefícios)", f"R$ {total_valor:,.2f}")
        else:
            st.metric("Valor Total (Benefícios)", "N/A")
    
    st.markdown("---")

    # --- Filtros ---
    st.markdown("#### 🔍 Filtros e Pesquisa")
    col_filtro1, col_filtro2, col_filtro3 = st.columns([2, 2, 3])
    
    df_visualizado = df.copy()

    with col_filtro1:
        if "Status" in df_visualizado.columns:
            status_options = ["Todos"] + list(df_visualizado["Status"].dropna().unique())
            status_filtro = st.selectbox("Filtrar por Status:", options=status_options, key="vis_status_beneficio")
            if status_filtro != "Todos":
                df_visualizado = df_visualizado[df_visualizado["Status"] == status_filtro]
    
    with col_filtro2:
        if "TIPO DE PROCESSO" in df_visualizado.columns:
            tipo_options = ["Todos"] + list(df_visualizado["TIPO DE PROCESSO"].dropna().unique())
            tipo_filtro = st.selectbox("Filtrar por Tipo:", options=tipo_options, key="vis_tipo_beneficio")
            if tipo_filtro != "Todos":
                df_visualizado = df_visualizado[df_visualizado["TIPO DE PROCESSO"] == tipo_filtro]
    
    with col_filtro3:
        busca_texto = st.text_input("Buscar por Nº do Processo ou Parte:", key="vis_busca_beneficio")
        if busca_texto:
            df_visualizado = df_visualizado[
                df_visualizado["Nº DO PROCESSO"].str.contains(busca_texto, case=False, na=False) |
                df_visualizado["PARTE"].str.contains(busca_texto, case=False, na=False)
            ]

    # --- Lógica de Paginação ---
    items_per_page = 10
    total_registros = len(df_visualizado)
    total_pages = math.ceil(total_registros / items_per_page) if items_per_page > 0 else 1
    
    if st.session_state.current_page_vis_beneficios > total_pages:
        st.session_state.current_page_vis_beneficios = 1

    start_idx = (st.session_state.current_page_vis_beneficios - 1) * items_per_page
    end_idx = start_idx + items_per_page
    df_paginado = df_visualizado.iloc[start_idx:end_idx]

    # --- Tabela de Dados ---
    st.markdown(f"#### 📊 Dados ({total_registros} registros encontrados)")
    
    colunas_exibir = [
        "Nº DO PROCESSO", "PARTE", "Status", "Data Cadastro", 
        "TIPO DE PROCESSO", "Valor do Benefício"
    ]
    colunas_disponiveis = [col for col in colunas_exibir if col in df_visualizado.columns]

    # Botões de Download (para os dados filtrados completos)
    if not df_visualizado.empty:
        col_btn1, col_btn2, _ = st.columns([1.5, 1.5, 7])
        with col_btn1:
            csv = df_visualizado[colunas_disponiveis].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar CSV", data=csv, file_name="beneficios_filtrados.csv",
                mime="text/csv", use_container_width=True
            )
        with col_btn2:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_visualizado[colunas_disponiveis].to_excel(writer, index=False, sheet_name='Beneficios')
            excel_data = output.getvalue()
            st.download_button(
                label="📥 Baixar Excel", data=excel_data, file_name="beneficios_filtrados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True
            )

    # Tabela com dados paginados
    if not df_paginado.empty:
        st.markdown(f'<p style="font-size: small; color: steelblue;">Mostrando {start_idx+1} a {min(end_idx, total_registros)} de {total_registros} registros</p>', unsafe_allow_html=True)
        st.dataframe(
            df_paginado[colunas_disponiveis],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Nenhum registro encontrado com os filtros aplicados.")

    # --- Controles de Paginação ---
    if total_pages > 1:
        st.markdown("---")
        col_nav1, col_nav2, col_nav3 = st.columns([3, 2, 3])
        with col_nav1:
            if st.session_state.current_page_vis_beneficios > 1:
                if st.button("<< Primeira", key="vis_ben_primeira"): st.session_state.current_page_vis_beneficios = 1; st.rerun()
                if st.button("< Anterior", key="vis_ben_anterior"): st.session_state.current_page_vis_beneficios -= 1; st.rerun()
        with col_nav2:
            st.write(f"Página {st.session_state.current_page_vis_beneficios} de {total_pages}")
        with col_nav3:
            if st.session_state.current_page_vis_beneficios < total_pages:
                if st.button("Próxima >", key="vis_ben_proxima"): st.session_state.current_page_vis_beneficios += 1; st.rerun()
                if st.button("Última >>", key="vis_ben_ultima"): st.session_state.current_page_vis_beneficios = total_pages; st.rerun()

# =====================================
# FUNÇÕES DE EXPORTAÇÃO E IMPORTAÇÃO - BENEFÍCIOS
# =====================================

def carregar_beneficios():
    """Carrega os dados de benefícios do GitHub"""
    df, file_sha = load_data_from_github("lista_beneficios.csv")
    
    # Garantir que o DataFrame tenha a coluna ID
    df = garantir_coluna_id(df)
    
    return df