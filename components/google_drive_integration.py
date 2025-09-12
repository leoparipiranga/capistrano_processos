"""
Módulo para integração com Google Drive
Funcionalidades:
- Upload de arquivos para pasta específica
- Autenticação OAuth 2.0
- Organização por pastas de processos
"""

import os
import io
import streamlit as st
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime

# Permitir HTTP local para desenvolvimento OAuth
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


class GoogleDriveIntegration:
    """Classe para gerenciar integração com Google Drive"""
    
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/drive.file']
        self.credentials = None
        self.service = None
        
    def get_credentials(self):
        """Obter credenciais do Google Drive com renovação automática de tokens"""
        try:
            if "google_drive" not in st.secrets:
                st.error("❌ Configuração google_drive não encontrada")
                return False
                
            creds_info = dict(st.secrets["google_drive"])
            
            # Campos obrigatórios
            required_fields = ['client_id', 'client_secret', 'refresh_token']
            missing_fields = [field for field in required_fields if field not in creds_info]
            
            if missing_fields:
                st.error(f"❌ Campos obrigatórios ausentes: {missing_fields}")
                return False
            
            # Criar credenciais com refresh token
            creds_data = {
                'client_id': creds_info['client_id'],
                'client_secret': creds_info['client_secret'],
                'refresh_token': creds_info['refresh_token'],
                'token_uri': creds_info.get('token_uri', 'https://oauth2.googleapis.com/token')
            }
            
            # Incluir token atual se existir (opcional)
            if 'token' in creds_info:
                creds_data['token'] = creds_info['token']
            
            # Criar objeto de credenciais
            self.credentials = Credentials.from_authorized_user_info(creds_data, self.SCOPES)
            
            # IMPORTANTE: Renovar automaticamente se necessário
            if not self.credentials.valid:
                if self.credentials.expired and self.credentials.refresh_token:
                    try:
                        self.credentials.refresh(Request())
                        st.info("🔄 Token renovado automaticamente")
                    except Exception as refresh_error:
                        st.error(f"❌ Erro ao renovar token: {refresh_error}")
                        st.error(" Dica: Gere um novo refresh token na aba 'Configurações'")
                        return False
                else:
                    st.error("❌ Token inválido e sem refresh token")
                    return False
            
            return True
                
        except Exception as e:
            st.error(f"❌ Erro ao obter credenciais: {e}")
            return False
            
        except Exception as e:
            st.error(f"❌ Erro nas credenciais: {str(e)}")
            return False
    
    def initialize_service(self):
        """Inicializar serviço do Google Drive"""
        if not self.get_credentials():
            return False
            
        try:
            self.service = build('drive', 'v3', credentials=self.credentials)
            return True
        except Exception as e:
            print(f"Erro ao inicializar serviço do Google Drive: {str(e)}")
            return False
    
    def create_folder(self, folder_name, parent_folder_id=None):
        """Criar pasta no Google Drive"""
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]
                
            folder = self.service.files().create(body=file_metadata).execute()
            return folder.get('id')
        except Exception as e:
            # Log mais detalhado do erro
            print(f"Erro ao criar pasta '{folder_name}': {str(e)}")
            return None
    
    def find_folder(self, folder_name, parent_folder_id=None):
        """Buscar pasta no Google Drive"""
        try:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
            if parent_folder_id:
                query += f" and '{parent_folder_id}' in parents"
                
            results = self.service.files().list(q=query).execute()
            items = results.get('files', [])
            
            if items:
                return items[0]['id']
            return None
        except Exception:
            return None
    
    def upload_file(self, file_content, file_name, folder_id=None, mime_type='application/pdf'):
        """Upload de arquivo para Google Drive"""
        try:
            file_metadata = {'name': file_name}
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            if isinstance(file_content, bytes):
                media = MediaIoBaseUpload(io.BytesIO(file_content), mimetype=mime_type)
            else:
                media = MediaIoBaseUpload(io.BytesIO(file_content.read()), mimetype=mime_type)
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media
            ).execute()
            
            return file.get('id'), file.get('name')
        except Exception as e:
            print(f"Erro no upload do arquivo '{file_name}': {str(e)}")
            return None, None
    
    def upload_alvara_documents(self, processo, comprovante_file, pdf_file):
        """Upload específico para documentos de alvará"""
        if not self.initialize_service():
            return False, "Erro na inicialização do Google Drive"
        
        try:
            main_folder_id = st.secrets.get("google_drive", {}).get("alvaras_folder_id")
            if not main_folder_id:
                return False, "Pasta principal não configurada"
            
            # Criar ou encontrar pasta do processo
            processo_folder_name = f"Processo_{processo}"
            processo_folder_id = self.find_folder(processo_folder_name, main_folder_id)
            
            if not processo_folder_id:
                processo_folder_id = self.create_folder(processo_folder_name, main_folder_id)
                if not processo_folder_id:
                    return False, "Erro ao criar pasta do processo"
            
            # Upload dos arquivos
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            comprovante_name = f"{processo}_comprovante_{timestamp}_{comprovante_file.name}"
            pdf_name = f"{processo}_alvara_{timestamp}_{pdf_file.name}"
            
            comprovante_id, _ = self.upload_file(
                comprovante_file.getvalue(),
                comprovante_name,
                processo_folder_id,
                comprovante_file.type
            )
            
            pdf_id, _ = self.upload_file(
                pdf_file.getvalue(),
                pdf_name,
                processo_folder_id,
                pdf_file.type
            )
            
            if comprovante_id and pdf_id:
                return True, {
                    'comprovante_id': comprovante_id,
                    'comprovante_name': comprovante_name,
                    'pdf_id': pdf_id,
                    'pdf_name': pdf_name,
                    'folder_id': processo_folder_id
                }
            else:
                return False, "Erro no upload dos arquivos"
                
        except Exception as e:
            return False, f"Erro: {str(e)}"
    
    def test_connection(self):
        """Testar conexão com Google Drive"""
        try:
            # Verificar credenciais
            if not self.get_credentials():
                return False, "❌ Credenciais não configuradas ou inválidas"
            
            # Inicializar serviço
            if not self.initialize_service():
                return False, "❌ Erro ao inicializar serviço Google Drive"
            
            # Testar conectividade
            self.service.files().list(pageSize=1).execute()
            
            # Verificar pasta de alvarás
            folder_id = st.secrets.get("google_drive", {}).get("alvaras_folder_id")
            if folder_id:
                try:
                    folder_info = self.service.files().get(fileId=folder_id).execute()
                    return True, f"✅ Google Drive funcionando! Pasta: {folder_info.get('name', 'Alvarás')}"
                except Exception:
                    return True, "✅ Conexão OK, mas verifique a pasta de alvarás no secrets.toml"
            else:
                return True, "✅ Conexão OK, mas configure o alvaras_folder_id no secrets.toml"
                
        except Exception as e:
            return False, f"❌ Erro na conexão: {str(e)}"


