// =====================================================
// config.js - Configuration modal management
// =====================================================

let allEnvVars = {};

// Load configuration
async function loadConfig() {
    try {
        const resp = await fetch('/config');
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        const cfg = await resp.json();
        
        allEnvVars = cfg.vars || {};
        
        // Generate dynamic config form
        const formSection = document.querySelector('#configModal .form-section');
        formSection.innerHTML = '';
        
        const sortedKeys = Object.keys(allEnvVars).sort();
        
        if (sortedKeys.length === 0) {
            formSection.innerHTML = '<p class="form-help" style="text-align: center;">No environment variables found in .env</p>';
            return;
        }
        
        sortedKeys.forEach(key => {
            const varData = allEnvVars[key];
            const isSecret = varData.is_secret;
            const present = varData.present;
            
            const formGroup = document.createElement('div');
            formGroup.className = 'form-group';
            
            // Label with badge
            const label = document.createElement('label');
            label.className = 'form-label';
            label.innerHTML = `
                ${key}
                <span class="badge ${present ? 'present' : 'absent'}">${present ? 'present' : 'absent'}</span>
            `;
            
            // Input (password for secrets, text for others)
            const input = document.createElement('input');
            input.id = `env_${key}`;
            input.type = isSecret ? 'password' : 'text';
            input.className = 'form-input';
            input.placeholder = isSecret 
                ? 'New value (leave empty to keep current)' 
                : (varData.value || 'Enter value');
            input.value = ''; // Always empty for security
            
            // Help text with current masked value for secrets
            const help = document.createElement('div');
            help.className = 'form-help';
            if (isSecret && present) {
                help.textContent = `Current: ${varData.masked_value}`;
            } else if (!isSecret && present) {
                help.textContent = `Current: ${varData.value}`;
            } else {
                help.textContent = 'Not set';
            }
            
            formGroup.appendChild(label);
            formGroup.appendChild(input);
            formGroup.appendChild(help);
            formSection.appendChild(formGroup);
        });
        
    } catch (e) {
        console.error('Failed to load config:', e);
        showConfigStatus('❌ Failed to load config: ' + e.message, 'error');
    }
}

// Save configuration
async function saveConfig() {
    try {
        const payload = {};
        
        // Collect all non-empty values
        Object.keys(allEnvVars).forEach(key => {
            const input = document.getElementById(`env_${key}`);
            if (input && input.value.trim()) {
                payload[key] = input.value.trim();
            }
        });
        
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
        showConfigStatus(`✅ Saved ${data.updated} variable(s) successfully`, 'success');
        
        // Clear all password fields
        Object.keys(allEnvVars).forEach(key => {
            const input = document.getElementById(`env_${key}`);
            if (input && allEnvVars[key].is_secret) {
                input.value = '';
            }
        });
        
        // Reload to show updated values
        await loadConfig();
    } catch (e) {
        showConfigStatus('❌ Failed to save: ' + e.message, 'error');
    }
}

// Show config status message
function showConfigStatus(message, type) {
    const el = document.getElementById('configStatus');
    el.textContent = message;
    el.className = 'config-status ' + type;
    el.style.display = 'block';
    setTimeout(() => { el.style.display = 'none'; }, 5000);
}

// Open config modal
function openConfig() {
    document.getElementById('configModal').classList.add('active');
    loadConfig();
}

// Close config modal
function closeConfig() {
    document.getElementById('configModal').classList.remove('active');
}

// Close modal on outside click
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('configModal').addEventListener('click', (e) => {
        if (e.target.id === 'configModal') {
            closeConfig();
        }
    });
});
