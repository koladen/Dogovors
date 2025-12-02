// API Base URL
const API_BASE = '';

// Глобальные переменные
let currentUser = null;
let currentAnalysisResult = null;
let currentFilename = null;

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

function logout() {
    // В нашей системе достаточно просто перенаправить на логин
    // IP будет оставаться авторизованным, но пользователь может войти под другим аккаунтом
    window.location.href = '/static/login.html';
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

    const filename = currentFilename ? currentFilename.replace(/\.[^/.]+$/, "") + '_анализ' : 'Анализ_договора';

    try {
        const response = await fetch(`${API_BASE}/api/export`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                content: currentAnalysisResult,
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