# Função auxiliar para integração com o sistema existente
def upload_to_google_drive(processo, comprovante_file, pdf_file):
    """Função auxiliar para upload de documentos de alvará"""
    drive = GoogleDriveIntegration()
    return drive.upload_alvara_documents(processo, comprovante_file, pdf_file)


def upload_log_to_drive(arquivo_local, nome_arquivo="log_exclusoes.csv"):
    """
    Função específica para upload de logs CSV para Google Drive
    
    Args:
        arquivo_local: Caminho para o arquivo local
        nome_arquivo: Nome do arquivo no Drive
        
    Returns:
        bool: True se sucesso, False se falha
    """
    try:
        drive = GoogleDriveIntegration()
        
        # Verificar se arquivo local existe
        if not os.path.exists(arquivo_local):
            return False
        
        # Inicializar serviço
        if not drive.initialize_service():
            return False
        
        # Encontrar ou criar pasta de Logs
        pasta_logs_id = drive.find_folder("Logs_Sistema")
        if not pasta_logs_id:
            pasta_logs_id = drive.create_folder("Logs_Sistema")
            if not pasta_logs_id:
                return False
        
        # Ler arquivo local
        with open(arquivo_local, 'rb') as file:
            file_content = file.read()
        
        # Upload para Drive
        file_id, uploaded_name = drive.upload_file(
            file_content=file_content,
            file_name=nome_arquivo,
            folder_id=pasta_logs_id,
            mime_type='text/csv'
        )
        
        if file_id:
            # Log informações do upload
            file_size = len(file_content)
            st.success(f"📁 Log enviado para Google Drive: {uploaded_name} ({file_size} bytes)")
            return True
        else:
            return False
        
    except Exception as e:
        st.error(f"Erro ao enviar log para Drive: {str(e)}")
        return False


def test_google_drive_connection():
    """Função para testar conexão com Google Drive - Interface Streamlit"""
    drive = GoogleDriveIntegration()
    
    with st.spinner("🔍 Testando conexão com Google Drive..."):
        success, message = drive.test_connection()
    
    if success:
        st.success(message)
    else:
        st.error(message)
        if "Credenciais" in message:
            st.info("""
            🔧 **Para resolver:**
            1. Vá em "⚙️ Configurações" > "☁️ Google Drive"
            2. Complete o processo de autenticação OAuth
            3. Verifique se todas as credenciais estão no secrets.toml
            """)
    
    return success
