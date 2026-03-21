/* Archivo: static/servicios/js/destino_filtros.js */

document.addEventListener('DOMContentLoaded', function() {

    var $ = (typeof django !== 'undefined' && django.jQuery) ? django.jQuery : (window.jQuery || undefined);
    if (!$) {
        console.error('Error: jQuery no encontrado. El script de filtros no funcionará.');
        return;
    }

    $(document).ready(function() {
        console.log('Script de interdependencia País-Ciudad (Autocomplete) cargado correctamente.');

        var $pais = $('#id_pais');
        var $ciudad = $('#id_ciudad');

        if ($pais.length === 0 || $ciudad.length === 0) {
            return; // Evita errores en páginas donde no estén estos campos
        }

        // 1. Interceptar llamadas AJAX del Autocomplete de Django
        $.ajaxPrefilter(function(options, originalOptions, jqXHR) {
            if (options.url && options.url.indexOf('/admin/autocomplete/') !== -1) {
                if (options.data && typeof options.data === 'string' && options.data.indexOf('field_name=ciudad') !== -1) {
                    var paisId = $pais.val();
                    if (paisId) {
                        options.data += '&pais_id=' + encodeURIComponent(paisId);
                    }
                }
            }
        });

        // 2. Si se elige Ciudad sin País, auto-completar País
        $ciudad.on('change', function() {
            var ciudadId = $(this).val();
            var paisId = $pais.val();
            
            if (ciudadId && !paisId) {
                $.ajax({
                    url: '/api/ciudades/' + ciudadId + '/',
                    method: 'GET',
                    success: function(response) {
                        if (response.pais && response.pais_nombre) {
                            var newOption = new Option(response.pais_nombre, response.pais, true, true);
                            $pais.append(newOption).trigger('change.select2');
                        }
                    },
                    error: function(xhr, errmsg, err) {
                        console.log('Error consultando la ciudad elegida:', errmsg);
                    }
                });
            }
        });

        // 3. Si cambias el país y la ciudad seleccionada no es de ese país, vaciarla.
        $pais.on('change', function() {
            var paisId = $(this).val();
            var ciudadId = $ciudad.val();
            
            if (paisId && ciudadId) {
                $.ajax({
                    url: '/api/ciudades/' + ciudadId + '/',
                    method: 'GET',
                    success: function(response) {
                        if (String(response.pais) !== String(paisId)) {
                            $ciudad.val(null).trigger('change.select2');
                        }
                    }
                });
            }
        });

    });
});
