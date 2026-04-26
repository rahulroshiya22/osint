/* ═══════════════════════════════════════════════════
   INFO HUB BY RAHUL — Main JavaScript
   ═══════════════════════════════════════════════════ */

const API_BASE = window.location.origin;
let botsConfig = {};

document.addEventListener('DOMContentLoaded', async () => {
    // Intro Animation Sequence
    setTimeout(() => {
        document.getElementById('intro-screen').style.opacity = '0';
        setTimeout(() => {
            document.getElementById('intro-screen').style.display = 'none';
            const token = localStorage.getItem('token');
            if (token === '#rahul#123_verified') {
                initDashboard();
            } else {
                showScreen('auth-screen');
            }
        }, 500);
    }, 2500);

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const authVisible = document.getElementById('auth-screen').classList.contains('active');
            if (authVisible) verifyPassword();
        }
    });

    initMatrixBackground();
});

// ──────────────── Matrix Background ────────────────
function initMatrixBackground() {
    const canvas = document.getElementById('matrix-bg');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    let width = canvas.width = canvas.parentElement.clientWidth || window.innerWidth;
    let height = canvas.height = window.innerHeight;

    window.addEventListener('resize', () => {
        width = canvas.width = canvas.parentElement.clientWidth || window.innerWidth;
        height = canvas.height = window.innerHeight;
    });

    const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789$+-*/=%""\'#&_(),.;:?!\\|{}<>[]^~'.split('');
    const fontSize = 12;
    let columns = width / fontSize;
    const drops = [];
    for(let x = 0; x < columns; x++) drops[x] = 1;

    function drawMatrix() {
        // Very dark fade for black background
        ctx.fillStyle = 'rgba(5, 5, 5, 0.1)';
        ctx.fillRect(0, 0, width, height);

        ctx.fillStyle = '#FF6B00'; // Pure Orange
        ctx.font = fontSize + 'px "JetBrains Mono", monospace';

        for(let i = 0; i < drops.length; i++) {
            const text = letters[Math.floor(Math.random() * letters.length)];
            ctx.fillText(text, i * fontSize, drops[i] * fontSize);
            if(drops[i] * fontSize > height && Math.random() > 0.975) drops[i] = 0;
            drops[i]++;
        }
    }
    setInterval(drawMatrix, 50);
}

// ──────────────── API ────────────────
async function apiRequest(method, path, body = null) {
    const headers = { 'Content-Type': 'application/json' };
    const token = localStorage.getItem('token');
    if (token) headers['Authorization'] = `Bearer ${token}`;
    
    const opts = { method, headers };
    if (body) opts.body = JSON.stringify(body);
    
    const res = await fetch(`${API_BASE}${path}`, opts);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Request failed');
    return data;
}

const apiGet = (p) => apiRequest('GET', p);
const apiPost = (p, b) => apiRequest('POST', p, b);

// ──────────────── Navigation ────────────────
function showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(id)?.classList.add('active');
}

function switchTab(id) {
    document.querySelectorAll('.tab-btn').forEach(n => n.classList.remove('active'));
    document.querySelector(`.tab-btn[data-tab="${id}"]`)?.classList.add('active');
    document.querySelectorAll('.tool-panel').forEach(p => p.classList.remove('active'));
    document.getElementById(`panel-${id}`)?.classList.add('active');
}

// ──────────────── Auth ────────────────
function showAuthMessage(m, t = 'error') {
    const el = document.getElementById('auth-message');
    el.textContent = m;
    el.className = `auth-message ${t}`;
    el.classList.remove('hidden');
    el.style.color = t === 'error' ? '#ff4444' : '#00ff41';
    el.style.marginTop = '15px';
    el.style.textAlign = 'center';
    el.style.fontFamily = 'var(--font-mono)';
    el.style.fontSize = '0.8rem';
}

async function verifyPassword() {
    const p = document.getElementById('login-password').value;
    if (!p) return showAuthMessage('ENTER ACCESS CODE');
    const btn = document.getElementById('login-btn');
    setButtonLoading(btn, true);
    try {
        const d = await apiPost('/api/verify', { password: p });
        if (d.success) {
            localStorage.setItem('token', '#rahul#123_verified');
            await initDashboard();
        } else {
            showAuthMessage('INVALID ACCESS CODE');
        }
    } catch (e) {
        showAuthMessage(e.message.toUpperCase());
    } finally {
        setButtonLoading(btn, false);
    }
}

function handleLogout() { 
    localStorage.removeItem('token'); 
    showScreen('auth-screen'); 
    document.getElementById('login-password').value = '';
}

// ──────────────── Dashboard ────────────────
async function initDashboard() {
    showScreen('dashboard-screen');
    try {
        const d = await apiGet('/api/bots');
        botsConfig = d.bots;
        buildToolPanels();
    } catch (e) {
        showToast('SYSTEM ERROR: UNABLE TO FETCH BOTS', 'error');
    }
    switchTab('number_to_info');
}

