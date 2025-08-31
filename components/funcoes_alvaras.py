# components/funcoes_alvaras.py
import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime
import math
import unicodedata
from streamlit_js_eval import streamlit_js_eval
from components.autocomplete_manager import (
    inicializar_autocomplete_session,
    adicionar_orgao_judicial,
    campo_orgao_judicial
)
from components.functions_controle import salvar_arquivo, save_data_to_github_seguro

# =====================================
# FUNÇÕES AUXILIARES
# =====================================

def safe_get_value_alvara(valor, default="Não informado"):
    """
    Função para tratar valores NaN e vazios de forma segura
    """
    if valor is None or valor == "" or str(valor).lower() in ['nan', 'nat', 'none']:
        return default
    return str(valor)

def safe_format_currency_alvara(valor, default="Não informado"):
    """
    Formatar valores monetários de forma segura, tratando NaN
    """
    try:
        if valor is None or valor == "" or str(valor).lower() in ['nan', 'nat', 'none']:
            return default
        
        # Tentar converter para float
        valor_float = float(valor)
        if math.isnan(valor_float):
            return default
        
        return f"R$ {valor_float:.2f}"
    except (ValueError, TypeError):
        return default

# =====================================
# CONFIGURAÇÕES DE PERFIS - ALVARÁS
# =====================================

PERFIS_ALVARAS = {
    "Cadastrador": ["Cadastrado", "Enviado para o Financeiro"],
    "Financeiro": ["Enviado para o Financeiro", "Financeiro - Enviado para Rodrigo", "Finalizado"],
    "Administrativo": ["Cadastrado", "Enviado para o Financeiro", "Financeiro - Enviado para Rodrigo", "Finalizado"],  # Pode visualizar tudo
    "SAC": ["Cadastrado", "Enviado para o Financeiro", "Financeiro - Enviado para Rodrigo", "Finalizado"],  # Pode visualizar tudo
    "Admin": ["Cadastrado", "Enviado para o Financeiro", "Financeiro - Enviado para Rodrigo", "Finalizado"]  # Admin tem acesso total
}

STATUS_ETAPAS_ALVARAS = {
    1: "Cadastrado",
    2: "Enviado para o Financeiro", 
    3: "Financeiro - Enviado para Rodrigo",
    4: "Finalizado"
}

# Órgãos Judiciais para autocomplete
ORGAOS_JUDICIAIS_DEFAULT = [
    "TRF 5A REGIAO",
    "JFSE",
    "TJSE",
    "STJ",
    "STF",
    "TRT 20A REGIAO",
    "TST"
]

def normalizar_orgao_judicial(texto):
    """Normaliza nome do órgão judicial removendo acentos e convertendo para maiúsculo"""
    if not texto:
        return ""
    # Remove acentos
    texto_normalizado = unicodedata.normalize('NFD', texto)
    texto_sem_acento = ''.join(c for c in texto_normalizado if unicodedata.category(c) != 'Mn')
    return texto_sem_acento.upper().strip()

def obter_orgaos_judiciais():
    """Retorna lista de órgãos judiciais salvos + padrões"""
    # Inicializa dados de autocomplete da sessão com dados persistidos
    inicializar_autocomplete_session()
    
    # Combina dados padrão com customizados
    orgaos_customizados = st.session_state.get("orgaos_judiciais_customizados", [])
    return list(set(ORGAOS_JUDICIAIS_DEFAULT + orgaos_customizados))

def safe_get_value_alvara(data, key, default=''):
    """Obtém valor de forma segura, tratando NaN e valores None"""
    value = data.get(key, default)
    if value is None:
        return default
    # Converter para string e verificar se não é 'nan'
    str_value = str(value)
    if str_value.lower() in ['nan', 'none', '', 'null']:
        return default
    return str_value

