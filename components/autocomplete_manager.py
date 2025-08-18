"""
Módulo para gerenciamento permanente de dados de autocomplete
Salva e carrega entradas personalizadas de assuntos e órgãos no GitHub
"""

import json
import streamlit as st

# Arquivo para armazenar dados de autocomplete
ARQUIVO_AUTOCOMPLETE = "autocomplete_data.json"

def carregar_dados_autocomplete():
    """Carrega dados de autocomplete do arquivo JSON do repositório"""
    try:
        import os
        arquivo_repo = "autocomplete_data.json"
        arquivo_local = "autocomplete_data_local.json"
        
        # Primeiro tentar carregar do arquivo do repositório
        if os.path.exists(arquivo_repo):
            with open(arquivo_repo, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                # Garantir que todas as chaves existam
                dados.setdefault("orgaos_judiciais", [])
                dados.setdefault("assuntos_beneficios", [])
                dados.setdefault("assuntos_rpv", [])
                dados.setdefault("orgaos_rpv", [])
                return dados
        
        # Fallback para arquivo local se existir
        elif os.path.exists(arquivo_local):
            with open(arquivo_local, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                dados.setdefault("orgaos_judiciais", [])
                dados.setdefault("assuntos_beneficios", [])
                dados.setdefault("assuntos_rpv", [])
                dados.setdefault("orgaos_rpv", [])
                return dados
        
        # Se não existir nenhum arquivo, criar estrutura vazia
        dados_vazios = {
            "orgaos_judiciais": [],
            "assuntos_beneficios": [],
            "assuntos_rpv": [],
            "orgaos_rpv": []
        }
        
        # Salvar arquivo do repositório para próximas sessões
        with open(arquivo_repo, 'w', encoding='utf-8') as f:
            json.dump(dados_vazios, f, indent=2, ensure_ascii=False)
            
        return dados_vazios
            
    except Exception as e:
        # Em caso de erro, retornar estrutura vazia
        return {
            "orgaos_judiciais": [],
            "assuntos_beneficios": [],
            "assuntos_rpv": [],
            "orgaos_rpv": []
        }

def salvar_dados_autocomplete(dados):
    """Salva dados de autocomplete no arquivo JSON do repositório"""
    try:
        import os
        arquivo_repo = "autocomplete_data.json"
        
        # Salvar no arquivo do repositório (será commitado)
        with open(arquivo_repo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
        
        return True
            
    except Exception as e:
        return False

def adicionar_orgao_judicial(novo_orgao):
    """Adiciona um novo órgão judicial e salva permanentemente"""
    if not novo_orgao or novo_orgao.strip() == "":
        return False
        
    # Normaliza o órgão
    import unicodedata
    orgao_normalizado = unicodedata.normalize('NFD', novo_orgao.upper().strip())
    orgao_normalizado = ''.join(c for c in orgao_normalizado if unicodedata.category(c) != 'Mn')
    
    # Carrega dados atuais
    dados = carregar_dados_autocomplete()
    
    # Adiciona se não existir
    if orgao_normalizado not in dados["orgaos_judiciais"]:
        dados["orgaos_judiciais"].append(orgao_normalizado)
        dados["orgaos_judiciais"].sort()  # Mantém ordenado
        
        # Salva no GitHub
        if salvar_dados_autocomplete(dados):
            # Também adiciona na sessão atual
            if "orgaos_judiciais_customizados" not in st.session_state:
                st.session_state.orgaos_judiciais_customizados = []
            if orgao_normalizado not in st.session_state.orgaos_judiciais_customizados:
                st.session_state.orgaos_judiciais_customizados.append(orgao_normalizado)
            return True
    
    return False

def adicionar_assunto_beneficio(novo_assunto):
    """Adiciona um novo assunto de benefício e salva permanentemente"""
    if not novo_assunto or novo_assunto.strip() == "":
        return False
        
    # Normaliza o assunto
    import unicodedata
    assunto_normalizado = unicodedata.normalize('NFD', novo_assunto.upper().strip())
    assunto_normalizado = ''.join(c for c in assunto_normalizado if unicodedata.category(c) != 'Mn')
    
    # Carrega dados atuais
    dados = carregar_dados_autocomplete()
    
    # Adiciona se não existir
    if assunto_normalizado not in dados["assuntos_beneficios"]:
        dados["assuntos_beneficios"].append(assunto_normalizado)
        dados["assuntos_beneficios"].sort()  # Mantém ordenado
        
        # Salva no GitHub
        if salvar_dados_autocomplete(dados):
            # Também adiciona na sessão atual
            if "assuntos_beneficios_customizados" not in st.session_state:
                st.session_state.assuntos_beneficios_customizados = []
            if assunto_normalizado not in st.session_state.assuntos_beneficios_customizados:
                st.session_state.assuntos_beneficios_customizados.append(assunto_normalizado)
            return True
    
    return False

def adicionar_assunto_rpv(novo_assunto):
    """Adiciona um novo assunto de RPV e salva permanentemente"""
    if not novo_assunto or novo_assunto.strip() == "":
        return False
        
    # Normaliza o assunto
    import unicodedata
    assunto_normalizado = unicodedata.normalize('NFD', novo_assunto.upper().strip())
    assunto_normalizado = ''.join(c for c in assunto_normalizado if unicodedata.category(c) != 'Mn')
    
    # Carrega dados atuais
    dados = carregar_dados_autocomplete()
    
    # Adiciona se não existir
    if assunto_normalizado not in dados["assuntos_rpv"]:
        dados["assuntos_rpv"].append(assunto_normalizado)
        dados["assuntos_rpv"].sort()  # Mantém ordenado
        
        # Salva no GitHub
        if salvar_dados_autocomplete(dados):
            # Também adiciona na sessão atual (se existir no RPV)
            return True
    
    return False

def adicionar_orgao_rpv(novo_orgao):
    """Adiciona um novo órgão de RPV e salva permanentemente"""
    if not novo_orgao or novo_orgao.strip() == "":
        return False
        
    # Normaliza o órgão
    import unicodedata
    orgao_normalizado = unicodedata.normalize('NFD', novo_orgao.upper().strip())
    orgao_normalizado = ''.join(c for c in orgao_normalizado if unicodedata.category(c) != 'Mn')
    
    # Carrega dados atuais
    dados = carregar_dados_autocomplete()
    
    # Adiciona se não existir
    if orgao_normalizado not in dados["orgaos_rpv"]:
        dados["orgaos_rpv"].append(orgao_normalizado)
        dados["orgaos_rpv"].sort()  # Mantém ordenado
        
        # Salva no GitHub
        if salvar_dados_autocomplete(dados):
            return True
    
    return False

def inicializar_autocomplete_session():
    """Inicializa os dados de autocomplete na sessão carregando do arquivo persistente"""
    dados = carregar_dados_autocomplete()
    
    # Inicializa session_state com dados persistidos
    if not hasattr(st.session_state, 'orgaos_judiciais_customizados') or st.session_state.orgaos_judiciais_customizados is None:
        st.session_state.orgaos_judiciais_customizados = dados.get("orgaos_judiciais", []).copy()
    else:
        # Merge com dados salvos (sem duplicatas)
        existentes = set(st.session_state.orgaos_judiciais_customizados)
        salvos = set(dados.get("orgaos_judiciais", []))
        st.session_state.orgaos_judiciais_customizados = sorted(list(existentes.union(salvos)))
    
    if not hasattr(st.session_state, 'assuntos_beneficios_customizados') or st.session_state.assuntos_beneficios_customizados is None:
        st.session_state.assuntos_beneficios_customizados = dados.get("assuntos_beneficios", []).copy()
    else:
        # Merge com dados salvos (sem duplicatas)
        existentes = set(st.session_state.assuntos_beneficios_customizados)
        salvos = set(dados.get("assuntos_beneficios", []))
        st.session_state.assuntos_beneficios_customizados = sorted(list(existentes.union(salvos)))
    
    # Para RPV, inicializar os assuntos também
    if not hasattr(st.session_state, 'assuntos_rpv_customizados') or st.session_state.assuntos_rpv_customizados is None:
        st.session_state.assuntos_rpv_customizados = dados.get("assuntos_rpv", []).copy()
    else:
        # Merge com dados salvos (sem duplicatas)  
        existentes = set(st.session_state.assuntos_rpv_customizados)
        salvos = set(dados.get("assuntos_rpv", []))
        st.session_state.assuntos_rpv_customizados = sorted(list(existentes.union(salvos)))

# ========================================
# COMPONENTES DE INTERFACE - SOLUÇÃO 1
# ========================================

def obter_orgaos_judiciais_completo():
    """Obtém lista completa de órgãos judiciais (padrão + salvos)"""
    # Dados padrão
    ORGAOS_JUDICIAIS_BASE = [
        "COMARCA DE BELO HORIZONTE",
        "COMARCA DE CONTAGEM", 
        "COMARCA DE BETIM",
        "COMARCA DE RIBEIRÃO DAS NEVES",
        "TRIBUNAL DE JUSTIÇA DE MINAS GERAIS (TJMG)",
        "SUPERIOR TRIBUNAL DE JUSTIÇA (STJ)",
        "SUPREMO TRIBUNAL FEDERAL (STF)",
        "TRIBUNAL REGIONAL FEDERAL 1ª REGIÃO (TRF1)",
        "TRIBUNAL REGIONAL DO TRABALHO 3ª REGIÃO (TRT3)"
    ]
    
    # Dados salvos
    dados_salvos = carregar_dados_autocomplete()
    orgaos_salvos = dados_salvos.get("orgaos_judiciais", [])
    
    # Combinar e ordenar
    return sorted(list(set(ORGAOS_JUDICIAIS_BASE + orgaos_salvos)))

def obter_assuntos_beneficios_completo():
    """Obtém lista completa de assuntos de benefícios (padrão + salvos)"""
    # Dados padrão
    ASSUNTOS_BENEFICIOS_BASE = [
        "AUXÍLIO-DOENÇA",
        "APOSENTADORIA POR IDADE",
        "APOSENTADORIA POR INVALIDEZ", 
        "APOSENTADORIA ESPECIAL",
        "AUXÍLIO-ACIDENTE",
        "PENSÃO POR MORTE",
        "SALÁRIO-MATERNIDADE",
        "BENEFÍCIO DE PRESTAÇÃO CONTINUADA (BPC)",
        "REVISÃO DE BENEFÍCIO",
        "DIFERENÇAS DE APOSENTADORIA"
    ]
    
    # Dados salvos
    dados_salvos = carregar_dados_autocomplete()
    assuntos_salvos = dados_salvos.get("assuntos_beneficios", [])
    
    # Combinar e ordenar
    return sorted(list(set(ASSUNTOS_BENEFICIOS_BASE + assuntos_salvos)))

def obter_assuntos_rpv_completo():
    """Obtém lista completa de assuntos de RPV (padrão + salvos)"""
    # Dados padrão
    ASSUNTOS_RPV_BASE = [
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
        "ABONO ANUAL (13º SALARIO)",
        "AUXILIO-ALIMENTACAO",
        "ADICIONAL DE INSALUBRIDADE",
        "ADICIONAL NOTURNO",
        "HORAS EXTRAS",
        "INDENIZACAO POR DANOS MORAIS",
        "REINTEGRAÇÃO DE SERVIDOR",
        "DIFERENÇAS SALARIAIS",
        "LICENÇA-PRÊMIO"
    ]
    
    # Dados salvos
    dados_salvos = carregar_dados_autocomplete()
    assuntos_salvos = dados_salvos.get("assuntos_rpv", [])
    
    # Combinar e ordenar
    return sorted(list(set(ASSUNTOS_RPV_BASE + assuntos_salvos)))

def obter_orgaos_rpv_completo():
    """Obtém lista completa de órgãos de RPV (padrão + salvos)"""
    # Dados padrão
    ORGAOS_RPV_BASE = [
        "TRIBUNAL DE JUSTIÇA DE MINAS GERAIS (TJMG)",
        "TRIBUNAL REGIONAL FEDERAL 1ª REGIÃO (TRF1)",
        "TRIBUNAL REGIONAL DO TRABALHO 3ª REGIÃO (TRT3)",
        "SUPERIOR TRIBUNAL DE JUSTIÇA (STJ)",
        "SUPREMO TRIBUNAL FEDERAL (STF)",
        "PREFEITURA DE BELO HORIZONTE",
        "GOVERNO DO ESTADO DE MINAS GERAIS",
        "UNIÃO FEDERAL",
        "INSS - INSTITUTO NACIONAL DO SEGURO SOCIAL"
    ]
    
    # Dados salvos
    dados_salvos = carregar_dados_autocomplete()
    orgaos_salvos = dados_salvos.get("orgaos_rpv", [])
    
    # Combinar e ordenar
    return sorted(list(set(ORGAOS_RPV_BASE + orgaos_salvos)))

def campo_orgao_judicial(label="🏛️ Órgão Judicial:", key_prefix="orgao"):
    """Campo selectbox + botão para órgão judicial com opção de adicionar novo"""
    
    # Obter lista completa (padrão + salvos)
    orgaos_existentes = obter_orgaos_judiciais_completo()
    
    # Adicionar opção especial
    opcoes = orgaos_existentes + ["➕ Adicionar novo órgão"]
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        orgao_selecionado = st.selectbox(
            label,
            opcoes,
            key=f"select_{key_prefix}"
        )
    
    with col2:
        # Botão só aparece se "Adicionar novo" foi selecionado
        if orgao_selecionado == "➕ Adicionar novo órgão":
            if st.button("➕ Novo", key=f"btn_novo_{key_prefix}"):
                st.session_state[f"show_modal_{key_prefix}"] = True
    
    # Modal para adicionar novo
    modal_key = f"show_modal_{key_prefix}"
    if st.session_state.get(modal_key, False):
        st.markdown("---")
        st.markdown("**✏️ Adicionar Novo Órgão Judicial:**")
        
        novo_orgao = st.text_input(
            "Digite o nome do novo órgão:", 
            key=f"input_novo_{key_prefix}",
            placeholder="Ex: TRF 5ª REGIÃO"
        )
        
        col_modal1, col_modal2 = st.columns(2)
        with col_modal1:
            if st.button("✅ Salvar", key=f"salvar_{key_prefix}"):
                if novo_orgao.strip():
                    if adicionar_orgao_judicial(novo_orgao.strip()):
                        st.session_state[modal_key] = False
                        st.success(f"✅ '{novo_orgao}' adicionado com sucesso!")
                        # Limpar o input
                        if f"input_novo_{key_prefix}" in st.session_state:
                            del st.session_state[f"input_novo_{key_prefix}"]
                        st.rerun()
                    else:
                        st.error("❌ Erro ao adicionar órgão ou órgão já existe")
                else:
                    st.warning("⚠️ Digite um nome válido para o órgão")
        
        with col_modal2:
            if st.button("❌ Cancelar", key=f"cancelar_{key_prefix}"):
                st.session_state[modal_key] = False
                # Limpar o input
                if f"input_novo_{key_prefix}" in st.session_state:
                    del st.session_state[f"input_novo_{key_prefix}"]
                st.rerun()
        
        st.markdown("---")
    
    # Retorna o valor selecionado (ou vazio se for "adicionar novo")
    if orgao_selecionado == "➕ Adicionar novo órgão":
        return ""
    return orgao_selecionado

def campo_assunto_beneficio(label="📄 Assunto:", key_prefix="assunto_ben"):
    """Campo selectbox + botão para assunto de benefício com opção de adicionar novo"""
    
    # Obter lista completa (padrão + salvos)
    assuntos_existentes = obter_assuntos_beneficios_completo()
    
    # Adicionar opção especial
    opcoes = assuntos_existentes + ["➕ Adicionar novo assunto"]
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        assunto_selecionado = st.selectbox(
            label,
            opcoes,
            key=f"select_{key_prefix}"
        )
    
    with col2:
        # Botão só aparece se "Adicionar novo" foi selecionado
        if assunto_selecionado == "➕ Adicionar novo assunto":
            if st.button("➕ Novo", key=f"btn_novo_{key_prefix}"):
                st.session_state[f"show_modal_{key_prefix}"] = True
    
    # Modal para adicionar novo
    modal_key = f"show_modal_{key_prefix}"
    if st.session_state.get(modal_key, False):
        st.markdown("---")
        st.markdown("**✏️ Adicionar Novo Assunto de Benefício:**")
        
        novo_assunto = st.text_input(
            "Digite o nome do novo assunto:", 
            key=f"input_novo_{key_prefix}",
            placeholder="Ex: AUXÍLIO EMERGENCIAL"
        )
        
        col_modal1, col_modal2 = st.columns(2)
        with col_modal1:
            if st.button("✅ Salvar", key=f"salvar_{key_prefix}"):
                if novo_assunto.strip():
                    if adicionar_assunto_beneficio(novo_assunto.strip()):
                        st.session_state[modal_key] = False
                        st.success(f"✅ '{novo_assunto}' adicionado com sucesso!")
                        # Limpar o input
                        if f"input_novo_{key_prefix}" in st.session_state:
                            del st.session_state[f"input_novo_{key_prefix}"]
                        st.rerun()
                    else:
                        st.error("❌ Erro ao adicionar assunto ou assunto já existe")
                else:
                    st.warning("⚠️ Digite um nome válido para o assunto")
        
        with col_modal2:
            if st.button("❌ Cancelar", key=f"cancelar_{key_prefix}"):
                st.session_state[modal_key] = False
                # Limpar o input
                if f"input_novo_{key_prefix}" in st.session_state:
                    del st.session_state[f"input_novo_{key_prefix}"]
                st.rerun()
        
        st.markdown("---")
    
    # Retorna o valor selecionado (ou vazio se for "adicionar novo")
    if assunto_selecionado == "➕ Adicionar novo assunto":
        return ""
    return assunto_selecionado

def campo_assunto_rpv(label="📄 Assunto:", key_prefix="assunto_rpv"):
    """Campo selectbox + botão para assunto de RPV com opção de adicionar novo"""
    
    # Obter lista completa (padrão + salvos)
    assuntos_existentes = obter_assuntos_rpv_completo()
    
    # Adicionar opção especial
    opcoes = assuntos_existentes + ["➕ Adicionar novo assunto"]
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        assunto_selecionado = st.selectbox(
            label,
            opcoes,
            key=f"select_{key_prefix}"
        )
    
    with col2:
        # Botão só aparece se "Adicionar novo" foi selecionado
        if assunto_selecionado == "➕ Adicionar novo assunto":
            if st.button("➕ Novo", key=f"btn_novo_{key_prefix}"):
                st.session_state[f"show_modal_{key_prefix}"] = True
    
    # Modal para adicionar novo
    modal_key = f"show_modal_{key_prefix}"
    if st.session_state.get(modal_key, False):
        st.markdown("---")
        st.markdown("**✏️ Adicionar Novo Assunto de RPV:**")
        
        novo_assunto = st.text_input(
            "Digite o nome do novo assunto:", 
            key=f"input_novo_{key_prefix}",
            placeholder="Ex: PRECATÓRIO FEDERAL"
        )
        
        col_modal1, col_modal2 = st.columns(2)
        with col_modal1:
            if st.button("✅ Salvar", key=f"salvar_{key_prefix}"):
                if novo_assunto.strip():
                    if adicionar_assunto_rpv(novo_assunto.strip()):
                        st.session_state[modal_key] = False
                        st.success(f"✅ '{novo_assunto}' adicionado com sucesso!")
                        # Limpar o input
                        if f"input_novo_{key_prefix}" in st.session_state:
                            del st.session_state[f"input_novo_{key_prefix}"]
                        st.rerun()
                    else:
                        st.error("❌ Erro ao adicionar assunto ou assunto já existe")
                else:
                    st.warning("⚠️ Digite um nome válido para o assunto")
        
        with col_modal2:
            if st.button("❌ Cancelar", key=f"cancelar_{key_prefix}"):
                st.session_state[modal_key] = False
                # Limpar o input
                if f"input_novo_{key_prefix}" in st.session_state:
                    del st.session_state[f"input_novo_{key_prefix}"]
                st.rerun()
        
        st.markdown("---")
    
    # Retorna o valor selecionado (ou vazio se for "adicionar novo")
    if assunto_selecionado == "➕ Adicionar novo assunto":
        return ""
    return assunto_selecionado

def campo_orgao_rpv(label="🏛️ Órgão Judicial:", key_prefix="orgao_rpv"):
    """Campo selectbox + botão para órgão de RPV com opção de adicionar novo"""
    
    # Obter lista completa (padrão + salvos)
    orgaos_existentes = obter_orgaos_rpv_completo()
    
    # Adicionar opção especial
    opcoes = orgaos_existentes + ["➕ Adicionar novo órgão"]
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        orgao_selecionado = st.selectbox(
            label,
            opcoes,
            key=f"select_{key_prefix}"
        )
    
    with col2:
        # Botão só aparece se "Adicionar novo" foi selecionado
        if orgao_selecionado == "➕ Adicionar novo órgão":
            if st.button("➕ Novo", key=f"btn_novo_{key_prefix}"):
                st.session_state[f"show_modal_{key_prefix}"] = True
    
    # Modal para adicionar novo
    modal_key = f"show_modal_{key_prefix}"
    if st.session_state.get(modal_key, False):
        st.markdown("---")
        st.markdown("**✏️ Adicionar Novo Órgão de RPV:**")
        
        novo_orgao = st.text_input(
            "Digite o nome do novo órgão:", 
            key=f"input_novo_{key_prefix}",
            placeholder="Ex: TRF 2ª REGIÃO"
        )
        
        col_modal1, col_modal2 = st.columns(2)
        with col_modal1:
            if st.button("✅ Salvar", key=f"salvar_{key_prefix}"):
                if novo_orgao.strip():
                    if adicionar_orgao_rpv(novo_orgao.strip()):
                        st.session_state[modal_key] = False
                        st.success(f"✅ '{novo_orgao}' adicionado com sucesso!")
                        # Limpar o input
                        if f"input_novo_{key_prefix}" in st.session_state:
                            del st.session_state[f"input_novo_{key_prefix}"]
                        st.rerun()
                    else:
                        st.error("❌ Erro ao adicionar órgão ou órgão já existe")
                else:
                    st.warning("⚠️ Digite um nome válido para o órgão")
        
        with col_modal2:
            if st.button("❌ Cancelar", key=f"cancelar_{key_prefix}"):
                st.session_state[modal_key] = False
                # Limpar o input
                if f"input_novo_{key_prefix}" in st.session_state:
                    del st.session_state[f"input_novo_{key_prefix}"]
                st.rerun()
        
        st.markdown("---")
    
    # Retorna o valor selecionado (ou vazio se for "adicionar novo")
    if orgao_selecionado == "➕ Adicionar novo órgão":
        return ""
    return orgao_selecionado
