function convertirCotizacionOtAjax(cotId) {
    Swal.fire({
        title: '¿Convertir Presupuesto a OT?',
        text: "Se ingresará automáticamente el vehículo al Tablero Kanban en la columna Recepción.",
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#3b82f6',
        confirmButtonText: 'Sí, Convertir e Ingresar'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch('/convertir_cotizacion_ot/' + cotId, { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        Swal.fire({ title: '¡Convertida!', text: 'El vehículo fue ingresado al Kanban.', icon: 'success' })
                            .then(() => location.reload());
                    }
                });
        }
    });
}

function evaluarNuevaMarcaCot() {
    const select = document.getElementById('select-marca-cot');
    const inputNueva = document.getElementById('input-marca-nueva-cot');
    if (select && inputNueva) {
        if (select.value === 'OTRA') {
            inputNueva.classList.remove('hidden');
        } else {
            inputNueva.classList.add('hidden');
        }
    }
}

function autocompletarDatosCotizacion() {
    const patente = document.getElementById('cot-patente-input').value.trim();
    if (patente.length < 5) return;

    fetch('/buscar_patente_cotizacion/' + encodeURIComponent(patente))
        .then(res => res.json())
        .then(data => {
            if (data && data.encontrado) {
                document.getElementById('cot-cliente-input').value = data.cliente;
                document.getElementById('cot-telefono-input').value = data.telefono;
                document.getElementById('cot-modelo-input').value = data.modelo;

                const selectMarca = document.getElementById('select-marca-cot');
                if (selectMarca) {
                    selectMarca.value = data.marca;
                    evaluarNuevaMarcaCot();
                }

                document.getElementById('cot-msg-autocompletado').classList.remove('hidden');
            }
        });
}

function rechazarCotizacionAjax(cotId) {
    Swal.fire({
        title: '¿Marcar Cotización como Rechazada?',
        text: "La cotización quedará archivada en el histórico del taller.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#e11d48',
        confirmButtonText: 'Sí, Rechazar'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch('/rechazar_cotizacion/' + cotId, { method: 'POST' })
                .then(res => res.json())
                .then(() => location.reload());
        }
    });
}

function revalidarCotizacionAjax(cotId) {
    Swal.fire({
        title: '¿Revalidar Presupuesto?',
        text: "Se actualizará la fecha del presupuesto a hoy para renovar su validez por 15 días hábiles.",
        icon: 'info',
        showCancelButton: true,
        confirmButtonColor: '#d97706',
        confirmButtonText: 'Sí, Revalidar Fecha'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch('/revalidar_cotizacion/' + cotId, { method: 'POST' })
                .then(res => res.json())
                .then(() => location.reload());
        }
    });
}

function actualizarModelosSegunMarca(prefix) {
    const selectMarca = document.getElementById(`select-marca-${prefix}`);
    const inputMarcaNueva = document.getElementById(`input-marca-nueva-${prefix}`);
    const selectModelo = document.getElementById(`select-modelo-${prefix}`);
    const inputModeloNuevo = document.getElementById(`input-modelo-nuevo-${prefix}`);

    if (!selectMarca || !selectModelo) return;

    const marcaSeleccionada = selectMarca.value;

    if (marcaSeleccionada === 'OTRA') {
        inputMarcaNueva.classList.remove('hidden');
        selectModelo.innerHTML = '<option value="OTRO">+ Agregar Nuevo Modelo...</option>';
        selectModelo.value = 'OTRO';
        evaluarNuevoModelo(prefix);
    } else {
        inputMarcaNueva.classList.add('hidden');
        selectModelo.innerHTML = '<option value="">Seleccionar Modelo...</option>';

        if (typeof mapaMarcasModelos !== 'undefined' && mapaMarcasModelos[marcaSeleccionada]) {
            mapaMarcasModelos[marcaSeleccionada].forEach(mod => {
                const opt = document.createElement('option');
                opt.value = mod;
                opt.innerText = mod;
                selectModelo.appendChild(opt);
            });
        }

        const optOtro = document.createElement('option');
        optOtro.value = 'OTRO';
        optOtro.innerText = '+ Agregar Nuevo Modelo...';
        selectModelo.appendChild(optOtro);

        if (inputModeloNuevo) inputModeloNuevo.classList.add('hidden');
    }
}

