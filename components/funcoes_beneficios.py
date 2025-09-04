# components/funcoes_beneficios.py
import streamlit as st
import pandas as pd
import io
from datetime import datetime
import math
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
    limpar_campos_formulario
)

def safe_get_value_beneficio(data, key, default='Não cadastrado'):
    """Obtém valor de forma segura, tratando NaN e valores None"""
    value = data.get(key, default)
    if value is None:
        return default
    # Converter para string e verificar se não é 'nan'
    str_value = str(value)
    if str_value.lower() in ['nan', 'none', '']:
        return default
    return str_value

def safe_get_hc_value_beneficio(data, key, default=0.0):
    """Obtém valor de honorário contratual de forma segura para Benefícios"""
    value = data.get(key, default)
    if pd.isna(value) or value == "nan" or value == "" or value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def calcular_total_hc_beneficio(linha_beneficio):
    """Calcula o total dos honorários contratuais (HC + HC1 + HC2) para Benefícios"""
    hc = safe_get_hc_value_beneficio(linha_beneficio, "Honorarios Contratuais", 0.0)
    hc1 = safe_get_hc_value_beneficio(linha_beneficio, "HC1", 0.0)
    hc2 = safe_get_hc_value_beneficio(linha_beneficio, "HC2", 0.0)
    return hc + hc1 + hc2

def mostrar_detalhes_hc_beneficio(linha_beneficio, key_suffix=""):
    """Mostra detalhes individuais dos honorários contratuais para Benefícios"""
    total_hc = calcular_total_hc_beneficio(linha_beneficio)
    
    if total_hc > 0:
        with st.expander(f"💼 Ver Detalhes dos Honorários Contratuais (Total: R$ {total_hc:.2f})"):
            col1, col2, col3 = st.columns(3)
            
            hc = safe_get_hc_value_beneficio(linha_beneficio, "Honorarios Contratuais", 0.0)
            hc1 = safe_get_hc_value_beneficio(linha_beneficio, "HC1", 0.0)
            hc2 = safe_get_hc_value_beneficio(linha_beneficio, "HC2", 0.0)
            
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
        st.info("💼 Nenhum honorário contratual cadastrado para este benefício.")

def limpar_estados_dialogo_beneficio():
    """Limpa todos os estados relacionados aos diálogos de benefícios"""
    st.session_state.show_beneficio_dialog = False
    st.session_state.beneficio_aberto_id = None

def exibir_informacoes_basicas_beneficio(linha_beneficio, estilo="compacto"):
    """Exibe informações básicas do Benefício de forma organizada e visual
    
    Args:
        linha_beneficio: Dados da linha do Benefício
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
    
    status_atual = safe_get_value_beneficio(linha_beneficio, 'Status')
    status_class = {
        "Enviado para administrativo": "background-color: #fff3cd; color: #856404;",
        "Implantado": "background-color: #d1ecf1; color: #0c5460;",
        "Enviado para o SAC": "background-color: #e7f1ff; color: #004085;",
        "Enviado para o financeiro": "background-color: #d4edda; color: #155724;",
        "Finalizado": "background-color: #d1e7dd; color: #0f5132;"
    }.get(status_atual, "background-color: #e2e3e5; color: #383d41;")
    
    # Calcular total de honorários contratuais
    total_hc = calcular_total_hc_beneficio(linha_beneficio)
    
    st.markdown("### 📋 Resumo do Benefício")
    st.markdown(f"""
    <div class="compact-grid">
        <div class="compact-item">
            <div class="compact-label">📄 PROCESSO</div>
            <div class="compact-value">{safe_get_value_beneficio(linha_beneficio, 'Nº DO PROCESSO')}</div>
        </div>
        <div class="compact-item">
            <div class="compact-label">👤 PARTE</div>
            <div class="compact-value">{safe_get_value_beneficio(linha_beneficio, 'PARTE')}</div>
        </div>
        <div class="compact-item">
            <div class="compact-label">🆔 CPF</div>
            <div class="compact-value">{safe_get_value_beneficio(linha_beneficio, 'CPF')}</div>
        </div>
        <div class="compact-item">
            <div class="compact-label">📊 STATUS</div>
            <div class="compact-value">
                <span class="compact-status" style="{status_class}">{status_atual}</span>
            </div>
        </div>
        <div class="compact-item">
            <div class="compact-label">💼 TOTAL HC</div>
            <div class="compact-value">R$ {total_hc:.2f}</div>
        </div>
        <div class="compact-item">
            <div class="compact-label">📅 DATA CONCESSÃO</div>
            <div class="compact-value">{safe_get_value_beneficio(linha_beneficio, 'DATA DA CONCESSÃO DA LIMINAR')}</div>
        </div>
        <div class="compact-item">
            <div class="compact-label">📋 DETALHE</div>
            <div class="compact-value">{safe_get_value_beneficio(linha_beneficio, 'DETALHE PROCESSO')[:20]}...</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    # Mostrar detalhes dos honorários contratuais
    mostrar_detalhes_hc_beneficio(linha_beneficio, "compacto")

# =====================================
# CONFIGURAÇÕES DE PERFIS - BENEFÍCIOS
# =====================================

# PERFIS E PERMISSÕES
PERFIS_BENEFICIOS = {
    "Cadastrador": ["Implantado"],
    "Administrativo": ["Enviado para administrativo"],
    "SAC": ["Enviado para o SAC"],
    "Financeiro": ["Enviado para o financeiro"],
    "Admin": ["Enviado para administrativo", "Implantado", "Enviado para o SAC", "Enviado para o financeiro", "Finalizado"]
}

# CONFIGURAÇÕES DE PAGAMENTO PARCELADO
OPCOES_PAGAMENTO = {
    "À vista": {"parcelas": 1, "permite_parcelamento": False},
    "2x": {"parcelas": 2, "permite_parcelamento": True},
    "3x": {"parcelas": 3, "permite_parcelamento": True},
    "4x": {"parcelas": 4, "permite_parcelamento": True},
    "5x": {"parcelas": 5, "permite_parcelamento": True},
    "6x": {"parcelas": 6, "permite_parcelamento": True},
    "7x": {"parcelas": 7, "permite_parcelamento": True},
    "8x": {"parcelas": 8, "permite_parcelamento": True},
    "9x": {"parcelas": 9, "permite_parcelamento": True},
    "10x": {"parcelas": 10, "permite_parcelamento": True},
    "11x": {"parcelas": 11, "permite_parcelamento": True},
    "12x": {"parcelas": 12, "permite_parcelamento": True}
}

def obter_colunas_controle_beneficios():
    """Retorna lista das colunas de controle do fluxo de benefícios"""
    return [
        # Campos básicos existentes
        "Nº DO PROCESSO", "DETALHE PROCESSO", "PARTE", "CPF",
        "DATA DA CONCESSÃO DA LIMINAR", "PROVÁVEL PRAZO FATAL PARA CUMPRIMENTO",
        "OBSERVAÇÕES", "linhas", "Status", "Data Cadastro", "Cadastrado Por",
        "Data Envio Administrativo", "Enviado Administrativo Por", "Implantado",
        "Data Implantação", "Implantado Por", "Benefício Verificado", "Percentual Cobrança",
        "Data Envio SAC", "Enviado SAC Por", "Cliente Contatado", "Data Contato SAC", "Contatado Por",
        "Data Envio Financeiro", "Enviado Financeiro Por",
        
        # Novos campos para pagamento parcelado
        "Tipo Pagamento", "Numero Parcelas", "Valor Total Honorarios", "Valor Parcela",
        "Parcela_1_Status", "Parcela_1_Comprovante", "Parcela_1_Data_Pagamento",
        "Parcela_2_Status", "Parcela_2_Comprovante", "Parcela_2_Data_Pagamento",
        "Parcela_3_Status", "Parcela_3_Comprovante", "Parcela_3_Data_Pagamento",
        "Parcela_4_Status", "Parcela_4_Comprovante", "Parcela_4_Data_Pagamento",
        "Parcela_5_Status", "Parcela_5_Comprovante", "Parcela_5_Data_Pagamento",
        "Parcela_6_Status", "Parcela_6_Comprovante", "Parcela_6_Data_Pagamento",
        "Parcela_7_Status", "Parcela_7_Comprovante", "Parcela_7_Data_Pagamento",
        "Parcela_8_Status", "Parcela_8_Comprovante", "Parcela_8_Data_Pagamento",
        "Parcela_9_Status", "Parcela_9_Comprovante", "Parcela_9_Data_Pagamento",
        "Parcela_10_Status", "Parcela_10_Comprovante", "Parcela_10_Data_Pagamento",
        "Parcela_11_Status", "Parcela_11_Comprovante", "Parcela_11_Data_Pagamento",
        "Parcela_12_Status", "Parcela_12_Comprovante", "Parcela_12_Data_Pagamento",
        
        # Campos de honorários contratuais
        "Honorarios Contratuais", "HC1", "HC2",
        
        # Campos de finalização
        "Todas_Parcelas_Pagas", "Data Finalização", "Finalizado Por"
    ]

