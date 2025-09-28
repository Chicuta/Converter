"""
Conversor Universal de Arquivos
================================

Sistema completo para conversão de arquivos suportando:
- Vídeos: MP4, MOV, AVI, MKV e outros
- Imagens: JPG, PNG, WEBP, TIFF e outros  
- Documentos: PDF, DOCX, PPTX, XLSX
- Áudio: MP3, WAV, FLAC, AAC e outros

Desenvolvido para ser simples, rápido e confiável.
"""

# ==================== IMPORTS ====================
import os
import tempfile
import uuid
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum
import logging
from dataclasses import dataclass
from datetime import datetime
import subprocess

# ==================== BIBLIOTECAS EXTERNAS ====================
# Processamento de imagens
from PIL import Image, ImageOps

# Bibliotecas de documentos (opcionais)
try:
    import docx2pdf
    from pdf2docx import Converter as PDFToDocxConverter
    import win32com.client
    OFFICE_AVAILABLE = True
except ImportError:
    OFFICE_AVAILABLE = False
    logging.warning("Bibliotecas do Office não disponíveis. Conversões de documentos limitadas.")

# Bibliotecas de áudio (opcionais)
try:
    from pydub import AudioSegment
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    logging.warning("Bibliotecas de áudio não disponíveis.")

# ==================== CONFIGURAÇÃO DE LOGS ====================
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


# ==================== CLASSES E ENUMS ====================

class FileCategory(Enum):
    """Categorias de tipos de arquivo suportados"""
    VIDEO = "video"
    IMAGE = "image" 
    DOCUMENT = "document"
    AUDIO = "audio"
    UNSUPPORTED = "unsupported"


class ConversionStatus(Enum):
    """Status do processo de conversão"""
    PENDING = "pending"          # Aguardando processamento
    PROCESSING = "processing"    # Em processamento
    COMPLETED = "completed"      # Concluído com sucesso
    FAILED = "failed"           # Falhou com erro


@dataclass
class ConversionTask:
    """
    Classe para armazenar informações de uma tarefa de conversão
    
    Attributes:
        task_id: ID único da tarefa
        input_file: Arquivo de entrada
        output_file: Arquivo de saída
        input_format: Formato do arquivo de entrada
        output_format: Formato desejado de saída
        status: Status atual da conversão
        created_at: Data/hora de criação
        completed_at: Data/hora de conclusão (opcional)
        error_message: Mensagem de erro (opcional)
        options: Opções de conversão (opcional)
    """
    task_id: str
    input_file: str
    output_file: str
    input_format: str
    output_format: str
    status: ConversionStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    options: Dict[str, Any] = None


# ==================== CLASSE PRINCIPAL ====================

