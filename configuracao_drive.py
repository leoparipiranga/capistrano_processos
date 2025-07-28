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
    st.title("🔧 Configuração do Google Drive")
    st.info(
        "Esta página ajuda a gerar as credenciais de `refresh_token` necessárias para o app. "
        "Ela usa a configuração `[web]` que você já deve ter adicionado aos segredos do Streamlit."
    )

    # ETAPA 1: Verificar se a configuração inicial [web] existe nos segredos
    st.markdown("---")
    st.subheader("Passo 1: Verificação da Configuração Inicial")

    if "web" not in st.secrets or "client_id" not in st.secrets.web:
        st.error("❌ Configuração `[web]` não encontrada nos segredos do Streamlit.")
        st.warning(
            "Adicione o conteúdo do seu `client_secret.json` como uma seção `[web]` "
            "nos segredos do seu app no Streamlit Cloud antes de continuar."
        )
        return

    client_config = st.secrets.web
    st.success("✅ Configuração `[web]` encontrada nos segredos!")
    st.write(f"**Client ID:** `{client_config.get('client_id', 'N/A')}`")

    # ETAPA 2: Verificar se o refresh_token já foi gerado e configurado
    st.markdown("---")
    st.subheader("Passo 2: Verificação do Token de Acesso")

    if "google_drive" in st.secrets and "refresh_token" in st.secrets.google_drive:
        st.success("✅ O app já está configurado com um `refresh_token` na seção `[google_drive]`!")
        st.info("Você pode testar a conexão abaixo ou gerar um novo token se necessário.")
        if not st.checkbox("Quero gerar um novo token mesmo assim"):
            # Teste de conexão
            st.markdown("---")
            st.subheader("🧪 Teste de Conexão")
            if st.button("🧪 Testar Google Drive", type="primary"):
                from components.google_drive_integration import test_google_drive_connection
                test_google_drive_connection()
            return

    st.warning("⚠️ `Refresh token` ainda não configurado na seção `[google_drive]` dos segredos.")

    # ETAPA 3: Gerar o token
    st.markdown("---")
    st.subheader("Passo 3: Gerar Novo Token de Acesso")

    redirect_uris = client_config.get("redirect_uris", [])
    if not redirect_uris:
        st.error("❌ Nenhuma `redirect_uris` encontrada na sua configuração `[web]` nos segredos.")
        return

    # Permite ao usuário escolher qual URI usar, crucial para funcionar local e remotamente
    selected_redirect_uri = st.selectbox(
        "Selecione a URI de Redirecionamento para usar:",
        options=redirect_uris,
        help="Use 'localhost' para rodar localmente e a URL do Streamlit Cloud para rodar no deploy."
    )

    if st.button("📝 Gerar Link de Autorização", type="primary"):
        try:
            flow = Flow.from_client_config(
                client_config.to_dict(),  # Converte para dict para a biblioteca
                scopes=['https://www.googleapis.com/auth/drive'], # Escopo de escrita/leitura
                redirect_uri=selected_redirect_uri
            )
            auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
            st.session_state.oauth_flow = flow
            st.session_state.auth_url = auth_url
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erro ao gerar link: {e}")

    if "auth_url" in st.session_state:
        st.success("✅ Link gerado! Clique abaixo para autorizar o acesso.")
        st.markdown(f"### [🔗 CLIQUE AQUI PARA AUTORIZAR]({st.session_state.auth_url})")
        st.markdown("---")

        response_url = st.text_area(
            "Após autorizar, cole a URL completa que aparecer no seu navegador aqui:",
            height=100
        )

        if st.button("🔄 Obter Token a partir da URL", disabled=not response_url):
            with st.spinner("Processando..."):
                try:
                    flow = st.session_state.oauth_flow
                    flow.fetch_token(authorization_response=response_url)
                    credentials = flow.credentials

                    if not credentials.refresh_token:
                        st.error("❌ Falha ao obter o `refresh_token`.")
                        st.info("Isso pode acontecer se você já autorizou este app antes. Revogue o acesso em 'myaccount.google.com/permissions' e tente gerar um novo link.")
                        st.stop()

                    st.success("✅ Sucesso! Token de acesso gerado.")
                    st.info("Copie o bloco abaixo e cole nos segredos do seu app no Streamlit Cloud.")

                    # Monta o TOML para o usuário copiar
                    credentials_toml = f"""[google_drive]
client_id = "{credentials.client_id}"
client_secret = "{credentials.client_secret}"
refresh_token = "{credentials.refresh_token}"
token_uri = "{credentials.token_uri}"
# Adicione outras chaves necessárias, como o folder_id
alvaras_folder_id = "COLOQUE_O_ID_DA_PASTA_AQUI"
"""
                    st.code(credentials_toml, language="toml")

                    # Limpa o estado da sessão
                    del st.session_state.oauth_flow
                    del st.session_state.auth_url
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Erro ao processar o token: {e}")
                    if "invalid_grant" in str(e).lower():
                        st.warning("O código de autorização expirou ou é inválido. Por favor, gere um novo link de autorização.")

if __name__ == "__main__":
    configurar_google_drive()