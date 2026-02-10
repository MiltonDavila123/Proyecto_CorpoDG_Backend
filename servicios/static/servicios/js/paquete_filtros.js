(function($) {
    'use strict';

    $(document).ready(function() {
        var regionSelect = $('#id_region');
        var paisSelect = $('#id_pais_destino');
        var ciudadSelect = $('#id_ciudad_destino');

        function updatePaisOptions(pais_id) {
            var regionId = regionSelect.val();
            if (!regionId) {
                paisSelect.html('<option value="">---------</option>');
                paisSelect.val('');
                updateCiudadOptions(null);
                return;
            }

            $.ajax({
                url: '/api/admin-ajax/paises-por-region/' + regionId + '/',
                success: function(data) {
                    var options = '<option value="">---------</option>';
                    data.forEach(function(pais) {
                        options += '<option value="' + pais.id + '">' + pais.nombre + '</option>';
                    });
                    paisSelect.html(options);
                    
                    // Si hay un país preseleccionado (al editar), lo restauramos
                    if (pais_id) {
                        paisSelect.val(pais_id);
                    }
                    // Actualizamos las ciudades en base a la nueva lista de países
                    updateCiudadOptions(ciudadSelect.val());
                }
            });
        }

        function updateCiudadOptions(ciudad_id) {
            var paisId = paisSelect.val();
            if (!paisId) {
                ciudadSelect.html('<option value="">---------</option>');
                ciudadSelect.val('');
                return;
            }

            $.ajax({
                url: '/api/admin-ajax/ciudades-por-pais/' + paisId + '/',
                success: function(data) {
                    var options = '<option value="">---------</option>';
                    data.forEach(function(ciudad) {
                        options += '<option value="' + ciudad.id + '">' + ciudad.nombre + '</option>';
                    });
                    ciudadSelect.html(options);

                    // Si hay una ciudad preseleccionada, la restauramos
                    if (ciudad_id) {
                        ciudadSelect.val(ciudad_id);
                    }
                }
            });
        }

        regionSelect.on('change', function() {
            updatePaisOptions(null); // Al cambiar región, reseteamos el país
        });
        
        paisSelect.on('change', function() {
            updateCiudadOptions(null); // Al cambiar país, reseteamos la ciudad
        });

        // Carga inicial al abrir un paquete existente
        if (regionSelect.val()) {
            // Guardamos los valores actuales para restaurarlos después del AJAX
            var paisActual = paisSelect.val();
            var ciudadActual = ciudadSelect.val();
            
            // Llamamos a la función con los IDs para que se pre-seleccionen
            updatePaisOptions(paisActual);
            // La ciudad se actualizará dentro de updatePaisOptions
        }
    });
})(django.jQuery);
