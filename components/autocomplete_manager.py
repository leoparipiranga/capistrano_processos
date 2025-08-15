"""
Módulo para gerenciamento permanente de dados de autocomplete
Salva e carrega entradas personalizadas de assuntos e órgãos no GitHub
"""

import json
import streamlit as st
from components.functions_controle import load_data_from_github, save_data_to_github_seguro

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
