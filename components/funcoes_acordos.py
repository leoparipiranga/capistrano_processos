# components/funcoes_acordos.py
import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta
import math
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode, JsCode
from components.autocomplete_manager import (
    inicializar_autocomplete_session,
    adicionar_assunto_beneficio,
    campo_assunto_beneficio
)
from components.functions_controle import (
    # Funções GitHub
    get_github_api_info, load_data_from_github,
    save_data_local, save_data_to_github_seguro,
    
    # Funções de arquivo
    salvar_arquivo, baixar_arquivo_drive,
    gerar_id_unico, garantir_coluna_id,
    
    # Funções de limpeza comuns
    limpar_campos_formulario,
    
    # Função de cores de status
    obter_cor_status
)

def safe_get_value_acordo(data, key, default='Não cadastrado'):
    """Obtém valor de forma segura, tratando NaN e valores None"""
    value = data.get(key, default)
    if value is None:
        return default
    # Converter para string e verificar se não é 'nan'
    str_value = str(value)
    if str_value.lower() in ['nan', 'none', '']:
        return default
    return str_value

def safe_get_float_value_acordo(data, key, default=0.0):
    """Obtém valor float de forma segura para Acordos"""
    value = data.get(key, default)
    if pd.isna(value) or value == "nan" or value == "" or value is None:
        return default
    try:
        # Remove formatação brasileira se presente
        if isinstance(value, str):
            value = value.replace("R$", "").replace(".", "").replace(",", ".").strip()
        return float(value)
    except (ValueError, TypeError):
        return default

def limpar_estados_dialogo_acordo():
    """Limpa todos os estados relacionados aos diálogos de acordos"""
    st.session_state.show_acordo_dialog = False
    st.session_state.acordo_aberto_id = None

def proximo_dia_util(data):
    """Calcula o próximo dia útil a partir de uma data"""
    # Se for sábado ou domingo, vai para segunda
    if data.weekday() == 5:  # Sábado
        return data + timedelta(days=2)
    elif data.weekday() == 6:  # Domingo
        return data + timedelta(days=1)
    return data

def calcular_datas_parcelas(data_primeiro_pagamento, num_parcelas):
    """Calcula as datas de pagamento das parcelas (30 dias úteis entre elas)"""
    datas = []
    data_atual = datetime.strptime(data_primeiro_pagamento, "%Y-%m-%d")
    
    for i in range(num_parcelas):
        if i == 0:
            # Primeira parcela usa a data informada
            datas.append(proximo_dia_util(data_atual))
        else:
            # Próximas parcelas: 30 dias depois
            data_atual = data_atual + timedelta(days=30)
            datas.append(proximo_dia_util(data_atual))
    
    return datas

