import streamlit as st
import pandas as pd
import math
import re
import os
import time
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode
from components.autocomplete_manager import (
    inicializar_autocomplete_session,
    adicionar_assunto_rpv,
    adicionar_orgao_rpv,
    adicionar_vara_rpv,
    campo_orgao_rpv,
    campo_assunto_rpv,
    campo_vara_rpv,
    carregar_dados_autocomplete,
    normalizar_vara_rpv,
    obter_varas_rpv,
    obter_orgaos_rpv
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
    limpar_campos_formulario,
    
    # Função de cores de status
    obter_cor_status
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

def gerar_timestamp_unico():
    """Gera um timestamp único de 4 dígitos para usar em chaves de componentes"""
    return int(time.time() * 1000) % 10000

def limpar_estados_dialog_rpv():
    """Limpa estados de diálogo e cards expandidos para RPV"""
    if st.session_state.get("show_rpv_dialog", False):
        st.session_state.show_rpv_dialog = False
    if st.session_state.get("rpv_aberto_id") is not None:
        st.session_state.rpv_aberto_id = None

def aplicar_css_cards_rpv():
    """Aplica CSS padrão para cards RPV"""
    st.markdown("""
    <style>
    .rpv-card {
        border: 1px solid #e0e6ed;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        background-color: transparent;
        transition: all 0.3s ease;
    }
    .rpv-card:hover {
        border-color: #0066cc;
        box-shadow: 0 2px 8px rgba(0,102,204,0.15);
    }
    .rpv-card.expanded {
        background-color: transparent;
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

def validar_campos_obrigatorios_rpv(campos):
    """
    Valida campos obrigatórios para RPV
    
    Args:
        campos (dict): Dicionário com os campos a serem validados
        
    Returns:
        list: Lista de campos vazios encontrados
    """
    campos_vazios = []
    
    # Definir campos obrigatórios e suas labels amigáveis
    campos_obrigatorios = {
        'processo': 'Número do Processo',
        'beneficiario': 'Beneficiário', 
        'cpf': 'CPF',
        'assunto': 'Assunto',
        'orgao_judicial': 'Órgão Judicial',
        'banco': 'Banco',
        'mes_competencia': 'Mês de Competência',
        'solicitar_certidao': 'Solicitar Certidão'
    }
    
    for campo_key, campo_label in campos_obrigatorios.items():
        valor = campos.get(campo_key)
        if not valor or str(valor).strip() == "":
            campos_vazios.append(campo_label)
    
    return campos_vazios

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
        "HC2",
        "Descricao RPV",  # Nova coluna para múltiplos RPVs
        "Observacoes Honorarios Contratuais",  # Nova coluna para observações HC
        "Valor Saque",  # Nova coluna para valor do saque
        "H Sucumbenciais",  # Nova coluna para honorários sucumbenciais
        "Valor Parceiro Prospector",  # Nova coluna para valor de parceiro/prospector
        "Outros Valores",  # Nova coluna para outros valores
        "Observacoes Gerais",  # Nova coluna para observações gerais
        "Forma Pagamento"  # Nova coluna para forma de pagamento
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
        "Assunto", "Vara", "Solicitar Certidão", "Status", "Status Secundario", "Data Cadastro", "Cadastrado Por",
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

def confirmar_exclusao_massa_rpv(df, processos_selecionados):
    """Função para confirmar exclusão em massa de RPVs"""
    
    @st.dialog("🗑️ Confirmar Exclusão em Massa", width="large")
    def dialog_confirmacao():
        st.error("⚠️ **ATENÇÃO:** Esta ação não pode ser desfeita!")
        
        # Mostrar processos que serão excluídos
        st.markdown(f"### Você está prestes a excluir **{len(processos_selecionados)}** RPV(s):")
        
        # Converter IDs para string para garantir comparação correta
        processos_selecionados_str = [str(pid) for pid in processos_selecionados]
        processos_para_excluir = df[df["ID"].astype(str).isin(processos_selecionados_str)]
        
        for _, processo in processos_para_excluir.iterrows():
            processo_num = safe_get_value(processo, 'Processo', 'N/A')
            beneficiario = safe_get_value(processo, 'Beneficiário', 'N/A')
            st.markdown(f"- **{processo_num}** - {beneficiario}")
        
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
                        id_processo=processo.get('ID', 'N/A'),
                        tipo_processo="RPV",
                        processo=safe_get_value(processo, 'Processo', 'N/A'),
                        beneficiario=safe_get_value(processo, 'Beneficiário', 'N/A'),
                        status=safe_get_value(processo, 'Status', 'N/A'),
                        usuario=usuario_atual
                    )
                
                # Converter IDs para o mesmo tipo para garantir comparação
                processos_selecionados_str = [str(pid) for pid in processos_selecionados]
                
                # Remover processos do DataFrame
                st.session_state.df_editado_rpv = st.session_state.df_editado_rpv[
                    ~st.session_state.df_editado_rpv["ID"].astype(str).isin(processos_selecionados_str)
                ].reset_index(drop=True)
                
                # Salvar arquivo
                salvar_arquivo(st.session_state.df_editado_rpv, "lista_rpv.csv")
                
                # Limpar seleções
                st.session_state.modo_exclusao_rpv = False
                st.session_state.processos_selecionados_rpv = []
                
                st.success(f"✅ {len(processos_selecionados)} RPV(s) excluído(s) com sucesso!")
                st.rerun()
        
        with col_canc:
            if st.button("❌ Cancelar", use_container_width=True):
                st.rerun()
    
    # Executar o diálogo
    dialog_confirmacao()

def interface_lista_rpv(df, perfil_usuario):
    """Interface principal para listar RPVs com sistema de dropdown"""
    
    # LIMPAR ESTADOS DE DIÁLOGO ao entrar na aba de lista
    limpar_estados_dialog_rpv()
    
    # Inicializar estado dos cards expandidos - GARANTIR que seja um set
    if "rpv_expanded_cards" not in st.session_state:
        st.session_state.rpv_expanded_cards = set()
    elif not isinstance(st.session_state.rpv_expanded_cards, set):
        # Converter para set se não for (por segurança)
        st.session_state.rpv_expanded_cards = set(st.session_state.rpv_expanded_cards)
    
    # Remover conversão automática para evitar problemas de comparação
    # st.session_state.rpv_expanded_cards = {str(id_) for id_ in st.session_state.rpv_expanded_cards}
    
    if df.empty:
        st.info("ℹ️ Não há RPVs cadastrados ainda. Use a aba 'Cadastrar RPV' para adicionar o primeiro registro.")
        return

    # Filtros
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
        # Auto-filtro com rerun automático
        def on_rpv_search_change():
            """Função chamada quando o texto de busca muda"""
            pass  # O rerun é automático com key no session_state
            
        pesquisa = st.text_input(
            "🔎 Pesquisar por Beneficiário ou Processo:", 
            key="lista_rpv_search", 
            placeholder="Digite para filtrar",
            on_change=on_rpv_search_change
        )
        
        # Usar session_state para o valor do filtro
        if "lista_rpv_search" in st.session_state:
            pesquisa = st.session_state.lista_rpv_search
            
        if pesquisa:
            st.caption(f"🔍 Buscando por: '{pesquisa}' ({len(pesquisa)} caracteres)")

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
    
    # Mostrar resultado da busca
    if pesquisa:
        st.success(f"🔍 {total_registros_filtrados} resultado(s) encontrado(s) para '{pesquisa}'")
    elif total_registros_filtrados < len(df):
        st.info(f"📊 {total_registros_filtrados} de {len(df)} registros (filtros aplicados)")

    # Botões de exclusão em massa
    usuario_atual = st.session_state.get("usuario", "")
    perfil_atual = st.session_state.get("perfil_usuario", "")
    pode_excluir = (perfil_atual in ["Admin", "Cadastrador"] or usuario_atual == "admin")
    
    # Inicializar variáveis de estado se não existirem
    if "modo_exclusao_rpv" not in st.session_state:
        st.session_state.modo_exclusao_rpv = False
    if "processos_selecionados_rpv" not in st.session_state:
        st.session_state.processos_selecionados_rpv = []
    
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

    # Botões de Abrir/Fechar Todos
    if total_registros_filtrados > 0:
        st.markdown("---")
        col_exp1, col_exp2, col_exp3, col_exp_space = st.columns([2, 2, 2, 4])
        
        with col_exp1:
            if st.button("🔽 Abrir Todos", key="abrir_todos_rpv"):
                # Adicionar todos os IDs dos RPVs filtrados ao set de expandidos
                for _, processo in df_filtrado.iterrows():
                    rpv_id = processo.get("ID", "N/A")
                    if rpv_id != "N/A" and rpv_id is not None and rpv_id != "":
                        # Converter para string para consistência
                        st.session_state.rpv_expanded_cards.add(str(rpv_id))
                st.rerun()
        
        with col_exp2:
            if st.button("🔼 Fechar Todos", key="fechar_todos_rpv"):
                # Limpar o set de cards expandidos
                st.session_state.rpv_expanded_cards.clear()
                st.rerun()
        
        with col_exp3:
            if st.button("🔄 Limpar Cache", key="limpar_cache_rpv", help="Limpa o estado de expansão para corrigir problemas"):
                # Limpar completamente o estado de expansão e forçar recarregamento
                st.session_state.rpv_expanded_cards = set()
                if "rpv_aberto_id" in st.session_state:
                    del st.session_state["rpv_aberto_id"]
                if "show_rpv_dialog" in st.session_state:
                    del st.session_state["show_rpv_dialog"]
                st.success("✅ Cache limpo! Cada RPV agora abre individualmente.")
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

    # CSS para cards dropdown (aplicado via função reutilizável)
    aplicar_css_cards_rpv()

    # Lista de RPVs
    if not df_paginado.empty:
        st.markdown(f"### 📋 Lista de RPVs ({total_registros} encontrados)")
        
        # Renderizar cards
        for idx, rpv in enumerate(df_paginado.iterrows()):
            _, rpv = rpv  # Desempacotar o tuple
            rpv_id = rpv.get("ID", "N/A")
            
            # GARANTIR que o ID seja único e válido
            if rpv_id == "N/A" or rpv_id is None or rpv_id == "":
                continue  # Pular RPVs sem ID válido
            
            # Converter ID para string para garantir consistência
            rpv_id = str(rpv_id)
            
            # Criar chave única para this specific card instance (incluindo página e posição)
            pagina_atual = st.session_state.get("current_page_rpvs", 1)
            card_key = f"{rpv_id}_{pagina_atual}_{idx}"
            
            # Usar o ID único do RPV ao invés de agrupar por processo
            is_expanded = card_key in st.session_state.rpv_expanded_cards
            
            card_class = "rpv-card expanded" if is_expanded else "rpv-card"
            
            with st.container():
                # Layout com checkbox e botão expandir (igual aos Benefícios)
                if st.session_state.modo_exclusao_rpv:
                    col_check, col_expand, col_info = st.columns([0.3, 0.7, 9])
                    
                    with col_check:
                        # Usar chave única que inclui página e índice para evitar duplicatas
                        checkbox_key = f"rpv_select_{rpv_id}_{pagina_atual}_{idx}"
                        if st.checkbox("", key=checkbox_key, label_visibility="collapsed"):
                            if rpv_id not in st.session_state.processos_selecionados_rpv:
                                st.session_state.processos_selecionados_rpv.append(rpv_id)
                        elif rpv_id in st.session_state.processos_selecionados_rpv:
                            st.session_state.processos_selecionados_rpv.remove(rpv_id)
                else:
                    col_expand, col_info = st.columns([1, 9])
                
                with col_expand if not st.session_state.modo_exclusao_rpv else col_expand:
                    expand_text = "▼ Fechar" if is_expanded else "▶ Abrir"
                    # Usar chave única baseada no card_key
                    button_key = f"expand_rpv_{card_key}"
                    
                    if st.button(expand_text, key=button_key):
                        if is_expanded:
                            # Remover apenas este card específico
                            st.session_state.rpv_expanded_cards.discard(card_key)
                        else:
                            # Adicionar apenas este card específico
                            st.session_state.rpv_expanded_cards.add(card_key)
                        st.rerun()
                
                with col_info:
                    # Informações resumidas (sempre visíveis) com status colorido
                    status_atual = safe_get_value(rpv, 'Status', 'Não informado')
                    status_info = obter_cor_status(status_atual, "rpv")
                    
                    # Título com processo e beneficiário
                    processo_titulo = safe_get_value(rpv, 'Processo', 'Não informado')
                    descricao_rpv = safe_get_value(rpv, 'Descricao RPV', '')
                    
                    # Verificar se é um RPV múltiplo (processo contém "-1", "-2", etc.)
                    processo_base = processo_titulo.split('-')[0] if '-' in processo_titulo else processo_titulo
                    is_multiplo = '-' in processo_titulo and len(processo_titulo.split('-')) >= 2
                    
                    if is_multiplo:
                        partes_processo = processo_titulo.split('-')
                        numero_rpv = partes_processo[-1] if len(partes_processo) > 1 else "?"
                    
                    if descricao_rpv and descricao_rpv != 'Não informado':
                        st.markdown("---")
                        if is_multiplo:
                            st.markdown(f"📄 **Processo:** {processo_base} - **RPV #{numero_rpv}**")
                            st.markdown(f"**📝 Descrição:** {descricao_rpv}")
                        else:
                            st.markdown(f"📄 **Processo:** {processo_titulo}")
                            st.markdown(f"**📝 Descrição:** {descricao_rpv}")
                    else:
                        if is_multiplo:
                            st.markdown(f"📄 **Processo:** {processo_base} - **RPV #{numero_rpv}**")
                        else:
                            st.markdown(f"📄 **Processo:** {processo_titulo}")

                    st.markdown(f"""
                    <div class="rpv-info-grid">
                        <div class="info-item">
                            <div class="info-label">Processo</div>
                            <div class="info-value">{safe_get_value(rpv, 'Processo', 'Não informado')}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Beneficiário</div>
                            <div class="info-value">{safe_get_value(rpv, 'Beneficiário', 'Não informado')}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">CPF</div>
                            <div class="info-value">{safe_get_value(rpv, 'CPF', 'Não informado')}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Valor Cliente</div>
                            <div class="info-value">R$ {safe_get_value(rpv, 'Valor Cliente', '0.00')}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Status</div>
                            <div class="info-value">{status_info['html']}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Mês Competência</div>
                            <div class="info-value">{safe_get_value(rpv, 'Mês Competência', 'Não informado')}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Conteúdo expandido (tabs)
                if is_expanded:
                    st.markdown("---")
                    # Incluir descrição do RPV no título se existir
                    descricao_rpv = safe_get_value(rpv, 'Descricao RPV', '')
                    titulo_processo = safe_get_value(rpv, 'Processo', 'Não informado')
                    
                    # Verificar se é RPV múltiplo e mostrar informação adequada
                    is_multiplo = '-' in titulo_processo and len(titulo_processo.split('-')) >= 2
                    
                    if is_multiplo:
                        processo_base = titulo_processo.split('-')[0]
                        numero_rpv = titulo_processo.split('-')[-1]
                        st.markdown(f" 📄 {processo_base} - 🔢 RPV {numero_rpv}")
                    else:
                        if descricao_rpv and descricao_rpv != 'Não informado':
                            st.markdown(f" 📄 {titulo_processo}")
                            st.markdown(f"**📝 Descrição:** {descricao_rpv}")
                        else:
                            st.markdown(f" 📄 {titulo_processo}")
                    
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
        # Exibir descrição do RPV se existir
        descricao_rpv = safe_get_value(processo, 'Descricao RPV', '')
        if descricao_rpv and descricao_rpv != 'Não informado':
            st.write(f"**Descrição do RPV:** {descricao_rpv}")
        
        st.write(f"**CPF:** {safe_get_value(processo, 'CPF')}")
        st.write(f"**Agência:** {safe_get_value(processo, 'Agência')}")
        st.write(f"**Conta:** {safe_get_value(processo, 'Conta')}")
        st.write(f"**Banco:** {safe_get_value(processo, 'Banco')}")
    
    with col_det2:
        st.markdown("**💰 Valores:**")
        
        # Exibir novos campos de valores
        houve_destaque = safe_get_value(processo, 'Houve Destaque Honorarios', 'Não')
        st.write(f"**Houve destaque de honorários:** {houve_destaque}")
        
        valor_cliente = safe_get_value(processo, 'Valor Cliente', '0.00')
        st.write(f"**Valor Cliente:** R$ {valor_cliente}")
        
        honorarios_contratuais = safe_get_value(processo, 'Honorarios Contratuais', '0.00')
        st.write(f"**Honorários Contratuais:** R$ {honorarios_contratuais}")
        
        valor_parceiro = safe_get_value(processo, 'Valor Parceiro Prospector', '0.00')
        st.write(f"**Valor Parceiro/Prospector:** R$ {valor_parceiro}")
        
        valor_sucumbencial = safe_get_value(processo, 'Valor Honorario Sucumbencial', '0.00')
        st.write(f"**Honorário Sucumbencial:** R$ {valor_sucumbencial}")
        
        outros_valores = safe_get_value(processo, 'Outros Valores', '0.00')
        st.write(f"**Outros Valores:** R$ {outros_valores}")
        
        # Observações sobre valores
        obs_valores = safe_get_value(processo, 'Observacoes Valores', '')
        if obs_valores and obs_valores != 'Não informado':
            st.write(f"**Observações sobre valores:** {obs_valores}")
        st.write(f"**Mês Competência:** {safe_get_value(processo, 'Mês Competência')}")
        st.write(f"**Assunto:** {safe_get_value(processo, 'Assunto')}")
        st.write(f"**Órgão Judicial:** {safe_get_value(processo, 'Orgao Judicial')}")
    
    # Mostrar detalhes dos honorários contratuais
    mostrar_detalhes_hc_rpv(processo, f"info_{rpv_id}")
    
    # Observações sobre honorários contratuais
    obs_hc = safe_get_value(processo, 'Observacoes Honorarios Contratuais', '')
    if obs_hc and obs_hc != 'Não informado':
        st.markdown("##### 💼 Observações dos Honorários Contratuais")
        st.info(obs_hc)
    
    # Observações gerais
    if safe_get_value(processo, 'Observações'):
        st.markdown("##### 📝 Observações Gerais")
        st.info(safe_get_value(processo, 'Observações'))

def render_tab_acoes_rpv(df, processo, rpv_id, status_atual, perfil_usuario):
    """Renderiza a tab de ações do RPV - inclui edição completa para Cadastradores e Admins"""
    
    # Import necessário para salvamento
    from components.functions_controle import save_data_to_github_seguro
    
    # Usar a função original de edição, mas sem o cabeçalho
    linha_processo_df = df[df["ID"].astype(str) == str(rpv_id)]
    
    if len(linha_processo_df) == 0:
        st.error(f"❌ RPV com ID {rpv_id} não encontrado")
        return
    
    linha_processo = linha_processo_df.iloc[0]
    numero_processo = linha_processo.get("Processo", "N/A")
    
    # NOVA SEÇÃO: EDIÇÃO COMPLETA PARA CADASTRADORES E ADMINS
    if perfil_usuario in ["Cadastrador", "Admin"]:
        with st.expander("✏️ Editar Dados do Cadastro", expanded=False):
            # Adicionar página atual e timestamp para garantir chave única
            pagina_atual = st.session_state.get("current_page_rpvs", 1)
            timestamp = gerar_timestamp_unico()
            form_key = f"form_edicao_completa_rpv_{rpv_id}_{pagina_atual}_{timestamp}"
            with st.form(form_key):
                col_edit1, col_edit2 = st.columns(2)
            
                with col_edit1:
                    st.markdown("**📋 Dados Básicos:**")
                    
                    # Campo editável para o processo
                    processo_editado = st.text_input(
                        "Número do Processo:",
                        value=safe_get_value(linha_processo, "Processo", ""),
                        key=f"edit_processo_rpv_{rpv_id}_{pagina_atual}_{timestamp}"
                    )
                    
                    # Campo editável para beneficiário
                    beneficiario_editado = st.text_input(
                        "Beneficiário:",
                        value=safe_get_value(linha_processo, "Beneficiário", ""),
                        key=f"edit_beneficiario_rpv_{rpv_id}_{pagina_atual}_{timestamp}"
                    )
                    
                    # Campo editável para CPF
                    cpf_editado = st.text_input(
                        "CPF:",
                        value=safe_get_value(linha_processo, "CPF", ""),
                        key=f"edit_cpf_rpv_{rpv_id}_{pagina_atual}_{timestamp}"
                    )
                    
                    # Campo editável para descrição do RPV
                    descricao_editada = st.text_input(
                        "Descrição do RPV:",
                        value=safe_get_value(linha_processo, "Descricao RPV", ""),
                        key=f"edit_descricao_rpv_{rpv_id}_{pagina_atual}_{timestamp}"
                    )
                    
                    # Campo editável para assunto
                    assunto_editado = st.text_input(
                        "Assunto:",
                        value=safe_get_value(linha_processo, "Assunto", ""),
                        key=f"edit_assunto_rpv_{rpv_id}_{pagina_atual}_{timestamp}"
                    )
                    
                    # Campo editável para órgão judicial
                    orgao_editado = st.text_input(
                        "Órgão Judicial:",
                        value=safe_get_value(linha_processo, "Orgao Judicial", ""),
                        key=f"edit_orgao_rpv_{rpv_id}_{pagina_atual}_{timestamp}"
                    )
                    
                    # Campo editável para vara
                    vara_editada = st.text_input(
                        "Vara:",
                        value=safe_get_value(linha_processo, "Vara", ""),
                        key=f"edit_vara_rpv_{rpv_id}_{pagina_atual}_{timestamp}"
                    )
                
                with col_edit2:
                    st.markdown("**💰 Dados Bancários e Outros:**")
                    
                    # Campo editável para banco
                    banco_editado = st.selectbox(
                        "Banco:",
                        options=["CEF", "BB"],
                        index=0 if safe_get_value(linha_processo, "Banco", "CEF") == "CEF" else 1,
                        key=f"edit_banco_rpv_{rpv_id}_{pagina_atual}_{timestamp}"
                    )
                    
                    # Campo editável para agência
                    agencia_editada = st.text_input(
                        "Agência:",
                        value=safe_get_value(linha_processo, "Agência", ""),
                        key=f"edit_agencia_rpv_{rpv_id}_{pagina_atual}_{timestamp}"
                    )
                    
                    # Campo editável para conta
                    conta_editada = st.text_input(
                        "Conta:",
                        value=safe_get_value(linha_processo, "Conta", ""),
                        key=f"edit_conta_rpv_{rpv_id}_{pagina_atual}_{timestamp}"
                    )
                    
                    # Campo editável para mês competência
                    mes_competencia_editado = st.text_input(
                        "Mês Competência (mm/yyyy):",
                        value=safe_get_value(linha_processo, "Mês Competência", ""),
                        key=f"edit_mes_competencia_rpv_{rpv_id}_{pagina_atual}_{timestamp}"
                    )
                    
                    # Campo editável para solicitar certidão
                    certidao_editada = st.selectbox(
                        "Solicitar Certidão:",
                        options=["Sim", "Não"],
                        index=0 if safe_get_value(linha_processo, "Solicitar Certidão", "Não") == "Sim" else 1,
                        key=f"edit_certidao_rpv_{rpv_id}_{pagina_atual}_{timestamp}"
                    )
                    
                    # Campo editável para observações gerais
                    observacoes_editadas = st.text_area(
                        "Observações:",
                        value=safe_get_value(linha_processo, "Observações", ""),
                        height=100,
                        key=f"edit_observacoes_rpv_{rpv_id}_{pagina_atual}_{timestamp}"
                    )
                
                # Botão para salvar edições
                salvar_edicao = st.form_submit_button("💾 Salvar Alterações", type="primary")
                
                if salvar_edicao:
                    try:
                        idx = df[df["ID"] == rpv_id].index[0]
                        
                        # Atualizar todos os campos editados
                        st.session_state.df_editado_rpv.loc[idx, "Processo"] = processo_editado
                        st.session_state.df_editado_rpv.loc[idx, "Beneficiário"] = beneficiario_editado
                        st.session_state.df_editado_rpv.loc[idx, "CPF"] = cpf_editado
                        st.session_state.df_editado_rpv.loc[idx, "Descricao RPV"] = descricao_editada
                        st.session_state.df_editado_rpv.loc[idx, "Assunto"] = assunto_editado
                        st.session_state.df_editado_rpv.loc[idx, "Orgao Judicial"] = orgao_editado
                        st.session_state.df_editado_rpv.loc[idx, "Vara"] = vara_editada
                        st.session_state.df_editado_rpv.loc[idx, "Banco"] = banco_editado
                        st.session_state.df_editado_rpv.loc[idx, "Agência"] = agencia_editada
                        st.session_state.df_editado_rpv.loc[idx, "Conta"] = conta_editada
                        st.session_state.df_editado_rpv.loc[idx, "Mês Competência"] = mes_competencia_editado
                        st.session_state.df_editado_rpv.loc[idx, "Solicitar Certidão"] = certidao_editada
                        st.session_state.df_editado_rpv.loc[idx, "Observações"] = observacoes_editadas
                        
                        # Salvamento automático no GitHub
                        save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                        
                        st.success("✅ Dados editados e salvos automaticamente!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao salvar edições: {str(e)}")
        
        st.markdown("---")
    
    # Renderizar ações baseadas no status - usando a lógica original da interface_edicao_rpv
    if status_atual == "Cadastro" and perfil_usuario in ["Cadastrador", "Admin"]:
        st.info("Após finalizar o cadastro, este RPV será enviado para os perfis SAC e Administrativo.")
        
        # Usar timestamp para chave única
        timestamp = gerar_timestamp_unico()
        pagina_atual = st.session_state.get("current_page_rpvs", 1)
        
        if st.button("✅ Finalizar Cadastro e Enviar", type="primary", key=f"finalizar_cadastro_tab_{rpv_id}_{pagina_atual}_{timestamp}"):
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
            
            # Salvamento automático
            novo_sha = save_data_to_github_seguro(
                st.session_state.df_editado_rpv,
                "lista_rpv.csv",
                "file_sha_rpv"
            )
            if novo_sha:
                st.session_state.file_sha_rpv = novo_sha
                st.session_state.rpv_expanded_cards.discard(rpv_id)
                st.success("✅ RPV enviado simultaneamente para SAC e Administrativo e salvo automaticamente!")
                st.rerun()
            else:
                st.error("❌ Erro ao salvar. Tente novamente.")
    
    elif (perfil_usuario in ["SAC", "Admin"]) and ("SAC - aguardando documentação" in obter_status_simultaneo_ativo(linha_processo)):
        st.info("Marque quando a documentação SAC estiver pronta.")
        
        # Verificar se já está marcado
        sac_doc_pronta = linha_processo.get("SAC Documentacao Pronta", "") == "Sim"
        
        # Usar timestamp para chave única
        timestamp = gerar_timestamp_unico()
        pagina_atual = st.session_state.get("current_page_rpvs", 1)
        
        if not sac_doc_pronta:
            if st.checkbox("✅ Documentação SAC pronta", key=f"sac_doc_tab_{rpv_id}_{pagina_atual}_{timestamp}"):
                if st.button("🔄 Marcar SAC como Pronto", type="primary", key=f"marcar_sac_tab_{rpv_id}_{pagina_atual}_{timestamp}"):
                    idx = df[df["ID"] == rpv_id].index[0]
                    
                    # Atualizar status SAC (sempre no status principal)
                    st.session_state.df_editado_rpv.loc[idx, "Status"] = "SAC - documentação pronta"
                    st.session_state.df_editado_rpv.loc[idx, "SAC Documentacao Pronta"] = "Sim"
                    st.session_state.df_editado_rpv.loc[idx, "Data SAC Documentacao"] = str(datetime.now().strftime("%d/%m/%Y %H:%M"))
                    st.session_state.df_editado_rpv.loc[idx, "SAC Responsavel"] = str(st.session_state.get("usuario", "Sistema"))
                    
                    # Salvamento automático
                    save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                    st.session_state.rpv_expanded_cards.discard(rpv_id)
                    st.success("✅ Status SAC atualizado e salvo automaticamente!")
                    st.rerun()
        else:
            st.success(f"✅ SAC já marcou documentação como pronta em {linha_processo.get('Data SAC Documentacao', 'N/A')}")
    
    elif (perfil_usuario in ["Administrativo", "Admin"]) and ("Administrativo - aguardando documentação" in obter_status_simultaneo_ativo(linha_processo)):
        st.info("Marque quando a documentação Administrativa estiver pronta.")
        
        # Verificar se já está marcado
        admin_doc_pronta = linha_processo.get("Admin Documentacao Pronta", "") == "Sim"
        
        # Usar timestamp para chave única
        timestamp = gerar_timestamp_unico()
        pagina_atual = st.session_state.get("current_page_rpvs", 1)
        
        if not admin_doc_pronta:
            if st.checkbox("✅ Documentação Administrativa pronta", key=f"admin_doc_tab_{rpv_id}_{pagina_atual}_{timestamp}"):
                if st.button("🔄 Marcar Administrativo como Pronto", type="primary", key=f"marcar_admin_tab_{rpv_id}_{pagina_atual}_{timestamp}"):
                    idx = df[df["ID"] == rpv_id].index[0]
                    
                    # Atualizar status Administrativo (sempre no status secundário)
                    st.session_state.df_editado_rpv.loc[idx, "Status Secundario"] = "Administrativo - documentação pronta"
                    st.session_state.df_editado_rpv.loc[idx, "Admin Documentacao Pronta"] = "Sim"
                    st.session_state.df_editado_rpv.loc[idx, "Data Admin Documentacao"] = str(datetime.now().strftime("%d/%m/%Y %H:%M"))
                    st.session_state.df_editado_rpv.loc[idx, "Admin Responsavel"] = str(st.session_state.get("usuario", "Sistema"))
                    
                    # Salvamento automático
                    save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                    st.session_state.rpv_expanded_cards.discard(rpv_id)
                    st.success("✅ Status Administrativo atualizado e salvo automaticamente!")
                    st.rerun()
        else:
            st.success(f"✅ Administrativo já marcou documentação como pronta em {linha_processo.get('Data Admin Documentacao', 'N/A')}")
    
    # SEÇÃO DE VALORES FINANCEIROS - Disponível para Financeiro e Admin
    if perfil_usuario in ["Financeiro", "Admin"]:
        st.markdown("---")
        st.markdown("### 💰 Valores Financeiros")
        
        timestamp = gerar_timestamp_unico()
        pagina_atual = st.session_state.get("current_page_rpvs", 1)
        with st.form(f"form_valores_rpv_tab_{rpv_id}_{pagina_atual}_{timestamp}"):
            # Checkbox para destaque de honorários
            houve_destaque = st.checkbox(
                "✅ Houve destaque de honorários",
                value=safe_get_value(linha_processo, "Houve Destaque Honorarios", "Não") == "Sim",
                help="Marque se houve destaque de honorários",
                key=f"destaque_rpv_tab_{rpv_id}_{pagina_atual}_{timestamp}"
            )
            
            col_val1, col_val2 = st.columns(2)
            
            with col_val1:
                # Valor do saque (NOVO CAMPO)
                valor_saque = st.number_input(
                    "💰 Valor do saque (R$):",
                    min_value=0.0,
                    value=float(safe_get_value(linha_processo, "Valor Saque", "0") or "0"),
                    step=0.01,
                    format="%.2f",
                    help="Valor total do saque do RPV",
                    key=f"valor_saque_rpv_tab_{rpv_id}_{pagina_atual}_{timestamp}"
                )
                
                # Honorários contratuais
                honorarios_contratuais = st.number_input(
                    "💼 Honorários contratuais (R$):",
                    min_value=0.0,
                    value=float(safe_get_value(linha_processo, "Honorarios Contratuais", "0") or "0"),
                    step=0.01,
                    format="%.2f",
                    help="Valor dos honorários contratuais",
                    key=f"honorarios_rpv_tab_{rpv_id}_{pagina_atual}_{timestamp}"
                )
                
                # H. Sucumbenciais (NOVO CAMPO)
                h_sucumbenciais = st.number_input(
                    "⚖️ H. Sucumbenciais (R$):",
                    min_value=0.0,
                    value=float(safe_get_value(linha_processo, "H Sucumbenciais", "0") or "0"),
                    step=0.01,
                    format="%.2f",
                    help="Valor dos honorários sucumbenciais",
                    key=f"h_sucumbenciais_rpv_tab_{rpv_id}_{pagina_atual}_{timestamp}"
                )
                
                # Valor cliente
                valor_cliente = st.number_input(
                    "👤 Valor cliente (R$):",
                    min_value=0.0,
                    value=float(safe_get_value(linha_processo, "Valor Cliente", "0") or "0"),
                    step=0.01,
                    format="%.2f",
                    help="Valor destinado ao cliente",
                    key=f"valor_cliente_rpv_tab_{rpv_id}_{pagina_atual}_{timestamp}"
                )
            
            with col_val2:
                # Valor parceiro/prospector
                valor_parceiro_prospector = st.number_input(
                    "🤝 Valor parceiro/prospector (R$):",
                    min_value=0.0,
                    value=float(safe_get_value(linha_processo, "Valor Parceiro Prospector", "0") or "0"),
                    step=0.01,
                    format="%.2f",
                    help="Valor destinado ao parceiro/prospector",
                    key=f"parceiro_rpv_tab_{rpv_id}_{pagina_atual}_{timestamp}"
                )
                
                # Outros valores
                outros_valores = st.number_input(
                    "🔢 Outros valores (R$):",
                    min_value=0.0,
                    value=float(safe_get_value(linha_processo, "Outros Valores", "0") or "0"),
                    step=0.01,
                    format="%.2f",
                    help="Outros valores relacionados",
                    key=f"outros_rpv_tab_{rpv_id}_{pagina_atual}_{timestamp}"
                )
                
                # Forma de pagamento (NOVO CAMPO)
                forma_pagamento = st.selectbox(
                    "💳 Forma de pagamento ao cliente:",
                    options=["PIX", "Transferência", "Dinheiro"],
                    index=0 if safe_get_value(linha_processo, "Forma Pagamento", "PIX") == "PIX" else 
                          1 if safe_get_value(linha_processo, "Forma Pagamento", "PIX") == "Transferência" else 2,
                    help="Forma como o pagamento será feito ao cliente",
                    key=f"forma_pagamento_rpv_tab_{rpv_id}_{pagina_atual}_{timestamp}"
                )
                
                # Seção de resumo financeiro
                st.markdown("---")
                st.markdown("**📊 Resumo Financeiro:**")
                
                # Cálculos
                total_honorarios_outros = honorarios_contratuais + h_sucumbenciais + outros_valores
                total_pago_cliente = valor_saque - total_honorarios_outros
                total_recebido_escritorio = total_honorarios_outros - valor_parceiro_prospector
                
                # Métricas de resumo
                col_res1, col_res2, col_res3 = st.columns(3)
                
                with col_res1:
                    st.metric(
                        "💰 Total pago ao cliente", 
                        f"R$ {total_pago_cliente:,.2f}",
                        help="(Valor do Saque) - (Honorários + Outros)"
                    )
                
                with col_res2:
                    st.metric(
                        "🏢 Total recebido pelo escritório", 
                        f"R$ {total_recebido_escritorio:,.2f}",
                        help="(Honorários + Outros) - (Valor pago a parceiros/prospectores)"
                    )
                
                with col_res3:
                    st.metric(
                        "🤝 Total pago a parceiro/prospector", 
                        f"R$ {valor_parceiro_prospector:,.2f}",
                        help="Valor destinado ao parceiro/prospector"
                    )
            
            # Observações sobre valores
            observacoes_valores = st.text_area(
                "📝 Observações sobre valores:",
                value=safe_get_value(linha_processo, "Observacoes Valores", ""),
                help="Detalhes ou observações sobre os valores",
                height=100,
                key=f"obs_valores_rpv_tab_{rpv_id}_{pagina_atual}_{timestamp}"
            )
            
            # Nova seção: Observações específicas para honorários contratuais
            observacoes_hc = st.text_area(
                "💼 Observações para honorários contratuais (antes de enviar para Rodrigo):",
                value=safe_get_value(linha_processo, "Observacoes Honorarios Contratuais", ""),
                help="Observações específicas sobre honorários contratuais que serão consideradas antes do envio para Rodrigo",
                height=80,
                key=f"obs_hc_rpv_tab_{rpv_id}_{pagina_atual}_{timestamp}"
            )
            
            # Botão para salvar valores
            salvar_valores = st.form_submit_button("💾 Salvar Valores Financeiros", type="primary")
            
            if salvar_valores:
                try:
                    idx = df[df["ID"] == rpv_id].index[0]
                    
                    # Salvar todos os valores
                    st.session_state.df_editado_rpv.loc[idx, "Houve Destaque Honorarios"] = "Sim" if houve_destaque else "Não"
                    st.session_state.df_editado_rpv.loc[idx, "Valor Saque"] = valor_saque
                    st.session_state.df_editado_rpv.loc[idx, "Honorarios Contratuais"] = honorarios_contratuais
                    st.session_state.df_editado_rpv.loc[idx, "H Sucumbenciais"] = h_sucumbenciais
                    st.session_state.df_editado_rpv.loc[idx, "Valor Cliente"] = valor_cliente
                    st.session_state.df_editado_rpv.loc[idx, "Valor Parceiro Prospector"] = valor_parceiro_prospector
                    st.session_state.df_editado_rpv.loc[idx, "Outros Valores"] = outros_valores
                    st.session_state.df_editado_rpv.loc[idx, "Forma Pagamento"] = forma_pagamento
                    st.session_state.df_editado_rpv.loc[idx, "Observacoes Valores"] = observacoes_valores
                    st.session_state.df_editado_rpv.loc[idx, "Observacoes Honorarios Contratuais"] = observacoes_hc
                    
                    # Salvamento automático no GitHub
                    save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                    
                    # Calcular total para exibir na mensagem
                    total_honorarios_outros = honorarios_contratuais + h_sucumbenciais + outros_valores
                    total_pago_cliente = valor_saque - total_honorarios_outros
                    st.success(f"✅ Valores financeiros salvos automaticamente! Total pago ao cliente: R$ {total_pago_cliente:,.2f}")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erro ao salvar valores: {str(e)}")
    
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
            
            <div class="info-title">⚖️ Vara</div>
            <div class="info-value">{safe_get_value(linha_rpv, 'Vara', 'Não informada')}</div>
            
            <div class="info-title">📂 Assunto</div>
            <div class="info-value">{safe_get_value(linha_rpv, 'Assunto')}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        valor_cliente = safe_get_value(linha_rpv, 'Valor Cliente', '0.00')
        mes_competencia = safe_get_value(linha_rpv, 'Mês Competência')
        data_cadastro = safe_get_value(linha_rpv, 'Data Cadastro')
        cadastrado_por = safe_get_value(linha_rpv, 'Cadastrado Por')
        
        st.markdown(f"""
        <div class="info-card">
            <div class="info-title">💰 Valor Cliente</div>
            <div class="info-value">R$ {valor_cliente}</div>
            
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
            <div class="compact-label">💰 VALOR CLIENTE</div>
            <div class="compact-value">R$ {safe_get_value(linha_rpv, 'Valor Cliente', '0.00')}</div>
        </div>
        <div class="compact-item">
            <div class="compact-label">💼 TOTAL HC</div>
            <div class="compact-value">R$ {total_hc:.2f}</div>
        </div>
        <div class="compact-item">
            <div class="compact-label">🏛️ ÓRGÃO</div>
            <div class="compact-value">{safe_get_value(linha_rpv, 'Orgao Judicial')[:20]}...</div>
        </div>
        <div class="compact-item">
            <div class="compact-label">⚖️ VARA</div>
            <div class="compact-value">{safe_get_value(linha_rpv, 'Vara', 'N/A')[:15]}...</div>
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
    valor_val = safe_get_value(linha_rpv, 'Valor Cliente', '0.00')
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
            
            # Salvamento automático
            novo_sha = save_data_to_github_seguro(
                st.session_state.df_editado_rpv,
                "lista_rpv.csv",
                "file_sha_rpv"
            )
            if novo_sha:
                st.session_state.file_sha_rpv = novo_sha
                st.session_state.show_rpv_dialog = False
                st.success("✅ RPV enviado simultaneamente para SAC e Administrativo e salvo automaticamente!")
                st.rerun()
            else:
                st.error("❌ Erro ao salvar. Tente novamente.")
    
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
                    
                    # Salvamento automático
                    save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                    st.session_state.show_rpv_dialog = False
                    st.success("✅ Status SAC atualizado e salvo automaticamente!")
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
                    
                    # Salvamento automático
                    save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                    st.session_state.show_rpv_dialog = False
                    st.success("✅ Status Administrativo atualizado e salvo automaticamente!")
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
    
    elif perfil_usuario in ["Financeiro", "Admin"]:
        # Verificar se ambos SAC e Administrativo finalizaram (independente do status atual)
        sac_finalizado = linha_rpv.get("SAC Documentacao Pronta", "") == "Sim"
        admin_finalizado = linha_rpv.get("Admin Documentacao Pronta", "") == "Sim"
        
        # Se ambos finalizaram E ainda não foi validado pelo financeiro
        if (sac_finalizado and admin_finalizado and 
            linha_rpv.get("Validado Financeiro", "Não") == "Não" and
            status_atual not in ["Enviado para Rodrigo", "aguardando pagamento", "finalizado"]):
            
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
                    
                    # Salvamento automático
                    save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                    st.session_state.show_rpv_dialog = False
                    st.success("✅ RPV validado e enviado para Rodrigo automaticamente!")
                    st.rerun()
        
        # Se nem todos finalizaram ainda, mostrar progresso
        elif not (sac_finalizado and admin_finalizado) and status_atual not in ["Enviado para Rodrigo", "aguardando pagamento", "finalizado"]:
            # Mostrar status de progresso para Financeiro
            st.markdown("#### 💰 Aguardando Conclusão das Etapas Anteriores")
            
            col1, col2 = st.columns(2)
            with col1:
                if sac_finalizado:
                    st.success("✅ SAC - Documentação pronta")
                else:
                    st.info("⏳ SAC - Aguardando documentação")
            
            with col2:
                if admin_finalizado:
                    st.success("✅ Administrativo - Documentação pronta")
                else:
                    st.info("⏳ Administrativo - Aguardando documentação")
            
            st.info("💡 Quando ambas as etapas estiverem completas, você poderá validar e enviar para Rodrigo.")
    
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
        
        timestamp = gerar_timestamp_unico()
        with st.form(f"form_hc_rpv_{rpv_id}_{st.session_state.get('current_page_rpvs', 1)}_{timestamp}"):
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
                    
                    # Salvamento automático no GitHub
                    save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                    
                    total_novo = honorarios_contratuais + hc1_valor + hc2_valor
                    st.success(f"✅ Honorários salvos automaticamente! Total: R$ {total_novo:.2f}")
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
    limpar_estados_dialog_rpv()
    
    if df.empty:
        st.info("ℹ️ Não há RPVs para visualizar.")
        return

    # Cards de estatísticas compactos
    total_rpvs = len(df)
    finalizados = len(df[df["Status"] == "finalizado"]) if "Status" in df.columns else 0
    pendentes = total_rpvs - finalizados
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total de RPVs", total_rpvs)
    
    with col2:
        taxa_finalizados = (finalizados/total_rpvs*100) if total_rpvs > 0 else 0
        st.metric("✅ Finalizados", f"{finalizados} ({taxa_finalizados:.1f}%)")
    
    with col3:
        taxa_pendentes = (pendentes/total_rpvs*100) if total_rpvs > 0 else 0
        st.metric("⏳ Em Andamento", f"{pendentes} ({taxa_pendentes:.1f}%)")
    
    with col4:
        if "Data Cadastro" in df.columns:
            hoje = datetime.now().strftime("%d/%m/%Y")
            df_temp = df.copy()
            df_temp["Data Cadastro"] = df_temp["Data Cadastro"].astype(str)
            hoje_count = len(df_temp[df_temp["Data Cadastro"].str.contains(hoje, na=False)])
        else:
            hoje_count = 0
        st.metric("📅 Cadastrados Hoje", hoje_count)

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

    # Exibição com AgGrid
    st.markdown(f"### 📋 Lista de RPVs ({len(df_visualizado)} registros)")
    
    if not df_visualizado.empty:
        # Preparar dados para o AgGrid
        df_display = df_visualizado.copy()
        
        # Selecionar e renomear colunas para exibição
        # Mapear nomes reais das colunas do arquivo para nomes de exibição
        colunas_para_exibir = {
            'Processo': 'Processo',
            'Beneficiário': 'Beneficiário', 
            'CPF': 'CPF',
            'Valor Cliente': 'Valor Cliente (R$)',
            'Status': 'Status',
            'Assunto': 'Assunto',
            'Orgao Judicial': 'Órgão Judicial',
            'Data Cadastro': 'Data Cadastro',
            'Cadastrado Por': 'Cadastrado Por',
            'Mês Competência': 'Mês Competência'
        }
        
        # Verificar colunas alternativas que existem no arquivo
        colunas_alternativas = {
            'Data Cadastro': 'Data de Cadastro',
            'Cadastrado Por': 'Cadastrado por'
        }
        
        # Filtrar apenas as colunas que existem no DataFrame
        colunas_existentes = {}
        for coluna_esperada, nome_exibicao in colunas_para_exibir.items():
            if coluna_esperada in df_display.columns:
                colunas_existentes[coluna_esperada] = nome_exibicao
            elif coluna_esperada in colunas_alternativas and colunas_alternativas[coluna_esperada] in df_display.columns:
                # Usar coluna alternativa se a principal não existir
                colunas_existentes[colunas_alternativas[coluna_esperada]] = nome_exibicao
        
        df_display = df_display[list(colunas_existentes.keys())].rename(columns=colunas_existentes)
        
        # Formatar valor monetário
        if 'Valor Cliente (R$)' in df_display.columns:
            df_display['Valor Cliente (R$)'] = df_display['Valor Cliente (R$)'].apply(
                lambda x: f"R$ {float(x):,.2f}" if pd.notna(x) and str(x).replace('.', '').replace(',', '').isdigit() else str(x)
            )
        
        # Configurar o AgGrid
        gb = GridOptionsBuilder.from_dataframe(df_display)
        
        # Configurações gerais
        gb.configure_default_column(
            groupable=False,
            value=True,
            enableRowGroup=False,
            aggFunc="sum",
            editable=False,
            filterable=True,
            sortable=True,
            resizable=True
        )
        
        # Configurar colunas específicas
        if 'Processo' in df_display.columns:
            gb.configure_column("Processo", width=180, pinned='left')
        if 'Beneficiário' in df_display.columns:
            gb.configure_column("Beneficiário", width=200)
        if 'CPF' in df_display.columns:
            gb.configure_column("CPF", width=130)
        if 'Valor Cliente (R$)' in df_display.columns:
            gb.configure_column("Valor Cliente (R$)", width=150, type="numericColumn")
        if 'Status' in df_display.columns:
            gb.configure_column("Status", width=140)
        if 'Assunto' in df_display.columns:
            gb.configure_column("Assunto", width=160)
        if 'Órgão Judicial' in df_display.columns:
            gb.configure_column("Órgão Judicial", width=180)
        if 'Data Cadastro' in df_display.columns:
            gb.configure_column("Data Cadastro", width=120)
        if 'Cadastrado Por' in df_display.columns:
            gb.configure_column("Cadastrado Por", width=140)
        if 'Mês Competência' in df_display.columns:
            gb.configure_column("Mês Competência", width=130)
        
        # Configurações de paginação e seleção
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
        gb.configure_side_bar()
        
        # Só configurar seleção se temos colunas no DataFrame
        if not df_display.empty and len(df_display.columns) > 0:
            gb.configure_selection(selection_mode="multiple", use_checkbox=True)
        
        # Tema
        gb.configure_grid_options(
            enableRangeSelection=True,
            domLayout='normal'
        )
        
        grid_options = gb.build()
        
        # Renderizar AgGrid
        grid_response = AgGrid(
            df_display,
            gridOptions=grid_options,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            fit_columns_on_grid_load=True,
            theme='streamlit',
            height=600,
            width='100%',
            reload_data=False
        )
        
        # Informações sobre seleção
        selected_rows = grid_response['selected_rows']
        if selected_rows is not None and len(selected_rows) > 0:
            st.info(f"✅ {len(selected_rows)} linha(s) selecionada(s)")
            
            # Opção para exportar apenas as linhas selecionadas
            if st.button("📥 Baixar Selecionados", key="export_selected_rpv"):
                df_selected = pd.DataFrame(selected_rows)
                csv_selected = df_selected.to_csv(index=False, sep=';').encode('utf-8')
                st.download_button(
                    label="📥 Download CSV Selecionados",
                    data=csv_selected,
                    file_name=f"rpvs_selecionados_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    key="download_selected_rpv"
                )
        
    else:
        st.info("📭 Nenhum registro encontrado com os filtros aplicados.")

def interface_cadastro_rpv(df, perfil_usuario):
    """Interface para cadastrar novos RPVs"""
    
    # LIMPAR ESTADOS DE DIÁLOGO ao entrar na aba de cadastro
    limpar_estados_dialog_rpv()
    
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

    # Checkbox para múltiplos RPVs
    multiplos_rpvs = st.checkbox(
        "📋 Cadastrar múltiplos RPVs com mesmo beneficiário",
        value=False,
        help="Marque para cadastrar vários RPVs para o mesmo beneficiário com valores diferentes",
        key="multiplos_rpvs_checkbox"
    )
    
    # Número de RPVs se múltiplos estiver marcado
    num_rpvs = 1
    if multiplos_rpvs:
        num_rpvs = st.number_input(
            "Quantos RPVs deseja cadastrar?",
            min_value=2,
            max_value=10,
            value=2,
            step=1,
            key="num_rpvs_input"
        )
    
    col1, col2 = st.columns(2)
    
    processo_key = "new_rpv_processo"
    beneficiario_key = "new_rpv_beneficiario"
    cpf_key = "new_rpv_cpf"
    certidao_key = "new_rpv_certidao"
    obs_key = "new_rpv_observacoes"
    multiplos_key = "new_rpv_multiplos"
    competencia_key = "new_rpv_competencia"
    
    with col1:
        st.markdown("**👤 Dados do Beneficiário (comum para todos os RPVs):**")
        processo = st.text_input("Número do Processo Principal: *", key=processo_key)
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
        
        # Campo Vara com nova interface
        vara_selecionada = campo_vara_rpv(
            label="Vara:",
            key_prefix="new_rpv_vara"
        )
        
        # Converter para formato compatível
        vara_final = vara_selecionada if vara_selecionada else ""
        
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
        
        # Campo de observações gerais (comum)
        observacoes = st.text_area("Observações gerais:", height=68, key=obs_key)
    
    with col2:
        # Mostrar campos específicos para cada RPV
        st.markdown(f"**💰 Dados Específicos dos RPVs ({num_rpvs} RPV{'s' if num_rpvs > 1 else ''}):**")
        
        # Inicializar dicionário para armazenar dados de cada RPV
        if f"rpvs_data_{num_rpvs}" not in st.session_state:
            st.session_state[f"rpvs_data_{num_rpvs}"] = {}
        
        rpvs_data = st.session_state[f"rpvs_data_{num_rpvs}"]
        
        # Criar tabs para cada RPV se múltiplos
        if multiplos_rpvs and num_rpvs > 1:
            rpv_tabs = st.tabs([f"RPV {i+1}" for i in range(num_rpvs)])
            
            for i, tab in enumerate(rpv_tabs):
                with tab:
                    rpv_key = f"rpv_{i+1}"
                    if rpv_key not in rpvs_data:
                        rpvs_data[rpv_key] = {}
                    
                    # Descrição específica do RPV
                    rpvs_data[rpv_key]['descricao'] = st.text_input(
                        f"Descrição do RPV {i+1}: *",
                        key=f"descricao_rpv_{i+1}",
                        help="Descreva especificamente este RPV"
                    )
                    
                    # Valores financeiros específicos
                    col2_1, col2_2 = st.columns(2)
                    
                    with col2_1:
                        # Houve destaque de honorários (checkbox)
                        rpvs_data[rpv_key]['houve_destaque_honorarios'] = st.checkbox(
                            "✅ Houve destaque de honorários",
                            value=False,
                            help="Marque se houve destaque de honorários",
                            key=f"destaque_honorarios_rpv_{i+1}"
                        )
                        
                        # Valor do saque
                        rpvs_data[rpv_key]['valor_saque'] = st.number_input(
                            "Valor do saque (R$): *",
                            min_value=0.0,
                            step=0.01,
                            format="%.2f",
                            help="Valor total do saque do RPV",
                            key=f"valor_saque_rpv_{i+1}"
                        )
                        
                        # Honorários contratuais
                        rpvs_data[rpv_key]['honorarios_contratuais'] = st.number_input(
                            "Honorários contratuais (R$):",
                            min_value=0.0,
                            step=0.01,
                            format="%.2f",
                            help="Valor dos honorários contratuais",
                            key=f"honorarios_contratuais_rpv_{i+1}"
                        )
                        
                        # Honorários sucumbenciais
                        rpvs_data[rpv_key]['h_sucumbenciais'] = st.number_input(
                            "H. Sucumbenciais (R$):",
                            min_value=0.0,
                            step=0.01,
                            format="%.2f",
                            help="Valor dos honorários sucumbenciais",
                            key=f"h_sucumbenciais_rpv_{i+1}"
                        )
                        
                        # Valor cliente
                        rpvs_data[rpv_key]['valor_cliente'] = st.number_input(
                            "Valor cliente (R$): *",
                            min_value=0.0,
                            step=0.01,
                            format="%.2f",
                            help="Valor destinado ao cliente",
                            key=f"valor_cliente_rpv_{i+1}"
                        )
                    
                    with col2_2:
                        # Valor de honorário sucumbencial (removido pois já existe H. Sucumbenciais)
                        # rpvs_data[rpv_key]['valor_honorario_sucumbencial'] = st.number_input(
                        
                        # Valor parceiro/prospector
                        rpvs_data[rpv_key]['valor_parceiro_prospector'] = st.number_input(
                            "Valor parceiro/prospector (R$):",
                            min_value=0.0,
                            step=0.01,
                            format="%.2f",
                            help="Valor destinado ao parceiro/prospector",
                            key=f"valor_parceiro_rpv_{i+1}"
                        )
                        
                        # Outros valores
                        rpvs_data[rpv_key]['outros_valores'] = st.number_input(
                            "Outros valores (R$):",
                            min_value=0.0,
                            step=0.01,
                            format="%.2f",
                            help="Outros valores relacionados",
                            key=f"outros_valores_rpv_{i+1}"
                        )
                        
                        # Forma de pagamento
                        rpvs_data[rpv_key]['forma_pagamento'] = st.selectbox(
                            "Forma de pagamento ao cliente:",
                            options=["PIX", "Transferência", "Dinheiro"],
                            help="Forma como o pagamento será feito ao cliente",
                            key=f"forma_pagamento_rpv_{i+1}"
                        )
                    
                        # Observações sobre valores
                        rpvs_data[rpv_key]['observacoes_valores'] = st.text_area(
                            "Observações sobre valores:",
                            height=68,
                            help="Detalhes ou observações sobre os valores",
                            key=f"observacoes_valores_rpv_{i+1}"
                        )
                        
                        # Nova seção: Observações específicas para honorários contratuais
                        rpvs_data[rpv_key]['observacoes_hc'] = st.text_area(
                            "Observações honorários contratuais:",
                            height=68,
                            help="Observações específicas sobre honorários contratuais (consideradas antes do envio para Rodrigo)",
                            key=f"observacoes_hc_rpv_{i+1}"
                        )                    # Upload de PDF específico
                    rpvs_data[rpv_key]['pdf_rpv'] = st.file_uploader(
                        f"PDF do RPV {i+1}: *",
                        type=["pdf"],
                        key=f"pdf_rpv_{i+1}"
                    )
        else:
            # Caso seja apenas um RPV
            rpv_key = "rpv_1"
            if rpv_key not in rpvs_data:
                rpvs_data[rpv_key] = {}
            
            # Descrição do RPV (opcional para RPV único)
            rpvs_data[rpv_key]['descricao'] = st.text_input(
                "Descrição do RPV:",
                key="descricao_rpv_unico",
                help="Descrição específica deste RPV (opcional)"
            )
            
            # Seção de Valores Financeiros
            col2_1, col2_2 = st.columns(2)
            
            with col2_1:
                # Houve destaque de honorários (checkbox)
                rpvs_data[rpv_key]['houve_destaque_honorarios'] = st.checkbox(
                    "✅ Houve destaque de honorários",
                    value=False,
                    help="Marque se houve destaque de honorários",
                    key="new_rpv_destaque_honorarios"
                )
                
                # Valor do saque
                rpvs_data[rpv_key]['valor_saque'] = st.number_input(
                    "Valor do saque (R$): *",
                    min_value=0.0,
                    step=0.01,
                    format="%.2f",
                    help="Valor total do saque do RPV",
                    key="new_rpv_valor_saque"
                )
                
                # Honorários contratuais
                rpvs_data[rpv_key]['honorarios_contratuais'] = st.number_input(
                    "Honorários contratuais (R$):",
                    min_value=0.0,
                    step=0.01,
                    format="%.2f",
                    help="Valor dos honorários contratuais",
                    key="new_rpv_honorarios_contratuais"
                )
                
                # Honorários sucumbenciais
                rpvs_data[rpv_key]['h_sucumbenciais'] = st.number_input(
                    "H. Sucumbenciais (R$):",
                    min_value=0.0,
                    step=0.01,
                    format="%.2f",
                    help="Valor dos honorários sucumbenciais",
                    key="new_rpv_h_sucumbenciais"
                )
                
                # Valor cliente
                rpvs_data[rpv_key]['valor_cliente'] = st.number_input(
                    "Valor cliente (R$): *",
                    min_value=0.0,
                    step=0.01,
                    format="%.2f",
                    help="Valor destinado ao cliente",
                    key="new_rpv_valor_cliente"
                )
            
            with col2_2:
                # Valor parceiro/prospector
                rpvs_data[rpv_key]['valor_parceiro_prospector'] = st.number_input(
                    "Valor parceiro/prospector (R$):",
                    min_value=0.0,
                    step=0.01,
                    format="%.2f",
                    help="Valor destinado ao parceiro/prospector",
                    key="new_rpv_valor_parceiro"
                )
                
                # Outros valores
                rpvs_data[rpv_key]['outros_valores'] = st.number_input(
                    "Outros valores (R$):",
                    min_value=0.0,
                    step=0.01,
                    format="%.2f",
                    help="Outros valores relacionados",
                    key="new_rpv_outros_valores"
                )
                
                # Forma de pagamento
                rpvs_data[rpv_key]['forma_pagamento'] = st.selectbox(
                    "Forma de pagamento ao cliente:",
                    options=["PIX", "Transferência", "Dinheiro"],
                    help="Forma como o pagamento será feito ao cliente",
                    key="new_rpv_forma_pagamento"
                )
                
                # Valor de honorário sucumbencial (removido pois já existe H. Sucumbenciais)
                # rpvs_data[rpv_key]['valor_honorario_sucumbencial'] = st.number_input(
            
            # Observações sobre valores
            rpvs_data[rpv_key]['observacoes_valores'] = st.text_area(
                "Observações sobre valores:",
                height=68,
                help="Detalhes ou observações sobre os valores",
                key="new_rpv_observacoes_valores"
            )
            
            # Nova seção: Observações específicas para honorários contratuais
            rpvs_data[rpv_key]['observacoes_hc'] = st.text_area(
                "Observações honorários contratuais:",
                height=68,
                help="Observações específicas sobre honorários contratuais (consideradas antes do envio para Rodrigo)",
                key="new_rpv_observacoes_hc"
            )
            
            # Checkbox para anexar múltiplos PDFs
            anexar_multiplos_pdf = st.checkbox("Anexar múltiplos PDFs", key=multiplos_key)
            
            # Usar keys diferentes para múltiplos vs único para evitar conflitos
            if anexar_multiplos_pdf:
                rpvs_data[rpv_key]['pdf_rpv'] = st.file_uploader(
                    "PDFs do RPV: *",
                    type=["pdf"],
                    accept_multiple_files=True,
                    key="pdf_rpv_multiplos"
                )
                rpvs_data[rpv_key]['multiplos_pdfs'] = True
            else:
                rpvs_data[rpv_key]['pdf_rpv'] = st.file_uploader(
                    "PDF do RPV: *",
                    type=["pdf"],
                    key="pdf_rpv_unico"
                )
                rpvs_data[rpv_key]['multiplos_pdfs'] = False

    # ===== SEÇÃO DE RESUMO FINANCEIRO =====
    st.markdown("---")
    st.markdown("### 💰 Resumo Financeiro")
    
    # Cálculos para cada RPV
    resumo_total = {
        'total_saque': 0.0,
        'total_honorarios': 0.0,
        'total_parceiro': 0.0,
        'total_outros': 0.0,
        'total_cliente': 0.0,
        'total_escritorio': 0.0
    }
    
    for i in range(num_rpvs):
        rpv_key = f"rpv_{i+1}"
        if rpv_key in rpvs_data:
            dados_rpv = rpvs_data[rpv_key]
            
            # Obter valores (com fallback para 0.0 se não preenchido)
            valor_saque = dados_rpv.get('valor_saque', 0.0) or 0.0
            honorarios_contratuais = dados_rpv.get('honorarios_contratuais', 0.0) or 0.0
            h_sucumbenciais = dados_rpv.get('h_sucumbenciais', 0.0) or 0.0
            valor_parceiro = dados_rpv.get('valor_parceiro_prospector', 0.0) or 0.0
            outros_valores = dados_rpv.get('outros_valores', 0.0) or 0.0
            
            # Cálculos por RPV
            total_honorarios_rpv = honorarios_contratuais + h_sucumbenciais
            total_deducoes_rpv = total_honorarios_rpv + outros_valores
            total_cliente_rpv = valor_saque - total_deducoes_rpv
            total_escritorio_rpv = total_honorarios_rpv + outros_valores - valor_parceiro
            
            # Acumular totais
            resumo_total['total_saque'] += valor_saque
            resumo_total['total_honorarios'] += total_honorarios_rpv
            resumo_total['total_parceiro'] += valor_parceiro
            resumo_total['total_outros'] += outros_valores
            resumo_total['total_cliente'] += total_cliente_rpv
            resumo_total['total_escritorio'] += total_escritorio_rpv
            
            # Mostrar resumo individual se múltiplos RPVs
            if num_rpvs > 1:
                with st.expander(f"📊 Resumo RPV {i+1}", expanded=False):
                    col_res1, col_res2, col_res3 = st.columns(3)
                    
                    with col_res1:
                        st.metric(
                            "💰 Total pago ao cliente",
                            f"R$ {total_cliente_rpv:,.2f}",
                            help=f"Valor do saque (R$ {valor_saque:,.2f}) - Honorários e outros (R$ {total_deducoes_rpv:,.2f})"
                        )
                    
                    with col_res2:
                        st.metric(
                            "🏢 Total recebido pelo escritório",
                            f"R$ {total_escritorio_rpv:,.2f}",
                            help=f"Honorários e outros (R$ {total_honorarios_rpv + outros_valores:,.2f}) - Parceiro/prospector (R$ {valor_parceiro:,.2f})"
                        )
                    
                    with col_res3:
                        st.metric(
                            "🤝 Total pago a parceiro/prospector",
                            f"R$ {valor_parceiro:,.2f}"
                        )
    
    # Resumo consolidado
    col_res1, col_res2, col_res3 = st.columns(3)
    
    with col_res1:
        st.metric(
            "💰 Total pago ao cliente",
            f"R$ {resumo_total['total_cliente']:,.2f}",
            help=f"Soma dos valores líquidos para todos os clientes"
        )
    
    with col_res2:
        st.metric(
            "🏢 Total recebido pelo escritório",
            f"R$ {resumo_total['total_escritorio']:,.2f}",
            help=f"Soma dos valores líquidos para o escritório"
        )
    
    with col_res3:
        st.metric(
            "🤝 Total pago a parceiro/prospector",
            f"R$ {resumo_total['total_parceiro']:,.2f}",
            help=f"Soma dos valores para parceiros/prospectores"
        )

    # Botão de submissão fora do formulário
    if st.button("📝 Adicionar RPVs", type="primary", use_container_width=True):
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
        
        # Processar vara
        if vara_selecionada and len(vara_selecionada) > 0:
            vara_processada = normalizar_vara_rpv(vara_selecionada)
            varas_existentes = obter_varas_rpv()
            if vara_processada and vara_processada not in varas_existentes:
                if adicionar_vara_rpv(vara_processada):
                    st.success(f"🆕 Nova vara '{vara_processada}' salva permanentemente!")
            vara_final = vara_processada
        
        # =====================================
        # VALIDAÇÃO COMPLETA DE CAMPOS OBRIGATÓRIOS COMUNS
        # =====================================
        
        campos_vazios = []
        
        # Validar campos de texto obrigatórios comuns
        if not processo or processo.strip() == "":
            campos_vazios.append("Número do Processo Principal")
        if not beneficiario or beneficiario.strip() == "":
            campos_vazios.append("Beneficiário")
        if not cpf or cpf.strip() == "":
            campos_vazios.append("CPF")
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
        
        # =====================================
        # VALIDAÇÃO ESPECÍFICA DOS RPVs
        # =====================================
        
        rpvs_validos = []
        for i in range(num_rpvs):
            rpv_key = f"rpv_{i+1}"
            if rpv_key in rpvs_data:
                rpv_data = rpvs_data[rpv_key]
                rpv_errors = []
                
                # Validar descrição para múltiplos RPVs
                if multiplos_rpvs and (not rpv_data.get('descricao') or rpv_data.get('descricao', '').strip() == ''):
                    rpv_errors.append(f"Descrição do RPV {i+1}")
                
                # Validar valor cliente obrigatório
                if rpv_data.get('valor_cliente', 0) <= 0.0:
                    rpv_errors.append(f"Valor cliente do RPV {i+1}")
                
                # Validar PDF
                pdf_rpv = rpv_data.get('pdf_rpv')
                if multiplos_rpvs:
                    if not pdf_rpv:
                        rpv_errors.append(f"PDF do RPV {i+1}")
                else:
                    # Para RPV único, verificar se há múltiplos PDFs ou único
                    multiplos_pdfs = rpv_data.get('multiplos_pdfs', False)
                    if multiplos_pdfs:
                        if not pdf_rpv or len(pdf_rpv) == 0:
                            rpv_errors.append("PDFs do RPV")
                    else:
                        if not pdf_rpv:
                            rpv_errors.append("PDF do RPV")
                
                if rpv_errors:
                    campos_vazios.extend(rpv_errors)
                else:
                    rpvs_validos.append((rpv_key, rpv_data))
        
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
                # =====================================
                # CRIAR LINHAS PARA CADA RPV VÁLIDO
                # =====================================
                
                novas_linhas = []
                for rpv_index, (rpv_key, rpv_data) in enumerate(rpvs_validos):
                    
                    # NOVO FLUXO: Status inicial é Cadastro, que depois se transforma nos dois status simultâneos
                    status_inicial = "Cadastro"
                    
                    # Criar número do processo específico para cada RPV
                    if multiplos_rpvs and len(rpvs_validos) > 1:
                        processo_especifico = f"{processo_formatado}-{rpv_index + 1}"
                    else:
                        processo_especifico = processo_formatado
                    
                    # Salvar PDF(s)
                    pdf_rpv = rpv_data.get('pdf_rpv')
                    if multiplos_rpvs or not rpv_data.get('multiplos_pdfs', False):
                        # Salvar arquivo único
                        pdf_url = salvar_arquivo(pdf_rpv, processo_especifico, f"rpv")
                    else:
                        # Salvar múltiplos arquivos (apenas para RPV único com múltiplos PDFs)
                        pdf_urls = []
                        for i, arquivo in enumerate(pdf_rpv):
                            url = salvar_arquivo(arquivo, processo_especifico, f"rpv_{i+1}")
                            pdf_urls.append(url)
                        pdf_url = "; ".join(pdf_urls)
                    
                    # Criar nova linha
                    nova_linha = {
                        "ID": gerar_id_unico(st.session_state.df_editado_rpv, "ID"),
                        "Processo": processo_especifico,
                        "Beneficiário": beneficiario,
                        "CPF": cpf,
                        
                        # Nova coluna: Descrição do RPV
                        "Descricao RPV": rpv_data.get('descricao', ''),
                        
                        # Campos de valores específicos
                        "Houve Destaque Honorarios": "Sim" if rpv_data.get('houve_destaque_honorarios', False) else "Não",
                        "Valor Saque": rpv_data.get('valor_saque', 0.0),  # Nova coluna
                        "Honorarios Contratuais": rpv_data.get('honorarios_contratuais', 0.0),
                        "H Sucumbenciais": rpv_data.get('h_sucumbenciais', 0.0),  # Nova coluna
                        "Valor Cliente": rpv_data.get('valor_cliente', 0.0),
                        "Valor Parceiro Prospector": rpv_data.get('valor_parceiro_prospector', 0.0),
                        "Outros Valores": rpv_data.get('outros_valores', 0.0),
                        "Forma Pagamento": rpv_data.get('forma_pagamento', 'PIX'),  # Nova coluna
                        "Observacoes Gerais": rpv_data.get('observacoes_valores', ''),  # Nova coluna (renomeada)
                        "Observacoes Honorarios Contratuais": rpv_data.get('observacoes_hc', ''),
                        
                        "Banco": banco_rpv,
                        "Assunto": assunto_final,
                        "Orgao Judicial": orgao_final,
                        "Vara": vara_final if vara_final else "",
                        "Mês Competência": mes_competencia if mes_competencia else "",
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
                    
                    novas_linhas.append(nova_linha)
                
                # Adicionar todas as linhas ao DataFrame em memória
                for nova_linha in novas_linhas:
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
                keys_to_clear = [processo_key, beneficiario_key, cpf_key, obs_key, competencia_key,
                               certidao_key, multiplos_key, "new_rpv_banco", "multiplos_rpvs_checkbox", "num_rpvs_input",
                               "descricao_rpv_unico", "new_rpv_destaque_honorarios", 
                               "new_rpv_valor_saque", "new_rpv_honorarios_contratuais", "new_rpv_h_sucumbenciais",
                               "new_rpv_valor_cliente", "new_rpv_valor_parceiro", "new_rpv_outros_valores",
                               "new_rpv_forma_pagamento", "new_rpv_observacoes_valores", "new_rpv_observacoes_hc",
                               "select_new_rpv_assunto", "input_novo_new_rpv_assunto",
                               "select_new_rpv_orgao", "input_novo_new_rpv_orgao",
                               "select_new_rpv_vara", "input_nova_new_rpv_vara",
                               "pdf_rpv_unico", "pdf_rpv_multiplos"]
                
                # Limpar campos específicos dos RPVs múltiplos
                for i in range(10):  # Limpar até 10 RPVs
                    keys_to_clear.extend([
                        f"descricao_rpv_{i+1}",
                        f"destaque_honorarios_rpv_{i+1}",
                        f"valor_saque_rpv_{i+1}",
                        f"honorarios_contratuais_rpv_{i+1}",
                        f"h_sucumbenciais_rpv_{i+1}",
                        f"valor_cliente_rpv_{i+1}",
                        f"valor_parceiro_rpv_{i+1}",
                        f"outros_valores_rpv_{i+1}",
                        f"forma_pagamento_rpv_{i+1}",
                        f"observacoes_valores_rpv_{i+1}",
                        f"observacoes_hc_rpv_{i+1}",
                        f"pdf_rpv_{i+1}"
                    ])
                
                # Limpar session state
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                
                # Limpar dados temporários dos RPVs
                keys_to_remove = [k for k in st.session_state.keys() if k.startswith("rpvs_data_")]
                for key in keys_to_remove:
                    del st.session_state[key]
                
                num_linhas_adicionadas = len(novas_linhas)
                if num_linhas_adicionadas == 1:
                    st.success("✅ RPV adicionado! Salve para persistir os dados.")
                else:
                    st.success(f"✅ {num_linhas_adicionadas} RPVs adicionados! Salve para persistir os dados.")
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

def interface_relatorio_certidao_rpv(df):
    """Interface para gerar relatório de certidão de RPVs em formato de tabela clássica."""
    
    # LIMPAR ESTADOS DE DIÁLOGO ao entrar na aba de relatório
    limpar_estados_dialog_rpv()
    
    if df.empty:
        st.info("ℹ️ Não há RPVs cadastrados para gerar o relatório.")
        return

    st.markdown("### 📊 Relatório de Certidão - RPVs")
    
    # Filtros no topo
    col_filtro1, col_filtro2, col_filtro3, col_filtro4 = st.columns(4)
    
    with col_filtro1:
        # Filtro de data de cadastro (intervalo)
        st.markdown("**📅 Intervalo de Data de Cadastro:**")
        data_inicio = st.date_input(
            "Data início:",
            value=None,
            key="relatorio_rpv_data_inicio"
        )
        data_fim = st.date_input(
            "Data fim:",
            value=None,
            key="relatorio_rpv_data_fim"
        )
    
    with col_filtro2:
        # Filtro de Certidão (checkboxes separados)
        st.markdown("**📋 Certidão:**")
        
        col_cert1, col_cert2 = st.columns(2)
        with col_cert1:
            incluir_sim = st.checkbox(
                "✅ Sim",
                value=True,
                key="relatorio_rpv_cert_sim"
            )
        with col_cert2:
            incluir_nao = st.checkbox(
                "❌ Não", 
                value=True,
                key="relatorio_rpv_cert_nao"
            )
        
        # Construir lista de opções baseada nos checkboxes
        certidao_options = []
        if incluir_sim:
            certidao_options.append("Sim")
        if incluir_nao:
            certidao_options.append("Não")
    
    with col_filtro3:
        # Filtro de Status
        status_unicos = ["Todos"] + sorted(list(df["Status"].dropna().unique())) if "Status" in df.columns else ["Todos"]
        status_filtro = st.selectbox(
            "📊 Status:",
            options=status_unicos,
            key="relatorio_rpv_status"
        )
    
    with col_filtro4:
        # Filtro de busca livre
        pesquisa = st.text_input(
            "🔎 Pesquisar:",
            placeholder="Processo, beneficiário, CPF...",
            key="relatorio_rpv_pesquisa"
        )

    # Aplicar filtros
    df_filtrado = df.copy()
    
    # Filtro de data de cadastro
    if data_inicio or data_fim:
        if "Data Cadastro" in df.columns:
            # Converter coluna de data para datetime
            df_filtrado["Data Cadastro Parsed"] = pd.to_datetime(
                df_filtrado["Data Cadastro"], 
                format="%d/%m/%Y %H:%M", 
                errors="coerce"
            )
            
            if data_inicio:
                data_inicio_dt = pd.to_datetime(data_inicio)
                df_filtrado = df_filtrado[df_filtrado["Data Cadastro Parsed"] >= data_inicio_dt]
            
            if data_fim:
                data_fim_dt = pd.to_datetime(data_fim) + pd.Timedelta(days=1)
                df_filtrado = df_filtrado[df_filtrado["Data Cadastro Parsed"] < data_fim_dt]
    
    # Filtro de certidão
    if certidao_options and "Solicitar Certidão" in df.columns:
        df_filtrado = df_filtrado[df_filtrado["Solicitar Certidão"].isin(certidao_options)]
    
    # Filtro de status
    if status_filtro != "Todos" and "Status" in df.columns:
        df_filtrado = df_filtrado[df_filtrado["Status"] == status_filtro]
    
    # Filtro de pesquisa
    if pesquisa:
        mask = pd.Series([False] * len(df_filtrado))
        colunas_pesquisa = ["Processo", "Beneficiário", "CPF"]
        for col in colunas_pesquisa:
            if col in df_filtrado.columns:
                mask |= df_filtrado[col].astype(str).str.contains(pesquisa, case=False, na=False)
        df_filtrado = df_filtrado[mask]

    st.markdown("---")

    # Botões de exportação
    if not df_filtrado.empty:
        # Preparar dados para exportação (selecionar colunas relevantes)
        colunas_relatorio = [
            "Processo", "Beneficiário", "CPF", "Orgao Judicial", "Valor Cliente", "Status"
        ]
        
        # Verificar quais colunas existem
        colunas_disponiveis = [col for col in colunas_relatorio if col in df_filtrado.columns]
        
        # Adicionar colunas alternativas se as principais não existirem
        if "Orgao Judicial" not in df_filtrado.columns and "Órgão Judicial" in df_filtrado.columns:
            colunas_disponiveis = [col.replace("Orgao Judicial", "Órgão Judicial") for col in colunas_disponiveis]
        
        if "Valor Cliente" not in df_filtrado.columns and "Valor RPV" in df_filtrado.columns:
            colunas_disponiveis = [col.replace("Valor Cliente", "Valor RPV") for col in colunas_disponiveis]
        
        # Se não encontramos nenhuma coluna específica, usar todas as disponíveis
        if not colunas_disponiveis and not df_filtrado.empty:
            colunas_disponiveis = df_filtrado.columns.tolist()
        
        # Criar DataFrame para exportação
        if colunas_disponiveis:
            df_exportacao = df_filtrado[colunas_disponiveis].copy()
        else:
            # DataFrame vazio mas com estrutura
            df_exportacao = pd.DataFrame()
        
        # Renomear colunas para o relatório
        rename_dict = {
            "Processo": "Número do Processo",
            "Orgao Judicial": "Órgão Banco",
            "Órgão Judicial": "Órgão Banco",
            "Valor RPV": "Valor Total",
            "Valor Cliente": "Valor Total"
        }
        
        # Renomear colunas apenas se temos dados
        if not df_exportacao.empty:
            df_exportacao.rename(columns=rename_dict, inplace=True)
        
        col_export1, col_export2, col_export3 = st.columns([2, 2, 6])
        
        with col_export1:
            # Exportar Excel
            from io import BytesIO
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_exportacao.to_excel(writer, index=False, sheet_name='Relatório Certidão RPV')
                
                # Formatação do Excel
                workbook = writer.book
                worksheet = writer.sheets['Relatório Certidão RPV']
                
                # Formato para cabeçalho
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#4472C4',
                    'font_color': 'white',
                    'border': 1
                })
                
                # Aplicar formato ao cabeçalho
                for col_num, value in enumerate(df_exportacao.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Ajustar largura das colunas
                for i, col in enumerate(df_exportacao.columns):
                    max_length = max(
                        df_exportacao[col].astype(str).str.len().max(),
                        len(col)
                    )
                    worksheet.set_column(i, i, min(max_length + 2, 50))
            
            excel_data = output.getvalue()
            
            st.download_button(
                label="📊 Exportar Excel",
                data=excel_data,
                file_name=f"relatorio_certidao_rpv_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        with col_export2:
            # Exportar PDF
            try:
                from reportlab.lib import colors
                from reportlab.lib.pagesizes import letter, A4
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                
                # Criar PDF em memória
                pdf_buffer = BytesIO()
                doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, topMargin=1*inch)
                
                # Estilos
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=16,
                    spaceAfter=30,
                    alignment=1  # Centro
                )
                
                # Elementos do PDF
                elements = []
                
                # Título
                title = Paragraph("Relatório de Certidão - RPVs", title_style)
                elements.append(title)
                
                # Data de geração
                data_geracao = Paragraph(
                    f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
                    styles['Normal']
                )
                elements.append(data_geracao)
                elements.append(Spacer(1, 20))
                
                # Resumo
                resumo = Paragraph(
                    f"Total de registros: {len(df_exportacao)}",
                    styles['Normal']
                )
                elements.append(resumo)
                elements.append(Spacer(1, 20))
                
                # Tabela
                if len(df_exportacao) > 0 and len(df_exportacao.columns) > 0:
                    # Preparar dados da tabela
                    data = [df_exportacao.columns.tolist()]
                    for _, row in df_exportacao.iterrows():
                        # Truncar textos muito longos
                        row_data = []
                        for item in row:
                            item_str = str(item)
                            if len(item_str) > 30:
                                item_str = item_str[:27] + "..."
                            row_data.append(item_str)
                        data.append(row_data)
                    
                    # Verificar se temos dados válidos para a tabela
                    if data and len(data) > 0 and len(data[0]) > 0:
                        # Criar tabela
                        table = Table(data)
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 10),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                            ('FONTSIZE', (0, 1), (-1, -1), 8),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        elements.append(table)
                    else:
                        # Adicionar mensagem quando dados não são adequados para tabela
                        sem_dados_validos = Paragraph(
                            "Dados não adequados para exibição em tabela.",
                            styles['Normal']
                        )
                        elements.append(sem_dados_validos)
                else:
                    # Adicionar mensagem quando não há dados para a tabela
                    sem_dados = Paragraph(
                        "Nenhum dado disponível para exibir na tabela.",
                        styles['Normal']
                    )
                    elements.append(sem_dados)
                
                # Gerar PDF
                doc.build(elements)
                pdf_data = pdf_buffer.getvalue()
                
                st.download_button(
                    label="📄 Exportar PDF",
                    data=pdf_data,
                    file_name=f"relatorio_certidao_rpv_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
            except ImportError:
                st.warning("⚠️ Para exportar PDF, instale: pip install reportlab")
        
        with col_export3:
            st.info(f"📋 {len(df_filtrado)} registros encontrados")

    # Tabela com AgGrid
    st.markdown(f"### 📋 Tabela de Dados ({len(df_filtrado)} registros)")
    
    if not df_filtrado.empty:
        # Preparar dados para AgGrid
        df_display = df_filtrado.copy()
        
        # Selecionar e renomear colunas para o relatório
        colunas_relatorio = {
            'Processo': 'Número do Processo',
            'Beneficiário': 'Beneficiário',
            'CPF': 'CPF',
            'Orgao Judicial': 'Órgão Judicial',
            'Valor Cliente': 'Valor Total (R$)',
            'Status': 'Status',
            'Solicitar Certidão': 'Certidão',
            'Data Cadastro': 'Data Cadastro'
        }
        
        # Verificar colunas alternativas
        if 'Orgao Judicial' not in df_display.columns and 'Órgão Judicial' in df_display.columns:
            colunas_relatorio['Órgão Judicial'] = 'Órgão Judicial'
            del colunas_relatorio['Orgao Judicial']
            
        if 'Valor Cliente' not in df_display.columns and 'Valor RPV' in df_display.columns:
            colunas_relatorio['Valor RPV'] = 'Valor Total (R$)'
            del colunas_relatorio['Valor Cliente']
        
        # Filtrar apenas colunas existentes
        colunas_existentes = {k: v for k, v in colunas_relatorio.items() if k in df_display.columns}
        df_display = df_display[list(colunas_existentes.keys())].rename(columns=colunas_existentes)
        
        # Formatar valores monetários
        if 'Valor Total (R$)' in df_display.columns:
            df_display['Valor Total (R$)'] = df_display['Valor Total (R$)'].apply(
                lambda x: f"R$ {float(x):,.2f}" if pd.notna(x) and str(x).replace('.', '').replace(',', '').replace('-', '').isdigit() else str(x)
            )
        
        # Formatar datas
        if 'Data Cadastro' in df_display.columns:
            df_display['Data Cadastro'] = df_display['Data Cadastro'].apply(
                lambda x: str(x).split(' ')[0] if pd.notna(x) else 'N/A'
            )
        
        # Configurar AgGrid
        gb = GridOptionsBuilder.from_dataframe(df_display)
        
        # Configurações gerais
        gb.configure_default_column(
            groupable=False,
            value=True,
            enableRowGroup=False,
            aggFunc="sum",
            editable=False,
            filterable=True,
            sortable=True,
            resizable=True
        )
        
        # Configurar colunas específicas
        if 'Número do Processo' in df_display.columns:
            gb.configure_column("Número do Processo", width=200, pinned='left')
        if 'Beneficiário' in df_display.columns:
            gb.configure_column("Beneficiário", width=250)
        if 'CPF' in df_display.columns:
            gb.configure_column("CPF", width=140)
        if 'Órgão Judicial' in df_display.columns:
            gb.configure_column("Órgão Judicial", width=200)
        if 'Valor Total (R$)' in df_display.columns:
            gb.configure_column("Valor Total (R$)", width=150, type="numericColumn")
        if 'Status' in df_display.columns:
            gb.configure_column("Status", width=130)
        if 'Certidão' in df_display.columns:
            gb.configure_column("Certidão", width=100)
        if 'Data Cadastro' in df_display.columns:
            gb.configure_column("Data Cadastro", width=120)
        
        # Configurações de paginação e seleção
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=25)
        gb.configure_side_bar()
        
        # Só configurar seleção se temos colunas no DataFrame
        if not df_display.empty and len(df_display.columns) > 0:
            gb.configure_selection(selection_mode="multiple", use_checkbox=True)
        
        # Tema
        gb.configure_grid_options(
            enableRangeSelection=True,
            domLayout='normal'
        )
        
        grid_options = gb.build()
        
        # Renderizar AgGrid
        grid_response = AgGrid(
            df_display,
            gridOptions=grid_options,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            fit_columns_on_grid_load=True,
            theme='streamlit',
            height=600,
            width='100%',
            reload_data=False
        )
        
        # Informações sobre seleção
        selected_rows = grid_response['selected_rows']
        if selected_rows is not None and len(selected_rows) > 0:
            st.info(f"✅ {len(selected_rows)} linha(s) selecionada(s)")
            
            # Opção para exportar apenas as linhas selecionadas
            col_sel1, col_sel2 = st.columns(2)
            with col_sel1:
                if st.button("� Baixar Selecionados (Excel)", key="export_selected_excel"):
                    df_selected = pd.DataFrame(selected_rows)
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_selected.to_excel(writer, index=False, sheet_name='Selecionados')
                    excel_data = output.getvalue()
                    st.download_button(
                        label="📊 Download Excel Selecionados",
                        data=excel_data,
                        file_name=f"rpvs_selecionados_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_selected_excel"
                    )
            
            with col_sel2:
                if st.button("📥 Baixar Selecionados (CSV)", key="export_selected_csv"):
                    df_selected = pd.DataFrame(selected_rows)
                    csv_data = df_selected.to_csv(index=False, sep=';').encode('utf-8')
                    st.download_button(
                        label="📥 Download CSV Selecionados",
                        data=csv_data,
                        file_name=f"rpvs_selecionados_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        key="download_selected_csv"
                    )
        
        # Informações adicionais
        st.markdown("---")
        col_info1, col_info2, col_info3 = st.columns(3)
        
        with col_info1:
            # Contagem por status
            status_counts = df_filtrado["Status"].value_counts() if "Status" in df_filtrado.columns else pd.Series()
            st.markdown("**📊 Por Status:**")
            for status, count in status_counts.items():
                st.write(f"• {status}: {count}")
        
        with col_info2:
            # Contagem por certidão
            if "Solicitar Certidão" in df_filtrado.columns:
                certidao_counts = df_filtrado["Solicitar Certidão"].value_counts()
                st.markdown("**📋 Por Certidão:**")
                for certidao, count in certidao_counts.items():
                    st.write(f"• {certidao}: {count}")
        
        with col_info3:
            # Valor total
            valor_total = 0
            valor_col = None
            if "Valor Cliente" in df_filtrado.columns:
                valor_col = "Valor Cliente"
            elif "Valor RPV" in df_filtrado.columns:
                valor_col = "Valor RPV"
            
            if valor_col:
                try:
                    df_filtrado[valor_col] = pd.to_numeric(df_filtrado[valor_col], errors='coerce')
                    valor_total = df_filtrado[valor_col].sum()
                    st.markdown("**💰 Valor Total:**")
                    st.write(f"R$ {valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                except:
                    st.markdown("**💰 Valor Total:**")
                    st.write("Não calculável")
    
    else:
        st.info("📭 Nenhum registro encontrado com os filtros aplicados.")