def inicializar_linha_vazia_beneficios():
    """Retorna dicionário com campos vazios para nova linha de benefício"""
    campos_controle = obter_colunas_controle_beneficios()
    linha_vazia = {}
    
    for campo in campos_controle:
        if "Status" in campo and "Parcela" in campo:
            linha_vazia[campo] = "Pendente"  # Status padrão das parcelas
        elif campo == "Todas_Parcelas_Pagas":
            linha_vazia[campo] = "Não"
        else:
            linha_vazia[campo] = ""
    
    return linha_vazia

def calcular_status_parcelas(linha_beneficio, num_parcelas):
    """Calcula quantas parcelas foram pagas e se todas estão quitadas"""
    parcelas_pagas = 0
    
    for i in range(1, int(num_parcelas) + 1):
        status_parcela = linha_beneficio.get(f"Parcela_{i}_Status", "Pendente")
        if status_parcela == "Paga":
            parcelas_pagas += 1
    
    todas_pagas = parcelas_pagas == int(num_parcelas)
    
    return parcelas_pagas, todas_pagas


# Assuntos para autocomplete
ASSUNTOS_BENEFICIOS_DEFAULT = [
    "LOAS",
    "LOAS DEFICIENTE",
    "LOAS IDOSO",
    "APOSENTADORIA POR INVALIDEZ",
    "APOSENTADORIA POR IDADE",
    "AUXILIO DOENCA",
    "AUXILIO ACIDENTE",
    "PENSAO POR MORTE",
    "SALARIO MATERNIDADE",
    "OUTROS"
]

def normalizar_assunto_beneficio(texto):
    """Normaliza nome do assunto removendo acentos e convertendo para maiúsculo"""
    if not texto:
        return ""
    import unicodedata
    # Remove acentos
    texto_normalizado = unicodedata.normalize('NFD', texto)
    texto_sem_acento = ''.join(c for c in texto_normalizado if unicodedata.category(c) != 'Mn')
    return texto_sem_acento.upper().strip()

def obter_assuntos_beneficios():
    """Retorna lista de assuntos salvos + padrões"""
    # Inicializa dados de autocomplete da sessão com dados persistidos
    inicializar_autocomplete_session()
    
    # Combina dados padrão com customizados
    assuntos_customizados = st.session_state.get("assuntos_beneficios_customizados", [])
    return sorted(list(set(ASSUNTOS_BENEFICIOS_DEFAULT + assuntos_customizados)))

STATUS_ETAPAS_BENEFICIOS = {
    1: "Enviado para administrativo",  # Começa aqui automaticamente
    2: "Implantado",
    3: "Enviado para o financeiro",
    4: "Finalizado"
}

def pode_editar_status_beneficios(status_atual, perfil_usuario):
    """Verifica se o usuário pode editar determinado status de benefício"""
    return status_atual in PERFIS_BENEFICIOS.get(perfil_usuario, [])

# =====================================
# FUNÇÕES DE INTERFACE E AÇÕES - BENEFÍCIOS
# =====================================

