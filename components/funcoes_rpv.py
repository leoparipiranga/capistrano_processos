# components/funcoes_rpv.py
import streamlit as st
import pandas as pd
import math
import re
import os
from datetime import datetime
from components.autocomplete_manager import (
    inicializar_autocomplete_session,
    adicionar_assunto_rpv,
    adicionar_orgao_rpv,
    campo_orgao_rpv,
    campo_assunto_rpv,
    carregar_dados_autocomplete
)
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

def safe_get_value(data, key, default='Não informado'):
    """
    Função para acessar valores de forma segura de um dicionário ou série pandas.
    Retorna o valor padrão se a chave não existir ou se o valor for None/NaN.
    """
    if hasattr(data, 'get'):
        value = data.get(key, default)
    else:
        try:
            value = data[key] if key in data else default
        except (KeyError, TypeError):
            return default
    
    # Verificar se é NaN, None ou string vazia
    if pd.isna(value) or value is None or value == '' or str(value).lower() in ['nan', 'none']:
        return default
    
    return str(value)

# =====================================
# CONFIGURAÇÕES DE PERFIS - RPV
# =====================================

# a) Novos Status - NOVO FLUXO DE TRABALHO
STATUS_ETAPAS_RPV = {
    1: "Cadastro",
    2: "SAC - aguardando documentação",
    3: "Administrativo - aguardando documentação",
    4: "SAC - documentação pronta",
    5: "Administrativo - documentação pronta",
    6: "Enviado para Rodrigo",
    7: "aguardando pagamento",
    8: "finalizado"
}

# Status que podem coexistir simultaneamente
STATUS_SIMULTANEOS_RPV = [
    ["SAC - aguardando documentação", "Administrativo - aguardando documentação"],
    ["SAC - documentação pronta", "Administrativo - documentação pronta"]
]

# b) Novas Permissões de Edição por Perfil - NOVO FLUXO
PERFIS_RPV = {
    "Cadastrador": ["Cadastro"], # Cadastrador apenas cria e pode editar cadastros
    "Financeiro": ["Enviado para Rodrigo", "aguardando pagamento"], # Financeiro atua nos estágios finais
    "Administrativo": ["SAC - aguardando documentação", "Administrativo - aguardando documentação", "SAC - documentação pronta", "Administrativo - documentação pronta"], # Perfil administrativo
    "SAC": ["SAC - aguardando documentação", "Administrativo - aguardando documentação", "SAC - documentação pronta", "Administrativo - documentação pronta"], # Perfil SAC
    "Admin": list(STATUS_ETAPAS_RPV.values())  # Admin tem acesso total
}

# c) Lista de Assuntos Comuns para RPV
ASSUNTOS_RPV = [
    "APOSENTADORIA POR INVALIDEZ",
    "APOSENTADORIA POR IDADE",
    "APOSENTADORIA ESPECIAL",
    "AUXILIO-DOENCA",
    "AUXILIO-ACIDENTE",
    "BENEFICIO DE PRESTACAO CONTINUADA (BPC)",
    "PENSAO POR MORTE",
    "SALARIO-MATERNIDADE",
    "REVISAO DE BENEFICIO",
    "DIFERENCAS DE APOSENTADORIA",
    "RENDA MENSAL VITALICIA",
    "OUTROS"
]

# d) Lista de Órgãos Judiciais Comuns para RPV
ORGAOS_JUDICIAIS_RPV = [
    "TRF1 - TRIBUNAL REGIONAL FEDERAL DA 1A REGIAO",
    "TRF2 - TRIBUNAL REGIONAL FEDERAL DA 2A REGIAO",
    "TRF3 - TRIBUNAL REGIONAL FEDERAL DA 3A REGIAO",
    "TRF4 - TRIBUNAL REGIONAL FEDERAL DA 4A REGIAO",
    "TRF5 - TRIBUNAL REGIONAL FEDERAL DA 5A REGIAO",
    "TRF6 - TRIBUNAL REGIONAL FEDERAL DA 6A REGIAO",
    "STJ - SUPERIOR TRIBUNAL DE JUSTICA",
    "STF - SUPREMO TRIBUNAL FEDERAL",
    "TST - TRIBUNAL SUPERIOR DO TRABALHO",
    "OUTROS"
]

