// API Base URL
const API_BASE = '';

// Глобальные переменные
let currentUser = null;
let currentAnalysisResult = null;
let currentFilename = null;
let currentTranscription = null;
let currentProtocol = null;

// ===== ПРОВЕРКА АВТОРИЗАЦИИ =====

async function checkAuth() {
    try {
        const response = await fetch(`${API_BASE}/api/check-auth`);
        const data = await response.json();

        if (data.authorized) {
            currentUser = {
                username: data.username,
                role: data.role
            };
            return true;
        }
        return false;
    } catch (error) {
        console.error('Ошибка проверки авторизации:', error);
        return false;
    }
}

async function checkAuthAndRedirect() {
    // Не проверяем авторизацию автоматически при выходе
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('logout') === 'true') {
        console.log('Пропускаем проверку авторизации после выхода');
        return;
    }

    const isAuth = await checkAuth();

    if (window.location.pathname.includes('login.html')) {
        if (isAuth) {
            window.location.href = '/static/index.html';
        }
    } else {
        if (!isAuth) {
            window.location.href = '/static/login.html';
        }
    }
}

// ===== ЛОГИН =====

async function handleLogin(event) {
    event.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('error-message');

    try {
        const response = await fetch(`${API_BASE}/api/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (data.success) {
            window.location.href = '/static/index.html';
        } else {
            errorDiv.textContent = data.message;
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        errorDiv.textContent = 'Ошибка при авторизации';
        errorDiv.style.display = 'block';
    }
}

// ===== ВЫХОД =====

async function logout() {
    console.log('=== НАЧАЛО ПРОЦЕССА ВЫХОДА ===');
    console.log('Текущий URL:', window.location.href);
    console.log('Протокол:', window.location.protocol);
    console.log('API_BASE:', API_BASE);
    console.log('URL для запроса:', `${API_BASE}/api/logout`);

    // Проверка, что страница открыта через HTTP/HTTPS
    if (window.location.protocol === 'file:') {
        alert('Приложение должно открываться через веб-сервер (http://), а не как локальный файл (file://)');
        console.error('Страница открыта как file:// - запросы к localhost невозможны');
        return;
    }

    try {
        // Показываем индикатор выхода
        const logoutBtn = document.querySelector('button[onclick="logout()"]');
        console.log('Найдена кнопка выхода:', logoutBtn);
        if (logoutBtn) {
            logoutBtn.disabled = true;
            logoutBtn.textContent = 'Выход...';
        }

        console.log('Отправка запроса на выход...');

        // Отправляем запрос на сервер с timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 секунд timeout

        const response = await fetch(`${API_BASE}/api/logout`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        console.log('Ответ сервера получен:', response.status, response.statusText);

        if (response.ok) {
            const data = await response.json();
            console.log('Данные ответа:', data);
            console.log('Выход выполнен успешно');
        } else {
            console.error('HTTP ошибка:', response.status, response.statusText);
            try {
                const errorText = await response.text();
                console.error('Тело ошибки:', errorText);
            } catch (e) {
                console.error('Не удалось прочитать тело ошибки');
            }
            alert('Ошибка при выходе: ' + response.status + ' ' + response.statusText);
            return; // Не перенаправляем при ошибке
        }

    } catch (error) {
        console.error('Ошибка сети при выходе:', error);
        if (error.name === 'AbortError') {
            alert('Превышено время ожидания ответа сервера (5 секунд)');
        } else if (error.message.includes('fetch')) {
            alert('Не удалось подключиться к серверу. Убедитесь, что:\n1. Сервер запущен (python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000)\n2. Страница открыта через http://localhost:8000/static/, а не как file://');
        } else {
            alert('Ошибка сети при выходе: ' + error.message);
        }
        return; // Не перенаправляем при ошибке
    }

    // Теперь перенаправляем на страницу логина с параметром logout=true
    console.log('Перенаправление на страницу логина...');
    window.location.href = '/static/login.html?logout=true';
    console.log('=== КОНЕЦ ПРОЦЕССА ВЫХОДА ===');
}

// ===== ПЕРЕХОД В АДМИН-ПАНЕЛЬ =====

function goToAdmin() {
    console.log('Redirecting to admin panel...');
    window.location.href = '/static/admin.html';
}


// ===== ПЕРЕКЛЮЧЕНИЕ ВКЛАДОК =====

function showMainTab(tabName) {
    // Скрыть все вкладки контента
    document.getElementById('contracts-tab').style.display = 'none';
    document.getElementById('transcription-tab').style.display = 'none';
    
    // Убрать active со всех кнопок
    document.querySelectorAll('.main-tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Показать выбранную вкладку
    if (tabName === 'contracts') {
        document.getElementById('contracts-tab').style.display = 'block';
    } else if (tabName === 'transcription') {
        document.getElementById('transcription-tab').style.display = 'block';
    }
    
    // Активировать кнопку
    event.target.classList.add('active');
}


// ===== ТРАНСКРИБАЦИЯ АУДИО =====

async function handleTranscribe(event) {
    event.preventDefault();
    
    const audioInput = document.getElementById('audio-file');
    const errorDiv = document.getElementById('transcribe-error');
    const spinnerDiv = document.getElementById('transcribe-spinner');
    const resultSection = document.getElementById('transcription-result-section');
    
    // Скрыть ошибки и результаты
    errorDiv.style.display = 'none';
    resultSection.style.display = 'none';
    
    // Показать спиннер
    spinnerDiv.style.display = 'block';
    
    const formData = new FormData();
    formData.append('audio_file', audioInput.files[0]);
    
    try {
        const response = await fetch(`${API_BASE}/api/transcribe`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        // Скрыть спиннер
        spinnerDiv.style.display = 'none';
        
        if (data.success) {
            currentTranscription = data.transcription;
            currentProtocol = data.protocol;
            
            // Отобразить транскрипцию
            document.getElementById('transcription-content').textContent = data.transcription || '';
            
            // Отобразить протокол (может быть пустым)
            const protocolContent = document.getElementById('protocol-content');
            if (data.protocol) {
                protocolContent.innerHTML = marked.parse(data.protocol);
            } else {
                protocolContent.textContent = data.error || 'Протокол не сгенерирован';
            }
            
            resultSection.style.display = 'block';
            resultSection.scrollIntoView({ behavior: 'smooth' });
        } else {
            errorDiv.textContent = data.error || 'Ошибка транскрибации';
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        spinnerDiv.style.display = 'none';
        errorDiv.textContent = 'Ошибка сети при транскрибации';
        errorDiv.style.display = 'block';
    }
}


// ===== ЭКСПОРТ ТРАНСКРИПЦИИ =====

async function exportTranscription() {
    if (!currentTranscription) {
        alert('Нет транскрипции для экспорта');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/export-transcript`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content: currentTranscription,
                filename: 'Транскрипция',
                content_type: 'markdown'
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            
            // Извлечь имя файла из заголовка
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'Транскрипция.docx';
            if (contentDisposition) {
                const match = contentDisposition.match(/filename\*=UTF-8''(.+)/);
                if (match) {
                    filename = decodeURIComponent(match[1]);
                }
            }
            
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            alert('Ошибка при экспорте транскрипции');
        }
    } catch (error) {
        alert('Ошибка при экспорте транскрипции');
    }
}

