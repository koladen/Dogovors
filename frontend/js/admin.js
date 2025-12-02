// ===== ИНИЦИАЛИЗАЦИЯ АДМИН-ПАНЕЛИ =====

async function initAdmin() {
    const isAuth = await checkAuth();

    if (!isAuth) {
        window.location.href = '/static/login.html';
        return;
    }

    // Проверить права администратора
    if (currentUser.role !== 'admin') {
        alert('Доступ запрещен. Требуются права администратора.');
        window.location.href = '/static/index.html';
        return;
    }

    // Отобразить имя пользователя
    const usernameDisplay = document.getElementById('username-display');
    if (usernameDisplay) {
        usernameDisplay.textContent = `Администратор: ${currentUser.username}`;
    }

    // Загрузить данные для первого таба (пользователи)
    loadUsers();
}

// ===== УПРАВЛЕНИЕ ТАБАМИ =====

function showTab(tabName) {
    // Скрыть все табы
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    // Убрать активный класс с кнопок
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });

    // Показать выбранный таб
    const selectedTab = document.getElementById(`${tabName}-tab`);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }

    // Активировать кнопку
    event.target.classList.add('active');

    // Загрузить данные для таба
    switch(tabName) {
        case 'users':
            loadUsers();
            break;
        case 'prompts':
            loadPrompts();
            break;
        case 'llm':
            loadLLMConfig();
            break;
        case 'settings':
            loadSettings();
            break;
        case 'stats':
            loadTokenStats();
            break;
        case 'logs':
            loadLogs();
            break;
    }
}

// ===== УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ =====

async function loadUsers() {
    try {
        const response = await fetch(`${API_BASE}/api/admin/users`);
        const data = await response.json();

        if (data.success) {
            renderUsersTable(data.users);
        } else {
            showNotification('Ошибка загрузки пользователей', 'error');
        }
    } catch (error) {
        showNotification('Ошибка сети', 'error');
    }
}

function renderUsersTable(users) {
    const container = document.getElementById('users-list');

    let html = `
        <table class="users-table">
            <thead>
                <tr>
                    <th>Логин</th>
                    <th>Роль</th>
                    <th>Действия</th>
                </tr>
            </thead>
            <tbody>
    `;

    users.forEach(user => {
        const roleClass = user.role === 'admin' ? 'role-admin' : 'role-user';
        const roleText = user.role === 'admin' ? 'Администратор' : 'Пользователь';

        html += `
            <tr>
                <td>${user.username}</td>
                <td><span class="${roleClass}">${roleText}</span></td>
                <td>
                    <button onclick="editUser('${user.username}')" class="btn btn-secondary btn-small">Редактировать</button>
                </td>
            </tr>
        `;
    });

    html += '</tbody></table>';
    container.innerHTML = html;
}

function showCreateUserForm() {
    const html = `
        <div class="edit-form">
            <h3>Создать пользователя</h3>
            <form id="createUserForm">
                <div class="form-group">
                    <label for="new-username">Логин:</label>
                    <input type="text" id="new-username" required>
                </div>
                <div class="form-group">
                    <label for="new-password">Пароль:</label>
                    <input type="password" id="new-password" required>
                </div>
                <div class="form-group">
                    <label for="new-role">Роль:</label>
                    <select id="new-role">
                        <option value="user">Пользователь</option>
                        <option value="admin">Администратор</option>
                    </select>
                </div>
                <button type="submit" class="btn btn-success">Создать</button>
                <button type="button" onclick="loadUsers()" class="btn btn-secondary">Отмена</button>
            </form>
        </div>
    `;

    document.getElementById('users-list').innerHTML += html;

    document.getElementById('createUserForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await createUser();
    });
}

async function createUser() {
    const username = document.getElementById('new-username').value;
    const password = document.getElementById('new-password').value;
    const role = document.getElementById('new-role').value;

    try {
        const response = await fetch(`${API_BASE}/api/admin/users`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, role })
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Пользователь создан', 'success');
            loadUsers();
        } else {
            showNotification(data.error || 'Ошибка создания', 'error');
        }
    } catch (error) {
        showNotification('Ошибка сети', 'error');
    }
}

