function editarClienteModal(id, nombre, rut, telefono) {
    document.getElementById('cli-edit-id').value = id;
    document.getElementById('cli-vehiculo-cliente-id').value = id;
    document.getElementById('cli-edit-nombre').value = nombre;
    document.getElementById('cli-edit-rut').value = rut;
    document.getElementById('cli-edit-telefono').value = telefono;

    fetch('/obtener_cliente/' + id)
        .then(res => res.json())
        .then(data => {
            const cont = document.getElementById('cli-lista-vehiculos');
            if (data && data.vehiculos && data.vehiculos.length > 0) {
                let html = '<ul class="space-y-1">';
                data.vehiculos.forEach(v => {
                    html += `<li class="flex justify-between items-center bg-slate-900 p-2 rounded-lg border border-slate-800">
                        <span class="font-mono font-bold text-blue-400">[${v[1]}]</span>
                        <span class="text-white font-semibold">${v[2]} ${v[3]}</span>
                        <span class="text-slate-400 text-[10px]">${v[4]} KM</span>
                    </li>`;
                });
                html += '</ul>';
                cont.innerHTML = html;
            } else {
                cont.innerHTML = '<span class="text-slate-500 italic">No tiene vehículos registrados.</span>';
            }
            document.getElementById('modal-editar-cliente').classList.remove('hidden');
        });
}

function cerrarModalCliente() {
    document.getElementById('modal-editar-cliente').classList.add('hidden');
}