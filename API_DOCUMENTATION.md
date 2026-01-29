# 📚 Documentación de APIs - CorpoDG Backend

## 🌐 Base URL

```
http://localhost:8000/api/
```

## 📋 Endpoints Disponibles

### 1️⃣ **Destinos Turísticos**

- **GET** `/api/destinos/` - Listar todos los destinos activos
- **GET** `/api/destinos/{id}/` - Ver detalle de un destino
- **POST** `/api/destinos/` - Crear nuevo destino
- **PUT** `/api/destinos/{id}/` - Actualizar destino completo
- **PATCH** `/api/destinos/{id}/` - Actualizar destino parcial
- **DELETE** `/api/destinos/{id}/` - Eliminar destino

**Ejemplo de respuesta:**

```json
{
  "id": 1,
  "nombre": "Galápagos",
  "pais": "Ecuador",
  "descripcion": "Islas paradisíacas con flora y fauna única",
  "imagen_url": "https://ejemplo.com/galapagos.jpg",
  "precio_desde": 1500.0,
  "destacado": true,
  "activo": true,
  "fecha_creacion": "2026-01-29T10:00:00Z",
  "fecha_actualizacion": "2026-01-29T10:00:00Z"
}
```

---

### 2️⃣ **Hoteles**

- **GET** `/api/hoteles/` - Listar todos los hoteles disponibles
- **GET** `/api/hoteles/?destino={id}` - Filtrar hoteles por destino
- **GET** `/api/hoteles/{id}/` - Ver detalle de un hotel
- **POST** `/api/hoteles/` - Crear nuevo hotel
- **PUT** `/api/hoteles/{id}/` - Actualizar hotel completo
- **PATCH** `/api/hoteles/{id}/` - Actualizar hotel parcial
- **DELETE** `/api/hoteles/{id}/` - Eliminar hotel

**Ejemplo de respuesta:**

```json
{
  "id": 1,
  "nombre": "Finch Bay Galapagos Hotel",
  "destino": 1,
  "destino_nombre": "Galápagos",
  "descripcion": "Hotel boutique en la playa",
  "imagen_url": "https://ejemplo.com/hotel.jpg",
  "direccion": "Puerto Ayora, Santa Cruz",
  "estrellas": 5,
  "precio_noche": 280.0,
  "servicios": "Wi-Fi, Piscina, Restaurante, Spa",
  "servicios_lista": ["Wi-Fi", "Piscina", "Restaurante", "Spa"],
  "disponible": true,
  "fecha_creacion": "2026-01-29T10:00:00Z",
  "fecha_actualizacion": "2026-01-29T10:00:00Z"
}
```

---

### 3️⃣ **Vuelos**

- **GET** `/api/vuelos/` - Listar todos los vuelos disponibles
- **GET** `/api/vuelos/?origen={ciudad}` - Filtrar por origen
- **GET** `/api/vuelos/?destino={ciudad}` - Filtrar por destino
- **GET** `/api/vuelos/{id}/` - Ver detalle de un vuelo
- **POST** `/api/vuelos/` - Crear nuevo vuelo
- **PUT** `/api/vuelos/{id}/` - Actualizar vuelo completo
- **PATCH** `/api/vuelos/{id}/` - Actualizar vuelo parcial
- **DELETE** `/api/vuelos/{id}/` - Eliminar vuelo

**Ejemplo de respuesta:**

```json
{
  "id": 1,
  "aerolinea": "TAME",
  "origen": "Quito",
  "destino": "Galápagos",
  "tipo_vuelo": "directo",
  "duracion": "1h 45m",
  "precio": 280.0,
  "imagen_url": "https://ejemplo.com/vuelo.jpg",
  "moneda": "USD",
  "disponible": true,
  "fecha_creacion": "2026-01-29T10:00:00Z",
  "fecha_actualizacion": "2026-01-29T10:00:00Z"
}
```

---

### 4️⃣ **Renta de Autos**

- **GET** `/api/renta-autos/` - Listar todos los autos disponibles
- **GET** `/api/renta-autos/?tipo={tipo}` - Filtrar por tipo (economico, sedan, suv, lujo, van)
- **GET** `/api/renta-autos/?ubicacion={ciudad}` - Filtrar por ubicación
- **GET** `/api/renta-autos/{id}/` - Ver detalle de un auto
- **POST** `/api/renta-autos/` - Crear nuevo auto
- **PUT** `/api/renta-autos/{id}/` - Actualizar auto completo
- **PATCH** `/api/renta-autos/{id}/` - Actualizar auto parcial
- **DELETE** `/api/renta-autos/{id}/` - Eliminar auto

