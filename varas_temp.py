# =====================================
# SISTEMA DE VARAS PARA RPV
# =====================================

def obter_varas_rpv():
    """Obtém lista de varas salvas para RPV"""
    dados = carregar_dados_autocomplete()
    return dados.get("varas_rpv", [])

def obter_varas_rpv_padrao():
    """Lista de varas padrão para RPV"""
    return [
        "1ª Vara Federal",
        "2ª Vara Federal", 
        "3ª Vara Federal",
        "4ª Vara Federal",
        "5ª Vara Federal",
        "6ª Vara Federal",
        "7ª Vara Federal",
        "8ª Vara Federal",
        "9ª Vara Federal",
        "10ª Vara Federal",
        "11ª Vara Federal",
        "12ª Vara Federal",
        "13ª Vara Federal",
        "14ª Vara Federal",
        "15ª Vara Federal",
        "16ª Vara Federal",
        "17ª Vara Federal",
        "18ª Vara Federal",
        "19ª Vara Federal",
        "20ª Vara Federal",
        "Vara Federal Especializada",
        "Vara Federal de Execução Fiscal",
        "Juizado Especial Federal",
        "1ª Vara da Fazenda Pública",
        "2ª Vara da Fazenda Pública",
        "3ª Vara da Fazenda Pública",
        "4ª Vara da Fazenda Pública",
        "5ª Vara da Fazenda Pública",
        "Vara Especializada da Fazenda Pública",
        "Vara de Precatórios"
    ]

def obter_varas_rpv_completo():
    """Obtém lista completa de varas (padrão + salvas)"""
    varas_padrao = obter_varas_rpv_padrao()
    varas_salvas = obter_varas_rpv()
    
    # Combinar e remover duplicatas, mantendo ordem
    varas_completas = []
    for vara in varas_padrao + varas_salvas:
        if vara not in varas_completas:
            varas_completas.append(vara)
    
    return sorted(varas_completas)

def normalizar_vara_rpv(vara):
    """Normaliza entrada de vara para RPV"""
    if not vara:
        return ""
    return vara.strip().title()

def adicionar_vara_rpv(nova_vara):
    """Adiciona nova vara à lista de RPV"""
    try:
        dados = carregar_dados_autocomplete()
        
        # Normalizar entrada
        nova_vara_norm = normalizar_vara_rpv(nova_vara)
        
        if not nova_vara_norm:
            return False
        
        # Verificar se já existe
        varas_existentes = dados.get("varas_rpv", [])
        if nova_vara_norm not in varas_existentes:
            varas_existentes.append(nova_vara_norm)
            dados["varas_rpv"] = sorted(varas_existentes)
            
            # Salvar alterações
            return salvar_dados_autocomplete(dados)
        
        return True  # Já existe
        
    except Exception as e:
        print(f"Erro ao adicionar vara RPV: {e}")
        return False

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
    
    # Se "Adicionar novo" foi selecionado, mostra campo de texto SEMPRE
    if vara_selecionada == "➕ Adicionar nova vara":
        nova_vara = st.text_input(
            "📝 Digite o nome da nova vara:",
            key=f"input_novo_{key_prefix}",
            placeholder="Ex: 21ª Vara Federal",
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
