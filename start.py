#!/usr/bin/env python3
"""
Script de inicialização do Conversor de Arquivos Multimídia
Verifica dependências e inicia o servidor
"""

import sys
import subprocess
import os
from pathlib import Path

def check_python_version():
    """Verifica se a versão do Python é compatível"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 ou superior é necessário")
        print(f"Versão atual: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detectado")
    return True

def check_ffmpeg():
    """Verifica se o FFmpeg está instalado"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, check=True)
        print("✅ FFmpeg detectado")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg não encontrado")
        print("Instale o FFmpeg:")
        print("- Windows: winget install Gyan.FFmpeg")
        print("- Ubuntu/Debian: sudo apt install ffmpeg")
        print("- macOS: brew install ffmpeg")
        return False

def check_virtual_environment():
    """Verifica se está em um ambiente virtual"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Ambiente virtual detectado")
        return True
    else:
        print("⚠️  Não está em um ambiente virtual")
        print("Recomenda-se usar um ambiente virtual:")
        print("python -m venv .venv")
        print(".venv\\Scripts\\activate  # Windows")
        print("source .venv/bin/activate  # Linux/macOS")
        return False

def install_dependencies():
    """Instala as dependências do requirements.txt"""
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ Arquivo requirements.txt não encontrado")
        return False
    
    try:
        print("📦 Instalando dependências...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True)
        print("✅ Dependências instaladas com sucesso")
        return True
    except subprocess.CalledProcessError:
        print("❌ Erro ao instalar dependências")
        return False

def create_directories():
    """Cria diretórios necessários"""
    directories = ['uploads', 'outputs']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    print("✅ Diretórios criados")

def start_server():
    """Inicia o servidor da aplicação"""
    try:
        print("🚀 Iniciando servidor...")
        print("📡 Servidor disponível em: http://localhost:8000")
        print("📖 Documentação API: http://localhost:8000/docs")
        print("🛑 Pressione Ctrl+C para parar")
        print("-" * 50)
        
        subprocess.run([sys.executable, 'api.py'], check=True)
    except KeyboardInterrupt:
        print("\n👋 Servidor parado pelo usuário")
    except subprocess.CalledProcessError:
        print("❌ Erro ao iniciar servidor")
        return False
    return True

def main():
    """Função principal"""
    print("🎬 Conversor de Arquivos Multimídia")
    print("=" * 40)
    
    # Verificações
    if not check_python_version():
        sys.exit(1)
    
    if not check_ffmpeg():
        sys.exit(1)
    
    check_virtual_environment()
    
    # Preparação
    create_directories()
    
    # Instalar dependências se necessário
    try:
        import fastapi
        print("✅ Dependências já instaladas")
    except ImportError:
        if not install_dependencies():
            sys.exit(1)
    
    # Iniciar servidor
    start_server()

if __name__ == "__main__":
    main()