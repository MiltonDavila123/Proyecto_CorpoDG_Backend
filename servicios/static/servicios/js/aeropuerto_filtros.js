/* Archivo: static/servicios/js/aeropuerto_filtros.js */

document.addEventListener('DOMContentLoaded', function() {

    var $ = (typeof django !== 'undefined' && django.jQuery) ? django.jQuery : (window.jQuery || undefined);
    if (!$) {
        console.error("Error: jQuery no encontrado. El script de filtros no funcionará.");
        return;
    }

    $(document).ready(function() {
        console.log("Script de filtros de aeropuerto cargado correctamente."); // Debug

        var paisSelect = $('#id_pais');
        var ciudadSelect = $('#id_ciudad');

        function updateCiudadOptions(selectedCiudadId) {
            var paisId = paisSelect.val();

            if (!paisId) {
                ciudadSelect.html('<option value="">---------</option>').val('');
                return;
            }

            ciudadSelect.html('<option value="">Cargando ciudades...</option>');

            $.ajax({
                url: '/api/admin-ajax/ciudades-por-pais/' + paisId + '/',
                success: function(data) {
                    var options = '<option value="">---------</option>';
                    data.forEach(function(ciudad) {
                        options += '<option value="' + ciudad.id + '">' + ciudad.nombre + '</option>';
                    });
                    ciudadSelect.html(options);

                    if (selectedCiudadId) {
                        ciudadSelect.val(selectedCiudadId);
                    }
                },
                error: function(xhr, errmsg, err) {
                    console.log("Error AJAX Ciudades: " + errmsg);
                }
            });
        }

        paisSelect.on('change', function() {
            updateCiudadOptions(null);
        });

        // Lógica de inicio (Editar registro existente)
        if (paisSelect.val() && !ciudadSelect.val()) {
             // Si hay pais por defecto pero ciudad vacia al cargar o por error
             // En edicion normal la ciudad ya viene cargada desde el backend
             // asi que este paso podria sobreescribirla si no tenemos el ID
             // Para estar seguros de no perder la ciudad si Django ya la renderizó, no actualizamos si no es necesario.
        } else if (paisSelect.val() && ciudadSelect.val() === "") {
             // updateCiudadOptions(null);
        }
        
    });
});
