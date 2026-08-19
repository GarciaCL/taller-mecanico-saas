function actualizarModelosSugeridos() {
    const marcaIngresada = document.getElementById('comp-marca').value.trim().toLowerCase();
    const datalistModelos = document.getElementById('dl-modelos');
    datalistModelos.innerHTML = '';

    for (let m in mapaMarcasModelos) {
        if (m.toLowerCase() === marcaIngresada) {
            mapaMarcasModelos[m].forEach(mod => {
                const opt = document.createElement('option');
                opt.value = mod;
                datalistModelos.appendChild(opt);
            });
            break;
        }
    }
}

let listaCompatibilidades = [];

function agregarEtiquetaCompatibilidad() {
    const marca = document.getElementById('comp-marca').value.trim();
    const modelo = document.getElementById('comp-modelo').value.trim();
    const anio = document.getElementById('comp-anio').value.trim();

    if (!marca && !modelo) {
        Swal.fire({ title: 'Atención', text: 'Ingresa al menos la Marca o el Modelo.', icon: 'warning', confirmButtonColor: '#3b82f6' });
        return;
    }

    let itemStr = `${marca} ${modelo}`.trim();
    if (anio) itemStr += ` (${anio})`;

    if (!listaCompatibilidades.includes(itemStr)) {
        listaCompatibilidades.push(itemStr);
        actualizarChipsCompatibilidad();
    }

    document.getElementById('comp-marca').value = '';
    document.getElementById('comp-modelo').value = '';
    document.getElementById('comp-anio').value = '';
}

function removerCompatibilidad(index) {
    listaCompatibilidades.splice(index, 1);
    actualizarChipsCompatibilidad();
}

function actualizarChipsCompatibilidad() {
    const contenedor = document.getElementById('contenedor-chips-compat');
    const inputFinal = document.getElementById('compatibilidades_final');

    if (listaCompatibilidades.length === 0) {
        contenedor.innerHTML = '<span class="text-[11px] text-slate-500 italic">Sin aplicaciones asignadas (por defecto será Universal).</span>';
        inputFinal.value = 'Universal';
    } else {
        let html = '';
        listaCompatibilidades.forEach((item, idx) => {
            html += `<span class="bg-blue-950 border border-blue-500/40 text-blue-300 text-xs px-2.5 py-1 rounded-xl flex items-center gap-1.5">
                🚗 ${item}
                <button type="button" onclick="removerCompatibilidad(${idx})" class="text-rose-400 hover:text-rose-300 font-bold text-xs ml-1">✕</button>
            </span>`;
        });
        contenedor.innerHTML = html;
        inputFinal.value = listaCompatibilidades.join(', ');
    }
}

function filtrarRepuestosInventario() {
    const query = document.getElementById('buscador-repuesto-input').value.toLowerCase().trim();
    const desplegable = document.getElementById('desplegable-autocompletado');
    const opciones = document.querySelectorAll('.opcion-repuesto');

    if (query.length < 1) {
        desplegable.classList.add('hidden');
        return;
    }

    let coincidencias = 0;
    opciones.forEach(opt => {
        const codigo = opt.getAttribute('data-codigo').toLowerCase();
        const nombre = opt.getAttribute('data-nombre').toLowerCase();

        if (codigo.includes(query) || nombre.includes(query)) {
            opt.classList.remove('hidden');
            coincidencias++;
        } else {
            opt.classList.add('hidden');
        }
    });

    if (coincidencias > 0) desplegable.classList.remove('hidden'); else desplegable.classList.add('hidden');
}

function seleccionarRepuestoAutocompletado(id, codigo, nombre, stock) {
    document.getElementById('repuesto-id-seleccionado').value = id;
    document.getElementById('buscador-repuesto-input').value = `[${codigo}] ${nombre}`;
    document.getElementById('desplegable-autocompletado').classList.add('hidden');
}

function agregarRepuestoAOrdenAjax() {
    const ordenId = document.getElementById('edit-orden-id').value;
    const inventarioId = document.getElementById('repuesto-id-seleccionado').value;
    const cantidad = document.getElementById('repuesto-cantidad-input').value;
    const precioUnidad = document.getElementById('repuesto-precio-input').value || 0;

    if (!inventarioId) {
        Swal.fire({ title: 'Atención', text: 'Por favor busca y selecciona un repuesto de la lista.', icon: 'warning', confirmButtonColor: '#3b82f6' });
        return;
    }

    const formData = new FormData();
    formData.append('orden_id', ordenId);
    formData.append('inventario_id', inventarioId);
    formData.append('cantidad', cantidad);
    formData.append('precio_unidad', precioUnidad);

    fetch('/vincular_repuesto_ot', { method: 'POST', body: formData }).then(() => {
        document.getElementById('buscador-repuesto-input').value = '';
        document.getElementById('repuesto-id-seleccionado').value = '';
        document.getElementById('repuesto-cantidad-input').value = '1';
        document.getElementById('repuesto-precio-input').value = '';
        cargarRepuestosVinculadosOT(ordenId);
    });
}

