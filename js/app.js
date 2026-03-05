// Initialize app (Wait for login instead of loading data immediately)
document.addEventListener('DOMContentLoaded', () => {
    // We do not load data until login is successful.

    // Table search filtering
    document.getElementById('searchInput').addEventListener('input', function (e) {
        const text = e.target.value.toLowerCase();
        const rows = document.querySelectorAll('#tableBody tr');
        rows.forEach(row => {
            const ci = row.children[1].textContent.toLowerCase();
            const cliente = row.children[2].textContent.toLowerCase();
            if (ci.includes(text) || cliente.includes(text)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    });

    // Handle "Forma de Recepción" toggle for "Referencia"
    const inpForma = document.getElementById('inpForma');
    const groupReferencia = document.getElementById('groupReferencia');

    inpForma.addEventListener('change', function () {
        if (this.value === 'Efectivo') {
            groupReferencia.style.display = 'none';
            document.getElementById('inpReferencia').value = ''; // clear when hidden
        } else {
            groupReferencia.style.display = 'flex';
        }
    });
});

// Auto-calculate difference
function calcularDiferencia() {
    const recibido = parseFloat(document.getElementById('inpDineroRecibido').value) || 0;
    const factura = parseFloat(document.getElementById('inpFactura').value) || 0;

    // Si aún no hay factura, la diferencia es 0 (o puede ser saldo a favor del cliente)
    // Si la factura sí existe, la diferencia es Factura - Recibido
    const diferencia = factura > 0 ? (factura - recibido) : 0;
    document.getElementById('inpDiferencia').value = diferencia.toFixed(2);
}

// System state
let registrosGlobal = [];
let currentUserRole = null; // 'admin' or 'user'
let activeTab = 'Pendiente'; // 'Pendiente' o 'Procesado'

function cambiarTab(tab) {
    activeTab = tab;
    // Update button styles
    document.getElementById('tabPendientes').classList.toggle('active', tab === 'Pendiente');
    document.getElementById('tabProcesados').classList.toggle('active', tab === 'Procesado');
    // Re-render
    renderRecords();
}

let isLoginMode = true;

function toggleAuthMode() {
    isLoginMode = !isLoginMode;
    if (isLoginMode) {
        document.getElementById('formLogin').style.display = 'block';
        document.getElementById('formRegister').style.display = 'none';
    } else {
        document.getElementById('formLogin').style.display = 'none';
        document.getElementById('formRegister').style.display = 'block';
    }
}

// Login logic
async function iniciarSesion() {
    const user = document.getElementById('loginUser').value;
    const pass = document.getElementById('loginPass').value;
    const errorEl = document.getElementById('loginError');

    // Clear previous error
    errorEl.style.display = 'none';

    if (!user || !pass) {
        errorEl.textContent = "Ingresa usuario y contraseña";
        errorEl.style.display = 'block';
        return;
    }

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pass })
        });
        const res = await response.json();

        if (res.status === 'ok') {
            currentUserRole = res.role;
            document.getElementById('loginScreen').classList.add('hidden');
            document.getElementById('appMain').classList.add('visible');

            // Update user UI
            document.getElementById('userDisplay').innerHTML = `${user} <span class="role-badge">${res.role}</span>`;

            // Apply permissions
            applyRolePermissions();

            // Initialize form date
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('inpFecha').value = today;

            cargarRegistros();
            showToast(`Bienvenido ${user}`, "success");
        } else {
            errorEl.textContent = "Usuario o contraseña incorrecto";
            errorEl.style.display = 'block';
        }
    } catch (e) {
        errorEl.textContent = "Error de conexión con el servidor";
        errorEl.style.display = 'block';
    }
}

async function registrarUsuario() {
    const user = document.getElementById('regUser').value;
    const pass = document.getElementById('regPass').value;

    if (!user || !pass) return showToast("Ingresa usuario y contraseña", "error");

    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pass })
        });
        const res = await response.json();

        if (res.status === 'ok') {
            showToast(res.msg, "success");
            toggleAuthMode();
            document.getElementById('loginUser').value = user;
            document.getElementById('loginPass').value = '';
        } else {
            showToast(res.msg, "error");
        }
    } catch (e) {
        showToast("Error de conexión", "error");
    }
}

function cerrarSesion() {
    currentUserRole = null;
    document.getElementById('appMain').classList.remove('visible');
    document.getElementById('loginScreen').classList.remove('hidden');
    document.getElementById('loginUser').value = '';
    document.getElementById('loginPass').value = '';
}

function applyRolePermissions() {
    const adminElements = document.querySelectorAll('.admin-only');
    adminElements.forEach(el => {
        el.style.display = currentUserRole === 'admin' ? '' : 'none';
    });
}