async function exportProtocol() {
    if (!currentProtocol) {
        alert('Нет протокола для экспорта');
        return;
    }
    
    const protocolHtml = document.getElementById('protocol-content').innerHTML;
    
    try {
        const response = await fetch(`${API_BASE}/api/export-protocol`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content: protocolHtml,
                filename: 'Протокол',
                content_type: 'html'
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'Протокол.docx';
            if (contentDisposition) {
                const match = contentDisposition.match(/filename\*=UTF-8''(.+)/);
                if (match) {
                    filename = decodeURIComponent(match[1]);
                }
            }
            
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            alert('Ошибка при экспорте протокола');
        }
    } catch (error) {
        alert('Ошибка при экспорте протокола');
    }
}

function copyTranscription() {
    if (!currentTranscription) {
        alert('Нет транскрипции для копирования');
        return;
    }
    
    navigator.clipboard.writeText(currentTranscription).then(() => {
        alert('Транскрипция скопирована в буфер обмена');
    }).catch(() => {
        alert('Ошибка при копировании');
    });
}

function copyProtocol() {
    if (!currentProtocol) {
        alert('Нет протокола для копирования');
        return;
    }
    
    navigator.clipboard.writeText(currentProtocol).then(() => {
        alert('Протокол скопирован в буфер обмена');
    }).catch(() => {
        alert('Ошибка при копировании');
    });
}

