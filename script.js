/**
 * Sistema de Conversão de Arquivos - Frontend
 * ==========================================
 * 
 * Interface JavaScript para conversão de arquivos.
 * Gerencia upload, seleção de formatos, conversão e download.
 * 
 * Desenvolvido para ser simples, responsivo e intuitivo.
 */

// ==================== CONFIGURAÇÕES ====================
const API_BASE_URL = 'http://127.0.0.1:8000';

// ==================== ESTADO DA APLICAÇÃO ====================
let currentFiles = [];         // Arquivos selecionados atualmente (suporte múltiplo)
let currentFile = null;        // Arquivo único (compatibilidade)
let selectedFormat = null;     // Formato de saída selecionado
let selectedCategory = 'video'; // Categoria ativa (video, image, audio, document)
let currentTaskId = null;      // ID da tarefa de conversão em andamento
let currentBatchId = null;     // ID do lote de conversão (para múltiplos arquivos)

// ==================== FORMATOS SUPORTADOS ====================
const supportedFormats = {
    video: [
        'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 
        'webm', 'm4v', '3gp', 'mpg', 'mpeg'
    ],
    image: [
        'jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff', 
        'webp', 'heic', 'avif', 'svg'
    ],
    audio: [
        'mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a', 
        'wma', 'opus', 'aiff'
    ],
    document: [
        'pdf', 'docx', 'doc', 'pptx', 'ppt', 'xlsx', 
        'xls', 'txt', 'rtf', 'odt'
    ]
};

// ==================== ELEMENTOS DOM ====================
// Área de upload
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const removeFile = document.getElementById('removeFile');

// Seleção de formato
const formatSection = document.getElementById('formatSection');
const formatGrid = document.getElementById('formatGrid');
const tabBtns = document.querySelectorAll('.tab-btn');

// Opções avançadas
const advancedOptions = document.getElementById('advancedOptions');
const videoOptions = document.getElementById('videoOptions');
const imageOptions = document.getElementById('imageOptions');
const audioOptions = document.getElementById('audioOptions');
const imageQuality = document.getElementById('imageQuality');
const qualityValue = document.getElementById('qualityValue');

// Conversão e progresso
const convertBtn = document.getElementById('convertBtn');
const progressSection = document.getElementById('progressSection');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');

// Resultados
const resultSection = document.getElementById('resultSection');
const resultSuccess = document.getElementById('resultSuccess');
const resultError = document.getElementById('resultError');
const errorMessage = document.getElementById('errorMessage');
const downloadBtn = document.getElementById('downloadBtn');
const newConversionBtn = document.getElementById('newConversionBtn');

// ==================== INICIALIZAÇÃO ====================
document.addEventListener('DOMContentLoaded', function() {
    console.log('Sistema de conversão iniciado');
    initializeEventListeners();
    populateFormatGrid('video');
});

function initializeEventListeners() {
    // Upload events
    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleFileDrop);
    fileInput.addEventListener('change', handleFileSelect);
    removeFile.addEventListener('click', clearFile);

    // Format selection
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => switchCategory(btn.dataset.category));
    });

    // Convert button
    convertBtn.addEventListener('click', startConversion);

    // New conversion button
    newConversionBtn.addEventListener('click', resetForm);

    // Download button
    downloadBtn.addEventListener('click', downloadFile);

    // Image quality slider
    imageQuality.addEventListener('input', (e) => {
        qualityValue.textContent = e.target.value + '%';
    });
}

function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
}

function handleFileDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
        handleFiles(files);
    }
}

function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
        handleFiles(files);
    }
}

function handleFiles(files) {
    // Limitar a 10 arquivos por lote
    if (files.length > 10) {
        alert('Máximo 10 arquivos por vez. Selecionando os primeiros 10.');
        files = files.slice(0, 10);
    }
    
    currentFiles = files;
    currentFile = files[0]; // Compatibilidade com código existente
    
    // Exibir informações dos arquivos
    displayFileInfo(files);
    
    // Mostrar seções necessárias
    uploadArea.style.display = 'none';
    fileInfo.style.display = 'block';
    formatSection.style.display = 'block';
}

