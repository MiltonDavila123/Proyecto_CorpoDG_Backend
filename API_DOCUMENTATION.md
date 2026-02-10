# 📚 Documentación de APIs - CorpoDG Backend

## 📋 Índice

1. [Información General](#información-general)
2. [Autenticación](#autenticación)
3. [Endpoints de Clientes](#endpoints-de-clientes)
4. [Endpoints de Solicitudes](#endpoints-de-solicitudes)
5. [Endpoint de Contacto](#endpoint-de-contacto)
6. [Endpoints de Destinos](#endpoints-de-destinos)
7. [Endpoints de Hoteles](#endpoints-de-hoteles)
8. [Endpoints de Vuelos](#endpoints-de-vuelos)
9. [Endpoints de Renta de Autos](#endpoints-de-renta-de-autos)
10. [Endpoints de Regiones](#endpoints-de-regiones)
11. [Endpoints de Países](#endpoints-de-países)
12. [Endpoints de Ciudades](#endpoints-de-ciudades)
13. [Endpoints de Aerolíneas](#endpoints-de-aerolíneas)
14. [Endpoints de Paquetes Turísticos](#endpoints-de-paquetes-turísticos)
15. [Endpoints AJAX para Admin](#endpoints-ajax-para-admin)

---

## 📌 Información General

**URL Base:** `http://127.0.0.1:8000/api/`

**Formato de Respuesta:** JSON

**Framework:** Django REST Framework

---

## 🔐 Autenticación

Actualmente, las APIs están configuradas sin autenticación para facilitar el acceso público. Para producción, se recomienda implementar autenticación mediante tokens o JWT.

---

## 👥 Endpoints de Clientes

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

### 1. Listar todas las solicitudes

- **Método:** `GET`
- **Endpoint:** `/api/solicitudes/`
- **Descripción:** Obtiene una lista de todas las solicitudes
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
- **Descripción:** Endpoint principal para el formulario de contacto del sitio web. Si el cliente existe (por email), solo crea la solicitud. Si no existe, crea el cliente y la solicitud. También envía notificaciones por email y WhatsApp.
- **Body:**

```json
{
  "nombre_completo": "Carlos Rodríguez",
  "email": "carlos@example.com",
  "telefono": "+593998765432",
  "mensaje": "Me gustaría recibir información sobre paquetes a Sudamérica"
}
```

- **Respuesta Exitosa:**

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

- **Respuesta de Error:**

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

### 1. Listar todos los destinos

- **Método:** `GET`
- **Endpoint:** `/api/destinos/`
- **Descripción:** Obtiene una lista de todos los destinos turísticos activos
- **Respuesta:**

```json
[
  {
    "id": 1,
    "nombre": "Cancún",
    "pais": "México",
    "descripcion": "Playas paradisíacas del Caribe mexicano",
    "imagen_url": "https://example.com/cancun.jpg",
    "precio_desde": 899.99,
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

### 3. Crear un destino

- **Método:** `POST`
- **Endpoint:** `/api/destinos/`
- **Descripción:** Crea un nuevo destino (requiere permisos de administrador)

### 4. Actualizar un destino

- **Método:** `PUT` / `PATCH`
- **Endpoint:** `/api/destinos/{id}/`

### 5. Eliminar un destino

- **Método:** `DELETE`
- **Endpoint:** `/api/destinos/{id}/`

---

## 🏨 Endpoints de Hoteles

### 1. Listar todos los hoteles

- **Método:** `GET`
- **Endpoint:** `/api/hoteles/`
- **Descripción:** Obtiene una lista de todos los hoteles disponibles
- **Query Parameters:**
  - `destino` (opcional): Filtrar hoteles por ID de destino
- **Ejemplo:** `/api/hoteles/?destino=1`
- **Respuesta:**

```json
[
  {
    "id": 1,
    "nombre": "Hotel Paradisus Cancún",
    "destino": 1,
    "destino_nombre": "Cancún",
    "descripcion": "Resort todo incluido frente al mar",
    "imagen_url": "https://example.com/hotel-paradisus.jpg",
    "direccion": "Blvd. Kukulcan Km 16.5, Zona Hotelera",
    "estrellas": 5,
    "precio_noche": 250.0,
    "servicios": "Wi-Fi, Piscina, Spa, Restaurante, Bar",
    "servicios_lista": ["Wi-Fi", "Piscina", "Spa", "Restaurante", "Bar"],
    "disponible": true,
    "pdf_url": "https://drive.google.com/file/d/xyz789/preview",
    "mensaje_reserva": "Me interesa el Hotel Paradisus Cancún"
  }
]
```

### 2. Obtener un hotel específico

- **Método:** `GET`
- **Endpoint:** `/api/hoteles/{id}/`

### 3-5. Crear, Actualizar, Eliminar hotel

- Métodos: `POST`, `PUT/PATCH`, `DELETE`
- Endpoints: `/api/hoteles/`, `/api/hoteles/{id}/`

---

## ✈️ Endpoints de Vuelos

### 1. Listar todos los vuelos

- **Método:** `GET`
- **Endpoint:** `/api/vuelos/`
- **Descripción:** Obtiene una lista de todos los vuelos disponibles
- **Query Parameters:**
  - `origen` (opcional): Filtrar por ciudad de origen
  - `destino` (opcional): Filtrar por ciudad de destino
- **Ejemplo:** `/api/vuelos/?origen=Quito&destino=Miami`
- **Respuesta:**

```json
[
  {
    "id": 1,
    "aerolinea": 1,
    "aerolinea_nombre": "LATAM Airlines",
    "aerolinea_logo": "https://example.com/latam-logo.png",
    "origen": 5,
    "origen_nombre": "Quito",
    "origen_pais": "Ecuador",
    "destino": 12,
    "destino_nombre": "Miami",
    "destino_pais": "Estados Unidos",
    "tipo_vuelo": "directo",
    "numero_vuelo": "LA2479",
    "duracion": "4h 30m",
    "precio": 450.0,
    "imagen_url": "https://example.com/vuelo-imagen.jpg",
    "moneda": "USD",
    "disponible": true,
    "pdf_url": "https://drive.google.com/file/d/vuelo123/preview",
    "mensaje_reserva": "Me interesa el vuelo LA2479"
  }
]
```

### 2. Obtener un vuelo específico

- **Método:** `GET`
- **Endpoint:** `/api/vuelos/{id}/`

### 3-5. Crear, Actualizar, Eliminar vuelo

- Métodos: `POST`, `PUT/PATCH`, `DELETE`
- Endpoints: `/api/vuelos/`, `/api/vuelos/{id}/`

---

## 🚗 Endpoints de Renta de Autos

### 1. Listar todos los autos disponibles

- **Método:** `GET`
- **Endpoint:** `/api/renta-autos/`
- **Descripción:** Obtiene una lista de todos los autos disponibles para renta
- **Query Parameters:**
  - `tipo` (opcional): Filtrar por tipo de auto (economico, sedan, suv, lujo, van)
  - `ubicacion` (opcional): Filtrar por ubicación
  - `ciudad` (opcional): Filtrar por ID de ciudad
  - `pais` (opcional): Filtrar por ID de país
  - `region` (opcional): Filtrar por ID de región
- **Ejemplo:** `/api/renta-autos/?tipo=suv&ciudad=1`
- **Respuesta:**

```json
[
  {
    "id": 1,
    "marca": "Toyota",
    "modelo": "RAV4",
    "tipo": "suv",
    "ano": 2024,
    "capacidad_pasajeros": 5,
    "transmision": "automatica",
    "precio_dia": 75.0,
    "imagen_url": "https://example.com/toyota-rav4.jpg",
    "ciudad": 1,
    "ciudad_nombre": "Quito",
    "ciudad_pais": "Ecuador",
    "direccion": "Aeropuerto Internacional Mariscal Sucre",
    "caracteristicas": "Aire acondicionado, GPS, Bluetooth, 4x4",
    "caracteristicas_lista": ["Aire acondicionado", "GPS", "Bluetooth", "4x4"],
    "disponible": true,
    "pdf_url": "https://drive.google.com/file/d/auto123/preview",
    "mensaje_reserva": "Me interesa rentar Toyota RAV4"
  }
]
```

### 2. Obtener un auto específico

- **Método:** `GET`
- **Endpoint:** `/api/renta-autos/{id}/`

### 3-5. Crear, Actualizar, Eliminar auto

- Métodos: `POST`, `PUT/PATCH`, `DELETE`
- Endpoints: `/api/renta-autos/`, `/api/renta-autos/{id}/`

---

## 🌍 Endpoints de Regiones

### 1. Listar todas las regiones

- **Método:** `GET`
- **Endpoint:** `/api/regiones/`
- **Descripción:** Obtiene una lista de todas las regiones activas con sus países y ciudades
- **Respuesta:**

```json
[
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
        "codigo_pais": "MEX",
        "bandera_url": "https://example.com/bandera-mexico.png",
        "region": 1,
        "region_nombre": "Caribe",
        "ciudades": [
          {
            "id": 1,
            "nombre": "Cancún",
            "codigo_aeropuerto": "CUN",
            "es_capital": false,
            "imagen_url": "https://example.com/cancun.jpg",
            "pais": 1,
            "pais_nombre": "México",
            "region_nombre": "Caribe",
            "ubicacion_completa": "Cancún, México (Caribe)",
            "activo": true
          }
        ],
        "cantidad_ciudades": 1,
        "activo": true
      }
    ],
    "cantidad_paquetes": 15
  }
]
```

### 2. Obtener una región específica

- **Método:** `GET`
- **Endpoint:** `/api/regiones/{id}/`

### 3. Obtener países de una región

- **Método:** `GET`
- **Endpoint:** `/api/regiones/{id}/paises/`
- **Descripción:** Acción personalizada que retorna solo los países de una región específica

### 4. Obtener paquetes de una región

- **Método:** `GET`
- **Endpoint:** `/api/regiones/{id}/paquetes/`
- **Descripción:** Acción personalizada que retorna los paquetes turísticos de una región

---

## 🌎 Endpoints de Países

### 1. Listar todos los países

- **Método:** `GET`
- **Endpoint:** `/api/paises-region/`
- **Descripción:** Obtiene una lista de todos los países/destinos de regiones
- **Query Parameters:**
  - `region` (opcional): Filtrar países por ID de región
- **Ejemplo:** `/api/paises-region/?region=1`
- **Respuesta (listado):**

```json
[
  {
    "id": 1,
    "nombre": "México",
    "codigo_pais": "MEX",
    "bandera_url": "https://example.com/bandera-mexico.png",
    "region": 1,
    "region_nombre": "Caribe",
    "cantidad_ciudades": 3,
    "activo": true
  }
]
```

### 2. Obtener un país específico

- **Método:** `GET`
- **Endpoint:** `/api/paises-region/{id}/`
- **Descripción:** Obtiene los detalles de un país incluyendo todas sus ciudades
- **Respuesta (detalle):**

```json
{
  "id": 1,
  "nombre": "México",
  "codigo_pais": "MEX",
  "bandera_url": "https://example.com/bandera-mexico.png",
  "region": 1,
  "region_nombre": "Caribe",
  "ciudades": [
    {
      "id": 1,
      "nombre": "Cancún",
      "codigo_aeropuerto": "CUN",
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
```

### 3. Obtener ciudades de un país

- **Método:** `GET`
- **Endpoint:** `/api/paises-region/{id}/ciudades/`
- **Descripción:** Acción personalizada que retorna solo las ciudades de un país

### 4. Obtener paquetes de un país

- **Método:** `GET`
- **Endpoint:** `/api/paises-region/{id}/paquetes/`
- **Descripción:** Acción personalizada que retorna los paquetes turísticos de un país

---

## 🏙️ Endpoints de Ciudades

### 1. Listar todas las ciudades

- **Método:** `GET`
- **Endpoint:** `/api/ciudades/`
- **Descripción:** Obtiene una lista de todas las ciudades activas
- **Query Parameters:**
  - `pais` (opcional): Filtrar ciudades por ID de país
  - `region` (opcional): Filtrar ciudades por ID de región
  - `capital` (opcional): Filtrar solo capitales (valores: `true` o `false`)
- **Ejemplo:** `/api/ciudades/?pais=1&capital=true`
- **Respuesta:**

```json
[
  {
    "id": 5,
    "nombre": "Quito",
    "codigo_aeropuerto": "UIO",
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

### 1. Listar todas las aerolíneas

- **Método:** `GET`
- **Endpoint:** `/api/aerolineas/`
- **Descripción:** Obtiene una lista de todas las aerolíneas activas
- **Respuesta:**

```json
[
  {
    "id": 1,
    "nombre": "LATAM Airlines",
    "logo_url": "https://example.com/latam-logo.png",
    "activo": true
  },
  {
    "id": 2,
    "nombre": "Copa Airlines",
    "logo_url": "https://example.com/copa-logo.png",
    "activo": true
  }
]
```

### 2. Obtener una aerolínea específica

- **Método:** `GET`
- **Endpoint:** `/api/aerolineas/{id}/`

### 3. Obtener vuelos de una aerolínea

- **Método:** `GET`
- **Endpoint:** `/api/aerolineas/{id}/vuelos/`
- **Descripción:** Acción personalizada que retorna todos los vuelos de una aerolínea específica

---

## 🎁 Endpoints de Paquetes Turísticos

### 1. Listar todos los paquetes

- **Método:** `GET`
- **Endpoint:** `/api/paquetes/`
- **Descripción:** Obtiene una lista de todos los paquetes turísticos activos
- **Query Parameters:**
  - `region` (opcional): Filtrar por ID de región
  - `pais` (opcional): Filtrar por ID de país
  - `tipo` (opcional): Filtrar por tipo de paquete (vacaciones, promo, oferta, todo_incluido, aventura, luna_miel, familiar, negocios)
  - `temporada` (opcional): Filtrar por temporada (baja, media, alta)
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
    "pais_bandera": "https://example.com/bandera-mexico.png",
    "ciudad_destino": 1,
    "ciudad_nombre": "Cancún",
    "precio": 1299.99,
    "moneda": "USD",
    "tipo_paquete": "todo_incluido",
    "tipo_paquete_display": "Todo Incluido",
    "duracion_dias": 6,
    "duracion_noches": 5,
    "salidas": "Quito y Guayaquil",
    "fecha_salidas_texto": "2026 Enero a Diciembre",
    "aerolinea": 1,
    "aerolinea_nombre": "LATAM Airlines",
    "aerolinea_logo": "https://example.com/latam-logo.png",
    "temporada": "alta",
    "temporada_display": "Temporada Alta",
    "tipo_viaje": "familiar",
    "tipo_viaje_display": "Viajes de familia",
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
    "mensaje_reserva": "Me interesa el Paquete Todo Incluido Cancún"
  }
]
```

### 2. Obtener un paquete específico (Detalle completo)

- **Método:** `GET`
- **Endpoint:** `/api/paquetes/{id}/`
- **Descripción:** Obtiene todos los detalles de un paquete turístico
- **Respuesta:** Incluye todos los campos del listado más:

```json
{
  "titulo_detalle": "Descubre el Paraíso del Caribe Mexicano",
  "descripcion_extensa": "Texto extenso describiendo el paquete...",
  "precio_aplica_desde": "2026-01-01",
  "precio_aplica_hasta": "2026-12-31",
  "ubicacion_mapa_url": "https://example.com/mapa-cancun.jpg",
  "idioma": "Oficial Español (México)",
  "moneda_local": "Peso Mexicano",
  "documentos_requeridos": "Pasaporte vigente con al menos 6 meses de validez",
  "temperatura": "24°C - 32°C",
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

### 3. Obtener solo paquetes destacados

- **Método:** `GET`
- **Endpoint:** `/api/paquetes/destacados/`
- **Descripción:** Acción personalizada que retorna solo los paquetes marcados como destacados

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
      },
      {
        "id": 2,
        "titulo": "Aventura en Punta Cana",
        "...": "..."
      }
    ]
  },
  {
    "region": {
      "id": 2,
      "nombre": "sudamerica",
      "nombre_display": "Sudamérica",
      "...": "..."
    },
    "paquetes": []
  }
]
```

---

## 🔧 Endpoints AJAX para Admin

Estos endpoints están diseñados para ser usados en el panel de administración de Django para cargas dinámicas de datos.

### 1. Obtener países por región

- **Método:** `GET`
- **Endpoint:** `/api/admin-ajax/paises-por-region/{region_id}/`
- **Descripción:** Retorna los países de una región específica (formato simple para select)
- **Respuesta:**

```json
[
  {
    "id": 1,
    "nombre": "México"
  },
  {
    "id": 2,
    "nombre": "República Dominicana"
  }
]
```

### 2. Obtener ciudades por país

- **Método:** `GET`
- **Endpoint:** `/api/admin-ajax/ciudades-por-pais/{pais_id}/`
- **Descripción:** Retorna las ciudades de un país específico (formato simple para select)
- **Respuesta:**

```json
[
  {
    "id": 1,
    "nombre": "Cancún"
  },
  {
    "id": 2,
    "nombre": "Playa del Carmen"
  }
]
```

---

## 📊 Modelos de Datos

### Cliente

- `id`: Integer (auto)
- `nombre_completo`: String (50)
- `email`: Email (80, único)
- `telefono`: String (15)
- `fecha_registro`: DateTime (auto)

### Solicitud

- `id`: Integer (auto)
- `cliente`: ForeignKey (Cliente)
- `mensaje`: Text (500)
- `fecha_creacion`: DateTime (auto)
- `atendido`: Boolean (default: false)

### Destino

- `id`: Integer (auto)
- `nombre`: String (100)
- `pais`: String (100)
- `descripcion`: Text
- `imagen_url`: URL (500)
- `precio_desde`: Decimal (10,2)
- `destacado`: Boolean
- `activo`: Boolean
- `pdf_url`: URL (500, opcional)
- `mensaje_reserva`: Text (opcional)
- `fecha_creacion`: DateTime (auto)
- `fecha_actualizacion`: DateTime (auto)

### Hotel

- `id`: Integer (auto)
- `nombre`: String (200)
- `destino`: ForeignKey (Destino)
- `descripcion`: Text
- `imagen_url`: URL (500)
- `direccion`: String (300)
- `estrellas`: Integer (1-5)
- `precio_noche`: Decimal (10,2)
- `servicios`: Text
- `disponible`: Boolean
- `pdf_url`: URL (500, opcional)
- `mensaje_reserva`: Text (opcional)

### Vuelo

- `id`: Integer (auto)
- `aerolinea`: ForeignKey (Aerolinea)
- `origen`: ForeignKey (Ciudad)
- `destino`: ForeignKey (Ciudad)
- `tipo_vuelo`: Choice (directo, escala)
- `numero_vuelo`: String (20)
- `duracion`: String (50)
- `precio`: Decimal (10,2)
- `imagen_url`: URL (500, opcional)
- `moneda`: String (3, default: USD)
- `disponible`: Boolean
- `pdf_url`: URL (500, opcional)
- `mensaje_reserva`: Text (opcional)

### RentaAuto

- `id`: Integer (auto)
- `marca`: String (100)
- `modelo`: String (100)
- `tipo`: Choice (economico, sedan, suv, lujo, van)
- `ano`: Integer
- `capacidad_pasajeros`: Integer
- `transmision`: Choice (manual, automatica)
- `precio_dia`: Decimal (10,2)
- `imagen_url`: URL (500)
- `ciudad`: ForeignKey (Ciudad)
- `direccion`: String (300, opcional)
- `caracteristicas`: Text
- `disponible`: Boolean
- `pdf_url`: URL (500, opcional)
- `mensaje_reserva`: Text (opcional)

### Region

- `id`: Integer (auto)
- `nombre`: Choice (caribe, sudamerica, centroamerica, norteamerica, europa, medio_oriente, africa, asia, ecuador)
- `descripcion`: Text (opcional)
- `imagen_url`: URL (500, opcional)
- `activo`: Boolean
- `orden`: Integer (default: 0)

### PaisRegion

- `id`: Integer (auto)
- `region`: ForeignKey (Region)
- `nombre`: String (100)
- `codigo_pais`: String (3, opcional)
- `bandera_url`: URL (500, opcional)
- `activo`: Boolean

### Ciudad

- `id`: Integer (auto)
- `pais`: ForeignKey (PaisRegion)
- `nombre`: String (100)
- `codigo_aeropuerto`: String (5, opcional)
- `es_capital`: Boolean
- `imagen_url`: URL (500, opcional)
- `activo`: Boolean

### Aerolinea

- `id`: Integer (auto)
- `nombre`: String (100)
- `codigo_iata`: String (3, opcional)
- `logo_url`: URL (500, opcional)
- `pais_origen`: String (100, opcional)
- `sitio_web`: URL (300, opcional)
- `activo`: Boolean

### PaqueteTuristico

- `id`: Integer (auto)
- `titulo`: String (200)
- `subtitulo`: String (200, opcional)
- `imagen_url`: URL (500)
- `descripcion_corta`: Text (500)
- `region`: ForeignKey (Region)
- `pais_destino`: ForeignKey (PaisRegion)
- `ciudad_destino`: ForeignKey (Ciudad, opcional)
- `precio`: Decimal (10,2)
- `moneda`: String (3, default: USD)
- `tipo_paquete`: Choice (vacaciones, promo, oferta, todo_incluido, aventura, luna_miel, familiar, negocios)
- `duracion_dias`: Integer
- `duracion_noches`: Integer
- `salidas`: String (200)
- `fecha_salidas_texto`: String (100, opcional)
- `aerolinea`: ForeignKey (Aerolinea, opcional)
- `titulo_detalle`: String (300, opcional)
- `descripcion_extensa`: Text (opcional)
- `temporada`: Choice (baja, media, alta)
- `tipo_viaje`: Choice (familiar, pareja, amigos, solo, negocios, aventura)
- `precio_aplica_desde`: Date (opcional)
- `precio_aplica_hasta`: Date (opcional)
- `ubicacion_mapa_url`: URL (500, opcional)
- `idioma`: String (100, opcional)
- `moneda_local`: String (100, opcional)
- `lugares_destacados`: Text (opcional)
- `documentos_requeridos`: Text (opcional)
- `temperatura`: String (50, opcional)
- `programa_incluye`: Text (opcional)
- `no_incluye`: Text (opcional)
- `como_reservar`: Text (opcional)
- `importante`: Text (opcional)
- `horarios_vuelo`: Text (opcional)
- `politicas_equipaje`: Text (opcional)
- `requisitos_viaje`: Text (opcional)
- `formas_pago`: Text (opcional)
- `politica_cancelacion`: Text (opcional)
- `incluye_vuelo`: Boolean (default: true)
- `incluye_hotel`: Boolean (default: true)
- `incluye_alimentacion`: Boolean (default: false)
- `incluye_traslados`: Boolean (default: false)
- `incluye_tours`: Boolean (default: false)
- `incluye_seguro`: Boolean (default: false)
- `pdf_url`: URL (500, opcional)
- `mensaje_reserva`: Text (opcional)
- `destacado`: Boolean
- `activo`: Boolean
- `fecha_creacion`: DateTime (auto)
- `fecha_actualizacion`: DateTime (auto)

---

## 🔍 Filtros Disponibles

### Hoteles

- `?destino={id}` - Filtrar por destino

### Vuelos

- `?origen={ciudad}` - Filtrar por origen
- `?destino={ciudad}` - Filtrar por destino

### Renta de Autos

- `?tipo={tipo}` - Filtrar por tipo
- `?ubicacion={ubicacion}` - Filtrar por ubicación
- `?ciudad={id}` - Filtrar por ciudad
- `?pais={id}` - Filtrar por país
- `?region={id}` - Filtrar por región

### Países

- `?region={id}` - Filtrar por región

### Ciudades

- `?pais={id}` - Filtrar por país
- `?region={id}` - Filtrar por región
- `?capital=true` - Solo capitales

### Paquetes Turísticos

- `?region={id}` - Filtrar por región
- `?pais={id}` - Filtrar por país
- `?tipo={tipo}` - Filtrar por tipo de paquete
- `?temporada={temporada}` - Filtrar por temporada
- `?precio_max={precio}` - Filtrar por precio máximo
- `?destacados=true` - Solo destacados
- `?aerolinea={id}` - Filtrar por aerolínea

---

## 📝 Notas Adicionales

### Validación de PDFs

Todos los campos `pdf_url` aceptan URLs de Google Drive y automáticamente las convierten al formato de vista previa (`/preview`). El formato esperado es:

```
https://drive.google.com/file/d/ID_DEL_ARCHIVO/view
```

### Notificaciones

El endpoint `/api/contacto/` envía automáticamente:

1. Un correo electrónico a la empresa con los datos del contacto
2. Una notificación por WhatsApp (si está configurado)

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
```

### Python (requests)

```python
import requests

# Obtener paquetes de una región específica
response = requests.get('http://127.0.0.1:8000/api/paquetes/', params={'region': 1})
paquetes = response.json()

# Crear una solicitud
data = {
    'cliente': 1,
    'mensaje': 'Solicito información adicional'
}
response = requests.post('http://127.0.0.1:8000/api/solicitudes/', json=data)
```

---

## 📧 Contacto y Soporte

Para más información o soporte técnico, contacta al equipo de desarrollo.

**Última actualización:** Febrero 10, 2026
