
function confirmarBorrado(id) {
    if (confirm("¿Estás seguro de que deseas eliminar este registro?")) {
        window.location.href = '/borrar/' + id;
    }
}