function cargarRepuestosVinculadosOT(ordenId) {
    fetch('/obtener_repuestos_ot/' + ordenId)
        .then(res => res.json())
        .then(items => {
            const contenedor = document.getElementById('lista-repuestos-orden');
            if (!items || items.length === 0) {
                contenedor.innerHTML = '<span class="text-slate-500 text-[11px]">Sin repuestos vinculados a esta orden.</span>';
            } else {
                let html = '<ul class="space-y-1.5">';
                items.forEach(i => {
                    const subtotal = i.precio * i.cantidad;
                    html += `<li class="flex justify-between items-center bg-slate-950 p-2.5 rounded-xl border border-slate-800/80">
                        <div class="flex items-center gap-2">
                            <span class="text-blue-400 font-bold">🔧 ${i.nombre}</span>
                            <span class="bg-slate-800 text-slate-300 font-mono text-[10px] px-1.5 py-0.5 rounded">x${i.cantidad}</span>
                        </div>
                        <div class="flex items-center gap-3">
                            <span class="text-emerald-400 font-bold">$${subtotal.toLocaleString('es-CL')}</span>
                            <button onclick="editarRepuestoOtModal('${i.id}', '${i.nombre}', '${i.cantidad}', '${i.precio}', '${ordenId}')" class="text-slate-400 hover:text-blue-400 font-semibold text-xs">✏️</button>
                            <button onclick="eliminarRepuestoOtAjax('${i.id}', '${ordenId}')" class="text-rose-400 hover:text-rose-300 font-semibold text-xs">🗑️</button>
                        </div>
                    </li>`;
                });
                html += '</ul>';
                contenedor.innerHTML = html;
            }
        });
}

function eliminarRepuestoOtAjax(itemId, ordenId) {
    fetch('/eliminar_repuesto_ot/' + itemId, { method: 'POST' }).then(() => cargarRepuestosVinculadosOT(ordenId));
}

function editarRepuestoOtModal(itemId, nombre, cantActual, precioActual, ordenId) {
    Swal.fire({
        title: `Editar ${nombre}`,
        html: `
            <div class="space-y-3 text-left">
                <div><label class="block text-xs font-semibold text-slate-400 mb-1">Cantidad</label><input type="number" id="swal-cant" value="${cantActual}" min="1" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"></div>
                <div><label class="block text-xs font-semibold text-slate-400 mb-1">Precio Unidad ($)</label><input type="number" id="swal-precio" value="${precioActual}" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-emerald-400 font-bold"></div>
            </div>
        `,
        showCancelButton: true,
        confirmButtonText: 'Guardar Cambios',
        confirmButtonColor: '#3b82f6',
        preConfirm: () => ({ cantidad: document.getElementById('swal-cant').value, precio: document.getElementById('swal-precio').value })
    }).then((result) => {
        if (result.isConfirmed) {
            fetch('/actualizar_repuesto_ot', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ item_id: itemId, cantidad: result.value.cantidad, precio: result.value.precio })
            }).then(() => cargarRepuestosVinculadosOT(ordenId));
        }
    });
}

function toggleSeleccionarTodos(chkPrincipal) {
    document.querySelectorAll('.check-repuesto').forEach(chk => chk.checked = chkPrincipal.checked);
    evaluarSeleccionados();
}

function evaluarSeleccionados() {
    const seleccionados = document.querySelectorAll('.check-repuesto:checked');
    const btnEliminar = document.getElementById('btn-eliminar-seleccionados');
    document.getElementById('cant-seleccionados').innerText = seleccionados.length;
    if (seleccionados.length > 0) btnEliminar.classList.remove('hidden'); else btnEliminar.classList.add('hidden');
}

function eliminarRepuestoIndividual(id, nombre) {
    Swal.fire({
        title: '¿Eliminar Repuesto?',
        text: `¿Estás seguro de eliminar permanentemente '${nombre}'?`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#e11d48',
        confirmButtonText: 'Sí, Eliminar'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch('/eliminar_repuesto/' + id, { method: 'POST' }).then(() => location.reload());
        }
    });
}

function eliminarSeleccionadosMasivo() {
    const seleccionados = Array.from(document.querySelectorAll('.check-repuesto:checked')).map(c => c.value);
    if (seleccionados.length === 0) return;

    Swal.fire({
        title: `¿Eliminar ${seleccionados.length} repuestos?`,
        text: "Esta acción no se puede deshacer.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#e11d48',
        confirmButtonText: 'Sí, Eliminar Todo'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch('/eliminar_repuestos_masivo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ids: seleccionados })
            }).then(() => location.reload());
        }
    });
}

let paginaActual = 1;
const filasPorPagina = 10;

function renderizarPaginacion() {
    const filasVisibles = Array.from(document.querySelectorAll('.fila-repuesto')).filter(f => f.getAttribute('data-visible') !== 'false');
    const total = filasVisibles.length;
    const totalPaginas = Math.ceil(total / filasPorPagina) || 1;
    const inicio = (paginaActual - 1) * filasPorPagina;
    const fin = inicio + filasPorPagina;

    filasVisibles.forEach((f, idx) => {
        f.style.display = (idx >= inicio && idx < fin) ? '' : 'none';
    });

    document.getElementById('info-paginacion').innerText = `Mostrando ${total > 0 ? inicio + 1 : 0}-${Math.min(fin, total)} de ${total} repuestos`;
    document.getElementById('btn-pag-prev').disabled = (paginaActual === 1);
    document.getElementById('btn-pag-sig').disabled = (paginaActual >= totalPaginas);
}

function cambiarPagina(delta) {
    paginaActual += delta;
    renderizarPaginacion();
}