def exibir_informacoes_basicas_alvara(linha_alvara, estilo="compacto"):
    """Exibe informações básicas do Alvará de forma organizada e visual
    
    Args:
        linha_alvara: Dados da linha do Alvará
        estilo: "padrao", "compacto", ou "horizontal"
    """
    
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
    
    status_atual = safe_get_value_alvara(linha_alvara, 'Status')
    status_class = {
        "Cadastrado": "background-color: #fff3cd; color: #856404;",
        "Enviado para o Financeiro": "background-color: #d1ecf1; color: #0c5460;",
        "Financeiro - Enviado para Rodrigo": "background-color: #d4edda; color: #155724;",
        "Finalizado": "background-color: #d1e7dd; color: #0f5132;"
    }.get(status_atual, "background-color: #e2e3e5; color: #383d41;")
    
    st.markdown("### 📋 Resumo do Alvará")
    st.markdown(f"""
    <div class="compact-grid">
        <div class="compact-item">
            <div class="compact-label">📄 PROCESSO</div>
            <div class="compact-value">{safe_get_value_alvara(linha_alvara, 'Processo')}</div>
        </div>
        <div class="compact-item">
            <div class="compact-label">👤 PARTE</div>
            <div class="compact-value">{safe_get_value_alvara(linha_alvara, 'Parte')}</div>
        </div>
        <div class="compact-item">
            <div class="compact-label">🆔 CPF</div>
            <div class="compact-value">{safe_get_value_alvara(linha_alvara, 'CPF')}</div>
        </div>
        <div class="compact-item">
            <div class="compact-label">📊 STATUS</div>
            <div class="compact-value">
                <span class="compact-status" style="{status_class}">{status_atual}</span>
            </div>
        </div>
        <div class="compact-item">
            <div class="compact-label">💰 PAGAMENTO</div>
            <div class="compact-value">{safe_get_value_alvara(linha_alvara, 'Pagamento')}</div>
        </div>
        <div class="compact-item">
            <div class="compact-label">🏛️ ÓRGÃO</div>
            <div class="compact-value">{safe_get_value_alvara(linha_alvara, 'Órgão Judicial')[:20]}...</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

def search_orgaos_judiciais(searchterm):
    """Função de busca para o autocomplete de órgãos judiciais"""
    orgaos_disponiveis = obter_orgaos_judiciais()
    
    if not searchterm:
        return orgaos_disponiveis[:10]  # Mostrar primeiros 10 se não há busca
    
    # Normalizar termo de busca
    termo_normalizado = searchterm.upper().strip()
    
    # Buscar órgãos que contenham o termo
    resultados = []
    for orgao in orgaos_disponiveis:
        if termo_normalizado in orgao.upper():
            resultados.append(orgao)
    
    return resultados[:10]  # Limitar a 10 resultados

# =====================================
# FUNÇÕES DE PERFIL E CONTROLE - ALVARÁS
# =====================================

def verificar_perfil_usuario_alvaras():
    """Verifica o perfil do usuário logado para Alvarás a partir do session_state."""
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
    try:
        perfil = st.secrets.usuarios.get(usuario_atual, {}).get("perfil", "Visitante")
    except:
        perfil = "Visitante"
    
    return perfil
def pode_editar_status_alvaras(status_atual, perfil_usuario):
    """Verifica se o usuário pode editar determinado status"""
    return status_atual in PERFIS_ALVARAS.get(perfil_usuario, [])

# Funções auxiliares para o cadastro de alvarás
def obter_colunas_controle():
    """Retorna lista das colunas de controle do fluxo"""
    return [
        "Status", "Data Cadastro", "Cadastrado Por", "Comprovante Conta", 
        "PDF Alvará", "Data Envio Financeiro", "Enviado Financeiro Por",
        "Valor Total Alvara", "Valor Devido Cliente", "Valor Escritorio Contratual",
        "Valor Escritorio Sucumbencial", "Observacoes Financeiras",
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

def toggle_alvara_selection(alvara_id):
    """Função callback para alternar seleção de Alvará"""
    # Garantir que a lista existe
    if "processos_selecionados_alvaras" not in st.session_state:
        st.session_state.processos_selecionados_alvaras = []
    
    # Converter para string para consistência
    alvara_id_str = str(alvara_id)
    
    # Remover qualquer versão duplicada (int ou str)
    st.session_state.processos_selecionados_alvaras = [
        pid for pid in st.session_state.processos_selecionados_alvaras 
        if str(pid) != alvara_id_str
    ]
    
    # Se o checkbox está marcado, adicionar à lista
    checkbox_key = f"check_alvara_{alvara_id}"
    if st.session_state.get(checkbox_key, False):
        st.session_state.processos_selecionados_alvaras.append(alvara_id_str)

def interface_lista_alvaras(df, perfil_usuario):
    """Lista de alvarás com paginação e modal para ações"""
    
    # Inicializar o estado do diálogo
    if "show_alvara_dialog" not in st.session_state:
        st.session_state.show_alvara_dialog = False
        st.session_state.processo_aberto_id = None
    
    # Inicializar estado de exclusão em massa
    if "modo_exclusao_alvaras" not in st.session_state:
        st.session_state.modo_exclusao_alvaras = False
    if "processos_selecionados_alvaras" not in st.session_state:
        st.session_state.processos_selecionados_alvaras = []
    
    # Validar consistência da lista de selecionados
    if st.session_state.processos_selecionados_alvaras:
        ids_existentes = set(df["ID"].astype(str).tolist())
        st.session_state.processos_selecionados_alvaras = [
            pid for pid in st.session_state.processos_selecionados_alvaras 
            if str(pid) in ids_existentes
        ]

    # Botão para habilitar exclusão (apenas para Admin e Cadastrador)
    usuario_atual = st.session_state.get("usuario", "")
    perfil_atual = st.session_state.get("perfil_usuario", "")
    pode_excluir = (perfil_atual in ["Admin", "Cadastrador"] or usuario_atual == "admin")
    
    if pode_excluir:
        col_btn1, col_btn2, col_rest = st.columns([2, 2, 6])
        with col_btn1:
            if not st.session_state.modo_exclusao_alvaras:
                if st.button("🗑️ Habilitar Exclusão", key="habilitar_exclusao_alvaras"):
                    st.session_state.modo_exclusao_alvaras = True
                    st.session_state.processos_selecionados_alvaras = []
                    # Fechar qualquer diálogo aberto
                    if "show_alvara_dialog" in st.session_state:
                        st.session_state.show_alvara_dialog = False
                    st.rerun()
            else:
                if st.button("❌ Cancelar Exclusão", key="cancelar_exclusao_alvaras"):
                    st.session_state.modo_exclusao_alvaras = False
                    st.session_state.processos_selecionados_alvaras = []
                    # Fechar qualquer diálogo aberto
                    if "show_alvara_dialog" in st.session_state:
                        st.session_state.show_alvara_dialog = False
                    st.rerun()
        
        with col_btn2:
            if st.session_state.modo_exclusao_alvaras and st.session_state.processos_selecionados_alvaras:
                if st.button(f"🗑️ Excluir ({len(st.session_state.processos_selecionados_alvaras)})", 
                           key="confirmar_exclusao_alvaras", type="primary"):
                    confirmar_exclusao_massa_alvaras(df, st.session_state.processos_selecionados_alvaras)

    # Filtros - agora em 5 colunas
    col_filtro1, col_filtro2, col_filtro3, col_filtro4, col_filtro5 = st.columns(5)
    
    with col_filtro1:
        if "Status" in df.columns:
            status_filtro = st.selectbox(
                "🔍 Filtrar por Status:",
                ["Todos"] + list(STATUS_ETAPAS_ALVARAS.values())
            )
        else:
            status_filtro = "Todos"
    
    with col_filtro2:
        processo_filtro = st.text_input(
            "🔍 Filtrar por Processo:",
            placeholder="Digite o número do processo..."
        )
    
    with col_filtro3:
        nome_filtro = st.text_input(
            "🔍 Filtrar por Nome:",
            placeholder="Digite o nome da parte..."
        )
    
    with col_filtro4:
        # Filtro de órgão judicial
        if "Órgão Judicial" in df.columns:
            orgaos_unicos = ["Todos"] + sorted(df["Órgão Judicial"].dropna().unique().tolist())
            orgao_filtro = st.selectbox(
                "🔍 Filtrar por Órgão:",
                orgaos_unicos
            )
        else:
            orgao_filtro = "Todos"
    
    with col_filtro5:
        mostrar_apenas_meus = False
        if perfil_usuario == "Financeiro":
            # Usar key único para evitar reabertura de processos
            checkbox_key = f"filtro_meus_processos_{perfil_usuario}"
            mostrar_apenas_meus = st.checkbox(
                "Mostrar apenas processos que posso editar", 
                key=checkbox_key
            )
    
    # Aplicar filtros
    df_filtrado = df.copy()
    
    if status_filtro != "Todos" and "Status" in df.columns:
        df_filtrado = df_filtrado[df_filtrado["Status"] == status_filtro]
    if processo_filtro:
        df_filtrado = df_filtrado[df_filtrado["Processo"].astype(str).str.contains(processo_filtro, case=False, na=False)]
    if nome_filtro:
        df_filtrado = df_filtrado[df_filtrado["Parte"].astype(str).str.contains(nome_filtro, case=False, na=False)]
    if orgao_filtro != "Todos" and "Órgão Judicial" in df.columns:
        df_filtrado = df_filtrado[df_filtrado["Órgão Judicial"] == orgao_filtro]
    
    # Fechar qualquer diálogo aberto ao aplicar filtros para evitar reaberturas
    if mostrar_apenas_meus and perfil_usuario == "Financeiro":
        # Verificar se o estado do filtro mudou para fechar diálogo
        filtro_anterior = st.session_state.get("filtro_anterior_financeiro", False)
        if filtro_anterior != mostrar_apenas_meus:
            st.session_state.show_alvara_dialog = False
            st.session_state.processo_aberto_id = None
            st.session_state.filtro_anterior_financeiro = mostrar_apenas_meus
        
        df_filtrado = df_filtrado[df_filtrado["Status"].isin(["Enviado para o Financeiro", "Financeiro - Enviado para Rodrigo"])]
    
    # Ordenar por data de cadastro mais novo
    if "Data Cadastro" in df_filtrado.columns:
        df_filtrado["Data Cadastro Temp"] = pd.to_datetime(df_filtrado["Data Cadastro"], format="%d/%m/%Y %H:%M", errors="coerce")
        df_filtrado = df_filtrado.sort_values("Data Cadastro Temp", ascending=False, na_position="last").drop("Data Cadastro Temp", axis=1)
    else:
        df_filtrado = df_filtrado.sort_index(ascending=False)
    
    # Garantir IDs únicos
    df_trabalho = df_filtrado.copy()
    for idx in df_trabalho.index:
        id_atual = df_trabalho.loc[idx, "ID"]
        if pd.isna(id_atual) or str(id_atual).strip() == "" or "E+" in str(id_atual).upper():
            processo_hash = hash(str(df_trabalho.loc[idx, "Processo"]))
            novo_id = f"{idx}_{abs(processo_hash)}"
            df_trabalho.loc[idx, "ID"] = novo_id
            st.session_state.df_editado_alvaras.loc[idx, "ID"] = novo_id

    # --- LÓGICA DE PAGINAÇÃO ---
    if "current_page_alvaras" not in st.session_state:
        st.session_state.current_page_alvaras = 1
    
    items_per_page = 20
    total_registros = len(df_trabalho)
    total_pages = math.ceil(total_registros / items_per_page) if items_per_page > 0 else 1
    
    start_idx = (st.session_state.current_page_alvaras - 1) * items_per_page
    end_idx = start_idx + items_per_page
    df_paginado = df_trabalho.iloc[start_idx:end_idx]

    # Botão para salvar alterações pendentes
    if "preview_novas_linhas" in st.session_state and len(st.session_state["preview_novas_linhas"]) > 0:
        st.markdown("### 📋 Linhas Adicionadas (não salvas)")
        if st.button("💾 Salvar Alterações", type="primary"):
            # ... (sua lógica de salvar) ...
            st.rerun()
    
    # Exibir lista com botão Abrir
    if len(df_paginado) > 0:
        st.markdown(f'<p style="font-size: small; color: steelblue;">Mostrando {start_idx+1} a {min(end_idx, total_registros)} de {total_registros} alvarás</p>', unsafe_allow_html=True)
        
        # Cabeçalhos dinâmicos baseados no modo de exclusão
        if st.session_state.modo_exclusao_alvaras:
            col_check, col_abrir, col_processo, col_parte, col_valor, col_status = st.columns([0.5, 1, 2, 2, 1.5, 2])
            with col_check: st.markdown("**☑️**")
            with col_abrir: st.markdown("**Ação**")
            with col_processo: st.markdown("**Processo**")
            with col_parte: st.markdown("**Parte**")
            with col_valor: st.markdown("**Valor**")
            with col_status: st.markdown("**Status**")
        else:
            col_abrir, col_processo, col_parte, col_valor, col_status = st.columns([1, 2, 2, 1.5, 2])
            with col_abrir: st.markdown("**Ação**")
            with col_processo: st.markdown("**Processo**")
            with col_parte: st.markdown("**Parte**")
            with col_valor: st.markdown("**Valor**")
            with col_status: st.markdown("**Status**")
        
        st.markdown('<hr style="margin-top: 0.1rem; margin-bottom: 0.5rem;" />', unsafe_allow_html=True)
        
        for idx, processo in df_paginado.iterrows():
            alvara_id = processo.get("ID", f"temp_{idx}")
            
            if st.session_state.modo_exclusao_alvaras:
                col_check, col_abrir, col_processo, col_parte, col_valor, col_status = st.columns([0.5, 1, 2, 2, 1.5, 2])
                
                with col_check:
                    current_value = alvara_id in st.session_state.processos_selecionados_alvaras
                    
                    is_selected = st.checkbox(
                        "",
                        value=current_value,
                        key=f"check_alvara_{alvara_id}",
                        on_change=lambda aid=alvara_id: toggle_alvara_selection(aid)
                    )
                
                with col_abrir:
                    if st.button(f"🔓 Abrir", key=f"abrir_alvara_id_{alvara_id}"):
                        st.session_state.show_alvara_dialog = True
                        st.session_state.processo_aberto_id = alvara_id
                        st.rerun()
                
                with col_processo: st.write(f"**{processo.get('Processo', 'Não informado')}**")
                with col_parte: st.write(processo.get('Parte', 'Não informado'))
                with col_valor: st.write(safe_get_value_alvara(processo, 'Pagamento', '-'))
                with col_status:
                    status_atual = processo.get('Status', 'Não informado')
                    cor = {"Cadastrado": "🟡", "Enviado para o Financeiro": "🟠", "Financeiro - Enviado para Rodrigo": "🔵", "Finalizado": "🟢"}.get(status_atual, "")
                    st.write(f"{cor} {status_atual}")
            else:
                col_abrir, col_processo, col_parte, col_valor, col_status = st.columns([1, 2, 2, 1.5, 2])
                
                with col_abrir:
                    if st.button(f"🔓 Abrir", key=f"abrir_alvara_id_{alvara_id}"):
                        st.session_state.show_alvara_dialog = True
                        st.session_state.processo_aberto_id = alvara_id
                        st.rerun()
                
                with col_processo: st.write(f"**{processo.get('Processo', 'Não informado')}**")
                with col_parte: st.write(processo.get('Parte', 'Não informado'))
                with col_valor: st.write(safe_get_value_alvara(processo, 'Pagamento', '-'))
                with col_status:
                    status_atual = processo.get('Status', 'Não informado')
                    cor = {"Cadastrado": "🟡", "Enviado para o Financeiro": "🟠", "Financeiro - Enviado para Rodrigo": "🔵", "Finalizado": "🟢"}.get(status_atual, "")
                    st.write(f"{cor} {status_atual}")

       # --- IMPLEMENTAÇÃO COM st.dialog ---
    if st.session_state.show_alvara_dialog:
        alvara_id_aberto = st.session_state.processo_aberto_id
        linha_processo = df[df["ID"].astype(str) == str(alvara_id_aberto)]
        titulo_dialog = f"Detalhes do Alvará: {linha_processo.iloc[0].get('Processo', 'Não informado')}" if not linha_processo.empty else "Detalhes do Alvará"

        @st.dialog(titulo_dialog, width="large")
        def alvara_dialog():
            if not linha_processo.empty:
                status_atual = linha_processo.iloc[0].get("Status", "")
                # Chama a função de edição que você já tem
                interface_edicao_processo(df, alvara_id_aberto, status_atual, perfil_usuario)
            else:
                st.error("❌ Alvará não encontrado.")
            
            if st.button("Fechar", key="fechar_dialog"):
                st.session_state.show_alvara_dialog = False
                st.rerun()

        # Chama a função para renderizar o diálogo
        alvara_dialog()

        # --- CONTROLES DE PAGINAÇÃO (EMBAIXO) ---
        st.markdown("---")
        col_nav1, col_nav2, col_nav3 = st.columns([3, 2, 3])

        with col_nav1:
            if st.session_state.current_page_alvaras > 1:
                if st.button("<< Primeira", key="btn_primeira"):
                    st.session_state.current_page_alvaras = 1
                    st.rerun()
                if st.button("< Anterior", key="btn_anterior"):
                    st.session_state.current_page_alvaras -= 1
                    st.rerun()

        with col_nav2:
            st.write(f"Página {st.session_state.current_page_alvaras} de {total_pages}")

        with col_nav3:
            if st.session_state.current_page_alvaras < total_pages:
                if st.button("Próxima >", key="btn_proxima"):
                    st.session_state.current_page_alvaras += 1
                    st.rerun()
                if st.button("Última >>", key="btn_ultima"):
                    st.session_state.current_page_alvaras = total_pages
                    st.rerun()
    else:
        st.info("Nenhum alvará encontrado com os filtros aplicados")

def interface_anexar_documentos(df, processo):
    """Interface para anexar comprovante e PDF do alvará"""
    st.markdown(f"### Anexar Documentos - Processo: {processo}")
    
    # Buscar dados do processo
    linha_processo = df[df["Processo"] == processo].iloc[0]
    
    if linha_processo["Status"] != "Cadastrado":
        st.warning("⚠️ Este processo não está na etapa de anexação de documentos")
        return
    
    # Checkbox para múltiplos anexos
    anexar_multiplos = st.checkbox("Anexar múltiplos documentos", key=f"multiplos_alvara_{processo}")
    
    col_doc1, col_doc2 = st.columns(2)
    
    with col_doc1:
        st.markdown("**📄 Comprovante da Conta**")
        if anexar_multiplos:
            comprovante_conta = st.file_uploader(
                "Anexar comprovantes da conta:",
                type=["pdf", "jpg", "jpeg", "png"],
                accept_multiple_files=True,
                key=f"comprovante_{processo}"
            )
        else:
            comprovante_conta = st.file_uploader(
                "Anexar comprovante da conta:",
                type=["pdf", "jpg", "jpeg", "png"],
                key=f"comprovante_{processo}"
            )
    
    with col_doc2:
        st.markdown("**📄 PDF do Alvará**")
        if anexar_multiplos:
            pdf_alvara = st.file_uploader(
                "Anexar PDFs do alvará:",
                type=["pdf"],
                accept_multiple_files=True,
                key=f"pdf_{processo}"
            )
        else:
            pdf_alvara = st.file_uploader(
                "Anexar PDF do alvará:",
                type=["pdf"],
                key=f"pdf_{processo}"
            )
    
    # Verificar se documentos foram anexados (considerando múltiplos)
    docs_anexados = False
    if anexar_multiplos:
        docs_anexados = comprovante_conta and pdf_alvara and len(comprovante_conta) > 0 and len(pdf_alvara) > 0
    else:
        docs_anexados = comprovante_conta and pdf_alvara
    
    if docs_anexados:
        if anexar_multiplos:
            st.success(f"✅ {len(comprovante_conta)} comprovante(s) e {len(pdf_alvara)} PDF(s) anexados!")
        else:
            st.success("✅ Ambos os documentos foram anexados!")
        
        if st.button("📤 Enviar para Financeiro", type="primary"):
            with st.spinner("📤 Enviando documentos para o Google Drive..."):
                try:
                    # Upload para Google Drive
                    from components.google_drive_integration import upload_to_google_drive
                    
                    success, result = upload_to_google_drive(processo, comprovante_conta, pdf_alvara)
                    
                    if success:
                        st.success("✅ Documentos enviados para o Google Drive com sucesso!")
                        
                        # Atualizar status
                        idx = df[df["Processo"] == processo].index[0]
                        st.session_state.df_editado_alvaras.loc[idx, "Status"] = "Enviado para o Financeiro"
                        st.session_state.df_editado_alvaras.loc[idx, "Comprovante Conta"] = f"Drive: {result['comprovante_name']}"
                        st.session_state.df_editado_alvaras.loc[idx, "PDF Alvará"] = f"Drive: {result['pdf_name']}"
                        st.session_state.df_editado_alvaras.loc[idx, "Data Envio Financeiro"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                        st.session_state.df_editado_alvaras.loc[idx, "Enviado Financeiro Por"] = st.session_state.get("usuario", "Sistema")
                        
                        st.success("✅ Processo enviado para o Financeiro! Arquivos salvos no Google Drive.")
                        st.rerun()
                    else:
                        st.error(f"❌ Erro no upload: {result}")
                        # Fallback para sistema local
                        st.warning("⚠️ Tentando salvar localmente...")
                        from components.functions_controle import salvar_arquivo
                        comprovante_path = salvar_arquivo(comprovante_conta, processo, "comprovante")
                        pdf_path = salvar_arquivo(pdf_alvara, processo, "alvara")
                        
                        # Atualizar status com paths locais
                        idx = df[df["Processo"] == processo].index[0]
                        st.session_state.df_editado_alvaras.loc[idx, "Status"] = "Enviado para o Financeiro"
                        st.session_state.df_editado_alvaras.loc[idx, "Comprovante Conta"] = comprovante_path
                        st.session_state.df_editado_alvaras.loc[idx, "PDF Alvará"] = pdf_path
                        st.session_state.df_editado_alvaras.loc[idx, "Data Envio Financeiro"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                        st.session_state.df_editado_alvaras.loc[idx, "Enviado Financeiro Por"] = st.session_state.get("usuario", "Sistema")
                        
                        st.info("✅ Processo salvo localmente e enviado para o Financeiro!")
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ Erro inesperado: {str(e)}")
                    # Fallback para sistema local
                    st.warning("⚠️ Salvando localmente...")
                    from components.functions_controle import salvar_arquivo
                    comprovante_path = salvar_arquivo(comprovante_conta, processo, "comprovante")
                    pdf_path = salvar_arquivo(pdf_alvara, processo, "alvara")
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
                # Checkbox para múltiplos comprovantes
                anexar_multiplos_comp = st.checkbox(
                    "Anexar múltiplos comprovantes", 
                    key=f"multiplos_comprovante_{processo['Processo']}"
                )
                
                if anexar_multiplos_comp:
                    comprovante_recebimento = st.file_uploader(
                        "Anexar comprovantes de recebimento:",
                        type=["pdf", "jpg", "jpeg", "png"],
                        accept_multiple_files=True,
                        key=f"comprovante_recebimento_{processo['Processo']}"
                    )
                else:
                    comprovante_recebimento = st.file_uploader(
                        "Anexar comprovante de recebimento:",
                        type=["pdf", "jpg", "jpeg", "png"],
                        key=f"comprovante_recebimento_{processo['Processo']}"
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
        st.write(f"**Pagamento:** {linha_processo.get('Pagamento', 'Não informado')}")
        st.write(f"**Parte:** {linha_processo.get('Parte', 'Não informado')}")
        st.write(f"**CPF/CNPJ:** {linha_processo.get('CPF/CNPJ', 'Não informado')}")
    with col_info2:
        st.write(f"**Agência:** {linha_processo.get('Agência', 'Não informado')}")
        st.write(f"**Conta:** {linha_processo.get('Conta', 'Não informado')}")
    with col_info3:
        st.write(f"**Cadastrado em:** {linha_processo.get('Data Cadastro', 'Não informado')}")
        st.write(f"**Última atualização:** {linha_processo.get('Data Atualização', 'Não informado')}")
        st.write(f"**Valor:** {safe_format_currency_alvara(linha_processo.get('Valor'))}")
    
    # Adicionar mais visualizações de dados conforme necessário

def interface_edicao_processo(df, alvara_id, status_atual, perfil_usuario):
    """Interface de edição baseada no status e perfil"""
    
    linha_processo_df = df[df["ID"].astype(str) == str(alvara_id)]
    
    if len(linha_processo_df) == 0:
        st.error(f"❌ Alvará com ID {alvara_id} não encontrado")
        return
    
    linha_processo = linha_processo_df.iloc[0]
    numero_processo = linha_processo.get("Processo", "N/A")
    
    # Exibir informações básicas do processo com layout compacto
    exibir_informacoes_basicas_alvara(linha_processo, "compacto")
    if status_atual == "Cadastrado" and perfil_usuario in ["Cadastrador", "Admin"]:
        st.markdown("#### Anexar Documentos")
        
        # Checkbox para anexar múltiplos documentos
        anexar_multiplos = st.checkbox("Anexar múltiplos documentos", key=f"multiplos_edicao_{alvara_id}")
        
        col_doc1, col_doc2 = st.columns(2)
        
        with col_doc1:
            st.markdown("**📄 Comprovante da Conta**")
            if anexar_multiplos:
                comprovante_conta = st.file_uploader(
                    "Anexar comprovantes da conta:",
                    type=["pdf", "jpg", "jpeg", "png"],
                    accept_multiple_files=True,
                    key=f"comprovante_{numero_processo}"
                )
            else:
                comprovante_conta = st.file_uploader(
                    "Anexar comprovante da conta:",
                    type=["pdf", "jpg", "jpeg", "png"],
                    key=f"comprovante_{numero_processo}"
                )
                    
        with col_doc2:
            st.markdown("**📄 PDF do Alvará**")
            if anexar_multiplos:
                pdf_alvara = st.file_uploader(
                    "Anexar PDFs do alvará:",
                    type=["pdf"],
                    accept_multiple_files=True,
                    key=f"pdf_{numero_processo}"
                )
            else:
                pdf_alvara = st.file_uploader(
                    "Anexar PDF do alvará:",
                    type=["pdf"],
                    key=f"pdf_{numero_processo}"
                )
            
        # Verificar se documentos foram anexados (considerando múltiplos)
        docs_anexados = False
        if anexar_multiplos:
            docs_anexados = comprovante_conta and pdf_alvara and len(comprovante_conta) > 0 and len(pdf_alvara) > 0
        else:
            docs_anexados = comprovante_conta and pdf_alvara
            
        if docs_anexados:
            if anexar_multiplos:
                st.success(f"✅ {len(comprovante_conta)} comprovante(s) e {len(pdf_alvara)} PDF(s) anexados!")
            else:
                st.success("✅ Ambos os documentos foram anexados!")
            
            if st.button("📤 Enviar para Financeiro", type="primary", key=f"enviar_fin_id_{alvara_id}"):
                # Salvar arquivos
                
                if anexar_multiplos:
                    # Salvar múltiplos arquivos
                    comprovante_urls = []
                    for i, arquivo in enumerate(comprovante_conta):
                        url = salvar_arquivo(arquivo, numero_processo, f"comprovante_{i+1}")
                        comprovante_urls.append(url)
                    comprovante_url = "; ".join(comprovante_urls)
                    
                    pdf_urls = []
                    for i, arquivo in enumerate(pdf_alvara):
                        url = salvar_arquivo(arquivo, numero_processo, f"alvara_{i+1}")
                        pdf_urls.append(url)
                    pdf_url = "; ".join(pdf_urls)
                else:
                    # Salvar arquivos únicos
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
                    st.session_state.show_alvara_dialog = False
                    st.rerun()
        elif comprovante_conta or pdf_alvara:
            if anexar_multiplos:
                st.warning("⚠️ Anexe pelo menos um arquivo de cada tipo para prosseguir")
            else:
                st.warning("⚠️ Anexe ambos os documentos para prosseguir")
        else:
            st.info("📋 Anexe o comprovante da conta e o PDF do alvará")
    
    elif status_atual == "Enviado para o Financeiro":
        
        # Apenas Financeiro e Admin podem preencher valores financeiros
        if perfil_usuario in ["Financeiro", "Admin"]:
            
            # Checkbox para controle de pendência
            pendente_cadastro = st.checkbox(
                "⏳ Pendente de cadastro",
                value=linha_processo.get("Pendente de Cadastro", "") == "Sim",
                help="Marque se os dados ainda estão pendentes de cadastro. Isso desabilitará os campos de valor.",
                key=f"pendente_{alvara_id}"
            )
            
            st.markdown("---")
            
            # Controle HC com botão progressivo (FORA do formulário)
            if st.button("➕ Adicionar HC", key=f"btn_hc_{alvara_id}"):
                # Inicializar estado do botão HC se não existir
                if f"hc_nivel_{alvara_id}" not in st.session_state:
                    st.session_state[f"hc_nivel_{alvara_id}"] = 0
                
                st.session_state[f"hc_nivel_{alvara_id}"] = (st.session_state[f"hc_nivel_{alvara_id}"] + 1) % 3
                st.rerun()
            
            # Inicializar estado do botão HC
            if f"hc_nivel_{alvara_id}" not in st.session_state:
                st.session_state[f"hc_nivel_{alvara_id}"] = 0
            
            # Formulário para valores financeiros
            with st.form(f"form_valores_financeiros_{alvara_id}"):
                st.markdown("**Valores Financeiros:**")
                
                col_val1, col_val2 = st.columns(2)
                
                with col_val1:
                    valor_sacado = st.number_input(
                        "💵 Valor Sacado (valor real atualizado):",
                        min_value=0.0,
                        value=float(linha_processo.get("Valor Sacado", "0") or "0"),
                        step=0.01,
                        format="%.2f",
                        help="Valor real atualizado que foi sacado",
                        disabled=pendente_cadastro
                    )
                    
                    honorarios_sucumbenciais = st.number_input(
                        "⚖️ Honorários Sucumbenciais:",
                        min_value=0.0,
                        value=float(linha_processo.get("Honorarios Sucumbenciais Valor", "0") or "0"),
                        step=0.01,
                        format="%.2f",
                        help="Valor dos honorários sucumbenciais",
                        disabled=pendente_cadastro
                    )
                
                with col_val2:
                    prospector_parceiro = st.number_input(
                        "🤝 Prospector/Parceiro:",
                        min_value=0.0,
                        value=float(linha_processo.get("Prospector Parceiro", "0") or "0"),
                        step=0.01,
                        format="%.2f",
                        help="Valor destinado ao prospector/parceiro",
                        disabled=pendente_cadastro
                    )
                    
                    valor_cliente = st.number_input(
                        "👤 Valor do Cliente:",
                        min_value=0.0,
                        value=float(linha_processo.get("Valor Cliente Final", "0") or "0"),
                        step=0.01,
                        format="%.2f",
                        help="Valor final destinado ao cliente",
                        disabled=pendente_cadastro
                    )
                
                # Seção de Honorários Contratuais dentro do form
                st.markdown("---")
                
                honorarios_contratuais = st.number_input(
                    "Honorário Contratual 1:",
                    min_value=0.0,
                    value=float(linha_processo.get("Honorarios Contratuais", "0") or "0"),
                    step=0.01,
                    format="%.2f",
                    help="Valor dos honorários contratuais principais",
                    disabled=pendente_cadastro
                )
                
                # Campos HC adicionais (aparecem conforme o nível do botão)
                hc1_valor, hc2_valor, hc3_valor = 0.0, 0.0, 0.0
                nivel_hc = st.session_state.get(f"hc_nivel_{alvara_id}", 0)
                
                if nivel_hc >= 1:  # Primeira pressão: Mostrar HC2
                    hc1_valor = st.number_input(
                        "Honorário Contratual 2:",
                        min_value=0.0,
                        value=float(linha_processo.get("HC1", "0") or "0"),
                        step=0.01,
                        format="%.2f",
                        disabled=pendente_cadastro,
                        key=f"hc2_{alvara_id}"
                    )
                
                if nivel_hc >= 2:  # Segunda pressão: Mostrar HC3
                    hc2_valor = st.number_input(
                        "Honorário Contratual 3:",
                        min_value=0.0,
                        value=float(linha_processo.get("HC2", "0") or "0"),
                        step=0.01,
                        format="%.2f",
                        disabled=pendente_cadastro,
                        key=f"hc3_{alvara_id}"
                    )
                
                # Campo de observações
                observacoes_financeiras = st.text_area(
                    "📝 Observações Financeiras:",
                    value=safe_get_value_alvara(linha_processo, "Observacoes Financeiras", ""),
                    help="Observações sobre os valores financeiros",
                    height=100
                )
                
                # Botões de ação
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    salvar_valores = st.form_submit_button(
                        "Salvar Valores", 
                        type="primary" if not pendente_cadastro else "secondary"
                    )
                
                with col_btn2:
                    enviar_rodrigo = st.form_submit_button(
                        "📤 Enviar para Rodrigo",
                        type="primary"
                    )
                    if pendente_cadastro:
                        st.info("ℹ️ Processo será enviado com dados em branco para preenchimento")
                
                # Lógica de processamento
                if salvar_valores:
                    try:
                        idx = df[df["ID"] == alvara_id].index[0]
                        
                        # Salvar status de pendência
                        st.session_state.df_editado_alvaras.loc[idx, "Pendente de Cadastro"] = "Sim" if pendente_cadastro else "Não"
                        
                        # Salvar valores apenas se não estiver pendente
                        if not pendente_cadastro:
                            st.session_state.df_editado_alvaras.loc[idx, "Valor Sacado"] = valor_sacado
                            st.session_state.df_editado_alvaras.loc[idx, "Honorarios Sucumbenciais Valor"] = honorarios_sucumbenciais
                            st.session_state.df_editado_alvaras.loc[idx, "Prospector Parceiro"] = prospector_parceiro
                            st.session_state.df_editado_alvaras.loc[idx, "Valor Cliente Final"] = valor_cliente
                            
                            # Salvar honorários contratuais
                            st.session_state.df_editado_alvaras.loc[idx, "Honorarios Contratuais"] = honorarios_contratuais
                            
                            # Salvar HC adicionais se foram preenchidos
                            nivel_hc = st.session_state.get(f"hc_nivel_{alvara_id}", 0)
                            if nivel_hc >= 1:  # HC2 está visível
                                st.session_state.df_editado_alvaras.loc[idx, "HC1"] = hc1_valor
                            if nivel_hc >= 2:  # HC3 está visível
                                st.session_state.df_editado_alvaras.loc[idx, "HC2"] = hc2_valor
                        
                        # Salvar observações sempre
                        st.session_state.df_editado_alvaras.loc[idx, "Observacoes Financeiras"] = observacoes_financeiras
                        
                        # Salvar no GitHub
                        novo_sha = save_data_to_github_seguro(
                            st.session_state.df_editado_alvaras,
                            "lista_alvaras.csv",
                            st.session_state.file_sha_alvaras
                        )
                        st.session_state.file_sha_alvaras = novo_sha
                        
                        st.success("✅ Valores salvos com sucesso!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao salvar valores: {str(e)}")
                
                elif enviar_rodrigo:
                    try:
                        idx = df[df["ID"] == alvara_id].index[0]
                        
                        # Salvar valores apenas se não estiver pendente de cadastro
                        if not pendente_cadastro:
                            # Salvar valores finais antes de enviar
                            st.session_state.df_editado_alvaras.loc[idx, "Valor Sacado"] = valor_sacado
                            st.session_state.df_editado_alvaras.loc[idx, "Honorarios Sucumbenciais Valor"] = honorarios_sucumbenciais
                            st.session_state.df_editado_alvaras.loc[idx, "Prospector Parceiro"] = prospector_parceiro
                            st.session_state.df_editado_alvaras.loc[idx, "Valor Cliente Final"] = valor_cliente
                            st.session_state.df_editado_alvaras.loc[idx, "Observacoes Financeiras"] = observacoes_financeiras
                            
                            # Salvar honorários contratuais
                            st.session_state.df_editado_alvaras.loc[idx, "Honorarios Contratuais"] = honorarios_contratuais
                            
                            # Salvar HC adicionais se foram preenchidos
                            nivel_hc = st.session_state.get(f"hc_nivel_{alvara_id}", 0)
                            if nivel_hc >= 1:  # HC2 está visível
                                st.session_state.df_editado_alvaras.loc[idx, "HC1"] = hc1_valor
                            if nivel_hc >= 2:  # HC3 está visível
                                st.session_state.df_editado_alvaras.loc[idx, "HC2"] = hc2_valor
                        else:
                            # Se pendente de cadastro, enviar com valores em branco/zero
                            st.session_state.df_editado_alvaras.loc[idx, "Valor Sacado"] = 0.0
                            st.session_state.df_editado_alvaras.loc[idx, "Honorarios Sucumbenciais Valor"] = 0.0
                            st.session_state.df_editado_alvaras.loc[idx, "Prospector Parceiro"] = 0.0
                            st.session_state.df_editado_alvaras.loc[idx, "Valor Cliente Final"] = 0.0
                            st.session_state.df_editado_alvaras.loc[idx, "Honorarios Contratuais"] = 0.0
                            st.session_state.df_editado_alvaras.loc[idx, "HC1"] = 0.0
                            st.session_state.df_editado_alvaras.loc[idx, "HC2"] = 0.0
                            st.session_state.df_editado_alvaras.loc[idx, "Observacoes Financeiras"] = ""
                        
                        # Atualizar status para próxima etapa
                        st.session_state.df_editado_alvaras.loc[idx, "Status"] = "Financeiro - Enviado para Rodrigo"
                        st.session_state.df_editado_alvaras.loc[idx, "Data Envio Rodrigo"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                        st.session_state.df_editado_alvaras.loc[idx, "Enviado Rodrigo Por"] = st.session_state.get("usuario", "Sistema")
                        
                        # Manter status de pendência para que Rodrigo saiba que precisa preencher do zero
                        if pendente_cadastro:
                            st.session_state.df_editado_alvaras.loc[idx, "Pendente de Cadastro"] = "Sim - Enviado para Rodrigo"
                        else:
                            st.session_state.df_editado_alvaras.loc[idx, "Pendente de Cadastro"] = "Não"
                        
                        # Salvar no GitHub
                        novo_sha = save_data_to_github_seguro(
                            st.session_state.df_editado_alvaras,
                            "lista_alvaras.csv",
                            st.session_state.file_sha_alvaras
                        )
                        st.session_state.file_sha_alvaras = novo_sha
                        
                        if pendente_cadastro:
                            st.success("✅ Processo Enviado para Rodrigo com dados em branco para preenchimento!")
                        else:
                            st.success("✅ Processo Enviado para Rodrigo com sucesso!")
                        st.session_state.show_alvara_dialog = False
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao enviar para Rodrigo: {str(e)}")
            
            # Mostrar resumo dos valores atuais se não estiver pendente
            if not pendente_cadastro:
                st.markdown("---")
                st.markdown("**📊 Resumo dos Valores Atuais:**")
                
                col_res1, col_res2, col_res3, col_res4 = st.columns(4)
                
                with col_res1:
                    valor_atual = linha_processo.get("Valor Sacado", "0")
                    st.metric("💵 Valor Sacado", safe_format_currency_alvara(valor_atual))
                
                with col_res2:
                    honor_atual = linha_processo.get("Honorarios Sucumbenciais Valor", "0")
                    st.metric("⚖️ Honorários", safe_format_currency_alvara(honor_atual))
                
                with col_res3:
                    prosp_atual = linha_processo.get("Prospector Parceiro", "0")
                    st.metric("🤝 Prospector", safe_format_currency_alvara(prosp_atual))
                
                with col_res4:
                    cliente_atual = linha_processo.get("Valor Cliente Final", "0")
                    st.metric("👤 Cliente", safe_format_currency_alvara(cliente_atual))
        
        else:
            st.warning("⚠️ Apenas usuários Financeiro e Admin podem gerenciar valores financeiros.")
    
    elif status_atual == "Financeiro - Enviado para Rodrigo" and perfil_usuario in ["Financeiro", "Admin"]:
        st.markdown("**📋 Informações do processo:**")
        st.write(f"- Enviado para Rodrigo em: {linha_processo.get('Data Envio Rodrigo', 'Não informado')}")
        st.write(f"- Enviado por: {linha_processo.get('Enviado Rodrigo Por', 'Não informado')}")
        
        st.markdown("---")
        
        # Controle HC com botão progressivo (FORA do formulário)
        if st.button("➕ Adicionar HC", key=f"btn_hc_rodrigo_{alvara_id}"):
            # Inicializar estado do botão HC se não existir
            if f"hc_nivel_rodrigo_{alvara_id}" not in st.session_state:
                st.session_state[f"hc_nivel_rodrigo_{alvara_id}"] = 0
            
            st.session_state[f"hc_nivel_rodrigo_{alvara_id}"] = (st.session_state[f"hc_nivel_rodrigo_{alvara_id}"] + 1) % 3
            st.rerun()

        # Inicializar estado do botão HC
        if f"hc_nivel_rodrigo_{alvara_id}" not in st.session_state:
            st.session_state[f"hc_nivel_rodrigo_{alvara_id}"] = 0

        # Formulário para valores financeiros (AGORA HABILITADOS para Rodrigo)
        with st.form(f"form_valores_rodrigo_{alvara_id}"):
            st.markdown("**💰 Valores Financeiros:**")
            
            col_val1, col_val2 = st.columns(2)
            
            with col_val1:
                valor_sacado = st.number_input(
                    "💵 Valor Sacado (valor real atualizado):",
                    min_value=0.0,
                    value=float(linha_processo.get("Valor Sacado", "0") or "0"),
                    step=0.01,
                    format="%.2f",
                    help="Valor real atualizado que foi sacado"
                )
                
                honorarios_sucumbenciais = st.number_input(
                    "⚖️ Honorários Sucumbenciais:",
                    min_value=0.0,
                    value=float(linha_processo.get("Honorarios Sucumbenciais Valor", "0") or "0"),
                    step=0.01,
                    format="%.2f",
                    help="Valor dos honorários sucumbenciais"
                )
            
            with col_val2:
                prospector_parceiro = st.number_input(
                    "🤝 Prospector/Parceiro:",
                    min_value=0.0,
                    value=float(linha_processo.get("Prospector Parceiro", "0") or "0"),
                    step=0.01,
                    format="%.2f",
                    help="Valor destinado ao prospector/parceiro"
                )
                
                valor_cliente = st.number_input(
                    "👤 Valor do Cliente:",
                    min_value=0.0,
                    value=float(linha_processo.get("Valor Cliente Final", "0") or "0"),
                    step=0.01,
                    format="%.2f",
                    help="Valor final destinado ao cliente"
                )
            
            # Seção de Honorários Contratuais dentro do form
            st.markdown("---")
            
            honorarios_contratuais = st.number_input(
                "Honorário Contratual 1:",
                min_value=0.0,
                value=float(linha_processo.get("Honorarios Contratuais", "0") or "0"),
                step=0.01,
                format="%.2f",
                help="Valor dos honorários contratuais principais"
            )
            
            # Campos HC adicionais (aparecem conforme o nível do botão)
            hc1_valor, hc2_valor, hc3_valor = 0.0, 0.0, 0.0
            nivel_hc = st.session_state.get(f"hc_nivel_rodrigo_{alvara_id}", 0)
            
            if nivel_hc >= 1:  # Primeira pressão: Mostrar HC2
                hc1_valor = st.number_input(
                    "Honorário Contratual 2:",
                    min_value=0.0,
                    value=float(linha_processo.get("HC1", "0") or "0"),
                    step=0.01,
                    format="%.2f",
                    key=f"hc2_rodrigo_{alvara_id}"
                )
            
            if nivel_hc >= 2:  # Segunda pressão: Mostrar HC3
                hc2_valor = st.number_input(
                    "Honorário Contratual 3:",
                    min_value=0.0,
                    value=float(linha_processo.get("HC2", "0") or "0"),
                    step=0.01,
                    format="%.2f",
                    key=f"hc3_rodrigo_{alvara_id}"
                )
            
            # Campo de observações
            observacoes_financeiras = st.text_area(
                "📝 Observações Financeiras:",
                value=safe_get_value_alvara(linha_processo, "Observacoes Financeiras", ""),
                help="Observações sobre os valores financeiros",
                height=100
            )
            
            # Botões de ação
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                salvar_valores_rodrigo = st.form_submit_button(
                    "💾 Salvar Valores",
                    type="secondary"
                )
            
            with col_btn2:
                finalizar_processo = st.form_submit_button(
                    "🎯 Finalizar Processo",
                    type="primary"
                )
            
            # Lógica de processamento
            if salvar_valores_rodrigo:
                try:
                    idx = df[df["ID"] == alvara_id].index[0]
                    
                    # Salvar todos os valores
                    st.session_state.df_editado_alvaras.loc[idx, "Valor Sacado"] = valor_sacado
                    st.session_state.df_editado_alvaras.loc[idx, "Honorarios Sucumbenciais Valor"] = honorarios_sucumbenciais
                    st.session_state.df_editado_alvaras.loc[idx, "Prospector Parceiro"] = prospector_parceiro
                    st.session_state.df_editado_alvaras.loc[idx, "Valor Cliente Final"] = valor_cliente
                    st.session_state.df_editado_alvaras.loc[idx, "Observacoes Financeiras"] = observacoes_financeiras
                    
                    # Salvar honorários contratuais
                    st.session_state.df_editado_alvaras.loc[idx, "Honorarios Contratuais"] = honorarios_contratuais
                    
                    # Salvar HC adicionais se foram preenchidos
                    nivel_hc = st.session_state.get(f"hc_nivel_rodrigo_{alvara_id}", 0)
                    if nivel_hc >= 1:  # HC2 está visível
                        st.session_state.df_editado_alvaras.loc[idx, "HC1"] = hc1_valor
                    if nivel_hc >= 2:  # HC3 está visível
                        st.session_state.df_editado_alvaras.loc[idx, "HC2"] = hc2_valor
                    
                    # Salvar no GitHub
                    novo_sha = save_data_to_github_seguro(
                        st.session_state.df_editado_alvaras,
                        "lista_alvaras.csv",
                        st.session_state.file_sha_alvaras
                    )
                    st.session_state.file_sha_alvaras = novo_sha
                    
                    st.success("✅ Valores salvos com sucesso!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erro ao salvar valores: {str(e)}")
            
            elif finalizar_processo:
                try:
                    idx = df[df["ID"] == alvara_id].index[0]
                    
                    # Salvar valores finais antes de finalizar
                    st.session_state.df_editado_alvaras.loc[idx, "Valor Sacado"] = valor_sacado
                    st.session_state.df_editado_alvaras.loc[idx, "Honorarios Sucumbenciais Valor"] = honorarios_sucumbenciais
                    st.session_state.df_editado_alvaras.loc[idx, "Prospector Parceiro"] = prospector_parceiro
                    st.session_state.df_editado_alvaras.loc[idx, "Valor Cliente Final"] = valor_cliente
                    st.session_state.df_editado_alvaras.loc[idx, "Observacoes Financeiras"] = observacoes_financeiras
                    
                    # Salvar honorários contratuais
                    st.session_state.df_editado_alvaras.loc[idx, "Honorarios Contratuais"] = honorarios_contratuais
                    
                    # Salvar HC adicionais se foram preenchidos
                    nivel_hc = st.session_state.get(f"hc_nivel_rodrigo_{alvara_id}", 0)
                    if nivel_hc >= 1:
                        st.session_state.df_editado_alvaras.loc[idx, "HC1"] = hc1_valor
                    if nivel_hc >= 2:
                        st.session_state.df_editado_alvaras.loc[idx, "HC2"] = hc2_valor
                    
                    # Atualizar status para finalizado
                    st.session_state.df_editado_alvaras.loc[idx, "Status"] = "Finalizado"
                    st.session_state.df_editado_alvaras.loc[idx, "Data Finalizacao"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                    st.session_state.df_editado_alvaras.loc[idx, "Finalizado Por"] = st.session_state.get("usuario", "Sistema")
                    
                    # Salvar no GitHub
                    novo_sha = save_data_to_github_seguro(
                        st.session_state.df_editado_alvaras,
                        "lista_alvaras.csv",
                        st.session_state.file_sha_alvaras
                    )
                    st.session_state.file_sha_alvaras = novo_sha
                    
                    st.success("✅ Processo finalizado com sucesso!")
                    st.session_state.show_alvara_dialog = False
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erro ao finalizar processo: {str(e)}")
    
    elif status_atual == "Finalizado":
        st.markdown("#### 🎉 Processo Finalizado")
        st.success("✅ Este processo foi concluído com sucesso!")
        
        # Mostrar valores financeiros sempre (A, B, C)
        st.markdown("**� Valores Financeiros:**")
        col_val1, col_val2, col_val3 = st.columns(3)
        
        with col_val1:
            valor_total = linha_processo.get("Valor Sacado", "")
            st.write(f"**Valor Sacado:** {safe_format_currency_alvara(valor_total)}")
        
        with col_val2:
            valor_cliente = linha_processo.get("Valor Cliente Final", "")
            st.write(f"**Valor Cliente:** {safe_format_currency_alvara(valor_cliente)}")
        
        with col_val3:
            honorarios = linha_processo.get("Honorarios Contratuais", "")
            st.write(f"**Honorários:** {safe_format_currency_alvara(honorarios)}")
        
        st.markdown("---")
        
        col_final1, col_final2 = st.columns(2)
        
        with col_final1:
            st.markdown("**� Datas importantes:**")
            st.write(f"- Cadastrado: {linha_processo.get('Data Cadastro', 'Não informado')}")
            st.write(f"- Enviado Financeiro: {linha_processo.get('Data Envio Financeiro', 'Não informado')}")
            st.write(f"- Enviado Rodrigo: {linha_processo.get('Data Envio Rodrigo', 'Não informado')}")
            st.write(f"- Finalizado: {linha_processo.get('Data Finalizacao', 'Não informado')}")
        
        with col_final2:
            st.markdown("**👥 Responsáveis:**")
            st.write(f"- Cadastrado por: {linha_processo.get('Cadastrado Por', 'Não informado')}")
            st.write(f"- Enviado Financeiro por: {linha_processo.get('Enviado Financeiro Por', 'Não informado')}")
            st.write(f"- Enviado Rodrigo por: {linha_processo.get('Enviado Rodrigo Por', 'Não informado')}")
            st.write(f"- Finalizado por: {linha_processo.get('Finalizado Por', 'Não informado')}")
        
        # Documentos anexados
        st.markdown("**📄 Documentos anexados:**")
        col_docs1, col_docs2 = st.columns(2)
        
        with col_docs1:
            if linha_processo.get("Comprovante Conta"):
                from components.functions_controle import baixar_arquivo_drive
                baixar_arquivo_drive(linha_processo["Comprovante Conta"], "📄 Comprovante Conta")
        
        with col_docs2:
            if linha_processo.get("PDF Alvará"):
                from components.functions_controle import baixar_arquivo_drive
                baixar_arquivo_drive(linha_processo["PDF Alvará"], "📄 PDF Alvará")
    
    # FALLBACK: Status não reconhecido ou sem permissão
    else:
        # Verificar se Admin pode editar qualquer coisa (Admin tem poder total)
        if perfil_usuario == "Admin":
            st.warning("⚠️ Status não reconhecido ou não implementado. Como Admin, você pode visualizar mas não há interface de edição definida.")
            st.info(f"Status atual: {status_atual}")
        else:
            st.error(f"❌ Seu perfil ({perfil_usuario}) não pode editar processos com status '{status_atual}'")
            
            if perfil_usuario == "Cadastrador":
                st.info("💡 Cadastradores só podem editar processos com status 'Cadastrado'")
            elif perfil_usuario == "Financeiro":
                st.info("💡 Financeiro pode editar processos 'Enviado para o Financeiro' e 'Financeiro - Enviado para Rodrigo'")
            elif perfil_usuario in ["Administrativo", "SAC"]:
                st.info("💡 Seu perfil pode visualizar mas não editar processos em algumas etapas")
    
def interface_cadastro_alvara(df, perfil_usuario):
    """Interface para cadastrar novos alvarás"""
    if perfil_usuario not in ["Cadastrador", "Admin"]:
        st.warning("⚠️ Apenas Cadastradores e Administradores podem criar novos alvarás")
        return
    
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
                
                # Mostrar mensagem de "salvando"
                with st.spinner("Salvando no GitHub..."):
                    novo_sha = save_data_to_github_seguro(
                        st.session_state.df_editado_alvaras,
                        "lista_alvaras.csv",
                        st.session_state.file_sha_alvaras
                    )
                
                if novo_sha and novo_sha != st.session_state.file_sha_alvaras:  # Se salvou com sucesso
                    st.session_state.file_sha_alvaras = novo_sha
                    del st.session_state["preview_novas_linhas"]
                    st.toast("✅ Todas as linhas foram salvas com sucesso!", icon="🎉")
                    st.rerun()
                else:
                    st.error("❌ Falha ao salvar. O SHA do arquivo não mudou.")
                
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
        "Honorários Sucumbenciais": "Marque se houver honorários sucumbenciais",
        "Observação Honorários": "Detalhes sobre os honorários sucumbenciais",
    }
    
    # O st.form foi removido para permitir a atualização dinâmica dos widgets.
    nova_linha = {}
    aviso_letras = False
    
    # DEFINIR COLUNAS PARA CADA LADO DO FORMULÁRIO
    colunas_esquerda = ["Processo", "Parte", "CPF", "Órgão Judicial"]
    colunas_direita = ["Pagamento", "Observação pagamento", "Honorários Sucumbenciais", "Observação Honorários"]

    col_form_1, col_form_2 = st.columns(2)

    # --- COLUNA ESQUERDA ---
    with col_form_1:
        for col in colunas_esquerda:
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
            
            elif col == "Parte":
                valor = st.text_input(
                    f"{col}",
                    key=f"input_alvaras_{col}_{st.session_state.form_reset_counter_alvaras}",
                    max_chars=100,
                    help=hints.get(col, ""),
                    placeholder="NOME COMPLETO DA PARTE"
                ).upper()

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

            elif col == "Órgão Judicial":
                # Campo selectbox + botão usando nova interface
                valor = campo_orgao_judicial(
                    label=f"{col}",
                    key_prefix=f"alvaras_{st.session_state.form_reset_counter_alvaras}"
                )
                
                # Se retornou vazio, não preencher o campo
                if not valor:
                    valor = ""
            
            nova_linha[col] = valor

    # --- COLUNA DIREITA ---
    with col_form_2:
        for col in colunas_direita:
            if col == "Pagamento":
                valor_raw = st.text_input(
                    f"{col} *",
                    key=f"input_alvaras_{col}_{st.session_state.form_reset_counter_alvaras}",
                    max_chars=20,
                    help=hints.get(col, "") + " (Campo obrigatório)",
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

    # Validação antes de submeter (REMOVIDA)
    submitted = st.button("📝 Adicionar Linha", type="primary", use_container_width=True)
        
    # Lógica de submissão
    if submitted:
        # Primeiro, processar e salvar novos valores de autocomplete
        for col, valor in nova_linha.items():
            if col == "Órgão Judicial" and valor:
                # Normalizar e verificar se é um novo órgão
                valor_normalizado = normalizar_orgao_judicial(valor)
                orgaos_existentes = obter_orgaos_judiciais()
                if valor_normalizado and valor_normalizado not in orgaos_existentes:
                    if adicionar_orgao_judicial(valor_normalizado):
                        st.success(f"🆕 Novo órgão '{valor_normalizado}' salvo permanentemente!")
                    nova_linha[col] = valor_normalizado  # Usar valor normalizado
        
        # Validações
        cpf_valor = nova_linha.get("CPF", "")
        cpf_numeros = ''.join([c for c in cpf_valor if c.isdigit()])
        pagamento_valor = nova_linha.get("Pagamento", "").strip()
        campos_obrigatorios = ["Processo", "Parte", "CPF", "Pagamento"]
        campos_vazios = [col for col in campos_obrigatorios if not nova_linha.get(col, "").strip()]
        
        if campos_vazios:
            st.error(f"❌ Preencha os campos obrigatórios: {', '.join(campos_vazios)}")
        elif cpf_valor and len(cpf_numeros) != 11:
            st.error("❌ CPF deve conter exatamente 11 números.")
        elif not pagamento_valor:
            st.error("❌ O valor do pagamento é obrigatório.")
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
            
            st.session_state.form_reset_counter_alvaras += 1
            st.toast("✅ Linha adicionada! Salve para persistir os dados.", icon="👍")
            st.rerun()

def interface_visualizar_dados(df):
    """Interface aprimorada para visualizar e gerenciar dados com paginação."""
    
    if len(df) == 0:
        st.info("ℹ️ Não há dados para visualizar.")
        return

    # Estatísticas gerais
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    with col_stat1:
        st.metric("Total de Processos", len(df))
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
    col_filtro1, col_filtro2, col_filtro3, col_filtro4 = st.columns(4)
    
    with col_filtro1:
        status_unicos = df["Status"].dropna().unique() if "Status" in df.columns else []
        status_filtro = st.multiselect("Status:", options=status_unicos, default=status_unicos)
        
    with col_filtro2:
        usuarios_unicos = df["Cadastrado Por"].dropna().unique() if "Cadastrado Por" in df.columns else []
        usuario_filtro = st.multiselect("Cadastrado Por:", options=usuarios_unicos, default=usuarios_unicos)
    
    with col_filtro3:
        # Filtro por órgão judicial (incluindo novos órgãos salvos)
        if "Orgao Judicial" in df.columns:
            orgaos_df = df["Orgao Judicial"].dropna().unique()
            orgaos_salvos = obter_orgaos_judiciais()  # Inclui novos órgãos salvos
            
            # Combina órgãos do DF com órgãos salvos
            orgaos_todos = list(set(list(orgaos_df) + orgaos_salvos))
            orgaos_todos = [o for o in orgaos_todos if o and str(o) != 'nan']
            orgaos_todos = sorted(orgaos_todos)
            
            orgao_filtro = st.multiselect("Órgão Judicial:", options=orgaos_todos, default=orgaos_todos)
        else:
            orgao_filtro = []
    
    with col_filtro4:
        # a) Alinhamento vertical do checkbox
        st.markdown("<br>", unsafe_allow_html=True)
        mostrar_todas_colunas = st.checkbox("Mostrar todas as colunas", value=False)
    
    # Aplicar filtros
    df_visualizado = df.copy()
    if status_filtro and "Status" in df.columns:
        df_visualizado = df_visualizado[df_visualizado["Status"].isin(status_filtro)]
    if usuario_filtro and "Cadastrado Por" in df.columns:
        df_visualizado = df_visualizado[df_visualizado["Cadastrado Por"].isin(usuario_filtro)]
    if orgao_filtro and "Orgao Judicial" in df.columns:
        df_visualizado = df_visualizado[df_visualizado["Orgao Judicial"].isin(orgao_filtro)]
        df_visualizado = df_visualizado[df_visualizado["Cadastrado Por"].isin(usuario_filtro)]
    
    # Selecionar colunas para exibir
    if mostrar_todas_colunas:
        colunas_exibir = df_visualizado.columns.tolist()
    else:
        colunas_principais = ["Processo", "Parte", "Pagamento", "Status", "Data Cadastro", "Cadastrado Por"]
        colunas_exibir = [col for col in colunas_principais if col in df_visualizado.columns]
    
    st.markdown("---")

    # d) Botões de download acima da tabela
    if not df_visualizado.empty:
        from io import BytesIO
        
        # Preparar dados para download
        csv_data = df_visualizado.to_csv(index=False, sep=';').encode('utf-8')
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_visualizado.to_excel(writer, index=False, sheet_name='Dados')
        excel_data = output.getvalue()

        col_down1, col_down2, _ = st.columns([1.5, 1.5, 7])
        with col_down1:
            st.download_button(
                label="📥 Baixar CSV",
                data=csv_data,
                file_name=f"dados_alvaras_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )
        with col_down2:
            st.download_button(
                label="📊 Baixar Excel",
                data=excel_data,
                file_name=f"dados_alvaras_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    # b) Lógica de Paginação
    if "current_page_visualizar" not in st.session_state:
        st.session_state.current_page_visualizar = 1
    
    items_per_page = 10
    total_registros = len(df_visualizado)
    total_pages = math.ceil(total_registros / items_per_page) if items_per_page > 0 else 1
    
    start_idx = (st.session_state.current_page_visualizar - 1) * items_per_page
    end_idx = start_idx + items_per_page
    df_paginado = df_visualizado.iloc[start_idx:end_idx]

    # Exibir dados
    st.markdown(f"### 📊 Dados ({total_registros} registros encontrados)")
    
    if not df_paginado.empty:
        # b) Contador de itens
        st.markdown(f'<p style="font-size: small; color: steelblue;">Mostrando {start_idx+1} a {min(end_idx, total_registros)} de {total_registros} registros</p>', unsafe_allow_html=True)
        
        # e) Exibir tabela sem altura fixa
        st.dataframe(
            df_paginado[colunas_exibir],
            use_container_width=True
        )
        
        # b) Controles de paginação
        st.markdown("---")
        col_nav1, col_nav2, col_nav3 = st.columns([3, 2, 3])
        with col_nav1:
            if st.session_state.current_page_visualizar > 1:
                if st.button("<< Primeira", key="viz_primeira"): st.session_state.current_page_visualizar = 1; st.rerun()
                if st.button("< Anterior", key="viz_anterior"): st.session_state.current_page_visualizar -= 1; st.rerun()
        with col_nav2:
            st.write(f"Página {st.session_state.current_page_visualizar} de {total_pages}")
        with col_nav3:
            if st.session_state.current_page_visualizar < total_pages:
                if st.button("Próxima >", key="viz_proxima"): st.session_state.current_page_visualizar += 1; st.rerun()
                if st.button("Última >>", key="viz_ultima"): st.session_state.current_page_visualizar = total_pages; st.rerun()
    else:
        st.info("Nenhum registro encontrado com os filtros aplicados.")

def confirmar_exclusao_massa_alvaras(df, processos_selecionados):
    """Função para confirmar exclusão em massa de alvarás"""
    
    @st.dialog("🗑️ Confirmar Exclusão em Massa", width="large")
    def dialog_confirmacao():
        st.error("⚠️ **ATENÇÃO:** Esta ação não pode ser desfeita!")
        
        # Mostrar processos que serão excluídos
        st.markdown(f"### Você está prestes a excluir **{len(processos_selecionados)}** processo(s):")
        
        # Converter IDs para string para garantir comparação correta
        processos_selecionados_str = [str(pid) for pid in processos_selecionados]
        processos_para_excluir = df[df["ID"].astype(str).isin(processos_selecionados_str)]
        
        for _, processo in processos_para_excluir.iterrows():
            st.markdown(f"- **{processo.get('Processo', 'Não informado')}** - {processo.get('Parte', 'Não informado')}")
        
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
                        tipo_processo="Alvará",
                        processo_numero=processo.get('Processo', 'Não informado'),
                        dados_excluidos=processo,
                        usuario=usuario_atual
                    )
                
                # Converter IDs para o mesmo tipo para garantir comparação
                processos_selecionados_str = [str(pid) for pid in processos_selecionados]
                
                # Remover processos do DataFrame
                st.session_state.df_editado_alvaras = st.session_state.df_editado_alvaras[
                    ~st.session_state.df_editado_alvaras["ID"].astype(str).isin(processos_selecionados_str)
                ].reset_index(drop=True)
                
                # Salvar no GitHub
                
                with st.spinner("Salvando alterações..."):
                    novo_sha = save_data_to_github_seguro(
                        st.session_state.df_editado_alvaras,
                        "lista_alvaras.csv",
                        "file_sha_alvaras"
                    )
                
                if novo_sha:
                    st.session_state.file_sha_alvaras = novo_sha
                    st.success(f"✅ {len(processos_selecionados)} processo(s) excluído(s) com sucesso!")
                    
                    # Resetar estado de exclusão
                    st.session_state.modo_exclusao_alvaras = False
                    st.session_state.processos_selecionados_alvaras = []
                    
                    st.rerun()
                else:
                    st.error("❌ Erro ao salvar. Exclusão cancelada.")
        
        with col_canc:
            if st.button("❌ Cancelar", use_container_width=True):
                st.rerun()
    
    dialog_confirmacao()


def interface_visualizar_dados_alvara(df):
    """Interface para visualizar dados de alvarás em formato de tabela limpa."""
    if df.empty:
        st.info("ℹ️ Não há alvarás para visualizar.")
        return

    # Cards de estatísticas compactos
    total_alvaras = len(df)
    finalizados = len(df[df["Status"] == "Finalizado"]) if "Status" in df.columns else 0
    pendentes = total_alvaras - finalizados
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 15px; border-radius: 8px; text-align: center; color: white; margin-bottom: 10px;">
            <h3 style="margin: 0; font-size: 1.8em;">{}</h3>
            <p style="margin: 3px 0 0 0; font-size: 0.9em;">Total de Alvarás</p>
        </div>
        """.format(total_alvaras), unsafe_allow_html=True)
    
    with col2:
        taxa_finalizados = (finalizados/total_alvaras*100) if total_alvaras > 0 else 0
        st.markdown("""
        <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 15px; border-radius: 8px; text-align: center; color: white; margin-bottom: 10px;">
            <h3 style="margin: 0; font-size: 1.8em;">{}</h3>
            <p style="margin: 3px 0 0 0; font-size: 0.9em;">Finalizados ({:.1f}%)</p>
        </div>
        """.format(finalizados, taxa_finalizados), unsafe_allow_html=True)
    
    with col3:
        taxa_pendentes = (pendentes/total_alvaras*100) if total_alvaras > 0 else 0
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
        status_filtro = st.selectbox("Status:", options=status_unicos, key="viz_alvara_status")
        
    with col_filtro2:
        usuarios_unicos = ["Todos"] + list(df["Cadastrado Por"].dropna().unique()) if "Cadastrado Por" in df.columns else ["Todos"]
        usuario_filtro = st.selectbox("Cadastrado Por:", options=usuarios_unicos, key="viz_alvara_user")
    
    with col_filtro3:
        orgaos_unicos = ["Todos"] + list(df["Órgão Judicial"].dropna().unique()) if "Órgão Judicial" in df.columns else ["Todos"]
        orgao_filtro = st.selectbox("Órgão Judicial:", options=orgaos_unicos, key="viz_alvara_orgao")
    
    with col_filtro4:
        pesquisa = st.text_input("🔎 Pesquisar por Requerente ou Processo:", key="viz_alvara_search")

    # Aplicar filtros
    df_filtrado = df.copy()
    
    if status_filtro != "Todos" and "Status" in df.columns:
        df_filtrado = df_filtrado[df_filtrado["Status"] == status_filtro]
    
    if usuario_filtro != "Todos" and "Cadastrado Por" in df.columns:
        df_filtrado = df_filtrado[df_filtrado["Cadastrado Por"] == usuario_filtro]
        
    if orgao_filtro != "Todos" and "Órgão Judicial" in df.columns:
        df_filtrado = df_filtrado[df_filtrado["Órgão Judicial"] == orgao_filtro]
    
    if pesquisa:
        mask = pd.Series([False] * len(df_filtrado))
        if "Requerente" in df_filtrado.columns:
            mask |= df_filtrado["Requerente"].astype(str).str.contains(pesquisa, case=False, na=False)
        if "Processo" in df_filtrado.columns:
            mask |= df_filtrado["Processo"].astype(str).str.contains(pesquisa, case=False, na=False)
        df_filtrado = df_filtrado[mask]

    # Ordenar por data de cadastro mais recente
    if "Data Cadastro" in df_filtrado.columns:
        df_filtrado["_temp_data"] = pd.to_datetime(df_filtrado["Data Cadastro"], format="%d/%m/%Y %H:%M", errors="coerce")
        df_filtrado = df_filtrado.sort_values("_temp_data", ascending=False, na_position="last")
        df_filtrado = df_filtrado.drop("_temp_data", axis=1)

    # Botões de download
    if not df_filtrado.empty:
        from io import BytesIO
        
        csv_data = df_filtrado.to_csv(index=False, sep=';').encode('utf-8')
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_filtrado.to_excel(writer, index=False, sheet_name='Alvaras')
        excel_data = output.getvalue()

        col_down1, col_down2, _ = st.columns([1.5, 1.5, 7])
        with col_down1:
            st.download_button(
                label="📥 Baixar CSV",
                data=csv_data,
                file_name=f"alvaras_relatorio_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )
        with col_down2:
            st.download_button(
                label="📊 Baixar Excel",
                data=excel_data,
                file_name=f"alvaras_relatorio_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    # Lógica de Paginação
    if "current_page_visualizar_alvara" not in st.session_state:
        st.session_state.current_page_visualizar_alvara = 1
    
    items_per_page = 15
    total_registros = len(df_filtrado)
    total_pages = math.ceil(total_registros / items_per_page) if items_per_page > 0 else 1
    
    start_idx = (st.session_state.current_page_visualizar_alvara - 1) * items_per_page
    end_idx = start_idx + items_per_page
    df_paginado = df_filtrado.iloc[start_idx:end_idx]

    # Selecionar colunas específicas do relatório
    colunas_relatorio = [
        "Processo", "Requerente", "Órgão Judicial", "Valor do Alvará", 
        "Status", "Data Cadastro", "Cadastrado Por"
    ]
    
    # Verificar quais colunas existem no DataFrame
    colunas_existentes = [col for col in colunas_relatorio if col in df_filtrado.columns]
    
    if not df_paginado.empty:
        # Contador de itens
        st.markdown(f'<p style="font-size: small; color: steelblue;">Mostrando {start_idx+1} a {min(end_idx, total_registros)} de {total_registros} registros</p>', unsafe_allow_html=True)
        
        # Cabeçalhos da tabela
        col_processo, col_parte, col_orgao, col_valor, col_status, col_data = st.columns([2, 2, 2, 1.5, 2, 1.5])
        with col_processo: st.markdown("**Processo**")
        with col_parte: st.markdown("**Requerente**")
        with col_orgao: st.markdown("**Órgão Judicial**")
        with col_valor: st.markdown("**Valor**")
        with col_status: st.markdown("**Status**")
        with col_data: st.markdown("**Data Cadastro**")
        
        st.markdown('<hr style="margin-top: 0.1rem; margin-bottom: 0.5rem;" />', unsafe_allow_html=True)
        
        # Linhas da tabela
        for _, processo in df_paginado.iterrows():
            col_processo, col_parte, col_orgao, col_valor, col_status, col_data = st.columns([2, 2, 2, 1.5, 2, 1.5])
            
            with col_processo: 
                processo_num = safe_get_value_alvara(processo, 'Processo', 'N/A')
                st.write(f"**{processo_num[:20]}{'...' if len(processo_num) > 20 else ''}**")
            
            with col_parte: 
                requerente = safe_get_value_alvara(processo, 'Requerente', 'N/A')
                st.write(f"{requerente[:25]}{'...' if len(requerente) > 25 else ''}")
                
            with col_orgao:
                orgao = safe_get_value_alvara(processo, 'Órgão Judicial', 'N/A')
                st.write(f"{orgao[:20]}{'...' if len(orgao) > 20 else ''}")
            
            with col_valor: 
                st.write(safe_format_currency_alvara(processo.get('Valor do Alvará')))
                
            with col_status:
                status_atual = safe_get_value_alvara(processo, 'Status', 'N/A')
                # Colorir status
                if status_atual == "Finalizado":
                    st.markdown(f'<span style="color: green; font-weight: bold;">🟢 {status_atual}</span>', unsafe_allow_html=True)
                elif "Financeiro" in status_atual:
                    st.markdown(f'<span style="color: orange; font-weight: bold;">🟠 {status_atual}</span>', unsafe_allow_html=True)
                elif status_atual == "Cadastrado":
                    st.markdown(f'<span style="color: #DAA520; font-weight: bold;">🟡 {status_atual}</span>', unsafe_allow_html=True)
                else:
                    st.write(status_atual)
                    
            with col_data:
                data_cadastro = safe_get_value_alvara(processo, 'Data Cadastro', 'N/A')
                # Extrair apenas a data (sem horário)
                if data_cadastro != 'N/A':
                    try:
                        data_apenas = data_cadastro.split(' ')[0]
                        st.write(data_apenas)
                    except:
                        st.write(data_cadastro)
                else:
                    st.write(data_cadastro)
        
        # Controles de paginação
        st.markdown("---")
        col_nav1, col_nav2, col_nav3 = st.columns([3, 2, 3])
        
        with col_nav1:
            if st.session_state.current_page_visualizar_alvara > 1:
                if st.button("<< Primeira", key="alvara_viz_primeira"):
                    st.session_state.current_page_visualizar_alvara = 1
                    st.rerun()
                if st.button("< Anterior", key="alvara_viz_anterior"):
                    st.session_state.current_page_visualizar_alvara -= 1
                    st.rerun()
        
        with col_nav2:
            st.write(f"Página {st.session_state.current_page_visualizar_alvara} de {total_pages}")
        
        with col_nav3:
            if st.session_state.current_page_visualizar_alvara < total_pages:
                if st.button("Próxima >", key="alvara_viz_proxima"):
                    st.session_state.current_page_visualizar_alvara += 1
                    st.rerun()
                if st.button("Última >>", key="alvara_viz_ultima"):
                    st.session_state.current_page_visualizar_alvara = total_pages
                    st.rerun()
    else:
        st.info("Nenhum registro encontrado com os filtros aplicados.")
