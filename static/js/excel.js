function descargarPlantillaExcel() {
    const data = [
        { codigo: "FIL-001", nombre: "Filtro de Aceite Nissan", categoria: "Filtros", stock: 15, compatabilidades: "Nissan Qashqai, Nissan X-Trail" },
        { codigo: "PAST-002", nombre: "Pastillas de Freno Delanteras", categoria: "Frenos", stock: 8, compatabilidades: "Toyota Yaris, Toyota Corolla" }
    ];
    const ws = XLSX.utils.json_to_sheet(data);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Plantilla_Inventario");
    XLSX.writeFile(wb, "Plantilla_Carga_Inventario.xlsx");
}

let repuestosMasivosLeidos = [];

document.getElementById('archivo-excel-input').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function(evt) {
        const bstr = evt.target.result;
        const wb = XLSX.read(bstr, { type: 'binary' });
        const wsname = wb.SheetNames[0];
        const ws = wb.Sheets[wsname];
        repuestosMasivosLeidos = XLSX.utils.sheet_to_json(ws);

        const divPreview = document.getElementById('vista-previa-excel');
        divPreview.classList.remove('hidden');
        divPreview.innerHTML = `<strong>${repuestosMasivosLeidos.length} repuestos detectados:</strong><br/>` + 
            repuestosMasivosLeidos.slice(0, 5).map(r => `• [${r.codigo || 'S/C'}] ${r.nombre || ''} (Stock: ${r.stock || 0})`).join('<br/>') +
            (repuestosMasivosLeidos.length > 5 ? '<br/><i>...y más</i>' : '');
    };
    reader.readAsBinaryString(file);
});

function procesarCargaMasivaExcel() {
    if (repuestosMasivosLeidos.length === 0) {
        Swal.fire({ title: 'Atención', text: 'Por favor selecciona un archivo con datos válidos.', icon: 'warning' });
        return;
    }

    fetch('/carga_masiva_repuestos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repuestos: repuestosMasivosLeidos })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            Swal.fire({
                title: '¡Carga Exitosa!',
                text: `Se importaron ${data.count} repuestos correctamente.`,
                icon: 'success',
                confirmButtonColor: '#10b981'
            }).then(() => location.reload());
        } else {
            Swal.fire({ title: 'Error', text: 'No se pudieron importar los datos.', icon: 'error' });
        }
    });
}