async function editUser(username) {
    const newPassword = prompt(`Новый пароль для ${username} (оставьте пустым, чтобы не менять):`);
    const newRole = prompt(`Новая роль для ${username} (admin или user, оставьте пустым, чтобы не менять):`);

    if (newPassword === null && newRole === null) return;

    const updates = {};
    if (newPassword) updates.password = newPassword;
    if (newRole && (newRole === 'admin' || newRole === 'user')) updates.role = newRole;

    if (Object.keys(updates).length === 0) {
        showNotification('Нет изменений', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/admin/users/${username}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates)
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Пользователь обновлен', 'success');
            loadUsers();
        } else {
            showNotification(data.error || 'Ошибка обновления', 'error');
        }
    } catch (error) {
        showNotification('Ошибка сети', 'error');
    }
}

// ===== УПРАВЛЕНИЕ ПРОМПТАМИ =====

async function loadPrompts() {
    try {
        const response = await fetch(`${API_BASE}/api/admin/prompts`);
        const data = await response.json();

        if (data.success) {
            renderPromptsEditor(data.prompts);
        } else {
            showNotification('Ошибка загрузки промптов', 'error');
        }
    } catch (error) {
        showNotification('Ошибка сети', 'error');
    }
}

function renderPromptsEditor(prompts) {
    const container = document.getElementById('prompts-content');

    container.innerHTML = `
        <div class="prompt-editor">
            <h4>Промпт для детальной выжимки договора</h4>
            <textarea id="prompt-summary">${prompts.summary || ''}</textarea>
            <div class="prompt-actions">
                <button onclick="savePrompt('summary')" class="btn btn-success">Сохранить</button>
                <button onclick="resetPrompt('summary')" class="btn btn-secondary">Сбросить к исходному</button>
            </div>
        </div>

        <div class="prompt-editor">
            <h4>Промпт для проверки законодательства</h4>
            <textarea id="prompt-legal_check">${prompts.legal_check || ''}</textarea>
            <div class="prompt-actions">
                <button onclick="savePrompt('legal_check')" class="btn btn-success">Сохранить</button>
                <button onclick="resetPrompt('legal_check')" class="btn btn-secondary">Сбросить к исходному</button>
            </div>
        </div>
    `;
}

async function savePrompt(promptType) {
    const content = document.getElementById(`prompt-${promptType}`).value;

    try {
        const response = await fetch(`${API_BASE}/api/admin/prompts`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt_type: promptType, content })
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Промпт сохранен', 'success');
        } else {
            showNotification(data.error || 'Ошибка сохранения', 'error');
        }
    } catch (error) {
        showNotification('Ошибка сети', 'error');
    }
}

async function resetPrompt(promptType) {
    if (!confirm('Вы уверены, что хотите сбросить промпт к исходному значению?')) return;

    try {
        const response = await fetch(`${API_BASE}/api/admin/prompts/reset`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt_type: promptType })
        });

        const data = await response.json();

        if (data.success) {
            document.getElementById(`prompt-${promptType}`).value = data.content;
            showNotification('Промпт сброшен', 'success');
        } else {
            showNotification(data.error || 'Ошибка сброса', 'error');
        }
    } catch (error) {
        showNotification('Ошибка сети', 'error');
    }
}

// ===== НАСТРОЙКИ LLM =====

async function loadLLMConfig() {
    try {
        const response = await fetch(`${API_BASE}/api/admin/llm-config`);
        const data = await response.json();

        if (data.success) {
            renderLLMConfig(data.config);
        } else {
            showNotification('Ошибка загрузки настроек LLM', 'error');
        }
    } catch (error) {
        showNotification('Ошибка сети', 'error');
    }
}

