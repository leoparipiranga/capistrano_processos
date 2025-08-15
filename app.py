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
        ### 🚀 **O que é o Sistema Capistrano?**
        
        O Sistema Capistrano é uma **plataforma web avançada** desenvolvida para gerenciar três tipos principais de processos com **funcionalidades completas de workflow** e **sistema de pagamento parcelado**:
        
        - **🏛️ Alvarás**: Processos relacionados a licenças e autorizações administrativas
        - **💰 RPV**: Requisições de Pequeno Valor com análise jurídica
        - **🎯 Benefícios**: Processos de benefícios sociais com **sistema SAC** e **parcelamento em até 12x**
        
        ### ⭐ **Principais Recursos Avançados**
        
        #### 💳 **Sistema de Pagamento Parcelado**
        - **Parcelamento em até 12x** para processos de benefícios
        - **Controle individual** de cada parcela (Pendente, Pago, Atrasado)
        - **Dashboard financeiro** com métricas detalhadas
        - **Timeline completa** de pagamentos
        
        #### 👥 **Novo Perfil SAC (Customer Service)**
        - **Atendimento especializado** ao cliente
        - **Workflow dedicado** para contato com beneficiários
        - **Integração completa** com o fluxo de benefícios
        
        #### 🔄 **Workflow Inteligente**
        - **Fluxos específicos** para cada tipo de processo
        - **Transições controladas** por perfil de usuário
        - **Histórico completo** de todas as operações
        - **Estados bem definidos** para cada etapa
        
        #### 📊 **Dashboard e Relatórios**
        - **Métricas em tempo real** de todos os processos
        - **Gráficos interativos** por status e responsável
        - **Filtros avançados** por período e tipo
        - **Exportação de dados** para análise
        
        #### 🔒 **Segurança e Controle**
        - **6 perfis de usuário** com permissões específicas
        - **Log completo** de todas as operações
        - **Backup automático** via Google Drive
        - **Controle de versões** de documentos
        """)
        
        st.success("🎉 **Sistema 100% atualizado** - Incluindo novo perfil SAC e sistema de parcelamento avançado!")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                label="📋 Tipos de Processo", 
                value="3", 
                help="Alvarás, RPV e Benefícios"
            )
        with col2:
            st.metric(
                label="👥 Perfis de Usuário", 
                value="6", 
                help="Admin, Cadastrador, Administrativo, Financeiro, Jurídico, SAC"
            )
        with col3:
            st.metric(
                label="💳 Parcelas Máximas", 
                value="12x", 
                help="Sistema de parcelamento para benefícios"
            )
    
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
                "descricao": "Atendimento ao cliente - Etapa de contato",
                "permissoes": [
                    "✅ Visualizar processos enviados para SAC",
                    "✅ Marcar cliente como contatado",
                    "✅ Enviar processos para financeiro",
                    "❌ Editar informações do processo",
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
        st.header("📋 Gerenciamento de Processos")
        
        st.markdown("""
        ### Tipos de Processos
        
        O sistema gerencia três categorias principais de processos:
        """)
        
        # Sub-abas para cada tipo de processo
        sub_tab1, sub_tab2, sub_tab3 = st.tabs(["🏛️ Alvarás", "💰 RPV", "🎯 Benefícios"])
        
        with sub_tab1:
            st.markdown("""
            #### 🏛️ Alvarás - Licenças e Autorizações
            
            **Fluxo do Processo:**
            1. **📝 Cadastrado:** Inserção inicial dos dados do alvará
            2. **💰 Enviado para Financeiro:** Processo enviado para análise financeira
            3. **👔 Enviado para o Chefe:** Aprovação final e autorização
            4. **🎯 Finalizado:** Processo concluído com pagamento registrado
            
            **Responsabilidades por Perfil:**
            - **Cadastrador**: Criação e cadastro inicial
            - **Financeiro**: Análise de valores e documentos
            - **Admin**: Aprovação final e gestão completa
            
            **Funcionalidades:**
            - Cadastro de novos alvarás
            - Upload de documentos comprobatórios
            - Controle de status e acompanhamento
            - Gestão de pagamentos
            - Relatórios e visualizações
            """)
        
        with sub_tab2:
            st.markdown("""
            #### � RPV - Requisições de Pequeno Valor
            
            **Fluxo do Processo:**
            1. **📝 Cadastrado:** Registro da requisição inicial
            2. **⚖️ Em Análise Jurídica:** Avaliação legal do processo
            3. **💰 Aprovado - Aguardando Pagamento:** Preparação para pagamento
            4. **✅ Pago:** RPV processado e finalizado
            
            **Responsabilidades por Perfil:**
            - **Cadastrador**: Registro inicial da RPV
            - **Jurídico**: Análise legal e aprovação
            - **Financeiro**: Processamento de pagamentos
            - **Admin**: Gestão completa do fluxo
            
            **Funcionalidades:**
            - Controle de prazos e vencimentos
            - Gestão de documentação
            - Acompanhamento de status
            - Relatórios financeiros
            - Operações em massa (exclusão)
            """)
        
        with sub_tab3:
            st.markdown("""
            #### 🎯 Benefícios - Processos de Benefícios Sociais
            
            **Fluxo Completo do Processo:**
            1. **📝 Ativo:** Cadastrador cria o processo inicial
            2. **🏢 Enviado para Administrativo:** Processo enviado para análise
            3. **💻 Implantado:** Processo implantado pelo administrativo
            4. **📞 Enviado para SAC:** Processo enviado para contato com cliente
            5. **☎️ Contato SAC:** SAC faz contato e marca como contatado
            6. **💰 Enviado para Financeiro:** Processo enviado para cobrança
            7. **🎯 Finalizado:** Processo concluído com pagamento
            
            **Responsabilidades por Perfil:**
            - **Cadastrador**: Criação do processo inicial
            - **Administrativo**: Análise, documentação e implantação
            - **SAC**: Contato com clientes e acompanhamento
            - **Financeiro**: Gestão de pagamentos e parcelamentos
            - **Admin**: Controle total do sistema
            
            **Funcionalidades Avançadas:**
            - **Sistema de Pagamento Parcelado:** Suporte a parcelamento em até 12x
            - **Controle Individual de Parcelas:** Acompanhamento detalhado de cada parcela
            - **Timeline Completa:** Histórico detalhado de todas as etapas
            - **Gestão de Documentos:** Upload e controle de comprovantes
            - **Dashboard Financeiro:** Visão completa dos pagamentos
            - **Workflow SAC:** Sistema completo de atendimento ao cliente
            """)
        
        st.markdown("""
        ---
        ### 🔄 Estados e Transições
        
        Cada tipo de processo possui estados específicos e regras de transição definidas pelos perfis de usuário.
        
        ### 👥 Novo Perfil: SAC (Customer Service)
        
        O perfil **SAC** foi criado especificamente para gerenciar o atendimento ao cliente nos processos de benefícios:
        - **Acesso**: Apenas processos de benefícios
        - **Funcionalidades**: Contato com clientes, atualização de status
        - **Workflow**: Recebe processos implantados e faz contato com beneficiários
        """)
        
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
                "pergunta": "❓ Como funciona o sistema de pagamento parcelado?",
                "resposta": """
                **Sistema disponível apenas para Benefícios:**
                1. Na edição do processo, escolha "Pagamento Parcelado"
                2. Selecione o número de parcelas (até 12x)
                3. O sistema criará automaticamente todas as parcelas
                4. Cada parcela tem status individual: Pendente, Pago, Atrasado
                5. Use o dashboard para acompanhar o progresso dos pagamentos
                """
            },
            {
                "pergunta": "❓ O que é o perfil SAC e como funciona?",
                "resposta": """
                **SAC (Customer Service)** é o novo perfil para atendimento ao cliente:
                - **Função**: Fazer contato com beneficiários de processos implantados
                - **Acesso**: Apenas processos de benefícios enviados para SAC
                - **Workflow**: Recebe processos → Faz contato → Marca como contatado → Envia para financeiro
                - **Permissões**: Visualizar processos SAC, marcar como contatado, enviar para financeiro
                """
            },
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
                Para **RPV**, use a funcionalidade de exclusão em massa selecionando múltiplos itens.
                """
            },
            {
                "pergunta": "❓ Como funciona o novo fluxo de benefícios?",
                "resposta": """
                **Fluxo completo em 7 etapas:**
                1. **Ativo** (Cadastrador)
                2. **Enviado para Administrativo** (Administrativo analisa)
                3. **Implantado** (Administrativo implanta)
                4. **Enviado para SAC** (SAC faz contato)
                5. **Contato SAC** (Cliente contatado)
                6. **Enviado para Financeiro** (Cobrança)
                7. **Finalizado** (Processo concluído)
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
                **Novos perfis disponíveis**: Admin, Cadastrador, Administrativo, Financeiro, Jurídico, SAC
                """
            },
            {
                "pergunta": "❓ O que acontece se eu excluir um processo por engano?",
                "resposta": """
                Todas as exclusões são registradas no Log de Exclusões.
                Entre em contato com o administrador para possível recuperação.
                **RPV**: Use a exclusão em massa para eficiência.
                """
            },
            {
                "pergunta": "❓ Como funciona a integração com Google Drive?",
                "resposta": """
                - Arquivos são automaticamente enviados para o Drive
                - Organizados por tipo de processo
                - Backup de segurança dos dados
                - Configuração necessária apenas pelo Admin
                - Suporte a múltiplos documentos por processo
                """
            },
            {
                "pergunta": "❓ Como acompanhar parcelas em atraso?",
                "resposta": """
                **Para usuários Financeiro e Admin:**
                1. Acesse a lista de Benefícios
                2. Use os filtros para mostrar apenas "Parcelado"
                3. Na edição do processo, veja o status de cada parcela
                4. Parcelas em vermelho estão atrasadas
                5. Use o dashboard para métricas gerais de pagamento
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
