// ==========================================
// COMPILADOR DSL — FRONTEND APP
// ==========================================

const API_URL = '/api/compilar';

// Elementos del DOM
const codigoInput = document.getElementById('codigo-input');
const btnCompilar = document.getElementById('btn-compilar');
const btnLimpiar = document.getElementById('btn-limpiar');
const btnCopiar = document.getElementById('btn-copiar');
const charCount = document.getElementById('char-count');
const tokensBody = document.getElementById('tokens-body');
const tokenCount = document.getElementById('token-count');
const astBody = document.getElementById('ast-body');
const jsonPanel = document.getElementById('json-panel');
const jsonOutput = document.getElementById('json-output');
const statusBadge = document.getElementById('status-badge');
const processorBadge = document.getElementById('processor-badge');
const btnHistorial = document.getElementById('btn-historial');
const historyPanel = document.getElementById('history-panel');
const historyBody = document.getElementById('history-body');
const readerBadge = document.getElementById('reader-badge');

// Chips de ejemplos rápidos
const chips = document.querySelectorAll('.chip');

// ==========================================
// EVENT LISTENERS
// ==========================================

codigoInput.addEventListener('input', () => {
    charCount.textContent = `${codigoInput.value.length} caracteres`;
});

chips.forEach(chip => {
    chip.addEventListener('click', () => {
        const code = chip.getAttribute('data-code');
        codigoInput.value = code;
        charCount.textContent = `${code.length} caracteres`;
        // Compilar automáticamente al hacer clic
        compilar();
    });
});

btnLimpiar.addEventListener('click', () => {
    codigoInput.value = '';
    charCount.textContent = '0 caracteres';
    limpiarResultados();
});

btnCopiar.addEventListener('click', () => {
    navigator.clipboard.writeText(jsonOutput.textContent);
    btnCopiar.textContent = '✓ Copiado';
    setTimeout(() => btnCopiar.textContent = 'Copiar', 1500);
});

btnHistorial.addEventListener('click', async () => {
    historyPanel.style.display = 'block';
    historyBody.innerHTML = '<div class="empty-state"><span class="empty-icon">[!]</span><p>Cargando historial...</p></div>';
    
    try {
        const response = await fetch('/api/historial');
        const data = await response.json();
        
        readerBadge.textContent = 'Leído por: ' + data.nodo_lector;
        
        if (!data.registros || data.registros.length === 0) {
            historyBody.innerHTML = '<div class="empty-state"><span class="empty-icon">[0]</span><p>No hay compilaciones guardadas aún</p></div>';
            return;
        }

        let html = '<div class="token-list">';
        data.registros.forEach((reg) => {
            const statusClass = reg.status === 'success' ? 'origen' : 'error';
            html += `<div class="token-item">`;
            html += `  <span class="token-badge ${statusClass}">${reg.status}</span>`;
            html += `  <span class="token-badge kw">${reg.nodo_procesador}</span>`;
            html += `  <span class="token-value" style="flex-grow: 1;">${escapeHtml(reg.codigo_fuente)}</span>`;
            html += `  <span class="hint" style="font-size: 10px;">${new Date(reg.fecha).toLocaleString()}</span>`;
            html += `</div>`;
        });
        html += '</div>';
        
        historyBody.innerHTML = html;
        historyPanel.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        historyBody.innerHTML = '<div class="empty-state" style="color:var(--error)"><span class="empty-icon">[X]</span><p>Error cargando historial</p></div>';
    }
});

btnCompilar.addEventListener('click', compilar);

codigoInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        compilar();
    }
});

// ==========================================
// COMPILAR
// ==========================================

async function compilar() {
    const codigo = codigoInput.value.trim();
    if (!codigo) return;

    btnCompilar.classList.add('loading');
    btnCompilar.innerHTML = '<span class="btn-icon">⟳</span> Compilando...';
    statusBadge.textContent = '● Procesando';
    statusBadge.style.color = '#d29922';

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ codigo })
        });

        const data = await response.json();
        renderResultados(data);

        statusBadge.textContent = '● Conectado';
        statusBadge.style.color = '';
    } catch (error) {
        statusBadge.textContent = '● Desconectado';
        statusBadge.style.color = '#f85149';
        astBody.innerHTML = `<div class="ast-error-box">Error de conexión: No se pudo contactar al servidor en ${API_URL}</div>`;
    } finally {
        btnCompilar.classList.remove('loading');
        btnCompilar.innerHTML = '<span class="btn-icon">▶</span> Compilar';
    }
}

// ==========================================
// RENDER RESULTADOS
// ==========================================

function renderResultados(data) {
    const { tokens_resultantes, nodo_procesador } = data;
    const { tokens, ast } = tokens_resultantes;

    // Render Badge
    if (nodo_procesador) {
        processorBadge.textContent = 'Procesado en: ' + nodo_procesador;
        processorBadge.style.display = 'inline-block';
    }

    // Render Tokens
    renderTokens(tokens);

    // Render AST
    renderAST(ast);

    // Render JSON
    jsonPanel.style.display = 'block';
    jsonOutput.textContent = JSON.stringify(data, null, 2);
}

