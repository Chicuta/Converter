# Conversor de Arquivos

Converte vídeos, áudios e imagens de forma simples direto no navegador. Criei isso porque estava cansado de ficar procurando conversores online que só deixam fazer um arquivo por vez ou têm limite de tamanho.

## O que faz

- **Vídeos**: MP4, MOV, AVI, MKV, WebM
- **Áudios**: MP3, WAV, AAC, OGG, FLAC  
- **Imagens**: JPG, PNG, WebP, GIF, BMP
- **Múltiplos arquivos**: Converte vários de uma vez
- **Interface web**: Simples de usar
- **Rápido**: Usa FFmpeg por baixo dos panos

## Como instalar

Precisa ter Python 3.8+ e FFmpeg no seu sistema.

### Jeito fácil
```bash
# Clone o projeto
git clone https://github.com/Chicuta/Converter.git
cd Converter

# Roda o script que configura tudo
python start.py
```

### Jeito manual

**Windows:**
```bash
# Instala o FFmpeg
winget install Gyan.FFmpeg

# Cria ambiente virtual e instala
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Linux/Mac:**
```bash
# Instala FFmpeg primeiro
# Ubuntu: sudo apt install ffmpeg
# Mac: brew install ffmpeg

# Depois instala as dependências
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Como usar

1. **Inicia o servidor**:
   ```bash
   python api.py
   ```

2. **Abre no navegador**: http://localhost:8000

3. **Usa normalmente**:
   - Arrasta os arquivos ou clica para selecionar
   - Escolhe o formato que quer
   - Clica em "Converter"
   - Baixa os arquivos convertidos

## Estrutura do projeto

```
Converter/
├──api.py              # Servidor principal
├── converter.py        # Lógica de conversão
├── index.html         # Interface web
├── script.js          # JavaScript
├── style.css          # Estilos
├── start.py           # Script de inicialização
└── requirements.txt   # Dependências
```

## Configurações

A interface já vem com as configurações mais usadas, mas se quiser mexer:

- **Vídeos**: Qualidade boa (CRF 23), preset medium
- **Áudios**: 128k de bitrate, codec AAC
- **Imagens**: 85% de qualidade para JPEG

## API (se quiser integrar)

A API é bem simples:
- `POST /convert-simple` - Converte um arquivo
- `POST /batch/convert` - Converte vários
- `GET /health` - Verifica se tá funcionando
- `GET /docs` - Documentação automática

## Contribuir

Se quiser melhorar algo:
1. Faz um fork
2. Cria uma branch nova
3. Faz as mudanças
4. Manda um pull request

## Problemas?

Se der algum erro, abre uma issue aqui no GitHub. Ajuda se você incluir:
- O que você estava tentando fazer
- Qual erro apareceu
- Seu sistema operacional

## Licença

MIT - pode usar como quiser.

---

Feito com Python + FFmpeg. Se ajudou, deixa uma ⭐