def interface_cadastro_acordo(df, perfil_usuario):
    """Interface para cadastro de novos acordos"""
    
    # Verificar permissões
    perfis_permitidos = ["Admin", "Cadastrador"]
    if perfil_usuario not in perfis_permitidos:
        st.warning("⚠️ Você não tem permissão para cadastrar acordos.")
        return

    with st.form("form_cadastro_acordo"):
        # Dados básicos do processo
        col1, col2 = st.columns(2)
        
        with col1:
            processo = st.text_input(
                "Número do Processo *",
                placeholder="Ex: 0001234-56.2024.5.02.0001",
                help="Número completo do processo judicial"
            )
            nome_reu = st.text_input(
                "Nome do Réu *",
                placeholder="Nome completo da parte ré",
                help="Nome da empresa/pessoa que vai pagar"
            )
            cpf_reu = st.text_input(
                "CPF/CNPJ do Réu *",
                placeholder="000.000.000-00 ou 00.000.000/0001-00",
                help="CPF ou CNPJ da parte ré"
            )
        
        with col2:
            nome_cliente = st.text_input(
                "Nome do Cliente *",
                placeholder="Nome completo do cliente",
                help="Nome da pessoa/empresa que vai receber"
            )
            cpf_cliente = st.text_input(
                "CPF/CNPJ do Cliente *",
                placeholder="000.000.000-00 ou 00.000.000/0001-00",
                help="CPF ou CNPJ do cliente"
            )
            banco = st.selectbox(
                "Banco *",
                ["", "CEF", "BB", "Bradesco", "Itaú", "Santander", "Outro"],
                help="Banco onde será feito o depósito"
            )

        # Dados do acordo
        st.markdown("---")

        col3, col4 = st.columns(2)
        
        with col3:
            valor_total = st.number_input(
                "Valor Total do Acordo *",
                min_value=0.0,
                format="%.2f",
                help="Valor total que será pago"
            )
            forma_acordo = st.selectbox(
                "Forma do Acordo *",
                ["", "Judicial", "Extrajudicial", "Administrativo"],
                help="Tipo de acordo firmado"
            )
        
        with col4:
            a_vista = st.checkbox(
                "Pagamento à Vista",
                help="Marque se o pagamento será à vista"
            )
            
            if not a_vista:
                num_parcelas = st.number_input(
                    "Número de Parcelas",
                    min_value=1,
                    max_value=24,
                    value=1,
                    help="Quantidade de parcelas para pagamento"
                )
            else:
                num_parcelas = 1
        
        # Data do primeiro pagamento
        data_primeiro_pagamento = st.date_input(
            "Data do Primeiro Pagamento *",
            value=datetime.now().date(),
            help="Data prevista para o primeiro pagamento"
        )
        
        # Observações
        observacoes = st.text_area(
            "Observações",
            placeholder="Informações adicionais sobre o acordo...",
            help="Campo livre para observações gerais"
        )

        submitted = st.form_submit_button("Cadastrar Acordo", type="primary")
        
        if submitted:
            # Validação dos campos obrigatórios
            if not all([processo, nome_reu, cpf_reu, nome_cliente, cpf_cliente, banco, valor_total > 0, forma_acordo]):
                st.error("❌ Por favor, preencha todos os campos obrigatórios marcados com *")
                return
            
            # Gerar ID único
            novo_id = gerar_id_unico()
            
            # Preparar dados do novo acordo
            novo_acordo = {
                "ID": novo_id,
                "Processo": processo,
                "Nome_Reu": nome_reu,
                "CPF_Reu": cpf_reu,
                "Nome_Cliente": nome_cliente,
                "CPF_Cliente": cpf_cliente,
                "Banco": banco,
                "Valor_Total": valor_total,
                "Forma_Acordo": forma_acordo,
                "A_Vista": a_vista,
                "Num_Parcelas": num_parcelas,
                "Data_Primeiro_Pagamento": data_primeiro_pagamento.strftime("%Y-%m-%d"),
                "Status": "Aguardando Pagamento",
                "Cadastrado_Por": st.session_state.get("usuario", "admin"),
                "Data_Cadastro": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "Comprovante_Pago": "",
                "Honorarios_Contratuais": 0.0,
                "Valor_Cliente": 0.0,
                "H_Sucumbenciais": 0.0,
                "Valor_Parceiro": 0.0,
                "Outros_Valores": 0.0,
                "Observacoes": observacoes,
                "Valor_Atualizado": 0.0,
                "Houve_Renegociacao": False,
                "Nova_Num_Parcelas": 0,
                "Novo_Valor_Parcela": 0.0,
                "Acordo_Nao_Cumprido": False,
                "Data_Ultimo_Update": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "Usuario_Ultimo_Update": st.session_state.get("usuario", "admin")
            }
            
            # Adicionar ao DataFrame
            df_novo = pd.concat([df, pd.DataFrame([novo_acordo])], ignore_index=True)
            
            # Salvar
            success = save_data_to_github_seguro(df_novo, "lista_acordos.csv", "file_sha_acordos")
            
            if success:
                st.session_state.df_editado_acordos = df_novo
                st.success(f"✅ Acordo cadastrado com sucesso! ID: {novo_id}")
                st.rerun()
            else:
                st.error("❌ Erro ao salvar o acordo. Tente novamente.")