def salvar_arquivo_anexo(uploaded_file, rpv_id, tipo_comprovante):
    """Salva arquivo anexo no diretório anexos/ e retorna o nome do arquivo"""
    try:
        # Garantir que o diretório anexos existe
        anexos_dir = "anexos"
        if not os.path.exists(anexos_dir):
            os.makedirs(anexos_dir)
        
        # Criar nome único para o arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extensao = uploaded_file.name.split(".")[-1] if "." in uploaded_file.name else "pdf"
        nome_arquivo = f"{tipo_comprovante}_{rpv_id}_{timestamp}.{extensao}"
        caminho_arquivo = os.path.join(anexos_dir, nome_arquivo)
        
        # Salvar arquivo
        with open(caminho_arquivo, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        return nome_arquivo
    except Exception as e:
        st.error(f"Erro ao salvar arquivo: {str(e)}")
        return None

def normalizar_assunto_rpv(texto):
    """Normaliza nome do assunto removendo acentos e convertendo para maiúsculo"""
    if not texto:
        return ""
    import unicodedata
    # Remove acentos
    texto_normalizado = unicodedata.normalize('NFD', texto)
    texto_sem_acento = ''.join(c for c in texto_normalizado if unicodedata.category(c) != 'Mn')
    return texto_sem_acento.upper().strip()

def normalizar_orgao_rpv(texto):
    """Normaliza nome do órgão removendo acentos e convertendo para maiúsculo"""
    if not texto:
        return ""
    import unicodedata
    # Remove acentos
    texto_normalizado = unicodedata.normalize('NFD', texto)
    texto_sem_acento = ''.join(c for c in texto_normalizado if unicodedata.category(c) != 'Mn')
    return texto_sem_acento.upper().strip()

def obter_assuntos_rpv():
    """Retorna lista de assuntos RPV salvos + padrões"""
    # Inicializa dados de autocomplete da sessão com dados persistidos
    inicializar_autocomplete_session()
    
    # Carrega dados salvos
    dados_salvos = carregar_dados_autocomplete()
    assuntos_salvos = dados_salvos.get("assuntos_rpv", [])
    
    return sorted(list(set(ASSUNTOS_RPV + assuntos_salvos)))

def obter_orgaos_rpv():
    """Retorna lista de órgãos RPV salvos + padrões"""
    # Inicializa dados de autocomplete da sessão com dados persistidos
    inicializar_autocomplete_session()
    
    # Carrega dados salvos
    dados_salvos = carregar_dados_autocomplete()
    orgaos_salvos = dados_salvos.get("orgaos_rpv", [])
    
    return sorted(list(set(ORGAOS_JUDICIAIS_RPV + orgaos_salvos)))

# =====================================
# FUNÇÕES DE PERFIL E CONTROLE - RPV
# =====================================

def validar_mes_competencia(mes_competencia):
    """Valida se o mês de competência está no formato mm/yyyy"""
    if not mes_competencia:
        return True  # Campo opcional
    
    # Se for string, validar formato mm/yyyy
    if isinstance(mes_competencia, str):
        mes_competencia = mes_competencia.strip()
        if len(mes_competencia) != 7 or mes_competencia[2] != '/':
            return False
        
        try:
            mes, ano = mes_competencia.split('/')
            if len(mes) != 2 or len(ano) != 4:
                return False
            
            mes_int = int(mes)
            ano_int = int(ano)
            
            # Validar ranges
            if not (1 <= mes_int <= 12):
                return False
            if not (2020 <= ano_int <= 2030):
                return False
                
            return True
        except (ValueError, IndexError):
            return False
    
    # Se for um objeto datetime.date, não precisa validar (já está correto)
    if hasattr(mes_competencia, 'strftime'):
        return True
    
    import re
    # Padrão: mm/yyyy (01-12/ano de 4 dígitos) - apenas para strings
    padrao = r'^(0[1-9]|1[0-2])\/\d{4}$'
    return bool(re.match(padrao, str(mes_competencia)))

def verificar_perfil_usuario_rpv():
    """Verifica o perfil do usuário logado para RPV a partir do session_state."""
    # Primeiro tenta pegar do session_state (definido no login)
    perfil = st.session_state.get("perfil_usuario", "")
    
    if perfil and perfil != "N/A":
        return perfil
    
    # Fallback: tentar pegar do secrets se não estiver no session_state
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
    """Verifica se o usuário pode editar determinado status RPV - NOVO FLUXO"""
    return status_atual in PERFIS_RPV.get(perfil_usuario, [])

def garantir_colunas_novo_fluxo(df):
    """Garante que as colunas do novo fluxo existem no DataFrame"""
    colunas_novas = [
        "Status Secundario",
        "SAC Documentacao Pronta",
        "Data SAC Documentacao",
        "SAC Responsavel",
        "Admin Documentacao Pronta",
        "Data Admin Documentacao",
        "Admin Responsavel",
        "Validado Financeiro",
        "Data Validacao",
        "Validado Por",
        "Comprovante Recebimento",
        "Data Recebimento",
        "Recebido Por",
        "Comprovante Pagamento",
        "Data Pagamento",
        "Pago Por",
        "Data Finalizacao",
        "Honorarios Contratuais",
        "HC1",
        "HC2"
    ]
    
    for coluna in colunas_novas:
        if coluna not in df.columns:
            df[coluna] = ""
    
    return df

def safe_get_status_secundario(linha_rpv):
    """Obtém status secundário de forma segura, tratando float/NaN"""
    status_secundario = linha_rpv.get("Status Secundario", "")
    
    # Converter para string segura
    status_sec_str = str(status_secundario) if status_secundario is not None else ""
    if status_sec_str.lower() in ['nan', 'none', '']:
        return ""
    
    return status_sec_str.strip()

def tem_status_simultaneo(linha_rpv):
    """Verifica se o RPV tem status simultâneo ativo"""
    status_sec_str = safe_get_status_secundario(linha_rpv)
    return status_sec_str != ""

def obter_status_simultaneo_ativo(linha_rpv):
    """Retorna lista com os status ativos (principal + secundário se existir)"""
    status_principal = linha_rpv.get("Status", "")
    status_sec_str = safe_get_status_secundario(linha_rpv)
    
    status_ativos = [status_principal] if status_principal else []
    if status_sec_str:
        status_ativos.append(status_sec_str)
    
    return status_ativos

def iniciar_status_simultaneo(df, rpv_id, status_principal, status_secundario):
    """Inicia status simultâneo para um RPV"""
    idx = df[df["ID"] == rpv_id].index[0]
    df.loc[idx, "Status"] = status_principal
    df.loc[idx, "Status Secundario"] = status_secundario
    return df

def finalizar_status_simultaneo(df, rpv_id, novo_status):
    """Finaliza status simultâneo e define status único"""
    idx = df[df["ID"] == rpv_id].index[0]
    df.loc[idx, "Status"] = novo_status
    df.loc[idx, "Status Secundario"] = ""  # Limpa status secundário
    return df

def pode_editar_qualquer_status_simultaneo(linha_rpv, perfil_usuario):
    """Verifica se o usuário pode editar pelo menos um dos status simultâneos"""
    status_ativos = obter_status_simultaneo_ativo(linha_rpv)
    
    for status in status_ativos:
        if pode_editar_status_rpv(status, perfil_usuario):
            return True
    
    return False

def obter_colunas_controle_rpv():
    """Retorna lista das colunas de controle do fluxo RPV - NOVO FLUXO"""
    return [
        "Assunto", "Solicitar Certidão", "Status", "Status Secundario", "Data Cadastro", "Cadastrado Por",
        "PDF RPV", "Data Envio", "Enviado Por", "Mês Competência",
        "SAC Documentacao Pronta", "Data SAC Documentacao", "SAC Responsavel",
        "Admin Documentacao Pronta", "Data Admin Documentacao", "Admin Responsavel",
        "Validado Financeiro", "Data Validacao", "Validado Por",
        "Comprovante Recebimento", "Data Comprovante Recebimento", "Recebimento Por",
        "Comprovante Pagamento", "Valor Líquido", "Observações Pagamento",
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
    """Interface principal para listar RPVs com sistema de dropdown"""
    
    # LIMPAR ESTADOS DE DIÁLOGO ao entrar na aba de lista
    if st.session_state.get("show_rpv_dialog", False):
        st.session_state.show_rpv_dialog = False
    if st.session_state.get("rpv_aberto_id") is not None:
        st.session_state.rpv_aberto_id = None
    
    # Inicializar estado dos cards expandidos
    if "rpv_expanded_cards" not in st.session_state:
        st.session_state.rpv_expanded_cards = set()
    
    if df.empty:
        st.info("ℹ️ Não há RPVs para visualizar.")
        return

    # Cards de estatísticas
    total_rpvs = len(df)
    finalizados = len(df[df["Status"] == "finalizado"]) if "Status" in df.columns else 0
    pendentes = total_rpvs - finalizados
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de RPVs", total_rpvs)
    
    with col2:
        st.metric("Finalizados", finalizados)
    
    with col3:
        st.metric("Pendentes", pendentes)
    
    with col4:
        if "Data Cadastro" in df.columns:
            hoje = datetime.now().strftime("%d/%m/%Y")
            df_temp = df.copy()
            df_temp["Data Cadastro"] = df_temp["Data Cadastro"].astype(str)
            hoje_count = len(df_temp[df_temp["Data Cadastro"].str.contains(hoje, na=False)])
        else:
            hoje_count = 0
        st.metric("Cadastrados Hoje", hoje_count)

    # Filtros
    st.markdown("---")
    col_filtro1, col_filtro2, col_filtro3, col_filtro4 = st.columns(4)
    
    with col_filtro1:
        status_unicos = ["Todos"] + list(df["Status"].dropna().unique()) if "Status" in df.columns else ["Todos"]
        status_filtro = st.selectbox("Status:", options=status_unicos, key="lista_rpv_status")
        
    with col_filtro2:
        usuarios_unicos = ["Todos"] + list(df["Cadastrado Por"].dropna().unique()) if "Cadastrado Por" in df.columns else ["Todos"]
        usuario_filtro = st.selectbox("Cadastrado Por:", options=usuarios_unicos, key="lista_rpv_user")
    
    with col_filtro3:
        if "Orgao Judicial" in df.columns:
            orgaos_unicos = ["Todos"] + list(df["Orgao Judicial"].dropna().unique())
            orgao_filtro = st.selectbox("Órgão Judicial:", options=orgaos_unicos, key="lista_rpv_orgao")
        else:
            orgao_filtro = "Todos"
    
    with col_filtro4:
        pesquisa = st.text_input("🔎 Pesquisar:", key="lista_rpv_search")

    # Aplicar filtros
    df_filtrado = df.copy()
    
    if status_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Status"] == status_filtro]
    
    if usuario_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Cadastrado Por"] == usuario_filtro]
        
    if orgao_filtro != "Todos" and "Orgao Judicial" in df.columns:
        df_filtrado = df_filtrado[df_filtrado["Orgao Judicial"] == orgao_filtro]
    
    if pesquisa:
        mask = pd.Series([False] * len(df_filtrado))
        for col in ["Beneficiário", "Processo", "CPF"]:
            if col in df_filtrado.columns:
                mask |= df_filtrado[col].astype(str).str.contains(pesquisa, case=False, na=False)
        df_filtrado = df_filtrado[mask]

    # Calcular total de registros filtrados
    total_registros_filtrados = len(df_filtrado)

    # Botões de Expandir/Recolher Todos
    if total_registros_filtrados > 0:
        st.markdown("---")
        col_exp1, col_exp2, col_exp_space = st.columns([2, 2, 6])
        
        with col_exp1:
            if st.button("🔽 Expandir Todos", key="expandir_todos_rpv"):
                # Adicionar todos os IDs dos RPVs filtrados ao set de expandidos
                for _, processo in df_filtrado.iterrows():
                    rpv_id = processo.get("ID", "N/A")
                    st.session_state.rpv_expanded_cards.add(rpv_id)
                st.rerun()
        
        with col_exp2:
            if st.button("🔼 Recolher Todos", key="recolher_todos_rpv"):
                # Limpar o set de cards expandidos
                st.session_state.rpv_expanded_cards.clear()
                st.rerun()

    # Paginação
    if "current_page_rpvs" not in st.session_state:
        st.session_state.current_page_rpvs = 1
    
    items_per_page = 10
    total_registros = len(df_filtrado)
    total_pages = math.ceil(total_registros / items_per_page) if items_per_page > 0 else 1
    
    start_idx = (st.session_state.current_page_rpvs - 1) * items_per_page
    end_idx = start_idx + items_per_page
    df_paginado = df_filtrado.iloc[start_idx:end_idx]

    # CSS para cards dropdown (exatamente igual ao benefícios)
    st.markdown("""
    <style>
    .rpv-card {
        border: 1px solid #e0e6ed;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        background-color: #fafbfc;
        transition: all 0.3s ease;
    }
    .rpv-card:hover {
        border-color: #0066cc;
        box-shadow: 0 2px 8px rgba(0,102,204,0.15);
        background-color: #f8f9ff;
    }
    .rpv-card.expanded {
        background-color: #f0f4ff;
        border-color: #0066cc;
        border-width: 2px;
        box-shadow: 0 4px 12px rgba(0,102,204,0.2);
    }
    .rpv-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        cursor: pointer;
    }
    .rpv-info-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 8px;
        margin-top: 8px;
    }
    .info-item {
        background: rgba(255,255,255,0.7);
        padding: 6px 8px;
        border-radius: 4px;
        border-left: 3px solid #0066cc;
    }
    .expanded .info-item {
        background: rgba(255,255,255,0.9);
        border-left: 3px solid #0055aa;
    }
    .info-label {
        font-size: 0.8em;
        color: #666;
        font-weight: bold;
    }
    .info-value {
        font-size: 0.9em;
        color: #333;
    }
    .tab-button {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 4px;
        padding: 8px 16px;
        margin-right: 8px;
        cursor: pointer;
        transition: all 0.2s;
    }
    .tab-button:hover {
        background: #e9ecef;
    }
    .tab-button.active {
        background: #0066cc;
        color: white;
        border-color: #0066cc;
    }
    </style>
    """, unsafe_allow_html=True)

    # Lista de RPVs
    if not df_paginado.empty:
        st.markdown(f"### 📋 Lista de RPVs ({total_registros} encontrados)")
        
        # Renderizar cards
        for _, rpv in df_paginado.iterrows():
            rpv_id = rpv.get("ID", "N/A")
            is_expanded = rpv_id in st.session_state.rpv_expanded_cards
            
            card_class = "rpv-card expanded" if is_expanded else "rpv-card"
            
            with st.container():
                # Card principal (exatamente como benefícios)
                st.markdown(f"""
                <div class="{card_class}">
                    <div class="rpv-card-header">
                        <div>
                            <strong>📄 {safe_get_value(rpv, 'Processo', 'Não informado')}</strong><br>
                            👤 {safe_get_value(rpv, 'Beneficiário', 'Não informado')}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Layout com botão expandir e informações
                col_expand, col_info = st.columns([1, 9])
                
                with col_expand:
                    expand_text = "▼ Fechar" if is_expanded else "▶ Abrir"
                    if st.button(expand_text, key=f"expand_rpv_{rpv_id}"):
                        if is_expanded:
                            st.session_state.rpv_expanded_cards.discard(rpv_id)
                        else:
                            st.session_state.rpv_expanded_cards.add(rpv_id)
                        st.rerun()
                
                with col_info:
                    # Informações resumidas (sempre visíveis)
                    st.markdown(f"""
                    <div class="rpv-info-grid">
                        <div class="info-item">
                            <div class="info-label">Valor RPV</div>
                            <div class="info-value">{safe_get_value(rpv, 'Valor RPV', 'Não informado')}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Mês Competência</div>
                            <div class="info-value">{safe_get_value(rpv, 'Mês Competência', 'Não informado')}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Assunto</div>
                            <div class="info-value">{safe_get_value(rpv, 'Assunto', 'Não informado')}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Órgão</div>
                            <div class="info-value">{safe_get_value(rpv, 'Orgao Judicial', 'Não informado')}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Conteúdo expandido (tabs)
                if is_expanded:
                    st.markdown("---")
                    st.markdown(f"### 📄 {safe_get_value(rpv, 'Processo', 'Não informado')}")
                    
                    # Tabs
                    tab_info, tab_acoes, tab_historico = st.tabs(["📋 Informações", "⚙️ Ações", "📜 Histórico"])
                    
                    # Definir status atual
                    status_atual = safe_get_value(rpv, 'Status', 'Não informado')
                    
                    with tab_info:
                        render_tab_info_rpv(rpv, rpv_id)
                    
                    with tab_acoes:
                        render_tab_acoes_rpv(df_filtrado, rpv, rpv_id, status_atual, perfil_usuario)
                    
                    with tab_historico:
                        render_tab_historico_rpv(rpv, rpv_id)
                    
    else:
        st.info("Nenhum RPV encontrado com os filtros aplicados.")

    # Controles de paginação
    if total_pages > 1:
        st.markdown("---")
        col_nav1, col_nav2, col_nav3 = st.columns([3, 2, 3])
        
        with col_nav1:
            if st.session_state.current_page_rpvs > 1:
                if st.button("<< Primeira", key="rpv_lista_primeira"):
                    st.session_state.current_page_rpvs = 1
                    st.rerun()
                if st.button("< Anterior", key="rpv_lista_anterior"):
                    st.session_state.current_page_rpvs -= 1
                    st.rerun()
        
        with col_nav2:
            st.write(f"Página {st.session_state.current_page_rpvs} de {total_pages}")
        
        with col_nav3:
            if st.session_state.current_page_rpvs < total_pages:
                if st.button("Próxima >", key="rpv_lista_proxima"):
                    st.session_state.current_page_rpvs += 1
                    st.rerun()
                if st.button("Última >>", key="rpv_lista_ultima"):
                    st.session_state.current_page_rpvs = total_pages
                    st.rerun()

def render_tab_info_rpv(processo, rpv_id):
    """Renderiza a tab de informações do RPV"""
        
    col_det1, col_det2 = st.columns(2)
    
    with col_det1:
        st.markdown("**📋 Dados Básicos:**")
        st.write(f"**CPF:** {safe_get_value(processo, 'CPF')}")
        st.write(f"**Agência:** {safe_get_value(processo, 'Agência')}")
        st.write(f"**Conta:** {safe_get_value(processo, 'Conta')}")
        st.write(f"**Banco:** {safe_get_value(processo, 'Banco')}")
    
    with col_det2:
        st.markdown("**💰 Valores:**")
        st.write(f"**Valor RPV:** {safe_get_value(processo, 'Valor RPV')}")
        st.write(f"**Mês Competência:** {safe_get_value(processo, 'Mês Competência')}")
        st.write(f"**Assunto:** {safe_get_value(processo, 'Assunto')}")
        st.write(f"**Órgão Judicial:** {safe_get_value(processo, 'Orgao Judicial')}")
    
    # Mostrar detalhes dos honorários contratuais
    mostrar_detalhes_hc_rpv(processo, f"info_{rpv_id}")
    
    # Observações
    if safe_get_value(processo, 'Observações'):
        st.markdown("### 📝 Observações")
        st.info(safe_get_value(processo, 'Observações'))

def render_tab_acoes_rpv(df, processo, rpv_id, status_atual, perfil_usuario):
    """Renderiza a tab de ações do RPV - mantém toda a lógica original"""
    
    # Usar a função original de edição, mas sem o cabeçalho
    linha_processo_df = df[df["ID"].astype(str) == str(rpv_id)]
    
    if len(linha_processo_df) == 0:
        st.error(f"❌ RPV com ID {rpv_id} não encontrado")
        return
    
    linha_processo = linha_processo_df.iloc[0]
    numero_processo = linha_processo.get("Processo", "N/A")
    
    # Renderizar ações baseadas no status - usando a lógica original da interface_edicao_rpv
    if status_atual == "Cadastro" and perfil_usuario in ["Cadastrador", "Admin"]:
        st.info("Após finalizar o cadastro, este RPV será enviado para os perfis SAC e Administrativo.")
        
        if st.button("✅ Finalizar Cadastro e Enviar", type="primary", key=f"finalizar_cadastro_tab_{rpv_id}"):
            idx = df[df["ID"] == rpv_id].index[0]
            
            # Iniciar status simultâneo
            st.session_state.df_editado_rpv = iniciar_status_simultaneo(
                st.session_state.df_editado_rpv,
                rpv_id,
                "SAC - aguardando documentação",
                "Administrativo - aguardando documentação"
            )
            
            # Adicionar data de envio
            now = str(datetime.now().strftime("%d/%m/%Y %H:%M"))
            st.session_state.df_editado_rpv.loc[idx, "Data Envio"] = now
            st.session_state.df_editado_rpv.loc[idx, "Enviado Por"] = str(st.session_state.get("usuario", "Sistema"))
            
            save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
            st.session_state.rpv_expanded_cards.discard(rpv_id)
            st.success("✅ RPV enviado simultaneamente para SAC e Administrativo!")
            st.rerun()
    
    elif (perfil_usuario in ["SAC", "Admin"]) and ("SAC - aguardando documentação" in obter_status_simultaneo_ativo(linha_processo)):
        st.info("Marque quando a documentação SAC estiver pronta.")
        
        # Verificar se já está marcado
        sac_doc_pronta = linha_processo.get("SAC Documentacao Pronta", "") == "Sim"
        
        if not sac_doc_pronta:
            if st.checkbox("✅ Documentação SAC pronta", key=f"sac_doc_tab_{rpv_id}"):
                if st.button("🔄 Marcar SAC como Pronto", type="primary", key=f"marcar_sac_tab_{rpv_id}"):
                    idx = df[df["ID"] == rpv_id].index[0]
                    
                    # Atualizar status SAC (sempre no status principal)
                    st.session_state.df_editado_rpv.loc[idx, "Status"] = "SAC - documentação pronta"
                    st.session_state.df_editado_rpv.loc[idx, "SAC Documentacao Pronta"] = "Sim"
                    st.session_state.df_editado_rpv.loc[idx, "Data SAC Documentacao"] = str(datetime.now().strftime("%d/%m/%Y %H:%M"))
                    st.session_state.df_editado_rpv.loc[idx, "SAC Responsavel"] = str(st.session_state.get("usuario", "Sistema"))
                    
                    save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                    st.session_state.rpv_expanded_cards.discard(rpv_id)
                    st.success("✅ Status SAC atualizado!")
                    st.rerun()
        else:
            st.success(f"✅ SAC já marcou documentação como pronta em {linha_processo.get('Data SAC Documentacao', 'N/A')}")
    
    elif (perfil_usuario in ["Administrativo", "Admin"]) and ("Administrativo - aguardando documentação" in obter_status_simultaneo_ativo(linha_processo)):
        st.info("Marque quando a documentação Administrativa estiver pronta.")
        
        # Verificar se já está marcado
        admin_doc_pronta = linha_processo.get("Admin Documentacao Pronta", "") == "Sim"
        
        if not admin_doc_pronta:
            if st.checkbox("✅ Documentação Administrativa pronta", key=f"admin_doc_tab_{rpv_id}"):
                if st.button("🔄 Marcar Administrativo como Pronto", type="primary", key=f"marcar_admin_tab_{rpv_id}"):
                    idx = df[df["ID"] == rpv_id].index[0]
                    
                    # Atualizar status Administrativo (sempre no status secundário)
                    st.session_state.df_editado_rpv.loc[idx, "Status Secundario"] = "Administrativo - documentação pronta"
                    st.session_state.df_editado_rpv.loc[idx, "Admin Documentacao Pronta"] = "Sim"
                    st.session_state.df_editado_rpv.loc[idx, "Data Admin Documentacao"] = str(datetime.now().strftime("%d/%m/%Y %H:%M"))
                    st.session_state.df_editado_rpv.loc[idx, "Admin Responsavel"] = str(st.session_state.get("usuario", "Sistema"))
                    
                    save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                    st.session_state.rpv_expanded_cards.discard(rpv_id)
                    st.success("✅ Status Administrativo atualizado!")
                    st.rerun()
        else:
            st.success(f"✅ Administrativo já marcou documentação como pronta em {linha_processo.get('Data Admin Documentacao', 'N/A')}")
    
    # SEÇÃO DE HONORÁRIOS CONTRATUAIS - Disponível para Financeiro e Admin
    if perfil_usuario in ["Financeiro", "Admin"]:
        st.markdown("---")
        st.markdown("### 💼 Honorários Contratuais")
        
        with st.form(f"form_hc_rpv_tab_{rpv_id}"):
            col_hc1, col_hc2 = st.columns(2)
            
            with col_hc1:
                honorarios_contratuais = st.number_input(
                    "Honorário Contratual 1:",
                    min_value=0.0,
                    value=safe_get_hc_value_rpv(linha_processo, "Honorarios Contratuais"),
                    step=0.01,
                    format="%.2f",
                    help="Valor principal dos honorários contratuais",
                    key=f"hc_rpv_tab_{rpv_id}"
                )
                
                # Campos HC adicionais
                hc1_valor, hc2_valor = 0.0, 0.0
                nivel_hc = st.session_state.get(f"hc_nivel_rpv_tab_{rpv_id}", 0)
                
                if nivel_hc >= 1:
                    hc1_valor = st.number_input(
                        "Honorário Contratual 2:",
                        min_value=0.0,
                        value=safe_get_hc_value_rpv(linha_processo, "HC1"),
                        step=0.01,
                        format="%.2f",
                        key=f"hc1_rpv_tab_{rpv_id}"
                    )
                
                if nivel_hc >= 2:
                    hc2_valor = st.number_input(
                        "Honorário Contratual 3:",
                        min_value=0.0,
                        value=safe_get_hc_value_rpv(linha_processo, "HC2"),
                        step=0.01,
                        format="%.2f",
                        key=f"hc2_rpv_tab_{rpv_id}"
                    )
            
            with col_hc2:
                # Mostrar total atual
                total_atual = calcular_total_hc_rpv(linha_processo)
                st.metric("Total HC Atual", f"R$ {total_atual:.2f}")
                
                # Mostrar detalhamento se há HCs adicionais
                if nivel_hc > 0:
                    st.markdown("**Detalhamento:**")
                    hc_principal = safe_get_hc_value_rpv(linha_processo, "Honorarios Contratuais")
                    st.write(f"HC1: R$ {hc_principal:.2f}")
                    if nivel_hc >= 1:
                        hc1_atual = safe_get_hc_value_rpv(linha_processo, "HC1")
                        st.write(f"HC2: R$ {hc1_atual:.2f}")
                    if nivel_hc >= 2:
                        hc2_atual = safe_get_hc_value_rpv(linha_processo, "HC2")
                        st.write(f"HC3: R$ {hc2_atual:.2f}")
            
            # Botão para salvar honorários
            salvar_hc = st.form_submit_button("💾 Salvar Honorários Contratuais", type="primary")
            
            if salvar_hc:
                try:
                    idx = df[df["ID"] == rpv_id].index[0]
                    
                    # Salvar valores
                    st.session_state.df_editado_rpv.loc[idx, "Honorarios Contratuais"] = honorarios_contratuais
                    
                    # Salvar HCs adicionais se foram preenchidos
                    if nivel_hc >= 1:
                        st.session_state.df_editado_rpv.loc[idx, "HC1"] = hc1_valor
                    if nivel_hc >= 2:
                        st.session_state.df_editado_rpv.loc[idx, "HC2"] = hc2_valor
                    
                    # Salvar no GitHub
                    save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                    
                    total_novo = honorarios_contratuais + hc1_valor + hc2_valor
                    st.success(f"✅ Honorários salvos! Total: R$ {total_novo:.2f}")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erro ao salvar honorários: {str(e)}")
    
    # Botão para expandir HCs (fora do form)
    if perfil_usuario in ["Financeiro", "Admin"]:
        if st.button("➕ Adicionar Honorários Contratuais", key=f"btn_hc_tab_{rpv_id}"):
            nivel_atual = st.session_state.get(f"hc_nivel_rpv_tab_{rpv_id}", 0)
            st.session_state[f"hc_nivel_rpv_tab_{rpv_id}"] = min(nivel_atual + 1, 2)
            st.rerun()
    
    # Outros status e ações...
    if status_atual not in ["Cadastro"] and not pode_editar_status_rpv(status_atual, perfil_usuario):
        st.info(f"Status Atual: {status_atual}")
        if perfil_usuario != "Admin":
            st.warning(f"⚠️ Seu perfil ({perfil_usuario}) não pode editar este status.")

def render_tab_historico_rpv(processo, rpv_id):
    """Renderiza a tab de histórico do RPV"""
    
    st.markdown("### 📜 Histórico do Processo")
    
    # Timeline do processo
    status_atual = safe_get_value(processo, 'Status')
    
    # Etapas do fluxo RPV
    etapas = [
        {
            "titulo": "📝 Cadastrado",
            "data": safe_get_value(processo, 'Data Cadastro'),
            "responsavel": safe_get_value(processo, 'Cadastrado Por'),
            "concluida": True  # Sempre concluída se existe
        },
        {
            "titulo": "📤 Enviado para SAC/Administrativo",
            "data": safe_get_value(processo, 'Data Envio'),
            "responsavel": safe_get_value(processo, 'Enviado Por'),
            "concluida": status_atual not in ["Cadastro"]
        },
        {
            "titulo": "📋 SAC - Documentação Pronta",
            "data": safe_get_value(processo, 'Data SAC Documentacao'),
            "responsavel": safe_get_value(processo, 'SAC Responsavel'),
            "concluida": safe_get_value(processo, 'SAC Documentacao Pronta') == "Sim"
        },
        {
            "titulo": "🏢 Administrativo - Documentação Pronta",
            "data": safe_get_value(processo, 'Data Admin Documentacao'),
            "responsavel": safe_get_value(processo, 'Admin Responsavel'),
            "concluida": safe_get_value(processo, 'Admin Documentacao Pronta') == "Sim"
        },
        {
            "titulo": "💰 Validado pelo Financeiro",
            "data": safe_get_value(processo, 'Data Validacao'),
            "responsavel": safe_get_value(processo, 'Validado Por'),
            "concluida": safe_get_value(processo, 'Validado Financeiro') == "Sim"
        },
        {
            "titulo": "📨 Comprovante de Recebimento",
            "data": safe_get_value(processo, 'Data Recebimento'),
            "responsavel": safe_get_value(processo, 'Recebido Por'),
            "concluida": safe_get_value(processo, 'Comprovante Recebimento') != ""
        },
        {
            "titulo": "🎯 Finalizado",
            "data": safe_get_value(processo, 'Data Finalizacao'),
            "responsavel": safe_get_value(processo, 'Finalizado Por'),
            "concluida": status_atual == "finalizado"
        }
    ]
    
    for i, etapa in enumerate(etapas):
        if etapa["concluida"] and etapa["data"] != "Não informado":
            # Etapa concluída
            st.markdown(f"""
            <div style="border-left: 4px solid #28a745; padding-left: 16px; margin-bottom: 16px;">
                <div style="color: #28a745; font-weight: bold;">✅ {etapa["titulo"]}</div>
                <div style="color: #6c757d; font-size: 0.9em;">
                    📅 {etapa["data"]}<br>
                    👤 {etapa["responsavel"]}
                </div>
            </div>
            """, unsafe_allow_html=True)
        elif etapa["concluida"]:
            # Etapa atual (sem data específica)
            st.markdown(f"""
            <div style="border-left: 4px solid #ffc107; padding-left: 16px; margin-bottom: 16px;">
                <div style="color: #ffc107; font-weight: bold;">🔄 {etapa["titulo"]}</div>
                <div style="color: #6c757d; font-size: 0.9em;">Em andamento</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Etapa futura
            st.markdown(f"""
            <div style="border-left: 4px solid #dee2e6; padding-left: 16px; margin-bottom: 16px;">
                <div style="color: #6c757d; font-weight: bold;">⏳ {etapa["titulo"]}</div>
                <div style="color: #6c757d; font-size: 0.9em;">Pendente</div>
            </div>
            """, unsafe_allow_html=True)

def confirmar_exclusao_massa_rpv(df, processos_selecionados):
    """Função para confirmar exclusão em massa de RPVs"""
    
    @st.dialog("🗑️ Confirmar Exclusão em Massa", width="large")
    def dialog_confirmacao():
        st.error("⚠️ **ATENÇÃO:** Esta ação não pode ser desfeita!")
        
        # Mostrar processos que serão excluídos
        st.markdown(f"### Você está prestes a excluir **{len(processos_selecionados)}** processo(s):")
        
        # Converter IDs para string para garantir comparação correta
        processos_selecionados_str = [str(pid) for pid in processos_selecionados]
        processos_para_excluir = df[df["ID"].astype(str).isin(processos_selecionados_str)]
        
        for _, processo in processos_para_excluir.iterrows():
            st.markdown(f"- **{processo.get('Processo', 'Não informado')}** - {processo.get('Beneficiário', 'Não informado')}")
        
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
                        processo_numero=processo.get('Processo', 'Não informado'),
                        dados_excluidos=processo,
                        usuario=usuario_atual
                    )
                
                # Converter IDs para o mesmo tipo para garantir comparação
                processos_selecionados_str = [str(pid) for pid in processos_selecionados]
                
                # Remover processos do DataFrame
                st.session_state.df_editado_rpv = st.session_state.df_editado_rpv[
                    ~st.session_state.df_editado_rpv["ID"].astype(str).isin(processos_selecionados_str)
                ].reset_index(drop=True)
                
                # Salvar no GitHub
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

def safe_get_hc_value_rpv(data, key, default=0.0):
    """Obtém valor de honorário contratual de forma segura, tratando NaN e valores None"""
    value = data.get(key, default)
    if value is None or value == "":
        return default
    try:
        # Converter para float
        float_value = float(value)
        if math.isnan(float_value):
            return default
        return float_value
    except (ValueError, TypeError):
        return default

def calcular_total_hc_rpv(linha_rpv):
    """Calcula o total dos honorários contratuais (HC + HC1 + HC2)"""
    hc = safe_get_hc_value_rpv(linha_rpv, "Honorarios Contratuais", 0.0)
    hc1 = safe_get_hc_value_rpv(linha_rpv, "HC1", 0.0)
    hc2 = safe_get_hc_value_rpv(linha_rpv, "HC2", 0.0)
    return hc + hc1 + hc2

def mostrar_detalhes_hc_rpv(linha_rpv, key_suffix=""):
    """Mostra detalhes individuais dos honorários contratuais para RPV"""
    total_hc = calcular_total_hc_rpv(linha_rpv)
    
    if total_hc > 0:
        with st.expander(f"💼 Ver Detalhes dos Honorários Contratuais (Total: R$ {total_hc:.2f})"):
            col1, col2, col3 = st.columns(3)
            
            hc = safe_get_hc_value_rpv(linha_rpv, "Honorarios Contratuais", 0.0)
            hc1 = safe_get_hc_value_rpv(linha_rpv, "HC1", 0.0)
            hc2 = safe_get_hc_value_rpv(linha_rpv, "HC2", 0.0)
            
            with col1:
                if hc > 0:
                    st.metric("💼 HC1", f"R$ {hc:.2f}")
                else:
                    st.info("💼 HC1: Não informado")
            
            with col2:
                if hc1 > 0:
                    st.metric("💰 HC2", f"R$ {hc1:.2f}")
                else:
                    st.info("💰 HC2: Não informado")
            
            with col3:
                if hc2 > 0:
                    st.metric("📊 HC3", f"R$ {hc2:.2f}")
                else:
                    st.info("📊 HC3: Não informado")
                    
            st.success(f"💎 **Total Geral:** R$ {total_hc:.2f}")
    else:
        st.info("💼 Nenhum honorário contratual cadastrado para esta RPV.")

def exibir_informacoes_basicas_rpv(linha_rpv, estilo="padrao"):
    """Exibe informações básicas do RPV de forma organizada e visual
    
    Args:
        linha_rpv: Dados da linha do RPV
        estilo: "padrao", "compacto", ou "horizontal"
    """
    
    if estilo == "padrao":
        exibir_info_estilo_padrao(linha_rpv)
    elif estilo == "compacto":
        exibir_info_estilo_compacto(linha_rpv)
    elif estilo == "horizontal":
        exibir_info_estilo_horizontal(linha_rpv)

def exibir_info_estilo_padrao(linha_rpv):
    """Estilo padrão - 3 colunas com cards verticais"""
    # Estilo CSS para os cards
    st.markdown("""
    <style>
    .info-card {
        background-color: #f8f9fa;
        border-left: 4px solid #0066cc;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .info-title {
        font-weight: bold;
        color: #0066cc;
        font-size: 14px;
        margin-bottom: 5px;
    }
    .info-value {
        font-size: 16px;
        color: #333;
        margin-bottom: 8px;
    }
    .status-badge {
        padding: 5px 10px;
        border-radius: 15px;
        font-weight: bold;
        font-size: 12px;
        display: inline-block;
    }
    .status-enviado { background-color: #fff3cd; color: #856404; }
    .status-aguardando { background-color: #d1ecf1; color: #0c5460; }
    .status-pagamento { background-color: #d4edda; color: #155724; }
    .status-atrasado { background-color: #f8d7da; color: #721c24; }
    .status-finalizado { background-color: #d1e7dd; color: #0f5132; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📋 Informações do Processo")
    
    # Layout em colunas para informações básicas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="info-card">
            <div class="info-title">📄 Número do Processo</div>
            <div class="info-value">{safe_get_value(linha_rpv, 'Processo')}</div>
            
            <div class="info-title">👤 Beneficiário</div>
            <div class="info-value">{safe_get_value(linha_rpv, 'Beneficiário')}</div>
            
            <div class="info-title">🆔 CPF</div>
            <div class="info-value">{safe_get_value(linha_rpv, 'CPF')}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        status_atual = safe_get_value(linha_rpv, 'Status')
        status_class = {
            "Enviado ao Financeiro": "status-enviado",
            "Aguardando Certidão": "status-aguardando",
            "Aguardando Pagamento": "status-pagamento",
            "Pagamento Atrasado": "status-atrasado",
            "Finalizado": "status-finalizado"
        }.get(status_atual, "status-enviado")
        
        st.markdown(f"""
        <div class="info-card">
            <div class="info-title">📊 Status Atual</div>
            <div class="info-value">
                <span class="status-badge {status_class}">{status_atual}</span>
            </div>
            
            <div class="info-title">🏛️ Órgão Judicial</div>
            <div class="info-value">{safe_get_value(linha_rpv, 'Orgao Judicial')}</div>
            
            <div class="info-title">📂 Assunto</div>
            <div class="info-value">{safe_get_value(linha_rpv, 'Assunto')}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        valor_rpv = safe_get_value(linha_rpv, 'Valor RPV')
        mes_competencia = safe_get_value(linha_rpv, 'Mês Competência')
        data_cadastro = safe_get_value(linha_rpv, 'Data Cadastro')
        cadastrado_por = safe_get_value(linha_rpv, 'Cadastrado Por')
        
        st.markdown(f"""
        <div class="info-card">
            <div class="info-title">💰 Valor RPV</div>
            <div class="info-value">{valor_rpv}</div>
            
            <div class="info-title">📅 Mês Competência</div>
            <div class="info-value">{mes_competencia}</div>
            
            <div class="info-title">📝 Cadastrado por</div>
            <div class="info-value">{cadastrado_por}</div>
            
            <div class="info-title">🕐 Data Cadastro</div>
            <div class="info-value">{data_cadastro}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Informações adicionais se houver
    observacoes = safe_get_value(linha_rpv, 'Observações', '')
    # Verificar se observacoes é uma string válida e não vazia
    if observacoes and observacoes != 'N/A' and observacoes.strip():
        st.markdown(f"""
        <div class="info-card">
            <div class="info-title">📝 Observações</div>
            <div class="info-value">{observacoes}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")

def exibir_info_estilo_compacto(linha_rpv):
    """Estilo compacto - informações em grid menor"""
    st.markdown("""
    <style>
    .compact-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 10px;
        background: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #dee2e6;
        margin: 10px 0;
    }
    .compact-item {
        text-align: center;
        padding: 10px;
        background: transparent;
        border-radius: 8px;
        box-shadow: none;
    }
    .compact-label {
        font-size: 12px;
        color: #6c757d;
        font-weight: 600;
        margin-bottom: 5px;
    }
    .compact-value {
        font-size: 14px;
        color: #212529;
        font-weight: 500;
    }
    .compact-status {
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)
    
    status_atual = safe_get_value(linha_rpv, 'Status')
    status_class = {
        "Enviado ao Financeiro": "background-color: #fff3cd; color: #856404;",
        "Aguardando Certidão": "background-color: #d1ecf1; color: #0c5460;",
        "Aguardando Pagamento": "background-color: #d4edda; color: #155724;",
        "Pagamento Atrasado": "background-color: #f8d7da; color: #721c24;",
        "Finalizado": "background-color: #d1e7dd; color: #0f5132;"
    }.get(status_atual, "background-color: #e2e3e5; color: #383d41;")
    
    # Calcular total de honorários contratuais
    total_hc = calcular_total_hc_rpv(linha_rpv)
    
    st.markdown("### 📋 Resumo do Processo")
    st.markdown(f"""
    <div class="compact-grid">
        <div class="compact-item">
            <div class="compact-label">📄 PROCESSO</div>
            <div class="compact-value">{safe_get_value(linha_rpv, 'Processo')}</div>
        </div>
        <div class="compact-item">
            <div class="compact-label">👤 BENEFICIÁRIO</div>
            <div class="compact-value">{safe_get_value(linha_rpv, 'Beneficiário')}</div>
        </div>
        <div class="compact-item">
            <div class="compact-label">🆔 CPF</div>
            <div class="compact-value">{safe_get_value(linha_rpv, 'CPF')}</div>
        </div>
        <div class="compact-item">
            <div class="compact-label">📊 STATUS</div>
            <div class="compact-value">
                <span class="compact-status" style="{status_class}">{status_atual}</span>
            </div>
        </div>
        <div class="compact-item">
            <div class="compact-label">💰 VALOR RPV</div>
            <div class="compact-value">{safe_get_value(linha_rpv, 'Valor RPV')}</div>
        </div>
        <div class="compact-item">
            <div class="compact-label">💼 TOTAL HC</div>
            <div class="compact-value">R$ {total_hc:.2f}</div>
        </div>
        <div class="compact-item">
            <div class="compact-label">🏛️ ÓRGÃO</div>
            <div class="compact-value">{safe_get_value(linha_rpv, 'Orgao Judicial')[:20]}...</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    # Mostrar detalhes dos honorários contratuais
    mostrar_detalhes_hc_rpv(linha_rpv, "compacto")

def exibir_info_estilo_horizontal(linha_rpv):
    """Estilo horizontal - cards em linha"""
    st.markdown("""
    <style>
    .horizontal-container {
        display: flex;
        gap: 15px;
        margin: 20px 0;
        overflow-x: auto;
        padding: 10px 0;
    }
    .horizontal-card {
        min-width: 250px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        flex-shrink: 0;
    }
    .horizontal-card.primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .horizontal-card.success { background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%); }
    .horizontal-card.warning { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
    .horizontal-title {
        font-size: 14px;
        opacity: 0.9;
        margin-bottom: 8px;
        font-weight: 500;
    }
    .horizontal-value {
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .horizontal-subtitle {
        font-size: 12px;
        opacity: 0.8;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📋 Visão Geral do Processo")
    
    status_atual = safe_get_value(linha_rpv, 'Status')
    card_class = "primary"
    if status_atual == "Finalizado":
        card_class = "success"
    elif "Atrasado" in status_atual:
        card_class = "warning"
    
    processo_val = safe_get_value(linha_rpv, 'Processo')
    beneficiario_val = safe_get_value(linha_rpv, 'Beneficiário')
    valor_val = safe_get_value(linha_rpv, 'Valor RPV')
    competencia_val = safe_get_value(linha_rpv, 'Mês Competência')
    orgao_val = safe_get_value(linha_rpv, 'Orgao Judicial')
    assunto_val = safe_get_value(linha_rpv, 'Assunto')
    
    # Truncar textos longos de forma segura
    orgao_truncado = orgao_val[:15] + '...' if len(orgao_val) > 15 and orgao_val != 'N/A' else orgao_val
    assunto_truncado = assunto_val[:20] + '...' if len(assunto_val) > 20 and assunto_val != 'N/A' else assunto_val
    
    st.markdown(f"""
    <div class="horizontal-container">
        <div class="horizontal-card primary">
            <div class="horizontal-title">📄 PROCESSO</div>
            <div class="horizontal-value">{processo_val}</div>
            <div class="horizontal-subtitle">{beneficiario_val}</div>
        </div>
        
        <div class="horizontal-card {card_class}">
            <div class="horizontal-title">📊 STATUS</div>
            <div class="horizontal-value">{status_atual}</div>
            <div class="horizontal-subtitle">Última atualização</div>
        </div>
        
        <div class="horizontal-card primary">
            <div class="horizontal-title">💰 VALOR</div>
            <div class="horizontal-value">{valor_val}</div>
            <div class="horizontal-subtitle">Competência: {competencia_val}</div>
        </div>
        
        <div class="horizontal-card primary">
            <div class="horizontal-title">🏛️ ÓRGÃO</div>
            <div class="horizontal-value">{orgao_truncado}</div>
            <div class="horizontal-subtitle">Assunto: {assunto_truncado}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

def interface_edicao_rpv(df, rpv_id, status_atual, perfil_usuario):
    """Interface de edição completamente redesenhada para o NOVO FLUXO DE TRABALHO RPV."""
    
    linha_rpv = df[df["ID"] == rpv_id].iloc[0]
    numero_processo = linha_rpv.get("Processo", "Não informado")
    
    # Exibir informações básicas do processo com layout compacto
    exibir_informacoes_basicas_rpv(linha_rpv, "compacto")
    
    # Verificar status simultâneo
    tem_simultaneo = tem_status_simultaneo(linha_rpv)
    status_secundario = linha_rpv.get("Status Secundario", "")
    status_ativos = obter_status_simultaneo_ativo(linha_rpv)
    if status_atual == "Cadastro" and perfil_usuario in ["Cadastrador", "Admin"]:
        st.info("Após finalizar o cadastro, este RPV será enviado para os perfis SAC e Administrativo.")
        
        if st.button("✅ Finalizar Cadastro e Enviar", type="primary"):
            idx = df[df["ID"] == rpv_id].index[0]
            
            # Iniciar status simultâneo
            st.session_state.df_editado_rpv = iniciar_status_simultaneo(
                st.session_state.df_editado_rpv,
                rpv_id,
                "SAC - aguardando documentação",
                "Administrativo - aguardando documentação"
            )
            
            # Adicionar data de envio
            now = str(datetime.now().strftime("%d/%m/%Y %H:%M"))
            st.session_state.df_editado_rpv.loc[idx, "Data Envio"] = now
            st.session_state.df_editado_rpv.loc[idx, "Enviado Por"] = str(st.session_state.get("usuario", "Sistema"))
            
            save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
            st.session_state.show_rpv_dialog = False
            st.success("✅ RPV enviado simultaneamente para SAC e Administrativo!")
            st.rerun()
    
    elif (perfil_usuario in ["SAC", "Admin"]) and ("SAC - aguardando documentação" in status_ativos):
        st.info("Marque quando a documentação SAC estiver pronta.")
        
        # Verificar se já está marcado
        sac_doc_pronta = linha_rpv.get("SAC Documentacao Pronta", "") == "Sim"
        
        if not sac_doc_pronta:
            if st.checkbox("✅ Documentação SAC pronta", key=f"sac_doc_{rpv_id}"):
                if st.button("🔄 Marcar SAC como Pronto", type="primary"):
                    idx = df[df["ID"] == rpv_id].index[0]
                    
                    # Atualizar status SAC (sempre no status principal)
                    st.session_state.df_editado_rpv.loc[idx, "Status"] = "SAC - documentação pronta"
                    st.session_state.df_editado_rpv.loc[idx, "SAC Documentacao Pronta"] = "Sim"
                    st.session_state.df_editado_rpv.loc[idx, "Data SAC Documentacao"] = str(datetime.now().strftime("%d/%m/%Y %H:%M"))
                    st.session_state.df_editado_rpv.loc[idx, "SAC Responsavel"] = str(st.session_state.get("usuario", "Sistema"))
                    
                    save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                    st.session_state.show_rpv_dialog = False
                    st.success("✅ Status SAC atualizado!")
                    st.rerun()
        else:
            st.success(f"✅ SAC já marcou documentação como pronta em {linha_rpv.get('Data SAC Documentacao', 'N/A')}")
    elif (perfil_usuario in ["Administrativo", "Admin"]) and ("Administrativo - aguardando documentação" in status_ativos):
        st.info("Marque quando a documentação Administrativa estiver pronta.")
        
        # Verificar se já está marcado
        admin_doc_pronta = linha_rpv.get("Admin Documentacao Pronta", "") == "Sim"
        
        if not admin_doc_pronta:
            if st.checkbox("✅ Documentação Administrativa pronta", key=f"admin_doc_{rpv_id}"):
                if st.button("🔄 Marcar Administrativo como Pronto", type="primary"):
                    idx = df[df["ID"] == rpv_id].index[0]
                    
                    # Atualizar status Administrativo (sempre no status secundário)
                    st.session_state.df_editado_rpv.loc[idx, "Status Secundario"] = "Administrativo - documentação pronta"
                    st.session_state.df_editado_rpv.loc[idx, "Admin Documentacao Pronta"] = "Sim"
                    st.session_state.df_editado_rpv.loc[idx, "Data Admin Documentacao"] = str(datetime.now().strftime("%d/%m/%Y %H:%M"))
                    st.session_state.df_editado_rpv.loc[idx, "Admin Responsavel"] = str(st.session_state.get("usuario", "Sistema"))
                    
                    save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                    st.session_state.show_rpv_dialog = False
                    st.success("✅ Status Administrativo atualizado!")
                    st.rerun()
        else:
            st.success(f"✅ Administrativo já marcou documentação como pronta em {linha_rpv.get('Data Admin Documentacao', 'N/A')}")

    # ADMIN: INTERFACE ESPECIAL PARA STATUS SIMULTÂNEOS (APENAS QUANDO AINDA AGUARDANDO)
    elif (perfil_usuario == "Admin" and len(status_ativos) > 1 and
          ("SAC - aguardando documentação" in status_ativos or "Administrativo - aguardando documentação" in status_ativos)):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📋 SAC:**")
            sac_ativo = "SAC - aguardando documentação" in status_ativos
            sac_pronto = "SAC - documentação pronta" in status_ativos
            sac_doc_pronta = linha_rpv.get("SAC Documentacao Pronta", "") == "Sim"
            
            if sac_ativo and not sac_doc_pronta:
                if st.checkbox("✅ Documentação SAC pronta", key=f"admin_sac_doc_{rpv_id}"):
                    if st.button("🔄 Marcar SAC como Pronto", key=f"admin_sac_btn_{rpv_id}"):
                        idx = df[df["ID"] == rpv_id].index[0]
                        
                        st.session_state.df_editado_rpv.loc[idx, "Status"] = "SAC - documentação pronta"
                        st.session_state.df_editado_rpv.loc[idx, "SAC Documentacao Pronta"] = "Sim"
                        st.session_state.df_editado_rpv.loc[idx, "Data SAC Documentacao"] = str(datetime.now().strftime("%d/%m/%Y %H:%M"))
                        st.session_state.df_editado_rpv.loc[idx, "SAC Responsavel"] = str(st.session_state.get("usuario", "Admin"))
                        
                        save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                        st.rerun()
            elif sac_pronto or sac_doc_pronta:
                st.success("✅ SAC finalizado")
            else:
                st.info("ℹ️ SAC não está ativo")
        
        with col2:
            st.markdown("**🏢 Administrativo:**")
            admin_ativo = "Administrativo - aguardando documentação" in status_ativos
            admin_pronto = "Administrativo - documentação pronta" in status_ativos
            admin_doc_pronta = linha_rpv.get("Admin Documentacao Pronta", "") == "Sim"
            
            if admin_ativo and not admin_doc_pronta:
                if st.checkbox("✅ Documentação Administrativa pronta", key=f"admin_admin_doc_{rpv_id}"):
                    if st.button("🔄 Marcar Administrativo como Pronto", key=f"admin_admin_btn_{rpv_id}"):
                        idx = df[df["ID"] == rpv_id].index[0]
                        
                        st.session_state.df_editado_rpv.loc[idx, "Status Secundario"] = "Administrativo - documentação pronta"
                        st.session_state.df_editado_rpv.loc[idx, "Admin Documentacao Pronta"] = "Sim"
                        st.session_state.df_editado_rpv.loc[idx, "Data Admin Documentacao"] = str(datetime.now().strftime("%d/%m/%Y %H:%M"))
                        st.session_state.df_editado_rpv.loc[idx, "Admin Responsavel"] = str(st.session_state.get("usuario", "Admin"))
                        
                        save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                        st.rerun()
            elif admin_pronto or admin_doc_pronta:
                st.success("✅ Administrativo finalizado")
            else:
                st.info("ℹ️ Administrativo não está ativo")
    
    elif perfil_usuario in ["Financeiro", "Admin"] and status_atual in ["SAC - documentação pronta", "Administrativo - documentação pronta"]:
        # Verificar se ambos SAC e Administrativo finalizaram
        sac_finalizado = linha_rpv.get("SAC Documentacao Pronta", "") == "Sim"
        admin_finalizado = linha_rpv.get("Admin Documentacao Pronta", "") == "Sim"
        
        if sac_finalizado and admin_finalizado:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**📋 SAC:**")
                st.write(f"✅ Finalizado em: {linha_rpv.get('Data SAC Documentacao', 'N/A')}")
                st.write(f"👤 Responsável: {linha_rpv.get('SAC Responsavel', 'N/A')}")
            
            with col2:
                st.markdown("**🏢 Administrativo:**")
                st.write(f"✅ Finalizado em: {linha_rpv.get('Data Admin Documentacao', 'N/A')}")
                st.write(f"👤 Responsável: {linha_rpv.get('Admin Responsavel', 'N/A')}")
            
            if st.checkbox("✅ Validar trabalhos realizados", key=f"validar_{rpv_id}"):
                if st.button("📤 Enviar para Rodrigo", type="primary"):
                    idx = df[df["ID"] == rpv_id].index[0]
                    
                    # Finalizar status simultâneo
                    st.session_state.df_editado_rpv = finalizar_status_simultaneo(
                        st.session_state.df_editado_rpv,
                        rpv_id,
                        "Enviado para Rodrigo"
                    )
                    
                    # Marcar validação
                    st.session_state.df_editado_rpv.loc[idx, "Validado Financeiro"] = "Sim"
                    st.session_state.df_editado_rpv.loc[idx, "Data Validacao"] = str(datetime.now().strftime("%d/%m/%Y %H:%M"))
                    st.session_state.df_editado_rpv.loc[idx, "Validado Por"] = str(st.session_state.get("usuario", "Sistema"))
                    
                    save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                    st.session_state.show_rpv_dialog = False
                    st.success("✅ RPV validado e Enviado para Rodrigo!")
                    st.rerun()
        else:
            # Mostrar status de progresso para Financeiro
            st.markdown("#### 💰 Aguardando Conclusão das Etapas Anteriores")
            
            col1, col2 = st.columns(2)
            with col1:
                if sac_finalizado:
                    st.success("✅ SAC - Documentação pronta")
                else:
                    st.info("SAC - Aguardando documentação")
            
            with col2:
                if admin_finalizado:
                    st.success("✅ Administrativo - Documentação pronta")
                else:
                    st.info("Administrativo - Aguardando documentação")
            
            st.info("Quando ambas as etapas estiverem completas, você poderá validar e enviar para Rodrigo.")
    
    elif status_atual == "Enviado para Rodrigo" and perfil_usuario in ["Financeiro", "Admin"]:
        st.info("Anexe o comprovante de recebimento para prosseguir para o pagamento.")
        
        # Mostrar informações da validação
        if linha_rpv.get("Validado Financeiro") == "Sim":
            st.success(f"✅ Validado pelo financeiro em: {linha_rpv.get('Data Validacao', 'N/A')}")
            st.success(f"👤 Validado por: {linha_rpv.get('Validado Por', 'N/A')}")
        
        # Verificar se já tem comprovante
        comprovante_recebimento = linha_rpv.get("Comprovante Recebimento", "")
        
        if not comprovante_recebimento:
            # Upload do comprovante
            uploaded_file = st.file_uploader(
                "Anexar Comprovante de Recebimento",
                type=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'],
                key=f"comprovante_recebimento_{rpv_id}"
            )
            
            if uploaded_file is not None:
                if st.button("💾 Salvar Comprovante e Prosseguir", type="primary"):
                    idx = df[df["ID"] == rpv_id].index[0]
                    
                    # Salvar arquivo no diretório anexos
                    arquivo_nome = salvar_arquivo_anexo(uploaded_file, rpv_id, "recebimento")
                    
                    if arquivo_nome:
                        # Atualizar status para aguardando pagamento
                        st.session_state.df_editado_rpv.loc[idx, "Status"] = "aguardando pagamento"
                        st.session_state.df_editado_rpv.loc[idx, "Comprovante Recebimento"] = str(arquivo_nome)
                        st.session_state.df_editado_rpv.loc[idx, "Data Recebimento"] = str(datetime.now().strftime("%d/%m/%Y %H:%M"))
                        st.session_state.df_editado_rpv.loc[idx, "Recebido Por"] = str(st.session_state.get("usuario", "Sistema"))
                        
                        save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                        st.session_state.show_rpv_dialog = False
                        st.success("✅ Comprovante salvo! RPV agora está aguardando pagamento.")
                        st.rerun()
        else:
            st.success(f"✅ Comprovante de recebimento anexado: {comprovante_recebimento}")
            st.info(f"📅 Recebido em: {linha_rpv.get('Data Recebimento', 'N/A')}")
            st.info(f"👤 Por: {linha_rpv.get('Recebido Por', 'N/A')}")
            
            # Botão para avançar manualmente caso o comprovante já esteja anexado
            if st.button("➡️ Prosseguir para Aguardando Pagamento", type="primary"):
                idx = df[df["ID"] == rpv_id].index[0]
                st.session_state.df_editado_rpv.loc[idx, "Status"] = "aguardando pagamento"
                save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                st.session_state.show_rpv_dialog = False
                st.success("✅ RPV avançado para aguardando pagamento!")
                st.rerun()
    
    elif status_atual == "aguardando pagamento" and perfil_usuario in ["Financeiro", "Admin"]:
        st.info("Anexe o comprovante de pagamento para finalizar o RPV.")
        
        # Mostrar info do recebimento
        st.success(f"✅ Recebimento confirmado em: {linha_rpv.get('Data Recebimento', 'N/A')}")
        
        # Verificar se já tem comprovante de pagamento
        comprovante_pagamento = linha_rpv.get("Comprovante Pagamento", "")
        
        if not comprovante_pagamento:
            # Upload do comprovante de pagamento
            uploaded_file = st.file_uploader(
                "Anexar Comprovante de Pagamento",
                type=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'],
                key=f"comprovante_pagamento_{rpv_id}"
            )
            
            if uploaded_file is not None:
                if st.button("💾 Salvar Comprovante e Finalizar RPV", type="primary"):
                    idx = df[df["ID"] == rpv_id].index[0]
                    
                    # Salvar arquivo no diretório anexos
                    arquivo_nome = salvar_arquivo_anexo(uploaded_file, rpv_id, "pagamento")
                    
                    if arquivo_nome:
                        # Finalizar RPV
                        st.session_state.df_editado_rpv.loc[idx, "Status"] = "finalizado"
                        st.session_state.df_editado_rpv.loc[idx, "Comprovante Pagamento"] = str(arquivo_nome)
                        st.session_state.df_editado_rpv.loc[idx, "Data Pagamento"] = str(datetime.now().strftime("%d/%m/%Y %H:%M"))
                        st.session_state.df_editado_rpv.loc[idx, "Pago Por"] = str(st.session_state.get("usuario", "Sistema"))
                        st.session_state.df_editado_rpv.loc[idx, "Data Finalizacao"] = str(datetime.now().strftime("%d/%m/%Y %H:%M"))
                        
                        save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                        st.session_state.show_rpv_dialog = False
                        st.success("🎉 RPV finalizado com sucesso!")
                        st.balloons()
                        st.rerun()
        else:
            st.success(f"✅ Comprovante de pagamento anexado: {comprovante_pagamento}")
            st.info(f"📅 Pago em: {linha_rpv.get('Data Pagamento', 'N/A')}")
            st.info(f"👤 Por: {linha_rpv.get('Pago Por', 'N/A')}")
    
    elif status_atual == "finalizado":
        st.markdown("### Timeline do Processo:")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**📝 Cadastro:**")
            st.write(f"📅 Enviado: {linha_rpv.get('Data Envio', 'N/A')}")
            st.write(f"👤 Por: {linha_rpv.get('Enviado Por', 'N/A')}")
            
            st.markdown("**📋 SAC:**")
            st.write(f"📅 Finalizado: {linha_rpv.get('Data SAC Documentacao', 'N/A')}")
            st.write(f"👤 Por: {linha_rpv.get('SAC Responsavel', 'N/A')}")
            
            st.markdown("**💰 Validação:**")
            st.write(f"📅 Validado: {linha_rpv.get('Data Validacao', 'N/A')}")
            st.write(f"👤 Por: {linha_rpv.get('Validado Por', 'N/A')}")
        
        with col2:
            st.markdown("**🏢 Administrativo:**")
            st.write(f"📅 Finalizado: {linha_rpv.get('Data Admin Documentacao', 'N/A')}")
            st.write(f"👤 Por: {linha_rpv.get('Admin Responsavel', 'N/A')}")
            
            st.markdown("**📨 Recebimento:**")
            st.write(f"📅 Recebido: {linha_rpv.get('Data Recebimento', 'N/A')}")
            st.write(f"👤 Por: {linha_rpv.get('Recebido Por', 'N/A')}")
            
            st.markdown("**💳 Pagamento:**")
            st.write(f"📅 Pago: {linha_rpv.get('Data Pagamento', 'N/A')}")
            st.write(f"👤 Por: {linha_rpv.get('Pago Por', 'N/A')}")
        
        # Mostrar comprovantes com botões de download
        st.markdown("### Comprovantes Anexados:")
        
        col_comp1, col_comp2 = st.columns(2)
        
        with col_comp1:
            comprovante_recebimento = linha_rpv.get("Comprovante Recebimento", "")
            if comprovante_recebimento:
                st.markdown("**� Comprovante de Recebimento:**")
                st.info(f"📄 {comprovante_recebimento}")
                
                # Botão de download
                caminho_arquivo_rec = os.path.join("anexos", comprovante_recebimento)
                if os.path.exists(caminho_arquivo_rec):
                    with open(caminho_arquivo_rec, "rb") as file:
                        btn_rec = st.download_button(
                            label="📥 Baixar Comprovante de Recebimento",
                            data=file.read(),
                            file_name=comprovante_recebimento,
                            mime="application/octet-stream",
                            key=f"download_rec_{rpv_id}"
                        )
                else:
                    st.warning("⚠️ Arquivo não encontrado no diretório anexos")
            else:
                st.info("📨 Nenhum comprovante de recebimento anexado")
        
        with col_comp2:
            comprovante_pagamento = linha_rpv.get("Comprovante Pagamento", "")
            if comprovante_pagamento:
                st.markdown("**� Comprovante de Pagamento:**")
                st.info(f"📄 {comprovante_pagamento}")
                
                # Botão de download
                caminho_arquivo_pag = os.path.join("anexos", comprovante_pagamento)
                if os.path.exists(caminho_arquivo_pag):
                    with open(caminho_arquivo_pag, "rb") as file:
                        btn_pag = st.download_button(
                            label="📥 Baixar Comprovante de Pagamento",
                            data=file.read(),
                            file_name=comprovante_pagamento,
                            mime="application/octet-stream",
                            key=f"download_pag_{rpv_id}"
                        )
                else:
                    st.warning("⚠️ Arquivo não encontrado no diretório anexos")
            else:
                st.info("💳 Nenhum comprovante de pagamento anexado")
        
        st.markdown("---")
        st.markdown(f"🏁 **Finalizado em:** {linha_rpv.get('Data Finalizacao', 'N/A')}")
    
    # SEÇÃO DE HONORÁRIOS CONTRATUAIS - Disponível para Financeiro e Admin
    if perfil_usuario in ["Financeiro", "Admin"]:
        st.markdown("---")
        st.markdown("### 💼 Honorários Contratuais")
        
        with st.form(f"form_hc_rpv_{rpv_id}"):
            col_hc1, col_hc2 = st.columns(2)
            
            with col_hc1:
                honorarios_contratuais = st.number_input(
                    "Honorário Contratual 1:",
                    min_value=0.0,
                    value=safe_get_hc_value_rpv(linha_rpv, "Honorarios Contratuais"),
                    step=0.01,
                    format="%.2f",
                    help="Valor principal dos honorários contratuais",
                    key=f"hc_rpv_{rpv_id}"
                )
                
                # Campos HC adicionais (aparecem conforme o nível do botão)
                hc1_valor, hc2_valor = 0.0, 0.0
                nivel_hc = st.session_state.get(f"hc_nivel_rpv_{rpv_id}", 0)
                
                if nivel_hc >= 1:  # Primeira pressão: Mostrar HC2
                    hc1_valor = st.number_input(
                        "Honorário Contratual 2:",
                        min_value=0.0,
                        value=safe_get_hc_value_rpv(linha_rpv, "HC1"),
                        step=0.01,
                        format="%.2f",
                        key=f"hc1_rpv_{rpv_id}"
                    )
                
                if nivel_hc >= 2:  # Segunda pressão: Mostrar HC3
                    hc2_valor = st.number_input(
                        "Honorário Contratual 3:",
                        min_value=0.0,
                        value=safe_get_hc_value_rpv(linha_rpv, "HC2"),
                        step=0.01,
                        format="%.2f",
                        key=f"hc2_rpv_{rpv_id}"
                    )
            
            with col_hc2:
                # Mostrar total atual
                total_atual = calcular_total_hc_rpv(linha_rpv)
                st.metric("Total HC Atual", f"R$ {total_atual:.2f}")
                
                # Botão para expandir HCs
                expand_hc = st.form_submit_button("➕ Adicionar Honorários Contratuais", help="Clique para adicionar Honorários Contratuais, HC3...")
                if expand_hc:
                    nivel_atual = st.session_state.get(f"hc_nivel_rpv_{rpv_id}", 0)
                    st.session_state[f"hc_nivel_rpv_{rpv_id}"] = min(nivel_atual + 1, 2)
                    st.rerun()
                
                # Mostrar detalhamento se há HCs adicionais
                if nivel_hc > 0:
                    st.markdown("**Detalhamento:**")
                    hc_principal = safe_get_hc_value_rpv(linha_rpv, "Honorarios Contratuais")
                    st.write(f"HC1: R$ {hc_principal:.2f}")
                    if nivel_hc >= 1:
                        hc1_atual = safe_get_hc_value_rpv(linha_rpv, "HC1")
                        st.write(f"HC2: R$ {hc1_atual:.2f}")
                    if nivel_hc >= 2:
                        hc2_atual = safe_get_hc_value_rpv(linha_rpv, "HC2")
                        st.write(f"HC3: R$ {hc2_atual:.2f}")
            
            # Botão para salvar honorários
            salvar_hc = st.form_submit_button("💾 Salvar Honorários Contratuais", type="primary")
            
            if salvar_hc:
                try:
                    idx = df[df["ID"] == rpv_id].index[0]
                    
                    # Salvar valores
                    st.session_state.df_editado_rpv.loc[idx, "Honorarios Contratuais"] = honorarios_contratuais
                    
                    # Salvar HCs adicionais se foram preenchidos
                    if nivel_hc >= 1:
                        st.session_state.df_editado_rpv.loc[idx, "HC1"] = hc1_valor
                    if nivel_hc >= 2:
                        st.session_state.df_editado_rpv.loc[idx, "HC2"] = hc2_valor
                    
                    # Salvar no GitHub
                    save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                    
                    total_novo = honorarios_contratuais + hc1_valor + hc2_valor
                    st.success(f"✅ Honorários salvos! Total: R$ {total_novo:.2f}")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erro ao salvar honorários: {str(e)}")
    
    # OUTROS PERFIS E STATUS - VISUALIZAÇÃO APENAS
    else:
        # Mostrar status de forma informativa
        if len(status_ativos) > 1:
            status_info = []
            for status in status_ativos:
                if status in ["SAC - documentação pronta", "Administrativo - documentação pronta"]:
                    status_info.append(f"✅ {status}")
                else:
                    status_info.append(f"{status}")
            st.info(f"Status: {' + '.join(status_info)}")
        else:
            st.info(f"Status Atual: {status_atual}")

def interface_visualizar_dados_rpv(df):
    """Interface melhorada para visualizar dados de RPVs em formato de tabela limpa."""
    
    # LIMPAR ESTADOS DE DIÁLOGO ao entrar na aba de visualização
    if st.session_state.get("show_rpv_dialog", False):
        st.session_state.show_rpv_dialog = False
    if st.session_state.get("rpv_aberto_id") is not None:
        st.session_state.rpv_aberto_id = None
    
    if df.empty:
        st.info("ℹ️ Não há RPVs para visualizar.")
        return

    # Cards de estatísticas compactos
    total_rpvs = len(df)
    finalizados = len(df[df["Status"] == "finalizado"]) if "Status" in df.columns else 0
    pendentes = total_rpvs - finalizados
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 15px; border-radius: 8px; text-align: center; color: white; margin-bottom: 10px;">
            <h3 style="margin: 0; font-size: 1.8em;">{}</h3>
            <p style="margin: 3px 0 0 0; font-size: 0.9em;">Total de RPVs</p>
        </div>
        """.format(total_rpvs), unsafe_allow_html=True)
    
    with col2:
        taxa_finalizados = (finalizados/total_rpvs*100) if total_rpvs > 0 else 0
        st.markdown("""
        <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 15px; border-radius: 8px; text-align: center; color: white; margin-bottom: 10px;">
            <h3 style="margin: 0; font-size: 1.8em;">{}</h3>
            <p style="margin: 3px 0 0 0; font-size: 0.9em;">Finalizados ({:.1f}%)</p>
        </div>
        """.format(finalizados, taxa_finalizados), unsafe_allow_html=True)
    
    with col3:
        taxa_pendentes = (pendentes/total_rpvs*100) if total_rpvs > 0 else 0
        st.markdown("""
        <div style="background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); padding: 15px; border-radius: 8px; text-align: center; color: #8B4513; margin-bottom: 10px;">
            <h3 style="margin: 0; font-size: 1.8em;">{}</h3>
            <p style="margin: 3px 0 0 0; font-size: 0.9em;">Em Andamento ({:.1f}%)</p>
        </div>
        """.format(pendentes, taxa_pendentes), unsafe_allow_html=True)
    
    with col4:
        if "Data Cadastro" in df.columns:
            hoje = datetime.now().strftime("%d/%m/%Y")
            df_temp = df.copy()
            df_temp["Data Cadastro"] = df_temp["Data Cadastro"].astype(str)
            hoje_count = len(df_temp[df_temp["Data Cadastro"].str.contains(hoje, na=False)])
        else:
            hoje_count = 0
            
        st.markdown("""
        <div style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); padding: 15px; border-radius: 8px; text-align: center; color: #2c3e50; margin-bottom: 10px;">
            <h3 style="margin: 0; font-size: 1.8em;">{}</h3>
            <p style="margin: 3px 0 0 0; font-size: 0.9em;">Cadastrados Hoje</p>
        </div>
        """.format(hoje_count), unsafe_allow_html=True)

    st.markdown("---")

    col_filtro1, col_filtro2, col_filtro3, col_filtro4 = st.columns(4)
    
    with col_filtro1:
        status_unicos = ["Todos"] + list(df["Status"].dropna().unique()) if "Status" in df.columns else ["Todos"]
        status_filtro = st.selectbox("Status:", options=status_unicos, key="viz_rpv_status")
        
    with col_filtro2:
        usuarios_unicos = ["Todos"] + list(df["Cadastrado Por"].dropna().unique()) if "Cadastrado Por" in df.columns else ["Todos"]
        usuario_filtro = st.selectbox("Cadastrado Por:", options=usuarios_unicos, key="viz_rpv_user")
    
    with col_filtro3:
        assuntos_unicos = ["Todos"] + list(df["Assunto"].dropna().unique()) if "Assunto" in df.columns else ["Todos"]
        assunto_filtro = st.selectbox("Assunto:", options=assuntos_unicos, key="viz_rpv_assunto")
    
    with col_filtro4:
        pesquisa = st.text_input("🔎 Pesquisar por Beneficiário ou Processo:", key="viz_rpv_search")

    # Aplicar filtros
    df_visualizado = df.copy()
    if status_filtro != "Todos" and "Status" in df.columns:
        df_visualizado = df_visualizado[df_visualizado["Status"] == status_filtro]
    if usuario_filtro != "Todos" and "Cadastrado Por" in df.columns:
        df_visualizado = df_visualizado[df_visualizado["Cadastrado Por"] == usuario_filtro]
    if assunto_filtro != "Todos" and "Assunto" in df.columns:
        df_visualizado = df_visualizado[df_visualizado["Assunto"] == assunto_filtro]
    if pesquisa:
        df_visualizado = df_visualizado[
            df_visualizado["Beneficiário"].astype(str).str.contains(pesquisa, case=False, na=False) |
            df_visualizado["Processo"].astype(str).str.contains(pesquisa, case=False, na=False)
        ]
    
    st.markdown("---")

    # Botões de download
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

    # Exibição em formato de tabela organizada igual ao "Gerenciar Processos"
    st.markdown(f"### 📋 Lista de RPVs ({len(df_visualizado)} registros)")
    
    if not df_visualizado.empty:
        # Lógica de Paginação
        if "current_page_visualizar_rpv" not in st.session_state:
            st.session_state.current_page_visualizar_rpv = 1
        
        items_per_page = 20  # Aumentando para 20 como nas outras telas
        total_registros = len(df_visualizado)
        total_pages = math.ceil(total_registros / items_per_page) if items_per_page > 0 else 1
        
        if st.session_state.current_page_visualizar_rpv > total_pages:
            st.session_state.current_page_visualizar_rpv = 1
        
        start_idx = (st.session_state.current_page_visualizar_rpv - 1) * items_per_page
        end_idx = start_idx + items_per_page
        df_paginado = df_visualizado.iloc[start_idx:end_idx]
        
        st.markdown(f'<p style="font-size: small; color: steelblue;">Mostrando {start_idx+1} a {min(end_idx, total_registros)} de {total_registros} registros</p>', unsafe_allow_html=True)
        
        # Cabeçalhos da tabela organizada
        col_h1, col_h2, col_h3, col_h4, col_h5, col_h6 = st.columns([2.5, 2, 2, 1.5, 1.5, 1.5])
        with col_h1: st.markdown("**Beneficiário**")
        with col_h2: st.markdown("**Processo**")
        with col_h3: st.markdown("**Assunto**")
        with col_h4: st.markdown("**Status**")
        with col_h5: st.markdown("**Data Cadastro**")
        with col_h6: st.markdown("**Cadastrado Por**")
        
        st.markdown('<hr style="margin-top: 0.1rem; margin-bottom: 0.5rem;" />', unsafe_allow_html=True)

        # Linhas da tabela
        for _, row in df_paginado.iterrows():
            col_b1, col_b2, col_b3, col_b4, col_b5, col_b6 = st.columns([2.5, 2, 2, 1.5, 1.5, 1.5])
            
            with col_b1:
                beneficiario = str(row.get('Beneficiário', 'N/A'))
                st.write(f"**{beneficiario[:30]}{'...' if len(beneficiario) > 30 else ''}**")
            with col_b2:
                processo = str(row.get('Processo', 'N/A'))
                st.write(processo[:20] + ('...' if len(processo) > 20 else ''))
            with col_b3:
                assunto = str(row.get('Assunto', 'N/A'))
                st.write(assunto[:15] + ('...' if len(assunto) > 15 else ''))
            with col_b4:
                status = row.get('Status', 'N/A')
                status_secundario = row.get('Status Secundario', '')
                
                # Colorir status principal
                if status == "finalizado":
                    st.markdown(f'<span style="color: green; font-weight: bold;">✅ {status}</span>', unsafe_allow_html=True)
                elif status == "Cadastro":
                    st.markdown(f'<span style="color: blue; font-weight: bold;">🔵 {status}</span>', unsafe_allow_html=True)
                elif "aguardando" in str(status).lower():
                    st.markdown(f'<span style="color: orange; font-weight: bold;">� {status}</span>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<span style="color: purple; font-weight: bold;">� {status}</span>', unsafe_allow_html=True)
                    
                # Mostrar status secundário se existir - converter para string segura
                status_sec_str = str(status_secundario) if status_secundario is not None else ""
                if status_sec_str and status_sec_str.strip() != "" and status_sec_str.lower() not in ['nan', 'none']:
                    st.markdown(f'<span style="color: orange; font-size: 12px;">+ {status_sec_str}</span>', unsafe_allow_html=True)
            with col_b5:
                data_cadastro = row.get('Data Cadastro')
                if pd.isna(data_cadastro):
                    st.write("N/A")
                else:
                    st.write(str(data_cadastro).split(' ')[0])
            with col_b6:
                st.write(str(row.get('Cadastrado Por', 'N/A'))[:10] + ('...' if len(str(row.get('Cadastrado Por', 'N/A'))) > 10 else ''))

        # Controles de paginação
        if total_pages > 1:
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
        st.info("📭 Nenhum registro encontrado com os filtros aplicados.")

def interface_cadastro_rpv(df, perfil_usuario):
    """Interface para cadastrar novos RPVs"""
    
    # LIMPAR ESTADOS DE DIÁLOGO ao entrar na aba de cadastro
    if st.session_state.get("show_rpv_dialog", False):
        st.session_state.show_rpv_dialog = False
    if st.session_state.get("rpv_aberto_id") is not None:
        st.session_state.rpv_aberto_id = None
    
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

    col1, col2 = st.columns(2)
    
    processo_key = "new_rpv_processo"
    beneficiario_key = "new_rpv_beneficiario"
    cpf_key = "new_rpv_cpf"
    certidao_key = "new_rpv_certidao"
    valor_key = "new_rpv_valor"
    obs_key = "new_rpv_observacoes"
    multiplos_key = "new_rpv_multiplos"
    competencia_key = "new_rpv_competencia"
    
    with col1:
        processo = st.text_input("Número do Processo: *", key=processo_key)
        beneficiario = st.text_input("Beneficiário: *", key=beneficiario_key)
        cpf = st.text_input("CPF: *", key=cpf_key)
        
        # Campo Assunto com nova interface
        assunto_selecionado = campo_assunto_rpv(
            label="Assunto: *",
            key_prefix="new_rpv_assunto"
        )
        
        # Converter para formato compatível
        assunto_final = assunto_selecionado if assunto_selecionado else ""
        
        # Campo Órgão Judicial com nova interface
        orgao_selecionado = campo_orgao_rpv(
            label="Órgão Judicial: *",
            key_prefix="new_rpv_orgao"
        )
        
        # Converter para formato compatível
        orgao_final = orgao_selecionado if orgao_selecionado else ""
        
        solicitar_certidao = st.selectbox(
            "Solicitar Certidão? *",
            options=["Sim", "Não"],
            key=certidao_key
        )
        
        # Campo Banco
        banco_rpv = st.selectbox(
            "Banco: *",
            options=["CEF", "BB"],
            key="new_rpv_banco"
        )
        
        # Novo campo: Mês de Competência
        mes_competencia_raw = st.text_input(
            "Mês de Competência: *",
            value="",
            help="Digite no formato mm/yyyy (ex: 12/2024)",
            placeholder="mm/yyyy",
            max_chars=7,
            key=competencia_key
        )
        
        # Processar e validar formato mm/yyyy
        mes_competencia = None
        if mes_competencia_raw:
            # Remover espaços e garantir formato
            mes_competencia_limpo = mes_competencia_raw.strip()
            # Verificar se tem o formato básico mm/yyyy
            if len(mes_competencia_limpo) == 7 and mes_competencia_limpo[2] == '/':
                try:
                    mes, ano = mes_competencia_limpo.split('/')
                    if len(mes) == 2 and len(ano) == 4 and mes.isdigit() and ano.isdigit():
                        mes_int = int(mes)
                        ano_int = int(ano)
                        if 1 <= mes_int <= 12 and 2020 <= ano_int <= 2030:
                            mes_competencia = mes_competencia_limpo
                        else:
                            st.warning("⚠️ Mês deve ser entre 01-12 e ano entre 2020-2030")
                    else:
                        st.warning("⚠️ Use apenas números no formato mm/yyyy")
                except:
                    st.warning("⚠️ Formato inválido. Use mm/yyyy (ex: 12/2024)")
            elif mes_competencia_limpo:
                st.warning("⚠️ Formato deve ser mm/yyyy (ex: 12/2024)")
    
    with col2:
        valor_rpv = st.text_input("Valor da RPV (R$): *", key=valor_key)
        observacoes = st.text_area("Observações:", height=125, key=obs_key)
        
        # Checkbox para anexar múltiplos PDFs
        anexar_multiplos_pdf = st.checkbox("Anexar múltiplos PDFs", key=multiplos_key)
        
        # Usar keys diferentes para múltiplos vs único para evitar conflitos
        if anexar_multiplos_pdf:
            pdf_rpv = st.file_uploader(
                "PDFs do RPV: *",
                type=["pdf"],
                accept_multiple_files=True,
                key="pdf_rpv_multiplos"
            )
        else:
            pdf_rpv = st.file_uploader(
                "PDF do RPV: *",
                type=["pdf"],
                key="pdf_rpv_unico"
            )

    # Botão de submissão fora do formulário
    if st.button("📝 Adicionar Linha", type="primary", use_container_width=True):
        # Primeiro, processar e salvar permanentemente novos valores de autocomplete
        
        # Processar assunto
        if assunto_selecionado and len(assunto_selecionado) > 0:
            assunto_processado = normalizar_assunto_rpv(assunto_selecionado)
            assuntos_existentes = obter_assuntos_rpv()
            if assunto_processado and assunto_processado not in assuntos_existentes:
                if adicionar_assunto_rpv(assunto_processado):
                    st.success(f"🆕 Novo assunto '{assunto_processado}' salvo permanentemente!")
            assunto_final = assunto_processado
        
        # Processar órgão
        if orgao_selecionado and len(orgao_selecionado) > 0:
            orgao_processado = normalizar_orgao_rpv(orgao_selecionado)
            orgaos_existentes = obter_orgaos_rpv()
            if orgao_processado and orgao_processado not in orgaos_existentes:
                if adicionar_orgao_rpv(orgao_processado):
                    st.success(f"🆕 Novo órgão '{orgao_processado}' salvo permanentemente!")
            orgao_final = orgao_processado
        
        # =====================================
        # VALIDAÇÃO COMPLETA DE CAMPOS OBRIGATÓRIOS
        # =====================================
        
        campos_vazios = []
        
        # Validar campos de texto obrigatórios
        if not processo or processo.strip() == "":
            campos_vazios.append("Número do Processo")
        if not beneficiario or beneficiario.strip() == "":
            campos_vazios.append("Beneficiário")
        if not cpf or cpf.strip() == "":
            campos_vazios.append("CPF")
        if not valor_rpv or valor_rpv.strip() == "":
            campos_vazios.append("Valor da RPV")
        if not assunto_final or assunto_final.strip() == "":
            campos_vazios.append("Assunto")
        if not orgao_final or orgao_final.strip() == "":
            campos_vazios.append("Órgão Judicial")
        
        # Validar banco (já vem selecionado por padrão, mas verificar)
        if "new_rpv_banco" not in st.session_state or not st.session_state.new_rpv_banco:
            campos_vazios.append("Banco")
        else:
            banco_rpv = st.session_state.new_rpv_banco
        
        # Validar mês de competência
        if not mes_competencia:
            campos_vazios.append("Mês de Competência")
        
        # Validar solicitar certidão (já vem selecionado por padrão, mas verificar)
        if not solicitar_certidao:
            campos_vazios.append("Solicitar Certidão")
        
        # Validar PDF(s)
        pdf_valido = False
        if anexar_multiplos_pdf:
            if pdf_rpv and len(pdf_rpv) > 0:
                pdf_valido = True
            else:
                campos_vazios.append("PDFs do RPV")
        else:
            if pdf_rpv is not None:
                pdf_valido = True
            else:
                campos_vazios.append("PDF do RPV")
        
        # Se há campos vazios, exibir erro detalhado
        if campos_vazios:
            if len(campos_vazios) == 1:
                st.error(f"❌ O campo obrigatório **{campos_vazios[0]}** deve ser preenchido.")
            else:
                campos_texto = ", ".join(campos_vazios[:-1]) + " e " + campos_vazios[-1]
                st.error(f"❌ Os seguintes campos obrigatórios devem ser preenchidos: **{campos_texto}**.")
        # Validações adicionais de formato
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
                # NOVO FLUXO: Status inicial é Cadastro, que depois se transforma nos dois status simultâneos
                status_inicial = "Cadastro"

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
                    "Banco": banco_rpv,
                    "Assunto": assunto_final,
                    "Orgao Judicial": orgao_final,
                    "Mês Competência": mes_competencia.strftime("%d/%m/%Y") if mes_competencia else "",
                    "Observações": observacoes,
                    "Solicitar Certidão": solicitar_certidao,
                    "Status": status_inicial,
                    "Status Secundario": "",  # Novo campo para status simultâneo
                    "Data Cadastro": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Cadastrado Por": st.session_state.get("usuario", "Sistema"),
                    "PDF RPV": pdf_url,
                    # Adicionar os novos campos de controle do novo fluxo
                    "SAC Documentacao Pronta": "Não",
                    "Data SAC Documentacao": "",
                    "SAC Responsavel": "",
                    "Admin Documentacao Pronta": "Não",
                    "Data Admin Documentacao": "",
                    "Admin Responsavel": "",
                    "Validado Financeiro": "Não",
                    "Data Validacao": "",
                    "Validado Por": "",
                    "Comprovante Recebimento": "",
                    "Data Comprovante Recebimento": "",
                    "Recebimento Por": ""
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
                for key in [processo_key, beneficiario_key, cpf_key, valor_key, obs_key, competencia_key,
                           certidao_key, multiplos_key, "new_rpv_banco",
                           "select_new_rpv_assunto", "input_novo_new_rpv_assunto",
                           "select_new_rpv_orgao", "input_novo_new_rpv_orgao",
                           "pdf_rpv_unico", "pdf_rpv_multiplos"]:
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
        
        # Converter IDs para string para garantir comparação correta
        processos_selecionados_str = [str(pid) for pid in processos_selecionados]
        processos_para_excluir = df[df["ID"].astype(str).isin(processos_selecionados_str)]
        
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
                
                # Converter IDs para o mesmo tipo para garantir comparação
                processos_selecionados_str = [str(pid) for pid in processos_selecionados]
                
                # Remover processos do DataFrame
                st.session_state.df_editado_rpv = st.session_state.df_editado_rpv[
                    ~st.session_state.df_editado_rpv["ID"].astype(str).isin(processos_selecionados_str)
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
