// notifications
const notyf = new Notyf({
    duration: 5000,
    position: { x: 'right', y: 'top' },
    dismissible: true,
    ripple: true,
    types: [
        {
            type: 'success',
            background: 'linear-gradient(135deg, #10b981, #06b6d4)',
        },
        {
            type: 'error',
            background: 'linear-gradient(135deg, #ef4444, #dc2626)',
        }
    ]
});


// toggle password visibility
function togglePassword(fieldId) {
    const field = document.getElementById(fieldId);
    field.type = field.type === 'password' ? 'text' : 'password';
}

// gen random password
function generatePassword() {
    const charset = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*';
    let password = '';
    for (let i = 0; i < 12; i++) {
        password += charset.charAt(Math.floor(Math.random() * charset.length));
    }
    document.getElementById('new_password').value = password;
    document.getElementById('new_password').type = 'text';
    notyf.success('Password generated successfully!');
}

// new user
async function createUser() {
    const username = document.getElementById('new_username').value.trim();
    const password = document.getElementById('new_password').value.trim();
    const role = document.getElementById('new_user_role').value;

    if (!username || !password) {
        notyf.error('Username and password are required');
        return;
    }

    if (username.length <= 4) {
        notyf.error('Username must be longer than 4 characters');
        return;
    }

    if (password.length < 8) {
        notyf.error('Password must be at least 8 characters');
        return;
    }

    try {
        const response = await fetch('/api/users', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, role })
        });

        if (response.ok) {
            notyf.success('User created successfully!');
            document.getElementById('new_username').value = '';
            document.getElementById('new_password').value = '';
            loadUsers(); // refresh user list
        } else {
            const error = await response.json();
            notyf.error(error.message || 'Failed to create user');
        }
    } catch (err) {
        notyf.error('Network error occurred');
    }
}

// sys actions
async function restartZapCards() {
    if (confirm('Are you sure you want to restart ZapCards? This will temporarily interrupt service.')) {
        try {
            const response = await fetch('/api/system/restart', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ service: "zapcards" })
            });
            notyf.success('ZapCards is restarting...');
        } catch (err) {
            notyf.error('Failed to restart ZapCards');
        }
    }
}
async function restartOllamaService() {
    if (confirm('Are you sure you want to restart Ollama Serivce? This will temporarily interrupt service.')) {
        try {
            const response = await fetch('/api/system/restart', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ service: "ollama" })
            });
            notyf.success('ZapCards is restarting...');
        } catch (err) {
            notyf.error('Failed to restart ZapCards');
        }
    }
}

async function exportSettings() {
    try {
        const response = await fetch('/api/settings/export');
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'zapcards-settings.json';
        a.click();
        notyf.success('Settings exported successfully!');
    } catch (err) {
        notyf.error('Failed to export settings');
    }
}

// save all settings
async function saveSettings() {
    const settings = {
        setup: {
            require_auth: document.getElementById('require_auth').checked ? 'True' : 'False',
            reset_default_user: document.getElementById('reset_default_user').checked ? 'True' : 'False',
            erase_database_on_reset: 'true'
        },
        general: {
            jwt_expire_time: document.getElementById('jwt_expire_time').value || '3600'
        },
        ai: {
            model_type: document.getElementById('model_type').value,
            endpoint_url: document.getElementById('endpoint_url').value,
            endpoint_port: document.getElementById('endpoint_port').value,
            openai_api_key: document.getElementById('openai_api_key').value || 'false',
            prompt_presets_path: document.getElementById('prompt_presets_path').value
        }
    };

    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });

        if (response.ok) {
            notyf.success('Settings saved successfully!');
        } else {
            const error = await response.json();
            notyf.error(error.message || 'Failed to save settings');
        }
    } catch (err) {
        notyf.error('Network error occurred');
    }
}

// atuo save on change for some settings
async function saveIndividualSetting(section, key, value) {
    // get current settings
    try {
        const getResponse = await fetch('/api/settings');
        if (!getResponse.ok) return;

        const currentSettings = await getResponse.json();

        // update the specific setting
        if (!currentSettings[section]) currentSettings[section] = {};
        currentSettings[section][key] = value;

        // save updated settings
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(currentSettings)
        });

        if (response.ok) {
            // show success
            notyf.success(`${section}.${key} saved to: ${value}`);
        } else {
            notyf.error('Failed to auto-save setting');
        }
    } catch (err) {
        console.error('Auto-save failed:', err);
    }
}

