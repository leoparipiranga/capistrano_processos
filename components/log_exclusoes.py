import streamlit as st
import pandas as pd
from datetime import datetime
import os
from components.google_drive_integration import upload_log_to_drive

def should_create_backup(df_log):
    """
    Determina se deve criar um backup automático baseado em critérios:
    - A cada 5 exclusões
    - Uma vez por dia
    - Se nunca foi feito backup
    """
    try:
        # Verificar último backup
        arquivo_backup_info = "last_backup.txt"
        hoje = datetime.now().strftime("%Y-%m-%d")
        
        if os.path.exists(arquivo_backup_info):
            with open(arquivo_backup_info, 'r') as f:
                content = f.read().strip()
                if content:
                    ultimo_backup_data, ultimo_backup_count = content.split(',')
                    
                    # Se já fez backup hoje, só criar novo a cada 5 exclusões
                    if ultimo_backup_data == hoje:
                        current_count = len(df_log)
                        last_count = int(ultimo_backup_count)
                        return (current_count - last_count) >= 5
                    else:
                        # Novo dia, deve fazer backup
                        return True
        
        # Primeira vez ou arquivo corrompido, deve fazer backup
        return True
        
    except Exception:
        # Em caso de erro, sempre fazer backup por segurança
        return True

def save_last_backup_timestamp():
    """Salva informações do último backup"""
    try:
        arquivo_backup_info = "last_backup.txt"
        hoje = datetime.now().strftime("%Y-%m-%d")
        
        # Contar quantas exclusões temos atualmente
        arquivo_log = "log_exclusoes.csv"
        caminho_local = os.path.join(os.getcwd(), arquivo_log)
        
        if os.path.exists(caminho_local):
            df_log = pd.read_csv(caminho_local)
            count = len(df_log)
        else:
            count = 0
        
        with open(arquivo_backup_info, 'w') as f:
            f.write(f"{hoje},{count}")
            
    except Exception:
        pass  # Falha silenciosa, não é crítica

def registrar_exclusao(tipo_processo, processo_numero, dados_excluidos, usuario):
    """
    Registra uma exclusão no log
    
    Args:
        tipo_processo: "Alvará", "RPV" ou "Benefício"
        processo_numero: Número do processo excluído
        dados_excluidos: Dados completos do registro excluído
        usuario: Usuário que realizou a exclusão
    """
    try:
        # Criar entrada do log
        log_entry = {
            "Data_Exclusao": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "Usuario": usuario,
            "Tipo_Processo": tipo_processo,
            "Numero_Processo": processo_numero,
            "Beneficiario": dados_excluidos.get("Beneficiário", "N/A"),
            "CPF": dados_excluidos.get("CPF", "N/A"),
            "Status": dados_excluidos.get("Status", "N/A"),
            "Valor": dados_excluidos.get("Valor", "N/A"),
            "Dados_Completos": str(dados_excluidos.to_dict() if hasattr(dados_excluidos, 'to_dict') else dados_excluidos)
        }
        
        # Nome do arquivo de log
        arquivo_log = "log_exclusoes.csv"
        caminho_local = os.path.join(os.getcwd(), arquivo_log)
        
        # Verificar if arquivo existe
        if os.path.exists(caminho_local):
            # Carregar log existente
            df_log = pd.read_csv(caminho_local)
            # Adicionar nova entrada
            df_log = pd.concat([df_log, pd.DataFrame([log_entry])], ignore_index=True)
        else:
            # Criar novo log
            df_log = pd.DataFrame([log_entry])
        
        # Salvar localmente
        df_log.to_csv(caminho_local, index=False)
        
        # Log foi salvo localmente com sucesso - isso é o principal
        log_salvo_com_sucesso = True
        
        # Tentar criar backup no Drive apenas a cada 5 exclusões ou uma vez por dia
        deve_fazer_backup = should_create_backup(df_log)
        
        if deve_fazer_backup:
            # Tentar enviar para o Google Drive (não crítico)
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                nome_backup = f"log_exclusoes_auto_{timestamp}.csv"
                
                upload_result = upload_log_to_drive(
                    arquivo_local=caminho_local,
                    nome_arquivo=nome_backup
                )
                
                if upload_result:
                    st.success(f"📝 Exclusão registrada e backup automático criado: {tipo_processo} - {processo_numero}")
                    # Salvar timestamp do último backup
                    save_last_backup_timestamp()
                else:
                    st.warning("📝 Exclusão registrada localmente. Falha no backup automático.")
                    
            except Exception as e:
                st.warning(f"📝 Exclusão registrada localmente. Erro no backup: {str(e)}")
        else:
            st.success(f"📝 Exclusão registrada: {tipo_processo} - {processo_numero}")
            
        return log_salvo_com_sucesso
            
    except Exception as e:
        st.error(f"❌ Erro ao registrar exclusão: {str(e)}")
        return False

