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