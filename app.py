import streamlit as st
import pandas as pd
import uuid
from datetime import datetime

# Funções para dados de teste
def criar_dados_teste(quantidade_por_tipo=2, incluir_multiplos_status=True):
    """
    Cria dados de exemplo para todos os tipos de processo e status
    
    Args:
        quantidade_por_tipo (int): Quantidade de processos por tipo (padrão: 2)
        incluir_multiplos_status (bool): Se deve incluir processos com status variados (padrão: True)
    """
    try:
        # Importar as funções necessárias
        from components.functions_controle import save_data_to_github_seguro, load_data_from_github
        
        # Verificar se já existem dados de teste
        try:
            df_rpv_existente, _ = load_data_from_github("lista_rpv.csv")
            df_alvaras_existente, _ = load_data_from_github("lista_alvaras.csv")
            df_beneficios_existente, _ = load_data_from_github("lista_beneficios.csv")
            df_acordos_existente, _ = load_data_from_github("lista_acordos.csv")
            
            # Contar quantos dados de teste já existem
            teste_rpv = len(df_rpv_existente[df_rpv_existente["Beneficiário"].str.contains("Teste", na=False)]) if not df_rpv_existente.empty else 0
            teste_alvaras = len(df_alvaras_existente[df_alvaras_existente["Parte"].str.contains("Teste", na=False)]) if not df_alvaras_existente.empty else 0
            teste_beneficios = len(df_beneficios_existente[df_beneficios_existente["PARTE"].str.contains("Teste", na=False)]) if not df_beneficios_existente.empty else 0
            teste_acordos = len(df_acordos_existente[df_acordos_existente["Nome_Cliente"].str.contains("Teste", na=False) | 
                                                    df_acordos_existente["Nome_Reu"].str.contains("Teste", na=False)]) if not df_acordos_existente.empty else 0
            
            if teste_rpv > 0 or teste_alvaras > 0 or teste_beneficios > 0 or teste_acordos > 0:
                st.warning(f"""
                ⚠️ **Dados de teste já existem no sistema:**
                - RPV: {teste_rpv} processos
                - Alvarás: {teste_alvaras} processos
                - Benefícios: {teste_beneficios} processos
                - Acordos: {teste_acordos} processos
                
                Para evitar duplicação, remova os dados existentes antes de criar novos.
                """)
                return
                
        except Exception:
            # Se não conseguir verificar, continuar
            pass
        
        # Lista de status variados para testar diferentes fluxos
        if incluir_multiplos_status:
            status_rpv = ["Cadastro", "SAC - aguardando documentação", "Enviado para Rodrigo", "finalizado"]
            status_alvaras = ["Cadastrado", "Enviado para o Financeiro", "Financeiro - Enviado para Rodrigo", "Finalizado"]
            status_beneficios = ["Cadastro", "Aguardando Documentos", "Implantado", "Finalizado"]
            status_acordos = ["Aguardando Pagamento", "Enviado para Financeiro", "Recebido", "Finalizado"]
        else:
            status_rpv = ["Cadastro"]
            status_alvaras = ["Cadastrado"] 
            status_beneficios = ["Cadastro"]
            status_acordos = ["Aguardando Pagamento"]
        
        # Nomes de teste variados
        nomes_teste = [
            "João da Silva Teste", "Maria dos Santos Teste", "Pedro Oliveira Teste",
            "Ana Costa Teste", "Carlos Mendes Teste", "Lucia Santos Teste",
            "Roberto Silva Teste", "Sandra Costa Teste", "Fernando Lima Teste",
            "Patricia Souza Teste"
        ]
        
        # CPFs de teste válidos
        cpfs_teste = [
            "123.456.789-01", "987.654.321-09", "456.789.123-45", "789.123.456-78",
            "321.654.987-12", "654.987.321-65", "111.222.333-44", "555.666.777-88",
            "999.888.777-66", "333.444.555-22"
        ]
        
        # ===== DADOS DE TESTE RPV =====
        dados_rpv_teste = []
        
        for i in range(min(quantidade_por_tipo, len(nomes_teste))):
            dados_rpv_teste.append({
                "ID": str(uuid.uuid4()),
                "Processo": f"000{1000+i}-{56+i}.2024.5.02.000{1+i}",
                "Beneficiário": nomes_teste[i],
                "CPF": cpfs_teste[i],
                "Descricao RPV": f"Processo trabalhista - teste {i+1}",
                "Assunto": "TRABALHISTA" if i % 2 == 0 else "PREVIDENCIARIO",
                "Orgao Judicial": "TRT 2ª Região" if i % 2 == 0 else "TRF 5ª Região",
                "Vara": f"{i+1}ª Vara do Trabalho",
                "Banco": "CEF" if i % 2 == 0 else "BB",
                "Agência": f"{1234+i}",
                "Conta": f"{56789+i}-{i}",
                "Mês Competência": f"{9+i:02d}/2024",
                "Solicitar Certidão": "Sim" if i % 2 == 0 else "Não",
                "Observações": f"Processo de teste {i+1} - RPV",
                "Status": status_rpv[i % len(status_rpv)],
                "Cadastrado por": "admin",
                "Data de Cadastro": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "Observações Honorários": f"Observações de teste {i+1}",
                "Valor Cliente": float(1000 + (i * 500)),
                "Honorarios Contratuais": float(300 + (i * 100)),
                "Valor Saque": float(1500 + (i * 600))
            })
        
        # ===== DADOS DE TESTE ALVARÁS =====
        dados_alvaras_teste = []
        
        for i in range(min(quantidade_por_tipo, len(nomes_teste))):
            dados_alvaras_teste.append({
                "ID": str(uuid.uuid4()),
                "Processo": f"000{3000+i}-{78+i}.2024.8.26.000{1+i}",
                "Parte": nomes_teste[i],
                "CPF": cpfs_teste[i],
                "Advogado": f"Dr. Advogado {i+1}",
                "Descricao Alvara": f"Alvará judicial - teste {i+1}",
                "Valor": f"R$ {15000 + (i * 5000):.2f}",
                "Banco": "CEF" if i % 2 == 0 else "BB",
                "Agência": f"{9000+i}",
                "Conta": f"{80000+i}-{i}",
                "Obs Gerais": f"Alvará de teste {i+1}",
                "Status": status_alvaras[i % len(status_alvaras)],
                "Cadastrado por": "admin",
                "Data de Cadastro": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            })
        
        # ===== DADOS DE TESTE BENEFÍCIOS =====
        dados_beneficios_teste = []
        
        for i in range(min(quantidade_por_tipo, len(nomes_teste))):
            dados_beneficios_teste.append({
                "ID": str(uuid.uuid4()),
                "Nº DO PROCESSO": f"000{5000+i}-{90+i}.2024.8.26.000{3+i}",
                "PARTE": nomes_teste[i],
                "CPF": cpfs_teste[i],
                "DETALHE PROCESSO": f"Benefício previdenciário - teste {i+1}",
                "DATA DA CONCESSÃO DA LIMINAR": f"{15+i}/09/2024",
                "VALOR MENSAL": f"R$ {1412 + (i * 200):.2f}",
                "VALOR RETROATIVO": f"R$ {8472 + (i * 1000):.2f}",
                "TOTAL GERAL": f"R$ {9884 + (i * 1200):.2f}",
                "VALOR DE HONORÁRIOS": f"R$ {2471 + (i * 300):.2f}",
                "STATUS": status_beneficios[i % len(status_beneficios)],
                "Cadastrado por": "admin",
                "Data de Cadastro": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            })
        
        # ===== DADOS DE TESTE ACORDOS =====
        dados_acordos_teste = []
        
        for i in range(min(quantidade_por_tipo, len(nomes_teste))):
            dados_acordos_teste.append({
                "ID": str(uuid.uuid4()),
                "Processo": f"000{7000+i}-{12+i}.2024.8.26.000{5+i}",
                "Nome_Reu": f"Empresa {i+1} Ltda Teste",
                "CPF_Reu": f"{12+i:02d}.{345+i:03d}.{678+i:03d}/0001-{90+i:02d}",
                "Nome_Cliente": nomes_teste[i],
                "CPF_Cliente": cpfs_teste[i],
                "Banco": "CEF" if i % 2 == 0 else "BB",
                "Valor_Total": float(25000 + (i * 10000)),
                "Forma_Acordo": "Judicial" if i % 2 == 0 else "Extrajudicial",
                "A_Vista": i % 3 == 0,  # Alguns à vista
                "Num_Parcelas": 1 if i % 3 == 0 else (i + 3),  # Varia as parcelas
                "Data_Primeiro_Pagamento": f"2024-{10+i:02d}-15",
                "Status": status_acordos[i % len(status_acordos)],
                "Cadastrado_Por": "admin",
                "Data_Cadastro": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "Comprovante_Pago": "",
                "Honorarios_Contratuais": 0.0,
                "Valor_Cliente": 0.0,
                "H_Sucumbenciais": 0.0,
                "Valor_Parceiro": 0.0,
                "Outros_Valores": 0.0,
                "Observacoes": f"Acordo de teste {i+1}",
                "Valor_Atualizado": 0.0,
                "Houve_Renegociacao": False,
                "Nova_Num_Parcelas": 0,
                "Novo_Valor_Parcela": 0.0,
                "Acordo_Nao_Cumprido": False,
                "Data_Ultimo_Update": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "Usuario_Ultimo_Update": "admin"
            })
        
        # Salvar dados nos respectivos arquivos
        df_rpv = pd.DataFrame(dados_rpv_teste)
        df_alvaras = pd.DataFrame(dados_alvaras_teste)
        df_beneficios = pd.DataFrame(dados_beneficios_teste)
        df_acordos = pd.DataFrame(dados_acordos_teste)
        
        # Carregar dados existentes e concatenar
        try:
            df_rpv_existente, _ = load_data_from_github("lista_rpv.csv")
            df_alvaras_existente, _ = load_data_from_github("lista_alvaras.csv")
            df_beneficios_existente, _ = load_data_from_github("lista_beneficios.csv")
            df_acordos_existente, _ = load_data_from_github("lista_acordos.csv")
            
            # Concatenar com dados existentes (se houver)
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
        st.session_state.df_editado_beneficios = df_beneficios
        st.session_state.df_editado_acordos = df_acordos
        
        save_data_to_github_seguro(df_rpv, "lista_rpv.csv", "file_sha_rpv")
        save_data_to_github_seguro(df_alvaras, "lista_alvaras.csv", "file_sha_alvara")
        save_data_to_github_seguro(df_beneficios, "lista_beneficios.csv", "file_sha_beneficio")
        save_data_to_github_seguro(df_acordos, "lista_acordos.csv", "file_sha_acordos")
        
        st.success("✅ Dados de teste criados com sucesso!")
        
        # Mensagem personalizada baseada na quantidade
        if quantidade_por_tipo <= 2:
            st.info(f"""
            **📊 Resumo dos dados criados (BÁSICO):**
            - 📄 **RPV**: {quantidade_por_tipo} processos com status variados
            - 🏛️ **Alvarás**: {quantidade_por_tipo} processos em diferentes etapas
            - 🎯 **Benefícios**: {quantidade_por_tipo} processos previdenciários 
            - 🤝 **Acordos**: {quantidade_por_tipo} acordos com diferentes formas de pagamento
            
            **✨ Melhorias implementadas:**
            - ✅ Evita criação duplicada
            - ✅ Status variados para teste completo
            - ✅ Dados mais realistas
            - ✅ Campo Banco corrigido em Alvarás (dropdown BB/CEF)
            """)
        else:
            st.info(f"""
            **📊 Resumo dos dados criados (AMPLIADO):**
            - 📄 **RPV**: {quantidade_por_tipo} processos com status: {', '.join(status_rpv)}
            - 🏛️ **Alvarás**: {quantidade_por_tipo} processos com status: {', '.join(status_alvaras)}
            - 🎯 **Benefícios**: {quantidade_por_tipo} processos com status: {', '.join(status_beneficios)}
            - 🤝 **Acordos**: {quantidade_por_tipo} acordos com status: {', '.join(status_acordos)}
            
            **✨ Ideal para testar fluxos complexos!**
            """)
        
        # Recarregar a página para mostrar os novos dados
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Erro ao criar dados de teste: {str(e)}")
        st.info("💡 Tente reduzir a quantidade ou verificar se há conflitos nos dados existentes.")

