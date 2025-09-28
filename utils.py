"""
Utilitários do Sistema de Conversão
==================================

Funções auxiliares e utilitários para o sistema de conversão de arquivos.
Inclui validação de arquivos, formatação de dados e funções de limpeza.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import logging
from datetime import datetime, timedelta
import hashlib

# ==================== CONFIGURAÇÃO DE LOGS ====================
logger = logging.getLogger(__name__)

# ==================== VALIDAÇÃO DE ARQUIVOS ====================

def is_supported_format(file_path: str, supported_extensions: List[str]) -> bool:
    """
    Verifica se o formato do arquivo é suportado
    
    Args:
        file_path: Caminho do arquivo
        supported_extensions: Lista de extensões suportadas
        
    Returns:
        bool: True se suportado, False caso contrário
    """
    ext = Path(file_path).suffix.lower()
    return ext in supported_extensions


def get_file_size_mb(file_path: str) -> float:
    """
    Retorna o tamanho do arquivo em MB
    
    Args:
        file_path: Caminho do arquivo
        
    Returns:
        float: Tamanho em MB
    """
    try:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except OSError:
        return 0.0


def format_file_size(size_bytes: int) -> str:
    """
    Formata o tamanho do arquivo para exibição
    
    Args:
        size_bytes: Tamanho em bytes
        
    Returns:
        str: Tamanho formatado (ex: "1.5 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def validate_file_upload(file_path: str, max_size_mb: float = 100) -> Tuple[bool, str]:
    """
    Valida um arquivo enviado
    
    Args:
        file_path: Caminho do arquivo
        max_size_mb: Tamanho máximo em MB
        
    Returns:
        Tuple[bool, str]: (é_válido, mensagem_erro)
    """
    # Verificar se o arquivo existe
    if not os.path.exists(file_path):
        return False, "Arquivo não encontrado"
    
    # Verificar se não é um diretório
    if os.path.isdir(file_path):
        return False, "Não é possível processar diretórios"
    
    # Verificar tamanho
    size_mb = get_file_size_mb(file_path)
    if size_mb > max_size_mb:
        return False, f"Arquivo muito grande ({size_mb:.1f}MB). Máximo: {max_size_mb}MB"
    
    # Verificar se o arquivo não está vazio
    if size_mb == 0:
        return False, "Arquivo está vazio"
    
    return True, "Arquivo válido"


# ==================== MANIPULAÇÃO DE CAMINHOS ====================

def create_safe_filename(filename: str) -> str:
    """
    Cria um nome de arquivo seguro removendo caracteres problemáticos
    
    Args:
        filename: Nome original do arquivo
        
    Returns:
        str: Nome do arquivo seguro
    """
    # Caracteres problemáticos para remover/substituir
    unsafe_chars = '<>:"/\\|?*'
    safe_name = filename
    
    for char in unsafe_chars:
        safe_name = safe_name.replace(char, '_')
    
    # Remover espaços extras e pontos no final
    safe_name = safe_name.strip('. ')
    
    # Garantir que não fique vazio
    if not safe_name:
        safe_name = f"arquivo_{int(datetime.now().timestamp())}"
    
    return safe_name


def get_unique_filename(directory: str, filename: str) -> str:
    """
    Gera um nome de arquivo único em um diretório
    
    Args:
        directory: Diretório onde o arquivo será salvo
        filename: Nome desejado do arquivo
        
    Returns:
        str: Nome único do arquivo
    """
    base_path = Path(directory)
    base_path.mkdir(parents=True, exist_ok=True)
    
    file_path = base_path / filename
    
    # Se não existe, usar o nome original
    if not file_path.exists():
        return filename
    
    # Gerar nome único
    name_part = file_path.stem
    ext_part = file_path.suffix
    counter = 1
    
    while file_path.exists():
        new_name = f"{name_part}_{counter}{ext_part}"
        file_path = base_path / new_name
        counter += 1
        
        # Evitar loop infinito
        if counter > 1000:
            # Usar timestamp como fallback
            timestamp = int(datetime.now().timestamp())
            new_name = f"{name_part}_{timestamp}{ext_part}"
            break
    
    return file_path.name


def create_temp_file(suffix: str = "", prefix: str = "conv_") -> str:
    """
    Cria um arquivo temporário único
    
    Args:
        suffix: Sufixo/extensão do arquivo
        prefix: Prefixo do nome do arquivo
        
    Returns:
        str: Caminho completo do arquivo temporário
    """
    temp_fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
    os.close(temp_fd)  # Fechar o file descriptor
    return temp_path


# ==================== LIMPEZA E MANUTENÇÃO ====================

def cleanup_old_files(directory: str, max_age_hours: int = 24) -> int:
    """
    Remove arquivos antigos de um diretório
    
    Args:
        directory: Diretório para limpar
        max_age_hours: Idade máxima dos arquivos em horas
        
    Returns:
        int: Número de arquivos removidos
    """
    if not os.path.exists(directory):
        return 0
    
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    removed_count = 0
    
    try:
        for file_path in Path(directory).iterdir():
            if file_path.is_file():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_time:
                    try:
                        file_path.unlink()
                        removed_count += 1
                        logger.info(f"Arquivo antigo removido: {file_path}")
                    except OSError as e:
                        logger.error(f"Erro ao remover {file_path}: {e}")
    
    except OSError as e:
        logger.error(f"Erro ao acessar diretório {directory}: {e}")
    
    return removed_count


def get_directory_size(directory: str) -> int:
    """
    Calcula o tamanho total de um diretório em bytes
    
    Args:
        directory: Caminho do diretório
        
    Returns:
        int: Tamanho total em bytes
    """
    total_size = 0
    
    try:
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    total_size += os.path.getsize(file_path)
                except OSError:
                    pass  # Ignorar arquivos inacessíveis
    except OSError:
        pass
    
    return total_size


def ensure_directory_exists(directory: str) -> bool:
    """
    Garante que um diretório existe, criando se necessário
    
    Args:
        directory: Caminho do diretório
        
    Returns:
        bool: True se o diretório existe ou foi criado com sucesso
    """
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        logger.error(f"Erro ao criar diretório {directory}: {e}")
        return False


# ==================== FORMATAÇÃO E CONVERSÃO ====================

def seconds_to_duration(seconds: float) -> str:
    """
    Converte segundos para formato de duração legível
    
    Args:
        seconds: Número de segundos
        
    Returns:
        str: Duração formatada (ex: "2m 30s")
    """
    if seconds < 60:
        return f"{seconds:.0f}s"
    
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    
    if minutes < 60:
        return f"{minutes}m {remaining_seconds}s"
    
    hours = int(minutes // 60)
    remaining_minutes = int(minutes % 60)
    
    return f"{hours}h {remaining_minutes}m {remaining_seconds}s"


def generate_file_hash(file_path: str) -> str:
    """
    Gera um hash MD5 para um arquivo
    
    Args:
        file_path: Caminho do arquivo
        
    Returns:
        str: Hash MD5 do arquivo
    """
    hash_md5 = hashlib.md5()
    
    try:
        with open(file_path, "rb") as f:
            # Ler em chunks para arquivos grandes
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
    except OSError:
        return ""
    
    return hash_md5.hexdigest()


# ==================== VERIFICAÇÃO DE SISTEMA ====================

def check_ffmpeg_available() -> bool:
    """
    Verifica se o FFmpeg está disponível no sistema
    
    Returns:
        bool: True se FFmpeg está disponível
    """
    try:
        result = shutil.which('ffmpeg')
        return result is not None
    except Exception:
        return False


def get_system_info() -> Dict[str, Any]:
    """
    Retorna informações básicas do sistema
    
    Returns:
        Dict: Informações do sistema
    """
    import platform
    import psutil
    
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "python_version": platform.python_version(),
        "cpu_count": os.cpu_count(),
        "memory_gb": round(psutil.virtual_memory().total / (1024**3), 1),
        "ffmpeg_available": check_ffmpeg_available()
    }


# ==================== INICIALIZAÇÃO ====================
logger.info("Utilitários do sistema carregados")