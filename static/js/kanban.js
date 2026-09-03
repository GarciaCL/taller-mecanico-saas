function evaluarTiemposKanban() {
    const tarjetas = document.querySelectorAll('.card-orden');
    const ahora = new Date();

    tarjetas.forEach(card => {
        const fechaStr = card.getAttribute('data-fecha');
        const horasEstimadas = parseInt(card.getAttribute('data-horas') || '4');
        const estado = card.getAttribute('data-estado');
        const tag = card.querySelector('.tag-tiempo');

        if (fechaStr && estado !== 'entrega') {
            const fechaIngreso = new Date(fechaStr);
            const horasTranscurridas = Math.floor((ahora - fechaIngreso) / (1000 * 60 * 60));

            if (horasTranscurridas >= horasEstimadas) {
                card.classList.add('border-rose-500/80', 'bg-rose-950/20');
                if (tag) tag.innerHTML = `<span class="px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30 flex items-center gap-1">⚠️ Tiempo Excedido (+${horasTranscurridas - horasEstimadas}h)</span>`;
            } else {
                if (tag) tag.innerHTML = `<span class="px-2 py-0.5 rounded bg-slate-800 text-slate-400 flex items-center gap-1">⏱️ ${horasTranscurridas}h / ${horasEstimadas}h est.</span>`;
            }
        } else if (estado === 'entrega') {
            if (tag) tag.innerHTML = `<span class="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 flex items-center gap-1">✅ Listo</span>`;
        }
    });
}

let patenteActualModalOT = '';

function abrirDetalleOrden(id, patente, vehiculo, cliente, telefono, km, combustible, sintomas, costo, token, fechaStr, horasEst) {
    patenteActualModalOT = patente; // Guardar patente seleccionada

    document.getElementById('edit-orden-id').value = id;
    document.getElementById('archivar-orden-id').value = id;
    document.getElementById('m-patente').innerText = patente;
    document.getElementById('m-vehiculo').innerText = vehiculo;
    document.getElementById('m-cliente').value = cliente;
    document.getElementById('m-telefono').value = telefono;
    document.getElementById('edit-km').value = km;
    document.getElementById('edit-combustible').value = combustible;
    document.getElementById('edit-tiempo').value = horasEst || '4';
    document.getElementById('edit-sintomas').value = sintomas;
    document.getElementById('edit-costo').value = costo;

    document.getElementById('btn-pdf-modal').setAttribute('href', '/descargar_pdf/' + token);

    if (typeof cargarRepuestosVinculadosOT === 'function') {
        cargarRepuestosVinculadosOT(id);
    }

    const urlSeguimiento = "https://taller-mecanico-saas.onrender.com/seguimiento/" + token;
    const ahora = new Date();
    const fechaIngreso = new Date(fechaStr);
    const horasTranscurridas = Math.floor((ahora - fechaIngreso) / (1000 * 60 * 60));
    const esExcedido = horasTranscurridas >= parseInt(horasEst || '4');

    const alertBox = document.getElementById('m-alerta-box');
    let mensajeWa = esExcedido 
        ? `Hola ${cliente} 👋 Quería escribirte para comentarte el avance de tu vehículo ${vehiculo} (${patente}). Estamos afinando los últimos detalles técnicos para entregártelo perfecto. Puedes revisar el estatus aquí: ${urlSeguimiento}`
        : `Hola ${cliente} 👋 Puedes consultar el avance en tiempo real de tu vehículo ${vehiculo} (${patente}) aquí: ${urlSeguimiento}`;

    if (alertBox) {
        if (esExcedido) alertBox.classList.remove('hidden'); else alertBox.classList.add('hidden');
    }

    const telLimpio = telefono.replace(/\+/g, '').replace(/\s/g, '');
    document.getElementById('btn-whatsapp-modal').setAttribute('href', `https://wa.me/${telLimpio}?text=${encodeURIComponent(mensajeWa)}`);
    document.getElementById('modal-detalle').classList.remove('hidden');
}

// Función para abrir el modal del historial directamente desde el modal de detalle de OT
function abrirHistorialModalDesdeOT() {
    if (patenteActualModalOT) {
        abrirHistorialModal(patenteActualModalOT);
    }
}
function cerrarDetalleOrden() {
    document.getElementById('modal-detalle').classList.add('hidden');
}

