# components/funcoes_rpv.py
import streamlit as st
import pandas as pd
import requests
import base64
import math
import re
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

# =====================================
# CONFIGURAÇÕES DE PERFIS - RPV
# =====================================

# a) Novos Status
STATUS_ETAPAS_RPV = {
    1: "Enviado ao Financeiro", 
    2: "Aguardando Certidão",
    3: "Aguardando Pagamento",
    4: "Pagamento Atrasado",
    5: "Finalizado"
}

# b) Novas Permissões de Edição por Perfil
PERFIS_RPV = {
    "Cadastrador": [], # Cadastrador apenas cria, não edita RPVs no fluxo.
    "Jurídico": ["Aguardando Certidão"],
    "Financeiro": ["Enviado ao Financeiro", "Aguardando Pagamento", "Pagamento Atrasado"],
    "Admin": ["Enviado ao Financeiro", "Aguardando Certidão", "Aguardando Pagamento", "Pagamento Atrasado", "Finalizado"]  # Admin tem acesso total
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
    """Verifica se o usuário pode editar determinado status RPV"""
    return status_atual in PERFIS_RPV.get(perfil_usuario, [])

def obter_colunas_controle_rpv():
    """Retorna lista das colunas de controle do fluxo RPV"""
    return [
        "Assunto", "Solicitar Certidão", "Status", "Data Cadastro", "Cadastrado Por", 
        "PDF RPV", "Data Envio", "Enviado Por", "Mês Competência",
        "Certidão Anexada", "Data Certidão", "Anexado Certidão Por",
        "Documentação Organizada", "Certidão no Korbil", 
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
    
    # Verificação mais robusta de permissão para exclusão
    pode_excluir = (
        perfil_atual in ["Admin", "Cadastrador"] or 
        usuario_atual == "admin" or
        perfil_usuario in ["Admin", "Cadastrador"]  # usar o perfil passado como parâmetro
    )
    
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
            if st.session_state.modo_exclusao_rpv:
                num_selecionados = len(st.session_state.processos_selecionados_rpv)
                if num_selecionados > 0:
                    if st.button(f"🗑️ Excluir ({num_selecionados})", 
                               key="confirmar_exclusao_rpv", type="primary"):
                        confirmar_exclusao_massa_rpv(df, st.session_state.processos_selecionados_rpv)
                else:
                    # Mostrar mensagem quando nenhum item está selecionado
                    st.write("*Selecione itens para excluir*")

    # Filtros
    col_filtro1, col_filtro2, col_filtro3, col_filtro4, col_filtro5 = st.columns(5)
    
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
            "📅 Filtrar por Mês de Competência:",
            meses_disponiveis,
            key="rpv_mes_filter"
        )
    
    with col_filtro3:
        # Filtro por assunto
        # Filtro de assunto: combina assuntos salvos + assuntos únicos do DataFrame
        assuntos_salvos = obter_assuntos_rpv()  # Inclui novos assuntos salvos
        assuntos_disponiveis = ["Todos"] + assuntos_salvos
        
        # Também incluir assuntos únicos do DataFrame atual (caso não estejam salvos ainda)
        if "Assunto" in df.columns:
            assuntos_df = df["Assunto"].dropna().unique()
            assuntos_df = [a for a in assuntos_df if a and str(a) != 'nan']
            # Adiciona assuntos do DF que não estão na lista salva
            for assunto in assuntos_df:
                if assunto not in assuntos_disponiveis:
                    assuntos_disponiveis.append(assunto)
        
        assuntos_disponiveis = sorted(set(assuntos_disponiveis))  # Remove duplicatas e ordena
        assuntos_disponiveis = ["Todos"] + [a for a in assuntos_disponiveis if a != "Todos"]  # Garante "Todos" no início
        
        assunto_filtro = st.selectbox(
            "Filtrar por Assunto:",
            assuntos_disponiveis,
            key="rpv_assunto_filter"
        )
    
    with col_filtro4:
        # Filtro de órgão: combina órgãos salvos + órgãos únicos do DataFrame
        orgaos_salvos = obter_orgaos_rpv()  # Inclui novos órgãos salvos
        orgaos_disponiveis = ["Todos"] + orgaos_salvos
        
        # Também incluir órgãos únicos do DataFrame atual (caso não estejam salvos ainda)
        if "Orgao Judicial" in df.columns:
            orgaos_df = df["Orgao Judicial"].dropna().unique()
            orgaos_df = [o for o in orgaos_df if o and str(o) != 'nan']
            # Adiciona órgãos do DF que não estão na lista salva
            for orgao in orgaos_df:
                if orgao not in orgaos_disponiveis:
                    orgaos_disponiveis.append(orgao)
        
        orgaos_disponiveis = sorted(set(orgaos_disponiveis))  # Remove duplicatas e ordena
        orgaos_disponiveis = ["Todos"] + [o for o in orgaos_disponiveis if o != "Todos"]  # Garante "Todos" no início
        
        orgao_filtro = st.selectbox(
            "Filtrar por Órgão:",
            orgaos_disponiveis,
            key="rpv_orgao_filter"
        )
    
    with col_filtro5:
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
    
    # Filtro por assunto
    if assunto_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Assunto"] == assunto_filtro]
    
    # Filtro por órgão
    if orgao_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Orgao Judicial"] == orgao_filtro]
    
    if mostrar_apenas_meus:
        if perfil_usuario == "Jurídico":
            df_filtrado = df_filtrado[
                (df_filtrado["Solicitar Certidão"] == "Sim") &
                (df_filtrado["Status"].isin(["Enviado ao Financeiro", "Aguardando Certidão"]))
            ]
        elif perfil_usuario == "Financeiro":
            df_filtrado = df_filtrado[df_filtrado["Status"].isin(["Enviado ao Financeiro", "Aguardando Pagamento", "Pagamento Atrasado"])]

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
                    # Seguir o padrão dos outros sistemas (alvarás/benefícios)
                    rpv_id_str = str(rpv_id)
                    current_value = rpv_id_str in [str(pid) for pid in st.session_state.processos_selecionados_rpv]
                    
                    is_selected = st.checkbox(
                        "",
                        value=current_value,
                        key=f"check_rpv_{rpv_id}",
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
                    cor = {"Enviado ao Financeiro": "🟠", "Aguardando Certidão": "🔵", "Aguardando Pagamento": "�", "Pagamento Atrasado": "�", "Finalizado": "🟢"}.get(status_atual, "⚫")
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
                    cor = {"Enviado ao Financeiro": "🟠", "Aguardando Certidão": "🔵", "Aguardando Pagamento": "�", "Pagamento Atrasado": "�", "Finalizado": "🟢"}.get(status_atual, "⚫")
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

def safe_get_value(data, key, default='Não cadastrado'):
    """Obtém valor de forma segura, tratando NaN e valores None"""
    value = data.get(key, default)
    if value is None:
        return default
    # Converter para string e verificar se não é 'nan'
    str_value = str(value)
    if str_value.lower() in ['nan', 'none', '']:
        return default
    return str_value

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
        background: white;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
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
            <div class="compact-label">💰 VALOR</div>
            <div class="compact-value">{safe_get_value(linha_rpv, 'Valor RPV')}</div>
        </div>
        <div class="compact-item">
            <div class="compact-label">🏛️ ÓRGÃO</div>
            <div class="compact-value">{safe_get_value(linha_rpv, 'Orgao Judicial')[:20]}...</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

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
    """Interface de edição completamente redesenhada para o novo fluxo de RPV."""
    
    linha_rpv = df[df["ID"] == rpv_id].iloc[0]
    numero_processo = linha_rpv.get("Processo", "N/A")
    
    # Exibir informações básicas do processo com layout compacto
    exibir_informacoes_basicas_rpv(linha_rpv, "compacto")
    
    # Verificar permissão de edição - Admin tem acesso total
    if perfil_usuario != "Admin" and not pode_editar_status_rpv(status_atual, perfil_usuario):
        st.error(f"❌ Seu perfil ({perfil_usuario}) não pode editar RPVs com status '{status_atual}'.")
        # Mensagens de ajuda mais claras
        if perfil_usuario == "Jurídico":
            st.info("💡 O Jurídico só pode atuar em RPVs com status 'Aguardando Certidão'.")
        elif perfil_usuario == "Financeiro":
            st.info("💡 O Financeiro atua em RPVs com status 'Enviado ao Financeiro', 'Aguardando Pagamento' e 'Pagamento Atrasado'.")
        else:
            st.info("💡 Apenas Jurídico e Financeiro podem editar RPVs após o cadastro.")
        return
    
    # --- SEÇÃO ESPECIAL PARA ADMIN ---
    if perfil_usuario == "Admin":
        st.markdown("#### 🔧 Acesso de Administrador")
        st.info(f"Como Admin, você pode editar este RPV independente do status atual: **{status_atual}**")
        
        # Admin pode executar ações de qualquer perfil
        col_admin1, col_admin2 = st.columns(2)
        
        with col_admin1:
            st.markdown("**Ações do Financeiro:**")
            if status_atual == "Enviado ao Financeiro":
                doc_ok = st.checkbox("✅ Documentação organizada", key=f"admin_doc_{rpv_id}")
                solicitar_certidao = linha_rpv.get("Solicitar Certidão", "Não")
                
                if doc_ok:
                    if solicitar_certidao == "Sim":
                        if st.button("📋 → Aguardando Certidão", key=f"admin_cert_{rpv_id}"):
                            idx = df[df["ID"] == rpv_id].index[0]
                            st.session_state.df_editado_rpv.loc[idx, "Status"] = "Aguardando Certidão"
                            st.session_state.df_editado_rpv.loc[idx, "Documentação Organizada"] = "Sim"
                            save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                            st.session_state.show_rpv_dialog = False
                            st.success("✅ Status atualizado!")
                            st.rerun()
                    else:
                        if st.button("💰 → Aguardando Pagamento", key=f"admin_pag_{rpv_id}"):
                            idx = df[df["ID"] == rpv_id].index[0]
                            st.session_state.df_editado_rpv.loc[idx, "Status"] = "Aguardando Pagamento"
                            st.session_state.df_editado_rpv.loc[idx, "Documentação Organizada"] = "Sim"
                            save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                            st.session_state.show_rpv_dialog = False
                            st.success("✅ Status atualizado!")
                            st.rerun()
        
        with col_admin2:
            st.markdown("**Ações do Jurídico:**")
            if status_atual == "Aguardando Certidão":
                certidao_ok = st.checkbox("✅ Certidão no Korbil", key=f"admin_korbil_{rpv_id}")
                if certidao_ok:
                    if st.button("💰 → Aguardando Pagamento", key=f"admin_jur_pag_{rpv_id}"):
                        idx = df[df["ID"] == rpv_id].index[0]
                        st.session_state.df_editado_rpv.loc[idx, "Status"] = "Aguardando Pagamento"
                        st.session_state.df_editado_rpv.loc[idx, "Certidão no Korbil"] = "Sim"
                        save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                        st.session_state.show_rpv_dialog = False
                        st.success("✅ Status atualizado!")
                        st.rerun()
        
        # Finalização para Admin
        if status_atual in ["Aguardando Pagamento", "Pagamento Atrasado"]:
            st.markdown("**Finalização do Processo:**")
            
            col_fin1, col_fin2 = st.columns(2)
            with col_fin1:
                comp_admin = st.file_uploader("Comprovante", type=["pdf", "png", "jpg"], key=f"admin_comp_{rpv_id}")
            with col_fin2:
                valor_admin = st.number_input("Valor Líquido (R$)", min_value=0.0, format="%.2f", key=f"admin_valor_{rpv_id}")
                obs_admin = st.text_area("Observações", key=f"admin_obs_{rpv_id}")
            
            if comp_admin and valor_admin > 0:
                if st.button("✅ Finalizar RPV (Admin)", type="primary"):
                    idx = df[df["ID"] == rpv_id].index[0]
                    st.session_state.df_editado_rpv.loc[idx, "Status"] = "Finalizado"
                    st.session_state.df_editado_rpv.loc[idx, "Valor Líquido"] = valor_admin
                    st.session_state.df_editado_rpv.loc[idx, "Observações Pagamento"] = obs_admin
                    st.session_state.df_editado_rpv.loc[idx, "Comprovante Pagamento"] = "Arquivo anexado"
                    save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                    st.session_state.show_rpv_dialog = False
                    st.success("✅ RPV finalizado!")
                    st.rerun()
        
        st.markdown("---")

    # --- ETAPA 1: Ação do Financeiro ---
    if status_atual == "Enviado ao Financeiro" and perfil_usuario in ["Financeiro", "Admin"]:
        st.markdown("#### Ação do Financeiro")
        
        # Verificar se precisa de certidão
        solicitar_certidao = linha_rpv.get("Solicitar Certidão", "Não")
        
        if solicitar_certidao == "Sim":
            st.info("📋 Este RPV requer certidão. O processo será direcionado para o jurídico após organização da documentação.")
            
            doc_ok = st.checkbox("✅ Documentação do cliente organizada", key=f"doc_ok_{rpv_id}")
            
            if doc_ok:
                if st.button("📋 Enviar para Aguardando Certidão", type="primary"):
                    idx = df[df["ID"] == rpv_id].index[0]
                    st.session_state.df_editado_rpv.loc[idx, "Status"] = "Aguardando Certidão"
                    st.session_state.df_editado_rpv.loc[idx, "Documentação Organizada"] = "Sim"
                    save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                    st.session_state.show_rpv_dialog = False
                    st.success("✅ RPV enviado para Aguardando Certidão!")
                    st.rerun()
        else:
            st.info("📋 Este RPV não requer certidão. Organize a documentação e prossiga diretamente para o pagamento.")
            
            doc_ok = st.checkbox("✅ Documentação do cliente organizada", key=f"doc_ok_{rpv_id}")
            
            if doc_ok:
                if st.button("💰 Enviar para Aguardando Pagamento", type="primary"):
                    idx = df[df["ID"] == rpv_id].index[0]
                    st.session_state.df_editado_rpv.loc[idx, "Status"] = "Aguardando Pagamento"
                    st.session_state.df_editado_rpv.loc[idx, "Documentação Organizada"] = "Sim"
                    save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                    st.session_state.show_rpv_dialog = False
                    st.success("✅ RPV enviado para Aguardando Pagamento!")
                    st.rerun()

    # --- ETAPA 2: Ação do Jurídico (Certidão) ---
    elif status_atual == "Aguardando Certidão" and perfil_usuario in ["Jurídico", "Admin"]:
        st.markdown("#### Ação do Jurídico - Certidão")
        st.info("Verifique a necessidade da certidão e confirme a inserção no sistema Korbil.")
        
        certidao_korbil = st.checkbox("✅ Certidão inserida no Korbil", key=f"korbil_{rpv_id}")
        
        if certidao_korbil:
            if st.button("💰 Enviar para Aguardando Pagamento", type="primary"):
                idx = df[df["ID"] == rpv_id].index[0]
                st.session_state.df_editado_rpv.loc[idx, "Status"] = "Aguardando Pagamento"
                st.session_state.df_editado_rpv.loc[idx, "Certidão no Korbil"] = "Sim"
                save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                st.session_state.show_rpv_dialog = False
                st.success("✅ RPV enviado para Aguardando Pagamento!")
                st.rerun()

    # --- ETAPA 3: Ação do Financeiro (Pagamento) ---
    elif status_atual in ["Aguardando Pagamento", "Pagamento Atrasado"] and perfil_usuario in ["Financeiro", "Admin"]:
        st.markdown("#### Ação do Financeiro - Pagamento")
        st.info("Anexe os comprovantes e preencha os valores para finalizar o processo.")
        
        # Checkbox para anexar múltiplos documentos
        anexar_multiplos = st.checkbox("📎 Anexar múltiplos documentos", key=f"multiplos_rpv_{rpv_id}")
        
        col1, col2 = st.columns(2)
        with col1:
            if anexar_multiplos:
                comp_saque = st.file_uploader("Comprovantes de Pagamento", 
                                            type=["pdf", "png", "jpg", "jpeg"],
                                            accept_multiple_files=True,
                                            key=f"comp_saque_mult_{rpv_id}")
            else:
                comp_saque = st.file_uploader("Comprovante de Pagamento", 
                                            type=["pdf", "png", "jpg", "jpeg"],
                                            key=f"comp_saque_{rpv_id}")
        
        with col2:
            valor_liquido = st.number_input("💰 Valor Líquido (R$)", 
                                          min_value=0.0, 
                                          format="%.2f",
                                          key=f"valor_liq_{rpv_id}")
            
            # Campos adicionais
            observacoes_pagamento = st.text_area("📝 Observações do Pagamento", 
                                               key=f"obs_pag_{rpv_id}")
        
        # Botão para finalizar
        if comp_saque and valor_liquido > 0:
            if st.button("✅ Finalizar RPV", type="primary"):
                idx = df[df["ID"] == rpv_id].index[0]
                st.session_state.df_editado_rpv.loc[idx, "Status"] = "Finalizado"
                st.session_state.df_editado_rpv.loc[idx, "Valor Líquido"] = valor_liquido
                st.session_state.df_editado_rpv.loc[idx, "Observações Pagamento"] = observacoes_pagamento
                
                # Anexar arquivos se houver
                if comp_saque:
                    # Para simplificar, vamos apenas registrar que foi anexado
                    st.session_state.df_editado_rpv.loc[idx, "Comprovante Pagamento"] = "Arquivo anexado"
                
                save_data_to_github_seguro(st.session_state.df_editado_rpv, "lista_rpv.csv", "file_sha_rpv")
                st.session_state.show_rpv_dialog = False
                st.success("✅ RPV finalizado com sucesso!")
                st.rerun()
        else:
            st.warning("⚠️ Anexe o comprovante e preencha o valor para finalizar.")

    # Status não reconhecido ou sem permissão
    else:
        st.error("❌ Status não reconhecido ou sem permissão para editar.")

def ver_rpv_dialog(rpv_id, perfil_usuario):
    """Interface para visualizar RPVs com timeline"""
    # Implementação da visualização será adicionada futuramente
    st.info("Visualização em desenvolvimento")

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
    col_filtro1, col_filtro2, col_filtro3, col_filtro4 = st.columns(4)
    
    with col_filtro1:
        status_unicos = df["Status"].dropna().unique() if "Status" in df.columns else []
        status_filtro = st.multiselect("Status:", options=status_unicos, default=status_unicos, key="viz_rpv_status")
        
    with col_filtro2:
        usuarios_unicos = df["Cadastrado Por"].dropna().unique() if "Cadastrado Por" in df.columns else []
        usuario_filtro = st.multiselect("Cadastrado Por:", options=usuarios_unicos, default=usuarios_unicos, key="viz_rpv_user")
    
    with col_filtro3:
        assuntos_unicos = df["Assunto"].dropna().unique() if "Assunto" in df.columns else []
        assunto_filtro = st.multiselect("Assunto:", options=assuntos_unicos, default=assuntos_unicos, key="viz_rpv_assunto")
    
    with col_filtro4:
        pesquisa = st.text_input("Pesquisar por Beneficiário ou Processo:", key="viz_rpv_search")

    # Aplicar filtros
    df_visualizado = df.copy()
    if status_filtro and "Status" in df.columns:
        df_visualizado = df_visualizado[df_visualizado["Status"].isin(status_filtro)]
    if usuario_filtro and "Cadastrado Por" in df.columns:
        df_visualizado = df_visualizado[df_visualizado["Cadastrado Por"].isin(usuario_filtro)]
    if assunto_filtro and "Assunto" in df.columns:
        df_visualizado = df_visualizado[df_visualizado["Assunto"].isin(assunto_filtro)]
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
        
        # Campo Assunto com nova interface
        assunto_selecionado = campo_assunto_rpv(
            label="Assunto:",
            key_prefix="new_rpv_assunto"
        )
        
        # Converter para formato compatível
        assunto_final = assunto_selecionado if assunto_selecionado else ""
        
        # Campo Órgão Judicial com nova interface
        orgao_selecionado = campo_orgao_rpv(
            label="Órgão Judicial:",
            key_prefix="new_rpv_orgao"
        )
        
        # Converter para formato compatível
        orgao_final = orgao_selecionado if orgao_selecionado else ""
        
        solicitar_certidao = st.selectbox(
            "Solicitar Certidão?",
            options=["Sim", "Não"],
            key=certidao_key
        )
        # Novo campo: Mês de Competência
        mes_competencia = st.date_input(
            "Mês de Competência:",
            value=None,
            help="Selecione o mês e ano de competência",
            format="DD/MM/YYYY",
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
        # Primeiro, processar e salvar permanentemente novos valores de autocomplete
        
        # Processar assunto
        if assunto_selecionado and len(assunto_selecionado) > 0:
            assunto_processado = normalizar_assunto_rpv(assunto_selecionado[0])
            assuntos_existentes = obter_assuntos_rpv()
            if assunto_processado and assunto_processado not in assuntos_existentes:
                if adicionar_assunto_rpv(assunto_processado):
                    st.success(f"🆕 Novo assunto '{assunto_processado}' salvo permanentemente!")
            assunto_final = assunto_processado
        
        # Processar órgão
        if orgao_selecionado and len(orgao_selecionado) > 0:
            orgao_processado = normalizar_orgao_rpv(orgao_selecionado[0])
            orgaos_existentes = obter_orgaos_rpv()
            if orgao_processado and orgao_processado not in orgaos_existentes:
                if adicionar_orgao_rpv(orgao_processado):
                    st.success(f"🆕 Novo órgão '{orgao_processado}' salvo permanentemente!")
            orgao_final = orgao_processado
        
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
                # Sempre enviar para o Financeiro (removido o status "Enviado ao Jurídico")
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
                    "Assunto": assunto_final,
                    "Orgao Judicial": orgao_final,
                    "Mês Competência": mes_competencia.strftime("%d/%m/%Y") if mes_competencia else "",
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