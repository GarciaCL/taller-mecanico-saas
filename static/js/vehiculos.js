function filtrarVehiculosCRM() {
    const query = document.getElementById('filtro-vehiculo-input').value.toLowerCase().trim();
    const filas = document.querySelectorAll('.fila-vehiculo-crm');

    filas.forEach(f => {
        const txt = f.innerText.toLowerCase();
        f.style.display = txt.includes(query) ? '' : 'none';
    });
}

function ordenarVehiculosCRM(criterio) {
    fetch('/obtener_vehiculos_crm?orden=' + criterio)
        .then(res => res.json())
        .then(data => {
            const tbody = document.getElementById('tbody-vehiculos-crm');
            let html = '';

            data.forEach(v => {
                let badgeRt = `<span class="px-2.5 py-1 rounded-lg bg-slate-800 text-slate-400 text-[10px]">✅ Al día (Mes ${v.mes_rt})</span>`;
                if (v.alerta_rt === 'urgente') {
                    badgeRt = `<span class="px-2.5 py-1 rounded-lg bg-rose-500/20 border border-rose-500/30 text-rose-300 text-[10px] font-bold">🔴 Vence este mes (Dígito ${v.digito})</span>`;
                } else if (v.alerta_rt === 'proximo') {
                    badgeRt = `<span class="px-2.5 py-1 rounded-lg bg-amber-500/20 border border-amber-500/30 text-amber-300 text-[10px] font-bold">⚠️ Vence próximo mes</span>`;
                }

                const telLimpio = v.telefono.replace(/\+/g, '').replace(/\s/g, '');
                const msgWa = encodeURIComponent(`Hola ${v.cliente} 👋 Te escribimos del taller para recordarte que tu vehículo ${v.vehiculo} (${v.patente}) está próximo a su revisión/mantención sugerida.`);

                html += `<tr class="fila-vehiculo-crm hover:bg-slate-900/50">
                    <td class="p-4 font-mono font-bold text-white bg-slate-950/40 rounded-lg">${v.patente}</td>
                    <td class="p-4 font-bold text-slate-200">${v.vehiculo}</td>
                    <td class="p-4"><span class="block font-bold text-white">${v.cliente}</span><span class="block text-[10px] text-slate-400">📱 ${v.telefono}</span></td>
                    <td class="p-4"><span class="block font-bold text-slate-200">${v.km_actual.toLocaleString('es-CL')} KM</span><span class="block text-[10px] text-emerald-400">🛢️ Prox: ${v.km_proximo_aceite.toLocaleString('es-CL')} KM</span></td>
                    <td class="p-4">${badgeRt}</td>
                    <td class="p-4 font-semibold text-slate-400">${v.ultima_visita}</td>
                    <td class="p-4 text-right flex justify-end gap-2">
                        <a href="/historial/${v.patente}" target="_blank" class="bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold px-2.5 py-1.5 rounded-lg text-[11px]">📜 Historial</a>
                        <a href="https://wa.me/${telLimpio}?text=${msgWa}" target="_blank" class="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-2.5 py-1.5 rounded-lg text-[11px] shadow-lg shadow-emerald-600/20">📱 Recordatorio</a>
                    </td>
                </tr>`;
            });

            tbody.innerHTML = html;
        });
}

function abrirHistorialModal(patente) {
    const elPatente = document.getElementById('modal-historial-patente');
    const contenedor = document.getElementById('contenedor-historial-lista');
    const modal = document.getElementById('modal-historial');

    if (!modal || !contenedor) {
        console.error("No se encontraron los elementos del modal de historial en el DOM.");
        return;
    }

    if (elPatente) {
        elPatente.innerText = patente;
    }

    contenedor.innerHTML = '<p class="text-center text-slate-500 py-6">Cargando historial...</p>';
    
    modal.classList.remove('hidden');
    modal.classList.add('flex');

    fetch('/api/historial/' + patente)
        .then(r => r.json())
        .then(data => {
            if (!data || data.length === 0) {
                contenedor.innerHTML = '<p class="text-center text-slate-500 py-6">No hay registros de atenciones previas para este vehículo.</p>';
                return;
            }

            let html = '';
            data.forEach(h => {
                let badgeEstado = '';
                
                if (h.archivada || h.estado === 'finalizado') {
                    badgeEstado = '<span class="px-2.5 py-1 rounded-lg bg-emerald-500/20 text-emerald-400 font-bold border border-emerald-500/30">✅ ENTREGADO Y ARCHIVADO</span>';
                } else if (h.estado === 'entrega') {
                    badgeEstado = '<span class="px-2.5 py-1 rounded-lg bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30">🚀 LISTO PARA ENTREGA</span>';
                } else {
                    badgeEstado = `<span class="px-2.5 py-1 rounded-lg bg-blue-500/20 text-blue-400 font-bold border border-blue-500/30">🔧 EN TALLER (${h.estado.toUpperCase()})</span>`;
                }

                html += `
                    <div class="bg-slate-950 border ${h.archivada ? 'border-slate-800/60' : 'border-blue-500/40'} p-4 rounded-xl space-y-2">
                        <div class="flex justify-between items-start">
                            <div>
                                <span class="font-mono font-bold text-amber-400 text-sm">OT #${h.id}</span>
                                <span class="text-slate-500 text-[11px] block">📅 Ingreso: ${h.fecha}</span>
                            </div>
                            <div class="text-right">
                                ${badgeEstado}
                                <span class="block text-emerald-400 font-bold text-sm mt-1">$${Number(h.costo).toLocaleString('es-CL')}</span>
                            </div>
                        </div>

                        <div class="grid grid-cols-2 gap-2 text-[11px] bg-slate-900/60 p-2 rounded-lg border border-slate-800/80">
                            <div><b class="text-slate-400">Kilometraje:</b> <span class="text-slate-200">${Number(h.km).toLocaleString('es-CL')} KM</span></div>
                            <div><b class="text-slate-400">Combustible:</b> <span class="text-slate-200">${h.combustible}</span></div>
                        </div>

                        <p class="text-slate-300 text-xs bg-slate-900/40 p-2 rounded-lg"><b class="text-slate-400">Motivo / Síntomas:</b> ${h.sintomas || 'Sin detalle'}</p>

                        <div class="text-right pt-1">
                            <a href="/descargar_pdf/${h.token}" target="_blank" class="text-amber-400 hover:text-amber-300 font-semibold text-[11px]">📄 Descargar PDF Ficha</a>
                        </div>
                    </div>
                `;
            });

            contenedor.innerHTML = html;
        })
        .catch(err => {
            console.error("Error cargando historial:", err);
            contenedor.innerHTML = '<p class="text-center text-rose-400 py-6">Error al obtener el historial.</p>';
        });
}

function cerrarHistorialModal() {
    const modal = document.getElementById('modal-historial');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

function cerrarModalHistorial() {
    document.getElementById('modal-historial').classList.add('hidden');
}

function cerrarModalHistorial() {
    document.getElementById('modal-historial').classList.add('hidden');
}