def criar_backup_completo_logs():
    """
    Cria um backup completo dos logs no Google Drive
    Útil para ser executado periodicamente ou manualmente
    """
    try:
        arquivo_log = "log_exclusoes.csv"
        caminho_local = os.path.join(os.getcwd(), arquivo_log)
        
        if not os.path.exists(caminho_local):
            st.warning("📁 Nenhum log local encontrado para backup.")
            return False
        
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_backup = f"log_exclusoes_backup_{timestamp}.csv"
        
        with st.spinner("☁️ Criando backup dos logs no Google Drive..."):
            sucesso = upload_log_to_drive(caminho_local, nome_backup)
        
        if sucesso:
            st.success(f"✅ Backup criado com sucesso: {nome_backup}")
            return True
        else:
            st.error("❌ Falha ao criar backup no Drive.")
            return False
            
    except Exception as e:
        st.error(f"❌ Erro ao criar backup: {str(e)}")
        return False

def sincronizar_logs_com_drive():
    """
    Sincroniza todos os logs locais com o Google Drive
    Útil para migração inicial ou recuperação
    """
    try:
        arquivo_log = "log_exclusoes.csv"
        caminho_local = os.path.join(os.getcwd(), arquivo_log)
        
        if not os.path.exists(caminho_local):
            st.warning("📁 Nenhum log local encontrado para sincronizar.")
            return
        
        st.info("🔄 Iniciando sincronização completa com Google Drive...")
        
        # Criar backup principal
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_principal = f"log_exclusoes_sync_{timestamp}.csv"
        
        with st.spinner("☁️ Enviando logs para Google Drive..."):
            sucesso_principal = upload_log_to_drive(caminho_local, nome_principal)
        
        if sucesso_principal:
            st.success(f"✅ Sincronização concluída: {nome_principal}")
            
            # Atualizar informações de backup
            save_last_backup_timestamp()
            
            # Mostrar estatísticas
            df_log = pd.read_csv(caminho_local)
            st.info(f"📊 Total de {len(df_log)} registros sincronizados")
            
        else:
            st.error("❌ Falha na sincronização.")
            
    except Exception as e:
        st.error(f"❌ Erro na sincronização: {str(e)}")

def test_log_system():
    """Função para testar o sistema de logs"""
    st.info("🧪 Iniciando teste do sistema de logs...")
    
    # Teste 1: Verificar se consegue criar entrada no log
    try:
        dados_teste = {
            "Processo": "0000000-00.0000.0.00.0000",
            "Beneficiário": "Teste Sistema",
            "CPF": "000.000.000-00",
            "Status": "Teste",
            "Valor": "R$ 1.000,00"
        }
        
        st.write("📝 Teste 1: Criando entrada de log...")
        sucesso = registrar_exclusao(
            tipo_processo="Teste",
            processo_numero="TESTE-001",
            dados_excluidos=dados_teste,
            usuario="Sistema-Teste"
        )
        
        if sucesso:
            st.success("✅ Teste 1: Log criado com sucesso!")
        else:
            st.error("❌ Teste 1: Falha ao criar log")
            
    except Exception as e:
        st.error(f"❌ Teste 1 falhou: {str(e)}")
    
    # Teste 2: Verificar se arquivo foi criado
    try:
        arquivo_log = "log_exclusoes.csv"
        caminho_local = os.path.join(os.getcwd(), arquivo_log)
        
        st.write("📁 Teste 2: Verificando arquivo local...")
        if os.path.exists(caminho_local):
            st.success(f"✅ Teste 2: Arquivo existe em {caminho_local}")
            
            # Mostrar conteúdo
            df_log = pd.read_csv(caminho_local)
            st.info(f"📊 Arquivo contém {len(df_log)} registro(s)")
            
            if len(df_log) > 0:
                st.dataframe(df_log.tail(3))
        else:
            st.error("❌ Teste 2: Arquivo não encontrado")
            
    except Exception as e:
        st.error(f"❌ Teste 2 falhou: {str(e)}")
    
    # Teste 3: Teste de conexão com Google Drive
    try:
        st.write("☁️ Teste 3: Testando Google Drive...")
        from components.google_drive_integration import GoogleDriveIntegration
        
        drive = GoogleDriveIntegration()
        sucesso_drive, msg_drive = drive.test_connection()
        
        if sucesso_drive:
            st.success(f"✅ Teste 3: {msg_drive}")
        else:
            st.warning(f"⚠️ Teste 3: {msg_drive}")
            
    except Exception as e:
        st.error(f"❌ Teste 3 falhou: {str(e)}")

