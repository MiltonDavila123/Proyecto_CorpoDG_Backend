/* Archivo: static/servicios/js/paquete_filtros.js */

// Usamos un event listener nativo para esperar a que cargue el DOM
document.addEventListener('DOMContentLoaded', function() {
    
    // Verificamos si django.jQuery existe, si no, intentamos usar jQuery global
    var $ = (typeof django !== 'undefined' && django.jQuery) ? django.jQuery : (window.jQuery || undefined);

    if (!$) {
        console.error("Error: jQuery no encontrado. El script de filtros no funcionará.");
        return;
    }

    // Aquí comienza tu lógica original
    $(document).ready(function() {
        console.log("Script de filtros cargado correctamente."); // Debug

        var regionSelect = $('#id_region');
        var paisSelect = $('#id_pais_destino');
        var ciudadSelect = $('#id_ciudad_destino');

        // Función para cargar países
        function updatePaisOptions(selectedPaisId, selectedCiudadId) {
            var regionId = regionSelect.val();
            
            if (!regionId) {
                paisSelect.html('<option value="">---------</option>').val('').trigger('change');
                ciudadSelect.html('<option value="">---------</option>').val('');
                return;
            }

            paisSelect.html('<option value="">Cargando países...</option>');

            $.ajax({
                url: '/api/admin-ajax/paises-por-region/' + regionId + '/',
                success: function(data) {
                    var options = '<option value="">---------</option>';
                    data.forEach(function(pais) {
                        options += '<option value="' + pais.id + '">' + pais.nombre + '</option>';
                    });
                    paisSelect.html(options);
                    
                    // Si la región es Ecuador, auto-seleccionar el país Ecuador
                    var regionText = regionSelect.find('option:selected').text().trim().toLowerCase();
                    if (regionText === 'ecuador' && !selectedPaisId) {
                        // Buscar la opción Ecuador y seleccionarla
                        paisSelect.find('option').each(function() {
                            if ($(this).text().trim().toLowerCase() === 'ecuador') {
                                paisSelect.val($(this).val());
                                updateCiudadOptions(null);
                                return false; // break
                            }
                        });
                    } else if (selectedPaisId) {
                        paisSelect.val(selectedPaisId);
                        updateCiudadOptions(selectedCiudadId);
                    }
                },
                error: function(xhr, errmsg, err) {
                    console.log("Error AJAX Paises: " + errmsg);
                }
            });
        }

        // Función para cargar ciudades
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

        // Eventos
        regionSelect.on('change', function() {
            updatePaisOptions(null, null);
        });
        
        paisSelect.on('change', function() {
            updateCiudadOptions(null);
        });

        // Lógica de inicio (Editar registro existente)
        if (regionSelect.val()) {
            var paisActual = paisSelect.val();
            var ciudadActual = ciudadSelect.val();
            updatePaisOptions(paisActual, ciudadActual);
        }
    });
});