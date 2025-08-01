"""
Módulo para configuração e renovação do Google Drive OAuth
Integrado ao sistema principal do Capistrano
"""

import streamlit as st
import os
from google_auth_oauthlib.flow import Flow

# Permitir HTTP local para desenvolvimento OAuth
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

def interface_configuracao_drive():
    """Interface para configuração do Google Drive integrada ao app"""
    
    st.subheader("🔧 Configuração Google Drive")
    
    # Verificar configuração atual
    if "google_drive" in st.secrets and "refresh_token" in st.secrets.google_drive:
        st.success("✅ Google Drive configurado!")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧪 Testar Conexão"):
                from components.google_drive_integration import test_google_drive_connection
                test_google_drive_connection()
        
        with col2:
            if st.button("🔄 Gerar Novo Token"):
                st.session_state.show_token_generator = True
                st.rerun()
    else:
        st.warning("⚠️ Google Drive não configurado")
        if st.button("⚙️ Configurar Agora"):
            st.session_state.show_token_generator = True
            st.rerun()
    
    # Mostrar gerador de token se solicitado
    if st.session_state.get("show_token_generator", False):
        st.markdown("---")
        _mostrar_gerador_token()

def _mostrar_gerador_token():
    """Interface para gerar novo refresh token"""
    
    st.markdown("### 🔄 Gerar Novo Refresh Token")
    
    # Verificar configuração [web]
    if "web" not in st.secrets:
        st.error("❌ Configuração `[web]` não encontrada no secrets.toml")
        st.info("Adicione a seção [web] com as credenciais do Google Cloud")
        return
    
    client_config = st.secrets.web
    
    # Seleção da URI de redirecionamento
    redirect_uris = client_config.get("redirect_uris", [])
    if not redirect_uris:
        st.error("❌ Nenhuma `redirect_uris` encontrada na configuração")
        return
    
    selected_redirect_uri = st.selectbox(
        "URI de Redirecionamento:",
        options=redirect_uris,
        help="Use localhost para desenvolvimento local"
    )
    
    # Gerar link de autorização
    if st.button("🔗 Gerar Link de Autorização", type="primary"):
        try:
            client_config_dict = {
                "web": {
                    "client_id": client_config["client_id"],
                    "project_id": client_config["project_id"],
                    "auth_uri": client_config["auth_uri"],
                    "token_uri": client_config["token_uri"],
                    "auth_provider_x509_cert_url": client_config["auth_provider_x509_cert_url"],
                    "client_secret": client_config["client_secret"],
                    "redirect_uris": list(client_config["redirect_uris"])
                }
            }
            
            flow = Flow.from_client_config(
                client_config_dict,
                scopes=['https://www.googleapis.com/auth/drive.file'],
                redirect_uri=selected_redirect_uri
            )
            
            auth_url, _ = flow.authorization_url(
                prompt='consent',
                access_type='offline'
            )
            
            st.session_state.oauth_flow = flow
            st.session_state.auth_url = auth_url
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Erro ao gerar link: {e}")
    
    # Processar autorização
    if "auth_url" in st.session_state:
        st.success("✅ Link gerado!")
        st.markdown(f"### [🔗 AUTORIZAR ACESSO]({st.session_state.auth_url})")
        
        st.info("""
        **Instruções:**
        1. Clique no link acima
        2. Faça login e autorize o acesso
        3. Copie a URL completa da página final
        4. Cole no campo abaixo
        """)
        
        response_url = st.text_area(
            "Cole a URL de resposta:",
            height=100
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Processar Token", disabled=not response_url):
                _processar_token(response_url)
        
        with col2:
            if st.button("❌ Cancelar"):
                _limpar_sessao_oauth()
                st.rerun()

def _processar_token(response_url):
    """Processar URL de resposta e gerar tokens"""
    try:
        flow = st.session_state.oauth_flow
        flow.fetch_token(authorization_response=response_url)
        credentials = flow.credentials
        
        if not credentials.refresh_token:
            st.error("❌ Refresh token não obtido")
            st.warning("💡 Revogue o acesso em https://myaccount.google.com/permissions e tente novamente")
            return
        
        st.success("🎉 Tokens gerados com sucesso!")
        
        # Mostrar nova configuração
        st.markdown("### 📝 Nova Configuração:")
        
        new_config = f"""[google_drive]
client_id = "{credentials.client_id}"
client_secret = "{credentials.client_secret}"
refresh_token = "{credentials.refresh_token}"
token_uri = "{credentials.token_uri}"
type = "authorized_user"
alvaras_folder_id = "1eky76L8XF6G2uKxsSh0KmfRg-XEOmnN0"
"""
        
        st.code(new_config, language="toml")
        
        st.success("""
        ✅ **Próximos passos:**
        1. Copie a configuração acima
        2. Substitua a seção [google_drive] no secrets.toml
        3. Reinicie o aplicativo
        """)
        
        _limpar_sessao_oauth()
        
    except Exception as e:
        st.error(f"❌ Erro ao processar: {e}")
        if "invalid_grant" in str(e).lower():
            st.warning("⚠️ Código expirado. Gere um novo link.")

def _limpar_sessao_oauth():
    """Limpar dados da sessão OAuth"""
    keys_to_remove = ['oauth_flow', 'auth_url', 'show_token_generator']
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]

def interface_teste_drive():
    """Interface simples para teste do Google Drive"""
    
    st.subheader("🧪 Teste Google Drive")
    
    if st.button("🔗 Testar Conexão", type="primary"):
        from components.google_drive_integration import test_google_drive_connection
        test_google_drive_connection()
    
    st.markdown("---")
    
    # Informações da configuração atual
    if "google_drive" in st.secrets:
        st.markdown("### 📋 Configuração Atual:")
        config = st.secrets.google_drive
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Client ID:** {config.get('client_id', 'N/A')[:20]}...")
            st.write(f"**Pasta ID:** {config.get('alvaras_folder_id', 'N/A')}")
        
        with col2:
            has_refresh = 'refresh_token' in config
            has_token = 'token' in config
            st.write(f"**Refresh Token:** {'✅' if has_refresh else '❌'}")
            st.write(f"**Access Token:** {'✅' if has_token else '❌'}")
    else:
        st.warning("⚠️ Configuração do Google Drive não encontrada")