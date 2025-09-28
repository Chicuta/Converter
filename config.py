"""
Configurações do Sistema de Conversão de Arquivos
================================================

Arquivo central de configurações para o conversor.
Centraliza parâmetros, caminhos e opções padrão.
"""

import os
from pathlib import Path

# ==================== INFORMAÇÕES DA APLICAÇÃO ====================
APP_NAME = "Conversor de Arquivos"
APP_VERSION = "1.0.0" 
APP_DESCRIPTION = "Sistema simples e eficiente para conversão de arquivos"

# ==================== CONFIGURAÇÕES DA API ====================
API_HOST = "127.0.0.1"           # Host local para desenvolvimento
API_PORT = 8000                  # Porta padrão
DEBUG = True                     # Modo debug ativo

# ==================== CONFIGURAÇÕES DE ARMAZENAMENTO ====================
# Diretórios de trabalho
UPLOAD_DIR = "./uploads"         # Arquivos enviados
OUTPUT_DIR = "./outputs"         # Arquivos convertidos
TEMP_DIR = "./temp"             # Arquivos temporários

# Limites de arquivo
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB (mais realista)
MAX_STORAGE_GB = 5                  # 5GB máximo de armazenamento

# ==================== CONFIGURAÇÕES DE CONVERSÃO ====================
# Limites de processamento
MAX_CONCURRENT_CONVERSIONS = 2     # Máximo 2 conversões simultâneas
MAX_VIDEO_RESOLUTION = "1920x1080" # Full HD máximo (mais rápido)
MAX_AUDIO_BITRATE = 320            # 320kbps máximo

# ==================== CONFIGURAÇÕES DE QUALIDADE ====================
# Padrões de qualidade (balanceados)
DEFAULT_VIDEO_CRF = 23           # Qualidade boa e tamanho razoável
DEFAULT_VIDEO_PRESET = "medium"   # Velocidade média
DEFAULT_IMAGE_QUALITY = 85        # Qualidade boa sem arquivo muito grande  
DEFAULT_AUDIO_BITRATE = 128       # 128kbps padrão (boa qualidade)

# ==================== CONFIGURAÇÕES DE LIMPEZA ====================
AUTO_CLEANUP_HOURS = 6           # Limpar arquivos temporários a cada 6 horas
CLEANUP_ON_STARTUP = True        # Limpar ao iniciar o sistema

# ==================== CONFIGURAÇÕES DE LOG ====================
LOG_LEVEL = "INFO"               # Nível de log
LOG_FORMAT = "[%(levelname)s] %(message)s"  # Formato simples

print(f"[INFO] {APP_NAME} v{APP_VERSION} - Configurações carregadas")