// ===== ИНИЦИАЛИЗАЦИЯ ГЛАВНОЙ СТРАНИЦЫ =====

async function initApp() {
    const isAuth = await checkAuth();

    if (!isAuth) {
        window.location.href = '/static/login.html';
        return;
    }

    // Отобразить имя пользователя
    const usernameDisplay = document.getElementById('username-display');
    if (usernameDisplay) {
        usernameDisplay.textContent = `Пользователь: ${currentUser.username}`;
    }

    // Показать кнопку админ-панели для администраторов
    const adminButton = document.getElementById('admin-button');
    console.log('Admin button check:', {
        adminButton: !!adminButton,
        currentUser: currentUser,
        role: currentUser?.role,
        isAdmin: currentUser?.role === 'admin'
    });

    if (adminButton && currentUser && currentUser.role === 'admin') {
        console.log('Setting admin button to visible');
        adminButton.style.visibility = 'visible';
    } else {
        console.log('Admin button conditions not met');
    }

    // Добавить обработчик формы
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleAnalyze);
    }

    // Добавить обработчик выбора файла
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const fileName = document.getElementById('file-name');
            if (this.files.length > 0) {
                fileName.textContent = this.files[0].name;
            }
        });
    }
    
    // Добавить обработчик формы транскрибации
    const transcribeForm = document.getElementById('transcribeForm');
    if (transcribeForm) {
        transcribeForm.addEventListener('submit', handleTranscribe);
    }
    
    // Добавить обработчик выбора аудиофайла
    const audioInput = document.getElementById('audio-file');
    if (audioInput) {
        audioInput.addEventListener('change', function() {
            const audioFileName = document.getElementById('audio-file-name');
            if (this.files.length > 0) {
                audioFileName.textContent = this.files[0].name;
            }
        });
    }
}

// ===== АНАЛИЗ ДОГОВОРА =====

async function handleAnalyze(event) {
    event.preventDefault();

    const fileInput = document.getElementById('file');
    const analysisType = document.querySelector('input[name="analysis_type"]:checked').value;
    const errorDiv = document.getElementById('error-message');
    const progressSection = document.getElementById('progress-section');
    const resultSection = document.getElementById('result-section');

    // Скрыть ошибки и результаты
    errorDiv.style.display = 'none';
    resultSection.style.display = 'none';

    // Показать прогресс
    progressSection.style.display = 'block';

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('analysis_type', analysisType);

    try {
        const response = await fetch(`${API_BASE}/api/analyze`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        // Скрыть прогресс
        progressSection.style.display = 'none';

        if (data.success) {
            currentAnalysisResult = data.result;
            currentFilename = data.filename;

            // Отобразить результат
            const resultContent = document.getElementById('result-content');
            resultContent.innerHTML = marked.parse(data.result);
            resultSection.style.display = 'block';

            // Прокрутить к результатам
            resultSection.scrollIntoView({ behavior: 'smooth' });
        } else {
            errorDiv.textContent = data.error;
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        progressSection.style.display = 'none';
        errorDiv.textContent = 'Ошибка при анализе документа';
        errorDiv.style.display = 'block';
    }
}

// ===== ЭКСПОРТ В WORD =====

async function exportToWord() {
    if (!currentAnalysisResult) {
        alert('Нет результата для экспорта');
        return;
    }

    // Получить отрендеренный HTML из result-content вместо сырого Markdown
    const resultContent = document.getElementById('result-content');
    const htmlContent = resultContent ? resultContent.innerHTML : currentAnalysisResult;

    const filename = currentFilename ? currentFilename.replace(/\.[^/.]+$/, "") + '_анализ' : 'Анализ_договора';

    try {
        const response = await fetch(`${API_BASE}/api/export`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                content: htmlContent,
                content_type: 'html', // Указываем тип контента
                filename: filename
            })
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${filename}.docx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            alert('Ошибка при экспорте документа');
        }
    } catch (error) {
        alert('Ошибка при экспорте документа');
    }
}

// ===== КОПИРОВАНИЕ В БУФЕР ОБМЕНА =====

function copyToClipboard() {
    if (!currentAnalysisResult) {
        alert('Нет результата для копирования');
        return;
    }

    navigator.clipboard.writeText(currentAnalysisResult).then(() => {
        alert('Результат скопирован в буфер обмена');
    }).catch(() => {
        alert('Ошибка при копировании');
    });
}