// INICIALIZACIÓN DE SORTABLEJS PARA ESCRITORIO
document.querySelectorAll('.kanban-col').forEach(columna => {
    new Sortable(columna, {
        group: 'kanban',
        animation: 150,
        ghostClass: 'kanban-ghost',
        onEnd: function (evt) {
            const ordenId = evt.item.getAttribute('data-id');
            const nuevoEstado = evt.to.getAttribute('data-estado');
            
            moverOrdenDeEstadoAjax(ordenId, nuevoEstado);
        }
    });
});

// FUNCIÓN PARA MOVER LA TARJETA VÍA BOTONES MÓVILES O ARRASTRE
function moverOrdenDeEstadoAjax(ordenId, nuevoEstado) {
    const card = document.querySelector(`.card-orden[data-id="${ordenId}"]`);
    const destinoCol = document.getElementById(`col-${nuevoEstado}`);

    if (card && destinoCol && card.parentElement !== destinoCol) {
        destinoCol.appendChild(card);
    }

    if (card) {
        card.setAttribute('data-estado', nuevoEstado);
    }

    fetch('/cambiar_estado_ot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ orden_id: ordenId, nuevo_estado: nuevoEstado })
    })
    .then(r => r.json())
    .then(() => {
        evaluarTiemposKanban();
        generarBotonesMovilKanban();
    })
    .catch(err => console.error('Error al actualizar estado:', err));
}

// GENERAR BOTONES DE NAVEGACIÓN EN MÓVILES (ESTILO TRELLO)
function generarBotonesMovilKanban() {
    const flujoEstados = ['recepcion', 'diagnostico', 'reparacion', 'entrega'];
    const nombresEstados = {
        'recepcion': 'Recepción',
        'diagnostico': 'Diagnóstico',
        'reparacion': 'Reparación',
        'entrega': 'Entrega'
    };

    document.querySelectorAll('.card-orden').forEach(card => {
        const ordenId = card.getAttribute('data-id');
        const estadoActual = card.getAttribute('data-estado');
        const idxActual = flujoEstados.indexOf(estadoActual);

        // Limpiar controles móviles previos si existen
        let barraMovil = card.querySelector('.bar-control-movil');
        if (barraMovil) barraMovil.remove();

        // Crear la barra de controles móviles
        barraMovil = document.createElement('div');
        barraMovil.className = 'bar-control-movil lg:hidden flex justify-between gap-1 pt-2 mt-2 border-t border-slate-800/80';

        let htmlBotones = '';

        // Botón Estado Anterior (si no es el primero)
        if (idxActual > 0) {
            const estadoPrev = flujoEstados[idxActual - 1];
            htmlBotones += `
                <button type="button" 
                        onclick="event.stopPropagation(); moverOrdenDeEstadoAjax('${ordenId}', '${estadoPrev}')" 
                        class="bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold px-2 py-1 rounded text-[10px] flex items-center gap-1">
                    ⬅ ${nombresEstados[estadoPrev]}
                </button>`;
        } else {
            htmlBotones += `<div></div>`;
        }

        // Botón Estado Siguiente (si no es el último)
        if (idxActual < flujoEstados.length - 1) {
            const estadoSig = flujoEstados[idxActual + 1];
            htmlBotones += `
                <button type="button" 
                        onclick="event.stopPropagation(); moverOrdenDeEstadoAjax('${ordenId}', '${estadoSig}')" 
                        class="bg-blue-600 hover:bg-blue-500 text-white font-bold px-2 py-1 rounded text-[10px] flex items-center gap-1 shadow-sm">
                    ${nombresEstados[estadoSig]} ➔
                </button>`;
        }

        barraMovil.innerHTML = htmlBotones;
        card.appendChild(barraMovil);
    });
}

function filtrarKanbanPorMecanico(mecanicoId) {
    const cards = document.querySelectorAll('.card-orden');
    cards.forEach(card => {
        const mecId = card.getAttribute('data-mecanico');
        if (!mecanicoId || mecanicoId === '' || mecId === mecanicoId) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });
}

function evaluarNuevoMecanico(select) {
    if (select.value === 'NUEVO') {
        select.value = '';
        document.getElementById('modal-crear-mecanico').classList.remove('hidden');
    }
}

