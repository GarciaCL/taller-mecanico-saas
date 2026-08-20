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
    document.getElementById('hist-modal-patente').innerText = patente;
    const cont = document.getElementById('hist-modal-contenedor');
    cont.innerHTML = '<div class="text-center text-slate-500 py-6">🔍 Cargando historial de intervenciones...</div>';
    document.getElementById('modal-historial').classList.remove('hidden');

    fetch('/api/historial/' + encodeURIComponent(patente))
        .then(res => {
            if (!res.ok) throw new Error('Error al obtener datos');
            return res.json();
        })
        .then(data => {
            if (!data || data.length === 0) {
                cont.innerHTML = '<div class="text-center text-slate-500 py-6">No hay registros de atenciones previas para este vehículo.</div>';
                return;
            }

            let html = '<div class="space-y-3">';
            data.forEach(ot => {
                const subtotalStr = Number(ot.costo).toLocaleString('es-CL');
                const kmStr = Number(ot.km).toLocaleString('es-CL');

                html += `
                    <div class="bg-slate-950 border border-slate-800 p-4 rounded-xl space-y-2">
                        <div class="flex justify-between items-center text-xs">
                            <span class="font-bold text-blue-400 font-mono">OT #${ot.id} - ${ot.fecha}</span>
                            <span class="bg-slate-800 text-emerald-400 font-bold px-2 py-0.5 rounded">$${subtotalStr}</span>
                        </div>
                        <div class="text-xs text-white font-semibold">👤 ${ot.cliente} (${ot.telefono})</div>
                        <p class="text-xs text-slate-300 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/80">🔧 ${ot.sintomas}</p>
                        <div class="flex justify-between items-center pt-1 text-[11px] text-slate-400">
                            <span>🏎️ ${kmStr} KM | ⛽ ${ot.combustible}</span>
                            <a href="/descargar_pdf/${ot.token}" target="_blank" class="text-blue-400 hover:underline font-semibold flex items-center gap-1">📄 Ver PDF OT</a>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            cont.innerHTML = html;
        })
        .catch(err => {
            console.error(err);
            cont.innerHTML = '<div class="text-center text-rose-400 py-6">⚠️ Ocurrió un error al cargar el historial del vehículo.</div>';
        });
}

function cerrarModalHistorial() {
    document.getElementById('modal-historial').classList.add('hidden');
}

function cerrarModalHistorial() {
    document.getElementById('modal-historial').classList.add('hidden');
}