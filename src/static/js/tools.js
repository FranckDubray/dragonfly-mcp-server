// =====================================================
// tools.js - Tools loading, rendering and execution
// =====================================================

let tools = [];
let currentTool = null;
let currentETag = null;
let favorites = new Set(JSON.parse(localStorage.getItem('favorites') || '[]'));

// Load tools from server
async function loadTools() {
    try {
        updateStatus('⏳ Loading tools...', '');
        const response = await fetch('/tools');
        
        if (response.ok) {
            tools = await response.json();
            renderToolsList('');
            updateStatus(`✅ Loaded ${tools.length} tools`, 'success');
            currentETag = response.headers.get('ETag');
        } else {
            updateStatus(`❌ Failed to load tools: ${response.statusText}`, 'error');
        }
    } catch (error) {
        updateStatus(`❌ Error loading tools: ${error.message}`, 'error');
    }
}

// Render tools list grouped by category (with optional text filter)
function renderToolsList(filterQuery = '') {
    const list = document.getElementById('toolsList');
    list.innerHTML = '';

    const q = (filterQuery || '').toLowerCase().trim();
    const grouped = groupToolsByCategory(tools); // tag filtering is applied in search.js wrapper

    const tagFilterActive = (typeof window !== 'undefined' && typeof activeTag !== 'undefined' && activeTag !== null);
    const hasAnyFilter = tagFilterActive || q.length > 0;

    // Favorites section (only when no filter and there are favorites)
    if (!hasAnyFilter && favorites.size > 0) {
        const favItems = tools.filter(t => favorites.has(t.name));
        if (favItems.length > 0) {
            list.appendChild(buildCategorySection('__favorites__', {emoji: '⭐', label: 'Favorites'}, favItems, q, hasAnyFilter));
        }
    }

    // Render each category in canonical order
    CATEGORIES.forEach(categoryMeta => {
        const items = grouped[categoryMeta.key] || [];
        if (!items || items.length === 0) return;
        list.appendChild(buildCategorySection(categoryMeta.key, categoryMeta, items, q, hasAnyFilter));
    });
}

function buildCategorySection(key, meta, items, q, hasAnyFilter) {
    // Text filter per tool
    const filtered = q
        ? items.filter(t => {
            const dn = (t.displayName || '').toLowerCase();
            const nm = (t.name || '').toLowerCase();
            return dn.includes(q) || nm.includes(q) || (meta.label || '').toLowerCase().includes(q);
          })
        : items;

    if (!filtered || filtered.length === 0) return document.createComment('empty');

    // Create category section
    const section = document.createElement('div');
    section.className = 'category-section';
    section.dataset.category = key;

    // Header
    const header = document.createElement('div');
    header.className = 'category-header';
    header.innerHTML = `
        <span class="category-emoji">${meta.emoji || '🧰'}</span>
        <span>${meta.label || key}</span>
        <span class="category-count">${filtered.length}</span>
        <span class="category-chevron">▾</span>
    `;
    header.addEventListener('click', () => {
        section.classList.toggle('collapsed');
    });
    section.appendChild(header);

    // Tools container
    const toolsContainer = document.createElement('div');
    toolsContainer.className = 'category-tools';

    // Sort tools alphabetically by displayName
    const sortedTools = [...filtered].sort((a, b) => {
        const nameA = (a.displayName || a.name || '').toLowerCase();
        const nameB = (b.displayName || b.name || '').toLowerCase();
        return nameA.localeCompare(nameB);
    });

    // Render tools in this category
    sortedTools.forEach(tool => {
        const item = document.createElement('div');
        item.className = 'tool-item';
        item.onclick = (e) => selectTool(tool, e);

        const icon = getToolIcon(tool.name);
        const isFav = favorites.has(tool.name);

        item.innerHTML = `
            <span class="tool-icon">${icon}</span>
            <span class="tool-name">${tool.displayName || tool.name}</span>
            <span class="tool-badge" title="${tool.name}">${tool.name}</span>
            <button class="fav-btn" title="Pin/Unpin">${isFav ? '★' : '☆'}</button>
        `;

        const favBtn = item.querySelector('.fav-btn');
        favBtn.addEventListener('click', (ev) => {
            ev.stopPropagation();
            toggleFavorite(tool.name, favBtn);
        });

        toolsContainer.appendChild(item);
    });

    section.appendChild(toolsContainer);

    // Collapsed by default (no filter), expanded when searching/tag filtering
    if (!hasAnyFilter) {
        section.classList.add('collapsed');
    }

    return section;
}