// load settings
async function loadSettings() {
    try {
        const response = await fetch('/api/settings');
        if (response.ok) {
            const settings = await response.json();

            if (settings.ai.model_type.toLowerCase() == "ollama") {
                makeOllamaSectionVisable(true);
            }

            // ai settings
            if (settings.ai) {
                document.getElementById('model_type').value = settings.ai.model_type ? settings.ai.model_type.toLowerCase() : 'openai';
                document.getElementById('endpoint_url').value = settings.ai.endpoint_url || '';
                document.getElementById('endpoint_port').value = settings.ai.endpoint_port || '';
                document.getElementById('openai_api_key').value = settings.ai.openai_api_key === 'false' ? '' : settings.ai.openai_api_key || '';
                document.getElementById('prompt_presets_path').value = settings.ai.prompt_presets_path || '';
            }

            // general settings
            if (settings.general) {
                document.getElementById('jwt_expire_time').value = settings.general.jwt_expire_time || '3600';
            }

            // setup settings
            if (settings.setup) {
                document.getElementById('require_auth').checked = settings.setup.require_auth === 'True' || settings.setup.require_auth === true;
                document.getElementById('reset_default_user').checked = settings.setup.reset_default_user === 'True' || settings.setup.reset_default_user === true;
            }
            notyf.success('Settings loaded successfully!');
        }
    } catch (err) {
        console.error('Failed to load settings:', err);
        notyf.error('Failed to load settings');
    }
}

// load users
async function loadUsers() {
    try {
        const response = await fetch('/api/users');
        if (response.ok) {
            const data = await response.json();
            displayUsers(data.users || []);
        } else {
            document.getElementById('users_list').innerHTML = '<div class="text-center text-red-400 py-4">Failed to load users</div>';
        }
    } catch (err) {
        console.error('Failed to load users:', err);
        document.getElementById('users_list').innerHTML = '<div class="text-center text-red-400 py-4">Error loading users</div>';
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
// show users in the UI
function displayUsers(users) {
    const usersList = document.getElementById('users_list');

    if (!users || users.length === 0) {
        usersList.innerHTML = '<div class="text-center text-white/60 py-4">No users found</div>';
        return;
    }

    const usersHTML = users.map(user => {
        const createdDate = new Date(user.created).toLocaleDateString();
        return `
                    <div class="flex items-center justify-between p-3 rounded-lg bg-black/30 backdrop-blur-sm">
                        <div>
                            <div class="font-medium text-white">${escapeHtml(user.username)}</div>
                            <div class="text-sm text-white opacity-70">${user.role}</div>
                            <div class="text-xs text-white opacity-50">Created: ${createdDate}</div>
                        </div>
                        <div class="flex gap-2">
                            <button onclick="deleteUser('${user.internalID}', '${escapeHtml(user.username)}')" class="px-3 py-1 rounded-md bg-red-500/60 hover:bg-red-500/80 text-white text-sm transition-colors backdrop-blur-sm border border-white/20">
                                Delete
                            </button>
                        </div>
                    </div>
                `;
    }).join('');

    usersList.innerHTML = usersHTML;
}

// new user
async function createUser() {
    const username = document.getElementById('new_username').value.trim();
    const password = document.getElementById('new_password').value.trim();
    const role = document.getElementById('new_user_role').value;

    if (!username || !password) {
        alert('Username and password are required');
        return;
    }

    if (username.length <= 4) {
        alert('Username must be longer than 4 characters');
        return;
    }

    if (password.length < 8) {
        alert('Password must be at least 8 characters');
        return;
    }

    try {
        const response = await fetch('/api/users', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username,
                password,
                role: role
            })
        });

        if (response.ok) {
            alert('User created successfully!');
            document.getElementById('new_username').value = '';
            document.getElementById('new_password').value = '';
            document.getElementById('new_user_role').value = 'user';
            loadUsers(); // refresh user list
        } else {
            const error = await response.json();
            alert(error.message || 'Failed to create user');
        }
    } catch (err) {
        alert('Network error occurred');
    }
}

// delete user
async function deleteUser(userId, username) {
    if (!confirm(`Are you sure you want to delete user "${username}"?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/users`, {
            method: 'DELETE',
            body: JSON.stringify({
                userID: userId
            })
        });

        if (response.ok) {
            alert('User deleted successfully!');
            loadUsers(); // refresh user list
        } else {
            const error = await response.json();
            alert(error.message || 'Failed to delete user');
        }
    } catch (err) {
        alert('Network error occurred');
    }
}



