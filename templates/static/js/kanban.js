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
                tag.innerHTML = `<span class="px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30 flex items-center gap-1">⚠️ Tiempo Excedido (+${horasTranscurridas - horasEstimadas}h)</span>`;
            } else {
                tag.innerHTML = `<span class="px-2 py-0.5 rounded bg-slate-800 text-slate-400 flex items-center gap-1">⏱️ ${horasTranscurridas}h / ${horasEstimadas}h est.</span>`;
            }
        } else if (estado === 'entrega') {
            tag.innerHTML = `<span class="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 flex items-center gap-1">✅ Listo</span>`;
        }
    });
}

function abrirDetalleOrden(id, patente, vehiculo, cliente, telefono, km, combustible, sintomas, costo, token, fechaStr, horasEst) {
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

    document.getElementById('btn-historial-patente').setAttribute('href', '/historial/' + patente);
    document.getElementById('btn-pdf-modal').setAttribute('href', '/descargar_pdf/' + token);

    cargarRepuestosVinculadosOT(id);

    const urlSeguimiento = "https://taller-mecanico-saas.onrender.com/seguimiento/" + token;
    const ahora = new Date();
    const fechaIngreso = new Date(fechaStr);
    const horasTranscurridas = Math.floor((ahora - fechaIngreso) / (1000 * 60 * 60));
    const esExcedido = horasTranscurridas >= parseInt(horasEst || '4');

    const alertBox = document.getElementById('m-alerta-box');
    let mensajeWa = esExcedido 
        ? `Hola ${cliente} 👋 Quería escribirte para comentarte el avance de tu vehículo ${vehiculo} (${patente}). Estamos afinando los últimos detalles técnicos para entregártelo perfecto. Puedes revisar el estatus aquí: ${urlSeguimiento}`
        : `Hola ${cliente} 👋 Puedes consultar el avance en tiempo real de tu vehículo ${vehiculo} (${patente}) aquí: ${urlSeguimiento}`;

    if (esExcedido) alertBox.classList.remove('hidden'); else alertBox.classList.add('hidden');

    const telLimpio = telefono.replace(/\+/g, '').replace(/\s/g, '');
    document.getElementById('btn-whatsapp-modal').setAttribute('href', `https://wa.me/${telLimpio}?text=${encodeURIComponent(mensajeWa)}`);
    document.getElementById('modal-detalle').classList.remove('hidden');
}

function cerrarDetalleOrden() {
    document.getElementById('modal-detalle').classList.add('hidden');
}

document.querySelectorAll('.kanban-col').forEach(columna => {
    new Sortable(columna, {
        group: 'kanban',
        animation: 150,
        ghostClass: 'kanban-ghost',
        onEnd: function (evt) {
            const ordenId = evt.item.getAttribute('data-id');
            const nuevoEstado = evt.to.getAttribute('data-estado');
            evt.item.setAttribute('data-estado', nuevoEstado);

            fetch('/cambiar_estado_ot', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ orden_id: ordenId, nuevo_estado: nuevoEstado })
            }).then(() => evaluarTiemposKanban());
        }
    });
});