# 📚 Documentación de APIs - CorpoDG Backend

## 📋 Índice

1. [Información General](#información-general)
2. [Autenticación](#autenticación)
3. [Endpoints de Clientes](#endpoints-de-clientes)
4. [Endpoints de Solicitudes](#endpoints-de-solicitudes)
5. [Endpoint de Contacto](#endpoint-de-contacto)
6. [Endpoints de Destinos](#endpoints-de-destinos)
7. [Endpoints de Vuelos](#endpoints-de-vuelos)
8. [Endpoint de Búsqueda de Vuelos en Vivo (Sabre)](#endpoint-de-búsqueda-de-vuelos-en-vivo-sabre)
9. [Endpoint de Revalidación de Vuelo](#endpoint-de-revalidación-de-vuelo)
10. [Endpoint de Mapa de Asientos (SeatMap)](#endpoint-de-mapa-de-asientos-seatmap)
11. [Endpoints de Booking de Vuelos (Stripe)](#endpoints-de-booking-de-vuelos-stripe)
12. [Endpoints de Booking de Paquetes (Stripe)](#endpoints-de-booking-de-paquetes-stripe)
13. [Endpoint de Chatbot](#endpoint-de-chatbot)
14. [Endpoints de Regiones](#endpoints-de-regiones)
15. [Endpoints de Países](#endpoints-de-países)
16. [Endpoints de Ciudades](#endpoints-de-ciudades)
17. [Endpoints de Aerolíneas](#endpoints-de-aerolíneas)
18. [Endpoints de Aeropuertos](#endpoints-de-aeropuertos)
19. [Endpoints de Tipos de Paquete](#endpoints-de-tipos-de-paquete)
20. [Endpoints de Temporadas](#endpoints-de-temporadas)
21. [Endpoints de Paquetes Turísticos](#endpoints-de-paquetes-turísticos)
22. [Endpoints AJAX para Admin](#endpoints-ajax-para-admin)
23. [Endpoints de Utilidad (Health y Seed)](#endpoints-de-utilidad-health-y-seed)
24. [Modelos de Datos](#modelos-de-datos)
25. [Filtros Disponibles](#filtros-disponibles)
26. [Notas Adicionales](#notas-adicionales)
27. [Ejemplos de Uso](#ejemplos-de-uso)

---

## 📌 Información General

**URL Base:** `http://127.0.0.1:8000/api/`

**Formato de Respuesta:** JSON

**Framework:** Django REST Framework

**Rutas raíz:**
| Prefijo | Descripción |
|---------|-------------|
| `/admin/` | Panel de administración de Django |
| `/api/` | Todas las APIs REST |

**Rutas registradas en el router:**
| Ruta | ViewSet |
|------|--------|
| `/api/clientes/` | `ClienteViewSet` |
| `/api/solicitudes/` | `SolicitudViewSet` |
| `/api/destinos/` | `DestinoViewSet` |
| `/api/vuelos/` | `VueloViewSet` |
| `/api/regiones/` | `RegionViewSet` |
| `/api/paises-region/` | `PaisRegionViewSet` |
| `/api/ciudades/` | `CiudadViewSet` |
| `/api/aerolineas/` | `AerolineaViewSet` |
| `/api/aeropuertos/` | `AeropuertoViewSet` |
| `/api/paquetes/` | `PaqueteTuristicoViewSet` |
| `/api/tipos-paquete/` | `TipoPaqueteViewSet` |
| `/api/temporadas/` | `TemporadaViewSet` |

**Rutas individuales (fuera del router):**
| Ruta | Vista | Método(s) |
|------|-------|-----------|
| `/api/contacto/` | `contacto` | POST |
| `/api/buscar-vuelos-live/` | `BuscadorVuelosSabreView` | POST |
| `/api/revalidar-vuelo/` | `RevalidarVueloView` | POST |
| `/api/seatmap/` | `SeatMapView` | POST |
| `/api/booking/checkout/` | `BookingCheckoutView` | POST |
| `/api/booking/confirm/` | `BookingConfirmView` | POST |
| `/api/booking/webhook/` | `StripeWebhookView` | POST |
| `/api/booking/voucher/` | `BookingVoucherView` | GET / POST |
| `/api/paquetes/booking/checkout/` | `PaqueteCheckoutView` | POST |
| `/api/paquetes/booking/confirm/` | `PaqueteConfirmView` | POST |
| `/api/paquetes/booking/voucher/` | `PaqueteVoucherView` | GET / POST |
| `/api/chatbot/` | `ChatbotView` | POST |
| `/api/health/` | `health_check` | GET |
| `/api/seed/` | `seed_database` | GET |
| `/api/admin-ajax/...` | Funciones AJAX para admin | GET |

---

## 🔐 Autenticación

Actualmente, las APIs están configuradas sin autenticación para facilitar el acceso público. Para producción, se recomienda implementar autenticación mediante tokens o JWT.

---

## 👥 Endpoints de Clientes

> **ViewSet:** `ClienteViewSet` — CRUD completo

### 1. Listar todos los clientes

- **Método:** `GET`
- **Endpoint:** `/api/clientes/`
- **Descripción:** Obtiene una lista de todos los clientes registrados
- **Respuesta:**

```json
[
  {
    "id": 1,
    "nombre_completo": "Juan Pérez",
    "email": "juan@example.com",
    "telefono": "+593987654321",
    "fecha_registro": "2026-01-15T10:30:00Z",
    "solicitudes": [
      {
        "id": 1,
        "mensaje": "Me interesa un paquete al Caribe",
        "fecha_creacion": "2026-01-15T10:30:00Z",
        "atendido": false
      }
    ]
  }
]
```

### 2. Obtener un cliente específico

- **Método:** `GET`
- **Endpoint:** `/api/clientes/{id}/`
- **Descripción:** Obtiene los detalles de un cliente específico
- **Parámetros:** `id` (en la URL)

### 3. Crear un cliente

- **Método:** `POST`
- **Endpoint:** `/api/clientes/`
- **Descripción:** Crea un nuevo cliente
- **Body:**

```json
{
  "nombre_completo": "María García",
  "email": "maria@example.com",
  "telefono": "+593912345678"
}
```

### 4. Actualizar un cliente

- **Método:** `PUT` / `PATCH`
- **Endpoint:** `/api/clientes/{id}/`
- **Descripción:** Actualiza los datos de un cliente existente

### 5. Eliminar un cliente

- **Método:** `DELETE`
- **Endpoint:** `/api/clientes/{id}/`
- **Descripción:** Elimina un cliente del sistema

---

## 📝 Endpoints de Solicitudes

> **ViewSet:** `SolicitudViewSet` — CRUD completo

### 1. Listar todas las solicitudes

- **Método:** `GET`
- **Endpoint:** `/api/solicitudes/`
- **Descripción:** Obtiene una lista de todas las solicitudes (ordenadas por fecha descendente)
- **Respuesta:**

```json
[
  {
    "id": 1,
    "mensaje": "Necesito información sobre paquetes a Europa",
    "fecha_creacion": "2026-02-10T14:20:00Z",
    "atendido": false
  }
]
```

### 2. Obtener una solicitud específica

- **Método:** `GET`
- **Endpoint:** `/api/solicitudes/{id}/`
- **Descripción:** Obtiene los detalles de una solicitud específica

### 3. Crear una solicitud

- **Método:** `POST`
- **Endpoint:** `/api/solicitudes/`
- **Descripción:** Crea una nueva solicitud
- **Body:**

```json
{
  "cliente": 1,
  "mensaje": "Quiero reservar un paquete turístico"
}
```

### 4. Actualizar una solicitud

- **Método:** `PUT` / `PATCH`
- **Endpoint:** `/api/solicitudes/{id}/`
- **Descripción:** Actualiza una solicitud (por ejemplo, marcarla como atendida)

### 5. Eliminar una solicitud

- **Método:** `DELETE`
- **Endpoint:** `/api/solicitudes/{id}/`
- **Descripción:** Elimina una solicitud

---

## 💬 Endpoint de Contacto

### Enviar formulario de contacto

- **Método:** `POST`
- **Endpoint:** `/api/contacto/`
- **Descripción:** Endpoint principal para el formulario de contacto del sitio web. Si el cliente existe (por email), actualiza sus datos y crea la solicitud. Si no existe, crea el cliente y la solicitud. También envía notificaciones por email y WhatsApp.
- **Body:**

```json
{
  "nombre_completo": "Carlos Rodríguez",
  "email": "carlos@example.com",
  "telefono": "+593998765432",
  "mensaje": "Me gustaría recibir información sobre paquetes a Sudamérica"
}
```

- **Respuesta Exitosa (201 Created):**

```json
{
  "success": true,
  "message": "Solicitud recibida correctamente",
  "cliente": {
    "id": 5,
    "nombre_completo": "Carlos Rodríguez",
    "email": "carlos@example.com",
    "es_nuevo": true
  },
  "solicitud_id": 12
}
```

- **Respuesta de Error (400 Bad Request):**

```json
{
  "success": false,
  "errors": {
    "email": ["Este campo es requerido."]
  }
}
```

---

## 🏝️ Endpoints de Destinos

> **ViewSet:** `DestinoViewSet` — CRUD completo (solo muestra activos)

### 1. Listar todos los destinos

- **Método:** `GET`
- **Endpoint:** `/api/destinos/`
- **Descripción:** Obtiene una lista de todos los destinos turísticos activos
- **Query Parameters:**
  - `pais` (opcional): Filtrar por ID de país (`PaisRegion`)
  - `ciudad` (opcional): Filtrar por ID de ciudad
  - `destacado` (opcional): Filtrar destacados (`true` / `false`)
- **Ejemplo:** `/api/destinos/?pais=3&destacado=true`
- **Respuesta:**

```json
[
  {
    "id": 1,
    "nombre": "Cancún",
    "pais": 5,
    "pais_nombre": "México",
    "ciudad": 12,
    "ciudad_nombre": "Cancún",
    "descripcion": "Playas paradisíacas del Caribe mexicano",
    "imagen_url": "https://example.com/cancun.jpg",
    "precio_desde": "899.99",
    "destacado": true,
    "activo": true,
    "pdf_url": "https://drive.google.com/file/d/abc123/preview",
    "mensaje_reserva": "Me interesa el destino Cancún",
    "fecha_creacion": "2026-01-10T08:00:00Z",
    "fecha_actualizacion": "2026-02-05T10:30:00Z"
  }
]
```

### 2. Obtener un destino específico

- **Método:** `GET`
- **Endpoint:** `/api/destinos/{id}/`
- **Descripción:** Obtiene los detalles completos de un destino

### 3. Obtener destinos destacados (con orden personalizado)

- **Método:** `GET`
- **Endpoint:** `/api/destinos/destacados/`
- **Descripción:** Retorna destinos destacados respetando el orden configurado desde el admin. La cantidad máxima está controlada por `ConfiguracionDestacados.limite_destinos`.

### 4. Crear un destino

- **Método:** `POST`
- **Endpoint:** `/api/destinos/`

### 5. Actualizar un destino

- **Método:** `PUT` / `PATCH`
- **Endpoint:** `/api/destinos/{id}/`

### 6. Eliminar un destino

- **Método:** `DELETE`
- **Endpoint:** `/api/destinos/{id}/`

---

## ✈️ Endpoints de Vuelos

> **ViewSet:** `VueloViewSet` — CRUD completo (solo muestra disponibles)

### 1. Listar todos los vuelos

- **Método:** `GET`
- **Endpoint:** `/api/vuelos/`
- **Descripción:** Obtiene una lista de todos los vuelos disponibles
- **Query Parameters:**
  - `origen` (opcional): Busca en nombre del aeropuerto, ciudad o código IATA de origen
  - `destino` (opcional): Busca en nombre del aeropuerto, ciudad o código IATA de destino
- **Ejemplo:** `/api/vuelos/?origen=Quito&destino=MIA`
- **Respuesta:**

```json
[
  {
    "id": 1,
    "aerolinea": 1,
    "aerolinea_nombre": "LATAM Airlines",
    "aerolinea_logo": "https://example.com/latam-logo.png",
    "aerolinea_brandmark": "https://example.com/latam-brandmark.png",
    "aerolinea_iata": "LA",
    "origen": 5,
    "origen_nombre": "Aeropuerto Mariscal Sucre",
    "origen_pais": "Ecuador",
    "origen_ciudad": "Quito",
    "origen_codigo_iata": "UIO",
    "destino": 12,
    "destino_nombre": "Miami International Airport",
    "destino_pais": "Estados Unidos",
    "destino_ciudad": "Miami",
    "destino_codigo_iata": "MIA",
    "duracion": "4h 30m",
    "precio": "450.00",
    "imagen_url": "https://example.com/vuelo-imagen.jpg",
    "moneda": "USD",
    "destacado": true,
    "disponible": true,
    "mensaje_reserva": "Me interesa este vuelo",
    "fecha_creacion": "2026-01-20T12:00:00Z",
    "fecha_actualizacion": "2026-02-15T09:00:00Z"
  }
]
```

### 2. Obtener un vuelo específico

- **Método:** `GET`
- **Endpoint:** `/api/vuelos/{id}/`

### 3. Obtener vuelos destacados (con orden personalizado)

- **Método:** `GET`
- **Endpoint:** `/api/vuelos/destacados/`
- **Descripción:** Retorna vuelos destacados respetando el orden configurado desde el admin. La cantidad máxima está controlada por `ConfiguracionDestacados.limite_vuelos`.

### 4. Crear un vuelo

- **Método:** `POST`
- **Endpoint:** `/api/vuelos/`

### 5. Actualizar un vuelo

- **Método:** `PUT` / `PATCH`
- **Endpoint:** `/api/vuelos/{id}/`

### 6. Eliminar un vuelo

- **Método:** `DELETE`
- **Endpoint:** `/api/vuelos/{id}/`

---

## 🔎 Endpoint de Búsqueda de Vuelos en Vivo (Sabre)

### Buscar vuelos en tiempo real

- **Método:** `POST`
- **Endpoint:** `/api/buscar-vuelos-live/`
- **Descripción:** Busca vuelos en tiempo real utilizando la API de Sabre BFM (Bargain Finder Max). Soporta búsquedas de solo ida o ida y vuelta, con múltiples tipos de pasajeros y clases de cabina.
- **Body:**

```json
{
  "origin": "UIO",
  "destination": "MIA",
  "date": "2026-06-15",
  "return_date": "2026-06-22",
  "adults": 2,
  "children": 1,
  "infants": 0,
  "cabin_class": "Y",
  "limit": 20
}
```

| Campo         | Tipo       | Requerido | Descripción                                                                            |
| ------------- | ---------- | --------- | -------------------------------------------------------------------------------------- |
| `origin`      | String (3) | ✅        | Código IATA del aeropuerto de origen                                                   |
| `destination` | String (3) | ✅        | Código IATA del aeropuerto de destino                                                  |
| `date`        | String     | ✅        | Fecha de ida (formato `YYYY-MM-DD`)                                                    |
| `return_date` | String     | ❌        | Fecha de vuelta (formato `YYYY-MM-DD`). Si se omite, se busca solo ida                 |
| `adults`      | Integer    | ❌        | Número de adultos (default: 0)                                                         |
| `children`    | Integer    | ❌        | Número de niños (default: 0)                                                           |
| `infants`     | Integer    | ❌        | Número de infantes (default: 0)                                                        |
| `cabin_class` | String     | ❌        | Clase de cabina: `Y` (Económica), `S` (Premium Economy), `C` (Business), `F` (Primera) |
| `limit`       | Integer    | ❌        | Máximo de resultados (default: 20, máximo: 200)                                        |

- **Respuesta Exitosa (200 OK):**

```json
[
  {
    "id": 1,
    "proveedor": "sabre",
    "id_itinerario_proveedor": "1",
    "id_itinerario_unico": "sabre:1",
    "precio_total": 685.5,
    "precio_base": 520.0,
    "impuestos": 165.5,
    "moneda": "USD",
    "aerolinea_validadora": "LA",
    "ultima_fecha_compra": "2026-06-10",
    "tramos": [
      {
        "tipo": "ida",
        "origen": {
          "aeropuerto": "UIO",
          "ciudad": "QUI",
          "pais": "EC",
          "hora": "08:30"
        },
        "destino": {
          "aeropuerto": "MIA",
          "ciudad": "MIA",
          "pais": "US",
          "hora": "14:45"
        },
        "duracion_total": "6h 15m",
        "duracion_minutos": 375,
        "tiene_escalas": false,
        "numero_escalas": 0,
        "segmentos": [
          {
            "numero_segmento": 1,
            "vuelo": "LA1442",
            "aerolinea": {
              "codigo": "LA",
              "operada_por": "LA",
              "nombre_compartido": "",
              "alianza": "oneworld"
            },
            "salida": {
              "aeropuerto": "UIO",
              "ciudad": "QUI",
              "pais": "EC",
              "hora": "08:30",
              "terminal": null
            },
            "llegada": {
              "aeropuerto": "MIA",
              "ciudad": "MIA",
              "pais": "US",
              "hora": "14:45",
              "terminal": "N",
              "dia_siguiente": false
            },
            "duracion": "6h 15m",
            "duracion_minutos": 375,
            "millas": 1755,
            "avion": "789",
            "paradas_intermedias": 0
          }
        ]
      },
      {
        "tipo": "vuelta",
        "origen": {
          "aeropuerto": "MIA",
          "ciudad": "MIA",
          "pais": "US",
          "hora": "18:00"
        },
        "destino": {
          "aeropuerto": "UIO",
          "ciudad": "QUI",
          "pais": "EC",
          "hora": "22:30"
        },
        "duracion_total": "4h 30m",
        "duracion_minutos": 270,
        "tiene_escalas": false,
        "numero_escalas": 0,
        "segmentos": ["..."]
      }
    ],
    "resumen": {
      "aerolineas_ida": ["LA"],
      "aerolineas_vuelta": ["LA"],
      "es_vuelo_directo_ida": true,
      "es_vuelo_directo_vuelta": true
    }
  }
]
```

**Cuando hay escalas**, cada tramo incluye adicionalmente:

```json
{
  "escalas": [
    {
      "aeropuerto": "BOG",
      "ciudad": "BOG",
      "pais": "CO",
      "hora_llegada": "10:15",
      "hora_salida": "12:30"
    }
  ]
}
```

- **Respuesta de Error - Datos faltantes (400):**

```json
{
  "error": "Faltan datos obligatorios (origin, destination, date)"
}
```

- **Respuesta de Error - Sabre (código variable):**

```json
{
  "error": "Error en Sabre",
  "code": 500,
  "detail": { "...": "..." }
}
```

> **Nota:** Los resultados se ordenan automáticamente por: menor escalas → menor duración → menor precio.

---

## ✅ Endpoint de Revalidación de Vuelo

### Confirmar disponibilidad de un itinerario

- **Método:** `POST`
- **Endpoint:** `/api/revalidar-vuelo/`
- **Descripción:** Confirma si un itinerario obtenido en la búsqueda sigue disponible para reservar (Sabre Revalidate). Acepta un objeto con `tramos` construido manualmente, o directamente el objeto `opcion` devuelto por `/api/buscar-vuelos-live/`.
- **Body:**

```json
{
  "adults": 1,
  "children": 0,
  "infants": 0,
  "tramos": [
    {
      "fecha_salida": "2026-05-31",
      "segmentos": [
        {
          "numero_vuelo": 833,
          "clase_servicio": "V",
          "origen": "EWR",
          "destino": "MIA",
          "fecha_hora_salida": "2026-05-31T12:20:00",
          "fecha_hora_llegada": "2026-05-31T15:26:00",
          "aerolinea_marketing": "AA",
          "aerolinea_operadora": "AA"
        }
      ]
    }
  ]
}
```

- **Respuesta Exitosa (200 OK):**

```json
{
  "disponible": true,
  "mensaje": "El vuelo sigue disponible",
  "precio_total": 685.5,
  "precio_base": 520.0,
  "impuestos": 165.5,
  "moneda": "USD",
  "ultima_fecha_compra": "2026-05-30",
  "ultima_hora_compra": "23:59",
  "aerolinea_validadora": "AA"
}
```

- **Respuesta - Vuelo no disponible (409 Conflict):**

```json
{
  "disponible": false,
  "error": "El vuelo ya no esta disponible para reserva"
}
```

- **Respuesta - Faltan tramos (400):**

```json
{
  "disponible": false,
  "error": "Faltan los tramos del itinerario"
}
```

---

## 💺 Endpoint de Mapa de Asientos (SeatMap)

### Obtener mapa de asientos de un itinerario

- **Método:** `POST`
- **Endpoint:** `/api/seatmap/`
- **Descripción:** Devuelve el mapa de asientos de un itinerario vía Sabre Get Seats v3. En modo sandbox (`SEATMAP_SANDBOX`) genera una respuesta simulada con la misma estructura.
- **Body:**

```json
{
  "opcion": { "...": "la opción completa devuelta por /api/buscar-vuelos-live/" },
  "pasajeros": [
    { "passengerType": "ADT", "givenName": "JUAN", "surname": "PEREZ" }
  ],
  "moneda": "USD"
}
```

| Campo       | Tipo   | Requerido | Descripción                                               |
| ----------- | ------ | --------- | --------------------------------------------------------- |
| `opcion`    | Object | ✅        | La opción completa (con `tramos`) devuelta por la búsqueda |
| `pasajeros` | Array  | ❌        | Lista de pasajeros (default: 1 adulto de prueba)          |
| `moneda`    | String | ❌        | Moneda para precios de asientos (default: USD)            |

- **Respuesta Exitosa (200 OK):**

```json
{
  "offer_id": "OFFER-...",
  "expira": "2026-06-15T12:00:00Z",
  "mapas": [
    {
      "...": "mapa de asientos por segmento (filas, columnas, asientos, precios)"
    }
  ],
  "warnings": [],
  "sandbox": true
}
```

- **Errores posibles:**

| Código | Descripción                                                    |
| ------ | -------------------------------------------------------------- |
| 400    | Falta `opcion` con sus `tramos` o datos incompletos            |
| 404    | La aerolínea no expone mapa de asientos para este vuelo        |
| 422    | Sabre no pudo generar el mapa (errores críticos)               |
| 500    | Error de conexión / autenticación con Sabre                    |

---

## 💳 Endpoints de Booking de Vuelos (Stripe)

Flujo de reserva: **checkout** (crea sesión de pago Stripe) → el usuario paga → **confirm** (verifica el pago y crea la reserva) → **voucher** (documento imprimible/PDF). El modo sandbox se controla con `BOOKING_SANDBOX` (simula Sabre createBooking).

### 1. Crear sesión de pago (Checkout)

- **Método:** `POST`
- **Endpoint:** `/api/booking/checkout/`
- **Descripción:** Crea una sesión de Stripe Checkout y guarda el intento de reserva en cache (24h)
- **Body:**

```json
{
  "opcion": { "...": "opción del buscador de vuelos" },
  "pasajeros": [
    { "givenName": "JUAN", "surname": "PEREZ", "passengerType": "ADT" }
  ],
  "contacto": { "email": "juan@example.com", "phone": "+593987654321" },
  "asientos_seleccionados": [
    {
      "segmento_indice": 1,
      "pasajero_id": 0,
      "asiento_id": "17F",
      "offer_item_id": "OITEM-...",
      "monto": 8.0
    }
  ],
  "moneda": "USD",
  "success_url": "https://mi-frontend.com/reserva/confirmada",
  "cancel_url": "https://mi-frontend.com/reserva/cancelada"
}
```

| Campo                    | Tipo   | Requerido | Descripción                                  |
| ------------------------ | ------ | --------- | -------------------------------------------- |
| `opcion`                 | Object | ✅        | Opción con `tramos` devuelta por la búsqueda |
| `pasajeros`              | Array  | ✅        | Lista de pasajeros                           |
| `contacto.email`         | String | ✅        | Email de contacto                            |
| `asientos_seleccionados` | Array  | ❌        | Asientos elegidos en el seatmap (con costo)  |
| `moneda`                 | String | ❌        | Default: USD                                 |
| `success_url` / `cancel_url` | String | ❌    | URLs de retorno de Stripe                    |

- **Respuesta Exitosa (200 OK):**

```json
{
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_...",
  "session_id": "cs_test_...",
  "booking_ref": "A1B2C3D4E5F6",
  "monto": 693.5,
  "moneda": "USD",
  "expira": "2026-07-19T15:00:00Z"
}
```

### 2. Confirmar reserva (post-pago)

- **Método:** `POST`
- **Endpoint:** `/api/booking/confirm/`
- **Descripción:** Verifica en Stripe que el pago fue exitoso y crea la reserva (Sabre createBooking o simulación en sandbox). Devuelve la reserva tipo `createBookingResponse` con `confirmationId` (PNR), pasajeros, itinerario y `resumen`. También envía el voucher por email en segundo plano. La reserva queda en cache 7 días (por `session_id` y por PNR).
- **Body:**

```json
{ "session_id": "cs_test_..." }
```

- **Errores posibles:**

| Código | Descripción                                                |
| ------ | ---------------------------------------------------------- |
| 400    | Falta `session_id`                                         |
| 402    | El pago aún no está completado (incluye `payment_status`)  |
| 404    | No se encontró el intento de reserva (expiró la cache)     |
| 502    | No se pudo verificar la sesión con Stripe                  |

### 3. Webhook de Stripe

- **Método:** `POST`
- **Endpoint:** `/api/booking/webhook/`
- **Descripción:** Endpoint opcional para recibir eventos de Stripe (ej: `checkout.session.completed`). Valida la firma si `STRIPE_WEBHOOK_SECRET` está configurado.
- **Respuesta:** `{ "received": true, "type": "checkout.session.completed" }`

### 4. Voucher / Boletos (HTML o PDF)

- **Método:** `GET` / `POST`
- **Endpoint:** `/api/booking/voucher/`
- **Descripción:** Genera el documento imprimible (HTML) o descargable (PDF) de una reserva confirmada.
- **Uso GET (reserva en cache):**
  - `/api/booking/voucher/?session_id=cs_test_...&format=pdf`
  - `/api/booking/voucher/?pnr=ABCDEF&format=html&doc=boletos`
- **Uso POST (si la cache expiró, se reenvía la reserva):**

```json
{ "reserva": { "...": "createBookingResponse" }, "format": "pdf", "doc": "voucher" }
```

| Parámetro    | Valores                | Descripción                                             |
| ------------ | ---------------------- | ------------------------------------------------------- |
| `session_id` / `pnr` | String         | Clave para recuperar la reserva (requerido en GET)      |
| `format`     | `html` (default) / `pdf` | HTML listo para imprimir o archivo PDF                |
| `doc`        | `voucher` (default) / `boletos` | Comprobante CorpoDG o boletos estilo aerolínea |

- **Errores:** `400` falta clave o reserva, `404` reserva no encontrada/expirada, `500` no se pudo generar el PDF.

---

## 🧳 Endpoints de Booking de Paquetes (Stripe)

Mismo flujo que el booking de vuelos, pero para paquetes turísticos: **checkout** → pago → **confirm** → **voucher**.

### 1. Crear sesión de pago (Checkout)

- **Método:** `POST`
- **Endpoint:** `/api/paquetes/booking/checkout/`
- **Body:**

```json
{
  "paquete_id": 12,
  "n_personas": 2,
  "contacto": { "email": "juan@example.com", "phone": "+593987654321" },
  "viajeros": [
    { "nombre": "Milton", "apellido": "Davila", "documento": "0912345678" }
  ],
  "fecha_viaje": "2026-08-15",
  "moneda": "USD",
  "success_url": "https://mi-frontend.com/reserva/confirmada",
  "cancel_url": "https://mi-frontend.com/reserva/cancelada"
}
```

| Campo            | Tipo    | Requerido | Descripción                                    |
| ---------------- | ------- | --------- | ---------------------------------------------- |
| `paquete_id`     | Integer | ✅        | ID del paquete turístico (debe estar activo)   |
| `n_personas`     | Integer | ✅        | Número de personas (>= 1)                      |
| `contacto.email` | String  | ✅        | Email de contacto                              |
| `viajeros`       | Array   | ❌        | Nombres de los viajeros                        |
| `fecha_viaje`    | String  | ❌        | Fecha tentativa del viaje (`YYYY-MM-DD`)       |
| `moneda`         | String  | ❌        | Default: moneda del paquete (USD)              |
| `success_url` / `cancel_url` | String | ❌ | URLs de retorno de Stripe                    |

- **Respuesta Exitosa (200 OK):**

```json
{
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_...",
  "session_id": "cs_test_...",
  "paquete_id": 12,
  "monto": 2599.98,
  "moneda": "USD",
  "n_personas": 2,
  "expira": "2026-07-19T15:00:00Z"
}
```

- **Errores:** `400` datos faltantes o monto inválido, `404` paquete no encontrado o inactivo, `502` error de Stripe.

### 2. Confirmar reserva (post-pago)

- **Método:** `POST`
- **Endpoint:** `/api/paquetes/booking/confirm/`
- **Body:** `{ "session_id": "cs_test_..." }`
- **Descripción:** Verifica el pago en Stripe y devuelve la reserva normalizada del paquete. Envía el voucher por email en segundo plano.
- **Respuesta Exitosa (200 OK):**

```json
{
  "tipo": "paquete",
  "localizador": "CDGPK-X7K2M9",
  "estado": "CONFIRMADA",
  "emitida": true,
  "fecha_creacion": "2026-07-18T15:30:00Z",
  "paquete": { "...": "snapshot del paquete (titulo, destino, precio, etc.)" },
  "viajeros": [{ "...": "..." }],
  "n_personas": 2,
  "fecha_viaje": "2026-08-15",
  "contacto": { "email": "juan@example.com", "phone": "+593987654321" },
  "pago": { "proveedor": "stripe", "...": "datos del pago" },
  "sandbox": true
}
```

- **Errores:** `400` falta `session_id`, `402` pago no completado, `404` intento expirado, `502` error de Stripe.

### 3. Voucher del paquete (HTML o PDF)

- **Método:** `GET` / `POST`
- **Endpoint:** `/api/paquetes/booking/voucher/`
- **Uso GET:**
  - `/api/paquetes/booking/voucher/?session_id=cs_test_...&format=pdf`
  - `/api/paquetes/booking/voucher/?loc=CDGPK-XXXXXX&format=html`
- **Uso POST (si la cache expiró):**

```json
{ "reserva": { "...": "reserva con 'paquete'" }, "format": "pdf" }
```

| Parámetro                 | Valores                  | Descripción                                        |
| ------------------------- | ------------------------ | -------------------------------------------------- |
| `session_id` / `loc` / `localizador` | String        | Clave para recuperar la reserva (requerido en GET) |
| `format`                  | `html` (default) / `pdf` | HTML listo para imprimir o archivo PDF             |

- **Errores:** `400` falta clave o reserva, `404` reserva no encontrada/expirada, `500` no se pudo generar el PDF.

---

## 🤖 Endpoint de Chatbot

### Conversar con el asistente

- **Método:** `POST`
- **Endpoint:** `/api/chatbot/`
- **Descripción:** Chatbot de CorpoDG (impulsado por Groq con tools internas). Puede consultar paquetes, destinos, vuelos y aerolíneas del catálogo, buscar vuelos en vivo, y sugerir redirecciones al frontend. Recibe el mensaje del usuario y el historial previo, y retorna la respuesta más el historial actualizado (máximo 20 mensajes de contexto).
- **Body:**

```json
{
  "mensaje": "¿Qué paquetes tienen al Caribe?",
  "historial": [
    { "role": "user", "content": "Hola" },
    { "role": "assistant", "content": "¡Hola! ¿En qué puedo ayudarte?" }
  ]
}
```

| Campo       | Tipo   | Requerido | Descripción                                            |
| ----------- | ------ | --------- | ------------------------------------------------------ |
| `mensaje`   | String | ✅        | Mensaje del usuario (no puede estar vacío)             |
| `historial` | Array  | ❌        | Mensajes previos `[{role, content}, ...]`              |

- **Respuesta Exitosa (200 OK):**

```json
{
  "respuesta": "Tenemos estos paquetes al Caribe: ...",
  "historial": [
    { "role": "user", "content": "Hola" },
    { "role": "assistant", "content": "¡Hola! ¿En qué puedo ayudarte?" },
    { "role": "user", "content": "¿Qué paquetes tienen al Caribe?" },
    { "role": "assistant", "content": "Tenemos estos paquetes al Caribe: ..." }
  ],
  "accion": {
    "tipo": "redirect_paquete",
    "label": "Ver detalles y reservar",
    "path": "/paquetes/12",
    "params": {}
  }
}
```

> El campo `accion` puede ser `null`, o un objeto de redirección (`redirect_paquete`, `redirect_vuelos`) que el frontend puede usar para mostrar un botón de acción. El historial devuelto se reenvía tal cual en el siguiente request.

- **Errores:** `400` mensaje vacío, `500` error procesando el mensaje.

---

## 🌍 Endpoints de Regiones

> **ViewSet:** `RegionViewSet` — Solo lectura (`GET`)

### 1. Listar todas las regiones

- **Método:** `GET`
- **Endpoint:** `/api/regiones/`
- **Descripción:** Obtiene un listado simplificado de todas las regiones activas (con conteos)
- **Respuesta:**

```json
[
  {
    "id": 1,
    "nombre": "caribe",
    "nombre_display": "Caribe",
    "imagen_url": "https://example.com/caribe.jpg",
    "activo": true,
    "orden": 1,
    "cantidad_paises": 5,
    "cantidad_paquetes": 15
  }
]
```

### 2. Obtener una región específica (detalle con países y ciudades)

- **Método:** `GET`
- **Endpoint:** `/api/regiones/{id}/`
- **Descripción:** Obtiene el detalle completo de una región incluyendo todos sus países y ciudades anidados
- **Respuesta:**

```json
{
  "id": 1,
  "nombre": "caribe",
  "nombre_display": "Caribe",
  "descripcion": "Destinos paradisíacos del Caribe",
  "imagen_url": "https://example.com/caribe.jpg",
  "activo": true,
  "orden": 1,
  "paises": [
    {
      "id": 1,
      "nombre": "México",
      "nombre_en": "Mexico",
      "codigo_iso": "MX",
      "codigo_iso3": "MEX",
      "capital": "Ciudad de México",
      "bandera_png": "https://flagcdn.com/w320/mx.png",
      "bandera_svg": "https://flagcdn.com/mx.svg",
      "bandera_url": "https://flagcdn.com/mx.svg",
      "region": 1,
      "region_nombre": "Caribe",
      "ciudades": [
        {
          "id": 1,
          "nombre": "Cancún",
          "codigo_ciudad": "CUN",
          "codigo_aeropuerto": "CUN",
          "latitud": 21.1619,
          "longitud": -86.8515,
          "es_capital": false,
          "imagen_url": "https://example.com/cancun.jpg",
          "pais": 1,
          "pais_nombre": "México",
          "region_nombre": "Caribe",
          "ubicacion_completa": "Cancún, México (Caribe)",
          "activo": true
        }
      ],
      "cantidad_ciudades": 3,
      "activo": true
    }
  ],
  "cantidad_paquetes": 15
}
```

### 3. Obtener países de una región

- **Método:** `GET`
- **Endpoint:** `/api/regiones/{id}/paises/`
- **Descripción:** Retorna solo los países activos de una región específica (formato listado simplificado)

### 4. Obtener paquetes de una región

- **Método:** `GET`
- **Endpoint:** `/api/regiones/{id}/paquetes/`
- **Descripción:** Retorna los paquetes turísticos activos de una región

---

## 🌎 Endpoints de Países

> **ViewSet:** `PaisRegionViewSet` — Solo lectura (`GET`)

### 1. Listar todos los países

- **Método:** `GET`
- **Endpoint:** `/api/paises-region/`
- **Descripción:** Obtiene una lista simplificada de todos los países activos
- **Query Parameters:**
  - `region` (opcional): Filtrar países por ID de región
- **Ejemplo:** `/api/paises-region/?region=1`
- **Respuesta (listado):**

```json
[
  {
    "id": 1,
    "nombre": "México",
    "nombre_en": "Mexico",
    "codigo_iso": "MX",
    "capital": "Ciudad de México",
    "bandera_url": "https://flagcdn.com/mx.svg",
    "region": 1,
    "region_nombre": "Caribe",
    "cantidad_ciudades": 3,
    "activo": true
  }
]
```

### 2. Obtener un país específico (con ciudades)

- **Método:** `GET`
- **Endpoint:** `/api/paises-region/{id}/`
- **Descripción:** Obtiene los detalles de un país incluyendo todas sus ciudades
- **Respuesta (detalle):**

```json
{
  "id": 1,
  "nombre": "México",
  "nombre_en": "Mexico",
  "codigo_iso": "MX",
  "codigo_iso3": "MEX",
  "capital": "Ciudad de México",
  "bandera_png": "https://flagcdn.com/w320/mx.png",
  "bandera_svg": "https://flagcdn.com/mx.svg",
  "bandera_url": "https://flagcdn.com/mx.svg",
  "region": 1,
  "region_nombre": "Caribe",
  "ciudades": [
    {
      "id": 1,
      "nombre": "Cancún",
      "codigo_ciudad": "CUN",
      "codigo_aeropuerto": "CUN",
      "latitud": 21.1619,
      "longitud": -86.8515,
      "es_capital": false,
      "imagen_url": null,
      "pais": 1,
      "pais_nombre": "México",
      "region_nombre": "Caribe",
      "ubicacion_completa": "Cancún, México (Caribe)",
      "activo": true
    }
  ],
  "cantidad_ciudades": 3,
  "activo": true
}
```

### 3. Obtener ciudades de un país

- **Método:** `GET`
- **Endpoint:** `/api/paises-region/{id}/ciudades/`
- **Descripción:** Retorna solo las ciudades activas de un país

### 4. Obtener paquetes de un país

- **Método:** `GET`
- **Endpoint:** `/api/paises-region/{id}/paquetes/`
- **Descripción:** Retorna los paquetes turísticos activos de un país

---

## 🏙️ Endpoints de Ciudades

> **ViewSet:** `CiudadViewSet` — Solo lectura (`GET`)

### 1. Listar todas las ciudades

- **Método:** `GET`
- **Endpoint:** `/api/ciudades/`
- **Descripción:** Obtiene una lista de todas las ciudades activas
- **Query Parameters:**
  - `pais` (opcional): Filtrar ciudades por ID de país
  - `region` (opcional): Filtrar ciudades por ID de región
  - `capital` (opcional): Filtrar solo capitales (valor: `true`)
- **Ejemplo:** `/api/ciudades/?pais=1&capital=true`
- **Respuesta:**

```json
[
  {
    "id": 5,
    "nombre": "Quito",
    "codigo_ciudad": "UIO",
    "codigo_aeropuerto": "UIO",
    "latitud": -0.1807,
    "longitud": -78.4678,
    "es_capital": true,
    "imagen_url": "https://example.com/quito.jpg",
    "pais": 3,
    "pais_nombre": "Ecuador",
    "region_nombre": "Ecuador",
    "ubicacion_completa": "Quito, Ecuador (Ecuador)",
    "activo": true
  }
]
```

### 2. Obtener una ciudad específica

- **Método:** `GET`
- **Endpoint:** `/api/ciudades/{id}/`

---

## 🛫 Endpoints de Aerolíneas

> **ViewSet:** `AerolineaViewSet` — Solo lectura (`GET`)

### 1. Listar todas las aerolíneas

- **Método:** `GET`
- **Endpoint:** `/api/aerolineas/`
- **Descripción:** Obtiene una lista de todas las aerolíneas activas
- **Query Parameters:**
  - `pais` (opcional): Filtrar por país de origen (búsqueda parcial)
  - `search` (opcional): Buscar por nombre, código IATA o código ICAO
- **Ejemplo:** `/api/aerolineas/?search=LATAM`
- **Respuesta:**

```json
[
  {
    "id": 1,
    "nombre": "LATAM Airlines",
    "codigo_iata": "LA",
    "codigo_icao": "LAN",
    "pais_origen": "Chile",
    "anio_creacion": "2012",
    "base_aeropuerto": "Aeropuerto Arturo Merino Benítez",
    "logo_url": "https://example.com/latam-logo.png",
    "brandmark_url": "https://example.com/latam-brandmark.png",
    "sitio_web": "https://www.latamairlines.com",
    "activo": true,
    "cantidad_vuelos": 12
  }
]
```

### 2. Obtener una aerolínea específica

- **Método:** `GET`
- **Endpoint:** `/api/aerolineas/{id}/`

### 3. Obtener vuelos de una aerolínea

- **Método:** `GET`
- **Endpoint:** `/api/aerolineas/{id}/vuelos/`
- **Descripción:** Retorna todos los vuelos disponibles de una aerolínea específica

### 4. Buscar aerolínea por código IATA

- **Método:** `GET`
- **Endpoint:** `/api/aerolineas/buscar_iata/?codigo={CODIGO}`
- **Descripción:** Busca una aerolínea por código IATA exacto (case-insensitive, se convierte a mayúsculas)
- **Ejemplo:** `/api/aerolineas/buscar_iata/?codigo=AV`
- **Respuesta exitosa:**

```json
{
  "id": 5,
  "nombre": "Avianca",
  "codigo_iata": "AV",
  "codigo_icao": "AVA",
  "pais_origen": "Colombia",
  "anio_creacion": "1919",
  "base_aeropuerto": "Aeropuerto El Dorado",
  "logo_url": "https://example.com/avianca-logo.png",
  "brandmark_url": "https://example.com/avianca-brandmark.png",
  "sitio_web": "https://www.avianca.com",
  "activo": true,
  "cantidad_vuelos": 8
}
```

- **Error (sin parámetro):**

```json
{ "error": "Parámetro \"codigo\" requerido" }
```

- **Error (no encontrada):**

```json
{ "error": "Aerolínea con código IATA \"XX\" no encontrada" }
```

---

## 🛬 Endpoints de Aeropuertos

> **ViewSet:** `AeropuertoViewSet` — Solo lectura (`GET`)

### 1. Listar todos los aeropuertos

- **Método:** `GET`
- **Endpoint:** `/api/aeropuertos/`
- **Descripción:** Obtiene una lista simplificada de todos los aeropuertos activos
- **Query Parameters:**
  - `pais` (opcional): Filtrar por ID de país
  - `region` (opcional): Filtrar por estado/provincia (texto exacto, case-insensitive)
  - `ciudad` (opcional): Filtrar por ID de ciudad
  - `search` (opcional): Buscar por nombre, código IATA, código ICAO o nombre de ciudad
- **Ejemplo:** `/api/aeropuertos/?pais=3&search=guayaquil`
- **Respuesta (listado simplificado):**

```json
[
  {
    "id": 1,
    "codigo_iata": "GYE",
    "codigo_icao": "SEGU",
    "nombre": "Aeropuerto José Joaquín de Olmedo",
    "ciudad_nombre": "Guayaquil",
    "pais_nombre": "Ecuador"
  }
]
```

### 2. Obtener un aeropuerto específico (detalle completo)

- **Método:** `GET`
- **Endpoint:** `/api/aeropuertos/{id}/`
- **Respuesta:**

```json
{
  "id": 1,
  "codigo_iata": "GYE",
  "codigo_icao": "SEGU",
  "nombre": "Aeropuerto José Joaquín de Olmedo",
  "ciudad": 5,
  "ciudad_nombre": "Guayaquil",
  "pais": 3,
  "pais_nombre": "Ecuador",
  "pais_codigo": "EC",
  "nombre_ciudad": "Guayaquil",
  "region": "Guayas",
  "region_nombre": "Ecuador",
  "latitud": -2.1574,
  "longitud": -79.8837,
  "elevacion_ft": 15,
  "zona_horaria": "America/Guayaquil",
  "ubicacion_completa": "Guayaquil, Ecuador",
  "activo": true
}
```

### 3. Autocompletado de aeropuertos

- **Método:** `GET`
- **Endpoint:** `/api/aeropuertos/autocomplete/?q={query}`
- **Descripción:** Endpoint optimizado para autocompletado. Busca en código IATA, ICAO, nombre, ciudad y país. Devuelve máximo 10 resultados. Requiere mínimo 2 caracteres.
- **Ejemplo:** `/api/aeropuertos/autocomplete/?q=bogota`
- **Respuesta:**

```json
{
  "results": [
    {
      "id": 10,
      "codigo_iata": "BOG",
      "nombre": "Aeropuerto Internacional El Dorado",
      "ciudad": "Bogotá",
      "pais": "Colombia",
      "label": "BOG - Aeropuerto Internacional El Dorado, Bogotá, Colombia"
    }
  ],
  "count": 1
}
```

- **Respuesta con menos de 2 caracteres:**

```json
{
  "results": [],
  "message": "Ingresa al menos 2 caracteres para buscar"
}
```

---

## 📦 Endpoints de Tipos de Paquete

> **ViewSet:** `TipoPaqueteViewSet` — Solo lectura (`GET`)

### 1. Listar todos los tipos de paquete

- **Método:** `GET`
- **Endpoint:** `/api/tipos-paquete/`
- **Descripción:** Obtiene una lista de todos los tipos de paquete activos
- **Respuesta:**

```json
[
  {
    "id": 1,
    "nombre": "Todo Incluido"
  },
  {
    "id": 2,
    "nombre": "Vacaciones"
  },
  {
    "id": 3,
    "nombre": "Aventura"
  }
]
```

### 2. Obtener un tipo de paquete específico

- **Método:** `GET`
- **Endpoint:** `/api/tipos-paquete/{id}/`
- **Descripción:** Obtiene los detalles de un tipo de paquete específico
- **Respuesta:**

```json
{
  "id": 1,
  "nombre": "Todo Incluido"
}
```

---

## 🗓️ Endpoints de Temporadas

> **ViewSet:** `TemporadaViewSet` — Solo lectura (`GET`)

### 1. Listar todas las temporadas

- **Método:** `GET`
- **Endpoint:** `/api/temporadas/`
- **Descripción:** Obtiene una lista de todas las temporadas activas
- **Respuesta:**

```json
[
  {
    "id": 1,
    "nombre": "Temporada Alta"
  },
  {
    "id": 2,
    "nombre": "Temporada Baja"
  }
]
```

### 2. Obtener una temporada específica

- **Método:** `GET`
- **Endpoint:** `/api/temporadas/{id}/`
- **Descripción:** Obtiene los detalles de una temporada específica
- **Respuesta:**

```json
{
  "id": 1,
  "nombre": "Temporada Alta"
}
```

---

## 🎁 Endpoints de Paquetes Turísticos

> **ViewSet:** `PaqueteTuristicoViewSet` — Solo lectura (`GET`)

### 1. Listar todos los paquetes

- **Método:** `GET`
- **Endpoint:** `/api/paquetes/`
- **Descripción:** Obtiene una lista de todos los paquetes turísticos activos
- **Query Parameters:**
  - `region` (opcional): Filtrar por ID de región
  - `pais` (opcional): Filtrar por ID de país destino
  - `tipo` (opcional): Filtrar por nombre de tipo de paquete (ej: `Vacaciones`, `Todo Incluido`)
  - `temporada` (opcional): Filtrar por nombre de temporada (ej: `Alta`, `Baja`)
  - `precio_max` (opcional): Filtrar por precio máximo
  - `destacados` (opcional): Filtrar solo destacados (valor: `true`)
  - `aerolinea` (opcional): Filtrar por ID de aerolínea
- **Ejemplo:** `/api/paquetes/?region=1&destacados=true&precio_max=2000`
- **Respuesta:**

```json
[
  {
    "id": 1,
    "titulo": "Paquete Todo Incluido Cancún",
    "subtitulo": "Enero a Diciembre",
    "imagen_url": "https://example.com/paquete-cancun.jpg",
    "descripcion_corta": "Disfruta del paraíso caribeño con todo incluido",
    "region": 1,
    "region_nombre": "Caribe",
    "pais_destino": 1,
    "pais_nombre": "México",
    "pais_bandera": "https://flagcdn.com/mx.svg",
    "ciudad_destino": 1,
    "ciudad_nombre": "Cancún",
    "precio": "1299.99",
    "moneda": "USD",
    "tipo_paquete": 1,
    "tipo_paquete_display": "Todo Incluido",
    "duracion_dias": 6,
    "duracion_noches": 5,
    "salidas": "Quito y Guayaquil",
    "fecha_salidas_texto": "2026 Enero a Diciembre",
    "aerolinea": 1,
    "aerolinea_nombre": "LATAM Airlines",
    "aerolinea_logo": "https://example.com/latam-logo.png",
    "aerolinea_brandmark": "https://example.com/latam-brandmark.png",
    "aerolinea_iata": "LA",
    "temporada": 1,
    "temporada_display": "Temporada Alta",
    "tipo_viaje": 1,
    "tipo_viaje_display": "Familiar",
    "paquete_incluye": {
      "vuelo": true,
      "hotel": true,
      "alimentacion": true,
      "traslados": true,
      "tours": false,
      "seguro": true
    },
    "lugares_destacados_lista": [
      "Zona Hotelera",
      "Playa Delfines",
      "Mercado 28"
    ],
    "texto_paquete": "Paquete a México, Tour de 5 noches mínimo",
    "destino_completo": "Caribe - Cancún",
    "destacado": true,
    "activo": true,
    "pdf_url": "https://drive.google.com/file/d/paquete123/preview",
    "mensaje_reserva": "Me interesa el Paquete Todo Incluido Cancún",
    "fecha_creacion": "2026-01-10T08:00:00Z",
    "fecha_actualizacion": "2026-03-01T14:20:00Z"
  }
]
```

### 2. Obtener un paquete específico (Detalle completo)

- **Método:** `GET`
- **Endpoint:** `/api/paquetes/{id}/`
- **Descripción:** Obtiene todos los detalles de un paquete turístico. Incluye todos los campos del listado más los campos de detalle:
- **Campos adicionales en el detalle:**

```json
{
  "titulo_detalle": "Descubre el Paraíso del Caribe Mexicano",
  "descripcion_extensa": "Texto extenso describiendo el paquete...",
  "precio_aplica_desde": "2026-01-01",
  "precio_aplica_hasta": "2026-12-31",
  "ubicacion_mapa_url": "https://www.openstreetmap.org/#map=11/21.1619/-86.8515",
  "idioma": "Oficial Español (México)",
  "moneda_local": "Peso Mexicano",
  "documentos_requeridos": "Pasaporte vigente con al menos 6 meses de validez",
  "temperatura": "24°C - 32°C",
  "lugares_destacados": "Zona Hotelera, Playa Delfines, Mercado 28",
  "programa_incluye": "- 5 noches de alojamiento\n- Vuelo ida y vuelta\n- Alimentación todo incluido...",
  "no_incluye": "- Propinas\n- Gastos personales\n- Seguro médico adicional...",
  "como_reservar": "1. Contacta con nosotros\n2. Envía documentación...",
  "importante": "Información importante sobre el viaje",
  "horarios_vuelo": "Salida: 08:00 AM\nRegreso: 06:00 PM",
  "politicas_equipaje": "1 maleta de 23kg + 1 carry-on de 10kg",
  "requisitos_viaje": "Pasaporte vigente, visa si aplica",
  "formas_pago": "Tarjetas de crédito, transferencias bancarias",
  "politica_cancelacion": "Cancelación con reembolso hasta 30 días antes"
}
```

### 3. Obtener paquetes destacados (con orden personalizado)

- **Método:** `GET`
- **Endpoint:** `/api/paquetes/destacados/`
- **Descripción:** Retorna paquetes destacados respetando el orden configurado desde el admin. La cantidad máxima está controlada por `ConfiguracionDestacados.limite_paquetes`.

### 4. Obtener paquetes agrupados por región

- **Método:** `GET`
- **Endpoint:** `/api/paquetes/por_region/`
- **Descripción:** Retorna paquetes agrupados por región (máximo 6 por región)
- **Respuesta:**

```json
[
  {
    "region": {
      "id": 1,
      "nombre": "caribe",
      "nombre_display": "Caribe",
      "imagen_url": "https://example.com/caribe.jpg",
      "activo": true,
      "orden": 1,
      "cantidad_paises": 5,
      "cantidad_paquetes": 15
    },
    "paquetes": [
      {
        "id": 1,
        "titulo": "Paquete Todo Incluido Cancún",
        "...": "..."
      }
    ]
  }
]
```

---

## 🔧 Endpoints AJAX para Admin

Estos endpoints están diseñados para ser usados en el panel de administración de Django para cargas dinámicas de datos en selectores.

### 1. Obtener países por región

- **Método:** `GET`
- **Endpoint:** `/api/admin-ajax/paises-por-region/{region_id}/`
- **Descripción:** Retorna los países activos de una región (formato simple para `<select>`)
- **Respuesta:**

```json
[
  { "id": 1, "nombre": "México" },
  { "id": 2, "nombre": "República Dominicana" }
]
```

### 2. Obtener ciudades por país

- **Método:** `GET`
- **Endpoint:** `/api/admin-ajax/ciudades-por-pais/{pais_id}/`
- **Descripción:** Retorna las ciudades activas de un país (formato simple para `<select>`)
- **Respuesta:**

```json
[
  { "id": 1, "nombre": "Cancún" },
  { "id": 2, "nombre": "Playa del Carmen" }
]
```

### 3. Obtener aeropuertos por ciudad

- **Método:** `GET`
- **Endpoint:** `/api/admin-ajax/aeropuertos-por-ciudad/{ciudad_id}/`
- **Descripción:** Retorna aeropuertos activos de una ciudad. Si no hay aeropuertos para esa ciudad, devuelve los del país correspondiente.
- **Respuesta:**

```json
[
  {
    "id": 1,
    "nombre": "Aeropuerto José Joaquín de Olmedo",
    "codigo_iata": "GYE"
  }
]
```

### 4. Obtener aeropuertos por país

- **Método:** `GET`
- **Endpoint:** `/api/admin-ajax/aeropuertos-por-pais/{pais_id}/`
- **Descripción:** Retorna todos los aeropuertos activos de un país
- **Respuesta:**

```json
[
  {
    "id": 1,
    "nombre": "Aeropuerto José Joaquín de Olmedo",
    "codigo_iata": "GYE"
  },
  { "id": 2, "nombre": "Aeropuerto Mariscal Sucre", "codigo_iata": "UIO" }
]
```

---

## 🩺 Endpoints de Utilidad (Health y Seed)

### 1. Health check

- **Método:** `GET`
- **Endpoint:** `/api/health/`
- **Descripción:** Verifica que el servicio está activo (útil para monitoreo y plataformas de despliegue)
- **Respuesta:**

```json
{ "status": "ok" }
```

### 2. Seed de la base de datos

- **Método:** `GET`
- **Endpoint:** `/api/seed/?secret={SECRET}`
- **Descripción:** Endpoint interno para poblar la base de datos con paquetes de ejemplo (crea países base y ejecuta el seeder de paquetes). Requiere el parámetro `secret` correcto; si no coincide devuelve `403`.
- **Respuesta Exitosa:**

```json
{ "status": "seed complete", "paquetes": 12 }
```

- **Respuesta de Error (403):**

```json
{ "error": "invalid secret" }
```

---

## 📊 Modelos de Datos

### Cliente

| Campo             | Tipo              | Descripción                 |
| ----------------- | ----------------- | --------------------------- |
| `id`              | Integer (auto)    | Identificador único         |
| `nombre_completo` | String (50)       | Nombre completo del cliente |
| `email`           | Email (80, único) | Email único del cliente     |
| `telefono`        | String (15)       | Teléfono del cliente        |
| `fecha_registro`  | DateTime (auto)   | Fecha de registro           |

### Solicitud

| Campo            | Tipo                     | Descripción                      |
| ---------------- | ------------------------ | -------------------------------- |
| `id`             | Integer (auto)           | Identificador único              |
| `cliente`        | ForeignKey → Cliente     | Cliente que realiza la solicitud |
| `mensaje`        | Text (500)               | Mensaje de la solicitud          |
| `fecha_creacion` | DateTime (auto)          | Fecha de creación                |
| `atendido`       | Boolean (default: false) | Si fue atendida                  |

### Destino

| Campo                 | Tipo                               | Descripción                    |
| --------------------- | ---------------------------------- | ------------------------------ |
| `id`                  | Integer (auto)                     | Identificador único            |
| `nombre`              | String (100)                       | Nombre del destino             |
| `pais`                | ForeignKey → PaisRegion (opcional) | País del destino               |
| `ciudad`              | ForeignKey → Ciudad (opcional)     | Ciudad del destino             |
| `descripcion`         | Text                               | Descripción del destino        |
| `imagen_url`          | URL (500)                          | Imagen del destino             |
| `precio_desde`        | Decimal (10,2)                     | Precio desde                   |
| `destacado`           | Boolean                            | Si es destacado                |
| `activo`              | Boolean                            | Si está activo                 |
| `pdf_url`             | URL (500, opcional)                | PDF de Google Drive            |
| `mensaje_reserva`     | Text (opcional)                    | Mensaje predefinido de reserva |
| `fecha_creacion`      | DateTime (auto)                    | Fecha de creación              |
| `fecha_actualizacion` | DateTime (auto)                    | Fecha de actualización         |

### Vuelo

| Campo                 | Tipo                     | Descripción             |
| --------------------- | ------------------------ | ----------------------- |
| `id`                  | Integer (auto)           | Identificador único     |
| `aerolinea`           | ForeignKey → Aerolinea   | Aerolínea del vuelo     |
| `origen`              | ForeignKey → Aeropuerto  | Aeropuerto de origen    |
| `destino`             | ForeignKey → Aeropuerto  | Aeropuerto de destino   |
| `duracion`            | String (50)              | Duración (ej: "1h 45m") |
| `precio`              | Decimal (10,2)           | Precio del vuelo        |
| `imagen_url`          | URL (500, opcional)      | Imagen del vuelo        |
| `moneda`              | String (3, default: USD) | Moneda del precio       |
| `destacado`           | Boolean                  | Si es destacado         |
| `disponible`          | Boolean                  | Si está disponible      |
| `mensaje_reserva`     | Text (opcional)          | Mensaje de reserva      |
| `fecha_creacion`      | DateTime (auto)          | Fecha de creación       |
| `fecha_actualizacion` | DateTime (auto)          | Fecha de actualización  |

### Region

| Campo         | Tipo                 | Descripción                                                                                                                         |
| ------------- | -------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `id`          | Integer (auto)       | Identificador único                                                                                                                 |
| `nombre`      | Choice (único)       | Valores: `caribe`, `sudamerica`, `centroamerica`, `norteamerica`, `europa`, `medio_oriente`, `africa`, `asia`, `oceania`, `ecuador` |
| `descripcion` | Text (opcional)      | Descripción de la región                                                                                                            |
| `imagen_url`  | URL (500, opcional)  | Imagen de la región                                                                                                                 |
| `activo`      | Boolean              | Si está activa                                                                                                                      |
| `orden`       | Integer (default: 0) | Orden de aparición                                                                                                                  |

### PaisRegion

| Campo         | Tipo                   | Descripción                      |
| ------------- | ---------------------- | -------------------------------- |
| `id`          | Integer (auto)         | Identificador único              |
| `region`      | ForeignKey → Region    | Región a la que pertenece        |
| `nombre`      | String (100)           | Nombre en español                |
| `nombre_en`   | String (100, opcional) | Nombre en inglés                 |
| `codigo_iso`  | String (2, opcional)   | Código ISO de 2 letras (ej: MX)  |
| `codigo_iso3` | String (3, opcional)   | Código ISO de 3 letras (ej: MEX) |
| `capital`     | String (100, opcional) | Capital del país                 |
| `bandera_png` | URL (500, opcional)    | URL de bandera en PNG            |
| `bandera_svg` | URL (500, opcional)    | URL de bandera en SVG            |
| `activo`      | Boolean                | Si está activo                   |

> **Propiedad:** `bandera_url` — retorna SVG si existe, sino PNG.
> **Unique together:** `region` + `nombre`

### Ciudad

| Campo           | Tipo                    | Descripción                       |
| --------------- | ----------------------- | --------------------------------- |
| `id`            | Integer (auto)          | Identificador único               |
| `pais`          | ForeignKey → PaisRegion | País al que pertenece             |
| `nombre`        | String (100)            | Nombre de la ciudad               |
| `codigo_ciudad` | String (5, opcional)    | Código ISO de la ciudad (ej: GYE) |
| `latitud`       | Float (opcional)        | Latitud                           |
| `longitud`      | Float (opcional)        | Longitud                          |
| `es_capital`    | Boolean                 | Si es capital                     |
| `imagen_url`    | URL (500, opcional)     | Imagen de la ciudad               |
| `activo`        | Boolean                 | Si está activa                    |

> **Propiedad:** `codigo_aeropuerto` — alias de `codigo_ciudad`
> **Propiedad:** `ubicacion_completa` — retorna "Ciudad, País (Región)"
> **Unique together:** `pais` + `codigo_ciudad`

### Aerolinea

| Campo             | Tipo                   | Descripción                |
| ----------------- | ---------------------- | -------------------------- |
| `id`              | Integer (auto)         | Identificador único        |
| `nombre`          | String (200)           | Nombre de la aerolínea     |
| `codigo_iata`     | String (3, opcional)   | Código IATA (ej: LA, AV)   |
| `codigo_icao`     | String (4, opcional)   | Código ICAO (ej: LAN, AVA) |
| `pais_origen`     | String (100, opcional) | País de origen             |
| `anio_creacion`   | String (10, opcional)  | Año de creación            |
| `base_aeropuerto` | String (300, opcional) | Aeropuerto base            |
| `logo_url`        | URL (500, opcional)    | URL del logo completo      |
| `brandmark_url`   | URL (500, opcional)    | URL del brandmark/isotipo  |
| `sitio_web`       | URL (300, opcional)    | Sitio web                  |
| `activo`          | Boolean                | Si está activa             |

### Aeropuerto

| Campo           | Tipo                           | Descripción                |
| --------------- | ------------------------------ | -------------------------- |
| `id`            | Integer (auto)                 | Identificador único        |
| `codigo_iata`   | String (3, único)              | Código IATA (ej: GYE, UIO) |
| `codigo_icao`   | String (4, opcional)           | Código ICAO (ej: SEGU)     |
| `nombre`        | String (200)                   | Nombre del aeropuerto      |
| `ciudad`        | ForeignKey → Ciudad (opcional) | Ciudad vinculada           |
| `pais`          | ForeignKey → PaisRegion        | País del aeropuerto        |
| `nombre_ciudad` | String (100, opcional)         | Ciudad en texto libre      |
| `region`        | String (100, opcional)         | Estado / Provincia         |
| `latitud`       | Float (opcional)               | Latitud                    |
| `longitud`      | Float (opcional)               | Longitud                   |
| `elevacion_ft`  | Integer (opcional)             | Elevación en pies          |
| `zona_horaria`  | String (50, opcional)          | Zona horaria               |
| `activo`        | Boolean                        | Si está activo             |

> **Propiedad:** `ubicacion_completa` — retorna "Ciudad, País"

### TipoPaquete

| Campo    | Tipo               | Descripción                                     |
| -------- | ------------------ | ----------------------------------------------- |
| `id`     | Integer (auto)     | Identificador único                             |
| `nombre` | String (50, único) | Nombre del tipo (ej: Vacaciones, Todo Incluido) |
| `activo` | Boolean            | Si está activo                                  |

### Temporada

| Campo    | Tipo               | Descripción                             |
| -------- | ------------------ | --------------------------------------- |
| `id`     | Integer (auto)     | Identificador único                     |
| `nombre` | String (50, único) | Nombre de la temporada (ej: Alta, Baja) |
| `activo` | Boolean            | Si está activa                          |

### TipoViaje

| Campo    | Tipo               | Descripción                            |
| -------- | ------------------ | -------------------------------------- |
| `id`     | Integer (auto)     | Identificador único                    |
| `nombre` | String (50, único) | Nombre del tipo (ej: Familiar, Pareja) |
| `activo` | Boolean            | Si está activo                         |

### PaqueteTuristico

| Campo                          | Tipo                                | Descripción                       |
| ------------------------------ | ----------------------------------- | --------------------------------- |
| `id`                           | Integer (auto)                      | Identificador único               |
| **Info básica del card**       |                                     |                                   |
| `titulo`                       | String (200)                        | Título del paquete                |
| `subtitulo`                    | String (200, opcional)              | Subtítulo (ej: Enero a Diciembre) |
| `imagen_url`                   | URL (500)                           | Imagen principal                  |
| `descripcion_corta`            | Text (500)                          | Descripción breve                 |
| **Ubicación**                  |                                     |                                   |
| `region`                       | ForeignKey → Region                 | Región del paquete                |
| `pais_destino`                 | ForeignKey → PaisRegion             | País destino                      |
| `ciudad_destino`               | ForeignKey → Ciudad (opcional)      | Ciudad destino                    |
| **Precios**                    |                                     |                                   |
| `precio`                       | Decimal (10,2)                      | Precio desde                      |
| `moneda`                       | String (3, default: USD)            | Moneda                            |
| `tipo_paquete`                 | ForeignKey → TipoPaquete (opcional) | Tipo de paquete                   |
| **Duración**                   |                                     |                                   |
| `duracion_noches`              | Integer                             | Número de noches                  |
| `duracion_dias`                | Integer (default: 1)                | Número de días                    |
| `salidas`                      | String (200)                        | Ciudades de salida                |
| `fecha_salidas_texto`          | String (100, opcional)              | Texto de fechas de salida         |
| **Aerolínea**                  |                                     |                                   |
| `aerolinea`                    | ForeignKey → Aerolinea (opcional)   | Aerolínea del paquete             |
| **Detalle**                    |                                     |                                   |
| `titulo_detalle`               | String (300, opcional)              | Título en página de detalle       |
| `descripcion_extensa`          | Text (opcional)                     | Descripción completa              |
| **Detalles del destino**       |                                     |                                   |
| `temporada`                    | ForeignKey → Temporada (opcional)   | Temporada del paquete             |
| `tipo_viaje`                   | ForeignKey → TipoViaje (opcional)   | Tipo de viaje                     |
| `precio_aplica_desde`          | Date (opcional)                     | Inicio vigencia precio            |
| `precio_aplica_hasta`          | Date (opcional)                     | Fin vigencia precio               |
| **Info del destino (sidebar)** |                                     |                                   |
| `ubicacion_mapa_url`           | URL (500, opcional)                 | URL de OpenStreetMap              |
| `idioma`                       | String (100, opcional)              | Idioma del destino                |
| `moneda_local`                 | String (100, opcional)              | Moneda local                      |
| `lugares_destacados`           | Text (opcional)                     | Lugares separados por comas       |
| `documentos_requeridos`        | Text (opcional)                     | Documentos necesarios             |
| `temperatura`                  | String (50, opcional)               | Temperatura del destino           |
| **Secciones de texto**         |                                     |                                   |
| `programa_incluye`             | Text (opcional)                     | Qué incluye el programa           |
| `no_incluye`                   | Text (opcional)                     | Qué no incluye                    |
| `como_reservar`                | Text (opcional)                     | Cómo reservar                     |
| `importante`                   | Text (opcional)                     | Información importante            |
| `horarios_vuelo`               | Text (opcional)                     | Horarios de vuelos                |
| `politicas_equipaje`           | Text (opcional)                     | Políticas de equipaje             |
| `requisitos_viaje`             | Text (opcional)                     | Requisitos de viaje               |
| `formas_pago`                  | Text (opcional)                     | Formas de pago                    |
| `politica_cancelacion`         | Text (opcional)                     | Política de cancelación           |
| **Paquete incluye (iconos)**   |                                     |                                   |
| `incluye_vuelo`                | Boolean (default: true)             | ¿Incluye vuelo?                   |
| `incluye_hotel`                | Boolean (default: true)             | ¿Incluye hotel?                   |
| `incluye_alimentacion`         | Boolean (default: false)            | ¿Incluye alimentación?            |
| `incluye_traslados`            | Boolean (default: false)            | ¿Incluye traslados?               |
| `incluye_tours`                | Boolean (default: false)            | ¿Incluye tours?                   |
| `incluye_seguro`               | Boolean (default: false)            | ¿Incluye seguro?                  |
| **PDF y contacto**             |                                     |                                   |
| `pdf_url`                      | URL (500, opcional)                 | PDF de Google Drive               |
| `mensaje_reserva`              | Text (opcional)                     | Mensaje predefinido de reserva    |
| **Estado**                     |                                     |                                   |
| `destacado`                    | Boolean                             | Si es destacado                   |
| `activo`                       | Boolean                             | Si está activo                    |
| `fecha_creacion`               | DateTime (auto)                     | Fecha de creación                 |
| `fecha_actualizacion`          | DateTime (auto)                     | Fecha de actualización            |

> **Propiedad:** `texto_paquete` — "Paquete a {país}, Tour de {noches} noches mínimo"
> **Propiedad:** `destino_completo` — "{Región} - {Ciudad o País}"

### ConfiguracionDestacados (Singleton)

| Campo             | Tipo                  | Descripción                     |
| ----------------- | --------------------- | ------------------------------- |
| `limite_vuelos`   | Integer (default: 10) | Máx. vuelos destacados en API   |
| `limite_paquetes` | Integer (default: 10) | Máx. paquetes destacados en API |
| `limite_destinos` | Integer (default: 10) | Máx. destinos destacados en API |

---

## 🔍 Filtros Disponibles (Resumen)

### Destinos

- `?pais={id}` — Filtrar por país
- `?ciudad={id}` — Filtrar por ciudad
- `?destacado=true` — Solo destacados

### Vuelos

- `?origen={texto}` — Buscar por nombre de aeropuerto, ciudad o código IATA de origen
- `?destino={texto}` — Buscar por nombre de aeropuerto, ciudad o código IATA de destino

### Países

- `?region={id}` — Filtrar por región

### Ciudades

- `?pais={id}` — Filtrar por país
- `?region={id}` — Filtrar por región
- `?capital=true` — Solo capitales

### Aerolíneas

- `?pais={texto}` — Filtrar por país de origen
- `?search={texto}` — Buscar por nombre, IATA o ICAO

### Aeropuertos

- `?pais={id}` — Filtrar por país
- `?region={texto}` — Filtrar por estado/provincia
- `?ciudad={id}` — Filtrar por ciudad
- `?search={texto}` — Buscar por nombre, IATA, ICAO o ciudad

### Paquetes Turísticos

- `?region={id}` — Filtrar por región
- `?pais={id}` — Filtrar por país
- `?tipo={nombre}` — Filtrar por tipo de paquete (nombre exacto)
- `?temporada={nombre}` — Filtrar por temporada (nombre exacto)
- `?precio_max={precio}` — Filtrar por precio máximo
- `?destacados=true` — Solo destacados
- `?aerolinea={id}` — Filtrar por aerolínea

---

## 📝 Notas Adicionales

### Validación de PDFs

Todos los campos `pdf_url` aceptan URLs de Google Drive y automáticamente las convierten al formato de vista previa (`/preview`). El formato esperado es:

```
https://drive.google.com/file/d/ID_DEL_ARCHIVO/view
```

### Validación de Mapas

El campo `ubicacion_mapa_url` en paquetes turísticos solo acepta URLs de OpenStreetMap:

```
https://www.openstreetmap.org/#map=11/4.6497/-74.1165
```

### Notificaciones

El endpoint `/api/contacto/` envía automáticamente:

1. Un correo electrónico a la empresa con los datos del contacto
2. Una notificación por WhatsApp (si está configurado)

### Destacados con Orden Personalizado

Los endpoints `/api/vuelos/destacados/`, `/api/paquetes/destacados/` y `/api/destinos/destacados/` respetan el orden configurado desde el panel de administración mediante los modelos `OrdenVueloDestacado`, `OrdenPaqueteDestacado` y `OrdenDestinoDestacado`. Los elementos sin orden configurado se agregan al final por fecha de creación. Los límites se configuran en `ConfiguracionDestacados`.

### Serializers Dinámicos

Algunos ViewSets usan serializers diferentes según la acción:

| Endpoint              | Listado (`list`)                      | Detalle (`retrieve`)                       |
| --------------------- | ------------------------------------- | ------------------------------------------ |
| `/api/regiones/`      | `RegionListSerializer` (compacto)     | `RegionSerializer` (con países y ciudades) |
| `/api/paises-region/` | `PaisRegionListSerializer` (compacto) | `PaisRegionSerializer` (con ciudades)      |
| `/api/aeropuertos/`   | `AeropuertoListSerializer` (compacto) | `AeropuertoSerializer` (completo)          |
| `/api/paquetes/`      | `PaqueteTuristicoListSerializer`      | `PaqueteTuristicoDetailSerializer`         |

### Vigencia de Paquetes

Los endpoints de paquetes ejecutan `PaqueteTuristico.sincronizar_vigencia()` antes de responder: desactivan automáticamente los paquetes cuyo `precio_aplica_hasta` ya venció y reactivan los que vuelven a estar vigentes.

### Variables de Entorno del Booking

| Variable | Descripción |
| -------- | ----------- |
| `STRIPE_SECRET_KEY` | Clave secreta de Stripe (`sk_test_...` / `sk_live_...`) |
| `STRIPE_WEBHOOK_SECRET` | Secreto para validar la firma del webhook (opcional) |
| `BOOKING_SANDBOX` | `1` (default) simula Sabre createBooking; `0` intenta la llamada real |
| `BOOKING_SEND_EMAIL` | `1` (default) envía el voucher por correo tras confirmar |
| `SEATMAP_SANDBOX` | Activa la respuesta simulada del mapa de asientos |
| `FRONTEND_BOOKING_SUCCESS_URL` / `FRONTEND_BOOKING_CANCEL_URL` | URLs de retorno por defecto de Stripe |
| `FRONTEND_PAQUETE_SUCCESS_URL` / `FRONTEND_PAQUETE_CANCEL_URL` | URLs de retorno para booking de paquetes |
| `GROQ_API_KEY` | API key de Groq para el chatbot |

### Cache de Reservas

- El **intento de reserva** (checkout) se guarda en cache por **24 horas** — si no se confirma en ese tiempo, `confirm` devuelve `404`.
- La **reserva confirmada** se guarda por **7 días**, indexada por `session_id` y por PNR/localizador. Si expiró, el voucher se puede regenerar reenviando la reserva completa por `POST`.

### CORS

Para producción, asegúrate de configurar correctamente CORS en `settings.py` para permitir peticiones desde tu frontend.

### Paginación

Por defecto, Django REST Framework puede incluir paginación. Verifica la configuración en `settings.py` si necesitas ajustar el número de resultados por página.

---

## 🚀 Ejemplos de Uso

### JavaScript (Fetch API)

```javascript
// Obtener todos los paquetes destacados
fetch("http://127.0.0.1:8000/api/paquetes/destacados/")
  .then((response) => response.json())
  .then((data) => console.log(data))
  .catch((error) => console.error("Error:", error));

// Enviar formulario de contacto
fetch("http://127.0.0.1:8000/api/contacto/", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    nombre_completo: "Juan Pérez",
    email: "juan@example.com",
    telefono: "+593987654321",
    mensaje: "Quiero información sobre paquetes",
  }),
})
  .then((response) => response.json())
  .then((data) => console.log(data))
  .catch((error) => console.error("Error:", error));

// Autocompletado de aeropuertos
fetch("http://127.0.0.1:8000/api/aeropuertos/autocomplete/?q=miami")
  .then((response) => response.json())
  .then((data) => console.log(data.results))
  .catch((error) => console.error("Error:", error));

// Buscar vuelos en vivo con Sabre
fetch("http://127.0.0.1:8000/api/buscar-vuelos-live/", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    origin: "UIO",
    destination: "MIA",
    date: "2026-06-15",
    return_date: "2026-06-22",
    adults: 2,
    children: 0,
    infants: 0,
    cabin_class: "Y",
    limit: 20,
  }),
})
  .then((response) => response.json())
  .then((data) => console.log(data))
  .catch((error) => console.error("Error:", error));
```

### Python (requests)

```python
import requests

# Obtener paquetes de una región específica
response = requests.get('http://127.0.0.1:8000/api/paquetes/', params={'region': 1})
paquetes = response.json()

# Buscar aerolínea por código IATA
response = requests.get('http://127.0.0.1:8000/api/aerolineas/buscar_iata/', params={'codigo': 'AV'})
aerolinea = response.json()

# Buscar vuelos en vivo
response = requests.post('http://127.0.0.1:8000/api/buscar-vuelos-live/', json={
    'origin': 'GYE',
    'destination': 'BOG',
    'date': '2026-07-01',
    'adults': 1,
    'cabin_class': 'Y'
})
vuelos = response.json()

# Reservar un paquete (crear checkout de Stripe)
response = requests.post('http://127.0.0.1:8000/api/paquetes/booking/checkout/', json={
    'paquete_id': 12,
    'n_personas': 2,
    'contacto': {'email': 'juan@example.com', 'phone': '+593987654321'},
    'fecha_viaje': '2026-08-15'
})
checkout = response.json()  # -> redirigir al usuario a checkout['checkout_url']

# Confirmar la reserva tras el pago
response = requests.post('http://127.0.0.1:8000/api/paquetes/booking/confirm/', json={
    'session_id': checkout['session_id']
})
reserva = response.json()

# Chatbot
response = requests.post('http://127.0.0.1:8000/api/chatbot/', json={
    'mensaje': '¿Qué paquetes tienen al Caribe?',
    'historial': []
})
chat = response.json()  # -> chat['respuesta'], chat['historial'], chat['accion']
```

---

## 📧 Contacto y Soporte

Para más información o soporte técnico, contacta al equipo de desarrollo.

**Última actualización:** Julio 18, 2026
