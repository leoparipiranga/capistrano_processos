import streamlit as st
import pandas as pd
import uuid
from datetime import datetime

# Funções para dados de teste
def criar_dados_teste():
    """Cria dados de exemplo para todos os tipos de processo e status"""
    try:
        # Importar as funções necessárias
        from components.functions_controle import save_data_to_github_seguro
        
        # ===== DADOS DE TESTE RPV =====
        dados_rpv_teste = [
            {
                "ID": str(uuid.uuid4()),
                "Processo": "0001234-56.2024.5.02.0001",
                "Beneficiário": "João da Silva Teste",
                "CPF": "123.456.789-01",
                "Descricao RPV": "Diferenças salariais - teste",
                "Assunto": "Trabalhista",
                "Orgao Judicial": "TRT 2ª Região",
                "Vara": "1ª Vara do Trabalho",
                "Banco": "CEF",
                "Agência": "1234",
                "Conta": "56789-0",
                "Mês Competência": "09/2024",
                "Solicitar Certidão": "Sim",
                "Observações": "Processo de teste - RPV",
                "Status": "Cadastro",
                "Cadastrado por": "admin",
                "Data de Cadastro": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "Observações Honorários": "Teste de observações contratuais"
            },
            {
                "ID": str(uuid.uuid4()),
                "Processo": "0002345-67.2024.5.02.0002",
                "Beneficiário": "Maria dos Santos Teste",
                "CPF": "987.654.321-09",
                "Descricao RPV": "Horas extras - teste",
                "Assunto": "Trabalhista",
                "Orgao Judicial": "TRT 2ª Região",
                "Vara": "2ª Vara do Trabalho",
                "Banco": "BB",
                "Agência": "5678",
                "Conta": "12345-6",
                "Mês Competência": "10/2024",
                "Solicitar Certidão": "Não",
                "Observações": "Processo de teste - Enviado SAC",
                "Status": "Enviado SAC",
                "Cadastrado por": "admin",
                "Data de Cadastro": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "Observações Honorários": ""
            }
        ]
        
        # ===== DADOS DE TESTE ALVARÁS =====
        dados_alvaras_teste = [
            {
                "ID": str(uuid.uuid4()),
                "Processo": "0003456-78.2024.8.26.0001",
                "Parte": "Pedro Oliveira Teste",
                "CPF": "456.789.123-45",
                "Advogado": "Dr. Carlos Silva",
                "Descricao Alvara": "Liberação de valores - teste",
                "Valor": "R$ 15.000,00",
                "Banco": "CEF",
                "Agência": "9999",
                "Conta": "88888-8",
                "Obs Gerais": "Alvará de teste - Cadastro",
                "Status": "Cadastro",
                "Cadastrado por": "admin",
                "Data de Cadastro": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            },
            {
                "ID": str(uuid.uuid4()),
                "Processo": "0004567-89.2024.8.26.0002",
                "Parte": "Ana Costa Teste",
                "CPF": "789.123.456-78",
                "Advogado": "Dra. Fernanda Lima",
                "Descricao Alvara": "Herança - teste",
                "Valor": "R$ 50.000,00",
                "Banco": "BB",
                "Agência": "7777",
                "Conta": "66666-6",
                "Obs Gerais": "Alvará de teste - Enviado Rodrigo",
                "Status": "Enviado Rodrigo",
                "Cadastrado por": "admin",
                "Data de Cadastro": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
        ]
        
        # ===== DADOS DE TESTE BENEFÍCIOS =====
        dados_beneficios_teste = [
            {
                "ID": str(uuid.uuid4()),
                "Nº DO PROCESSO": "0005678-90.2024.8.26.0003",
                "PARTE": "Carlos Mendes Teste",
                "CPF": "321.654.987-12",
                "DETALHE PROCESSO": "Auxílio-doença - teste",
                "DATA DA CONCESSÃO DA LIMINAR": "15/09/2024",
                "VALOR MENSAL": "R$ 1.412,00",
                "VALOR RETROATIVO": "R$ 8.472,00",
                "TOTAL GERAL": "R$ 9.884,00",
                "VALOR DE HONORÁRIOS": "R$ 2.471,00",
                "STATUS": "Cadastro",
                "Cadastrado por": "admin",
                "Data de Cadastro": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            },
            {
                "ID": str(uuid.uuid4()),
                "Nº DO PROCESSO": "0006789-01.2024.8.26.0004",
                "PARTE": "Lucia Santos Teste",
                "CPF": "654.987.321-65",
                "DETALHE PROCESSO": "Aposentadoria - teste",
                "DATA DA CONCESSÃO DA LIMINAR": "20/09/2024",
                "VALOR MENSAL": "R$ 2.500,00",
                "VALOR RETROATIVO": "R$ 15.000,00",
                "TOTAL GERAL": "R$ 17.500,00",
                "VALOR DE HONORÁRIOS": "R$ 4.375,00",
                "STATUS": "Implantado",
                "Cadastrado por": "admin",
                "Data de Cadastro": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
        ]
        
        # ===== DADOS DE TESTE ACORDOS (FUTURO) =====
        dados_acordos_teste = [
            {
                "ID": str(uuid.uuid4()),
                "Processo": "0007890-12.2024.8.26.0005",
                "Parte": "Roberto Silva Teste",
                "CPF": "111.222.333-44",
                "Descricao Acordo": "Acordo trabalhista - teste",
                "Valor Acordo": "R$ 25.000,00",
                "Data Acordo": "22/09/2024",
                "Condicoes": "Pagamento em 6 parcelas mensais",
                "Obs Gerais": "Acordo de teste - Em desenvolvimento",
                "Status": "Proposto",
                "Cadastrado por": "admin",
                "Data de Cadastro": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            },
            {
                "ID": str(uuid.uuid4()),
                "Processo": "0008901-23.2024.8.26.0006",
                "Parte": "Sandra Costa Teste",
                "CPF": "555.666.777-88",
                "Descricao Acordo": "Acordo de indenização - teste",
                "Valor Acordo": "R$ 40.000,00",
                "Data Acordo": "25/09/2024",
                "Condicoes": "Pagamento à vista",
                "Obs Gerais": "Acordo de teste - Aceito",
                "Status": "Aceito",
                "Cadastrado por": "admin",
                "Data de Cadastro": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
        ]
        
        # Salvar dados nos respectivos arquivos
        df_rpv = pd.DataFrame(dados_rpv_teste)
        df_alvaras = pd.DataFrame(dados_alvaras_teste)
        df_beneficios = pd.DataFrame(dados_beneficios_teste)
        df_acordos = pd.DataFrame(dados_acordos_teste)
        
        # Verificar se já existem dados e adicionar aos existentes
        try:
            # Tentar carregar dados existentes
            from components.functions import load_data_from_github
            
            df_rpv_existente = load_data_from_github("lista_rpv.csv")
            df_alvaras_existente = load_data_from_github("lista_alvaras.csv")
            df_beneficios_existente = load_data_from_github("lista_beneficios.csv")
            df_acordos_existente = load_data_from_github("lista_acordos.csv")
            
            # Concatenar com dados existentes
            if not df_rpv_existente.empty:
                df_rpv = pd.concat([df_rpv_existente, df_rpv], ignore_index=True)
            if not df_alvaras_existente.empty:
                df_alvaras = pd.concat([df_alvaras_existente, df_alvaras], ignore_index=True)
            if not df_beneficios_existente.empty:
                df_beneficios = pd.concat([df_beneficios_existente, df_beneficios], ignore_index=True)
            if not df_acordos_existente.empty:
                df_acordos = pd.concat([df_acordos_existente, df_acordos], ignore_index=True)
                
        except Exception:
            # Se não conseguir carregar dados existentes, usar apenas os de teste
            pass
        
        # Salvar nos session_state e no GitHub
        st.session_state.df_editado_rpv = df_rpv
        st.session_state.df_editado_alvara = df_alvaras
        st.session_state.df_editado_beneficio = df_beneficios
        st.session_state.df_editado_acordo = df_acordos
        
        save_data_to_github_seguro(df_rpv, "lista_rpv.csv", "file_sha_rpv")
        save_data_to_github_seguro(df_alvaras, "lista_alvaras.csv", "file_sha_alvara")
        save_data_to_github_seguro(df_beneficios, "lista_beneficios.csv", "file_sha_beneficio")
        save_data_to_github_seguro(df_acordos, "lista_acordos.csv", "file_sha_acordo")
        
        st.success("✅ Dados de teste criados com sucesso!")
        st.info(f"""
        **Dados criados:**
        - 📄 **RPV**: 2 processos (Cadastro, Enviado SAC)
        - 🏛️ **Alvarás**: 2 processos (Cadastro, Enviado Rodrigo)
        - 🎯 **Benefícios**: 2 processos (Cadastro, Implantado)
        - 🤝 **Acordos**: 2 processos (Proposto, Aceito) - *Em desenvolvimento*
        
        **Observação:** Módulo de Acordos está em fase de planejamento.
        """)
        
        # Recarregar a página para mostrar os novos dados
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Erro ao criar dados de teste: {str(e)}")

def remover_dados_teste():
    """Remove todos os dados de teste do sistema"""
    try:
        from components.functions_controle import save_data_to_github_seguro
        
        # Carregar dados existentes
        from components.functions_controle import load_data_from_github
        
        df_rpv = load_data_from_github("lista_rpv.csv")
        df_alvaras = load_data_from_github("lista_alvaras.csv")
        df_beneficios = load_data_from_github("lista_beneficios.csv")
        df_acordos = load_data_from_github("lista_acordos.csv")
        
        # Remover dados que contenham "Teste" no nome/parte
        if not df_rpv.empty:
            df_rpv = df_rpv[~df_rpv["Beneficiário"].str.contains("Teste", na=False)]
        if not df_alvaras.empty:
            df_alvaras = df_alvaras[~df_alvaras["Parte"].str.contains("Teste", na=False)]
        if not df_beneficios.empty:
            df_beneficios = df_beneficios[~df_beneficios["PARTE"].str.contains("Teste", na=False)]
        if not df_acordos.empty:
            df_acordos = df_acordos[~df_acordos["Parte"].str.contains("Teste", na=False)]
        
        # Atualizar session_state
        st.session_state.df_editado_rpv = df_rpv
        st.session_state.df_editado_alvara = df_alvaras
        st.session_state.df_editado_beneficio = df_beneficios
        st.session_state.df_editado_acordo = df_acordos
        
        # Salvar no GitHub
        save_data_to_github_seguro(df_rpv, "lista_rpv.csv", "file_sha_rpv")
        save_data_to_github_seguro(df_alvaras, "lista_alvaras.csv", "file_sha_alvara")
        save_data_to_github_seguro(df_beneficios, "lista_beneficios.csv", "file_sha_beneficio")
        save_data_to_github_seguro(df_acordos, "lista_acordos.csv", "file_sha_acordo")
        
        st.success("✅ Dados de teste removidos com sucesso!")
        st.info("🗑️ Todos os processos contendo 'Teste' foram removidos do sistema (RPV, Alvarás, Benefícios e Acordos).")
        
        # Recarregar a página
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Erro ao remover dados de teste: {str(e)}")

st.set_page_config(
    page_title="Capistrano Advogados",
    layout="wide",
    page_icon="⚖️",
    initial_sidebar_state="expanded"
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
        # Converter usuario para lowercase para comparação case-insensitive
        usuario_lower = usuario.lower()
        
        # Procurar o usuário ignorando case
        for usuario_secrets in usuarios:
            if usuario_secrets.lower() == usuario_lower:
                usuario_data = usuarios[usuario_secrets]
                return senha == usuario_data["senha"]
        return False
    except Exception as e:
        st.error(f"Erro na autenticação: {e}")
        return False

def obter_dados_usuario(usuario):
    """Obtém dados completos do usuário autenticado"""
    try:
        usuarios = st.secrets["usuarios"]
        # Converter usuario para lowercase para comparação case-insensitive
        usuario_lower = usuario.lower()
        
        # Procurar o usuário ignorando case
        for usuario_secrets in usuarios:
            if usuario_secrets.lower() == usuario_lower:
                return usuarios[usuario_secrets]
        return None
    except Exception as e:
        st.error(f"Erro ao obter dados do usuário: {e}")
        return None

def limpar_todos_estados_dialogo():
    """Limpa todos os estados de diálogo para evitar reabrir processos automaticamente"""
    estados_para_limpar = [
        "show_alvara_dialog", "processo_aberto_id",
        "show_rpv_dialog", "rpv_aberto_id",
        "show_beneficio_dialog", "beneficio_aberto_id"
    ]
    
    for estado in estados_para_limpar:
        if estado in st.session_state:
            if "show_" in estado:
                st.session_state[estado] = False
            else:
                st.session_state[estado] = None

def mostrar_guia_utilizacao():
    """Mostra o guia de utilização do sistema."""
    st.title("📖 Guia de Utilização")
    
    # Introdução
    st.markdown("""
    ## Bem-vindo ao Sistema de Processos Capistrano!
    
    Este guia fornece instruções detalhadas sobre como utilizar todas as funcionalidades do sistema.
    """)
    
    # Navegação por abas
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏠 Visão Geral",
        "👥 Perfis e Permissões", 
        "📋 Processos",
        "❓ FAQ"
    ])
    
    with tab1:
        st.header("Visão Geral do Sistema")
        st.markdown("""
        ### 🚀 **O que é o Sistema Capistrano?**
        
        O Sistema Capistrano é uma **plataforma web avançada** desenvolvida para gerenciar quatro tipos principais de processos:
        
        - **🏛️ Alvarás**: Processos relacionados a licenças e autorizações administrativas
        - **💰 RPV**: Requisições de Pequeno Valor com análise jurídica
        - **🎯 Benefícios**: Processos de benefícios sociais com **sistema SAC** e **parcelamento em até 12x**
        - **🤝 Acordos**: Acordos judiciais e extrajudiciais (em desenvolvimento)
        
        ### ⭐ **Principais Recursos Avançados**
        
        #### 💳 **Sistema de Pagamento Parcelado**
        - **Parcelamento em até 12x** para processos de benefícios
        - **Controle individual** de cada parcela (Pendente, Pago, Atrasado)
        - **Dashboard financeiro** com métricas detalhadas
        - **Timeline completa** de pagamentos
        
        #### 👥 **Perfil SAC (Customer Service)**
        - **Atendimento especializado** ao cliente
        - **Workflow dedicado** para contato com beneficiários
        - **Integração completa** com o fluxo de benefícios
        
        #### 🔄 **Workflow Inteligente**
        - **Fluxos específicos** para cada tipo de processo
        - **Transições controladas** por perfil de usuário
        - **Histórico completo** de todas as operações
        - **Estados bem definidos** para cada etapa
        
        #### 🔍 **Busca em Tempo Real**
        - **Auto-filtro** que funciona enquanto você digita
        - **Busca por Nome, CPF e Processo**
        - **Resultados instantâneos**
        - **Contador de caracteres** para acompanhar a busca
        """)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                label="📋 Tipos de Processo",
                value="4",
                help="Alvarás, RPV, Benefícios e Acordos"
            )
        with col2:
            st.metric(
                label="👥 Perfis de Usuário", 
                value="5",
                help="Admin, Cadastrador, Administrativo, Financeiro, SAC"
            )
        with col3:
            st.metric(
                label="💳 Parcelas Máximas",
                value="12x",
                help="Sistema de parcelamento para benefícios"
            )
    
    with tab2:
        st.header("Perfis e Permissões")
        
        # Conteúdo dos perfis aqui...
        st.markdown("### Perfis Disponíveis")
        
        # Admin
        st.markdown("#### 🔧 **Admin**")
        st.success("**Acesso Total** - Pode fazer tudo em todos os processos")
        
        # Outros perfis
        perfis_info = {
            "👤 Cadastrador": "Responsável pelo cadastro de novos processos",
            "💰 Financeiro": "Acesso a informações financeiras dos processos", 
            "🏢 Administrativo": "Gerenciamento administrativo geral",
            "📞 SAC": "Atendimento ao cliente - Etapa de contato"
        }
        
        for perfil, descricao in perfis_info.items():
            st.markdown(f"#### {perfil}")
            st.info(descricao)
    
    with tab3:
        st.header("📋 Gerenciamento de Processos")
        
        st.markdown("""
        ### Tipos de Processos
        
        O sistema gerencia quatro categorias principais de processos:
        """)
        
        # Sub-abas para cada tipo de processo
        sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs(["🏛️ Alvarás", "💰 RPV", "🎯 Benefícios", "🤝 Acordos"])
        
        with sub_tab1:
            st.markdown("""
            #### 🏛️ Alvarás - Licenças e Autorizações
            
            **Fluxo do Processo:**
            1. **📝 Cadastrado:** Inserção inicial dos dados do alvará
            2. **💰 Enviado para Financeiro:** Processo enviado para análise financeira
            3. **👔 Enviado para o Chefe:** Aprovação final e autorização
            4. **🎯 Finalizado:** Processo concluído com pagamento registrado
            """)
        
        with sub_tab2:
            st.markdown("""
            #### 💰 RPV - Requisições de Pequeno Valor
            
            **Fluxo do Processo:**
            1. **📝 Cadastro:** Cadastrador registra a requisição inicial
            2. **📋 Status Simultâneos:** SAC e Administrativo trabalham em paralelo
            3. **💰 Validação Financeiro:** Financeiro valida trabalhos
            4. **📤 Enviado para Rodrigo:** Financeiro anexa comprovante
            5. **💳 Aguardando Pagamento:** Financeiro anexa comprovante
            6. **🎉 Finalizado:** RPV processado com timeline completa
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
            """)
        
        with sub_tab4:
            st.markdown("""
            #### 🤝 Acordos - Acordos Judiciais e Extrajudiciais
            
            **Status de Desenvolvimento:** 🚧 **EM PLANEJAMENTO**
            
            **Fluxo Previsto do Processo:**
            1. **📝 Proposto:** Criação da proposta de acordo
            2. **🤝 Negociação:** Processo em fase de negociação
            3. **✅ Aceito:** Acordo aceito pelas partes
            4. **📋 Em Cumprimento:** Acordo sendo cumprido
            5. **🎯 Cumprido:** Acordo totalmente cumprido
            6. **❌ Descumprido:** Acordo não cumprido (reiniciar processo)
            
            ⚠️ **Nota:** Este módulo será implementado em versão futura do sistema.
            """)
    
    with tab4:
        st.header("Perguntas Frequentes (FAQ)")
        
        faqs = [
            {
                "pergunta": "❓ Como funciona o auto-filtro de busca?",
                "resposta": """
                **Busca em tempo real implementada:**
                - Digite no campo de busca e os resultados aparecem automaticamente
                - Funciona com **Nomes, CPF e Números de Processo**
                - Contador de caracteres mostra o progresso
                - Disponível em **todos os módulos**: RPV, Alvarás e Benefícios
                """
            },
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
                **SAC (Customer Service)** é o perfil para atendimento ao cliente:
                - **Função**: Fazer contato com beneficiários de processos implantados
                - **Acesso**: Apenas processos de benefícios enviados para SAC
                - **Workflow**: Recebe processos → Faz contato → Marca como contatado → Envia para financeiro
                - **Permissões**: Visualizar processos SAC, marcar como contatado, enviar para financeiro
                """
            },
            {
                "pergunta": "❓ Como acessar dados de teste?",
                "resposta": """
                **Apenas para Administradores:**
                1. Acesse "Configurações" na barra lateral (apenas Admin vê)
                2. Clique em "🧪 Dados de Teste"
                3. Use "Criar Dados de Teste" para gerar exemplos
                4. Use "Remover Dados de Teste" para limpar
                
                **Dados criados incluem:** RPV, Alvarás, Benefícios e estrutura para Acordos
                """
            }
        ]
        
        for faq in faqs:
            with st.expander(faq["pergunta"]):
                st.markdown(faq["resposta"])

if "logado" not in st.session_state:
    st.session_state.logado = False

if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "processo_alvaras"  # Inicia direto na tela de Alvarás

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
                        # Salvar o nome de usuário original para manter case do secrets.toml
                        dados_usuario = obter_dados_usuario(usuario)
                        if dados_usuario:
                            # Encontrar o nome real do usuário no secrets.toml
                            usuarios = st.secrets["usuarios"]
                            usuario_lower = usuario.lower()
                            for usuario_secrets in usuarios:
                                if usuario_secrets.lower() == usuario_lower:
                                    st.session_state.usuario = usuario_secrets  # Nome real do secrets
                                    break
                            
                            st.session_state.nome_completo = dados_usuario.get("nome_completo", usuario)
                            st.session_state.perfil_usuario = dados_usuario.get("perfil", "N/A")
                        else:
                            st.session_state.usuario = usuario
                        
                        # Limpar estados de diálogos ao fazer login para evitar pop-ups automáticos
                        dialogos_para_limpar = [
                            "show_alvara_dialog", "processo_aberto_id",
                            "show_rpv_dialog", "rpv_aberto_id",
                            "show_beneficio_dialog", "beneficio_aberto_id"
                        ]
                        for key in dialogos_para_limpar:
                            if "show_" in key:
                                st.session_state[key] = False
                            else:
                                st.session_state[key] = None
                        
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
            # Só limpar estados se estiver mudando de página
            if st.session_state.get("pagina_atual") != "processo_alvaras":
                limpar_estados_dialogos()
            st.session_state.pagina_atual = "processo_alvaras"
            st.rerun()
        
        if st.button("📄 RPV", key='processo_rpv', use_container_width=True):
            # Só limpar estados se estiver mudando de página
            if st.session_state.get("pagina_atual") != "processo_rpv":
                limpar_estados_dialogos()
            st.session_state.pagina_atual = "processo_rpv"
            st.rerun()
            
        if st.button("📋 Benefícios", key='processo_beneficios', use_container_width=True):
            # Só limpar estados se estiver mudando de página  
            if st.session_state.get("pagina_atual") != "processo_beneficios":
                limpar_estados_dialogos()
            st.session_state.pagina_atual = "processo_beneficios"
            st.rerun()
            
        if st.button("🤝 Acordos", key='processo_acordos', use_container_width=True):
            # Só limpar estados se estiver mudando de página  
            if st.session_state.get("pagina_atual") != "processo_acordos":
                limpar_estados_dialogos()
            st.session_state.pagina_atual = "processo_acordos"
            st.rerun()
    
    # GUIA DE UTILIZAÇÃO
    with st.sidebar.expander("📖 Guia", expanded=False):
        if st.button("📚 Guia de Utilização", key='guia_app', use_container_width=True):
            if st.session_state.get("pagina_atual") != "guia_utilizacao":
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
                if st.session_state.get("pagina_atual") != "config_drive":
                    limpar_estados_dialogos()
                st.session_state.pagina_atual = "config_drive"
                st.rerun()
            
            if st.button("📋 Log de Exclusões", key='log_exclusoes', use_container_width=True):
                if st.session_state.get("pagina_atual") != "log_exclusoes":
                    limpar_estados_dialogos()
                st.session_state.pagina_atual = "log_exclusoes"
                st.rerun()
                
            if st.button("🗂️ Gerenciar Autocomplete", key='gerenciar_autocomplete', use_container_width=True):
                if st.session_state.get("pagina_atual") != "gerenciar_autocomplete":
                    limpar_estados_dialogos()
                st.session_state.pagina_atual = "gerenciar_autocomplete"
                st.rerun()
                
            if st.button("🧪 Dados de Teste", key='dados_teste', use_container_width=True):
                if st.session_state.get("pagina_atual") != "dados_teste":
                    limpar_estados_dialogos()
                st.session_state.pagina_atual = "dados_teste"
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
    elif st.session_state.pagina_atual == "processo_acordos":
        from processos import lista_acordos
        lista_acordos.show()
    elif st.session_state.pagina_atual == "config_drive":
        from configuracao_drive import interface_configuracao_drive
        interface_configuracao_drive()
    elif st.session_state.pagina_atual == "log_exclusoes":
        from components.log_exclusoes import visualizar_log_exclusoes
        visualizar_log_exclusoes()
    elif st.session_state.pagina_atual == "gerenciar_autocomplete":
        from components.gerenciar_autocomplete import interface_gerenciamento_autocomplete
        interface_gerenciamento_autocomplete()
    elif st.session_state.pagina_atual == "dados_teste":
        # Página de dados de teste (apenas para Admin)
        st.header("🧪 Dados de Teste")

        st.warning("⚠️ Esta seção é destinada para testes e desenvolvimento. Use com cuidado!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("➕ Criar Dados de Teste", type="primary", key="criar_teste_admin"):
                criar_dados_teste()
            
        with col2:
            if st.button("🗑️ Remover Dados de Teste", type="secondary", key="remover_teste_admin"):
                remover_dados_teste()
        
        st.markdown("""
        ⚠️ Dados de teste são identificados pela palavra "Teste" no nome/parte.
        """)
    elif st.session_state.pagina_atual == "guia_utilizacao":
        mostrar_guia_utilizacao()