def interface_lista_acordos(df, perfil_usuario):
    """Interface para listar e gerenciar acordos"""
    
    st.header("📊 Lista de Acordos")
    
    if df.empty:
        st.info("📋 Nenhum acordo cadastrado ainda.")
        return
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filtro_status = st.selectbox(
            "📊 Filtrar por Status",
            ["Todos"] + list(df["Status"].unique()) if "Status" in df.columns else ["Todos"],
            key="filtro_status_acordos"
        )
    
    with col2:
        filtro_busca = st.text_input(
            "🔍 Buscar",
            placeholder="Nome, CPF ou processo...",
            help="Busque por nome do cliente/réu, CPF ou número do processo",
            key="filtro_busca_acordos"
        )
    
    with col3:
        st.metric("📈 Total de Acordos", len(df))
    
    # Aplicar filtros
    df_filtrado = df.copy()
    
    if filtro_status != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Status"] == filtro_status]
    
    if filtro_busca:
        mask = (
            df_filtrado["Nome_Cliente"].str.contains(filtro_busca, case=False, na=False) |
            df_filtrado["Nome_Reu"].str.contains(filtro_busca, case=False, na=False) |
            df_filtrado["CPF_Cliente"].str.contains(filtro_busca, case=False, na=False) |
            df_filtrado["CPF_Reu"].str.contains(filtro_busca, case=False, na=False) |
            df_filtrado["Processo"].str.contains(filtro_busca, case=False, na=False)
        )
        df_filtrado = df_filtrado[mask]
    
    if df_filtrado.empty:
        st.info("🔍 Nenhum acordo encontrado com os filtros aplicados.")
        return
    
    # Configurar AgGrid
    gb = GridOptionsBuilder.from_dataframe(df_filtrado)
    gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, editable=False)
    gb.configure_column("ID", hide=True)
    gb.configure_column("Processo", header_name="📋 Processo", width=150)
    gb.configure_column("Nome_Cliente", header_name="👤 Cliente", width=200)
    gb.configure_column("Nome_Reu", header_name="⚖️ Réu", width=200)
    gb.configure_column("Valor_Total", header_name="💰 Valor", width=120)
    gb.configure_column("Status", header_name="📊 Status", width=150)
    gb.configure_column("Data_Cadastro", header_name="📅 Cadastro", width=120)
    
    # Ocultar colunas desnecessárias na lista
    colunas_ocultar = [
        "CPF_Reu", "CPF_Cliente", "Banco", "Forma_Acordo", "A_Vista", 
        "Num_Parcelas", "Data_Primeiro_Pagamento", "Cadastrado_Por",
        "Comprovante_Pago", "Honorarios_Contratuais", "Valor_Cliente",
        "H_Sucumbenciais", "Valor_Parceiro", "Outros_Valores", "Observacoes",
        "Valor_Atualizado", "Houve_Renegociacao", "Nova_Num_Parcelas",
        "Novo_Valor_Parcela", "Acordo_Nao_Cumprido", "Data_Ultimo_Update",
        "Usuario_Ultimo_Update"
    ]
    
    for coluna in colunas_ocultar:
        if coluna in df_filtrado.columns:
            gb.configure_column(coluna, hide=True)
    
    gb.configure_selection('single')
    gridOptions = gb.build()
    
    # Renderizar grid
    grid_response = AgGrid(
        df_filtrado,
        gridOptions=gridOptions,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        height=400,
        theme="alpine"
    )
    
    # Processar seleção
    selected_rows = grid_response['selected_rows']
    
    if selected_rows is not None and len(selected_rows) > 0:
        acordo_selecionado = selected_rows[0]
        acordo_id = acordo_selecionado['ID']
        
        # Botões de ação
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            if st.button("👁️ Ver Detalhes", key=f"ver_acordo_{acordo_id}"):
                # Criar request de diálogo
                request_id = f"dialogo_acordo_request_{datetime.now().timestamp()}"
                st.session_state[request_id] = {
                    "show_acordo_dialog": True,
                    "acordo_aberto_id": acordo_id
                }
                st.rerun()
        
        with col_btn2:
            if st.button("✏️ Editar", key=f"editar_acordo_{acordo_id}"):
                # Verificar permissões para edição
                perfis_edicao = ["Admin", "Cadastrador", "Financeiro"]
                if perfil_usuario in perfis_edicao:
                    request_id = f"dialogo_acordo_request_{datetime.now().timestamp()}"
                    st.session_state[request_id] = {
                        "show_acordo_dialog": True,
                        "acordo_aberto_id": acordo_id
                    }
                    st.rerun()
                else:
                    st.warning("⚠️ Você não tem permissão para editar acordos.")
        
        with col_btn3:
            if st.button("🗑️ Excluir", key=f"excluir_acordo_{acordo_id}"):
                # Verificar permissões para exclusão
                if perfil_usuario == "Admin":
                    st.session_state[f"confirmar_exclusao_acordo_{acordo_id}"] = True
                    st.rerun()
                else:
                    st.warning("⚠️ Apenas administradores podem excluir acordos.")
        
        # Confirmar exclusão
        if st.session_state.get(f"confirmar_exclusao_acordo_{acordo_id}", False):
            st.warning("⚠️ Tem certeza que deseja excluir este acordo?")
            col_conf1, col_conf2 = st.columns(2)
            
            with col_conf1:
                if st.button("✅ Sim, excluir", key=f"confirmar_excl_{acordo_id}"):
                    # Excluir o acordo
                    df_novo = df[df["ID"] != acordo_id].copy()
                    success = save_data_to_github_seguro(df_novo, "lista_acordos.csv", "file_sha_acordos")
                    
                    if success:
                        st.session_state.df_editado_acordos = df_novo
                        # Limpar estado de confirmação
                        del st.session_state[f"confirmar_exclusao_acordo_{acordo_id}"]
                        st.success("✅ Acordo excluído com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Erro ao excluir acordo.")
            
            with col_conf2:
                if st.button("❌ Cancelar", key=f"cancelar_excl_{acordo_id}"):
                    del st.session_state[f"confirmar_exclusao_acordo_{acordo_id}"]
                    st.rerun()

