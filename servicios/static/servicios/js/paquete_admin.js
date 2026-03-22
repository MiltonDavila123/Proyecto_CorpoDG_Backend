document.addEventListener('DOMContentLoaded', function() {
    // Referencias a los campos
    const diasInput = document.getElementById('id_duracion_dias');
    const nochesInput = document.getElementById('id_duracion_noches');
    const precioInput = document.getElementById('id_precio');

    // Función para validar que no existan valores negativos
    function preventNegativeInput(inputElement) {
        if (inputElement) {
            inputElement.addEventListener('input', function() {
                if (parseFloat(this.value) < 0) {
                    this.value = 0;
                }
            });
            
            // También validar cuando el elemento pierde el foco
            inputElement.addEventListener('change', function() {
                if (parseFloat(this.value) < 0) {
                    this.value = 0;
                }
            });
        }
    }

    // Aplicar la prohibición de valores negativos al precio
    preventNegativeInput(precioInput);
    preventNegativeInput(diasInput);
    preventNegativeInput(nochesInput);

    // Lógica para sincronizar y bloquear días y noches de forma automática
    if (diasInput && nochesInput) {
        
        function syncFromDias() {
            let diasValue = parseInt(diasInput.value, 10);
            if (!isNaN(diasValue) && diasValue > 0) {
                nochesInput.value = Math.max(0, diasValue - 1);
            } else if (!isNaN(diasValue) && diasValue === 0) {
                nochesInput.value = 0;
            }
        }

        function syncFromNoches() {
            let nochesValue = parseInt(nochesInput.value, 10);
            if (!isNaN(nochesValue) && nochesValue >= 0) {
                diasInput.value = nochesValue + 1;
            }
        }

        // Si escribo en días, actualizo noches
        diasInput.addEventListener('input', syncFromDias);
        diasInput.addEventListener('keyup', syncFromDias);
        diasInput.addEventListener('change', syncFromDias);

        // Si escribo en noches, actualizo días
        nochesInput.addEventListener('input', syncFromNoches);
        nochesInput.addEventListener('keyup', syncFromNoches);
        nochesInput.addEventListener('change', syncFromNoches);

        // Bloquear el campo opuesto al hacer foco (para que no pueda cambiarse el otro manualmente "al mismo tiempo")
        diasInput.addEventListener('focus', function() {
            nochesInput.setAttribute('readonly', 'readonly');
            nochesInput.style.backgroundColor = '#e9ecef'; // Color de campo bloqueado
        });

        nochesInput.addEventListener('focus', function() {
            diasInput.setAttribute('readonly', 'readonly');
            diasInput.style.backgroundColor = '#e9ecef'; // Color de campo bloqueado
        });

        // Desbloquear al perder el foco en caso de querer editar el otro
        diasInput.addEventListener('blur', function() {
            nochesInput.removeAttribute('readonly');
            nochesInput.style.backgroundColor = '';
        });

        nochesInput.addEventListener('blur', function() {
            diasInput.removeAttribute('readonly');
            diasInput.style.backgroundColor = '';
        });

        // Sincronización inicial al cargar la página
        // Especialmente útil para formularios nuevos donde "días" tiene un valor por defecto (ej: 1) o se precargó algo.
        if (diasInput.value && (nochesInput.value === '' || nochesInput.value === null)) {
            diasInput.dispatchEvent(new Event('input'));
        } else if (nochesInput.value && (diasInput.value === '' || diasInput.value === null)) {
            nochesInput.dispatchEvent(new Event('input'));
        }
    }
});