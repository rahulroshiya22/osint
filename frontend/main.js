/* ═══════════════════════════════════════════════════
   OSINT Dashboard — Main JavaScript
   ═══════════════════════════════════════════════════ */

const API_BASE = window.location.origin;
let botsConfig = {};

document.addEventListener('DOMContentLoaded', async () => {
    // Intro Animation Sequence
    setTimeout(() => {
        document.getElementById('intro-screen').classList.remove('active');
        const token = localStorage.getItem('token');
        if (token === '#rahul#123_verified') {
            initDashboard();
        } else {
            showScreen('auth-screen');
        }
    }, 2500); // Intro lasts 2.5 seconds

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const f = document.querySelector('.auth-form:not(.hidden)');
            if (f) verifyPassword();
        }
    });
});

// ──────────────── API ────────────────
async function apiRequest(method, path, body = null) {
    const h = { 'Content-Type': 'application/json' };
    const t = localStorage.getItem('token');
    if (t) h['Authorization'] = `Bearer ${t}`;
    const opts = { method, headers: h };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(`${API_BASE}${path}`, opts);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Request failed');
    return data;
}
const apiGet = (p) => apiRequest('GET', p);
const apiPost = (p, b) => apiRequest('POST', p, b);

// ──────────────── Screens ────────────────
function showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(id)?.classList.add('active');
}

// ──────────────── Auth ────────────────
function showAuthMessage(m, t = 'error') { const el = document.getElementById('auth-message'); el.textContent = m; el.className = `auth-message ${t}`; el.classList.remove('hidden'); }

async function verifyPassword() {
    const p = document.getElementById('login-password').value;
    if (!p) return showAuthMessage('Enter access code');
    const btn = document.getElementById('login-btn'); setButtonLoading(btn, true);
    try {
        const d = await apiPost('/api/verify', { password: p });
        if (d.success) {
            localStorage.setItem('token', '#rahul#123_verified');
            showToast('Access Granted', 'success');
            await initDashboard();
        } else {
            showAuthMessage('Invalid access code');
        }
    } catch (e) { showAuthMessage(e.message); } finally { setButtonLoading(btn, false); }
}

function handleLogout() { 
    localStorage.removeItem('token'); 
    showScreen('auth-screen'); 
    document.getElementById('login-password').value = '';
}

// ──────────────── Dashboard ────────────────
async function initDashboard() {
    showScreen('dashboard-screen');
    try { const d = await apiGet('/api/bots'); botsConfig = d.bots; buildToolPanels(); } catch (e) { showToast('Failed to load bots', 'error'); }
    switchTab('number_to_info');
}

function buildToolPanels() {
    for (const [key, cfg] of Object.entries(botsConfig)) {
        const p = document.getElementById(`panel-${key}`);
        if (!p) continue;
        p.innerHTML = `
            <div class="tool-header">
                <h2><span class="icon-3d-text pulse">${cfg.icon}</span> ${cfg.display_name}</h2>
                <p>${cfg.description}</p>
            </div>
            <div class="search-box">
                <input type="text" id="input-${key}" placeholder="${cfg.input_placeholder}" onkeydown="if(event.key==='Enter')performLookup('${key}')">
                <button class="btn-3d" onclick="performLookup('${key}')" id="btn-${key}">
                    <span class="btn-text">Search 🚀</span>
                    <span class="btn-loader hidden"></span>
                </button>
            </div>
            <div id="result-${key}"></div>
        `;
    }
}

// ──────────────── Tabs ────────────────
function switchTab(id) {
    document.querySelectorAll('.tab-btn').forEach(n => n.classList.remove('active'));
    document.querySelector(`.tab-btn[data-tab="${id}"]`)?.classList.add('active');
    document.querySelectorAll('.tool-panel').forEach(p => p.classList.remove('active'));
    document.getElementById(`panel-${id}`)?.classList.add('active');
}

