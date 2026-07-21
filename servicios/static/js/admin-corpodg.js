/* JS del panel admin CorpoDG (cargado por jazzmin custom_js en todas las páginas)
   - Dos notificaciones independientes que se refrescan cada minuto:
       1) Reservas sin revisar
       2) Solicitudes sin atender */
(function () {
  'use strict';

  var ESTILOS = [
    '#corpodg-notif-wrap {',
    '  position: fixed; top: 70px; right: 18px; z-index: 9999;',
    '  display: flex; flex-direction: column; gap: 10px; max-width: 320px;',
    '}',
    '.corpodg-notif-card {',
    '  display: none; position: relative; background: #1a365d; color: #fff;',
    '  border-left: 5px solid #ed8936; border-radius: 8px;',
    '  box-shadow: 0 4px 14px rgba(0,0,0,0.35); padding: 14px 16px;',
    '  font-size: 0.85rem;',
    '}',
    '.corpodg-notif-card strong { color: #ed8936; }',
    '.corpodg-notif-card a { color: #fff; text-decoration: underline; }',
    '.corpodg-notif-card .notif-close {',
    '  position: absolute; top: 4px; right: 8px; cursor: pointer;',
    '  color: rgba(255,255,255,0.7); background: none; border: none; font-size: 1rem;',
    '}'
  ].join('\n');

  var CAMPANA =
    '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"' +
    ' style="width:14px;height:14px;fill:#ed8936;vertical-align:-2px;margin-right:4px;">' +
    '<path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2zm6-6v-5c0-3.1-1.6-5.6-4.5-6.3V4' +
    'c0-.8-.7-1.5-1.5-1.5S10.5 3.2 10.5 4v.7C7.6 5.4 6 7.9 6 11v5l-2 2v1h16v-1l-2-2z"/></svg>';

  function inyectarEstilos() {
    var style = document.createElement('style');
    style.textContent = ESTILOS;
    document.head.appendChild(style);
  }

  function contenedor() {
    var wrap = document.getElementById('corpodg-notif-wrap');
    if (!wrap) {
      wrap = document.createElement('div');
      wrap.id = 'corpodg-notif-wrap';
      document.body.appendChild(wrap);
    }
    return wrap;
  }

  function tarjeta(id) {
    var card = document.getElementById(id);
    if (!card) {
      card = document.createElement('div');
      card.id = id;
      card.className = 'corpodg-notif-card';
      contenedor().appendChild(card);
    }
    return card;
  }

  function pintarTarjeta(id, mostrar, cuerpoHtml) {
    var card = tarjeta(id);
    if (!mostrar) {
      card.style.display = 'none';
      return;
    }
    card.innerHTML =
      '<button type="button" class="notif-close" title="Ocultar">&times;</button>' +
      CAMPANA + cuerpoHtml;
    card.style.display = 'block';
    card.querySelector('.notif-close').onclick = function () {
      card.style.display = 'none';
    };
  }

  function pintarNotificaciones(data) {
    data = data || {};

    // 1) Reservas sin revisar
    var reservas = (data.reservas_vuelo || 0) + (data.reservas_paquete || 0);
    var partes = [];
    if (data.reservas_vuelo) {
      partes.push('<a href="/admin/servicios/reservavuelo/?revisada__exact=0">' +
                  data.reservas_vuelo + ' de vuelo</a>');
    }
    if (data.reservas_paquete) {
      partes.push('<a href="/admin/servicios/reservapaquete/?revisada__exact=0">' +
                  data.reservas_paquete + ' de paquete</a>');
    }
    pintarTarjeta(
      'corpodg-notif-reservas',
      reservas > 0,
      '<strong>' + reservas + ' reserva(s) sin revisar</strong><br>' +
      'Pendientes: ' + partes.join(' y ') + '.'
    );

    // 2) Solicitudes sin atender (notificación independiente)
    var solicitudes = data.solicitudes || 0;
    pintarTarjeta(
      'corpodg-notif-solicitudes',
      solicitudes > 0,
      '<strong>' + solicitudes + ' solicitud(es) sin atender</strong><br>' +
      '<a href="/admin/servicios/solicitud/?atendido__exact=0">Ver solicitudes</a>.'
    );
  }

  function consultar() {
    fetch('/api/admin-notificaciones/', { credentials: 'same-origin' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(pintarNotificaciones)
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