def toggle_beneficio_selection(beneficio_id):
    """Função callback para alternar seleção de Benefício"""
    # Garantir que a lista existe
    if "processos_selecionados_beneficios" not in st.session_state:
        st.session_state.processos_selecionados_beneficios = []
    
    # Converter para string para consistência
    beneficio_id_str = str(beneficio_id)
    
    # Remover qualquer versão duplicada (int ou str)
    st.session_state.processos_selecionados_beneficios = [
        pid for pid in st.session_state.processos_selecionados_beneficios
        if str(pid) != beneficio_id_str
    ]
    
    # Se o checkbox está marcado, adicionar à lista
    checkbox_key = f"check_beneficio_{beneficio_id}"
    if st.session_state.get(checkbox_key, False):
        st.session_state.processos_selecionados_beneficios.append(beneficio_id_str)

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

    # Inicializar estado do diálogo e paginação APENAS se não existirem
    if "show_beneficio_dialog" not in st.session_state:
        st.session_state.show_beneficio_dialog = False
    if "beneficio_aberto_id" not in st.session_state:
        st.session_state.beneficio_aberto_id = None
    if "current_page_beneficios" not in st.session_state:
        st.session_state.current_page_beneficios = 1
    
    # VERIFICAR E LIMPAR ESTADOS ÓRFÃOS DE DIÁLOGO
    # Se o diálogo está aberto mas não há ID, limpar
    if st.session_state.get("show_beneficio_dialog", False) and not st.session_state.get("beneficio_aberto_id"):
        st.session_state.show_beneficio_dialog = False
    
    # Se há ID mas não deveria mostrar o diálogo, limpar o ID
    if not st.session_state.get("show_beneficio_dialog", False) and st.session_state.get("beneficio_aberto_id"):
        st.session_state.beneficio_aberto_id = None
    
    # Inicializar estado de exclusão em massa
    if "modo_exclusao_beneficios" not in st.session_state:
        st.session_state.modo_exclusao_beneficios = False
    if "processos_selecionados_beneficios" not in st.session_state:
        st.session_state.processos_selecionados_beneficios = []
    
    # Validar consistência da lista de selecionados
    if st.session_state.processos_selecionados_beneficios:
        ids_existentes = set(df["ID"].astype(str).tolist())
        st.session_state.processos_selecionados_beneficios = [
            pid for pid in st.session_state.processos_selecionados_beneficios
            if str(pid) in ids_existentes
        ]

    # Botão para habilitar exclusão (apenas para Admin e Cadastrador)
    usuario_atual = st.session_state.get("usuario", "")
    perfil_atual = st.session_state.get("perfil_usuario", "")
    pode_excluir = (perfil_atual in ["Admin", "Cadastrador"] or usuario_atual == "admin")
    
    if pode_excluir:
        col_btn1, col_btn2, col_rest = st.columns([2, 2, 6])
        with col_btn1:
            if not st.session_state.modo_exclusao_beneficios:
                if st.button("🗑️ Habilitar Exclusão", key="habilitar_exclusao_beneficios"):
                    st.session_state.modo_exclusao_beneficios = True
                    st.session_state.processos_selecionados_beneficios = []
                    st.rerun()
            else:
                if st.button("❌ Cancelar Exclusão", key="cancelar_exclusao_beneficios"):
                    st.session_state.modo_exclusao_beneficios = False
                    st.session_state.processos_selecionados_beneficios = []
                    st.rerun()
        
        with col_btn2:
            if st.session_state.modo_exclusao_beneficios and st.session_state.processos_selecionados_beneficios:
                if st.button(f"🗑️ Excluir ({len(st.session_state.processos_selecionados_beneficios)})",
                           key="confirmar_exclusao_beneficios", type="primary"):
                    confirmar_exclusao_massa_beneficios(df, st.session_state.processos_selecionados_beneficios)
    
    # FILTROS
    col1, col2, col3, col4 = st.columns(4)
    
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
        # Filtro por assunto (se a coluna existir)
        if "ASSUNTO" in df.columns:
            assuntos_unicos = ["Todos"] + list(df["ASSUNTO"].dropna().unique())
            filtro_assunto = st.selectbox(
                "Assunto:",
                options=assuntos_unicos,
                key="beneficio_assunto_filter"
            )
        else:
            filtro_assunto = "Todos"

    with col4:
        filtro_busca = st.text_input("Buscar por Parte, CPF ou Nº Processo:", key="beneficio_search")

    # Aplicar filtros
    df_filtrado = df_ordenado.copy()
    if filtro_status != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Status"] == filtro_status]
    if filtro_tipo != "Todos":
        df_filtrado = df_filtrado[df_filtrado["TIPO DE PROCESSO"] == filtro_tipo]
    if filtro_assunto != "Todos" and "ASSUNTO" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["ASSUNTO"] == filtro_assunto]
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
        
        # Cabeçalhos dinâmicos baseados no modo de exclusão
        if st.session_state.modo_exclusao_beneficios:
            col_check, col_h1, col_h2, col_h3, col_h4, col_h5, col_h6 = st.columns([0.5, 1, 3, 2, 2, 2, 2])
            with col_check: st.markdown("**☑️**")
            with col_h1: st.markdown("**Ação**")
            with col_h2: st.markdown("**Parte**")
            with col_h3: st.markdown("**Processo**")
            with col_h4: st.markdown("**Tipo**")
            with col_h5: st.markdown("**Status**")
            with col_h6: st.markdown("**Data Cadastro**")
        else:
            col_h1, col_h2, col_h3, col_h4, col_h5, col_h6 = st.columns([1, 3, 2, 2, 2, 2])
            with col_h1: st.markdown("**Ação**")
            with col_h2: st.markdown("**Parte**")
            with col_h3: st.markdown("**Processo**")
            with col_h4: st.markdown("**Tipo**")
            with col_h5: st.markdown("**Status**")
            with col_h6: st.markdown("**Data Cadastro**")
        
        st.markdown('<hr style="margin-top: 0.1rem; margin-bottom: 0.5rem;" />', unsafe_allow_html=True)

        for _, row in df_paginado.iterrows():
            beneficio_id = row.get("ID")
            
            if st.session_state.modo_exclusao_beneficios:
                col_check, col_b1, col_b2, col_b3, col_b4, col_b5, col_b6 = st.columns([0.5, 1, 3, 2, 2, 2, 2])
                
                with col_check:
                    current_value = beneficio_id in st.session_state.processos_selecionados_beneficios
                    
                    is_selected = st.checkbox(
                        "Selecionar",
                        value=current_value,
                        key=f"check_beneficio_{beneficio_id}",
                        label_visibility="collapsed",
                        on_change=lambda bid=beneficio_id: toggle_beneficio_selection(bid)
                    )
                
                with col_b1:
                    if st.button("🔓 Abrir", key=f"abrir_beneficio_id_{beneficio_id}"):
                        # Usar sistema de timestamp para requests de diálogo
                        import time
                        timestamp = str(int(time.time() * 1000))
                        st.session_state[f"dialogo_beneficio_request_{timestamp}"] = {
                            "show_beneficio_dialog": True,
                            "beneficio_aberto_id": beneficio_id,
                            "timestamp": timestamp
                        }
                
                with col_b2: st.write(f"**{row.get('PARTE', 'N/A')}**")
                with col_b3: st.write(row.get('Nº DO PROCESSO', 'N/A'))
                with col_b4: st.write(row.get('TIPO DE PROCESSO', 'N/A'))
                with col_b5: st.write(row.get('Status', 'N/A'))
                with col_b6:
                    data_cadastro = row.get('Data Cadastro')
                    if pd.isna(data_cadastro):
                        st.write("N/A")
                    else:
                        st.write(str(data_cadastro).split(' ')[0])
            else:
                col_b1, col_b2, col_b3, col_b4, col_b5, col_b6 = st.columns([1, 3, 2, 2, 2, 2])
                
                with col_b1:
                    if st.button("🔓 Abrir", key=f"abrir_beneficio_id_{beneficio_id}"):
                        # Usar sistema de timestamp para requests de diálogo
                        import time
                        timestamp = str(int(time.time() * 1000))
                        st.session_state[f"dialogo_beneficio_request_{timestamp}"] = {
                            "show_beneficio_dialog": True,
                            "beneficio_aberto_id": beneficio_id,
                            "timestamp": timestamp
                        }
                
                with col_b2: st.write(f"**{row.get('PARTE', 'N/A')}**")
                with col_b3: st.write(row.get('Nº DO PROCESSO', 'N/A'))
                with col_b4: st.write(row.get('TIPO DE PROCESSO', 'N/A'))
                with col_b5: st.write(row.get('Status', 'N/A'))
                with col_b6:
                    data_cadastro = row.get('Data Cadastro')
                    if pd.isna(data_cadastro):
                        st.write("N/A")
                    else:
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