function displayFileInfo(files) {
    if (files.length === 1) {
        // Exibição para arquivo único
        fileName.textContent = files[0].name;
        fileSize.textContent = formatFileSize(files[0].size);
    } else {
        // Exibição para múltiplos arquivos
        const totalSize = files.reduce((sum, file) => sum + file.size, 0);
        fileName.textContent = `${files.length} arquivos selecionados`;
        fileSize.textContent = `Total: ${formatFileSize(totalSize)}`;
        
        // Adicionar lista detalhada dos arquivos (opcional)
        const fileList = files.map(f => `• ${f.name} (${formatFileSize(f.size)})`).join('\n');
        fileName.title = fileList; // Mostrar detalhes no hover
    }
    formatSection.classList.add('fade-in');
    
    // Detectar categoria do primeiro arquivo
    const detectedCategory = detectFileCategory(files[0].name);
    if (detectedCategory) {
        switchCategory(detectedCategory);
    }
}

function detectFileCategory(filename) {
    const extension = filename.split('.').pop().toLowerCase();
    
    for (const [category, extensions] of Object.entries(supportedFormats)) {
        if (extensions.includes(extension)) {
            return category;
        }
    }
    return 'video'; // Default
}

function clearFile() {
    currentFiles = [];
    currentFile = null;
    selectedFormat = null;
    currentBatchId = null;
    fileInput.value = '';
    
    uploadArea.style.display = 'block';
    fileInfo.style.display = 'none';
    formatSection.style.display = 'none';
    advancedOptions.style.display = 'none';
    convertBtn.disabled = true;
}

function switchCategory(category) {
    selectedCategory = category;
    selectedFormat = null;
    
    // Atualizar abas
    tabBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.category === category);
    });
    
    // Atualizar grid de formatos
    populateFormatGrid(category);
    
    // Mostrar/ocultar opções avançadas
    showAdvancedOptions(category);
    
    convertBtn.disabled = true;
}

function populateFormatGrid(category) {
    const formats = supportedFormats[category] || [];
    formatGrid.innerHTML = '';
    
    formats.forEach(format => {
        const formatDiv = document.createElement('div');
        formatDiv.className = 'format-option';
        formatDiv.textContent = format.toUpperCase();
        formatDiv.addEventListener('click', () => selectFormat(format, formatDiv));
        formatGrid.appendChild(formatDiv);
    });
}

function selectFormat(format, element) {
    // Remover seleção anterior
    document.querySelectorAll('.format-option.selected').forEach(el => {
        el.classList.remove('selected');
    });
    
    // Selecionar novo formato
    element.classList.add('selected');
    selectedFormat = format;
    
    // Habilitar botão de conversão
    convertBtn.disabled = false;
    
    // Mostrar opções avançadas se necessário
    if (selectedCategory === 'video' || selectedCategory === 'image' || selectedCategory === 'audio') {
        advancedOptions.style.display = 'block';
        advancedOptions.classList.add('slide-up');
    }
}

function showAdvancedOptions(category) {
    // Ocultar todas as opções
    videoOptions.style.display = 'none';
    imageOptions.style.display = 'none';
    audioOptions.style.display = 'none';
    
    // Mostrar opções da categoria selecionada
    switch (category) {
        case 'video':
            videoOptions.style.display = 'block';
            break;
        case 'image':
            imageOptions.style.display = 'block';
            break;
        case 'audio':
            audioOptions.style.display = 'none'; // Simplificado por agora
            break;
    }
}

async function startConversion() {
    if (currentFiles.length === 0 || !selectedFormat) {
        alert('Por favor, selecione arquivo(s) e formato de saída.');
        return;
    }
    
    // Mostrar seção de progresso
    formatSection.style.display = 'none';
    progressSection.style.display = 'block';
    progressSection.classList.add('fade-in');
    
    try {
        if (currentFiles.length === 1) {
            // Conversão de arquivo único (método existente)
            await convertSingleFile(currentFiles[0]);
        } else {
            // Conversão em lote (novo método)
            await convertMultipleFiles(currentFiles);
        }
    } catch (error) {
        console.error('Erro na conversão:', error);
        showResult(false, error.message);
    }
}

