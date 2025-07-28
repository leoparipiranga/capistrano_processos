"""
Script para configuração inicial do Google Drive OAuth 2.0
"""

import streamlit as st
from google_auth_oauthlib.flow import Flow
import json
import os
from urllib.parse import urlparse, parse_qs

# Permitir HTTP local para desenvolvimento OAuth
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

def extrair_codigo_da_url(url):
    """Extrair código de autorização da URL de resposta"""
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        code = query_params.get('code', [None])[0]
        return code
    except Exception:
        return None

def configurar_google_drive():
    st.title("🔧 Teste Google Drive")
    
    # Verificar arquivo client_secret.json
    client_secret_path = ".streamlit/client_secret.json"
    
    if not os.path.exists(client_secret_path):
        st.error(f"❌ Arquivo {client_secret_path} não encontrado!")
        return
    
    st.success("✅ Arquivo client_secret.json encontrado!")
    
    # Ler credenciais
    try:
        with open(client_secret_path, 'r') as f:
            credentials_data = json.load(f)
        
        client_config = credentials_data.get('web', credentials_data.get('installed', {}))
        
        if not client_config:
            st.error("❌ Arquivo de credenciais inválido")
            return
        
        st.info(f"**Client ID:** {client_config.get('client_id', 'N/A')}")
        
        # Verificar se já temos refresh_token
        existing_creds = st.secrets.get("google_drive", {})
        if existing_creds.get('refresh_token') and not str(existing_creds.get('refresh_token')).startswith('seu_'):
            st.success("✅ Já possui refresh_token configurado!")
            return
        
        st.warning("⚠️ Refresh token não configurado.")
        
        # Formulário OAuth usando expander
        with st.expander("🔐 Configurar OAuth", expanded=True):
            
            # Etapa 1: Gerar link
            st.markdown("**Etapa 1: Gerar Link de Autorização**")
            if st.button("📝 Gerar Link"):
                try:
                    flow = Flow.from_client_config(
                        credentials_data,
                        scopes=['https://www.googleapis.com/auth/drive.file'],
                        redirect_uri='http://localhost:8501'
                    )
                    auth_url, _ = flow.authorization_url(prompt='consent')
                    
                    # Salvar no session state
                    st.session_state.oauth_flow = flow
                    st.session_state.auth_url = auth_url
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")
            
            # Mostrar link se existe
            if hasattr(st.session_state, 'auth_url'):
                st.success("✅ Link gerado!")
                st.markdown(f"[**🔗 Clique aqui para autorizar**]({st.session_state.auth_url})")
                
                st.markdown("**Etapa 2: Processar Código**")
                
                # Formulário para URL
                with st.form("oauth_form"):
                    response_url = st.text_area(
                        "Cole a URL de resposta aqui:",
                        placeholder="http://localhost:8501/?code=...",
                        height=100
                    )
                    
                    submitted = st.form_submit_button("🔄 Processar")
                
                if submitted and response_url:
                    with st.spinner("Processando..."):
                        try:
                            # Extrair código
                            codigo = extrair_codigo_da_url(response_url.strip())
                            if not codigo:
                                st.error("❌ URL inválida")
                                st.stop()
                            
                            st.write(f"✅ Código: {codigo[:20]}...")
                            
                            # Processar
                            flow = st.session_state.oauth_flow
                            flow.fetch_token(authorization_response=response_url.strip())
                            credentials = flow.credentials
                            
                            if not credentials.refresh_token:
                                st.error("❌ Refresh token não recebido")
                                st.info("💡 Revogue o acesso em https://myaccount.google.com/permissions e tente novamente")
                                st.stop()
                            
                            # Mostrar resultado
                            st.success("✅ Sucesso!")
                            
                            credentials_toml = f"""[google_drive]
client_id = "{credentials.client_id}"
client_secret = "{credentials.client_secret}"
refresh_token = "{credentials.refresh_token}"
token = "{credentials.token}"
token_uri = "{credentials.token_uri}"
type = "authorized_user"
alvaras_folder_id = "1eky76L8XF6G2uKxsSh0KmfRg-XEOmnN0\""""
                            
                            st.code(credentials_toml, language="toml")
                            st.success("📋 Copie o código acima e substitua no secrets.toml")
                            
                            # Limpar session state
                            if hasattr(st.session_state, 'oauth_flow'):
                                del st.session_state.oauth_flow
                            if hasattr(st.session_state, 'auth_url'):
                                del st.session_state.auth_url
                            
                        except Exception as e:
                            st.error(f"❌ Erro: {str(e)}")
                            if "invalid_grant" in str(e):
                                st.info("💡 Código expirado. Gere um novo link.")
                
                elif submitted and not response_url:
                    st.warning("⚠️ Cole a URL de resposta antes de processar")
    
    except Exception as e:
        st.error(f"❌ Erro ao ler credenciais: {str(e)}")
    
    # Teste de conexão
    st.markdown("---")
    st.subheader("🧪 Teste de Conexão")
    
    if st.button("🧪 Testar Google Drive", type="primary"):
        from components.google_drive_integration import test_google_drive_connection
        test_google_drive_connection()


if __name__ == "__main__":
    configurar_google_drive()