def interface_cadastro_beneficio(df, perfil_usuario):
    """Interface para cadastrar novos benefícios, com validações e dicas."""
    
    # LIMPAR ESTADOS DE DIÁLOGO ao entrar na aba de cadastro
    if st.session_state.get("show_beneficio_dialog", False):
        st.session_state.show_beneficio_dialog = False
    if st.session_state.get("beneficio_aberto_id") is not None:
        st.session_state.beneficio_aberto_id = None
    
    # Verificar se o usuário pode cadastrar benefícios
    if perfil_usuario not in ["Cadastrador", "Admin"]:
        st.warning("⚠️ Apenas Cadastradores e Administradores podem criar novos benefícios")
        return

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
                with st.spinner("Salvando no GitHub..."):
                    novo_sha = save_data_to_github_seguro(
                        st.session_state.df_editado_beneficios,
                        "lista_beneficios.csv",
                        "file_sha_beneficios"
                    )
                
                if novo_sha:
                    st.session_state.file_sha_beneficios = novo_sha
                    del st.session_state["preview_novas_linhas_beneficios"]
                    
                    # Garantir que nenhum diálogo seja aberto automaticamente
                    limpar_estados_dialogo_beneficio()
                    
                    st.toast("✅ Todas as linhas foram salvas com sucesso!", icon="🎉")
                    st.rerun()
                else:
                    st.error("❌ Falha ao salvar. Tente novamente.")

        with col_limpar:
            if st.button("🗑️ Descartar Linhas", type="secondary", key="descartar_beneficios"):
                num_linhas_remover = len(st.session_state["preview_novas_linhas_beneficios"])
                st.session_state.df_editado_beneficios = st.session_state.df_editado_beneficios.iloc[:-num_linhas_remover]
                del st.session_state["preview_novas_linhas_beneficios"]
                
                # Garantir que nenhum diálogo seja aberto automaticamente
                limpar_estados_dialogo_beneficio()
                
                st.warning("🗑️ Linhas descartadas!")
                st.rerun()
        
        st.markdown("---")

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
        
        # Campo de assunto (que agora inclui tipos de processo)
        assunto_selecionado = campo_assunto_beneficio(
            label="ASSUNTO/TIPO DE PROCESSO *",
            key_prefix=f"beneficio_{st.session_state.form_reset_counter_beneficios}"
        )
    
    with col2:
        data_liminar = st.date_input(
            "DATA DA CONCESSÃO DA LIMINAR",
            value=None,
            help="Opcional: Data em que a liminar foi concedida.",
            format="DD/MM/YYYY"
        )
        prazo_fatal = st.date_input(
            "PROVÁVEL PRAZO FATAL PARA CUMPRIMENTO",
            value=None,
            help="Opcional: Prazo final para o cumprimento da obrigação.",
            format="DD/MM/YYYY"
        )
        percentual_cobrado = st.number_input(
            "PERCENTUAL COBRADO (%)",
            min_value=0.0,
            max_value=100.0,
            value=30.0,
            step=0.1,
            help="Percentual de honorários cobrado do cliente (padrão: 30%)"
        )
        observacoes = st.text_area(
            "OBSERVAÇÕES",
            placeholder="Detalhes importantes sobre o caso...",
            height=100
        )
        
        # Campos de pagamento parcelado (sem título)
        tipo_pagamento = st.selectbox(
            "TIPO DE PAGAMENTO DOS HONORÁRIOS",
            list(OPCOES_PAGAMENTO.keys()),
            index=0,
            help="Selecione se o pagamento será à vista ou parcelado"
        )
        
        # Campos condicionais para pagamento parcelado
        valor_total_honorarios = None
        if OPCOES_PAGAMENTO[tipo_pagamento]["permite_parcelamento"]:
            valor_total_honorarios = st.number_input(
                "VALOR TOTAL DOS HONORÁRIOS (R$)",
                min_value=0.0,
                step=100.0,
                format="%.2f",
                help="Valor total dos honorários que será dividido em parcelas"
            )
            
            if valor_total_honorarios > 0:
                num_parcelas = OPCOES_PAGAMENTO[tipo_pagamento]["parcelas"]
                valor_parcela = valor_total_honorarios / num_parcelas
                st.info(f"💡 {num_parcelas} parcelas de R$ {valor_parcela:.2f} cada")

    submitted = st.button("📝 Adicionar Linha", type="primary", use_container_width=True)

    # Lógica de submissão
    if submitted:
        # Processar assunto selecionado e salvar permanentemente
        assunto_processado = ""
        if assunto_selecionado and assunto_selecionado.strip():
            assunto_processado = normalizar_assunto_beneficio(assunto_selecionado)
            
            # Se não está na lista, adicionar automaticamente e salvar permanentemente
            assuntos_existentes = obter_assuntos_beneficios()
            if assunto_processado and assunto_processado not in assuntos_existentes:
                if adicionar_assunto_beneficio(assunto_processado):
                    st.success(f"🆕 Novo assunto '{assunto_processado}' salvo permanentemente!")
                else:
                    st.warning(f"⚠️ Erro ao salvar novo assunto '{assunto_processado}'")
        
        # Validações
        campos_obrigatorios = {
            "Nº DO PROCESSO": processo,
            "PARTE": parte,
            "CPF": cpf,
            "ASSUNTO/TIPO DE PROCESSO": assunto_processado
        }
        campos_vazios = [nome for nome, valor in campos_obrigatorios.items() if not valor or not valor.strip()]
        
        cpf_numeros = ''.join(filter(str.isdigit, cpf))
        
        # Validação específica para pagamento parcelado
        erro_pagamento = False
        if OPCOES_PAGAMENTO[tipo_pagamento]["permite_parcelamento"]:
            if not valor_total_honorarios or valor_total_honorarios <= 0:
                st.error("❌ Para pagamento parcelado, informe o valor total dos honorários.")
                erro_pagamento = True
        
        if campos_vazios:
            st.error(f"❌ Preencha os campos obrigatórios: {', '.join(campos_vazios)}")
        elif cpf and len(cpf_numeros) != 11:
            st.error(f"❌ O CPF '{cpf}' é inválido. Deve conter 11 números.")
        elif erro_pagamento:
            pass  # Erro já mostrado acima
        else:
            
            # Calcular dados de parcelamento
            num_parcelas = OPCOES_PAGAMENTO[tipo_pagamento]["parcelas"]
            valor_parcela = 0
            if valor_total_honorarios and valor_total_honorarios > 0:
                valor_parcela = valor_total_honorarios / num_parcelas
            
            nova_linha = {
                "ID": gerar_id_unico(st.session_state.df_editado_beneficios, "ID"),
                "Nº DO PROCESSO": processo,
                "PARTE": parte,
                "CPF": cpf_numeros, # Salva apenas os números
                "TIPO DE PROCESSO": assunto_processado,  # Agora usa o assunto como tipo de processo
                "ASSUNTO": assunto_processado,
                "DATA DA CONCESSÃO DA LIMINAR": data_liminar.strftime("%d/%m/%Y") if data_liminar else "",
                "PROVÁVEL PRAZO FATAL PARA CUMPRIMENTO": prazo_fatal.strftime("%d/%m/%Y") if prazo_fatal else "",
                "PERCENTUAL COBRADO": f"{percentual_cobrado:.1f}%",
                "OBSERVAÇÕES": observacoes,
                
                # Campos de pagamento parcelado
                "Tipo Pagamento": tipo_pagamento,
                "Numero Parcelas": num_parcelas,
                "Valor Total Honorarios": f"R$ {valor_total_honorarios:.2f}" if valor_total_honorarios else "",
                "Valor Parcela": f"R$ {valor_parcela:.2f}" if valor_parcela > 0 else "",
                "Todas_Parcelas_Pagas": "Não",
                
                "Status": "Enviado para administrativo",
                "Data Cadastro": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Cadastrado Por": st.session_state.get("usuario", "Sistema")
            }
            
            # Inicializar campos de controle de parcelas
            linha_controle = inicializar_linha_vazia_beneficios()
            nova_linha.update({k: v for k, v in linha_controle.items() if k not in nova_linha})
            
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
            
            # Garantir que nenhum diálogo seja aberto automaticamente
            limpar_estados_dialogo_beneficio()
            
            st.toast("✅ Linha adicionada! Salve para persistir os dados.", icon="👍")
            st.rerun()

