"""
API REST para Conversor de Arquivos
===================================

API FastAPI que fornece endpoints para conversão de arquivos.
Suporta upload, conversão e download de arquivos em diferentes formatos.

Desenvolvido para ser simples, rápido e confiável.
"""

# ==================== IMPORTS ====================
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import tempfile
import uuid
import logging
import asyncio
import json
from datetime import datetime
from pathlib import Path
import shutil

from converter import FileConverter, ConversionStatus

# ==================== CONFIGURAÇÃO DA API ====================
app = FastAPI(
    title="API Conversor de Arquivos",
    description="Converte arquivos entre diferentes formatos de forma simples e rápida",
    version="1.0.0"
)

# Configurar CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios permitidos
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# ==================== CONFIGURAÇÃO DE LOGS ====================
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# ==================== INSTÂNCIA DO CONVERSOR ====================
converter = FileConverter()
logger.info("API iniciada com sucesso")

# ==================== MODELOS DE DADOS ====================

class VideoOptions(BaseModel):
    """Opções de configuração para conversão de vídeos"""
    codec: Optional[str] = "libx264"        # Codec de vídeo (H.264 padrão)
    crf: Optional[int] = 23                 # Qualidade (18=alta, 23=boa, 28=baixa)
    preset: Optional[str] = "medium"        # Velocidade de conversão
    resolution: Optional[str] = None        # Resolução (ex: "1920x1080")
    fps: Optional[int] = None               # Frames por segundo
    bitrate: Optional[str] = None           # Bitrate (ex: "5M")
    max_bitrate: Optional[str] = None       # Bitrate máximo
    audio_codec: Optional[str] = "aac"      # Codec de áudio
    audio_bitrate: Optional[str] = "128k"   # Bitrate do áudio
    deinterlace: Optional[bool] = False     # Remover entrelaçamento
    denoise: Optional[bool] = False         # Reduzir ruído
    sharpen: Optional[bool] = False         # Aumentar nitidez


class ImageOptions(BaseModel):
    """Opções de configuração para conversão de imagens"""
    quality: Optional[int] = 85             # Qualidade (1-100)
    resize: Optional[tuple] = None          # Redimensionar (largura, altura)
    rotate: Optional[int] = None            # Rotacionar em graus
    auto_orient: Optional[bool] = True      # Orientação automática
    compress_level: Optional[int] = 6       # Nível de compressão


class AudioOptions(BaseModel):
    """Opções de configuração para conversão de áudio"""
    bitrate: Optional[int] = 128            # Bitrate em kbps
    sample_rate: Optional[int] = None       # Taxa de amostragem em Hz
    channels: Optional[int] = None          # Número de canais (1=mono, 2=estéreo)


class ConversionRequest(BaseModel):
    """Estrutura da requisição de conversão"""
    output_format: str                      # Formato de saída desejado
    video_options: Optional[VideoOptions] = VideoOptions()
    image_options: Optional[ImageOptions] = ImageOptions()
    audio_options: Optional[AudioOptions] = AudioOptions()


class ConversionResponse(BaseModel):
    """Estrutura da resposta de conversão"""
    task_id: str                           # ID único da tarefa
    status: str                            # Status atual
    message: str                           # Mensagem informativa
    estimated_time: Optional[str] = None   # Tempo estimado


class TaskStatus(BaseModel):
    """Status detalhado de uma tarefa de conversão"""
    task_id: str                           # ID da tarefa
    status: str                            # Status atual
    input_file: str                        # Arquivo de entrada
    output_file: str                       # Arquivo de saída
    input_format: str                      # Formato de entrada
    output_format: str                     # Formato de saída
    created_at: str                        # Data/hora de criação
    completed_at: Optional[str] = None     # Data/hora de conclusão
    error_message: Optional[str] = None    # Mensagem de erro
    file_size: Optional[int] = None        # Tamanho do arquivo
    progress: Optional[int] = None         # Progresso (0-100%)


class BatchConversionRequest(BaseModel):
    """Estrutura para conversão em lote"""
    output_format: str                     # Formato de saída para todos os arquivos
    video_options: Optional[VideoOptions] = VideoOptions()
    image_options: Optional[ImageOptions] = ImageOptions()
    audio_options: Optional[AudioOptions] = AudioOptions()
    preserve_names: Optional[bool] = True  # Preservar nomes originais