// Inicializar tiempos y controles en móviles al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    evaluarTiemposKanban();
    generarBotonesMovilKanban();
});

// FUNCIÓN PARA ARCHIVAR/ENTREGAR ORDEN DE TRABAJO
function confirmarArchivar() {
    const ordenId = document.getElementById('archivar-orden-id').value;

    if (!ordenId) {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'No se identificó el número de la orden de trabajo.'
        });
        return;
    }

    Swal.fire({
        title: '¿Entregar y Archivar Vehículo?',
        text: 'La orden pasará al historial de entregados y se liberará espacio en el tablero Kanban.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#10b981',
        cancelButtonColor: '#64748b',
        confirmButtonText: '✅ Sí, Entregar y Archivar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch('/archivar_ot', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ orden_id: ordenId })
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'ok') {
                    cerrarDetalleOrden();
                    // Remover la tarjeta del tablero en tiempo real
                    const card = document.querySelector(`.card-orden[data-id="${ordenId}"]`);
                    if (card) card.remove();

                    Swal.fire({
                        icon: 'success',
                        title: '¡Vehículo Entregado!',
                        text: 'La orden fue archivada con éxito.',
                        timer: 1500,
                        showConfirmButton: false
                    });
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Atención',
                        text: data.mensaje || 'No se pudo archivar la orden.'
                    });
                }
            })
            .catch(err => {
                console.error('Error al archivar la orden:', err);
                Swal.fire({
                    icon: 'error',
                    title: 'Error de Conexión',
                    text: 'Ocurrió un problema procesando la entrega.'
                });
            });
        }
    });
}

function cerrarModalMecanico() {
    document.getElementById('modal-crear-mecanico').classList.add('hidden');
}

function guardarMecanicoAjax() {
    const nombre = document.getElementById('mec-nombre').value.trim();
    const especialidad = document.getElementById('mec-especialidad').value.trim();

    if (!nombre) {
        Swal.fire({ icon: 'warning', title: 'Atención', text: 'Ingresa el nombre del mecánico.' });
        return;
    }

    fetch('/crear_mecanico_ajax', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nombre: nombre, especialidad: especialidad })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'ok') {
            // Agregar al select del modal de la OT activa
            const selectOT = document.getElementById('select-mecanico-ot'); // Asegúrate que tu select en crear_ot.html tenga id="select-mecanico-ot"
            if (selectOT) {
                const opt = document.createElement('option');
                opt.value = data.id;
                opt.textContent = data.nombre;
                opt.selected = true;
                selectOT.appendChild(opt);
            }

            cerrarModalMecanico();
            document.getElementById('form-crear-mecanico-ajax').reset();

            Swal.fire({
                icon: 'success',
                title: 'Mecánico Registrado',
                text: `${data.nombre} ha sido asignado a la orden actual.`,
                timer: 1500,
                showConfirmButton: false
            });
        } else {
            Swal.fire({ icon: 'error', title: 'Error', text: data.mensaje });
        }
    });
}

function previsualizarFoto(input, imgId) {
    const img = document.getElementById(imgId);
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            img.src = e.target.result;
            img.classList.remove('hidden');
        }
        reader.readAsDataURL(input.files[0]);
    }
}

function buscarPatenteExistente(patente) {
    if (!patente || patente.trim().length < 3) return;

    fetch('/api/buscar_vehiculo/' + encodeURIComponent(patente.trim()))
        .then(r => r.json())
        .then(data => {
            if (data.encontrado) {
                // Auto-completar pero dejando los campos editables si es un nuevo usuario/dueño
                if (data.cliente) document.getElementById('ot-input-cliente').value = data.cliente;
                if (data.telefono) document.getElementById('ot-input-telefono').value = data.telefono;
                if (data.marca) document.getElementById('ot-input-marca').value = data.marca;
                if (data.modelo) document.getElementById('ot-input-modelo').value = data.modelo;

                const banner = document.getElementById('banner-vehiculo-encontrado');
                if (banner) {
                    banner.classList.remove('hidden');
                    banner.innerText = "ℹ️ Vehículo registrado previamente. Puedes modificar el cliente si cambió de dueño.";
                }
            }
        })
        .catch(err => console.error("Error buscando patente:", err));
}