def interface_edicao_beneficio(df, beneficio_id, perfil_usuario):
    """
    Interface de edição com o fluxo de trabalho corrigido e adaptada para st.dialog.
    """

    linha_beneficio = df[df["ID"] == beneficio_id].iloc[0]
    status_atual = linha_beneficio.get("Status", "N/A")
    processo = linha_beneficio.get("Nº DO PROCESSO", "N/A")

    # Exibir informações básicas do benefício com layout compacto
    exibir_informacoes_basicas_beneficio(linha_beneficio, "compacto")

    if status_atual == "Enviado para administrativo" and perfil_usuario in ["Administrativo", "Admin"]:
        st.markdown("#### 🔧 Análise Administrativa")
        st.info("Após inserir os documentos no Korbil, marque a caixa abaixo e salve.")
        
        korbil_ok = st.checkbox("Carta de Concessão e Histórico de Crédito inseridos no Korbil")
        
        if st.button("💾 Salvar e Devolver para Cadastrador", type="primary", disabled=not korbil_ok):
            atualizar_status_beneficio(beneficio_id, "Implantado", df)

    elif status_atual == "Implantado" and perfil_usuario in ["Cadastrador", "Admin"]:
        st.markdown("#### 📞 Enviar para SAC")
        st.info("🔍 Processo implantado e pronto para contato com cliente via SAC.")

        if st.button("� Enviar para SAC", type="primary", use_container_width=True):
            atualizar_status_beneficio(
                beneficio_id, "Enviado para o SAC", df
            )

    elif status_atual == "Enviado para o SAC" and perfil_usuario in ["SAC", "Admin"]:
        st.markdown("#### 📞 Contato com Cliente - SAC")
        st.info("📋 Entre em contato com o cliente e marque quando concluído.")
        
        cliente_contatado = st.checkbox("Cliente contatado")
        
        if st.button("📤 Enviar para Financeiro", type="primary", disabled=not cliente_contatado):
            # Adicionar informação de que foi contatado
            atualizar_status_beneficio(beneficio_id, "Enviado para o financeiro", df,
                                     dados_adicionais={"Cliente Contatado": "Sim",
                                                      "Data Contato SAC": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                                      "Contatado Por": perfil_usuario})

    elif status_atual == "Enviado para o financeiro" and perfil_usuario in ["Financeiro", "Admin"]:
        st.markdown("#### 💰 Gestão de Pagamento")
        
        # Verificar tipo de pagamento
        tipo_pagamento = linha_beneficio.get("Tipo Pagamento", "À vista")
        num_parcelas = int(linha_beneficio.get("Numero Parcelas", 1))
        valor_total = safe_get_value_beneficio(linha_beneficio, "Valor Total Honorarios", "A definir")
        valor_parcela = safe_get_value_beneficio(linha_beneficio, "Valor Parcela", "")
        
        # Exibir informações do pagamento
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.metric("Tipo de Pagamento", tipo_pagamento)
        with col_info2:
            st.metric("Número de Parcelas", num_parcelas)
        with col_info3:
            # Tratar valores nan e formatar monetário se possível
            if valor_total and valor_total != "A definir":
                try:
                    # Se é uma string com "R$", extrair o valor
                    if "R$" in str(valor_total):
                        valor_limpo = str(valor_total).replace("R$", "").replace(",", "").strip()
                        valor_float = float(valor_limpo)
                        st.metric("Valor Total", f"R$ {valor_float:,.2f}")
                    else:
                        valor_float = float(valor_total)
                        st.metric("Valor Total", f"R$ {valor_float:,.2f}")
                except:
                    st.metric("Valor Total", "A definir")
            else:
                st.metric("Valor Total", "A definir")
        
        st.markdown("---")

        # Controle HC com botão progressivo (FORA do formulário)
        if st.button("➕ Adicionar Honorários Contratuais", key=f"btn_hc_beneficio_{beneficio_id}"):
            # Inicializar estado do botão HC se não existir
            if f"hc_nivel_beneficio_{beneficio_id}" not in st.session_state:
                st.session_state[f"hc_nivel_beneficio_{beneficio_id}"] = 0
            
            st.session_state[f"hc_nivel_beneficio_{beneficio_id}"] = (st.session_state[f"hc_nivel_beneficio_{beneficio_id}"] + 1) % 3
            st.rerun()
        
        # Inicializar estado do botão HC
        if f"hc_nivel_beneficio_{beneficio_id}" not in st.session_state:
            st.session_state[f"hc_nivel_beneficio_{beneficio_id}"] = 0
        
        # Formulário para honorários contratuais
        with st.form(f"form_hc_beneficio_{beneficio_id}"):
            
            def safe_get_hc_value(linha, campo):
                valor = linha.get(campo, "0")
                if pd.isna(valor) or valor == "nan" or valor == "" or valor is None:
                    return 0.0
                try:
                    return float(valor)
                except:
                    return 0.0
            
            honorarios_contratuais = st.number_input(
                "Honorário Contratual 1:",
                min_value=0.0,
                value=safe_get_hc_value(linha_beneficio, "Honorarios Contratuais"),
                step=0.01,
                format="%.2f",
                help="Valor dos honorários contratuais principais"
            )
            
            # Campos HC adicionais (aparecem conforme o nível do botão)
            hc1_valor, hc2_valor = 0.0, 0.0
            nivel_hc = st.session_state.get(f"hc_nivel_beneficio_{beneficio_id}", 0)
            
            if nivel_hc >= 1:  # Primeira pressão: Mostrar HC2
                hc1_valor = st.number_input(
                    "Honorário Contratual 2:",
                    min_value=0.0,
                    value=safe_get_hc_value(linha_beneficio, "HC1"),
                    step=0.01,
                    format="%.2f",
                    key=f"hc2_beneficio_{beneficio_id}"
                )
            
            if nivel_hc >= 2:  # Segunda pressão: Mostrar HC3
                hc2_valor = st.number_input(
                    "Honorário Contratual 3:",
                    min_value=0.0,
                    value=safe_get_hc_value(linha_beneficio, "HC2"),
                    step=0.01,
                    format="%.2f",
                    key=f"hc3_beneficio_{beneficio_id}"
                )
            
            # Botão salvar dentro do formulário
            submitted_hc = st.form_submit_button("💾 Salvar Honorários Contratuais", type="primary")
            
            if submitted_hc:
                try:
                    idx = df[df["ID"] == beneficio_id].index[0]
                    
                    # Salvar honorários contratuais
                    st.session_state.df_editado_beneficios.loc[idx, "Honorarios Contratuais"] = honorarios_contratuais
                    
                    # Salvar HC adicionais se foram preenchidos
                    if nivel_hc >= 1:  # HC2 está visível
                        st.session_state.df_editado_beneficios.loc[idx, "HC1"] = hc1_valor
                    if nivel_hc >= 2:  # HC3 está visível
                        st.session_state.df_editado_beneficios.loc[idx, "HC2"] = hc2_valor
                    
                    # Salvar no GitHub
                    novo_sha = save_data_to_github_seguro(
                        st.session_state.df_editado_beneficios,
                        "lista_beneficios.csv",
                        st.session_state.file_sha_beneficios
                    )
                    st.session_state.file_sha_beneficios = novo_sha
                    
                    st.success("✅ Honorários contratuais salvos com sucesso!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erro ao salvar honorários: {str(e)}")
        
        st.markdown("---")
        
        # =====================================
        # GESTÃO DE PAGAMENTO (ORIGINAL)
        # =====================================
        
        if tipo_pagamento == "À vista":
            # Pagamento à vista - interface simples
            st.info("💡 Pagamento à vista - Anexe comprovante para finalizar")
            
            pago_em_dinheiro = st.checkbox("Pago em dinheiro")
            
            comprovante = None
            if not pago_em_dinheiro:
                comprovante = st.file_uploader("Comprovante de Pagamento *", type=["pdf", "jpg", "png"])
            
            pode_finalizar = pago_em_dinheiro or comprovante is not None
            
            if st.button("✅ Finalizar Benefício", type="primary", disabled=not pode_finalizar):
                comprovante_url = ""
                tipo_pagamento_final = "Dinheiro" if pago_em_dinheiro else "Anexo"
                
                if comprovante:
                    with st.spinner("Enviando anexo..."):
                        comprovante_url = salvar_arquivo(comprovante, processo, "pagamento_beneficio")
                
                # Marcar como finalizado
                atualizar_dados_finalizacao(
                    beneficio_id, "Finalizado", df,
                    comprovante_url=comprovante_url,
                    tipo_pagamento=tipo_pagamento_final
                )
        
        else:
            # Pagamento parcelado - interface avançada
            st.markdown("#### 📋 Controle de Parcelas")
            
            parcelas_pagas, todas_pagas = calcular_status_parcelas(linha_beneficio, num_parcelas)
            
            # Status geral das parcelas
            st.metric("Parcelas Pagas", f"{parcelas_pagas}/{num_parcelas}")
            
            # Lista de parcelas para gestão
            st.markdown("##### Gerenciar Parcelas:")
            
            for i in range(1, num_parcelas + 1):
                status_parcela = linha_beneficio.get(f"Parcela_{i}_Status", "Pendente")
                data_pagamento = linha_beneficio.get(f"Parcela_{i}_Data_Pagamento", "")
                comprovante_parcela = linha_beneficio.get(f"Parcela_{i}_Comprovante", "")
                
                with st.expander(f"Parcela {i} - {valor_parcela} - Status: {status_parcela}",
                               expanded=(status_parcela == "Pendente")):
                    
                    if status_parcela == "Pendente":
                        # Permitir marcar como paga
                        col_pag1, col_pag2 = st.columns(2)
                        
                        with col_pag1:
                            pago_dinheiro_parcela = st.checkbox(f"Pago em dinheiro - Parcela {i}",
                                                              key=f"dinheiro_{beneficio_id}_{i}")
                        
                        with col_pag2:
                            if not pago_dinheiro_parcela:
                                comprovante_upload = st.file_uploader(
                                    f"Comprovante Parcela {i}",
                                    type=["pdf", "jpg", "png"],
                                    key=f"comp_parcela_{beneficio_id}_{i}"
                                )
                            else:
                                comprovante_upload = None
                        
                        # Botão para confirmar pagamento da parcela
                        pode_confirmar = pago_dinheiro_parcela or comprovante_upload is not None
                        if st.button(f"✅ Confirmar Pagamento Parcela {i}",
                                   key=f"confirmar_{beneficio_id}_{i}",
                                   disabled=not pode_confirmar):
                            
                            # Salvar comprovante se houver
                            url_comprovante = ""
                            if comprovante_upload:
                                with st.spinner(f"Salvando comprovante da parcela {i}..."):
                                    url_comprovante = salvar_arquivo(comprovante_upload, processo, f"parcela_{i}")
                            
                            # Atualizar dados da parcela
                            atualizar_pagamento_parcela(beneficio_id, i, df, url_comprovante, pago_dinheiro_parcela)
                    
                    else:
                        # Parcela já paga - mostrar informações
                        st.success(f"✅ Parcela {i} quitada")
                        if data_pagamento:
                            st.write(f"**Data:** {data_pagamento}")
                        if comprovante_parcela and comprovante_parcela != "Pago em dinheiro":
                            st.write(f"**Comprovante:** Anexado")
                        elif comprovante_parcela == "Pago em dinheiro":
                            st.write(f"**Pagamento:** Em dinheiro")
            
            # Botão para finalizar apenas se todas as parcelas estiverem pagas
            if todas_pagas:
                st.success("🎉 Todas as parcelas foram quitadas!")
                if st.button("✅ Finalizar Benefício", type="primary", key=f"finalizar_{beneficio_id}"):
                    atualizar_dados_finalizacao(beneficio_id, "Finalizado", df)
            else:
                st.warning(f"⚠️ Aguardando pagamento de {num_parcelas - parcelas_pagas} parcela(s) restante(s)")

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
                st.markdown("**Comprovante:**")
                baixar_arquivo_drive(linha_beneficio["Comprovante Pagamento"], "Baixar Comprovante")
        
            
            with col_final2:
                st.markdown("**📋 Informações do Benefício:**")
                st.write(f"- Benefício: {linha_beneficio.get('Benefício Verificado', 'N/A')}")
                st.write(f"- Percentual: {linha_beneficio.get('Percentual Cobrança', 'N/A')}")
                st.write(f"- Finalizado por: {linha_beneficio.get('Finalizado Por', 'N/A')}")
            
            # Timeline
            st.markdown("**📅 Timeline do Benefício:**")
            timeline_data = []
            if linha_beneficio.get("Data Cadastro"):
                timeline_data.append(f"• **Cadastrado:** {linha_beneficio['Data Cadastro']} por {linha_beneficio.get('Cadastrado Por', 'Não cadastrado')}")
            if linha_beneficio.get("Data Envio Administrativo"):
                timeline_data.append(f"• **Enviado para Administrativo:** {linha_beneficio['Data Envio Administrativo']} por {linha_beneficio.get('Enviado Administrativo Por', 'Não cadastrado')}")
            if linha_beneficio.get("Data Implantação"):
                timeline_data.append(f"• **Implantado:** {linha_beneficio['Data Implantação']} por {linha_beneficio.get('Implantado Por', 'Não cadastrado')}")
            if linha_beneficio.get("Data Envio SAC"):
                timeline_data.append(f"• **Enviado para SAC:** {linha_beneficio['Data Envio SAC']} por {linha_beneficio.get('Enviado SAC Por', 'Não cadastrado')}")
            if linha_beneficio.get("Data Contato SAC"):
                timeline_data.append(f"• **Cliente Contatado pelo SAC:** {linha_beneficio['Data Contato SAC']} por {linha_beneficio.get('Contatado Por', 'Não cadastrado')}")
            if linha_beneficio.get("Data Envio Financeiro"):
                timeline_data.append(f"• **Enviado para Financeiro:** {linha_beneficio['Data Envio Financeiro']} por {linha_beneficio.get('Enviado Financeiro Por', 'Não cadastrado')}")
            if linha_beneficio.get("Data Finalização"):
                timeline_data.append(f"• **Finalizado:** {linha_beneficio['Data Finalização']} por {linha_beneficio.get('Finalizado Por', 'Não cadastrado')}")
            
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
    
    elif novo_status == "Enviado para o SAC":
        st.session_state.df_editado_beneficios.loc[idx, "Data Envio SAC"] = data_atual
        st.session_state.df_editado_beneficios.loc[idx, "Enviado SAC Por"] = usuario_atual
    
    elif novo_status == "Enviado para o financeiro":
        st.session_state.df_editado_beneficios.loc[idx, "Data Envio Financeiro"] = data_atual
        st.session_state.df_editado_beneficios.loc[idx, "Enviado Financeiro Por"] = usuario_atual
        # Salva os novos campos de valor e percentual
        if 'valor_beneficio' in kwargs:
            st.session_state.df_editado_beneficios.loc[idx, "Valor do Benefício"] = kwargs['valor_beneficio']
        if 'percentual_cobranca' in kwargs:
            st.session_state.df_editado_beneficios.loc[idx, "Percentual Cobrança"] = kwargs['percentual_cobranca']
        
        # Adicionar dados adicionais se fornecidos
        if 'dados_adicionais' in kwargs:
            for campo, valor in kwargs['dados_adicionais'].items():
                st.session_state.df_editado_beneficios.loc[idx, campo] = valor

    # Salvar e fechar
    novo_sha = save_data_to_github_seguro(st.session_state.df_editado_beneficios, "lista_beneficios.csv", "file_sha_beneficios")
    if novo_sha:
        st.session_state.file_sha_beneficios = novo_sha
        st.toast(f"Status atualizado para: {novo_status}", icon="✅")
        limpar_estados_dialogo_beneficio()
        st.rerun()
    else:
        st.error("Falha ao salvar a atualização.")

