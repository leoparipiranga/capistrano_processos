import streamlit as st
import math

st.set_page_config(
    page_title="Capistrano Advogados", 
    layout="wide",
    page_icon="⚖️",
    initial_sidebar_state="expanded"  # Inicia aberto para mostrar o botão nativo
)

# CSS para estilização da página de login e preservar controles nativos
st.markdown("""
<style>
    .stDeployButton {display:none;}
    footer {visibility: hidden;}
    
    /* Manter o botão de menu nativo visível */
    [data-testid="collapsedControl"] {
        display: block !important;
        visibility: visible !important;
    }

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

def mostrar_guia_utilizacao():
    """Mostra o guia de utilização do sistema."""
    st.title("📖 Guia de Utilização")
    
    # Introdução
    st.markdown("""
    ## Bem-vindo ao Sistema de Processos Capistrano!
    
    Este guia fornece instruções detalhadas sobre como utilizar todas as funcionalidades do sistema.
    """)
    
    # Navegação por abas
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Visão Geral", 
        "👥 Perfis e Permissões", 
        "📋 Processos", 
        "🔧 Configurações", 
        "❓ FAQ"
    ])
    
    with tab1:
        st.header("Visão Geral do Sistema")
        st.markdown("""
        ### O que é o Sistema Capistrano?
        O Sistema Capistrano é uma plataforma web desenvolvida para gerenciar três tipos principais de processos:
        
        - **🏛️ Alvarás**: Processos relacionados a licenças e autorizações
        - **💰 RPV**: Requisições de Pequeno Valor
        - **🎯 Benefícios**: Processos de benefícios sociais
        
        """)
    
    with tab2:
        st.header("Perfis e Permissões")
        
        st.markdown("### Perfis Disponíveis")
        
        # Admin
        st.markdown("#### 🔧 **Admin**")
        st.success("**Acesso Total** - Pode fazer tudo em todos os processos")
        with st.expander("Detalhes das permissões Admin"):
            st.markdown("""
            - ✅ Visualizar todos os processos
            - ✅ Adicionar novos processos
            - ✅ Editar qualquer processo
            - ✅ Excluir qualquer processo
            - ✅ Fazer upload de anexos
            - ✅ Acessar configurações do Drive
            - ✅ Visualizar log de exclusões
            - ✅ Gerenciar todos os tipos de processo (Alvarás, RPV, Benefícios)
            """)
        
        # Outros perfis
        perfis_info = {
            "👤 Cadastrador": {
                "cor": "info",
                "descricao": "Responsável pelo cadastro de novos processos",
                "permissoes": [
                    "✅ Visualizar processos",
                    "✅ Adicionar novos processos", 
                    "✅ Fazer upload de anexos",
                    "✅ Excluir processos"
                ]
            },
            "💰 Financeiro": {
                "cor": "warning", 
                "descricao": "Acesso a informações financeiras dos processos",
                "permissoes": [
                    "✅ Visualizar processos",
                    "✅ Editar valores financeiros",
                    "✅ Fazer upload de comprovantes",
                    "❌ Excluir processos"
                ]
            },
            "⚖️ Jurídico": {
                "cor": "info",
                "descricao": "Acesso a aspectos legais dos processos", 
                "permissoes": [
                    "✅ Visualizar processos",
                    "✅ Editar informações jurídicas",
                    "✅ Fazer upload de documentos legais",
                    "❌ Excluir processos"
                ]
            },
            "🏢 Administrativo": {
                "cor": "secondary",
                "descricao": "Gerenciamento administrativo geral",
                "permissoes": [
                    "✅ Visualizar processos",
                    "✅ Editar informações administrativas", 
                    "✅ Fazer upload de documentos",
                    "❌ Excluir processos"
                ]
            },
            "📞 SAC": {
                "cor": "primary",
                "descricao": "Atendimento ao cliente",
                "permissoes": [
                    "✅ Visualizar processos",
                    "✅ Consultar status",
                    "❌ Editar processos",
                    "❌ Excluir processos"
                ]
            }
        }
        
        for perfil, info in perfis_info.items():
            st.markdown(f"#### {perfil}")
            if info["cor"] == "info":
                st.info(info["descricao"])
            elif info["cor"] == "warning":
                st.warning(info["descricao"])
            elif info["cor"] == "secondary":
                st.success(info["descricao"])
            elif info["cor"] == "primary":
                st.info(info["descricao"])
            
            with st.expander(f"Permissões do {perfil}"):
                for permissao in info["permissoes"]:
                    st.markdown(f"- {permissao}")
    
    with tab3:
        st.header("Fluxo de Processos por Status")
        
        # Alvarás
        st.markdown("### 🏛️ **Fluxo de Alvarás**")
        with st.expander("Status e Perfis Responsáveis"):
            st.markdown("""
            **📋 Cadastrado**
            - **Responsável**: Cadastrador, Admin
            - **Ação**: Processo recém-criado, aguardando documentação
            - **Próximo passo**: Upload de comprovante de conta e PDF do alvará
            
            **💰 Enviado para o Financeiro**
            - **Responsável**: Financeiro, Admin
            - **Ação**: Análise de valores e documentos financeiros
            - **Próximo passo**: Verificação e envio para o chefe
            
            **👔 Enviado para o Chefe**
            - **Responsável**: Admin
            - **Ação**: Aprovação final e autorização de pagamento
            - **Próximo passo**: Upload do comprovante de recebimento
            
            **🎯 Finalizado**
            - **Status final**: Processo completo e pago
            - **Responsável**: Admin
            - **Documentos**: Todos os comprovantes arquivados
            """)
        
        # RPV
        st.markdown("### 📄 **Fluxo de RPV**")
        with st.expander("Status e Perfis Responsáveis"):
            st.markdown("""
            **📝 Cadastrado**
            - **Responsável**: Cadastrador, Admin
            - **Ação**: RPV criada, dados básicos preenchidos
            - **Próximo passo**: Análise jurídica e definição de valores
            
            **⚖️ Em Análise Jurídica**
            - **Responsável**: Jurídico, Admin
            - **Ação**: Verificação legal da requisição
            - **Próximo passo**: Aprovação e envio para financeiro
            
            **💰 Aprovado - Aguardando Pagamento**
            - **Responsável**: Financeiro, Admin
            - **Ação**: Processamento do pagamento
            - **Próximo passo**: Confirmação do pagamento
            
            **✅ Pago**
            - **Status final**: RPV quitada
            - **Responsável**: Financeiro, Admin
            - **Documentos**: Comprovantes de pagamento arquivados
            """)
        
        # Benefícios
        st.markdown("### 📋 **Fluxo de Benefícios**")
        with st.expander("Status e Perfis Responsáveis"):
            st.markdown("""
            **📝 Ativo**
            - **Responsável**: Cadastrador, Admin
            - **Ação**: Benefício cadastrado, aguardando análise
            - **Próximo passo**: Verificação administrativa
            
            **🏢 Enviado para Administrativo**
            - **Responsável**: Administrativo, Admin
            - **Ação**: Análise documental e verificação de elegibilidade
            - **Próximo passo**: Implantação ou correções
            
            **💻 Implantado**
            - **Responsável**: Administrativo, Admin
            - **Ação**: Benefício aprovado e implantado no sistema
            - **Próximo passo**: Envio para análise financeira
            
            **💰 Enviado para Financeiro**
            - **Responsável**: Financeiro, Admin
            - **Ação**: Cálculo de valores e definição de pagamento
            - **Próximo passo**: Finalização do processo
            
            **🎯 Finalizado**
            - **Status final**: Benefício processado e concluído
            - **Responsável**: Admin
            - **Documentos**: Processo arquivado completamente
            """)
            
        st.markdown("---")
        st.info("💡 **Dica**: Cada perfil tem acesso apenas aos status relevantes para suas funções. Admins podem gerenciar todos os status.")
    with tab4:
        st.header("Configurações do Sistema")
        
        st.markdown("### 🔧 Configurações (apenas Admin)")
        st.info("Apenas usuários com perfil **Admin** têm acesso às configurações.")
        
        with st.expander("Configuração do Google Drive"):
            st.markdown("""
            **Como configurar:**
            1. Acesse "Configurações" na barra lateral
            2. Clique em "Configuração Drive"
            3. Faça upload do arquivo de credenciais JSON
            4. Configure a pasta de destino
            5. Teste a conexão
            
            **Arquivos necessários:**
            - `credentials.json` do Google Cloud Console
            - Permissões adequadas na pasta do Drive
            """)
        
        with st.expander("Log de Exclusões"):
            st.markdown("""
            **Funcionalidade:**
            - Registra todas as exclusões realizadas no sistema
            - Mantém histórico para auditoria
            - Backup automático no Google Drive
            
            **Como acessar:**
            1. Vá em "Configurações" → "Log de Exclusões"
            2. Visualize o histórico completo
            3. Exporte relatórios se necessário
            """)
    
    with tab5:
        st.header("Perguntas Frequentes (FAQ)")
        
        faqs = [
            {
                "pergunta": "❓ Como faço upload de múltiplos arquivos?",
                "resposta": """
                1. Marque a caixa "Anexar múltiplos documentos" 
                2. Clique em "Escolher arquivos"
                3. Selecione múltiplos arquivos (Ctrl+Click no Windows)
                4. Confirme o upload
                """
            },
            {
                "pergunta": "❓ Não consigo excluir um processo, por quê?",
                "resposta": """
                Apenas usuários com perfil **Admin** ou **Cadastrador** podem excluir processos.
                Outros perfis têm permissões limitadas por segurança.
                """
            },
            {
                "pergunta": "❓ Como sei se meu arquivo foi enviado?",
                "resposta": """
                Após o upload bem-sucedido, você verá:
                - Mensagem de confirmação verde
                - Nome do arquivo na lista de anexos
                - Atualização automática da interface
                """
            },
            {
                "pergunta": "❓ Posso alterar meu perfil de usuário?",
                "resposta": """
                Os perfis são definidos pelo administrador do sistema.
                Entre em contato com o responsável para alterações de perfil.
                """
            },
            {
                "pergunta": "❓ O que acontece se eu excluir um processo por engano?",
                "resposta": """
                Todas as exclusões são registradas no Log de Exclusões.
                Entre em contato com o administrador para possível recuperação.
                """
            },
            {
                "pergunta": "❓ Como funciona a integração com Google Drive?",
                "resposta": """
                - Arquivos são automaticamente enviados para o Drive
                - Organizados por tipo de processo
                - Backup de segurança dos dados
                - Configuração necessária apenas pelo Admin
                """
            }
        ]
        
        for faq in faqs:
            with st.expander(faq["pergunta"]):
                st.markdown(faq["resposta"])

if "logado" not in st.session_state:
    st.session_state.logado = False

if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "home"

if not st.session_state.logado:
    
    col1, col2, col3 = st.columns([2, 3, 2])

    with col2:
        st.markdown('<div class="centered-content">', unsafe_allow_html=True)       
        with st.container():
            # Logo centralizada e maior
            col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
            with col_logo2:
                st.image("logomarca.png", width=400)
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
    # Mostrar informações do usuário logado e controles na sidebar
    with st.sidebar:
        # Informações do usuário
        nome = st.session_state.get("nome_completo", "Usuário")
        perfil = st.session_state.get("perfil_usuario", "N/A")
        st.markdown(f"👤 **Perfil:** {perfil}")
        
        # Botão de logout na sidebar
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            # Limpar todas as informações da sessão
            keys_to_clear = ["logado", "usuario", "nome_completo", "perfil_usuario"]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        
        st.markdown("---")
    
    # Função para limpar estados de diálogos ao mudar de página
    def limpar_estados_dialogos():
        """Limpa todos os estados de diálogos abertos para evitar que reabram automaticamente"""
        dialogos_para_limpar = [
            "show_alvara_dialog", "processo_aberto_id",
            "show_rpv_dialog", "rpv_aberto_id", 
            "show_beneficio_dialog", "beneficio_aberto_id"
        ]
        
        for key in dialogos_para_limpar:
            if key in st.session_state:
                if "show_" in key:
                    st.session_state[key] = False
                else:
                    st.session_state[key] = None

    # MENU LATERAL - PROCESSOS
    with st.sidebar.expander("⚖️ Processos", expanded=True):
        if st.button("💰 Alvarás", key='processo_alvaras', use_container_width=True):
            limpar_estados_dialogos()
            st.session_state.pagina_atual = "processo_alvaras"
            st.rerun()
        
        if st.button("📄 RPV", key='processo_rpv', use_container_width=True):
            limpar_estados_dialogos()
            st.session_state.pagina_atual = "processo_rpv"
            st.rerun()
            
        if st.button("📋 Benefícios", key='processo_beneficios', use_container_width=True):
            limpar_estados_dialogos()
            st.session_state.pagina_atual = "processo_beneficios"
            st.rerun()
    
    # GUIA DE UTILIZAÇÃO
    with st.sidebar.expander("📖 Guia", expanded=False):
        if st.button("📚 Guia de Utilização", key='guia_app', use_container_width=True):
            limpar_estados_dialogos()
            st.session_state.pagina_atual = "guia_utilizacao"
            st.rerun()
    
    # CONFIGURAÇÕES - APENAS PARA ADMIN
    perfil_usuario = st.session_state.get("perfil_usuario", "N/A")
    usuario_atual = st.session_state.get("usuario", "")
    
    # Verificar se é Admin
    is_admin = (perfil_usuario == "Admin" or usuario_atual == "admin")
    
    if is_admin:
        with st.sidebar.expander("⚙️ Configurações", expanded=False):
            if st.button("☁️ Google Drive", key='config_drive', use_container_width=True):
                limpar_estados_dialogos()
                st.session_state.pagina_atual = "config_drive"
                st.rerun()
            
            if st.button("📋 Log de Exclusões", key='log_exclusoes', use_container_width=True):
                limpar_estados_dialogos()
                st.session_state.pagina_atual = "log_exclusoes"
                st.rerun()

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
    elif st.session_state.pagina_atual == "log_exclusoes":
        from components.log_exclusoes import visualizar_log_exclusoes
        visualizar_log_exclusoes()
    elif st.session_state.pagina_atual == "guia_utilizacao":
        mostrar_guia_utilizacao()