**Ejemplo de respuesta:**

```json
{
  "id": 1,
  "marca": "Toyota",
  "modelo": "RAV4",
  "tipo": "suv",
  "ano": 2024,
  "capacidad_pasajeros": 5,
  "transmision": "automatica",
  "precio_dia": 85.0,
  "imagen_url": "https://ejemplo.com/auto.jpg",
  "ubicacion": "Quito",
  "caracteristicas": "GPS, Aire acondicionado, Bluetooth",
  "caracteristicas_lista": ["GPS", "Aire acondicionado", "Bluetooth"],
  "disponible": true,
  "fecha_creacion": "2026-01-29T10:00:00Z",
  "fecha_actualizacion": "2026-01-29T10:00:00Z"
}
```

---

### 5️⃣ **Mensajes de Contacto**

- **GET** `/api/mensajes/` - Listar todos los mensajes
- **GET** `/api/mensajes/{id}/` - Ver detalle de un mensaje
- **POST** `/api/mensajes/` - Crear nuevo mensaje
- **PATCH** `/api/mensajes/{id}/` - Marcar como leído/respondido
- **DELETE** `/api/mensajes/{id}/` - Eliminar mensaje

**Ejemplo de request (POST):**

```json
{
  "nombre": "Juan Pérez",
  "email": "juan@example.com",
  "telefono": "0998765432",
  "asunto": "Consulta sobre viaje a Galápagos",
  "mensaje": "Quisiera información sobre paquetes disponibles para 4 personas"
}
```

**Ejemplo de respuesta:**

```json
{
  "id": 1,
  "nombre": "Juan Pérez",
  "email": "juan@example.com",
  "telefono": "0998765432",
  "asunto": "Consulta sobre viaje a Galápagos",
  "mensaje": "Quisiera información sobre paquetes disponibles para 4 personas",
  "fecha_envio": "2026-01-29T10:00:00Z",
  "leido": false,
  "respondido": false
}
```

---

### 6️⃣ **Clientes y Solicitudes (Ya existentes)**

- **GET** `/api/clientes/` - Listar todos los clientes
- **GET** `/api/solicitudes/` - Listar todas las solicitudes
- **POST** `/api/contacto/` - Formulario de contacto con envío de email

---

## 🔧 Panel de Administración

Accede al panel de administración de Django en:

```
http://localhost:8000/admin/
```

Desde ahí puedes:

- ✅ Crear, editar y eliminar **Destinos**
- ✅ Crear, editar y eliminar **Hoteles**
- ✅ Crear, editar y eliminar **Vuelos**
- ✅ Crear, editar y eliminar **Renta de Autos**
- ✅ Ver y gestionar **Mensajes** recibidos
- ✅ Ver **Clientes** y **Solicitudes**

---

## 🚀 Cómo usar desde el Frontend

### Ejemplo de fetch en React/Vue:

```javascript
// Obtener todos los destinos
const destinos = await fetch("http://localhost:8000/api/destinos/").then(
  (res) => res.json(),
);

// Obtener hoteles de un destino específico
const hoteles = await fetch(
  "http://localhost:8000/api/hoteles/?destino=1",
).then((res) => res.json());

// Obtener vuelos desde Quito
const vuelos = await fetch(
  "http://localhost:8000/api/vuelos/?origen=Quito",
).then((res) => res.json());

// Enviar un mensaje
await fetch("http://localhost:8000/api/mensajes/", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    nombre: "María García",
    email: "maria@example.com",
    telefono: "0987654321",
    asunto: "Consulta de viaje",
    mensaje: "Hola, quisiera más información...",
  }),
});
```

---

## ✅ Características

- ✅ CRUD completo para todos los servicios
- ✅ Filtros por parámetros en URLs
- ✅ Panel de administración completo
- ✅ API REST con JSON
- ✅ CORS configurado para frontend
- ✅ Campos de fecha automáticos
- ✅ Sistema de disponibilidad/activo

---

## 🎯 Próximos pasos

1. Inicia el servidor: `python manage.py runserver`
2. Accede al admin: http://localhost:8000/admin/
3. Agrega datos de prueba (hoteles, vuelos, etc.)
4. Conecta tu frontend a las APIs
5. ¡Listo! 🎉
