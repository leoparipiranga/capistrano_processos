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
    # Configurações Benefícios
    PERFIS_BENEFICIOS, STATUS_ETAPAS_BENEFICIOS,
    
    # Funções de perfil Benefícios
    verificar_perfil_usuario_beneficios, pode_editar_status_beneficios,
    
    # Funções GitHub
    get_github_api_info, load_data_from_github, 
    save_data_local, save_data_to_github_seguro,
    
    # Funções de arquivo
    salvar_arquivo, baixar_arquivo_github,
    gerar_id_unico, garantir_coluna_id,
    
    # Funções de análise
    mostrar_diferencas, validar_cpf, formatar_processo,
    
    # Funções de limpeza Benefícios
    limpar_campos_formulario, obter_colunas_controle_beneficios, inicializar_linha_vazia_beneficios
)

def show():
    """Função principal do módulo Benefícios"""
    
    # CSS para estilização
    st.markdown("""
    <style>
        .stSelectbox > div > div > select {
            background-color: #f0f2f6;
        }
        .stTextInput > div > div > input {
            background-color: #f0f2f6;
        }
        .metric-container {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #28a745;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Verificação de perfil
    perfil_usuario = verificar_perfil_usuario_beneficios()
    st.sidebar.info(f"👤 **Perfil Benefícios:** {perfil_usuario}")
    
    # Título
    st.title("🏥 Gestão de Benefícios")
    st.markdown(f"**Perfil ativo:** {perfil_usuario}")
    
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
    
    # Abas
    aba = st.tabs(["📝 Cadastrar Benefício", "📊 Lista de Benefícios", "🔄 Fluxo de Trabalho", "📁 Visualizar Dados"])
    
    with aba[0]:
        interface_cadastro_beneficio(df, perfil_usuario)
    
    with aba[1]:
        interface_lista_beneficios(df, perfil_usuario)
    
    with aba[2]:
        interface_fluxo_trabalho_beneficios(df, perfil_usuario)
    
    with aba[3]:
        interface_visualizar_dados_beneficios(df)

def interface_cadastro_beneficio(df, perfil_usuario):
    """Interface para cadastrar novos benefícios"""
    if perfil_usuario != "Cadastrador":
        st.warning("⚠️ Apenas Cadastradores podem criar novos benefícios")
        return
    
    st.subheader("📝 Cadastrar Novo Benefício")
    
    # INICIALIZAR CONTADOR PARA RESET DO FORM
    if "form_reset_counter_beneficios" not in st.session_state:
        st.session_state.form_reset_counter_beneficios = 0
    
    # MOSTRAR LINHAS TEMPORÁRIAS PRIMEIRO (se existirem)
    if "preview_novas_linhas_beneficios" in st.session_state and len(st.session_state["preview_novas_linhas_beneficios"]) > 0:
        st.markdown("### 📋 Linhas Adicionadas (não salvas)")
        st.warning(f"⚠️ Você tem {len(st.session_state['preview_novas_linhas_beneficios'])} linha(s) não salva(s)")
        
        # Mostrar tabela das linhas temporárias
        st.dataframe(st.session_state["preview_novas_linhas_beneficios"], use_container_width=True)
        
        # Botão para salvar
        col_salvar, col_limpar = st.columns(2)
        
        with col_salvar:
            if st.button("💾 Salvar Todas as Linhas", type="primary"):
                novo_sha = save_data_to_github_seguro(
                    st.session_state.df_editado_beneficios,
                    "lista_beneficios.csv",
                    "file_sha_beneficios"
                )
                if novo_sha:
                    st.session_state.file_sha_beneficios = novo_sha
                if novo_sha != st.session_state.file_sha_beneficios:
                    st.session_state.file_sha_beneficios = novo_sha
                    del st.session_state["preview_novas_linhas_beneficios"]
                    
                    # INCREMENTAR CONTADOR PARA FORÇAR RESET DO FORM
                    st.session_state.form_reset_counter_beneficios += 1
                    
                    st.success("✅ Todas as linhas foram salvas e enviadas para administrativo!")
                    st.balloons()
                    st.rerun()
        
        with col_limpar:
            if st.button("🗑️ Descartar Linhas", type="secondary"):
                num_linhas_remover = len(st.session_state["preview_novas_linhas_beneficios"])
                st.session_state.df_editado_beneficios = st.session_state.df_editado_beneficios.iloc[:-num_linhas_remover]
                del st.session_state["preview_novas_linhas_beneficios"]
                st.warning("🗑️ Linhas descartadas!")
                st.rerun()
        
        st.markdown("---")
    
    # FORMULÁRIO COM COLUNAS ORIGINAIS
    hints = {
        "Nº DO PROCESSO": "Ex: 0000000-00.0000.0.00.0000",
        "PARTE": "Nome completo do beneficiário",
        "CPF": "Ex: 000.000.000-00",
        "DETALHE PROCESSO": "Ex: LOAS, Aposentadoria, Auxílio Doença",
        "OBSERVAÇÕES": "Observações sobre o benefício"
    }
    
    with st.form(f"adicionar_linha_form_beneficios_{st.session_state.form_reset_counter_beneficios}"):
        nova_linha = {}
        aviso_letras = False
        
        # Filtrar colunas (excluir colunas de controle)
        colunas_controle = obter_colunas_controle_beneficios()
        colunas_originais = [
            "Nº DO PROCESSO", "DETALHE PROCESSO", "PARTE", "CPF", 
            "DATA DA CONCESSÃO DA LIMINAR", "PROVÁVEL PRAZO FATAL PARA CUMPRIMENTO", 
            "OBSERVAÇÕES", "linhas"
        ]
        
        # Campos principais
        col_form1, col_form2 = st.columns(2)
        
        with col_form1:
            # Processo
            processo_raw = st.text_input(
                "Nº DO PROCESSO *",
                key=f"input_beneficios_processo_{st.session_state.form_reset_counter_beneficios}",
                max_chars=50,
                help=hints.get("Nº DO PROCESSO", ""),
                placeholder="0000000-00.0000.0.00.0000"
            )
            if any(c.isalpha() for c in processo_raw):
                aviso_letras = True
            nova_linha["Nº DO PROCESSO"] = ''.join([c for c in processo_raw if not c.isalpha()])
            
            # CPF
            cpf_raw = st.text_input(
                "CPF *",
                key=f"input_beneficios_cpf_{st.session_state.form_reset_counter_beneficios}",
                max_chars=14,
                help=hints.get("CPF", ""),
                placeholder="000.000.000-00"
            )
            if any(c.isalpha() for c in cpf_raw):
                aviso_letras = True
            nova_linha["CPF"] = ''.join([c for c in cpf_raw if not c.isalpha()])
            
            # Detalhe Processo (Tipo Benefício)
            nova_linha["DETALHE PROCESSO"] = st.selectbox(
                "DETALHE PROCESSO *",
                ["", "LOAS", "LOAS DEFICIENTE", "LOAS IDOSO", "Aposentadoria por Invalidez", 
                 "Aposentadoria por Idade", "Auxílio Doença", "Auxílio Acidente", 
                 "Pensão por Morte", "Salário Maternidade", "Outros"],
                key=f"input_beneficios_detalhe_{st.session_state.form_reset_counter_beneficios}",
                help=hints.get("DETALHE PROCESSO", "")
            )
            
            # Data da Concessão da Liminar
            data_concessao = st.date_input(
                "DATA DA CONCESSÃO DA LIMINAR",
                key=f"input_beneficios_data_concessao_{st.session_state.form_reset_counter_beneficios}",
                help="Data da concessão da liminar (opcional)",
                value=None
            )
            nova_linha["DATA DA CONCESSÃO DA LIMINAR"] = data_concessao.strftime("%d/%m/%Y") if data_concessao else ""
            
            # Prazo Fatal
            prazo_fatal = st.date_input(
                "PROVÁVEL PRAZO FATAL PARA CUMPRIMENTO",
                key=f"input_beneficios_prazo_{st.session_state.form_reset_counter_beneficios}",
                help="Prazo fatal para cumprimento (opcional)",
                value=None
            )
            nova_linha["PROVÁVEL PRAZO FATAL PARA CUMPRIMENTO"] = prazo_fatal.strftime("%d/%m/%Y") if prazo_fatal else ""
        
        with col_form2:
            # Parte (Beneficiário)
            nova_linha["PARTE"] = st.text_input(
                "PARTE *",
                key=f"input_beneficios_parte_{st.session_state.form_reset_counter_beneficios}",
                max_chars=100,
                help=hints.get("PARTE", ""),
                placeholder="NOME COMPLETO DO BENEFICIÁRIO"
            ).upper()
            
            # Observações
            nova_linha["OBSERVAÇÕES"] = st.text_area(
                "OBSERVAÇÕES",
                key=f"input_beneficios_observacoes_{st.session_state.form_reset_counter_beneficios}",
                max_chars=300,
                help=hints.get("OBSERVAÇÕES", ""),
                placeholder="Observações sobre o benefício...",
                height=120
            )
            
            # Campo linhas (numérico padrão)
            nova_linha["linhas"] = "1"  # Valor padrão
        
        # Aviso sobre letras removidas
        if aviso_letras:
            st.warning("⚠️ Letras foram removidas automaticamente dos campos numéricos")

        # Validação antes de submeter
        col_submit, col_validacao = st.columns([1, 2])

        with col_submit:
            submitted = st.form_submit_button("📝 Cadastrar Benefício", type="primary")

        with col_validacao:
            # Mostrar validação em tempo real
            campos_obrigatorios = ["Nº DO PROCESSO", "PARTE", "CPF", "DETALHE PROCESSO"]
            campos_preenchidos = [col for col in campos_obrigatorios if nova_linha.get(col, "").strip()]
            
            if len(campos_preenchidos) == len(campos_obrigatorios):
                st.success(f"✅ Todos os campos obrigatórios preenchidos")
            else:
                faltando = [col for col in campos_obrigatorios if not nova_linha.get(col, "").strip()]
                st.warning(f"⚠️ Faltando: {', '.join(faltando)}")

    # Lógica de submissão
    if submitted:
        # Validações
        cpf_valor = nova_linha.get("CPF", "")
        cpf_numeros = ''.join([c for c in cpf_valor if c.isdigit()])
        campos_obrigatorios = ["Nº DO PROCESSO", "PARTE", "CPF", "DETALHE PROCESSO"]
        campos_vazios = [col for col in campos_obrigatorios if not nova_linha.get(col, "").strip()]
        
        if campos_vazios:
            st.error(f"❌ Preencha os campos obrigatórios: {', '.join(campos_vazios)}")
        elif cpf_valor and len(cpf_numeros) != 11:
            st.error("❌ CPF deve conter exatamente 11 números.")
        else:
            # GERAR ID ÚNICO PARA NOVA LINHA
            novo_id = gerar_id_unico(st.session_state.df_editado_beneficios, "ID")
            nova_linha["ID"] = novo_id
            # ENVIO AUTOMÁTICO PARA ADMINISTRATIVO
            nova_linha["Status"] = "Enviado para administrativo"
            nova_linha["Data Cadastro"] = datetime.now().strftime("%d/%m/%Y %H:%M")
            nova_linha["Cadastrado Por"] = st.session_state.get("usuario", "Sistema")
            nova_linha["Data Envio Administrativo"] = datetime.now().strftime("%d/%m/%Y %H:%M")
            nova_linha["Enviado Administrativo Por"] = st.session_state.get("usuario", "Sistema")
            
            # Campos vazios para próximas etapas
            linha_vazia = inicializar_linha_vazia_beneficios()
            for campo in linha_vazia:
                if campo not in nova_linha:
                    nova_linha[campo] = linha_vazia[campo]
            
            # Adicionar linha ao DataFrame
            st.session_state.df_editado_beneficios = pd.concat(
                [st.session_state.df_editado_beneficios, pd.DataFrame([nova_linha])],
                ignore_index=True
            )
            
            # Guardar preview
            if "preview_novas_linhas_beneficios" not in st.session_state:
                st.session_state["preview_novas_linhas_beneficios"] = pd.DataFrame()
            st.session_state["preview_novas_linhas_beneficios"] = pd.concat(
                [st.session_state["preview_novas_linhas_beneficios"], pd.DataFrame([nova_linha])],
                ignore_index=True
            )
            
            # INCREMENTAR CONTADOR PARA LIMPAR FORM
            st.session_state.form_reset_counter_beneficios += 1
            
            st.success("✅ Benefício cadastrado e enviado automaticamente para **Administrativo**!")
            st.info("💡 O benefício está aguardando implantação no sistema")
            st.rerun()

def interface_lista_beneficios(df, perfil_usuario):
    """Lista de benefícios com botão Abrir para ações"""
    st.subheader("📊 Lista de Benefícios")
    
    # Filtros - agora em 5 colunas
    col_filtro1, col_filtro2, col_filtro3, col_filtro4, col_filtro5 = st.columns(5)
    
    with col_filtro1:
        if "Status" in df.columns:
            status_filtro = st.selectbox(
                "🔍 Filtrar por Status:",
                ["Todos"] + list(STATUS_ETAPAS_BENEFICIOS.values())
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
        # Filtro por Parte
        parte_filtro = st.text_input(
            "🔍 Filtrar por Parte:",
            placeholder="Digite o nome da parte..."
        )
    
    with col_filtro4:
        # Filtro por Tipo (Detalhe Processo)
        tipo_filtro = st.text_input(
            "🔍 Filtrar por Tipo:",
            placeholder="Digite o tipo do processo..."
        )
    
    with col_filtro5:
        mostrar_apenas_meus = False
        if perfil_usuario == "Administrativo":
            mostrar_apenas_meus = st.checkbox("Mostrar apenas benefícios para implantar")
        elif perfil_usuario == "Financeiro":
            mostrar_apenas_meus = st.checkbox("Mostrar apenas benefícios para finalizar")
    
    # Seletor de quantidade de registros
    col_qtd1, col_qtd2 = st.columns([1, 4])
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
        df_filtrado = df_filtrado[df_filtrado["Nº DO PROCESSO"].astype(str).str.contains(processo_filtro, case=False, na=False)]
    
    # Filtro por parte
    if parte_filtro:
        df_filtrado = df_filtrado[df_filtrado["PARTE"].astype(str).str.contains(parte_filtro, case=False, na=False)]
    
    # Filtro por tipo (detalhe processo)
    if tipo_filtro:
        df_filtrado = df_filtrado[df_filtrado["DETALHE PROCESSO"].astype(str).str.contains(tipo_filtro, case=False, na=False)]
    
    if mostrar_apenas_meus:
        if perfil_usuario == "Administrativo" and "Status" in df.columns:
            df_filtrado = df_filtrado[df_filtrado["Status"] == "Enviado para administrativo"]
        elif perfil_usuario == "Financeiro" and "Status" in df.columns:
            df_filtrado = df_filtrado[df_filtrado["Status"] == "Enviado para o financeiro"]
    
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
    
    # Aplicar limite de quantidade
    total_registros = len(df_filtrado)
    if qtd_mostrar != "Todos":
        df_filtrado = df_filtrado.head(qtd_mostrar)
    
    # Exibir lista com botão Abrir - USAR ID
    if len(df_filtrado) > 0:
        # Mostrar informações de quantidade
        if qtd_mostrar != "Todos":
            st.markdown(f"### 📋 Lista (mostrando {len(df_filtrado)} de {total_registros} benefícios)")
        else:
            st.markdown(f"### 📋 Lista ({len(df_filtrado)} benefícios)")
        
        # Cabeçalhos das colunas
        col_abrir, col_processo, col_parte, col_tipo, col_status = st.columns([1, 2, 2, 1.5, 2])
        
        with col_abrir:
            st.markdown("**Ação**")
        with col_processo:
            st.markdown("**Processo**")
        with col_parte:
            st.markdown("**Parte**")
        with col_tipo:
            st.markdown("**Tipo**")
        with col_status:
            st.markdown("**Status**")
        
        st.markdown("---")  # Linha separadora
        
        for idx, beneficio in df_filtrado.iterrows():
            col_abrir, col_processo, col_parte, col_tipo, col_status = st.columns([1, 2, 2, 1.5, 2])
            
            # GARANTIR ID ÚNICO E VÁLIDO
            beneficio_id = beneficio.get("ID")
            
            # Se ID é vazio, NaN ou inválido, usar índice + timestamp para garantir unicidade
            if pd.isna(beneficio_id) or str(beneficio_id).strip() == "" or str(beneficio_id) == "nan":
                beneficio_id = f"temp_{idx}_{hash(str(beneficio.get('Nº DO PROCESSO', '')))}".replace('-', 'neg')
                # Atualizar o DataFrame com ID gerado
                st.session_state.df_editado_beneficios.loc[idx, "ID"] = beneficio_id
            
            # Garantir que beneficio_id seja string e válido para key
            beneficio_id = str(beneficio_id).replace(" ", "_").replace(".", "_").replace("-", "_")
            
            with col_abrir:
                if st.button(f"🔓 Abrir", key=f"abrir_beneficio_id_{beneficio_id}"):
                    st.session_state['beneficio_aberto'] = beneficio_id
                    st.rerun()
            
            with col_processo:
                st.write(f"**{beneficio['Nº DO PROCESSO']}**")
            
            with col_parte:
                st.write(beneficio.get('PARTE', 'N/A'))
            
            with col_tipo:
                detalhe = beneficio.get('DETALHE PROCESSO', 'N/A')
                if detalhe and detalhe != 'N/A' and str(detalhe).strip():
                    st.write(detalhe)
                else:
                    st.write('-')
                
            with col_status:
                # Colorir status
                status_atual = beneficio.get('Status', 'N/A')
                if status_atual == 'Enviado para administrativo':
                    st.write(f"🟠 {status_atual}")
                elif status_atual == 'Implantado':
                    st.write(f"🔵 {status_atual}")
                elif status_atual == 'Enviado para o financeiro':
                    st.write(f"🟣 {status_atual}")
                elif status_atual == 'Finalizado':
                    st.write(f"🟢 {status_atual}")
                else:
                    st.write(status_atual)
        
        # Interface de edição se benefício foi aberto
        if 'beneficio_aberto' in st.session_state:
            st.markdown("---")
            beneficio_id = st.session_state['beneficio_aberto']
            
            # Botão para fechar
            if st.button("❌ Fechar", key="fechar_beneficio"):
                del st.session_state['beneficio_aberto']
                st.rerun()
            
            # Buscar dados do benefício POR ID
            linha_beneficio = df[df["ID"].astype(str) == str(beneficio_id)]  # ← BUSCAR COMO STRING
            if len(linha_beneficio) > 0:
                linha_beneficio = linha_beneficio.iloc[0]
                processo = linha_beneficio["Nº DO PROCESSO"]
                status_atual = linha_beneficio.get("Status", "")
                
                # Interface baseada no status e perfil
                interface_edicao_beneficio(df, beneficio_id, status_atual, perfil_usuario)
            else:
                st.error("❌ Benefício não encontrado")
    else:
        st.info("Nenhum benefício encontrado com os filtros aplicados")

def interface_edicao_beneficio(df, beneficio_id, status_atual, perfil_usuario):
    """Interface de edição baseada no ID único"""
    
    # Buscar dados do benefício POR ID
    linha_beneficio_df = df[df["ID"].astype(str) == str(beneficio_id)]
    
    if len(linha_beneficio_df) == 0:
        st.error(f"❌ Benefício com ID {beneficio_id} não encontrado")
        return
    
    linha_beneficio = linha_beneficio_df.iloc[0]
    processo = linha_beneficio["Nº DO PROCESSO"]
    
    st.markdown(f"### 🏥 Editando Benefício: {processo}")
    st.markdown(f"**ID:** {beneficio_id} | **Beneficiário:** {linha_beneficio.get('PARTE', 'N/A')}")
    st.markdown(f"**Status atual:** {status_atual}")

    # Mostrar informações básicas
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.write(f"**Tipo:** {linha_beneficio.get('DETALHE PROCESSO', 'N/A')}")
    with col_info2:
        st.write(f"**CPF:** {linha_beneficio.get('CPF', 'N/A')}")
    with col_info3:
        st.write(f"**Cadastrado em:** {linha_beneficio.get('Data Cadastro', 'N/A')}")
    
    st.markdown("---")
    
    # ETAPA 2: Enviado para administrativo -> Implantar (Administrativo)
    if status_atual == "Enviado para administrativo" and perfil_usuario == "Administrativo":
        st.markdown("#### 🔧 Implantar no Sistema")
        
        st.info("📋 **Instruções:** Acesse o Korbil, anexe a carta de concessão e histórico de crédito, e marque como implantado")
        
        st.markdown("**📅 Informações do envio:**")
        st.write(f"- Enviado para administrativo em: {linha_beneficio.get('Data Envio Administrativo', 'N/A')}")
        st.write(f"- Enviado por: {linha_beneficio.get('Enviado Administrativo Por', 'N/A')}")
        
        if st.button("✅ Marcar como Implantado", type="primary", key=f"implantar_id_{beneficio_id}"):
            # Atualizar status
            idx = df[df["ID"] == beneficio_id].index[0]
            st.session_state.df_editado_beneficios.loc[idx, "Status"] = "Implantado"
            st.session_state.df_editado_beneficios.loc[idx, "Implantado"] = "Sim"
            st.session_state.df_editado_beneficios.loc[idx, "Data Implantação"] = datetime.now().strftime("%d/%m/%Y %H:%M")
            st.session_state.df_editado_beneficios.loc[idx, "Implantado Por"] = st.session_state.get("usuario", "Sistema")
            
            # Salvar no GitHub
            novo_sha = save_data_to_github_seguro(
                st.session_state.df_editado_beneficios,
                "lista_beneficios.csv",
                st.session_state.file_sha_beneficios
            )
            st.session_state.file_sha_beneficios = novo_sha
            
            st.success("✅ Benefício marcado como implantado e devolvido para cadastrador!")
            del st.session_state['beneficio_aberto']
            st.rerun()
    
    # ETAPA 3: Implantado -> Verificar e enviar para financeiro (Cadastrador)
    elif status_atual == "Implantado" and perfil_usuario == "Cadastrador":
        st.markdown("#### 🔍 Verificar Documentação no Korbil")
        
        st.info("📋 **Instruções:** Acesse o Korbil, verifique os dados implantados e informe o benefício e percentual")
        
        st.markdown("**📅 Informações da implantação:**")
        st.write(f"- Implantado em: {linha_beneficio.get('Data Implantação', 'N/A')}")
        st.write(f"- Implantado por: {linha_beneficio.get('Implantado Por', 'N/A')}")
        
        # Campos para preenchimento
        col_verif1, col_verif2 = st.columns(2)
        
        with col_verif1:
            beneficio_verificado = st.text_input(
                "Benefício Verificado *",
                key=f"beneficio_verif_{processo}",
                placeholder="Ex: LOAS, Aposentadoria por Invalidez",
                help="Confirme o tipo de benefício após verificação no Korbil"
            )
        
        with col_verif2:
            percentual_cobranca = st.selectbox(
                "Percentual de Cobrança *",
                ["", "10%", "15%", "20%", "25%", "30%", "Outros"],
                key=f"percentual_{processo}",
                help="Informe o percentual a ser cobrado"
            )
            
            if percentual_cobranca == "Outros":
                percentual_personalizado = st.text_input(
                    "Especificar percentual:",
                    key=f"percentual_outro_{processo}",
                    placeholder="Ex: 35%"
                )
                percentual_final = percentual_personalizado
            else:
                percentual_final = percentual_cobranca
        
        if beneficio_verificado and percentual_final:
            if st.button("📤 Enviar para Financeiro", type="primary", key=f"enviar_financeiro_{processo}"):
                # Atualizar status
                idx = df[df["Processo"] == processo].index[0]
                st.session_state.df_editado_beneficios.loc[idx, "Status"] = "Enviado para o financeiro"
                st.session_state.df_editado_beneficios.loc[idx, "Benefício Verificado"] = beneficio_verificado
                st.session_state.df_editado_beneficios.loc[idx, "Percentual Cobrança"] = percentual_final
                st.session_state.df_editado_beneficios.loc[idx, "Data Envio Financeiro"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                st.session_state.df_editado_beneficios.loc[idx, "Enviado Financeiro Por"] = st.session_state.get("usuario", "Sistema")
                
                # Salvar no GitHub
                novo_sha = save_data_to_github_seguro(
                    st.session_state.df_editado_beneficios,
                    "lista_beneficios.csv",
                    st.session_state.file_sha_beneficios
                )
                st.session_state.file_sha_beneficios = novo_sha
                
                st.success("✅ Benefício enviado para o Financeiro!")
                del st.session_state['beneficio_aberto']
                st.rerun()
        else:
            st.info("📋 Preencha o benefício verificado e o percentual para prosseguir")
    
    # ETAPA 4: Finalizar (Financeiro)
    elif status_atual == "Enviado para o financeiro" and perfil_usuario == "Financeiro":
        st.markdown("#### 💰 Finalizar Benefício")
        
        st.markdown("**📋 Informações do benefício:**")
        st.write(f"- Benefício verificado: {linha_beneficio.get('Benefício Verificado', 'N/A')}")
        st.write(f"- Percentual de cobrança: {linha_beneficio.get('Percentual Cobrança', 'N/A')}")
        st.write(f"- Enviado para financeiro em: {linha_beneficio.get('Data Envio Financeiro', 'N/A')}")
        
        # Tipo de pagamento
        st.markdown("**💳 Informações do Pagamento:**")
        tipo_pagamento = st.selectbox(
            "Tipo de Pagamento *",
            ["", "PIX", "Transferência", "Boleto", "Dinheiro", "Cartão"],
            key=f"tipo_pagamento_{processo}",
            help="Como o cliente pagou"
        )
        
        # Upload do comprovante (opcional para dinheiro)
        if tipo_pagamento and tipo_pagamento != "Dinheiro":
            comprovante_pagamento = st.file_uploader(
                "Comprovante de Pagamento *",
                type=["pdf", "jpg", "jpeg", "png"],
                key=f"comprovante_{processo}",
                help="Anexar comprovante do pagamento"
            )
        else:
            comprovante_pagamento = None
        
        # Valor pago - APENAS NÚMERO
        valor_pago_raw = st.text_input(
            "Valor Pago (apenas números) *",
            key=f"valor_pago_{processo}",
            placeholder="Ex: 1500.50",
            help="Valor efetivamente pago pelo cliente (apenas números)"
        )
        
        # Validar se é número válido
        valor_pago_valido = False
        valor_pago_float = 0.0
        
        if valor_pago_raw.strip():
            try:
                # Converter vírgula para ponto e validar
                valor_limpo = valor_pago_raw.replace(',', '.')
                valor_pago_float = float(valor_limpo)
                valor_pago_valido = True
                st.success(f"✅ Valor válido: R$ {valor_pago_float:,.2f}")
            except ValueError:
                st.error("❌ Digite apenas números (ex: 1500.50)")
                valor_pago_valido = False
        
        # Validar se pode finalizar
        pode_finalizar = False
        if tipo_pagamento == "Dinheiro":
            pode_finalizar = tipo_pagamento and valor_pago_valido
        else:
            pode_finalizar = tipo_pagamento and comprovante_pagamento and valor_pago_valido
        
        if pode_finalizar:
            if st.button("✅ Finalizar Benefício", key=f"finalizar_beneficio_{processo}", type="primary"):
                # Salvar comprovante se existir
                comprovante_url = ""
                if comprovante_pagamento:
                    comprovante_url = salvar_arquivo(comprovante_pagamento, processo, "pagamento_beneficio")
                
                # Atualizar status
                idx = df[df["Nº DO PROCESSO"] == processo].index[0]
                st.session_state.df_editado_beneficios.loc[idx, "Status"] = "Finalizado"
                st.session_state.df_editado_beneficios.loc[idx, "Tipo Pagamento"] = tipo_pagamento
                st.session_state.df_editado_beneficios.loc[idx, "Comprovante Pagamento"] = comprovante_url
                st.session_state.df_editado_beneficios.loc[idx, "Valor Pago"] = valor_pago_float  # ← SALVAR APENAS O NÚMERO
                st.session_state.df_editado_beneficios.loc[idx, "Data Finalização"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                st.session_state.df_editado_beneficios.loc[idx, "Finalizado Por"] = st.session_state.get("usuario", "Sistema")
                
                # Salvar no GitHub
                novo_sha = save_data_to_github_seguro(
                    st.session_state.df_editado_beneficios,
                    "lista_beneficios.csv",
                    st.session_state.file_sha_beneficios
                )
                st.session_state.file_sha_beneficios = novo_sha
                
                st.success("🎉 Benefício finalizado com sucesso!")
                st.balloons()
                del st.session_state['beneficio_aberto']
                st.rerun()
        else:
            if tipo_pagamento == "Dinheiro":
                st.info("📋 Preencha o tipo de pagamento e valor (válido) para finalizar")
            else:
                st.info("📋 Anexe o comprovante, tipo e valor (válido) do pagamento para finalizar")
    
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
                baixar_arquivo_github(linha_beneficio["Comprovante Pagamento"], "📎 Baixar Comprovante")
        
            
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
        st.error(f"❌ Seu perfil ({perfil_usuario}) não pode editar benefícios com status '{status_atual}'")
        
        if perfil_usuario == "Cadastrador":
            st.info("💡 Cadastradores podem editar benefícios 'Implantado'")
        elif perfil_usuario == "Administrativo":
            st.info("💡 Administrativo pode implantar benefícios 'Enviado para administrativo'")
        elif perfil_usuario == "Financeiro":
            st.info("💡 Financeiro pode finalizar benefícios 'Enviado para o financeiro'")

def interface_fluxo_trabalho_beneficios(df, perfil_usuario):
    """Interface do fluxo de trabalho Benefícios"""
    st.subheader("🔄 Fluxo de Trabalho - Benefícios")
    
    # Dashboard geral
    col_dash1, col_dash2, col_dash3, col_dash4 = st.columns(4)
    
    # Contadores por status
    if "Status" in df.columns:
        total_administrativo = len(df[df["Status"] == "Enviado para administrativo"])
        total_implantados = len(df[df["Status"] == "Implantado"])
        total_financeiro = len(df[df["Status"] == "Enviado para o financeiro"])
        total_finalizados = len(df[df["Status"] == "Finalizado"])
    else:
        total_administrativo = total_implantados = total_financeiro = total_finalizados = 0
    
    with col_dash1:
        st.metric("🔧 Administrativo", total_administrativo)
    
    with col_dash2:
        st.metric("✅ Implantados", total_implantados)
    
    with col_dash3:
        st.metric("💰 Financeiro", total_financeiro)
    
    with col_dash4:
        st.metric("🎉 Finalizados", total_finalizados)
    
    st.markdown("---")
    
    # Interface específica por perfil
    if perfil_usuario == "Cadastrador":
        st.markdown("### 👨‍💻 Pendências do Cadastrador")
        if "Status" in df.columns:
            beneficios_implantados = df[df["Status"] == "Implantado"]
            if len(beneficios_implantados) > 0:
                st.markdown(f"#### 🔍 Benefícios para verificar no Korbil ({len(beneficios_implantados)}):")
                st.dataframe(beneficios_implantados[["Processo", "Beneficiário", "Tipo Benefício", "Data Implantação"]], 
                           use_container_width=True)
            else:
                st.success("✅ Todos os benefícios implantados foram verificados!")
    
    elif perfil_usuario == "Administrativo":
        st.markdown("### 🔧 Pendências do Administrativo")
        if "Status" in df.columns:
            beneficios_administrativo = df[df["Status"] == "Enviado para administrativo"]
            if len(beneficios_administrativo) > 0:
                st.markdown(f"#### 📋 Benefícios para implantar ({len(beneficios_administrativo)}):")
                st.dataframe(beneficios_administrativo[["Processo", "Beneficiário", "Tipo Benefício", "Data Envio Administrativo"]], 
                           use_container_width=True)
            else:
                st.success("✅ Todos os benefícios foram implantados!")
    
    elif perfil_usuario == "Financeiro":
        st.markdown("### 💰 Pendências do Financeiro")
        if "Status" in df.columns:
            beneficios_financeiro = df[df["Status"] == "Enviado para o financeiro"]
            if len(beneficios_financeiro) > 0:
                st.markdown(f"#### 💳 Benefícios para finalizar ({len(beneficios_financeiro)}):")
                st.dataframe(beneficios_financeiro[["Processo", "Beneficiário", "Benefício Verificado", "Percentual Cobrança", "Data Envio Financeiro"]], 
                           use_container_width=True)
            else:
                st.success("✅ Todos os benefícios foram finalizados!")
    
    elif perfil_usuario == "SAC":
        st.markdown("### 📞 Visão Geral do SAC")
        st.info("📋 O SAC pode visualizar todos os benefícios em qualquer etapa do fluxo")
        
        if "Status" in df.columns and len(df) > 0:
            status_counts = df["Status"].value_counts()
            
            col_sac1, col_sac2 = st.columns(2)
            
            with col_sac1:
                st.markdown("**📊 Distribuição por Status:**")
                st.bar_chart(status_counts)
            
            with col_sac2:
                st.markdown("**📋 Resumo:**")
                for status, count in status_counts.items():
                    porcentagem = (count / len(df)) * 100
                    st.write(f"• **{status}:** {count} ({porcentagem:.1f}%)")

def interface_visualizar_dados_beneficios(df):
    """Interface para visualizar dados Benefícios"""
    st.subheader("📁 Visualizar Dados - Benefícios")
    
    if len(df) == 0:
        st.info("📋 Nenhum benefício encontrado para visualizar")
        return
    
    # Resumo geral
    col_resumo1, col_resumo2, col_resumo3, col_resumo4 = st.columns(4)
    
    with col_resumo1:
        st.metric("Total de Benefícios", len(df))
    
    with col_resumo2:
        if "Status" in df.columns:
            finalizados = len(df[df["Status"] == "Finalizado"])
            st.metric("Finalizados", finalizados)
        else:
            st.metric("Finalizados", "N/A")
    
    with col_resumo3:
        if "DETALHE PROCESSO" in df.columns:
            tipos_unicos = df["DETALHE PROCESSO"].nunique()
            st.metric("Tipos Diferentes", tipos_unicos)
        else:
            st.metric("Tipos Diferentes", "N/A")
    
    with col_resumo4:
        # CALCULAR VALOR TOTAL CORRETAMENTE (SEM R$)
        if "Valor Pago" in df.columns:
            # Filtrar valores não nulos e numéricos
            valores_numericos = pd.to_numeric(df["Valor Pago"], errors='coerce')
            valores_validos = valores_numericos.dropna()
            
            if len(valores_validos) > 0:
                total_valor = valores_validos.sum()
                st.metric("Valor Total Recebido", f"R$ {total_valor:,.2f}")
            else:
                st.metric("Valor Total Recebido", "R$ 0,00")
        else:
            st.metric("Valor Total Recebido", "R$ 0,00")
    
    
    # Filtros e tabela (similar aos outros módulos)
    st.markdown("### 🔍 Filtros")
    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
    
    with col_filtro1:
        if "Status" in df.columns:
            status_filtro = st.multiselect(
                "Status:",
                options=df["Status"].unique(),
                default=df["Status"].unique()
            )
        else:
            status_filtro = []
    
    with col_filtro2:
        if "Tipo Benefício" in df.columns:
            tipo_filtro = st.multiselect(
                "Tipo Benefício:",
                options=df["Tipo Benefício"].unique(),
                default=df["Tipo Benefício"].unique()
            )
        else:
            tipo_filtro = []
    
    with col_filtro3:
        mostrar_todas_colunas = st.checkbox("Mostrar todas as colunas", value=False)
    
    # Aplicar filtros
    df_visualizado = df.copy()
    
    if status_filtro and "Status" in df.columns:
        df_visualizado = df_visualizado[df_visualizado["Status"].isin(status_filtro)]
    
    if tipo_filtro and "Tipo Benefício" in df.columns:
        df_visualizado = df_visualizado[df_visualizado["Tipo Benefício"].isin(tipo_filtro)]
    
    # Selecionar colunas para exibir
    if mostrar_todas_colunas:
        colunas_exibir = df_visualizado.columns.tolist()
    else:
        colunas_principais = [
            "Processo", "Beneficiário", "Tipo Benefício", "Status", 
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
            df_visualizado = df_visualizado.sort_values(ordenar_por, ascending=False)
        
        # Exibir tabela
        st.dataframe(
            df_visualizado[colunas_exibir].head(max_rows),
            use_container_width=True,
            height=400
        )
        
        # Análise por status e tipo
        if "Status" in df.columns and "Tipo Benefício" in df.columns and len(df) > 0:
            st.markdown("### 📈 Análises")
            
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.markdown("**Distribuição por Status:**")
                status_counts = df["Status"].value_counts()
                st.bar_chart(status_counts)
            
            with col_chart2:
                st.markdown("**Distribuição por Tipo:**")
                tipo_counts = df["Tipo Benefício"].value_counts()
                st.bar_chart(tipo_counts)
    
    else:
        st.info("Nenhum registro encontrado com os filtros aplicados")