def atualizar_pagamento_parcela(beneficio_id, numero_parcela, df, url_comprovante="", pago_dinheiro=False):
    """Atualiza o status de pagamento de uma parcela específica"""
    try:
        idx = df[df["ID"] == beneficio_id].index[0]
        
        # Atualizar campos da parcela
        st.session_state.df_editado_beneficios.loc[idx, f"Parcela_{numero_parcela}_Status"] = "Paga"
        st.session_state.df_editado_beneficios.loc[idx, f"Parcela_{numero_parcela}_Data_Pagamento"] = datetime.now().strftime("%d/%m/%Y")
        
        if pago_dinheiro:
            st.session_state.df_editado_beneficios.loc[idx, f"Parcela_{numero_parcela}_Comprovante"] = "Pago em dinheiro"
        else:
            st.session_state.df_editado_beneficios.loc[idx, f"Parcela_{numero_parcela}_Comprovante"] = url_comprovante
        
        # Verificar se todas as parcelas foram pagas
        linha_beneficio = st.session_state.df_editado_beneficios.loc[idx]
        num_parcelas = int(linha_beneficio.get("Numero Parcelas", 1))
        parcelas_pagas, todas_pagas = calcular_status_parcelas(linha_beneficio, num_parcelas)
        
        # Atualizar status geral
        if todas_pagas:
            st.session_state.df_editado_beneficios.loc[idx, "Todas_Parcelas_Pagas"] = "Sim"
        
        # Salvar no GitHub
        novo_sha = save_data_to_github_seguro(
            st.session_state.df_editado_beneficios,
            "lista_beneficios.csv",
            "file_sha_beneficios"
        )
        
        if novo_sha:
            st.session_state.file_sha_beneficios = novo_sha
            st.success(f"✅ Parcela {numero_parcela} marcada como paga!")
            st.rerun()
        else:
            st.error("❌ Erro ao salvar. Tente novamente.")
            
    except Exception as e:
        st.error(f"❌ Erro ao atualizar parcela: {e}")