// Format numbers as currency
const formatCurrency = (amount, moneda = 'USD') => {
    // Si la moneda es VES, usamos formato VE
    if (moneda === 'VES') {
        const VES = new Intl.NumberFormat('es-VE', { style: 'currency', currency: 'VES' }).format(amount);
        return VES.replace("VES", "Bs");
    }
    // Por defecto USD
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
};

// Render Table and Stats
async function cargarRegistros() {
    try {
        const response = await fetch('/api/registros');
        const res = await response.json();

        if (res.status === 'ok') {
            registrosGlobal = res.data;
            renderRecords();
        } else {
            showToast(res.msg, 'error');
        }
    } catch (e) {
        showToast("Error obteniendo registros", 'error');
    }
}

function renderRecords() {
    const tbody = document.getElementById('tableBody');
    tbody.innerHTML = '';

    let totalRecibidoUSD = 0, totalRecibidoVES = 0;
    let totalPagarUSD = 0, totalPagarVES = 0;
    let totalDiferenciaUSD = 0, totalDiferenciaVES = 0;

    // Filter by active tab
    const filteredRecords = registrosGlobal.filter(r => (r.estado || 'Pendiente') === activeTab);

    filteredRecords.forEach(reg => {
        // Acumular totales según moneda
        if (reg.moneda === 'VES') {
            totalRecibidoVES += reg.dinero_recibido;
            totalPagarVES += reg.factura;
            totalDiferenciaVES += reg.diferencia;
        } else {
            totalRecibidoUSD += reg.dinero_recibido;
            totalPagarUSD += reg.factura;
            totalDiferenciaUSD += reg.diferencia;
        }

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td data-label="Fecha">${reg.fecha_recepcion}</td>
            <td data-label="C.I"><strong>${reg.ci}</strong></td>
            <td data-label="Cliente">${reg.cliente}</td>
            <td data-label="Moneda"><strong>${reg.moneda}</strong></td>
            <td data-label="Recibido" style="color: var(--success)">${formatCurrency(reg.dinero_recibido, reg.moneda)}</td>
            <td data-label="Forma"><span class="badge">${reg.forma_recepcion}</span></td>
            <td data-label="Referencia">${reg.referencia || '-'}</td>
            <td data-label="a Pagar" style="color: var(--blue)">
                ${reg.factura > 0 ? formatCurrency(reg.factura, reg.moneda) : '<span style="color:var(--text-muted); font-size: 0.8em; font-style: italic;">Pendiente</span>'}
            </td>
            <td data-label="Diferencia" style="color: ${reg.diferencia > 0 ? 'var(--danger)' : 'var(--success)'}">
                ${reg.factura > 0 ? formatCurrency(reg.diferencia, reg.moneda) : '-'}
            </td>
            <td data-label="Teléfono">${reg.telefono}</td>
            <td data-label="Acción" class="admin-only" style="display: ${currentUserRole === 'admin' ? 'flex' : 'none'}; gap: 8px;">
                ${(reg.estado || 'Pendiente') === 'Pendiente' ? `<button class="btn btn-success" style="padding: 6px 10px; background: var(--success); color: white;" onclick="marcarPagado(${reg.id})" title="Marcar como Pagado"><i class='bx bx-check-double'></i></button>` : ''}
                <button class="btn btn-outline" style="padding: 6px 10px;" onclick="abrirModal(${reg.id})" title="Editar">
                    <i class='bx bx-edit'></i>
                </button>
                <button class="btn btn-danger" style="padding: 6px 10px;" onclick="eliminarRegistro(${reg.id})" title="Eliminar">
                    <i class='bx bx-trash'></i>
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });

    // Update Dashboard Stats for USD
    document.getElementById('statTotalRecibidoUSD').innerText = formatCurrency(totalRecibidoUSD, 'USD');
    document.getElementById('statTotalPagarUSD').innerText = formatCurrency(totalPagarUSD, 'USD');
    document.getElementById('statTotalDiferenciaUSD').innerText = formatCurrency(totalDiferenciaUSD, 'USD');

    // Update Dashboard Stats for VES
    document.getElementById('statTotalRecibidoVES').innerText = formatCurrency(totalRecibidoVES, 'VES');
    document.getElementById('statTotalPagarVES').innerText = formatCurrency(totalPagarVES, 'VES');
    document.getElementById('statTotalDiferenciaVES').innerText = formatCurrency(totalDiferenciaVES, 'VES');
}