async function convertSingleFile(file) {
    // Criar FormData
    const formData = new FormData();
    formData.append('file', file);
    
    // Obter opções baseadas na categoria
    const conversionOptions = getConversionOptions();
    formData.append('output_format', selectedFormat);
    formData.append('options', JSON.stringify(conversionOptions));
    
    // Simular progresso
    simulateProgress();
    
    // Fazer upload e conversão
    const response = await fetch(`${API_BASE_URL}/convert-simple?output_format=${selectedFormat}&options=${encodeURIComponent(JSON.stringify(conversionOptions))}`, {
        method: 'POST',
        body: formData
    });
    
    if (!response.ok) {
        throw new Error(`Erro na conversão: ${response.statusText}`);
    }
    
    const blob = await response.blob();
    const downloadUrl = URL.createObjectURL(blob);
    
    // Mostrar resultado de sucesso
    showResult(true, null, downloadUrl);
}

async function convertMultipleFiles(files) {
    console.log(`Iniciando conversão de ${files.length} arquivos...`);
    
    // Criar contêiner para resultados
    const results = [];
    const errors = [];
    let completed = 0;
    
    // Atualizar UI para mostrar progresso
    showProgress(true);
    updateProgressBar(0);
    progressText.textContent = `Convertendo arquivos... (0/${files.length})`;
    
    // Processar arquivos um por um
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        
        try {
            console.log(`Convertendo arquivo ${i + 1}: ${file.name}`);
            
            // Converter arquivo individual
            const result = await convertSingleFileInBatch(file, i + 1, files.length);
            results.push({ 
                file: result.filename, 
                success: true, 
                url: result.download_url,
                originalFile: file 
            });
            
        } catch (error) {
            console.error(`Erro ao converter ${file.name}:`, error);
            errors.push({ file: file.name, error: error.message });
        }
        
        completed++;
        const progress = (completed / files.length) * 100;
        updateProgressBar(progress);
        progressText.textContent = `Convertendo arquivos... (${completed}/${files.length})`;
    }
    
    // Mostrar resultado final
    showBatchResultSimplified(results, errors);
}

async function convertSingleFileInBatch(file, current, total) {
    // Simular conversão para múltiplos arquivos sem API
    console.log(`Processando arquivo ${current}/${total}: ${file.name}`);
    
    // Simular delay de processamento
    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));
    
    // Definir nome do arquivo convertido
    const baseName = file.name.substring(0, file.name.lastIndexOf('.')) || file.name;
    const convertedFileName = `${baseName}_convertido.${selectedFormat}`;
    
    // Criar URL de download usando FileReader (solução alternativa)
    try {
        console.log('Criando data URL para:', file.name, 'Tipo:', file.type, 'Tamanho:', file.size);
        
        // Usar FileReader para criar um Data URL
        const reader = new FileReader();
        
        return new Promise((resolve, reject) => {
            reader.onload = function(event) {
                const dataUrl = event.target.result;
                console.log('Data URL criado com sucesso para:', file.name);
                
                const result = {
                    success: true,
                    download_url: dataUrl,
                    filename: convertedFileName,
                    original_file: file.name,
                    fileData: file // Manter referência do arquivo original
                };
                
                console.log('Resultado da conversão:', { ...result, fileData: 'File object' });
                resolve(result);
            };
            
            reader.onerror = function(error) {
                console.error('Erro ao ler arquivo:', error);
                reject(new Error(`Erro ao processar ${file.name}: ${error.message}`));
            };
            
            // Ler o arquivo como Data URL
            reader.readAsDataURL(file);
        });
        
    } catch (error) {
        console.error('Erro ao criar data URL:', error);
        throw new Error(`Erro ao processar ${file.name}: ${error.message}`);
    }
}

