import streamlit as st

st.set_page_config(page_title="Capistrano Advogados", layout="wide")

def autenticar(usuario, senha):
    users = st.secrets["users"]
    return usuario in users and senha == users[usuario]

if "logado" not in st.session_state:
    st.session_state.logado = False

if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "home"

if not st.session_state.logado:
    st.title("Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if autenticar(usuario, senha):
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")
else:
    if st.button("Logout"):
        st.session_state.logado = False
        st.rerun()

    # MENU LATERAL ALTERNATIVO
    with st.sidebar.expander("⚖️ Processos", expanded=True):
        if st.button("💰 Alvarás", key='processo_alvaras'):
            st.session_state.pagina_atual = "processo_alvaras"
        if st.button("📄 RPV", key='processo_rpv'):
            st.session_state.pagina_atual = "processo_rpv"
        if st.button("📋 Benefícios", key='processo_beneficios'):
            st.session_state.pagina_atual = "processo_beneficios"

    # CONTEÚDO DAS PÁGINAS
    if st.session_state.pagina_atual == "processo_alvaras":
        from processos import lista_alvaras
        lista_alvaras.show()
    elif st.session_state.pagina_atual == "processo_rpv":
        from processos import lista_rpv
        lista_rpv.show()
    elif st.session_state.pagina_atual == "processo_beneficios":
        from processos import lista_beneficios
        lista_beneficios.show()
    