function buildToolPanels() {
    for (const [key, cfg] of Object.entries(botsConfig)) {
        const p = document.getElementById(`panel-${key}`);
        if (!p) continue;
        p.innerHTML = `
            <div class="tool-header">
                <h2><span class="accent">${cfg.icon}</span> ${cfg.display_name.toUpperCase()}</h2>
                <p>${cfg.description}</p>
            </div>
            <div class="search-box">
                <input type="text" id="input-${key}" placeholder="${cfg.input_placeholder}" 
                       onkeydown="if(event.key==='Enter')performLookup('${key}')">
                <button class="btn-3d" onclick="performLookup('${key}')" id="btn-${key}">
                    <span class="btn-text">EXECUTE SEARCH</span>
                    <span class="btn-loader hidden">PROCESSING...</span>
                </button>
            </div>
            <div id="result-${key}"></div>
        `;
    }
}

// ──────────────── Lookup ────────────────
async function performLookup(botKey) {
    const input = document.getElementById(`input-${botKey}`).value.trim();
    if (!input) return showToast('INPUT REQUIRED', 'error');

    const btn = document.getElementById(`btn-${botKey}`);
    const rc = document.getElementById(`result-${botKey}`);

    rc.innerHTML = `
        <div class="result-card">
            <div class="result-header">
                <div class="status">SEARCHING...</div>
            </div>
            <div class="result-body">
                <div class="hacker-loader">
                    <div class="hacker-loader-line"></div>
                </div>
                <p class="hacker-loader-text blink">FETCHING ENCRYPTED DATA STREAMS...</p>
            </div>
        </div>
    `;
    setButtonLoading(btn, true);

    try {
        const data = await apiPost(`/api/lookup/${botKey}`, { input });
        renderResult(rc, data, botKey);
    } catch (e) {
        rc.innerHTML = `
            <div class="result-card">
                <div class="result-header">
                    <div class="status" style="color:#ff4444">ERROR</div>
                </div>
                <div class="result-body">
                    <p style="color:#ff4444; font-family:var(--font-mono); font-size:0.8rem;">${esc(e.message)}</p>
                </div>
            </div>
        `;
    } finally {
        setButtonLoading(btn, false);
    }
}

function renderResult(container, data, botKey) {
    if (!data.success) {
        container.innerHTML = `
            <div class="result-card">
                <div class="result-header">
                    <div class="status" style="color:#ff4444">FAILED</div>
                    <span class="bot-name">${esc(data.bot||botKey)}</span>
                </div>
                <div class="result-body">
                    <p style="color:#ff4444; font-family:var(--font-mono); font-size:0.8rem;">${esc(data.error||'UNKNOWN ERROR')}</p>
                </div>
            </div>
        `;
        return;
    }

    const r = data.data;
    const si = data.demo ? 'DEMO MODE' : data.cached ? 'CACHED DATA' : 'LIVE DATA SECURED';

    let html = `
        <div class="result-card">
            <div class="result-header">
                <div class="status">${si}</div>
                <span class="bot-name">${esc(data.bot||botKey)}</span>
            </div>
            <div class="result-body">
    `;

    if (r.text) {
        html += `<div class="raw-content"><pre>${esc(r.text)}</pre></div>`;
    }

    if (r.media && r.media.length > 0) {
        for (const m of r.media) {
            if (m.type === 'photo') html += `<div class="media-box" style="margin-top:15px; border-radius:8px; overflow:hidden;"><img src="${API_BASE}${m.url}" style="width:100%; display:block;"></div>`;
            else if (m.type === 'video' && m.url !== '#demo') html += `<div class="media-box" style="margin-top:15px; border-radius:8px; overflow:hidden;"><video controls style="width:100%; display:block;"><source src="${API_BASE}${m.url}"></video></div>`;
        }
    }

    if (data.chain) {
        html += `<div style="margin-top:20px; border-top:1px solid var(--border); padding-top:15px;">
                    <div style="font-family:var(--font-mono); font-size:0.8rem; color:var(--primary); margin-bottom:10px;">🔗 LINKED AADHAAR DATA</div>`;
        if (data.chain.aadhaar_info) html += `<div class="raw-content" style="margin-bottom:10px;"><pre>${esc(data.chain.aadhaar_info.text)}</pre></div>`;
        if (data.chain.aadhaar_family) html += `<div class="raw-content"><pre>${esc(data.chain.aadhaar_family.text)}</pre></div>`;
        html += `</div>`;
    }

    html += `</div></div>`;
    container.innerHTML = html;
}

// ──────────────── Utils ────────────────
function setButtonLoading(b, l) {
    if (!b) return;
    const t = b.querySelector('.btn-text');
    const s = b.querySelector('.btn-loader');
    if (l) {
        b.disabled = true;
        t?.classList.add('hidden');
        s?.classList.remove('hidden');
    } else {
        b.disabled = false;
        t?.classList.remove('hidden');
        s?.classList.add('hidden');
    }
}

function showToast(m, t = 'info') {
    const c = document.getElementById('toast-container');
    const el = document.createElement('div');
    el.className = `toast ${t}`;
    el.textContent = m;
    c.appendChild(el);
    setTimeout(() => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(-20px)';
        setTimeout(() => el.remove(), 300);
    }, 4000);
}

function esc(s) {
    if (!s) return '';
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
}
