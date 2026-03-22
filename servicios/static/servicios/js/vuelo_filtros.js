/* Archivo: static/servicios/js/vuelo_filtros.js */

document.addEventListener('DOMContentLoaded', function() {
    
    // Evitar que el precio del vuelo sea negativo
    const precioInput = document.getElementById('id_precio');
    if (precioInput) {
        function validateNoNegative() {
            if (parseFloat(this.value) < 0) {
                this.value = 0;
            }
        }
        precioInput.addEventListener('input', validateNoNegative);
        precioInput.addEventListener('change', validateNoNegative);
    }
    
    var $ = (typeof django !== 'undefined' && django.jQuery) ? django.jQuery : (window.jQuery || undefined);

    if (!$) {
        console.error("Error: jQuery no encontrado. El script de filtros no funcionará.");
        return;
    }

    $(document).ready(function() {

        function setupFilters(prefix) {
            var ciudadSelect = $('#id_ciudad_' + prefix + '_filtro');
            var aeropuertoSelect = $('#id_' + prefix); // El select nativo de origen / destino
            
            if (!ciudadSelect.length || !aeropuertoSelect.length) {
                return;
            }

            // Inicializar Select2 en nuestro select regular de aeropuertos para que se vea bien en el Admin
            if ($.fn.select2) {
                aeropuertoSelect.select2({
                    width: '100%'
                });
            }

            // Guardamos el select de aeropuerto original si no está vacío
            var selectedAeropuertoId = aeropuertoSelect.val();

            function updateAeropuertoOptions(selectedId) {
                var ciudadId = ciudadSelect.val();

                if (!ciudadId) {
                    return;
                }
                
                var url = '/api/admin-ajax/aeropuertos-por-ciudad/' + ciudadId + '/';

                $.ajax({
                    url: url,
                    success: function(data) {
                        if (data.length > 0) {
                            // Limpiamos opciones existentes
                            aeropuertoSelect.empty();
                            
                            // Insertamos siempre un campo vacío al principio
                            aeropuertoSelect.append(new Option('---------', '', false, false));
                            
                            data.forEach(function(aeropuerto) {
                                var text = aeropuerto.nombre + ' (' + aeropuerto.codigo_iata + ')';
                                var option = new Option(text, aeropuerto.id, false, false);
                                aeropuertoSelect.append(option);
                            });

                            // Autoseleccionamos
                            if (selectedId) {
                                aeropuertoSelect.val(selectedId);
                            } else if (data.length > 0) {
                                // Seleccionar el primero por defecto si el usuario cambia la ciudad
                                aeropuertoSelect.val(data[0].id);
                            }
                            
                            // Notificar a select2 del cambio visual
                            aeropuertoSelect.trigger('change.select2');
                            aeropuertoSelect.trigger('change');
                        } else {
                            aeropuertoSelect.empty();
                            aeropuertoSelect.append(new Option('No hay aeropuertos para este país', '', false, false));
                            aeropuertoSelect.trigger('change.select2');
                            aeropuertoSelect.trigger('change');
                        }
                    },
                    error: function(xhr, errmsg, err) {
                        console.log("Error AJAX Aeropuertos: " + errmsg);
                    }
                });
            }

            // Evento: Al cambiar la ciudad, actualizamos la lista de aeropuertos en cascada
            ciudadSelect.on('change', function() {
                updateAeropuertoOptions(null);
            });
        }

        setupFilters('origen');
        setupFilters('destino');

    });
});