def atualizar_dados_finalizacao(beneficio_id, novo_status, df, comprovante_url="", tipo_pagamento=""):
    """Atualiza os dados de finalização de um benefício, salva e fecha o diálogo."""

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
    
    # Atualizar campos de pagamento apenas se fornecidos
    if comprovante_url:
        st.session_state.df_editado_beneficios.loc[idx, "Comprovante Pagamento"] = comprovante_url
    if tipo_pagamento:
        st.session_state.df_editado_beneficios.loc[idx, "Tipo Pagamento"] = tipo_pagamento

    # Salvar e fechar
    novo_sha = save_data_to_github_seguro(st.session_state.df_editado_beneficios, "lista_beneficios.csv", "file_sha_beneficios")
    if novo_sha:
        st.session_state.file_sha_beneficios = novo_sha
        st.toast("Benefício finalizado com sucesso!", icon="🎉")
        st.balloons()
        limpar_estados_dialogo_beneficio()
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

    col_filtro1, col_filtro2, col_filtro3, col_filtro4 = st.columns([2, 2, 2, 3])
    
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
        if "ASSUNTO" in df_visualizado.columns:
            assunto_options = ["Todos"] + list(df_visualizado["ASSUNTO"].dropna().unique())
            assunto_filtro = st.selectbox("Filtrar por Assunto:", options=assunto_options, key="vis_assunto_beneficio")
            if assunto_filtro != "Todos":
                df_visualizado = df_visualizado[df_visualizado["ASSUNTO"] == assunto_filtro]
    
    with col_filtro4:
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

    # Tabela com dados paginados em formato de colunas (igual ao gerenciar)
    if not df_paginado.empty:
        st.markdown(f'<p style="font-size: small; color: steelblue;">Mostrando {start_idx+1} a {min(end_idx, total_registros)} de {total_registros} registros</p>', unsafe_allow_html=True)
        
        # Cabeçalho da tabela
        st.markdown("---")
        col_h1, col_h2, col_h3, col_h4, col_h5, col_h6 = st.columns([1, 3, 2, 2, 2, 2])
        with col_h1: st.markdown("**Ação**")
        with col_h2: st.markdown("**Parte**")
        with col_h3: st.markdown("**Nº Processo**")
        with col_h4: st.markdown("**Tipo Processo**")
        with col_h5: st.markdown("**Status**")
        with col_h6: st.markdown("**Data Cadastro**")
        
        # Linhas dos dados
        for _, row in df_paginado.iterrows():
            beneficio_id = row.get("ID")
            
            col_b1, col_b2, col_b3, col_b4, col_b5, col_b6 = st.columns([1, 3, 2, 2, 2, 2])
            
            with col_b1:
                if st.button("🔓 Abrir", key=f"vis_abrir_beneficio_id_{beneficio_id}"):
                    # Usar sistema de timestamp para requests de diálogo
                    import time
                    timestamp = str(int(time.time() * 1000))
                    st.session_state[f"dialogo_beneficio_request_{timestamp}"] = {
                        "show_beneficio_dialog": True,
                        "beneficio_aberto_id": beneficio_id,
                        "timestamp": timestamp
                    }
            
            with col_b2: st.write(f"**{safe_get_value_beneficio(row, 'PARTE')}**")
            with col_b3: st.write(safe_get_value_beneficio(row, 'Nº DO PROCESSO'))
            with col_b4: st.write(safe_get_value_beneficio(row, 'TIPO DE PROCESSO'))
            with col_b5: st.write(safe_get_value_beneficio(row, 'Status'))
            with col_b6:
                data_cadastro = row.get('Data Cadastro')
                if pd.isna(data_cadastro) or data_cadastro == "nan" or data_cadastro == "":
                    st.write("Não informado")
                else:
                    try:
                        st.write(str(data_cadastro).split(' ')[0])
                    except:
                        st.write("Não informado")
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

def confirmar_exclusao_massa_beneficios(df, processos_selecionados):
    """Função para confirmar exclusão em massa de benefícios"""
    
    @st.dialog("🗑️ Confirmar Exclusão em Massa", width="large")
    def dialog_confirmacao():
        st.error("⚠️ **ATENÇÃO:** Esta ação não pode ser desfeita!")
        
        # Mostrar processos que serão excluídos
        st.markdown(f"### Você está prestes a excluir **{len(processos_selecionados)}** processo(s):")
        
        # Converter IDs para string para garantir comparação correta
        processos_selecionados_str = [str(pid) for pid in processos_selecionados]
        processos_para_excluir = df[df["ID"].astype(str).isin(processos_selecionados_str)]
        
        for _, processo in processos_para_excluir.iterrows():
            st.markdown(f"- **{processo.get('Nº DO PROCESSO', 'N/A')}** - {processo.get('PARTE', 'N/A')}")
        
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
                        tipo_processo="Benefício",
                        processo_numero=processo.get('Nº DO PROCESSO', 'N/A'),
                        dados_excluidos=processo,
                        usuario=usuario_atual
                    )
                
                # Converter IDs para o mesmo tipo para garantir comparação
                processos_selecionados_str = [str(pid) for pid in processos_selecionados]
                
                # Remover processos do DataFrame
                st.session_state.df_editado_beneficios = st.session_state.df_editado_beneficios[
                    ~st.session_state.df_editado_beneficios["ID"].astype(str).isin(processos_selecionados_str)
                ].reset_index(drop=True)
                
                # Salvar no GitHub
                with st.spinner("Salvando alterações..."):
                    novo_sha = save_data_to_github_seguro(
                        st.session_state.df_editado_beneficios,
                        "lista_beneficios.csv",
                        "file_sha_beneficios"
                    )
                
                if novo_sha:
                    st.session_state.file_sha_beneficios = novo_sha
                    st.success(f"✅ {len(processos_selecionados)} processo(s) excluído(s) com sucesso!")
                    
                    # Resetar estado de exclusão
                    st.session_state.modo_exclusao_beneficios = False
                    st.session_state.processos_selecionados_beneficios = []
                    
                    st.rerun()
                else:
                    st.error("❌ Erro ao salvar. Exclusão cancelada.")
        
        with col_canc:
            if st.button("❌ Cancelar", use_container_width=True):
                st.rerun()
    
    dialog_confirmacao()