def interface_edicao_acordo(df, acordo_id, perfil_usuario):
    """Interface para edição de acordos"""
    
    # Buscar dados do acordo
    linha_acordo = df[df["ID"].astype(str) == str(acordo_id)]
    
    if linha_acordo.empty:
        st.error("❌ Acordo não encontrado.")
        return
    
    acordo_data = linha_acordo.iloc[0].to_dict()
    
    # Verificar permissões baseadas no status e perfil
    status_atual = safe_get_value_acordo(acordo_data, "Status", "Aguardando Pagamento")
    
    st.subheader(f"✏️ Editando: {safe_get_value_acordo(acordo_data, 'Nome_Cliente')}")
    
    # Mostrar informações básicas
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        st.info(f"📋 **Processo:** {safe_get_value_acordo(acordo_data, 'Processo')}")
        st.info(f"👤 **Cliente:** {safe_get_value_acordo(acordo_data, 'Nome_Cliente')}")
        st.info(f"💰 **Valor Total:** R$ {safe_get_float_value_acordo(acordo_data, 'Valor_Total', 0):.2f}")
    
    with col_info2:
        st.info(f"⚖️ **Réu:** {safe_get_value_acordo(acordo_data, 'Nome_Reu')}")
        st.info(f"📊 **Status Atual:** {status_atual}")
        st.info(f"🔢 **Parcelas:** {safe_get_float_value_acordo(acordo_data, 'Num_Parcelas', 1):.0f}")
    
    # Interface baseada no perfil e status
    if perfil_usuario == "Cadastrador":
        interface_cadastrador_acordo(df, acordo_data, acordo_id)
    elif perfil_usuario == "Financeiro":
        interface_financeiro_acordo(df, acordo_data, acordo_id)
    elif perfil_usuario == "Admin":
        # Admin pode acessar todas as interfaces
        tab_cad, tab_fin = st.tabs(["👤 Visão Cadastrador", "💰 Visão Financeiro"])
        
        with tab_cad:
            interface_cadastrador_acordo(df, acordo_data, acordo_id)
        
        with tab_fin:
            interface_financeiro_acordo(df, acordo_data, acordo_id)
    else:
        st.warning("⚠️ Você não tem permissão para editar este acordo.")