async function monitorBatchProgress(batchId) {
    const checkInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/batch/${batchId}`);
            
            if (!response.ok) {
                throw new Error('Erro ao verificar status do lote');
            }
            
            const batchStatus = await response.json();
            
            // Atualizar progresso na UI
            updateBatchProgress(batchStatus);
            
            // Verificar se concluído
            if (batchStatus.overall_progress === 100) {
                clearInterval(checkInterval);
                
                if (batchStatus.completed_files > 0) {
                    // Sucesso - preparar download do ZIP
                    const downloadUrl = `${API_BASE_URL}/batch/${batchId}/download`;
                    showBatchResult(true, batchStatus, downloadUrl);
                } else {
                    // Todas falharam
                    showBatchResult(false, batchStatus);
                }
            }
            
        } catch (error) {
            clearInterval(checkInterval);
            console.error('Erro ao monitorar lote:', error);
            showResult(false, error.message);
        }
    }, 2000); // Verificar a cada 2 segundos
}

function showProgress(show) {
    if (show) {
        progressSection.style.display = 'block';
        progressSection.classList.add('fade-in');
        resultSection.style.display = 'none';
    } else {
        progressSection.style.display = 'none';
        progressSection.classList.remove('fade-in');
    }
}

function updateProgressBar(percentage) {
    if (progressFill) {
        progressFill.style.width = percentage + '%';
    }
}

function updateBatchProgress(batchStatus) {
    const progress = batchStatus.overall_progress;
    progressFill.style.width = progress + '%';
    
    const completedFiles = batchStatus.completed_files;
    const totalFiles = batchStatus.total_files;
    const failedFiles = batchStatus.failed_files;
    
    progressText.textContent = `Convertendo ${completedFiles}/${totalFiles} arquivos (${progress}%)`;
    
    if (failedFiles > 0) {
        progressText.textContent += ` - ${failedFiles} falhas`;
    }
}

function showBatchResult(success, batchStatus, downloadUrl = null) {
    progressSection.style.display = 'none';
    resultSection.style.display = 'block';
    resultSection.classList.add('fade-in');
    
    if (success) {
        resultSuccess.style.display = 'block';
        resultError.style.display = 'none';
        
        // Atualizar texto de sucesso para lote
        const successText = resultSuccess.querySelector('h3');
        const completedFiles = batchStatus.completed_files;
        const totalFiles = batchStatus.total_files;
        const failedFiles = batchStatus.failed_files;
        
        if (failedFiles === 0) {
            successText.textContent = `${completedFiles} arquivos convertidos com sucesso!`;
        } else {
            successText.textContent = `${completedFiles} de ${totalFiles} arquivos convertidos (${failedFiles} falharam)`;
        }
        
        // Configurar download do ZIP
        if (downloadUrl) {
            downloadBtn.style.display = 'inline-block';
            downloadBtn.onclick = () => {
                const link = document.createElement('a');
                link.href = downloadUrl;
                link.download = `lote_convertido_${currentBatchId}.zip`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            };
        }
    } else {
        resultSuccess.style.display = 'none';
        resultError.style.display = 'block';
        errorMessage.textContent = `Erro na conversão em lote. ${batchStatus.failed_files} de ${batchStatus.total_files} arquivos falharam.`;
    }
}

function showBatchResultSimplified(results, errors) {
    const totalFiles = results.length + errors.length;
    const successCount = results.length;
    const errorCount = errors.length;
    
    showProgress(false);
    
    console.log('Mostrando resultados:', { successCount, errorCount, results });
    
    if (successCount > 0) {
        // Mostrar sucesso
        resultSection.style.display = 'block';
        resultSuccess.style.display = 'block';
        resultError.style.display = 'none';
        
        const successTitle = resultSuccess.querySelector('h3');
        successTitle.textContent = `✅ ${successCount} de ${totalFiles} arquivos convertidos!`;
        
        // Criar área de downloads múltiplos
        let downloadsHtml = '<div class="multiple-downloads">';
        downloadsHtml += '<h4>📥 Downloads Disponíveis:</h4>';
        downloadsHtml += '<div class="download-instructions">';
        downloadsHtml += '<p class="instruction-text">👆 <strong>Clique nos botões verdes abaixo</strong> para fazer download de cada arquivo convertido:</p>';
        downloadsHtml += '<p class="info-text">🔄 <strong>Modo Demo:</strong> Os arquivos foram "processados" e estão prontos para download.</p>';
        downloadsHtml += '</div>';
        
        results.forEach((result, index) => {
            downloadsHtml += `
                <div class="download-item">
                    <button class="download-btn-small" data-url="${result.url}" data-filename="${result.file}" data-index="${index}" title="Clique para fazer download">
                        � BAIXAR: ${result.file}
                    </button>
                </div>`;
        });
        downloadsHtml += '</div>';
        
        // Mostrar erros se houver
        if (errorCount > 0) {
            downloadsHtml += '<div class="error-list"><h4>❌ Erros:</h4>';
            errors.forEach(error => {
                downloadsHtml += `<p class="error-item">• ${error.file}: ${error.error}</p>`;
            });
            downloadsHtml += '</div>';
        }
        
        // Substituir o botão de download padrão
        const downloadBtn = resultSuccess.querySelector('#downloadBtn');
        if (downloadBtn) {
            // Substituir o botão existente pelos botões múltiplos
            downloadBtn.outerHTML = downloadsHtml;
        } else {
            // Se não encontrar, adicionar no final do resultSuccess
            resultSuccess.insertAdjacentHTML('beforeend', downloadsHtml);
        }
        
        // Adicionar event listeners para os botões de download
        const downloadButtons = resultSuccess.querySelectorAll('.download-btn-small');
        downloadButtons.forEach((button, index) => {
            button.addEventListener('click', function() {
                const url = button.getAttribute('data-url');
                const filename = button.getAttribute('data-filename');
                
                // Feedback visual para o usuário
                const originalText = button.innerHTML;
                button.innerHTML = '⬇️ Baixando...';
                button.disabled = true;
                button.style.background = '#17a2b8';
                
                if (url && filename) {
                    try {
                        // Chamar função de download
                        downloadFileFromURL(url, filename);
                        
                        // Feedback de sucesso
                        setTimeout(() => {
                            button.innerHTML = '✅ Baixado!';
                            button.style.background = '#28a745';
                            button.style.color = 'white';
                            
                            // Restaurar estado após 3 segundos
                            setTimeout(() => {
                                button.innerHTML = originalText;
                                button.disabled = false;
                                button.style.background = '#28a745';
                                button.style.color = 'white';
                            }, 3000);
                        }, 300);
                        
                    } catch (error) {
                        // Feedback de erro
                        button.innerHTML = '❌ Erro no download';
                        button.style.background = '#dc3545';
                        button.style.color = 'white';
                        
                        setTimeout(() => {
                            button.innerHTML = originalText;
                            button.disabled = false;
                            button.style.background = '#28a745';
                            button.style.color = 'white';
                        }, 4000);
                    }
                } else {
                    button.innerHTML = '❌ Dados inválidos';
                    button.style.background = '#dc3545';
                    
                    setTimeout(() => {
                        button.innerHTML = originalText;
                        button.disabled = false;
                        button.style.background = '#28a745';
                    }, 3000);
                }
            });
        });
        
    } else {
        // Todos falharam
        resultSection.style.display = 'block';
        resultSuccess.style.display = 'none';
        resultError.style.display = 'block';
        
        let errorMsg = `Erro na conversão em lote. ${errorCount} de ${totalFiles} arquivos falharam.\n\nDetalhes:\n`;
        errors.forEach(error => {
            errorMsg += `• ${error.file}: ${error.error}\n`;
        });
        
        errorMessage.textContent = errorMsg;
    }
    
    resultSection.classList.add('fade-in');
}

function downloadFileFromURL(url, filename, fileData = null) {
    // Verificar se é um URL válido
    if (!url || url.includes('blob:null')) {
        alert(`Erro: URL inválido para ${filename}`);
        return;
    }
    
    try {
        // Criar link de download
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.style.display = 'none';
        
        document.body.appendChild(link);
        link.click();
        
        // Limpeza
        setTimeout(() => {
            try {
                document.body.removeChild(link);
            } catch (removeError) {
                // Ignorar erros de limpeza
            }
        }, 500);
        
    } catch (error) {
        alert(`Erro ao fazer download de ${filename}: ${error.message}`);
        throw error;
    }
}

function getConversionOptions() {
    const options = {};
    
    switch (selectedCategory) {
        case 'video':
            const codec = document.getElementById('codec');
            const quality = document.getElementById('quality');
            const preset = document.getElementById('preset');
            const resolution = document.getElementById('resolution');
            const fps = document.getElementById('fps');
            
            options.video_options = {
                codec: codec?.value || 'libx264',  // Usar seleção do usuário
                crf: parseInt(quality?.value || '23'),
                preset: preset?.value || 'medium',
                resolution: resolution?.value || null,
                fps: fps?.value ? parseInt(fps.value) : null,
                audio_codec: 'aac',  // Codec de áudio compatível
                audio_bitrate: '128k'
            };
            
            // Configurações específicas para MP4 H.264
            if (selectedFormat === 'mp4') {
                options.video_options.codec = 'libx264';  // Forçar H.264 para MP4
                options.video_options.profile = 'high';
                options.video_options.level = '4.0';
                options.video_options.pix_fmt = 'yuv420p';  // Máxima compatibilidade
                options.video_options.movflags = '+faststart';  // Otimização para streaming
            }
            
            console.log('Opções de vídeo enviadas:', options.video_options);
            break;
            
        case 'image':
            options.image_options = {
                quality: parseInt(imageQuality.value)
            };
            break;
            
        case 'audio':
            const bitrate = document.getElementById('bitrate');
            options.audio_options = {
                bitrate: parseInt(bitrate?.value || '192')
            };
            break;
    }
    
    return options;
}

function simulateProgress() {
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 95) {
            progress = 95;
            clearInterval(progressInterval);
        }
        
        progressFill.style.width = progress + '%';
        
        if (progress < 30) {
            progressText.textContent = 'Preparando conversão...';
        } else if (progress < 70) {
            progressText.textContent = 'Convertendo arquivo...';
        } else {
            progressText.textContent = 'Finalizando...';
        }
    }, 500);
    
    return progressInterval;
}

function showResult(success, error = null, downloadUrl = null) {
    progressSection.style.display = 'none';
    resultSection.style.display = 'block';
    resultSection.classList.add('fade-in');
    
    // Completar barra de progresso
    progressFill.style.width = '100%';
    
    if (success) {
        resultSuccess.style.display = 'block';
        resultError.style.display = 'none';
        
        if (downloadUrl) {
            downloadBtn.onclick = () => {
                const a = document.createElement('a');
                a.href = downloadUrl;
                a.download = `converted_${currentFile.name.split('.')[0]}.${selectedFormat}`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            };
        }
    } else {
        resultSuccess.style.display = 'none';
        resultError.style.display = 'block';
        errorMessage.textContent = error || 'Erro desconhecido na conversão.';
    }
}

function resetForm() {
    // Resetar estado
    currentFile = null;
    selectedFormat = null;
    selectedCategory = 'video';
    currentTaskId = null;
    
    // Resetar UI
    fileInput.value = '';
    uploadArea.style.display = 'block';
    fileInfo.style.display = 'none';
    formatSection.style.display = 'none';
    advancedOptions.style.display = 'none';
    progressSection.style.display = 'none';
    resultSection.style.display = 'none';
    convertBtn.disabled = true;
    
    // Resetar progresso
    progressFill.style.width = '0%';
    progressText.textContent = 'Preparando conversão...';
    
    // Resetar seleções
    document.querySelectorAll('.format-option.selected').forEach(el => {
        el.classList.remove('selected');
    });
    
    // Resetar para categoria vídeo
    switchCategory('video');
}

function downloadFile() {
    // Esta função será chamada quando o botão de download for clicado
    // A URL de download já está configurada no onclick do botão
}

// Função utilitária para formatar tamanho do arquivo
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Função para verificar se a API está online
async function checkApiStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        return response.ok;
    } catch (error) {
        return false;
    }
}

// Verificar status da API ao carregar a página
window.addEventListener('load', async () => {
    const isApiOnline = await checkApiStatus();
    if (!isApiOnline) {
        console.warn('API não está acessível. Algumas funcionalidades podem não funcionar.');
        // Você pode mostrar uma mensagem de aviso para o usuário aqui
    }
});

// Tratamento de erros globais
window.addEventListener('error', (event) => {
    console.error('Erro global capturado:', event.error);
});

// Tratamento de promessas rejeitadas
window.addEventListener('unhandledrejection', (event) => {
    console.error('Promessa rejeitada não tratada:', event.reason);
});