def remover_dados_teste():
    """Remove todos os dados de teste do sistema"""
    try:
        from components.functions_controle import save_data_to_github_seguro
        
        # Carregar dados existentes
        from components.functions_controle import load_data_from_github
        
        df_rpv, _ = load_data_from_github("lista_rpv.csv")
        df_alvaras, _ = load_data_from_github("lista_alvaras.csv")
        df_beneficios, _ = load_data_from_github("lista_beneficios.csv")
        df_acordos, _ = load_data_from_github("lista_acordos.csv")
        
        # Remover dados que contenham "Teste" no nome/parte
        if not df_rpv.empty:
            df_rpv = df_rpv[~df_rpv["Beneficiário"].str.contains("Teste", na=False)]
        if not df_alvaras.empty:
            df_alvaras = df_alvaras[~df_alvaras["Parte"].str.contains("Teste", na=False)]
        if not df_beneficios.empty:
            df_beneficios = df_beneficios[~df_beneficios["PARTE"].str.contains("Teste", na=False)]
        if not df_acordos.empty:
            # Para acordos, verificar tanto cliente quanto réu
            df_acordos = df_acordos[
                ~(df_acordos["Nome_Cliente"].str.contains("Teste", na=False) | 
                  df_acordos["Nome_Reu"].str.contains("Teste", na=False))
            ]
        
        # Atualizar session_state
        st.session_state.df_editado_rpv = df_rpv
        st.session_state.df_editado_alvara = df_alvaras
        st.session_state.df_editado_beneficios = df_beneficios
        st.session_state.df_editado_acordos = df_acordos
        
        # Salvar no GitHub
        save_data_to_github_seguro(df_rpv, "lista_rpv.csv", "file_sha_rpv")
        save_data_to_github_seguro(df_alvaras, "lista_alvaras.csv", "file_sha_alvara")
        save_data_to_github_seguro(df_beneficios, "lista_beneficios.csv", "file_sha_beneficio")
        save_data_to_github_seguro(df_acordos, "lista_acordos.csv", "file_sha_acordos")
        
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
                help="Desenvolvedor, Cadastrador, Administrativo, Financeiro, SAC"
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
        
        # Desenvolvedor
        st.markdown("#### 🔧 **Desenvolvedor**")
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
            3. **�‍💼 Financeiro - Enviado para Rodrigo:** Aprovação final e autorização
            4. **🎯 Finalizado:** Processo concluído com comprovante de pagamento
            
            **Campos obrigatórios no cadastro:**
            - Número do Processo
            - Parte (nome completo)
            - CPF
            - Valor do Pagamento
            - Órgão Judicial
            
            **Campos opcionais:**
            - Conta bancária
            - Agência bancária
            - Observações sobre o pagamento
            - Honorários Sucumbenciais (Sim/Não)
            - Observações sobre honorários
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
                **Apenas para Desenvolvedores:**
                1. Acesse "Configurações" na barra lateral (apenas Desenvolvedor vê)
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
    
    # CONFIGURAÇÕES - APENAS PARA DESENVOLVEDOR
    perfil_usuario = st.session_state.get("perfil_usuario", "N/A")
    usuario_atual = st.session_state.get("usuario", "")
    
    # Verificar se é Desenvolvedor
    is_admin = (perfil_usuario == "Desenvolvedor" or usuario_atual == "dev")
    
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
        # Página de dados de teste (apenas para Desenvolvedor)
        st.header("🧪 Dados de Teste - VERSÃO MELHORADA")

        st.warning("⚠️ Esta seção é destinada para testes e desenvolvimento. Use com cuidado!")
        
        # Seção de configuração de testes
        st.subheader("⚙️ Configurações de Teste")
        
        col_config1, col_config2 = st.columns(2)
        
        with col_config1:
            quantidade = st.slider(
                "📊 Quantidade de processos por tipo:",
                min_value=1, 
                max_value=10, 
                value=3,
                help="Quantidade de processos de cada tipo que será criada"
            )
            
        with col_config2:
            incluir_multiplos = st.checkbox(
                "🔄 Incluir múltiplos status",
                value=True,
                help="Se marcado, cria processos com status variados para testar diferentes fluxos"
            )
        
        st.markdown("---")
        
        # Botões de ação
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("➕ Criar Dados de Teste", type="primary", key="criar_teste_admin"):
                criar_dados_teste(quantidade_por_tipo=quantidade, incluir_multiplos_status=incluir_multiplos)
            
        with col2:
            if st.button("🗑️ Remover Dados de Teste", type="secondary", key="remover_teste_admin"):
                remover_dados_teste()
        
        # Informações sobre as melhorias
        with st.expander("✨ Novidades nesta versão", expanded=False):
            st.markdown("""
            **🎯 Melhorias Implementadas:**
            
            **1. Campo Banco corrigido em Alvarás:**
            - ✅ Agora usa dropdown com opções BB e CEF (igual ao RPV)
            - ❌ Antes: campo de texto livre
            
            **2. Funcionalidade de teste melhorada:**
            - ✅ Controle de quantidade personalizável (1-10 processos)
            - ✅ Opção de incluir status variados para teste completo
            - ✅ Validação para evitar criação duplicada
            - ✅ Dados mais realistas e variados
            - ✅ Mensagens de feedback aprimoradas
            - ✅ Melhor tratamento de erros
            
            **3. Variedade de dados de teste:**
            - 📄 **RPV**: Status desde Cadastro até Finalizado
            - 🏛️ **Alvarás**: Fluxo completo Cadastrado → Finalizado  
            - 🎯 **Benefícios**: Diferentes estágios previdenciários
            - 🤝 **Acordos**: Várias formas de pagamento e parcelamento
            """)
        
        st.markdown("""
        ---
        **💡 Dica:** Dados de teste são identificados pela palavra "**Teste**" no nome/parte e podem ser removidos com segurança.
        
        **⚠️ Atenção:** O sistema previne criação duplicada - remova os dados existentes antes de criar novos.
        """)
        
    elif st.session_state.pagina_atual == "guia_utilizacao":
        mostrar_guia_utilizacao()