function evaluarNuevoModelo(prefix) {
    const selectModelo = document.getElementById(`select-modelo-${prefix}`);
    const inputModeloNuevo = document.getElementById(`input-modelo-nuevo-${prefix}`);

    if (selectModelo && inputModeloNuevo) {
        if (selectModelo.value === 'OTRO') {
            inputModeloNuevo.classList.remove('hidden');
        } else {
            inputModeloNuevo.classList.add('hidden');
        }
    }
}

let listaItemsCot = [];

function buscarClientePorContactoCot() {
    const q = document.getElementById('cot-telefono-input').value.trim();
    const msg = document.getElementById('cot-msg-cliente-hallado');

    if (q.length < 3) {
        if (msg) msg.classList.add('hidden');
        return;
    }

    fetch('/api/buscar_cliente_contacto?q=' + encodeURIComponent(q))
        .then(res => res.json())
        .then(data => {
            if (data && data.encontrado) {
                document.getElementById('cot-cliente-input').value = data.nombre;
                if (msg) msg.classList.remove('hidden');
            } else {
                if (msg) msg.classList.add('hidden');
            }
        });
}

function seleccionarRepuestoBodegaCot() {
    const select = document.getElementById('cot-item-select');
    const opt = select.options[select.selectedIndex];
    if (opt && opt.value !== '') {
        document.getElementById('cot-item-desc').value = opt.getAttribute('data-nombre');
        document.getElementById('cot-item-precio').value = opt.getAttribute('data-precio') || 0;
    }
}

function agregarLineaCotizacion() {
    const select = document.getElementById('cot-item-select');
    const descInput = document.getElementById('cot-item-desc').value.trim();
    const cant = parseInt(document.getElementById('cot-item-cant').value) || 1;
    const precio = parseFloat(document.getElementById('cot-item-precio').value) || 0;

    const invId = select.value !== '' ? parseInt(select.value) : null;
    const desc = descInput || (select.options[select.selectedIndex] ? select.options[select.selectedIndex].getAttribute('data-nombre') : 'Servicio / Repuesto');

    if (!desc || desc === '') {
        Swal.fire('Atención', 'Ingresa una descripción o selecciona un repuesto', 'warning');
        return;
    }

    listaItemsCot.push({
        inventario_id: invId,
        descripcion: desc,
        cantidad: cant,
        precio_unidad: precio
    });

    // Limpiar inputs
    select.value = '';
    document.getElementById('cot-item-desc').value = '';
    document.getElementById('cot-item-cant').value = '1';
    document.getElementById('cot-item-precio').value = '';

    renderizarItemsCot();
}

function eliminarLineaCot(index) {
    listaItemsCot.splice(index, 1);
    renderizarItemsCot();
}

function renderizarItemsCot() {
    const cont = document.getElementById('cot-items-contenedor');
    const sinItems = document.getElementById('cot-sin-items');
    const totalVista = document.getElementById('cot-total-vista');
    const inputHidden = document.getElementById('items_cotizacion_json');

    if (!cont) return;

    if (listaItemsCot.length === 0) {
        cont.innerHTML = '<span id="cot-sin-items" class="text-[11px] text-slate-500 italic block text-center py-2">Sin ítems o repuestos añadidos al presupuesto.</span>';
        if (totalVista) totalVista.innerText = 'Total: $0';
        if (inputHidden) inputHidden.value = '[]';
        return;
    }

    let html = '';
    let sumaTotal = 0;

    listaItemsCot.forEach((it, idx) => {
        const subtotal = it.cantidad * it.precio_unidad;
        sumaTotal += subtotal;

        html += `
            <div class="flex justify-between items-center bg-slate-900 border border-slate-800/80 px-3 py-2 rounded-xl text-xs">
                <span class="text-white font-semibold">${it.descripcion} x${it.cantidad}</span>
                <div class="flex items-center gap-3">
                    <span class="text-emerald-400 font-bold">$${subtotal.toLocaleString('es-CL')}</span>
                    <button type="button" onclick="eliminarLineaCot(${idx})" class="text-rose-400 hover:text-rose-300 font-bold">✕</button>
                </div>
            </div>
        `;
    });

    cont.innerHTML = html;
    if (totalVista) totalVista.innerText = 'Total Válido: $' + sumaTotal.toLocaleString('es-CL');
    if (inputHidden) inputHidden.value = JSON.stringify(listaItemsCot);
}