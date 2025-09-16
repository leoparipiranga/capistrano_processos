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
                dados.setdefault("varas_rpv", [])
                return dados
        
        # Fallback para arquivo local se existir
        elif os.path.exists(arquivo_local):
            with open(arquivo_local, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                dados.setdefault("orgaos_judiciais", [])
                dados.setdefault("assuntos_beneficios", [])
                dados.setdefault("assuntos_rpv", [])
                dados.setdefault("orgaos_rpv", [])
                dados.setdefault("varas_rpv", [])
                return dados
        
        # Se não existir nenhum arquivo, criar estrutura vazia
        dados_vazios = {
            "orgaos_judiciais": [],
            "assuntos_beneficios": [],
            "assuntos_rpv": [],
            "orgaos_rpv": [],
            "varas_rpv": []
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

def remover_orgao_judicial(orgao_para_remover):
    """Remove um órgão judicial da lista permanentemente"""
    if not orgao_para_remover or orgao_para_remover.strip() == "":
        return False
        
    # Normaliza o órgão
    import unicodedata
    orgao_normalizado = unicodedata.normalize('NFD', orgao_para_remover.upper().strip())
    orgao_normalizado = ''.join(c for c in orgao_normalizado if unicodedata.category(c) != 'Mn')
    
    # Carrega dados atuais
    dados = carregar_dados_autocomplete()
    
    # Remove se existir
    if orgao_normalizado in dados["orgaos_judiciais"]:
        dados["orgaos_judiciais"].remove(orgao_normalizado)
        
        # Salva no arquivo
        if salvar_dados_autocomplete(dados):
            return True
    
    return False

def remover_assunto_beneficio(assunto_para_remover):
    """Remove um assunto de benefício da lista permanentemente"""
    if not assunto_para_remover or assunto_para_remover.strip() == "":
        return False
        
    # Normaliza o assunto
    import unicodedata
    assunto_normalizado = unicodedata.normalize('NFD', assunto_para_remover.upper().strip())
    assunto_normalizado = ''.join(c for c in assunto_normalizado if unicodedata.category(c) != 'Mn')
    
    # Carrega dados atuais
    dados = carregar_dados_autocomplete()
    
    # Remove se existir
    if assunto_normalizado in dados["assuntos_beneficios"]:
        dados["assuntos_beneficios"].remove(assunto_normalizado)
        
        # Salva no arquivo
        if salvar_dados_autocomplete(dados):
            return True
    
    return False

def remover_assunto_rpv(assunto_para_remover):
    """Remove um assunto de RPV da lista permanentemente"""
    if not assunto_para_remover or assunto_para_remover.strip() == "":
        return False
        
    # Normaliza o assunto
    import unicodedata
    assunto_normalizado = unicodedata.normalize('NFD', assunto_para_remover.upper().strip())
    assunto_normalizado = ''.join(c for c in assunto_normalizado if unicodedata.category(c) != 'Mn')
    
    # Carrega dados atuais
    dados = carregar_dados_autocomplete()
    
    # Remove se existir
    if assunto_normalizado in dados["assuntos_rpv"]:
        dados["assuntos_rpv"].remove(assunto_normalizado)
        
        # Salva no arquivo
        if salvar_dados_autocomplete(dados):
            return True
    
    return False

def remover_orgao_rpv(orgao_para_remover):
    """Remove um órgão de RPV da lista permanentemente"""
    if not orgao_para_remover or orgao_para_remover.strip() == "":
        return False
        
    # Normaliza o órgão
    import unicodedata
    orgao_normalizado = unicodedata.normalize('NFD', orgao_para_remover.upper().strip())
    orgao_normalizado = ''.join(c for c in orgao_normalizado if unicodedata.category(c) != 'Mn')
    
    # Carrega dados atuais
    dados = carregar_dados_autocomplete()
    
    # Remove se existir
    if orgao_normalizado in dados["orgaos_rpv"]:
        dados["orgaos_rpv"].remove(orgao_normalizado)
        
        # Salva no arquivo
        if salvar_dados_autocomplete(dados):
            return True
    
    return False

def adicionar_vara_rpv(nova_vara):
    """Adiciona uma nova vara de RPV e salva permanentemente"""
    if not nova_vara or nova_vara.strip() == "":
        return False
        
    # Normaliza a vara
    import unicodedata
    vara_normalizada = unicodedata.normalize('NFD', nova_vara.upper().strip())
    vara_normalizada = ''.join(c for c in vara_normalizada if unicodedata.category(c) != 'Mn')
    
    # Carrega dados atuais
    dados = carregar_dados_autocomplete()
    
    # Adiciona se não existir
    if vara_normalizada not in dados["varas_rpv"]:
        dados["varas_rpv"].append(vara_normalizada)
        dados["varas_rpv"].sort()  # Mantém ordenado
        
        # Salva no GitHub
        if salvar_dados_autocomplete(dados):
            return True
    
    return False

def remover_vara_rpv(vara_para_remover):
    """Remove uma vara de RPV da lista permanentemente"""
    if not vara_para_remover or vara_para_remover.strip() == "":
        return False
        
    # Normaliza a vara
    import unicodedata
    vara_normalizada = unicodedata.normalize('NFD', vara_para_remover.upper().strip())
    vara_normalizada = ''.join(c for c in vara_normalizada if unicodedata.category(c) != 'Mn')
    
    # Carrega dados atuais
    dados = carregar_dados_autocomplete()
    
    # Remove se existir
    if vara_normalizada in dados["varas_rpv"]:
        dados["varas_rpv"].remove(vara_normalizada)
        
        # Salva no arquivo
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
        "TRIBUNAL REGIONAL FEDERAL DA 5.ª REGIÃO (TRF5)",
    ]
    
    # Dados salvos
    dados_salvos = carregar_dados_autocomplete()
    orgaos_salvos = dados_salvos.get("orgaos_judiciais", [])
    
    # Combinar e ordenar
    return sorted(list(set(ORGAOS_JUDICIAIS_BASE + orgaos_salvos)))

def obter_assuntos_beneficios_completo():
    """Obtém lista completa de assuntos de benefícios (padrão + salvos)"""
    # Dados padrão (incluindo tipos de processo)
    ASSUNTOS_BENEFICIOS_BASE = [
        # Tipos de processo principais
        "LOAS",
        "LOAS DEFICIENTE",
        "LOAS IDOSO",
        "APOSENTADORIA POR INVALIDEZ",
        "APOSENTADORIA POR IDADE",
        "AUXÍLIO DOENÇA",
        "AUXÍLIO ACIDENTE",
        "PENSÃO POR MORTE",
        "SALÁRIO MATERNIDADE",
        "OUTROS",
        # Assuntos específicos adicionais
        "AUXÍLIO-DOENÇA",
        "APOSENTADORIA ESPECIAL",
        "BENEFÍCIO DE PRESTAÇÃO CONTINUADA (BPC)",
        "REVISÃO DE BENEFÍCIO",
        "DIFERENÇAS DE APOSENTADORIA",
        "ABONO ANUAL (13º SALÁRIO)",
        "AUXÍLIO-ALIMENTAÇÃO",
        "LICENÇA-PRÊMIO"
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
        "TRIBUNAL REGIONAL FEDERAL 5ª REGIÃO (TRF5)",
    ]
    
    # Dados salvos
    dados_salvos = carregar_dados_autocomplete()
    orgaos_salvos = dados_salvos.get("orgaos_rpv", [])
    
    # Combinar e ordenar
    return sorted(list(set(ORGAOS_RPV_BASE + orgaos_salvos)))

def obter_varas_rpv_completo():
    """Obtém lista completa de varas de RPV (padrão + salvos)"""
    # Dados padrão
    VARAS_RPV_BASE = [
        "1ª VARA CÍVEL",
    ]
    
    # Dados salvos
    dados_salvos = carregar_dados_autocomplete()
    varas_salvas = dados_salvos.get("varas_rpv", [])
    
    # Combinar e ordenar
    return sorted(list(set(VARAS_RPV_BASE + varas_salvas)))

def obter_assuntos_rpv():
    """Alias para manter compatibilidade - obtém lista de assuntos RPV"""
    return obter_assuntos_rpv_completo()

def obter_orgaos_rpv():
    """Alias para manter compatibilidade - obtém lista de órgãos RPV"""
    return obter_orgaos_rpv_completo()

def obter_varas_rpv():
    """Alias para manter compatibilidade - obtém lista de varas RPV"""
    return obter_varas_rpv_completo()

def normalizar_assunto_rpv(assunto):
    """Normaliza assunto de RPV"""
    if not assunto:
        return ""
    import unicodedata
    normalizado = unicodedata.normalize('NFD', assunto.upper().strip())
    return ''.join(c for c in normalizado if unicodedata.category(c) != 'Mn')

def normalizar_orgao_rpv(orgao):
    """Normaliza órgão de RPV"""
    if not orgao:
        return ""
    import unicodedata
    normalizado = unicodedata.normalize('NFD', orgao.upper().strip())
    return ''.join(c for c in normalizado if unicodedata.category(c) != 'Mn')

def normalizar_vara_rpv(vara):
    """Normaliza vara de RPV"""
    if not vara:
        return ""
    import unicodedata
    normalizado = unicodedata.normalize('NFD', vara.upper().strip())
    return ''.join(c for c in normalizado if unicodedata.category(c) != 'Mn')

def campo_orgao_judicial(label="🏛️ Órgão Judicial:", key_prefix="orgao"):
    """Campo selectbox + campo de texto para órgão judicial - Aparece imediatamente"""
    
    # Obter lista completa (padrão + salvos)
    orgaos_existentes = obter_orgaos_judiciais_completo()
    
    # Adicionar opção especial
    opcoes = orgaos_existentes + ["➕ Adicionar novo órgão"]
    
    orgao_selecionado = st.selectbox(
        label,
        opcoes,
        key=f"select_{key_prefix}",
        help="Selecione um órgão existente ou '➕ Adicionar novo órgão' para criar um novo"
    )
    
    # Se "Adicionar novo" foi selecionado, mostra campo de texto SEMPRE
    if orgao_selecionado == "➕ Adicionar novo órgão":
        novo_orgao = st.text_input(
            "📝 Digite o nome do novo órgão:",
            key=f"input_novo_{key_prefix}",
            placeholder="Ex: TRF 5ª REGIÃO",
            help="Este órgão será adicionado automaticamente ao confirmar o formulário"
        )
        
        if novo_orgao and novo_orgao.strip():
            st.info(f"✏️ Novo órgão será adicionado: **{novo_orgao.strip()}**")
            return novo_orgao.strip()
        else:
            if novo_orgao == "":  # Campo vazio (não foi digitado ainda)
                return None
            else:  # Campo foi tocado mas está vazio
                st.warning("⚠️ Digite o nome do novo órgão antes de continuar")
                return None
    else:
        return orgao_selecionado

def campo_assunto_beneficio(label="📄 Assunto:", key_prefix="assunto_ben"):
    """Campo selectbox + campo de texto para assunto de benefício - Aparece imediatamente"""
    
    # Obter lista completa (padrão + salvos)
    assuntos_existentes = obter_assuntos_beneficios_completo()
    
    # Adicionar opção especial
    opcoes = assuntos_existentes + ["➕ Adicionar novo assunto"]
    
    assunto_selecionado = st.selectbox(
        label,
        opcoes,
        key=f"select_{key_prefix}",
        help="Selecione um assunto existente ou '➕ Adicionar novo assunto' para criar um novo"
    )
    
    # Se "Adicionar novo" foi selecionado, mostra campo de texto SEMPRE
    if assunto_selecionado == "➕ Adicionar novo assunto":
        novo_assunto = st.text_input(
            "📝 Digite o nome do novo assunto:",
            key=f"input_novo_{key_prefix}",
            placeholder="Ex: AUXÍLIO EMERGENCIAL",
            help="Este assunto será adicionado automaticamente ao confirmar o formulário"
        )
        
        if novo_assunto and novo_assunto.strip():
            st.info(f"✏️ Novo assunto será adicionado: **{novo_assunto.strip()}**")
            return novo_assunto.strip()
        else:
            if novo_assunto == "":  # Campo vazio (não foi digitado ainda)
                return None
            else:  # Campo foi tocado mas está vazio
                st.warning("⚠️ Digite o nome do novo assunto antes de continuar")
                return None
    else:
        return assunto_selecionado

def campo_assunto_rpv(label="📄 Assunto:", key_prefix="assunto_rpv"):
    """Campo selectbox + campo de texto para assunto de RPV - Aparece imediatamente"""
    
    # Obter lista completa (padrão + salvos)
    assuntos_existentes = obter_assuntos_rpv_completo()
    
    # Adicionar opção especial
    opcoes = assuntos_existentes + ["➕ Adicionar novo assunto"]
    
    assunto_selecionado = st.selectbox(
        label,
        opcoes,
        key=f"select_{key_prefix}",
        help="Selecione um assunto existente ou '➕ Adicionar novo assunto' para criar um novo"
    )
    
    # Se "Adicionar novo" foi selecionado, mostra campo de texto SEMPRE
    if assunto_selecionado == "➕ Adicionar novo assunto":
        novo_assunto = st.text_input(
            "📝 Digite o nome do novo assunto:",
            key=f"input_novo_{key_prefix}",
            placeholder="Ex: PRECATÓRIO FEDERAL",
            help="Este assunto será adicionado automaticamente ao confirmar o formulário"
        )
        
        if novo_assunto and novo_assunto.strip():
            st.info(f"✏️ Novo assunto será adicionado: **{novo_assunto.strip()}**")
            return novo_assunto.strip()
        else:
            if novo_assunto == "":  # Campo vazio (não foi digitado ainda)
                return None
            else:  # Campo foi tocado mas está vazio
                st.warning("⚠️ Digite o nome do novo assunto antes de continuar")
                return None
    else:
        return assunto_selecionado

def campo_orgao_rpv(label="🏛️ Órgão Judicial:", key_prefix="orgao_rpv"):
    """Campo selectbox + campo de texto para órgão de RPV - Aparece imediatamente"""
    
    # Obter lista completa (padrão + salvos)
    orgaos_existentes = obter_orgaos_rpv_completo()
    
    # Adicionar opção especial
    opcoes = orgaos_existentes + ["➕ Adicionar novo órgão"]
    
    orgao_selecionado = st.selectbox(
        label,
        opcoes,
        key=f"select_{key_prefix}",
        help="Selecione um órgão existente ou '➕ Adicionar novo órgão' para criar um novo"
    )
    
    # Se "Adicionar novo" foi selecionado, mostra campo de texto SEMPRE
    if orgao_selecionado == "➕ Adicionar novo órgão":
        novo_orgao = st.text_input(
            "📝 Digite o nome do novo órgão:",
            key=f"input_novo_{key_prefix}",
            placeholder="Ex: TRF 2ª REGIÃO",
            help="Este órgão será adicionado automaticamente ao confirmar o formulário"
        )
        
        if novo_orgao and novo_orgao.strip():
            st.info(f"✏️ Novo órgão será adicionado: **{novo_orgao.strip()}**")
            return novo_orgao.strip()
        else:
            if novo_orgao == "":  # Campo vazio (não foi digitado ainda)
                return None
            else:  # Campo foi tocado mas está vazio
                st.warning("⚠️ Digite o nome do novo órgão antes de continuar")
                return None
    else:
        return orgao_selecionado

def campo_vara_rpv(label="⚖️ Vara:", key_prefix="vara_rpv"):
    """Campo selectbox + campo de texto para vara de RPV - Aparece imediatamente"""
    
    # Obter lista completa (padrão + salvos)
    varas_existentes = obter_varas_rpv_completo()
    
    # Adicionar opção especial
    opcoes = varas_existentes + ["➕ Adicionar nova vara"]
    
    vara_selecionada = st.selectbox(
        label,
        opcoes,
        key=f"select_{key_prefix}",
        help="Selecione uma vara existente ou '➕ Adicionar nova vara' para criar uma nova"
    )
    
    # Se "Adicionar nova" foi selecionado, mostra campo de texto SEMPRE
    if vara_selecionada == "➕ Adicionar nova vara":
        nova_vara = st.text_input(
            "📝 Digite o nome da nova vara:",
            key=f"input_nova_{key_prefix}",
            placeholder="Ex: 6ª VARA CÍVEL",
            help="Esta vara será adicionada automaticamente ao confirmar o formulário"
        )
        
        if nova_vara and nova_vara.strip():
            st.info(f"✏️ Nova vara será adicionada: **{nova_vara.strip()}**")
            return nova_vara.strip()
        else:
            if nova_vara == "":  # Campo vazio (não foi digitado ainda)
                return None
            else:  # Campo foi tocado mas está vazio
                st.warning("⚠️ Digite o nome da nova vara antes de continuar")
                return None
    else:
        return vara_selecionada