function renderTokens(tokens) {
    if (!tokens || tokens.length === 0) {
        tokensBody.innerHTML = '<div class="empty-state"><span class="empty-icon">[0]</span><p>Sin tokens</p></div>';
        tokenCount.textContent = '0';
        return;
    }

    tokenCount.textContent = tokens.length;

    let html = '<div class="token-list">';
    tokens.forEach((token, i) => {
        const badgeClass = getTokenBadgeClass(token.tipo);
        const delay = i * 0.08;

        html += `<div class="token-item" style="animation-delay: ${delay}s">`;
        html += `  <span class="token-badge ${badgeClass}">${token.tipo}</span>`;
        html += `  <span class="token-value">${escapeHtml(token.valor)}</span>`;
        html += `</div>`;

        if (token.tipo === 'ERROR_LEXICO' && (token.cause || token.suggestion)) {
            html += `<div class="token-error-detail" style="animation-delay: ${delay + 0.05}s">`;
            if (token.cause) html += `<strong>Causa:</strong> ${escapeHtml(token.cause)}<br>`;
            if (token.suggestion) html += `<strong>Sugerencia:</strong> ${escapeHtml(token.suggestion)}`;
            html += `</div>`;
        }
    });
    html += '</div>';

    tokensBody.innerHTML = html;
}

function renderAST(ast) {
    if (!ast) {
        astBody.innerHTML = '<div class="empty-state"><span class="empty-icon">[0]</span><p>Sin AST</p></div>';
        return;
    }

    let html = '';
    
    // 1. Mostrar Errores Principales (Sintáctico o Semántico)
    if (ast.error_sintactico) {
        html += `<div class="ast-error-box" style="margin-bottom: 15px;">[X] Error Sintáctico/Léxico: ${escapeHtml(ast.error_sintactico)}</div>`;
    } else if (ast.error_semantico) {
        html += `<div class="ast-error-box" style="background: rgba(248, 81, 73, 0.1); border: 1px solid #f85149; margin-bottom: 15px;">[X] Error Semántico (Java): ${escapeHtml(ast.error_semantico)}</div>`;
    } else if (ast.resultado_semantico) {
        html += `<div class="ast-success-box" style="background: rgba(46, 160, 67, 0.1); border: 1px solid #2ea043; margin-bottom: 15px;">[OK] Resultado (Java): ${escapeHtml(ast.resultado_semantico.resultado_texto)}</div>`;
    } else {
        html += '<div class="ast-success-box" style="margin-bottom: 15px;">[OK] AST Construido exitosamente</div>';
    }

    // 2. Mostrar Análisis LLM si existe
    if (ast.analisis_llm && ast.analisis_llm.errores && ast.analisis_llm.errores.length > 0) {
        html += `<div class="ast-error-box" style="background: rgba(88, 166, 255, 0.1); border: 1px solid #58a6ff; color: #c9d1d9; margin-bottom: 15px;">`;
        html += `<strong style="color: #58a6ff;">Respuesta LLM:</strong><br><br>`;
        ast.analisis_llm.errores.forEach(err => {
            html += `<div style="margin-bottom: 10px; padding-left: 10px; border-left: 2px solid #58a6ff;">`;
            html += `<strong>Tipo:</strong> ${escapeHtml(err.tipo_error.toUpperCase())}<br>`;
            html += `<strong>Causa:</strong> ${escapeHtml(err.causa)}<br>`;
            html += `<strong>Sugerencia:</strong> ${escapeHtml(err.sugerencia)}<br>`;
            if (err.ejemplo_corregido) {
                html += `<strong>Corregido:</strong> <code style="background: rgba(0,0,0,0.3); padding: 2px 5px; border-radius: 3px;">${escapeHtml(err.ejemplo_corregido)}</code>`;
            }
            html += `</div>`;
        });
        html += `</div>`;
    }

    // Si hay error sintáctico, detenemos el renderizado del árbol aquí
    if (ast.error_sintactico) {
        astBody.innerHTML = html;
        return;
    }
    
    html += '<div class="ast-tree">';
    html += `<div class="ast-node ast-root" style="animation-delay: 0.1s">[ROOT] ${ast.nodo_raiz}</div>`;

    if (ast.hijos) {
        ast.hijos.forEach((hijo, i) => {
            const delay = 0.2 + (i * 0.1);
            const isLast = i === ast.hijos.length - 1;
            const branch = isLast ? '└── ' : '├── ';

            html += `<div class="ast-node" style="animation-delay: ${delay}s">`;
            html += `<span class="ast-branch">${branch}</span>`;
            html += `<span class="ast-label">${hijo.nodo}: </span>`;

            if (hijo.valor !== undefined) {
                html += `<span class="ast-value">${hijo.valor}</span>`;
            }
            if (hijo.unidad) {
                html += `<span class="ast-value">${hijo.unidad}</span>`;
            }

            html += `</div>`;
        });
    }

    html += '</div>';
    astBody.innerHTML = html;
}

// ==========================================
// UTILIDADES
// ==========================================

function getTokenBadgeClass(tipo) {
    if (tipo === 'KW_CONVERTIR') return 'kw';
    if (tipo === 'NUMERO') return 'num';
    if (tipo === 'UNIDAD_ORIGEN_C') return 'origen';
    if (tipo === 'UNIDAD_DESTINO_F') return 'destino';
    if (tipo === 'ERROR_LEXICO') return 'error';
    return '';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function limpiarResultados() {
    tokensBody.innerHTML = '<div class="empty-state"><span class="empty-icon">[*]</span><p>Ingresa código y presiona Compilar</p></div>';
    tokenCount.textContent = '0';
    astBody.innerHTML = '<div class="empty-state"><span class="empty-icon">[*]</span><p>El AST aparecerá aquí</p></div>';
    jsonPanel.style.display = 'none';
}