function renderLLMConfig(config) {
    const container = document.getElementById('llm-config');

    container.innerHTML = `
        <div class="llm-settings">
            <div class="llm-option ${config.llm_type === 'deepseek' ? 'selected' : ''}" onclick="selectLLM('deepseek')">
                <h4>☁️ DeepSeek API (облачная)</h4>
                <p>Быстрая обработка, требует интернет</p>
            </div>
            <div class="llm-option ${config.llm_type === 'lmstudio' ? 'selected' : ''}" onclick="selectLLM('lmstudio')">
                <h4>🖥️ LM Studio (локальная)</h4>
                <p>Конфиденциальность, без интернета</p>
            </div>
        </div>

        <form id="llmConfigForm" class="edit-form" style="margin-top: 20px;">
            <h3>Настройки подключения</h3>

            <div class="form-group">
                <label>Текущий тип LLM:</label>
                <select id="llm-type">
                    <option value="deepseek" ${config.llm_type === 'deepseek' ? 'selected' : ''}>DeepSeek API</option>
                    <option value="lmstudio" ${config.llm_type === 'lmstudio' ? 'selected' : ''}>LM Studio</option>
                </select>
            </div>

            <div class="form-group">
                <label>DeepSeek API Key:</label>
                <input type="password" id="deepseek-api-key" value="${config.deepseek_api_key || ''}" placeholder="sk-...">
            </div>

            <div class="form-group">
                <label>LM Studio URL:</label>
                <input type="text" id="lmstudio-url" value="${config.lmstudio_base_url || 'http://localhost:1234/v1'}">
            </div>

            <div class="form-group">
                <label>LM Studio Model:</label>
                <input type="text" id="lmstudio-model" value="${config.lmstudio_model || 'deepseek-coder'}">
            </div>

            <button type="submit" class="btn btn-success">Сохранить настройки</button>
        </form>
    `;

    document.getElementById('llmConfigForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await saveLLMConfig();
    });
}

function selectLLM(type) {
    document.querySelectorAll('.llm-option').forEach(el => el.classList.remove('selected'));
    event.currentTarget.classList.add('selected');
    document.getElementById('llm-type').value = type;
}

async function saveLLMConfig() {
    const config = {
        llm_type: document.getElementById('llm-type').value,
        deepseek_api_key: document.getElementById('deepseek-api-key').value,
        lmstudio_base_url: document.getElementById('lmstudio-url').value,
        lmstudio_model: document.getElementById('lmstudio-model').value
    };

    try {
        const response = await fetch(`${API_BASE}/api/admin/llm-config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Настройки LLM сохранены', 'success');
        } else {
            showNotification(data.error || 'Ошибка сохранения', 'error');
        }
    } catch (error) {
        showNotification('Ошибка сети', 'error');
    }
}

// ===== НАСТРОЙКИ СИСТЕМЫ =====

async function loadSettings() {
    try {
        const response = await fetch(`${API_BASE}/api/admin/settings`);
        const data = await response.json();

        if (data.success) {
            renderSettings(data.settings);
        } else {
            showNotification('Ошибка загрузки настроек', 'error');
        }
    } catch (error) {
        showNotification('Ошибка сети', 'error');
    }
}

function renderSettings(settings) {
    const container = document.getElementById('settings-content');

    container.innerHTML = `
        <form id="settingsForm" class="edit-form">
            <div class="form-group">
                <label>Максимальный размер файла (МБ):</label>
                <input type="number" id="max-file-size" value="${settings.max_file_size_mb || 50}" min="1" max="500">
            </div>

            <div class="form-group">
                <label>Макс. одновременных обработок:</label>
                <input type="number" id="max-concurrent" value="${settings.max_concurrent_requests || 5}" min="1" max="20">
            </div>

            <div class="form-group">
                <label>Макс. запросов в очереди:</label>
                <input type="number" id="max-queue" value="${settings.max_queue_size || 5}" min="1" max="20">
            </div>

            <div class="form-group">
                <label>Rate limit (запросов в минуту):</label>
                <input type="number" id="rate-limit" value="${settings.rate_limit_per_minute || 10}" min="1" max="100">
            </div>

            <button type="submit" class="btn btn-success">Сохранить настройки</button>
        </form>
    `;

    document.getElementById('settingsForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await saveSettings();
    });
}

async function saveSettings() {
    const settings = {
        max_file_size_mb: parseInt(document.getElementById('max-file-size').value),
        max_concurrent_requests: parseInt(document.getElementById('max-concurrent').value),
        max_queue_size: parseInt(document.getElementById('max-queue').value),
        rate_limit_per_minute: parseInt(document.getElementById('rate-limit').value)
    };

    try {
        const response = await fetch(`${API_BASE}/api/admin/settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Настройки сохранены', 'success');
        } else {
            showNotification(data.error || 'Ошибка сохранения', 'error');
        }
    } catch (error) {
        showNotification('Ошибка сети', 'error');
    }
}

