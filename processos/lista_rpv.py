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

# Importar funções do módulo específico de RPV
from components.funcoes_rpv import (
    # Configurações RPV
    PERFIS_RPV, STATUS_ETAPAS_RPV,
    
    # Funções de perfil RPV
    verificar_perfil_usuario_rpv, pode_editar_status_rpv,
    
    # Funções de limpeza RPV
    obter_colunas_controle_rpv, inicializar_linha_vazia_rpv,
    
    # Funções de interface
    interface_lista_rpv, interface_cadastro_rpv, interface_edicao_rpv,
    interface_fluxo_trabalho_rpv, interface_cadastrador_fluxo_rpv,
    interface_juridico_fluxo_rpv, interface_financeiro_fluxo_rpv,
    interface_visualizar_dados_rpv
)

# Importar funções comuns que ainda estão no módulo de controle
from components.functions_controle import (
    # Funções GitHub
    get_github_api_info, load_data_from_github, 
    save_data_local, save_data_to_github_seguro,
    
    # Funções de arquivo
    salvar_arquivo, baixar_arquivo_github,
    gerar_id_unico, garantir_coluna_id,
    
    # Funções de análise
    mostrar_diferencas, validar_cpf, formatar_processo,
    
    # Funções de limpeza comuns
    limpar_campos_formulario
)

def show():
    """Função principal do módulo RPV"""
    
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
            border-left: 4px solid #007bff;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Verificação de perfil
    perfil_usuario = verificar_perfil_usuario_rpv()
    st.sidebar.info(f"👤 **Perfil RPV:** {perfil_usuario}")
    
    # Título
    st.title("📄 Gestão de RPV")
    st.markdown(f"**Perfil ativo:** {perfil_usuario}")
    
    # Carregar dados
    selected_file_name = "lista_rpv.csv"
    
    if "df_editado_rpv" not in st.session_state or st.session_state.get("last_file_path_rpv") != selected_file_name:
        df, file_sha = load_data_from_github(selected_file_name)
        st.session_state.df_editado_rpv = df.copy()
        st.session_state.last_file_path_rpv = selected_file_name
        st.session_state.file_sha_rpv = file_sha
    
    df = st.session_state.df_editado_rpv
    
    # Limpar colunas sem nome
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # Abas
    aba = st.tabs(["📝 Cadastrar RPV", "📊 Lista de RPVs", "🔄 Fluxo de Trabalho", "📁 Visualizar Dados"])
    
    with aba[0]:
        interface_cadastro_rpv(df, perfil_usuario)
    
    with aba[1]:
        interface_lista_rpv(df, perfil_usuario)
    
    with aba[2]:
        interface_fluxo_trabalho_rpv(df, perfil_usuario)
    
    with aba[3]:
        interface_visualizar_dados_rpv(df)