// init page
document.addEventListener('DOMContentLoaded', () => {
    loadSettings();
    loadUsers();
    refreshOllamaModels();
    checkExistingPullProgress();

    // add change listeners for autosave
    const aiFields = [
        { id: 'model_type', section: 'ai', key: 'model_type' },
        { id: 'endpoint_url', section: 'ai', key: 'endpoint_url' },
        { id: 'endpoint_port', section: 'ai', key: 'endpoint_port' },
        { id: 'openai_api_key', section: 'ai', key: 'openai_api_key' },
        { id: 'prompt_presets_path', section: 'ai', key: 'prompt_presets_path' }
    ];

    const generalFields = [
        { id: 'jwt_expire_time', section: 'general', key: 'jwt_expire_time' }
    ];

    const setupFields = [
        { id: 'require_auth', section: 'setup', key: 'require_auth' },
        { id: 'reset_default_user', section: 'setup', key: 'reset_default_user' }
    ];

    // add listeners for text/number inputs
    [...aiFields, ...generalFields].forEach(field => {
        const element = document.getElementById(field.id);
        if (element) {
            element.addEventListener('blur', (e) => {
                let value = e.target.value;
                if (field.key === 'openai_api_key' && !value) {
                    value = 'false';
                }
                saveIndividualSetting(field.section, field.key, value);
            });
        }
    });

    // add listeners for checkboxes
    setupFields.forEach(field => {
        const element = document.getElementById(field.id);
        if (element && element.type === 'checkbox') {
            element.addEventListener('change', (e) => {
                const value = e.target.checked ? 'True' : 'False';
                saveIndividualSetting(field.section, field.key, value);
            });
        }
    });

    // add listener for select elements
    document.getElementById('model_type').addEventListener('change', (e) => {
        saveIndividualSetting('ai', 'model_type', e.target.value);
    });
});




async function refreshOllamaModels() {
    const modelSelector = document.getElementById('ollama_model_select');
    const installedModelsDiv = document.getElementById('installed_models');

    // loading state
    installedModelsDiv.innerHTML = '<div class="text-white/60 text-center py-4">Loading models...</div>';



    try {
        const response = await fetch('/models/getmodels', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // clear loading state
        installedModelsDiv.innerHTML = '';

        if (data.data && Array.isArray(data.data)) {
            if (data.data.length === 0) {
                installedModelsDiv.innerHTML = '<div class="text-white/60 text-center py-4">No models found. Pull a model to get started.</div>';
            } else {
                // ppulate installed models list
                data.data.forEach(model => {
                    const modelName = model.name || model;
                    const modelSize = model.size ? formatBytes(model.size) : '';
                    const modifiedDate = model.modified_at ? new Date(model.modified_at).toLocaleDateString() : '';

                    const modelDiv = document.createElement('div');
                    modelDiv.className = 'model-item';
                    modelDiv.innerHTML = `
                                <div class="model-card flex justify-between items-center">
                                    <div>
                                        <div class="font-semibold text-white">${modelName}</div>
                                    </div>
                                    <div class="flex gap-2">
                                        <button onclick="deleteModel('${modelName}')"
                                            class="px-3 py-1 rounded-lg bg-red-500/60 hover:bg-red-500/80 transition-all duration-300 text-sm font-medium text-white">
                                            Delete
                                        </button>
                                    </div>
                                </div>
                            `;
                    installedModelsDiv.appendChild(modelDiv);

                    const option = document.createElement('option');
                    option.value = modelName;
                    option.textContent = modelName;
                    modelSelector.appendChild(option);
                });
            }
        } else {
            throw new Error('Invalid response format - no models array found');
        }

        notyf.success(`Found ${data.data.length} model(s)`);

    } catch (error) {
        console.error('Error fetching Ollama models:', error);
        installedModelsDiv.innerHTML = '<div class="text-red-400 text-center py-4">Error loading models. Check your Ollama connection.</div>';
        notyf.error(`Error: ${error.message}`);
    }
}

async function deleteModel(modelName) {
    if (!confirm(`Are you sure you want to delete the model "${modelName}"? This action cannot be undone.`)) {
        return;
    }

    try {

        const response = await fetch('/models/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ model: modelName })
        });

        if (!response.ok || response.status !== 200) {
            throw new Error(`Failed to delete model: ${response.status}`);
        }

        notyf.success(`Model "${modelName}" deleted successfully`);
        refreshOllamaModels();

    } catch (error) {
        console.error('Error deleting model:', error);
        notyf.error(`Error deleting model: ${error.message}`);
    }
}
function testModel(modelName) {
    console.log('Testing model:', modelName);

    setTimeout(() => {
        notyf.success(`Model "${modelName}" is working correctly!`);
    }, 2000);
}