// ──────────────── LOOKUP ────────────────
async function performLookup(botKey) {
    const input = document.getElementById(`input-${botKey}`).value.trim();
    if (!input) return showToast('Enter a value', 'error');

    const btn = document.getElementById(`btn-${botKey}`);
    const rc = document.getElementById(`result-${botKey}`);

    rc.innerHTML = `<div class="result-card"><div class="result-header"><div class="status">⏳ Extracting Intel...</div></div><div class="result-body"><div class="skeleton-box"></div><div class="skeleton-box" style="width:70%"></div></div></div>`;
    setButtonLoading(btn, true);

    try {
        const data = await apiPost(`/api/lookup/${botKey}`, { input });
        renderResult(rc, data, botKey);
    } catch (e) {
        rc.innerHTML = `<div class="result-card"><div class="result-header"><div class="status error">❌ Target Evaded</div></div><div class="result-body"><p class="danger">${esc(e.message)}</p></div></div>`;
    } finally { setButtonLoading(btn, false); }
}

function renderResult(container, data, botKey) {
    if (!data.success) {
        container.innerHTML = `<div class="result-card"><div class="result-header"><div class="status error">❌ Mission Failed</div><span class="bot-name">${esc(data.bot||botKey)}</span></div><div class="result-body"><p class="danger">${esc(data.error||'Unknown error')}</p></div></div>`;
        return;
    }

    const r = data.data;
    const st = data.demo ? 'demo' : data.cached ? 'cached' : 'success';
    const si = data.demo ? '🧪 DEMO MODE' : data.cached ? '📦 CACHED INTEL' : '✅ LIVE INTEL SECURED';

    let html = `<div class="result-card">
        <div class="result-header"><div class="status ${st}">${si}</div><span class="bot-name">${esc(data.bot||botKey)}</span></div>
        <div class="result-body">`;

    // Raw response content
    if (r.text) {
        html += `<div class="raw-content"><pre>${esc(r.text)}</pre></div>`;
    } else {
        html += `<div class="raw-content"><pre>No text content returned.</pre></div>`;
    }

    // Media
    if (r.media && r.media.length > 0) {
        for (const m of r.media) {
            if (m.type === 'photo') html += `<div class="media-box"><img src="${API_BASE}${m.url}" alt="Result"></div>`;
            else if (m.type === 'video' && m.url !== '#demo') html += `<div class="media-box"><video controls><source src="${API_BASE}${m.url}"></video></div>`;
        }
    }

    // Chained Aadhaar Results (Clean Raw only)
    if (data.chain) {
        html += `<div class="chain-section">
            <div class="chain-header"><span class="icon-3d-text pulse">🔗</span> Auto-Fetched Aadhaar Details <span class="chain-badge">${esc(data.chained_aadhaar||'')}</span></div>`;

        if (data.chain.aadhaar_info) {
            html += renderChainBlock('🪪 Aadhaar Personal Info', data.chain.aadhaar_info);
        }
        if (data.chain.aadhaar_family) {
            html += renderChainBlock('👨‍👩‍👧‍👦 Family Information', data.chain.aadhaar_family);
        }
        html += '</div>';
    }

    html += '</div></div>';
    container.innerHTML = html;
}

function renderChainBlock(title, chainData) {
    let h = `<div class="chain-block"><h4>${title}</h4>`;
    if (chainData.text) {
        h += `<div class="raw-content" style="margin-top:0"><pre>${esc(chainData.text)}</pre></div>`;
    }
    h += '</div>';
    return h;
}

// ──────────────── Utils ────────────────
function setButtonLoading(b,l){if(!b)return;const t=b.querySelector('.btn-text'),s=b.querySelector('.btn-loader');if(l){b.disabled=true;t?.classList.add('hidden');s?.classList.remove('hidden');}else{b.disabled=false;t?.classList.remove('hidden');s?.classList.add('hidden');}}
function showToast(m,t='info'){const c=document.getElementById('toast-container'),el=document.createElement('div');el.className=`toast ${t}`;el.innerHTML=`<span class="icon-3d-text small">${t==='success'?'🎉':'⚠️'}</span> `+m;c.appendChild(el);setTimeout(()=>{el.classList.add('toast-exit');setTimeout(()=>el.remove(),300);},4000);}
function esc(s){if(!s)return'';const d=document.createElement('div');d.textContent=s;return d.innerHTML;}
