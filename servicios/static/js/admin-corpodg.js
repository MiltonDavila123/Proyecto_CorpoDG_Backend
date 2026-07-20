/* JS del panel admin CorpoDG (cargado por jazzmin custom_js en todas las páginas)
   - Banner de notificación de reservas sin revisar (se refresca cada minuto). */
(function () {
  'use strict';

  var ESTILOS = [
    '#corpodg-notif-reservas {',
    '  display: none; position: fixed; top: 70px; right: 18px; z-index: 9999;',
    '  max-width: 320px; background: #1a365d; color: #fff;',
    '  border-left: 5px solid #ed8936; border-radius: 8px;',
    '  box-shadow: 0 4px 14px rgba(0,0,0,0.35); padding: 14px 16px;',
    '  font-size: 0.85rem;',
    '}',
    '#corpodg-notif-reservas strong { color: #ed8936; }',
    '#corpodg-notif-reservas a { color: #fff; text-decoration: underline; }',
    '#corpodg-notif-reservas .notif-close {',
    '  position: absolute; top: 4px; right: 8px; cursor: pointer;',
    '  color: rgba(255,255,255,0.7); background: none; border: none; font-size: 1rem;',
    '}'
  ].join('\n');

  function inyectarEstilos() {
    var style = document.createElement('style');
    style.textContent = ESTILOS;
    document.head.appendChild(style);
  }

  function pintarNotificacion(data) {
    var banner = document.getElementById('corpodg-notif-reservas');
    if (!banner) {
      banner = document.createElement('div');
      banner.id = 'corpodg-notif-reservas';
      document.body.appendChild(banner);
    }
    if (!data || !data.total) {
      banner.style.display = 'none';
      return;
    }
    var partes = [];
    if (data.reservas_vuelo) {
      partes.push('<a href="/admin/servicios/reservavuelo/?revisada__exact=0">' +
                  data.reservas_vuelo + ' de vuelo</a>');
    }
    if (data.reservas_paquete) {
      partes.push('<a href="/admin/servicios/reservapaquete/?revisada__exact=0">' +
                  data.reservas_paquete + ' de paquete</a>');
    }
    var campana =
      '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"' +
      ' style="width:14px;height:14px;fill:#ed8936;vertical-align:-2px;margin-right:4px;">' +
      '<path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2zm6-6v-5c0-3.1-1.6-5.6-4.5-6.3V4' +
      'c0-.8-.7-1.5-1.5-1.5S10.5 3.2 10.5 4v.7C7.6 5.4 6 7.9 6 11v5l-2 2v1h16v-1l-2-2z"/></svg>';
    banner.innerHTML =
      '<button type="button" class="notif-close" title="Ocultar">&times;</button>' +
      campana + '<strong>' + data.total + ' reserva(s) sin revisar</strong><br>' +
      'Pendientes: ' + partes.join(' y ') + '.';
    banner.style.display = 'block';
    banner.querySelector('.notif-close').onclick = function () {
      banner.style.display = 'none';
    };
  }

  function consultar() {
    fetch('/api/admin-notificaciones/', { credentials: 'same-origin' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(pintarNotificacion)
      .catch(function () {});
  }

  function iniciar() {
    inyectarEstilos();
    consultar();
    setInterval(consultar, 60000); // refrescar cada minuto
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciar);
  } else {
    iniciar();
  }
})();