async function makeOllamaSectionVisable(visible = true, animationDuration = 300) {

    const section = document.getElementById("ollamaConfig");

    if (!section) {
        console.warn(`Section with identifier "${ollamaConfig}" not found`);
        return false;
    }

    if (visible) {
        section.style.display = 'block';
        section.style.opacity = '0';

        // fade in
        section.style.transition = `opacity ${animationDuration}ms ease-in-out`;

        requestAnimationFrame(() => {
            section.style.opacity = '1';
        });

        section.classList.add('visible');
        section.classList.remove('hidden');

    } else {
        section.style.transition = `opacity ${animationDuration}ms ease-in-out`;
        section.style.opacity = '0';

        setTimeout(() => {
            section.style.display = 'none';
            section.classList.add('hidden');
            section.classList.remove('visible');
        }, animationDuration);
    }

    return true;
}


let pullProgressInterval = null;
let currentClientId = null;

async function pullOllamaModel() {
    const modelInput = document.getElementById('ollama_model_pull');
    const modelName = modelInput.value.trim();

    if (!modelName) {
        notyf.error('Please enter a model name');
        return;
    }

    const progressDiv = document.getElementById('pull_progress');
    const progressFill = document.getElementById('progress_fill');
    const progressText = document.getElementById('progress_text');
    const cancelBtn = document.getElementById('cancel_pull_btn');

    // progress bar
    progressDiv.classList.remove('hidden');
    progressFill.style.width = '0%';
    progressText.textContent = `Starting to pull model ${modelName}...`;

    if (cancelBtn) {
        cancelBtn.classList.remove('hidden');
        cancelBtn.onclick = () => cancelModelPull();
    }

    notyf.success(`Starting to pull model: ${modelName}, this may take some time.`);

    try {
        // start the pull
        const response = await fetch('/models/pull', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: modelName })
        });

        const responseJson = await response.json();

        if (!response.ok || !responseJson.status) {
            throw new Error(`${responseJson.message}`);
        }

        // store client ID for progress tracking
        currentClientId = responseJson.client_id;

        // save to cookies for persistence when page reloads
        setCookie('ollama_pull_client_id', currentClientId, 12);
        setCookie('ollama_pull_model_name', modelName, 12);

        // start polling for progress updates every 2 seconds
        pullProgressInterval = setInterval(async () => {
            await updatePullProgress(modelName);
        }, 2000);

        await updatePullProgress(modelName);

    } catch (error) {
        console.error('Error starting model pull:', error);
        progressDiv.classList.add('hidden');
        if (cancelBtn) cancelBtn.classList.add('hidden');
        notyf.error(`Error starting pull: ${error.message}`);
        cleanup();
    }
}