def visualizar_log_exclusoes():
    """Interface para visualizar o log de exclusões"""
    st.header("📋 Log de Exclusões")
    
    # Botão de teste para debug
    col_test, col_info = st.columns([1, 3])
    with col_test:
        if st.button("🧪 Teste do Sistema", help="Testa as funções de log"):
            test_log_system()
    
    with col_info:
        st.info(" Use o botão de teste para verificar se o sistema está funcionando corretamente.")
    
    st.markdown("---")
    
    arquivo_log = "log_exclusoes.csv"
    caminho_local = os.path.join(os.getcwd(), arquivo_log)
    
    if os.path.exists(caminho_local):
        try:
            df_log = pd.read_csv(caminho_local)
            
            if not df_log.empty:
                # Informações de status dos backups
                col_info1, col_info2 = st.columns(2)
                
                with col_info1:
                    st.success(f"📊 Total de exclusões registradas: {len(df_log)}")
                
                with col_info2:
                    # Verificar status do último backup
                    arquivo_backup_info = "last_backup.txt"
                    if os.path.exists(arquivo_backup_info):
                        with open(arquivo_backup_info, 'r') as f:
                            content = f.read().strip()
                            if content:
                                ultimo_backup_data, ultimo_backup_count = content.split(',')
                                st.info(f"🔄 Último backup: {ultimo_backup_data} ({ultimo_backup_count} registros)")
                            else:
                                st.warning("⚠️ Nenhum backup no Drive ainda")
                    else:
                        st.warning("⚠️ Nenhum backup no Drive ainda")
                
                # Botões de ação
                col_backup, col_sync, col_download, _ = st.columns([2, 2, 2, 4])
                
                with col_backup:
                    if st.button("☁️ Backup Manual", help="Cria backup pontual no Google Drive"):
                        criar_backup_completo_logs()
                
                with col_sync:
                    if st.button("🔄 Sincronizar Tudo", help="Sincroniza todos os logs com o Drive"):
                        sincronizar_logs_com_drive()
                
                with col_download:
                    csv_completo = df_log.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Local",
                        data=csv_completo,
                        file_name=f"log_exclusoes_local_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        help="Baixa cópia local dos logs"
                    )
                
                st.markdown("---")
                
                # Filtros
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    filtro_tipo = st.selectbox(
                        "Filtrar por tipo:",
                        ["Todos"] + list(df_log["Tipo_Processo"].unique())
                    )
                
                with col2:
                    filtro_usuario = st.selectbox(
                        "Filtrar por usuário:",
                        ["Todos"] + list(df_log["Usuario"].unique())
                    )
                
                with col3:
                    filtro_data = st.date_input("Filtrar por data:")
                
                # Aplicar filtros
                df_filtrado = df_log.copy()
                
                if filtro_tipo != "Todos":
                    df_filtrado = df_filtrado[df_filtrado["Tipo_Processo"] == filtro_tipo]
                    
                if filtro_usuario != "Todos":
                    df_filtrado = df_filtrado[df_filtrado["Usuario"] == filtro_usuario]
                
                if filtro_data:
                    data_str = filtro_data.strftime("%d/%m/%Y")
                    df_filtrado = df_filtrado[df_filtrado["Data_Exclusao"].str.contains(data_str)]
                
                # Mostrar resultados
                st.dataframe(
                    df_filtrado[["Data_Exclusao", "Usuario", "Tipo_Processo", "Numero_Processo", "Beneficiario", "Status"]],
                    use_container_width=True
                )
                
                # Botão para download
                csv = df_filtrado.to_csv(index=False)
                st.download_button(
                    label="📥 Baixar log filtrado",
                    data=csv,
                    file_name=f"log_exclusoes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
                
            else:
                st.info("📋 Nenhuma exclusão registrada ainda.")
                
        except Exception as e:
            st.error(f"❌ Erro ao carregar log: {str(e)}")
    else:
        st.info("📋 Arquivo de log não encontrado. Nenhuma exclusão foi registrada ainda.")

def confirmar_exclusao_com_log(tipo_processo, processo_numero, dados_processo, usuario):
    """
    Interface para confirmar exclusão com registro automático no log
    
    Returns:
        bool: True se a exclusão foi confirmada
    """
    st.warning(f"⚠️ Você está prestes a excluir o {tipo_processo}: **{processo_numero}**")
    
    # Mostrar dados do processo
    with st.expander("👁️ Ver dados do processo"):
        if hasattr(dados_processo, 'to_dict'):
            for key, value in dados_processo.to_dict().items():
                st.text(f"{key}: {value}")
        else:
            st.json(dados_processo)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("❌ Confirmar Exclusão", type="primary", key=f"confirmar_exclusao_{processo_numero}"):
            # Registrar no log
            sucesso_log = registrar_exclusao(tipo_processo, processo_numero, dados_processo, usuario)
            
            if sucesso_log:
                st.success("✅ Processo excluído e registrado no log!")
            else:
                st.warning("⚠️ Processo excluído, mas houve problema no registro do log.")
            
            return True
    
    with col2:
        if st.button("🚫 Cancelar", key=f"cancelar_exclusao_{processo_numero}"):
            st.info("🚫 Exclusão cancelada.")
            return False
    
    return False