def interface_visualizar_dados_beneficio(df):
    """Interface para visualizar dados de benefícios em formato de tabela limpa."""
    
    # LIMPAR ESTADOS DE DIÁLOGO ao entrar na aba de visualização
    if st.session_state.get("show_beneficio_dialog", False):
        st.session_state.show_beneficio_dialog = False
    if st.session_state.get("beneficio_aberto_id") is not None:
        st.session_state.beneficio_aberto_id = None
    
    if df.empty:
        st.info("ℹ️ Não há benefícios para visualizar.")
        return

    # Cards de estatísticas compactos
    total_beneficios = len(df)
    finalizados = len(df[df["Status"] == "Finalizado"]) if "Status" in df.columns else 0
    pendentes = total_beneficios - finalizados
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 15px; border-radius: 8px; text-align: center; color: white; margin-bottom: 10px;">
            <h3 style="margin: 0; font-size: 1.8em;">{}</h3>
            <p style="margin: 3px 0 0 0; font-size: 0.9em;">Total de Benefícios</p>
        </div>
        """.format(total_beneficios), unsafe_allow_html=True)
    
    with col2:
        taxa_finalizados = (finalizados/total_beneficios*100) if total_beneficios > 0 else 0
        st.markdown("""
        <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 15px; border-radius: 8px; text-align: center; color: white; margin-bottom: 10px;">
            <h3 style="margin: 0; font-size: 1.8em;">{}</h3>
            <p style="margin: 3px 0 0 0; font-size: 0.9em;">Finalizados ({:.1f}%)</p>
        </div>
        """.format(finalizados, taxa_finalizados), unsafe_allow_html=True)
    
    with col3:
        taxa_pendentes = (pendentes/total_beneficios*100) if total_beneficios > 0 else 0
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
        status_filtro = st.selectbox("Status:", options=status_unicos, key="viz_beneficio_status")
        
    with col_filtro2:
        usuarios_unicos = ["Todos"] + list(df["Cadastrado Por"].dropna().unique()) if "Cadastrado Por" in df.columns else ["Todos"]
        usuario_filtro = st.selectbox("Cadastrado Por:", options=usuarios_unicos, key="viz_beneficio_user")
    
    with col_filtro3:
        tipos_unicos = ["Todos"] + list(df["TIPO DE PROCESSO"].dropna().unique()) if "TIPO DE PROCESSO" in df.columns else ["Todos"]
        tipo_filtro = st.selectbox("Tipo de Processo:", options=tipos_unicos, key="viz_beneficio_tipo")
    
    with col_filtro4:
        pesquisa = st.text_input("🔎 Pesquisar por Parte ou Processo:", key="viz_beneficio_search")

    # Aplicar filtros
    df_filtrado = df.copy()
    
    if status_filtro != "Todos" and "Status" in df.columns:
        df_filtrado = df_filtrado[df_filtrado["Status"] == status_filtro]
    
    if usuario_filtro != "Todos" and "Cadastrado Por" in df.columns:
        df_filtrado = df_filtrado[df_filtrado["Cadastrado Por"] == usuario_filtro]
        
    if tipo_filtro != "Todos" and "TIPO DE PROCESSO" in df.columns:
        df_filtrado = df_filtrado[df_filtrado["TIPO DE PROCESSO"] == tipo_filtro]
    
    if pesquisa:
        mask = pd.Series([False] * len(df_filtrado))
        if "PARTE" in df_filtrado.columns:
            mask |= df_filtrado["PARTE"].astype(str).str.contains(pesquisa, case=False, na=False)
        if "Nº DO PROCESSO" in df_filtrado.columns:
            mask |= df_filtrado["Nº DO PROCESSO"].astype(str).str.contains(pesquisa, case=False, na=False)
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
            df_filtrado.to_excel(writer, index=False, sheet_name='Beneficios')
        excel_data = output.getvalue()

        col_down1, col_down2, _ = st.columns([1.5, 1.5, 7])
        with col_down1:
            st.download_button(
                label="📥 Baixar CSV",
                data=csv_data,
                file_name=f"beneficios_relatorio_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )
        with col_down2:
            st.download_button(
                label="📊 Baixar Excel",
                data=excel_data,
                file_name=f"beneficios_relatorio_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    # Lógica de Paginação
    if "current_page_visualizar_beneficio" not in st.session_state:
        st.session_state.current_page_visualizar_beneficio = 1
    
    items_per_page = 15
    total_registros = len(df_filtrado)
    total_pages = math.ceil(total_registros / items_per_page) if items_per_page > 0 else 1
    
    start_idx = (st.session_state.current_page_visualizar_beneficio - 1) * items_per_page
    end_idx = start_idx + items_per_page
    df_paginado = df_filtrado.iloc[start_idx:end_idx]

    # Selecionar colunas específicas do relatório
    colunas_relatorio = [
        "Nº DO PROCESSO", "PARTE", "TIPO DE PROCESSO", "NB",
        "Valor Pago", "Status", "Data Cadastro", "Cadastrado Por"
    ]
    
    # Verificar quais colunas existem no DataFrame
    colunas_existentes = [col for col in colunas_relatorio if col in df_filtrado.columns]
    
    if not df_paginado.empty:
        # Contador de itens
        st.markdown(f'<p style="font-size: small; color: steelblue;">Mostrando {start_idx+1} a {min(end_idx, total_registros)} de {total_registros} registros</p>', unsafe_allow_html=True)
        
        # Cabeçalhos da tabela
        col_processo, col_parte, col_tipo, col_nb, col_valor, col_status, col_data = st.columns([2, 2, 1.5, 1, 1.5, 1.5, 1.5])
        with col_processo: st.markdown("**Processo**")
        with col_parte: st.markdown("**Parte**")
        with col_tipo: st.markdown("**Tipo**")
        with col_nb: st.markdown("**NB**")
        with col_valor: st.markdown("**Valor Pago**")
        with col_status: st.markdown("**Status**")
        with col_data: st.markdown("**Data Cadastro**")
        
        st.markdown('<hr style="margin-top: 0.1rem; margin-bottom: 0.5rem;" />', unsafe_allow_html=True)
        
        # Linhas da tabela
        for _, beneficio in df_paginado.iterrows():
            col_processo, col_parte, col_tipo, col_nb, col_valor, col_status, col_data = st.columns([2, 2, 1.5, 1, 1.5, 1.5, 1.5])
            
            with col_processo:
                processo = safe_get_value_beneficio(beneficio, 'Nº DO PROCESSO', 'N/A')
                st.write(f"**{processo[:18]}{'...' if len(processo) > 18 else ''}**")
            
            with col_parte:
                parte = safe_get_value_beneficio(beneficio, 'PARTE', 'N/A')
                st.write(f"{parte[:20]}{'...' if len(parte) > 20 else ''}")
                
            with col_tipo:
                tipo = safe_get_value_beneficio(beneficio, 'TIPO DE PROCESSO', 'N/A')
                st.write(f"{tipo[:12]}{'...' if len(tipo) > 12 else ''}")
                
            with col_nb:
                nb = safe_get_value_beneficio(beneficio, 'NB', 'N/A')
                st.write(nb)
            
            with col_valor:
                valor_pago = beneficio.get('Valor Pago', 0)
                if valor_pago and str(valor_pago) != 'nan':
                    try:
                        valor_num = float(valor_pago)
                        st.write(f"R$ {valor_num:,.2f}")
                    except:
                        st.write("Não informado")
                else:
                    st.write("Não informado")
                
            with col_status:
                status_atual = safe_get_value_beneficio(beneficio, 'Status', 'N/A')
                # Colorir status
                if status_atual == "Finalizado":
                    st.markdown(f'<span style="color: green; font-weight: bold;">🟢 {status_atual}</span>', unsafe_allow_html=True)
                elif "financeiro" in status_atual.lower():
                    st.markdown(f'<span style="color: orange; font-weight: bold;">🟠 {status_atual}</span>', unsafe_allow_html=True)
                elif "administrativo" in status_atual.lower():
                    st.markdown(f'<span style="color: blue; font-weight: bold;">🔵 {status_atual}</span>', unsafe_allow_html=True)
                elif "implantado" in status_atual.lower():
                    st.markdown(f'<span style="color: purple; font-weight: bold;">🟣 {status_atual}</span>', unsafe_allow_html=True)
                else:
                    st.write(status_atual)
                    
            with col_data:
                data_cadastro = safe_get_value_beneficio(beneficio, 'Data Cadastro', 'N/A')
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
            if st.session_state.current_page_visualizar_beneficio > 1:
                if st.button("<< Primeira", key="beneficio_viz_primeira"):
                    st.session_state.current_page_visualizar_beneficio = 1
                    st.rerun()
                if st.button("< Anterior", key="beneficio_viz_anterior"):
                    st.session_state.current_page_visualizar_beneficio -= 1
                    st.rerun()
        
        with col_nav2:
            st.write(f"Página {st.session_state.current_page_visualizar_beneficio} de {total_pages}")
        
        with col_nav3:
            if st.session_state.current_page_visualizar_beneficio < total_pages:
                if st.button("Próxima >", key="beneficio_viz_proxima"):
                    st.session_state.current_page_visualizar_beneficio += 1
                    st.rerun()
                if st.button("Última >>", key="beneficio_viz_ultima"):
                    st.session_state.current_page_visualizar_beneficio = total_pages
                    st.rerun()
    else:
        st.info("Nenhum registro encontrado com os filtros aplicados.")
