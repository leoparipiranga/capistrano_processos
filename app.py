import streamlit as st
import math

st.set_page_config(
    page_title="Capistrano Advogados", 
    layout="wide",
    page_icon="⚖️",
    initial_sidebar_state="expanded"
)

# CSS para estilização da página de login e ocultar elementos do Streamlit
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    .stDeployButton {display:none;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Estilização do container de login */
    .login-container {
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        background-color: #f9f9f9;
        text-align: center;
    }
    .login-header h1 {
        color: #333;
        margin-bottom: 0.5rem;
    }
    .login-header p {
        color: #666;
        margin: 0;
    }

    /* Classe para centralizar conteúdo */
    .centered-content {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
</style>
""", unsafe_allow_html=True)

def autenticar(usuario, senha):
    try:
        usuarios = st.secrets["usuarios"]
        if usuario in usuarios:
            usuario_data = usuarios[usuario]
            return senha == usuario_data["senha"]
        return False
    except Exception as e:
        st.error(f"Erro na autenticação: {e}")
        return False

def obter_dados_usuario(usuario):
    """Obtém dados completos do usuário autenticado"""
    try:
        usuarios = st.secrets["usuarios"]
        if usuario in usuarios:
            return usuarios[usuario]
        return None
    except Exception as e:
        st.error(f"Erro ao obter dados do usuário: {e}")
        return None

if "logado" not in st.session_state:
    st.session_state.logado = False

if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "home"

if not st.session_state.logado:
    
    col1, col2, col3 = st.columns([2, 3, 2])

    with col2:
        st.markdown('<div class="centered-content">', unsafe_allow_html=True)       
        with st.container():
            st.image("logo.jpg", width=300)
            st.markdown("### 🔐 Acesso ao Sistema")

            # Envolve os inputs e o botão em um formulário
            with st.form(key="login_form"):
                usuario = st.text_input(
                    "👤 Usuário",
                    placeholder="Digite seu usuário",
                    label_visibility="collapsed"
                )
                senha = st.text_input(
                    "🔑 Senha",
                    type="password",
                    placeholder="Digite sua senha",
                    label_visibility="collapsed"
                )

                # Usa st.form_submit_button em vez de st.button
                submitted = st.form_submit_button("Entrar", use_container_width=True, type="primary")
                
                if submitted:
                    if autenticar(usuario, senha):
                        st.session_state.logado = True
                        st.session_state.usuario = usuario
                        
                        dados_usuario = obter_dados_usuario(usuario)
                        if dados_usuario:
                            st.session_state.nome_completo = dados_usuario.get("nome_completo", usuario)
                            st.session_state.perfil_usuario = dados_usuario.get("perfil", "N/A")
                        
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos.")
            
        st.markdown("</div>", unsafe_allow_html=True)

else:
    # Mostrar informações do usuário logado
    col_user, col_logout = st.columns([3, 1])
    
    with col_user:
        nome = st.session_state.get("nome_completo", "Usuário")
        perfil = st.session_state.get("perfil_usuario", "N/A")
        st.write(f"👤 **{nome}** | 🏷️ {perfil}")
    
    with col_logout:
        if st.button("Logout"):
            # Limpar todas as informações da sessão
            keys_to_clear = ["logado", "usuario", "nome_completo", "perfil_usuario"]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    # MENU LATERAL ALTERNATIVO
    with st.sidebar.expander("⚖️ Processos", expanded=True):
        if st.button("💰 Alvarás", key='processo_alvaras'):
            st.session_state.pagina_atual = "processo_alvaras"
        if st.button("📄 RPV", key='processo_rpv'):
            st.session_state.pagina_atual = "processo_rpv"
        if st.button("📋 Benefícios", key='processo_beneficios'):
            st.session_state.pagina_atual = "processo_beneficios"
    
    with st.sidebar.expander("⚙️ Configurações", expanded=False):
        if st.button("☁️ Google Drive", key='config_drive'):
            st.session_state.pagina_atual = "config_drive"

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
    elif st.session_state.pagina_atual == "config_drive":
        from configuracao_drive import interface_configuracao_drive
        interface_configuracao_drive()
    