// Modal Logic
function abrirModal(id = null) {
    document.getElementById('registroModal').classList.add('active');
    document.getElementById('registroForm').reset();

    const inpForma = document.getElementById('inpForma');
    const groupReferencia = document.getElementById('groupReferencia');

    if (id) {
        // Modo Edición
        document.getElementById('modalTitle').innerText = "Editar Adelanto o Factura";
        const reg = registrosGlobal.find(r => r.id === id);
        if (reg) {
            document.getElementById('inpId').value = reg.id;
            document.getElementById('inpCI').value = reg.ci;
            document.getElementById('inpCliente').value = reg.cliente;
            document.getElementById('inpDineroRecibido').value = reg.dinero_recibido;
            document.getElementById('inpFactura').value = reg.factura > 0 ? reg.factura : '';
            document.getElementById('inpDiferencia').value = reg.diferencia;
            inpForma.value = reg.forma_recepcion;
            document.getElementById('inpMoneda').value = reg.moneda || 'USD';
            document.getElementById('inpFecha').value = reg.fecha_recepcion;
            document.getElementById('inpReferencia').value = reg.referencia || '';
            document.getElementById('inpTelefono').value = reg.telefono;
            document.getElementById('inpEstado').value = reg.estado || 'Pendiente';
        }
    } else {
        // Modo Nuevo
        document.getElementById('modalTitle').innerText = "Añadir Nuevo Adelanto";
        document.getElementById('inpId').value = '';
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('inpFecha').value = today;
        inpForma.value = 'Efectivo';
        document.getElementById('inpMoneda').value = 'USD';
        document.getElementById('inpEstado').value = 'Pendiente';
        document.getElementById('inpDiferencia').value = 0.00;
    }

    // Trigger display toggle for Reference
    if (inpForma.value === 'Efectivo') {
        groupReferencia.style.display = 'none';
    } else {
        groupReferencia.style.display = 'flex';
    }
}

function cerrarModal() {
    document.getElementById('registroModal').classList.remove('active');
}

// Save or Update Record
async function guardarRegistro() {
    const id = document.getElementById('inpId').value;
    const ci = document.getElementById('inpCI').value;
    const cliente = document.getElementById('inpCliente').value;
    const dinero_recibido = document.getElementById('inpDineroRecibido').value;
    const factura = document.getElementById('inpFactura').value;
    const diferencia = document.getElementById('inpDiferencia').value;
    const forma_recepcion = document.getElementById('inpForma').value;
    const moneda = document.getElementById('inpMoneda').value;
    const estado = document.getElementById('inpEstado').value;
    const fecha_recepcion = document.getElementById('inpFecha').value;
    const referencia = document.getElementById('inpReferencia').value;
    const telefono = document.getElementById('inpTelefono').value;

    if (!ci || !cliente || !dinero_recibido || !fecha_recepcion || !telefono) {
        showToast("Por favor llena todos los campos requeridos (*)", 'error');
        return;
    }

    const datos = {
        id, ci, cliente, dinero_recibido, factura, diferencia,
        forma_recepcion, fecha_recepcion, referencia, telefono, moneda, estado
    };

    try {
        let res;
        if (id) {
            const req = await fetch(`/api/registros/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(datos)
            });
            res = await req.json();
        } else {
            const req = await fetch('/api/registros', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(datos)
            });
            res = await req.json();
        }

        if (res.status === 'ok') {
            showToast(res.msg, 'success');
            cerrarModal();
            cargarRegistros();
        } else {
            showToast(res.msg, 'error');
        }
    } catch (e) {
        showToast("Error guardando el registro", "error");
    }
}

// Delete Record
async function eliminarRegistro(id) {
    if (confirm("¿Estás seguro de que deseas eliminar este registro?")) {
        try {
            const req = await fetch(`/api/registros/${id}`, { method: 'DELETE' });
            const res = await req.json();

            if (res.status === 'ok') {
                showToast("Registro eliminado con éxito", 'success');
                cargarRegistros();
            } else {
                showToast(res.msg, 'error');
            }
        } catch (e) {
            showToast("Error al eliminar", "error");
        }
    }
}

// Marcar como pagado
async function marcarPagado(id) {
    if (confirm("¿Marcar este adelanto como procesado/pagado?")) {
        try {
            const reg = registrosGlobal.find(r => r.id === id);
            if (!reg) return;

            // Conservar el resto de los datos y cambiar solo estado
            const datos = {
                id: reg.id,
                ci: reg.ci,
                cliente: reg.cliente,
                dinero_recibido: reg.dinero_recibido,
                factura: reg.factura,
                diferencia: reg.diferencia,
                forma_recepcion: reg.forma_recepcion,
                fecha_recepcion: reg.fecha_recepcion,
                referencia: reg.referencia,
                telefono: reg.telefono,
                moneda: reg.moneda,
                estado: 'Procesado' // Cambio clave
            };

            const req = await fetch(`/api/registros/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(datos)
            });
            const res = await req.json();

            if (res.status === 'ok') {
                showToast("Registro marcado como pagado", 'success');
                cargarRegistros();
            } else {
                showToast(res.msg, 'error');
            }
        } catch (e) {
            showToast("Error al procesar", "error");
        }
    }
}

// Toast helper
function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icon = type === 'success' ? 'bx-check-circle' : 'bx-error-circle';
    toast.innerHTML = `<i class='bx ${icon}'></i> <span>${message}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s ease forwards';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