// ===== СТАТИСТИКА ТОКЕНОВ =====

async function loadTokenStats() {
    try {
        const response = await fetch(`${API_BASE}/api/admin/tokens-stats`);
        const data = await response.json();

        if (data.success) {
            renderTokenStats(data.stats);
        } else {
            showNotification('Ошибка загрузки статистики', 'error');
        }
    } catch (error) {
        showNotification('Ошибка сети', 'error');
    }
}

function renderTokenStats(stats) {
    const container = document.getElementById('stats-content');

    container.innerHTML = `
        <div class="stats-summary">
            <div class="stat-card">
                <h4>Всего токенов</h4>
                <div class="stat-value">${(stats.total_prompt_tokens + stats.total_completion_tokens).toLocaleString()}</div>
            </div>
            <div class="stat-card">
                <h4>Затраты (USD)</h4>
                <div class="stat-value">$${stats.total_cost_usd.toFixed(4)}</div>
            </div>
            <div class="stat-card">
                <h4>Активных пользователей</h4>
                <div class="stat-value">${Object.keys(stats.users).length}</div>
            </div>
        </div>

        <div class="stats-details">
            <h4>По пользователям:</h4>
            <table class="stats-table">
                <thead>
                    <tr>
                        <th>Пользователь</th>
                        <th>Токены</th>
                        <th>Затраты</th>
                        <th>Последняя активность</th>
                    </tr>
                </thead>
                <tbody>
                    ${Object.entries(stats.users).map(([username, userStats]) => `
                        <tr>
                            <td>${username}</td>
                            <td>${(userStats.prompt_tokens + userStats.completion_tokens).toLocaleString()}</td>
                            <td>$${userStats.cost_usd.toFixed(4)}</td>
                            <td>${new Date(userStats.last_used).toLocaleString('ru-RU')}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

// ===== ЛОГИ =====

async function loadLogs(type = 'app') {
    try {
        const response = await fetch(`${API_BASE}/api/admin/logs?type=${type}`);
        const data = await response.json();

        if (data.success) {
            renderLogs(data.logs, type);
        } else {
            showNotification('Ошибка загрузки логов', 'error');
        }
    } catch (error) {
        showNotification('Ошибка сети', 'error');
    }
}

function renderLogs(logs, currentType) {
    const container = document.getElementById('logs-content');

    const logsHtml = logs.map(line => {
        const isError = line.includes('ERROR');
        return `<div class="log-line ${isError ? 'log-error' : 'log-info'}">${line}</div>`;
    }).join('');

    container.innerHTML = `
        <div class="logs-filter">
            <label>Тип логов:</label>
            <select onchange="loadLogs(this.value)">
                <option value="app" ${currentType === 'app' ? 'selected' : ''}>Действия</option>
                <option value="error" ${currentType === 'error' ? 'selected' : ''}>Ошибки</option>
            </select>
            <button onclick="loadLogs('${currentType}')" class="btn btn-secondary btn-small">Обновить</button>
        </div>
        <div class="logs-container">
            ${logsHtml || '<div class="log-line">Нет записей</div>'}
        </div>
    `;
}

// ===== УВЕДОМЛЕНИЯ =====

function showNotification(message, type = 'success') {
    // Удалить существующие уведомления
    document.querySelectorAll('.notification').forEach(el => el.remove());

    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;

    document.body.appendChild(notification);

    // Удалить через 3 секунды
    setTimeout(() => {
        notification.remove();
    }, 3000);
}