function toggleFavorite(toolName, btnEl) {
    if (favorites.has(toolName)) {
        favorites.delete(toolName);
    } else {
        favorites.add(toolName);
    }
    localStorage.setItem('favorites', JSON.stringify(Array.from(favorites)));
    if (btnEl) btnEl.textContent = favorites.has(toolName) ? '★' : '☆';

    // Re-render list to keep favorites section in sync
    const searchInput = document.getElementById('searchInput');
    renderToolsList(searchInput ? searchInput.value : '');
}

// Get tool icon (emoji)
function getToolIcon(toolName) {
    const icons = {
        'call_llm': '🤖',
        'ollama_local': '🦙',
        'academic_research_super': '📚',
        'git': '🧬',
        'gitbook': '📖',
        'email_send': '📨',
        'imap': '📧',
        'discord_webhook': '💬',
        'sqlite_db': '🗄️',
        'excel_to_sqlite': '📊',
        'script_executor': '🐍',
        'pdf_download': '📥',
        'pdf_search': '🔍',
        'pdf2text': '📄',
        'office_to_pdf': '📝',
        'universal_doc_scraper': '🕷️',
        'youtube_search': '🔎',
        'youtube_download': '📺',
        'video_transcribe': '🎥',
        'ffmpeg_frames': '🎞️',
        'flight_tracker': '✈️',
        'aviation_weather': '🌤️',
        'ship_tracker': '🚢',
        'velib': '🚲',
        'http_client': '🌐',
        'math': '🔢',
        'date': '📅',
        'chess_com': '♟️',
        'reddit_intelligence': '🎯',
        'generate_edit_image': '🖼️'
    };
    return icons[toolName] || '🛠️';
}

// Select a tool
function selectTool(tool, event) {
    currentTool = tool;

    // Update active state
    document.querySelectorAll('.tool-item').forEach(item => {
        item.classList.remove('active');
    });
    if (event && event.currentTarget) event.currentTarget.classList.add('active');

    // Render tool view
    renderToolView(tool);
}

// Render tool view (form + result)
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
    const category = spec.function.category || '';
    const catMeta = (typeof getCategoryMeta === 'function') ? getCategoryMeta(category) : {emoji:'🧰', label: category};

    let html = `
        <div class="tool-view">
            <div class="tool-header">
                <h1 class="tool-title">
                    ${getToolIcon(tool.name)} ${tool.displayName || tool.name}
                    <span class="tool-badge" style="margin-left:8px;">${catMeta.emoji} ${catMeta.label}</span>
                    <span class="tool-badge" title="Technical name" style="margin-left:6px; background:#eef2ff; color:#3730a3;">${tool.name}</span>
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
                <button class="execute-btn" id="executeBtn">▶️ Execute</button>
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

    // Bind execute button + one-time shortcut
    document.getElementById('executeBtn').addEventListener('click', executeTool);
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            executeTool();
        }
    }, { once: true });
}

// Execute tool
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
            let errorText = '';
            try { errorText = JSON.stringify(await response.json(), null, 2); } catch { errorText = await response.text(); }
            resultBody.textContent = `❌ Error\n\n${errorText}`;
            resultBody.className = 'result-body error';
        }
    } catch (error) {
        resultBody.textContent = `❌ Error\n\n${error.message}`;
        resultBody.className = 'result-body error';
    }
}

// Update status bar
function updateStatus(message, type) {
    const statusBar = document.getElementById('statusBar');
    statusBar.textContent = message;
    statusBar.className = 'status-bar ' + type;
}
