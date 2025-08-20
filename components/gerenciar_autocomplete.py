"""
Interface para gerenciamento de dados de autocomplete (apenas admins)
"""

import streamlit as st
from components.autocomplete_manager import (
    carregar_dados_autocomplete,
    remover_orgao_judicial,
    remover_assunto_beneficio, 
    remover_assunto_rpv,
    remover_orgao_rpv,
    obter_orgaos_judiciais_completo,
    obter_assuntos_beneficios_completo,
    obter_assuntos_rpv_completo,
    obter_orgaos_rpv_completo
)

def interface_gerenciamento_autocomplete():
    """Interface principal para gerenciar dados de autocomplete"""
    
    st.title("🗂️ Gerenciamento de Autocomplete")
    st.markdown("---")
    
    # Verificar se é admin
    if not hasattr(st.session_state, 'perfil_usuario') or st.session_state.perfil_usuario != "Admin":
        st.error("🚫 Acesso negado. Esta funcionalidade é apenas para administradores.")
        return
    
    # Carregar dados atuais
    dados_salvos = carregar_dados_autocomplete()
    
    st.info("ℹ️ **Importante:** Esta interface permite remover apenas itens que foram adicionados manualmente. Itens padrão do sistema não podem ser removidos.")
    
    # Tabs para cada categoria
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏛️ Órgãos Judiciais", 
        "📄 Assuntos Benefícios", 
        "📋 Assuntos RPV", 
        "🏢 Órgãos RPV"
    ])
    
    with tab1:
        gerenciar_orgaos_judiciais(dados_salvos)
    
    with tab2:
        gerenciar_assuntos_beneficios(dados_salvos)
    
    with tab3:
        gerenciar_assuntos_rpv(dados_salvos)
        
    with tab4:
        gerenciar_orgaos_rpv(dados_salvos)

def gerenciar_orgaos_judiciais(dados_salvos):
    """Interface para gerenciar órgãos judiciais"""
    
    st.subheader("🏛️ Órgãos Judiciais")
    
    # Mostrar estatísticas
    todos_orgaos = obter_orgaos_judiciais_completo()
    orgaos_salvos = dados_salvos.get("orgaos_judiciais", [])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Órgãos", len(todos_orgaos))
    with col2:
        st.metric("Órgãos Padrão", len(todos_orgaos) - len(orgaos_salvos))
    with col3:
        st.metric("Órgãos Adicionados", len(orgaos_salvos))
    
    st.markdown("---")
    
    if orgaos_salvos:
        st.write("**Órgãos que podem ser removidos:**")
        
        for orgao in sorted(orgaos_salvos):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.write(f"• {orgao}")
            
            with col2:
                if st.button("🗑️", key=f"remove_orgao_{orgao}", help=f"Remover {orgao}"):
                    if remover_orgao_judicial(orgao):
                        st.success(f"✅ '{orgao}' removido com sucesso!")
                        st.rerun()
                    else:
                        st.error(f"❌ Erro ao remover '{orgao}'")
    else:
        st.info("📝 Nenhum órgão judicial personalizado adicionado ainda.")

def gerenciar_assuntos_beneficios(dados_salvos):
    """Interface para gerenciar assuntos de benefícios"""
    
    st.subheader("📄 Assuntos de Benefícios")
    
    # Mostrar estatísticas
    todos_assuntos = obter_assuntos_beneficios_completo()
    assuntos_salvos = dados_salvos.get("assuntos_beneficios", [])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Assuntos", len(todos_assuntos))
    with col2:
        st.metric("Assuntos Padrão", len(todos_assuntos) - len(assuntos_salvos))
    with col3:
        st.metric("Assuntos Adicionados", len(assuntos_salvos))
    
    st.markdown("---")
    
    if assuntos_salvos:
        st.write("**Assuntos que podem ser removidos:**")
        
        for assunto in sorted(assuntos_salvos):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.write(f"• {assunto}")
            
            with col2:
                if st.button("🗑️", key=f"remove_assunto_ben_{assunto}", help=f"Remover {assunto}"):
                    if remover_assunto_beneficio(assunto):
                        st.success(f"✅ '{assunto}' removido com sucesso!")
                        st.rerun()
                    else:
                        st.error(f"❌ Erro ao remover '{assunto}'")
    else:
        st.info("📝 Nenhum assunto de benefício personalizado adicionado ainda.")

def gerenciar_assuntos_rpv(dados_salvos):
    """Interface para gerenciar assuntos de RPV"""
    
    st.subheader("📋 Assuntos de RPV")
    
    # Mostrar estatísticas
    todos_assuntos = obter_assuntos_rpv_completo()
    assuntos_salvos = dados_salvos.get("assuntos_rpv", [])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Assuntos", len(todos_assuntos))
    with col2:
        st.metric("Assuntos Padrão", len(todos_assuntos) - len(assuntos_salvos))
    with col3:
        st.metric("Assuntos Adicionados", len(assuntos_salvos))
    
    st.markdown("---")
    
    if assuntos_salvos:
        st.write("**Assuntos que podem ser removidos:**")
        
        for assunto in sorted(assuntos_salvos):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.write(f"• {assunto}")
            
            with col2:
                if st.button("🗑️", key=f"remove_assunto_rpv_{assunto}", help=f"Remover {assunto}"):
                    if remover_assunto_rpv(assunto):
                        st.success(f"✅ '{assunto}' removido com sucesso!")
                        st.rerun()
                    else:
                        st.error(f"❌ Erro ao remover '{assunto}'")
    else:
        st.info("📝 Nenhum assunto de RPV personalizado adicionado ainda.")

def gerenciar_orgaos_rpv(dados_salvos):
    """Interface para gerenciar órgãos de RPV"""
    
    st.subheader("🏢 Órgãos de RPV")
    
    # Mostrar estatísticas
    todos_orgaos = obter_orgaos_rpv_completo()
    orgaos_salvos = dados_salvos.get("orgaos_rpv", [])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Órgãos", len(todos_orgaos))
    with col2:
        st.metric("Órgãos Padrão", len(todos_orgaos) - len(orgaos_salvos))
    with col3:
        st.metric("Órgãos Adicionados", len(orgaos_salvos))
    
    st.markdown("---")
    
    if orgaos_salvos:
        st.write("**Órgãos que podem ser removidos:**")
        
        for orgao in sorted(orgaos_salvos):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.write(f"• {orgao}")
            
            with col2:
                if st.button("🗑️", key=f"remove_orgao_rpv_{orgao}", help=f"Remover {orgao}"):
                    if remover_orgao_rpv(orgao):
                        st.success(f"✅ '{orgao}' removido com sucesso!")
                        st.rerun()
                    else:
                        st.error(f"❌ Erro ao remover '{orgao}'")
    else:
        st.info("📝 Nenhum órgão de RPV personalizado adicionado ainda.")
