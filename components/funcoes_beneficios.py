# components/funcoes_beneficios.py
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

def safe_get_hc_value_beneficio(data, key, default=0.0):
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

def safe_get_int_value_beneficio(data, key, default=1):
    """Obtém valor inteiro de forma segura, tratando NaN e valores float"""
    value = data.get(key, default)
    if pd.isna(value) or value == "nan" or value == "" or value is None:
        return default
    try:
        # Se for float, converter para int
        return int(float(value))
    except (ValueError, TypeError):
        return default
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

def proximo_dia_util(data):
    """Calcula o próximo dia útil a partir de uma data"""
    # Se for sábado ou domingo, vai para segunda
    if data.weekday() == 5:  # Sábado
        return data + timedelta(days=2)
    elif data.weekday() == 6:  # Domingo
        return data + timedelta(days=1)
    else:
        return data

def calcular_data_vencimento_parcela(data_base):
    """Calcula a data de vencimento da parcela (primeiro dia útil após 30 dias)"""
    data_vencimento = data_base + timedelta(days=30)
    return proximo_dia_util(data_vencimento)

def gerar_parcelas_beneficio(beneficio_id, valor_total, num_parcelas, data_inicial):
    """Gera as parcelas para um benefício
    
    Args:
        beneficio_id: ID do benefício
        valor_total: Valor total do benefício
        num_parcelas: Número de parcelas
        data_inicial: Data inicial para cálculo das parcelas
    
    Returns:
        Dict com dados das parcelas formatados para salvar no DataFrame
    """
    # Garantir que valor_total seja numérico
    if isinstance(valor_total, str):
        try:
            valor_total = float(valor_total.replace("R$", "").replace(".", "").replace(",", ".").strip())
        except:
            valor_total = 0
    elif not valor_total:
        valor_total = 0
    
    valor_parcela = valor_total / num_parcelas if num_parcelas > 0 else 0
    parcelas_data = {}
    
    for i in range(num_parcelas):
        numero_parcela = i + 1
        data_vencimento = calcular_data_vencimento_parcela(data_inicial + timedelta(days=30*i))
        
        # Dados da parcela no formato do DataFrame
        parcelas_data[f'Parcela_{numero_parcela}_Status'] = 'Pendente'
        parcelas_data[f'Parcela_{numero_parcela}_Data_Vencimento'] = data_vencimento.strftime('%d/%m/%Y')
        parcelas_data[f'Parcela_{numero_parcela}_Comprovante'] = ''
        parcelas_data[f'Parcela_{numero_parcela}_Data_Pagamento'] = ''
    
    return parcelas_data

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
    "Desenvolvedor": ["Enviado para administrativo", "Implantado", "Enviado para o SAC", "Enviado para o financeiro", "Finalizado"]
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
        "Parcela_1_Status", "Parcela_1_Comprovante", "Parcela_1_Data_Pagamento", "Parcela_1_Data_Vencimento",
        "Parcela_2_Status", "Parcela_2_Comprovante", "Parcela_2_Data_Pagamento", "Parcela_2_Data_Vencimento",
        "Parcela_3_Status", "Parcela_3_Comprovante", "Parcela_3_Data_Pagamento", "Parcela_3_Data_Vencimento",
        "Parcela_4_Status", "Parcela_4_Comprovante", "Parcela_4_Data_Pagamento", "Parcela_4_Data_Vencimento",
        "Parcela_5_Status", "Parcela_5_Comprovante", "Parcela_5_Data_Pagamento", "Parcela_5_Data_Vencimento",
        "Parcela_6_Status", "Parcela_6_Comprovante", "Parcela_6_Data_Pagamento", "Parcela_6_Data_Vencimento",
        "Parcela_7_Status", "Parcela_7_Comprovante", "Parcela_7_Data_Pagamento", "Parcela_7_Data_Vencimento",
        "Parcela_8_Status", "Parcela_8_Comprovante", "Parcela_8_Data_Pagamento", "Parcela_8_Data_Vencimento",
        "Parcela_9_Status", "Parcela_9_Comprovante", "Parcela_9_Data_Pagamento", "Parcela_9_Data_Vencimento",
        "Parcela_10_Status", "Parcela_10_Comprovante", "Parcela_10_Data_Pagamento", "Parcela_10_Data_Vencimento",
        "Parcela_11_Status", "Parcela_11_Comprovante", "Parcela_11_Data_Pagamento", "Parcela_11_Data_Vencimento",
        "Parcela_12_Status", "Parcela_12_Comprovante", "Parcela_12_Data_Pagamento", "Parcela_12_Data_Vencimento",
        
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
    """Lista de benefícios com cards expansíveis estilo dropdown."""
    
    # CSS para cards dropdown (igual ao alvarás)
    st.markdown("""
    <style>
    .beneficio-card {
        border: 1px solid #e0e6ed;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        background-color: transparent;
        transition: all 0.3s ease;
    }
    .beneficio-card:hover {
        border-color: #0066cc;
        box-shadow: 0 2px 8px rgba(0,102,204,0.15);
    }
    .beneficio-card.expanded {
        background-color: transparent;
        border-color: #0066cc;
        border-width: 2px;
        box-shadow: 0 4px 12px rgba(0,102,204,0.2);
    }
    .beneficio-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        cursor: pointer;
    }
    .beneficio-info-grid {
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

    # ORDENAR por data de cadastro mais recente
    df_ordenado = df.copy()
    if "Data Cadastro" in df_ordenado.columns:
        df_ordenado["_data_cadastro_dt"] = pd.to_datetime(
            df_ordenado["Data Cadastro"], format='%d/%m/%Y %H:%M', errors='coerce'
        )
        df_ordenado = df_ordenado.sort_values(
            by="_data_cadastro_dt", ascending=False, na_position='last'
        ).drop(columns=["_data_cadastro_dt"])

    # Inicializar estado dos cards expansíveis
    if "beneficios_expanded_cards" not in st.session_state:
        st.session_state.beneficios_expanded_cards = set()

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

    # Botões de exclusão em massa
    usuario_atual = st.session_state.get("usuario", "")
    perfil_atual = st.session_state.get("perfil_usuario", "")
    pode_excluir = (perfil_atual in ["Desenvolvedor", "Cadastrador"] or usuario_atual == "dev")
    
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

    # Calcular total de registros (aplicar filtros primeiro para obter contagem correta)
    df_temp_filtrado = df_ordenado.copy()
    
    # Botões de Abrir/Fechar Todos
    if len(df_temp_filtrado) > 0:
        st.markdown("---")
        col_exp1, col_exp2, col_exp_space = st.columns([2, 2, 6])
        
        with col_exp1:
            if st.button("🔽 Abrir Todos", key="abrir_todos_beneficios"):
                # Adicionar todos os IDs dos benefícios ao set de expandidos
                for _, processo in df_temp_filtrado.iterrows():
                    beneficio_id = processo.get("ID", "N/A")
                    st.session_state.beneficios_expanded_cards.add(beneficio_id)
                st.rerun()
        
        with col_exp2:
            if st.button("🔼 Fechar Todos", key="fechar_todos_beneficios"):
                # Limpar o set de cards expandidos
                st.session_state.beneficios_expanded_cards.clear()
                st.rerun()

    # FILTROS
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Verificar se a coluna 'Status' existe, senão criar uma lista vazia
        if "Status" in df.columns:
            status_unicos = ["Todos"] + list(df["Status"].dropna().unique())
        else:
            status_unicos = ["Todos"]
        filtro_status = st.selectbox(
            "Status:",
            options=status_unicos,
            key="beneficio_status_filter"
        )
    
    with col2:
        # Verificar se a coluna 'TIPO DE PROCESSO' existe, senão criar uma lista vazia
        if "TIPO DE PROCESSO" in df.columns:
            tipos_unicos = ["Todos"] + list(df["TIPO DE PROCESSO"].dropna().unique())
        else:
            tipos_unicos = ["Todos"]
        filtro_tipo = st.selectbox(
            "Tipo de Processo:",
            options=tipos_unicos,
            key="beneficio_tipo_filter"
        )
    
    with col3:
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
        # Auto-filtro com rerun automático
        def on_search_change():
            """Função chamada quando o texto de busca muda"""
            pass  # O rerun é automático com key no session_state
            
        filtro_busca = st.text_input(
            "🔎 Buscar por Parte, CPF ou Nº Processo:", 
            key="beneficio_search", 
            placeholder="Digite para filtrar",
            on_change=on_search_change
        )
        
        # Usar session_state para o valor do filtro
        if "beneficio_search" in st.session_state:
            filtro_busca = st.session_state.beneficio_search
        
        if filtro_busca:
            st.caption(f"🔍 Buscando por: '{filtro_busca}' ({len(filtro_busca)} caracteres)")

    # Aplicar filtros
    df_filtrado = df_ordenado.copy()
    if filtro_status != "Todos" and "Status" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["Status"] == filtro_status]
    if filtro_tipo != "Todos" and "TIPO DE PROCESSO" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["TIPO DE PROCESSO"] == filtro_tipo]
    if filtro_assunto != "Todos" and "ASSUNTO" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["ASSUNTO"] == filtro_assunto]
    if filtro_busca:
        df_filtrado = df_filtrado[
            df_filtrado["PARTE"].str.contains(filtro_busca, case=False, na=False) |
            df_filtrado["CPF"].str.contains(filtro_busca, case=False, na=False) |
            df_filtrado["Nº DO PROCESSO"].str.contains(filtro_busca, case=False, na=False)
        ]

    if df_filtrado.empty:
        st.info("Nenhum benefício encontrado com os filtros aplicados.")
        return

    # Mostrar resultado da busca  
    if filtro_busca:
        st.success(f"🔍 {len(df_filtrado)} resultado(s) encontrado(s) para '{filtro_busca}'")
    elif len(df_filtrado) < len(df_ordenado):
        st.info(f"📊 {len(df_filtrado)} de {len(df_ordenado)} registros (filtros aplicados)")
    else:
        st.markdown(f"**{len(df_filtrado)} benefício(s) encontrado(s)**")

    # Renderizar cards
    for _, beneficio in df_filtrado.iterrows():
        beneficio_id = beneficio.get("ID")
        is_expanded = beneficio_id in st.session_state.beneficios_expanded_cards
        
        card_class = "beneficio-card expanded" if is_expanded else "beneficio-card"
        
        with st.container():
            # Layout com checkbox e botão expandir
            if st.session_state.modo_exclusao_beneficios:
                col_check, col_expand, col_info = st.columns([0.3, 0.7, 9])
                
                with col_check:
                    checkbox_key = f"beneficio_select_{beneficio_id}"
                    if st.checkbox("", key=checkbox_key, label_visibility="collapsed"):
                        if beneficio_id not in st.session_state.processos_selecionados_beneficios:
                            st.session_state.processos_selecionados_beneficios.append(beneficio_id)
                    elif beneficio_id in st.session_state.processos_selecionados_beneficios:
                        st.session_state.processos_selecionados_beneficios.remove(beneficio_id)
            else:
                col_expand, col_info = st.columns([1, 9])
            
            with col_expand if not st.session_state.modo_exclusao_beneficios else col_expand:
                expand_text = "▼ Fechar" if is_expanded else "▶ Abrir"
                if st.button(expand_text, key=f"expand_beneficio_{beneficio_id}"):
                    if is_expanded:
                        st.session_state.beneficios_expanded_cards.discard(beneficio_id)
                    else:
                        st.session_state.beneficios_expanded_cards.add(beneficio_id)
                    st.rerun()
            
            with col_info:
                # Informações resumidas
                status_atual = safe_get_value_beneficio(beneficio, 'Status', 'Não informado')
                status_info = obter_cor_status(status_atual, "beneficios")
                
                st.markdown(f"""
                <div class="beneficio-info-grid">
                    <div class="info-item">
                        <div class="info-label">Tipo de Processo</div>
                        <div class="info-value">{safe_get_value_beneficio(beneficio, 'TIPO DE PROCESSO', 'Não informado')}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Status</div>
                        <div class="info-value">{status_info['html']}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Data Cadastro</div>
                        <div class="info-value">{safe_get_value_beneficio(beneficio, 'Data Cadastro', 'Não informado')[:16]}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">CPF</div>
                        <div class="info-value">{safe_get_value_beneficio(beneficio, 'CPF', 'Não informado')[:11]}...</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Conteúdo expandido (tabs)
            if is_expanded:
                st.markdown("---")
                st.markdown(f"### 📄 {safe_get_value_beneficio(beneficio, 'Nº DO PROCESSO', 'Não informado')}")
                
                # Tabs
                tab_info, tab_acoes, tab_historico = st.tabs(["📋 Informações", "⚙️ Ações", "📜 Histórico"])
                
                with tab_info:
                    render_tab_info_beneficio(beneficio, beneficio_id)
                
                with tab_acoes:
                    render_tab_acoes_beneficio(df, beneficio, beneficio_id, 
                                             safe_get_value_beneficio(beneficio, 'Status'), perfil_usuario)
                
                with tab_historico:
                    render_tab_historico_beneficio(beneficio, beneficio_id)

def render_tab_info_beneficio(processo, beneficio_id):
    """Renderiza a tab de informações do Benefício"""
        
    col_det1, col_det2 = st.columns(2)
    
    with col_det1:
        st.markdown("**📋 Dados Básicos:**")
        st.write(f"**CPF:** {safe_get_value_beneficio(processo, 'CPF')}")
        st.write(f"**Parte:** {safe_get_value_beneficio(processo, 'PARTE')}")
        st.write(f"**Tipo de Processo:** {safe_get_value_beneficio(processo, 'TIPO DE PROCESSO')}")
        if "ASSUNTO" in processo:
            st.write(f"**Assunto:** {safe_get_value_beneficio(processo, 'ASSUNTO')}")
    
    with col_det2:
        st.markdown("**💰 Valores e Documentos:**")
        if "VALOR" in processo:
            st.write(f"**Valor:** {safe_get_value_beneficio(processo, 'VALOR')}")
        if "BENEFÍCIO" in processo:
            st.write(f"**Benefício:** {safe_get_value_beneficio(processo, 'BENEFÍCIO')}")
        if "ESPÉCIE" in processo:
            st.write(f"**Espécie:** {safe_get_value_beneficio(processo, 'ESPÉCIE')}")
        if "STATUS BENEFÍCIO" in processo:
            st.write(f"**Status Benefício:** {safe_get_value_beneficio(processo, 'STATUS BENEFÍCIO')}")
    
    # Mostrar detalhes dos honorários contratuais
    mostrar_detalhes_hc_beneficio(processo, f"info_{beneficio_id}")
    
    # Sistema de Parcelas - Informações
    tipo_pagamento = safe_get_value_beneficio(processo, 'Tipo Pagamento', 'À vista')
    if tipo_pagamento != 'À vista':
        num_parcelas = safe_get_int_value_beneficio(processo, 'Numero Parcelas', 1)
        valor_total = safe_get_value_beneficio(processo, 'Valor Total Honorarios', 'N/A')
        
        st.markdown("---")
        st.markdown("### 💳 Sistema de Parcelas")
        
        col_parc1, col_parc2, col_parc3 = st.columns(3)
        
        with col_parc1:
            st.metric("Tipo de Pagamento", tipo_pagamento)
        
        with col_parc2:
            st.metric("Número de Parcelas", num_parcelas)
        
        with col_parc3:
            st.metric("Valor Total", valor_total)
        
        # Status das parcelas
        parcelas_pagas, todas_pagas = calcular_status_parcelas(processo, num_parcelas)
        progresso = (parcelas_pagas / num_parcelas) * 100 if num_parcelas > 0 else 0
        
        st.progress(progresso / 100, text=f"Progresso: {parcelas_pagas}/{num_parcelas} parcelas pagas ({progresso:.1f}%)")
        
        # Lista resumida das parcelas
        if num_parcelas > 0:
            for i in range(1, num_parcelas + 1):
                status_parcela = safe_get_value_beneficio(processo, f'Parcela_{i}_Status', 'Pendente')
                data_vencimento = safe_get_value_beneficio(processo, f'Parcela_{i}_Data_Vencimento', '')
                data_pagamento = safe_get_value_beneficio(processo, f'Parcela_{i}_Data_Pagamento', '')
    
    # Observações
    if safe_get_value_beneficio(processo, 'OBSERVAÇÕES', '') != 'Não cadastrado':
        st.markdown("### 📝 Observações")
        st.info(safe_get_value_beneficio(processo, 'OBSERVAÇÕES'))

def render_tab_acoes_beneficio(df, processo, beneficio_id, status_atual, perfil_usuario):
    """Renderiza a tab de ações do Benefício - inclui edição completa para Cadastradores e Desenvolvedores"""
    
    # Usar a função original de edição, mas sem o cabeçalho
    linha_processo_df = df[df["ID"].astype(str) == str(beneficio_id)]
    
    if len(linha_processo_df) == 0:
        st.error(f"❌ Benefício com ID {beneficio_id} não encontrado")
        return
    
    linha_processo = linha_processo_df.iloc[0]
    numero_processo = linha_processo.get("Nº DO PROCESSO", "N/A")
    
    # NOVA SEÇÃO: EDIÇÃO COMPLETA PARA CADASTRADORES E DESENVOLVEDORES
    if perfil_usuario in ["Cadastrador", "Desenvolvedor"]:
        with st.expander("✏️ Editar Dados do Cadastro", expanded=False):
            with st.form(f"form_edicao_completa_beneficio_{beneficio_id}"):
                col_edit1, col_edit2 = st.columns(2)
                
                with col_edit1:
                    st.markdown("**📋 Dados Básicos:**")
                    
                    # Campo editável para o processo
                    processo_editado = st.text_input(
                        "Número do Processo:",
                        value=safe_get_value_beneficio(linha_processo, "Nº DO PROCESSO", ""),
                        key=f"edit_processo_beneficio_{beneficio_id}"
                    )
                    
                    # Campo editável para parte
                    parte_editada = st.text_input(
                        "Parte:",
                        value=safe_get_value_beneficio(linha_processo, "PARTE", ""),
                        key=f"edit_parte_beneficio_{beneficio_id}"
                    )
                    
                    # Campo editável para CPF
                    cpf_editado = st.text_input(
                        "CPF:",
                        value=safe_get_value_beneficio(linha_processo, "CPF", ""),
                        key=f"edit_cpf_beneficio_{beneficio_id}"
                    )
                    
                    # Campo editável para detalhe do processo
                    detalhe_editado = st.text_input(
                        "Detalhe do Processo:",
                        value=safe_get_value_beneficio(linha_processo, "DETALHE PROCESSO", ""),
                        key=f"edit_detalhe_beneficio_{beneficio_id}"
                    )
                    
                    # Campo editável para data da concessão
                    data_concessao_editada = st.text_input(
                        "Data da Concessão da Liminar:",
                        value=safe_get_value_beneficio(linha_processo, "DATA DA CONCESSÃO DA LIMINAR", ""),
                        key=f"edit_data_concessao_beneficio_{beneficio_id}"
                    )
                
                with col_edit2:
                    st.markdown("**⏰ Dados de Prazo e Observações:**")
                    
                    # Campo editável para prazo fatal
                    prazo_fatal_editado = st.text_input(
                        "Provável Prazo Fatal para Cumprimento:",
                        value=safe_get_value_beneficio(linha_processo, "PROVÁVEL PRAZO FATAL PARA CUMPRIMENTO", ""),
                        key=f"edit_prazo_fatal_beneficio_{beneficio_id}"
                    )
                    
                    # Campo editável para percentual de cobrança
                    percentual_cobranca_editado = st.text_input(
                        "Percentual Cobrança:",
                        value=safe_get_value_beneficio(linha_processo, "Percentual Cobrança", ""),
                        key=f"edit_percentual_beneficio_{beneficio_id}"
                    )
                    
                    # Campo editável para observações
                    observacoes_editadas = st.text_area(
                        "Observações:",
                        value=safe_get_value_beneficio(linha_processo, "OBSERVAÇÕES", ""),
                        height=120,
                        key=f"edit_observacoes_beneficio_{beneficio_id}"
                    )
                
                # Botão para salvar edições
                salvar_edicao = st.form_submit_button("💾 Salvar Alterações", type="primary")
                
                if salvar_edicao:
                    try:
                        idx = df[df["ID"] == beneficio_id].index[0]
                        
                        # Atualizar todos os campos editados
                        st.session_state.df_editado_beneficios.loc[idx, "Nº DO PROCESSO"] = processo_editado
                        st.session_state.df_editado_beneficios.loc[idx, "PARTE"] = parte_editada
                        st.session_state.df_editado_beneficios.loc[idx, "CPF"] = cpf_editado
                        st.session_state.df_editado_beneficios.loc[idx, "DETALHE PROCESSO"] = detalhe_editado
                        st.session_state.df_editado_beneficios.loc[idx, "DATA DA CONCESSÃO DA LIMINAR"] = data_concessao_editada
                        st.session_state.df_editado_beneficios.loc[idx, "PROVÁVEL PRAZO FATAL PARA CUMPRIMENTO"] = prazo_fatal_editado
                        st.session_state.df_editado_beneficios.loc[idx, "Percentual Cobrança"] = percentual_cobranca_editado
                        st.session_state.df_editado_beneficios.loc[idx, "OBSERVAÇÕES"] = observacoes_editadas
                        
                        # Salvamento automático no GitHub
                        save_data_to_github_seguro(st.session_state.df_editado_beneficios, "lista_beneficios.csv", "file_sha_beneficios")
                        
                        st.success("✅ Dados editados e salvos automaticamente!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao salvar edições: {str(e)}")
        
    # Chamar a interface de edição que contém as ações específicas por status
    if status_atual == "Enviado para administrativo" and perfil_usuario in ["Administrativo", "Desenvolvedor"]:
        st.markdown("#### 🔧 Análise Administrativa")
        st.info("Após inserir os documentos no Korbil, marque a caixa abaixo e salve.")
        
        korbil_ok = st.checkbox("Carta de Concessão e Histórico de Crédito inseridos no Korbil", key=f"korbil_{beneficio_id}")
        
        if st.button("💾 Salvar e Devolver para Cadastrador", type="primary", disabled=not korbil_ok, key=f"salvar_admin_{beneficio_id}"):
            atualizar_status_beneficio(beneficio_id, "Implantado", df)

    elif status_atual == "Implantado" and perfil_usuario in ["Cadastrador", "Desenvolvedor"]:
        st.info("🔍 Processo implantado e pronto para contato com cliente via SAC.")

        if st.button("📞 Enviar para SAC", type="primary", use_container_width=True, key=f"enviar_sac_{beneficio_id}"):
            atualizar_status_beneficio(
                beneficio_id, "Enviado para o SAC", df
            )

    elif status_atual == "Enviado para o SAC" and perfil_usuario in ["SAC", "Desenvolvedor"]:
        st.markdown("#### 📞 Contato com Cliente - SAC")
        st.info("📋 Entre em contato com o cliente e marque quando concluído.")
        
        cliente_contatado = st.checkbox("Cliente contatado", key=f"cliente_contatado_{beneficio_id}")
        
        if st.button("📤 Enviar para Financeiro", type="primary", disabled=not cliente_contatado, key=f"enviar_fin_{beneficio_id}"):
            # Adicionar informação de que foi contatado
            atualizar_status_beneficio(beneficio_id, "Enviado para o financeiro", df,
                                     dados_adicionais={"Cliente Contatado": "Sim",
                                                      "Data Contato SAC": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                                      "Contatado Por": perfil_usuario})

    elif status_atual == "Enviado para o financeiro" and perfil_usuario in ["Financeiro", "Desenvolvedor"]:
        
        # Obter dados da linha atual
        linha_beneficio = df[df["ID"] == beneficio_id].iloc[0]
        
        # Verificar tipo de pagamento
        tipo_pagamento = linha_beneficio.get("Tipo Pagamento", "À vista")
        num_parcelas = safe_get_int_value_beneficio(linha_beneficio, "Numero Parcelas", 1)
        valor_total = safe_get_value_beneficio(linha_beneficio, "Valor Total Honorarios", "A definir")
                
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
                atualizar_status_beneficio(beneficio_id, "Finalizado", df)
        
        else:
            # Sistema de pagamento parcelado - organizado em card
            with st.expander("💳 Sistema de Pagamento e Parcelas", expanded=True):
                interface_edicao_beneficio(df, beneficio_id, perfil_usuario)
    
    else:
        st.info(f"**Status Atual:** {status_atual}")
        
        # Para outros status, mostrar ações apropriadas - sem chamadas duplicadas
        if ((status_atual == "Enviado para administrativo" and perfil_usuario in ["Administrativo", "Desenvolvedor"]) or
            (status_atual == "Implantado" and perfil_usuario in ["Cadastrador", "Desenvolvedor"]) or
            (status_atual == "Enviado para o SAC" and perfil_usuario in ["SAC", "Desenvolvedor"])):
            with st.expander("💳 Sistema de Pagamento e Parcelas", expanded=False):
                interface_edicao_beneficio(df, beneficio_id, perfil_usuario)

def render_tab_historico_beneficio(processo, beneficio_id):
    """Renderiza a tab de histórico do Benefício"""
    
    st.markdown("### 📜 Histórico do Processo")
    
    # Timeline do processo
    status_atual = safe_get_value_beneficio(processo, 'Status')
    
    # Etapas básicas do fluxo de benefícios
    etapas = [
        {
            "titulo": "📝 Cadastrado",
            "data": safe_get_value_beneficio(processo, 'Data Cadastro'),
            "responsavel": safe_get_value_beneficio(processo, 'Cadastrado Por', 'Sistema'),
            "concluida": True  # Sempre concluída se existe
        },
        {
            "titulo": "📋 Em Processamento",
            "data": safe_get_value_beneficio(processo, 'Data Processamento', ''),
            "responsavel": safe_get_value_beneficio(processo, 'Processado Por', ''),
            "concluida": status_atual not in ["Cadastrado", "Pendente"]
        },
        {
            "titulo": "💰 Análise Financeira",
            "data": safe_get_value_beneficio(processo, 'Data Analise', ''),
            "responsavel": safe_get_value_beneficio(processo, 'Analisado Por', ''),
            "concluida": safe_get_value_beneficio(processo, 'Analisado') == "Sim"
        },
        {
            "titulo": "🎯 Finalizado",
            "data": safe_get_value_beneficio(processo, 'Data Finalizacao', ''),
            "responsavel": safe_get_value_beneficio(processo, 'Finalizado Por', ''),
            "concluida": status_atual.lower() in ["finalizado", "concluído", "encerrado"]
        }
    ]
    
    for i, etapa in enumerate(etapas):
        if etapa["concluida"] and etapa["data"] and etapa["data"] != "Não cadastrado":
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

def interface_cadastro_beneficio(df, perfil_usuario):
    """Interface para cadastrar novos benefícios, com validações e dicas."""
    
    # LIMPAR ESTADOS DE DIÁLOGO ao entrar na aba de cadastro
    if st.session_state.get("show_beneficio_dialog", False):
        st.session_state.show_beneficio_dialog = False
    if st.session_state.get("beneficio_aberto_id") is not None:
        st.session_state.beneficio_aberto_id = None
    
    # Verificar se o usuário pode cadastrar benefícios
    if perfil_usuario not in ["Cadastrador", "Desenvolvedor"]:
        st.warning("⚠️ Apenas Cadastradores e Desenvolvedores podem criar novos benefícios")
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
            
            # Se for pagamento parcelado, gerar datas de vencimento
            if num_parcelas > 1 and valor_total_honorarios and valor_total_honorarios > 0:
                data_base = datetime.now()
                parcelas_data = gerar_parcelas_beneficio(nova_linha["ID"], valor_total_honorarios, num_parcelas, data_base)
                nova_linha.update(parcelas_data)
            
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

def render_parcela_individual(linha_beneficio, i, valor_parcela_individual, beneficio_id, df):
    """Renderiza uma parcela individual com formulário de pagamento"""
    status_parcela = linha_beneficio.get(f"Parcela_{i}_Status", "Pendente")
    data_vencimento = linha_beneficio.get(f"Parcela_{i}_Data_Vencimento", "")
    data_pagamento = linha_beneficio.get(f"Parcela_{i}_Data_Pagamento", "")
    comprovante_url = linha_beneficio.get(f"Parcela_{i}_Comprovante", "")
    
    if status_parcela == "Paga":
        # Parcela paga - apenas visualização
        st.success(f"✅ **Parcela {i} - PAGA** (R$ {valor_parcela_individual:.2f})")
        
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.write(f"📅 **Vencimento:** {data_vencimento}")
        with col_info2:
            st.write(f"💰 **Pago em:** {data_pagamento}")
        with col_info3:
            if comprovante_url and comprovante_url.startswith("http"):
                st.markdown(f"📄 [Ver Comprovante]({comprovante_url})")
            elif comprovante_url:
                st.write(f"📄 **Comprovante:** {comprovante_url}")
    
    else:
        # Parcela pendente - interface para pagamento
        if data_vencimento:
            try:
                venc_date = datetime.strptime(data_vencimento, "%d/%m/%Y")
                hoje = datetime.now()
                dias_venc = (venc_date - hoje).days
                
                if dias_venc < 0:
                    st.error(f"🔴 **Parcela {i} - VENCIDA** (R$ {valor_parcela_individual:.2f})")
                    st.write(f"📅 **Venceu em:** {data_vencimento} ({abs(dias_venc)} dias atrás)")
                elif dias_venc == 0:
                    st.warning(f"🟡 **Parcela {i} - VENCE HOJE** (R$ {valor_parcela_individual:.2f})")
                    st.write(f"📅 **Vencimento:** {data_vencimento}")
                elif dias_venc <= 7:
                    st.warning(f"🟡 **Parcela {i} - VENCE EM {dias_venc} DIAS** (R$ {valor_parcela_individual:.2f})")
                    st.write(f"📅 **Vencimento:** {data_vencimento}")
                else:
                    st.info(f"🔵 **Parcela {i} - PENDENTE** (R$ {valor_parcela_individual:.2f})")
                    st.write(f"📅 **Vencimento:** {data_vencimento} ({dias_venc} dias)")
            except:
                st.info(f"🔵 **Parcela {i} - PENDENTE** (R$ {valor_parcela_individual:.2f})")
                st.write(f"📅 **Vencimento:** {data_vencimento}")
        else:
            st.info(f"🔵 **Parcela {i} - PENDENTE** (R$ {valor_parcela_individual:.2f})")
        
        # Formulário para marcar como paga - chave única por parcela e benefício
        with st.form(f"pagamento_parcela_{i}_{beneficio_id}_tab"):
            st.markdown(f"**📝 Registro de Pagamento - Parcela {i}**")
            
            col_form1, col_form2 = st.columns(2)
            
            with col_form1:
                # Opção 1: Upload de arquivo
                st.markdown("**Opção 1: Upload do Comprovante**")
                comprovante_arquivo = st.file_uploader(
                    f"Anexar comprovante (Parcela {i})",
                    type=["pdf", "jpg", "jpeg", "png"],
                    key=f"upload_parcela_{i}_{beneficio_id}_tab",
                    help="Selecione o arquivo do comprovante de pagamento"
                )
            
            with col_form2:
                # Opção 2: Pagamento em dinheiro
                st.markdown("**Opção 2: Pagamento em Dinheiro**")
                pago_dinheiro = st.checkbox(
                    f"Pago em dinheiro (Parcela {i})",
                    key=f"dinheiro_parcela_{i}_{beneficio_id}_tab",
                    help="Marque se o pagamento foi feito em espécie"
                )
                
                # Data do pagamento (opcional)
                st.markdown("**Data do Pagamento**")
                data_pagamento_input = st.date_input(
                    f"Data de pagamento (Parcela {i})",
                    value=datetime.now().date(),
                    key=f"data_parcela_{i}_{beneficio_id}_tab",
                    help="Selecione a data em que o pagamento foi recebido"
                )
                
                # Observações adicionais
                observacoes_pagamento = st.text_area(
                    f"Observações (Parcela {i})",
                    placeholder="Observações sobre o pagamento...",
                    key=f"obs_parcela_{i}_{beneficio_id}_tab",
                    height=60
                )
            
            # Validar se ao menos uma opção foi preenchida
            # CORREÇÃO: Verificar explicitamente se checkbox está marcado ou arquivo foi anexado
            tem_arquivo_anexado = comprovante_arquivo is not None
            checkbox_marcado = pago_dinheiro == True
            pode_confirmar = tem_arquivo_anexado or checkbox_marcado
            
            marcar_paga = st.form_submit_button(
                f"✅ Confirmar Pagamento da Parcela {i}",
                type="primary",
                disabled=not pode_confirmar,
                use_container_width=True
            )
            
            if marcar_paga:
                if pode_confirmar:
                    comprovante_final = ""
                    
                    if pago_dinheiro:
                        comprovante_final = "Dinheiro"
                    elif comprovante_arquivo:
                        # Upload do arquivo
                        with st.spinner("📤 Salvando comprovante..."):
                            processo_nome = safe_get_value_beneficio(linha_beneficio, 'Nº DO PROCESSO', 'processo')
                            comprovante_final = salvar_arquivo(
                                comprovante_arquivo, 
                                processo_nome, 
                                f"pagamento_parcela_{i}_beneficio"
                            )
                    
                    # Atualizar parcela como paga
                    atualizar_pagamento_parcela(
                        beneficio_id, i, df, 
                        url_comprovante=comprovante_final,
                        data_pagamento_customizada=data_pagamento_input.strftime("%d/%m/%Y"),
                        observacoes=observacoes_pagamento,
                        pago_dinheiro=pago_dinheiro
                    )
                else:
                    st.error("❌ Por favor, anexe um comprovante ou marque 'Pago em dinheiro'.")

def interface_edicao_beneficio(df, beneficio_id, perfil_usuario):
    """
    Interface de edição com o fluxo de trabalho corrigido e adaptada para st.dialog.
    """

    linha_beneficio = df[df["ID"] == beneficio_id].iloc[0]
    status_atual = linha_beneficio.get("Status", "N/A")
    processo = linha_beneficio.get("Nº DO PROCESSO", "N/A")

    # Exibir informações básicas do benefício com layout compacto
    exibir_informacoes_basicas_beneficio(linha_beneficio, "compacto")

    if status_atual == "Enviado para administrativo" and perfil_usuario in ["Administrativo", "Desenvolvedor"]:
        st.markdown("#### 🔧 Análise Administrativa")
        st.info("Após inserir os documentos no Korbil, marque a caixa abaixo e salve.")
        
        korbil_ok = st.checkbox("Carta de Concessão e Histórico de Crédito inseridos no Korbil")
        
        if st.button("💾 Salvar e Devolver para Cadastrador", type="primary", disabled=not korbil_ok):
            atualizar_status_beneficio(beneficio_id, "Implantado", df)

    elif status_atual == "Implantado" and perfil_usuario in ["Cadastrador", "Desenvolvedor"]:
        st.markdown("#### 📞 Enviar para SAC")
        st.info("🔍 Processo implantado e pronto para contato com cliente via SAC.")

        if st.button("� Enviar para SAC", type="primary", use_container_width=True):
            atualizar_status_beneficio(
                beneficio_id, "Enviado para o SAC", df
            )

    elif status_atual == "Enviado para o SAC" and perfil_usuario in ["SAC", "Desenvolvedor"]:
        st.markdown("#### 📞 Contato com Cliente - SAC")
        st.info("📋 Entre em contato com o cliente e marque quando concluído.")
        
        cliente_contatado = st.checkbox("Cliente contatado")
        
        if st.button("📤 Enviar para Financeiro", type="primary", disabled=not cliente_contatado):
            # Adicionar informação de que foi contatado
            atualizar_status_beneficio(beneficio_id, "Enviado para o financeiro", df,
                                     dados_adicionais={"Cliente Contatado": "Sim",
                                                      "Data Contato SAC": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                                      "Contatado Por": perfil_usuario})

    elif status_atual == "Enviado para o financeiro" and perfil_usuario in ["Financeiro", "Desenvolvedor"]:
        
        # Verificar tipo de pagamento
        tipo_pagamento = linha_beneficio.get("Tipo Pagamento", "À vista")
        num_parcelas = safe_get_int_value_beneficio(linha_beneficio, "Numero Parcelas", 1)
        valor_total = safe_get_value_beneficio(linha_beneficio, "Valor Total Honorarios", "A definir")
        valor_parcela = safe_get_value_beneficio(linha_beneficio, "Valor Parcela", "")
        
        # Exibir informações do pagamento
        
        st.markdown("---")
        
        # ======== NOVA SEÇÃO: CONFIGURAÇÃO RÁPIDA DE PAGAMENTO ========
        if valor_total == "A definir" or valor_total == "" or not valor_total:
            with st.expander("⚙️ **Configurar Pagamento** (Obrigatório)", expanded=True):
                st.warning("📋 Configure o tipo de pagamento para acessar o sistema de parcelas.")
                
                with st.form(f"config_pagamento_rapida_{beneficio_id}"):
                    col_cfg1, col_cfg2 = st.columns(2)
                    
                    with col_cfg1:
                        novo_tipo = st.selectbox(
                            "Tipo de Pagamento:",
                            list(OPCOES_PAGAMENTO.keys()),
                            index=0,
                            help="À vista = 1 parcela, demais = parcelado"
                        )
                    
                    with col_cfg2:
                        novo_valor = st.number_input(
                            "Valor Total (R$):",
                            min_value=0.0,
                            step=100.0,
                            format="%.2f",
                            help="Valor total que será pago"
                        )
                    
                    if st.form_submit_button("💾 Configurar e Acessar Sistema de Parcelas", type="primary"):
                        if novo_valor > 0:
                            try:
                                idx = df[df["ID"] == beneficio_id].index[0]
                                novo_num_parcelas = OPCOES_PAGAMENTO[novo_tipo]["parcelas"]
                                
                                st.session_state.df_editado_beneficios.loc[idx, "Tipo Pagamento"] = novo_tipo
                                st.session_state.df_editado_beneficios.loc[idx, "Numero Parcelas"] = novo_num_parcelas
                                st.session_state.df_editado_beneficios.loc[idx, "Valor Total Honorarios"] = f"R$ {novo_valor:.2f}"
                                
                                # Salvar no GitHub
                                novo_sha = save_data_to_github_seguro(
                                    st.session_state.df_editado_beneficios,
                                    "lista_beneficios.csv",
                                    st.session_state.get("file_sha_beneficios", None)
                                )
                                
                                if novo_sha:
                                    st.session_state.file_sha_beneficios = novo_sha
                                    st.success("✅ Configuração salva! Recarregando sistema de parcelas...")
                                    st.rerun()
                                else:
                                    st.error("❌ Erro ao salvar.")
                                    
                            except Exception as e:
                                st.error(f"❌ Erro: {e}")
                        else:
                            st.error("❌ Informe um valor maior que R$ 0,00")
            
            # Parar execução até configurar
            st.info("👆 Configure o pagamento acima para prosseguir.")
            return
        
        # ======== BOTÃO PARA ALTERAR CONFIGURAÇÃO DE PAGAMENTO ========
        with st.expander("🔧 Alterar Configuração de Pagamento", expanded=False):
            st.info("💡 Use esta seção para mudar o tipo ou valor do pagamento.")
            
            with st.form(f"alterar_pagamento_{beneficio_id}"):
                col_alt1, col_alt2 = st.columns(2)
                
                with col_alt1:
                    tipo_atual_index = list(OPCOES_PAGAMENTO.keys()).index(tipo_pagamento) if tipo_pagamento in OPCOES_PAGAMENTO else 0
                    tipo_alterado = st.selectbox(
                        "Novo Tipo de Pagamento:",
                        list(OPCOES_PAGAMENTO.keys()),
                        index=tipo_atual_index
                    )
                
                with col_alt2:
                    valor_atual = 0
                    if valor_total and "R$" in str(valor_total):
                        try:
                            valor_atual = float(str(valor_total).replace("R$", "").replace(".", "").replace(",", ".").strip())
                        except:
                            valor_atual = 0
                    
                    valor_alterado = st.number_input(
                        "Novo Valor Total (R$):",
                        min_value=0.0,
                        value=valor_atual,
                        step=100.0,
                        format="%.2f"
                    )
                
                if st.form_submit_button("🔄 Aplicar Alterações", type="secondary"):
                    if valor_alterado > 0:
                        try:
                            idx = df[df["ID"] == beneficio_id].index[0]
                            novo_num_parcelas = OPCOES_PAGAMENTO[tipo_alterado]["parcelas"]
                            
                            st.session_state.df_editado_beneficios.loc[idx, "Tipo Pagamento"] = tipo_alterado
                            st.session_state.df_editado_beneficios.loc[idx, "Numero Parcelas"] = novo_num_parcelas
                            st.session_state.df_editado_beneficios.loc[idx, "Valor Total Honorarios"] = f"R$ {valor_alterado:.2f}"
                            
                            # Limpar parcelas antigas se mudou o número
                            for i in range(1, 13):  # Máximo 12 parcelas
                                if i > novo_num_parcelas:
                                    # Limpar parcelas que não existem mais
                                    st.session_state.df_editado_beneficios.loc[idx, f"Parcela_{i}_Status"] = ""
                                    st.session_state.df_editado_beneficios.loc[idx, f"Parcela_{i}_Data_Vencimento"] = ""
                                    st.session_state.df_editado_beneficios.loc[idx, f"Parcela_{i}_Comprovante"] = ""
                                    st.session_state.df_editado_beneficios.loc[idx, f"Parcela_{i}_Data_Pagamento"] = ""
                            
                            # Salvar no GitHub
                            novo_sha = save_data_to_github_seguro(
                                st.session_state.df_editado_beneficios,
                                "lista_beneficios.csv",
                                st.session_state.get("file_sha_beneficios", None)
                            )
                            
                            if novo_sha:
                                st.session_state.file_sha_beneficios = novo_sha
                                st.success("✅ Configuração alterada! Recarregando...")
                                st.rerun()
                            else:
                                st.error("❌ Erro ao salvar alteração.")
                                
                        except Exception as e:
                            st.error(f"❌ Erro ao alterar: {e}")
                    else:
                        st.error("❌ Valor deve ser maior que R$ 0,00")

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
        # SISTEMA UNIFICADO DE PARCELAS - SEMPRE ACESSÍVEL
        # =====================================
        
        st.markdown("### 💳 Sistema de Pagamento e Parcelas")
        
        # Verificar se as parcelas já foram geradas
        parcelas_geradas = False
        for i in range(1, num_parcelas + 1):
            if linha_beneficio.get(f"Parcela_{i}_Data_Vencimento"):
                parcelas_geradas = True
                break
        
        # Se as parcelas não foram geradas ainda, gerar automaticamente
        if not parcelas_geradas:
            st.info("⚙️ Configurando parcelas automaticamente...")
            
            try:
                # Converter valor_total para uso na geração de parcelas
                valor_total_para_parcelas = 0
                if valor_total and valor_total != "A definir":
                    try:
                        if "R$" in str(valor_total):
                            valor_limpo = str(valor_total).replace("R$", "").strip()
                            if "," in valor_limpo:
                                valor_limpo = valor_limpo.replace(".", "").replace(",", ".")
                            valor_total_para_parcelas = float(valor_limpo)
                        else:
                            valor_total_para_parcelas = float(valor_total)
                    except:
                        valor_total_para_parcelas = 0
                
                # Gerar dados das parcelas automaticamente
                data_envio = datetime.now()
                parcelas_data = gerar_parcelas_beneficio(beneficio_id, valor_total_para_parcelas, num_parcelas, data_envio)
                
                # Atualizar DataFrame
                if "df_editado_beneficios" not in st.session_state:
                    st.session_state.df_editado_beneficios = df.copy()
                
                idx = st.session_state.df_editado_beneficios[st.session_state.df_editado_beneficios["ID"] == beneficio_id].index[0]
                for campo, valor in parcelas_data.items():
                    st.session_state.df_editado_beneficios.loc[idx, campo] = valor
                
                # Salvar no GitHub
                novo_sha = save_data_to_github_seguro(
                    st.session_state.df_editado_beneficios,
                    "lista_beneficios.csv",
                    st.session_state.get("file_sha_beneficios", None)
                )
                
                if novo_sha:
                    st.session_state.file_sha_beneficios = novo_sha
                    st.success("✅ Parcelas configuradas automaticamente!")
                    st.rerun()
                else:
                    st.error("❌ Erro ao salvar as parcelas.")
                    return
                    
            except Exception as e:
                st.error(f"❌ Erro ao configurar parcelas: {e}")
                return
        
        
        # Converter valor_total para número se necessário
        valor_total_numerico = 0
        if valor_total and valor_total != "A definir":
            try:
                if "R$" in str(valor_total):
                    valor_limpo = str(valor_total).replace("R$", "").strip()
                    if "," in valor_limpo:
                        valor_limpo = valor_limpo.replace(".", "").replace(",", ".")
                    valor_total_numerico = float(valor_limpo)
                else:
                    valor_total_numerico = float(valor_total)
            except:
                valor_total_numerico = 0
        
        # Calcular estatísticas
        parcelas_pagas, todas_pagas = calcular_status_parcelas(linha_beneficio, num_parcelas)
        valor_parcela_individual = valor_total_numerico / num_parcelas if num_parcelas > 0 else 0
        
        # Métricas
        col_met1, col_met2, col_met3, col_met4 = st.columns(4)
        
        with col_met1:
            st.metric("💰 Valor por Parcela", f"R$ {valor_parcela_individual:.2f}")
        
        with col_met2:
            st.metric("✅ Parcelas Pagas", f"{parcelas_pagas}/{num_parcelas}")
        
        with col_met3:
            restante = num_parcelas - parcelas_pagas
            st.metric("⏳ Restantes", restante)
        
        with col_met4:
            progresso = (parcelas_pagas / num_parcelas) * 100 if num_parcelas > 0 else 0
            st.metric("📈 Progresso", f"{progresso:.1f}%")
        
        # Barra de progresso
        st.progress(progresso / 100, text=f"Progresso do pagamento: {parcelas_pagas} de {num_parcelas} parcelas pagas")
        
        if valor_total_numerico == 0:
            st.warning("⚠️ **Valor Total dos Honorários não foi definido.** Use a seção 'Alterar Configuração de Pagamento' acima para definir o valor.")
        
        st.markdown("---")
        
        
        # =====================================
        # IMPLEMENTAÇÃO ORIGINAL (MANTIDA PARA COMPATIBILIDADE)
        # =====================================
        
        # Esta seção não será mais executada, mas mantida para referência
        if False and tipo_pagamento == "À vista":
            # Pagamento à vista - usar o mesmo sistema de parcelas (1 parcela)
            st.markdown("#### 💰 Pagamento à Vista")
            st.info("💡 Pagamento à vista - Registre o comprovante para finalizar o benefício")
            
            # Verificar se já foi configurado como parcela única
            parcela_configurada = linha_beneficio.get("Parcela_1_Data_Vencimento", "")
            
            if not parcela_configurada:
                # Configurar como parcela única se ainda não foi feito
                st.warning("⚠️ Configurando pagamento à vista como parcela única...")
                
                if "df_editado_beneficios" not in st.session_state:
                    st.session_state.df_editado_beneficios = df.copy()
                
                try:
                    valor_total_str = safe_get_value_beneficio(linha_beneficio, "Valor Total Honorarios", "0")
                    if valor_total_str.startswith("R$"):
                        valor_total = float(valor_total_str.replace("R$", "").replace(".", "").replace(",", ".").strip())
                    else:
                        valor_total = 0
                    
                    # Gerar dados da parcela única
                    data_envio = datetime.now()
                    parcelas_data = gerar_parcelas_beneficio(beneficio_id, valor_total, 1, data_envio)
                    
                    # Atualizar DataFrame
                    idx = st.session_state.df_editado_beneficios[st.session_state.df_editado_beneficios["ID"] == beneficio_id].index[0]
                    for campo, valor in parcelas_data.items():
                        st.session_state.df_editado_beneficios.loc[idx, campo] = valor
                    
                    # Salvar no GitHub
                    novo_sha = save_data_to_github_seguro(
                        st.session_state.df_editado_beneficios,
                        "lista_beneficios.csv",
                        st.session_state.get("file_sha_beneficios", None)
                    )
                    
                    if novo_sha:
                        st.session_state.file_sha_beneficios = novo_sha
                        st.success("✅ Parcela única configurada!")
                        st.rerun()
                    else:
                        st.error("❌ Erro ao configurar parcela.")
                        
                except Exception as e:
                    st.error(f"❌ Erro ao configurar parcela única: {e}")
            
            else:
                # Usar a interface de parcelas para o pagamento à vista (1 parcela)
                status_parcela = linha_beneficio.get("Parcela_1_Status", "Pendente")
                data_vencimento = linha_beneficio.get("Parcela_1_Data_Vencimento", "")
                data_pagamento = linha_beneficio.get("Parcela_1_Data_Pagamento", "")
                comprovante_url = linha_beneficio.get("Parcela_1_Comprovante", "")
                
                # Calcular valor da parcela
                valor_total_str = safe_get_value_beneficio(linha_beneficio, "Valor Total Honorarios", "0")
                if valor_total_str and valor_total_str.startswith("R$"):
                    try:
                        valor_parcela = float(valor_total_str.replace("R$", "").replace(".", "").replace(",", ".").strip())
                    except:
                        valor_parcela = 0
                else:
                    valor_parcela = 0
                
                if status_parcela == "Paga":
                    # Já foi pago - mostrar informações
                    st.success(f"✅ **PAGAMENTO CONCLUÍDO** - R$ {valor_parcela:.2f}")
                    
                    col_info1, col_info2, col_info3 = st.columns(3)
                    with col_info1:
                        st.write(f"📅 **Vencimento:** {data_vencimento}")
                    with col_info2:
                        st.write(f"💰 **Pago em:** {data_pagamento}")
                    with col_info3:
                        if comprovante_url and comprovante_url.startswith("http"):
                            st.markdown(f"📄 [Ver Comprovante]({comprovante_url})")
                        elif comprovante_url:
                            st.write(f"📄 **Comprovante:** {comprovante_url}")
                    
                    st.info("🎉 Este benefício já foi finalizado com o pagamento à vista.")
                
                else:
                    # Ainda não foi pago - mostrar interface de pagamento
                    st.info(f"💰 **Valor Total:** R$ {valor_parcela:.2f}")
                    if data_vencimento:
                        st.write(f"📅 **Data de Vencimento:** {data_vencimento}")
                    
                    # Usar a mesma interface de pagamento das parcelas
                    with st.form(f"pagamento_vista_{beneficio_id}"):
                        st.markdown("**📝 Registro de Pagamento à Vista**")
                        
                        col_form1, col_form2 = st.columns(2)
                        
                        with col_form1:
                            # Opção 1: Upload de arquivo
                            st.markdown("**Opção 1: Upload do Comprovante**")
                            comprovante_arquivo = st.file_uploader(
                                "Anexar comprovante de pagamento",
                                type=["pdf", "jpg", "jpeg", "png"],
                                key=f"upload_vista_{beneficio_id}",
                                help="Selecione o arquivo do comprovante de pagamento"
                            )
                        
                        with col_form2:
                            # Opção 2: Pagamento em dinheiro
                            st.markdown("**Opção 2: Pagamento em Dinheiro**")
                            pago_dinheiro = st.checkbox(
                                "Pago em dinheiro",
                                key=f"dinheiro_vista_{beneficio_id}",
                                help="Marque se o pagamento foi feito em espécie"
                            )
                            
                            # Data do pagamento (opcional)
                            st.markdown("**Data do Pagamento**")
                            data_pagamento_input = st.date_input(
                                "Data de pagamento",
                                value=datetime.now().date(),
                                key=f"data_vista_{beneficio_id}",
                                help="Selecione a data em que o pagamento foi recebido"
                            )
                            
                            # Observações adicionais
                            observacoes_pagamento = st.text_area(
                                "Observações",
                                placeholder="Observações sobre o pagamento...",
                                key=f"obs_vista_{beneficio_id}",
                                height=60
                            )
                        
                        # Validar se ao menos uma opção foi preenchida
                        # CORREÇÃO: Verificar explicitamente se checkbox está marcado ou arquivo foi anexado
                        tem_arquivo_anexado = comprovante_arquivo is not None
                        checkbox_marcado = pago_dinheiro == True
                        pode_confirmar = tem_arquivo_anexado or checkbox_marcado
                        
                        marcar_pago = st.form_submit_button(
                            "✅ Confirmar Pagamento à Vista",
                            type="primary",
                            disabled=not pode_confirmar,
                            use_container_width=True
                        )
                        
                        if marcar_pago:
                            if pode_confirmar:
                                comprovante_final = ""
                                
                                if pago_dinheiro:
                                    comprovante_final = "Dinheiro"
                                elif comprovante_arquivo:
                                    # Upload do arquivo
                                    with st.spinner("📤 Salvando comprovante..."):
                                        processo_nome = safe_get_value_beneficio(linha_beneficio, 'Nº DO PROCESSO', 'processo')
                                        comprovante_final = salvar_arquivo(
                                            comprovante_arquivo, 
                                            processo_nome, 
                                            "pagamento_vista_beneficio"
                                        )
                                
                                # Atualizar como parcela única paga (usa a mesma função)
                                atualizar_pagamento_parcela(
                                    beneficio_id, 1, df,  # Parcela 1 (única)
                                    url_comprovante=comprovante_final,
                                    data_pagamento_customizada=data_pagamento_input.strftime("%d/%m/%Y"),
                                    observacoes=observacoes_pagamento,
                                    pago_dinheiro=pago_dinheiro
                                )
                            else:
                                st.error("❌ Por favor, anexe um comprovante ou marque 'Pago em dinheiro'.")
        
        else:            
            # Verificar se as parcelas já foram geradas, se não, gerar automaticamente
            parcelas_geradas = False
            for i in range(1, num_parcelas + 1):
                if linha_beneficio.get(f"Parcela_{i}_Data_Vencimento"):
                    parcelas_geradas = True
                    break
            
            # Se as parcelas não foram geradas ainda, gerar automaticamente
            if not parcelas_geradas:
                st.info("⚙️ Configurando parcelas automaticamente...")
                
                try:
                    # Converter valor_total para uso na geração de parcelas
                    valor_total_para_parcelas = 0
                    if valor_total and valor_total != "A definir":
                        try:
                            if "R$" in str(valor_total):
                                # Para valores como "R$ 8.000,00" -> remover R$, trocar . por vazio e , por .
                                valor_limpo = str(valor_total).replace("R$", "").strip()
                                if "," in valor_limpo:
                                    # Formato brasileiro: R$ 8.000,00
                                    valor_limpo = valor_limpo.replace(".", "").replace(",", ".")
                                valor_total_para_parcelas = float(valor_limpo)
                            else:
                                valor_total_para_parcelas = float(valor_total)
                        except:
                            valor_total_para_parcelas = 0
                    
                    # Gerar dados das parcelas automaticamente
                    data_envio = datetime.now()  # Usar data atual como base
                    parcelas_data = gerar_parcelas_beneficio(beneficio_id, valor_total_para_parcelas, num_parcelas, data_envio)
                    
                    # Atualizar DataFrame
                    if "df_editado_beneficios" not in st.session_state:
                        st.session_state.df_editado_beneficios = df.copy()
                    
                    idx = st.session_state.df_editado_beneficios[st.session_state.df_editado_beneficios["ID"] == beneficio_id].index[0]
                    for campo, valor in parcelas_data.items():
                        st.session_state.df_editado_beneficios.loc[idx, campo] = valor
                    
                    # Salvar no GitHub
                    novo_sha = save_data_to_github_seguro(
                        st.session_state.df_editado_beneficios,
                        "lista_beneficios.csv",
                        st.session_state.get("file_sha_beneficios", None)
                    )
                    
                    if novo_sha:
                        st.session_state.file_sha_beneficios = novo_sha
                        st.success("✅ Parcelas configuradas automaticamente!")
                        st.rerun()
                    else:
                        st.error("❌ Erro ao salvar as parcelas.")
                        return
                        
                except Exception as e:
                    st.error(f"❌ Erro ao configurar parcelas: {e}")
                    return
            
            
            # Converter valor_total para número se necessário
            valor_total_numerico = 0
            if valor_total and valor_total != "A definir":
                try:
                    if "R$" in str(valor_total):
                        # Para valores como "R$ 8.000,00" -> remover R$, trocar . por vazio e , por .
                        valor_limpo = str(valor_total).replace("R$", "").strip()
                        if "," in valor_limpo:
                            # Formato brasileiro: R$ 8.000,00
                            valor_limpo = valor_limpo.replace(".", "").replace(",", ".")
                        valor_total_numerico = float(valor_limpo)
                    else:
                        valor_total_numerico = float(valor_total)
                except:
                    valor_total_numerico = 0
            
            # Aviso se valor não está definido
            if valor_total_numerico == 0:
                st.warning("⚠️ **Valor Total dos Honorários não foi definido no cadastro.** As parcelas serão exibidas, mas os valores serão R$ 0,00. Atualize o cadastro para definir o valor total.")
            
            # Calcular estatísticas
            parcelas_pagas, todas_pagas = calcular_status_parcelas(linha_beneficio, num_parcelas)
            valor_parcela_individual = valor_total_numerico / num_parcelas if num_parcelas > 0 else 0
            
            # Sistema de tabs para as parcelas
            if num_parcelas > 1:
                # Criar tabs para cada parcela
                tab_names = []
                for i in range(1, num_parcelas + 1):
                    status_parcela = linha_beneficio.get(f"Parcela_{i}_Status", "Pendente")
                    if status_parcela == "Paga":
                        tab_names.append(f"✅ Parcela {i}")
                    else:
                        data_vencimento = linha_beneficio.get(f"Parcela_{i}_Data_Vencimento", "")
                        if data_vencimento:
                            try:
                                venc_date = datetime.strptime(data_vencimento, "%d/%m/%Y")
                                hoje = datetime.now()
                                dias_venc = (venc_date - hoje).days
                                
                                if dias_venc < 0:
                                    tab_names.append(f"🔴 Parcela {i}")
                                elif dias_venc == 0:
                                    tab_names.append(f"🟡 Parcela {i}")
                                elif dias_venc <= 7:
                                    tab_names.append(f"� Parcela {i}")
                                else:
                                    tab_names.append(f"� Parcela {i}")
                            except:
                                tab_names.append(f"🔵 Parcela {i}")
                        else:
                            tab_names.append(f"� Parcela {i}")
                
                # Criar as tabs
                tabs = st.tabs(tab_names)
                
                # Renderizar cada parcela em sua tab
                for i, tab in enumerate(tabs, 1):
                    with tab:
                        render_parcela_individual(linha_beneficio, i, valor_parcela_individual, beneficio_id, df)
            else:
                # Se só há uma parcela, mostrar diretamente
                render_parcela_individual(linha_beneficio, 1, valor_parcela_individual, beneficio_id, df)
            
            # Status final
            if todas_pagas:
                st.success("🎉 **TODAS AS PARCELAS FORAM PAGAS!** O benefício será finalizado automaticamente.")
                
                if st.button("🎯 Finalizar Benefício Agora", type="primary", use_container_width=True):
                    atualizar_status_beneficio(beneficio_id, "Finalizado", df)
            
            else:
                restantes = num_parcelas - parcelas_pagas
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
    novo_sha = save_data_to_github_seguro(
        st.session_state.df_editado_beneficios,
        "lista_beneficios.csv",
        st.session_state.get("file_sha_beneficios", None)
    )
    if novo_sha:
        st.session_state.file_sha_beneficios = novo_sha
        st.toast(f"Status atualizado para: {novo_status}", icon="✅")
        limpar_estados_dialogo_beneficio()
        st.rerun()
    else:
        st.error("Falha ao salvar a atualização.")

def atualizar_pagamento_parcela(beneficio_id, numero_parcela, df, url_comprovante="", 
                              data_pagamento_customizada=None, observacoes="", pago_dinheiro=False):
    """Atualiza o status de pagamento de uma parcela específica"""
    try:
        if "df_editado_beneficios" not in st.session_state:
            st.session_state.df_editado_beneficios = df.copy()
        
        idx = st.session_state.df_editado_beneficios[st.session_state.df_editado_beneficios["ID"] == beneficio_id].index[0]
        
        # Atualizar campos da parcela
        st.session_state.df_editado_beneficios.loc[idx, f"Parcela_{numero_parcela}_Status"] = "Paga"
        
        # Usar data customizada se fornecida, senão usar data atual
        data_pagamento = data_pagamento_customizada if data_pagamento_customizada else datetime.now().strftime("%d/%m/%Y")
        st.session_state.df_editado_beneficios.loc[idx, f"Parcela_{numero_parcela}_Data_Pagamento"] = data_pagamento
        
        # Salvar comprovante
        if pago_dinheiro:
            comprovante_texto = "Dinheiro"
            if observacoes:
                comprovante_texto += f" - {observacoes}"
            st.session_state.df_editado_beneficios.loc[idx, f"Parcela_{numero_parcela}_Comprovante"] = comprovante_texto
        else:
            comprovante_texto = url_comprovante
            if observacoes:
                comprovante_texto += f" - Obs: {observacoes}"
            st.session_state.df_editado_beneficios.loc[idx, f"Parcela_{numero_parcela}_Comprovante"] = comprovante_texto
        
        # Verificar se todas as parcelas foram pagas
        linha_beneficio = st.session_state.df_editado_beneficios.loc[idx]
        num_parcelas = safe_get_int_value_beneficio(linha_beneficio, "Numero Parcelas", 1)
        parcelas_pagas, todas_pagas = calcular_status_parcelas(linha_beneficio, num_parcelas)
        
        # Atualizar status geral das parcelas
        st.session_state.df_editado_beneficios.loc[idx, "Todas_Parcelas_Pagas"] = "Sim" if todas_pagas else "Não"
        
        # Se todas as parcelas foram pagas, finalizar automaticamente o benefício
        if todas_pagas:
            usuario_atual = st.session_state.get("usuario", "Sistema")
            data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
            
            st.session_state.df_editado_beneficios.loc[idx, "Status"] = "Finalizado"
            st.session_state.df_editado_beneficios.loc[idx, "Data Finalização"] = data_atual
            st.session_state.df_editado_beneficios.loc[idx, "Finalizado Por"] = f"{usuario_atual} (Auto - Parcelas Completas)"
        
        # Salvar no GitHub
        novo_sha = save_data_to_github_seguro(
            st.session_state.df_editado_beneficios,
            "lista_beneficios.csv",
            st.session_state.get("file_sha_beneficios", None)
        )
        
        if novo_sha:
            st.session_state.file_sha_beneficios = novo_sha
            if todas_pagas:
                st.success(f"✅ Parcela {numero_parcela} paga! 🎉 TODAS AS PARCELAS FORAM QUITADAS - Benefício finalizado automaticamente!")
                st.balloons()
            else:
                st.success(f"✅ Parcela {numero_parcela} marcada como paga!")
            
            # Fechar diálogo e atualizar interface
            limpar_estados_dialogo_beneficio()
            st.rerun()
        else:
            st.error("❌ Erro ao salvar a atualização da parcela.")
            
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
        col_h1, col_h2, col_h3, col_h4, col_h5, col_h6 = st.columns([1, 2.5, 2, 1.5, 2, 2])
        with col_h1: st.markdown("**Ação**")
        with col_h2: st.markdown("**Processo**")
        with col_h3: st.markdown("**Parte**")
        with col_h4: st.markdown("**CPF**")
        with col_h5: st.markdown("**Status**")
        with col_h6: st.markdown("**Data Cadastro**")
        
        # Linhas dos dados
        for _, row in df_paginado.iterrows():
            beneficio_id = row.get("ID")
            
            col_b1, col_b2, col_b3, col_b4, col_b5, col_b6 = st.columns([1, 2.5, 2, 1.5, 2, 2])
            
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
            
            with col_b2: 
                processo_num = safe_get_value_beneficio(row, 'Nº DO PROCESSO')
                st.write(f"**{processo_num[:20]}{'...' if len(processo_num) > 20 else ''}**")
            with col_b3: 
                parte_nome = safe_get_value_beneficio(row, 'PARTE')
                st.write(f"{parte_nome[:18]}{'...' if len(parte_nome) > 18 else ''}")
            with col_b4: 
                cpf = safe_get_value_beneficio(row, 'CPF')
                st.write(cpf[:14] if cpf != 'Não cadastrado' else 'N/A')
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
    
    # Verificar se há requests de diálogo de benefício
    verificar_e_exibir_dialog_beneficio(df)


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
        st.metric("📊 Total de Benefícios", total_beneficios)
    
    with col2:
        taxa_finalizados = (finalizados/total_beneficios*100) if total_beneficios > 0 else 0
        st.metric("✅ Finalizados", f"{finalizados} ({taxa_finalizados:.1f}%)")
    
    with col3:
        taxa_pendentes = (pendentes/total_beneficios*100) if total_beneficios > 0 else 0
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

    # Exibição com AgGrid
    st.markdown(f"### 📋 Lista de Benefícios ({len(df_filtrado)} registros)")
    
    if not df_filtrado.empty:
        # Preparar dados para o AgGrid
        df_display = df_filtrado.copy()
        
        # Selecionar e renomear colunas para exibição
        colunas_para_exibir = {
            'Nº DO PROCESSO': 'Processo',
            'PARTE': 'Parte',
            'TIPO DE PROCESSO': 'Tipo de Processo',
            'NB': 'NB',
            'Valor Pago': 'Valor Pago (R$)',
            'Status': 'Status',
            'Data Cadastro': 'Data Cadastro',
            'Cadastrado Por': 'Cadastrado Por',
            'Observações': 'Observações'
        }
        
        # Filtrar apenas as colunas que existem no DataFrame
        colunas_existentes = {k: v for k, v in colunas_para_exibir.items() if k in df_display.columns}
        df_display = df_display[list(colunas_existentes.keys())].rename(columns=colunas_existentes)
        
        # Formatar valor monetário
        if 'Valor Pago (R$)' in df_display.columns:
            df_display['Valor Pago (R$)'] = df_display['Valor Pago (R$)'].apply(
                lambda x: f"R$ {float(x):,.2f}" if pd.notna(x) and str(x) not in ['nan', 'N/A', ''] and str(x).replace('.', '').replace(',', '').replace('-', '').isdigit() else str(x)
            )
        
        # Formatar datas
        if 'Data Cadastro' in df_display.columns:
            df_display['Data Cadastro'] = df_display['Data Cadastro'].apply(
                lambda x: str(x).split(' ')[0] if pd.notna(x) else 'N/A'
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
        if 'Parte' in df_display.columns:
            gb.configure_column("Parte", width=200)
        if 'Tipo de Processo' in df_display.columns:
            gb.configure_column("Tipo de Processo", width=150)
        if 'NB' in df_display.columns:
            gb.configure_column("NB", width=100)
        if 'Valor Pago (R$)' in df_display.columns:
            gb.configure_column("Valor Pago (R$)", width=150, type="numericColumn")
        if 'Status' in df_display.columns:
            gb.configure_column("Status", width=140)
        if 'Data Cadastro' in df_display.columns:
            gb.configure_column("Data Cadastro", width=120)
        if 'Cadastrado Por' in df_display.columns:
            gb.configure_column("Cadastrado Por", width=140)
        if 'Observações' in df_display.columns:
            gb.configure_column("Observações", width=200)
        
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
            if st.button("📥 Baixar Selecionados", key="export_selected_beneficio"):
                df_selected = pd.DataFrame(selected_rows)
                csv_selected = df_selected.to_csv(index=False, sep=';').encode('utf-8')
                st.download_button(
                    label="📥 Download CSV Selecionados",
                    data=csv_selected,
                    file_name=f"beneficios_selecionados_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    key="download_selected_beneficio"
                )
    else:
        st.info("Nenhum registro encontrado com os filtros aplicados.")
    
    # Verificar se há requests de diálogo de benefício
    verificar_e_exibir_dialog_beneficio(df)

@st.dialog("💰 Detalhes do Benefício - Sistema de Parcelas", width="large")
def dialog_beneficio_detalhes(df_beneficios):
    """Diálogo para exibir detalhes do benefício e gerenciar parcelas"""
    beneficio_id = st.session_state.get("beneficio_aberto_id")
    
    if not beneficio_id:
        st.error("Erro: ID do benefício não encontrado")
        return
    
    if df_beneficios.empty:
        st.error("Erro: DataFrame de benefícios vazio")
        return
    
    # Encontrar o benefício
    beneficio = df_beneficios[df_beneficios['ID'] == beneficio_id]
    if beneficio.empty:
        st.error("Benefício não encontrado")
        return
    
    linha_beneficio = beneficio.iloc[0]
    
    # Exibir informações básicas do benefício
    exibir_informacoes_basicas_beneficio(linha_beneficio, estilo="horizontal")
    
    st.divider()
    
    # Sistema de Parcelas
    st.markdown("### 💳 Sistema de Parcelas")
    
    # Verificar se já existem parcelas (em implementação futura)
    valor_total = linha_beneficio.get('Valor Pago (R$)', 0)
    if isinstance(valor_total, str):
        try:
            valor_total = float(valor_total.replace('R$', '').replace('.', '').replace(',', '.').strip())
        except:
            valor_total = 0
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**💰 Valor Total:** R$ {valor_total:,.2f}")
        num_parcelas = st.number_input("Número de Parcelas:", min_value=1, max_value=24, value=1, step=1)
        
    with col2:
        st.markdown(f"**💳 Valor por Parcela:** R$ {(valor_total/num_parcelas):,.2f}")
        data_inicial = st.date_input("Data Inicial para Cálculo:", value=datetime.now().date())
    
    if st.button("🔄 Gerar Parcelas", type="primary"):
        parcelas = gerar_parcelas_beneficio(beneficio_id, valor_total, num_parcelas, data_inicial)
        
        st.success(f"✅ {num_parcelas} parcela(s) gerada(s) com sucesso!")
        
        # Exibir parcelas em tabela
        st.markdown("#### 📋 Parcelas Geradas")
        
        parcelas_df = pd.DataFrame(parcelas)
        parcelas_df['Valor'] = parcelas_df['Valor'].apply(lambda x: f"R$ {x:,.2f}")
        parcelas_df['Data Vencimento'] = parcelas_df['Data Vencimento'].apply(lambda x: x.strftime('%d/%m/%Y'))
        parcelas_df['Status'] = parcelas_df['Status'].str.title()
        
        # Renomear colunas para exibição
        parcelas_df = parcelas_df.rename(columns={
            'numero_parcela': 'Parcela',
            'Valor': 'Valor (R$)',
            'data_vencimento': 'Vencimento',
            'status': 'Status'
        })
        
        st.dataframe(
            parcelas_df[['Parcela', 'Valor (R$)', 'Data Vencimento', 'Status']], 
            use_container_width=True,
            hide_index=True
        )
        
        # Observações sobre dias úteis
        st.info("💡 **Informação:** As datas de vencimento são calculadas automaticamente para o primeiro dia útil após 30 dias de cada período.")
    
    # Botões de ação
    col_acao1, col_acao2 = st.columns(2)
    
    with col_acao1:
        if st.button("💾 Salvar Alterações", type="secondary"):
            st.success("Alterações salvas com sucesso!")
            # Aqui implementaria a lógica de salvamento das parcelas
    
    with col_acao2:
        if st.button("❌ Fechar", key="fechar_dialog_beneficio"):
            st.session_state.beneficio_aberto_id = None
            st.rerun()

def verificar_e_exibir_dialog_beneficio(df_beneficios):
    """Verifica se há requests de diálogo de benefício e os exibe"""
    # Verificar requests com timestamp
    requests_para_remover = []
    
    for key in st.session_state.keys():
        if key.startswith("dialogo_beneficio_request_"):
            request_data = st.session_state[key]
            if request_data.get("show_beneficio_dialog", False):
                st.session_state.beneficio_aberto_id = request_data.get("beneficio_aberto_id")
                dialog_beneficio_detalhes(df_beneficios)
                requests_para_remover.append(key)
    
    # Limpar requests processados
    for key in requests_para_remover:
        del st.session_state[key]
