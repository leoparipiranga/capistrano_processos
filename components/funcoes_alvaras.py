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

def safe_get_field_value_alvara(linha_df, campo, default="Não informado"):
    """
    Função para extrair valor de um campo do DataFrame de forma segura
    """
    try:
        if linha_df.empty:
            return default
        valor = linha_df.iloc[0].get(campo, default)
        return safe_get_value_alvara(valor, default)
    except (IndexError, KeyError):
        return default

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

def safe_get_field_value_alvara(data, key, default=''):
    """Obtém valor de forma segura, tratando NaN e valores None"""
    value = data.get(key, default)
    if value is None:
        return default
    # Converter para string e verificar se não é 'nan'
    str_value = str(value)
    if str_value.lower() in ['nan', 'none', '', 'null']:
        return default
    return str_value

def safe_get_hc_value_alvara(data, key, default=0.0):
    """Obtém valor de honorário contratual de forma segura para Alvarás"""
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

def calcular_total_hc_alvara(linha_alvara):
    """Calcula o total dos honorários contratuais (HC + HC1 + HC2) para Alvarás"""
    hc = safe_get_hc_value_alvara(linha_alvara, "Honorarios Contratuais", 0.0)
    hc1 = safe_get_hc_value_alvara(linha_alvara, "HC1", 0.0)
    hc2 = safe_get_hc_value_alvara(linha_alvara, "HC2", 0.0)
    return hc + hc1 + hc2

