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