class FileConverter:
    """
    Conversor Universal de Arquivos
    
    Classe principal que gerencia conversões entre diferentes formatos de arquivo.
    Suporta vídeos, imagens, documentos e áudio com configurações avançadas.
    """
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Inicializa o conversor
        
        Args:
            temp_dir: Diretório temporário para arquivos (opcional)
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.tasks: Dict[str, ConversionTask] = {}
        
        # ==================== FORMATOS SUPORTADOS ====================
        self.format_mappings = {
            # VÍDEOS - Suporte amplo com aceleração por hardware
            FileCategory.VIDEO: {
                'extensions': [
                    # Formatos comuns
                    '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', 
                    # Formatos específicos
                    '.3gp', '.mpg', '.mpeg', '.ts', '.mts', '.m2ts', '.vob', '.ogv', 
                    '.dv', '.rm', '.rmvb', '.asf', '.f4v', '.f4p', '.f4a', '.f4b'
                ],
                'codecs': {
                    # H.264 (mais usado)
                    'h264': 'libx264',              # Software
                    'h264_nvenc': 'h264_nvenc',     # NVIDIA
                    'h264_qsv': 'h264_qsv',         # Intel
                    'h264_amf': 'h264_amf',         # AMD
                    
                    # H.265/HEVC (melhor compressão)
                    'h265': 'libx265',
                    'hevc_nvenc': 'hevc_nvenc',
                    'hevc_qsv': 'hevc_qsv',
                    'hevc_amf': 'hevc_amf',
                    
                    # Outros codecs
                    'vp8': 'libvpx',                # Google VP8
                    'vp9': 'libvpx-vp9',            # Google VP9
                    'av1': 'libaom-av1',            # AV1
                    'av1_nvenc': 'av1_nvenc',       # AV1 NVIDIA
                    'xvid': 'libxvid',              # Xvid
                    'prores': 'prores_ks'           # Apple ProRes
                },
                'presets': [
                    'ultrafast', 'superfast', 'veryfast', 
                    'faster', 'fast', 'medium', 
                    'slow', 'slower', 'veryslow'
                ],
                'crf_range': (0, 51)  # 0=sem perda, 23=padrão, 51=pior qualidade
            },
            
            # IMAGENS - Máxima compatibilidade
            FileCategory.IMAGE: {
                'extensions': [
                    # Formatos comuns
                    '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif', '.webp',
                    # Formatos modernos  
                    '.heic', '.heif', '.avif', '.svg', '.ico',
                    # Formatos profissionais
                    '.raw', '.cr2', '.nef', '.arw', '.dng', '.psd', '.xcf',
                    # Outros formatos
                    '.eps', '.pcx', '.tga', '.jp2', '.jxr'
                ],
                'quality_range': (1, 100),  # Qualidade de 1% a 100%
                'compression_formats': ['JPEG', 'PNG', 'WEBP', 'TIFF', 'BMP', 'GIF']
            },
            
            # DOCUMENTOS - Office e formatos de texto
            FileCategory.DOCUMENT: {
                'extensions': [
                    # Microsoft Office
                    '.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls',
                    # PDF
                    '.pdf',
                    # Texto simples
                    '.txt', '.rtf', '.md', '.html', '.htm', '.csv',
                    # LibreOffice
                    '.odt', '.ods', '.odp',
                    # Apple iWork
                    '.pages', '.numbers', '.key',
                    # E-books
                    '.epub', '.mobi', '.azw', '.azw3', '.fb2',
                    # Outros
                    '.tex'
                ],
                'office_formats': ['.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls'],
                'text_formats': ['.txt', '.rtf', '.md', '.html', '.htm', '.csv'],
                'ebook_formats': ['.epub', '.mobi', '.azw', '.azw3', '.fb2']
            },
            
            # ÁUDIO - Qualidade profissional
            FileCategory.AUDIO: {
                'extensions': [
                    # Formatos com perda
                    '.mp3', '.aac', '.ogg', '.m4a', '.wma', '.opus',
                    # Formatos sem perda
                    '.wav', '.flac', '.ape', '.tak', '.tta', '.wv',
                    # Formatos específicos
                    '.aiff', '.au', '.ra', '.amr', '.3ga', '.ac3', '.dts',
                    '.mka', '.caf', '.sd2'
                ],
                'bitrates': [64, 96, 128, 160, 192, 224, 256, 320, 500, 1000],  # kbps
                'sample_rates': [8000, 11025, 16000, 22050, 44100, 48000, 96000, 192000],  # Hz
                'channels': [1, 2, 6, 8]  # mono, estéreo, 5.1, 7.1
            }
        }
        
        self._setup_logging()
        logger.info("FileConverter inicializado com sucesso")
    
    # ==================== MÉTODOS UTILITÁRIOS ====================
    
    def _setup_logging(self):
        """Configura o sistema de logs"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def get_file_category(self, file_path: str) -> FileCategory:
        """
        Determina a categoria de um arquivo baseado na extensão
        
        Args:
            file_path: Caminho para o arquivo
            
        Returns:
            FileCategory: Categoria do arquivo (VIDEO, IMAGE, DOCUMENT, AUDIO ou UNSUPPORTED)
        """
        ext = Path(file_path).suffix.lower()
        
        # Procura em todas as categorias suportadas
        for category, info in self.format_mappings.items():
            if ext in info['extensions']:
                logger.info(f"Arquivo {file_path} identificado como {category.value}")
                return category
        
        logger.warning(f"Formato {ext} não suportado para {file_path}")
        return FileCategory.UNSUPPORTED
    
    def create_conversion_task(self, input_file: str, output_file: str, 
                             options: Dict[str, Any] = None) -> str:
        """
        Cria uma nova tarefa de conversão
        
        Args:
            input_file: Arquivo de entrada
            output_file: Arquivo de saída
            options: Opções de conversão (opcional)
            
        Returns:
            str: ID único da tarefa criada
        """
        task_id = str(uuid.uuid4())
        
        input_format = Path(input_file).suffix.lower()
        output_format = Path(output_file).suffix.lower()
        
        task = ConversionTask(
            task_id=task_id,
            input_file=input_file,
            output_file=output_file,
            input_format=input_format,
            output_format=output_format,
            status=ConversionStatus.PENDING,
            created_at=datetime.now(),
            options=options or {}
        )
        
        self.tasks[task_id] = task
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[ConversionTask]:
        """Get the status of a conversion task"""
        return self.tasks.get(task_id)
    
    def convert_file(self, input_file: str, output_file: str, 
                    options: Dict[str, Any] = None) -> bool:
        """Main conversion method - delegates to specific converters"""
        try:
            category = self.get_file_category(input_file)
            
            if category == FileCategory.VIDEO:
                return self._convert_video(input_file, output_file, options or {})
            elif category == FileCategory.IMAGE:
                return self._convert_image(input_file, output_file, options or {})
            elif category == FileCategory.DOCUMENT:
                return self._convert_document(input_file, output_file, options or {})
            elif category == FileCategory.AUDIO:
                return self._convert_audio(input_file, output_file, options or {})
            else:
                self.logger.error(f"Unsupported file format: {Path(input_file).suffix}")
                return False
                
        except Exception as e:
            self.logger.error(f"Conversion failed: {str(e)}")
            return False
    
    def _convert_video(self, input_file: str, output_file: str, options: Dict[str, Any]) -> bool:
        """Convert video files using FFmpeg with high-quality settings"""
        try:
            import subprocess
            import shutil
            
            # Try to find ffmpeg executable
            ffmpeg_cmd = None
            possible_paths = [
                'ffmpeg',
                'ffmpeg.exe',
                r'C:\ffmpeg\bin\ffmpeg.exe',
                r'C:\Program Files\FFmpeg\bin\ffmpeg.exe',
                os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0-full_build\bin\ffmpeg.exe'),
                shutil.which('ffmpeg')
            ]
            
            for path in possible_paths:
                if path:
                    if os.path.isfile(path) or shutil.which(path):
                        ffmpeg_cmd = path
                        break
            
            if not ffmpeg_cmd:
                self.logger.error("FFmpeg not found in system PATH")
                return False
            
            # High-quality default options
            codec = options.get('codec', 'libx264')
            crf = options.get('crf', 23)
            preset = options.get('preset', 'medium')
            resolution = options.get('resolution')
            fps = options.get('fps')
            audio_codec = options.get('audio_codec', 'aac')
            audio_bitrate = options.get('audio_bitrate', '128k')
            
            # Build FFmpeg command using subprocess
            cmd = [
                ffmpeg_cmd,
                '-i', input_file,
                '-c:v', codec,
                '-crf', str(crf),
                '-preset', preset,
                '-c:a', audio_codec,
                '-b:a', audio_bitrate,
                '-y',  # Overwrite output files
                output_file
            ]
            
            # Add resolution if specified
            if resolution:
                cmd.extend(['-vf', f'scale={resolution}'])
            
            # Add fps if specified
            if fps:
                cmd.extend(['-r', str(fps)])
            
            self.logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
            
            # Execute FFmpeg
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Video converted successfully: {input_file} -> {output_file}")
                return True
            else:
                self.logger.error(f"FFmpeg error: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Video conversion failed: {str(e)}")
            return False
    
    def _convert_image(self, input_file: str, output_file: str, options: Dict[str, Any]) -> bool:
        """Convert image files using PIL/Pillow"""
        try:
            with Image.open(input_file) as img:
                # Handle transparency for JPEG conversion
                if img.mode in ('RGBA', 'LA') and output_file.lower().endswith(('.jpg', '.jpeg')):
                    # Create white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                # Apply transformations
                if options.get('resize'):
                    width, height = options['resize']
                    img = img.resize((width, height), Image.Resampling.LANCZOS)
                
                if options.get('rotate'):
                    img = img.rotate(options['rotate'], expand=True)
                
                if options.get('auto_orient', True):
                    img = ImageOps.exif_transpose(img)
                
                # Save with quality settings
                save_options = {'optimize': True}
                if output_file.lower().endswith(('.jpg', '.jpeg')):
                    save_options['quality'] = options.get('quality', 95)
                elif output_file.lower().endswith('.png'):
                    save_options['compress_level'] = options.get('compress_level', 6)
                elif output_file.lower().endswith('.webp'):
                    save_options['quality'] = options.get('quality', 90)
                    save_options['method'] = 6
                
                img.save(output_file, **save_options)
                
            self.logger.info(f"Image converted: {input_file} -> {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Image conversion failed: {str(e)}")
            return False
    
    def _convert_document(self, input_file: str, output_file: str, options: Dict[str, Any]) -> bool:
        """Convert document files"""
        try:
            input_ext = Path(input_file).suffix.lower()
            output_ext = Path(output_file).suffix.lower()
            
            # Word to PDF
            if input_ext in ['.docx', '.doc'] and output_ext == '.pdf':
                return self._word_to_pdf(input_file, output_file)
            
            # PDF to Word
            elif input_ext == '.pdf' and output_ext in ['.docx']:
                return self._pdf_to_word(input_file, output_file)
            
            # Office conversions using COM (Windows only)
            elif OFFICE_AVAILABLE and input_ext in ['.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls']:
                return self._office_conversion(input_file, output_file)
            
            else:
                self.logger.error(f"Document conversion not supported: {input_ext} -> {output_ext}")
                return False
                
        except Exception as e:
            self.logger.error(f"Document conversion failed: {str(e)}")
            return False
    
    def _word_to_pdf(self, input_file: str, output_file: str) -> bool:
        """Convert Word documents to PDF"""
        try:
            if OFFICE_AVAILABLE:
                docx2pdf.convert(input_file, output_file)
                return True
            else:
                # Fallback using LibreOffice if available
                return self._libreoffice_conversion(input_file, output_file)
        except Exception as e:
            self.logger.error(f"Word to PDF conversion failed: {str(e)}")
            return False
    
    def _pdf_to_word(self, input_file: str, output_file: str) -> bool:
        """Convert PDF to Word document"""
        try:
            cv = PDFToDocxConverter(input_file)
            cv.convert(output_file)
            cv.close()
            return True
        except Exception as e:
            self.logger.error(f"PDF to Word conversion failed: {str(e)}")
            return False
    
    def _office_conversion(self, input_file: str, output_file: str) -> bool:
        """Convert Office documents using COM interface (Windows)"""
        try:
            input_ext = Path(input_file).suffix.lower()
            output_ext = Path(output_file).suffix.lower()
            
            if input_ext in ['.docx', '.doc']:
                app = win32com.client.Dispatch('Word.Application')
                app.Visible = False
                doc = app.Documents.Open(os.path.abspath(input_file))
                
                if output_ext == '.pdf':
                    doc.SaveAs(os.path.abspath(output_file), FileFormat=17)  # PDF format
                
                doc.Close()
                app.Quit()
                
            elif input_ext in ['.pptx', '.ppt']:
                app = win32com.client.Dispatch('PowerPoint.Application')
                presentation = app.Presentations.Open(os.path.abspath(input_file))
                
                if output_ext == '.pdf':
                    presentation.SaveAs(os.path.abspath(output_file), FileFormat=32)  # PDF format
                
                presentation.Close()
                app.Quit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Office conversion failed: {str(e)}")
            return False
    
    def _libreoffice_conversion(self, input_file: str, output_file: str) -> bool:
        """Fallback conversion using LibreOffice"""
        try:
            cmd = [
                'libreoffice',
                '--headless',
                '--convert-to',
                Path(output_file).suffix[1:],  # Remove the dot
                '--outdir',
                str(Path(output_file).parent),
                input_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return result.returncode == 0
            
        except Exception as e:
            self.logger.error(f"LibreOffice conversion failed: {str(e)}")
            return False
    
    def _convert_audio(self, input_file: str, output_file: str, options: Dict[str, Any]) -> bool:
        """Convert audio files using pydub"""
        try:
            if not AUDIO_AVAILABLE:
                self.logger.error("Audio conversion libraries not available")
                return False
            
            # Load audio file
            audio = AudioSegment.from_file(input_file)
            
            # Apply transformations
            if options.get('bitrate'):
                bitrate = f"{options['bitrate']}k"
            else:
                bitrate = "192k"
            
            if options.get('sample_rate'):
                audio = audio.set_frame_rate(options['sample_rate'])
            
            if options.get('channels'):
                audio = audio.set_channels(options['channels'])
            
            # Export with format-specific options
            output_ext = Path(output_file).suffix.lower()
            export_options = {'bitrate': bitrate}
            
            if output_ext == '.mp3':
                export_options['format'] = 'mp3'
            elif output_ext == '.wav':
                export_options['format'] = 'wav'
            elif output_ext == '.flac':
                export_options['format'] = 'flac'
            elif output_ext == '.aac':
                export_options['format'] = 'aac'
            
            audio.export(output_file, **export_options)
            
            self.logger.info(f"Audio converted: {input_file} -> {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Audio conversion failed: {str(e)}")
            return False
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get all supported file formats by category"""
        formats = {}
        for category, info in self.format_mappings.items():
            if category != FileCategory.UNSUPPORTED:
                formats[category.value] = info['extensions']
        return formats
    
    def batch_convert(self, file_pairs: List[tuple], options: Dict[str, Any] = None) -> Dict[str, bool]:
        """Convert multiple files in batch"""
        results = {}
        
        for input_file, output_file in file_pairs:
            task_id = self.create_conversion_task(input_file, output_file, options)
            success = self.convert_file(input_file, output_file, options)
            
            # Update task status
            if task_id in self.tasks:
                self.tasks[task_id].status = ConversionStatus.COMPLETED if success else ConversionStatus.FAILED
                self.tasks[task_id].completed_at = datetime.now()
            
            results[input_file] = success
        
        return results


# Example usage and testing
if __name__ == "__main__":
    converter = FileConverter()
    
    # Example conversions
    print("Supported formats:", converter.get_supported_formats())
    
    # Test video conversion
    # converter.convert_file("input.mov", "output.mp4", {
    #     'codec': 'libx264',
    #     'crf': 23,
    #     'preset': 'medium'
    # })
    
    # Test image conversion
    # converter.convert_file("input.png", "output.jpg", {
    #     'quality': 90,
    #     'resize': (1920, 1080)
    # })
    
    # Test document conversion
    # converter.convert_file("input.docx", "output.pdf")