def mostrar_detalhes_hc_alvara(linha_alvara, key_suffix=""):
    """Mostra detalhes individuais dos honorários contratuais com opção de expandir"""
    total_hc = calcular_total_hc_alvara(linha_alvara)
    
    if total_hc > 0:
        with st.expander(f"💼 Ver Detalhes dos Honorários Contratuais (Total: R$ {total_hc:.2f})"):
            col1, col2, col3 = st.columns(3)
            
            hc = safe_get_hc_value_alvara(linha_alvara, "Honorarios Contratuais", 0.0)
            hc1 = safe_get_hc_value_alvara(linha_alvara, "HC1", 0.0)
            hc2 = safe_get_hc_value_alvara(linha_alvara, "HC2", 0.0)
            
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
        st.info("💼 Nenhum honorário contratual cadastrado para este alvará.")

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
    
    status_atual = safe_get_field_value_alvara(linha_alvara, 'Status')
    status_class = {
        "Cadastrado": "background-color: #fff3cd; color: #856404;",
        "Enviado para o Financeiro": "background-color: #d1ecf1; color: #0c5460;",
        "Financeiro - Enviado para Rodrigo": "background-color: #d4edda; color: #155724;",
        "Finalizado": "background-color: #d1e7dd; color: #0f5132;"
    }.get(status_atual, "background-color: #e2e3e5; color: #383d41;")
    
    # Calcular total de honorários contratuais
    total_hc = calcular_total_hc_alvara(linha_alvara)
    
    st.markdown("### 📋 Resumo do Alvará")
    st.markdown(f"""
    <div class="compact-grid">
        <div class="compact-item">
            <div class="compact-label">📄 PROCESSO</div>
            <div class="compact-value">{safe_get_field_value_alvara(linha_alvara, 'Processo')}</div>
        </div>
        <div class="compact-item">
            <div class="compact-label">👤 PARTE</div>
            <div class="compact-value">{safe_get_field_value_alvara(linha_alvara, 'Parte')}</div>
        </div>
        <div class="compact-item">
            <div class="compact-label">🆔 CPF</div>
            <div class="compact-value">{safe_get_field_value_alvara(linha_alvara, 'CPF')}</div>
        </div>
        <div class="compact-item">
            <div class="compact-label">📊 STATUS</div>
            <div class="compact-value">
                <span class="compact-status" style="{status_class}">{status_atual}</span>
            </div>
        </div>
        <div class="compact-item">
            <div class="compact-label">💰 PAGAMENTO</div>
            <div class="compact-value">{safe_get_field_value_alvara(linha_alvara, 'Pagamento')}</div>
        </div>
        <div class="compact-item">
            <div class="compact-label">💼 TOTAL HC</div>
            <div class="compact-value">R$ {total_hc:.2f}</div>
        </div>
        <div class="compact-item">
            <div class="compact-label">🏛️ ÓRGÃO</div>
            <div class="compact-value">{safe_get_field_value_alvara(linha_alvara, 'Órgão Judicial')[:20]}...</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

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

def render_tab_anexos_alvara(processo, alvara_id, numero_processo):
    """Renderiza sistema de anexos dentro da tab de ações"""
    
    st.markdown("#### 📎 Anexar Documentos")
    
    # Checkbox para anexar múltiplos documentos
    anexar_multiplos = st.checkbox("Anexar múltiplos documentos", key=f"multiplos_tab_{alvara_id}")
    
    col_doc1, col_doc2 = st.columns(2)
    
    with col_doc1:
        st.markdown("**📄 Comprovante da Conta**")
        if anexar_multiplos:
            comprovante_conta = st.file_uploader(
                "Anexar comprovantes da conta:",
                type=["pdf", "jpg", "jpeg", "png"],
                accept_multiple_files=True,
                key=f"comprovante_tab_{numero_processo}"
            )
        else:
            comprovante_conta = st.file_uploader(
                "Anexar comprovante da conta:",
                type=["pdf", "jpg", "jpeg", "png"],
                key=f"comprovante_tab_{numero_processo}"
            )
                
    with col_doc2:
        st.markdown("**📄 PDF do Alvará**")
        if anexar_multiplos:
            pdf_alvara = st.file_uploader(
                "Anexar PDFs do alvará:",
                type=["pdf"],
                accept_multiple_files=True,
                key=f"pdf_tab_{numero_processo}"
            )
        else:
            pdf_alvara = st.file_uploader(
                "Anexar PDF do alvará:",
                type=["pdf"],
                key=f"pdf_tab_{numero_processo}"
            )
    
    return comprovante_conta, pdf_alvara, anexar_multiplos

# =====================================
# FUNÇÕES DE RENDERIZAÇÃO DE TABS
# =====================================

def render_tab_info_alvara(processo, alvara_id):
    """Renderiza a tab de informações do alvará"""
        
    col_det1, col_det2 = st.columns(2)
    
    with col_det1:
        st.markdown("**📋 Dados Básicos:**")
        st.write(f"**CPF:** {safe_get_field_value_alvara(processo, 'CPF')}")
        st.write(f"**Agência:** {safe_get_field_value_alvara(processo, 'Agência')}")
        st.write(f"**Conta:** {safe_get_field_value_alvara(processo, 'Conta')}")
        st.write(f"**Banco:** {safe_get_field_value_alvara(processo, 'Banco')}")
    
    with col_det2:
        st.markdown("**💰 Valores:**")
        st.write(f"**Valor Sacado:** {safe_format_currency_alvara(processo.get('Valor Sacado'))}")
        st.write(f"**Valor Cliente:** {safe_format_currency_alvara(processo.get('Valor Cliente Final'))}")
        st.write(f"**Honorários Sucumbenciais:** {safe_format_currency_alvara(processo.get('Honorarios Sucumbenciais Valor'))}")
        st.write(f"**Prospector/Parceiro:** {safe_format_currency_alvara(processo.get('Prospector Parceiro'))}")
    
    # Mostrar detalhes dos honorários contratuais
    mostrar_detalhes_hc_alvara(processo, f"info_{alvara_id}")
    
    # Observações
    if safe_get_field_value_alvara(processo, 'Observacoes Financeiras'):
        st.markdown("### 📝 Observações Financeiras")
        st.info(safe_get_field_value_alvara(processo, 'Observacoes Financeiras'))

def render_tab_acoes_alvara(df, processo, alvara_id, status_atual, perfil_usuario):
    """Renderiza a tab de ações do alvará - mantém toda a lógica original"""
    
    # Usar a função original de edição, mas sem o cabeçalho
    linha_processo_df = df[df["ID"].astype(str) == str(alvara_id)]
    
    if len(linha_processo_df) == 0:
        st.error(f"❌ Alvará com ID {alvara_id} não encontrado")
        return
    
    linha_processo = linha_processo_df.iloc[0]
    numero_processo = linha_processo.get("Processo", "N/A")
    
    # Renderizar ações baseadas no status - usando a lógica original
    if status_atual == "Cadastrado" and perfil_usuario in ["Cadastrador", "Admin"]:
        # Usar função auxiliar para anexos
        comprovante_conta, pdf_alvara, anexar_multiplos = render_tab_anexos_alvara(processo, alvara_id, numero_processo)
        
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
            
            if st.button("📤 Enviar para Financeiro", type="primary", key=f"enviar_fin_tab_{alvara_id}"):
                # Salvar arquivos
                
                if anexar_multiplos:
                    # Salvar múltiplos arquivos
                    comprovante_urls = []
                    for i, arquivo in enumerate(comprovante_conta):
                        url = salvar_arquivo(arquivo, numero_processo, f"comprovante_{i+1}")
                        if url:  # Só adicionar se não for None
                            comprovante_urls.append(url)
                    comprovante_url = "; ".join(comprovante_urls) if comprovante_urls else None
                    
                    pdf_urls = []
                    for i, arquivo in enumerate(pdf_alvara):
                        url = salvar_arquivo(arquivo, numero_processo, f"alvara_{i+1}")
                        if url:  # Só adicionar se não for None
                            pdf_urls.append(url)
                    pdf_url = "; ".join(pdf_urls) if pdf_urls else None
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
                    # Recolher o card após a ação
                    st.session_state.alvara_expanded_cards.discard(alvara_id)
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
            render_tab_acoes_financeiro_alvara(df, linha_processo, alvara_id)
        else:
            st.warning("⚠️ Apenas usuários Financeiro e Admin podem gerenciar valores financeiros.")
    
    elif status_atual == "Financeiro - Enviado para Rodrigo" and perfil_usuario in ["Financeiro", "Admin"]:
        render_tab_acoes_rodrigo_alvara(df, linha_processo, alvara_id)
    
    elif status_atual == "Finalizado":
        # Documentos anexados
        st.markdown("**📄 Documentos anexos:**")
        col_docs1, col_docs2 = st.columns(2)
        
        with col_docs1:
            if linha_processo.get("Comprovante Conta"):
                from components.functions_controle import baixar_arquivo_drive
                baixar_arquivo_drive(linha_processo["Comprovante Conta"], "📄 Comprovante Conta")
        
        with col_docs2:
            if linha_processo.get("PDF Alvará"):
                from components.functions_controle import baixar_arquivo_drive
                baixar_arquivo_drive(linha_processo["PDF Alvará"], "📄 PDF Alvará")
    
    else:
        # Status não reconhecido ou sem permissão
        if perfil_usuario == "Admin":
            st.warning("⚠️ Status não reconhecido ou não implementado.")
            st.info(f"Status atual: {status_atual}")
        else:
            st.error(f"❌ Seu perfil ({perfil_usuario}) não pode editar processos com status '{status_atual}'")

def render_tab_historico_alvara(processo, alvara_id):
    """Renderiza a tab de histórico do alvará"""
    
    st.markdown("### 📜 Histórico do Processo")
    
    # Timeline do processo
    status_atual = safe_get_field_value_alvara(processo, 'Status')
    
    # Etapas do fluxo
    etapas = [
        {
            "titulo": "📝 Cadastrado",
            "data": safe_get_field_value_alvara(processo, 'Data Cadastro'),
            "responsavel": safe_get_field_value_alvara(processo, 'Cadastrado Por'),
            "concluida": True  # Sempre concluída se existe
        },
        {
            "titulo": "📤 Enviado para Financeiro",
            "data": safe_get_field_value_alvara(processo, 'Data Envio Financeiro'),
            "responsavel": safe_get_field_value_alvara(processo, 'Enviado Financeiro Por'),
            "concluida": status_atual in ["Enviado para o Financeiro", "Financeiro - Enviado para Rodrigo", "Finalizado"]
        },
        {
            "titulo": "👨‍💼 Enviado para Rodrigo",
            "data": safe_get_field_value_alvara(processo, 'Data Envio Rodrigo'),
            "responsavel": safe_get_field_value_alvara(processo, 'Enviado Rodrigo Por'),
            "concluida": status_atual in ["Financeiro - Enviado para Rodrigo", "Finalizado"]
        },
        {
            "titulo": "🎯 Finalizado",
            "data": safe_get_field_value_alvara(processo, 'Data Finalizacao'),
            "responsavel": safe_get_field_value_alvara(processo, 'Finalizado Por'),
            "concluida": status_atual == "Finalizado"
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

def render_tab_acoes_financeiro_alvara(df, linha_processo, alvara_id):
    """Renderiza ações específicas para o perfil Financeiro"""
    
    # Checkbox para controle de pendência
    pendente_cadastro = st.checkbox(
        "⏳ Pendente de cadastro",
        value=linha_processo.get("Pendente de Cadastro", "") == "Sim",
        help="Marque se os dados ainda estão pendentes de cadastro. Isso desabilitará os campos de valor.",
        key=f"pendente_tab_{alvara_id}"
    )
    
    st.markdown("---")
    
    # Controle HC com botão progressivo (FORA do formulário)
    if st.button("➕ Adicionar Honorário Contratual", key=f"btn_hc_tab_{alvara_id}"):
        # Inicializar estado do botão HC se não existir
        if f"hc_nivel_tab_{alvara_id}" not in st.session_state:
            st.session_state[f"hc_nivel_tab_{alvara_id}"] = 0
        
        st.session_state[f"hc_nivel_tab_{alvara_id}"] = (st.session_state[f"hc_nivel_tab_{alvara_id}"] + 1) % 3
    
    # Inicializar estado do botão HC
    if f"hc_nivel_tab_{alvara_id}" not in st.session_state:
        st.session_state[f"hc_nivel_tab_{alvara_id}"] = 0
    
    # Formulário para valores financeiros
    with st.form(f"form_valores_financeiros_tab_{alvara_id}"):
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
        nivel_hc = st.session_state.get(f"hc_nivel_tab_{alvara_id}", 0)
        
        if nivel_hc >= 1:  # Primeira pressão: Mostrar HC2
            hc1_valor = st.number_input(
                "Honorário Contratual 2:",
                min_value=0.0,
                value=float(linha_processo.get("HC1", "0") or "0"),
                step=0.01,
                format="%.2f",
                disabled=pendente_cadastro,
                key=f"hc2_tab_{alvara_id}"
            )
        
        if nivel_hc >= 2:  # Segunda pressão: Mostrar HC3
            hc2_valor = st.number_input(
                "Honorário Contratual 3:",
                min_value=0.0,
                value=float(linha_processo.get("HC2", "0") or "0"),
                step=0.01,
                format="%.2f",
                disabled=pendente_cadastro,
                key=f"hc3_tab_{alvara_id}"
            )
        
        # Campo de observações
        observacoes_financeiras = st.text_area(
            "📝 Observações Financeiras:",
            value=safe_get_field_value_alvara(linha_processo, "Observacoes Financeiras", ""),
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
        
        # Lógica de processamento (igual à original)
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
                    nivel_hc = st.session_state.get(f"hc_nivel_tab_{alvara_id}", 0)
                    if nivel_hc >= 1:  # HC2 está visível
                        st.session_state.df_editado_alvaras.loc[idx, "HC1"] = hc1_valor
                    if nivel_hc >= 2:  # HC3 está visível
                        st.session_state.df_editado_alvaras.loc[idx, "HC2"] = hc2_valor
                
                # Salvar observações sempre (converter para string para evitar warning do pandas)
                observacoes_str = str(observacoes_financeiras) if observacoes_financeiras is not None else ""
                st.session_state.df_editado_alvaras.loc[idx, "Observacoes Financeiras"] = observacoes_str
                
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
                    nivel_hc = st.session_state.get(f"hc_nivel_tab_{alvara_id}", 0)
                    if nivel_hc >= 1:  # HC2 está visível
                        st.session_state.df_editado_alvaras.loc[idx, "HC1"] = hc1_valor
                    if nivel_hc >= 2:  # HC3 está visível
                        st.session_state.df_editado_alvaras.loc[idx, "HC2"] = hc2_valor
                else:
                    # Se pendente de cadastro, enviar com valores em branco
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
                
                # Recolher o card após a ação
                st.session_state.alvara_expanded_cards.discard(alvara_id)
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Erro ao enviar para Rodrigo: {str(e)}")

def render_tab_acoes_rodrigo_alvara(df, linha_processo, alvara_id):
    """Renderiza ações específicas para a etapa Rodrigo"""
    
    st.markdown("**📋 Informações do processo:**")
    st.write(f"- Enviado para Rodrigo em: {linha_processo.get('Data Envio Rodrigo', 'Não informado')}")
    st.write(f"- Enviado por: {linha_processo.get('Enviado Rodrigo Por', 'Não informado')}")
    
    st.markdown("---")
    
    # Controle HC com botão progressivo (FORA do formulário)
    if st.button("➕ Adicionar Honorário Contratual", key=f"btn_hc_rodrigo_tab_{alvara_id}"):
        # Inicializar estado do botão HC se não existir
        if f"hc_nivel_rodrigo_tab_{alvara_id}" not in st.session_state:
            st.session_state[f"hc_nivel_rodrigo_tab_{alvara_id}"] = 0
        
        st.session_state[f"hc_nivel_rodrigo_tab_{alvara_id}"] = (st.session_state[f"hc_nivel_rodrigo_tab_{alvara_id}"] + 1) % 3

    # Inicializar estado do botão HC
    if f"hc_nivel_rodrigo_tab_{alvara_id}" not in st.session_state:
        st.session_state[f"hc_nivel_rodrigo_tab_{alvara_id}"] = 0

    # Formulário para valores financeiros (AGORA HABILITADOS para Rodrigo)
    with st.form(f"form_valores_rodrigo_tab_{alvara_id}"):
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
        nivel_hc = st.session_state.get(f"hc_nivel_rodrigo_tab_{alvara_id}", 0)
        
        if nivel_hc >= 1:  # Primeira pressão: Mostrar HC2
            hc1_valor = st.number_input(
                "Honorário Contratual 2:",
                min_value=0.0,
                value=float(linha_processo.get("HC1", "0") or "0"),
                step=0.01,
                format="%.2f",
                key=f"hc2_rodrigo_tab_{alvara_id}"
            )
        
        if nivel_hc >= 2:  # Segunda pressão: Mostrar HC3
            hc2_valor = st.number_input(
                "Honorário Contratual 3:",
                min_value=0.0,
                value=float(linha_processo.get("HC2", "0") or "0"),
                step=0.01,
                format="%.2f",
                key=f"hc3_rodrigo_tab_{alvara_id}"
            )
        
        # Campo de observações
        observacoes_financeiras = st.text_area(
            "📝 Observações Financeiras:",
            value=safe_get_field_value_alvara(linha_processo, "Observacoes Financeiras", ""),
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
        
        # Lógica de processamento (igual à original)
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
                nivel_hc = st.session_state.get(f"hc_nivel_rodrigo_tab_{alvara_id}", 0)
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
                nivel_hc = st.session_state.get(f"hc_nivel_rodrigo_tab_{alvara_id}", 0)
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
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Erro ao finalizar processo: {str(e)}")
    
def interface_cadastro_alvara(df, perfil_usuario):
    """Interface para cadastrar novos alvarás"""
    
    # LIMPAR ESTADOS DE DIÁLOGO ao entrar na aba de cadastro
    if st.session_state.get("show_alvara_dialog", False):
        st.session_state.show_alvara_dialog = False
    if st.session_state.get("processo_aberto_id") is not None:
        st.session_state.processo_aberto_id = None
    
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
                    f"{col} *",
                    key=f"input_alvaras_{col}_{st.session_state.form_reset_counter_alvaras}",
                    max_chars=50,
                    help=hints.get(col, "") + " (Campo obrigatório)",
                    placeholder="0000000-00.0000.0.00.0000"
                )
                if any(c.isalpha() for c in valor_raw):
                    aviso_letras = True
                valor = ''.join([c for c in valor_raw if not c.isalpha()])
            
            elif col == "Parte":
                valor = st.text_input(
                    f"{col} *",
                    key=f"input_alvaras_{col}_{st.session_state.form_reset_counter_alvaras}",
                    max_chars=100,
                    help=hints.get(col, "") + " (Campo obrigatório)",
                    placeholder="NOME COMPLETO DA PARTE"
                ).upper()

            elif col == "CPF":
                valor_raw = st.text_input(
                    f"{col} *",
                    key=f"input_alvaras_{col}_{st.session_state.form_reset_counter_alvaras}",
                    max_chars=14,
                    help=hints.get(col, "") + " (Campo obrigatório)",
                    placeholder="000.000.000-00"
                )
                if any(c.isalpha() for c in valor_raw):
                    aviso_letras = True
                valor = ''.join([c for c in valor_raw if not c.isalpha()])

            elif col == "Órgão Judicial":
                # Campo selectbox + botão usando nova interface
                valor = campo_orgao_judicial(
                    label=f"{col} *",
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
        
        # =====================================
        # VALIDAÇÃO COMPLETA DE CAMPOS OBRIGATÓRIOS - ALVARÁ
        # =====================================
        
        campos_vazios = []
        
        # Validar campos obrigatórios
        if not nova_linha.get("Processo", "").strip():
            campos_vazios.append("Processo")
        if not nova_linha.get("Parte", "").strip():
            campos_vazios.append("Parte")
        if not nova_linha.get("CPF", "").strip():
            campos_vazios.append("CPF")
        if not nova_linha.get("Pagamento", "").strip():
            campos_vazios.append("Pagamento")
        if not nova_linha.get("Órgão Judicial", "").strip():
            campos_vazios.append("Órgão Judicial")
        
        # Se há campos vazios, exibir erro detalhado
        if campos_vazios:
            if len(campos_vazios) == 1:
                st.error(f"❌ O campo obrigatório **{campos_vazios[0]}** deve ser preenchido.")
            else:
                campos_texto = ", ".join(campos_vazios[:-1]) + " e " + campos_vazios[-1]
                st.error(f"❌ Os seguintes campos obrigatórios devem ser preenchidos: **{campos_texto}**.")
        # Validações adicionais de formato
        else:
            # Validar CPF
            cpf_valor = nova_linha.get("CPF", "")
            cpf_numeros = ''.join([c for c in cpf_valor if c.isdigit()])
            
            if cpf_valor and len(cpf_numeros) != 11:
                st.error("❌ CPF deve conter exatamente 11 números.")
            else:
                from components.functions_controle import validar_cpf
                
                if cpf_valor and not validar_cpf(cpf_valor):
                    st.error("❌ CPF inválido. Verifique e tente novamente.")
                # Verificar se processo já existe
                elif ("Processo" in df.columns and 
                      nova_linha.get("Processo", "") in df["Processo"].values):
                    st.warning(f"⚠️ Processo {nova_linha.get('Processo', '')} já cadastrado.")
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
    
    # LIMPAR ESTADOS DE DIÁLOGO ao entrar na aba de visualização
    if st.session_state.get("show_alvara_dialog", False):
        st.session_state.show_alvara_dialog = False
    if st.session_state.get("processo_aberto_id") is not None:
        st.session_state.processo_aberto_id = None
    
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
            
        st.markdown(f"**Cadastrados Hoje:** {hoje_count}")
    
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

    # b) Lógica de Paginação
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
                processo_num = safe_get_field_value_alvara(processo, 'Processo', 'N/A')
                st.write(f"**{processo_num[:20]}{'...' if len(processo_num) > 20 else ''}**")
            
            with col_parte:
                requerente = safe_get_field_value_alvara(processo, 'Requerente', 'N/A')
                st.write(f"{requerente[:25]}{'...' if len(requerente) > 25 else ''}")
                
            with col_orgao:
                orgao = safe_get_field_value_alvara(processo, 'Órgão Judicial', 'N/A')
                st.write(f"{orgao[:20]}{'...' if len(orgao) > 20 else ''}")
            
            with col_valor:
                st.write(safe_format_currency_alvara(processo.get('Valor do Alvará')))
                
            with col_status:
                status_atual = safe_get_field_value_alvara(processo, 'Status', 'N/A')
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
                data_cadastro = safe_get_field_value_alvara(processo, 'Data Cadastro', 'N/A')
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

# =====================================
# FUNÇÕES DE INTERFACE PRINCIPAL - ALVARÁS
# =====================================

def interface_lista_alvaras(df, perfil_usuario):
    """Interface principal para listar alvarás com sistema de dropdown"""
    
    # LIMPAR ESTADOS DE DIÁLOGO ao entrar na aba de lista
    if st.session_state.get("show_alvara_dialog", False):
        st.session_state.show_alvara_dialog = False
    if st.session_state.get("processo_aberto_id") is not None:
        st.session_state.processo_aberto_id = None
    
    # Inicializar estado dos cards expandidos
    if "alvara_expanded_cards" not in st.session_state:
        st.session_state.alvara_expanded_cards = set()
    
    if df.empty:
        st.info("ℹ️ Não há alvarás para visualizar.")
        return

    # Cards de estatísticas
    total_alvaras = len(df)
    finalizados = len(df[df["Status"] == "Finalizado"]) if "Status" in df.columns else 0
    pendentes = total_alvaras - finalizados
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Alvarás", total_alvaras)
    
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
        status_filtro = st.selectbox("Status:", options=status_unicos, key="lista_alvara_status")
        
    with col_filtro2:
        usuarios_unicos = ["Todos"] + list(df["Cadastrado Por"].dropna().unique()) if "Cadastrado Por" in df.columns else ["Todos"]
        usuario_filtro = st.selectbox("Cadastrado Por:", options=usuarios_unicos, key="lista_alvara_user")
    
    with col_filtro3:
        orgaos_unicos = ["Todos"] + list(df["Órgão Judicial"].dropna().unique()) if "Órgão Judicial" in df.columns else ["Todos"]
        orgao_filtro = st.selectbox("Órgão Judicial:", options=orgaos_unicos, key="lista_alvara_orgao")
    
    with col_filtro4:
        pesquisa = st.text_input("🔎 Pesquisar:", key="lista_alvara_search")

    # Aplicar filtros
    df_filtrado = df.copy()
    
    if status_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Status"] == status_filtro]
    
    if usuario_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Cadastrado Por"] == usuario_filtro]
        
    if orgao_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Órgão Judicial"] == orgao_filtro]
    
    if pesquisa:
        mask = pd.Series([False] * len(df_filtrado))
        for col in ["Parte", "Processo", "CPF"]:
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
            if st.button("🔽 Expandir Todos", key="expandir_todos_alvaras"):
                # Adicionar todos os IDs dos alvarás filtrados ao set de expandidos
                for _, processo in df_filtrado.iterrows():
                    alvara_id = processo.get("ID", "N/A")
                    st.session_state.alvara_expanded_cards.add(alvara_id)
                st.rerun()
        
        with col_exp2:
            if st.button("🔼 Recolher Todos", key="recolher_todos_alvaras"):
                # Limpar o set de cards expandidos
                st.session_state.alvara_expanded_cards.clear()
                st.rerun()

    # Paginação
    if "current_page_alvaras" not in st.session_state:
        st.session_state.current_page_alvaras = 1
    
    items_per_page = 10
    total_registros = len(df_filtrado)
    total_pages = math.ceil(total_registros / items_per_page) if items_per_page > 0 else 1
    
    start_idx = (st.session_state.current_page_alvaras - 1) * items_per_page
    end_idx = start_idx + items_per_page
    df_paginado = df_filtrado.iloc[start_idx:end_idx]

    # CSS para cards dropdown (exatamente igual ao benefícios)
    st.markdown("""
    <style>
    .alvara-card {
        border: none;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        background-color: transparent;
        transition: all 0.3s ease;
    }
    .alvara-card:hover {
        border-color: transparent;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .alvara-card.expanded {
        background-color: transparent;
        border-color: transparent;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }
    .alvara-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        cursor: pointer;
    }
    .alvara-info-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 8px;
        margin-top: 8px;
    }
    .info-item {
        background: transparent;
        padding: 6px 8px;
        border-radius: 4px;
        border-left: 3px solid #0066cc;
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

    # Lista de Alvarás
    if not df_paginado.empty:
        st.markdown(f"### 📋 Lista de Alvarás ({total_registros} encontrados)")
        
        # Renderizar cards
        for _, processo in df_paginado.iterrows():
            alvara_id = processo.get("ID", "N/A")
            status_atual = safe_get_field_value_alvara(processo, 'Status')
            
            # Verificar se o card está expandido
            is_expanded = alvara_id in st.session_state.alvara_expanded_cards
            
            card_class = "alvara-card expanded" if is_expanded else "alvara-card"
            
            with st.container():
                # Card principal (exatamente como benefícios)
                st.markdown(f"""
                <div class="{card_class}">
                    <div class="alvara-card-header">
                        <div>
                            <strong>📄 {safe_get_field_value_alvara(processo, 'Processo', 'Não informado')}</strong><br>
                            👤 {safe_get_field_value_alvara(processo, 'Parte', 'Não informado')}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Layout com botão expandir e informações
                col_expand, col_info = st.columns([1, 9])
                
                with col_expand:
                    expand_text = "▼ Fechar" if is_expanded else "▶ Abrir"
                    if st.button(expand_text, key=f"expand_alvara_{alvara_id}"):
                        if is_expanded:
                            st.session_state.alvara_expanded_cards.discard(alvara_id)
                        else:
                            st.session_state.alvara_expanded_cards.add(alvara_id)
                        st.rerun()
                
                with col_info:
                    # Informações resumidas (sempre visíveis)
                    st.markdown(f"""
                    <div class="alvara-info-grid">
                        <div class="info-item">
                            <div class="info-label">Número do Processo</div>
                            <div class="info-value">{safe_get_field_value_alvara(processo, 'Processo', 'Não informado')}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Status</div>
                            <div class="info-value">{status_atual}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Parte</div>
                            <div class="info-value">{safe_get_field_value_alvara(processo, 'Parte', 'Não informado')}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Valor</div>
                            <div class="info-value">{safe_get_field_value_alvara(processo, 'Pagamento', 'Não informado')}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Órgão</div>
                            <div class="info-value">{safe_get_field_value_alvara(processo, 'Órgão Judicial', 'Não informado')}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Conteúdo expandido (tabs)
                if is_expanded:
                    st.markdown("---")
                    st.markdown(f"### 📄 {safe_get_field_value_alvara(processo, 'Processo', 'Não informado')}")
                    
                    # Tabs
                    tab_info, tab_acoes, tab_historico = st.tabs(["📋 Informações", "⚙️ Ações", "📜 Histórico"])
                    
                    with tab_info:
                        render_tab_info_alvara(processo, alvara_id)
                    
                    with tab_acoes:
                        render_tab_acoes_alvara(df, processo, alvara_id, status_atual, perfil_usuario)
                    
                    with tab_historico:
                        render_tab_historico_alvara(processo, alvara_id)
                    
    else:
        st.info("Nenhum alvará encontrado com os filtros aplicados.")
        
    # Controles de paginação
    if total_registros > 0:
        st.markdown("---")
        col_nav1, col_nav2, col_nav3 = st.columns([3, 2, 3])

        with col_nav1:
            if st.session_state.current_page_alvaras > 1:
                if st.button("<< Primeira", key="btn_primeira_alvaras"):
                    st.session_state.current_page_alvaras = 1
                    st.rerun()
                if st.button("< Anterior", key="btn_anterior_alvaras"):
                    st.session_state.current_page_alvaras -= 1
                    st.rerun()

        with col_nav2:
            st.write(f"Página {st.session_state.current_page_alvaras} de {total_pages}")

        with col_nav3:
            if st.session_state.current_page_alvaras < total_pages:
                if st.button("Próxima >", key="btn_proxima_alvaras"):
                    st.session_state.current_page_alvaras += 1
                    st.rerun()
                if st.button("Última >>", key="btn_ultima_alvaras"):
                    st.session_state.current_page_alvaras = total_pages
                    st.rerun()