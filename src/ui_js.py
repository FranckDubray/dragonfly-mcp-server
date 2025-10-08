CONTROL_JS = '''
let tools = [];
let currentTool = null;
let currentETag = null;

// ----------------------
// Config (tokens) helpers
// ----------------------
async function loadConfig() {
    try {
        const resp = await fetch('/config');
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        const cfg = await resp.json();
        
        const ghBadge = document.getElementById('ghBadge');
        const aiBadge = document.getElementById('aiBadge');
        const epInput = document.getElementById('LLM_ENDPOINT');
        
        ghBadge.textContent = cfg.GITHUB_TOKEN.present ? 'present' : 'absent';
        ghBadge.className = 'badge ' + (cfg.GITHUB_TOKEN.present ? 'present' : 'absent');
        
        aiBadge.textContent = cfg.AI_PORTAL_TOKEN.present ? 'present' : 'absent';
        aiBadge.className = 'badge ' + (cfg.AI_PORTAL_TOKEN.present ? 'present' : 'absent');
        
        if (epInput) epInput.value = cfg.LLM_ENDPOINT || '';
    } catch (e) {
        console.error('Failed to load config:', e);
    }
}

async function saveConfig() {
    try {
        const gh = document.getElementById('GITHUB_TOKEN').value.trim();
        const ai = document.getElementById('AI_PORTAL_TOKEN').value.trim();
        const ep = document.getElementById('LLM_ENDPOINT').value.trim();
        
        const payload = {};
        if (gh) payload.GITHUB_TOKEN = gh;
        if (ai) payload.AI_PORTAL_TOKEN = ai;
        if (ep) payload.LLM_ENDPOINT = ep;
        
        if (Object.keys(payload).length === 0) {
            showConfigStatus('ℹ️ No changes to save', '');
            return;
        }
        
        const resp = await fetch('/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!resp.ok) {
            const err = await resp.text();
            throw new Error(err || ('HTTP ' + resp.status));
        }
        
        const data = await resp.json();
        showConfigStatus('✅ Configuration saved successfully', 'success');
        
        // Clear password fields
        document.getElementById('GITHUB_TOKEN').value = '';
        document.getElementById('AI_PORTAL_TOKEN').value = '';
        
        await loadConfig();
    } catch (e) {
        showConfigStatus('❌ Failed to save: ' + e.message, 'error');
    }
}

function showConfigStatus(message, type) {
    const el = document.getElementById('configStatus');
    el.textContent = message;
    el.className = 'config-status ' + type;
    el.style.display = 'block';
    setTimeout(() => { el.style.display = 'none'; }, 5000);
}

function openConfig() {
    document.getElementById('configModal').classList.add('active');
    loadConfig();
}

function closeConfig() {
    document.getElementById('configModal').classList.remove('active');
}

// ----------------------
// Tools UI
// ----------------------
async function loadTools() {
    try {
        updateStatus('⏳ Loading tools...', '');
        const response = await fetch('/tools');
        
        if (response.ok) {
            tools = await response.json();
            renderToolsList();
            updateStatus(`✅ Loaded ${tools.length} tools`, 'success');
            currentETag = response.headers.get('ETag');
        } else {
            updateStatus(`❌ Failed to load tools: ${response.statusText}`, 'error');
        }
    } catch (error) {
        updateStatus(`❌ Error loading tools: ${error.message}`, 'error');
    }
}

function renderToolsList() {
    const list = document.getElementById('toolsList');
    list.innerHTML = '';
    
    tools.forEach(tool => {
        const item = document.createElement('div');
        item.className = 'tool-item';
        item.onclick = () => selectTool(tool);
        
        const icon = getToolIcon(tool.name);
        item.innerHTML = `
            <span class="tool-icon">${icon}</span>
            <span class="tool-name">${tool.displayName || tool.name}</span>
        `;
        
        list.appendChild(item);
    });
}

function getToolIcon(toolName) {
    const icons = {
        'call_llm': '🤖',
        'math': '🔢',
        'date': '📅',
        'git': '🐙',
        'imap': '📧',
        'velib': '🚲',
        'pdf_download': '📥',
        'pdf_search': '🔍',
        'pdf2text': '📄',
        'sqlite_db': '🗄️',
        'http_client': '🌐',
        'discord_webhook': '💬',
        'script_executor': '🐍',
        'academic_research_super': '📚',
        'universal_doc_scraper': '🕷️',
        'ffmpeg_frames': '🎬',
        'gitbook': '📖',
        'reddit_intelligence': '🔮'
    };
    return icons[toolName] || '🔧';
}

function selectTool(tool) {
    currentTool = tool;
    
    // Update active state
    document.querySelectorAll('.tool-item').forEach(item => {
        item.classList.remove('active');
    });
    event.currentTarget.classList.add('active');
    
    // Render tool view
    renderToolView(tool);
}

function renderToolView(tool) {
    const mainView = document.getElementById('mainView');
    
    let spec;
    try {
        spec = JSON.parse(tool.json);
    } catch (e) {
        mainView.innerHTML = `
            <div class="tool-view">
                <div class="tool-header">
                    <h1 class="tool-title">❌ Error</h1>
                    <p class="tool-description">Invalid tool specification</p>
                </div>
            </div>
        `;
        return;
    }
    
    const params = spec.function.parameters.properties || {};
    const required = spec.function.parameters.required || [];
    
    let html = `
        <div class="tool-view">
            <div class="tool-header">
                <h1 class="tool-title">
                    ${getToolIcon(tool.name)} ${tool.displayName || tool.name}
                </h1>
                <p class="tool-description">${tool.description}</p>
            </div>
            
            <div class="form-section">
    `;
    
    // Generate form fields
    Object.keys(params).forEach(paramName => {
        const param = params[paramName];
        const isRequired = required.includes(paramName);
        
        html += `
            <div class="form-group">
                <label class="form-label">
                    ${paramName}${isRequired ? '<span class="required-mark"> *</span>' : ''}
                </label>
        `;
        
        if (param.enum && param.enum.length > 0) {
            html += `
                <select id="param_${paramName}" class="form-select" ${isRequired ? 'required' : ''}>
                    <option value="">-- Select ${paramName} --</option>
            `;
            param.enum.forEach(option => {
                html += `<option value="${option}">${option}</option>`;
            });
            html += `</select>`;
        } else if (param.type === 'boolean') {
            html += `
                <select id="param_${paramName}" class="form-select">
                    <option value="">-- Select --</option>
                    <option value="true">true</option>
                    <option value="false">false</option>
                </select>
            `;
        } else {
            const placeholder = param.type === 'number' ? 'Enter number' : 
                              param.type === 'integer' ? 'Enter integer' :
                              'Enter value';
            html += `
                <input type="text" 
                       id="param_${paramName}" 
                       class="form-input" 
                       placeholder="${placeholder}"
                       ${isRequired ? 'required' : ''}>
            `;
        }
        
        if (param.description) {
            html += `<div class="form-help">${param.description}</div>`;
        }
        
        if (param.enum && param.enum.length > 0) {
            html += `<div class="enum-hint">Options: ${param.enum.join(', ')}</div>`;
        }
        
        html += `</div>`;
    });
    
    html += `
                <button class="execute-btn" onclick="executeTool()">▶️ Execute</button>
            </div>
            
            <div id="resultSection" style="display: none;" class="result-section">
                <div class="result-header">
                    <span class="result-title">Result</span>
                </div>
                <div id="resultBody" class="result-body empty">
                    No result yet
                </div>
            </div>
        </div>
    `;
    
    mainView.innerHTML = html;
}

async function executeTool() {
    if (!currentTool) return;
    
    const resultSection = document.getElementById('resultSection');
    const resultBody = document.getElementById('resultBody');
    
    try {
        // Show loading
        resultSection.style.display = 'block';
        resultBody.textContent = '⏳ Executing...';
        resultBody.className = 'result-body';
        
        // Parse spec
        const spec = JSON.parse(currentTool.json);
        const paramDefs = spec.function.parameters.properties || {};
        const required = spec.function.parameters.required || [];
        
        // Collect parameters
        const params = {};
        for (const paramName of Object.keys(paramDefs)) {
            const input = document.getElementById(`param_${paramName}`);
            if (input && input.value.trim()) {
                let value = input.value.trim();
                
                // Type conversion
                if (paramDefs[paramName].type === 'number') {
                    const num = parseFloat(value);
                    if (isNaN(num)) {
                        throw new Error(`Parameter "${paramName}" must be a valid number`);
                    }
                    params[paramName] = num;
                } else if (paramDefs[paramName].type === 'integer') {
                    const num = parseInt(value, 10);
                    if (isNaN(num)) {
                        throw new Error(`Parameter "${paramName}" must be a valid integer`);
                    }
                    params[paramName] = num;
                } else if (paramDefs[paramName].type === 'boolean') {
                    params[paramName] = value === 'true';
                } else {
                    params[paramName] = value;
                }
            }
        }
        
        // Validate required params
        for (const reqParam of required) {
            if (!(reqParam in params)) {
                throw new Error(`Required parameter "${reqParam}" is missing`);
            }
        }
        
        // Execute
        const response = await fetch('/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                tool: currentTool.name,
                params: params
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            resultBody.textContent = `✅ Success\n\n${JSON.stringify(result, null, 2)}`;
            resultBody.className = 'result-body success';
        } else {
            const error = await response.json();
            resultBody.textContent = `❌ Error\n\n${error.detail || JSON.stringify(error, null, 2)}`;
            resultBody.className = 'result-body error';
        }
    } catch (error) {
        resultBody.textContent = `❌ Error\n\n${error.message}`;
        resultBody.className = 'result-body error';
    }
}

function updateStatus(message, type) {
    const statusBar = document.getElementById('statusBar');
    statusBar.textContent = message;
    statusBar.className = 'status-bar ' + type;
}

// Search functionality
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        document.querySelectorAll('.tool-item').forEach(item => {
            const toolName = item.querySelector('.tool-name').textContent.toLowerCase();
            if (toolName.includes(query)) {
                item.style.display = 'flex';
            } else {
                item.style.display = 'none';
            }
        });
    });
    
    // Load tools on start
    loadTools();
});

// Auto-reload tools (check every 5s)
setInterval(async () => {
    try {
        const response = await fetch('/tools', { method: 'HEAD' });
        const newETag = response.headers.get('ETag');
        
        if (newETag && newETag !== currentETag) {
            const loadResponse = await fetch('/tools');
            if (loadResponse.ok) {
                const newTools = await loadResponse.json();
                
                if (newTools.length !== tools.length || 
                    JSON.stringify(newTools.map(t => t.name).sort()) !== 
                    JSON.stringify(tools.map(t => t.name).sort())) {
                    tools = newTools;
                    renderToolsList();
                    updateStatus(`🔄 Auto-reloaded ${tools.length} tools`, 'success');
                }
            }
            currentETag = newETag;
        }
    } catch (error) {
        // Silent fail for background refresh
    }
}, 5000);

// Close modal on outside click
document.getElementById('configModal').addEventListener('click', (e) => {
    if (e.target.id === 'configModal') {
        closeConfig();
    }
});
'''