def interface_cadastrador_acordo(df, acordo_data, acordo_id):
    """Interface específica para cadastradores"""
    
    st.subheader("👤 Área do Cadastrador")
    
    status_atual = safe_get_value_acordo(acordo_data, "Status", "Aguardando Pagamento")
    
    # Upload de comprovante quando Rodrigo envia
    if status_atual == "Aguardando Pagamento":
        st.info("💡 **Próxima ação:** Aguardando comprovante de pagamento da primeira parcela")
        
        comprovante = st.file_uploader(
            "📎 Upload do Comprovante de Pagamento",
            type=['pdf', 'jpg', 'jpeg', 'png'],
            help="Faça upload do comprovante enviado por Rodrigo"
        )
        
        if comprovante and st.button("📤 Enviar para Financeiro"):
            # Salvar arquivo (aqui você implementaria a lógica de salvar no Google Drive)
            # Por enquanto, apenas atualizar o status
            
            # Atualizar dados
            idx = df[df["ID"].astype(str) == str(acordo_id)].index[0]
            df.loc[idx, "Status"] = "Enviado para Financeiro"
            df.loc[idx, "Comprovante_Pago"] = comprovante.name
            df.loc[idx, "Data_Ultimo_Update"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            df.loc[idx, "Usuario_Ultimo_Update"] = st.session_state.get("usuario", "admin")
            
            # Salvar
            success = save_data_to_github_seguro(df, "lista_acordos.csv", "file_sha_acordos")
            
            if success:
                st.session_state.df_editado_acordos = df
                st.success("✅ Comprovante enviado para o financeiro!")
                st.rerun()
            else:
                st.error("❌ Erro ao atualizar status.")
    
    else:
        st.info(f"📊 Status atual: **{status_atual}**")
        if status_atual == "Enviado para Financeiro":
            st.info("⏳ Aguardando processamento pelo financeiro...")

def interface_financeiro_acordo(df, acordo_data, acordo_id):
    """Interface específica para financeiro"""
    
    st.subheader("💰 Área do Financeiro")
    
    status_atual = safe_get_value_acordo(acordo_data, "Status", "Aguardando Pagamento")
    
    if status_atual == "Enviado para Financeiro":
        st.info("💡 **Ação necessária:** Registrar dados do pagamento")
        
        with st.form(f"form_financeiro_{acordo_id}"):
            col1, col2 = st.columns(2)
            
            with col1:
                honorarios_contratuais = st.number_input(
                    "💼 Honorários Contratuais",
                    value=safe_get_float_value_acordo(acordo_data, "Honorarios_Contratuais", 0.0),
                    min_value=0.0,
                    format="%.2f"
                )
                
                valor_cliente = st.number_input(
                    "👤 Valor do Cliente",
                    value=safe_get_float_value_acordo(acordo_data, "Valor_Cliente", 0.0),
                    min_value=0.0,
                    format="%.2f"
                )
                
                h_sucumbenciais = st.number_input(
                    "⚖️ H. Sucumbenciais",
                    value=safe_get_float_value_acordo(acordo_data, "H_Sucumbenciais", 0.0),
                    min_value=0.0,
                    format="%.2f"
                )
            
            with col2:
                valor_parceiro = st.number_input(
                    "🤝 Valor de Parceiro/Prospector",
                    value=safe_get_float_value_acordo(acordo_data, "Valor_Parceiro", 0.0),
                    min_value=0.0,
                    format="%.2f"
                )
                
                outros_valores = st.number_input(
                    "💰 Outros Valores",
                    value=safe_get_float_value_acordo(acordo_data, "Outros_Valores", 0.0),
                    min_value=0.0,
                    format="%.2f"
                )
            
            observacoes_financeiro = st.text_area(
                "📝 Observações do Financeiro",
                value=safe_get_value_acordo(acordo_data, "Observacoes", ""),
                help="Observações específicas sobre o pagamento"
            )
            
            if st.form_submit_button("💾 Registrar Pagamento"):
                # Verificar se ainda há parcelas pendentes
                num_parcelas = safe_get_float_value_acordo(acordo_data, "Num_Parcelas", 1)
                a_vista = acordo_data.get("A_Vista", False)
                
                # Atualizar dados
                idx = df[df["ID"].astype(str) == str(acordo_id)].index[0]
                df.loc[idx, "Honorarios_Contratuais"] = honorarios_contratuais
                df.loc[idx, "Valor_Cliente"] = valor_cliente
                df.loc[idx, "H_Sucumbenciais"] = h_sucumbenciais
                df.loc[idx, "Valor_Parceiro"] = valor_parceiro
                df.loc[idx, "Outros_Valores"] = outros_valores
                df.loc[idx, "Observacoes"] = observacoes_financeiro
                df.loc[idx, "Data_Ultimo_Update"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                df.loc[idx, "Usuario_Ultimo_Update"] = st.session_state.get("usuario", "admin")
                
                # Determinar próximo status baseado no tipo de pagamento
                if a_vista or num_parcelas <= 1:
                    # Se é à vista ou só tem 1 parcela, finalizar
                    df.loc[idx, "Status"] = "Finalizado"
                    st.success("✅ Acordo finalizado - pagamento à vista registrado!")
                else:
                    # Se há mais parcelas, volta para aguardar próximo pagamento
                    df.loc[idx, "Status"] = "Aguardando Pagamento"
                    # Reduzir número de parcelas restantes
                    novas_parcelas = max(1, num_parcelas - 1)
                    df.loc[idx, "Num_Parcelas"] = novas_parcelas
                    st.success(f"✅ Pagamento registrado! Restam {novas_parcelas} parcela(s).")
                
                # Salvar
                success = save_data_to_github_seguro(df, "lista_acordos.csv", "file_sha_acordos")
                
                if success:
                    st.session_state.df_editado_acordos = df
                    st.rerun()
                else:
                    st.error("❌ Erro ao registrar pagamento.")
    
    elif status_atual == "Finalizado":
        st.success("✅ **Acordo finalizado!** Todos os pagamentos foram processados.")
        
        # Mostrar resumo financeiro
        st.subheader("📊 Resumo Financeiro")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_hc = safe_get_float_value_acordo(acordo_data, "Honorarios_Contratuais", 0.0)
            st.metric("💼 Hon. Contratuais", f"R$ {total_hc:,.2f}")
        
        with col2:
            valor_cliente = safe_get_float_value_acordo(acordo_data, "Valor_Cliente", 0.0)
            st.metric("👤 Valor Cliente", f"R$ {valor_cliente:,.2f}")
        
        with col3:
            h_sucumb = safe_get_float_value_acordo(acordo_data, "H_Sucumbenciais", 0.0)
            st.metric("⚖️ H. Sucumbenciais", f"R$ {h_sucumb:,.2f}")
    
    else:
        st.info(f"📊 Status atual: **{status_atual}**")
        if status_atual == "Aguardando Pagamento":
            st.info("⏳ Aguardando comprovante da próxima parcela...")
    
    # Botões de controle do acordo
    st.divider()
    st.subheader("🔧 Controles do Acordo")
    
    # Só mostrar controles se não estiver finalizado
    if status_atual != "Finalizado":
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("❌ Acordo Não Cumprido/Renegociado", key=f"nao_cumprido_{acordo_id}"):
                st.session_state[f"mostrar_renegociacao_{acordo_id}"] = True
                st.rerun()
        
        with col_btn2:
            if st.button("💰 Atualizar Valor", key=f"atualizar_valor_{acordo_id}"):
                st.session_state[f"mostrar_atualizacao_{acordo_id}"] = True
                st.rerun()
        
        # Interface de renegociação
        if st.session_state.get(f"mostrar_renegociacao_{acordo_id}", False):
            interface_renegociacao_acordo(df, acordo_data, acordo_id)
        
        # Interface de atualização de valor
        if st.session_state.get(f"mostrar_atualizacao_{acordo_id}", False):
            interface_atualizacao_valor_acordo(df, acordo_data, acordo_id)
    else:
        st.info("ℹ️ Acordo finalizado. Controles não disponíveis.")

def interface_renegociacao_acordo(df, acordo_data, acordo_id):
    """Interface para renegociação de acordos"""
    
    st.subheader("🔄 Renegociação do Acordo")
    
    st.warning("⚠️ Esta ação irá excluir as parcelas faltantes e manter apenas as já pagas.")
    
    with st.form(f"form_renegociacao_{acordo_id}"):
        houve_renegociacao = st.checkbox(
            "✅ Houve Renegociação",
            help="Marque se o acordo foi renegociado"
        )
        
        if houve_renegociacao:
            col1, col2 = st.columns(2)
            
            with col1:
                nova_num_parcelas = st.number_input(
                    "🔢 Novo Número de Parcelas",
                    min_value=1,
                    max_value=24,
                    value=1
                )
            
            with col2:
                novo_valor_parcela = st.number_input(
                    "💰 Novo Valor por Parcela",
                    min_value=0.0,
                    format="%.2f"
                )
        
        observacoes_renegociacao = st.text_area(
            "📝 Observações da Renegociação",
            placeholder="Descreva os detalhes da renegociação..."
        )
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.form_submit_button("✅ Confirmar Renegociação"):
                # Atualizar dados
                idx = df[df["ID"].astype(str) == str(acordo_id)].index[0]
                df.loc[idx, "Acordo_Nao_Cumprido"] = True
                df.loc[idx, "Houve_Renegociacao"] = houve_renegociacao
                
                if houve_renegociacao:
                    df.loc[idx, "Nova_Num_Parcelas"] = nova_num_parcelas
                    df.loc[idx, "Novo_Valor_Parcela"] = novo_valor_parcela
                
                df.loc[idx, "Observacoes"] = f"{safe_get_value_acordo(acordo_data, 'Observacoes', '')} | RENEGOCIAÇÃO: {observacoes_renegociacao}"
                df.loc[idx, "Status"] = "Renegociado" if houve_renegociacao else "Não Cumprido"
                df.loc[idx, "Data_Ultimo_Update"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                df.loc[idx, "Usuario_Ultimo_Update"] = st.session_state.get("usuario", "admin")
                
                # Salvar
                success = save_data_to_github_seguro(df, "lista_acordos.csv", "file_sha_acordos")
                
                if success:
                    st.session_state.df_editado_acordos = df
                    st.session_state[f"mostrar_renegociacao_{acordo_id}"] = False
                    st.success("✅ Renegociação registrada com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Erro ao registrar renegociação.")
        
        with col_btn2:
            if st.form_submit_button("❌ Cancelar"):
                st.session_state[f"mostrar_renegociacao_{acordo_id}"] = False
                st.rerun()

def interface_atualizacao_valor_acordo(df, acordo_data, acordo_id):
    """Interface para atualização de valor do acordo"""
    
    st.subheader("💰 Atualização de Valor")
    
    valor_atual = safe_get_float_value_acordo(acordo_data, "Valor_Total", 0)
    st.info(f"💰 **Valor Atual:** R$ {valor_atual:.2f}")
    
    with st.form(f"form_atualizacao_{acordo_id}"):
        valor_atualizado = st.number_input(
            "💵 Novo Valor Atualizado",
            value=valor_atual,
            min_value=0.0,
            format="%.2f"
        )
        
        motivo_atualizacao = st.text_area(
            "📝 Motivo da Atualização",
            placeholder="Descreva o motivo da atualização do valor..."
        )
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.form_submit_button("✅ Atualizar Valor"):
                # Atualizar dados
                idx = df[df["ID"].astype(str) == str(acordo_id)].index[0]
                df.loc[idx, "Valor_Atualizado"] = valor_atualizado
                df.loc[idx, "Observacoes"] = f"{safe_get_value_acordo(acordo_data, 'Observacoes', '')} | ATUALIZAÇÃO: {motivo_atualizacao}"
                df.loc[idx, "Data_Ultimo_Update"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                df.loc[idx, "Usuario_Ultimo_Update"] = st.session_state.get("usuario", "admin")
                
                # Salvar
                success = save_data_to_github_seguro(df, "lista_acordos.csv", "file_sha_acordos")
                
                if success:
                    st.session_state.df_editado_acordos = df
                    st.session_state[f"mostrar_atualizacao_{acordo_id}"] = False
                    st.success("✅ Valor atualizado com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Erro ao atualizar valor.")
        
        with col_btn2:
            if st.form_submit_button("❌ Cancelar"):
                st.session_state[f"mostrar_atualizacao_{acordo_id}"] = False
                st.rerun()

def interface_visualizar_dados_acordo(df):
    """Interface para visualização de dados e estatísticas dos acordos"""
    
    st.header("📈 Dashboard de Acordos")
    
    if df.empty:
        st.info("📋 Nenhum dado disponível para visualização.")
        return
    
    # Métricas gerais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_acordos = len(df)
        st.metric("📊 Total de Acordos", total_acordos)
    
    with col2:
        valor_total = df["Valor_Total"].sum() if "Valor_Total" in df.columns else 0
        st.metric("💰 Valor Total", f"R$ {valor_total:,.2f}")
    
    with col3:
        aguardando = len(df[df["Status"] == "Aguardando Pagamento"]) if "Status" in df.columns else 0
        st.metric("⏳ Aguardando Pagamento", aguardando)
    
    with col4:
        finalizados = len(df[df["Status"] == "Finalizado"]) if "Status" in df.columns else 0
        st.metric("✅ Finalizados", finalizados)
    
    # Gráficos
    if "Status" in df.columns:
        st.subheader("📊 Distribuição por Status")
        status_counts = df["Status"].value_counts()
        st.bar_chart(status_counts)
    
    # Tabela resumo
    st.subheader("📋 Resumo Detalhado")
    
    colunas_resumo = ["Processo", "Nome_Cliente", "Nome_Reu", "Valor_Total", "Status", "Data_Cadastro"]
    colunas_existentes = [col for col in colunas_resumo if col in df.columns]
    
    if colunas_existentes:
        st.dataframe(
            df[colunas_existentes],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("📋 Dados insuficientes para exibir resumo.")