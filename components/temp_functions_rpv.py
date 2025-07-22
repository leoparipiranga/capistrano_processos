# Função adicional para o arquivo funcoes_rpv.py

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
