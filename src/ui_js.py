CONTROL_JS = '''
let tools = [];
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
        ghBadge.textContent = cfg.GITHUB_TOKEN.present ? ('present ' + (cfg.GITHUB_TOKEN.masked || '')) : 'absent';
        aiBadge.textContent = cfg.AI_PORTAL_TOKEN.present ? ('present ' + (cfg.AI_PORTAL_TOKEN.masked || '')) : 'absent';
        if (epInput) epInput.value = cfg.LLM_ENDPOINT || '';
        updateConfigStatus('✅ Configuration chargée', 'success');
    } catch (e) {
        updateConfigStatus('❌ Impossible de charger la configuration: ' + e.message, 'error');
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
            updateConfigStatus('ℹ️ Rien à enregistrer (aucune valeur renseignée).', '');
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
        updateConfigStatus('💾 Sauvegardé (' + data.updated + ' clé(s)) → ' + JSON.stringify(data.masked), 'success');
        document.getElementById('GITHUB_TOKEN').value = '';
        document.getElementById('AI_PORTAL_TOKEN').value = '';
        await loadConfig();
    } catch (e) {
        updateConfigStatus('❌ Enregistrement échoué: ' + e.message, 'error');
    }
}

function updateConfigStatus(message, type) {
    const el = document.getElementById('configStatus');
    el.textContent = message;
    el.className = 'status ' + (type || '');
}

// ----------------------
// Tools UI
// ----------------------
function saveFormValues() {
    const formData = {};
    const inputs = document.querySelectorAll('.param-input, .param-select');
    inputs.forEach(input => {
        if (input.value) {
            formData[input.id] = input.value;
        }
    });
    return formData;
}

function restoreFormValues(formData) {
    Object.keys(formData).forEach(inputId => {
        const input = document.getElementById(inputId);
        if (input) {
            input.value = formData[inputId];
        }
    });
}

async function loadTools(preserveValues = false) {
    let formData = {};
    if (preserveValues) formData = saveFormValues();
    try {
        const response = await fetch('/tools');
        if (response.ok) {
            tools = await response.json();
            renderTools();
            if (preserveValues && Object.keys(formData).length > 0) {
                setTimeout(() => restoreFormValues(formData), 100);
                updateStatus(`✅ Reloaded ${tools.length} tools (form values preserved): ${tools.map(t => t.name).join(', ')}`, 'success');
            } else {
                updateStatus(`Loaded ${tools.length} tools: ${tools.map(t => t.name).join(', ')}`, 'success');
            }
        } else {
            updateStatus(`Failed to load tools: ${response.statusText}`, 'error');
        }
    } catch (error) {
        updateStatus(`Error loading tools: ${error.message}`, 'error');
    }
}

async function reloadTools() {
    updateStatus('🔄 Force reloading tools (preserving form values)...', '');
    try {
        const response = await fetch('/tools?reload=1');
        if (response.ok) {
            const formData = saveFormValues();
            tools = await response.json();
            renderTools();
            if (Object.keys(formData).length > 0) {
                setTimeout(() => restoreFormValues(formData), 100);
                updateStatus(`✅ Force reloaded ${tools.length} tools (✅ form values preserved): ${tools.map(t => t.name).join(', ')}`, 'success');
            } else {
                updateStatus(`✅ Force reloaded ${tools.length} tools: ${tools.map(t => t.name).join(', ')}`, 'success');
            }
        } else {
            updateStatus(`❌ Failed to reload tools: ${response.statusText}`, 'error');
        }
    } catch (error) {
        updateStatus(`❌ Error reloading tools: ${error.message}`, 'error');
    }
}

function updateStatus(message, type) {
    const statusEl = document.getElementById('status');
    statusEl.textContent = message;
    statusEl.className = 'status ' + type;
}

function renderTools() {
    const grid = document.getElementById('toolGrid');
    grid.innerHTML = '';
    tools.forEach(tool => {
        const card = createToolCard(tool);
        grid.appendChild(card);
    });
}

function createToolCard(tool) {
    const card = document.createElement('div');
    card.className = 'tool-card';
    let spec;
    try { spec = JSON.parse(tool.json); }
    catch (e) { card.innerHTML = '<div class="tool-title">❌ Error</div><div class="error">Invalid tool spec</div>'; return card; }
    const params = spec.function.parameters.properties || {};
    const required = spec.function.parameters.required || [];
    let html = `
        <div class="tool-title">🔧 ${tool.displayName} (ID: ${tool.id})</div>
        <div class="tool-description">${tool.description}</div>
    `;
    Object.keys(params).forEach(paramName => {
        const param = params[paramName];
        const isRequired = required.includes(paramName);
        html += `
            <div class="param-group">
                <label class="param-label">
                    ${paramName}${isRequired ? '<span class="required-mark"> *</span>' : ''}
                </label>
        `;
        if (param.enum && param.enum.length > 0) {
            html += `
                <select id="${tool.name}_${paramName}" class="param-select" ${isRequired ? 'required' : ''}>
                    <option value="">-- Select ${paramName} --</option>
            `;
            param.enum.forEach(option => { html += `<option value="${option}">${option}</option>`; });
            html += `</select>`;
            html += `<div class="enum-options">Available: ${param.enum.join(', ')}</div>`;
        } else {
            const placeholder = param.type === 'number' ? 'Enter number' : param.enum ? param.enum[0] : 'Enter value';
            html += `
                <input type="text" id="${tool.name}_${paramName}" class="param-input" placeholder="${placeholder}" ${isRequired ? 'required' : ''}>
            `;
        }
        if (param.description) { html += `<div class="param-help">${param.description}</div>`; }
        html += `</div>`;
    });
    html += `
        <button class="execute-btn" onclick="executeTool('${tool.name}')">▶️ Execute ${tool.displayName}</button>
        <div id="${tool.name}_result" class="result-area">Ready to execute...</div>
    `;
    card.innerHTML = html; return card;
}

async function executeTool(toolName) {
    const tool = tools.find(t => t.name === toolName);
    if (!tool) return;
    const resultDiv = document.getElementById(toolName + '_result');
    const card = resultDiv.closest('.tool-card');
    try {
        card.classList.add('loading');
        resultDiv.textContent = '⏳ Executing...';
        resultDiv.className = 'result-area';
        const spec = JSON.parse(tool.json);
        const params = {};
        const paramDefs = spec.function.parameters.properties || {};
        for (const paramName of Object.keys(paramDefs)) {
            const input = document.getElementById(`${toolName}_${paramName}`);
            if (input && input.value.trim()) {
                let value = input.value.trim();
                if (paramDefs[paramName].type === 'number') {
                    const num = parseFloat(value);
                    if (isNaN(num)) { throw new Error(`Parameter "${paramName}" must be a valid number`); }
                    params[paramName] = num;
                } else { params[paramName] = value; }
            }
        }
        const required = spec.function.parameters.required || [];
        for (const reqParam of required) { if (!(reqParam in params)) { throw new Error(`Required parameter "${reqParam}" is missing`); } }
        const response = await fetch('/execute', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ tool_reg: toolName, params }) });
        if (response.ok) { const result = await response.json(); resultDiv.textContent = `✅ Result:\n${JSON.stringify(result.result, null, 2)}`; resultDiv.className = 'result-area success'; }
        else { const error = await response.json(); resultDiv.textContent = `❌ Error: ${error.detail}`; resultDiv.className = 'result-area error'; }
    } catch (error) { resultDiv.textContent = `❌ Error: ${error.message}`; resultDiv.className = 'result-area error'; }
    finally { card.classList.remove('loading'); }
}

setInterval(async function() {
    try {
        const response = await fetch('/tools', { method: 'HEAD' });
        if (response.headers.get('ETag') !== currentETag) {
            const formData = saveFormValues();
            const loadResponse = await fetch('/tools');
            if (loadResponse.ok) {
                const newTools = await loadResponse.json();
                if (newTools.length !== tools.length || JSON.stringify(newTools.map(t => t.name).sort()) !== JSON.stringify(tools.map(t => t.name).sort())) {
                    tools = newTools; renderTools(); setTimeout(() => restoreFormValues(formData), 100); updateStatus(`🔄 Auto-detected ${tools.length} tools: ${tools.map(t => t.name).join(', ')}`, 'success');
                }
            }
            currentETag = response.headers.get('ETag');
        }
    } catch (error) { }
}, 5000);

document.addEventListener('DOMContentLoaded', () => { loadTools(false); loadConfig(); });
'''
