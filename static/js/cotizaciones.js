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