class BatchTaskStatus(BaseModel):
    """Status de conversão em lote"""
    batch_id: str                          # ID do lote
    total_files: int                       # Total de arquivos
    completed_files: int                   # Arquivos concluídos
    failed_files: int                      # Arquivos com erro
    overall_progress: int                  # Progresso geral (0-100%)
    tasks: List[TaskStatus]                # Status individual de cada arquivo
    created_at: str                        # Data/hora de criação
    completed_at: Optional[str] = None     # Data/hora de conclusão

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Universal File Converter API",
        "version": "1.0.0",
        "supported_formats": converter.get_supported_formats()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "API is running"}

@app.post("/test-convert")
async def test_convert(file: UploadFile = File(...)):
    """Test endpoint to debug conversion issues"""
    try:
        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(await file.read()),
            "converter_available": hasattr(converter, 'convert_file')
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/convert-simple")
async def convert_simple(
    file: UploadFile = File(...),
    output_format: str = "mp4",
    options: Optional[str] = None
):
    """
    Simplified conversion endpoint that works directly with FormData
    Returns the converted file directly
    """
    try:
        import json
        import logging
        
        # Setup logging for debugging
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        
        logger.info(f"Converting file: {file.filename} to {output_format}")
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Parse options if provided
        conversion_options = {}
        if options:
            try:
                conversion_options = json.loads(options)
                logger.info(f"Parsed options: {conversion_options}")
            except Exception as e:
                logger.warning(f"Failed to parse options: {e}")
                conversion_options = {}
        
        # Create temporary files
        input_temp = tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix)
        with input_temp as temp_file:
            shutil.copyfileobj(file.file, temp_file)
        
        logger.info(f"Input temp file: {input_temp.name}")
        
        output_filename = f"{Path(file.filename).stem}.{output_format.lstrip('.')}"
        output_temp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{output_format.lstrip('.')}")
        output_temp.close()
        
        logger.info(f"Output temp file: {output_temp.name}")
        
        # For MP4 video conversion, ensure H.264 settings
        if output_format.lower() == 'mp4':
            video_options = conversion_options.get('video_options', {})
            # Simplify options to avoid issues
            video_options = {
                'codec': 'libx264',
                'crf': video_options.get('crf', 23),
                'preset': video_options.get('preset', 'medium'),
                'audio_codec': 'aac',
                'audio_bitrate': '128k'
            }
            conversion_options = {'video_options': video_options}
            logger.info(f"Final conversion options: {conversion_options}")
        
        # Perform conversion
        logger.info("Starting conversion...")
        
        # The convert_file method expects options directly, not wrapped in video_options
        final_options = conversion_options.get('video_options', conversion_options)
        
        success = converter.convert_file(input_temp.name, output_temp.name, final_options)
        
        if not success:
            # Clean up temp files
            try:
                os.unlink(input_temp.name)
                os.unlink(output_temp.name)
            except:
                pass
            raise HTTPException(status_code=500, detail="Conversion failed")
        
        # Return converted file (cleanup will happen automatically when temp files go out of scope)
        return FileResponse(
            output_temp.name,
            filename=output_filename,
            media_type='application/octet-stream'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion error: {str(e)}")

@app.get("/formats")
async def get_supported_formats():
    """Get all supported file formats"""
    return converter.get_supported_formats()

@app.post("/convert", response_model=ConversionResponse)
async def convert_file(
    request: ConversionRequest,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Convert uploaded file to specified format with advanced options
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Create temporary input file
        input_temp = tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix)
        with input_temp as temp_file:
            shutil.copyfileobj(file.file, temp_file)
        
        # Generate output filename
        output_filename = f"{Path(file.filename).stem}.{request.output_format.lstrip('.')}"
        output_temp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{request.output_format.lstrip('.')}")
        output_temp.close()
        
        # Determine file category and prepare options
        category = converter.get_file_category(input_temp.name)
        options = {}
        
        if category.value == "video":
            options = request.video_options.dict(exclude_none=True)
        elif category.value == "image":
            options = request.image_options.dict(exclude_none=True)
            # Convert tuple string to actual tuple for resize
            if 'resize' in options and isinstance(options['resize'], str):
                try:
                    w, h = options['resize'].split('x')
                    options['resize'] = (int(w), int(h))
                except:
                    del options['resize']
        elif category.value == "audio":
            options = request.audio_options.dict(exclude_none=True)
        
        # Create conversion task
        task_id = converter.create_conversion_task(
            input_temp.name, 
            output_temp.name, 
            options
        )
        
        # Estimate conversion time (rough estimation)
        file_size_mb = len(file.file.read()) / (1024 * 1024)
        file.file.seek(0)  # Reset file pointer
        estimated_time = f"{max(1, int(file_size_mb / 10))} minutes" if category.value == "video" else "< 1 minute"
        
        # Add background task for conversion
        background_tasks.add_task(
            perform_conversion, 
            task_id, 
            input_temp.name, 
            output_temp.name, 
            options
        )
        
        return ConversionResponse(
            task_id=task_id,
            status="pending",
            message=f"Conversion task created successfully for {category.value} file",
            estimated_time=estimated_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Conversion failed: {str(e)}")

async def perform_conversion(task_id: str, input_file: str, output_file: str, options: Dict[str, Any]):
    """Background task to perform file conversion"""
    try:
        # Update task status
        if task_id in converter.tasks:
            converter.tasks[task_id].status = ConversionStatus.PROCESSING
        
        # Perform conversion
        success = converter.convert_file(input_file, output_file, options)
        
        # Update task status
        if task_id in converter.tasks:
            converter.tasks[task_id].status = ConversionStatus.COMPLETED if success else ConversionStatus.FAILED
            if not success:
                converter.tasks[task_id].error_message = "Conversion failed"
    
    except Exception as e:
        # Update task with error
        if task_id in converter.tasks:
            converter.tasks[task_id].status = ConversionStatus.FAILED
            converter.tasks[task_id].error_message = str(e)

@app.get("/task/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """Get the status of a conversion task"""
    task = converter.get_task_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get file size if output exists
    file_size = None
    if os.path.exists(task.output_file):
        file_size = os.path.getsize(task.output_file)
    
    return TaskStatus(
        task_id=task.task_id,
        status=task.status.value,
        input_file=os.path.basename(task.input_file),
        output_file=os.path.basename(task.output_file),
        input_format=task.input_format,
        output_format=task.output_format,
        created_at=task.created_at.isoformat(),
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        error_message=task.error_message,
        file_size=file_size
    )

@app.get("/download/{task_id}")
async def download_converted_file(task_id: str):
    """Download the converted file"""
    task = converter.get_task_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status != ConversionStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Conversion not completed")
    
    if not os.path.exists(task.output_file):
        raise HTTPException(status_code=404, detail="Output file not found")
    
    return FileResponse(
        task.output_file,
        filename=Path(task.output_file).name,
        media_type='application/octet-stream'
    )

@app.post("/batch-convert")
async def batch_convert_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    output_format: str = "pdf"
):
    """Convert multiple files in batch"""
    task_ids = []
    
    for file in files:
        try:
            # Create temporary input file
            input_temp = tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix)
            with input_temp as temp_file:
                shutil.copyfileobj(file.file, temp_file)
            
            # Generate output filename
            output_temp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{output_format.lstrip('.')}")
            output_temp.close()
            
            # Create conversion task
            task_id = converter.create_conversion_task(input_temp.name, output_temp.name)
            task_ids.append(task_id)
            
            # Add background task
            background_tasks.add_task(
                perform_conversion, 
                task_id, 
                input_temp.name, 
                output_temp.name, 
                {}
            )
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to process {file.filename}: {str(e)}")
    
    return {"task_ids": task_ids, "message": f"Created {len(task_ids)} conversion tasks"}

@app.get("/presets/{category}")
async def get_quality_presets(category: str):
    """Get quality presets for different file categories"""
    presets = {
        "video": {
            "ultra_high": {
                "codec": "libx264",
                "crf": 15,
                "preset": "veryslow",
                "audio_bitrate": "320k",
                "description": "Ultra High Quality - Largest file size"
            },
            "high": {
                "codec": "libx264", 
                "crf": 18,
                "preset": "slow",
                "audio_bitrate": "192k",
                "description": "High Quality - Visually lossless"
            },
            "medium": {
                "codec": "libx264",
                "crf": 23,
                "preset": "medium", 
                "audio_bitrate": "128k",
                "description": "Medium Quality - Good balance"
            },
            "web_optimized": {
                "codec": "libx264",
                "crf": 25,
                "preset": "fast",
                "audio_bitrate": "128k",
                "description": "Web Optimized - Fast loading"
            },
            "h265_high": {
                "codec": "libx265",
                "crf": 20,
                "preset": "slow",
                "audio_bitrate": "192k", 
                "description": "H.265 High Quality - Better compression"
            }
        },
        "image": {
            "maximum": {"quality": 100, "description": "Maximum Quality"},
            "high": {"quality": 95, "description": "High Quality"}, 
            "medium": {"quality": 85, "description": "Medium Quality"},
            "web": {"quality": 75, "description": "Web Optimized"}
        },
        "audio": {
            "lossless": {"bitrate": 1000, "description": "Lossless Quality"},
            "high": {"bitrate": 320, "description": "High Quality"},
            "medium": {"bitrate": 192, "description": "Medium Quality"},
            "low": {"bitrate": 128, "description": "Low Quality"}
        }
    }
    
    if category not in presets:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return presets[category]

@app.post("/convert-preset/{preset_name}")
async def convert_with_preset(
    preset_name: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    output_format: str = "mp4"
):
    """Convert file using predefined quality preset"""
    try:
        category = converter.get_file_category(file.filename).value
        presets_response = await get_quality_presets(category)
        
        if preset_name not in presets_response:
            raise HTTPException(status_code=404, detail="Preset not found")
        
        preset_options = presets_response[preset_name].copy()
        preset_options.pop('description', None)
        
        # Create conversion request with preset
        if category == "video":
            request = ConversionRequest(
                output_format=output_format,
                video_options=VideoOptions(**preset_options)
            )
        elif category == "image":
            request = ConversionRequest(
                output_format=output_format,
                image_options=ImageOptions(**preset_options)
            )
        elif category == "audio":
            request = ConversionRequest(
                output_format=output_format,
                audio_options=AudioOptions(**preset_options)
            )
        else:
            request = ConversionRequest(output_format=output_format)
        
        return await convert_file(request, background_tasks, file)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Preset conversion failed: {str(e)}")

@app.delete("/task/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a conversion task"""
    task = converter.get_task_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Clean up temporary files
    try:
        if os.path.exists(task.input_file):
            os.unlink(task.input_file)
        if os.path.exists(task.output_file):
            os.unlink(task.output_file)
    except:
        pass
    
    # Remove task
    del converter.tasks[task_id]
    
    return {"message": "Task cancelled successfully"}


# ==================== ENDPOINTS DE CONVERSÃO MÚLTIPLA ====================

# Dicionário para armazenar lotes de conversão
batch_tasks = {}

@app.post("/convert-batch")
async def convert_batch(
    files: List[UploadFile] = File(...),
    output_format: str = Query(default="mp4"),
    options: Optional[str] = Query(default=None)
):
    """
    Converte múltiplos arquivos para o mesmo formato
    
    Args:
        files: Lista de arquivos para converter
        output_format: Formato de saída desejado
        options: Opções de conversão em JSON (opcional)
        
    Returns:
        BatchTaskStatus: Status do lote de conversão
    """
    logger.info(f"Recebida requisição de conversão em lote - Arquivos: {len(files) if files else 0}, Formato: {output_format}")
    
    if not files:
        logger.error("Nenhum arquivo enviado na requisição")
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")
    
    if len(files) > 10:  # Limite de 10 arquivos por lote
        logger.error(f"Muitos arquivos enviados: {len(files)} (máximo 10)")
        raise HTTPException(status_code=400, detail="Máximo 10 arquivos por lote")
    
    # Log dos nomes dos arquivos
    file_names = [f.filename for f in files]
    logger.info(f"Arquivos recebidos: {file_names}")
    logger.info(f"Iniciando conversão em lote: {len(files)} arquivos para {output_format}")
    
    # Gerar ID do lote
    batch_id = str(uuid.uuid4())
    
    # Parsear opções se fornecidas
    parsed_options = {}
    if options:
        try:
            parsed_options = json.loads(options)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Opções JSON inválidas")
    
    # Lista para armazenar tarefas individuais
    individual_tasks = []
    
    try:
        # Processar cada arquivo
        for i, file in enumerate(files):
            # Criar arquivo temporário de entrada
            input_temp = tempfile.NamedTemporaryFile(
                delete=False, 
                suffix=f"_{i}_{Path(file.filename).suffix}"
            )
            
            # Salvar arquivo enviado
            contents = await file.read()
            input_temp.write(contents)
            input_temp.close()
            
            # Definir nome do arquivo de saída
            base_name = Path(file.filename).stem
            output_filename = f"{base_name}_convertido.{output_format}"
            output_temp = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=f".{output_format}",
                prefix=f"batch_{batch_id}_{i}_"
            )
            output_temp.close()
            
            # Criar tarefa individual
            task_id = f"{batch_id}_{i}"
            task_status = TaskStatus(
                task_id=task_id,
                status="pending",
                input_file=input_temp.name,
                output_file=output_temp.name,
                input_format=Path(file.filename).suffix.lower(),
                output_format=output_format,
                created_at=datetime.now().isoformat(),
                file_size=len(contents)
            )
            
            individual_tasks.append(task_status)
            logger.info(f"Tarefa criada: {task_id} - {file.filename}")
        
        # Criar status do lote
        batch_status = BatchTaskStatus(
            batch_id=batch_id,
            total_files=len(files),
            completed_files=0,
            failed_files=0,
            overall_progress=0,
            tasks=individual_tasks,
            created_at=datetime.now().isoformat()
        )
        
        # Armazenar lote
        batch_tasks[batch_id] = batch_status
        
        # Iniciar conversões em background
        asyncio.create_task(process_batch_conversion(batch_id, parsed_options))
        
        return batch_status
        
    except Exception as e:
        logger.error(f"Erro ao criar lote de conversão: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao criar lote: {str(e)}")


async def process_batch_conversion(batch_id: str, options: Dict[str, Any]):
    """
    Processa conversão em lote em background
    
    Args:
        batch_id: ID do lote
        options: Opções de conversão
    """
    batch = batch_tasks.get(batch_id)
    if not batch:
        return
    
    logger.info(f"Processando lote {batch_id} com {batch.total_files} arquivos")
    
    completed = 0
    failed = 0
    
    # Processar cada tarefa
    for i, task in enumerate(batch.tasks):
        try:
            logger.info(f"Convertendo arquivo {i+1}/{batch.total_files}: {task.task_id}")
            
            # Atualizar status para processando
            task.status = "processing"
            batch.overall_progress = int((i / batch.total_files) * 100)
            
            # Executar conversão
            result = converter.convert_file(
                input_file=task.input_file,
                output_file=task.output_file,
                output_format=task.output_format,
                options=options
            )
            
            # Atualizar status de sucesso
            task.status = "completed"
            task.completed_at = datetime.now().isoformat()
            completed += 1
            
            logger.info(f"Conversão concluída: {task.task_id}")
            
        except Exception as e:
            # Atualizar status de erro
            task.status = "failed"
            task.error_message = str(e)
            task.completed_at = datetime.now().isoformat()
            failed += 1
            
            logger.error(f"Erro na conversão {task.task_id}: {e}")
    
    # Atualizar status final do lote
    batch.completed_files = completed
    batch.failed_files = failed
    batch.overall_progress = 100
    batch.completed_at = datetime.now().isoformat()
    
    logger.info(f"Lote {batch_id} concluído: {completed} sucessos, {failed} falhas")


@app.get("/batch/{batch_id}")
async def get_batch_status(batch_id: str):
    """
    Obtém o status de um lote de conversão
    
    Args:
        batch_id: ID do lote
        
    Returns:
        BatchTaskStatus: Status atual do lote
    """
    batch = batch_tasks.get(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Lote não encontrado")
    
    return batch


@app.get("/batch/{batch_id}/download")
async def download_batch_results(batch_id: str):
    """
    Cria e retorna um arquivo ZIP com todos os arquivos convertidos do lote
    
    Args:
        batch_id: ID do lote
        
    Returns:
        FileResponse: Arquivo ZIP com os resultados
    """
    batch = batch_tasks.get(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Lote não encontrado")
    
    if batch.completed_files == 0:
        raise HTTPException(status_code=400, detail="Nenhum arquivo foi convertido com sucesso")
    
    try:
        import zipfile
        
        # Criar arquivo ZIP temporário
        zip_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
        zip_temp.close()
        
        with zipfile.ZipFile(zip_temp.name, 'w') as zip_file:
            for task in batch.tasks:
                if task.status == "completed" and os.path.exists(task.output_file):
                    # Nome do arquivo no ZIP baseado no arquivo original
                    original_name = Path(task.input_file).stem
                    zip_filename = f"{original_name}.{task.output_format}"
                    
                    zip_file.write(task.output_file, zip_filename)
        
        return FileResponse(
            zip_temp.name,
            filename=f"batch_{batch_id}_converted.zip",
            media_type='application/zip'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar ZIP: {str(e)}")


@app.delete("/batch/{batch_id}")
async def cancel_batch(batch_id: str):
    """
    Cancela um lote de conversão
    
    Args:
        batch_id: ID do lote
    """
    batch = batch_tasks.get(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Lote não encontrado")
    
    # Limpar arquivos temporários
    for task in batch.tasks:
        try:
            if os.path.exists(task.input_file):
                os.unlink(task.input_file)
            if os.path.exists(task.output_file):
                os.unlink(task.output_file)
        except:
            pass
    
    # Remover lote
    del batch_tasks[batch_id]
    
    return {"message": f"Lote {batch_id} cancelado com sucesso"}


# Bloco de execução principal desabilitado para evitar conflitos
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)