def interface_cadastro_rpv(df, perfil_usuario):
    """Interface para cadastrar novos RPVs"""
    if perfil_usuario != "Cadastrador":
        st.warning("⚠️ Apenas Cadastradores podem criar novos RPVs")
        return
    
    st.subheader("📝 Cadastrar Novo RPV")
    
    # INICIALIZAR CONTADOR PARA RESET DO FORM
    if "form_reset_counter_rpv" not in st.session_state:
        st.session_state.form_reset_counter_rpv = 0

    # MOSTRAR LINHAS TEMPORÁRIAS PRIMEIRO (se existirem)
    if "preview_novas_linhas_rpv" in st.session_state and len(st.session_state["preview_novas_linhas_rpv"]) > 0:
        st.markdown("### 📋 Linhas Adicionadas (não salvas)")
        st.warning(f"⚠️ Você tem {len(st.session_state['preview_novas_linhas_rpv'])} linha(s) não salva(s)")
        
        # Mostrar tabela das linhas temporárias
        st.dataframe(st.session_state["preview_novas_linhas_rpv"], use_container_width=True)
        
        # Botão para salvar
        col_salvar, col_limpar = st.columns(2)
        
        with col_salvar:
            if st.button("💾 Salvar Todas as Linhas", type="primary"):
                novo_sha = save_data_to_github_seguro(
                    st.session_state.df_editado_rpv,
                    "lista_rpv.csv",
                    "file_sha_rpv"
                )
                if novo_sha:
                    st.session_state.file_sha_rpv = novo_sha
                if novo_sha != st.session_state.file_sha_rpv:
                    st.session_state.file_sha_rpv = novo_sha
                    del st.session_state["preview_novas_linhas_rpv"]
                    
                    # INCREMENTAR CONTADOR PARA FORÇAR RESET DO FORM
                    st.session_state.form_reset_counter_rpv += 1
                    
                    st.success("✅ Todas as linhas foram salvas e enviadas!")
                    st.balloons()
                    st.rerun()
        
        with col_limpar:
            if st.button("🗑️ Descartar Linhas", type="secondary"):
                num_linhas_remover = len(st.session_state["preview_novas_linhas_rpv"])
                st.session_state.df_editado_rpv = st.session_state.df_editado_rpv.iloc[:-num_linhas_remover]
                del st.session_state["preview_novas_linhas_rpv"]
                st.warning("🗑️ Linhas descartadas!")
                st.rerun()
        
        st.markdown("---")
    
    # FORMULÁRIO COM CONTADOR NO KEY
    hints = {
        "Processo": "Ex: 0000000-00.0000.0.00.0000",
        "Beneficiário": "Nome completo do beneficiário",
        "CPF": "Ex: 000.000.000-00",
        "Valor RPV": "Ex: 1500.50",
        "Observações": "Observações gerais sobre o RPV",
        "Solicitar Certidão": "Marque se for necessário solicitar certidão"
    }
    
    # USAR CONTADOR NO FORM KEY
    with st.form(f"adicionar_linha_form_rpv_{st.session_state.form_reset_counter_rpv}"):
        nova_linha = {}
        aviso_letras = False
        
        # Filtrar colunas (excluir colunas de controle)
        colunas_controle = obter_colunas_controle_rpv()
        colunas_form = [col for col in df.columns if col not in colunas_controle]
        
        # Campos principais
        col_form1, col_form2 = st.columns(2)
        
        with col_form1:
            # Processo - USAR CONTADOR NOS KEYS
            processo_raw = st.text_input(
                "Processo *",
                key=f"input_rpv_processo_{st.session_state.form_reset_counter_rpv}",
                max_chars=50,
                help=hints.get("Processo", ""),
                placeholder="0000000-00.0000.0.00.0000"
            )
            if any(c.isalpha() for c in processo_raw):
                aviso_letras = True
            nova_linha["Processo"] = ''.join([c for c in processo_raw if not c.isalpha()])
            
            # CPF - USAR CONTADOR NOS KEYS
            cpf_raw = st.text_input(
                "CPF *",
                key=f"input_rpv_cpf_{st.session_state.form_reset_counter_rpv}",
                max_chars=14,
                help=hints.get("CPF", ""),
                placeholder="000.000.000-00"
            )
            if any(c.isalpha() for c in cpf_raw):
                aviso_letras = True
            nova_linha["CPF"] = ''.join([c for c in cpf_raw if not c.isalpha()])
            
            # Valor RPV - USAR CONTADOR NOS KEYS
            valor_raw = st.text_input(
                "Valor RPV *",
                key=f"input_rpv_valor_{st.session_state.form_reset_counter_rpv}",
                max_chars=20,
                help=hints.get("Valor RPV", ""),
                placeholder="1500.50"
            )
            valor_numerico = ''.join([c for c in valor_raw if c.isdigit() or c in '.,'])
            if valor_numerico:
                valor_numerico = valor_numerico.replace(',', '.')
                try:
                    float(valor_numerico)
                    nova_linha["Valor RPV"] = f"R$ {valor_numerico}"
                except ValueError:
                    nova_linha["Valor RPV"] = valor_numerico
            else:
                nova_linha["Valor RPV"] = ""
            if any(c.isalpha() for c in valor_raw):
                aviso_letras = True
        
        with col_form2:
            # Beneficiário - USAR CONTADOR NOS KEYS
            nova_linha["Beneficiário"] = st.text_input(
                "Beneficiário *",
                key=f"input_rpv_beneficiario_{st.session_state.form_reset_counter_rpv}",
                max_chars=100,
                help=hints.get("Beneficiário", ""),
                placeholder="NOME COMPLETO DO BENEFICIÁRIO"
            ).upper()
            
            # Observações - USAR CONTADOR NOS KEYS
            nova_linha["Observações"] = st.text_area(
                "Observações",
                key=f"input_rpv_observacoes_{st.session_state.form_reset_counter_rpv}",
                max_chars=300,
                help=hints.get("Observações", ""),
                placeholder="Observações sobre o RPV...",
                height=100
            )
            
            # PDF RPV - USAR CONTADOR NOS KEYS
            pdf_rpv = st.file_uploader(
                "PDF do RPV *",
                type=["pdf"],
                key=f"input_rpv_pdf_{st.session_state.form_reset_counter_rpv}",
                help="Anexar PDF do RPV"
            )
        
        # Campo especial: Solicitar Certidão - USAR CONTADOR NOS KEYS
        st.markdown("### 📋 Configurações Especiais")
        solicitar_certidao = st.checkbox(
            "✅ Solicitar Certidão",
            key=f"input_rpv_solicitar_certidao_{st.session_state.form_reset_counter_rpv}",
            help="Marque se for necessário solicitar certidão (enviar para jurídico também)"
        )
        nova_linha["Solicitar Certidão"] = "Sim" if solicitar_certidao else "Não"

        
        # Aviso sobre letras removidas
        if aviso_letras:
            st.warning("⚠️ Letras foram removidas automaticamente dos campos numéricos")

        # Validação antes de submeter
        col_submit, col_validacao = st.columns([1, 2])

        with col_submit:
            submitted = st.form_submit_button("📝 Cadastrar RPV", type="primary")

        with col_validacao:
            # Mostrar validação em tempo real
            campos_obrigatorios = ["Processo", "Beneficiário", "CPF", "Valor RPV"]
            campos_preenchidos = [col for col in campos_obrigatorios if nova_linha.get(col, "").strip()]
            
            if len(campos_preenchidos) == len(campos_obrigatorios) and pdf_rpv:
                st.success(f"✅ Todos os campos obrigatórios preenchidos + PDF anexado")
            else:
                faltando = [col for col in campos_obrigatorios if not nova_linha.get(col, "").strip()]
                if not pdf_rpv:
                    faltando.append("PDF do RPV")
                st.warning(f"⚠️ Faltando: {', '.join(faltando)}")

    # Lógica de submissão
    if submitted:
        # Validações
        cpf_valor = nova_linha.get("CPF", "")
        cpf_numeros = ''.join([c for c in cpf_valor if c.isdigit()])
        campos_obrigatorios = ["Processo", "Beneficiário", "CPF", "Valor RPV"]
        campos_vazios = [col for col in campos_obrigatorios if not nova_linha.get(col, "").strip()]
        
        if campos_vazios:
            st.error(f"❌ Preencha os campos obrigatórios: {', '.join(campos_vazios)}")
        elif not pdf_rpv:
            st.error("❌ Anexe o PDF do RPV")
        elif cpf_valor and len(cpf_numeros) != 11:
            st.error("❌ CPF deve conter exatamente 11 números.")
        else:
            # GERAR ID ÚNICO PARA NOVA LINHA
            novo_id = gerar_id_unico(st.session_state.df_editado_rpv, "ID")
            nova_linha["ID"] = novo_id
            # Salvar PDF
            pdf_url = salvar_arquivo(pdf_rpv, nova_linha["Processo"], "rpv")
            
            if pdf_url:
                # ADICIONAR CAMPOS DE CONTROLE
                solicitar_certidao = nova_linha.get("Solicitar Certidão", "Não") == "Sim"
                
                # ENVIAR AUTOMATICAMENTE (ao invés de só cadastrar)
                nova_linha["Status"] = "Enviado"  # ← MUDANÇA: vai direto para "Enviado"
                nova_linha["Data Cadastro"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                nova_linha["Cadastrado Por"] = st.session_state.get("usuario", "Sistema")
                nova_linha["PDF RPV"] = pdf_url
                
                # ADICIONAR DADOS DO ENVIO AUTOMÁTICO
                nova_linha["Data Envio"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                nova_linha["Enviado Por"] = st.session_state.get("usuario", "Sistema")
                
                # Campos vazios para próximas etapas
                linha_vazia = inicializar_linha_vazia_rpv()
                for campo in linha_vazia:
                    if campo not in nova_linha:
                        nova_linha[campo] = linha_vazia[campo]
                
                # Adicionar linha ao DataFrame
                st.session_state.df_editado_rpv = pd.concat(
                    [st.session_state.df_editado_rpv, pd.DataFrame([nova_linha])],
                    ignore_index=True
                )
                
                # Guardar preview
                if "preview_novas_linhas_rpv" not in st.session_state:
                    st.session_state["preview_novas_linhas_rpv"] = pd.DataFrame()
                st.session_state["preview_novas_linhas_rpv"] = pd.concat(
                    [st.session_state["preview_novas_linhas_rpv"], pd.DataFrame([nova_linha])],
                    ignore_index=True
                )
                
                # LIMPAR CAMPOS DO FORMULÁRIO
                limpar_campos_formulario("input_rpv_")
                
                st.session_state.form_reset_counter_rpv += 1
                
                # MENSAGEM DE SUCESSO DETALHADA
                if solicitar_certidao:
                    st.success("✅ RPV cadastrado e enviado automaticamente para **Financeiro** e **Jurídico** (certidão solicitada)!")
                else:
                    st.success("✅ RPV cadastrado e enviado automaticamente para **Financeiro**!")
                
                st.info("💡 O RPV foi automaticamente enviado e está disponível para as próximas etapas do fluxo")
                st.rerun()

def interface_lista_rpv(df, perfil_usuario):
    """Lista de RPVs com botão Abrir para ações"""
    st.subheader("📊 Lista de RPVs")
    
    # Filtros
    col_filtro1, col_filtro2 = st.columns(2)
    
    with col_filtro1:
        if "Status" in df.columns:
            status_filtro = st.selectbox(
                "🔍 Filtrar por Status:",
                ["Todos"] + list(STATUS_ETAPAS_RPV.values())
            )
        else:
            status_filtro = "Todos"
    
    with col_filtro2:
        mostrar_apenas_meus = False
        if perfil_usuario == "Jurídico":
            mostrar_apenas_meus = st.checkbox("Mostrar apenas RPVs que preciso de certidão")
        elif perfil_usuario == "Financeiro":
            mostrar_apenas_meus = st.checkbox("Mostrar apenas RPVs que posso editar")
    
    # Aplicar filtros
    df_filtrado = df.copy()
    
    if status_filtro != "Todos" and "Status" in df.columns:
        df_filtrado = df_filtrado[df_filtrado["Status"] == status_filtro]
    
    if mostrar_apenas_meus:
        if perfil_usuario == "Jurídico" and "Solicitar Certidão" in df.columns:
            df_filtrado = df_filtrado[
                (df_filtrado["Solicitar Certidão"] == "Sim") &
                (df_filtrado["Status"].isin(["Enviado", "Certidão anexa"]))
            ]
        elif perfil_usuario == "Financeiro" and "Status" in df.columns:
            df_filtrado = df_filtrado[df_filtrado["Status"].isin([
                "Enviado", "Certidão anexa", "Enviado para Rodrigo"
            ])]
    
    # Exibir lista com botão Abrir - USAR ID
    if len(df_filtrado) > 0:
        st.markdown(f"### 📋 Lista ({len(df_filtrado)} RPVs)")
        
        for idx, rpv in df_filtrado.iterrows():
            col_abrir, col_processo, col_beneficiario, col_valor, col_status = st.columns([1, 2, 2, 1.5, 2])
            
            # USAR ID ÚNICO EM VEZ DE PROCESSO
            rpv_id = rpv.get("ID", idx)  # Fallback para índice se ID não existir
            
            with col_abrir:
                if st.button(f"🔓 Abrir", key=f"abrir_rpv_id_{rpv_id}"):  # ← MUDANÇA AQUI
                    st.session_state['rpv_aberto'] = rpv_id  # ← SALVAR ID EM VEZ DE PROCESSO
                    st.rerun()
            
            with col_processo:
                st.write(f"**{rpv.get('Processo', 'N/A')}**")
            
            with col_beneficiario:
                st.write(rpv.get('Beneficiário', 'N/A'))
            
            with col_valor:
                st.write(rpv.get('Valor RPV', 'N/A'))
            
            with col_status:
                # Colorir status
                status_atual = rpv.get('Status', 'N/A')
                if status_atual == 'Cadastrado':
                    st.write(f"🟡 {status_atual}")
                elif status_atual == 'Enviado':
                    st.write(f"🟠 {status_atual}")
                elif status_atual == 'Certidão anexa':
                    st.write(f"🔵 {status_atual}")
                elif status_atual == 'Enviado para Rodrigo':
                    st.write(f"🟣 {status_atual}")
                elif status_atual == 'Finalizado':
                    st.write(f"🟢 {status_atual}")
                else:
                    st.write(status_atual)
        
        # Interface de edição se RPV foi aberto - USAR ID
        if 'rpv_aberto' in st.session_state:
            st.markdown("---")
            rpv_id = st.session_state['rpv_aberto']  # ← PEGAR ID
            
            # Botão para fechar
            if st.button("❌ Fechar", key="fechar_rpv"):
                del st.session_state['rpv_aberto']
                st.rerun()
            
            # Buscar dados do RPV POR ID
            linha_rpv = df[df["ID"] == rpv_id]  # ← BUSCAR POR ID
            if len(linha_rpv) > 0:
                linha_rpv = linha_rpv.iloc[0]
                processo = linha_rpv["Processo"]  # ← OBTER PROCESSO DO REGISTRO
                status_atual = linha_rpv.get("Status", "")
                
                # Interface baseada no status e perfil
                interface_edicao_rpv(df, rpv_id, status_atual, perfil_usuario)  # ← PASSAR ID
            else:
                st.error("❌ RPV não encontrado")
    else:
        st.info("Nenhum RPV encontrado com os filtros aplicados")

def interface_edicao_rpv(df, rpv_id, status_atual, perfil_usuario):  # ← RECEBER ID EM VEZ DE PROCESSO
    """Interface de edição baseada no ID único"""
    
    # Buscar dados do RPV POR ID
    linha_rpv = df[df["ID"] == rpv_id].iloc[0]  # ← BUSCAR POR ID
    processo = linha_rpv["Processo"]  # ← OBTER PROCESSO
    
    st.markdown(f"### 📄 Editando RPV: {processo}")
    st.markdown(f"**ID:** {rpv_id} | **Beneficiário:** {linha_rpv.get('Beneficiário', 'N/A')}")
    st.markdown(f"**Beneficiário:** {linha_rpv.get('Beneficiário', 'N/A')}")
    st.markdown(f"**Status atual:** {status_atual}")
    st.markdown(f"**Solicitar Certidão:** {linha_rpv.get('Solicitar Certidão', 'N/A')}")
    
    # Mostrar informações básicas
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.write(f"**Valor:** {linha_rpv.get('Valor RPV', 'N/A')}")
    with col_info2:
        st.write(f"**CPF:** {linha_rpv.get('CPF', 'N/A')}")
    with col_info3:
        st.write(f"**Cadastrado em:** {linha_rpv.get('Data Cadastro', 'N/A')}")
    
    # Mostrar PDF se existe
    if linha_rpv.get("PDF RPV"):
        st.markdown("**📄 PDF do RPV:**")
        baixar_arquivo_github(linha_rpv["PDF RPV"], "📎 Baixar PDF")
    
    st.markdown("---")
    
    # ETAPA 2: Enviado -> Anexar Certidão (Jurídico)
    if status_atual == "Enviado" and perfil_usuario == "Jurídico":
        solicitar_certidao = linha_rpv.get("Solicitar Certidão", "Não") == "Sim"
        
        if not solicitar_certidao:
            st.warning("⚠️ Este RPV não requer certidão")
            return
            
        st.markdown("#### 📎 Anexar Certidão")
        
        # Verificar se já existe certidão
        if linha_rpv.get("Certidão Anexada"):
            st.success("✅ Certidão já anexada")
            baixar_arquivo_github(linha_rpv["Certidão Anexada"], "📎 Ver Certidão")
        
        certidao_arquivo = st.file_uploader(
            "Anexar Certidão:",
            type=["pdf", "jpg", "jpeg", "png"],
            key=f"certidao_{processo}"
        )
        
        if certidao_arquivo:
            if st.button("📎 Anexar Certidão", key=f"enviar_rpv_id_{rpv_id}", type="primary"):
                # Salvar certidão
                certidao_url = salvar_arquivo(certidao_arquivo, processo, "certidao")
                
                if certidao_url:
                    # Atualizar status
                    idx = df[df["ID"] == rpv_id].index[0]
                    st.session_state.df_editado_rpv.loc[idx, "Status"] = "Certidão anexa"
                    st.session_state.df_editado_rpv.loc[idx, "Certidão Anexada"] = certidao_url
                    st.session_state.df_editado_rpv.loc[idx, "Data Certidão"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                    st.session_state.df_editado_rpv.loc[idx, "Anexado Certidão Por"] = st.session_state.get("usuario", "Sistema")
                    
                    # Salvar no GitHub
                    novo_sha = save_data_to_github_seguro(
                        st.session_state.df_editado_rpv,
                        "lista_rpv.csv",
                        st.session_state.file_sha_rpv
                    )
                    st.session_state.file_sha_rpv = novo_sha
                    
                    st.success("✅ Certidão anexada com sucesso!")
                    del st.session_state['rpv_aberto']
                    st.rerun()
    
    # ETAPA 4: Enviar para Rodrigo (Financeiro)
    elif status_atual in ["Enviado", "Certidão anexa"] and perfil_usuario == "Financeiro":
        st.markdown("#### 👨‍💼 Enviar para Rodrigo")
        
        # Mostrar certidão se existe
        if linha_rpv.get("Certidão Anexada"):
            st.markdown("**📎 Certidão anexada:**")
            baixar_arquivo_github(linha_rpv["Certidão Anexada"], "📎 Ver Certidão")
        
        st.markdown("**📋 Informações do envio:**")
        st.write(f"- Enviado em: {linha_rpv.get('Data Envio', 'N/A')}")
        st.write(f"- Enviado por: {linha_rpv.get('Enviado Por', 'N/A')}")
        
        if st.button("👨‍💼 Enviar para Rodrigo", type="primary", key=f"enviar_rpv_id_{rpv_id}"):
            # Atualizar status
            idx = df[df["ID"] == rpv_id].index[0]
            st.session_state.df_editado_rpv.loc[idx, "Status"] = "Enviado para Rodrigo"
            st.session_state.df_editado_rpv.loc[idx, "Data Envio Rodrigo"] = datetime.now().strftime("%d/%m/%Y %H:%M")
            st.session_state.df_editado_rpv.loc[idx, "Enviado Rodrigo Por"] = st.session_state.get("usuario", "Sistema")
            
            # Salvar no GitHub
            novo_sha = save_data_to_github_seguro(
                st.session_state.df_editado_rpv,
                "lista_rpv.csv",
                st.session_state.file_sha_rpv
            )
            st.session_state.file_sha_rpv = novo_sha
            
            st.success("✅ RPV enviado para Rodrigo!")
            del st.session_state['rpv_aberto']
            st.rerun()
    
    # ETAPA 5: Finalizar RPV (Financeiro)
    elif status_atual == "Enviado para Rodrigo" and perfil_usuario == "Financeiro":
        st.markdown("#### ✅ Finalizar RPV")
        
        st.markdown("**📋 Informações do processo:**")
        st.write(f"- Enviado para Rodrigo em: {linha_rpv.get('Data Envio Rodrigo', 'N/A')}")
        st.write(f"- Enviado por: {linha_rpv.get('Enviado Rodrigo Por', 'N/A')}")
        
        # Uploads finais
        col_upload1, col_upload2 = st.columns(2)
        
        with col_upload1:
            st.markdown("**📄 Comprovante de Saque (Rodrigo)**")
            comprovante_saque = st.file_uploader(
                "Comprovante de saque:",
                type=["pdf", "jpg", "jpeg", "png"],
                key=f"saque_{processo}"
            )
            
            # Mostrar se já existe
            if linha_rpv.get("Comprovante Saque"):
                baixar_arquivo_github(linha_rpv["Comprovante Saque"], "📎 Ver Comprovante")
        
        with col_upload2:
            st.markdown("**📄 Comprovante de Pagamento (Clientes)**")
            comprovante_pagamento = st.file_uploader(
                "Comprovante de pagamento:",
                type=["pdf", "jpg", "jpeg", "png"],
                key=f"pagamento_{processo}"
            )
            
            # Mostrar se já existe
            if linha_rpv.get("Comprovante Pagamento"):
                baixar_arquivo_github(linha_rpv["Comprovante Pagamento"], "📎 Ver Comprovante")
        
        # Campo valor final
        st.markdown("**💰 Valor Final para o Escritório**")
        valor_final = st.text_area(
            "Detalhamento do valor final:",
            key=f"valor_final_{processo}",
            height=100,
            placeholder="Ex: Valor bruto: R$ 10.000,00\nDescontos: R$ 2.000,00\nValor líquido escritório: R$ 8.000,00\nDetalhes: ..."
        )
        
        if comprovante_saque and comprovante_pagamento and valor_final.strip():
            if st.button("✅ Finalizar RPV", key=f"enviar_rpv_id_{rpv_id}", type="primary"):
                # Salvar comprovantes
                saque_url = salvar_arquivo(comprovante_saque, processo, "saque")
                pagamento_url = salvar_arquivo(comprovante_pagamento, processo, "pagamento")
                
                if saque_url and pagamento_url:
                    # Atualizar status
                    idx = df[df["ID"] == rpv_id].index[0]
                    st.session_state.df_editado_rpv.loc[idx, "Status"] = "Finalizado"
                    st.session_state.df_editado_rpv.loc[idx, "Comprovante Saque"] = saque_url
                    st.session_state.df_editado_rpv.loc[idx, "Comprovante Pagamento"] = pagamento_url
                    st.session_state.df_editado_rpv.loc[idx, "Valor Final Escritório"] = valor_final
                    st.session_state.df_editado_rpv.loc[idx, "Data Finalização"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                    st.session_state.df_editado_rpv.loc[idx, "Finalizado Por"] = st.session_state.get("usuario", "Sistema")
                    
                    # Salvar no GitHub
                    novo_sha = save_data_to_github_seguro(
                        st.session_state.df_editado_rpv,
                        "lista_rpv.csv",
                        st.session_state.file_sha_rpv
                    )
                    st.session_state.file_sha_rpv = novo_sha
                    
                    st.success("🎉 RPV finalizado com sucesso!")
                    st.balloons()
                    del st.session_state['rpv_aberto']
                    st.rerun()
        else:
            st.info("📋 Anexe ambos os comprovantes e preencha o valor final para finalizar")
    
    # RPV FINALIZADO - Apenas visualização
    elif status_atual == "Finalizado":
        st.markdown("#### 🎉 RPV Finalizado")
        st.success("✅ Este RPV foi concluído com sucesso!")
        
        # Mostrar documentos finais
        col_final1, col_final2 = st.columns(2)
        
        with col_final1:
            if linha_rpv.get("Comprovante Saque"):
                st.markdown("**📄 Comprovante de Saque:**")
                baixar_arquivo_github(linha_rpv["Comprovante Saque"], "📎 Baixar Comprovante")
        
        with col_final2:
            if linha_rpv.get("Comprovante Pagamento"):
                st.markdown("**📄 Comprovante de Pagamento:**")
                baixar_arquivo_github(linha_rpv["Comprovante Pagamento"], "📎 Baixar Comprovante")
        
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

def interface_fluxo_trabalho_rpv(df, perfil_usuario):
    """Interface do fluxo de trabalho RPV"""
    st.subheader("🔄 Fluxo de Trabalho - RPV")
    
    # Dashboard geral (4 colunas em vez de 5, já que não há mais "Cadastrado")
    col_dash1, col_dash2, col_dash3, col_dash4 = st.columns(4)
    
    # Contadores por status
    if "Status" in df.columns:
        total_enviados = len(df[df["Status"] == "Enviado"])
        total_certidao = len(df[df["Status"] == "Certidão anexa"])
        total_rodrigo = len(df[df["Status"] == "Enviado para Rodrigo"])
        total_finalizados = len(df[df["Status"] == "Finalizado"])
    else:
        total_enviados = total_certidao = total_rodrigo = total_finalizados = 0
    
    with col_dash1:
        st.metric("📤 Enviados", total_enviados)
    
    with col_dash2:
        st.metric("📎 Com Certidão", total_certidao)
    
    with col_dash3:
        st.metric("👨‍💼 Com Rodrigo", total_rodrigo)
    
    with col_dash4:
        st.metric("✅ Finalizados", total_finalizados)
    
    st.markdown("---")
    
    # Interface específica por perfil
    if perfil_usuario == "Cadastrador":
        st.markdown("### 👨‍💻 Pendências do Cadastrador")
        if "Status" in df.columns:
            rpv_cadastrados = df[df["Status"] == "Cadastrado"]
            if len(rpv_cadastrados) > 0:
                st.markdown(f"#### 📤 RPVs para enviar ({len(rpv_cadastrados)}):")
                st.dataframe(rpv_cadastrados[["Processo", "Beneficiário", "Valor RPV", "Solicitar Certidão", "Data Cadastro"]], 
                           use_container_width=True)
            else:
                st.success("✅ Todos os RPVs cadastrados foram enviados!")
    
    elif perfil_usuario == "Jurídico":
        st.markdown("### ⚖️ Pendências do Jurídico")
        if "Status" in df.columns and "Solicitar Certidão" in df.columns:
            rpv_juridico = df[(df["Status"] == "Enviado") & (df["Solicitar Certidão"] == "Sim")]
            if len(rpv_juridico) > 0:
                st.markdown(f"#### 📎 RPVs aguardando certidão ({len(rpv_juridico)}):")
                st.dataframe(rpv_juridico[["Processo", "Beneficiário", "Valor RPV", "Data Envio"]], 
                           use_container_width=True)
            else:
                st.success("✅ Todas as certidões foram anexadas!")
    
    elif perfil_usuario == "Financeiro":
        st.markdown("### 💰 Pendências do Financeiro")
        if "Status" in df.columns:
            # RPVs para enviar para Rodrigo
            rpv_para_rodrigo = df[df["Status"].isin(["Enviado", "Certidão anexa"])]
            if len(rpv_para_rodrigo) > 0:
                st.markdown(f"#### 👨‍💼 RPVs para enviar para Rodrigo ({len(rpv_para_rodrigo)}):")
                st.dataframe(rpv_para_rodrigo[["Processo", "Beneficiário", "Valor RPV", "Status", "Solicitar Certidão"]], 
                           use_container_width=True)
            
            # RPVs para finalizar
            rpv_para_finalizar = df[df["Status"] == "Enviado para Rodrigo"]
            if len(rpv_para_finalizar) > 0:
                st.markdown(f"#### ✅ RPVs para finalizar ({len(rpv_para_finalizar)}):")
                st.dataframe(rpv_para_finalizar[["Processo", "Beneficiário", "Valor RPV", "Data Envio Rodrigo"]], 
                           use_container_width=True)
            
            if len(rpv_para_rodrigo) == 0 and len(rpv_para_finalizar) == 0:
                st.success("✅ Todas as pendências do financeiro foram resolvidas!")

def interface_visualizar_dados_rpv(df):
    """Interface para visualizar dados RPV"""
    st.subheader("📁 Visualizar Dados - RPV")
    
    if len(df) == 0:
        st.info("📋 Nenhum RPV encontrado para visualizar")
        return
    
    # Resumo geral
    col_resumo1, col_resumo2, col_resumo3, col_resumo4 = st.columns(4)
    
    with col_resumo1:
        st.metric("Total de RPVs", len(df))
    
    with col_resumo2:
        if "Status" in df.columns:
            finalizados = len(df[df["Status"] == "Finalizado"])
            st.metric("Finalizados", finalizados)
        else:
            st.metric("Finalizados", "N/A")
    
    with col_resumo3:
        if "Valor RPV" in df.columns:
            valores_validos = df[df["Valor RPV"].str.contains("R\$", na=False)]
            if len(valores_validos) > 0:
                valores = []
                for valor in valores_validos["Valor RPV"]:
                    try:
                        num = float(valor.replace("R$", "").replace(",", ".").strip())
                        valores.append(num)
                    except:
                        continue
                total_valor = sum(valores) if valores else 0
                st.metric("Valor Total", f"R$ {total_valor:,.2f}")
            else:
                st.metric("Valor Total", "R$ 0,00")
        else:
            st.metric("Valor Total", "N/A")
    
    with col_resumo4:
        if "Solicitar Certidão" in df.columns:
            com_certidao = len(df[df["Solicitar Certidão"] == "Sim"])
            st.metric("Com Certidão", com_certidao)
        else:
            st.metric("Com Certidão", "N/A")
    
    # Filtros para visualização
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
        if "Solicitar Certidão" in df.columns:
            certidao_filtro = st.multiselect(
                "Solicitar Certidão:",
                options=df["Solicitar Certidão"].unique(),
                default=df["Solicitar Certidão"].unique()
            )
        else:
            certidao_filtro = []
    
    with col_filtro3:
        mostrar_todas_colunas = st.checkbox("Mostrar todas as colunas", value=False)
    
    # Aplicar filtros
    df_visualizado = df.copy()
    
    if status_filtro and "Status" in df.columns:
        df_visualizado = df_visualizado[df_visualizado["Status"].isin(status_filtro)]
    
    if certidao_filtro and "Solicitar Certidão" in df.columns:
        df_visualizado = df_visualizado[df_visualizado["Solicitar Certidão"].isin(certidao_filtro)]
    
    # Selecionar colunas para exibir
    if mostrar_todas_colunas:
        colunas_exibir = df_visualizado.columns.tolist()
    else:
        colunas_principais = [
            "Processo", "Beneficiário", "Valor RPV", "Status", 
            "Solicitar Certidão", "Data Cadastro", "Cadastrado Por"
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
        
        # Análise por status
        if "Status" in df.columns and len(df) > 0:
            st.markdown("### 📈 Análise por Status")
            
            status_counts = df["Status"].value_counts()
            
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.markdown("**Distribuição por Status:**")
                st.bar_chart(status_counts)
            
            with col_chart2:
                st.markdown("**Resumo Quantitativo:**")
                for status, count in status_counts.items():
                    porcentagem = (count / len(df)) * 100
                    st.write(f"• **{status}:** {count} ({porcentagem:.1f}%)")
    
    else:
        st.info("Nenhum registro encontrado com os filtros aplicados")