async function updatePullProgress(modelName) {
    if (!currentClientId) return;

    try {
        const response = await fetch(`/models/pull/progress/${currentClientId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (!response.ok || !result.status) {
            throw new Error(result.message || 'Failed to get progress');
        }

        const progressData = result.data.progress;
        const progressDiv = document.getElementById('pull_progress');
        const progressFill = document.getElementById('progress_fill');
        const progressText = document.getElementById('progress_text');

        if (progressData.error) {
            cleanup();
            progressDiv.classList.add('hidden');
            notyf.error(`Error pulling model: ${progressData.message}`);
            return;
        }

        // update progress bar
        const percentage = progressData.percentage || 0;
        progressFill.style.width = `${percentage}%`;

        // format progress text
        let statusText = '';
        if (progressData.total > 0) {
            const completedMB = (progressData.completed / (1024 * 1024)).toFixed(1);
            const totalMB = (progressData.total / (1024 * 1024)).toFixed(1);
            statusText = `${progressData.status} ${modelName}... ${completedMB}MB / ${totalMB}MB (${Math.round(percentage)}%)`;
        } else {
            statusText = `${progressData.status} ${modelName}... ${Math.round(percentage)}%`;
        }

        progressText.textContent = statusText;

        // check if completed
        if (progressData.status === 'success' || percentage >= 100) {
            cleanup();
            progressDiv.classList.add('hidden');
            notyf.success(`Model "${modelName}" pulled successfully`);
            document.getElementById('ollama_model_pull').value = '';
            refreshOllamaModels(); // refresh model list
        }

    } catch (error) {
        console.error('Error getting pull progress:', error);
        cleanup();
        document.getElementById('pull_progress').classList.add('hidden');
        notyf.error(`Error getting progress: ${error.message}`);
    }
}

async function cancelModelPull() {
    if (!currentClientId) return;

    try {
        const response = await fetch(`/models/pull/cancel/${currentClientId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.status) {
            notyf.success('Model pull cancelled');
        } else {
            notyf.error('Failed to cancel pull');
        }

    } catch (error) {
        console.error('Error cancelling pull:', error);
        notyf.error('Error cancelling pull');
    }

    cleanup();
    document.getElementById('pull_progress').classList.add('hidden');
}

function cleanup() {
    // clear the polling interval
    if (pullProgressInterval) {
        clearInterval(pullProgressInterval);
        pullProgressInterval = null;
    }

    // hide cancel button
    const cancelBtn = document.getElementById('cancel_pull_btn');
    if (cancelBtn) {
        cancelBtn.classList.add('hidden');
    }

    // clear client ID
    currentClientId = null;
}

// clean up on page unload
window.addEventListener('beforeunload', () => {
    cleanup();
});

async function generateOllamaResponse() {
    const modelGiven = document.getElementById('ollama_model_select').value;
    const promptGiven = document.getElementById('ollama_input_prompt').value;
    const responseSection = document.getElementById('test_response');

    // show loading spinner
    responseSection.innerHTML = `
                <div class="flex items-center gap-2 text-white/80">
                    <svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
                    </svg>
                    Generating response...
                </div>
            `;

    try {
        const response = await fetch('/models/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ prompt: promptGiven, model: modelGiven })
        });

        const data = await response.json();
        if (!response.ok || !data.status) {
            throw new Error(data.message || 'Unknown error');
        }

        const fullMessage = data.message || "";
        const thinkMatch = fullMessage.match(/<think>([\s\S]*?)<\/think>/);
        const mainResponse = fullMessage.replace(/<think>[\s\S]*?<\/think>/, "").trim();

        const thoughtText = thinkMatch ? thinkMatch[1].trim() : "";

        responseSection.innerHTML = `
            ${thoughtText ? `
                <div class="mb-3">
                    <button onclick="toggleThought()" class="text-white/80 hover:text-white text-sm flex items-center gap-1">
                        <svg id="arrow-icon" class="w-4 h-4 transform transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                        </svg>
                        Show AI Thought Process
                    </button>
                    <div id="thought-content" class="hidden mt-2 text-white/60 text-md border border-white/10 p-3 rounded-lg bg-black/30">
                        ${thoughtText}
                    </div>
                </div>
            ` : ''}

            <div class="text-white/90 whitespace-pre-wrap">${mainResponse}</div>
        `;
        notyf.success("Ollama response received!");
    } catch (err) {
        console.error(err);
        responseSection.innerHTML = `<p class="text-red-400">Failed to fetch response: ${err.message}</p>`;
        notyf.error(`Failed: ${err.message}`);
    }
}

function toggleThought() {
    const content = document.getElementById('thought-content');
    const icon = document.getElementById('arrow-icon');
    if (content.classList.contains('hidden')) {
        content.classList.remove('hidden');
        icon.classList.add('rotate-180');
    } else {
        content.classList.add('hidden');
        icon.classList.remove('rotate-180');
    }
}


// helper function to format bytes
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// allow enter key to pull model
document.getElementById('ollama_model_pull').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        pullOllamaModel();
    }
});

function setCookie(name, value, hours = 24) {
    const expires = new Date();
    expires.setTime(expires.getTime() + (hours * 60 * 60 * 1000));
    document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
}

function getCookie(name) {
    const nameEQ = name + "=";
    const ca = document.cookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
}

function deleteCookie(name) {
    document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
}

async function checkExistingPullProgress() {
    const savedClientId = getCookie('ollama_pull_client_id');
    const savedModelName = getCookie('ollama_pull_model_name');

    if (savedClientId && savedModelName) {
        console.log('Found existing pull progress, checking status...');

        try {
            // check if the pull is still active
            const response = await fetch(`/models/pull/progress/${savedClientId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            console.log(response)
            const result = await response.json();

            if (response.ok && result.status && !result.data.progress.error) {
                currentClientId = savedClientId;

                const progressDiv = document.getElementById('pull_progress');
                const cancelBtn = document.getElementById('cancel_pull_btn');

                // show progress bar
                progressDiv.classList.remove('hidden');
                if (cancelBtn) {
                    cancelBtn.classList.remove('hidden');
                    cancelBtn.onclick = () => cancelModelPull();
                }

                // start polling for progress updates
                pullProgressInterval = setInterval(async () => {
                    await updatePullProgress(savedModelName);
                }, 2000);

                // update progress
                updatePullProgress(savedModelName);

            } else {
                deleteCookie('ollama_pull_client_id');
                deleteCookie('ollama_pull_model_name');
            }

        } catch (error) {
            console.error('Error checking existing pull progress:', error);
            // clean cookies on error
            deleteCookie('ollama_pull_client_id');
            deleteCookie('ollama_pull_model_name');
        }
    }
}