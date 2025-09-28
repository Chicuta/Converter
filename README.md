# 🎬 Conversor de Arquivos Multimídia

Um conversor de arquivos multimídia moderno e intuitivo com interface web, suportando conversão em lote e múltiplos formatos.

## ✨ Funcionalidades

- 🎥 **Conversão de Vídeos**: MP4, MOV, AVI, MKV, WebM
- 🎵 **Conversão de Áudios**: MP3, WAV, AAC, OGG, FLAC
- 🖼️ **Conversão de Imagens**: JPG, PNG, WebP, GIF, BMP
- 📦 **Conversão em Lote**: Processe múltiplos arquivos simultaneamente
- 🌐 **Interface Web**: Design moderno e responsivo
- ⚡ **Processamento Rápido**: Otimizado com FFmpeg
- 📱 **Responsivo**: Funciona em desktop e mobile

## 🛠️ Tecnologias Utilizadas

- **Backend**: Python 3.8+, FastAPI, Uvicorn
- **Frontend**: HTML5, CSS3, JavaScript ES6+
- **Processamento**: FFmpeg 8.0
- **Servidor**: ASGI com CORS habilitado

## 📦 Instalação

### Pré-requisitos
- Python 3.8 ou superior
- FFmpeg instalado no sistema

### Windows
```bash
# Instalar FFmpeg via winget
winget install Gyan.FFmpeg

# Clonar o repositório
git clone https://github.com/seu-usuario/conversor-arquivos.git
cd conversor-arquivos

# Criar ambiente virtual
python -m venv .venv
.venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

### Linux/macOS
```bash
# Instalar FFmpeg
# Ubuntu/Debian: sudo apt install ffmpeg
# macOS: brew install ffmpeg

# Clonar o repositório
git clone https://github.com/seu-usuario/conversor-arquivos.git
cd conversor-arquivos

# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

## 🚀 Como Usar

1. **Iniciar o servidor**:
   ```bash
   python api.py
   ```

2. **Acessar a interface**:
   - Abra http://localhost:8000 no navegador

3. **Converter arquivos**:
   - Selecione um ou múltiplos arquivos
   - Escolha o formato de saída
   - Clique em "Converter Arquivos"
   - Faça download dos arquivos convertidos

## 📁 Estrutura do Projeto

```
conversor-arquivos/
├── api.py              # Servidor FastAPI principal
├── converter.py        # Classe principal de conversão
├── config.py          # Configurações do sistema
├── utils.py           # Funções utilitárias
├── index.html         # Interface web principal
├── script.js          # Lógica JavaScript
├── style.css          # Estilos CSS
├── requirements.txt   # Dependências Python
├── uploads/           # Pasta para arquivos carregados
├── outputs/           # Pasta para arquivos convertidos
└── README.md         # Este arquivo
```

## 🎛️ Configurações Avançadas

### Qualidade de Vídeo
- **CRF**: 18-28 (18 = máxima qualidade, 28 = qualidade padrão)
- **Preset**: ultrafast, fast, medium, slow, veryslow
- **Resolução**: Mantém original ou redimensiona

### Qualidade de Áudio
- **Bitrate**: 64k, 128k, 192k, 320k
- **Codec**: AAC (padrão), MP3, OGG

### Qualidade de Imagem
- **JPEG**: 1-100% (padrão: 85%)
- **PNG**: Compressão sem perda
- **WebP**: Otimizado para web

## 🔧 API Endpoints

### Conversão Simples
```http
POST /convert-simple?output_format={formato}&options={opcoes}
Content-Type: multipart/form-data
```

### Conversão em Lote
```http
POST /batch/convert
Content-Type: application/json
```

### Status da API
```http
GET /health
```

### Documentação Interativa
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🐛 Reportar Bugs

Encontrou um bug? Por favor, abra uma [issue](https://github.com/seu-usuario/conversor-arquivos/issues) com:
- Descrição detalhada do problema
- Passos para reproduzir
- Arquivos de exemplo (se possível)
- Sistema operacional e versão do Python

## 💡 Suporte

- 📧 Email: seu-email@exemplo.com
- 💬 Discussions: [GitHub Discussions](https://github.com/seu-usuario/conversor-arquivos/discussions)
- 📖 Wiki: [Documentação Completa](https://github.com/seu-usuario/conversor-arquivos/wiki)

## 🌟 Agradecimentos

- [FFmpeg](https://ffmpeg.org/) - Ferramenta de processamento multimídia
- [FastAPI](https://fastapi.tiangolo.com/) - Framework web moderno
- [Python](https://python.org/) - Linguagem de programação

---

⭐ **Se este projeto foi útil para você, considere dar uma estrela!** ⭐